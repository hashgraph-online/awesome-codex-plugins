// Keep the current JSONL path for readers. Only rotate and prune this plugin's named diagnostic logs.
import { randomUUID } from "node:crypto";
import { appendFileSync, lstatSync, mkdirSync, readdirSync, renameSync, unlinkSync } from "node:fs";
import { join } from "node:path";

const MIB = 1024 * 1024;
const POLICIES = {
  proxy: { activeBytes: 4 * MIB, archiveBytes: 28 * MIB, archiveName: /^\d{4}-\d{2}-\d{2}(?:\.\d+-[0-9a-f-]{36})?\.jsonl$/ },
  "plugin-server": { activeBytes: 2 * MIB, archiveBytes: 6 * MIB, archiveName: /^plugin-server\.\d+-[0-9a-f-]{36}\.jsonl$/ },
};
type Stream = keyof typeof POLICIES;
type Limits = { activeBytes: number; archiveBytes: number };
const lastSweep = new Map<Stream, string>();

function pruneArchives(dir: string, archiveName: RegExp, activeName: string, budget: number): void {
  const files = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (!entry.isFile() || entry.name === activeName || !archiveName.test(entry.name)) continue;
    const file = join(dir, entry.name);
    try {
      const stat = lstatSync(file, { throwIfNoEntry: false });
      if (stat?.isFile() && stat.nlink === 1) files.push({ file, size: stat.size, mtime: stat.mtimeMs });
    } catch { /* another process or the user may have moved it */ }
  }
  files.sort((a, b) => b.mtime - a.mtime || b.file.localeCompare(a.file));
  let kept = 0;
  for (const file of files) {
    if (kept + file.size <= budget) kept += file.size;
    else { try { unlinkSync(file.file); } catch { /* best effort */ } }
  }
}

export function writeDiagnosticLog(dir: string, stream: Stream, entry: Record<string, unknown>, now = new Date(), limits: Limits = POLICIES[stream]): void {
  try {
    const json = JSON.stringify(entry);
    if (json === undefined) return;
    const line = `${json}\n`;
    const bytes = Buffer.byteLength(line);
    if (bytes > limits.activeBytes) return;
    const day = now.toISOString().slice(0, 10);
    const stem = stream === "proxy" ? day : stream;
    const activeName = `${stem}.jsonl`;
    const file = join(dir, activeName);
    mkdirSync(dir, { recursive: true });
    if (!lstatSync(dir).isDirectory()) return;
    const stat = lstatSync(file, { throwIfNoEntry: false });
    if (stat && (!stat.isFile() || stat.nlink !== 1)) return;
    const rotate = stat !== undefined && stat.size + bytes > limits.activeBytes;
    if (rotate) {
      // Other plugin services can also rotate. Give each archive its own name to avoid overwriting it.
      try { renameSync(file, join(dir, `${stem}.${now.getTime()}-${randomUUID()}.jsonl`)); }
      catch (error) { if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error; }
    }
    const sweep = join(dir, day);
    if (rotate || lastSweep.get(stream) !== sweep) {
      lastSweep.set(stream, sweep);
      try { pruneArchives(dir, POLICIES[stream].archiveName, activeName, limits.archiveBytes); } catch { /* best effort */ }
    }
    appendFileSync(file, line);
  } catch { /* diagnostics must never interrupt a request */ }
}
