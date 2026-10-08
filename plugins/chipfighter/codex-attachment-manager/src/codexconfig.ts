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

function parts(text: string): { bom: string; body: string; eol: string } {
  const bom = text.startsWith("﻿") ? "﻿" : "";
  const body = bom ? text.slice(1) : text;
  return { bom, body, eol: body.includes("\r\n") ? "\r\n" : "\n" };
}

const isTable = (line: string) => /^\s*\[/.test(line);

// TOML top-level keys end at the first table header; a second top-level key would be a duplicate.
function topLevelValue(lines: string[], key: string): string | null {
  for (const line of lines) {
    if (isTable(line)) return null;
    const match = line.match(new RegExp(`^\\s*${key.replaceAll(".", "\\.")}\\s*=\\s*(.+?)\\s*(#.*)?$`));
    if (match) return match[1];
  }
  return null;
}

function featuresHeader(lines: string[]): number {
  return lines.findIndex((line) => /^\s*\[features\]\s*(#.*)?$/.test(line));
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
  return removeBlocks(text, BEGIN);
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
export function enableProxy(text: string, url: string): { text: string; changed: boolean } {
  const { bom, body, eol } = parts(disableProxy(text).text);
  const lines = body.split(eol);
  if (topLevelValue(lines, "openai_base_url") !== null) throw conflict("config.toml already sets openai_base_url; not overwriting it", "conflict.baseUrl");
  const own = userRespectSystemProxy(lines);
  if (own !== null && own !== "true") throw conflict("config.toml turns respect_system_proxy off; not overriding it", "conflict.systemProxy");
  const header = featuresHeader(lines);
  const top = [BEGIN, `openai_base_url = "${url}"`];
  if (own === null && header < 0) top.push("features.respect_system_proxy = true");
  top.push(END, "");
  if (own === null && header >= 0) lines.splice(header + 1, 0, BEGIN, "respect_system_proxy = true", END);
  const next = bom + top.join(eol) + eol + lines.join(eol);
  return { text: next, changed: next !== text };
}

export function proxyStatus(text: string): { enabled: boolean; url: string | null; conflict: boolean; respectSystemProxy: "managed" | "user" | "off" | "absent" } {
  const { body, eol } = parts(text);
  const lines = body.split(eol);
  const enabled = lines.some((line) => line.trim() === BEGIN);
  const begin = lines.findIndex((line) => line.trim() === BEGIN);
  const urlLine = begin >= 0 ? lines.slice(begin).find((line) => /^\s*openai_base_url\s*=/.test(line)) : undefined;
  const base = parts(disableProxy(text).text);
  const baseLines = base.body.split(base.eol);
  const own = userRespectSystemProxy(baseLines);
  const managedRsp = enabled && lines.some((line, i) => /respect_system_proxy\s*=\s*true/.test(line) && lines.slice(0, i).reverse().find((l) => l.trim() === BEGIN || l.trim() === END)?.trim() === BEGIN);
  return {
    enabled,
    url: urlLine ? (/"([^"]*)"/.exec(urlLine)?.[1] ?? null) : null,
    conflict: topLevelValue(baseLines, "openai_base_url") !== null,
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
