import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, renameSync, rmdirSync, unlinkSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { runJob, units } from "./job-runner.mjs";

const HELP = `usage: fanout jobs run <plan.json>
       fanout jobs status <run-id>
       fanout jobs resume <run-id> [--budget-micros <total>]
       fanout jobs abort <run-id>

Runs explicit, nonoverlapping partitions using a shared budget and request rate.
Set FANOUT_JOBS_DIR to override the default .fanout/jobs state directory.`;

const load = (path) => JSON.parse(readFileSync(path, "utf8"));
const positive = (n) => units(n) && n > 0;

function planFrom(path) {
  const plan = load(path);
  if (!plan || typeof plan !== "object") throw new Error("the job plan must be an object");
  const { worker, partitions, concurrency = 1, budgetMicros, requestsPerMinute } = plan;
  if (typeof worker?.command !== "string" || !worker.command.trim()
    || (worker.args != null && (!Array.isArray(worker.args) || !worker.args.every((arg) => typeof arg === "string"))))
    throw new Error("worker must specify an executable command and optionally an array of string args");
  if (!positive(concurrency) || !positive(requestsPerMinute) || !units(budgetMicros))
    throw new Error("set a nonnegative integer budgetMicros and positive integer requestsPerMinute and concurrency");
  if (!Array.isArray(partitions) || !partitions.length) throw new Error("add at least one partition");
  const ids = new Set(), items = new Set();
  for (const partition of partitions) {
    if (typeof partition?.id !== "string" || !partition.id.trim() || ids.has(partition.id))
      throw new Error("each partition must have a unique nonempty string ID");
    ids.add(partition.id);
    if (!Array.isArray(partition.items) || !partition.items.length) throw new Error(`partition ${partition.id} needs at least one item`);
    for (const item of partition.items) {
      if (typeof item !== "string" || !item.trim()) throw new Error("partition items must be nonempty string IDs");
      if (items.has(item)) throw new Error(`item ${JSON.stringify(item)} occurs more than once`);
      items.add(item);
    }
  }
  return { worker, partitions, concurrency, budgetMicros, requestsPerMinute, cwd: process.cwd() };
}

export function pidAlive(pid) {
  if (!Number.isSafeInteger(pid) || pid <= 1) return false;
  try { process.kill(pid, 0); return true; }
  catch (error) { return error.code === "EPERM"; }
}

// Publish a nonempty lock directory atomically. Contenders can remove an expired
// PID marker, but cannot remove a new owner's nonempty directory.
function lock(dir) {
  const target = join(dir, "lock"), pid = String(process.pid);
  const pending = mkdtempSync(join(dir, "lock-"));
  writeFileSync(join(pending, pid), "");
  const remove = (folder, marker) => {
    try { if (marker) unlinkSync(join(folder, marker)); } catch (error) { if (error.code !== "ENOENT") throw error; }
    try { rmdirSync(folder); } catch (error) { if (!["ENOENT", "ENOTEMPTY", "EEXIST"].includes(error.code)) throw error; }
  };
  try {
    for (let attempt = 0; attempt < 3; attempt++) {
      try { renameSync(pending, target); return () => remove(target, pid); }
      catch (error) {
        if (!existsSync(target)) {
          if (["ENOENT", "EPERM", "EACCES"].includes(error.code)) continue;
          throw error;
        }
      }
      let markers;
      try { markers = readdirSync(target); } catch (error) { if (error.code === "ENOENT") continue; throw error; }
      if (markers.length > 1 || (markers[0] && (!/^\d+$/.test(markers[0]) || pidAlive(Number(markers[0]))))) break;
      remove(target, markers[0]);
    }
    throw new Error("another supervisor holds the run lock");
  } finally {
    if (existsSync(pending)) remove(pending, pid);
  }
}

const statePath = (dir) => join(dir, "state.json");
const abortPath = (dir) => join(dir, "abort");

function save(dir, state) {
  const temp = join(dir, `state-${process.pid}.tmp`);
  writeFileSync(temp, JSON.stringify(state, null, 2) + "\n");
  renameSync(temp, statePath(dir));
}

function show(dir, state) {
  const phase = state.phase === "running" && !pidAlive(state.pid) ? "interrupted" : state.phase;
  console.log(`Job ${basename(dir)}: ${phase}`);
  if (state.error) console.log(state.error);
  console.log(`Budget (USD micros): ${state.spentMicros} charged (${state.uncertainMicros} unsettled), ${state.heldMicros} reserved, ${state.budgetMicros} total`);
  for (const part of state.partitions) {
    console.log(`  ${JSON.stringify(part.id)}  ${part.status}  attempts: ${part.attempts}${part.pid ? `  pid: ${part.pid}` : ""}${part.error ? `  ${part.error}` : ""}`);
  }
  console.log(`Logs and state: ${dir}`);
}

async function start(dir, plan, budgetMicros) {
  const unlock = lock(dir);
  try {
    const state = load(statePath(dir));
    if (pidAlive(state.pid)) throw new Error("this job already has a running supervisor");
    const remaining = state.partitions.filter((part) => part.status !== "completed");
    if (!remaining.length) { show(dir, state); return 0; }
    const orphan = remaining.find((part) => pidAlive(part.pid));
    if (orphan) throw new Error(`partition ${JSON.stringify(orphan.id)} still has worker PID ${orphan.pid}. Wait for that worker to stop before resuming.`);
    if (budgetMicros != null) {
      if (budgetMicros < state.budgetMicros) throw new Error("resume budget must be at least the previous total");
      state.budgetMicros = budgetMicros;
    }
    // Any permit that never settled may have been used. Charge its ceiling
    // before issuing more permits, including after an interrupted supervisor.
    state.spentMicros += state.heldMicros;
    state.uncertainMicros += state.heldMicros;
    state.heldMicros = 0;
    for (const part of remaining) Object.assign(part, { status: "pending", pid: null, error: null, hold: null });
    if (existsSync(abortPath(dir))) unlinkSync(abortPath(dir));
    console.log(`Job ${basename(dir)} starting. Logs and state: ${dir}`);
    const result = await runJob(dir, plan, state, {
      save: () => save(dir, state),
      abortRequested: () => existsSync(abortPath(dir)),
    });
    show(dir, state);
    return result;
  } finally { unlock(); }
}

export async function jobs(argv) {
  if (!argv.length || argv.includes("--help") || argv.includes("-h")) { console.log(HELP); return 0; }
  try {
    const [action, target, option, value] = argv;
    if (!target || !["run", "status", "resume", "abort"].includes(action) || argv.length > 4 ||
      (argv.length > 2 && (action !== "resume" || option !== "--budget-micros" || !/^\d+$/.test(value ?? "") || !units(Number(value)))))
      throw new Error(HELP);
    const base = resolve(process.env.FANOUT_JOBS_DIR || ".fanout/jobs");
    if (action === "run") {
      const plan = planFrom(target);
      mkdirSync(base, { recursive: true });
      const dir = mkdtempSync(join(base, "job-"));
      writeFileSync(join(dir, "plan.json"), JSON.stringify(plan, null, 2) + "\n");
      save(dir, { runId: basename(dir), phase: "pending", pid: null, budgetMicros: plan.budgetMicros, spentMicros: 0, heldMicros: 0, uncertainMicros: 0,
        permits: [], partitions: plan.partitions.map(({ id }) => ({ id, status: "pending", attempts: 0 })) });
      return await start(dir, plan);
    }
    if (!/^job-[A-Za-z0-9]+$/.test(target)) throw new Error("invalid job ID");
    const dir = join(base, target), state = load(statePath(dir));
    if (action === "status") { show(dir, state); return 0; }
    if (action === "resume") return await start(dir, load(join(dir, "plan.json")), value == null ? undefined : Number(value));
    if (state.phase !== "running" || !pidAlive(state.pid)) { show(dir, state); return 0; }
    writeFileSync(abortPath(dir), "");
    for (let attempt = 0; attempt < 100; attempt++) {
      await delay(100);
      const latest = load(statePath(dir));
      if (latest.phase !== "running" || latest.pid !== state.pid || !pidAlive(latest.pid)) {
        show(dir, latest);
        return latest.phase === "aborted" ? 0 : 1;
      }
    }
    throw new Error("abort requested. The supervisor has not finished stopping the workers");
  } catch (error) {
    console.error(`fanout jobs: ${error.message}`);
    return 1;
  }
}
