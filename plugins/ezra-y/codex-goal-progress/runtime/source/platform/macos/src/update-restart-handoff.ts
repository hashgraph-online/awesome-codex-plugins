import { spawnSync } from "node:child_process";
import { rm } from "node:fs/promises";
import { resolve } from "node:path";
import {
  type GoalProgressUpdateRestartResult,
  GoalProgressUpdateRestartResultSchema,
} from "../../../packages/contracts/src/index.js";
import { GoalProgressIpcClient } from "../../../packages/ipc/src/index.js";
import {
  type GoalProgressPaths,
  resolveGoalProgressPaths,
} from "../../../packages/store/src/index.js";
import { createCodexNormalRelaunchInvocation } from "./cdp-controller.js";
import {
  type CodexCdpRuntimeState,
  readCodexCdpRuntimeState,
  stopCodexCdpRuntime,
} from "./cdp-runtime.js";
import {
  type GoalProgressUpdateOperation,
  MacosGoalProgressUpdateOperationStore,
  verifyInstalledGoalProgressUpdate,
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

export const GOAL_PROGRESS_UPDATE_RESTART_HANDOFF_COMMAND = "__update-restart-handoff";

export interface CreateUpdateRestartHandoffInvocationInput
  extends CreateUpdateWorkerInvocationInput {}

export function createUpdateRestartHandoffInvocation(
  input: CreateUpdateRestartHandoffInvocationInput,
) {
  return createUpdateWorkerInvocation(input, "restart");
}

export function submitUpdateRestartHandoff(
  operationId: string,
  runner?: UpdateWorkerLaunchctlRunner,
): Promise<void> {
  return submitUpdateWorker(
    createUpdateRestartHandoffInvocation(currentUpdateWorkerInvocationInput(operationId)),
    runner,
  );
}

async function openCodex(appPath: string): Promise<void> {
  const invocation = createCodexNormalRelaunchInvocation(appPath);
  const result = spawnSync(invocation.command, invocation.args, {
    shell: false,
    stdio: "ignore",
  });
  if (result.status !== 0) {
    throw new Error("GOAL_PROGRESS_UPDATE_CODEX_OPEN_FAILED");
  }
}

function stableRestartError(error: unknown): string {
  const value = error instanceof Error ? error.message : String(error);
  return (
    /^(GOAL_PROGRESS_[A-Z0-9_]{2,127})/u.exec(value)?.[1] ?? "GOAL_PROGRESS_UPDATE_RESTART_FAILED"
  );
}

export interface RunUpdateRestartHandoffOptions {
  readonly paths: GoalProgressPaths;
  readonly operationId: string;
  readonly verifyInstalledUpdate?: (operation: GoalProgressUpdateOperation) => Promise<boolean>;
  readonly readRuntime?: () => Promise<CodexCdpRuntimeState>;
  readonly stopRuntime?: typeof stopCodexCdpRuntime;
  readonly removeRuntimeState?: () => Promise<void>;
  readonly openCodex?: (appPath: string) => Promise<void>;
  readonly reportResult?: (result: GoalProgressUpdateRestartResult) => Promise<void>;
  readonly notificationDelaysMs?: readonly number[];
  readonly removeJob?: () => void | Promise<void>;
  readonly now?: () => Date;
}

export interface UpdateRestartHandoffResult {
  readonly operationId: string;
  readonly targetVersion: string;
  readonly oldLaunchId: string;
}

async function executeUpdateRestartHandoff(
  options: RunUpdateRestartHandoffOptions,
): Promise<UpdateRestartHandoffResult> {
  const operationStore = new MacosGoalProgressUpdateOperationStore(options.paths);
  const operation = await operationStore.read();
  if (
    operation === null ||
    operation.operationId !== options.operationId ||
    operation.installStatus !== "succeeded"
  ) {
    throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
  }
  try {
    const state = await new MacosGoalProgressUpdateStateStore(options.paths).read();
    if (
      state === null ||
      state.phase !== "restarting" ||
      state.latestVersion !== operation.targetVersion
    ) {
      throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_STATE_MISMATCH");
    }
    const installed = await (
      options.verifyInstalledUpdate ??
      ((candidate) => verifyInstalledGoalProgressUpdate(options.paths, candidate))
    )(operation);
    if (!installed) {
      throw new Error("GOAL_PROGRESS_UPDATE_INSTALL_VERIFY_FAILED");
    }
    const runtime = await (
      options.readRuntime ?? (() => readCodexCdpRuntimeState(options.paths.cdpRuntimePath))
    )();
    if (runtime.launchId !== operation.previousCodexLaunchId) {
      throw new Error("GOAL_PROGRESS_UPDATE_RESTART_LAUNCH_MISMATCH");
    }
    await (options.stopRuntime ?? stopCodexCdpRuntime)(runtime);
    await (
      options.removeRuntimeState ?? (() => rm(options.paths.cdpRuntimePath, { force: true }))
    )();
    await (options.openCodex ?? openCodex)(runtime.appPath);
    const finishedAt = (options.now ?? (() => new Date()))().toISOString();
    await operationStore.completeRestart({
      operationId: operation.operationId,
      targetVersion: operation.targetVersion,
      status: "launched",
      finishedAt,
      errorCode: null,
    });
    const result = GoalProgressUpdateRestartResultSchema.parse({
      operationId: operation.operationId,
      targetVersion: operation.targetVersion,
      status: "launched",
      errorCode: null,
      finishedAt,
    });
    if (options.reportResult) {
      await notifyUpdateWorkerResult(
        () => options.reportResult?.(result) ?? Promise.resolve(),
        options.notificationDelaysMs,
      );
    }
    return {
      operationId: operation.operationId,
      targetVersion: operation.targetVersion,
      oldLaunchId: operation.previousCodexLaunchId,
    };
  } catch (error) {
    const code = stableRestartError(error);
    const finishedAt = (options.now ?? (() => new Date()))().toISOString();
    await operationStore
      .completeRestart({
        operationId: operation.operationId,
        targetVersion: operation.targetVersion,
        status: "failed",
        finishedAt,
        errorCode: code,
      })
      .catch(() => undefined);
    const failure = GoalProgressUpdateRestartResultSchema.parse({
      operationId: operation.operationId,
      targetVersion: operation.targetVersion,
      status: "failed",
      errorCode: code,
      finishedAt,
    });
    if (options.reportResult) {
      await notifyUpdateWorkerResult(
        () => options.reportResult?.(failure) ?? Promise.resolve(),
        options.notificationDelaysMs,
      );
    }
    throw new Error(code);
  }
}

export async function runUpdateRestartHandoff(
  options: RunUpdateRestartHandoffOptions,
): Promise<UpdateRestartHandoffResult> {
  try {
    return await executeUpdateRestartHandoff(options);
  } finally {
    await options.removeJob?.();
  }
}

export async function runUpdateRestartHandoffFromEnvironment(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): Promise<void> {
  if (environment.GOAL_PROGRESS_INTERNAL_UPDATE_RESTART !== "1") {
    throw new Error("GOAL_PROGRESS_UPDATE_RESTART_HANDOFF_UNAUTHORIZED");
  }
  const root = environment.GOAL_PROGRESS_ROOT;
  const operationId = environment.GOAL_PROGRESS_UPDATE_OPERATION_ID;
  if (!environment.HOME || !root || !operationId) {
    throw new Error("GOAL_PROGRESS_UPDATE_WORKER_ENVIRONMENT_INVALID");
  }
  const paths = resolveGoalProgressPaths({ root: resolve(root) });
  const invocation = createUpdateRestartHandoffInvocation(
    currentUpdateWorkerInvocationInput(operationId),
  );
  await runUpdateRestartHandoff({
    paths,
    operationId,
    reportResult: async (result) => {
      const client = new GoalProgressIpcClient(paths.helperSocketPath, {
        clientKind: "updater",
        timeoutMs: 5_000,
      });
      await client.request({
        method: "update.restart-result",
        params: result,
      });
    },
    removeJob: () => removeUpdateWorker(invocation),
  });
}
