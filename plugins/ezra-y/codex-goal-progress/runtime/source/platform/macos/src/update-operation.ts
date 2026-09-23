import { randomUUID } from "node:crypto";
import { lstat, mkdir, readFile, readlink, rename, rm, writeFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { z } from "zod";
import {
  GoalProgressUpdateWorkerResultSchema,
  StrictSemverSchema,
} from "../../../packages/contracts/src/index.js";
import {
  atomicWriteFile,
  ensurePrivateDirectory,
  type GoalProgressPaths,
} from "../../../packages/store/src/index.js";
import { fileSha256, readInstalledManifest, readVerifiedRelease } from "./verified-release.js";

const UpdateOperationErrorCodeSchema = z.string().regex(/^[A-Z][A-Z0-9_]{2,127}$/u);

export const GOAL_PROGRESS_UPDATE_INSTALL_WORKER_LEASE_MS = 12 * 60 * 1_000;
export const GOAL_PROGRESS_UPDATE_RESTART_WORKER_LEASE_MS = 2 * 60 * 1_000;
const UPDATE_OPERATION_LOCK_TIMEOUT_MS = 2_000;
const UPDATE_OPERATION_LOCK_STALE_MS = 30_000;
const UPDATE_OPERATION_LOCK_RETRY_MS = 10;

export const GoalProgressUpdateOperationSchema = z
  .object({
    schemaVersion: z.literal(1),
    operationId: z.string().uuid(),
    targetVersion: StrictSemverSchema,
    requestStateRevision: z.number().int().positive(),
    releaseManifestSha256: z.string().regex(/^[0-9a-f]{64}$/u),
    zipSha256: z.string().regex(/^[0-9a-f]{64}$/u),
    installStatus: z.enum(["pending", "succeeded", "failed"]),
    previousCodexLaunchId: z.string().uuid(),
    submittedAt: z.string().datetime({ offset: true }),
    finishedAt: z.string().datetime({ offset: true }).nullable(),
    errorCode: UpdateOperationErrorCodeSchema.nullable(),
    restartStatus: z.enum(["not-requested", "pending", "launched", "failed"]),
    restartFinishedAt: z.string().datetime({ offset: true }).nullable(),
    restartErrorCode: UpdateOperationErrorCodeSchema.nullable(),
    workerDeadlineAt: z.string().datetime({ offset: true }),
  })
  .strict()
  .superRefine((operation, context) => {
    if (
      (operation.installStatus === "pending" &&
        (operation.finishedAt !== null || operation.errorCode !== null)) ||
      (operation.installStatus === "succeeded" &&
        (operation.finishedAt === null || operation.errorCode !== null)) ||
      (operation.installStatus === "failed" &&
        (operation.finishedAt === null || operation.errorCode === null))
    ) {
      context.addIssue({
        code: "custom",
        message: "Update operation result fields do not match installStatus",
      });
    }
    if (
      ((operation.restartStatus === "not-requested" || operation.restartStatus === "pending") &&
        (operation.restartFinishedAt !== null || operation.restartErrorCode !== null)) ||
      (operation.restartStatus === "launched" &&
        (operation.restartFinishedAt === null || operation.restartErrorCode !== null)) ||
      (operation.restartStatus === "failed" &&
        (operation.restartFinishedAt === null || operation.restartErrorCode === null))
    ) {
      context.addIssue({
        code: "custom",
        message: "Update operation restart fields do not match restartStatus",
      });
    }
  });

export type GoalProgressUpdateOperation = z.infer<typeof GoalProgressUpdateOperationSchema>;

export const GoalProgressUpdateOperationResultSchema = GoalProgressUpdateWorkerResultSchema;

export type GoalProgressUpdateOperationResult = z.infer<
  typeof GoalProgressUpdateOperationResultSchema
>;

export interface GoalProgressUpdateOperationStore {
  readonly path: string;
  read(): Promise<GoalProgressUpdateOperation | null>;
  write(operation: GoalProgressUpdateOperation): Promise<GoalProgressUpdateOperation>;
  complete(result: GoalProgressUpdateOperationResult): Promise<GoalProgressUpdateOperation>;
  markRestartPending(input: {
    readonly operationId: string;
    readonly targetVersion: string;
    readonly workerDeadlineAt: string;
  }): Promise<GoalProgressUpdateOperation>;
  completeRestart(input: {
    readonly operationId: string;
    readonly targetVersion: string;
    readonly status: "launched" | "failed";
    readonly finishedAt: string;
    readonly errorCode: string | null;
  }): Promise<GoalProgressUpdateOperation>;
  remove(): Promise<void>;
}

function isNotFound(error: unknown): boolean {
  return (
    error instanceof Error && "code" in error && (error as NodeJS.ErrnoException).code === "ENOENT"
  );
}

function errorCode(error: unknown): string | undefined {
  return error instanceof Error && "code" in error
    ? (error as NodeJS.ErrnoException).code
    : undefined;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolveDelay) => setTimeout(resolveDelay, milliseconds));
}

export function resolveMacosUpdateOperationPath(paths: GoalProgressPaths): string {
  return resolve(paths.installRoot, "update-operation.json");
}

export async function verifyInstalledGoalProgressUpdate(
  paths: GoalProgressPaths,
  operation: GoalProgressUpdateOperation,
): Promise<boolean> {
  try {
    const installed = await readInstalledManifest(paths.installManifestPath);
    const expectedReleaseRoot = resolve(paths.programReleasesRoot, operation.targetVersion);
    if (
      !installed ||
      installed.releaseVersion !== operation.targetVersion ||
      installed.programReleaseRoot !== expectedReleaseRoot ||
      installed.currentReleasePath !== resolve(paths.installRoot, "current") ||
      (await readlink(installed.currentReleasePath)) !== expectedReleaseRoot
    ) {
      return false;
    }
    const release = await readVerifiedRelease(expectedReleaseRoot);
    return (
      release.releaseVersion === operation.targetVersion &&
      (await fileSha256(resolve(expectedReleaseRoot, "manifest.json"))) ===
        operation.releaseManifestSha256
    );
  } catch {
    return false;
  }
}

export class MacosGoalProgressUpdateOperationStore implements GoalProgressUpdateOperationStore {
  readonly path: string;
  readonly #lockPath: string;

  constructor(paths: GoalProgressPaths) {
    this.path = resolveMacosUpdateOperationPath(paths);
    this.#lockPath = `${this.path}.lock`;
  }

  async #lockIsStale(): Promise<boolean> {
    try {
      const owner = JSON.parse(await readFile(resolve(this.#lockPath, "owner.json"), "utf8")) as {
        createdAtMs?: unknown;
      };
      return (
        typeof owner.createdAtMs === "number" &&
        Date.now() - owner.createdAtMs > UPDATE_OPERATION_LOCK_STALE_MS
      );
    } catch {
      try {
        return Date.now() - (await lstat(this.#lockPath)).mtimeMs > UPDATE_OPERATION_LOCK_STALE_MS;
      } catch {
        return false;
      }
    }
  }

  async #acquireLock(): Promise<string> {
    await ensurePrivateDirectory(dirname(this.#lockPath));
    const deadline = Date.now() + UPDATE_OPERATION_LOCK_TIMEOUT_MS;
    const token = randomUUID();
    while (Date.now() <= deadline) {
      try {
        await mkdir(this.#lockPath, { mode: 0o700 });
        try {
          await writeFile(
            resolve(this.#lockPath, "owner.json"),
            `${JSON.stringify({ token, pid: process.pid, createdAtMs: Date.now() })}\n`,
            { encoding: "utf8", flag: "wx", mode: 0o600 },
          );
        } catch (ownerError) {
          await rm(this.#lockPath, { recursive: true, force: true });
          throw ownerError;
        }
        return token;
      } catch (error) {
        if (errorCode(error) !== "EEXIST") {
          throw error;
        }
        if (await this.#lockIsStale()) {
          const stalePath = `${this.#lockPath}.stale.${randomUUID()}`;
          try {
            await rename(this.#lockPath, stalePath);
            await rm(stalePath, { recursive: true, force: true });
          } catch (renameError) {
            if (errorCode(renameError) !== "ENOENT" && errorCode(renameError) !== "EEXIST") {
              throw renameError;
            }
          }
          continue;
        }
        await delay(UPDATE_OPERATION_LOCK_RETRY_MS);
      }
    }
    throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_LOCK_TIMEOUT");
  }

  async #releaseLock(token: string): Promise<void> {
    try {
      const owner = JSON.parse(await readFile(resolve(this.#lockPath, "owner.json"), "utf8")) as {
        token?: unknown;
      };
      if (owner.token === token) {
        await rm(this.#lockPath, { recursive: true, force: true });
      }
    } catch {
      // A stale-lock takeover may already have moved this owner's directory.
    }
  }

  async #withLock<Value>(work: () => Promise<Value>): Promise<Value> {
    const token = await this.#acquireLock();
    try {
      return await work();
    } finally {
      await this.#releaseLock(token);
    }
  }

  async read(): Promise<GoalProgressUpdateOperation | null> {
    try {
      const metadata = await lstat(this.path);
      if (!metadata.isFile() || metadata.isSymbolicLink() || (metadata.mode & 0o777) !== 0o600) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_INVALID");
      }
      return GoalProgressUpdateOperationSchema.parse(JSON.parse(await readFile(this.path, "utf8")));
    } catch (error) {
      if (isNotFound(error)) {
        return null;
      }
      if (error instanceof Error && error.message === "GOAL_PROGRESS_UPDATE_OPERATION_INVALID") {
        throw error;
      }
      throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_INVALID");
    }
  }

  async #writeUnlocked(
    operationInput: GoalProgressUpdateOperation,
  ): Promise<GoalProgressUpdateOperation> {
    const operation = GoalProgressUpdateOperationSchema.parse(operationInput);
    await atomicWriteFile(this.path, `${JSON.stringify(operation, null, 2)}\n`);
    return operation;
  }

  async write(operationInput: GoalProgressUpdateOperation): Promise<GoalProgressUpdateOperation> {
    return this.#withLock(() => this.#writeUnlocked(operationInput));
  }

  async complete(
    resultInput: GoalProgressUpdateOperationResult,
  ): Promise<GoalProgressUpdateOperation> {
    const result = GoalProgressUpdateOperationResultSchema.parse(resultInput);
    return this.#withLock(async () => {
      const operation = await this.read();
      if (
        operation === null ||
        operation.operationId !== result.operationId ||
        operation.targetVersion !== result.targetVersion
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      if (operation.installStatus !== "pending") {
        if (
          operation.installStatus === result.status &&
          operation.finishedAt === result.finishedAt &&
          operation.errorCode === result.errorCode
        ) {
          return operation;
        }
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_ALREADY_FINISHED");
      }
      return this.#writeUnlocked({
        ...operation,
        installStatus: result.status,
        finishedAt: result.finishedAt,
        errorCode: result.errorCode,
      });
    });
  }

  async markRestartPending(input: {
    readonly operationId: string;
    readonly targetVersion: string;
    readonly workerDeadlineAt: string;
  }): Promise<GoalProgressUpdateOperation> {
    return this.#withLock(async () => {
      const operation = await this.read();
      if (
        operation === null ||
        operation.operationId !== input.operationId ||
        operation.targetVersion !== input.targetVersion ||
        operation.installStatus !== "succeeded"
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      if (operation.restartStatus === "pending") {
        return operation;
      }
      return this.#writeUnlocked({
        ...operation,
        restartStatus: "pending",
        restartFinishedAt: null,
        restartErrorCode: null,
        workerDeadlineAt: z.string().datetime({ offset: true }).parse(input.workerDeadlineAt),
      });
    });
  }

  async completeRestart(input: {
    readonly operationId: string;
    readonly targetVersion: string;
    readonly status: "launched" | "failed";
    readonly finishedAt: string;
    readonly errorCode: string | null;
  }): Promise<GoalProgressUpdateOperation> {
    return this.#withLock(async () => {
      const operation = await this.read();
      if (
        operation === null ||
        operation.operationId !== input.operationId ||
        operation.targetVersion !== input.targetVersion ||
        operation.installStatus !== "succeeded"
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      if (
        (input.status === "launched" && input.errorCode !== null) ||
        (input.status === "failed" && input.errorCode === null)
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_INVALID");
      }
      if (
        operation.restartStatus === input.status &&
        operation.restartFinishedAt === input.finishedAt &&
        operation.restartErrorCode === input.errorCode
      ) {
        return operation;
      }
      if (operation.restartStatus !== "pending") {
        throw new Error("GOAL_PROGRESS_UPDATE_RESTART_NOT_PENDING");
      }
      return this.#writeUnlocked({
        ...operation,
        restartStatus: input.status,
        restartFinishedAt: z.string().datetime({ offset: true }).parse(input.finishedAt),
        restartErrorCode: input.errorCode,
      });
    });
  }

  async remove(): Promise<void> {
    await this.#withLock(() => rm(this.path, { force: true }));
  }
}
