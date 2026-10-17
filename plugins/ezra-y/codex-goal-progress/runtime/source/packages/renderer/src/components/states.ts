import { html } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";

export function renderPreparingView(
  viewModel: GoalProgressViewModel,
  messages: GoalProgressMessages,
) {
  const title =
    viewModel.preparingStep === "reading-goal"
      ? messages.preparingReadGoal
      : viewModel.preparingStep === "establishing-baseline"
        ? messages.preparingBaseline
        : messages.preparingObjectives;
  return html`
    <div class="state" role="status" aria-live="polite">
      <div>
        <div class="state-symbol preparing" aria-hidden="true"></div>
        <div class="state-title">${title}</div>
        <div class="state-copy">${messages.preparingCopy}</div>
      </div>
    </div>
  `;
}

export function renderErrorView(
  viewModel: GoalProgressViewModel | null,
  onRetry: () => void,
  onDetach: () => void,
  messages: GoalProgressMessages,
) {
  const summary =
    viewModel?.overallPercent === null || viewModel?.overallPercent === undefined
      ? messages.unavailableTitle
      : `${viewModel.overallPercent}% · ${messages.unavailableTitle}`;
  return html`
    <div class="state error" role="alert">
      <span class="error-summary">${summary}</span>
      <div class="state-actions">
        <button
          class="retry-button"
          type="button"
          aria-label=${messages.retryProgress}
          title=${messages.retry}
          @click=${onRetry}
        >
          ${messages.retry}
        </button>
        <button
          class="icon-button detach-button"
          type="button"
          aria-label=${messages.closeProgress}
          title=${messages.closeProgress}
          @click=${onDetach}
        >
          ×
        </button>
      </div>
    </div>
  `;
}
