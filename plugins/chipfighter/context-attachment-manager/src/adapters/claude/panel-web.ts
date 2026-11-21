// Purpose: v0.4 — the panel of a Claude Code session, served by the engine (v0.11: split from proxy.ts,
// docs/v0.11/plan.md): the page (the Codex panel with panel-web.js standing in for its host) and its local API.
// Input: requests to /__cam/panel and /__cam/claude/*. Output: the page, JSON answers.

import type { IncomingHttpHeaders } from "node:http";
import { ownRequest } from "../../core/engine/transport.ts";
import { webPanelPage } from "../../panel/page.ts";
import { claudePanelLanguage } from "../../panel/panel-language.ts";
import { applyClaudeSelection, claudeImageFor, loadClaudePanelState, type ClaudePanelOptions } from "./panel.ts";

type Json = Record<string, any>;

// v0.4: a Claude Code session's panel reads and changes its images here: the panel page the engine serves
// (/__cam/panel, panel.html with panel-web.js) and the Claude plugin's mod. The Codex panel goes through the plugin's
// MCP server; under Claude Code that is not open to a panel (a mod reaches it only through Claude Code's tool
// permissions, a prompt for every call, and Claude Code registers no app-only tool), so the engine, the one local HTTP
// service, serves the panel. Loopback only, like everything the engine serves; only a request naming the engine by a
// loopback name (no other site rebinding its name to 127.0.0.1), carrying our header, and coming from no other site's
// page (a browser's Origin, when sent, is the engine's own).
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

// The panel page for a Claude Code session: the same panel.html as in Codex, with panel-web.js before its own script.
export const claudePanelPage = () => webPanelPage();
export const PANEL_PAGE_CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";

export function claudePanelApi(method: string, url: string, headers: IncomingHttpHeaders, body: string | null, options: ClaudePanelOptions & { panelLocaleFiles?: readonly string[] } = {}): { status: number; body: Json } {
  if (!ownRequest(headers) || headers["x-cam-panel"] !== "1") return { status: 403, body: { error: "forbidden" } };
  const parsed = new URL(url, "http://localhost");
  const session = parsed.searchParams.get("session") ?? "";
  if (!SESSION_ID.test(session)) return { status: 400, body: { error: "no session" } };
  const lang = claudePanelLanguage({ settingsFiles: options.panelLocaleFiles });
  try {
    if (method === "GET" && parsed.pathname === "/__cam/claude/panel") return { status: 200, body: { ...loadClaudePanelState(session, options), lang } };
    if (method === "GET" && parsed.pathname === "/__cam/claude/image") {
      const max = Number(parsed.searchParams.get("max") ?? 160);
      return { status: 200, body: claudeImageFor(session, String(parsed.searchParams.get("id") ?? ""), Number.isFinite(max) && max > 0 ? max : 160, options) };
    }
    if (method === "POST" && parsed.pathname === "/__cam/claude/select") {
      if (body === null) return { status: 413, body: { error: "too large" } };
      const change = JSON.parse(body || "{}");
      const list = (value: unknown) => (Array.isArray(value) ? value.map(String) : undefined);
      const state = applyClaudeSelection(session, { uncheck: list(change.uncheck), check: list(change.check), checkAll: change.checkAll === true, auto: typeof change.auto === "boolean" ? change.auto : undefined, mode: change.mode === "auto" ? "auto" : "manual" }, options);
      return { status: 200, body: { ...state, lang } };
    }
    return { status: 404, body: { error: "not found" } };
  } catch (error) {
    return { status: 400, body: { error: error instanceof Error ? error.message : String(error) } };
  }
}
