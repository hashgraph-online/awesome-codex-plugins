import { spawn, spawnSync } from "node:child_process";
import { appendFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { createInterface } from "node:readline";

const WIN = process.platform === "win32";
const REQUEST_WINDOW_MS = 60_000;
export const units = (n) => Number.isSafeInteger(n) && n >= 0;

function stopWorker(child) {
  if (!child.pid) return;
  if (WIN) {
    if (spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true, stdio: "ignore" }).status !== 0) child.kill();
    return;
  }
  try { process.kill(-child.pid, "SIGKILL"); } catch { child.kill("SIGKILL"); }
}

export async function runJob(dir, plan, state, { save, abortRequested }) {
  const active = new Map(), waiting = [];
  const pending = state.partitions.map((part, index) => ({ part, index })).filter(({ part }) => part.status === "pending");
  let aborted = false, fatal, timer;
  state.phase = "running";
  state.pid = process.pid;
  state.error = null;
  save();

  function halt() {
    // Closing stdin also informs workers that observe supervisor disconnects.
    for (const { child } of active.values()) {
      child.stdin.end();
      stopWorker(child);
    }
  }

  function abort() {
    if (aborted) return;
    aborted = true;
    halt();
  }

  const guarded = (fn) => (...args) => {
    if (fatal) return;
    try { fn(...args); }
    catch (error) { fatal = error; halt(); }
  };

  function reportError(worker, message) {
    worker.error ??= message;
    stopWorker(worker.child);
  }

  function send(worker, decision) {
    worker.child.stdin.write(JSON.stringify(decision) + "\n");
  }

  function admit() {
    const now = Date.now(), cutoff = now - REQUEST_WINDOW_MS;
    while (state.permits.length && state.permits[0] <= cutoff) state.permits.shift();
    while (waiting.length) {
      const worker = waiting[0], request = worker.request;
      if (!request || worker.error || worker.closed) { waiting.shift(); continue; }
      const { id, maxMicros } = request;
      const remaining = state.budgetMicros - state.spentMicros;
      if (maxMicros > remaining) {
        worker.denied = true;
        worker.request = null;
        waiting.shift();
        send(worker, { type: "denied", id, reason: "budget" });
        worker.child.stdin.end();
        continue;
      }
      if (state.permits.length >= plan.requestsPerMinute || maxMicros > remaining - state.heldMicros) return;
      waiting.shift();
      worker.request = null;
      worker.part.hold = request;
      state.heldMicros += maxMicros;
      state.permits.push(now);
      save(); // Persist the reservation and rate slot before a worker can spend them.
      send(worker, { type: "permit", id });
    }
  }

  function onLine(worker, line) {
    appendFileSync(worker.stdout, line + "\n");
    if (aborted || worker.error || worker.denied) return;
    let event;
    try { event = JSON.parse(line); } catch { return; }
    const type = event?.type;
    if (!["reserve", "settle", "complete"].includes(type)) return;
    const { part } = worker;
    if (worker.complete) { reportError(worker, "sent a protocol event after complete"); return; }
    if (type === "reserve") {
      if (typeof event.id !== "string" || !event.id || worker.request || part.hold || !units(event.maxMicros)) {
        reportError(worker, "invalid reserve event or another request is in flight");
        return;
      }
      worker.request = { id: event.id, maxMicros: event.maxMicros };
      waiting.push(worker);
      return;
    }
    if (type === "settle") {
      if (!part.hold || part.hold.id !== event.id || !units(event.actualMicros)) {
        reportError(worker, "invalid settlement or no matching permit");
        return;
      }
      const held = part.hold.maxMicros;
      state.heldMicros -= held;
      state.spentMicros += event.actualMicros;
      part.hold = null;
      save();
      if (event.actualMicros > held) throw new Error(`partition ${JSON.stringify(part.id)} spent more than it reserved. All workers were stopped`);
      send(worker, { type: "settled", id: event.id });
      return;
    }
    if (worker.request || part.hold) { reportError(worker, "cannot complete with an unsettled request"); return; }
    worker.complete = true;
  }

  function launch({ part, index }) {
    const partitionFile = join(dir, `partition-${index + 1}.json`);
    writeFileSync(partitionFile, JSON.stringify(plan.partitions[index], null, 2) + "\n");
    const attempt = `partition-${index + 1}-attempt-${++part.attempts}`;
    const stdout = join(dir, attempt + ".stdout.log"), stderr = join(dir, attempt + ".stderr.log");
    writeFileSync(stdout, "");
    writeFileSync(stderr, "");
    const child = spawn(plan.worker.command, plan.worker.args ?? [], {
      cwd: plan.cwd, detached: !WIN, windowsHide: true,
      env: { ...process.env, FANOUT_JOB_PARTITION_FILE: partitionFile, FANOUT_JOB_RUN_ID: state.runId },
    });
    const worker = { child, part, stdout };
    active.set(index, worker);
    const lines = createInterface({ input: child.stdout, crlfDelay: Infinity });
    lines.on("line", guarded((line) => onLine(worker, line)));
    child.stderr.on("data", guarded((chunk) => appendFileSync(stderr, chunk)));
    child.stdin.on("error", (error) => { if (error.code !== "EPIPE") worker.error ??= error.message; });
    child.on("error", (error) => { worker.error ??= error.message; });
    child.on("close", (code, signal) => {
      worker.closed = true;
      active.delete(index);
      const outstanding = part.hold;
      if (outstanding) {
        state.heldMicros -= outstanding.maxMicros;
        state.spentMicros += outstanding.maxMicros;
        state.uncertainMicros += outstanding.maxMicros;
      }
      const success = !fatal && code === 0 && worker.complete && !worker.error && !outstanding;
      const status = success ? "completed" : aborted ? "aborted" : worker.denied ? "blocked" : "failed";
      const error = success ? null : worker.error || (worker.denied ? "shared budget exhausted"
        : aborted ? "aborted" : code === 0 ? "worker exited without completing the partition"
        : `worker exited with ${code ?? signal}`);
      Object.assign(part, { status, error, pid: null, hold: null });
      guarded(save)();
    });
    Object.assign(part, { status: "running", pid: child.pid ?? null });
    save();
  }

  process.on("SIGINT", abort);
  process.on("SIGTERM", abort);
  try {
    return await new Promise((done, reject) => {
      const progress = guarded(() => {
        if (abortRequested()) abort();
        if (aborted) return;
        admit();
        while (active.size < plan.concurrency && pending.length) launch(pending.shift());
      });
      const tick = () => {
        progress();
        if (active.size || (!aborted && !fatal && pending.length)) return;
        if (fatal) {
          Object.assign(state, { phase: "failed", pid: null, error: fatal.message });
          try { save(); } catch { /* Keep the most recent durable reservations if storage is unavailable. */ }
          reject(fatal);
          return;
        }
        state.phase = aborted ? "aborted" : state.partitions.every((part) => part.status === "completed") ? "completed" : "incomplete";
        state.pid = null;
        try { save(); } catch (error) { reject(error); return; }
        done(state.phase === "completed" ? 0 : aborted ? 130 : 1);
      };
      timer = setInterval(tick, 100);
      tick();
    });
  } finally {
    clearInterval(timer);
    process.off("SIGINT", abort);
    process.off("SIGTERM", abort);
  }
}
