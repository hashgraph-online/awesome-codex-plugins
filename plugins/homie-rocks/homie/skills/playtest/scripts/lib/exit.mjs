/**
 * Ending a controller: after its report is written and its browsers are closed, the process leaves, with the exit
 * code its result earned.
 *
 * Why this exists: a full run wrote its report, its sheets and the reviewer command, every Chrome and ffmpeg it
 * owned had closed, and the Node process stayed. Node only leaves by itself when nothing is left on its event loop,
 * and a controller that drives browsers collects things that sit there: a socket puppeteer kept, a pipe a child's
 * helper inherited, a race's losing timer, an AbortSignal's timer. Which one it was that time was never isolated,
 * so the end does not depend on finding it: run the cleanup (bounded), flush what was printed, then exit.
 *
 * The exit code is the one already decided (`process.exitCode`, or `code`): a failed run still exits non-zero.
 */

/** Race `p` against `ms`; the losing timer is cleared, so the race itself leaves nothing on the event loop. */
export function within(p, ms, fallback = null) {
  let timer = null;
  const late = new Promise((r) => { timer = setTimeout(() => r(fallback), ms); });
  return Promise.race([Promise.resolve(p).catch(() => fallback), late]).finally(() => clearTimeout(timer));
}

/**
 * Run `cleanup` (at most `graceMs`), wait for stdout and stderr to drain (at most 2 s), then exit with `code`
 * (default: process.exitCode, else 0). `exit` is process.exit (a test passes its own).
 */
export async function finish({ code = null, cleanup = null, graceMs = 15_000, exit = (c) => process.exit(c) } = {}) {
  if (cleanup) await within(Promise.resolve().then(cleanup), graceMs);
  // A pipe (a caller reading our JSON) takes writes asynchronously: an exit before the drain would cut the report.
  const drained = (s) => new Promise((r) => { if (!s?.writableLength) r(); else s.write('', () => r()); });
  await within(Promise.all([drained(process.stdout), drained(process.stderr)]), 2000);
  exit(code ?? process.exitCode ?? 0);
}
