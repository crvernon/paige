import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// During development the FastAPI backend runs on :8000. We proxy /api to it so
// the frontend can use same-origin relative URLs (matching the production
// Nginx setup).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
