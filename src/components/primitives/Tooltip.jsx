import { useState } from "react";

// Lightweight hover/focus tooltip. Wraps inline content and floats a small
// panel above it. `align` shifts the panel so values near a card edge don't
// clip ("start" = left-aligned, "end" = right-aligned, default centered).
// The panel resets case/tracking so it stays readable even inside uppercase,
// letter-spaced labels.
export const Tooltip = ({ content, children, align = "center", className = "" }) => {
  const [show, setShow] = useState(false);
  if (!content) return children;

  const pos =
    align === "start" ? "left-0"
    : align === "end" ? "right-0"
    : "left-1/2 -translate-x-1/2";

  return (
    <span
      className={`relative inline-flex ${className}`}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <span
          role="tooltip"
          className={`pointer-events-none absolute bottom-full ${pos} mb-1.5 z-50 w-max max-w-[230px] whitespace-normal
            border border-[#2a2b31] bg-[#0a0b0e] px-2.5 py-1.5 shadow-xl normal-case tracking-normal`}
        >
          {content}
        </span>
      )}
    </span>
  );
};
