import type { GoalProgressViewModel } from "../../contracts/src/index.js";
import type { GoalProgressMessages } from "./locale.js";

export type GoalProgressObjectiveView = GoalProgressViewModel["objectives"][number];

export function phaseLabel(
  viewModel: GoalProgressViewModel,
  messages: GoalProgressMessages,
): string {
  if (viewModel.trackingPhase === "paused") {
    return messages.phasePaused;
  }
  if (viewModel.trackingPhase === "completed") {
    return messages.phaseCompleted;
  }
  if (viewModel.trackingPhase === "blocked") {
    return viewModel.blockedReason === "usage-limit"
      ? messages.phaseUsageLimit
      : viewModel.blockedReason === "budget-limit"
        ? messages.phaseBudgetLimit
        : messages.phaseNativeGoalBlocked;
  }
  if (viewModel.trackingPhase === "detached") {
    return messages.phaseDetached;
  }
  if (viewModel.finalVerificationPending) {
    return messages.phaseFinalVerification;
  }
  return messages.phaseTracking;
}

export function statusLabel(
  objective: GoalProgressObjectiveView,
  messages: GoalProgressMessages,
): string {
  if (objective.status === "completed") {
    return objective.completionVerification === "verified"
      ? messages.statusCompletedVerified
      : messages.statusCompleted;
  }
  if (objective.status === "active") {
    return messages.statusActive;
  }
  if (objective.status === "blocked") {
    return messages.statusBlocked;
  }
  return messages.statusPending;
}
