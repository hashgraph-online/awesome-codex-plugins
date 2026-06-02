import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["../../tests/captcha-auto-skill/**/*.test.mjs"],
    exclude: ["../../tests/captcha-auto-skill/live/**"]
  }
});
