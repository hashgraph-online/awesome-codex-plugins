import pageHostVersionManifest from "./page-host-version.json" with { type: "json" };
import { GOAL_PROGRESS_RELEASE_VERSION } from "./release-version.js";
import type { GoalProgressUiIntent } from "./ui-preference.js";

export const GOAL_PROGRESS_ELEMENT_NAME = "codex-goal-progress";
export const GOAL_PROGRESS_HOT_ELEMENT_NAME = `codex-goal-progress-v${GOAL_PROGRESS_RELEASE_VERSION.replaceAll(".", "-")}-p${pageHostVersionManifest.pageHostVersion}`;
export const GOAL_PROGRESS_SET_COLLAPSED_EVENT = "goal-progress-set-collapsed";
export const GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT = "goal-progress-set-motion-paused";
export const GOAL_PROGRESS_SET_PLACEMENT_EVENT = "goal-progress-set-placement";
export const GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT = "goal-progress-set-floating-x-ratio";
export const GOAL_PROGRESS_REQUEST_RETRY_EVENT = "goal-progress-request-retry";
export const GOAL_PROGRESS_REQUEST_DETACH_EVENT = "goal-progress-request-detach";
export const GOAL_PROGRESS_LAYOUT_OFFSET_EVENT = "goal-progress-layout-offset";
export const GOAL_PROGRESS_FLOATING_LAYOUT_EVENT = "goal-progress-floating-layout";
export const GOAL_PROGRESS_UI_INTENT_BINDING_PREFIX = "__CODEX_GOAL_PROGRESS_UI_INTENT_";
export const GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION = 2 as const;
export const GOAL_PROGRESS_UI_INTENT_MAX_BYTES = 1_024;
export const GOAL_PROGRESS_UI_INTENT_MAX_PER_SECOND = 8;

export interface GoalProgressUiIntentEnvelope {
  readonly protocolVersion: typeof GOAL_PROGRESS_UI_INTENT_PROTOCOL_VERSION;
  readonly bridgeNonce: string;
  readonly contractId: string;
  readonly threadId: string;
  readonly userActivated: boolean;
  readonly intent: GoalProgressUiIntent;
}
