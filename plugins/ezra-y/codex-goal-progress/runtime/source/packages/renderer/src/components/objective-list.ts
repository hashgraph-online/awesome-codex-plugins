import { html, nothing } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";
import { renderObjectiveRow } from "./objective-row.js";

export interface ObjectiveListRenderOptions {
  readonly scrolling: boolean;
  readonly scrollable: boolean;
  readonly thumbSize: number;
  readonly thumbOffset: number;
  readonly messages: GoalProgressMessages;
}

export function renderObjectiveLists(
  viewModel: GoalProgressViewModel,
  options: ObjectiveListRenderOptions,
) {
  const listClasses = [
    "objective-list",
    options.scrolling ? "scrolling" : "",
    options.scrollable ? "scrollable" : "",
  ]
    .filter(Boolean)
    .join(" ");
  return html`
    ${
      viewModel.objectives.length > 0
        ? html`<div class="objective-scroll-shell">
          <div
            class=${listClasses}
            role="list"
            aria-label=${options.messages.objectiveList}
            tabindex=${options.scrollable ? "0" : nothing}
          >
            ${viewModel.objectives.map((objective, index) =>
              renderObjectiveRow(objective, index, viewModel.trackingPhase, options.messages),
            )}
          </div>
          ${
            options.scrollable
              ? html`<span
                class="scroll-indicator ${options.scrolling ? "visible" : ""}"
                aria-hidden="true"
              >
                <span
                  class="scroll-thumb"
                  style="height:${options.thumbSize.toFixed(
                    2,
                  )}px;--thumb-offset:${options.thumbOffset.toFixed(2)}px"
                ></span>
              </span>`
              : nothing
          }
        </div>`
        : html`<div class="empty-objectives">${options.messages.emptyObjectives}</div>`
    }
    ${
      (viewModel.optionalObjectives ?? []).length > 0
        ? html`<div
          class="optional-list"
          role="list"
          aria-label=${options.messages.optionalObjectives}
        >
          ${(viewModel.optionalObjectives ?? []).map((objective, index) =>
            renderObjectiveRow(
              objective,
              viewModel.objectives.length + index,
              viewModel.trackingPhase,
              options.messages,
              true,
            ),
          )}
        </div>`
        : nothing
    }
  `;
}
