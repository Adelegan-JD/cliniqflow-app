import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/record-officer": "http://127.0.0.1:8000",
      "/admin": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
      "/nlp": "http://127.0.0.1:8000",
      "/openapi.json": "http://127.0.0.1:8000",
      "/docs": "http://127.0.0.1:8000",
      "/redoc": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/patients": "http://127.0.0.1:8000",
      "/visits": "http://127.0.0.1:8000",
      "/ai": "http://127.0.0.1:8000",
      "/asr": "http://127.0.0.1:8000",
      "/translate": "http://127.0.0.1:8000",
      "/conversation": "http://127.0.0.1:8000",
      "/nurse": "http://127.0.0.1:8000",
      "/doctor": "http://127.0.0.1:8000",
      "/med-orders": "http://127.0.0.1:8000",
    },
  },
});
