// Purpose: the engine — local proxy between Codex and the ChatGPT backend. P1: HTTP requests and WebSocket upgrades
// are forwarded byte for byte. P2: requests of threads with unchecked images are rewritten. P3: one instance per
// machine, exits once no Codex process is left, and keeps per-thread statistics of the latest request.
// P4: the statistics also name the images each full request carried (the panel's size baseline), and note a
// WebSocket turn that kept running after images were unchecked (it cannot be rewritten).
// v0.1-3: reports its build and version; POST /__cam/retire hands the port to a newer engine (see engine.ts).
// v0.1-11: pixel fingerprints go to the shared cache in the data directory, for the panels to reuse.
// v0.1-14: the text for the model is in the language the panel last reported (Codex's interface language).
// v0.3: automatic selection — a thread with it on leaves out the images of earlier turns that are not pinned, and a
// copy the model fetched is sent in its own turn only (spec v0.3).
// v0.4: Claude Code too. Older clients are recognized by their own headers; ambiguous legacy requests are refused.
// 2026-10-22: Codex logged in with an API key goes to api.openai.com/v1 instead (see routeOf).
// v0.9: registered providers bind the client protocol and original endpoint, with a separate listener for new routes.
// Only metadata is logged (never auth headers or conversation content).
// Input: [--port 17891] [--stay (no auto-exit)] [--force-http] [--dump-requests (synthetic test threads only)];
// the outbound proxy is taken from HTTPS_PROXY/HTTP_PROXY or the system proxy settings (Windows, macOS).
// Output: responses streamed back to Codex; <data dir>/proxy/<date>.jsonl; <data dir>/state/requests/<thread>.json.

// v0.11: this file is the engine's entry (docs/v0.11/plan.md): the server, routing and the order of a request's steps.
// The way to the services is core/engine/transport.ts; what is particular to Codex and to Claude Code is in
// adapters/codex/engine.ts, adapters/claude/engine.ts and adapters/claude/panel-web.ts.

import http, { type IncomingHttpHeaders } from "node:http";
import type net from "node:net";
import { mkdirSync, watch, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { Duplex } from "node:stream";
import { setTimeout as sleep } from "node:timers/promises";
import { childOf, recordChild } from "./adapters/codex/children.ts";
import { claudeHome, loadClaudeIndex } from "./adapters/claude/claude-index.ts";
import { CLAUDE_HOST, claudeConversationRequest, claudeIdentity, claudeImageSizes, claudeNeedsRewrite, LATE_STEP_MS, LATE_WAIT_MS, rewriteClaudeBody, thinkingRejected, type ClaudeAttempt } from "./adapters/claude/engine.ts";
import { claudePanelApi, claudePanelPage, PANEL_PAGE_CSP } from "./adapters/claude/panel-web.ts";
import { codexHome } from "./adapters/codex/codexconfig.ts";
import { CODEX_BASE, imageSizesOf, needsRewrite, OPENAI_API_HOST, requestIdentity, rewriteBody, UPSTREAM_HOST, type RequestIdentity } from "./adapters/codex/engine.ts";
import { connectDirectly, keepRouted, pluginGone, usesEngine } from "./adapters/codex/setup.ts";
import { setPixelCache } from "./core/pixels.ts";
import { REMEMBERED, type SentPrefix } from "./adapters/protocols/anthropic-messages/cache.ts";
import { readThinkingRecord, recordSent, writeThinkingRecord, type ThinkingRecord } from "./adapters/protocols/anthropic-messages/thinking.ts";
import { connectUpstream, decodeBody, HOP_BY_HOP, log, outboundProxy, ownRequest, readSystemProxy, redactImages } from "./core/engine/transport.ts";
import { isEntryPoint } from "./core/entry.ts";
import { migrateDataOnce } from "./core/migrate-data.ts";
import { claudeRequestStatsDirOf, claudeSelectionDirOf, dataDir, pixelCacheDirOf, selectionDirOf } from "./core/paths.ts";
import { recordRequest } from "./core/request-stats.ts";
import { readRoute, registerRoute, routeBaseUrl, routingPort, validateBaseUrl, type Platform } from "./core/routes.ts";
import { buildOf, DEFAULT_PORT, ENGINE_SERVICE, engineHealth, versionOf, watchForClients } from "./engine.ts";
import { currentLang } from "./adapters/codex/language.ts";
import { say } from "./core/messages.ts";
import { headerOf } from "./core/platform.ts";
import { formatOf, rewritePlatformRequest } from "./adapters/protocols/any.ts";
import { corePlatformOf, isPlatform } from "./platforms.ts";
import { ensureAutoDefault, ensureStableIds, selectionDir, stableIdsSince } from "./core/selection.ts";

type Json = Record<string, any>;

// Codex logged in with an API key keeps the base URL the plugin set and sends its key (Bearer sk-…, no
// chatgpt-account-id), which chatgpt.com does not take: those requests go to api.openai.com, /backend-api/codex/
// becoming /v1/ (2026-10-22, seen with a fake key against a local server). The request bodies are the same Responses
// requests, so they are rewritten as before.
export type ForwardRoute = { host: string; url: string; platform?: Platform; protocol?: string; port?: number; clientPath?: string };
export function routeOf(url: string, headers: IncomingHttpHeaders, root = dataDir()): ForwardRoute | null {
  const claude = !!(headers["x-claude-code-session-id"] || headers["anthropic-version"] || headers["anthropic-beta"] || /^Bearer sk-ant-/i.test(String(headers.authorization ?? "")));
  const codex = !!(headers["chatgpt-account-id"] || headers["x-codex-turn-metadata"] || headers["x-codex-window-id"]);
  if (!url.startsWith("/") || /[\r\n\\]/.test(url)) return null;
  if (url.startsWith("/__cam/routes/")) {
    const match = /^\/__cam\/routes\/([a-f0-9]{32})(\/[^]*|\?[^]*|$)/.exec(url);
    const registered = match ? readRoute(match[1], root) : null;
    if (!registered || (registered.platform === "codex" && !!headers["x-claude-code-session-id"]) || (registered.platform === "claude" && codex)) return null;
    const target = validateBaseUrl(registered.baseUrl);
    const suffix = match![2] || "/";
    const at = suffix.indexOf("?");
    const clientPath = at < 0 ? suffix : suffix.slice(0, at) || "/";
    const query = [target.search.slice(1), at < 0 ? "" : suffix.slice(at + 1)].filter(Boolean).join("&");
    const path = `${target.pathname.replace(/\/$/, "")}/${clientPath.replace(/^\//, "")}`;
    return { host: target.hostname.replace(/^\[|\]$/g, ""), url: path + (query ? `?${query}` : ""), platform: registered.platform, protocol: target.protocol, port: Number(target.port || (target.protocol === "https:" ? 443 : 80)), clientPath };
  }
  if ((claude || headers["x-api-key"]) && codex) return null;
  if (claude || headers["x-api-key"]) {
    if (url.startsWith("/backend-api/")) return null;
    return { host: CLAUDE_HOST, url };
  }
  if (url.startsWith("/v1/")) return null;
  if (!url.startsWith("/backend-api/")) return null;
  const apiKey = /^Bearer sk-/i.test(String(headers.authorization ?? "")) && !headers["chatgpt-account-id"];
  if (apiKey && url.startsWith(CODEX_BASE)) return { host: OPENAI_API_HOST, url: `/v1/${url.slice(CODEX_BASE.length)}` };
  return { host: UPSTREAM_HOST, url };
}

// v0.11: a platform other than Codex and Claude Code keeps every header but the engine's own (x-cam-).
export function forwardHeaders(headers: IncomingHttpHeaders, upstream = UPSTREAM_HOST, platform?: Platform): Record<string, string | string[]> {
  const out: Record<string, string | string[]> = {};
  const client = platform ?? (upstream === CLAUDE_HOST ? "claude" : "codex");
  const removed = new Set(client === "claude" ? ["chatgpt-account-id"] : client === "codex" ? ["anthropic-beta", "anthropic-version", "x-claude-code-session-id", "x-claude-code-agent-id", ...(!platform ? ["x-api-key"] : [])] : []);
  for (const [name, value] of Object.entries(headers)) if (value !== undefined && !HOP_BY_HOP.has(name) && !removed.has(name) && !name.startsWith("x-cam-")) out[name] = value;
  out.host = upstream;
  return out;
}

// Metadata only: counts and sizes, never text or image content.
export function describeBody(path: string, json: Json): Json {
  if (/\/responses$/.test(path)) {
    const input: Json[] = Array.isArray(json.input) ? json.input : [];
    let images = 0;
    let imageBytes = 0;
    const visit = (value: unknown) => {
      if (Array.isArray(value)) return value.forEach(visit);
      if (!value || typeof value !== "object") return;
      const part = value as Json;
      if (part.type === "input_image" && typeof part.image_url === "string") { images++; imageBytes += part.image_url.length; }
      for (const child of Object.values(part)) if (typeof child === "object") visit(child);
    };
    visit(input);
    return { kind: "responses", model: json.model ?? null, inputItems: input.length, images, imageBytes, stream: json.stream ?? null, promptCacheKey: json.prompt_cache_key ?? null };
  }
  if (/\/images\/(generations|edits)$/.test(path)) {
    const inputs = Array.isArray(json.images) ? json.images : json.image ? [json.image] : [];
    return { kind: path.endsWith("edits") ? "image_edit" : "image_generation", model: json.model ?? null, inputImages: inputs.length, size: json.size ?? null };
  }
  // v0.4: Anthropic Messages, with images in user messages and inside tool results.
  if (path === "/v1/messages") {
    const messages: Json[] = Array.isArray(json.messages) ? json.messages : [];
    let images = 0;
    let imageBytes = 0;
    let thinkingBlocks = 0;
    const visit = (blocks: unknown) => {
      if (!Array.isArray(blocks)) return;
      for (const block of blocks as Json[]) {
        if (block?.type === "image" && typeof block.source?.data === "string") { images++; imageBytes += block.source.data.length; }
        if (block?.type === "thinking" || block?.type === "redacted_thinking") thinkingBlocks++;
        if (block?.type === "tool_result") visit(block.content);
      }
    };
    for (const message of messages) visit(message?.content);
    return { kind: "messages", model: json.model ?? null, messages: messages.length, images, imageBytes, thinkingBlocks, thinking: json.thinking?.type ?? null, stream: json.stream ?? null, tools: Array.isArray(json.tools) ? json.tools.length : 0 };
  }
  return { kind: "other" };
}

async function main(): Promise<void> {
  migrateDataOnce(); // v0.1-15: Windows moved the data folder
  // v0.6: tasks and sessions started from now on have automatic selection on by default (selection.ts).
  ensureAutoDefault(selectionDirOf());
  ensureAutoDefault(claudeSelectionDirOf());
  // v0.10: from now on Claude sessions resumed after a compaction keep their ids (claude-index.ts).
  ensureStableIds(claudeSelectionDirOf());
  const portIndex = process.argv.indexOf("--port");
  const port = Number(portIndex >= 0 ? process.argv[portIndex + 1] : DEFAULT_PORT);
  const providerPort = routingPort(port);
  // One engine per machine: a second start leaves the running one alone.
  const running = await engineHealth(port);
  if (running) {
    console.log(JSON.stringify({ alreadyRunning: true, pid: running.pid, port }));
    return;
  }
  // --force-http answers every Responses WebSocket upgrade with 426, Codex's own signal to use HTTP for the session.
  const forceHttp = process.argv.includes("--force-http");
  const dumpDir = process.argv.includes("--dump-requests") ? join(dataDir(), "p2", "requests") : null;
  const sessionsDir = join(codexHome(), "sessions");
  setPixelCache(pixelCacheDirOf());
  const via = outboundProxy(process.env, readSystemProxy, UPSTREAM_HOST);
  // v0.4: NO_PROXY may name one upstream host and not the other.
  const vias = new Map([CLAUDE_HOST, OPENAI_API_HOST].map((host) => [host, outboundProxy(process.env, readSystemProxy, host)]));
  const viaOf = (upstream: string) => {
    if (!vias.has(upstream)) vias.set(upstream, outboundProxy(process.env, readSystemProxy, upstream));
    return vias.get(upstream)!;
  };
  const startedAt = new Date().toISOString();
  // v0.11: when a plugin service last checked in (engine.ts, watchForClients); a platform other than Codex and Claude
  // Code keeps the engine this way.
  let lastClient = 0;
  // v0.1-3: which code this engine runs, so the plugin can tell when an update needs a new engine.
  const build = buildOf();
  const version = versionOf();
  let sequence = 0;
  // v0.7: a subagent's or side chat's request, noted under its task for the task's panel (children.ts).
  const noteChild = (identity: RequestIdentity, at: string) => {
    try {
      const found = childOf(identity, sessionsDir, at);
      if (found) recordChild(found.task, found.id, found.child);
    } catch { /* only the panel's list misses it */ }
  };
  // v0.4: per Claude Code session, whether its account refuses thinking after a changed history and what was sent
  // (anthropic-messages/thinking.ts); the latest sessions stay in memory.
  const thinkingRecords = new Map<string, ThinkingRecord>();
  const thinkingOf = (sessionId: string): ThinkingRecord => {
    const record = thinkingRecords.get(sessionId) ?? readThinkingRecord(sessionId);
    thinkingRecords.delete(sessionId);
    thinkingRecords.set(sessionId, record);
    for (const key of thinkingRecords.keys()) if (thinkingRecords.size > 50) thinkingRecords.delete(key);
    return record;
  };
  // v0.10: per session, where the conversation requests sent last had their cache marks, newest first
  // (anthropic-messages/cache.ts); memory only.
  const sentPrefixes = new Map<string, SentPrefix[]>();
  const rememberPrefix = (sessionId: string, prefix: SentPrefix) => {
    const kept = [prefix, ...(sentPrefixes.get(sessionId) ?? [])].slice(0, REMEMBERED);
    sentPrefixes.delete(sessionId);
    sentPrefixes.set(sessionId, kept);
    for (const key of sentPrefixes.keys()) if (sentPrefixes.size > 50) sentPrefixes.delete(key);
  };
  log({ at: startedAt, event: "engine-start", pid: process.pid, port, build, version });
  if (!process.argv.includes("--stay")) {
    // v0.1-5: a plugin removed or turned off without 停用 leaves Codex pointed at an engine nothing will start again.
    // Seen in two checks in a row (or once more as the engine exits, when Codex is gone and cannot be mid-write), Codex
    // goes back to connecting directly from its next start; until then this engine keeps serving. On Windows the engine
    // usually ends together with the plugin's MCP server, so there the panel's 停用 or the uninstall command does it.
    let gone = 0;
    const checkPlugin = (final: boolean) => {
      try {
        const state = pluginGone();
        gone = state ? gone + 1 : 0;
        if (!state || (!final && gone < 2) || !usesEngine()) return;
        connectDirectly();
        log({ at: new Date().toISOString(), event: "connect-directly", pid: process.pid, reason: `plugin ${state}` });
      } catch (error) {
        log({ at: new Date().toISOString(), event: "plugin-check-failed", pid: process.pid, error: String(error) });
      }
    };
    // v0.11: a provider switcher (cc-switch) wrote its provider over the engine's address: Codex is pointed at the engine
    // again, with a route to the provider the user picked (adapters/codex/setup.ts, keepRouted). Checked as soon as
    // config.toml changes, at start, and with the plugin check.
    const rerouted: number[] = [];
    let lastRerouteError = "";
    const reroute = (why: string) => {
      const result = keepRouted(port, rerouted);
      if (result.rerouted) log({ at: new Date().toISOString(), event: "codex-reroute", pid: process.pid, why });
      if (result.error && result.error !== lastRerouteError) log({ at: new Date().toISOString(), event: "codex-reroute-failed", pid: process.pid, why, error: result.error });
      lastRerouteError = result.error ?? "";
    };
    reroute("start");
    let settling: NodeJS.Timeout | null = null;
    try {
      watch(codexHome(), (_event, name) => {
        if (name !== "config.toml") return;
        if (settling) clearTimeout(settling);
        settling = setTimeout(() => { settling = null; reroute("config changed"); }, 1000);
      }).unref();
    } catch { /* no folder to watch yet: the periodic check still runs */ }
    setInterval(() => { checkPlugin(false); reroute("check"); }, 15_000).unref();
    watchForClients(() => {
      checkPlugin(true);
      log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: "no Codex or Claude Code process left, and no plugin service checked in" });
      process.exit(0);
    }, { lastClient: () => lastClient });
  }
  // Open WebSocket connections per thread. Over WebSocket Codex only sends new items and the server keeps the rest,
  // so a thread with unchecked images must move to HTTP: its idle connections are closed, and its next upgrade gets 426.
  type Live = { client: Duplex; socket: net.Socket; last: number; closedForSelection: boolean; activeWhileUnchecked: boolean; path: string; identity: Json };
  const live = new Map<string, Set<Live>>();
  // v0.1-3: a newer plugin's engine takes over. This one stops listening at once, lets idle connections go (Codex
  // reconnects to the new engine), keeps serving requests and WebSocket turns already under way, then exits.
  const servers: http.Server[] = [];
  const sockets = new Set<Live>();
  let inFlight = 0;
  let retiredAt: number | null = null;
  const retire = (by: string) => {
    if (retiredAt !== null) return;
    retiredAt = Date.now();
    log({ at: new Date().toISOString(), event: "engine-retire", pid: process.pid, build, by: by || null });
    for (const server of servers) { server.close(); server.closeIdleConnections(); }
    setInterval(() => {
      for (const connection of sockets) {
        if (Date.now() - connection.last < 1500) continue;
        connection.socket.destroy();
        connection.client.destroy();
      }
      for (const server of servers) server.closeIdleConnections();
      const done = inFlight === 0 && sockets.size === 0;
      if (!done && Date.now() - retiredAt! < 10 * 60_000) return;
      log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: done ? "replaced by a newer engine" : "replaced by a newer engine; connections still open after 10 minutes were dropped" });
      process.exit(0);
    }, 250);
  };
  setInterval(() => {
    for (const [threadId, connections] of live) {
      const forkedFrom = [...connections][0]?.identity.forkedFrom ?? null;
      if (!needsRewrite(threadId, selectionDir, sessionsDir, forkedFrom)) continue;
      for (const connection of connections) {
        if (Date.now() - connection.last < 1500) {
          // A turn still running here keeps the images the server already holds; noted once so the panel can say so.
          if (!connection.activeWhileUnchecked) {
            connection.activeWhileUnchecked = true;
            recordRequest(threadId, { at: new Date().toISOString(), transport: "websocket", event: "active-while-unchecked", path: connection.path, ...connection.identity });
          }
          continue;
        }
        connection.closedForSelection = true;
        connection.socket.destroy();
        connection.client.destroy();
      }
    }
  }, 500).unref();

  const onRequest = (req: http.IncomingMessage, res: http.ServerResponse) => {
    if (req.url === "/__cam/health") {
      if (req.headers["x-cam-client"]) lastClient = Date.now();
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ ok: true, service: ENGINE_SERVICE, pid: process.pid, startedAt, port, build, version, routingVersion: 1, routingPort: providerPort, upstream: UPSTREAM_HOST, upstreams: [UPSTREAM_HOST, CLAUDE_HOST, OPENAI_API_HOST], via: via ? `${via.host}:${via.port}` : "direct" }));
      return;
    }
    if (req.url === "/__cam/routes") {
      if (req.method !== "POST" || !ownRequest(req.headers) || req.headers.origin !== undefined || req.headers["x-cam-panel"] !== "1") {
        req.resume(); res.writeHead(403, { "content-type": "application/json" }); res.end(JSON.stringify({ error: "forbidden" })); return;
      }
      const chunks: Buffer[] = [];
      let size = 0;
      req.on("data", (chunk: Buffer) => { size += chunk.length; if (size <= 8192) chunks.push(chunk); });
      req.on("end", () => {
        try {
          if (size > 8192) { res.writeHead(413); res.end(); return; }
          const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
          if (!isPlatform(input.platform)) throw new Error("unknown platform");
          validateBaseUrl(input.baseUrl, port);
          const route = registerRoute(input);
          res.writeHead(200, { "content-type": "application/json", "cache-control": "no-store" });
          res.end(JSON.stringify({ id: route.id, baseUrl: routeBaseUrl(port, route.id).replace("localhost", "127.0.0.1") }));
        } catch { res.writeHead(400, { "content-type": "application/json" }); res.end(JSON.stringify({ error: say(currentLang(), "proxy.invalidRoute") })); }
      });
      return;
    }
    if (req.url === "/__cam/retire" && req.method === "POST") {
      res.writeHead(200, { "content-type": "application/json", connection: "close" });
      res.end(JSON.stringify({ retiring: true, pid: process.pid }));
      retire(String(req.headers["x-cam-build"] ?? ""));
      return;
    }
    // v0.4: a Claude Code session's panel: the page (panel.html as in Codex, with panel-web.js), and its API.
    if (req.method === "GET" && (req.url ?? "").split("?")[0] === "/__cam/panel") {
      if (!ownRequest(req.headers)) { res.writeHead(403, { "content-type": "text/plain" }); res.end("forbidden"); return; }
      let page: string;
      try {
        page = claudePanelPage();
      } catch (error) {
        res.writeHead(500, { "content-type": "text/plain" });
        res.end(String(error));
        return;
      }
      res.writeHead(200, { "content-type": "text/html; charset=utf-8", "cache-control": "no-store", "content-security-policy": PANEL_PAGE_CSP, "x-content-type-options": "nosniff", "referrer-policy": "no-referrer" });
      res.end(page);
      return;
    }
    if ((req.url ?? "").startsWith("/__cam/claude/")) {
      const chunks: Buffer[] = [];
      let size = 0;
      req.on("data", (chunk: Buffer) => { size += chunk.length; if (size <= 64 * 1024) chunks.push(chunk); });
      req.on("end", () => {
        const answer = claudePanelApi(req.method ?? "GET", req.url ?? "/", req.headers, size <= 64 * 1024 ? Buffer.concat(chunks).toString("utf8") : null);
        res.writeHead(answer.status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
        res.end(JSON.stringify(answer.body));
      });
      return;
    }
    inFlight++;
    res.on("close", () => { inFlight--; });
    // Once retired, no connection stays open for a next request.
    if (retiredAt !== null) res.shouldKeepAlive = false;
    const id = ++sequence;
    const started = Date.now();
    const route = routeOf(req.url ?? "/", req.headers);
    if (!route) {
      req.resume(); res.writeHead(421, { "content-type": "text/plain; charset=utf-8" }); res.end(say(currentLang(), "proxy.unknownRoute"));
      log({ at: new Date(started).toISOString(), id, transport: "http", status: 421, reason: "unrecognized or conflicting provider route" });
      return;
    }
    const path = route.clientPath ?? (req.url ?? "/").split("?")[0];
    const upstream = route.host;
    const platform = route.platform ?? (upstream === CLAUDE_HOST ? "claude" : "codex");
    const identity = requestIdentity(req.headers);
    const rewrite = platform === "codex" && req.method === "POST" && /\/responses(\/compact)?$/.test(path) && needsRewrite(identity.threadId, selectionDir, sessionsDir, identity.forkedFrom);
    // v0.4: a Claude Code request of a session's main conversation (a subagent's loop has its own); rewritten like a
    // Codex thread's once something is unchecked there.
    const claude = platform === "claude" ? claudeIdentity(req.headers) : null;
    const claudeSession = claude?.sessionId && !claude.agentId && req.method === "POST" && path === "/v1/messages" ? claude.sessionId : null;
    // Once the engine has sent the session a changed history, every request of it is looked at, even with nothing left
    // out now: thinking made after a changed history no longer fits the history as it was.
    const thinking = claudeSession ? thinkingOf(claudeSession) : null;
    const claudeRewrite = claudeNeedsRewrite(claudeSession) || !!thinking?.edited;
    const claudeFields = claude ? { claudeSessionId: claude.sessionId, claudeAgentId: claude.agentId } : {};
    // v0.11: a platform using the core alone (platforms.ts): every model request but its side requests, automatic
    // selection always on (adapters/protocols/any.ts).
    const core = corePlatformOf(route.platform);
    const coreRewrite = !!core && req.method === "POST" && formatOf(path) !== null && !core.sideRequest?.(req.headers);
    const coreSession = core ? core.sessionOf?.(req.headers) ?? headerOf(req.headers, "x-cam-session") : null;
    const coreFields = core ? { platform: core.name } : {};
    const chunks: Buffer[] = [];
    let requestBytes = 0;
    let responseBytes = 0;
    let status = 0;
    let finished = false;
    let extra: Json = {};
    // Synthetic test threads only (--dump-requests): the body as the engine sent it, after a rewrite.
    let sentBody: Buffer | null = null;
    const dumpName = (suffix: string) => join(dumpDir!, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}${suffix}`);
    const collect = () => req.on("data", (chunk: Buffer) => { chunks.push(chunk); requestBytes += chunk.length; });
    const finish = (error?: string) => {
      if (finished) return;
      finished = true;
      const body = Buffer.concat(chunks);
      const decoded = req.method === "POST" ? decodeBody(body, req.headers["content-encoding"] as string | undefined) : null;
      let details: Json = {};
      let imageSizes: Record<string, number> | null = null;
      if (decoded) {
        try {
          const json = JSON.parse(decoded.toString("utf8"));
          details = describeBody(path, json);
          // Measured on the body as Codex sent it, before any rewrite: the panel's "everything sent" baseline.
          if (/\/responses$/.test(path) && Array.isArray(json.input)) imageSizes = imageSizesOf(json.input);
          if (claudeSession && Array.isArray(json.messages)) imageSizes = claudeImageSizes(json.messages, loadClaudeIndex(claudeSession, claudeHome(), stableIdsSince(claudeSelectionDirOf())));
          if (dumpDir && (/\/responses$/.test(path) || path === "/v1/messages")) {
            mkdirSync(dumpDir, { recursive: true });
            const headers = Object.fromEntries(Object.entries(req.headers).filter(([name]) => /^(x-codex|session_id|conversation_id|openai-beta|content-|anthropic-(beta|version)|x-claude-code-|user-agent)/.test(name)));
            writeFileSync(join(dumpDir, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}.json`), JSON.stringify({ path, headers, body: redactImages(json) }, null, 2));
            if (sentBody) { const sent = decodeBody(sentBody, req.headers["content-encoding"] as string | undefined); if (sent) writeFileSync(join(dumpDir, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}.sent.json`), JSON.stringify({ path, body: redactImages(JSON.parse(sent.toString("utf8"))) }, null, 2)); }
          }
        } catch { details = { kind: "unparsed" }; }
      }
      const entry = { at: new Date(started).toISOString(), id, transport: "http", method: req.method, path, ...(upstream === OPENAI_API_HOST ? { upstream } : {}), status, requestBytes, decodedBytes: decoded?.length ?? null, contentEncoding: req.headers["content-encoding"] ?? null, responseBytes, ms: Date.now() - started, ...identity, ...claudeFields, ...coreFields, ...details, ...extra, error: error ?? null };
      log(entry);
      // Image keys go to the per-thread statistics only, not to the log.
      if (/\/responses$/.test(path)) {
        recordRequest(identity.threadId, imageSizes ? { ...entry, imageSizes } : entry);
        noteChild(identity, entry.at);
      }
      if (claudeSession && claudeConversationRequest(details)) recordRequest(claudeSession, imageSizes ? { ...entry, imageSizes } : entry, claudeRequestStatsDirOf());
    };
    // What to send, in order: body null streams the request through unchanged. v0.4: Anthropic refusing an attempt's
    // thinking after the changed history (thinkingRejected) moves on to the next one (see ClaudeAttempt), the last being
    // the original as Claude Code built it; the statistics say which went out (the panel shows a fallback).
    type Attempt = { body: Buffer | null; report: Json | null; edited: boolean } & Partial<Pick<ClaudeAttempt, "history" | "sent" | "made" | "sure" | "prefix">>;
    const connecting = new AbortController();
    res.once("close", () => {
      if (!res.writableFinished) { connecting.abort(); finish("client closed before the response ended"); }
    });
    const send = (attempts: Attempt[], at = 0): void => {
      if (res.destroyed) return;
      connectUpstream(viaOf(upstream), upstream, connecting.signal, route.port, route.protocol !== "http:").then((socket) => {
      // The client can cancel while CONNECT/TLS is still in progress.
      if (res.destroyed) { socket.destroy(); return; }
      const attempt = attempts[at];
      const outgoing = forwardHeaders(req.headers, upstream, route.platform);
      const hostname = upstream.includes(":") ? `[${upstream}]` : upstream;
      outgoing.host = route.port && route.port !== (route.protocol === "http:" ? 80 : 443) ? `${hostname}:${route.port}` : hostname;
      if (attempt.body) outgoing["content-length"] = String(attempt.body.length);
      const beta = attempt.report?.experiment?.beta;
      if (beta) outgoing["anthropic-beta"] = [String(outgoing["anthropic-beta"] ?? ""), beta].filter(Boolean).join(",");
      if (attempt.report) extra = { ...extra, rewrite: attempt.report };
      if (dumpDir) sentBody = attempt.edited ? attempt.body : null;
      // No `agent` option: with agent:false Node ignores createConnection and dials the host directly.
      const outbound = http.request({ host: upstream, method: req.method, path: route.url, headers: outgoing, createConnection: () => socket }, (answer) => {
        status = answer.statusCode ?? 0;
        const headers: Record<string, string | string[]> = {};
        for (const [name, value] of Object.entries(answer.headers)) if (value !== undefined && !HOP_BY_HOP.has(name)) headers[name] = value;
        if (at < attempts.length - 1 && status === 400) {
          const parts: Buffer[] = [];
          answer.on("data", (chunk: Buffer) => parts.push(chunk));
          answer.on("error", (error) => { finish(String(error)); res.destroy(error); });
          answer.on("end", () => {
            const raw = Buffer.concat(parts);
            const text = decodeBody(raw, answer.headers["content-encoding"] as string | undefined)?.toString("utf8") ?? "";
            if (thinkingRejected(status, text)) {
              extra = { ...extra, rejected: [...(extra.rejected ?? []), status] };
              if (dumpDir) { try { writeFileSync(dumpName(`.rejected-${at}.json`), text); } catch { /* experiments only */ } }
              // The account checks thinking: from now on the session's rewrites leave out what no longer fits. Refused
              // although the record said it all fits, the record misses what went out (a lost file, old entries): only
              // what goes out from now on counts.
              if (thinking && claudeSession && attempt.history) {
                thinking.strict = true;
                if (attempt.sure) thinking.sent.clear();
                try { writeThinkingRecord(claudeSession, thinking); } catch { /* kept in memory */ }
              }
              socket.destroy();
              send(attempts, at + 1);
              return;
            }
            res.writeHead(status, headers);
            responseBytes += raw.length;
            res.end(raw);
            finish();
          });
          return;
        }
        // The thinking the model makes now comes after what this attempt sent.
        if (status >= 200 && status < 300 && claudeSession && attempt.prefix) rememberPrefix(claudeSession, attempt.prefix);
        if (status >= 200 && status < 300 && thinking && claudeSession && attempt.history && attempt.sent && recordSent(thinking, attempt.history, attempt.sent, attempt.made ?? [])) {
          try { writeThinkingRecord(claudeSession, thinking); } catch { /* kept in memory */ }
        }
        res.writeHead(status, headers);
        // Experiments only (--dump-requests): the response too, for its usage and what Anthropic changed.
        const captured: Buffer[] = [];
        answer.on("data", (chunk: Buffer) => { responseBytes += chunk.length; if (dumpDir && claudeSession && responseBytes <= 8 * 1024 * 1024) captured.push(chunk); });
        answer.pipe(res);
        answer.on("end", () => {
          if (captured.length) {
            const raw = Buffer.concat(captured);
            try { writeFileSync(dumpName(".response.txt"), decodeBody(raw, answer.headers["content-encoding"] as string | undefined) ?? raw); } catch { /* experiments only */ }
          }
          finish();
        });
        // A partial response cannot be ended as if it were complete: propagate the broken stream to Codex.
        answer.on("error", (error) => { finish(String(error)); res.destroy(error); });
      });
      outbound.on("error", (error) => { if (!res.destroyed) { if (!res.headersSent) res.writeHead(502); res.end(); } finish(String(error)); });
      // Log once, and release the upstream stream when the client no longer consumes it.
      res.on("close", () => {
        if (!res.writableFinished) outbound.destroy();
        finish(res.writableFinished ? undefined : "client closed before the response ended");
      });
      if (attempt.body) outbound.end(attempt.body);
      else { collect(); req.pipe(outbound); }
    }, (error) => {
      if (!res.destroyed) {
        res.writeHead(502, { "content-type": "text/plain" });
        res.end(`codex-attachment-manager proxy: cannot reach ${upstream}`);
      }
      finish(String(error));
    }); };
    if (!rewrite && !claudeRewrite && !coreRewrite) { send([{ body: null, report: null, edited: false }]); return; }
    collect();
    req.on("end", async () => {
      const original = Buffer.concat(chunks);
      const encoding = req.headers["content-encoding"] as string | undefined;
      const rewriteNow = (): { body: Buffer; report: Json; attempts?: ClaudeAttempt[]; prefix?: SentPrefix } => {
        try { return coreRewrite ? rewritePlatformRequest(core!.name, path, original, encoding, coreSession, dataDir(), currentLang()) : claudeRewrite ?rewriteClaudeBody(original, encoding, claudeSession!, undefined, undefined, undefined, thinking, sentPrefixes.get(claudeSession!) ?? [], currentLang()) : rewriteBody(original, encoding, identity.threadId!, sessionsDir, selectionDir, identity.turnId, identity.forkedFrom); }
        catch (error) { return { body: original, report: { skipped: `rewrite failed: ${String(error)}` } }; }
      };
      let out = rewriteNow();
      // v0.10: the newest images not in the transcript yet (core/plan.ts, late): read it again for a moment, so
      // they go out with their ids now and the model can note them in this reply.
      let waited = 0;
      for (; claudeRewrite && out.report?.late && waited < LATE_WAIT_MS; waited += LATE_STEP_MS) { await sleep(LATE_STEP_MS); out = rewriteNow(); }
      const withWait = (report: Json) => (waited ? { ...report, waitedMs: waited } : report);
      const attempts: Attempt[] = out.attempts?.length ? out.attempts.map((attempt) => ({ ...attempt, report: withWait(attempt.report), edited: attempt.body !== original })) : [{ body: out.body, report: withWait(out.report), edited: out.body !== original, prefix: out.prefix }];
      send(attempts);
    });
  };

  const onUpgrade = (req: http.IncomingMessage, client: Duplex, head: Buffer) => {
    const id = ++sequence;
    const started = Date.now();
    const route = routeOf(req.url ?? "/", req.headers);
    const path = route?.clientPath ?? (req.url ?? "/").split("?")[0];
    const identity = requestIdentity(req.headers);
    // Node takes its own 'error' listener off an upgraded socket. Without one, a client resetting the connection (Codex
    // can, right after a 426) throws and stops the engine (2026-10-19: four probe engines at once).
    client.on("error", () => {});
    if (!route) {
      client.end("HTTP/1.1 421 Misdirected Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
      log({ at: new Date(started).toISOString(), id, transport: "websocket", declined: 421, reason: "unrecognized or conflicting provider route" });
      return;
    }
    // A retired engine takes no new WebSocket; Codex opens it again, on the new engine.
    if (retiredAt !== null) {
      client.end("HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
      return;
    }
    if (/\/responses$/.test(path) && (forceHttp || needsRewrite(identity.threadId, selectionDir, sessionsDir, identity.forkedFrom))) {
      client.end("HTTP/1.1 426 Upgrade Required\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
      log({ at: new Date(started).toISOString(), id, transport: "websocket", path, declined: 426, reason: forceHttp ? "--force-http" : "thread needs its requests rewritten", ...identity });
      return;
    }
    let up = head.length;
    let down = 0;
    let upstreamStatus: string | null = null;
    connectUpstream(viaOf(route.host), route.host, undefined, route.port, route.protocol !== "http:").then((socket) => {
      // The client went away while the upstream connected: its close has passed, nothing would close this one.
      if (client.destroyed) { socket.destroy(); return; }
      const connection: Live = { client, socket, last: Date.now(), closedForSelection: false, activeWhileUnchecked: false, path, identity };
      sockets.add(connection);
      if (identity.threadId) {
        if (!live.has(identity.threadId)) live.set(identity.threadId, new Set());
        live.get(identity.threadId)!.add(connection);
      }
      // Logged at open as well: a connection that dies with the engine would otherwise leave no trace.
      const opened = { at: new Date(started).toISOString(), id, transport: "websocket", event: "open", path, ...identity };
      log(opened);
      recordRequest(identity.threadId, opened);
      noteChild(identity, opened.at);
      const lines = [`${req.method} ${route.url} HTTP/1.1`];
      const outgoing = forwardHeaders(req.headers, route.host, route.platform);
      const hostname = route.host.includes(":") ? `[${route.host}]` : route.host;
      outgoing.host = route.port && route.port !== (route.protocol === "http:" ? 80 : 443) ? `${hostname}:${route.port}` : hostname;
      outgoing.connection = "Upgrade";
      outgoing.upgrade = String(req.headers.upgrade ?? "websocket");
      for (const [name, value] of Object.entries(outgoing)) for (const entry of Array.isArray(value) ? value : [value]) lines.push(`${name}: ${entry}`);
      socket.write(`${lines.join("\r\n")}\r\n\r\n`);
      if (head.length) socket.write(head);
      socket.once("data", (chunk: Buffer) => { upstreamStatus = chunk.toString("latin1", 0, Math.min(chunk.length, 40)).split("\r\n")[0]; });
      socket.on("data", (chunk: Buffer) => { down += chunk.length; connection.last = Date.now(); });
      client.on("data", (chunk: Buffer) => { up += chunk.length; connection.last = Date.now(); });
      socket.pipe(client);
      client.pipe(socket);
      let logged = false;
      const close = () => {
        if (logged) return;
        logged = true;
        socket.destroy();
        client.destroy();
        sockets.delete(connection);
        if (identity.threadId) live.get(identity.threadId)?.delete(connection);
        const entry = { at: new Date(started).toISOString(), id, transport: "websocket", path, ...(route.host === OPENAI_API_HOST ? { upstream: route.host } : {}), upstreamStatus, upBytes: up, downBytes: down, ms: Date.now() - started, closedForSelection: connection.closedForSelection, activeWhileUnchecked: connection.activeWhileUnchecked, ...identity };
        log(entry);
        recordRequest(identity.threadId, entry);
      };
      socket.on("close", close);
      client.on("close", close);
      socket.on("error", close);
      client.on("error", close);
    }, (error) => {
      client.end("HTTP/1.1 502 Bad Gateway\r\n\r\n");
      log({ at: new Date(started).toISOString(), id, transport: "websocket", path, error: String(error), ...requestIdentity(req.headers) });
    });
  };

  // Codex may resolve "localhost" to either loopback address, so listen on both (and only on loopback), one after the
  // other: an engine that loses a start race never holds half of the port. A busy port is tried again for a few
  // seconds, since an engine retiring for this one may still be letting go of it.
  const listen = (host: string, listenPort: number, attempt = 0): Promise<boolean> => new Promise((resolve) => {
    const allowed = (url: string) => url === "/__cam/health" || url.startsWith("/__cam/routes/") === (listenPort === providerPort);
    const server = http.createServer((req, res) => {
      if (allowed(req.url ?? "/")) { onRequest(req, res); return; }
      req.resume(); res.writeHead(421, { "content-type": "text/plain; charset=utf-8" }); res.end(say(currentLang(), "proxy.isolatedRoute"));
    });
    server.on("upgrade", (req, client, head) => {
      if (allowed(req.url ?? "/") && req.url !== "/__cam/health") { onUpgrade(req, client, head); return; }
      client.on("error", () => {});
      client.end("HTTP/1.1 421 Misdirected Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
    });
    server.requestTimeout = 0;
    server.once("error", (error: NodeJS.ErrnoException) => {
      if (error.code === "EADDRINUSE" && attempt < 20) { setTimeout(() => resolve(listen(host, listenPort, attempt + 1)), 150); return; }
      console.error(JSON.stringify({ host, error: String(error) }));
      // Loopback IPv6 may be missing; that is fine. A port another program holds is not.
      resolve(host === "::1" && ["EAFNOSUPPORT", "EADDRNOTAVAIL"].includes(error.code ?? ""));
    });
    server.listen(listenPort, host, () => {
      servers.push(server);
      server.on("error", (error) => console.error(JSON.stringify({ host, error: String(error) })));
      console.log(JSON.stringify({ listening: `http://${host.includes(":") ? `[${host}]` : host}:${listenPort}/${listenPort === providerPort ? "__cam/routes" : "backend-api/codex"}`, upstream: UPSTREAM_HOST, via: via ? `${via.host}:${via.port}` : "direct" }));
      resolve(true);
    });
  });
  // Bind the provider listener before advertising readiness on the legacy port. Older plugin copies never start
  // this listener, so they cannot misroute the persisted provider URLs after a mixed-version restart.
  for (const listenPort of [providerPort, port]) for (const host of ["127.0.0.1", "::1"]) {
    if (await listen(host, listenPort)) continue;
    log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: `port ${listenPort} unavailable on ${host}` });
    process.exit(1);
  }
}

if (isEntryPoint(import.meta.url)) await main();
