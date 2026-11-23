// Purpose: v0.12 — how a request reaches its service, whatever the platform (docs/design.md section 4).
// Over HTTP/2 when the service speaks it: connections stay open and the requests to one service share them, and each
// connection sends a PING every 15 s. A proxy may end connections that carry nothing for a while: the user's ended
// them after 60 s (2026-11-22, some routes after 20 s), and an image being generated sends nothing until it is done,
// so 2 in 3 image requests were cut in a month; a conversation request thinking quietly for a minute was cut too.
// Reusing a connection also saves the TLS handshake every request used to pay (~0.3 s through that proxy).
// Over a new HTTP/1.1 connection, as before, when the service answers the HTTP/2 offer with HTTP/1.1, for plain-HTTP
// routes, and with CAM_UPSTREAM_H2=0. A request that certainly never reached the service (no connection could be
// made, or the service refused the stream) is tried once more; any other failure goes back to the client, which has
// its own retries.
// Input: where to send (host, port, TLS or not, outbound proxy) and the request (method, path, headers, whole body).
// Output: the answer's status, headers and body stream, and how it went (protocol, connection reused, setup time,
// retries).

import http from "node:http";
import http2 from "node:http2";
import type net from "node:net";
import { PassThrough, type Readable } from "node:stream";
import type tls from "node:tls";
import { connectUpstream, HOP_BY_HOP } from "./transport.ts";

export type Via = { host: string; port: number } | null;
export type Target = { host: string; port: number; secure: boolean; via: Via };
// headers: as the engine forwards them, `host` included; body: the whole body, or null when the request has none.
export type Outgoing = { method: string; path: string; headers: Record<string, string | string[]>; body: Buffer | null };
export type Answer = {
  status: number; headers: Record<string, string | string[]>; body: Readable;
  proto: "h2" | "http/1.1"; reused: boolean; connectMs: number; retries: number;
  // Stops the request: the client went away.
  cancel: () => void;
};

const { NGHTTP2_CANCEL, NGHTTP2_NO_ERROR, NGHTTP2_REFUSED_STREAM, HTTP2_HEADER_STATUS } = http2.constants;
const number = (value: string | undefined, fallback: number) => (Number(value) > 0 ? Number(value) : fallback);
export const H2_ENABLED = process.env.CAM_UPSTREAM_H2 !== "0";
// The shortest cut seen was 20 s of nothing; the tests set shorter times.
const PING_MS = number(process.env.CAM_H2_PING_MS, 15_000);
// A connection no request has used for this long is closed.
const IDLE_MS = number(process.env.CAM_H2_IDLE_MS, 5 * 60_000);
// No PING answered for this long while requests are open on it: the connection is dead, and its requests fail now
// instead of waiting for the operating system to notice.
const SILENT_MS = number(process.env.CAM_H2_SILENT_MS, 120_000);
const MAX_CONNECTIONS = 4;
// Requests open on one connection before another connection to the same service is opened.
const SHARE_UP_TO = 8;
// Headers HTTP/2 does not allow (RFC 9113, 8.2.2) besides the hop-by-hop ones.
const NOT_IN_H2 = new Set(["http2-settings"]);

type Pooled = { session: http2.ClientHttp2Session; active: number; idleSince: number; heard: number; closing: boolean };
const pools = new Map<string, Pooled[]>();
// Services that answered an HTTP/2 offer with HTTP/1.1: offered again after a while.
const http1Until = new Map<string, number>();

type Retryable = Error & { retryable?: boolean };
const retryable = (error: unknown): Retryable => Object.assign(error instanceof Error ? error : new Error(String(error)), { retryable: true });

const keyOf = (target: Target) => `${target.host}:${target.port}|${target.via ? `${target.via.host}:${target.via.port}` : "direct"}`;
export const authorityOf = (target: Pick<Target, "host" | "port" | "secure">) => {
  const host = target.host.includes(":") ? `[${target.host}]` : target.host;
  return target.port !== (target.secure ? 443 : 80) ? `${host}:${target.port}` : host;
};

export async function sendUpstream(target: Target, out: Outgoing, signal: AbortSignal): Promise<Answer> {
  for (let retries = 0; ; retries++) {
    try {
      return { ...(await sendOnce(target, out, signal)), retries };
    } catch (error) {
      if (!(error as Retryable).retryable || retries >= 1 || signal.aborted) throw error;
      await new Promise((resolve) => setTimeout(resolve, 300));
    }
  }
}

async function sendOnce(target: Target, out: Outgoing, signal: AbortSignal): Promise<Omit<Answer, "retries">> {
  const key = keyOf(target);
  const h2 = H2_ENABLED && target.secure && (http1Until.get(key) ?? 0) < Date.now();
  if (h2) {
    const pooled = pick(key);
    if (pooled) return onHttp2(pooled, target, out, signal, true, 0);
  }
  const started = Date.now();
  let socket: net.Socket;
  // Nothing has been sent yet: a connection that cannot be made is tried again.
  try { socket = await connectUpstream(target.via, target.host, signal, target.port, target.secure, h2 ? ["h2", "http/1.1"] : ["http/1.1"]); } catch (error) { throw retryable(error); }
  const connectMs = Date.now() - started;
  if (h2 && (socket as tls.TLSSocket).alpnProtocol === "h2") return onHttp2(adopt(key, target, socket), target, out, signal, false, connectMs);
  if (h2) http1Until.set(key, Date.now() + 10 * 60_000);
  return onHttp1(socket, target, out, signal, connectMs);
}

const usable = (pooled: Pooled) => !pooled.closing && !pooled.session.closed && !pooled.session.destroyed;

function pick(key: string): Pooled | null {
  const pool = (pools.get(key) ?? []).filter(usable);
  pools.set(key, pool);
  if (!pool.length) return null;
  const best = pool.reduce((a, b) => (b.active < a.active ? b : a));
  const limit = Math.min(best.session.remoteSettings?.maxConcurrentStreams ?? 100, 100);
  if (best.active >= limit || (best.active >= SHARE_UP_TO && pool.length < MAX_CONNECTIONS)) return null;
  return best;
}

// An HTTP/2 connection over a socket that has just agreed on h2: into the pool, unless the pool is full, in which
// case it serves the request that opened it and then closes.
function adopt(key: string, target: Target, socket: net.Socket): Pooled {
  const session = http2.connect(`https://${authorityOf(target)}`, {
    createConnection: () => socket,
    // Large receive windows: with HTTP/2's default 64 KB a 3 MB image would take dozens of round trips to arrive.
    settings: { enablePush: false, initialWindowSize: 8 << 20 },
    maxSessionMemory: 64,
  });
  const pooled: Pooled = { session, active: 0, idleSince: Date.now(), heard: Date.now(), closing: false };
  // A broken connection ends its requests with their own errors; the connection's error needs no handling of its own.
  session.on("error", () => {});
  session.once("connect", () => { try { session.setLocalWindowSize(32 << 20); } catch { /* the default window still works */ } });
  session.once("goaway", () => { pooled.closing = true; });
  const timer = setInterval(() => {
    if (session.closed || session.destroyed || session.connecting) return;
    if (pooled.active === 0 && Date.now() - pooled.idleSince > IDLE_MS) { pooled.closing = true; session.close(); return; }
    if (pooled.active > 0 && Date.now() - pooled.heard > SILENT_MS) { session.destroy(new Error("upstream connection went silent")); return; }
    try { session.ping((error) => { if (!error) pooled.heard = Date.now(); }); } catch { /* closing */ }
  }, PING_MS);
  timer.unref();
  session.once("close", () => {
    clearInterval(timer);
    const pool = pools.get(key);
    if (pool) pools.set(key, pool.filter((other) => other !== pooled));
  });
  const pool = (pools.get(key) ?? []).filter(usable);
  if (pool.length >= MAX_CONNECTIONS) pooled.closing = true;
  else pools.set(key, [...pool, pooled]);
  return pooled;
}

function onHttp2(pooled: Pooled, target: Target, out: Outgoing, signal: AbortSignal, reused: boolean, connectMs: number): Promise<Omit<Answer, "retries">> {
  const headers: http2.OutgoingHttpHeaders = { ":method": out.method, ":path": out.path, ":scheme": "https", ":authority": String(out.headers.host ?? authorityOf(target)) };
  for (const [name, value] of Object.entries(out.headers)) if (!HOP_BY_HOP.has(name) && !NOT_IN_H2.has(name)) headers[name] = value;
  let stream: http2.ClientHttp2Stream;
  // The connection would not take a new request (it is closing): nothing was sent.
  try { stream = pooled.session.request(headers, { endStream: !out.body?.length }); } catch (error) { pooled.closing = true; return Promise.reject(retryable(error)); }
  pooled.active++;
  const cancel = () => { if (!stream.closed) stream.close(NGHTTP2_CANCEL); };
  signal.addEventListener("abort", cancel, { once: true });
  stream.on("error", () => {});
  stream.once("close", () => {
    signal.removeEventListener("abort", cancel);
    pooled.active--;
    pooled.idleSince = Date.now();
    if (pooled.closing && pooled.active === 0 && !pooled.session.closed) pooled.session.close();
  });
  return new Promise((resolve, reject) => {
    stream.once("response", (received) => {
      pooled.heard = Date.now();
      const back: Record<string, string | string[]> = {};
      for (const [name, value] of Object.entries(received)) if (!name.startsWith(":") && value !== undefined && !HOP_BY_HOP.has(name)) back[name] = value as string | string[];
      // When the connection under a stream dies, Node ends the stream's body as if it were complete (checked
      // 2026-11-22): the close code then says CANCEL, or NO_ERROR when the server had announced it was closing the
      // connection. What differs is that at the end of a complete answer Node still holds the stream's state, and it is
      // already gone when the connection died; with a content-length, the bytes counted say it too. So the body handed
      // on ends only for a complete answer; otherwise it breaks off, and the client sees a broken answer instead of a cut
      // one passed off as whole.
      const body = new PassThrough();
      body.on("error", () => {});
      let bytes = 0;
      let endedWithState = false;
      stream.on("data", (chunk: Buffer) => { bytes += chunk.length; });
      stream.once("end", () => { endedWithState = Object.keys(stream.state ?? {}).length > 0; });
      stream.pipe(body, { end: false });
      const status = Number(received[HTTP2_HEADER_STATUS]);
      const declared = out.method !== "HEAD" && status !== 204 && status !== 304 && back["content-length"] !== undefined ? Number(back["content-length"]) : NaN;
      stream.once("close", () => {
        const whole = Number.isFinite(declared) ? bytes === declared : endedWithState;
        if (stream.rstCode === NGHTTP2_NO_ERROR && stream.readableEnded && whole) body.end();
        else body.destroy(new Error(`upstream answer broke off (HTTP/2 code ${stream.rstCode}, ${bytes} bytes)`));
      });
      resolve({ status, headers: back, body, proto: "h2", reused, connectMs, cancel });
    });
    // A refused stream (also one past the last a closing connection accepted) never reached the service.
    const failed = (error: Error) => reject(stream.rstCode === NGHTTP2_REFUSED_STREAM ? retryable(error) : error);
    stream.once("error", failed);
    stream.once("close", () => failed(new Error(`upstream closed the request (HTTP/2 code ${stream.rstCode ?? "none"})`)));
    if (out.body?.length) stream.end(out.body);
  });
}

function onHttp1(socket: net.Socket, target: Target, out: Outgoing, signal: AbortSignal, connectMs: number): Promise<Omit<Answer, "retries">> {
  return new Promise((resolve, reject) => {
    // No `agent` option: with agent:false Node ignores createConnection and dials the host directly.
    const outbound = http.request({ host: target.host, method: out.method, path: out.path, headers: out.headers, createConnection: () => socket }, (answer) => {
      const back: Record<string, string | string[]> = {};
      for (const [name, value] of Object.entries(answer.headers)) if (value !== undefined && !HOP_BY_HOP.has(name)) back[name] = value;
      answer.on("error", () => {});
      resolve({ status: answer.statusCode ?? 0, headers: back, body: answer, proto: "http/1.1", reused: false, connectMs, cancel: () => outbound.destroy() });
    });
    outbound.on("error", reject);
    const cancel = () => outbound.destroy();
    signal.addEventListener("abort", cancel, { once: true });
    outbound.once("close", () => signal.removeEventListener("abort", cancel));
    outbound.end(out.body ?? undefined);
  });
}

// Tests: the open connections, and closing them all.
export const openConnections = () => [...pools.values()].reduce((sum, pool) => sum + pool.filter(usable).length, 0);
export function closeConnections(): void {
  for (const pool of pools.values()) for (const pooled of pool) pooled.session.destroy();
  pools.clear();
  http1Until.clear();
}
