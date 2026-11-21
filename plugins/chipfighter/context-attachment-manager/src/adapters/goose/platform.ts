// Purpose: v0.11 — goose (aaif-goose/goose, desktop and CLI): the core alone, no panel. config.yaml (~/.config/goose, or
// %APPDATA%\Block\goose\config on Windows) names the provider in GOOSE_PROVIDER and its address in <PROVIDER>_HOST
// (ANTHROPIC_HOST, OPENAI_HOST, GOOGLE_HOST), by default the providers' own (below, from goose's provider code); MCP
// servers are stdio extensions in the same file. It is YAML, which this tool does not write, so the steps are printed;
// the provider and its address are read from it. Shell commands run with GOOSE_TERMINAL=1. Its requests name no
// session the engine knows, so sessions are told apart by their first prompt. Not tested live.
// Input: the environment, config.yaml. Output: the platform's entry (core/platform.ts).

import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

const DEFAULTS: Record<string, string> = {
  anthropic: "https://api.anthropic.com",
  openai: "https://api.openai.com",
  google: "https://generativelanguage.googleapis.com",
};

const configFile = (home: string, env: NodeJS.ProcessEnv) => (process.platform === "win32" && env.APPDATA ? join(env.APPDATA, "Block", "goose", "config", "config.yaml") : join(home, ".config", "goose", "config.yaml"));
// A top-level `KEY: value` line of config.yaml.
function yamlValue(file: string, key: string): string | null {
  if (!existsSync(file)) return null;
  const match = new RegExp(`^${key}:[ \\t]*["']?([^"'\\r\\n#]+?)["']?[ \\t]*(?:#.*)?$`, "m").exec(readFileSync(file, "utf8"));
  return match ? match[1].trim() : null;
}

export const goose: CorePlatform = {
  name: "goose",
  title: "goose",
  upstream: null,
  detect: (env) => env.GOOSE_TERMINAL === "1",
  setup: ({ home, env, provider }) => {
    const file = configFile(home, env);
    const name = (provider ?? env.GOOSE_PROVIDER?.trim() ?? yamlValue(file, "GOOSE_PROVIDER"))?.toLowerCase() ?? null;
    if (!name) throw new Error("goose: name the provider whose requests should go through the engine, e.g. --provider anthropic");
    const key = `${name.toUpperCase()}_HOST`;
    return {
      current: env[key]?.trim() || yamlValue(file, key),
      fallback: DEFAULTS[name] ?? null,
      edits: () => [],
      manual: `goose keeps its settings in YAML (${file}), which this command does not write: set them by hand, or with goose configure`,
    };
  },
  connect: ({ url, mcp }) => [
    `In goose's config.yaml, set the address of the provider you use: <PROVIDER>_HOST: ${url} (ANTHROPIC_HOST, OPENAI_HOST or GOOGLE_HOST)`,
    `Add under "extensions:": ${MCP_NAME}: { type: stdio, name: ${MCP_NAME}, enabled: true, cmd: ${JSON.stringify(mcp.command)}, args: ${JSON.stringify(mcp.args)}, envs: ${JSON.stringify(mcp.env)}, timeout: 300 }`,
    "Restart goose.",
  ],
};
