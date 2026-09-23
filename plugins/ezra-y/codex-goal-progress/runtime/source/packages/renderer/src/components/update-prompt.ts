import { html, nothing } from "lit";
import type { GoalProgressUpdateState } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";

export interface UpdatePromptRenderOptions {
  readonly dismissed: boolean;
  readonly messages: GoalProgressMessages;
  readonly onRestartLater: () => void;
  readonly onRestartNow: () => void;
  readonly onRetry: () => void;
  readonly onStart: () => void;
  readonly state: GoalProgressUpdateState | null;
}

export function renderUpdatePrompt(options: UpdatePromptRenderOptions) {
  const state = options.state;
  if (!state || options.dismissed) {
    return nothing;
  }
  if (state.phase === "available") {
    return html`
      <span class="update-prompt" data-update-phase="available">
        <span class="update-state-text">${options.messages.updateAvailable}</span>
        <button class="update-action primary" type="button" @click=${options.onStart}>
          ${state.deliveryMode === "plugin-marketplace" ? options.messages.viewUpdateNotes : options.messages.updateNow}
        </button>
      </span>
    `;
  }
  if (
    state.phase === "preparing" ||
    state.phase === "verifying" ||
    state.phase === "installing" ||
    state.phase === "restarting"
  ) {
    const message =
      state.phase === "preparing"
        ? options.messages.preparingUpdate
        : state.phase === "verifying"
          ? options.messages.verifyingUpdate
          : state.phase === "installing"
            ? options.messages.installingUpdate
            : options.messages.restartingUpdate;
    return html`<span class="update-prompt" data-update-phase=${state.phase}>
      <span class="update-state-text">${message}</span>
    </span>`;
  }
  if (state.phase === "downloading") {
    const hasPercent =
      typeof state.totalBytes === "number" &&
      state.totalBytes > 0 &&
      typeof state.downloadPercent === "number";
    return html`<span class="update-prompt" data-update-phase="downloading">
      <span class="update-state-text">
        ${hasPercent ? options.messages.downloading : options.messages.downloadingUnknown}
      </span>
      ${
        hasPercent
          ? html`<strong class="update-percent">${Math.round(state.downloadPercent ?? 0)}%</strong>`
          : nothing
      }
    </span>`;
  }
  if (state.phase === "download-failed" || state.phase === "update-failed") {
    return html`
      <span class="update-prompt" data-update-phase=${state.phase}>
        <span class="update-state-text">
          ${
            state.phase === "download-failed"
              ? options.messages.downloadFailed
              : options.messages.updateFailed
          }
        </span>
        <button class="update-action secondary" type="button" @click=${options.onRetry}>
          ${options.messages.retry}
        </button>
      </span>
    `;
  }
  if (state.phase === "restart-required") {
    return html`
      <span class="update-prompt restart-required" data-update-phase="restart-required">
        <span class="update-state-text">${options.messages.restartReady}</span>
        <span class="update-prompt-actions">
          <button class="update-action primary" type="button" @click=${options.onRestartNow}>
            ${options.messages.restartNow}
          </button>
          <button class="update-action secondary" type="button" @click=${options.onRestartLater}>
            ${options.messages.restartLater}
          </button>
        </span>
      </span>
    `;
  }
  return nothing;
}
