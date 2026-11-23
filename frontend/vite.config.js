
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiProxyTarget =
  process.env.API_PROXY_TARGET || "http://localhost:5000";

export default defineConfig({
  plugins: [react()],

  server: {
    open: process.env.API_PROXY_TARGET ? false : "/login",

    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
      },
    },
  },
});
