import { html, nothing } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";
import type { GoalProgressObjectiveView } from "../view-labels.js";
import { renderMiniProgress } from "./mini-progress.js";
import { renderStatusIcon } from "./status-icon.js";

export function renderObjectiveRow(
  objective: GoalProgressObjectiveView,
  index: number,
  trackingPhase: GoalProgressViewModel["trackingPhase"],
  messages: GoalProgressMessages,
  optional = false,
) {
  return html`
    <div
      class="objective-row"
      data-objective-id=${objective.id}
      data-status=${objective.status}
      role="listitem"
    >
      <div>${renderStatusIcon(objective, index, trackingPhase, messages)}</div>
      <div class="objective-main">
        <div class="objective-line">
          <span class="objective-name" title=${objective.title}>${objective.title}</span>
          ${optional ? html`<span class="optional-badge">${messages.optional}</span>` : nothing}
        </div>
        ${renderMiniProgress(objective, index, messages)}
      </div>
      <span class="objective-percent">${objective.progressPercent}%</span>
    </div>
  `;
}
