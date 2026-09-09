import { constants } from "node:fs";
import { access } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import {
  checkGoalProgressUpdateManifest,
  type GoalProgressUpdateManifest,
  type GoalProgressUpdateOperation,
  type GoalProgressUpdateOperationStore,
  type GoalProgressUpdateStateStore,
  MacosGoalProgressUpdateStateStore,
  type PreparedGoalProgressUpdate,
  type PrepareGoalProgressUpdateOptions,
  requireSingleCodexMacosApp,
} from "../../../platform/macos/src/index.js";
import {
  type CodexAppServerRuntime,
  createCodexAppServerRuntime,
  GoalProgressCdpViewClient,
  type GoalProgressRendererBridgeDoctor,
  type GoalUsageSnapshot,
} from "../../codex-adapter/src/index.js";
import {
  DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
  type GoalContract,
  type GoalContractAny,
  type GoalProgressCommand,
  type GoalProgressTrackingOverlay,
  type GoalProgressUiPreference,
  type GoalProgressUpdateIntent,
  type GoalProgressUpdateState,
  type GoalProgressViewModel,
  GoalProgressViewModelSchema,
  issueRuntimeProof,
  type RuntimeContext,
  type RuntimeIdentity,
  type RuntimeProof,
  verifyRuntimeProof,
} from "../../contracts/src/index.js";
import { selectProgressTarget } from "../../contracts/src/progress-focus.js";
import {
  hashNativeGoalObjective,
  type ProjectViewModelOptions,
  planGoalProgressActivation,
  projectGoalProgressViewModel,
} from "../../core/src/index.js";
import {
  consumeRuntimeProofOnce,
  type GoalProgressActivationResumeResult,
  type GoalProgressIpcAuthorization,
  type GoalProgressIpcConnectionContext,
  type GoalProgressIpcHandler,
  GoalProgressIpcHandlerError,
  type GoalProgressIpcHandlerResult,
  GoalProgressIpcServer,
  loadOrCreateRuntimeProofKey,
} from "../../ipc/src/index.js";
import {
  acquireHelperInstanceLock,
  GoalEventStore,
  type GoalEventStoreOptions,
  type GoalEventStoreWriteSuccess,
  GoalProgressLogger,
  type GoalProgressLoggerOptions,
  type GoalProgressLogInput,
  type GoalProgressPaths,
  type HelperInstanceLock,
  type HelperLockOptions,
  hashGoalProgressIdentity,
  readGoalProgressTrackingOverlay,
  readGoalProgressUiPreference,
  resolveGoalProgressPaths,
  resolveGoalProgressSessionPaths,
  writeGoalProgressTrackingOverlay,
} from "../../store/src/index.js";
import {
  type GoalProgressDoctorResult,
  inspectGoalProgress,
  inspectGoalProgressLocal,
  inspectGoalProgressRuntime,
} from "./helper-doctor.js";
import { helperDiagnosticCauseCode, helperErrorCode } from "./helper-errors.js";
import {
  type HelperActivationIpcRequest,
  type HelperDoctorIpcRequest,
  type HelperHookIpcRequest,
  HelperIpcRouter,
  type HelperRendererIpcRequest,
  type HelperStoreIpcRequest,
  type HelperSystemIpcRequest,
  type HelperUiIpcRequest,
  type HelperUpdateIpcRequest,
} from "./helper-ipc-router.js";
import {
  assertBoundNativeGoal,
  contractNativeGoal,
  createModelContract,
  DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
  detachReasonForNativeGoalError,
  type GoalProgressActivationState,
  type GoalProgressDetachReason,
  GoalProgressSessionCoordinator,
  identityLogFields,
  isUserDetachedActivationState,
  type NativeGoalResolver,
  nativeGoalErrorDetachesContract,
  type ReadThreadIdentity,
  type ResolveCurrentThread,
  readGoalProgressActivationState,
  readGoalProgressActivationStateSnapshot,
  sanitizeModelEvidence,
  sanitizeModelObjective,
  type TrustedNativeGoal,
  trustedNativeGoalFromThreadGoal,
  writeGoalProgressActivationState,
} from "./helper-session-coordinator.js";
import { handleHelperUiIntent } from "./helper-ui-intent.js";
import { connectHelperRendererTargetSource } from "./renderer-bridge-runtime.js";
import { RendererTargetManager } from "./renderer-target-manager.js";
import {
  type GoalProgressStartupListener,
  hasRecoverableGoalProgress,
  type MacosCodexStartupEvent,
  type MacosCodexStartupResponse,
  MacosStartupHandoffController,
  MacosStartupListenerSupervisor,
  resolveStartupListenerExecutable,
} from "./startup-listener.js";
import {
  GoalProgressUpdateCoordinator,
  type GoalProgressUpdateIntentResult,
} from "./update-coordinator.js";
import { ViewModelPublisher, type ViewModelPublisherSink } from "./view-model-publisher.js";

export { type GoalProgressDoctorResult, inspectGoalProgress } from "./helper-doctor.js";
export type {
  NativeGoalResolver,
  ResolveCurrentThread,
  TrustedNativeGoal,
} from "./helper-session-coordinator.js";
export {
  RendererBridgeSupervisor,
  type RendererBridgeSupervisorConnection,
} from "./renderer-bridge-supervisor.js";
export * from "./renderer-target-manager.js";
export * from "./startup-listener.js";
export * from "./update-activation.js";
export * from "./update-coordinator.js";
export {
  ViewModelPublisher,
  type ViewModelPublisherCloseOptions,
  type ViewModelPublisherSink,
} from "./view-model-publisher.js";

export const HELPER_VISIBLE_THREAD_RECOVERY_DELAYS_MS = [
  0, 1_000, 2_000, 5_000, 10_000, 30_000,
] as const;

type UpdateActivationTrigger = "task-publish" | "visible-recovery" | "finite-retry";

interface VisibleThreadOrder {
  lifecycleId: string | null;
  sequence: number;
  retiredLifecycleIds: string[];
}

export function usesSourcePluginRuntime(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): boolean {
  return environment.GOAL_PROGRESS_SOURCE_RUNTIME === "1";
}

export async function sourcePluginUpdateManifest(): Promise<GoalProgressUpdateManifest> {
  // Query the published release, rather than reporting our own version as a remote result.
  return checkGoalProgressUpdateManifest();
}

export interface PreparedGoalProgressStartupListener {
  readonly startupListener: GoalProgressStartupListener;
  readonly startupHandoff: MacosStartupHandoffController;
}

export interface GoalProgressHelperOptions {
  readonly paths?: GoalProgressPaths;
  readonly lock?: HelperLockOptions;
  readonly store?: GoalEventStoreOptions;
  readonly logger?: GoalProgressLoggerOptions;
  readonly runtime?: CodexAppServerRuntime;
  readonly resolveNativeGoal?: NativeGoalResolver;
  readonly resolveCurrentThread?: ResolveCurrentThread;
  readonly readThreadIdentity?: ReadThreadIdentity;
  readonly viewModelSink?: ViewModelPublisherSink;
  readonly rendererDoctor?: (
    expectedThreadId?: string,
    targetId?: string,
  ) => Promise<GoalProgressRendererBridgeDoctor>;
  readonly visibleThreadRecoveryDelaysMs?: readonly number[];
  readonly startupListener?: GoalProgressStartupListener;
  readonly startupHandoff?: MacosStartupHandoffController;
  readonly prepareStartupListener?: () => Promise<PreparedGoalProgressStartupListener>;
  readonly updateStateStore?: GoalProgressUpdateStateStore;
  readonly updateOperationStore?: GoalProgressUpdateOperationStore;
  readonly updateDeliveryMode?: "prebuilt-release" | "plugin-marketplace";
  readonly openUpdateRelease?: (version: string) => Promise<void>;
  readonly checkForUpdate?: () => Promise<GoalProgressUpdateManifest>;
  readonly prepareUpdate?: (
    options: PrepareGoalProgressUpdateOptions,
  ) => Promise<PreparedGoalProgressUpdate>;
  readonly submitInstallWorker?: (operationId: string) => Promise<void> | void;
  readonly submitRestartWorker?: (operationId: string) => Promise<void> | void;
  readonly readCurrentLaunchId?: () => Promise<string | null>;
  readonly verifyInstalledUpdate?: (operation: GoalProgressUpdateOperation) => Promise<boolean>;
  readonly updateOperationId?: () => string;
  readonly sourcePluginRuntime?: boolean;
}

function requestAuthorization(
  params:
    | { readonly auth: GoalProgressIpcAuthorization }
    | {
        readonly runtimeContext: RuntimeContext;
        readonly runtimeProof: RuntimeProof;
      },
): GoalProgressIpcAuthorization {
  return "auth" in params
    ? params.auth
    : {
        kind: "hook-proof",
        runtimeContext: params.runtimeContext,
        runtimeProof: params.runtimeProof,
      };
}

export function resolveGoalProgressCodexCommand(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): string | undefined {
  const command = environment.GOAL_PROGRESS_CODEX_COMMAND?.trim();
  return command ? command : undefined;
}

function projectContract(
  contract: GoalContractAny,
  usage?: GoalUsageSnapshot,
  overlay: GoalProgressTrackingOverlay = DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
): GoalProgressViewModel {
  const projected = projectGoalProgressViewModel(contract, {
    ...viewModelOptionsFromUsage(usage, contract.sessionId),
    ...(overlay.detached ? { detached: true } : {}),
  });
  if (!projected.ok) {
    throw new GoalProgressIpcHandlerError(projected.code, projected.message, contract.revision);
  }
  return projected.viewModel;
}

function viewModelOptionsFromUsage(
  usage: GoalUsageSnapshot | undefined,
  sessionId: string,
): ProjectViewModelOptions {
  if (!usage || usage.threadId !== sessionId) {
    return {};
  }
  return {
    tokenUsage: usage.tokenUsage,
    ...(usage.stale ? { tokenStale: true } : {}),
    ...(usage.unavailable ? { tokenUnavailable: true } : {}),
  };
}

function projectContractState(
  contract: GoalContractAny,
  usage?: GoalUsageSnapshot,
  overlay: GoalProgressTrackingOverlay = DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
): {
  readonly viewModel: GoalProgressViewModel;
  readonly nextTargetId: string | null;
} {
  const viewModel = projectContract(contract, usage, overlay);
  if (viewModel.trackingPhase === "detached") {
    return { viewModel, nextTargetId: null };
  }
  const objectiveView = selectProgressTarget(viewModel.objectives);
  if (!objectiveView) {
    return { viewModel, nextTargetId: null };
  }
  if (objectiveView.status === "blocked") {
    return { viewModel, nextTargetId: objectiveView.id };
  }
  const objective = contract.objectives.find((candidate) => candidate.id === objectiveView.id);
  const item = selectProgressTarget(objective?.items ?? []);
  return { viewModel, nextTargetId: item?.id ?? objectiveView.id };
}

function sanitizeModelCommand(
  command: GoalProgressCommand,
  previous?: GoalContract,
): GoalProgressCommand {
  if (command.type === "update-items") {
    return {
      ...command,
      source: "model",
      changes: command.changes.map((change) => ({
        ...change,
        ...(change.evidence ? { evidence: change.evidence.map(sanitizeModelEvidence) } : {}),
      })),
    };
  }
  if (command.type === "rescope") {
    return {
      ...command,
      source: "model",
      objectives: command.objectives.map((objective) =>
        sanitizeModelObjective(
          objective,
          previous?.objectives.find((stored) => stored.id === objective.id),
        ),
      ),
    };
  }
  return { ...command, source: "model" };
}

export class GoalProgressHelper {
  readonly paths: GoalProgressPaths;
  readonly #lockOptions: HelperLockOptions;
  readonly #logger: GoalProgressLogger;
  readonly #store: GoalEventStore;
  readonly #runtime: CodexAppServerRuntime;
  readonly #sessionCoordinator: GoalProgressSessionCoordinator;
  readonly #rendererDoctor:
    | ((expectedThreadId?: string, targetId?: string) => Promise<GoalProgressRendererBridgeDoctor>)
    | undefined;
  readonly #viewModelPublisher: ViewModelPublisher;
  readonly #updateCoordinator: GoalProgressUpdateCoordinator;
  readonly #enableGoalWatch: boolean;
  readonly #visibleThreadRecoveryDelaysMs: readonly number[];
  readonly #prepareStartupListener:
    | (() => Promise<PreparedGoalProgressStartupListener>)
    | undefined;
  #startupListener: GoalProgressStartupListener | undefined;
  #startupHandoff: MacosStartupHandoffController | undefined;
  readonly #goalUsage = new Map<string, GoalUsageSnapshot>();
  readonly #preparingObjectives = new Map<string, string>();
  readonly #visibleThreadOrderByTarget = new Map<string, VisibleThreadOrder>();
  #lock: HelperInstanceLock | undefined;
  #server: GoalProgressIpcServer | undefined;
  #runtimeProofKey: Uint8Array | undefined;
  #visibleThreadRecoveryTimer: ReturnType<typeof setTimeout> | undefined;
  #lastUpdateStartupHandoff: MacosCodexStartupResponse | undefined;
  readonly #updateActivationRetryTimers = new Map<
    string,
    {
      readonly targetId: string | undefined;
      readonly threadId: string;
      readonly timer: ReturnType<typeof setTimeout>;
    }
  >();
  #updateActivationRunning = false;
  #ready = false;

  get currentUpdateState(): GoalProgressUpdateState | null {
    return this.#viewModelPublisher.currentUpdateState;
  }

  constructor(options: GoalProgressHelperOptions = {}) {
    this.paths = options.paths ?? resolveGoalProgressPaths();
    this.#lockOptions = options.lock ?? {};
    this.#logger = new GoalProgressLogger(this.paths.helperLogPath, options.logger);
    this.#store = new GoalEventStore(this.paths, {
      ...options.store,
      logger: this.#logger,
    });
    const codexCommand = resolveGoalProgressCodexCommand();
    this.#runtime =
      options.runtime ??
      createCodexAppServerRuntime(codexCommand === undefined ? {} : { command: codexCommand });
    this.#enableGoalWatch = options.resolveNativeGoal === undefined;
    const resolveNativeGoal =
      options.resolveNativeGoal ??
      (async (threadId) => trustedNativeGoalFromThreadGoal(await this.#runtime.getGoal(threadId)));
    const resolveCurrentThread =
      options.resolveCurrentThread ?? ((input) => this.#runtime.resolveCurrentThread(input));
    const readThreadIdentity =
      options.readThreadIdentity ?? ((threadId) => this.#runtime.readThreadIdentity(threadId));
    this.#sessionCoordinator = new GoalProgressSessionCoordinator({
      store: this.#store,
      resolveNativeGoal,
      resolveCurrentThread,
      readThreadIdentity,
      consumeRuntimeProof: (runtimeContext, runtimeProof) =>
        this.#consumeRuntimeProof(runtimeContext, runtimeProof),
      log: (input) => this.#log(input),
    });
    this.#viewModelPublisher = new ViewModelPublisher(options.viewModelSink);
    const sourcePluginRuntime = options.sourcePluginRuntime ?? usesSourcePluginRuntime();
    const checkForUpdate =
      options.checkForUpdate ?? (sourcePluginRuntime ? sourcePluginUpdateManifest : undefined);
    this.#updateCoordinator = new GoalProgressUpdateCoordinator({
      store: options.updateStateStore ?? new MacosGoalProgressUpdateStateStore(this.paths),
      paths: this.paths,
      deliveryMode:
        options.updateDeliveryMode ??
        (sourcePluginRuntime ? "plugin-marketplace" : "prebuilt-release"),
      ...(options.updateOperationStore === undefined
        ? {}
        : { operationStore: options.updateOperationStore }),
      ...(options.openUpdateRelease === undefined
        ? {}
        : { openRelease: options.openUpdateRelease }),
      ...(checkForUpdate === undefined ? {} : { checkForUpdate }),
      ...(options.prepareUpdate === undefined ? {} : { prepareUpdate: options.prepareUpdate }),
      ...(options.submitInstallWorker === undefined
        ? {}
        : { submitInstallWorker: options.submitInstallWorker }),
      ...(options.submitRestartWorker === undefined
        ? {}
        : { submitRestartWorker: options.submitRestartWorker }),
      ...(options.readCurrentLaunchId === undefined
        ? {}
        : { readCurrentLaunchId: options.readCurrentLaunchId }),
      ...(options.verifyInstalledUpdate === undefined
        ? {}
        : { verifyInstalledUpdate: options.verifyInstalledUpdate }),
      ...(options.updateOperationId === undefined
        ? {}
        : { operationId: options.updateOperationId }),
      onActivationResult: (result) =>
        this.#log({
          level: "info",
          event: "update.activation",
          code: result.code,
        }),
      onStateChange: (state) => this.#viewModelPublisher.setUpdateState(state),
    });
    this.#rendererDoctor = options.rendererDoctor;
    this.#visibleThreadRecoveryDelaysMs =
      options.visibleThreadRecoveryDelaysMs ?? HELPER_VISIBLE_THREAD_RECOVERY_DELAYS_MS;
    this.#prepareStartupListener = options.prepareStartupListener;
    this.#startupListener = options.startupListener;
    this.#startupHandoff = options.startupHandoff;
  }

  async #log(input: GoalProgressLogInput): Promise<void> {
    await this.#logger.write(input).catch(() => undefined);
  }

  #recordUpdateActivation(
    code: string,
    targetId: string | undefined,
    threadId: string,
    revision?: number,
    causeCode?: string,
    trigger?: UpdateActivationTrigger,
    attempt?: number,
  ): void {
    void this.#log({
      level: "info",
      event: "update.activation",
      code,
      threadKey: hashGoalProgressIdentity(threadId),
      ...(targetId === undefined ? {} : { sessionTreeKey: hashGoalProgressIdentity(targetId) }),
      ...(revision === undefined ? {} : { revision }),
      ...(causeCode === undefined ? {} : { causeCode }),
      ...(trigger === undefined ? {} : { trigger }),
      ...(attempt === undefined ? {} : { attempt }),
    });
  }

  async #handleStartupEvent(event: MacosCodexStartupEvent): Promise<MacosCodexStartupResponse> {
    const startedAt = Date.now();
    await this.#log({
      level: "info",
      event: "startup.event",
      pid: event.pid,
    });
    let response: MacosCodexStartupResponse;
    try {
      if (!this.#startupHandoff) {
        response = {
          schemaVersion: 1,
          pid: event.pid,
          action: "continue",
          code: "STARTUP_HANDLER_UNAVAILABLE",
        };
      } else {
        response = await this.#startupHandoff.handle(
          event,
          await hasRecoverableGoalProgress(this.paths),
          {
            isPending: () => this.#startupListener?.isPending(event.pid) === true,
            isStopped: () => this.#server === undefined,
          },
        );
        if (response.code === "STARTUP_HANDOFF_COMPLETE") {
          await this.#recoverAfterStartupHandoff(response);
        }
      }
    } catch {
      response = {
        schemaVersion: 1,
        pid: event.pid,
        action: "continue",
        code: "STARTUP_HANDLER_FAILED",
      };
    }
    await this.#log({
      level: "info",
      event: "startup.handoff",
      pid: event.pid,
      code: response.code,
      durationMs: Date.now() - startedAt,
      ...(response.mainPid === undefined ? {} : { mainPid: response.mainPid }),
      ...(response.port === undefined ? {} : { port: response.port }),
      ...(response.launchId === undefined ? {} : { launchId: response.launchId }),
    });
    return response;
  }

  async #recoverAfterStartupHandoff(response: MacosCodexStartupResponse): Promise<void> {
    if (this.#visibleThreadRecoveryTimer) {
      clearTimeout(this.#visibleThreadRecoveryTimer);
      this.#visibleThreadRecoveryTimer = undefined;
    }
    this.#clearUpdateActivationRetries();
    this.#lastUpdateStartupHandoff = response;
    await this.#reconcileUpdateState();
    if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      const targets = await this.#viewModelPublisher.reconnectTargets();
      for (const target of targets) {
        await this.#viewModelPublisher.activateTarget(target.targetId, target.threadId);
        if (!target.threadId) {
          continue;
        }
        await this.#restoreVisibleThread(target.threadId).catch(() => "retry");
      }
      return;
    }
    const visibleThreadId = await this.#viewModelPublisher.reconnect();
    if (!visibleThreadId) {
      this.#scheduleVisibleThreadRecovery(0);
      return;
    }
    const restored = await this.#restoreVisibleThread(visibleThreadId).catch(
      (): "retry" => "retry",
    );
    if (restored === "retry") {
      this.#scheduleVisibleThreadRecovery(0);
    }
  }

  async #reconcileUpdateState(): Promise<void> {
    const reconciled = await this.#updateCoordinator.reconcilePersistedUpdateState();
    await this.#viewModelPublisher.setUpdateState(reconciled);
    if (reconciled.phase !== "restart-required" && reconciled.phase !== "restarting") {
      this.#lastUpdateStartupHandoff = undefined;
      this.#clearUpdateActivationRetries();
    }
  }

  async #maybeCompleteUpdateActivation(
    targetId: string | undefined,
    threadId: string,
    trigger: UpdateActivationTrigger = "task-publish",
    attempt = 0,
  ): Promise<"complete" | "retry" | "not-applicable"> {
    const record = (code: string, revision?: number, causeCode?: string): void => {
      this.#recordUpdateActivation(code, targetId, threadId, revision, causeCode, trigger, attempt);
    };
    const startupHandoff = this.#lastUpdateStartupHandoff;
    if (!this.#server) {
      record("UPDATE_ACTIVATION_HELPER_STOPPED");
      return "not-applicable";
    }
    if (!startupHandoff) {
      record("UPDATE_ACTIVATION_HANDOFF_MISSING");
      return "not-applicable";
    }
    if (!this.#rendererDoctor) {
      record("UPDATE_ACTIVATION_DOCTOR_MISSING");
      return "not-applicable";
    }
    if (this.#updateActivationRunning) {
      record("UPDATE_ACTIVATION_ALREADY_RUNNING");
      return "retry";
    }
    const updateState = this.#updateCoordinator.currentState;
    const viewModel =
      targetId === undefined
        ? this.#viewModelPublisher.currentViewModel
        : this.#viewModelPublisher.currentViewModelForTarget(targetId);
    const deliveryCurrent =
      targetId === undefined
        ? this.#viewModelPublisher.deliveryCurrent
        : this.#viewModelPublisher.deliveryCurrentForTarget(targetId);
    if (updateState?.phase !== "restart-required" && updateState?.phase !== "restarting") {
      record("UPDATE_ACTIVATION_STATE_NOT_READY");
      return "not-applicable";
    }
    if (!viewModel) {
      record("UPDATE_ACTIVATION_VIEW_MISSING");
      return targetId !== undefined &&
        this.#viewModelPublisher.currentThreadIdForTarget(targetId) === threadId
        ? "retry"
        : "not-applicable";
    }
    if (viewModel.sessionId !== threadId) {
      record("UPDATE_ACTIVATION_THREAD_MISMATCH", viewModel.revision);
      return "not-applicable";
    }
    if (!deliveryCurrent) {
      record("UPDATE_ACTIVATION_DELIVERY_STALE", viewModel.revision);
      return "retry";
    }
    this.#updateActivationRunning = true;
    try {
      const [currentLaunchId, doctor] = await Promise.all([
        this.#updateCoordinator.currentLaunchId(),
        this.#rendererDoctor(threadId, targetId),
      ]);
      if (!this.#server || this.#lastUpdateStartupHandoff !== startupHandoff) {
        record("UPDATE_ACTIVATION_CONTEXT_CHANGED", viewModel.revision);
        return "not-applicable";
      }
      const currentViewModel =
        targetId === undefined
          ? this.#viewModelPublisher.currentViewModel
          : this.#viewModelPublisher.currentViewModelForTarget(targetId);
      const currentDelivery =
        targetId === undefined
          ? this.#viewModelPublisher.deliveryCurrent
          : this.#viewModelPublisher.deliveryCurrentForTarget(targetId);
      if (
        currentViewModel?.sessionId !== threadId ||
        currentViewModel.revision !== viewModel.revision
      ) {
        record("UPDATE_ACTIVATION_CURRENT_VIEW_CHANGED", viewModel.revision);
        return "not-applicable";
      }
      if (!currentDelivery) {
        record("UPDATE_ACTIVATION_CURRENT_DELIVERY_STALE", viewModel.revision);
        return "retry";
      }
      if (startupHandoff.launchId === undefined || currentLaunchId !== startupHandoff.launchId) {
        record("UPDATE_ACTIVATION_LAUNCH_MISMATCH", viewModel.revision);
        return "retry";
      }
      const completed = await this.#updateCoordinator.completeActivation({
        currentLaunchId,
        startupHandoffCode: startupHandoff.code,
        viewModelRevision: viewModel.revision,
        taskRecovered: true,
        deliveryCurrent,
        renderer: {
          componentVisible: doctor.componentVisible,
          componentCount: doctor.componentCount,
          currentThreadMatched: doctor.currentThreadMatched,
          latestViewModelRevision: doctor.latestViewModelRevision,
          bundleReleaseVersion: doctor.bundleReleaseVersion,
        },
      });
      if (!completed) {
        record("UPDATE_ACTIVATION_COORDINATOR_INCOMPLETE", viewModel.revision);
        return "retry";
      }
      await this.#viewModelPublisher.setUpdateState(completed);
      await this.#cleanupCompletedUpdate();
      this.#lastUpdateStartupHandoff = undefined;
      this.#clearUpdateActivationRetries();
      record("UPDATE_ACTIVATION_COMPLETE", viewModel.revision);
      return "complete";
    } catch (error) {
      record(
        "UPDATE_ACTIVATION_ATTEMPT_FAILED",
        viewModel.revision,
        helperDiagnosticCauseCode(error),
      );
      return "retry";
    } finally {
      this.#updateActivationRunning = false;
    }
  }

  async #attemptUpdateActivationForThread(
    threadId: string,
    trigger: UpdateActivationTrigger = "task-publish",
  ): Promise<"complete" | "retry" | "not-applicable"> {
    const targetIds = this.#viewModelPublisher.multiTargetAwarenessAvailable
      ? this.#viewModelPublisher.targetIdsForThread(threadId)
      : [undefined];
    let retry = false;
    for (const targetId of targetIds) {
      const result = await this.#maybeCompleteUpdateActivation(targetId, threadId, trigger, 0);
      if (result === "complete") {
        return "complete";
      }
      if (result === "retry") {
        retry = true;
        this.#scheduleUpdateActivationRetry(targetId, threadId, 0);
      }
    }
    return retry ? "retry" : "not-applicable";
  }

  #scheduleUpdateActivationRetry(
    targetId: string | undefined,
    threadId: string,
    attempt: number,
  ): void {
    const key = JSON.stringify([targetId ?? null, threadId]);
    if (
      this.#updateActivationRetryTimers.has(key) ||
      !this.#server ||
      !this.#lastUpdateStartupHandoff ||
      attempt >= this.#visibleThreadRecoveryDelaysMs.length
    ) {
      return;
    }
    const delay = this.#visibleThreadRecoveryDelaysMs[attempt];
    if (delay === undefined || !Number.isInteger(delay) || delay < 0 || delay > 60_000) {
      return;
    }
    const timer = setTimeout(() => {
      this.#updateActivationRetryTimers.delete(key);
      if (!this.#server) {
        return;
      }
      void this.#maybeCompleteUpdateActivation(targetId, threadId, "finite-retry", attempt + 1)
        .then((result) => {
          if (result === "retry") {
            this.#scheduleUpdateActivationRetry(targetId, threadId, attempt + 1);
          }
        })
        .catch(() => {
          this.#scheduleUpdateActivationRetry(targetId, threadId, attempt + 1);
        });
    }, delay);
    timer.unref?.();
    this.#updateActivationRetryTimers.set(key, { targetId, threadId, timer });
  }

  #clearUpdateActivationRetriesForTarget(targetId: string, activeThreadId: string | null): void {
    for (const [key, retry] of this.#updateActivationRetryTimers) {
      if (retry.targetId !== targetId || retry.threadId === activeThreadId) {
        continue;
      }
      clearTimeout(retry.timer);
      this.#updateActivationRetryTimers.delete(key);
    }
  }

  #clearUpdateActivationRetries(): void {
    for (const retry of this.#updateActivationRetryTimers.values()) {
      clearTimeout(retry.timer);
    }
    this.#updateActivationRetryTimers.clear();
  }

  async #cleanupCompletedUpdate(): Promise<void> {
    try {
      await this.#updateCoordinator.cleanupCompletedOperation();
    } catch (error) {
      await this.#log({
        level: "error",
        event: "update.cleanup.failed",
        code: helperDiagnosticCauseCode(error),
      });
    }
  }

  #usageFor(contract: GoalContractAny): GoalUsageSnapshot | undefined {
    const threadId = contract.schemaVersion === 2 ? contract.threadId : contract.sessionId;
    return this.#goalUsage.get(threadId);
  }

  #project(
    contract: GoalContractAny,
    overlay: GoalProgressTrackingOverlay = DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
  ): GoalProgressViewModel {
    return projectContract(contract, this.#usageFor(contract), overlay);
  }

  #projectState(
    contract: GoalContractAny,
    overlay: GoalProgressTrackingOverlay = DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
  ): {
    readonly viewModel: GoalProgressViewModel;
    readonly nextTargetId: string | null;
  } {
    return projectContractState(contract, this.#usageFor(contract), overlay);
  }

  #threadIdOf(contract: GoalContractAny): string {
    return contract.schemaVersion === 2 ? contract.threadId : contract.sessionId;
  }

  async #overlayFor(threadId: string): Promise<GoalProgressTrackingOverlay> {
    return readGoalProgressTrackingOverlay(resolveGoalProgressSessionPaths(this.paths, threadId));
  }

  async #activationStateForOverlay(
    threadId: string,
    overlay: GoalProgressTrackingOverlay,
  ): Promise<GoalProgressActivationState> {
    const snapshot = await readGoalProgressActivationStateSnapshot(threadId, this.paths);
    if (!overlay.detached || snapshot.exists) {
      return snapshot.state;
    }
    return writeGoalProgressActivationState(threadId, this.paths, {
      schemaVersion: 1,
      detachReason: "user-detached-tracking",
    });
  }

  async #detachTracking(
    threadId: string,
    detachReason: GoalProgressDetachReason,
  ): Promise<GoalProgressTrackingOverlay> {
    const sessionPaths = resolveGoalProgressSessionPaths(this.paths, threadId);
    const current = await readGoalProgressTrackingOverlay(sessionPaths);
    const activationState = await readGoalProgressActivationState(threadId, this.paths);
    if (
      current.detached &&
      (activationState.detachReason === detachReason ||
        activationState.detachReason === "user-dismissed-preparation" ||
        activationState.detachReason === "user-detached-tracking")
    ) {
      return current;
    }
    await writeGoalProgressActivationState(threadId, this.paths, {
      schemaVersion: 1,
      detachReason,
    });
    const detached = await writeGoalProgressTrackingOverlay(sessionPaths, {
      ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
      detached: true,
    });
    if (this.#enableGoalWatch) {
      this.#runtime.setPollingMode(
        this.#preparingObjectives.has(threadId) ? "collapsed-or-background" : "stopped",
        threadId,
      );
    }
    return detached;
  }

  #rememberChangedGoalPreparation(
    threadId: string,
    nativeGoal: TrustedNativeGoal | null,
    error: unknown,
  ): void {
    if (
      nativeGoal?.threadId === threadId &&
      error instanceof GoalProgressIpcHandlerError &&
      (error.code === "NATIVE_GOAL_REPLACED" || error.code === "NATIVE_GOAL_OBJECTIVE_CHANGED")
    ) {
      this.#preparingObjectives.set(threadId, nativeGoal.objective);
    }
  }

  async #reconcileDetachedPreparation(
    contract: GoalContract,
    nativeGoal: TrustedNativeGoal | null,
    overlay: GoalProgressTrackingOverlay,
  ): Promise<GoalProgressTrackingOverlay> {
    const activationState = await this.#activationStateForOverlay(contract.threadId, overlay);
    if (isUserDetachedActivationState(activationState) || !nativeGoal) {
      return overlay;
    }
    try {
      assertBoundNativeGoal(contract, nativeGoal, contract.revision);
      this.#preparingObjectives.delete(contract.threadId);
      await writeGoalProgressActivationState(
        contract.threadId,
        this.paths,
        DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
      );
      return writeGoalProgressTrackingOverlay(
        resolveGoalProgressSessionPaths(this.paths, contract.threadId),
        DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
      );
    } catch (error) {
      if (nativeGoalErrorDetachesContract(error)) {
        this.#rememberChangedGoalPreparation(contract.threadId, nativeGoal, error);
        return this.#detachTracking(contract.threadId, detachReasonForNativeGoalError(error));
      }
      return overlay;
    }
  }

  async #assertBoundNativeGoalOrDetach(
    contract: GoalContract,
    nativeGoal: TrustedNativeGoal | null,
  ): Promise<TrustedNativeGoal> {
    try {
      return assertBoundNativeGoal(contract, nativeGoal, contract.revision);
    } catch (error) {
      if (nativeGoalErrorDetachesContract(error)) {
        this.#rememberChangedGoalPreparation(contract.threadId, nativeGoal, error);
        await this.#detachTracking(contract.threadId, detachReasonForNativeGoalError(error));
      }
      throw error;
    }
  }

  async #overlayForCurrentNativeGoal(
    contract: GoalContractAny,
    usage?: GoalUsageSnapshot,
  ): Promise<GoalProgressTrackingOverlay> {
    const threadId = this.#threadIdOf(contract);
    const overlay = await this.#overlayFor(threadId);
    if (contract.schemaVersion !== 2 || usage?.stale) {
      return overlay;
    }
    if (contract.nativeGoal.status === "complete" && usage && !usage.goal) {
      return overlay;
    }
    let nativeGoal: TrustedNativeGoal | null;
    if (usage) {
      nativeGoal = trustedNativeGoalFromThreadGoal(usage.goal);
    } else {
      try {
        nativeGoal = await this.#sessionCoordinator.readNativeGoal(threadId, contract.revision);
      } catch {
        return overlay;
      }
    }
    if (contract.nativeGoal.status === "complete" && !nativeGoal) {
      return overlay;
    }
    if (overlay.detached) {
      return this.#reconcileDetachedPreparation(contract, nativeGoal, overlay);
    }
    try {
      assertBoundNativeGoal(contract, nativeGoal, contract.revision);
      return overlay;
    } catch (error) {
      this.#rememberChangedGoalPreparation(threadId, nativeGoal, error);
      return nativeGoalErrorDetachesContract(error)
        ? this.#detachTracking(threadId, detachReasonForNativeGoalError(error))
        : overlay;
    }
  }

  async #applyPollingMode(
    threadId: string,
    preference: GoalProgressUiPreference,
    overlay: GoalProgressTrackingOverlay,
    contract?: GoalContractAny,
  ): Promise<void> {
    if (!this.#enableGoalWatch) {
      return;
    }
    const usage = this.#goalUsage.get(threadId);
    if (preference.hidden) {
      this.#runtime.setPollingMode("stopped", threadId);
      return;
    }
    if (overlay.detached) {
      this.#runtime.setPollingMode(
        this.#preparingObjectives.has(threadId) ? "collapsed-or-background" : "stopped",
        threadId,
      );
      return;
    }
    if (!usage?.goal) {
      this.#runtime.setPollingMode("stopped", threadId);
      return;
    }
    if (usage.goal.status === "complete") {
      this.#runtime.setPollingMode("stopped", threadId);
      return;
    }
    if (
      contract?.phase === "paused" ||
      usage.goal.status === "paused" ||
      usage.goal.status === "blocked" ||
      usage.goal.status === "usageLimited" ||
      usage.goal.status === "budgetLimited"
    ) {
      this.#runtime.setPollingMode("paused", threadId);
      return;
    }
    if (preference.collapsed) {
      this.#runtime.setPollingMode("collapsed-or-background", threadId);
      return;
    }
    this.#runtime.setPollingMode("active", threadId);
  }

  #watchThread(threadId: string): void {
    if (!this.#enableGoalWatch) {
      return;
    }
    this.#runtime.watchGoalUsage(threadId, (snapshot) => {
      this.#goalUsage.set(snapshot.threadId, snapshot);
      void this.#publishUsageChange(snapshot).catch(() => undefined);
    });
  }

  #unwatchThreadIfUnused(threadId: string | null | undefined): void {
    if (
      !threadId ||
      !this.#enableGoalWatch ||
      !this.#viewModelPublisher.multiTargetAwarenessAvailable ||
      this.#viewModelPublisher.targetIdsForThread(threadId).length > 0
    ) {
      return;
    }
    this.#runtime.unwatchGoalUsage?.(threadId);
  }

  async #publishVerified(threadId: string, viewModel: GoalProgressViewModel): Promise<void> {
    if (viewModel.trackingPhase === "completed") {
      if (this.#enableGoalWatch) {
        this.#runtime.setPollingMode("stopped", threadId);
      }
      await this.#viewModelPublisher.clear(threadId);
      return;
    }
    if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      if (this.#viewModelPublisher.targetIdsForThread(threadId).length === 0) {
        return;
      }
    } else if (this.#viewModelPublisher.visibleThreadAwarenessAvailable) {
      const visibleThreadId = await this.#viewModelPublisher.recoverVisibleThreadId();
      if (
        (visibleThreadId !== undefined && visibleThreadId !== threadId) ||
        (visibleThreadId === undefined &&
          this.#viewModelPublisher.currentThreadId !== undefined &&
          this.#viewModelPublisher.currentThreadId !== threadId)
      ) {
        return;
      }
    }
    if (!this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      await this.#viewModelPublisher.activateThread(threadId);
    }
    await this.#viewModelPublisher.setUiPreference(await readGoalProgressUiPreference(this.paths));
    await this.#viewModelPublisher.publish(threadId, viewModel);
    const deliveryCurrent = this.#viewModelPublisher.multiTargetAwarenessAvailable
      ? this.#viewModelPublisher
          .targetIdsForThread(threadId)
          .every((targetId) => this.#viewModelPublisher.deliveryCurrentForTarget(targetId))
      : this.#viewModelPublisher.deliveryCurrent;
    if (!deliveryCurrent && !this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      this.#scheduleVisibleThreadRecovery(0);
      return;
    }
    await this.#attemptUpdateActivationForThread(threadId);
    void this.#maybeStartAutomaticUpdateCheck().catch(() => undefined);
  }

  async #maybeStartAutomaticUpdateCheck(): Promise<void> {
    if (
      !this.#ready ||
      this.#startupListener?.health().ready !== true ||
      !this.#viewModelPublisher.hasPublishedViewModel ||
      !this.#viewModelPublisher.hasCurrentDelivery
    ) {
      return;
    }
    const checking = await this.#updateCoordinator.beginAutomaticCheck();
    if (!checking) {
      return;
    }
    await this.#viewModelPublisher.setUpdateState(checking.updateState);
    const finalState = await checking.afterResponse?.();
    if (finalState) {
      await this.#viewModelPublisher.setUpdateState(finalState);
    }
  }

  async #syncNativeGoalStatus(snapshot: GoalUsageSnapshot): Promise<GoalContractAny | null> {
    const loaded = await this.#store.load(snapshot.threadId);
    const contract = loaded.contract;
    if (contract?.schemaVersion !== 2 || snapshot.stale) {
      return contract;
    }
    if (contract.nativeGoal.status === "complete" && !snapshot.goal) {
      return contract;
    }
    const overlay = await this.#overlayFor(snapshot.threadId);
    if (overlay.detached || !snapshot.goal) {
      return contract;
    }
    const nativeGoal = trustedNativeGoalFromThreadGoal(snapshot.goal);
    try {
      assertBoundNativeGoal(contract, nativeGoal, contract.revision);
    } catch (error) {
      if (nativeGoalErrorDetachesContract(error)) {
        this.#rememberChangedGoalPreparation(snapshot.threadId, nativeGoal, error);
        await this.#detachTracking(snapshot.threadId, detachReasonForNativeGoalError(error));
      }
      return contract;
    }
    if (!nativeGoal) {
      return contract;
    }
    const nextNativeGoal = contractNativeGoal(nativeGoal);
    if (JSON.stringify(nextNativeGoal) === JSON.stringify(contract.nativeGoal)) {
      return contract;
    }
    const syncKey = hashGoalProgressIdentity(
      `${contract.contractId}:${contract.revision}:${snapshot.goal.status}:${snapshot.goal.updatedAt}`,
    ).slice(0, 24);
    const occurredAt = new Date(
      Math.max(Date.parse(contract.updatedAt), snapshot.goal.updatedAt * 1_000),
    ).toISOString();
    const applied = await this.#store.apply({
      contractId: contract.contractId,
      sessionId: contract.sessionId,
      expectedRevision: contract.revision,
      eventId: `evt-native-sync-${syncKey}`,
      requestId: `req-native-sync-${syncKey}`,
      turnId: "system-native-goal-watch",
      occurredAt,
      source: "system",
      type: "sync-native-goal",
      nativeGoal: nextNativeGoal,
    });
    if (applied.ok) {
      return applied.contract;
    }
    return (await this.#store.load(snapshot.threadId)).contract;
  }

  #transientView(
    threadId: string,
    objective: string,
    phase: "preparing" | "error" | "detached",
    options: {
      readonly preparingStep?: "reading-goal" | "preparing-checklist" | "establishing-baseline";
      readonly errorCode?: string;
    } = {},
  ): GoalProgressViewModel {
    return GoalProgressViewModelSchema.parse({
      schemaVersion: 2,
      contractId: `gp_prepare_${hashGoalProgressIdentity(threadId).slice(0, 16)}`,
      sessionId: threadId,
      revision: 0,
      scopeRevision: 0,
      trackingPhase: phase,
      objective,
      overallProgressBps: null,
      overallPercent: null,
      finalVerificationPending: false,
      objectives: [],
      optionalObjectives: [],
      maxVisibleObjectives: 3,
      ...(options.preparingStep === undefined ? {} : { preparingStep: options.preparingStep }),
      ...(options.errorCode === undefined ? {} : { errorCode: options.errorCode }),
    });
  }

  async #publishPreparing(
    threadId: string,
    objective: string,
    preparingStep: "reading-goal" | "preparing-checklist" | "establishing-baseline",
  ): Promise<GoalProgressViewModel> {
    this.#preparingObjectives.set(threadId, objective);
    const viewModel = this.#transientView(threadId, objective, "preparing", {
      preparingStep,
    });
    await this.#publishVerified(threadId, viewModel);
    return viewModel;
  }

  async #publishPreparationError(threadId: string, code: string): Promise<GoalProgressViewModel> {
    const objective = this.#preparingObjectives.get(threadId) ?? "当前 Goal";
    const viewModel = this.#transientView(threadId, objective, "error", {
      errorCode: code,
    });
    await this.#publishVerified(threadId, viewModel);
    return viewModel;
  }

  async #publishResumeUnavailable(
    contract: GoalContractAny,
    code: string,
  ): Promise<GoalProgressViewModel> {
    const threadId = this.#threadIdOf(contract);
    const {
      blockedReason: _blockedReason,
      token: _token,
      ...confirmed
    } = projectContract(contract);
    const viewModel = GoalProgressViewModelSchema.parse({
      ...confirmed,
      trackingPhase: "error",
      finalVerificationPending: false,
      objectives: [],
      optionalObjectives: [],
      errorCode: code,
    });
    await this.#publishVerified(threadId, viewModel);
    return viewModel;
  }

  async #resumeTracking(threadId: string): Promise<GoalProgressActivationResumeResult> {
    const loaded = await this.#store.load(threadId);
    const contract = loaded.contract;
    if (!contract || contract.phase === "completed") {
      return { status: "inactive" };
    }
    const contractThreadId = contract.schemaVersion === 2 ? contract.threadId : contract.sessionId;
    if (contractThreadId !== threadId) {
      return { status: "inactive" };
    }
    const persistedOverlay = await this.#overlayFor(threadId);
    const activationState = await this.#activationStateForOverlay(threadId, persistedOverlay);
    if (isUserDetachedActivationState(activationState)) {
      if (!persistedOverlay.detached && activationState.detachReason) {
        await this.#detachTracking(threadId, activationState.detachReason);
      }
      return { status: "inactive" };
    }
    let nativeGoal: TrustedNativeGoal | null = null;
    try {
      nativeGoal = await this.#sessionCoordinator.readNativeGoal(threadId);
      if (!nativeGoal) {
        if (contract.schemaVersion === 2) {
          await this.#detachTracking(threadId, "native-goal-ended");
        }
        return { status: "inactive" };
      }
      if (contract.schemaVersion === 2) {
        assertBoundNativeGoal(contract, nativeGoal, contract.revision);
      } else if (nativeGoal.objective !== contract.nativeGoal.objective) {
        return { status: "inactive" };
      }
    } catch (error) {
      if (
        nativeGoalErrorDetachesContract(error) ||
        (error instanceof GoalProgressIpcHandlerError &&
          error.code === "NATIVE_GOAL_OBJECTIVE_TOO_LONG")
      ) {
        if (nativeGoalErrorDetachesContract(error)) {
          this.#rememberChangedGoalPreparation(threadId, nativeGoal, error);
          await this.#detachTracking(threadId, detachReasonForNativeGoalError(error));
        }
        return { status: "inactive" };
      }
      const causeCode = helperDiagnosticCauseCode(error);
      await this.#publishResumeUnavailable(contract, "GOAL_PROGRESS_TEMPORARILY_UNAVAILABLE").catch(
        () => undefined,
      );
      return {
        status: "temporarily_unavailable",
        reasonCode: causeCode,
      };
    }
    this.#watchThread(threadId);
    const usage = await this.#refreshUsage(threadId);
    const latest = (await this.#store.load(threadId)).contract ?? contract;
    const overlay = await this.#overlayForCurrentNativeGoal(latest, usage);
    await this.#publishVerified(threadId, this.#projectState(latest, overlay).viewModel);
    return {
      status: "active",
      contractId: latest.contractId,
      revision: latest.revision,
    };
  }

  async #recoverVisibleThread(): Promise<"done" | "retry"> {
    if (!this.#server) {
      return "done";
    }
    await this.#reconcileUpdateState();
    const threadId = await this.#viewModelPublisher.recoverVisibleThreadId();
    if (!threadId) {
      return "retry";
    }
    if (await this.#rendererMatchesVisibleThread(threadId)) {
      return (await this.#maybeCompleteUpdateActivation(
        undefined,
        threadId,
        "visible-recovery",
        0,
      )) === "retry"
        ? "retry"
        : "done";
    }
    return this.#restoreVisibleThread(threadId);
  }

  async #rendererMatchesVisibleThread(threadId: string): Promise<boolean> {
    if (this.#viewModelPublisher.currentThreadId !== threadId) {
      return false;
    }
    if (!this.#rendererDoctor) {
      return true;
    }
    try {
      const doctor = await this.#rendererDoctor(threadId);
      const expectedRevision = this.#viewModelPublisher.currentRevision;
      return (
        doctor.componentVisible === true &&
        doctor.componentCount === 1 &&
        doctor.currentThreadMatched === true &&
        doctor.displayMode !== null &&
        doctor.displayMode !== "hidden" &&
        expectedRevision !== undefined &&
        doctor.latestViewModelRevision === expectedRevision &&
        this.#viewModelPublisher.deliveryCurrent
      );
    } catch {
      return false;
    }
  }

  async #restoreVisibleThread(threadId: string): Promise<"done" | "retry"> {
    const resumed = await this.#resumeTracking(threadId);
    if (resumed.status === "temporarily_unavailable") {
      return "retry";
    }
    if (resumed.status === "inactive" || !this.#rendererDoctor) {
      return "done";
    }
    if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      return "done";
    }
    try {
      const doctor = await this.#rendererDoctor(threadId);
      if (
        doctor.componentVisible === true &&
        doctor.componentCount === 1 &&
        doctor.currentThreadMatched === true &&
        doctor.displayMode !== null &&
        doctor.displayMode !== "hidden" &&
        doctor.latestViewModelRevision === resumed.revision &&
        this.#viewModelPublisher.deliveryCurrent
      ) {
        return (await this.#maybeCompleteUpdateActivation(
          undefined,
          threadId,
          "visible-recovery",
          0,
        )) === "retry"
          ? "retry"
          : "done";
      }
    } catch {
      // The next bounded attempt reconnects the Bridge and republishes the same full snapshot.
    }
    await this.#viewModelPublisher.markDeliveryStale();
    return "retry";
  }

  #scheduleVisibleThreadRecovery(attempt: number): void {
    if (!this.#server || this.#visibleThreadRecoveryTimer) {
      return;
    }
    if (attempt >= this.#visibleThreadRecoveryDelaysMs.length) {
      return;
    }
    const delay = this.#visibleThreadRecoveryDelaysMs[attempt];
    if (delay === undefined || !Number.isInteger(delay) || delay < 0 || delay > 60_000) {
      return;
    }
    this.#visibleThreadRecoveryTimer = setTimeout(() => {
      this.#visibleThreadRecoveryTimer = undefined;
      void this.#recoverVisibleThread()
        .then((result) => {
          if (result === "retry") {
            this.#scheduleVisibleThreadRecovery(attempt + 1);
          }
        })
        .catch(() => {
          this.#scheduleVisibleThreadRecovery(attempt + 1);
        });
    }, delay);
    this.#visibleThreadRecoveryTimer.unref?.();
  }

  async #publishUsageChange(snapshot: GoalUsageSnapshot): Promise<void> {
    if (
      this.#viewModelPublisher.multiTargetAwarenessAvailable
        ? this.#viewModelPublisher.targetIdsForThread(snapshot.threadId).length === 0
        : snapshot.threadId !== this.#viewModelPublisher.currentThreadId
    ) {
      return;
    }
    const contract = await this.#syncNativeGoalStatus(snapshot);
    if (!contract) {
      return;
    }
    const overlay = await this.#overlayForCurrentNativeGoal(contract, snapshot);
    await this.#applyPollingMode(
      snapshot.threadId,
      await readGoalProgressUiPreference(this.paths),
      overlay,
      contract,
    );
    if (overlay.detached) {
      const preparingObjective = this.#preparingObjectives.get(snapshot.threadId);
      if (preparingObjective) {
        await this.#publishPreparing(snapshot.threadId, preparingObjective, "preparing-checklist");
      } else {
        await this.#viewModelPublisher.clear(snapshot.threadId);
      }
      return;
    }
    await this.#publishVerified(snapshot.threadId, this.#projectState(contract, overlay).viewModel);
    if (
      !this.#viewModelPublisher.multiTargetAwarenessAvailable &&
      !this.#viewModelPublisher.deliveryCurrent
    ) {
      this.#scheduleVisibleThreadRecovery(0);
    }
  }

  async #refreshUsage(threadId: string): Promise<GoalUsageSnapshot | undefined> {
    if (!this.#enableGoalWatch) {
      return this.#goalUsage.get(threadId);
    }
    try {
      const snapshot = await this.#runtime.refreshGoalUsage(threadId);
      this.#goalUsage.set(threadId, snapshot);
      const contract = await this.#syncNativeGoalStatus(snapshot);
      if (contract) {
        await this.#applyPollingMode(
          threadId,
          await readGoalProgressUiPreference(this.paths),
          await this.#overlayForCurrentNativeGoal(contract, snapshot),
          contract,
        );
      } else if (!snapshot.goal || snapshot.goal.status === "complete") {
        this.#runtime.setPollingMode("stopped", threadId);
      }
      return snapshot;
    } catch {
      return this.#goalUsage.get(threadId);
    }
  }

  async #inspectRuntimeDoctor(sessionId?: string): Promise<GoalProgressDoctorResult["runtime"]> {
    return inspectGoalProgressRuntime(sessionId, {
      rendererDoctor: this.#rendererDoctor,
      store: this.#store,
      refreshUsage: (threadId) => this.#refreshUsage(threadId),
      readNativeGoal: (threadId, revision) =>
        this.#sessionCoordinator.readNativeGoal(threadId, revision),
      startupListener: this.#startupListener,
    });
  }

  async #key(): Promise<Uint8Array> {
    this.#runtimeProofKey ??= await loadOrCreateRuntimeProofKey(this.paths.runtimeRoot);
    return this.#runtimeProofKey;
  }

  async #consumeRuntimeProof(
    runtimeContext: RuntimeContext,
    runtimeProof: RuntimeProof,
  ): Promise<boolean> {
    const nowMs = Date.now();
    return (
      (await verifyRuntimeProof(runtimeContext, runtimeProof, await this.#key(), nowMs)) &&
      (await consumeRuntimeProofOnce(this.paths.runtimeRoot, runtimeProof, nowMs))
    );
  }

  async #handleSystemIpc(request: HelperSystemIpcRequest): Promise<GoalProgressIpcHandlerResult> {
    if (request.method === "ping") {
      return {
        revision: null,
        result: {
          status: "ok",
          pid: this.#lock?.identity.pid ?? process.pid,
          instanceId: this.#lock?.identity.instanceId ?? null,
          ready: this.#ready,
        },
      };
    }
    if (request.method === "runtime-proof.issue") {
      const proof = await issueRuntimeProof(
        request.params.runtimeContext,
        request.params.toolUseId,
        await this.#key(),
      );
      return { revision: null, result: { runtimeProof: proof } };
    }
    const consumed = await this.#consumeRuntimeProof(
      request.params.runtimeContext,
      request.params.runtimeProof,
    );
    return { revision: null, result: { valid: consumed } };
  }

  async #handleHookIpc(request: HelperHookIpcRequest): Promise<GoalProgressIpcHandlerResult> {
    if (request.method === "activation.resume") {
      const resumed = await this.#resumeTracking(request.params.hookSessionId);
      if (resumed.status === "active") {
        await this.#log({
          level: "info",
          event: "hook.resume",
          sessionKey: hashGoalProgressIdentity(request.params.hookSessionId),
          sessionTreeKey: hashGoalProgressIdentity(request.params.hookSessionId),
          threadKey: hashGoalProgressIdentity(request.params.hookSessionId),
          contractId: resumed.contractId,
          revision: resumed.revision,
        });
      }
      const responseRevision =
        resumed.status === "active"
          ? resumed.revision
          : ((await this.#store.load(request.params.hookSessionId)).contract?.revision ?? null);
      return {
        revision: responseRevision,
        result: resumed,
      };
    }
    if (request.params.event === "ResumeTemporarilyUnavailable") {
      const loaded = await this.#store.load(request.params.hookSessionId);
      if (!loaded.contract || loaded.contract.phase === "completed") {
        return { revision: loaded.contract?.revision ?? null, result: { accepted: false } };
      }
      await this.#log({
        level: "warn",
        event: "hook.resume-unavailable",
        sessionKey: hashGoalProgressIdentity(request.params.hookSessionId),
        sessionTreeKey: hashGoalProgressIdentity(request.params.hookSessionId),
        threadKey: hashGoalProgressIdentity(request.params.hookSessionId),
        contractId: loaded.contract.contractId,
        revision: loaded.contract.revision,
        causeCode: request.params.reasonCode,
        count: 1,
      });
      return { revision: loaded.contract.revision, result: { accepted: true } };
    }
    if (request.params.event === "NativeGoalCompleted") {
      let identity: RuntimeIdentity;
      try {
        identity = await this.#sessionCoordinator.resolveCurrentThread({
          sessionTreeId: request.params.hookSessionId,
          turnId: request.params.turnId,
          cwd: request.params.cwd,
          model: request.params.model,
        });
      } catch {
        return { revision: null, result: { accepted: false } };
      }
      const loaded = await this.#store.load(identity.threadId);
      const contract = loaded.contract;
      if (!contract) {
        return { revision: null, result: { accepted: false } };
      }
      if (contract.nativeGoal.status === "complete") {
        return { revision: contract.revision, result: { accepted: true } };
      }
      const requestKey = hashGoalProgressIdentity(request.params.toolUseId);
      const applied = await this.#store.apply({
        contractId: contract.contractId,
        sessionId: identity.threadId,
        expectedRevision: contract.revision,
        eventId: `evt-native-complete-${requestKey}`,
        requestId: `req-native-complete-${requestKey}`,
        turnId: identity.turnId,
        occurredAt: new Date().toISOString(),
        source: "system",
        type: "sync-native-goal",
        nativeGoal: {
          objective: contract.nativeGoal.objective,
          status: "complete",
          ...(contract.nativeGoal.tokenBudget === undefined
            ? {}
            : { tokenBudget: contract.nativeGoal.tokenBudget }),
        },
      });
      if (!applied.ok) {
        return {
          revision: applied.currentRevision,
          result: { accepted: false },
        };
      }
      const sessionPaths = resolveGoalProgressSessionPaths(this.paths, identity.threadId);
      const existingOverlay = await this.#overlayFor(identity.threadId);
      const activationState = await this.#activationStateForOverlay(
        identity.threadId,
        existingOverlay,
      );
      if (isUserDetachedActivationState(activationState)) {
        if (this.#enableGoalWatch) {
          this.#runtime.setPollingMode("collapsed-or-background", identity.threadId);
        }
        await this.#log({
          level: "info",
          event: "hook.native-goal-complete",
          ...identityLogFields(identity),
          contractId: applied.contract.contractId,
          revision: applied.contract.revision,
        });
        return {
          revision: applied.contract.revision,
          result: { accepted: true },
        };
      }
      await writeGoalProgressActivationState(
        identity.threadId,
        this.paths,
        DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
      );
      const overlay = await writeGoalProgressTrackingOverlay(sessionPaths, {
        ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
        detached: false,
      });
      if (this.#enableGoalWatch) {
        this.#runtime.setPollingMode("collapsed-or-background", identity.threadId);
      }
      const projected = this.#projectState(applied.contract, overlay);
      await this.#publishVerified(identity.threadId, projected.viewModel);
      await this.#log({
        level: "info",
        event: "hook.native-goal-complete",
        ...identityLogFields(identity),
        contractId: applied.contract.contractId,
        revision: applied.contract.revision,
      });
      return {
        revision: applied.contract.revision,
        result: { accepted: true },
      };
    }
    return { revision: null, result: { accepted: false } };
  }

  async #handleActivationIpc(
    request: HelperActivationIpcRequest,
  ): Promise<GoalProgressIpcHandlerResult> {
    const identity = await this.#sessionCoordinator.authorizeSessionRequest(
      requestAuthorization(request.params),
    );
    await this.#log({
      level: "info",
      event: "activation.requested",
      ...identityLogFields(identity),
    });
    const nativeGoal = await this.#sessionCoordinator.readNativeGoal(identity.threadId);
    const loaded = await this.#store.load(identity.threadId);
    const current = await this.#sessionCoordinator.contractForWrite(
      identity,
      loaded.contract,
      loaded.contract?.revision ?? null,
      nativeGoal,
    );
    let contractId: string | null = null;
    let revision: number | null = null;
    let contractState: "none" | "matched" | "changed" = "none";
    if (current && nativeGoal) {
      contractId = current.contractId;
      revision = current.revision;
      try {
        assertBoundNativeGoal(current, nativeGoal, current.revision);
        contractState = "matched";
      } catch (error) {
        if (!nativeGoalErrorDetachesContract(error)) {
          throw error;
        }
        contractState = "changed";
        this.#rememberChangedGoalPreparation(identity.threadId, nativeGoal, error);
      }
    }
    const plan = planGoalProgressActivation({
      nativeGoalPresent: nativeGoal !== null,
      contractState,
    });
    if (current && plan.progressAction === "get") {
      const sessionPaths = resolveGoalProgressSessionPaths(this.paths, identity.threadId);
      const overlay = await this.#overlayFor(identity.threadId);
      const activationState = await this.#activationStateForOverlay(identity.threadId, overlay);
      if (isUserDetachedActivationState(activationState)) {
        await writeGoalProgressActivationState(
          identity.threadId,
          this.paths,
          DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
        );
        const activeOverlay = await writeGoalProgressTrackingOverlay(sessionPaths, {
          ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
          detached: false,
        });
        await this.#publishVerified(
          identity.threadId,
          this.#projectState(current, activeOverlay).viewModel,
        );
      }
    }
    if (plan.preparing) {
      if (nativeGoal) {
        const sessionPaths = resolveGoalProgressSessionPaths(this.paths, identity.threadId);
        await writeGoalProgressActivationState(
          identity.threadId,
          this.paths,
          DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
        );
        await writeGoalProgressTrackingOverlay(sessionPaths, {
          ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
          detached: false,
        });
        if (plan.progressAction === "rescope-or-replace") {
          await this.#detachTracking(identity.threadId, "stale-contract");
        }
        await this.#publishPreparing(identity.threadId, nativeGoal.objective, "reading-goal");
        await this.#publishPreparing(
          identity.threadId,
          nativeGoal.objective,
          "preparing-checklist",
        );
      }
    }
    return {
      revision,
      result: {
        ...plan,
        contractId,
        revision,
        ...(nativeGoal ? { currentNativeGoal: nativeGoal.objective } : {}),
      },
    };
  }

  async #handleStoreLoad(
    request: Extract<HelperStoreIpcRequest, { method: "store.load" }>,
  ): Promise<GoalProgressIpcHandlerResult> {
    const identity = await this.#sessionCoordinator.authorizeSessionRequest(
      requestAuthorization(request.params),
      request.params.sessionId,
    );
    let loaded = await this.#store.load(identity.threadId);
    const recovery = {
      snapshotRecovered: loaded.snapshotRecovered,
      tornTailRepaired: loaded.tornTailRepaired,
    };
    let contract = loaded.contract;
    if (contract?.schemaVersion === 1) {
      try {
        contract = await this.#sessionCoordinator.contractForWrite(
          identity,
          contract,
          contract.revision,
        );
      } catch {
        contract = loaded.contract;
      }
    }
    if (contract) {
      this.#watchThread(identity.threadId);
      const usage = await this.#refreshUsage(identity.threadId);
      loaded = await this.#store.load(identity.threadId);
      contract = loaded.contract ?? contract;
      const overlay = await this.#overlayForCurrentNativeGoal(contract, usage);
      const { contract: _ignored, ...latestDiagnostics } = loaded;
      const diagnostics = {
        ...latestDiagnostics,
        snapshotRecovered: recovery.snapshotRecovered || latestDiagnostics.snapshotRecovered,
        tornTailRepaired: recovery.tornTailRepaired || latestDiagnostics.tornTailRepaired,
      };
      const preparingObjective = this.#preparingObjectives.get(identity.threadId);
      if (overlay.detached && preparingObjective) {
        await this.#publishPreparing(identity.threadId, preparingObjective, "preparing-checklist");
        return {
          revision: contract.revision,
          result: {
            ...diagnostics,
            viewModel: null,
            nextTargetId: null,
            previousContractId: contract.contractId,
            previousRevision: contract.revision,
            currentNativeGoal: preparingObjective,
          },
        };
      }
      const projected = this.#projectState(contract, overlay);
      await this.#publishVerified(identity.threadId, projected.viewModel);
      return {
        revision: contract.revision,
        result: {
          ...diagnostics,
          ...projected,
        },
      };
    }
    const { contract: _ignored, ...diagnostics } = loaded;
    return {
      revision: null,
      result: {
        ...diagnostics,
        viewModel: null,
        nextTargetId: null,
      },
    };
  }

  async #handleRendererIpc(
    request: HelperRendererIpcRequest,
  ): Promise<GoalProgressIpcHandlerResult> {
    if (request.method === "renderer.visible-thread") {
      const targetId = request.params.targetId;
      if (
        this.#viewModelPublisher.multiTargetAwarenessAvailable &&
        !this.#viewModelPublisher.hasTarget(targetId)
      ) {
        throw new GoalProgressIpcHandlerError(
          "RENDERER_TARGET_UNKNOWN",
          "Renderer target is not managed by this Helper",
        );
      }
      const sequence = request.params.sequence;
      const lifecycleId = request.params.lifecycleId;
      let order = this.#visibleThreadOrderByTarget.get(targetId);
      if (!order) {
        order = {
          lifecycleId: lifecycleId ?? null,
          sequence: 0,
          retiredLifecycleIds: [],
        };
        this.#visibleThreadOrderByTarget.set(targetId, order);
      } else if (lifecycleId !== undefined && lifecycleId !== order.lifecycleId) {
        if (order.retiredLifecycleIds.includes(lifecycleId)) {
          const currentThreadId = this.#viewModelPublisher.currentThreadIdForTarget(targetId);
          return {
            revision: this.#viewModelPublisher.currentRevisionForTarget(targetId) ?? null,
            result: { status: currentThreadId ? "done" : "unknown" },
          };
        }
        if (order.lifecycleId) {
          order.retiredLifecycleIds.push(order.lifecycleId);
          order.retiredLifecycleIds = order.retiredLifecycleIds.slice(-16);
        }
        order.lifecycleId = lifecycleId;
        order.sequence = 0;
      }
      if (sequence !== undefined && sequence <= order.sequence) {
        const currentThreadId = this.#viewModelPublisher.currentThreadIdForTarget(targetId);
        return {
          revision: this.#viewModelPublisher.currentRevisionForTarget(targetId) ?? null,
          result: { status: currentThreadId ? "done" : "unknown" },
        };
      }
      if (sequence !== undefined) {
        order.sequence = sequence;
      }
      const previousThreadId = this.#viewModelPublisher.multiTargetAwarenessAvailable
        ? this.#viewModelPublisher.currentThreadIdForTarget(targetId)
        : undefined;
      const observedThreadId = this.#viewModelPublisher.multiTargetAwarenessAvailable
        ? await this.#viewModelPublisher.recoverTargetThreadId(targetId).catch(() => undefined)
        : undefined;
      const threadId = observedThreadId ?? request.params.threadId;
      if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
        this.#clearUpdateActivationRetriesForTarget(targetId, threadId);
        await this.#viewModelPublisher.activateTarget(targetId, threadId);
        if (previousThreadId !== threadId) {
          this.#unwatchThreadIfUnused(previousThreadId);
        }
      }
      if (threadId === null) {
        return {
          revision: null,
          result: { status: "unknown" },
        };
      }
      const result = await this.#restoreVisibleThread(threadId);
      if (result === "retry") {
        this.#scheduleVisibleThreadRecovery(0);
      }
      return {
        revision: this.#viewModelPublisher.multiTargetAwarenessAvailable
          ? (this.#viewModelPublisher.currentRevisionForTarget(targetId) ?? null)
          : this.#viewModelPublisher.currentThreadId === threadId
            ? (this.#viewModelPublisher.currentRevision ?? null)
            : null,
        result: { status: result },
      };
    }
    if (request.method === "renderer.disconnected") {
      if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
        if (!this.#viewModelPublisher.hasTarget(request.params.targetId)) {
          throw new GoalProgressIpcHandlerError(
            "RENDERER_TARGET_UNKNOWN",
            "Renderer target is not managed by this Helper",
          );
        }
        const disconnectedThreadId = this.#viewModelPublisher.currentThreadIdForTarget(
          request.params.targetId,
        );
        this.#visibleThreadOrderByTarget.delete(request.params.targetId);
        await this.#viewModelPublisher.handleTargetDisconnect(
          request.params.targetId,
          request.params.code,
        );
        this.#unwatchThreadIfUnused(disconnectedThreadId);
      } else {
        await this.#viewModelPublisher.handleDisconnect(request.params.code);
        this.#scheduleVisibleThreadRecovery(0);
      }
      return {
        revision: null,
        result: { status: "scheduled", code: request.params.code },
      };
    }
    const loaded = await this.#store.load(request.params.sessionId);
    if (!loaded.contract) {
      throw new GoalProgressIpcHandlerError(
        "STORE_NOT_INITIALIZED",
        "Session has no Goal Contract",
      );
    }
    const threadId = this.#threadIdOf(loaded.contract);
    this.#watchThread(threadId);
    const usage = await this.#refreshUsage(threadId);
    const contract = (await this.#store.load(threadId)).contract ?? loaded.contract;
    const overlay = await this.#overlayForCurrentNativeGoal(contract, usage);
    const preparingObjective = this.#preparingObjectives.get(threadId);
    if (overlay.detached && preparingObjective) {
      const viewModel = await this.#publishPreparing(
        threadId,
        preparingObjective,
        "preparing-checklist",
      );
      return {
        revision: null,
        result: {
          viewModel,
          uiPreference: await readGoalProgressUiPreference(this.paths),
        },
      };
    }
    const presented = {
      ...this.#projectState(contract, overlay),
      uiPreference: await readGoalProgressUiPreference(this.paths),
    };
    return {
      revision: contract.revision,
      result: {
        viewModel: presented.viewModel,
        uiPreference: presented.uiPreference,
      },
    };
  }

  async #handleUiIpc(request: HelperUiIpcRequest): Promise<GoalProgressIpcHandlerResult> {
    return await handleHelperUiIntent(request, {
      paths: this.paths,
      store: this.#store,
      preparingObjectives: this.#preparingObjectives,
      readNativeGoal: (threadId) => this.#sessionCoordinator.readNativeGoal(threadId),
      publishPreparationError: (threadId, code) => this.#publishPreparationError(threadId, code),
      publishPreparing: (threadId, objective, stage) =>
        this.#publishPreparing(threadId, objective, stage),
      transientView: (threadId, objective, phase) =>
        this.#transientView(threadId, objective, phase),
      clearView: (threadId) => this.#viewModelPublisher.clear(threadId),
      threadIdOf: (contract) => this.#threadIdOf(contract),
      overlayFor: (threadId) => this.#overlayFor(threadId),
      watchThread: (threadId) => this.#watchThread(threadId),
      refreshUsage: (threadId) => this.#refreshUsage(threadId),
      applyPollingMode: (threadId, preference, overlay, contract) =>
        this.#applyPollingMode(threadId, preference, overlay, contract),
      project: (contract, overlay) => this.#project(contract, overlay),
    });
  }

  async #handleUpdateIpc(request: HelperUpdateIpcRequest): Promise<GoalProgressIpcHandlerResult> {
    try {
      if (request.method === "update.restart-result") {
        const updateState = await this.#updateCoordinator.handleRestartResult(request.params);
        await this.#viewModelPublisher.setUpdateState(updateState);
        return {
          revision: this.#viewModelPublisher.currentRevision ?? null,
          result: {
            action: "state-updated",
            updateState,
          },
        };
      }
      if (request.method === "update.worker-result") {
        const updateState = await this.#updateCoordinator.handleWorkerResult(request.params);
        await this.#viewModelPublisher.setUpdateState(updateState);
        return {
          revision: this.#viewModelPublisher.currentRevision ?? null,
          result: {
            action: "state-updated",
            updateState,
          },
        };
      }
      const visibleTargetIds = this.#viewModelPublisher.targetIdsForThread(
        request.params.sessionId,
      );
      if (
        this.#viewModelPublisher.multiTargetAwarenessAvailable
          ? visibleTargetIds.length === 0
          : request.params.sessionId !== this.#viewModelPublisher.currentThreadId
      ) {
        throw new GoalProgressIpcHandlerError(
          "GOAL_PROGRESS_UPDATE_THREAD_MISMATCH",
          "Update intent does not belong to the visible Goal task",
        );
      }
      const result: GoalProgressUpdateIntentResult = await this.#updateCoordinator.handleIntent(
        request.params.intent as GoalProgressUpdateIntent,
      );
      this.#viewModelPublisher.rememberUpdateState(result.updateState);
      const { afterResponse, ...publicResult } = result;
      return {
        revision: this.#viewModelPublisher.multiTargetAwarenessAvailable
          ? (this.#viewModelPublisher.currentRevisionForTarget(visibleTargetIds[0] ?? "") ?? null)
          : (this.#viewModelPublisher.currentRevision ?? null),
        result: publicResult,
        ...(afterResponse === undefined
          ? {}
          : {
              afterResponse: async () => {
                const finalState = await afterResponse();
                if (finalState) {
                  await this.#viewModelPublisher.setUpdateState(finalState);
                }
              },
            }),
      };
    } catch (error) {
      if (error instanceof GoalProgressIpcHandlerError) {
        throw error;
      }
      const candidate = helperDiagnosticCauseCode(error);
      throw new GoalProgressIpcHandlerError(
        candidate.startsWith("GOAL_PROGRESS_UPDATE_")
          ? candidate
          : "GOAL_PROGRESS_UPDATE_REQUEST_FAILED",
        "Goal Progress update request failed",
      );
    }
  }

  async #handleStoreInitialize(
    request: Extract<HelperStoreIpcRequest, { method: "store.initialize" }>,
    context: GoalProgressIpcConnectionContext,
  ): Promise<GoalProgressIpcHandlerResult> {
    const identity = await this.#sessionCoordinator.authorizeSessionRequest(
      requestAuthorization(request.params),
      undefined,
      request.params.metadata.turnId,
    );
    try {
      const overlay = await this.#overlayFor(identity.threadId);
      const activationState = await this.#activationStateForOverlay(identity.threadId, overlay);
      if (activationState.detachReason === "user-dismissed-preparation") {
        throw new GoalProgressIpcHandlerError(
          "ACTIVATION_CANCELLED",
          "Goal Progress preparation was closed by the user before initialization",
        );
      }
      if (activationState.detachReason === "user-detached-tracking") {
        throw new GoalProgressIpcHandlerError(
          "TRACKING_DETACHED_BY_USER",
          "Goal Progress tracking was closed by the user",
        );
      }
      const preparingObjective = this.#preparingObjectives.get(identity.threadId);
      if (preparingObjective) {
        await this.#publishPreparing(
          identity.threadId,
          preparingObjective,
          "establishing-baseline",
        );
      }
      const nativeGoal = await this.#sessionCoordinator.trustedNativeGoal(identity.threadId);
      const current = await this.#store.load(identity.threadId);
      const currentContract = current.contract?.schemaVersion === 2 ? current.contract : null;
      const contract = createModelContract(
        request.params.initialization,
        nativeGoal,
        identity,
        request.params.metadata.occurredAt,
      );
      const metadata =
        context.clientKind === "mcp"
          ? { ...request.params.metadata, source: "model" as const }
          : request.params.metadata;
      let initialized: GoalEventStoreWriteSuccess;
      const currentBinding = currentContract?.nativeGoalBinding ?? null;
      const objectiveChangedInPlace =
        currentBinding !== null &&
        currentBinding.createdAt === nativeGoal.createdAt &&
        currentBinding.objectiveHash !== hashNativeGoalObjective(nativeGoal.objective);
      if (
        currentContract &&
        (currentContract.nativeGoalBinding.createdAt !== nativeGoal.createdAt ||
          objectiveChangedInPlace)
      ) {
        initialized = await this.#store.replace(contract, metadata, {
          contractId: currentContract.contractId,
          revision: currentContract.revision,
        });
      } else {
        if (currentContract) {
          assertBoundNativeGoal(currentContract, nativeGoal, currentContract.revision);
        }
        initialized = await this.#store.initialize(contract, metadata);
      }
      this.#preparingObjectives.delete(identity.threadId);
      this.#watchThread(identity.threadId);
      await this.#refreshUsage(identity.threadId);
      const latest = (await this.#store.load(identity.threadId)).contract ?? initialized.contract;
      await writeGoalProgressActivationState(
        identity.threadId,
        this.paths,
        DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
      );
      const activeOverlay = overlay.detached
        ? await writeGoalProgressTrackingOverlay(
            resolveGoalProgressSessionPaths(this.paths, identity.threadId),
            DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
          )
        : overlay;
      const projected = this.#projectState(latest, activeOverlay);
      await this.#publishVerified(identity.threadId, projected.viewModel);
      return {
        revision: latest.revision,
        result: {
          ...projected,
          duplicate: initialized.duplicate,
        },
      };
    } catch (error) {
      const loaded = await this.#store.load(identity.threadId).catch(() => null);
      if (!loaded?.contract && this.#preparingObjectives.has(identity.threadId)) {
        await this.#publishPreparationError(identity.threadId, helperErrorCode(error));
      }
      throw error;
    }
  }

  async #handleStoreApply(
    request: Extract<HelperStoreIpcRequest, { method: "store.apply" }>,
    context: GoalProgressIpcConnectionContext,
  ): Promise<GoalProgressIpcHandlerResult> {
    const identity = await this.#sessionCoordinator.authorizeSessionRequest(
      requestAuthorization(request.params),
      request.params.command.sessionId,
      request.params.command.turnId,
    );
    const persistedOverlay = await this.#overlayFor(identity.threadId);
    const activationState = await this.#activationStateForOverlay(
      identity.threadId,
      persistedOverlay,
    );
    if (isUserDetachedActivationState(activationState)) {
      throw new GoalProgressIpcHandlerError(
        "TRACKING_DETACHED_BY_USER",
        "Goal Progress tracking was closed by the user",
      );
    }
    const command = { ...request.params.command, sessionId: identity.threadId };
    if (command.type === "sync-native-goal" || command.type === "retarget-rescope") {
      throw new GoalProgressIpcHandlerError(
        "NATIVE_GOAL_SOURCE_UNVERIFIED",
        "Only the trusted native Goal adapter can synchronize or retarget native Goal state",
      );
    }
    const current = await this.#store.load(identity.threadId);
    const contract = await this.#sessionCoordinator.contractForWrite(
      identity,
      current.contract,
      current.contract?.revision ?? null,
    );
    let commandForStore: GoalProgressCommand =
      context.clientKind === "mcp" ? sanitizeModelCommand(command, contract ?? undefined) : command;
    let retargeted = false;
    if (contract && (command.type === "rescope" || contract.nativeGoal.status !== "complete")) {
      const nativeGoal = await this.#sessionCoordinator.readNativeGoal(
        identity.threadId,
        contract.revision,
      );
      if (command.type === "rescope" && nativeGoal) {
        try {
          assertBoundNativeGoal(contract, nativeGoal, contract.revision);
        } catch (error) {
          if (!nativeGoalErrorDetachesContract(error)) {
            throw error;
          }
          const sanitized = (
            context.clientKind === "mcp"
              ? sanitizeModelCommand(command, contract ?? undefined)
              : command
          ) as Extract<GoalProgressCommand, { type: "rescope" }>;
          commandForStore = {
            ...sanitized,
            type: "retarget-rescope",
            source: "system",
            nativeGoalBinding: {
              threadId: identity.threadId,
              createdAt: nativeGoal.createdAt,
              objectiveHash: hashNativeGoalObjective(nativeGoal.objective),
            },
            nativeGoal: contractNativeGoal(nativeGoal),
          };
          retargeted = true;
        }
      } else {
        await this.#assertBoundNativeGoalOrDetach(contract, nativeGoal);
      }
    }
    const applied = await this.#store.apply(commandForStore);
    if (!applied.ok) {
      if (applied.code === "REVISION_CONFLICT") {
        const latest = await this.#store.load(identity.threadId);
        if (latest.contract) {
          const currentViewModel = this.#project(
            latest.contract,
            await this.#overlayFor(identity.threadId),
          );
          throw new GoalProgressIpcHandlerError(
            applied.code,
            applied.message,
            currentViewModel.revision,
            currentViewModel,
          );
        }
      }
      throw new GoalProgressIpcHandlerError(applied.code, applied.message, applied.currentRevision);
    }
    const overlay = retargeted
      ? await (async () => {
          await writeGoalProgressActivationState(
            identity.threadId,
            this.paths,
            DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
          );
          return writeGoalProgressTrackingOverlay(
            resolveGoalProgressSessionPaths(this.paths, identity.threadId),
            {
              ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
              detached: false,
            },
          );
        })()
      : await this.#overlayFor(identity.threadId);
    if (retargeted) {
      this.#preparingObjectives.delete(identity.threadId);
    }
    this.#watchThread(identity.threadId);
    await this.#refreshUsage(identity.threadId);
    await this.#applyPollingMode(
      identity.threadId,
      await readGoalProgressUiPreference(this.paths),
      overlay,
      applied.contract,
    );
    const projected = this.#projectState(applied.contract, overlay);
    await this.#publishVerified(identity.threadId, projected.viewModel);
    return {
      revision: applied.contract.revision,
      result: {
        ...projected,
        duplicate: applied.duplicate,
      },
    };
  }

  async #handleStoreIpc(
    request: HelperStoreIpcRequest,
    context: GoalProgressIpcConnectionContext,
  ): Promise<GoalProgressIpcHandlerResult> {
    if (request.method === "store.load") {
      return this.#handleStoreLoad(request);
    }
    if (request.method === "store.initialize") {
      return this.#handleStoreInitialize(request, context);
    }
    return this.#handleStoreApply(request, context);
  }

  async #handleDoctorIpc(request: HelperDoctorIpcRequest): Promise<GoalProgressIpcHandlerResult> {
    const doctor = await inspectGoalProgressLocal(
      this.paths,
      request.params.sessionId,
      true,
      this.#store,
    );
    const runtime = await this.#inspectRuntimeDoctor(request.params.sessionId);
    return {
      revision:
        doctor.store.checked && doctor.store.revision !== null ? doctor.store.revision : null,
      result: { ...doctor, runtime },
    };
  }

  #handler(): GoalProgressIpcHandler {
    return new HelperIpcRouter({
      routes: {
        system: (request) => this.#handleSystemIpc(request),
        hook: (request) => this.#handleHookIpc(request),
        activation: (request) => this.#handleActivationIpc(request),
        store: (request, context) => this.#handleStoreIpc(request, context),
        renderer: (request) => this.#handleRendererIpc(request),
        ui: (request) => this.#handleUiIpc(request),
        update: (request) => this.#handleUpdateIpc(request),
        doctor: (request) => this.#handleDoctorIpc(request),
      },
      log: (input) => this.#log(input),
    }).handler();
  }

  async start(): Promise<void> {
    if (this.#lock || this.#server) {
      throw new GoalProgressIpcHandlerError(
        "HELPER_ALREADY_RUNNING",
        "This Helper instance is already running",
      );
    }
    this.#ready = false;
    const lock = await acquireHelperInstanceLock(this.paths, this.#lockOptions);
    const server = new GoalProgressIpcServer(this.paths.helperSocketPath, this.#handler());
    try {
      await this.#key();
      await server.start({ removeStaleSocket: true });
    } catch (error) {
      await lock.release();
      throw error;
    }
    this.#lock = lock;
    this.#server = server;
    if (!this.#startupListener && this.#prepareStartupListener) {
      try {
        const prepared = await this.#prepareStartupListener();
        if (this.#server !== server) {
          await prepared.startupListener.stop().catch(() => undefined);
          return;
        }
        this.#startupListener = prepared.startupListener;
        this.#startupHandoff = prepared.startupHandoff;
      } catch {
        // IPC remains available when optional Codex discovery cannot prepare the listener.
      }
    }
    if (this.#startupListener) {
      try {
        this.#startupListener.start((event) => this.#handleStartupEvent(event));
        const ready = await this.#startupListener.waitUntilReady();
        await this.#log({
          level: "info",
          event: "startup.listener.started",
          ...(ready ? {} : { code: "STARTUP_LISTENER_NOT_READY" }),
        });
      } catch {
        // Helper and ordinary Codex startup remain available without the optional listener.
      }
    }
    if (this.#server !== server) {
      return;
    }
    const recoveredTargets = this.#viewModelPublisher.multiTargetAwarenessAvailable
      ? await this.#viewModelPublisher.recoverVisibleTargets()
      : [];
    const recoveredVisibleThreadId = this.#viewModelPublisher.multiTargetAwarenessAvailable
      ? undefined
      : await this.#viewModelPublisher.recoverVisibleThreadId();
    await this.#viewModelPublisher.initialize();
    try {
      const updateState = await this.#updateCoordinator.initialize();
      await this.#viewModelPublisher.setUpdateState(updateState);
      if (updateState.phase === "up-to-date") {
        await this.#cleanupCompletedUpdate();
      }
    } catch {
      // Update state is optional; Goal tracking remains available if it cannot be restored.
    }
    if (this.#viewModelPublisher.multiTargetAwarenessAvailable) {
      for (const target of recoveredTargets) {
        await this.#viewModelPublisher.activateTarget(target.targetId, target.threadId);
        if (!target.threadId) {
          continue;
        }
        await this.#restoreVisibleThread(target.threadId).catch(() => "retry");
      }
    } else if (recoveredVisibleThreadId) {
      const restored = await this.#restoreVisibleThread(recoveredVisibleThreadId).catch(
        (): "retry" => "retry",
      );
      if (restored === "retry") {
        this.#scheduleVisibleThreadRecovery(0);
      }
    } else {
      this.#scheduleVisibleThreadRecovery(0);
    }
    this.#ready = true;
    void this.#maybeStartAutomaticUpdateCheck().catch(() => undefined);
    await this.#log({
      level: "info",
      event: "helper.started",
    });
  }

  async setViewModelSink(sink?: ViewModelPublisherSink): Promise<void> {
    await this.#viewModelPublisher.setSink(sink);
  }

  async stop(): Promise<void> {
    const preservePage = this.#viewModelPublisher.currentUpdateState?.phase === "installing";
    this.#ready = false;
    this.#clearUpdateActivationRetries();
    this.#visibleThreadOrderByTarget.clear();
    const server = this.#server;
    const lock = this.#lock;
    this.#server = undefined;
    this.#lock = undefined;
    if (this.#visibleThreadRecoveryTimer) {
      clearTimeout(this.#visibleThreadRecoveryTimer);
      this.#visibleThreadRecoveryTimer = undefined;
    }
    await this.#updateCoordinator.stop();
    await this.#startupListener?.stop().catch(() => undefined);
    if (this.#startupListener) {
      await this.#log({
        level: "info",
        event: "startup.listener.stopped",
      });
    }
    await server?.stop();
    await this.#viewModelPublisher.close(preservePage ? { preservePage: true } : undefined);
    await this.#runtime.close();
    await this.#log({
      level: "info",
      event: "helper.stopped",
    });
    await lock?.release();
  }
}

export async function runHelperCli(argv: readonly string[] = process.argv.slice(2)): Promise<void> {
  const root = process.env.GOAL_PROGRESS_ROOT;
  const paths = resolveGoalProgressPaths(root === undefined ? {} : { root: resolve(root) });
  if (argv[0] === "doctor") {
    const sessionFlag = argv.indexOf("--session-id");
    const sessionId = sessionFlag >= 0 && argv[sessionFlag + 1] ? argv[sessionFlag + 1] : undefined;
    const result = await inspectGoalProgress(paths, sessionId);
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
    return;
  }
  if (argv.length > 0 && argv[0] !== "serve") {
    throw new Error("Usage: goal-progress-helper [serve|doctor --json]");
  }
  const viewClient =
    process.platform === "darwin"
      ? new GoalProgressCdpViewClient(paths.helperSocketPath)
      : undefined;
  const viewModelSink =
    process.platform === "darwin"
      ? new RendererTargetManager({
          connector: () => connectHelperRendererTargetSource(paths),
          onTargetReady: (targetId, threadId, lifecycleId) => {
            void viewClient
              ?.reportVisibleThread(targetId, threadId, undefined, lifecycleId)
              .catch(() => undefined);
          },
          onTargetDestroyed: (targetId, code) => {
            void viewClient
              ?.reportDisconnected(targetId, code ?? "GOAL_PROGRESS_CDP_TARGET_DESTROYED")
              .catch(() => undefined);
          },
        })
      : undefined;
  const prepareStartupListener =
    process.platform === "darwin"
      ? async (): Promise<PreparedGoalProgressStartupListener> => {
          const app = await requireSingleCodexMacosApp();
          const listenerExecutable = resolveStartupListenerExecutable();
          await access(listenerExecutable, constants.X_OK);
          return {
            startupListener: new MacosStartupListenerSupervisor({
              executablePath: listenerExecutable,
              bundleId: app.bundleId,
              appPath: app.realAppPath,
              appExecutablePath: app.realExecutablePath,
            }),
            startupHandoff: new MacosStartupHandoffController({ paths }),
          };
        }
      : undefined;
  const helper = new GoalProgressHelper({
    paths,
    ...(viewModelSink === undefined ? {} : { viewModelSink }),
    ...(viewModelSink === undefined
      ? {}
      : {
          rendererDoctor: (expectedThreadId?: string, targetId?: string) =>
            targetId
              ? viewModelSink.doctorTarget(targetId, expectedThreadId)
              : viewModelSink.doctor(expectedThreadId),
        }),
    ...(prepareStartupListener === undefined ? {} : { prepareStartupListener }),
  });
  try {
    await helper.start();
  } catch (error) {
    await viewModelSink?.close();
    throw error;
  }
  const stop = async () => {
    await helper.stop();
    process.exitCode = 0;
  };
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
}

const entryPath = process.argv[1];
if (entryPath && import.meta.url === pathToFileURL(resolve(entryPath)).href) {
  runHelperCli().catch((error: unknown) => {
    process.stderr.write(`${helperErrorCode(error)}\n`);
    process.exitCode = 1;
  });
}
