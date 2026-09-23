import {
  Activity,
  Check,
  ExternalLink,
  type LucideIconData,
  type LucideIconNode,
  Move,
  Pin,
  RefreshCw,
  Tag,
} from "@lucide/icons";
import { html, nothing } from "lit";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";
import type {
  GoalProgressPlacement,
  GoalProgressUpdateState,
} from "../../../contracts/src/index.js";
import { isGoalProgressUpdateVersion } from "../../../contracts/src/update-state-runtime.js";
import type { GoalProgressMessages } from "../locale.js";
import { renderUpdatePrompt } from "./update-prompt.js";

export interface DisplaySettingsMenuRenderOptions {
  readonly motionPaused: boolean;
  readonly onCheckUpdate: () => void;
  readonly onOpenCurrentRelease: () => void;
  readonly onOpenLatestRelease: () => void;
  readonly onRestartLater: () => void;
  readonly onRestartNow: () => void;
  readonly onRetryUpdate: () => void;
  readonly onSelectPlacement: (placement: GoalProgressPlacement) => void;
  readonly onStartUpdate: () => void;
  readonly onToggleMotionPaused: () => void;
  readonly onTogglePlacementSettings: (event: MouseEvent) => void;
  readonly requestedPlacement: GoalProgressPlacement;
  readonly settingsOpen: boolean;
  readonly updatePromptDismissed: boolean;
  readonly updateState: GoalProgressUpdateState | null;
  readonly updateUnread: boolean;
  readonly messages: GoalProgressMessages;
}

function updateMenuStatus(state: GoalProgressUpdateState, messages: GoalProgressMessages): string {
  if (state.phase === "up-to-date") {
    return state.deliveryMode === "plugin-marketplace" && state.checkedAt === null
      ? "—"
      : messages.upToDate;
  }
  if (state.phase === "checking") {
    return messages.checkingUpdates;
  }
  if (state.phase === "check-failed") {
    return messages.checkFailed;
  }
  if (state.phase === "restart-required" && state.latestVersion) {
    return messages.restartPending;
  }
  return state.latestVersion ? messages.newVersion : messages.checkFailed;
}

function renderIconNode([tagName, attributes, children = []]: LucideIconNode): string {
  const serializedAttributes = Object.entries(attributes)
    .filter(([name]) => name !== "key")
    .map(([name, value]) => `${name}="${value}"`)
    .join(" ");
  const serializedChildren = children.map(renderIconNode).join("");
  return `<${tagName} ${serializedAttributes}>${serializedChildren}</${tagName}>`;
}

function renderMenuIcon(icon: LucideIconData, className = "menu-row-icon", size = 11) {
  return unsafeSVG(
    `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-${icon.name} ${className}" aria-hidden="true" focusable="false">${icon.node.map(renderIconNode).join("")}</svg>`,
  );
}

export function renderDisplaySettingsMenu(options: DisplaySettingsMenuRenderOptions) {
  const updateState = options.updateState;
  const showReleaseNotes =
    isGoalProgressUpdateVersion(updateState?.latestVersion) &&
    (updateState.phase === "available" || updateState.phase === "restart-required");
  const checkDisabled =
    updateState !== null &&
    updateState !== undefined &&
    [
      "checking",
      "preparing",
      "downloading",
      "verifying",
      "installing",
      "restart-required",
      "restarting",
    ].includes(updateState.phase);
  return html`
    <span class="placement-settings">
      ${renderUpdatePrompt({
        state: updateState,
        dismissed: options.updatePromptDismissed,
        messages: options.messages,
        onStart: options.onStartUpdate,
        onRetry: options.onRetryUpdate,
        onRestartNow: options.onRestartNow,
        onRestartLater: options.onRestartLater,
      })}
      <span class="placement-settings-trigger-wrap">
        <button
          class="placement-settings-trigger"
          type="button"
          aria-label=${options.messages.placementSettingsTriggerLabel}
          aria-haspopup="menu"
          aria-expanded=${String(options.settingsOpen)}
          title=${options.messages.placementSettingsTriggerLabel}
          @click=${options.onTogglePlacementSettings}
        >
          <svg class="more-icon" viewBox="0 0 12 6" aria-hidden="true">
            <circle cx="2" cy="3" r="0.9"></circle>
            <circle cx="6" cy="3" r="0.9"></circle>
            <circle cx="10" cy="3" r="0.9"></circle>
          </svg>
          ${
            options.updateUnread
              ? html`<span class="update-unread-dot" aria-hidden="true"></span>`
              : nothing
          }
        </button>
      </span>
      ${
        options.settingsOpen
          ? html`
            <span
              class="placement-menu"
              role="menu"
              aria-label=${options.messages.placementSettingsLabel}
            >
              <span class="placement-menu-title">
                ${updateState ? options.messages.versionSection : options.messages.effects}
              </span>
              ${
                updateState
                  ? html`
                    <button
                      class="update-menu-row"
                      type="button"
                      role="menuitem"
                      @click=${options.onOpenCurrentRelease}
                    >
                      <span class="menu-row-leading">
                        ${renderMenuIcon(Tag)}
                        <span class="menu-row-text update-current-version-label">
                          ${options.messages.currentVersion}
                        </span>
                      </span>
                      <span class="update-menu-value">
                        v${updateState.currentVersion}
                        ${renderMenuIcon(ExternalLink, "update-external-icon", 9)}
                      </span>
                    </button>
                    <button
                      class="update-menu-row ${updateState.phase}"
                      data-update-check
                      type="button"
                      role="menuitem"
                      ?disabled=${checkDisabled}
                      @click=${options.onCheckUpdate}
                    >
                      <span class="menu-row-leading">
                        ${renderMenuIcon(RefreshCw)}
                        <span class="menu-row-text">${options.messages.checkUpdates}</span>
                      </span>
                      <span
                        class="update-menu-value ${
                          updateState.phase === "up-to-date"
                            ? "muted"
                            : updateState.phase === "available"
                              ? "update-available"
                              : ""
                        }"
                      >
                        ${updateMenuStatus(updateState, options.messages)}
                      </span>
                    </button>
                    ${
                      showReleaseNotes
                        ? html`
                          <button
                            class="update-release-notes"
                            type="button"
                            role="menuitem"
                            @click=${options.onOpenLatestRelease}
                          >
                            <span>${options.messages.viewUpdateNotes}</span>
                          </button>
                        `
                        : nothing
                    }
                    <span class="update-menu-block-divider" aria-hidden="true"></span>
                    <span class="update-menu-section-title">${options.messages.effects}</span>
                  `
                  : nothing
              }
              <button
                class="motion-setting"
                type="button"
                role="menuitemcheckbox"
                aria-checked=${String(!options.motionPaused)}
                @click=${options.onToggleMotionPaused}
              >
                <span class="menu-row-leading">
                  ${renderMenuIcon(Activity)}
                  <span class="menu-row-text">${options.messages.animationEffects}</span>
                </span>
                <span
                  class="motion-switch"
                  data-on=${String(!options.motionPaused)}
                  aria-hidden="true"
                ><span class="motion-switch-knob"></span></span>
              </button>
              <span class="update-menu-block-divider" aria-hidden="true"></span>
              <span class="update-menu-section-title">${options.messages.displaySettings}</span>
              <button
                type="button"
                role="menuitemradio"
                aria-checked=${String(options.requestedPlacement === "inline")}
                @click=${() => options.onSelectPlacement("inline")}
              >
                <span class="menu-row-leading">
                  ${renderMenuIcon(Pin)}
                  <span class="menu-row-text">${options.messages.fixedDisplay}</span>
                </span>
                <span class="menu-radio-check" aria-hidden="true">
                  ${
                    options.requestedPlacement === "inline"
                      ? renderMenuIcon(Check, "menu-selection-icon")
                      : nothing
                  }
                </span>
              </button>
              <button
                type="button"
                role="menuitemradio"
                aria-checked=${String(options.requestedPlacement === "floating")}
                @click=${() => options.onSelectPlacement("floating")}
              >
                <span class="menu-row-leading">
                  ${renderMenuIcon(Move)}
                  <span class="menu-row-text">${options.messages.floatingDisplay}</span>
                </span>
                <span class="menu-radio-check" aria-hidden="true">
                  ${
                    options.requestedPlacement === "floating"
                      ? renderMenuIcon(Check, "menu-selection-icon")
                      : nothing
                  }
                </span>
              </button>
            </span>
          `
          : nothing
      }
    </span>
  `;
}
