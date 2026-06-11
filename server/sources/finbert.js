// ============================================================================
// FinBERT sentiment — scores each newswire headline positive / negative /
// neutral with ProsusAI/finbert (BERT fine-tuned on financial text), replacing
// the old bull/bear keyword regexes.
//
// Two backends, picked automatically:
//   • HF_TOKEN set  → Hugging Face's hosted Inference API does the inference.
//     Nothing heavy runs in this process, so it works on a tiny free host.
//   • otherwise     → the model runs LOCALLY in-process via Transformers.js
//     (ONNX, downloaded once & cached) — great for local dev, but needs ~1–2 GB
//     RAM so it's unsuitable for a 512 MB free instance.
//
// Everything degrades gracefully: if the chosen backend is unavailable,
// `scoreHeadlines` resolves to `null` and callers fall back to the keyword
// heuristic — the dashboard never breaks. Set FINBERT_DISABLE=1 to force the
// keyword fallback regardless.
// ============================================================================

const MODEL = "Xenova/finbert"; // ONNX port of ProsusAI/finbert (local backend)
const HF_TOKEN = (process.env.HF_TOKEN || process.env.HUGGINGFACE_TOKEN || "").trim();
// HF's current hosted-inference endpoint (the old api-inference.huggingface.co
// host was retired). Override with HF_URL if you use a different provider/model.
const HF_URL = process.env.HF_URL || "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert";

// Per-headline score cache. Headlines repeat across polls (the wire is cached
// 4 min and items linger for hours), so we never re-run the model on text we've
// already seen. Keyed by the exact headline string.
const scoreCache = new Map();
const MAX_CACHE = 2000;

let classifierPromise = null; // singleton; null until first use, then a Promise
// Set FINBERT_DISABLE=1 to skip the ML model entirely (e.g. on a small free host
// that can't fit it) — news sentiment then uses the keyword fallback. Also set
// automatically if the model fails to load, to stop retrying.
let disabled = ["1", "true", "yes"].includes((process.env.FINBERT_DISABLE || "").toLowerCase());

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
    // In a container the default cache dir may be read-only; point it at a
    // writable path when TRANSFORMERS_CACHE is set (see Dockerfile). No effect
    // locally where the var is unset.
    if (process.env.TRANSFORMERS_CACHE) env.cacheDir = process.env.TRANSFORMERS_CACHE;
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

// Warm up the LOCAL model in the background on import (so the first /api/news
// request doesn't pay the load cost). Skipped when offloading to HF or disabled.
if (!HF_TOKEN && !disabled) getClassifier();

// Score a batch of headlines via Hugging Face's hosted Inference API. Returns
// shaped records aligned to `texts`. `wait_for_model` lets HF spin the model up
// on a cold call instead of 503-ing. Throws on any HTTP/shape error so the
// caller falls back to keywords.
async function scoreViaHF(texts) {
  const res = await fetch(HF_URL, {
    method: "POST",
    headers: { Authorization: `Bearer ${HF_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({ inputs: texts, options: { wait_for_model: true } }),
  });
  if (!res.ok) throw new Error(`HF API ${res.status}: ${(await res.text()).slice(0, 120)}`);
  const data = await res.json();
  // Expected: Array<Array<{label,score}>> aligned to inputs.
  if (!Array.isArray(data) || !Array.isArray(data[0])) throw new Error("HF API unexpected response shape");
  return data.map(shape);
}

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
    if (disabled) return null;
    try {
      let records;
      if (HF_TOKEN) {
        // Hosted backend — nothing heavy runs here.
        records = await scoreViaHF(todo);
      } else {
        const clf = await getClassifier();
        if (!clf) return null; // local model unavailable → signal keyword fallback
        // top_k: 3 → all three class probabilities per headline. The pipeline
        // returns Array<Array<{label,score}>> for a batch, or a flat array for a
        // single input — normalize both shapes.
        const raw = await clf(todo, { top_k: 3 });
        const perText = todo.length === 1 && !Array.isArray(raw[0]) ? [raw] : raw;
        records = perText.map(shape);
      }
      todo.forEach((t, i) => scoreCache.set(t, records[i]));
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
