import { html, nothing } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";

export function renderNotices(viewModel: GoalProgressViewModel, messages: GoalProgressMessages) {
  if (!viewModel.scopeChangeNotice && !viewModel.progressCorrectionNotice) {
    return nothing;
  }
  return html`
    ${
      viewModel.scopeChangeNotice
        ? html`<div class="notice">
          ${messages.scopeUpdated(viewModel.scopeChangeNotice.reason)}
        </div>`
        : nothing
    }
    ${
      viewModel.progressCorrectionNotice
        ? html`<div class="notice">
          ${messages.progressCorrected(viewModel.progressCorrectionNotice.reason)}
        </div>`
        : nothing
    }
  `;
}
