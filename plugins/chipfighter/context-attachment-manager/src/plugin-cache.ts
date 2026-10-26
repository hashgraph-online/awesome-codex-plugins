// Codex may clean old cache contents even when Windows prevents removing the directory of a running plugin.
// Preserve program files before installation; restore older runtimes and restore the target too on failure.
import { cpSync, existsSync, mkdirSync, mkdtempSync, readdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function preservingPluginCache<T>(root: string, targetVersion: string, install: () => T): T {
  const versions = existsSync(root) ? readdirSync(root, { withFileTypes: true }).filter(entry => entry.isDirectory() && /^\d+\.\d+\.\d+(?:[-+][\w.-]+)?$/.test(entry.name)).map(entry => entry.name) : [];
  const backup = versions.length ? mkdtempSync(join(tmpdir(), "cam-runtime-backup-")) : null;
  for (const version of versions) cpSync(join(root, version), join(backup!, version), { recursive: true });
  let succeeded = false;
  try {
    const result = install();
    succeeded = true;
    return result;
  } finally {
    for (const version of versions) {
      if (succeeded && version === targetVersion) continue;
      mkdirSync(join(root, version), { recursive: true });
      cpSync(join(backup!, version), join(root, version), { recursive: true, force: true });
    }
  }
}
