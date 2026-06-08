// ============================================================================
// FinBERT sentiment — runs the ProsusAI/finbert model locally, in-process, via
// Transformers.js (ONNX). No Python, no API key, no network at inference time
// (the quantized model is downloaded once on first run and cached on disk).
//
// FinBERT is BERT fine-tuned on financial text; it classifies a sentence as
// positive / negative / neutral. We use it to score each newswire headline,
// replacing the old bull/bear keyword regexes.
//
// Everything here degrades gracefully: if the model can't load (offline first
// run, unsupported platform, etc.) `scoreHeadlines` resolves to `null` and the
// callers fall back to the keyword heuristic — the dashboard never breaks.
// ============================================================================

const MODEL = "Xenova/finbert"; // ONNX port of ProsusAI/finbert (positive/negative/neutral)

// Per-headline score cache. Headlines repeat across polls (the wire is cached
// 4 min and items linger for hours), so we never re-run the model on text we've
// already seen. Keyed by the exact headline string.
const scoreCache = new Map();
const MAX_CACHE = 2000;

let classifierPromise = null; // singleton; null until first use, then a Promise
let disabled = false; // set true if the model fails to load — stop retrying

// Lazily build the text-classification pipeline exactly once. We import
// @huggingface/transformers dynamically so a missing/broken install can't crash
// the whole backend at startup — it just disables FinBERT.
async function getClassifier() {
  if (disabled) return null;
  if (classifierPromise) return classifierPromise;

  classifierPromise = (async () => {
    const { pipeline, env } = await import("@huggingface/transformers");
    // Go straight to the HF hub on first run (skip the local-model probe that
    // otherwise logs a warning), then rely on the on-disk cache.
    env.allowLocalModels = false;
    // Try the small quantized weights first; fall back to default precision.
    try {
      return await pipeline("text-classification", MODEL, { dtype: "q8" });
    } catch {
      return await pipeline("text-classification", MODEL);
    }
  })().catch((err) => {
    console.warn(`[finbert] model unavailable, falling back to keyword sentiment: ${err.message}`);
    disabled = true;
    return null;
  });

  return classifierPromise;
}

// Kick off the (slow, one-time) model load in the background as soon as this
// module is imported, so the first /api/news request isn't the one that waits.
getClassifier();

// Normalize one model output (an array of {label, score} for the 3 classes)
// into a tidy record. `signed` ∈ [-1, 1] = P(positive) − P(negative), the single
// number we use for the news index and the bull/bear tilt.
function shape(scores) {
  const m = { positive: 0, negative: 0, neutral: 0 };
  for (const s of scores) m[String(s.label).toLowerCase()] = s.score;
  const top = scores.reduce((a, b) => (b.score > a.score ? b : a), scores[0]);
  return {
    label: String(top.label).toLowerCase(), // "positive" | "negative" | "neutral"
    score: +top.score.toFixed(4), // confidence of the winning class
    pos: +m.positive.toFixed(4),
    neg: +m.negative.toFixed(4),
    neu: +m.neutral.toFixed(4),
    signed: +(m.positive - m.negative).toFixed(4),
  };
}

/**
 * Score an array of headline strings with FinBERT.
 * @param {string[]} texts
 * @returns {Promise<Array<object>|null>} per-text sentiment records aligned to
 *   the input, or `null` if the model is unavailable (caller should fall back).
 */
export async function scoreHeadlines(texts = []) {
  if (!texts.length) return [];

  // Figure out which headlines we haven't scored yet.
  const todo = [...new Set(texts.filter((t) => t && !scoreCache.has(t)))];

  if (todo.length) {
    const clf = await getClassifier();
    if (!clf) return null; // model unavailable → signal keyword fallback

    try {
      // top_k: 3 → return all three class probabilities per headline.
      const raw = await clf(todo, { top_k: 3 });
      // The pipeline returns Array<Array<{label,score}>> for a batch, or a flat
      // Array<{label,score}> for a single input — normalize both shapes.
      const perText = todo.length === 1 && !Array.isArray(raw[0]) ? [raw] : raw;
      todo.forEach((t, i) => scoreCache.set(t, shape(perText[i])));
    } catch (err) {
      console.warn(`[finbert] inference failed, using keyword fallback: ${err.message}`);
      return null;
    }

    // Bound the cache so a long-running server doesn't grow without limit.
    if (scoreCache.size > MAX_CACHE) {
      for (const k of [...scoreCache.keys()].slice(0, scoreCache.size - MAX_CACHE)) {
        scoreCache.delete(k);
      }
    }
  }

  return texts.map((t) => scoreCache.get(t) || null);
}

// True once at least one successful classification has happened (used by
// /api/health so the UI can tell "FinBERT live" from "keyword fallback").
export const finbertReady = () => scoreCache.size > 0 && !disabled;
export const finbertDisabled = () => disabled;
