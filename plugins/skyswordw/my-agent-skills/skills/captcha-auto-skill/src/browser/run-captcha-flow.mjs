import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { chromium } from "playwright-core";

import { loadConfig } from "../config.mjs";
import { runCaptchaRouter } from "../router.mjs";
import { detectChromePath } from "./chrome-path.mjs";
import { locateCaptchaTargets } from "./locate-captcha.mjs";

export async function runCaptchaFlow({
  url,
  profile = "free-first",
  provider = null,
  model = null,
  debugScreenshots = false,
  applyPageActions = false,
  artifactsDir = path.resolve("artifacts"),
  modelscopeCatalog = null,
  dashscopeCatalog = null,
  refreshCatalog = false,
  catalogTtlSeconds = null,
  catalogCacheDir = null,
  modelscopeConfig = {},
  dashscopeConfig = {},
  launchBrowser = defaultLaunchBrowser,
  locateCaptcha = locateCaptchaTargets,
  runRouter = runCaptchaRouter
}) {
  const browser = await launchBrowser();
  const debugArtifacts = {};
  let page;
  let tempDir = null;
  let captchaPath = null;

  try {
    page = await browser.newPage();
    await page.goto(url);

    const fullPageBuffer =
      typeof page.screenshot === "function" ? await page.screenshot({ fullPage: true }) : null;

    if (debugScreenshots && fullPageBuffer) {
      await mkdir(artifactsDir, { recursive: true });
      debugArtifacts.fullPage = path.join(artifactsDir, "full-page.png");
      await writeFile(debugArtifacts.fullPage, fullPageBuffer);
    }

    const located = await locateCaptcha(page);
    tempDir = await mkdtemp(path.join(os.tmpdir(), "captcha-auto-crop-"));
    captchaPath = path.join(tempDir, "captcha.png");
    await writeFile(captchaPath, located.captchaBuffer);

    if (debugScreenshots) {
      await mkdir(artifactsDir, { recursive: true });
      debugArtifacts.captchaCrop = path.join(artifactsDir, "captcha-crop.png");
      await writeFile(debugArtifacts.captchaCrop, located.captchaBuffer);
    }

    const result = await runRouter({
      profile,
      provider,
      model,
      inputPath: captchaPath,
      imageBuffer: located.captchaBuffer,
      modelscopeCatalog,
      dashscopeCatalog,
      refreshCatalog,
      catalogTtlSeconds,
      catalogCacheDir,
      modelscopeConfig,
      dashscopeConfig
    });

    if (result.success && applyPageActions) {
      if (typeof located.fill === "function") {
        await located.fill(result.text);
      }
      if (typeof located.submit === "function") {
        await located.submit();
      }
    }

    return {
      ...result,
      debugArtifacts
    };
  } finally {
    if (tempDir) {
      await rm(tempDir, { recursive: true, force: true });
    } else if (captchaPath) {
      await rm(captchaPath, { force: true });
    }
    await browser.close();
  }
}

export async function runCaptchaFlowFromConfig(options = {}) {
  const config = loadConfig(options);
  if (!config.url) {
    throw new Error("Pass --url=<page-url> when using browser captcha flow.");
  }
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

async function defaultLaunchBrowser() {
  return chromium.launch({
    headless: true,
    executablePath: detectChromePath()
  });
}
