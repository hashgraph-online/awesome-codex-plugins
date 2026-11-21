// Purpose: v0.11 — Qwen Code (QwenLM/qwen-code, grown out of Gemini CLI): the core alone, no panel. ~/.qwen/settings.json
// lists models per protocol under `modelProviders` (`openai`, `anthropic`, …), each with its own `baseUrl`;
// `security.auth.selectedType` names the protocol in use and `model.name` the model, so the route is for that model's
// entry. Without an entry, OPENAI_BASE_URL or ANTHROPIC_BASE_URL in ~/.qwen/.env (or the shell) decides. The request
// format follows the protocol. Its requests name no session the engine knows, so sessions are told apart by their
// first prompt. MCP servers go under "mcpServers" in the same settings file; shell commands run with QWEN_CODE=1.
// Qwen OAuth and Vertex AI are not handled. Not tested live.
// Input: the environment, the settings files. Output: the platform's entry (core/platform.ts).

import { join } from "node:path";
import { envAt, jsonAt } from "../../core/config-edit.ts";
import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

const ENV_NAME: Record<string, string> = { openai: "OPENAI_BASE_URL", anthropic: "ANTHROPIC_BASE_URL" };
const DEFAULTS: Record<string, string> = { openai: "https://api.openai.com/v1", anthropic: "https://api.anthropic.com" };

export const qwenCode: CorePlatform = {
  name: "qwen-code",
  title: "Qwen Code",
  upstream: null,
  detect: (env) => env.QWEN_CODE === "1",
  setup: ({ home, env }) => {
    const dir = join(home, ".qwen");
    const settings = join(dir, "settings.json");
    const type = jsonAt(settings, ["security", "auth", "selectedType"]) ?? (env.OPENAI_API_KEY ? "openai" : undefined);
    if (typeof type !== "string" || !ENV_NAME[type]) throw new Error(`Qwen Code signs in with ${String(type ?? "nothing set yet")}; only an OpenAI-compatible or Anthropic provider can go through the engine (set one up with /auth first)`);
    const models = jsonAt(settings, ["modelProviders", type]);
    const model = jsonAt(settings, ["model", "name"]);
    const at = Array.isArray(models) ? models.findIndex((entry) => entry?.id === model) : -1;
    const mcp = (info: { mcp: { command: string; args: string[]; env: Record<string, string> } }) => ({ file: settings, json: ["mcpServers", MCP_NAME], value: { command: info.mcp.command, args: info.mcp.args, env: info.mcp.env } });
    if (at >= 0) {
      const set = (models as Array<Record<string, unknown>>)[at].baseUrl;
      return {
        current: typeof set === "string" ? set : null,
        fallback: DEFAULTS[type],
        edits: (info) => [{ file: settings, json: ["modelProviders", type, String(at), "baseUrl"], value: info.url }, mcp(info)],
      };
    }
    const envFile = join(dir, ".env");
    const name = ENV_NAME[type];
    return {
      current: envAt(envFile, name) ?? env[name]?.trim() ?? null,
      fallback: DEFAULTS[type],
      edits: (info) => [{ file: envFile, env: name, value: info.url }, mcp(info)],
      note: `A .env in your project folder that sets ${name} too wins over ~/.qwen/.env.`,
    };
  },
  connect: ({ url, mcp }) => [
    `In ~/.qwen/settings.json, set "baseUrl": "${url}" on the model you use under "modelProviders" (or OPENAI_BASE_URL / ANTHROPIC_BASE_URL in ~/.qwen/.env)`,
    `In ~/.qwen/settings.json, add: "mcpServers": { "${MCP_NAME}": { "command": ${JSON.stringify(mcp.command)}, "args": ${JSON.stringify(mcp.args)}, "env": ${JSON.stringify(mcp.env)} } }`,
    "Restart Qwen Code.",
  ],
};
