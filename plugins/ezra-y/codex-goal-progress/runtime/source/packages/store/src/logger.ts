import { rename, stat, unlink } from "node:fs/promises";
import { dirname } from "node:path";
import { z } from "zod";
import { appendDurableLine, ensurePrivateDirectory } from "./atomic.js";
import { GoalProgressStoreError } from "./errors.js";

const GoalProgressLogEntrySchema = z
  .object({
    timestamp: z.string().datetime({ offset: true }),
    level: z.enum(["info", "warn", "error"]),
    event: z.enum([
      "helper.started",
      "helper.stopped",
      "startup.listener.started",
      "startup.listener.stopped",
      "startup.event",
      "startup.handoff",
      "update.activation",
      "update.cleanup.failed",
      "store.initialized",
      "store.replaced",
      "store.migrated",
      "store.applied",
      "store.duplicate",
      "store.recovered",
      "store.error",
      "ipc.request",
      "ipc.response",
      "ipc.error",
      "doctor.completed",
      "activation.requested",
      "hook.native-goal-complete",
      "hook.resume",
      "hook.resume-unavailable",
    ]),
    sessionKey: z
      .string()
      .regex(/^[0-9a-f]{64}$/)
      .optional(),
    sessionTreeKey: z
      .string()
      .regex(/^[0-9a-f]{64}$/)
      .optional(),
    threadKey: z
      .string()
      .regex(/^[0-9a-f]{64}$/)
      .optional(),
    contractId: z.string().trim().min(1).max(128).optional(),
    revision: z.number().int().nonnegative().optional(),
    code: z.string().trim().min(1).max(128).optional(),
    causeCode: z.string().trim().min(1).max(128).optional(),
    trigger: z.enum(["task-publish", "visible-recovery", "finite-retry"]).optional(),
    attempt: z.number().int().nonnegative().optional(),
    count: z.number().int().nonnegative().optional(),
    durationMs: z.number().int().nonnegative().optional(),
    pid: z.number().int().positive().optional(),
    mainPid: z.number().int().positive().optional(),
    port: z.number().int().min(1_024).max(65_535).optional(),
    launchId: z.string().uuid().optional(),
  })
  .strict();

export type GoalProgressLogEntry = z.infer<typeof GoalProgressLogEntrySchema>;
export type GoalProgressLogInput = Omit<GoalProgressLogEntry, "timestamp">;

export interface GoalProgressLoggerOptions {
  readonly maxBytes?: number;
  readonly archiveCount?: number;
  readonly now?: () => Date;
}

function hasCode(error: unknown, code: string): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === code
  );
}

export class GoalProgressLogger {
  readonly #path: string;
  readonly #maxBytes: number;
  readonly #archiveCount: number;
  readonly #now: () => Date;
  #queue: Promise<void> = Promise.resolve();

  constructor(path: string, options: GoalProgressLoggerOptions = {}) {
    this.#path = path;
    this.#maxBytes = options.maxBytes ?? 1_048_576;
    this.#archiveCount = options.archiveCount ?? 2;
    this.#now = options.now ?? (() => new Date());
    if (!Number.isInteger(this.#maxBytes) || this.#maxBytes < 256) {
      throw new GoalProgressStoreError(
        "STORE_PATH_INVALID",
        "Log maxBytes must be an integer of at least 256",
      );
    }
    if (
      !Number.isInteger(this.#archiveCount) ||
      this.#archiveCount < 0 ||
      this.#archiveCount > 10
    ) {
      throw new GoalProgressStoreError(
        "STORE_PATH_INVALID",
        "Log archiveCount must be an integer from 0 to 10",
      );
    }
  }

  async #rotateIfNeeded(additionalBytes: number): Promise<void> {
    let currentBytes = 0;
    try {
      currentBytes = (await stat(this.#path)).size;
    } catch (error) {
      if (!hasCode(error, "ENOENT")) {
        throw error;
      }
    }
    if (currentBytes + additionalBytes <= this.#maxBytes) {
      return;
    }

    if (this.#archiveCount === 0) {
      await unlink(this.#path).catch((error: unknown) => {
        if (!hasCode(error, "ENOENT")) {
          throw error;
        }
      });
      return;
    }
    await unlink(`${this.#path}.${this.#archiveCount}`).catch((error: unknown) => {
      if (!hasCode(error, "ENOENT")) {
        throw error;
      }
    });
    for (let index = this.#archiveCount - 1; index >= 1; index -= 1) {
      try {
        await rename(`${this.#path}.${index}`, `${this.#path}.${index + 1}`);
      } catch (error) {
        if (!hasCode(error, "ENOENT")) {
          throw error;
        }
      }
    }
    try {
      await rename(this.#path, `${this.#path}.1`);
    } catch (error) {
      if (!hasCode(error, "ENOENT")) {
        throw error;
      }
    }
  }

  write(input: GoalProgressLogInput): Promise<void> {
    const operation = this.#queue.then(async () => {
      const entry = GoalProgressLogEntrySchema.safeParse({
        ...input,
        timestamp: this.#now().toISOString(),
      });
      if (!entry.success) {
        throw new GoalProgressStoreError(
          "STORE_COMMAND_INVALID",
          entry.error.issues[0]?.message ?? "Structured log entry is invalid",
        );
      }
      const line = JSON.stringify(entry.data);
      await ensurePrivateDirectory(dirname(this.#path));
      await this.#rotateIfNeeded(Buffer.byteLength(line) + 1);
      await appendDurableLine(this.#path, line);
    });
    this.#queue = operation.catch(() => undefined);
    return operation;
  }
}
