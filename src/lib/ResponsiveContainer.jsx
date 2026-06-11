import { useState, useRef, useLayoutEffect, cloneElement, Children } from "react";

// Drop-in replacement for recharts' <ResponsiveContainer>.
//
// recharts' own ResponsiveContainer measures its parent with a ResizeObserver
// and renders nothing until the observer's first callback reports a non-zero
// size. Under React.StrictMode (dev), the double mount/unmount can leave the
// surviving mount without that first "size changed" callback — so the chart
// stays at the 0×0 it measured initially and the panel renders as a blank gap
// (the bug this fixes).
//
// Here we instead measure synchronously in useLayoutEffect (before paint) and
// re-measure on every mount, so a StrictMode remount always re-derives the real
// size. The ResizeObserver only handles later layout changes. Same usage as the
// recharts component: a single chart child, sized to fill its parent.
export const ResponsiveContainer = ({ children, minHeight }) => {
  const ref = useRef(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const measure = () => {
      const w = Math.floor(el.clientWidth);
      const h = Math.floor(el.clientHeight);
      setSize((prev) => (prev.width === w && prev.height === h ? prev : { width: w, height: h }));
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const ready = size.width > 0 && size.height > 0;
  return (
    <div ref={ref} style={{ width: "100%", height: "100%", minHeight }}>
      {ready ? cloneElement(Children.only(children), { width: size.width, height: size.height }) : null}
    </div>
  );
};
