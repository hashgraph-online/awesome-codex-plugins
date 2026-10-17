import { html } from "lit";
import type { GoalProgressMessages } from "../locale.js";
import type { GoalProgressObjectiveView } from "../view-labels.js";

export function renderMiniProgress(
  objective: GoalProgressObjectiveView,
  index: number,
  messages: GoalProgressMessages,
) {
  const delay = -4.2 + index * 0.41;
  return html`
    <div
      class="mini-track"
      role="progressbar"
      aria-label=${messages.objectiveProgress(objective.title)}
      aria-valuemin="0"
      aria-valuemax="100"
      aria-valuenow=${String(objective.progressPercent)}
    >
      <span
        class="mini-fill"
        style="width:${objective.progressPercent}%;--sweep-delay:${delay.toFixed(2)}s"
      ></span>
    </div>
  `;
}
