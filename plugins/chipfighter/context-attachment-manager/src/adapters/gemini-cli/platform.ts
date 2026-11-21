// Purpose: v0.11 — Gemini CLI: the core alone, no panel. Signed in with an API key it sends Gemini generateContent
// requests to GOOGLE_GEMINI_BASE_URL (by default https://generativelanguage.googleapis.com); signed in with Google, the
// same contents wrapped in `request` to CODE_ASSIST_ENDPOINT (by default https://cloudcode-pa.googleapis.com). Which one
// is `security.auth.selectedType` in ~/.gemini/settings.json; Vertex AI is not handled. Gemini CLI loads the first .env
// it finds from the project folder upward, then ~/.gemini/.env. Its requests name no session the engine knows, so
// sessions are told apart by their first prompt. MCP servers go under "mcpServers" in ~/.gemini/settings.json; shell
// commands run with GEMINI_CLI=1. Not tested live.
// Input: the environment, the settings files. Output: the platform's entry (core/platform.ts).

import { join } from "node:path";
import { envAt, jsonAt } from "../../core/config-edit.ts";
import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

export const geminiCli: CorePlatform = {
  name: "gemini-cli",
  title: "Gemini CLI",
  upstream: "https://generativelanguage.googleapis.com",
  detect: (env) => env.GEMINI_CLI === "1",
  setup: ({ home, env }) => {
    const dir = join(home, ".gemini");
    const settings = join(dir, "settings.json");
    const auth = jsonAt(settings, ["security", "auth", "selectedType"]) ?? jsonAt(settings, ["selectedAuthType"]);
    if (auth !== undefined && auth !== "gemini-api-key" && auth !== "oauth-personal") throw new Error(`Gemini CLI signs in with ${String(auth)}; only an API key or a Google sign-in can go through the engine`);
    const google = auth === "oauth-personal";
    const name = google ? "CODE_ASSIST_ENDPOINT" : "GOOGLE_GEMINI_BASE_URL";
    const envFile = join(dir, ".env");
    return {
      current: envAt(envFile, name) ?? env[name]?.trim() ?? null,
      fallback: google ? "https://cloudcode-pa.googleapis.com" : "https://generativelanguage.googleapis.com",
      edits: ({ url, mcp }) => [
        { file: envFile, env: name, value: url },
        { file: settings, json: ["mcpServers", MCP_NAME], value: { command: mcp.command, args: mcp.args, env: mcp.env } },
      ],
      note: `A .env in your project folder that sets ${name} too wins over ~/.gemini/.env.`,
    };
  },
  connect: ({ url, mcp }) => [
    `In ~/.gemini/.env, set GOOGLE_GEMINI_BASE_URL=${url} (signed in with Google instead: CODE_ASSIST_ENDPOINT, with a route made by --base-url https://cloudcode-pa.googleapis.com)`,
    `In ~/.gemini/settings.json, add: "mcpServers": { "${MCP_NAME}": { "command": ${JSON.stringify(mcp.command)}, "args": ${JSON.stringify(mcp.args)}, "env": ${JSON.stringify(mcp.env)} } }`,
    "Restart Gemini CLI.",
  ],
};
