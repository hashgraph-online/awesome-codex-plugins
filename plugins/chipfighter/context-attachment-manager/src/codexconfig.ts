// Purpose: P1-1 — point Codex's built-in openai provider at the local proxy by managing marked blocks
// in config.toml (openai_base_url and respect_system_proxy), and remove exactly those blocks again.
// P2 — also a marked NO_PROXY block in $CODEX_HOME/.env, which Codex loads at startup, so its image generation
// client (which ignores respect_system_proxy before upstream #47742) reaches the local proxy too.
// Nothing else in either file is touched.
// P5 — a library only: cam.ts install / uninstall / status use it, and do every write and backup themselves.
// Input: file texts. Codex home comes from CODEX_HOME or ~/.codex. Output: next texts and status.
// .env may hold credentials: it is never copied or printed, and its block is removed byte-exactly.

import { execFileSync } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

// v0.1-14: a conflict with the user's settings carries a message key (messages.ts), so the panel and the command line
// can say it in the user's language; the message itself stays English for logs.
const conflict = (message: string, key: string, vars: Record<string, string> = {}) => Object.assign(new Error(message), { key, vars });

export const BEGIN = "# >>> codex-attachment-manager: managed proxy setting, remove it with the tool >>>";
export const END = "# <<< codex-attachment-manager <<<";
// Original endpoint lines stay in config.toml, beside their temporary local route. No credentials are copied.
export const UPSTREAM_BEGIN = "# >>> codex-attachment-manager: managed upstream setting >>>";

function parts(text: string): { bom: string; body: string; eol: string } {
  const bom = text.startsWith("﻿") ? "﻿" : "";
  const body = bom ? text.slice(1) : text;
  return { bom, body, eol: body.includes("\r\n") ? "\r\n" : "\n" };
}

const isTable = (line: string) => /^\s*\[/.test(line);

// TOML top-level keys end at the first table header; a second top-level key would be a duplicate.
function topLevelValue(lines: string[], key: string): string | null {
  let multiline: string | null = null;
  for (const line of lines) {
    const inside = multiline !== null;
    const scanned = scanLine(line, multiline);
    multiline = scanned.multiline;
    if (inside) continue;
    if (isTable(scanned.code)) return null;
    const match = scanned.code.match(new RegExp(`^\\s*${key.replaceAll(".", "\\.")}\\s*=\\s*(.+?)\\s*$`));
    if (match) return match[1];
  }
  return null;
}

function featuresHeader(lines: string[]): number {
  let multiline: string | null = null;
  for (let i = 0; i < lines.length; i++) {
    const inside = multiline !== null;
    const scanned = scanLine(lines[i], multiline);
    multiline = scanned.multiline;
    if (!inside && /^\s*\[features\]\s*$/.test(scanned.code)) return i;
  }
  return -1;
}

// The user's own respect_system_proxy, as a top-level dotted key or inside [features]; null when absent.
function userRespectSystemProxy(lines: string[]): string | null {
  const dotted = topLevelValue(lines, "features.respect_system_proxy");
  if (dotted !== null) return dotted;
  const header = featuresHeader(lines);
  if (header < 0) return null;
  for (const line of lines.slice(header + 1)) {
    if (isTable(line)) break;
    const match = /^\s*respect_system_proxy\s*=\s*(\S+)/.exec(line);
    if (match) return match[1];
  }
  return null;
}

// P3: a local MCP server for the panel, as a table appended at the end of config.toml. Its own marker keeps it
// independent of the proxy blocks: each can be switched on and off alone.
export const MCP_BEGIN = "# >>> codex-attachment-manager: managed MCP server, remove it with the tool >>>";

// Removes every managed block; the blank line enable adds after the top block goes with it.
export function disableProxy(text: string): { text: string; changed: boolean } {
  const restored = restoreUpstreams(text);
  const removed = removeBlocks(restored, BEGIN);
  return { text: removed.text, changed: removed.text !== text };
}

type EndpointLine = { prefix: string; key: string[]; value: string; suffix: string };
type AssignmentLine = Omit<EndpointLine, "value"> & { rawValue: string };

function stringValue(text: string): string | null {
  if (/^'[^']*'$/.test(text)) return text.slice(1, -1);
  if (!/^"(?:[^"\\]|\\.)*"$/.test(text)) return null;
  try { return JSON.parse(text); } catch { return null; }
}

function keyPath(text: string): string[] | null {
  const path: string[] = [];
  let rest = text.trim();
  while (rest) {
    const key = /^(?:[A-Za-z0-9_-]+|"(?:[^"\\]|\\.)*"|'[^']*')/.exec(rest)?.[0];
    if (!key) return null;
    path.push(key[0] === '"' || key[0] === "'" ? stringValue(key)! : key);
    rest = rest.slice(key.length).trim();
    if (!rest) return path;
    if (rest[0] !== ".") return null;
    rest = rest.slice(1).trim();
    if (!rest) return null;
  }
  return null;
}

// Only scalar endpoint settings are edited, but surrounding multiline strings and comments must be recognized.
function scanLine(line: string, multiline: string | null): { code: string; multiline: string | null } {
  for (let i = 0; i < line.length; i++) {
    if (multiline) {
      const at = line.indexOf(multiline, i);
      if (at < 0) return { code: line, multiline };
      i = at + 2;
      multiline = null;
    } else if (line[i] === "#") return { code: line.slice(0, i), multiline };
    else if (line.startsWith('"""', i) || line.startsWith("'''", i)) { multiline = line.slice(i, i + 3); i += 2; }
    else if (line[i] === '"' || line[i] === "'") {
      const quote = line[i];
      while (++i < line.length) {
        if (quote === '"' && line[i] === "\\") i++;
        else if (line[i] === quote) break;
      }
    }
  }
  return { code: line, multiline };
}

function assignmentLine(line: string): AssignmentLine | null {
  const code = scanLine(line, null).code;
  // Find '=' outside quoted keys (a quoted provider name may itself contain '=').
  let equals = -1;
  let quote: string | null = null;
  for (let i = 0; i < code.length; i++) {
    if (quote) {
      if (quote === '"' && code[i] === "\\") i++;
      else if (code[i] === quote) quote = null;
    } else if (code[i] === '"' || code[i] === "'") quote = code[i];
    else if (code[i] === "=") { equals = i; break; }
  }
  if (equals < 0) return null;
  const key = keyPath(code.slice(0, equals));
  if (!key) return null;
  return { prefix: code.slice(0, equals + 1), key, rawValue: code.slice(equals + 1).trim(), suffix: line.slice(code.trimEnd().length) };
}

function endpointLine(line: string): EndpointLine | null {
  const assignment = assignmentLine(line);
  if (!assignment) return null;
  const value = stringValue(assignment.rawValue);
  if (value === null) return null;
  return { prefix: assignment.prefix, key: assignment.key, value, suffix: assignment.suffix };
}

function restoreUpstreams(text: string): string {
  const { bom, body, eol } = parts(text);
  const lines = body.split(eol);
  const kept: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() !== UPSTREAM_BEGIN) { kept.push(lines[i]); continue; }
    const end = lines.findIndex((line, at) => at > i && line.trim() === END);
    if (end < 0) throw conflict("a managed upstream setting has no end marker", "conflict.noEnd");
    let original: string;
    let managed: string;
    try {
      original = JSON.parse(lines[i + 1].replace(/^# original: /, ""));
      managed = JSON.parse(lines[i + 2].replace(/^# managed: /, ""));
      if (typeof original !== "string" || typeof managed !== "string") throw new Error("invalid metadata");
    } catch { throw conflict("a managed upstream setting has invalid metadata", "conflict.noEnd"); }
    const current = lines.slice(i + 3, end);
    const expected = endpointLine(managed);
    for (const line of current) {
      const actual = endpointLine(line);
      if (actual && expected && actual.value === expected.value && JSON.stringify(actual.key) === JSON.stringify(expected.key)) kept.push(original);
      else kept.push(line); // The user's changed endpoint or additional lines win.
    }
    i = end;
  }
  return bom + kept.join(eol);
}

function upstreamSettings(lines: string[], strict = false): { index: number; line: EndpointLine; topLevel: boolean }[] {
  const found: { index: number; line: EndpointLine; topLevel: boolean }[] = [];
  let table: string[] = [];
  let multiline: string | null = null;
  for (let i = 0; i < lines.length; i++) {
    const wasMultiline = multiline !== null;
    const scanned = scanLine(lines[i], multiline);
    multiline = scanned.multiline;
    if (wasMultiline) continue;
    // An array table also ends the preceding provider table; its entries are not provider settings.
    if (/^\s*\[\[/.test(scanned.code)) { table = ["<array-table>"]; continue; }
    const header = /^\s*\[([^\[].*)\]\s*$/.exec(scanned.code.trim());
    if (header) { table = keyPath(header[1]) ?? []; continue; }
    const assignment = assignmentLine(lines[i]);
    if (!assignment) continue;
    const path = [...table, ...assignment.key];
    const endpoint = (path.length === 1 && path[0] === "openai_base_url") || (path.length === 3 && path[0] === "model_providers" && path[2] === "base_url");
    const inlineProvider = path[0] === "model_providers" && path.length < 3;
    const line = endpoint ? endpointLine(lines[i]) : null;
    if (strict && (inlineProvider || (endpoint && !line))) throw conflict("unsupported provider endpoint syntax; use a single-line endpoint setting", "conflict.endpointSyntax");
    if (!line) continue;
    found.push({ index: i, line, topLevel: path.length === 1 });
  }
  return found;
}

function routeUpstreams(lines: string[], route: (upstream: string) => string): void {
  let added = 0;
  for (const { index, line } of upstreamSettings(lines)) {
    const i = index + added;
    const managed = `${line.prefix} ${JSON.stringify(route(line.value))}${line.suffix}`;
    const block = [UPSTREAM_BEGIN, `# original: ${JSON.stringify(lines[i])}`, `# managed: ${JSON.stringify(managed)}`, managed, END];
    lines.splice(i, 1, ...block);
    added += block.length - 1;
  }
}

export function disableMcpServer(text: string): { text: string; changed: boolean } {
  return removeBlocks(text, MCP_BEGIN);
}

export function enableMcpServer(text: string, name: string, command: string, args: string[]): { text: string; changed: boolean } {
  const { bom, body, eol } = parts(disableMcpServer(text).text);
  if (body.split(eol).some((line) => line.trim() === `[mcp_servers.${name}]`)) throw conflict(`config.toml already defines mcp_servers.${name}; not overwriting it`, "conflict.mcpServer", { name });
  // JSON string syntax is valid TOML basic-string syntax, including backslashes in Windows paths.
  const block = [MCP_BEGIN, `[mcp_servers.${name}]`, `command = ${JSON.stringify(command)}`, `args = ${JSON.stringify(args)}`, 'default_tools_approval_mode = "approve"', END];
  const next = bom + body + (body === "" || body.endsWith(eol) ? "" : eol) + block.join(eol) + eol;
  return { text: next, changed: next !== text };
}

function removeBlocks(text: string, begin: string): { text: string; changed: boolean } {
  const { bom, body, eol } = parts(text);
  const lines = body.split(eol);
  const kept: string[] = [];
  let changed = false;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim() !== begin) { kept.push(lines[i]); continue; }
    const end = lines.findIndex((line, j) => j > i && line.trim() === END);
    if (end < 0) throw conflict("a managed block in config.toml has no end marker", "conflict.noEnd");
    const atTop = kept.length === 0;
    i = end;
    if (atTop && lines[i + 1] === "") i++;
    changed = true;
  }
  return changed ? { text: bom + kept.join(eol), changed } : { text, changed: false };
}

// Codex needs two settings to reach the proxy on Windows: openai_base_url (top level, so it goes first in the
// file) and features.respect_system_proxy, without which Codex sends even localhost through HTTP(S)_PROXY.
export function enableProxy(text: string, url: string, routeBaseUrl?: (upstream: string) => string): { text: string; changed: boolean } {
  const { bom, body, eol } = parts(disableProxy(text).text);
  const lines = body.split(eol);
  // Validate every relevant assignment before registering any route or emitting a managed config block.
  if (routeBaseUrl) upstreamSettings(lines, true);
  const customBaseUrl = topLevelValue(lines, "openai_base_url") !== null || upstreamSettings(lines).some((setting) => setting.topLevel);
  if (customBaseUrl && !routeBaseUrl) throw conflict("config.toml already sets openai_base_url; not overwriting it", "conflict.baseUrl");
  const own = userRespectSystemProxy(lines);
  if (own !== null && own !== "true") throw conflict("config.toml turns respect_system_proxy off; not overriding it", "conflict.systemProxy");
  const header = featuresHeader(lines);
  const top = [BEGIN];
  if (!customBaseUrl) top.push(`openai_base_url = "${url}"`);
  if (own === null && header < 0) top.push("features.respect_system_proxy = true");
  top.push(END, "");
  if (own === null && header >= 0) lines.splice(header + 1, 0, BEGIN, "respect_system_proxy = true", END);
  if (routeBaseUrl) routeUpstreams(lines, routeBaseUrl);
  const next = bom + top.join(eol) + eol + lines.join(eol);
  return { text: next, changed: next !== text };
}

export function proxyStatus(text: string): { enabled: boolean; url: string | null; conflict: boolean; respectSystemProxy: "managed" | "user" | "off" | "absent" } {
  const { body, eol } = parts(text);
  const lines = body.split(eol);
  const enabled = lines.some((line) => line.trim() === BEGIN);
  const begin = lines.findIndex((line) => line.trim() === BEGIN);
  const endpoint = enabled ? upstreamSettings(lines).find((setting) => setting.topLevel)?.line.value : null;
  const base = parts(disableProxy(text).text);
  const baseLines = base.body.split(base.eol);
  const own = userRespectSystemProxy(baseLines);
  const managedRsp = enabled && lines.some((line, i) => /respect_system_proxy\s*=\s*true/.test(line) && lines.slice(0, i).reverse().find((l) => l.trim() === BEGIN || l.trim() === END)?.trim() === BEGIN);
  return {
    enabled,
    url: endpoint ?? null,
    conflict: !enabled && (topLevelValue(baseLines, "openai_base_url") !== null || upstreamSettings(baseLines).some((setting) => setting.topLevel)),
    respectSystemProxy: managedRsp ? "managed" : own === "true" ? "user" : own !== null ? "off" : "absent",
  };
}

const LOOPBACK = ["localhost", "127.0.0.1", "::1"];
const NO_PROXY_LINE = /^\s*(export\s+)?no_proxy\s*=/i;

// The user's own NO_PROXY entries are kept, because the .env value replaces the variable inside Codex.
export function noProxyValue(existing: string | null): string {
  const entries = (existing ?? "").split(",").map((entry) => entry.trim()).filter(Boolean);
  for (const host of LOOPBACK) if (!entries.some((entry) => entry.toLowerCase() === host)) entries.push(host);
  return entries.join(",");
}

export function coversLoopback(value: string | null): boolean {
  const entries = (value ?? "").split(",").map((entry) => entry.trim().toLowerCase());
  return entries.includes("*") || LOOPBACK.every((host) => entries.includes(host));
}

// The block goes first, like in config.toml, so disableProxy removes it and the blank line after it.
export function enableNoProxy(text: string, value: string): { text: string; changed: boolean } {
  const { bom, body, eol } = parts(disableProxy(text).text);
  if (body.split(eol).some((line) => NO_PROXY_LINE.test(line))) throw conflict(".env already sets NO_PROXY; not overriding it", "conflict.noProxy");
  const next = bom + [BEGIN, `NO_PROXY=${value}`, END, ""].join(eol) + eol + body;
  return { text: next, changed: next !== text };
}

export function noProxyStatus(text: string): { managed: boolean; value: string | null; conflict: boolean } {
  const lines = parts(text).body.split(parts(text).eol);
  const begin = lines.findIndex((line) => line.trim() === BEGIN);
  const line = begin >= 0 ? lines.slice(begin).find((l) => NO_PROXY_LINE.test(l)) : undefined;
  const base = parts(disableProxy(text).text);
  return { managed: begin >= 0, value: line ? line.slice(line.indexOf("=") + 1).trim() : null, conflict: base.body.split(base.eol).some((l) => NO_PROXY_LINE.test(l)) };
}

// What the desktop app inherits: on Windows the user's variable overrides the machine's. On macOS and Linux there is
// no such store; the environment of the shell that runs the command is the closest guess (v0.1).
export function persistedEnv(name: string): string | null {
  if (process.platform !== "win32") return process.env[name] || process.env[name.toLowerCase()] || null;
  for (const key of ["HKCU\\Environment", "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment"]) {
    try {
      const out = execFileSync("reg", ["query", key, "/v", name], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
      const match = out.match(new RegExp(`${name}\\s+REG_(?:EXPAND_)?SZ\\s+(.*)`, "i"));
      if (match) return match[1].trim();
    } catch { /* not set at this level */ }
  }
  return null;
}

export function codexHome(): string {
  return process.env.CODEX_HOME?.trim() || join(homedir(), ".codex");
}
