// Purpose: v0.11 — Cherry Studio (a desktop chat client for many models): the core alone, no panel. Each model provider
// has its own "API 地址" (API host) in Cherry Studio's settings, to which it adds the format's path (/v1/chat/completions,
// /v1/messages, …); so the route is registered with that host as shown there (`--base-url`), and the same host replaced
// by the route's address gets the same path added. Its settings live in the app, not in a file this tool writes, and
// it runs no shell commands of its own, so the steps are printed for the user. Its requests name no session the engine
// knows, so conversations are told apart by their first prompt. Not tested live.
// Input: none. Output: the platform's entry (core/platform.ts).

import { MCP_NAME, type CorePlatform } from "../../core/platform.ts";

export const cherryStudio: CorePlatform = {
  name: "cherry-studio",
  title: "Cherry Studio",
  upstream: null,
  connect: ({ url, mcp }) => [
    `Run this with --base-url set to the API host your provider shows in Cherry Studio (Settings > Model Provider), then put ${url} in that same field`,
    `In Settings > MCP Servers, add a server: type stdio, name ${MCP_NAME}, command ${mcp.command}, arguments ${mcp.args.join(" ")}, environment ${Object.entries(mcp.env).map(([name, value]) => `${name}=${value}`).join(" ")}; turn it on in the chats you use`,
    "Start a new conversation.",
  ],
};
