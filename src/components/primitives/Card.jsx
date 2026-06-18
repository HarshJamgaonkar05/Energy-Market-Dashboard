export const Card = ({ children, className = "", padding = true, ...rest }) => (
  <div
    className={`surface border border-[#1c1d22] rounded-xl transition-colors duration-150 print-keep ${
      padding ? "p-4" : ""
    } ${className}`}
    {...rest}
  >
    {children}
  </div>
);
