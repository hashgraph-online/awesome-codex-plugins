// Purpose: v0.11 — WorkBuddy (Tencent's desktop agent, CodeBuddy Code inside; docs/v0.11/plan.md 4): the core alone, no
// panel. Its agent sends OpenAI Chat Completions requests to CODEBUDDY_BASE_URL + /chat/completions, which by default
// is WorkBuddy's own service under /v2 (a capture on 2026-11-02: without /v2 the service answers 405). Each request
// names its conversation in `x-conversation-id`; side requests (prompt enhancement and the like) say
// `x-agent-type: auxiliary`. `env` in ~/.workbuddy/settings.json reaches the agent's environment (WORKBUDDY_CONFIG_DIR
// moves the folder); user MCP servers go in ~/.workbuddy/.mcp.json, as in CodeBuddy's docs for ~/.codebuddy. Its shell
// commands run with CODEBUDDY=1, as do the CodeBuddy CLI's; WorkBuddy's own paths tell the two apart. Not tested live.
// Input: request headers, the environment, the settings files. Output: the platform's entry (core/platform.ts).

import { join } from "node:path";
import { jsonAt } from "../../core/config-edit.ts";
import { headerOf, MCP_NAME, type CorePlatform } from "../../core/platform.ts";

const configDir = (home: string, env: NodeJS.ProcessEnv) => env.WORKBUDDY_CONFIG_DIR?.trim() || join(home, ".workbuddy");

export const workbuddy: CorePlatform = {
  name: "workbuddy",
  title: "WorkBuddy",
  upstream: "https://www.workbuddy.cn/v2",
  sessionOf: (headers) => headerOf(headers, "x-conversation-id"),
  sideRequest: (headers) => headerOf(headers, "x-agent-type") === "auxiliary",
  // Any WORKBUDDY_ variable, or a CodeBuddy path inside WorkBuddy's folders.
  detect: (env) => env.CODEBUDDY === "1" && (Object.keys(env).some((name) => name.startsWith("WORKBUDDY_")) || /workbuddy/i.test([env.CODEBUDDY_CONFIG_DIR, env.CODEBUDDY_NODE_BIN, env.ACC_PRODUCT_CONFIG_PATH].join(" "))),
  setup: ({ home, env }) => {
    const dir = configDir(home, env);
    const settings = join(dir, "settings.json");
    const set = jsonAt(settings, ["env", "CODEBUDDY_BASE_URL"]);
    return {
      current: typeof set === "string" ? set : env.CODEBUDDY_BASE_URL?.trim() || null,
      fallback: "https://www.workbuddy.cn/v2",
      edits: ({ url, mcp }) => [
        { file: settings, json: ["env", "CODEBUDDY_BASE_URL"], value: url },
        { file: join(dir, ".mcp.json"), json: ["mcpServers", MCP_NAME], value: { type: "stdio", command: mcp.command, args: mcp.args, env: mcp.env } },
      ],
    };
  },
  connect: ({ url, mcp }) => [
    `In ~/.workbuddy/settings.json, add to "env": "CODEBUDDY_BASE_URL": "${url}"`,
    `In ~/.workbuddy/.mcp.json, add to "mcpServers": "${MCP_NAME}": ${JSON.stringify({ type: "stdio", command: mcp.command, args: mcp.args, env: mcp.env })}`,
    "Restart WorkBuddy.",
  ],
};
