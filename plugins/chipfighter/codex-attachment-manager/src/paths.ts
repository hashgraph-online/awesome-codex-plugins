// Purpose: one place for where the tool keeps its own data (selection state, request statistics, logs, backups; since
// v0.1-10 which task a panel was switched to, and v0.1-11 pixel fingerprints — never image content).
// Input: CAM_DATA_DIR when set; otherwise a per-user folder: %USERPROFILE%\.codex-attachment-manager on Windows,
// ~/Library/Application Support/codex-attachment-manager on macOS, $XDG_DATA_HOME (or ~/.local/share)/
// codex-attachment-manager on Linux. Never inside the plugin folder, which Codex replaces on every update, and never
// under ~/.codex.
// v0.1-15: Windows used %LOCALAPPDATA%\codex-attachment-manager until then. Codex and Claude are Microsoft Store (MSIX)
// apps, and new files that programs they start write under AppData go to each app's private folder, so the plugin
// service, the engine and the command line could each see different data there (a selection made in the panel was
// missing for an engine started outside Codex). The profile folder is not redirected; Codex keeps ~\.codex there too.
// migrate-data.ts brings the old data over.
// Output: absolute directory paths. Nothing here writes anything.

import { homedir } from "node:os";
import { join } from "node:path";

export function dataDir(env: NodeJS.ProcessEnv = process.env, platform: NodeJS.Platform = process.platform, home = homedir()): string {
  const chosen = env.CAM_DATA_DIR?.trim();
  if (chosen) return chosen;
  if (platform === "win32") return join(home, ".codex-attachment-manager");
  if (platform === "darwin") return join(home, "Library", "Application Support", "codex-attachment-manager");
  return join(env.XDG_DATA_HOME || join(home, ".local", "share"), "codex-attachment-manager");
}

export const selectionDirOf = (root = dataDir()) => join(root, "selection");
export const requestStatsDirOf = (root = dataDir()) => join(root, "state", "requests");
export const proxyLogDirOf = (root = dataDir()) => join(root, "proxy");
export const bindingsDirOf = (root = dataDir()) => join(root, "bindings");
export const pixelCacheDirOf = (root = dataDir()) => join(root, "cache", "pixels");
