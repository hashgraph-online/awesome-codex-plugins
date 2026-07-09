/**
 * Audit Write-Ahead Log
 *
 * Replaces the in-memory `auditBuffer` in daemon.mjs with an append-only
 * JSONL file on disk. Crash-recoverable: a daemon SIGKILL between disk
 * write and backend ack loses zero rows, because rows are on disk before
 * the caller is acknowledged.
 *
 * Layout under <dataDir>/audit/:
 *   current.jsonl       — append-only, today's audit rows
 *   shipped.offset      — last byte the backend has acked (atomic write)
 *   archive/YYYY-MM-DD-NNN.jsonl — rotated segments
 *
 * Industry pattern (OpenTelemetry Collector / Fluent Bit / Vector.dev /
 * Datadog Agent / Loki / Linux auditd). The shape is identical across all
 * of them: append → ack caller → background batch → advance offset →
 * truncate when fully shipped.
 *
 * Concurrency: POSIX `O_APPEND` is atomic for writes ≤ PIPE_BUF (≈4096 B
 * on macOS/Linux). Each audit row is ~500 bytes typical, so concurrent
 * appends from multiple hooks do not interleave. If a row grows past
 * ~4 KB the kernel may split the write — we cap appendAuditLine at 4000
 * bytes and reject larger payloads upstream rather than risk corruption.
 */

import {
  appendFile,
  mkdir,
  open,
  readFile,
  rename,
  stat,
  unlink,
  writeFile,
} from "node:fs/promises";
import { existsSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const MAX_LINE_BYTES = 4000; // stay under PIPE_BUF (~4 KB) for atomic appends
const DEFAULT_ROTATE_BYTES = 10 * 1024 * 1024; // 10 MB
const DEFAULT_ROTATE_AGE_MS = 60 * 60 * 1000; // 1 hour

export function createAuditWal(opts) {
  const dir = path.join(opts.dataDir, "audit");
  const currentPath = path.join(dir, "current.jsonl");
  const offsetPath = path.join(dir, "shipped.offset");
  const archiveDir = path.join(dir, "archive");
  const rotateBytes = opts.rotateBytes ?? DEFAULT_ROTATE_BYTES;
  const rotateAgeMs = opts.rotateAgeMs ?? DEFAULT_ROTATE_AGE_MS;

  let ensured = false;
  async function ensureDirs() {
    if (ensured) return;
    await mkdir(dir, { recursive: true });
    await mkdir(archiveDir, { recursive: true });
    ensured = true;
  }

  // Monotonic per-process sequence — used to recover the enqueue order
  // even when concurrent O_APPEND writes land on disk in a different order.
  // Resets on daemon restart, but each restart writes its own range that
  // is still locally consistent for sorting within that segment.
  let seqCounter = 0;

  async function appendLine(row) {
    // Stamp the row with enqueue order BEFORE any await — otherwise the
    // seq is assigned based on which `await ensureDirs()` resolves first
    // (non-deterministic for concurrent callers), which defeats the
    // purpose. The synchronous prefix of an async function runs in call
    // order; the post-await order does not.
    const enriched = {
      ...row,
      _seq: ++seqCounter,
      _enqueuedAt: Date.now(),
    };
    await ensureDirs();
    const json = JSON.stringify(enriched);
    if (Buffer.byteLength(json, "utf8") > MAX_LINE_BYTES) {
      throw new Error(
        `audit row too large (${json.length} bytes); cap is ${MAX_LINE_BYTES}`,
      );
    }
    await appendFile(currentPath, json + "\n", { encoding: "utf8" });
  }

  async function readShippedOffset() {
    try {
      const raw = await readFile(offsetPath, "utf8");
      const n = parseInt(raw.trim(), 10);
      return Number.isFinite(n) && n >= 0 ? n : 0;
    } catch (err) {
      if (err && err.code === "ENOENT") return 0;
      throw err;
    }
  }

  async function writeShippedOffset(offset) {
    await ensureDirs();
    const tmpPath = `${offsetPath}.tmp.${process.pid}.${Date.now()}`;
    await writeFile(tmpPath, String(offset), "utf8");
    await rename(tmpPath, offsetPath);
  }

  /**
   * Read a batch starting at the current shipped.offset. Returns up to
   * `maxRows` parseable JSON rows plus the byte offset *after* the last
   * row read. The caller is expected to ship the rows, then advance the
   * offset via advanceOffset(endOffset).
   *
   * Skips malformed lines (logs to stderr) so a single bad row can't
   * permanently block the stream.
   */
  async function readBatch(maxRows = 100) {
    await ensureDirs();
    if (!existsSync(currentPath)) return { rows: [], endOffset: 0 };

    const offset = await readShippedOffset();
    const fh = await open(currentPath, "r");
    try {
      const st = await fh.stat();
      if (offset >= st.size) return { rows: [], endOffset: offset };
      const length = st.size - offset;
      const buf = Buffer.alloc(length);
      await fh.read(buf, 0, length, offset);

      // Scan byte boundaries for \n (0x0a). Each complete line ends at a
      // newline; a trailing partial line without \n is left for the next
      // read. This is the same shape Fluent Bit / Vector use for tail
      // input — never advance past a partial line.
      const rows = [];
      let pos = 0;
      let lineEnd;
      while (rows.length < maxRows && (lineEnd = buf.indexOf(0x0a, pos)) !== -1) {
        const line = buf.slice(pos, lineEnd).toString("utf8");
        if (line.length > 0) {
          try {
            rows.push(JSON.parse(line));
          } catch (err) {
            process.stderr.write(
              `[audit-wal] skipping malformed line at offset ${offset + pos}: ${err?.message ?? err}\n`,
            );
          }
        }
        pos = lineEnd + 1; // skip past the \n
      }
      // Restore enqueue order. Concurrent O_APPEND writers may have landed
      // out of order on disk; the `_seq` stamp we wrote at appendLine time
      // is monotonic per daemon process. Fall back to `_enqueuedAt` for
      // ties (or for old rows written before the stamps existed). Then
      // strip the internal fields so the backend never sees them.
      rows.sort(compareForOrder);
      const stripped = rows.map((r) => {
        const { _seq, _enqueuedAt, ...rest } = r;
        return rest;
      });
      return { rows: stripped, endOffset: offset + pos };
    } finally {
      await fh.close();
    }
  }

  function compareForOrder(a, b) {
    const aSeq = typeof a?._seq === "number" ? a._seq : null;
    const bSeq = typeof b?._seq === "number" ? b._seq : null;
    if (aSeq !== null && bSeq !== null) return aSeq - bSeq;
    const aTs = typeof a?._enqueuedAt === "number" ? a._enqueuedAt : 0;
    const bTs = typeof b?._enqueuedAt === "number" ? b._enqueuedAt : 0;
    if (aTs !== bTs) return aTs - bTs;
    // Last resort: executed_at on the audit row (the time the tool
    // actually fired in Claude Code). String compare on ISO 8601 is correct.
    const aEx = typeof a?.executed_at === "string" ? a.executed_at : "";
    const bEx = typeof b?.executed_at === "string" ? b.executed_at : "";
    if (aEx < bEx) return -1;
    if (aEx > bEx) return 1;
    return 0;
  }

  /**
   * Advance the shipped offset after a successful backend ack. Then
   * check rotation criteria — if current.jsonl is fully shipped AND
   * (too big OR too old), rotate it into archive/ and reset offset to 0.
   */
  async function advanceOffset(newOffset) {
    if (typeof newOffset !== "number" || newOffset < 0) {
      throw new Error(`invalid offset: ${newOffset}`);
    }
    await writeShippedOffset(newOffset);
    await rotateIfNeeded();
  }

  async function rotateIfNeeded() {
    if (!existsSync(currentPath)) return;
    const st = await stat(currentPath);
    const offset = await readShippedOffset();
    const fullyShipped = offset >= st.size;
    const tooBig = st.size >= rotateBytes;
    const tooOld = Date.now() - st.mtimeMs >= rotateAgeMs;
    if (!fullyShipped) return;
    if (!tooBig && !tooOld) return;

    await ensureDirs();
    const ts = new Date().toISOString().slice(0, 10);
    let seq = 1;
    let archivePath;
    do {
      archivePath = path.join(archiveDir, `${ts}-${String(seq).padStart(3, "0")}.jsonl`);
      seq += 1;
    } while (existsSync(archivePath));
    await rename(currentPath, archivePath);
    await writeShippedOffset(0);
  }

  /**
   * Delete archived segments. Archives are rotated only AFTER they're
   * fully shipped (see rotateIfNeeded), so any file in archive/ is safe
   * to delete. Cap retention at `keep` newest segments for forensics —
   * defaults to 5 (matches Fluent Bit / OTel collector defaults).
   */
  async function pruneArchive(keep = 5) {
    if (!existsSync(archiveDir)) return [];
    const entries = readdirSync(archiveDir)
      .filter((f) => f.endsWith(".jsonl"))
      .map((f) => ({ name: f, mtime: statSync(path.join(archiveDir, f)).mtimeMs }))
      .sort((a, b) => b.mtime - a.mtime);
    const toDelete = entries.slice(keep);
    const deleted = [];
    for (const entry of toDelete) {
      try {
        await unlink(path.join(archiveDir, entry.name));
        deleted.push(entry.name);
      } catch (err) {
        process.stderr.write(`[audit-wal] failed to delete ${entry.name}: ${err?.message ?? err}\n`);
      }
    }
    return deleted;
  }

  /**
   * Total bytes pending ship — current.jsonl size minus shipped offset.
   * Useful for the daemon to decide whether the buffer is "hot" (flush
   * sooner) or for debug telemetry.
   */
  async function pendingBytes() {
    if (!existsSync(currentPath)) return 0;
    const st = await stat(currentPath);
    const offset = await readShippedOffset();
    return Math.max(0, st.size - offset);
  }

  return {
    appendLine,
    readBatch,
    advanceOffset,
    rotateIfNeeded,
    pruneArchive,
    pendingBytes,
    readShippedOffset,
    // Exposed for tests and ops only.
    _paths: { currentPath, offsetPath, archiveDir },
  };
}
