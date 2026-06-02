import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import { PROFILES, PROVIDERS } from "./contracts.mjs";
import {
  DASHSCOPE_DEFAULT_MODEL,
  DASHSCOPE_PINNED_FALLBACK_MODEL,
  isDeniedModel
} from "./model-preferences.mjs";

export const DEFAULT_PROFILE = "free-first";
export const DEFAULT_MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1";
export const DEFAULT_DASHSCOPE_BASE_URL =
  "https://dashscope.aliyuncs.com/compatible-mode/v1";
export const DEFAULT_CATALOG_TTL_SECONDS = 3600;

export function loadConfig({ argv = process.argv.slice(2), cwd = process.cwd(), env = process.env } = {}) {
  const args = parseArgs(argv);
  const fileEnv = loadDotEnvLocal(cwd);
  const mergedEnv = { ...fileEnv, ...env };
  const rawProfile = args.profile ?? mergedEnv.CAPTCHA_DEFAULT_PROFILE ?? DEFAULT_PROFILE;
  const profile = normalizeProfile(rawProfile);
  const provider = args.provider ? normalizeProvider(args.provider) : null;

  if (args.model && isDeniedModel(args.model)) {
    throw new Error(`Model ${args.model} is denylisted and cannot be selected.`);
  }

  return {
    url: args.url ?? null,
    inputPath: args.inputPath ? path.resolve(cwd, args.inputPath) : null,
    cwd,
    profile,
    provider,
    model: args.model ?? null,
    refreshCatalog: args.refreshCatalog,
    json: args.json,
    debugScreenshots: args.debugScreenshots,
    applyPageActions: args.applyPageActions,
    catalogTtlSeconds: parsePositiveInt(
      mergedEnv.CAPTCHA_CATALOG_TTL_SECONDS,
      DEFAULT_CATALOG_TTL_SECONDS
    ),
    catalogCacheDir: path.join(cwd, ".codex", "cache", "captcha-auto-skill", "catalogs"),
    modelscope: {
      baseUrl: mergedEnv.CAPTCHA_MODELSCOPE_BASE_URL ?? DEFAULT_MODELSCOPE_BASE_URL,
      apiKey: mergedEnv.CAPTCHA_MODELSCOPE_API_KEY ?? null
    },
    dashscope: {
      baseUrl: mergedEnv.CAPTCHA_DASHSCOPE_BASE_URL ?? DEFAULT_DASHSCOPE_BASE_URL,
      apiKey: mergedEnv.CAPTCHA_DASHSCOPE_API_KEY ?? null,
      defaultModel: DASHSCOPE_DEFAULT_MODEL,
      pinnedFallbackModel: DASHSCOPE_PINNED_FALLBACK_MODEL
    }
  };
}

function parseArgs(argv) {
  const args = {
    url: null,
    inputPath: null,
    profile: null,
    provider: null,
    model: null,
    refreshCatalog: false,
    json: false,
    debugScreenshots: false,
    applyPageActions: false
  };

  for (const arg of argv) {
    if (arg === "--refresh-catalog") {
      args.refreshCatalog = true;
      continue;
    }
    if (arg === "--json") {
      args.json = true;
      continue;
    }
    if (arg === "--debug-screenshots") {
      args.debugScreenshots = true;
      continue;
    }
    if (arg === "--apply-page-actions") {
      args.applyPageActions = true;
      continue;
    }
    if (arg.startsWith("--api-key")) {
      throw new Error(
        "The --api-key flag is disabled. Use project-local .env.local or process environment variables instead."
      );
    }

    const [rawKey, rawValue] = arg.split("=", 2);
    const value = rawValue ?? null;
    switch (rawKey) {
      case "--url":
        args.url = value;
        break;
      case "--input":
        args.inputPath = value;
        break;
      case "--profile":
        args.profile = value;
        break;
      case "--provider":
        args.provider = value;
        break;
      case "--model":
        args.model = value;
        break;
      default:
        break;
    }
  }

  return args;
}

function normalizeProfile(profile) {
  if (!PROFILES.includes(profile)) {
    throw new Error(`Unsupported profile: ${profile}`);
  }
  return profile;
}

function normalizeProvider(provider) {
  if (!PROVIDERS.includes(provider)) {
    throw new Error(`Unsupported provider: ${provider}`);
  }
  return provider;
}

function parsePositiveInt(rawValue, fallback) {
  const value = Number.parseInt(rawValue ?? "", 10);
  if (Number.isNaN(value) || value <= 0) {
    return fallback;
  }
  return value;
}

function loadDotEnvLocal(startDir) {
  for (const directory of walkUp(startDir)) {
    const filePath = path.join(directory, ".env.local");
    if (!existsSync(filePath)) {
      continue;
    }
    return parseDotEnv(readFileSync(filePath, "utf8"));
  }
  return {};
}

function* walkUp(startDir) {
  let current = path.resolve(startDir);
  while (true) {
    yield current;
    const parent = path.dirname(current);
    if (parent === current) {
      return;
    }
    current = parent;
  }
}

function parseDotEnv(content) {
  const env = {};
  for (const line of content.split(/\r?\n/u)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }
    const separator = trimmed.indexOf("=");
    if (separator <= 0) {
      continue;
    }
    const key = trimmed.slice(0, separator).trim();
    const value = trimmed.slice(separator + 1).trim().replace(/^['"]|['"]$/gu, "");
    env[key] = value;
  }
  return env;
}
