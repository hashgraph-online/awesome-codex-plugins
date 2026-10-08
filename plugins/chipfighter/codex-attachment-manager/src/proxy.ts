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
// Only metadata is logged (never auth headers or conversation content).
// Input: [--port 17891] [--stay (no auto-exit)] [--force-http] [--dump-requests (synthetic test threads only)];
// the outbound proxy is taken from HTTPS_PROXY/HTTP_PROXY or the system proxy settings (Windows, macOS).
// Output: responses streamed back to Codex; <data dir>/proxy/<date>.jsonl; <data dir>/state/requests/<thread>.json.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import http, { type IncomingHttpHeaders } from "node:http";
import net from "node:net";
import { join } from "node:path";
import type { Duplex } from "node:stream";
import tls from "node:tls";
import zlib from "node:zlib";
import { codexHome } from "./codexconfig.ts";
import { buildOf, DEFAULT_PORT, ENGINE_SERVICE, engineHealth, versionOf, watchForCodex } from "./engine.ts";
import { findImages, type ImageRef } from "./images.ts";
import { isEntryPoint } from "./entry.ts";
import { currentLang } from "./language.ts";
import { migrateDataOnce } from "./migrate-data.ts";
import { dataDir, pixelCacheDirOf, proxyLogDirOf } from "./paths.ts";
import { recordRequest } from "./request-stats.ts";
import { rewriteItems, type Described } from "./rewrite.ts";
import { connectDirectly, pluginGone, usesEngine } from "./setup.ts";
import { effectiveSelection, selectionDir } from "./selection.ts";
import { loadThreadIndex, pixelHashOf, setPixelCache, type ThreadIndex } from "./thread-index.ts";

type Json = Record<string, any>;
const UPSTREAM_HOST = "chatgpt.com";
const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-connection", "transfer-encoding", "te", "trailer", "upgrade", "host"]);

// Outbound proxy: environment first, then the system setting (Windows per-user, macOS); NO_PROXY is honoured for the
// upstream host.
export function outboundProxy(env = process.env, systemSetting = readSystemProxy): { host: string; port: number } | null {
  const noProxy = (env.NO_PROXY ?? env.no_proxy ?? "").split(",").map((s) => s.trim().replace(/^\./, "")).filter(Boolean);
  if (noProxy.some((entry) => entry === "*" || UPSTREAM_HOST === entry || UPSTREAM_HOST.endsWith(`.${entry}`))) return null;
  const fromEnv = env.HTTPS_PROXY ?? env.https_proxy ?? env.HTTP_PROXY ?? env.http_proxy;
  let value = fromEnv || systemSetting();
  if (!value) return null;
  // Windows may store per-protocol entries: "http=host:port;https=host:port".
  if (value.includes("=")) value = /https=([^;]+)/.exec(value)?.[1] ?? /http=([^;]+)/.exec(value)?.[1] ?? "";
  if (!value) return null;
  const url = new URL(/^[a-z]+:\/\//i.test(value) ? value : `http://${value}`);
  return { host: url.hostname, port: Number(url.port || 80) };
}

function readSystemProxy(): string | null {
  try {
    if (process.platform === "win32") {
      const out = execFileSync("reg", ["query", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings"], { encoding: "utf8" });
      if (!/ProxyEnable\s+REG_DWORD\s+0x1/.test(out)) return null;
      return /ProxyServer\s+REG_SZ\s+(\S+)/.exec(out)?.[1] ?? null;
    }
    if (process.platform === "darwin") return macProxy(execFileSync("scutil", ["--proxy"], { encoding: "utf8" }));
  } catch { /* no setting readable: connect directly */ }
  return null;
}

// v0.1: `scutil --proxy` lists the macOS system proxies as "Key : value" lines. Only HTTP(S) proxies are usable here
// (the engine tunnels with CONNECT); PAC files and SOCKS are not read. Linux has no system setting beyond the
// environment.
export function macProxy(scutil: string): string | null {
  const field = (key: string) => scutil.match(new RegExp(`^\\s*${key}\\s*:\\s*(\\S+)\\s*$`, "m"))?.[1] ?? null;
  for (const scheme of ["HTTPS", "HTTP"]) {
    const host = field(`${scheme}Proxy`);
    if (field(`${scheme}Enable`) === "1" && host) return `${host}:${field(`${scheme}Port`) ?? "80"}`;
  }
  return null;
}

function connectUpstream(via: { host: string; port: number } | null): Promise<tls.TLSSocket> {
  const startTls = (socket?: net.Socket) => new Promise<tls.TLSSocket>((ok, fail) => {
    const secure = tls.connect({ socket, host: socket ? undefined : UPSTREAM_HOST, port: 443, servername: UPSTREAM_HOST, ALPNProtocols: ["http/1.1"] }, () => ok(secure));
    secure.once("error", fail);
  });
  if (!via) return startTls();
  return new Promise((ok, fail) => {
    const socket = net.connect(via.port, via.host, () => socket.write(`CONNECT ${UPSTREAM_HOST}:443 HTTP/1.1\r\nHost: ${UPSTREAM_HOST}:443\r\n\r\n`));
    let buffered = Buffer.alloc(0);
    const onData = (chunk: Buffer) => {
      buffered = Buffer.concat([buffered, chunk]);
      const end = buffered.indexOf("\r\n\r\n");
      if (end < 0) return;
      socket.off("data", onData);
      const status = buffered.toString("latin1", 0, end).split(" ")[1];
      if (status !== "200") { socket.destroy(); fail(new Error(`outbound proxy refused CONNECT (${status})`)); return; }
      startTls(socket).then(ok, fail);
    };
    socket.on("data", onData);
    socket.once("error", fail);
  });
}

function forwardHeaders(headers: IncomingHttpHeaders): Record<string, string | string[]> {
  const out: Record<string, string | string[]> = {};
  for (const [name, value] of Object.entries(headers)) if (value !== undefined && !HOP_BY_HOP.has(name)) out[name] = value;
  out.host = UPSTREAM_HOST;
  return out;
}

// Which task a request belongs to, from Codex's own turn metadata header.
export function requestIdentity(headers: IncomingHttpHeaders): { threadId: string | null; turnId: string | null; windowId: string | null } {
  let meta: Json = {};
  try { meta = JSON.parse(String(headers["x-codex-turn-metadata"] ?? "{}")); } catch { /* not JSON */ }
  return { threadId: meta.thread_id ?? meta.session_id ?? null, turnId: meta.turn_id ?? null, windowId: (headers["x-codex-window-id"] as string) ?? null };
}

function decodeBody(body: Buffer, encoding: string | undefined): Buffer | null {
  try {
    if (!encoding || encoding === "identity") return body;
    if (encoding === "zstd") return zlib.zstdDecompressSync(body);
    if (encoding === "gzip") return zlib.gunzipSync(body);
    if (encoding === "br") return zlib.brotliDecompressSync(body);
  } catch { /* fall through */ }
  return null;
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
  return { kind: "other" };
}

function log(entry: Json): void {
  const dir = proxyLogDirOf();
  mkdirSync(dir, { recursive: true });
  appendFileSync(join(dir, `${new Date().toISOString().slice(0, 10)}.jsonl`), `${JSON.stringify(entry)}\n`);
}

// The images a request carried and the base64 characters each took, under the same keys as the thread index.
export function imageSizesOf(input: Json[]): Record<string, number> {
  return Object.fromEntries(findImages(input).map((ref) => [ref.key, ref.base64Chars]));
}

// P2-1 debugging aid for synthetic test threads only: the request with every inline image reduced to its hash and size.
export function redactImages(value: unknown, key = ""): unknown {
  if (typeof value === "string") {
    const inline = /^data:([^;,]+);base64,/.exec(value);
    const raw = inline ? value.slice(inline[0].length) : key === "result" && value.length > 256 ? value : null;
    if (raw === null) return value;
    const digest = createHash("sha256").update(raw).digest("hex").slice(0, 16);
    return `${inline ? `data:${inline[1]};base64,` : ""}<sha256:${digest} chars:${raw.length}>`;
  }
  if (Array.isArray(value)) return value.map((item) => redactImages(item));
  if (value && typeof value === "object") return Object.fromEntries(Object.entries(value).map(([name, child]) => [name, redactImages(child, name)]));
  return value;
}

function encodeBody(body: Buffer, encoding: string | undefined): Buffer {
  if (encoding === "zstd") return zlib.zstdCompressSync(body);
  if (encoding === "gzip") return zlib.gzipSync(body);
  if (encoding === "br") return zlib.brotliCompressSync(body);
  return body;
}

// Number tokens outside strings that JavaScript cannot represent exactly.
export function hasUnsafeInteger(json: string): boolean {
  for (const match of json.matchAll(/"(?:[^"\\]|\\.)*"|(?<![\d.eE+-])(-?\d+)(?![.\deE])/g)) {
    if (match[1] && !Number.isSafeInteger(Number(match[1]))) return true;
  }
  return false;
}

export function hasUnchecked(threadId: string | null, dir = selectionDir, sessionsDir = join(codexHome(), "sessions")): boolean {
  if (!threadId) return false;
  try { return Object.keys(effectiveSelection(threadId, sessionsDir, dir).unchecked).length > 0; } catch { return false; }
}

// Whether a thread's requests go through the rewrite (and so over HTTP): something unchecked, or automatic selection
// used at some point (v0.3), since from then on the history may hold copies the model fetched, left out of later turns.
export function needsRewrite(threadId: string | null, dir = selectionDir, sessionsDir = join(codexHome(), "sessions")): boolean {
  if (!threadId) return false;
  try {
    const selection = effectiveSelection(threadId, sessionsDir, dir);
    return Object.keys(selection.unchecked).length > 0 || !!selection.autoSince;
  } catch { return false; }
}

// The turn a request belongs to, as numbered in the index; a turn not written to the rollout yet comes after the last.
// Without a turn id the last one counts as current, so its images are sent rather than left out.
export function currentTurnOf(index: ThreadIndex, turnId: string | null): number {
  if (!turnId) return index.turns;
  return index.turnNumbers.get(turnId) ?? index.turns + 1;
}

// P2: replace the thread's unchecked images with placeholders. Whenever the body cannot be handled safely it is
// forwarded unchanged and the reason is logged; the report never contains conversation content.
// v0.3: with automatic selection on, the images of earlier turns that are not pinned instead; in either mode, copies
// the model fetched in an earlier turn.
export function rewriteBody(original: Buffer, encoding: string | undefined, threadId: string, sessionsDir: string, dir = selectionDir, turnId: string | null = null): { body: Buffer; report: Json } {
  const decoded = decodeBody(original, encoding);
  if (!decoded) return { body: original, report: { skipped: "undecodable body" } };
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return { body: original, report: { skipped: "unparsable body" } }; }
  if (!Array.isArray(json.input)) return { body: original, report: { skipped: "no input array" } };
  if (hasUnsafeInteger(text)) return { body: original, report: { skipped: "integer beyond 2^53 would change when re-serialized" } };
  let index: ThreadIndex;
  try { index = loadThreadIndex(sessionsDir, threadId); } catch (error) { return { body: original, report: { skipped: `thread index: ${String(error)}` } }; }
  const selection = effectiveSelection(threadId, sessionsDir, dir);
  const describe = (ref: ImageRef): Described | undefined => {
    const known = index.byKey.get(ref.key);
    if (known) return known;
    const stored = selection.unchecked[ref.key];
    return stored ? { id: stored.id, name: ref.name, label: ref.label, kind: ref.kind, turn: null, width: ref.width, height: ref.height } : undefined;
  };
  const pixels = (ref: ImageRef) => index.byKey.get(ref.key)?.pixelSha256 ?? pixelHashOf(json.input, ref);
  const current = currentTurnOf(index, turnId);
  const copies = new Map([...index.copies.values()].filter((copy) => copy.turn === null || copy.turn < current).map((copy) => [copy.key, copy.of]));
  let leaveOut = new Set(Object.keys(selection.unchecked));
  if (selection.auto) {
    const pinned = selection.pinned ?? {};
    leaveOut = new Set(index.images.filter((image) => image.replaceable && image.turn !== null && image.turn < current && !pinned[image.key]).map((image) => image.key));
  }
  const { items, report } = rewriteItems(json.input, describe, leaveOut, pixels, { lang: currentLang(), copies, ...(selection.auto ? { auto: { currentTurn: current } } : {}) });
  const summary: Json = {
    images: report.images,
    replaced: report.replaced.map(({ key: _key, ...rest }) => rest),
    locked: report.locked,
    sentImageHashes: report.sentContentIds.map((id) => id.slice(0, 16)),
    ...(selection.auto ? { auto: true } : {}),
    ...(report.copies.length ? { copies: report.copies } : {}),
  };
  if (!report.replaced.length && !report.copies.length) return { body: original, report: summary };
  json.input = items;
  const next = Buffer.from(JSON.stringify(json), "utf8");
  const body = encodeBody(next, encoding);
  return { body, report: { ...summary, decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length } };
}

async function main(): Promise<void> {
  migrateDataOnce(); // v0.1-15: Windows moved the data folder
  const portIndex = process.argv.indexOf("--port");
  const port = Number(portIndex >= 0 ? process.argv[portIndex + 1] : DEFAULT_PORT);
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
  const via = outboundProxy();
  const startedAt = new Date().toISOString();
  // v0.1-3: which code this engine runs, so the plugin can tell when an update needs a new engine.
  const build = buildOf();
  const version = versionOf();
  let sequence = 0;
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
    setInterval(() => checkPlugin(false), 15_000).unref();
    watchForCodex(() => {
      checkPlugin(true);
      log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: "no Codex process left" });
      process.exit(0);
    });
  }
  // Open WebSocket connections per thread. Over WebSocket Codex only sends new items and the server keeps the rest,
  // so a thread with unchecked images must move to HTTP: its idle connections are closed, and its next upgrade gets 426.
  type Live = { client: Duplex; socket: tls.TLSSocket; last: number; closedForSelection: boolean; activeWhileUnchecked: boolean; path: string; identity: Json };
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
      if (!needsRewrite(threadId)) continue;
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
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ ok: true, service: ENGINE_SERVICE, pid: process.pid, startedAt, port, build, version, upstream: UPSTREAM_HOST, via: via ? `${via.host}:${via.port}` : "direct" }));
      return;
    }
    if (req.url === "/__cam/retire" && req.method === "POST") {
      res.writeHead(200, { "content-type": "application/json", connection: "close" });
      res.end(JSON.stringify({ retiring: true, pid: process.pid }));
      retire(String(req.headers["x-cam-build"] ?? ""));
      return;
    }
    inFlight++;
    res.on("close", () => { inFlight--; });
    // Once retired, no connection stays open for a next request.
    if (retiredAt !== null) res.shouldKeepAlive = false;
    const id = ++sequence;
    const started = Date.now();
    const path = (req.url ?? "/").split("?")[0];
    const identity = requestIdentity(req.headers);
    const rewrite = req.method === "POST" && /\/responses(\/compact)?$/.test(path) && needsRewrite(identity.threadId);
    const chunks: Buffer[] = [];
    let requestBytes = 0;
    let responseBytes = 0;
    let status = 0;
    let finished = false;
    let extra: Json = {};
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
          if (dumpDir && /\/responses$/.test(path)) {
            mkdirSync(dumpDir, { recursive: true });
            const headers = Object.fromEntries(Object.entries(req.headers).filter(([name]) => /^(x-codex|session_id|conversation_id|openai-beta|content-)/.test(name)));
            writeFileSync(join(dumpDir, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}.json`), JSON.stringify({ path, headers, body: redactImages(json) }, null, 2));
          }
        } catch { details = { kind: "unparsed" }; }
      }
      const entry = { at: new Date(started).toISOString(), id, transport: "http", method: req.method, path, status, requestBytes, decodedBytes: decoded?.length ?? null, contentEncoding: req.headers["content-encoding"] ?? null, responseBytes, ms: Date.now() - started, ...identity, ...details, ...extra, error: error ?? null };
      log(entry);
      // Image keys go to the per-thread statistics only, not to the log.
      if (/\/responses$/.test(path)) recordRequest(identity.threadId, imageSizes ? { ...entry, imageSizes } : entry);
    };
    // body === null streams the request through unchanged.
    const send = (headers: Record<string, string | string[]>, body: Buffer | null) => connectUpstream(via).then((socket) => {
      // No `agent` option: with agent:false Node ignores createConnection and dials the host directly.
      const upstream = http.request({ host: UPSTREAM_HOST, method: req.method, path: req.url, headers, createConnection: () => socket }, (answer) => {
        status = answer.statusCode ?? 0;
        const headers: Record<string, string | string[]> = {};
        for (const [name, value] of Object.entries(answer.headers)) if (value !== undefined && !HOP_BY_HOP.has(name)) headers[name] = value;
        res.writeHead(status, headers);
        answer.on("data", (chunk: Buffer) => { responseBytes += chunk.length; });
        answer.pipe(res);
        answer.on("end", () => finish());
        answer.on("error", (error) => finish(String(error)));
      });
      upstream.on("error", (error) => { if (!res.headersSent) res.writeHead(502); res.end(); finish(String(error)); });
      // Codex may drop the connection mid-stream; still log the request once.
      res.on("close", () => finish(res.writableFinished ? undefined : "client closed before the response ended"));
      if (body) upstream.end(body);
      else { collect(); req.pipe(upstream); }
    }, (error) => {
      res.writeHead(502, { "content-type": "text/plain" });
      res.end(`codex-attachment-manager proxy: cannot reach ${UPSTREAM_HOST}`);
      finish(String(error));
    });
    if (!rewrite) { send(forwardHeaders(req.headers), null); return; }
    collect();
    req.on("end", () => {
      const original = Buffer.concat(chunks);
      let out: { body: Buffer; report: Json };
      try { out = rewriteBody(original, req.headers["content-encoding"] as string | undefined, identity.threadId!, sessionsDir, selectionDir, identity.turnId); }
      catch (error) { out = { body: original, report: { skipped: `rewrite failed: ${String(error)}` } }; }
      extra = { rewrite: out.report };
      const headers = forwardHeaders(req.headers);
      headers["content-length"] = String(out.body.length);
      send(headers, out.body);
    });
  };

  const onUpgrade = (req: http.IncomingMessage, client: Duplex, head: Buffer) => {
    const id = ++sequence;
    const started = Date.now();
    const path = (req.url ?? "/").split("?")[0];
    const identity = requestIdentity(req.headers);
    // A retired engine takes no new WebSocket; Codex opens it again, on the new engine.
    if (retiredAt !== null) {
      client.end("HTTP/1.1 503 Service Unavailable\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
      return;
    }
    if (/\/responses$/.test(path) && (forceHttp || needsRewrite(identity.threadId))) {
      client.end("HTTP/1.1 426 Upgrade Required\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
      log({ at: new Date(started).toISOString(), id, transport: "websocket", path, declined: 426, reason: forceHttp ? "--force-http" : "thread needs its requests rewritten", ...identity });
      return;
    }
    let up = head.length;
    let down = 0;
    let upstreamStatus: string | null = null;
    connectUpstream(via).then((socket) => {
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
      const lines = [`${req.method} ${req.url} HTTP/1.1`];
      for (let i = 0; i < req.rawHeaders.length; i += 2) {
        const name = req.rawHeaders[i];
        lines.push(`${name}: ${name.toLowerCase() === "host" ? UPSTREAM_HOST : req.rawHeaders[i + 1]}`);
      }
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
        const entry = { at: new Date(started).toISOString(), id, transport: "websocket", path, upstreamStatus, upBytes: up, downBytes: down, ms: Date.now() - started, closedForSelection: connection.closedForSelection, activeWhileUnchecked: connection.activeWhileUnchecked, ...identity };
        log(entry);
        recordRequest(identity.threadId, entry);
      };
      socket.on("close", close);
      client.on("close", close);
      socket.on("error", close);
      client.on("error", close);
    }, (error) => {
      client.end("HTTP/1.1 502 Bad Gateway\r\n\r\n");
      log({ at: new Date(started).toISOString(), id, transport: "websocket", path: req.url, error: String(error), ...requestIdentity(req.headers) });
    });
  };

  // Codex may resolve "localhost" to either loopback address, so listen on both (and only on loopback), one after the
  // other: an engine that loses a start race never holds half of the port. A busy port is tried again for a few
  // seconds, since an engine retiring for this one may still be letting go of it.
  const listen = (host: string, attempt = 0): Promise<boolean> => new Promise((resolve) => {
    const server = http.createServer(onRequest);
    server.on("upgrade", onUpgrade);
    server.requestTimeout = 0;
    server.once("error", (error: NodeJS.ErrnoException) => {
      if (error.code === "EADDRINUSE" && attempt < 20) { setTimeout(() => resolve(listen(host, attempt + 1)), 150); return; }
      console.error(JSON.stringify({ host, error: String(error) }));
      // Loopback IPv6 may be missing; that is fine. A port another program holds is not.
      resolve(error.code !== "EADDRINUSE");
    });
    server.listen(port, host, () => {
      servers.push(server);
      server.on("error", (error) => console.error(JSON.stringify({ host, error: String(error) })));
      console.log(JSON.stringify({ listening: `http://${host.includes(":") ? `[${host}]` : host}:${port}/backend-api/codex`, upstream: UPSTREAM_HOST, via: via ? `${via.host}:${via.port}` : "direct" }));
      resolve(true);
    });
  });
  for (const host of ["127.0.0.1", "::1"]) {
    if (await listen(host)) continue;
    log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: `port ${port} in use on ${host}` });
    process.exit(1);
  }
}

if (isEntryPoint(import.meta.url)) await main();
