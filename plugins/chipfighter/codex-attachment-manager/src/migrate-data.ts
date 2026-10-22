// Purpose: v0.1-15 — on Windows the tool's data moved from %LOCALAPPDATA%\codex-attachment-manager to
// %USERPROFILE%\.codex-attachment-manager (paths.ts says why). The old data may be split over several folders: the old
// folder itself, and a private copy for each Microsoft Store app whose programs wrote there
// (%LOCALAPPDATA%\Packages\<app>\LocalCache\Local\codex-attachment-manager). Once, before anything reads the new
// folder, this copies the selections, the panels' task switches, the request statistics, the remembered language and
// the config backups from all of them, the newest copy of each file winning. Logs and caches stay behind, and the old
// folders are left as they are.
// Input: LOCALAPPDATA and the new data folder. Output: copied files; <data dir>/migrated.json.

import { copyFileSync, existsSync, mkdirSync, readdirSync, rmSync, statSync, utimesSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { dataDir } from "./paths.ts";

const NAME = "codex-attachment-manager";
const KEPT_FOLDERS = ["selection", "bindings", join("state", "requests"), "config-backup"];
const KEPT_FILES = ["language.json"];

export function oldWindowsFolders(localAppData: string | undefined): string[] {
  if (!localAppData) return [];
  const folders = [join(localAppData, NAME)];
  let apps: string[] = [];
  try { apps = readdirSync(join(localAppData, "Packages")); } catch { /* no Store apps */ }
  for (const app of apps) folders.push(join(localAppData, "Packages", app, "LocalCache", "Local", NAME));
  return folders.filter((folder) => existsSync(folder));
}

function filesIn(folder: string, sub: string): string[] {
  try {
    return readdirSync(join(folder, sub), { withFileTypes: true }).filter((entry) => entry.isFile()).map((entry) => join(sub, entry.name));
  } catch { return []; }
}

const pause = (ms: number) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);

// Codex starts several plugin services at once: one of them copies, the others wait for it (but not for one that
// died halfway: a lock older than a minute is taken over).
export function migrateWindowsData(target = dataDir(), localAppData = process.env.LOCALAPPDATA, waitMs = 5000): { copied: number; sources: string[] } | null {
  const done = join(target, "migrated.json");
  if (existsSync(done)) return null;
  mkdirSync(target, { recursive: true });
  const lock = join(target, ".migrating");
  const take = () => { try { writeFileSync(lock, String(process.pid), { flag: "wx" }); return true; } catch { return false; } };
  if (!take()) {
    for (let waited = 0; waited < waitMs && !existsSync(done); waited += 100) pause(100);
    if (existsSync(done)) return null;
    try { if (Date.now() - statSync(lock).mtimeMs < 60_000) return null; } catch { /* gone meanwhile */ }
    rmSync(lock, { force: true });
    if (!take()) return null;
  }
  try {
    const sources = oldWindowsFolders(localAppData).filter((folder) => resolve(folder) !== resolve(target));
    const newest = new Map<string, { from: string; mtimeMs: number }>();
    for (const folder of sources) {
      const files = [...KEPT_FOLDERS.flatMap((sub) => filesIn(folder, sub)), ...KEPT_FILES.filter((file) => existsSync(join(folder, file)))];
      for (const file of files) {
        const { mtimeMs } = statSync(join(folder, file));
        if ((newest.get(file)?.mtimeMs ?? -1) < mtimeMs) newest.set(file, { from: join(folder, file), mtimeMs });
      }
    }
    let copied = 0;
    for (const [file, { from, mtimeMs }] of newest) {
      const to = join(target, file);
      if (existsSync(to) && statSync(to).mtimeMs >= mtimeMs) continue;
      mkdirSync(dirname(to), { recursive: true });
      copyFileSync(from, to);
      // Kept, so a later "newest wins" between copies still means something.
      utimesSync(to, new Date(), new Date(mtimeMs));
      copied++;
    }
    writeFileSync(done, JSON.stringify({ at: new Date().toISOString(), sources, copied }, null, 2));
    return { copied, sources };
  } finally {
    rmSync(lock, { force: true });
  }
}

// Called by every entry point (plugin service, engine, command line) before it touches the data folder. Only Windows
// had the old folder; CAM_DATA_DIR (tests, development) means a folder of its own.
export function migrateDataOnce(): void {
  if (process.platform !== "win32" || process.env.CAM_DATA_DIR?.trim()) return;
  try { migrateWindowsData(); } catch { /* best effort: the new folder works without the old data */ }
}
