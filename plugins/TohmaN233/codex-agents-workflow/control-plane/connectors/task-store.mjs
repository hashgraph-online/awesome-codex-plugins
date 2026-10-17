import { randomUUID } from 'node:crypto';
import { mkdir, open, readFile, stat, unlink } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { writeDurableJSON } from '../lib/workflow-events.mjs';

export const TERMINAL_STATES = new Set([
  'completed', 'failed', 'cancelled', 'scope_violation', 'abandoned',
]);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

const LOCK_RETRY_MS = 25;
const LOCK_TIMEOUT_MS = 30_000;
const STALE_LOCK_MS = 60_000;

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ownerAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error?.code === 'EPERM';
  }
}

export function resolveConnectorTaskPath(configPath) {
  return join(dirname(configPath), 'connector-tasks.json');
}

export class ConnectorTaskStore {
  constructor({ statePath }) {
    this.statePath = statePath;
    this.lockPath = `${statePath}.lock`;
    this.tasks = new Map();
    this.initialized = false;
    this.initializePromise = null;
    this.operationTail = Promise.resolve();
    this.persistenceError = null;
  }

  async initialize() {
    if (this.persistenceError) throw Object.assign(new Error(`Connector persistence failed; restart and reconcile: ${this.persistenceError.message}`), { code: 'CONNECTOR_STORE_FAILED', cause: this.persistenceError });
    if (this.initialized) return;
    if (this.initializePromise) return this.initializePromise;
    this.initializePromise = this.#withLock(async () => {
      const loaded = await this.#readCommitted({ markRestarted: true });
      this.tasks = loaded.tasks;
      if (loaded.changed) await this.#writeCommitted(this.tasks);
      this.initialized = true;
    });
    try {
      await this.initializePromise;
    } finally {
      this.initializePromise = null;
    }
  }

  async create(fields) {
    await this.initialize();
    return this.#enqueue(async () => this.#withLock(async () => {
      const loaded = await this.#readCommitted();
      const tasks = loaded.tasks;
      const now = new Date().toISOString();
      const task = {
        task_id: randomUUID(),
        state: 'starting',
        created_at: now,
        updated_at: now,
        finished_at: null,
        remote_identity: {},
        terminal_evidence: null,
        execution_cleanup: null,
        result: null,
        error: null,
        ...clone(fields),
      };
      if (tasks.has(task.task_id)) {
        throw Object.assign(new Error(`connector task already exists: ${task.task_id}`), { code: 'TASK_ID_CONFLICT' });
      }
      if (task.workspace) {
        const conflict = [...tasks.values()].find((candidate) =>
          candidate.workspace === task.workspace && !TERMINAL_STATES.has(candidate.state));
        if (conflict) {
          throw Object.assign(new Error(`Workspace already has an active connector task: ${conflict.task_id}`), {
            code: 'CONNECTOR_BUSY',
            actionRequired: 'Reach a terminal or explicitly abandoned state before starting overlapping work.',
          });
        }
      }
      tasks.set(task.task_id, task);
      await this.#writeCommitted(tasks);
      this.tasks = tasks;
      return clone(task);
    }));
  }

  async get(taskId) {
    await this.initialize();
    await this.operationTail;
    this.tasks = (await this.#readCommitted()).tasks;
    const task = this.tasks.get(String(taskId));
    return task ? clone(task) : null;
  }

  async update(taskId, patch, { guard } = {}) {
    await this.initialize();
    return this.#enqueue(async () => this.#withLock(async () => {
      const tasks = (await this.#readCommitted()).tasks;
      const current = tasks.get(String(taskId));
      if (!current) throw new Error(`unknown connector task: ${taskId}`);
      if (guard && !guard(clone(current))) return clone(current);
      const next = { ...current, ...clone(patch), updated_at: new Date().toISOString() };
      if (TERMINAL_STATES.has(next.state) && !next.finished_at) next.finished_at = next.updated_at;
      tasks.set(String(taskId), next);
      await this.#writeCommitted(tasks);
      this.tasks = tasks;
      return clone(next);
    }));
  }

  async activeForWorkspace(workspace) {
    await this.initialize();
    await this.operationTail;
    this.tasks = (await this.#readCommitted()).tasks;
    return [...this.tasks.values()]
      .filter((task) => task.workspace === workspace && !TERMINAL_STATES.has(task.state))
      .map(clone);
  }

  async flush() {
    await this.initialize();
    return this.#enqueue(async () => this.#withLock(async () => {
      // Refresh under the same lock so an explicit flush from one process
      // cannot overwrite records committed by another store instance.
      this.tasks = (await this.#readCommitted()).tasks;
      await this.#writeCommitted(this.tasks);
      return true;
    }));
  }

  #enqueue(operation) {
    const run = this.operationTail.then(operation);
    // Keep the queue settled for cleanup, but poison this instance explicitly:
    // no later read/dispatch may treat uncommitted in-memory tasks as durable.
    this.operationTail = run.then(() => {}, (error) => {
      if (!['CONNECTOR_BUSY', 'TASK_ID_CONFLICT'].includes(error?.code)
        && !String(error?.message || '').startsWith('unknown connector task:')) {
        this.persistenceError ||= error;
      }
    });
    return run;
  }

  async #readCommitted({ markRestarted = false } = {}) {
    let parsed = { version: 1, tasks: [] };
    try {
      parsed = JSON.parse(await readFile(this.statePath, 'utf8'));
    } catch (error) {
      if (error?.code !== 'ENOENT') {
        this.persistenceError ||= error;
        throw error;
      }
    }
    const tasks = new Map();
    let changed = false;
    for (const raw of Array.isArray(parsed.tasks) ? parsed.tasks : []) {
      const task = clone(raw);
      if (markRestarted && !TERMINAL_STATES.has(task.state)) {
        task.state = 'unknown_after_restart';
        task.error = {
          code: 'UNKNOWN_AFTER_RESTART',
          message: 'The connector process restarted before a terminal state was observed.',
          retryable: false,
          action_required: 'Inspect the remote session before abandoning or starting overlapping work.',
        };
        task.updated_at = new Date().toISOString();
        changed = true;
      }
      tasks.set(task.task_id, task);
    }
    return { tasks, changed };
  }

  async #writeCommitted(tasks) {
    if (this.persistenceError) throw this.persistenceError;
    try {
      await mkdir(dirname(this.statePath), { recursive: true, mode: 0o700 });
      await writeDurableJSON(this.statePath, { version: 1, tasks: [...tasks.values()] });
    } catch (error) {
      this.persistenceError ||= error;
      throw error;
    }
  }

  async #withLock(operation) {
    await mkdir(dirname(this.lockPath), { recursive: true, mode: 0o700 });
    const started = Date.now();
    let handle;
    while (!handle) {
      try {
        handle = await open(this.lockPath, 'wx', 0o600);
        try {
          await handle.writeFile(`${process.pid}\n${Date.now()}\n`);
          await handle.sync();
        } catch (error) {
          await handle.close().catch(() => {});
          await unlink(this.lockPath).catch(() => {});
          throw error;
        }
      } catch (error) {
        if (error?.code !== 'EEXIST') throw error;
        try {
          const owner = await stat(this.lockPath);
          if (Date.now() - owner.mtimeMs > STALE_LOCK_MS) {
            let pid = null;
            try { pid = Number.parseInt((await readFile(this.lockPath, 'utf8')).split(/\s+/u)[0], 10); } catch {}
            // Never unlink from a read-then-delete path: two reclaimers could
            // delete a newly acquired lock and admit simultaneous writers.
            if (!ownerAlive(pid)) {
              throw Object.assign(new Error(`Orphaned connector store lock: ${this.lockPath}. Stop all control-plane processes, inspect persisted tasks, then remove this lock before restarting.`), {
                code: 'CONNECTOR_STORE_ORPHANED_LOCK',
              });
            }
          }
        } catch (statError) {
          if (statError?.code !== 'ENOENT') throw statError;
        }
        if (Date.now() - started >= LOCK_TIMEOUT_MS) {
          throw Object.assign(new Error(`Timed out waiting for connector task store lock: ${this.lockPath}`), {
            code: 'CONNECTOR_STORE_LOCK_TIMEOUT',
          });
        }
        await delay(LOCK_RETRY_MS);
      }
    }
    try {
      return await operation();
    } finally {
      await handle.close();
      await unlink(this.lockPath).catch((error) => {
        if (error?.code !== 'ENOENT') throw error;
      });
    }
  }
}
