import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/health": "http://localhost:8000",
      "/scalar": "http://localhost:8000",
      "/openapi.json": "http://localhost:8000",
      "/api": "http://localhost:8000",
    },
  },
});
