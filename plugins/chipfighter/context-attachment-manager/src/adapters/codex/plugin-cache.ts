// Codex may clean old cache contents even when Windows prevents removing the directory of a running plugin.
// Preserve program files before installation; restore older runtimes and restore the target too on failure.
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function preservingPluginCache<T>(root: string, targetVersion: string, install: () => T): T {
  const kept = keep(root);
  let succeeded = false;
  try {
    const result = install();
    succeeded = true;
    return result;
  } finally {
    kept.restore(succeeded, targetVersion);
  }
}

// v0.13: the same around an install that runs asynchronously (core/update.ts: the plugin service keeps answering Codex
// while Codex's command line installs the new version).
export async function preservingPluginCacheAsync<T>(root: string, targetVersion: string, install: () => Promise<T>): Promise<T> {
  const kept = keep(root);
  let succeeded = false;
  try {
    const result = await install();
    succeeded = true;
    return result;
  } finally {
    kept.restore(succeeded, targetVersion);
  }
}

function keep(root: string) {
  const versions = existsSync(root) ? readdirSync(root, { withFileTypes: true }).filter(entry => entry.isDirectory() && /^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$/.test(entry.name)).map(entry => entry.name) : [];
  const backup = versions.length ? mkdtempSync(join(tmpdir(), "cam-runtime-backup-")) : null;
  const discard = () => {
    if (!backup) return;
    try { rmSync(backup, { recursive: true, force: true, maxRetries: 3 }); } catch { /* a cleanup error must not hide the install result */ }
  };
  try {
    for (const version of versions) cpSync(join(root, version), join(backup!, version), { recursive: true });
  } catch (error) {
    discard();
    throw error;
  }
  return {
    restore(succeeded: boolean, targetVersion: string) {
      for (const version of versions) {
        if (succeeded && version === targetVersion) continue;
        mkdirSync(join(root, version), { recursive: true });
        cpSync(join(backup!, version), join(root, version), { recursive: true, force: true });
      }
      // If restoration failed, the staged files may be the only remaining copy.
      discard();
    },
  };
}
