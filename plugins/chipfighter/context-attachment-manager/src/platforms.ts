// Purpose: v0.11 — the platforms the plugin connects (docs/v0.11/plan.md 3.8; ADAPTERS.md). Codex and Claude Code have
// adapters of their own, with the panel (adapters/codex, adapters/claude). The others use the core alone: their entry
// (core/platform.ts) is all the engine, the plugin's MCP service and `cam connect` need. A new platform adds its
// adapters/<name>/platform.ts and one line here. DeepSeek Harness is a dsh plugin of its own (adapters/dsh), no route,
// so it is not in CORE_PLATFORMS; `cam detect` still names it.
// Input: none. Output: the registry, and which platform a shell command runs in.

import { cherryStudio } from "./adapters/cherry-studio/platform.ts";
import { cline } from "./adapters/cline/platform.ts";
import { geminiCli } from "./adapters/gemini-cli/platform.ts";
import { goose } from "./adapters/goose/platform.ts";
import { kiloCode } from "./adapters/kilo-code/platform.ts";
import { opencode } from "./adapters/opencode/platform.ts";
import { pi } from "./adapters/pi/platform.ts";
import { qwenCode } from "./adapters/qwen-code/platform.ts";
import { workbuddy } from "./adapters/workbuddy/platform.ts";
import type { CorePlatform } from "./core/platform.ts";

export const CORE_PLATFORMS: CorePlatform[] = [workbuddy, opencode, geminiCli, pi, qwenCode, cline, kiloCode, cherryStudio, goose];
export const PANEL_PLATFORMS = ["codex", "claude"] as const;

export const corePlatformOf = (name: string | null | undefined): CorePlatform | null => CORE_PLATFORMS.find((platform) => platform.name === name) ?? null;
export const isPlatform = (name: unknown): name is string => typeof name === "string" && ((PANEL_PLATFORMS as readonly string[]).includes(name) || !!corePlatformOf(name));

// v0.11: the variables each platform sets for the shell commands its agent runs (checked in each one's code,
// 2026-11-02): Codex CODEX_THREAD_ID, Claude Code CLAUDECODE=1, DeepSeek Harness DSH_SHELL=1, and the core platforms'
// own (their `detect`). An agent started from another's shell carries both; then the user is asked.
const SIGNALS: Array<{ platform: string; test: (env: NodeJS.ProcessEnv) => boolean }> = [
  ...CORE_PLATFORMS.flatMap((platform) => (platform.detect ? [{ platform: platform.name, test: platform.detect }] : [])),
  { platform: "dsh", test: (env) => env.DSH_SHELL === "1" },
  { platform: "claude", test: (env) => env.CLAUDECODE === "1" },
  { platform: "codex", test: (env) => !!env.CODEX_THREAD_ID },
];

// The platform when exactly one matches; `codebuddy` names CodeBuddy's agent outside WorkBuddy, which has no adapter.
export function detectPlatform(env: NodeJS.ProcessEnv = process.env): { platform: string | null; matches: string[] } {
  const matches = SIGNALS.filter((signal) => signal.test(env)).map((signal) => signal.platform);
  if (env.CODEBUDDY === "1" && !matches.includes("workbuddy")) matches.push("codebuddy");
  return { platform: matches.length === 1 && matches[0] !== "codebuddy" ? matches[0] : null, matches };
}
