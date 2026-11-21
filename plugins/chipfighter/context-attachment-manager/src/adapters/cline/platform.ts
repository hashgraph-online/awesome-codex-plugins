// Purpose: v0.11 — Cline (VS Code, JetBrains and its CLI share one configuration): the core alone, no panel. Providers
// are in ~/.cline/data/settings/providers.json (CLINE_DIR moves ~/.cline), each with an optional `settings.baseUrl`
// over its built-in address (the defaults below, from Cline's provider list); `lastUsedProvider` is the one in use.
// Cline's own account provider goes to Cline's service and is not handled. The request format follows the provider.
// Its requests name no session the engine knows, so sessions are told apart by their first prompt. MCP servers are in
// ~/.cline/data/settings/cline_mcp_settings.json; its terminals run with CLINE_ACTIVE=true. providers.json also holds
// the API keys: only the one address is changed in it, and the file is never copied. Not tested live.
// Input: the environment, the settings files. Output: the platform's entry (core/platform.ts).

import { join } from "node:path";
import { jsonAt } from "../../core/config-edit.ts";
import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

const DEFAULTS: Record<string, string> = {
  anthropic: "https://api.anthropic.com/v1",
  "openai-native": "https://api.openai.com/v1",
  gemini: "https://generativelanguage.googleapis.com/v1beta",
  deepseek: "https://api.deepseek.com/v1",
  openrouter: "https://openrouter.ai/api/v1",
};

export const cline: CorePlatform = {
  name: "cline",
  title: "Cline",
  upstream: null,
  detect: (env) => env.CLINE_ACTIVE === "true",
  setup: ({ home, env, provider }) => {
    const settings = join(env.CLINE_DIR?.trim() || join(home, ".cline"), "data", "settings");
    const providers = join(settings, "providers.json");
    const used = jsonAt(providers, ["lastUsedProvider"]);
    const name = provider ?? (typeof used === "string" ? used : null);
    if (!name) throw new Error("Cline: name the provider whose requests should go through the engine, e.g. --provider anthropic");
    if (name === "cline") throw new Error("Cline: its own account provider goes to Cline's service; pick a provider with your own key (Anthropic, OpenAI, OpenRouter, …)");
    const set = jsonAt(providers, ["providers", name, "settings", "baseUrl"]);
    return {
      current: typeof set === "string" ? set : null,
      fallback: DEFAULTS[name] ?? null,
      edits: ({ url, mcp }) => [
        { file: providers, json: ["providers", name, "settings", "baseUrl"], value: url },
        { file: env.CLINE_MCP_SETTINGS_PATH?.trim() || join(settings, "cline_mcp_settings.json"), json: ["mcpServers", MCP_NAME], value: { command: mcp.command, args: mcp.args, env: mcp.env } },
      ],
    };
  },
  connect: ({ url, mcp }) => [
    `In Cline's provider settings, set the base URL of the provider you use to ${url}`,
    `In Cline's MCP servers (Configure MCP Servers), add: "${MCP_NAME}": ${JSON.stringify({ command: mcp.command, args: mcp.args, env: mcp.env })}`,
    "Reload the VS Code window (or restart the Cline CLI).",
  ],
};
