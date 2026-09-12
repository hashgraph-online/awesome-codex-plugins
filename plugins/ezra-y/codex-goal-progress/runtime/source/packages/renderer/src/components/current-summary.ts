import { html } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import { selectProgressTarget } from "../../../contracts/src/progress-focus.js";
import type { GoalProgressMessages } from "../locale.js";
import { phaseLabel } from "../view-labels.js";

export function renderCurrentSummary(
  viewModel: GoalProgressViewModel,
  messages: GoalProgressMessages,
) {
  const selected = selectProgressTarget(viewModel.objectives);
  // A pending candidate is not a report of work currently being performed.
  const current = selected?.status === "pending" ? undefined : selected;
  const currentTitle = current?.currentItemTitle ?? current?.title;
  const blocked = viewModel.trackingPhase === "blocked";
  const summary =
    viewModel.trackingPhase === "completed"
      ? messages.goalCompleted
      : blocked
        ? `${phaseLabel(viewModel, messages)} · ${
            currentTitle ?? messages.waitingNativeGoalRecovery
          }`
        : (currentTitle ?? phaseLabel(viewModel, messages));
  const state =
    viewModel.trackingPhase === "paused"
      ? messages.currentPaused
      : blocked
        ? messages.currentBlocked
        : messages.current;
  return html`<p class="current-summary">
    <svg
      class="current-leading-icon"
      viewBox="0 0 1024 1024"
      aria-hidden="true"
    >
      <path d="M512 960A448 448 0 1 0 512 64a448 448 0 0 0 0 896z m0 64A512 512 0 1 1 512 0a512 512 0 0 1 0 1024z"></path>
      <path d="M441.6 368.96v286.08L680.64 505.6 441.6 368.96z m33.92 340.352a64 64 0 0 1-97.92-54.272v-286.08a64 64 0 0 1 95.744-55.552l239.04 136.64a64 64 0 0 1 2.176 109.824L475.52 709.312z"></path>
    </svg>
    <strong>${state}</strong>
    <span class="current-summary-text">${summary}</span>
  </p>`;
}
