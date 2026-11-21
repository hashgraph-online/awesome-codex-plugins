// Purpose: v0.11 — what a platform's adapter tells the engine when the platform uses the core alone, without a panel
// (docs/v0.11/plan.md 3.8; ADAPTERS.md): its name, where its requests go, how its requests name their session, which
// of them are on the side, and what the user does to connect it. Everything else — which request format, which images,
// what is left out — the core and the request-format translators work out from the requests themselves.
// Input: none (types only). Output: the contract each adapters/<name>/platform.ts fills in.

import type { IncomingHttpHeaders } from "node:http";
import type { ConfigEdit } from "./config-edit.ts";

export type ConnectInfo = {
  // The local address the platform is pointed at, and the command that starts the plugin's MCP service for it.
  url: string;
  mcp: { command: string; args: string[]; env: Record<string, string> };
};

// v0.11: what `cam connect --apply` needs, read from the platform's own settings now. current: the address its
// requests go to as set now (a route of ours, when connected before), fallback: where they go when nothing is set.
// edits: what to write (core/config-edit.ts). provider: for a platform with one address per model provider, the one
// the user named (or the platform's shell said).
export type SetupContext = { home: string; env: NodeJS.ProcessEnv; provider: string | null };
// manual: why the settings are only printed, not written (a format this tool does not write, such as YAML).
export type SetupPlan = { current: string | null; fallback: string | null; edits: (info: ConnectInfo) => ConfigEdit[]; note?: string; manual?: string };

// The name of the plugin's MCP server in a platform's settings.
export const MCP_NAME = "context-attachment-manager";

export type CorePlatform = {
  // As in routes and data folders: lowercase letters, digits, hyphens.
  name: string;
  title: string;
  // Where its model requests go without the plugin, unless the user names another (`cam connect <name> --base-url`).
  upstream: string | null;
  // The session a request belongs to, from the platform's own headers. Without one the engine takes the `x-cam-session`
  // header a shim of ours may add, else tells sessions apart by their first prompt.
  sessionOf?: (headers: IncomingHttpHeaders) => string | null;
  // Requests the platform sends on the side (a title, a prompt suggestion): passed on as they are.
  sideRequest?: (headers: IncomingHttpHeaders) => boolean;
  // What the user does to connect it, one step per line (English, as in ADAPTERS.md).
  connect: (info: ConnectInfo) => string[];
  // v0.11: whether a shell command runs inside this platform, from the variables the platform sets for it (`cam
  // detect`, so an AI installing the plugin picks the right platform).
  detect?: (env: NodeJS.ProcessEnv) => boolean;
  // v0.11: the settings `cam connect --apply` writes; without it the steps are only printed.
  setup?: (context: SetupContext) => SetupPlan;
};

export const headerOf = (headers: IncomingHttpHeaders, name: string): string | null => {
  const value = headers[name];
  return (Array.isArray(value) ? value[0] : value) || null;
};
