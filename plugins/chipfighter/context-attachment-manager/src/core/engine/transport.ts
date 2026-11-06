// Purpose: the engine's way to the services, whatever the platform (v0.11: split from proxy.ts, docs/v0.11/plan.md):
// the outbound proxy (HTTPS_PROXY/HTTP_PROXY, else the system setting on Windows and macOS; NO_PROXY honoured per
// upstream host), a TLS connection through it, request bodies decoded and encoded again (zstd, gzip, br), the guard
// against integers JSON cannot carry, the log (metadata only), and whether a request comes from this machine's own
// pages.
// Output: sockets, buffers; <data dir>/proxy/<date>.jsonl.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { appendFileSync, mkdirSync } from "node:fs";
import type { IncomingHttpHeaders } from "node:http";
import net from "node:net";
import { join } from "node:path";
import tls from "node:tls";
import zlib from "node:zlib";
import { proxyLogDirOf } from "../paths.ts";

type Json = Record<string, any>;
export const HOP_BY_HOP = new Set(["connection", "keep-alive", "proxy-connection", "transfer-encoding", "te", "trailer", "upgrade", "host"]);

// Outbound proxy: environment first, then the system setting (Windows per-user, macOS); NO_PROXY is honoured for the
// upstream host.
export function outboundProxy(env = process.env, systemSetting = readSystemProxy, upstream = ""): { host: string; port: number } | null {
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

export function readSystemProxy(): string | null {
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

export function connectUpstream(via: { host: string; port: number } | null, upstream: string, signal?: AbortSignal, port = 443, secure = true): Promise<net.Socket> {
  const startTls = (socket?: net.Socket) => new Promise<net.Socket>((ok, fail) => {
    if (!secure) {
      if (socket) { ok(socket); return; }
      const plain = net.connect({ host: upstream, port, signal }, () => ok(plain));
      plain.once("error", fail);
      return;
    }
    const cleanup = () => signal?.removeEventListener("abort", abort);
    const connection = tls.connect({ socket, host: socket ? undefined : upstream, port, servername: net.isIP(upstream) ? undefined : upstream, ALPNProtocols: ["http/1.1"] }, () => { cleanup(); ok(connection); });
    const abort = () => { cleanup(); connection.destroy(); socket?.destroy(); fail(new Error("upstream connection cancelled")); };
    connection.once("error", (error) => { cleanup(); fail(error); });
    signal?.addEventListener("abort", abort, { once: true });
    if (signal?.aborted) abort();
  });
  if (!via) return startTls();
  return new Promise((ok, fail) => {
    const authority = `${upstream.includes(":") ? `[${upstream}]` : upstream}:${port}`;
    const socket = net.connect({ port: via.port, host: via.host, signal }, () => socket.write(`CONNECT ${authority} HTTP/1.1\r\nHost: ${authority}\r\n\r\n`));
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

export function decodeBody(body: Buffer, encoding: string | undefined): Buffer | null {
  try {
    if (!encoding || encoding === "identity") return body;
    if (encoding === "zstd") return zlib.zstdDecompressSync(body);
    if (encoding === "gzip") return zlib.gunzipSync(body);
    if (encoding === "br") return zlib.brotliDecompressSync(body);
  } catch { /* fall through */ }
  return null;
}

export function log(entry: Json): void {
  const dir = proxyLogDirOf();
  mkdirSync(dir, { recursive: true });
  appendFileSync(join(dir, `${new Date().toISOString().slice(0, 10)}.jsonl`), `${JSON.stringify(entry)}\n`);
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

export function encodeBody(body: Buffer, encoding: string | undefined): Buffer {
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

const LOOPBACK_HOST = /^(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$/;
export function ownRequest(headers: IncomingHttpHeaders): boolean {
  const host = String(headers.host ?? "");
  if (!LOOPBACK_HOST.test(host)) return false;
  return headers.origin === undefined || headers.origin === `http://${host}`;
}
