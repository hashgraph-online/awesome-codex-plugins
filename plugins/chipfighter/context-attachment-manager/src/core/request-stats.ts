// Purpose: P4 — per thread, what the engine last saw: the latest event (an HTTP request or a WebSocket connection)
// and the latest full HTTP /responses request, which the panel uses as the baseline of its size estimate. Kept apart,
// so a WebSocket connection does not erase the baseline. Metadata only: sizes, counts, image keys, never content.
// Input/Output: <data dir>/state/requests/<thread id>.json, e.g. { "latest": {…}, "lastHttp": {…, "imageSizes": {…}} }.

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { requestStatsDirOf } from "./paths.ts";
import { SESSION_KEY } from "./selection.ts";

type Json = Record<string, any>;
export type RequestStats = { latest: Json; lastHttp: Json | null };

// v0.11: under the session's key (selection.ts, sessionKeyOf), whatever the platform.
export function readRequestStats(threadId: string, dir = requestStatsDirOf()): RequestStats | null {
  if (!SESSION_KEY.test(threadId)) return null;
  const file = join(dir, `${threadId}.json`);
  if (!existsSync(file)) return null;
  try {
    const json = JSON.parse(readFileSync(file, "utf8"));
    // Files written before P4 held the latest entry alone.
    return "latest" in json ? json : { latest: json, lastHttp: json.transport === "http" ? json : null };
  } catch {
    return null;
  }
}

// v0.12: best effort, never throws. On Windows the rename fails now and then while another program (an antivirus
// scan, a panel reading the file) has the file open; it is tried a few more times, and if it still fails this update
// is lost. A throw here used to stop the engine, with every request going through it (2026-11-22: 238 engines in a
// month ended without a trace).
export function recordRequest(threadId: string | null, stats: Json, dir = requestStatsDirOf()): void {
  if (!threadId || !SESSION_KEY.test(threadId)) return;
  try {
    mkdirSync(dir, { recursive: true });
    const file = join(dir, `${threadId}.json`);
    const next: RequestStats = { latest: stats, lastHttp: stats.transport === "http" ? stats : readRequestStats(threadId, dir)?.lastHttp ?? null };
    // Written to a temporary file first, so the panel never reads a half-written file.
    writeFileSync(`${file}.tmp`, JSON.stringify(next, null, 2));
    renameWithRetry(`${file}.tmp`, file);
  } catch { /* the panel shows the previous request until the next one */ }
}

const pause = new Int32Array(new SharedArrayBuffer(4));
// Windows refuses to replace a file another program has open (EPERM, EACCES, EBUSY); such locks last milliseconds.
export function renameWithRetry(from: string, to: string, attempts = 4): void {
  for (let attempt = 1; ; attempt++) {
    try { renameSync(from, to); return; } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (attempt >= attempts || !["EPERM", "EACCES", "EBUSY"].includes(code ?? "")) throw error;
      Atomics.wait(pause, 0, 0, 15 * attempt);
    }
  }
}
