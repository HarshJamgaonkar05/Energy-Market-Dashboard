/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
      colors: {
        terminal: {
          bg: "#08090b",
          panel: "#0e0f12",
          panel2: "#131418",
          border: "#1c1d22",
          borderHi: "#2a2b31",
        },
        market: {
          bull: "#10b981",
          bear: "#ef4444",
          warn: "#f59e0b",
          info: "#38bdf8",
        },
        accent: {
          DEFAULT: "#f59e0b",
          dim: "#b45309",
        },
      },
      keyframes: {
        ticker: {
          "0%": { transform: "translateX(0%)" },
          "100%": { transform: "translateX(-50%)" },
        },
        blink: {
          "0%, 100%": { opacity: 1 },
          "50%": { opacity: 0.3 },
        },
        "fade-in": {
          "0%": { opacity: 0, transform: "translateY(4px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        ticker: "ticker 60s linear infinite",
        blink: "blink 2s ease-in-out infinite",
        "fade-in": "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
