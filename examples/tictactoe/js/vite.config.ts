// File UUID: 1f6b3e95-8c27-4d40-a9e2-7b5d0c8f4a16
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180, host: "localhost",
    proxy: {
      "/api/mcp": "http://127.0.0.1:4101",
      "/api/a2ui": "http://127.0.0.1:4201",
      "/api/agui": "http://127.0.0.1:4301",
      "/api/chat": "http://127.0.0.1:4401",
    },
  },
});
