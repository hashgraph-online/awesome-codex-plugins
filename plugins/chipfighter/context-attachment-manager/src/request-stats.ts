// Purpose: P4 — per thread, what the engine last saw: the latest event (an HTTP request or a WebSocket connection)
// and the latest full HTTP /responses request, which the panel uses as the baseline of its size estimate. Kept apart,
// so a WebSocket connection does not erase the baseline. Metadata only: sizes, counts, image keys, never content.
// Input/Output: <data dir>/state/requests/<thread id>.json, e.g. { "latest": {…}, "lastHttp": {…, "imageSizes": {…}} }.

import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { requestStatsDirOf } from "./paths.ts";

type Json = Record<string, any>;
export type RequestStats = { latest: Json; lastHttp: Json | null };

const THREAD_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export function readRequestStats(threadId: string, dir = requestStatsDirOf()): RequestStats | null {
  if (!THREAD_ID.test(threadId)) return null;
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

export function recordRequest(threadId: string | null, stats: Json, dir = requestStatsDirOf()): void {
  if (!threadId || !THREAD_ID.test(threadId)) return;
  mkdirSync(dir, { recursive: true });
  const file = join(dir, `${threadId}.json`);
  const next: RequestStats = { latest: stats, lastHttp: stats.transport === "http" ? stats : readRequestStats(threadId, dir)?.lastHttp ?? null };
  // Written to a temporary file first, so the panel never reads a half-written file.
  writeFileSync(`${file}.tmp`, JSON.stringify(next, null, 2));
  renameSync(`${file}.tmp`, file);
}
