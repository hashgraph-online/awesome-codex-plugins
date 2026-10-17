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
// v0.4: Claude Code too (the plugin's mod points ANTHROPIC_BASE_URL here): its /v1/… requests go to api.anthropic.com,
// everything else to chatgpt.com as before. A Claude session is told apart by x-claude-code-session-id.
// Only metadata is logged (never auth headers or conversation content).
// Input: [--port 17891] [--stay (no auto-exit)] [--force-http] [--dump-requests (synthetic test threads only)];
// the outbound proxy is taken from HTTPS_PROXY/HTTP_PROXY or the system proxy settings (Windows, macOS).
// Output: responses streamed back to Codex; <data dir>/proxy/<date>.jsonl; <data dir>/state/requests/<thread>.json.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import http, { type IncomingHttpHeaders } from "node:http";
import net from "node:net";
import { dirname, join } from "node:path";
import type { Duplex } from "node:stream";
import tls from "node:tls";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";
import { childOf, recordChild } from "./children.ts";
import { claudeHome, claudeImageData, claudeStartedAt, loadClaudeIndex, type ClaudeIndex } from "./claude-index.ts";
import { addCompacted, findRequestImages, rewriteMessages, summaryAt, type RequestImage, type Resend } from "./claude-rewrite.ts";
import { chainOf, fitThinking, readThinkingRecord, recordSent, writeThinkingRecord, type ThinkingRecord } from "./claude-thinking.ts";
import { codexHome } from "./codexconfig.ts";
import { buildOf, DEFAULT_PORT, ENGINE_SERVICE, engineHealth, versionOf, watchForCodex } from "./engine.ts";
import { findImages, type ImageRef } from "./images.ts";
import { isEntryPoint } from "./entry.ts";
import { currentLang } from "./language.ts";
import { migrateDataOnce } from "./migrate-data.ts";
import { applyClaudeSelection, claudeImageFor, loadClaudePanelState, type ClaudePanelOptions } from "./panel-state.ts";
import { claudeRequestStatsDirOf, claudeSelectionDirOf, dataDir, pixelCacheDirOf, proxyLogDirOf, selectionDirOf } from "./paths.ts";
import { recordRequest } from "./request-stats.ts";
import { rewriteItems, type Described } from "./rewrite.ts";
import { connectDirectly, pluginGone, usesEngine } from "./setup.ts";
import { claudeSelection, effectiveSelection, ensureAutoDefault, selectionDir, sideChatSelection } from "./selection.ts";
import { loadThreadIndex, pixelHashOf, pixelHashOfData, setPixelCache, sideChatOrigin, type ThreadIndex } from "./thread-index.ts";

type Json = Record<string, any>;
const here = dirname(fileURLToPath(import.meta.url));
const UPSTREAM_HOST = "chatgpt.com";
// v0.4: Claude Code's API host.
export const CLAUDE_HOST = "api.anthropic.com";
const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-connection", "transfer-encoding", "te", "trailer", "upgrade", "host"]);

// Codex's requests all start with /backend-api/ (its base URL ends in /backend-api/codex); Claude Code's with /v1/.
export function upstreamOf(path: string): string {
  return path.startsWith("/v1/") ? CLAUDE_HOST : UPSTREAM_HOST;
}

// Outbound proxy: environment first, then the system setting (Windows per-user, macOS); NO_PROXY is honoured for the
// upstream host.
export function outboundProxy(env = process.env, systemSetting = readSystemProxy, upstream = UPSTREAM_HOST): { host: string; port: number } | null {
  const noProxy = (env.NO_PROXY ?? env.no_proxy ?? "").split(",").map((s) => s.trim().replace(/^\./, "")).filter(Boolean);
  if (noProxy.some((entry) => entry === "*" || upstream === entry || upstream.endsWith(`.${entry}`))) return null;
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

function connectUpstream(via: { host: string; port: number } | null, upstream = UPSTREAM_HOST, signal?: AbortSignal): Promise<tls.TLSSocket> {
  const startTls = (socket?: net.Socket) => new Promise<tls.TLSSocket>((ok, fail) => {
    const cleanup = () => signal?.removeEventListener("abort", abort);
    const secure = tls.connect({ socket, host: socket ? undefined : upstream, port: 443, servername: upstream, ALPNProtocols: ["http/1.1"] }, () => { cleanup(); ok(secure); });
    const abort = () => { cleanup(); secure.destroy(); socket?.destroy(); fail(new Error("upstream connection cancelled")); };
    secure.once("error", (error) => { cleanup(); fail(error); });
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) abort();
  });
  if (!via) return startTls();
  return new Promise((ok, fail) => {
    const socket = net.connect({ port: via.port, host: via.host, signal }, () => socket.write(`CONNECT ${upstream}:443 HTTP/1.1\r\nHost: ${upstream}:443\r\n\r\n`));
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

export function forwardHeaders(headers: IncomingHttpHeaders, upstream = UPSTREAM_HOST): Record<string, string | string[]> {
  const out: Record<string, string | string[]> = {};
  for (const [name, value] of Object.entries(headers)) if (value !== undefined && !HOP_BY_HOP.has(name)) out[name] = value;
  out.host = upstream;
  return out;
}

// Which task a request belongs to, from Codex's own turn metadata header.
// v0.7: and where that task came from: a side chat (a fork Codex keeps in memory only) names the task it was forked
// from, a subagent its parent (also in Codex's own header).
export type RequestIdentity = { threadId: string | null; turnId: string | null; windowId: string | null; forkedFrom: string | null; parentThreadId: string | null; subagentKind: string | null; turnTrigger: string | null };
export function requestIdentity(headers: IncomingHttpHeaders): RequestIdentity {
  let meta: Json = {};
  try { meta = JSON.parse(String(headers["x-codex-turn-metadata"] ?? "{}")); } catch { /* not JSON */ }
  const header = (name: string) => { const value = headers[name]; return (Array.isArray(value) ? value[0] : value) || null; };
  return {
    threadId: meta.thread_id ?? meta.session_id ?? null, turnId: meta.turn_id ?? null, windowId: header("x-codex-window-id"),
    forkedFrom: meta.forked_from_thread_id ?? null, parentThreadId: meta.parent_thread_id ?? header("x-codex-parent-thread-id"), subagentKind: meta.subagent_kind ?? null,
    turnTrigger: meta.turn_trigger ?? null,
  };
}

// v0.4: which Claude Code session a request belongs to, and whether a subagent's loop sent it (its own conversation).
export function claudeIdentity(headers: IncomingHttpHeaders): { sessionId: string | null; agentId: string | null } {
  const one = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value) || null;
  return { sessionId: one(headers["x-claude-code-session-id"]), agentId: one(headers["x-claude-code-agent-id"]) };
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

// v0.4: the requests the panel's "last request" line is about: the session's conversation as the model works on it,
// Claude Code's main loop, which always carries its tools. Claude Desktop also sends side requests in the session (a
// status summary while the user is away, auto mode's safety check): no tools and none of the conversation's images.
// They are rewritten like the rest; only the line leaves them out (2026-10-10: it said "nothing replaced" after a turn
// whose four images had all been left out).
export const claudeConversationRequest = (details: Json): boolean => details.kind === "messages" && details.tools > 0;

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
    // v0.4: an Anthropic image block keeps its base64 in source.data; a thinking block's signature is opaque too.
    const raw = inline ? value.slice(inline[0].length) : (key === "result" || key === "data" || key === "signature") && value.length > 256 ? value : null;
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
// v0.7: a side chat's, unless its task's switch for subagents and side chats is off.
export function needsRewrite(threadId: string | null, dir = selectionDir, sessionsDir = join(codexHome(), "sessions"), forkedFrom: string | null = null): boolean {
  if (!threadId) return false;
  try {
    const origin = sideChatOrigin(threadId, forkedFrom, sessionsDir);
    if (origin) return sideChatSelection(origin, sessionsDir, dir) !== null;
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
// v0.7: a side chat's request carries the history of the task it came from: that task's index, with every one of its
// turns counting as earlier (sideChatSelection).
export function rewriteBody(original: Buffer, encoding: string | undefined, threadId: string, sessionsDir: string, dir = selectionDir, turnId: string | null = null, forkedFrom: string | null = null): { body: Buffer; report: Json } {
  const origin = sideChatOrigin(threadId, forkedFrom, sessionsDir);
  const side = origin ? sideChatSelection(origin, sessionsDir, dir) : null;
  if (origin && !side) return { body: original, report: { sideChatOf: origin, off: true } };
  const decoded = decodeBody(original, encoding);
  if (!decoded) return { body: original, report: { skipped: "undecodable body" } };
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return { body: original, report: { skipped: "unparsable body" } }; }
  if (!Array.isArray(json.input)) return { body: original, report: { skipped: "no input array" } };
  if (hasUnsafeInteger(text)) return { body: original, report: { skipped: "integer beyond 2^53 would change when re-serialized" } };
  let index: ThreadIndex;
  try { index = loadThreadIndex(sessionsDir, origin ?? threadId); } catch (error) { return { body: original, report: { skipped: `thread index: ${String(error)}` } }; }
  const selection = side ?? effectiveSelection(threadId, sessionsDir, dir);
  const describe = (ref: ImageRef): Described | undefined => {
    const known = index.byKey.get(ref.key);
    if (known) return known;
    const stored = selection.unchecked[ref.key];
    return stored ? { id: stored.id, name: ref.name, label: ref.label, kind: ref.kind, turn: null, width: ref.width, height: ref.height } : undefined;
  };
  const pixels = (ref: ImageRef) => index.byKey.get(ref.key)?.pixelSha256 ?? pixelHashOf(json.input, ref);
  const current = side ? index.turns + 1 : currentTurnOf(index, turnId);
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
    ...(origin ? { sideChatOf: origin } : {}),
  };
  if (!report.replaced.length && !report.copies.length) return { body: original, report: summary };
  json.input = items;
  const next = Buffer.from(JSON.stringify(json), "utf8");
  const body = encodeBody(next, encoding);
  return { body, report: { ...summary, decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length } };
}

// v0.4: a Claude Code session's requests are rewritten once something is unchecked there, or automatic selection was
// used (copies the model fetched may be in its history from then on). v0.5: or once it was compacted with images
// before the compaction, which the user may keep sending.
export function claudeNeedsRewrite(sessionId: string | null, dir = claudeSelectionDirOf(), home = claudeHome()): boolean {
  if (!sessionId) return false;
  let index: ClaudeIndex | null = null;
  try { index = loadClaudeIndex(sessionId, home); } catch { /* the selection still decides */ }
  try {
    const selection = claudeSelection(sessionId, dir, index ? claudeStartedAt(index) : null);
    if (Object.keys(selection.unchecked).length > 0 || selection.autoSince) return true;
  } catch { /* the transcript still decides */ }
  return !!index?.images.some((image) => image.compacted);
}

// The images a Claude Code request carried, by index key, with the base64 characters each took (the panel's
// baseline); images not in the transcript yet are left out.
export function claudeImageSizes(messages: Json[], index: ClaudeIndex): Record<string, number> {
  return Object.fromEntries(findRequestImages(messages, index).filter((ref) => ref.key).map((ref) => [ref.key!, ref.base64Chars]));
}

// Anthropic refuses a request whose earlier content changed under the thinking that followed it (accounts created from
// 2026-08-31, or a request that asks for it): docs/v0.4/plan.md §2.2. The engine then sends the original instead.
export function thinkingRejected(status: number, body: string): boolean {
  return status === 400 && /thinking/i.test(body) && /signature|bound to a different conversation|prefix/i.test(body);
}

// v0.4: what to send for a Claude Code request, each next one when Anthropic refuses the thinking after the changed
// history (thinkingRejected): the rewrite with all its thinking (an account that lets it through); the rewrite without
// the thinking that no longer fits (claude-thinking.ts), first once the account is known to refuse it; the rewrite
// without any thinking, always accepted; the original as Claude Code built it. history/sent: the chains to remember
// once the attempt goes through (null: not the session's conversation); made: the histories its thinking was made
// after; sure: the record says all its thinking fits, so a refusal means the record misses what went out.
export type ClaudeAttempt = { body: Buffer; report: Json; history: string | null; sent: string | null; made: string[]; sure: boolean };

// v0.4: the same rules as rewriteBody, for a Claude Code request (Anthropic Messages, claude-rewrite.ts). The current
// turn is the transcript's latest prompt: Claude Code writes it before it sends the request.
// CAM_EXPERIMENT_BLOCK_BINDING (experiments only, docs/v0.4/tasks.md T04-01): asks Anthropic to check thinking with
// that prefix_mismatch_behavior, as for an account created from 2026-08-31; the report names the beta header to add.
export function rewriteClaudeBody(original: Buffer, encoding: string | undefined, sessionId: string, dir = claudeSelectionDirOf(), home = claudeHome(), env = process.env, thinking: ThinkingRecord | null = null): { body: Buffer; report: Json; attempts: ClaudeAttempt[] } {
  const asIs = (report: Json) => ({ body: original, report, attempts: [] });
  const decoded = decodeBody(original, encoding);
  if (!decoded) return asIs({ skipped: "undecodable body" });
  const text = decoded.toString("utf8");
  let json: Json;
  try { json = JSON.parse(text); } catch { return asIs({ skipped: "unparsable body" }); }
  if (!Array.isArray(json.messages)) return asIs({ skipped: "no messages array" });
  if (hasUnsafeInteger(text)) return asIs({ skipped: "integer beyond 2^53 would change when re-serialized" });
  let index: ClaudeIndex;
  try { index = loadClaudeIndex(sessionId, home); } catch (error) { return asIs({ skipped: `thread index: ${String(error)}` }); }
  const selection = claudeSelection(sessionId, dir, claudeStartedAt(index));
  const current = index.turns;
  const copies = new Map([...index.copies.values()].filter((copy) => copy.turn === null || copy.turn < current).map((copy) => [copy.key, copy.of]));
  let leaveOut = new Set(Object.keys(selection.unchecked));
  if (selection.auto) {
    const pinned = selection.pinned ?? {};
    leaveOut = new Set(index.images.filter((image) => image.replaceable && image.turn !== null && image.turn < current && !pinned[image.key]).map((image) => image.key));
  }
  const pixels = (ref: RequestImage) => (ref.key ? index.byKey.get(ref.key)?.pixelSha256 : undefined) ?? pixelHashOfData(ref, ref.block.source.data);
  const lang = currentLang();
  // v0.5: after a compaction, the images from before it go back right after the summary (claude-rewrite.ts): the ones
  // the user keeps sending (checked, or pinned with automatic selection) read from the transcript, the others as
  // placeholders. With any of those, the full note follows the summary, and later messages get only their short notes.
  const compactedImages = index.images.filter((image) => image.compacted);
  const summaryIn = index.summary && compactedImages.length ? summaryAt(json.messages, index.summary) : null;
  const resend: Resend[] = summaryIn === null ? [] : compactedImages.filter((image) => !leaveOut.has(image.key)).flatMap((image) => {
    const data = claudeImageData(index, image);
    return data && image.mime ? [{ image, block: { type: "image", source: { type: "base64", media_type: image.mime, data } } }] : [];
  });
  const compactedOut = summaryIn !== null && resend.length < compactedImages.length;
  const rewrote = rewriteMessages(json.messages, index, leaveOut, pixels, { lang, copies, noted: compactedOut, ...(selection.auto ? { auto: { currentTurn: current } } : {}) });
  const report = rewrote.report;
  let messages = rewrote.messages;
  let compacted: Json | null = null;
  if (summaryIn !== null) {
    const added = addCompacted(messages, index.summary!, compactedImages, resend, { lang, auto: !!selection.auto });
    if (added.at !== null) {
      messages = added.messages;
      // The note's place: after the summary when it holds placeholders; a later one moves down with a message added.
      if (compactedOut) report.noteAt = added.at + 1;
      else if (added.inserted && report.noteAt !== undefined && report.noteAt > added.at) report.noteAt += 1;
      compacted = { at: added.at, listed: compactedImages.length, resent: resend.map(({ image }) => image.id) };
    }
  }
  const summary: Json = {
    images: report.images,
    replaced: report.replaced.map(({ key: _key, ...rest }) => rest),
    locked: report.locked,
    sentImageHashes: report.sentContentIds.map((id) => id.slice(0, 16)),
    thinkingBlocks: json.messages.reduce((sum: number, message: Json) => sum + (Array.isArray(message?.content) ? message.content.filter((block: Json) => block?.type === "thinking" || block?.type === "redacted_thinking").length : 0), 0),
    ...(report.noteAt !== undefined ? { noteAt: report.noteAt } : {}),
    ...(selection.auto ? { auto: true } : {}),
    ...(report.copies.length ? { copies: report.copies } : {}),
    ...(compacted ? { compacted } : {}),
  };
  const changed = report.replaced.length > 0 || report.copies.length > 0 || compacted !== null;
  // Once the engine has sent the session a changed history, thinking made after it may be in every later request, even
  // with nothing left out now (an image checked again).
  if (!changed && !thinking?.edited) return { body: original, report: summary, attempts: [] };
  const rewritten = changed ? messages : json.messages;
  const fit = thinking ? fitThinking(json.messages, rewritten, thinking) : null;
  // Side requests (no tools: the desktop's status summary, auto mode's check) are not the conversation.
  const conversation = Array.isArray(json.tools) && json.tools.length > 0;
  const history = fit && conversation ? fit.history : null;
  const experiment = env.CAM_EXPERIMENT_BLOCK_BINDING?.trim();
  const encode = (list: Json[], extra: Json) => {
    const out: Json = { ...json, messages: list };
    const asked = experiment && json.thinking && typeof json.thinking === "object";
    if (asked) out.thinking = { ...json.thinking, block_binding: { prefix_mismatch_behavior: experiment } };
    const next = Buffer.from(JSON.stringify(out), "utf8");
    const body = encodeBody(next, encoding);
    return { body, report: { ...summary, ...extra, ...(asked ? { experiment: { blockBinding: experiment, beta: "thinking-binding-controls-2026-08-01" } } : {}), decodedBefore: decoded.length, decodedAfter: next.length, encodedBefore: original.length, encodedAfter: body.length } };
  };
  const attempts: ClaudeAttempt[] = [];
  const made = fit?.made ?? [];
  const add = (list: Json[], extra: Json, sent: string, sure: boolean) => attempts.push({ ...encode(list, extra), history, sent: history ? sent : null, made, sure });
  const asBuilt = (extra: Json, sure: boolean) => attempts.push({ body: original, report: { ...summary, ...extra }, history, sent: history, made, sure });
  if (!thinking?.strict) {
    if (changed) add(rewritten, {}, chainOf(rewritten), fit?.left === 0);
    else asBuilt({}, fit!.left === 0);
  }
  if (fit && (thinking!.strict || fit.left)) add(fit.messages, { thinking: { kept: fit.kept, left: fit.left }, ...(thinking!.strict ? {} : { retry: "thinking-signature" }) }, fit.sent, true);
  if (fit?.kept) {
    const bare = fitThinking(json.messages, rewritten, thinking!, false);
    add(bare.messages, { thinking: { kept: 0, left: bare.left }, retry: "thinking-signature" }, bare.sent, false);
  }
  if (changed || thinking?.strict) asBuilt(changed ? { fallback: "thinking-signature" } : {}, false);
  return { body: attempts[0].body, report: attempts[0].report, attempts };
}

// v0.4: a Claude Code session's panel reads and changes its images here: the panel page the engine serves
// (/__cam/panel, panel.html with panel-web.js) and the Claude plugin's mod. The Codex panel goes through the plugin's
// MCP server; under Claude Code that is not open to a panel (a mod reaches it only through Claude Code's tool
// permissions, a prompt for every call, and Claude Code registers no app-only tool), so the engine, the one local HTTP
// service, serves the panel. Loopback only, like everything the engine serves; only a request naming the engine by a
// loopback name (no other site rebinding its name to 127.0.0.1), carrying our header, and coming from no other site's
// page (a browser's Origin, when sent, is the engine's own).
const SESSION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const LOOPBACK_HOST = /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/;
export function ownRequest(headers: IncomingHttpHeaders): boolean {
  const host = String(headers.host ?? "");
  if (!LOOPBACK_HOST.test(host)) return false;
  return headers.origin === undefined || headers.origin === `http://${host}`;
}

// The panel page for a Claude Code session: the same panel.html as in Codex, with panel-web.js before its own script.
export function claudePanelPage(dir = here): string {
  const page = readFileSync(join(dir, "panel.html"), "utf8");
  const bridge = readFileSync(join(dir, "panel-web.js"), "utf8");
  const at = page.indexOf("<script>");
  if (at < 0) throw new Error("panel.html has no script");
  return `${page.slice(0, at)}<script>\n${bridge}\n</script>\n${page.slice(at)}`;
}
export const PANEL_PAGE_CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'";

export function claudePanelApi(method: string, url: string, headers: IncomingHttpHeaders, body: string | null, options: ClaudePanelOptions = {}): { status: number; body: Json } {
  if (!ownRequest(headers) || headers["x-cam-panel"] !== "1") return { status: 403, body: { error: "forbidden" } };
  const parsed = new URL(url, "http://localhost");
  const session = parsed.searchParams.get("session") ?? "";
  if (!SESSION_ID.test(session)) return { status: 400, body: { error: "no session" } };
  const lang = currentLang();
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

async function main(): Promise<void> {
  migrateDataOnce(); // v0.1-15: Windows moved the data folder
  // v0.6: tasks and sessions started from now on have automatic selection on by default (selection.ts).
  ensureAutoDefault(selectionDirOf());
  ensureAutoDefault(claudeSelectionDirOf());
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
  // v0.4: NO_PROXY may name one upstream host and not the other.
  const claudeVia = outboundProxy(process.env, readSystemProxy, CLAUDE_HOST);
  const viaOf = (upstream: string) => (upstream === CLAUDE_HOST ? claudeVia : via);
  const startedAt = new Date().toISOString();
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
  // (claude-thinking.ts); the latest sessions stay in memory.
  const thinkingRecords = new Map<string, ThinkingRecord>();
  const thinkingOf = (sessionId: string): ThinkingRecord => {
    const record = thinkingRecords.get(sessionId) ?? readThinkingRecord(sessionId);
    thinkingRecords.delete(sessionId);
    thinkingRecords.set(sessionId, record);
    for (const key of thinkingRecords.keys()) if (thinkingRecords.size > 50) thinkingRecords.delete(key);
    return record;
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
    setInterval(() => checkPlugin(false), 15_000).unref();
    watchForCodex(() => {
      checkPlugin(true);
      log({ at: new Date().toISOString(), event: "engine-exit", pid: process.pid, reason: "no Codex or Claude Code process left" });
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
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ ok: true, service: ENGINE_SERVICE, pid: process.pid, startedAt, port, build, version, upstream: UPSTREAM_HOST, upstreams: [UPSTREAM_HOST, CLAUDE_HOST], via: via ? `${via.host}:${via.port}` : "direct" }));
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
    const path = (req.url ?? "/").split("?")[0];
    const upstream = upstreamOf(path);
    const identity = requestIdentity(req.headers);
    const rewrite = req.method === "POST" && /\/responses(\/compact)?$/.test(path) && needsRewrite(identity.threadId, selectionDir, sessionsDir, identity.forkedFrom);
    // v0.4: a Claude Code request of a session's main conversation (a subagent's loop has its own); rewritten like a
    // Codex thread's once something is unchecked there.
    const claude = upstream === CLAUDE_HOST ? claudeIdentity(req.headers) : null;
    const claudeSession = claude?.sessionId && !claude.agentId && req.method === "POST" && path === "/v1/messages" ? claude.sessionId : null;
    // Once the engine has sent the session a changed history, every request of it is looked at, even with nothing left
    // out now: thinking made after a changed history no longer fits the history as it was.
    const thinking = claudeSession ? thinkingOf(claudeSession) : null;
    const claudeRewrite = claudeNeedsRewrite(claudeSession) || !!thinking?.edited;
    const claudeFields = claude ? { claudeSessionId: claude.sessionId, claudeAgentId: claude.agentId } : {};
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
          if (claudeSession && Array.isArray(json.messages)) imageSizes = claudeImageSizes(json.messages, loadClaudeIndex(claudeSession));
          if (dumpDir && (/\/responses$/.test(path) || path === "/v1/messages")) {
            mkdirSync(dumpDir, { recursive: true });
            const headers = Object.fromEntries(Object.entries(req.headers).filter(([name]) => /^(x-codex|session_id|conversation_id|openai-beta|content-|anthropic-(beta|version)|x-claude-code-|user-agent)/.test(name)));
            writeFileSync(join(dumpDir, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}.json`), JSON.stringify({ path, headers, body: redactImages(json) }, null, 2));
            if (sentBody) { const sent = decodeBody(sentBody, req.headers["content-encoding"] as string | undefined); if (sent) writeFileSync(join(dumpDir, `${new Date(started).toISOString().replaceAll(":", "-")}-${id}.sent.json`), JSON.stringify({ path, body: redactImages(JSON.parse(sent.toString("utf8"))) }, null, 2)); }
          }
        } catch { details = { kind: "unparsed" }; }
      }
      const entry = { at: new Date(started).toISOString(), id, transport: "http", method: req.method, path, status, requestBytes, decodedBytes: decoded?.length ?? null, contentEncoding: req.headers["content-encoding"] ?? null, responseBytes, ms: Date.now() - started, ...identity, ...claudeFields, ...details, ...extra, error: error ?? null };
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
    type Attempt = { body: Buffer | null; report: Json | null; edited: boolean } & Partial<Pick<ClaudeAttempt, "history" | "sent" | "made" | "sure">>;
    const connecting = new AbortController();
    res.once("close", () => {
      if (!res.writableFinished) { connecting.abort(); finish("client closed before the response ended"); }
    });
    const send = (attempts: Attempt[], at = 0): void => {
      if (res.destroyed) return;
      connectUpstream(viaOf(upstream), upstream, connecting.signal).then((socket) => {
      // The client can cancel while CONNECT/TLS is still in progress.
      if (res.destroyed) { socket.destroy(); return; }
      const attempt = attempts[at];
      const outgoing = forwardHeaders(req.headers, upstream);
      if (attempt.body) outgoing["content-length"] = String(attempt.body.length);
      const beta = attempt.report?.experiment?.beta;
      if (beta) outgoing["anthropic-beta"] = [String(outgoing["anthropic-beta"] ?? ""), beta].filter(Boolean).join(",");
      if (attempt.report) extra = { ...extra, rewrite: attempt.report };
      if (dumpDir) sentBody = attempt.edited ? attempt.body : null;
      // No `agent` option: with agent:false Node ignores createConnection and dials the host directly.
      const outbound = http.request({ host: upstream, method: req.method, path: req.url, headers: outgoing, createConnection: () => socket }, (answer) => {
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
    if (!rewrite && !claudeRewrite) { send([{ body: null, report: null, edited: false }]); return; }
    collect();
    req.on("end", () => {
      const original = Buffer.concat(chunks);
      const encoding = req.headers["content-encoding"] as string | undefined;
      let out: { body: Buffer; report: Json; attempts?: ClaudeAttempt[] };
      try { out = claudeRewrite ? rewriteClaudeBody(original, encoding, claudeSession!, undefined, undefined, undefined, thinking) : rewriteBody(original, encoding, identity.threadId!, sessionsDir, selectionDir, identity.turnId, identity.forkedFrom); }
      catch (error) { out = { body: original, report: { skipped: `rewrite failed: ${String(error)}` } }; }
      const attempts: Attempt[] = out.attempts?.length ? out.attempts.map((attempt) => ({ ...attempt, edited: attempt.body !== original })) : [{ body: out.body, report: out.report, edited: out.body !== original }];
      send(attempts);
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
    if (/\/responses$/.test(path) && (forceHttp || needsRewrite(identity.threadId, selectionDir, sessionsDir, identity.forkedFrom))) {
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
      noteChild(identity, opened.at);
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
