import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

export const DEFAULT_QUERY_URL = "https://poll.kuaidi100.com/poll/query.do";
export const DEFAULT_AUTO_URL = "https://www.kuaidi100.com/autonumber/auto";
export const DEFAULT_RECENT_LIMIT = 3;

export function loadConfig({ argv = process.argv.slice(2), cwd = process.cwd(), env = process.env } = {}) {
  const args = parseArgs(argv);
  const fileEnv = loadDotEnvLocal(cwd);
  const mergedEnv = { ...fileEnv, ...env };

  return {
    cwd,
    number: args.number ?? null,
    carrier: args.carrier ?? null,
    phone: args.phone ?? "",
    from: args.from ?? "",
    to: args.to ?? "",
    json: args.json,
    recentLimit: parsePositiveInt(
      args.recent ?? mergedEnv.EXPRESS_TRACKING_DEFAULT_RECENT_LIMIT,
      DEFAULT_RECENT_LIMIT
    ),
    kuaidi100: {
      key: mergedEnv.EXPRESS_TRACKING_KUAIDI100_KEY ?? null,
      customer: mergedEnv.EXPRESS_TRACKING_KUAIDI100_CUSTOMER ?? null,
      queryUrl: mergedEnv.EXPRESS_TRACKING_KUAIDI100_QUERY_URL ?? DEFAULT_QUERY_URL,
      autoUrl: mergedEnv.EXPRESS_TRACKING_KUAIDI100_AUTO_URL ?? DEFAULT_AUTO_URL
    }
  };
}

function parseArgs(argv) {
  const args = {
    number: null,
    carrier: null,
    phone: null,
    from: null,
    to: null,
    recent: null,
    json: false
  };

  for (const arg of argv) {
    if (arg === "--json") {
      args.json = true;
      continue;
    }
    if (arg.startsWith("--key") || arg.startsWith("--customer") || arg.startsWith("--api-key")) {
      throw new Error("不要通过命令行传入凭据，请使用当前 shell 或项目根目录下的 .env.local。");
    }

    const [rawKey, rawValue] = arg.split("=", 2);
    const value = rawValue ?? null;
    switch (rawKey) {
      case "--number":
        args.number = value;
        break;
      case "--carrier":
        args.carrier = value;
        break;
      case "--phone":
        args.phone = value ?? "";
        break;
      case "--from":
        args.from = value ?? "";
        break;
      case "--to":
        args.to = value ?? "";
        break;
      case "--recent":
      case "--recent-limit":
        args.recent = value;
        break;
      case "-h":
      case "--help":
        printUsage();
        process.exit(0);
        break;
      default:
        if (rawKey.startsWith("--")) {
          throw new Error(`未知参数: ${rawKey}`);
        }
        break;
    }
  }

  return args;
}

function printUsage() {
  console.log(`用法:
  node .codex/skills/express-tracking/scripts/run.mjs --number="<tracking-number>" [--carrier="<kuaidi100-company-code>"] [--json] [--recent-limit="<count>"]`);
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
