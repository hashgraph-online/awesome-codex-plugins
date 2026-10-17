import { html } from "lit";
import type { GoalProgressPlacement, GoalProgressViewModel } from "../../../contracts/src/index.js";
import {
  type DisplaySettingsMenuRenderOptions,
  renderDisplaySettingsMenu,
} from "./display-settings-menu.js";
import { renderTokenUsage } from "./token-usage.js";

export interface CompletionFooterRenderOptions extends DisplaySettingsMenuRenderOptions {
  readonly placement: GoalProgressPlacement;
  readonly locale: string;
}

export function renderCompletionFooter(
  viewModel: GoalProgressViewModel,
  options: CompletionFooterRenderOptions,
) {
  const completedCount = viewModel.objectives.filter(
    (objective) => objective.status === "completed",
  ).length;
  return html`
    <footer class="completion-footer">
      <span class="completion-count">
        ${options.messages.completionCount(completedCount, viewModel.objectives.length)}
      </span>
      <span class="footer-actions">
        ${renderTokenUsage(viewModel.token, options.messages, options.locale)}
        ${renderDisplaySettingsMenu(options)}
      </span>
    </footer>
  `;
}
