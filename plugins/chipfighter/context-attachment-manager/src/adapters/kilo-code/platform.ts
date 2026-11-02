// Purpose: v0.11 — Kilo Code (VS Code, JetBrains and its CLI, built on OpenCode): the core alone, no panel. Its config
// is OpenCode's, renamed: kilo.json (or kilo.jsonc) in ~/.config/kilo (KILO_CONFIG_DIR moves it), with each provider's
// `provider.<id>.options.baseURL` and MCP servers under "mcp"; the route is for one provider, the one named or the one
// of the configured `model`. Kilo's own gateway account is not handled. Its process sets KILO=1, which its shell
// commands keep. Its requests name no session the engine knows, so sessions are told apart by their first prompt. Not
// tested live. (The same shape as adapters/opencode; adapters do not share code.)
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
  const dir = env.KILO_CONFIG_DIR?.trim() || join(home, ".config", "kilo");
  const jsonc = join(dir, "kilo.jsonc");
  return !existsSync(join(dir, "kilo.json")) && existsSync(jsonc) ? jsonc : join(dir, "kilo.json");
}

export const kiloCode: CorePlatform = {
  name: "kilo-code",
  title: "Kilo Code",
  upstream: null,
  detect: (env) => env.KILO === "1",
  setup: ({ home, env, provider }) => {
    const file = configFile(home, env);
    const model = jsonAt(file, ["model"]);
    const name = provider ?? (typeof model === "string" && model.includes("/") ? model.split("/")[0] : null);
    if (!name) throw new Error("Kilo Code: name the provider whose requests should go through the engine, e.g. --provider anthropic");
    if (name === "kilo") throw new Error("Kilo Code: its own gateway account goes to Kilo's service; pick a provider with your own key");
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
    `In kilo.json (~/.config/kilo), set your provider's base URL: "provider": { "<provider id>": { "options": { "baseURL": "${url}" } } }`,
    `Add the MCP server: "mcp": { "${MCP_NAME}": { "type": "local", "command": ${JSON.stringify([mcp.command, ...mcp.args])}, "environment": ${JSON.stringify(mcp.env)} } }`,
    "Restart Kilo Code.",
  ],
};
