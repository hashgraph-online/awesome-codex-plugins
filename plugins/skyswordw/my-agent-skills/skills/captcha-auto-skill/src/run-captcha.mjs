import { readFile } from "node:fs/promises";

import { loadConfig } from "./config.mjs";
import { runCaptchaRouter } from "./router.mjs";
import { runCaptchaFlow } from "./browser/run-captcha-flow.mjs";

export async function runCaptchaCandidate({
  inputPath,
  profile = "free-first",
  provider = null,
  model = null,
  modelscopeCatalog = null,
  dashscopeCatalog = null,
  refreshCatalog = false,
  catalogTtlSeconds = null,
  catalogCacheDir = null,
  modelscopeConfig = {},
  dashscopeConfig = {},
  readImage = readFile,
  runRouter = runCaptchaRouter
}) {
  if (!inputPath) {
    throw new Error("Pass --input=<captcha-image> to generate a candidate answer from a local file.");
  }

  const imageBuffer = await readImage(inputPath);

  return runRouter({
    profile,
    provider,
    model,
    inputPath,
    imageBuffer,
    modelscopeCatalog,
    dashscopeCatalog,
    refreshCatalog,
    catalogTtlSeconds,
    catalogCacheDir,
    modelscopeConfig,
    dashscopeConfig
  });
}

export async function runCaptchaFromConfig(options = {}) {
  const config = loadConfig(options);

  if (config.inputPath) {
    return runCaptchaCandidate({
      inputPath: config.inputPath,
      profile: config.profile,
      provider: config.provider,
      model: config.model,
      refreshCatalog: config.refreshCatalog,
      catalogTtlSeconds: config.catalogTtlSeconds,
      catalogCacheDir: config.catalogCacheDir,
      modelscopeConfig: config.modelscope,
      dashscopeConfig: config.dashscope
    });
  }

  if (config.url) {
    return runCaptchaFlow({
      url: config.url,
      profile: config.profile,
      provider: config.provider,
      model: config.model,
      debugScreenshots: config.debugScreenshots,
      applyPageActions: config.applyPageActions,
      refreshCatalog: config.refreshCatalog,
      catalogTtlSeconds: config.catalogTtlSeconds,
      catalogCacheDir: config.catalogCacheDir,
      modelscopeConfig: config.modelscope,
      dashscopeConfig: config.dashscope
    });
  }

  throw new Error(
    "Pass --input=<captcha-image> to generate a candidate answer or --url=<page-url> to inspect a captcha page."
  );
}
