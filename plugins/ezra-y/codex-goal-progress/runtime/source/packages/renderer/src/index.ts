import {
  GOAL_PROGRESS_ELEMENT_NAME,
  GOAL_PROGRESS_HOT_ELEMENT_NAME,
} from "../../contracts/src/renderer-events.js";
import { GoalProgressElement } from "./goal-progress-element.js";

export {
  GOAL_PROGRESS_ELEMENT_NAME,
  GOAL_PROGRESS_HOT_ELEMENT_NAME,
  GOAL_PROGRESS_SET_COLLAPSED_EVENT,
  GOAL_PROGRESS_SET_FLOATING_X_RATIO_EVENT,
  GOAL_PROGRESS_SET_MOTION_PAUSED_EVENT,
  GOAL_PROGRESS_SET_PLACEMENT_EVENT,
} from "../../contracts/src/renderer-events.js";
export type {
  GoalProgressUpdateIntent,
  GoalProgressUpdateState,
} from "../../contracts/src/update-state.js";
export { GOAL_PROGRESS_UPDATE_INTENT_EVENT } from "../../contracts/src/update-state-runtime.js";
export { GoalProgressElement } from "./goal-progress-element.js";

declare global {
  interface HTMLElementTagNameMap {
    "codex-goal-progress": GoalProgressElement;
  }
}

function registerGoalProgressElement(): string {
  if (typeof customElements === "undefined") {
    return GOAL_PROGRESS_ELEMENT_NAME;
  }
  const current = customElements.get(GOAL_PROGRESS_ELEMENT_NAME);
  if (current === undefined) {
    customElements.define(GOAL_PROGRESS_ELEMENT_NAME, GoalProgressElement);
    return GOAL_PROGRESS_ELEMENT_NAME;
  }
  if (current === GoalProgressElement) {
    return GOAL_PROGRESS_ELEMENT_NAME;
  }
  if (customElements.get(GOAL_PROGRESS_HOT_ELEMENT_NAME) === undefined) {
    customElements.define(GOAL_PROGRESS_HOT_ELEMENT_NAME, GoalProgressElement);
  }
  return GOAL_PROGRESS_HOT_ELEMENT_NAME;
}

export const GOAL_PROGRESS_ACTIVE_ELEMENT_NAME = registerGoalProgressElement();
