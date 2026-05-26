export const Card = ({ children, className = "", padding = true, ...rest }) => (
  <div
    className={`bg-[#0e0f12] border border-[#1c1d22] ${padding ? "p-4" : ""} ${className}`}
    {...rest}
  >
    {children}
  </div>
);
