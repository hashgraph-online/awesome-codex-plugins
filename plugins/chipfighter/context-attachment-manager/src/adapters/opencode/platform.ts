// Purpose: v0.11 — OpenCode: the core alone, no panel. Each provider in opencode.json takes its own base URL
// (`provider.<id>.options.baseURL`), so the route is for one provider: the one named, else the one of the configured
// `model` ("anthropic/…"); without a baseURL of its own a provider uses its SDK's address (the defaults below). The
// request format follows the provider. Its requests name no session the engine knows, so sessions are told apart by
// their first prompt; a plugin of OpenCode's own could add `x-cam-session` in its `model.request` hook. MCP servers go
// under "mcp"; the global config is in ~/.config/opencode (OPENCODE_CONFIG_DIR moves it); shell commands run with
// OPENCODE=1. Not tested live.
// Input: the environment, the config file. Output: the platform's entry (core/platform.ts).

import { existsSync } from "node:fs";
import { join } from "node:path";
import { jsonAt } from "../../core/config-edit.ts";
import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

// The AI SDK providers' own addresses.
const DEFAULTS: Record<string, string> = {
  anthropic: "https://api.anthropic.com/v1",
  openai: "https://api.openai.com/v1",
  google: "https://generativelanguage.googleapis.com/v1beta",
};

function configFile(home: string, env: NodeJS.ProcessEnv): string {
  const dir = env.OPENCODE_CONFIG_DIR?.trim() || join(home, ".config", "opencode");
  const jsonc = join(dir, "opencode.jsonc");
  return !existsSync(join(dir, "opencode.json")) && existsSync(jsonc) ? jsonc : join(dir, "opencode.json");
}

export const opencode: CorePlatform = {
  name: "opencode",
  title: "OpenCode",
  upstream: null,
  detect: (env) => env.OPENCODE === "1",
  setup: ({ home, env, provider }) => {
    const file = configFile(home, env);
    const model = jsonAt(file, ["model"]);
    const name = provider ?? (typeof model === "string" && model.includes("/") ? model.split("/")[0] : null);
    if (!name) throw new Error("OpenCode: name the provider whose requests should go through the engine, e.g. --provider anthropic");
    const set = jsonAt(file, ["provider", name, "options", "baseURL"]);
    return {
      current: typeof set === "string" ? set : null,
      fallback: DEFAULTS[name] ?? null,
      edits: ({ url, mcp }) => [
        { file, json: ["provider", name, "options", "baseURL"], value: url },
        { file, json: ["mcp", MCP_NAME], value: { type: "local", command: [mcp.command, ...mcp.args], environment: mcp.env, enabled: true } },
      ],
    };
  },
  connect: ({ url, mcp }) => [
    `In opencode.json, set your provider's base URL: "provider": { "<provider id>": { "options": { "baseURL": "${url}" } } }`,
    `Add the MCP server: "mcp": { "${MCP_NAME}": { "type": "local", "command": ${JSON.stringify([mcp.command, ...mcp.args])}, "environment": ${JSON.stringify(mcp.env)} } }`,
    "Restart OpenCode.",
  ],
};
