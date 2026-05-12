import { defineConfig } from "vite";

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        main: "index.html",
        privacy: "privacy/index.html",
        privacyRu: "privacy.ru/index.html",
      },
    },
  },
  publicDir: "public",
});
