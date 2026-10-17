import { html, nothing } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";
import { renderParticles, renderSparkles } from "./motion-effects.js";

export interface OverallProgressRenderOptions {
  readonly compact: boolean;
  readonly collapsed: boolean;
  readonly toggleDisabled?: boolean;
  readonly toggleDisabledLabel?: string;
  readonly onToggleCollapsed: () => void;
  readonly showUpdateUnread?: boolean;
  readonly messages: GoalProgressMessages;
}

export function renderOverallProgress(
  viewModel: GoalProgressViewModel,
  options: OverallProgressRenderOptions,
) {
  const percent = viewModel.overallPercent;
  if (percent === null) {
    return nothing;
  }
  return html`
    <section
      class="overall ${options.compact ? "compact" : ""}"
      aria-label=${options.messages.overallProgress}
    >
      <div class="overall-rail">
        <span class="overall-label">
          <svg
            class="overall-leading-icon"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <circle cx="10" cy="10" r="7.25"></circle>
            <path d="M10 5.75v4.5h3.25"></path>
          </svg>
          <span>${options.messages.overallLabel}</span>
        </span>
        <div
          class="overall-track"
          role="progressbar"
          aria-label=${options.messages.overallProgress}
          aria-valuemin="0"
          aria-valuemax="100"
          aria-valuenow=${String(percent)}
        >
          <div class="overall-fill" style="width:${percent}%">
            <div class="particle-field" aria-hidden="true">${renderParticles()}</div>
          </div>
          ${
            percent > 0
              ? html`<span
                class="frontier"
                style="--progress:clamp(7px, ${percent}%, calc(100% - 7px))"
                aria-hidden="true"
              ></span>`
              : nothing
          }
          ${
            percent > 0
              ? html`<div
                class="sparkle-field"
                style="width:${percent}%"
                aria-hidden="true"
              >
                ${renderSparkles()}
              </div>`
              : nothing
          }
        </div>
        <strong class="overall-percent">${percent}%</strong>
        <button
          class="icon-button collapse-toggle"
          type="button"
          aria-expanded=${String(!options.collapsed)}
          aria-label=${
            options.toggleDisabled
              ? (options.toggleDisabledLabel ?? options.messages.composerShorterAutoExpand)
              : options.collapsed
                ? options.messages.expandProgress
                : options.messages.collapseProgress
          }
          title=${
            options.toggleDisabled
              ? (options.toggleDisabledLabel ?? options.messages.composerShorterAutoExpand)
              : options.collapsed
                ? options.messages.expand
                : options.messages.collapse
          }
          ?disabled=${options.toggleDisabled}
          @click=${options.onToggleCollapsed}
        >
          <svg
            class="disclosure-icon"
            data-direction=${options.collapsed ? "up" : "down"}
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path d=${options.collapsed ? "m5 15.5 7-7 7 7" : "m5 8.5 7 7 7-7"}></path>
          </svg>
          ${
            options.showUpdateUnread
              ? html`<span class="update-unread-dot" aria-hidden="true"></span>`
              : nothing
          }
        </button>
      </div>
    </section>
  `;
}
