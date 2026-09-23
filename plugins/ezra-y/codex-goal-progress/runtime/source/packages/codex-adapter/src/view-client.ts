import {
  type GoalProgressUiIntent,
  type GoalProgressUiPreference,
  type GoalProgressUpdateIntent,
  type GoalProgressUpdateState,
  GoalProgressUpdateStateSchema,
  type GoalProgressViewModel,
  GoalProgressViewModelSchema,
  migrateGoalProgressUiPreference,
} from "../../contracts/src/index.js";
import { GoalProgressIpcClient } from "../../ipc/src/index.js";

export interface GoalProgressViewState {
  readonly viewModel: GoalProgressViewModel;
  readonly uiPreference: GoalProgressUiPreference;
  readonly dismissed?: boolean;
}

export interface GoalProgressUiIntentState {
  readonly viewModel: GoalProgressViewModel;
  readonly uiPreference: GoalProgressUiPreference;
  readonly dismissed?: boolean;
}

export interface GoalProgressUpdateIntentState {
  readonly action: "deferred" | "opened-release" | "state-updated";
  readonly updateState: GoalProgressUpdateState;
}

export function parseGoalProgressViewState(result: unknown): GoalProgressViewState {
  if (
    result === null ||
    typeof result !== "object" ||
    !("viewModel" in result) ||
    !("uiPreference" in result)
  ) {
    throw new Error("GOAL_PROGRESS_IPC_VIEW_RESPONSE_INVALID");
  }
  const uiPreference = migrateGoalProgressUiPreference(result.uiPreference);
  if (!uiPreference) {
    throw new Error("GOAL_PROGRESS_IPC_UI_PREFERENCE_INVALID");
  }
  return {
    viewModel: GoalProgressViewModelSchema.parse(result.viewModel),
    uiPreference,
    ...("dismissed" in result && result.dismissed === true ? { dismissed: true } : {}),
  };
}

export function parseGoalProgressUpdateIntentState(result: unknown): GoalProgressUpdateIntentState {
  if (
    result === null ||
    typeof result !== "object" ||
    !("action" in result) ||
    !("updateState" in result) ||
    (result.action !== "deferred" &&
      result.action !== "opened-release" &&
      result.action !== "state-updated")
  ) {
    throw new Error("GOAL_PROGRESS_IPC_UPDATE_RESPONSE_INVALID");
  }
  return {
    action: result.action,
    updateState: GoalProgressUpdateStateSchema.parse(result.updateState),
  };
}

export class GoalProgressCdpViewClient {
  readonly #client: GoalProgressIpcClient;

  constructor(socketPath: string) {
    this.#client = new GoalProgressIpcClient(socketPath, {
      clientKind: "cdp",
    });
  }

  async getView(sessionId: string): Promise<GoalProgressViewModel> {
    return (await this.getViewState(sessionId)).viewModel;
  }

  async getViewState(sessionId: string): Promise<GoalProgressViewState> {
    const response = await this.#client.request({
      method: "view.get",
      params: { sessionId },
    });
    return parseGoalProgressViewState(response.result);
  }

  async reportVisibleThread(
    targetId: string,
    threadId: string | null,
    sequence?: number,
    lifecycleId?: string,
  ): Promise<void> {
    await this.#client.request({
      method: "renderer.visible-thread",
      params: {
        targetId,
        threadId,
        ...(sequence === undefined ? {} : { sequence }),
        ...(lifecycleId === undefined ? {} : { lifecycleId }),
      },
    });
  }

  async reportDisconnected(targetId: string, code: string): Promise<void> {
    await this.#client.request({
      method: "renderer.disconnected",
      params: { targetId, code },
    });
  }

  async applyUiIntent(
    sessionId: string,
    intent: GoalProgressUiIntent,
  ): Promise<GoalProgressUiIntentState> {
    const response = await this.#client.request({
      method: "ui.intent",
      params: { sessionId, intent },
    });
    return parseGoalProgressViewState(response.result);
  }

  async applyUpdateIntent(
    sessionId: string,
    intent: GoalProgressUpdateIntent,
  ): Promise<GoalProgressUpdateIntentState> {
    const response = await this.#client.request({
      method: "update.intent",
      params: { sessionId, intent },
    });
    return parseGoalProgressUpdateIntentState(response.result);
  }
}
