import { defineConfig } from "vite";

export default defineConfig({
  build: {
    rollupOptions: {
      input: {
        deleteAccount: "delete-account/index.html",
        eula: "eula/index.html",
        eulaRu: "eula.ru/index.html",
        main: "index.html",
        privacy: "privacy/index.html",
        privacyRu: "privacy.ru/index.html",
      },
    },
  },
  publicDir: "public",
});
