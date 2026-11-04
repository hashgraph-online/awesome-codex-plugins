// Purpose: v0.11 — the pi extension (loaded by pi, not by the engine; docs/v0.11/plan.md 3.8). Two jobs: each model
// request names its pi session in `x-cam-session`, which the engine takes as the session (it never goes further: the
// engine drops x-cam- headers), and the plugin's MCP service is registered, so the model has cam_view_image and the
// engine keeps running while pi does. The model requests reach the engine through the provider's baseUrl in
// ~/.pi/agent/models.json (`cam connect pi`). Written against pi's extension docs (before_provider_headers,
// registerMcpServer); not tested live.
// Input: pi's extension API. Output: a header on each request, one MCP server for the session.

import { fileURLToPath } from "node:url";

type Pi = {
  on(event: "before_provider_headers", handler: (event: { headers: Record<string, string | null> }, ctx: { sessionManager: { getSessionId(): string } }) => void): void;
  registerMcpServer(name: string, config: { command: string; args: string[]; env?: Record<string, string> }): void;
};

export default function contextAttachmentManager(pi: Pi): void {
  pi.on("before_provider_headers", (event, ctx) => {
    const id = ctx.sessionManager.getSessionId();
    if (id) event.headers["x-cam-session"] = id;
  });
  pi.registerMcpServer("context_attachment_manager", {
    command: "node",
    args: [fileURLToPath(new URL("../../plugin-server.ts", import.meta.url))],
    env: { CAM_HOST: "pi" },
  });
}
