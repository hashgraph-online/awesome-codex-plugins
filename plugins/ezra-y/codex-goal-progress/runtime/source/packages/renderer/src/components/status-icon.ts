import { html } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";
import { type GoalProgressObjectiveView, statusLabel } from "../view-labels.js";

const visibleStatusLabels = {
  completed: "Success",
  active: "Working",
  pending: "Pending",
  blocked: "Blocked",
} as const;

export function renderStatusIcon(
  objective: GoalProgressObjectiveView,
  index: number,
  trackingPhase: GoalProgressViewModel["trackingPhase"],
  messages: GoalProgressMessages,
) {
  const label = statusLabel(objective, messages);
  const phaseStatus =
    objective.status !== "active"
      ? null
      : trackingPhase === "paused"
        ? "Paused"
        : trackingPhase === "blocked"
          ? "Blocked"
          : null;
  const accessibleLabel = phaseStatus ?? label;
  const visible = phaseStatus ?? visibleStatusLabels[objective.status];
  return html`
    <span class="status-index" aria-hidden="true">${index + 1}.</span>
    <span class="status ${objective.status}" aria-hidden="true">${visible}</span>
    <span class="sr-only">${accessibleLabel}</span>
  `;
}
