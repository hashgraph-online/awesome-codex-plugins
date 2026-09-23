import { randomUUID } from "node:crypto";
import { rm } from "node:fs/promises";
import { resolve } from "node:path";
import {
  checkGoalProgressUpdateManifest,
  cleanupOrphanedGoalProgressUpdateDownloads,
  compareGoalProgressVersions,
  GOAL_PROGRESS_MACOS_UPDATE_ASSET,
  GOAL_PROGRESS_UPDATE_INSTALL_WORKER_LEASE_MS,
  GOAL_PROGRESS_UPDATE_RESTART_WORKER_LEASE_MS,
  type GoalProgressUpdateManifest,
  type GoalProgressUpdateOperation,
  type GoalProgressUpdateOperationStore,
  type GoalProgressUpdateStateStore,
  MacosGoalProgressUpdateOperationStore,
  openMacosGoalProgressRelease,
  type PreparedGoalProgressUpdate,
  type PrepareGoalProgressUpdateOptions,
  prepareGoalProgressUpdate,
  readCodexCdpRuntimeState,
  submitUpdateInstallHandoff,
  submitUpdateRestartHandoff,
  verifyInstalledGoalProgressUpdate,
} from "../../../platform/macos/src/index.js";
import {
  type GoalProgressUpdateIntent,
  GoalProgressUpdateIntentSchema,
  type GoalProgressUpdateRestartResult,
  GoalProgressUpdateRestartResultSchema,
  type GoalProgressUpdateState,
  GoalProgressUpdateStateSchema,
  type GoalProgressUpdateWorkerResult,
  GoalProgressUpdateWorkerResultSchema,
  StrictSemverSchema,
} from "../../contracts/src/index.js";
import { GOAL_PROGRESS_RELEASE_VERSION } from "../../contracts/src/release-version.js";
import type { GoalProgressPaths } from "../../store/src/index.js";
import {
  evaluateGoalProgressUpdateActivation,
  type GoalProgressUpdateActivationProof,
  type GoalProgressUpdateActivationResult,
} from "./update-activation.js";

export type GoalProgressUpdateIntentAction = "deferred" | "opened-release" | "state-updated";

export interface GoalProgressUpdateIntentResult {
  readonly action: GoalProgressUpdateIntentAction;
  readonly updateState: GoalProgressUpdateState;
  readonly afterResponse?: () => Promise<GoalProgressUpdateState | undefined>;
}

export type GoalProgressUpdateDeliveryMode = "prebuilt-release" | "plugin-marketplace";

export interface GoalProgressUpdateCoordinatorOptions {
  readonly store: GoalProgressUpdateStateStore;
  readonly paths?: GoalProgressPaths;
  readonly operationStore?: GoalProgressUpdateOperationStore;
  readonly currentVersion?: string;
  readonly deliveryMode?: GoalProgressUpdateDeliveryMode;
  readonly now?: () => Date;
  readonly openRelease?: (version: string) => Promise<void>;
  readonly checkForUpdate?: () => Promise<GoalProgressUpdateManifest>;
  readonly prepareUpdate?: (
    options: PrepareGoalProgressUpdateOptions,
  ) => Promise<PreparedGoalProgressUpdate>;
  readonly submitInstallWorker?: (operationId: string) => Promise<void> | void;
  readonly submitRestartWorker?: (operationId: string) => Promise<void> | void;
  readonly readCurrentLaunchId?: () => Promise<string | null>;
  readonly verifyInstalledUpdate?: (operation: GoalProgressUpdateOperation) => Promise<boolean>;
  readonly onActivationResult?: (
    result: GoalProgressUpdateActivationResult,
  ) => Promise<void> | void;
  readonly onStateChange?: (state: GoalProgressUpdateState) => Promise<void> | void;
  readonly operationId?: () => string;
}

function initialUpdateState(currentVersion: string, now: Date): GoalProgressUpdateState {
  return GoalProgressUpdateStateSchema.parse({
    schemaVersion: 1,
    stateRevision: 1,
    currentVersion,
    latestVersion: null,
    phase: "up-to-date",
    checkedAt: null,
    lastSeenUpdateVersion: null,
    promptDismissedForVersion: null,
    downloadedBytes: 0,
    totalBytes: null,
    downloadPercent: null,
    restartRequired: false,
    lastErrorCode: null,
    nextStep: "check",
    updatedAt: now.toISOString(),
  });
}

function updateManifest(version: string): GoalProgressUpdateManifest {
  return {
    schemaVersion: 1,
    version,
    asset: GOAL_PROGRESS_MACOS_UPDATE_ASSET,
    activation: "after-restart",
  };
}

function stableUpdateError(error: unknown, fallback: string): string {
  const value = error instanceof Error ? error.message : String(error);
  return /^(GOAL_PROGRESS_[A-Z0-9_]{2,127})/u.exec(value)?.[1] ?? fallback;
}

const updateActivePhases = new Set<GoalProgressUpdateState["phase"]>([
  "preparing",
  "downloading",
  "verifying",
  "installing",
  "restart-required",
  "restarting",
]);

export class GoalProgressUpdateCoordinator {
  readonly #store: GoalProgressUpdateStateStore;
  readonly #paths: GoalProgressPaths | undefined;
  readonly #operationStore: GoalProgressUpdateOperationStore | undefined;
  readonly #currentVersion: string;
  readonly #deliveryMode: GoalProgressUpdateDeliveryMode;
  readonly #now: () => Date;
  readonly #openRelease: (version: string) => Promise<void>;
  readonly #checkForUpdate: () => Promise<GoalProgressUpdateManifest>;
  readonly #prepareUpdate: (
    options: PrepareGoalProgressUpdateOptions,
  ) => Promise<PreparedGoalProgressUpdate>;
  readonly #submitInstallWorker: (operationId: string) => Promise<void> | void;
  readonly #submitRestartWorker: (operationId: string) => Promise<void> | void;
  readonly #readCurrentLaunchId: () => Promise<string | null>;
  readonly #verifyInstalledUpdate: (operation: GoalProgressUpdateOperation) => Promise<boolean>;
  readonly #onActivationResult: (
    result: GoalProgressUpdateActivationResult,
  ) => Promise<void> | void;
  readonly #onStateChange: (state: GoalProgressUpdateState) => Promise<void> | void;
  readonly #newOperationId: () => string;
  #state: GoalProgressUpdateState | null = null;
  #checkScheduled = false;
  #automaticCheckAttempted = false;
  #queue: Promise<void> = Promise.resolve();
  #operationPromise: Promise<void> | null = null;
  #operationAbortController: AbortController | null = null;
  #activeOperationId: string | null = null;
  #deadlineTimer: ReturnType<typeof setTimeout> | null = null;
  #scheduledDeadlineAt: string | null = null;
  #stopping = false;

  constructor(options: GoalProgressUpdateCoordinatorOptions) {
    // Delivery mode is runtime configuration. Keep the old on-disk state shape for rollback.
    this.#store =
      options.deliveryMode === "plugin-marketplace"
        ? {
            path: options.store.path,
            read: () => options.store.read(),
            write: async (state) => {
              const { deliveryMode, ...persisted } = state;
              const stored = await options.store.write(persisted);
              return deliveryMode ? { ...stored, deliveryMode } : stored;
            },
          }
        : options.store;
    this.#paths = options.paths;
    this.#operationStore =
      options.operationStore ??
      (options.paths === undefined
        ? undefined
        : new MacosGoalProgressUpdateOperationStore(options.paths));
    this.#currentVersion = StrictSemverSchema.parse(
      options.currentVersion ?? GOAL_PROGRESS_RELEASE_VERSION,
    );
    this.#deliveryMode = options.deliveryMode ?? "prebuilt-release";
    this.#now = options.now ?? (() => new Date());
    this.#openRelease = options.openRelease ?? openMacosGoalProgressRelease;
    this.#checkForUpdate = options.checkForUpdate ?? (() => checkGoalProgressUpdateManifest());
    this.#prepareUpdate = options.prepareUpdate ?? prepareGoalProgressUpdate;
    this.#submitInstallWorker = options.submitInstallWorker ?? submitUpdateInstallHandoff;
    this.#submitRestartWorker = options.submitRestartWorker ?? submitUpdateRestartHandoff;
    this.#readCurrentLaunchId =
      options.readCurrentLaunchId ??
      (async () => {
        if (!this.#paths) {
          return null;
        }
        try {
          return (await readCodexCdpRuntimeState(this.#paths.cdpRuntimePath)).launchId;
        } catch {
          return null;
        }
      });
    this.#verifyInstalledUpdate =
      options.verifyInstalledUpdate ??
      ((operation) =>
        this.#paths
          ? verifyInstalledGoalProgressUpdate(this.#paths, operation)
          : Promise.resolve(false));
    this.#onActivationResult = options.onActivationResult ?? (() => undefined);
    this.#onStateChange = options.onStateChange ?? (() => undefined);
    this.#newOperationId = options.operationId ?? randomUUID;
  }

  get currentState(): GoalProgressUpdateState | null {
    return this.#state;
  }

  get activeOperationId(): string | null {
    return this.#activeOperationId;
  }

  async initialize(): Promise<GoalProgressUpdateState> {
    if (this.#paths) {
      await cleanupOrphanedGoalProgressUpdateDownloads(this.#paths);
    }
    let initialized: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      initialized = await this.#reconcileState(await this.#loadOrCreate());
    });
    if (!initialized) {
      throw new Error("GOAL_PROGRESS_UPDATE_STATE_UNAVAILABLE");
    }
    return initialized;
  }

  async handleIntent(intentInput: unknown): Promise<GoalProgressUpdateIntentResult> {
    let result: GoalProgressUpdateIntentResult | undefined;
    await this.#enqueue(async () => {
      const intent = GoalProgressUpdateIntentSchema.parse(intentInput);
      const state = await this.#reconcileState(await this.#loadOrCreate());
      this.#assertKnownVersion(intent, state);
      if (intent.type === "check") {
        result = updateActivePhases.has(state.phase)
          ? { action: "deferred", updateState: state }
          : await this.#beginCheck(state);
        return;
      }
      if (intent.type === "open-release") {
        await this.#openRelease(intent.version);
        result = { action: "opened-release", updateState: state };
        return;
      }
      if (intent.type === "start") {
        if (state.phase === "available" && intent.version === state.latestVersion) {
          if (this.#deliveryMode === "plugin-marketplace") {
            await this.#openRelease(intent.version);
            result = { action: "opened-release", updateState: state };
            return;
          }
          result = await this.#beginUpdate(state, intent.version);
          return;
        }
        if (updateActivePhases.has(state.phase)) {
          result = { action: "deferred", updateState: state };
          return;
        }
        throw new Error("GOAL_PROGRESS_UPDATE_INTENT_NOT_ALLOWED");
      }
      if (intent.type === "retry") {
        if (
          (state.phase !== "download-failed" && state.phase !== "update-failed") ||
          intent.version !== state.latestVersion
        ) {
          throw new Error("GOAL_PROGRESS_UPDATE_INTENT_NOT_ALLOWED");
        }
        if (this.#deliveryMode === "plugin-marketplace") {
          await this.#openRelease(intent.version);
          result = { action: "opened-release", updateState: state };
          return;
        }
        result = await this.#beginUpdate(state, intent.version);
        return;
      }
      if (intent.type === "restart-now") {
        if (state.phase === "restarting" && intent.version === state.latestVersion) {
          result = { action: "deferred", updateState: state };
          return;
        }
        if (state.phase !== "restart-required" || intent.version !== state.latestVersion) {
          throw new Error("GOAL_PROGRESS_UPDATE_INTENT_NOT_ALLOWED");
        }
        const operation = await this.#requireOperationStore().read();
        if (
          operation === null ||
          operation.targetVersion !== intent.version ||
          operation.installStatus !== "succeeded"
        ) {
          throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
        }
        const restarting = await this.#writeDirect(state, {
          phase: "restarting",
          restartRequired: true,
          lastErrorCode: null,
          nextStep: "restart",
        });
        let started = false;
        result = {
          action: "state-updated",
          updateState: restarting,
          afterResponse: async () => {
            if (started) {
              return;
            }
            started = true;
            const operationStore = this.#requireOperationStore();
            const workerDeadlineAt = new Date(
              this.#now().getTime() + GOAL_PROGRESS_UPDATE_RESTART_WORKER_LEASE_MS,
            ).toISOString();
            try {
              const pendingOperation = await operationStore.markRestartPending({
                operationId: operation.operationId,
                targetVersion: operation.targetVersion,
                workerDeadlineAt,
              });
              this.#scheduleDeadlineReconcile(pendingOperation);
              await this.#submitRestartWorker(operation.operationId);
            } catch (error) {
              const code = stableUpdateError(error, "GOAL_PROGRESS_UPDATE_RESTART_SUBMIT_FAILED");
              await operationStore
                .completeRestart({
                  operationId: operation.operationId,
                  targetVersion: operation.targetVersion,
                  status: "failed",
                  finishedAt: this.#now().toISOString(),
                  errorCode: code,
                })
                .catch(() => undefined);
              const reconciled = await this.reconcilePersistedUpdateState();
              await this.#onStateChange(reconciled);
            }
          },
        };
        return;
      }
      if (intent.type === "restart-later") {
        if (state.phase !== "restart-required" || intent.version !== state.latestVersion) {
          throw new Error("GOAL_PROGRESS_UPDATE_INTENT_NOT_ALLOWED");
        }
        if (
          state.lastSeenUpdateVersion === intent.version &&
          state.promptDismissedForVersion === intent.version
        ) {
          result = { action: "deferred", updateState: state };
          return;
        }
        const nextState = GoalProgressUpdateStateSchema.parse({
          ...state,
          stateRevision: state.stateRevision + 1,
          lastSeenUpdateVersion: intent.version,
          promptDismissedForVersion: intent.version,
          updatedAt: this.#now().toISOString(),
        });
        this.#state = await this.#store.write(nextState);
        result = { action: "state-updated", updateState: this.#state };
        return;
      }
      result = { action: "deferred", updateState: state };
    });
    if (!result) {
      throw new Error("GOAL_PROGRESS_UPDATE_INTENT_FAILED");
    }
    return result;
  }

  async handleWorkerResult(
    resultInput: GoalProgressUpdateWorkerResult,
  ): Promise<GoalProgressUpdateState> {
    let completed: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      const result = GoalProgressUpdateWorkerResultSchema.parse(resultInput);
      const operationStore = this.#requireOperationStore();
      const operation = await operationStore.read();
      const state = await this.#loadOrCreate();
      if (
        operation === null ||
        operation.operationId !== result.operationId ||
        operation.targetVersion !== result.targetVersion
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      if (
        state.phase !== "installing" ||
        state.latestVersion !== operation.targetVersion ||
        state.stateRevision !== operation.requestStateRevision
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_STATE_MISMATCH");
      }
      await operationStore.complete(result);
      completed = await this.#reconcileState(state);
    });
    if (!completed) {
      throw new Error("GOAL_PROGRESS_UPDATE_WORKER_RESULT_FAILED");
    }
    return completed;
  }

  async handleRestartResult(
    resultInput: GoalProgressUpdateRestartResult,
  ): Promise<GoalProgressUpdateState> {
    let reconciled: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      const result = GoalProgressUpdateRestartResultSchema.parse(resultInput);
      const operation = await this.#requireOperationStore().read();
      const state = await this.#loadOrCreate();
      if (
        operation === null ||
        operation.operationId !== result.operationId ||
        operation.targetVersion !== result.targetVersion
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      if (state.phase !== "restarting" || state.latestVersion !== operation.targetVersion) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_STATE_MISMATCH");
      }
      if (operation.restartStatus === "pending") {
        await this.#requireOperationStore().completeRestart({
          operationId: operation.operationId,
          targetVersion: operation.targetVersion,
          status: result.status,
          finishedAt: result.finishedAt,
          errorCode: result.errorCode,
        });
      } else if (
        operation.restartStatus !== result.status ||
        operation.restartFinishedAt !== result.finishedAt ||
        operation.restartErrorCode !== result.errorCode
      ) {
        throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH");
      }
      reconciled = await this.#reconcileState(state);
    });
    if (!reconciled) {
      throw new Error("GOAL_PROGRESS_UPDATE_RESTART_RESULT_FAILED");
    }
    return reconciled;
  }

  async completeActivation(
    proofInput: Omit<
      GoalProgressUpdateActivationProof,
      "targetVersion" | "previousLaunchId" | "installedVerified"
    >,
  ): Promise<GoalProgressUpdateState | null> {
    let completed: GoalProgressUpdateState | null = null;
    await this.#enqueue(async () => {
      const state = await this.#reconcileState(await this.#loadOrCreate());
      if (
        (state.phase !== "restart-required" && state.phase !== "restarting") ||
        !state.latestVersion
      ) {
        return;
      }
      const operation = await this.#requireOperationStore().read();
      if (
        operation === null ||
        operation.targetVersion !== state.latestVersion ||
        operation.installStatus !== "succeeded" ||
        operation.restartStatus === "pending"
      ) {
        return;
      }
      const installedVerified = await this.#verifyInstalledUpdate(operation);
      const proof = evaluateGoalProgressUpdateActivation({
        ...proofInput,
        targetVersion: operation.targetVersion,
        previousLaunchId: operation.previousCodexLaunchId,
        installedVerified,
      });
      await this.#onActivationResult(proof);
      if (!proof.complete) {
        return;
      }
      completed = await this.#writeDirect(state, {
        phase: "up-to-date",
        currentVersion: operation.targetVersion,
        latestVersion: null,
        lastSeenUpdateVersion: operation.targetVersion,
        promptDismissedForVersion: null,
        downloadedBytes: 0,
        totalBytes: null,
        downloadPercent: null,
        restartRequired: false,
        lastErrorCode: null,
        nextStep: "check",
      });
    });
    return completed;
  }

  async cleanupCompletedOperation(): Promise<void> {
    const operationStore = this.#requireOperationStore();
    const operation = await operationStore.read();
    const state = await this.#loadOrCreate();
    if (
      operation === null ||
      operation.installStatus !== "succeeded" ||
      state.phase !== "up-to-date" ||
      state.currentVersion !== operation.targetVersion
    ) {
      return;
    }
    await rm(resolve(this.#requirePaths().installRoot, "updates", operation.targetVersion), {
      recursive: true,
      force: true,
    });
    await operationStore.remove();
  }

  async beginAutomaticCheck(): Promise<GoalProgressUpdateIntentResult | null> {
    let result: GoalProgressUpdateIntentResult | null = null;
    await this.#enqueue(async () => {
      if (this.#automaticCheckAttempted) {
        return;
      }
      this.#automaticCheckAttempted = true;
      const state = await this.#loadOrCreate();
      if (updateActivePhases.has(state.phase)) {
        return;
      }
      const checkedAt = state.checkedAt === null ? null : Date.parse(state.checkedAt);
      if (checkedAt !== null && this.#now().getTime() - checkedAt < 24 * 60 * 60 * 1_000) {
        return;
      }
      result = await this.#beginCheck(state);
    });
    return result;
  }

  async waitForBackgroundOperation(): Promise<void> {
    await this.#operationPromise;
  }

  async currentLaunchId(): Promise<string | null> {
    return this.#readCurrentLaunchId();
  }

  async reconcilePersistedUpdateState(): Promise<GoalProgressUpdateState> {
    let reconciled: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      reconciled = await this.#reconcileState(await this.#loadOrCreate());
    });
    if (!reconciled) {
      throw new Error("GOAL_PROGRESS_UPDATE_STATE_UNAVAILABLE");
    }
    return reconciled;
  }

  async stop(): Promise<void> {
    this.#stopping = true;
    this.#operationAbortController?.abort();
    await this.#operationPromise;
    this.#clearDeadlineTimer();
    await this.reconcilePersistedUpdateState();
  }

  async #beginUpdate(
    state: GoalProgressUpdateState,
    version: string,
  ): Promise<GoalProgressUpdateIntentResult> {
    const preparing = GoalProgressUpdateStateSchema.parse({
      ...state,
      stateRevision: state.stateRevision + 1,
      phase: "preparing",
      downloadedBytes: 0,
      totalBytes: null,
      downloadPercent: null,
      restartRequired: false,
      lastErrorCode: null,
      nextStep: null,
      updatedAt: this.#now().toISOString(),
    });
    this.#state = await this.#store.write(preparing);
    let started = false;
    return {
      action: "state-updated",
      updateState: this.#state,
      afterResponse: async () => {
        if (started) {
          return;
        }
        started = true;
        this.#startBackgroundUpdate(version);
      },
    };
  }

  #startBackgroundUpdate(version: string): void {
    if (this.#operationPromise) {
      return;
    }
    const operationId = this.#newOperationId();
    const controller = new AbortController();
    this.#activeOperationId = operationId;
    this.#operationAbortController = controller;
    const operation = this.#runBackgroundUpdate(version, operationId, controller.signal).finally(
      () => {
        if (this.#activeOperationId === operationId) {
          this.#activeOperationId = null;
          this.#operationAbortController = null;
          this.#operationPromise = null;
        }
      },
    );
    this.#operationPromise = operation;
  }

  async #runBackgroundUpdate(
    version: string,
    operationId: string,
    signal: AbortSignal,
  ): Promise<void> {
    let prepared: PreparedGoalProgressUpdate;
    try {
      await this.#writeAndPublish({
        phase: "downloading",
        downloadedBytes: 0,
        totalBytes: null,
        downloadPercent: null,
        lastErrorCode: null,
        nextStep: null,
      });
      prepared = await this.#prepareUpdate({
        manifest: updateManifest(version),
        paths: this.#requirePaths(),
        signal,
        onProgress: async (progress) => {
          if (!signal.aborted) {
            await this.#writeAndPublish({
              phase: "downloading",
              downloadedBytes: progress.downloadedBytes,
              totalBytes: progress.totalBytes,
              downloadPercent: progress.downloadPercent,
              lastErrorCode: null,
              nextStep: null,
            });
          }
        },
        onVerificationStarted: async () => {
          if (!signal.aborted) {
            await this.#writeAndPublish({
              phase: "verifying",
              lastErrorCode: null,
              nextStep: null,
            });
          }
        },
      });
      if (signal.aborted) {
        return;
      }
    } catch (error) {
      if (!signal.aborted) {
        await this.#writeAndPublish({
          phase: "download-failed",
          restartRequired: false,
          lastErrorCode: stableUpdateError(error, "GOAL_PROGRESS_UPDATE_DOWNLOAD_HTTP_FAILED"),
          nextStep: "retry",
        });
      }
      return;
    }
    let operation: GoalProgressUpdateOperation | null = null;
    try {
      const previousCodexLaunchId = await this.#readCurrentLaunchId();
      if (previousCodexLaunchId === null) {
        throw new Error("GOAL_PROGRESS_UPDATE_PREVIOUS_LAUNCH_UNAVAILABLE");
      }
      const installing = await this.#writeAndPublish({
        phase: "installing",
        downloadedBytes: prepared.downloadedBytes,
        totalBytes: prepared.totalBytes,
        downloadPercent: prepared.totalBytes === null ? null : 100,
        restartRequired: false,
        lastErrorCode: null,
        nextStep: null,
      });
      const submittedAt = this.#now();
      operation = await this.#requireOperationStore().write({
        schemaVersion: 1,
        operationId,
        targetVersion: version,
        requestStateRevision: installing.stateRevision,
        releaseManifestSha256: prepared.releaseManifestSha256,
        zipSha256: prepared.zipSha256,
        installStatus: "pending",
        previousCodexLaunchId,
        submittedAt: submittedAt.toISOString(),
        finishedAt: null,
        errorCode: null,
        restartStatus: "not-requested",
        restartFinishedAt: null,
        restartErrorCode: null,
        workerDeadlineAt: new Date(
          submittedAt.getTime() + GOAL_PROGRESS_UPDATE_INSTALL_WORKER_LEASE_MS,
        ).toISOString(),
      });
      this.#scheduleDeadlineReconcile(operation);
      await this.#submitInstallWorker(operation.operationId);
    } catch (error) {
      if (!signal.aborted) {
        const code = stableUpdateError(error, "GOAL_PROGRESS_UPDATE_INSTALL_PREPARATION_FAILED");
        if (operation) {
          await this.#requireOperationStore()
            .complete({
              operationId: operation.operationId,
              targetVersion: operation.targetVersion,
              status: "failed",
              errorCode: code,
              finishedAt: this.#now().toISOString(),
            })
            .catch(() => undefined);
        }
        await this.#writeAndPublish({
          phase: "update-failed",
          restartRequired: false,
          lastErrorCode: code,
          nextStep: "retry",
        });
      }
    }
  }

  async #writeAndPublish(
    patch: Partial<GoalProgressUpdateState>,
  ): Promise<GoalProgressUpdateState> {
    let written: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      written = await this.#writeDirect(await this.#loadOrCreate(), patch);
    });
    if (!written) {
      throw new Error("GOAL_PROGRESS_UPDATE_STATE_UNAVAILABLE");
    }
    await this.#onStateChange(written);
    return written;
  }

  async #writeDirect(
    state: GoalProgressUpdateState,
    patch: Partial<GoalProgressUpdateState>,
  ): Promise<GoalProgressUpdateState> {
    const next = GoalProgressUpdateStateSchema.parse({
      ...state,
      ...patch,
      stateRevision: state.stateRevision + 1,
      updatedAt: this.#now().toISOString(),
    });
    this.#state = await this.#store.write(next);
    return this.#state;
  }

  async #beginCheck(state: GoalProgressUpdateState): Promise<GoalProgressUpdateIntentResult> {
    if (this.#checkScheduled) {
      return { action: "deferred", updateState: state };
    }
    const checking = GoalProgressUpdateStateSchema.parse({
      ...state,
      stateRevision: state.stateRevision + 1,
      phase: "checking",
      lastErrorCode: null,
      nextStep: null,
      updatedAt: this.#now().toISOString(),
    });
    this.#state = await this.#store.write(checking);
    this.#checkScheduled = true;
    let started = false;
    return {
      action: "state-updated",
      updateState: this.#state,
      afterResponse: async () => {
        if (started) {
          return this.#state ?? checking;
        }
        started = true;
        try {
          return await this.#completeCheck();
        } finally {
          this.#checkScheduled = false;
        }
      },
    };
  }

  async #completeCheck(): Promise<GoalProgressUpdateState> {
    let manifest: GoalProgressUpdateManifest | null = null;
    let errorCode: string | null = null;
    try {
      manifest = await this.#checkForUpdate();
    } catch (error) {
      errorCode = stableUpdateError(error, "GOAL_PROGRESS_UPDATE_CHECK_HTTP_FAILED");
    }
    let completed: GoalProgressUpdateState | undefined;
    await this.#enqueue(async () => {
      const state = await this.#loadOrCreate();
      const now = this.#now().toISOString();
      if (manifest === null) {
        completed = GoalProgressUpdateStateSchema.parse({
          ...state,
          stateRevision: state.stateRevision + 1,
          phase: "check-failed",
          lastErrorCode: errorCode,
          nextStep: "check",
          updatedAt: now,
        });
      } else if (compareGoalProgressVersions(manifest.version, this.#currentVersion) > 0) {
        completed = GoalProgressUpdateStateSchema.parse({
          ...state,
          stateRevision: state.stateRevision + 1,
          phase: "available",
          latestVersion: manifest.version,
          checkedAt: now,
          promptDismissedForVersion:
            state.latestVersion === manifest.version ? state.promptDismissedForVersion : null,
          lastErrorCode: null,
          nextStep: "download",
          updatedAt: now,
        });
      } else {
        completed = GoalProgressUpdateStateSchema.parse({
          ...state,
          stateRevision: state.stateRevision + 1,
          phase: "up-to-date",
          latestVersion: null,
          checkedAt: now,
          lastErrorCode: null,
          nextStep: "check",
          updatedAt: now,
        });
      }
      this.#state = await this.#store.write(completed);
    });
    if (!completed) {
      throw new Error("GOAL_PROGRESS_UPDATE_CHECK_FAILED");
    }
    return completed;
  }

  async #reconcileState(state: GoalProgressUpdateState): Promise<GoalProgressUpdateState> {
    if (
      state.phase === "preparing" ||
      state.phase === "downloading" ||
      state.phase === "verifying"
    ) {
      if (this.#operationPromise) {
        return state;
      }
      return this.#writeDirect(state, {
        phase: "download-failed",
        restartRequired: false,
        lastErrorCode: "GOAL_PROGRESS_UPDATE_INTERRUPTED",
        nextStep: "retry",
      });
    }
    if (
      state.phase !== "installing" &&
      state.phase !== "restart-required" &&
      state.phase !== "restarting"
    ) {
      this.#clearDeadlineTimer();
      return state;
    }
    if (this.#operationPromise && state.phase === "installing") {
      return state;
    }
    const operationStore = this.#operationStore;
    let operation: GoalProgressUpdateOperation | null = null;
    try {
      operation = operationStore ? await operationStore.read() : null;
    } catch {
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "update-failed",
        restartRequired: false,
        lastErrorCode: "GOAL_PROGRESS_UPDATE_OPERATION_INVALID",
        nextStep: "retry",
      });
    }
    if (
      operation === null ||
      operation.targetVersion !== state.latestVersion ||
      (state.phase === "installing" && operation.requestStateRevision !== state.stateRevision)
    ) {
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "update-failed",
        restartRequired: false,
        lastErrorCode: "GOAL_PROGRESS_UPDATE_OPERATION_MISMATCH",
        nextStep: "retry",
      });
    }
    if (operation.previousCodexLaunchId === null) {
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "update-failed",
        restartRequired: false,
        lastErrorCode: "GOAL_PROGRESS_UPDATE_PREVIOUS_LAUNCH_UNAVAILABLE",
        nextStep: "retry",
      });
    }
    const deadline = Date.parse(operation.workerDeadlineAt);
    const deadlineExpired = !Number.isFinite(deadline) || this.#now().getTime() > deadline;
    if (state.phase === "installing") {
      if (operation.installStatus === "pending") {
        if (!deadlineExpired) {
          this.#scheduleDeadlineReconcile(operation);
          return state;
        }
        this.#clearDeadlineTimer();
        const code = "GOAL_PROGRESS_UPDATE_WORKER_DEADLINE_EXCEEDED";
        await operationStore
          ?.complete({
            operationId: operation.operationId,
            targetVersion: operation.targetVersion,
            status: "failed",
            errorCode: code,
            finishedAt: this.#now().toISOString(),
          })
          .catch(() => undefined);
        return this.#writeDirect(state, {
          phase: "update-failed",
          restartRequired: false,
          lastErrorCode: code,
          nextStep: "retry",
        });
      }
      if (operation.installStatus === "failed") {
        this.#clearDeadlineTimer();
        return this.#writeDirect(state, {
          phase: "update-failed",
          restartRequired: false,
          lastErrorCode: operation.errorCode ?? "GOAL_PROGRESS_UPDATE_INSTALL_FAILED",
          nextStep: "retry",
        });
      }
      if (!(await this.#verifyInstalledUpdate(operation))) {
        this.#clearDeadlineTimer();
        return this.#writeDirect(state, {
          phase: "update-failed",
          restartRequired: false,
          lastErrorCode: "GOAL_PROGRESS_UPDATE_INSTALL_VERIFY_FAILED",
          nextStep: "retry",
        });
      }
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "restart-required",
        restartRequired: true,
        lastErrorCode: null,
        nextStep: "restart",
      });
    }
    if (
      operation.installStatus !== "succeeded" ||
      !(await this.#verifyInstalledUpdate(operation))
    ) {
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "update-failed",
        restartRequired: false,
        lastErrorCode:
          operation.installStatus === "failed"
            ? (operation.errorCode ?? "GOAL_PROGRESS_UPDATE_INSTALL_FAILED")
            : "GOAL_PROGRESS_UPDATE_INSTALL_VERIFY_FAILED",
        nextStep: "retry",
      });
    }
    if (operation.restartStatus === "failed") {
      this.#clearDeadlineTimer();
      if (
        state.phase === "restart-required" &&
        state.lastErrorCode === operation.restartErrorCode
      ) {
        return state;
      }
      return this.#writeDirect(state, {
        phase: "restart-required",
        restartRequired: true,
        lastErrorCode: operation.restartErrorCode ?? "GOAL_PROGRESS_UPDATE_RESTART_FAILED",
        nextStep: "restart",
      });
    }
    if (operation.restartStatus === "pending") {
      if (deadlineExpired) {
        this.#clearDeadlineTimer();
        const code = "GOAL_PROGRESS_UPDATE_WORKER_DEADLINE_EXCEEDED";
        await operationStore
          ?.completeRestart({
            operationId: operation.operationId,
            targetVersion: operation.targetVersion,
            status: "failed",
            finishedAt: this.#now().toISOString(),
            errorCode: code,
          })
          .catch(() => undefined);
        return this.#writeDirect(state, {
          phase: "restart-required",
          restartRequired: true,
          lastErrorCode: code,
          nextStep: "restart",
        });
      }
      this.#scheduleDeadlineReconcile(operation);
      if (state.phase === "restarting") {
        return state;
      }
      return this.#writeDirect(state, {
        phase: "restarting",
        restartRequired: true,
        lastErrorCode: null,
        nextStep: "restart",
      });
    }
    if (operation.restartStatus === "launched") {
      this.#clearDeadlineTimer();
      return state;
    }
    if (state.phase === "restarting") {
      this.#clearDeadlineTimer();
      return this.#writeDirect(state, {
        phase: "restart-required",
        restartRequired: true,
        lastErrorCode: "GOAL_PROGRESS_UPDATE_RESTART_INTERRUPTED",
        nextStep: "restart",
      });
    }
    this.#clearDeadlineTimer();
    return state;
  }

  #scheduleDeadlineReconcile(operation: GoalProgressUpdateOperation): void {
    if (this.#stopping) {
      return;
    }
    if (this.#scheduledDeadlineAt === operation.workerDeadlineAt) {
      return;
    }
    this.#clearDeadlineTimer();
    const delayMs = Math.max(0, Date.parse(operation.workerDeadlineAt) - this.#now().getTime());
    this.#scheduledDeadlineAt = operation.workerDeadlineAt;
    this.#deadlineTimer = setTimeout(() => {
      this.#deadlineTimer = null;
      this.#scheduledDeadlineAt = null;
      void this.reconcilePersistedUpdateState()
        .then((state) => this.#onStateChange(state))
        .catch(() => undefined);
    }, delayMs);
    this.#deadlineTimer.unref?.();
  }

  #clearDeadlineTimer(): void {
    if (this.#deadlineTimer) {
      clearTimeout(this.#deadlineTimer);
      this.#deadlineTimer = null;
    }
    this.#scheduledDeadlineAt = null;
  }

  #assertKnownVersion(intent: GoalProgressUpdateIntent, state: GoalProgressUpdateState): void {
    if (!("version" in intent)) {
      return;
    }
    if (intent.version !== state.currentVersion && intent.version !== state.latestVersion) {
      throw new Error("GOAL_PROGRESS_UPDATE_VERSION_MISMATCH");
    }
  }

  async #loadOrCreate(): Promise<GoalProgressUpdateState> {
    if (this.#state) {
      return this.#state;
    }
    const stored = await this.#store.read();
    if (stored === null) {
      this.#state = await this.#store.write({
        ...initialUpdateState(this.#currentVersion, this.#now()),
        ...(this.#deliveryMode === "plugin-marketplace"
          ? { deliveryMode: this.#deliveryMode }
          : {}),
      });
      return this.#state;
    }
    this.#state = stored;
    if (this.#deliveryMode === "plugin-marketplace" && stored.deliveryMode !== this.#deliveryMode) {
      // Discard legacy/placeholder check results when switching delivery modes.
      return this.#writeDirect(stored, {
        deliveryMode: this.#deliveryMode,
        currentVersion: this.#currentVersion,
        latestVersion: null,
        checkedAt: null,
        phase: "up-to-date",
        restartRequired: false,
        nextStep: "check",
        lastErrorCode: null,
        downloadedBytes: 0,
        totalBytes: null,
        downloadPercent: null,
      });
    }
    if (stored.currentVersion !== this.#currentVersion && !updateActivePhases.has(stored.phase)) {
      this.#state = await this.#writeDirect(stored, {
        currentVersion: this.#currentVersion,
      });
    }
    return this.#state;
  }

  #requirePaths(): GoalProgressPaths {
    if (!this.#paths) {
      throw new Error("GOAL_PROGRESS_UPDATE_PATHS_UNAVAILABLE");
    }
    return this.#paths;
  }

  #requireOperationStore(): GoalProgressUpdateOperationStore {
    if (!this.#operationStore) {
      throw new Error("GOAL_PROGRESS_UPDATE_OPERATION_STORE_UNAVAILABLE");
    }
    return this.#operationStore;
  }

  #enqueue(work: () => Promise<void>): Promise<void> {
    const run = this.#queue.then(work, work);
    this.#queue = run.catch(() => undefined);
    return run;
  }
}
