import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, lstat } from "node:fs/promises";
import { resolve } from "node:path";
import { z } from "zod";
import {
  type GoalProgressUpdateWorkerResult,
  GoalProgressUpdateWorkerResultSchema,
} from "../../../packages/contracts/src/index.js";
import { GoalProgressIpcClient } from "../../../packages/ipc/src/index.js";
import {
  type GoalProgressPaths,
  resolveGoalProgressPaths,
} from "../../../packages/store/src/index.js";
import {
  assertGoalProgressExtractedTree,
  assertGoalProgressRealDirectory,
  GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT,
} from "./update-downloader.js";
import {
  type GoalProgressUpdateOperation,
  MacosGoalProgressUpdateOperationStore,
} from "./update-operation.js";
import { MacosGoalProgressUpdateStateStore } from "./update-state-store.js";
import {
  type CreateUpdateWorkerInvocationInput,
  createUpdateWorkerInvocation,
  currentUpdateWorkerInvocationInput,
  notifyUpdateWorkerResult,
  removeUpdateWorker,
  submitUpdateWorker,
  type UpdateWorkerLaunchctlRunner,
} from "./update-worker-launchd.js";
import { fileSha256, readVerifiedRelease } from "./verified-release.js";

export const GOAL_PROGRESS_UPDATE_INSTALL_HANDOFF_COMMAND = "__update-install-handoff";
export const GOAL_PROGRESS_UPDATE_WORKER_TIMEOUT_MS = 10 * 60 * 1_000;
export const GOAL_PROGRESS_UPDATE_WORKER_MAX_OUTPUT_BYTES = 1024 * 1024;

export interface UpdateWorkerProgramResult {
  readonly status: number | null;
  readonly stdout: string;
  readonly stderr: string;
}

export interface UpdateWorkerProgramOptions {
  readonly shell: false;
  readonly timeoutMs: number;
  readonly maxOutputBytes: number;
  readonly env: Readonly<Record<string, string>>;
}

export type UpdateWorkerProgramExecutor = (
  executable: string,
  args: readonly string[],
  options: UpdateWorkerProgramOptions,
) => Promise<UpdateWorkerProgramResult>;

const UpgradeResultSchema = z
  .object({
    schemaVersion: z.literal(1),
    command: z.literal("upgrade"),
    ok: z.literal(true),
    code: z.enum(["UPGRADE_OK", "UPGRADE_ALREADY_CURRENT"]),
    changed: z.boolean(),
    nextStep: z.string().nullable(),
    details: z.record(z.string(), z.unknown()),
  })
  .strict();

export interface CreateUpdateInstallHandoffInvocationInput
  extends CreateUpdateWorkerInvocationInput {}

export function createUpdateInstallHandoffInvocation(
  input: CreateUpdateInstallHandoffInvocationInput,
) {
  return createUpdateWorkerInvocation(input, "install");
}

export function submitUpdateInstallHandoff(
  operationId: string,
  runner?: UpdateWorkerLaunchctlRunner,
): Promise<void> {
  return submitUpdateWorker(
    createUpdateInstallHandoffInvocation(currentUpdateWorkerInvocationInput(operationId)),
    runner,
  );
}

async function executeProgram(
  executable: string,
  args: readonly string[],
  options: UpdateWorkerProgramOptions,
): Promise<UpdateWorkerProgramResult> {
  return new Promise((resolveExecution) => {
    execFile(
      executable,
      [...args],
      {
        encoding: "utf8",
        env: options.env,
        maxBuffer: options.maxOutputBytes,
        shell: options.shell,
        timeout: options.timeoutMs,
      },
      (error, stdout, stderr) => {
        const status =
          error === null
            ? 0
            : "code" in error && typeof error.code === "number"
              ? error.code
              : null;
        resolveExecution({ status, stdout, stderr });
      },
    );
  });
}

async function verifiedInstallTarget(
  paths: GoalProgressPaths,
  operation: GoalProgressUpdateOperation,
): Promise<string> {
  const versionDirectory = resolve(paths.installRoot, "updates", operation.targetVersion);
  const releaseDirectory = resolve(versionDirectory, "release");
  const releaseRoot = resolve(releaseDirectory, GOAL_PROGRESS_UPDATE_ARCHIVE_ROOT);
  try {
    await assertGoalProgressRealDirectory(versionDirectory);
    await assertGoalProgressRealDirectory(releaseDirectory);
    await assertGoalProgressRealDirectory(releaseRoot);
    await assertGoalProgressExtractedTree(releaseDirectory);
    const release = await readVerifiedRelease(releaseRoot);
    if (
      release.releaseVersion !== operation.targetVersion ||
      (await fileSha256(resolve(releaseRoot, "manifest.json"))) !==
        operation.releaseManifestSha256 ||
      release.files.helper.path !== "bin/goal-progress"
    ) {
      throw new Error("release mismatch");
    }
    const helper = resolve(releaseRoot, "bin/goal-progress");
    const metadata = await lstat(helper);
    if (
      !metadata.isFile() ||
      metadata.isSymbolicLink() ||
      (await fileSha256(helper)) !== release.files.helper.sha256
    ) {
      throw new Error("helper mismatch");
    }
    await access(helper, constants.X_OK);
    return helper;
  } catch {
    throw new Error("GOAL_PROGRESS_UPDATE_RELEASE_INVALID");
  }
}

function stableWorkerError(error: unknown): string {
  const value = error instanceof Error ? error.message : String(error);
  return (
    /^(GOAL_PROGRESS_[A-Z0-9_]{2,127})/u.exec(value)?.[1] ?? "GOAL_PROGRESS_UPDATE_INSTALL_FAILED"
  );
}

export interface RunUpdateInstallHandoffOptions {
  readonly homeDirectory: string;
  readonly paths: GoalProgressPaths;
  readonly operationId: string;
  readonly executeProgram?: UpdateWorkerProgramExecutor;
  readonly reportResult?: (result: GoalProgressUpdateWorkerResult) => Promise<void>;
  readonly notificationDelaysMs?: readonly number[];
  readonly removeJob?: () => void | Promise<void>;
  readonly now?: () => Date;
}

async function executeUpdateInstallHandoff(
  options: RunUpdateInstallHandoffOptions,
): Promise<GoalProgressUpdateWorkerResult> {
  const operationStore = new MacosGoalProgressUpdateOperationStore(options.paths);
  const operation = await operationStore.read();
  if (operation === null || operation.operationId !== options.operationId) {
    throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
  }
  const state = await new MacosGoalProgressUpdateStateStore(options.paths).read();
  if (
    state === null ||
    state.phase !== "installing" ||
    state.latestVersion !== operation.targetVersion ||
    state.stateRevision !== operation.requestStateRevision
  ) {
    throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_STATE_MISMATCH");
  }
  const finish = async (
    status: "succeeded" | "failed",
    errorCode: string | null,
  ): Promise<GoalProgressUpdateWorkerResult> => {
    const result = GoalProgressUpdateWorkerResultSchema.parse({
      operationId: operation.operationId,
      targetVersion: operation.targetVersion,
      status,
      errorCode,
      finishedAt: (options.now ?? (() => new Date()))().toISOString(),
    });
    await operationStore.complete(result);
    if (options.reportResult) {
      await notifyUpdateWorkerResult(
        () => options.reportResult?.(result) ?? Promise.resolve(),
        options.notificationDelaysMs,
      );
    }
    return result;
  };
  try {
    const helper = await verifiedInstallTarget(options.paths, operation);
    const command = await (options.executeProgram ?? executeProgram)(
      helper,
      ["upgrade", "--json"],
      {
        shell: false,
        timeoutMs: GOAL_PROGRESS_UPDATE_WORKER_TIMEOUT_MS,
        maxOutputBytes: GOAL_PROGRESS_UPDATE_WORKER_MAX_OUTPUT_BYTES,
        env: {
          HOME: options.homeDirectory,
          GOAL_PROGRESS_ROOT: options.paths.root,
        },
      },
    );
    if (command.status !== 0) {
      throw new Error("GOAL_PROGRESS_UPDATE_UPGRADE_FAILED");
    }
    let parsed: unknown;
    try {
      parsed = JSON.parse(command.stdout);
    } catch {
      throw new Error("GOAL_PROGRESS_UPDATE_UPGRADE_RESULT_INVALID");
    }
    if (!UpgradeResultSchema.safeParse(parsed).success) {
      throw new Error("GOAL_PROGRESS_UPDATE_UPGRADE_RESULT_INVALID");
    }
    return await finish("succeeded", null);
  } catch (error) {
    const code = stableWorkerError(error);
    await finish("failed", code).catch(() => undefined);
    throw new Error(code);
  }
}

export async function runUpdateInstallHandoff(
  options: RunUpdateInstallHandoffOptions,
): Promise<GoalProgressUpdateWorkerResult> {
  try {
    return await executeUpdateInstallHandoff(options);
  } finally {
    await options.removeJob?.();
  }
}

export async function runUpdateInstallHandoffFromEnvironment(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): Promise<void> {
  if (environment.GOAL_PROGRESS_INTERNAL_UPDATE_INSTALL !== "1") {
    throw new Error("GOAL_PROGRESS_UPDATE_INSTALL_HANDOFF_UNAUTHORIZED");
  }
  const homeDirectory = environment.HOME;
  const root = environment.GOAL_PROGRESS_ROOT;
  const operationId = environment.GOAL_PROGRESS_UPDATE_OPERATION_ID;
  if (!homeDirectory || !root || !operationId) {
    throw new Error("GOAL_PROGRESS_UPDATE_WORKER_ENVIRONMENT_INVALID");
  }
  const paths = resolveGoalProgressPaths({ root: resolve(root) });
  const invocation = createUpdateInstallHandoffInvocation(
    currentUpdateWorkerInvocationInput(operationId),
  );
  await runUpdateInstallHandoff({
    homeDirectory: resolve(homeDirectory),
    paths,
    operationId,
    reportResult: async (result) => {
      const client = new GoalProgressIpcClient(paths.helperSocketPath, {
        clientKind: "updater",
        timeoutMs: 5_000,
      });
      await client.request({
        method: "update.worker-result",
        params: result,
      });
    },
    removeJob: () => removeUpdateWorker(invocation),
  });
}
