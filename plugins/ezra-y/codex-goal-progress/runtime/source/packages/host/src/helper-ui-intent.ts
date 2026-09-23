import { acceptGoalProgressUiIntent } from "../../codex-adapter/src/index.js";
import {
  DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
  type GoalContractAny,
  type GoalProgressTrackingOverlay,
  type GoalProgressUiPreference,
  type GoalProgressViewModel,
} from "../../contracts/src/index.js";
import {
  GoalProgressIpcHandlerError,
  type GoalProgressIpcHandlerResult,
  type GoalProgressIpcRequest,
} from "../../ipc/src/index.js";
import {
  type GoalEventStore,
  type GoalProgressPaths,
  readGoalProgressUiPreference,
  resolveGoalProgressSessionPaths,
  writeGoalProgressTrackingOverlay,
  writeGoalProgressUiPreference,
} from "../../store/src/index.js";
import {
  DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
  readGoalProgressActivationState,
  type TrustedNativeGoal,
  writeGoalProgressActivationState,
} from "./helper-session-coordinator.js";

type UiIntentRequest = Extract<GoalProgressIpcRequest, { method: "ui.intent" }>;

export interface HelperUiIntentDependencies {
  readonly paths: GoalProgressPaths;
  readonly store: GoalEventStore;
  readonly preparingObjectives: Map<string, string>;
  readonly readNativeGoal: (threadId: string) => Promise<TrustedNativeGoal | null>;
  readonly publishPreparationError: (
    threadId: string,
    code: string,
  ) => Promise<GoalProgressViewModel>;
  readonly publishPreparing: (
    threadId: string,
    objective: string,
    stage: "reading-goal" | "preparing-checklist",
  ) => Promise<GoalProgressViewModel>;
  readonly transientView: (
    threadId: string,
    objective: string,
    phase: "detached",
  ) => GoalProgressViewModel;
  readonly clearView: (threadId: string) => Promise<void>;
  readonly threadIdOf: (contract: GoalContractAny) => string;
  readonly overlayFor: (threadId: string) => Promise<GoalProgressTrackingOverlay>;
  readonly watchThread: (threadId: string) => void;
  readonly refreshUsage: (threadId: string) => Promise<unknown>;
  readonly applyPollingMode: (
    threadId: string,
    preference: GoalProgressUiPreference,
    overlay: GoalProgressTrackingOverlay,
    contract: GoalContractAny,
  ) => Promise<void>;
  readonly project: (
    contract: GoalContractAny,
    overlay: GoalProgressTrackingOverlay,
  ) => GoalProgressViewModel;
}

export async function handleHelperUiIntent(
  request: UiIntentRequest,
  dependencies: HelperUiIntentDependencies,
): Promise<GoalProgressIpcHandlerResult> {
  const accepted = acceptGoalProgressUiIntent(request.params.intent);
  if (!accepted.ok) {
    throw new GoalProgressIpcHandlerError(accepted.code, accepted.message);
  }
  const loaded = await dependencies.store.load(request.params.sessionId);
  if (!loaded.contract) {
    const threadId = request.params.sessionId;
    const sessionPaths = resolveGoalProgressSessionPaths(dependencies.paths, threadId);
    const preference = await readGoalProgressUiPreference(dependencies.paths);
    if (accepted.intent.type === "requestRetry") {
      const activationState = await readGoalProgressActivationState(threadId, dependencies.paths);
      if (activationState.detachReason === "user-dismissed-preparation") {
        throw new GoalProgressIpcHandlerError(
          "ACTIVATION_CANCELLED",
          "Goal Progress preparation was closed by the user",
        );
      }
      await writeGoalProgressActivationState(
        threadId,
        dependencies.paths,
        DEFAULT_GOAL_PROGRESS_ACTIVATION_STATE,
      );
      await writeGoalProgressTrackingOverlay(sessionPaths, {
        ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
        detached: false,
      });
      const nativeGoal = await dependencies.readNativeGoal(threadId);
      if (!nativeGoal) {
        const viewModel = await dependencies.publishPreparationError(
          threadId,
          "NATIVE_GOAL_DETACHED",
        );
        return {
          revision: null,
          result: { viewModel, uiPreference: preference },
        };
      }
      await dependencies.publishPreparing(threadId, nativeGoal.objective, "reading-goal");
      const viewModel = await dependencies.publishPreparing(
        threadId,
        nativeGoal.objective,
        "preparing-checklist",
      );
      return {
        revision: null,
        result: { viewModel, uiPreference: preference },
      };
    }
    if (accepted.intent.type === "requestDetach") {
      await writeGoalProgressActivationState(threadId, dependencies.paths, {
        schemaVersion: 1,
        detachReason: "user-dismissed-preparation",
      });
      await writeGoalProgressTrackingOverlay(sessionPaths, {
        ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
        detached: true,
      });
      const objective = dependencies.preparingObjectives.get(threadId) ?? "当前 Goal";
      const viewModel = dependencies.transientView(threadId, objective, "detached");
      dependencies.preparingObjectives.delete(threadId);
      await dependencies.clearView(threadId);
      return {
        revision: null,
        result: {
          viewModel,
          uiPreference: preference,
          dismissed: true,
        },
      };
    }
    throw new GoalProgressIpcHandlerError("STORE_NOT_INITIALIZED", "Session has no Goal Contract");
  }

  const threadId = dependencies.threadIdOf(loaded.contract);
  const sessionPaths = resolveGoalProgressSessionPaths(dependencies.paths, threadId);
  let preference = await readGoalProgressUiPreference(dependencies.paths);
  let overlay = await dependencies.overlayFor(threadId);
  let dismissedPreparation = false;
  if (accepted.intent.type === "setCollapsed") {
    preference = await writeGoalProgressUiPreference(dependencies.paths, {
      ...preference,
      collapsed: accepted.intent.collapsed,
    });
  } else if (accepted.intent.type === "setMotionPaused") {
    preference = await writeGoalProgressUiPreference(dependencies.paths, {
      ...preference,
      motionPaused: accepted.intent.motionPaused,
    });
  } else if (accepted.intent.type === "setPlacement") {
    preference = await writeGoalProgressUiPreference(dependencies.paths, {
      ...preference,
      placement: accepted.intent.placement,
    });
  } else if (accepted.intent.type === "setFloatingXRatio") {
    preference = await writeGoalProgressUiPreference(dependencies.paths, {
      ...preference,
      floatingXRatio: accepted.intent.floatingXRatio,
    });
  } else if (accepted.intent.type === "requestDetach") {
    dismissedPreparation = dependencies.preparingObjectives.has(threadId);
    await writeGoalProgressActivationState(threadId, dependencies.paths, {
      schemaVersion: 1,
      detachReason: dismissedPreparation ? "user-dismissed-preparation" : "user-detached-tracking",
    });
    overlay = await writeGoalProgressTrackingOverlay(sessionPaths, {
      ...DEFAULT_GOAL_PROGRESS_TRACKING_OVERLAY,
      detached: true,
    });
    if (dismissedPreparation) {
      dependencies.preparingObjectives.delete(threadId);
    }
  }
  dependencies.watchThread(threadId);
  await dependencies.refreshUsage(threadId);
  const contract = (await dependencies.store.load(threadId)).contract ?? loaded.contract;
  await dependencies.applyPollingMode(threadId, preference, overlay, contract);
  const viewModel = dependencies.project(contract, overlay);
  return {
    revision: contract.revision,
    result: {
      viewModel,
      uiPreference: preference,
      ...(dismissedPreparation ? { dismissed: true } : {}),
    },
  };
}
