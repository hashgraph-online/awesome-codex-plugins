// Purpose: P5 — find and run Codex's own command line, which registers marketplaces and installs or removes plugins
// (copying them into Codex's plugin cache). The desktop app ships one; a codex installed on its own is the fallback.
// v0.1: macOS and Linux as well.
// Input: CODEX_CLI_PATH; the desktop app's copy (Windows: %LOCALAPPDATA%\OpenAI\Codex\bin\<build>\codex.exe, macOS:
// <app>/Contents/Resources/codex); ~/.local/bin/codex (Codex's own installer); PATH.
// Output: the command's exit status and its combined output (Codex prints no secrets for these commands).

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

// Where a desktop app or Codex's installer puts the command line, most specific first. The Linux desktop app sets
// CODEX_CLI_PATH for the plugins it starts; from a terminal it is found on PATH.
export function cliCandidates(env: NodeJS.ProcessEnv = process.env, platform: NodeJS.Platform = process.platform, home = homedir()): string[] {
  if (platform === "win32") {
    // The desktop app keeps one folder per build; the newest one belongs to the app that runs now.
    const root = join(env.LOCALAPPDATA || join(home, "AppData", "Local"), "OpenAI", "Codex", "bin");
    const builds = existsSync(root) ? readdirSync(root).map((name) => join(root, name, "codex.exe")).filter((file) => existsSync(file)) : [];
    return builds.sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
  }
  const apps = platform === "darwin" ? ["/Applications", join(home, "Applications")].flatMap((dir) => ["ChatGPT.app", "Codex.app"].map((app) => join(dir, app, "Contents", "Resources", "codex"))) : [];
  return [...apps, join(home, ".local", "bin", "codex")];
}

export function findCodexCli(env: NodeJS.ProcessEnv = process.env): string | null {
  if (env.CODEX_CLI_PATH && existsSync(env.CODEX_CLI_PATH)) return env.CODEX_CLI_PATH;
  const found = cliCandidates(env).find((file) => existsSync(file));
  if (found) return found;
  try {
    const windows = process.platform === "win32";
    const onPath = execFileSync(windows ? "where" : "which", ["codex"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    // On Windows, npm also leaves an extensionless shell script next to its codex.cmd.
    return onPath.split(/\r?\n/).map((line) => line.trim()).find((line) => line && (!windows || /\.(exe|cmd)$/i.test(line))) ?? null;
  } catch {
    return null;
  }
}

export function runCodex(cli: string, args: string[], env: NodeJS.ProcessEnv = process.env): { ok: boolean; output: string } {
  // An npm-installed codex on Windows is a .cmd shim, which only cmd.exe can start.
  const shim = /\.cmd$/i.test(cli);
  const result = spawnSync(shim ? "cmd.exe" : cli, shim ? ["/d", "/s", "/c", cli, ...args] : args, { encoding: "utf8", windowsHide: true, env });
  return { ok: result.status === 0, output: `${result.stdout ?? ""}${result.stderr ?? ""}`.trim() };
}
