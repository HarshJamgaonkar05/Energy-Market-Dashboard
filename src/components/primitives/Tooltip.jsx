import { useState, useRef, useLayoutEffect, useCallback } from "react";
import { createPortal } from "react-dom";

// Lightweight hover/focus tooltip. The panel is rendered in a PORTAL on
// document.body with position:fixed, so it escapes every `overflow-hidden` /
// scrolling ancestor (cards, the scrollable main area) that would otherwise
// clip it. We measure the trigger + panel and clamp into the viewport, flipping
// below the trigger when there isn't room above — so the full text is always
// visible regardless of where the element sits.
//
// `align` biases the horizontal anchor ("start" = left edge, "end" = right
// edge, default centered); viewport clamping then guarantees it stays on-screen.
export const Tooltip = ({ content, children, align = "center", className = "" }) => {
  const [show, setShow] = useState(false);
  const [coords, setCoords] = useState(null); // {left, top} in viewport px, or null pre-measure
  const triggerRef = useRef(null);
  const tipRef = useRef(null);

  const place = useCallback(() => {
    const trigger = triggerRef.current;
    const tip = tipRef.current;
    if (!trigger || !tip) return;
    const t = trigger.getBoundingClientRect();
    const p = tip.getBoundingClientRect();
    const M = 8; // viewport margin
    const GAP = 6; // gap between trigger and panel

    // Horizontal anchor from `align`, then clamp inside the viewport.
    let left =
      align === "start" ? t.left
      : align === "end" ? t.right - p.width
      : t.left + t.width / 2 - p.width / 2;
    left = Math.max(M, Math.min(left, window.innerWidth - p.width - M));

    // Prefer above the trigger; flip below if it would clip the top edge.
    let top = t.top - p.height - GAP;
    if (top < M) top = t.bottom + GAP;

    setCoords({ left, top });
  }, [align]);

  // Measure synchronously before paint (avoids a visible flash at 0,0).
  useLayoutEffect(() => {
    if (show) place();
  }, [show, place]);

  if (!content) return children;

  return (
    <>
      <span
        ref={triggerRef}
        className={`relative inline-flex ${className}`}
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        onFocus={() => setShow(true)}
        onBlur={() => setShow(false)}
      >
        {children}
      </span>
      {show &&
        createPortal(
          <span
            ref={tipRef}
            role="tooltip"
            style={{ left: coords?.left ?? -9999, top: coords?.top ?? -9999, opacity: coords ? 1 : 0 }}
            className="pointer-events-none fixed z-[9999] w-max max-w-[260px] whitespace-normal
              border border-[#2a2b31] bg-[#0a0b0e] px-2.5 py-1.5 shadow-xl normal-case tracking-normal
              transition-opacity duration-75"
          >
            {content}
          </span>,
          document.body
        )}
    </>
  );
};
