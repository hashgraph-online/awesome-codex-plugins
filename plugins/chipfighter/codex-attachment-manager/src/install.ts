// Purpose: P3-4 — what installing and uninstalling change, as pure functions over the current file contents:
// config.toml gets the proxy settings; ~/.codex/.env gets NO_PROXY only when the user's environment proxy would
// otherwise swallow requests to this machine. Uninstall removes exactly those blocks.
// P5 — the MCP server now comes with the plugin, which Codex's own command line installs (see cam.ts); an MCP server
// block left by an earlier install is removed here. v0.1-14 — notes in the system language (the command line's reader).
// Input: current texts and the user's persisted proxy variables. Output: next texts (envText null = delete the file).

import { coversLoopback, disableMcpServer, disableProxy, enableNoProxy, enableProxy, noProxyValue } from "./codexconfig.ts";
import { systemLang } from "./language.ts";
import { say } from "./messages.ts";

export const PLUGIN = "codex-attachment-manager";
export const MARKETPLACE = "codex-attachment-manager";
export const PLUGIN_ID = `${PLUGIN}@${MARKETPLACE}`;
// The MCP server's name, in the plugin's .mcp.json and in config.toml blocks written before P5.
export const SERVER_NAME = "codex_attachment_manager";

export type UserProxyEnv = { httpProxy: string | null; noProxy: string | null };
export type Plan = { configText: string; configChanged: boolean; envText: string | null; envChanged: boolean; notes: string[] };

// Codex's image client follows the environment proxy; without NO_PROXY for loopback it cannot reach the engine.
export function needsNoProxy(env: UserProxyEnv): boolean {
  return !!env.httpProxy && !coversLoopback(env.noProxy);
}

export function planInstall(input: { configText: string; envText: string | null; env: UserProxyEnv; port: number }): Plan {
  const notes: string[] = [];
  const proxied = enableProxy(input.configText, `http://localhost:${input.port}/backend-api/codex`);
  const legacy = disableMcpServer(proxied.text);
  if (legacy.changed) notes.push(say(systemLang(), "note.legacyMcp"));
  let envText = input.envText;
  let envChanged = false;
  if (needsNoProxy(input.env)) {
    const next = enableNoProxy(input.envText ?? "", noProxyValue(input.env.noProxy));
    envText = next.text;
    envChanged = next.changed;
    notes.push(say(systemLang(), "note.noProxy"));
  } else {
    // A block from an earlier install is no longer needed.
    const cleared = input.envText === null ? { text: null, changed: false } : disableProxy(input.envText);
    envText = cleared.text;
    envChanged = cleared.changed;
  }
  return { configText: legacy.text, configChanged: legacy.text !== input.configText, envText: emptyToNull(envText), envChanged, notes };
}

export function planUninstall(input: { configText: string; envText: string | null }): Plan {
  const config = disableMcpServer(disableProxy(input.configText).text);
  const env = input.envText === null ? { text: null, changed: false } : disableProxy(input.envText);
  return { configText: config.text, configChanged: config.text !== input.configText, envText: emptyToNull(env.text), envChanged: env.changed, notes: [] };
}

// What config.toml says about our marketplace and plugin (Codex writes both; we only read them).
export function pluginStatus(configText: string): { marketplace: string | null; installed: boolean; enabled: boolean } {
  const lines = configText.replace(/^﻿/, "").split(/\r?\n/);
  const table = (header: string) => {
    const start = lines.findIndex((line) => line.trim() === header);
    if (start < 0) return null;
    const end = lines.findIndex((line, index) => index > start && /^\s*\[/.test(line));
    return lines.slice(start + 1, end < 0 ? undefined : end);
  };
  const value = (body: string[] | null, key: string) => {
    const line = body?.find((candidate) => new RegExp(`^\\s*${key}\\s*=`).test(candidate));
    return line ? line.slice(line.indexOf("=") + 1).trim().replace(/^['"]|['"]$/g, "") : null;
  };
  const marketplace = table(`[marketplaces.${MARKETPLACE}]`);
  const plugin = table(`[plugins."${PLUGIN_ID}"]`);
  return { marketplace: marketplace ? value(marketplace, "source") : null, installed: plugin !== null, enabled: plugin !== null && value(plugin, "enabled") !== "false" };
}

// A .env that held nothing but our block is removed rather than left empty.
function emptyToNull(text: string | null): string | null {
  return text === null || !text.replace(/^﻿/, "").trim() ? null : text;
}
