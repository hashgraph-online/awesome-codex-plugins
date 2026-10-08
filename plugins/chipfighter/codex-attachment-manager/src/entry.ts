// Purpose: v0.1 — whether a module is the script Node was started with. Node loads that script by its real path, while
// process.argv[1] keeps the path as it was given; the two differ when the path goes through a symlink (macOS's /var,
// or a ~/.codex that links somewhere else), and the script would then silently do nothing.
// Input: the module's import.meta.url. Output: true or false.

import { realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";

export function isEntryPoint(moduleUrl: string): boolean {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(moduleUrl));
  } catch {
    return false;
  }
}
