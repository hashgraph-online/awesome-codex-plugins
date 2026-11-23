// Purpose: v0.13 — keeping the plugin up to date in Claude Code (core/update.ts), with Claude Code's own command line:
// `claude plugin marketplace update` refreshes its copy of this repository, whose marketplace.json names the release
// to install (the plugin's source is this repository's HTTPS address at a release tag, moved at every release,
// docs/design.md section 13), and `claude plugin update` installs it. New sessions use it; running ones keep theirs.
// The address is HTTPS, not a "github" source: Claude Code clones that over SSH wherever the user's GitHub key works,
// and SSH straight to GitHub stalled on a machine whose HTTPS goes through a proxy (2026-11-23). Claude Code can update
// plugins by itself, but Claude Desktop turns that off for the sessions it starts (DISABLE_AUTOUPDATER=1, seen
// 2026-11-23), and those are where the panel is.
// Installed another way (a local folder, another repository, another scope than the user's) it is left alone.
// Input: `claude plugin list / marketplace list / marketplace update / update`. Output: Claude Code's plugin cache.

import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { failure, isOurRepo, jsonOf, runCommand, type Installed, type Platform, type Release } from "../../core/update.ts";

const MARKETPLACE = "codex-attachment-manager";
const PLUGIN_ID = `codex-attachment-manager@${MARKETPLACE}`;

// Claude Code's command line: the one on PATH, the native installer's, or the copy Claude Desktop keeps for its sessions.
export function findClaudeCli(env: NodeJS.ProcessEnv = process.env, platform: NodeJS.Platform = process.platform, home = homedir()): string | null {
  if (env.CAM_CLAUDE_CLI) return existsSync(env.CAM_CLAUDE_CLI) ? env.CAM_CLAUDE_CLI : null;
  const windows = platform === "win32";
  try {
    const found = execFileSync(windows ? "where" : "which", ["claude"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"], windowsHide: true, timeout: 5000, env });
    const line = found.split(/\r?\n/).map((each) => each.trim()).find((each) => each && (!windows || /\.(exe|cmd)$/i.test(each)));
    if (line) return line;
  } catch { /* not on PATH */ }
  const native = join(home, ".local", "bin", windows ? "claude.exe" : "claude");
  if (existsSync(native)) return native;
  // Claude Desktop on Windows: <LOCALAPPDATA>/Claude-Data/<id>/claude-code/<version>/<build>/claude.exe, newest first.
  const data = windows && env.LOCALAPPDATA ? join(env.LOCALAPPDATA, "Claude-Data") : null;
  if (data && existsSync(data)) {
    const found: string[] = [];
    const dirs = (dir: string) => { try { return readdirSync(dir, { withFileTypes: true }).filter((entry) => entry.isDirectory()).map((entry) => join(dir, entry.name)); } catch { return []; } };
    for (const profile of dirs(data)) for (const version of dirs(join(profile, "claude-code"))) for (const build of dirs(version)) if (existsSync(join(build, "claude.exe"))) found.push(join(build, "claude.exe"));
    found.sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
    if (found[0]) return found[0];
  }
  return null;
}

// The command line runs as a program of its own, not as part of the session the plugin service belongs to: the
// variables that tie a process to a session are left out; the rest (CLAUDE_CONFIG_DIR, the Git Bash path, a proxy)
// stays.
const SESSION_VARIABLES = /^(CLAUDECODE|CLAUDE_PID|CLAUDE_CODE_(SESSION_ID|ENTRYPOINT|CHILD_SESSION|MESSAGING_SOCKET|HOST_SESSION_ID|SESSION_ATTENDED|CHILD_NOTES_DIR)|CLAUDE_AGENT_SDK_\w+|CAM_HOST)$/;
export function cliEnv(env: NodeJS.ProcessEnv): NodeJS.ProcessEnv {
  return Object.fromEntries(Object.entries(env).filter(([name]) => !SESSION_VARIABLES.test(name)));
}

export function claudePlatform(options: { env?: NodeJS.ProcessEnv; cli?: string | null; anySource?: boolean } = {}): Platform {
  const env = options.env ?? process.env;
  const cli = () => options.cli ?? findClaudeCli(env);
  const claude = async (args: string[], what: string) => {
    const command = cli();
    if (!command) throw new Error("no Claude Code command line");
    const ran = await runCommand(command, args, { env: cliEnv(env) });
    if (!ran.ok) throw failure(`claude ${what}`, ran);
    return ran;
  };
  const installedVersion = async (): Promise<string | null> => {
    const listed = jsonOf((await claude(["plugin", "list", "--json"], "plugin list")).stdout);
    const plugins: any[] = Array.isArray(listed) ? listed : listed.plugins ?? listed.installed ?? [];
    const entry = plugins.find((plugin) => plugin?.id === PLUGIN_ID && (plugin.scope ?? "user") === "user");
    return typeof entry?.version === "string" ? entry.version : null;
  };
  return {
    host: "claude",
    async inspect(): Promise<Installed> {
      if (!cli()) return { eligible: false, reason: "no Claude Code command line" };
      const version = await installedVersion();
      if (!version) return { eligible: false, reason: "not installed for the user in Claude Code" };
      const listed = jsonOf((await claude(["plugin", "marketplace", "list", "--json"], "plugin marketplace list")).stdout);
      const marketplaces: any[] = Array.isArray(listed) ? listed : listed.marketplaces ?? [];
      const marketplace = marketplaces.find((entry) => entry?.name === MARKETPLACE);
      const ours = marketplace && (isOurRepo(marketplace.repo) || isOurRepo(marketplace.url));
      if (!options.anySource && !ours) return { eligible: false, reason: "installed from a local folder", version };
      return { eligible: true, version };
    },
    async apply(_release: Release): Promise<string> {
      await claude(["plugin", "marketplace", "update", MARKETPLACE], "plugin marketplace update");
      await claude(["plugin", "update", PLUGIN_ID, "--scope", "user"], "plugin update");
      // Whatever the marketplace names now: the release, or (its pointer not moved yet) the version already installed.
      const version = await installedVersion();
      if (!version) throw new Error("the plugin is no longer installed after the update");
      return version;
    },
  };
}
