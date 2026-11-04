// The polling loop for all three modes. Inputs are injected so tests can
// drive it with a fake reader and a fake clock:
//   reader: see github.mjs
//   clock:  { now(): seconds, sleep(seconds): Promise<void> }
//   write:  receives each verdict object
// Returns the process exit code.

import { asQueryError } from './errors.mjs';
import { resolveTarget, discoverStack } from './context.mjs';
import { readPr } from './snapshot.mjs';
import { decide, firstBlocker, isPending } from './classify.mjs';
import { EXIT } from './proof.mjs';
import { makeEmitter, rowSummary, blockerBody, queryBlockerBody, readyVerdictBody } from './verdicts.mjs';

const BACKOFF_FLOOR = 60;
const BACKOFF_CAP = 300;

// Wait before retry N: start from the poll interval (never below the floor),
// double for each further consecutive failure, and stop at the cap.
export function retryBackoff(interval, failures) {
  const start = interval < BACKOFF_FLOOR ? BACKOFF_FLOOR : interval;
  const doubled = start * Math.pow(2, failures - 1);
  return doubled > BACKOFF_CAP ? BACKOFF_CAP : doubled;
}

export async function watch(opts, cfg, { reader, clock, write }) {
  const emit = makeEmitter({ mode: opts.mode, now: () => clock.now(), write });
  const start = clock.now();
  const deadline = opts.timeout > 0 ? start + opts.timeout : null;
  const pastDeadline = () => deadline !== null && clock.now() >= deadline;
  const sleepCapped = (seconds) => clock.sleep(deadline === null ? seconds : Math.max(0, Math.min(seconds, deadline - clock.now())));
  const terminal = (kind, body, exitCode) => {
    emit(kind, body, { terminal: true, exitCode });
    return exitCode;
  };
  const queryBlocker = (err, failures) => {
    const { body, exitCode } = queryBlockerBody(err, failures);
    return terminal('BLOCKER', body, exitCode);
  };

  // ---- context ----
  let target;
  try {
    target = await resolveTarget(opts, reader);
    if (opts.mode === 'queued' && !opts.stackPrs) {
      target.numbers = await discoverStack(reader, target.owner, target.repo, target.numbers[0]);
    }
  } catch (err) {
    return queryBlocker(asQueryError(err), 1);
  }
  const { owner, repo } = target;

  // ---- failure handling shared by every mode ----
  let failures = 0;
  // Returns an exit code when the run must stop, or null to try again.
  const onFailure = async (raw) => {
    const err = asQueryError(raw);
    failures += 1;
    if (!err.retryable || failures >= opts.maxQueryErrors) return queryBlocker(err, failures);
    const backoff = retryBackoff(opts.interval, failures);
    emit('RETRY', { error: err.toJSON(), failures, backoffSeconds: backoff });
    if (pastDeadline()) return terminal('TIMEOUT', { reason: 'status-unavailable', failures }, EXIT.TIMEOUT);
    await sleepCapped(backoff);
    return null;
  };

  const readRows = async (numbers, queued) => {
    const rows = [];
    for (const n of numbers) rows.push(await readPr(reader, owner, repo, n, cfg, { queued }));
    return rows;
  };
  const currentNumbers = async () => (opts.mode === 'stack' ? discoverStack(reader, owner, repo, target.numbers[0]) : target.numbers);

  // ---- status only ----
  if (opts.statusOnly) {
    for (;;) {
      try {
        const rows = await readRows(await currentNumbers(), false);
        return terminal('STATUS', { rows: rows.map((r) => rowSummary(r, opts)) }, EXIT.READY);
      } catch (err) {
        const stop = await onFailure(err);
        if (stop !== null) return stop;
      }
    }
  }

  if (opts.mode === 'queued') return runQueued();

  // ---- single and stack ----
  for (;;) {
    let rows;
    try {
      rows = await readRows(await currentNumbers(), false);
    } catch (err) {
      const stop = await onFailure(err);
      if (stop !== null) return stop;
      continue;
    }
    failures = 0;
    if (opts.mode === 'stack') emit('STATUS', { rows: rows.map((r) => rowSummary(r, opts)) });

    const d = decide(rows, opts);
    if (d.outcome === 'blocker') {
      const { body, exitCode } = blockerBody(d.tier, d.snap, d.reason);
      return terminal('BLOCKER', body, exitCode);
    }
    if (d.outcome === 'ready') {
      const { body, exitCode } = readyVerdictBody(d.proofs, opts);
      return terminal('READY', body, exitCode);
    }
    const pending = d.snap.ci.pending.map((c) => c.name);
    emit('WAITING', { reason: 'checks', pr: d.snap.pr, pending });
    if (pastDeadline()) return terminal('TIMEOUT', { reason: 'deadline', pr: d.snap.pr, pending }, EXIT.TIMEOUT);
    await sleepCapped(opts.interval);
  }

  // ---- queued stack ----
  async function runQueued() {
    const order = target.numbers;
    const rows = new Map();
    emit('QUEUE', { prs: [...order] });

    const unmerged = () => order.filter((n) => rows.get(n)?.status !== 'merged');
    let sweep = [...order];
    let nextSweepAt = null;
    let frontier = null;
    let lastWait = null;

    for (;;) {
      const sweeping = sweep.length > 0;
      const n = sweeping ? sweep[0] : unmerged()[0];
      let snap;
      try {
        snap = await readPr(reader, owner, repo, n, cfg, { queued: true });
      } catch (err) {
        const stop = await onFailure(err);
        if (stop !== null) return stop;
        continue;
      }
      failures = 0;
      rows.set(n, snap);
      if (sweeping) {
        sweep.shift();
        if (sweep.length > 0) continue;
        emit('STATUS', { rows: order.filter((x) => rows.has(x)).map((x) => rowSummary(rows.get(x), opts)) });
        nextSweepAt = clock.now() + opts.sweepInterval;
      }

      const active = unmerged();
      if (active.length === 0) return terminal('COMPLETE', { merged: [...order] }, EXIT.READY);

      const activeRows = active.map((x) => rows.get(x)).filter(Boolean);
      const blocker = firstBlocker(activeRows, opts);
      if (blocker) {
        const { body, exitCode } = blockerBody(blocker.tier, blocker.snap, blocker.reason);
        return terminal('BLOCKER', body, exitCode);
      }

      const lowest = active[0];
      if (frontier !== null && lowest !== frontier) {
        const idx = order.indexOf(lowest);
        const merged = order.slice(0, idx).filter((x) => order.indexOf(x) >= order.indexOf(frontier));
        emit('ADVANCE', { merged, frontier: lowest, remaining: active.length });
        frontier = lowest;
        lastWait = null;
        continue;
      }
      frontier = lowest;

      if (pastDeadline()) return terminal('TIMEOUT', { reason: 'deadline', pr: frontier, unmerged: active.length }, EXIT.TIMEOUT);

      const fs = rows.get(frontier);
      const wait = fs && isPending(fs)
        ? { reason: 'checks', pr: frontier, pending: fs.ci.pending.map((c) => c.name) }
        : { reason: 'merge-queue', pr: frontier, unmerged: active.length };
      const key = `${wait.reason}:${wait.pr}:${wait.reason === 'checks' ? wait.pending.length : wait.unmerged}`;
      if (key !== lastWait) {
        emit('WAITING', wait);
        lastWait = key;
      }

      await sleepCapped(opts.interval);
      if (nextSweepAt !== null && clock.now() >= nextSweepAt) sweep = unmerged();
    }
  }
}
