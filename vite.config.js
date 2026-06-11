import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    // Split the heavy charting/animation vendors into their own chunks so they
    // cache independently of app code (and keep the per-page chunks small).
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules/recharts") || id.includes("node_modules/d3-") || id.includes("node_modules/victory-vendor")) return "recharts";
          if (id.includes("node_modules/framer-motion")) return "motion";
        },
      },
    },
  },
  server: {
    port: 5173,
    open: true,
    // Proxy API calls to the Node backend so the browser talks to one origin
    // (no CORS hassle in dev). Backend default port is 3001 (see server/index.js).
    proxy: {
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
