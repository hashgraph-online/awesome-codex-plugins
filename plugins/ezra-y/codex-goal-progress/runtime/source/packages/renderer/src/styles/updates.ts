import { css } from "lit";

export const updateStyles = css`
    :host([settings-open]) {
      position: relative;
      z-index: 30;
    }

    .content.has-update-prompt .current-summary {
      padding-inline-end: min(78%, 430px);
    }

    .placement-settings {
      width: max-content;
      min-width: 0;
      max-width: calc(100% - var(--gp-content-padding-left));
      align-items: center;
      gap: 6px;
    }

    .placement-settings-trigger-wrap {
      position: relative;
      display: inline-flex;
      flex: none;
    }

    .more-icon {
      display: block;
      width: 12px;
      height: 6px;
      fill: currentColor;
    }

    .more-icon circle {
      opacity: 0.82;
    }

    .update-unread-dot {
      position: absolute;
      z-index: 2;
      top: 3px;
      right: 2px;
      width: 5px;
      height: 5px;
      border: 1px solid var(--gp-panel);
      border-radius: 50%;
      background: var(--gp-accent);
      opacity: 0.88;
      pointer-events: none;
      transform: scale(1);
      animation: update-dot-breathe 3s ease-in-out infinite;
    }

    .collapse-toggle .update-unread-dot {
      top: 0;
      right: 2px;
    }

    .update-prompt {
      display: inline-flex;
      overflow: hidden;
      max-width: none;
      min-width: 0;
      flex: 0 1 auto;
      height: max(20px, calc(var(--gp-font-size) * 1.35));
      min-height: 0;
      align-items: center;
      justify-content: flex-end;
      gap: 7px;
      color: var(--gp-muted);
      font-size: var(--gp-font-size-xs);
      font-weight: 400;
      white-space: nowrap;
    }

    .update-state-text {
      overflow: hidden;
      min-width: 0;
      flex: 0 1 auto;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .update-percent {
      flex: none;
      color: var(--gp-text);
      direction: ltr;
      font-variant-numeric: tabular-nums;
      font-weight: 650;
      unicode-bidi: isolate;
    }

    .update-prompt-actions {
      display: inline-flex;
      flex: none;
      align-items: center;
      gap: 5px;
    }

    .update-action {
      height: max(20px, calc(var(--gp-font-size) * 1.35));
      min-width: 0;
      min-height: 0;
      flex: none;
      border: 1px solid transparent;
      border-radius: var(--gp-control-radius);
      padding: 1px 7px;
      cursor: pointer;
      font-size: max(9px, calc(var(--gp-font-size) - 4px));
      font-weight: 620;
      line-height: 1;
      white-space: nowrap;
    }

    .update-action.primary {
      background: var(--gp-accent);
      color: color-mix(in srgb, var(--gp-on-status) 88%, transparent);
    }

    .update-action.secondary {
      border-color: color-mix(in srgb, var(--gp-accent) 34%, var(--gp-line));
      background: color-mix(in srgb, var(--gp-accent) 10%, transparent);
      color: var(--gp-accent);
    }

    .update-action.primary:hover {
      color: var(--gp-on-status);
    }

    .update-action:focus-visible {
      outline: none;
      box-shadow: inset 0 0 0 1px color-mix(in srgb, currentColor 42%, transparent);
    }

    .placement-menu:has(.update-menu-row) {
      width: min(252px, calc(100vw - 32px));
      gap: 1px;
      padding: 6px;
      color: var(--gp-text);
    }

    .placement-menu:has(.update-menu-row) .placement-menu-title {
      padding: 3px 8px 2px;
      color: var(--gp-icon-muted);
      font-size: 10px;
      font-weight: 560;
    }

    .placement-menu:has(.update-menu-row) button {
      min-height: max(28px, calc(var(--gp-font-size) * 2));
      border-radius: 7px;
      padding: 5px 8px;
      background: transparent;
      color: var(--gp-text);
      font-size: var(--gp-font-size-xs);
      font-weight: var(--gp-native-title-font-weight, 400);
      transition:
        background-color 140ms ease,
        color 140ms ease;
    }

    .placement-menu:has(.update-menu-row) button:hover:not(:disabled) {
      background: var(--gp-hover);
      color: var(--gp-text);
    }

    .placement-menu:has(.update-menu-row) button:focus-visible {
      background: transparent;
      outline: 1px solid var(--gp-focus);
      outline-offset: -1px;
    }

    .placement-menu .update-menu-row {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 12px;
    }

    .menu-row-leading {
      display: inline-flex;
      min-width: 0;
      align-items: center;
      gap: 7px;
    }

    .menu-row-icon,
    .menu-selection-icon {
      display: block;
      width: 11px;
      height: 11px;
      flex: none;
      color: var(--gp-icon-muted);
    }

    .menu-row-text {
      min-width: 0;
    }

    .update-current-version-label,
    .update-menu-section-title {
      color: var(--gp-text);
      font-size: var(--gp-font-size-xs);
      font-weight: var(--gp-native-title-font-weight, 400);
    }

    .update-menu-section-title {
      margin-top: 3px;
      margin-bottom: 2px;
      padding: 4px 8px 2px;
      color: var(--gp-icon-muted);
      font-size: 10px;
      font-weight: 560;
      line-height: 1.25;
    }

    .placement-menu-title,
    .update-menu-section-title {
      text-align: start;
    }

    .placement-menu [data-update-check] .menu-row-text {
      color: var(--gp-text);
      font-size: var(--gp-font-size-xs);
      font-weight: var(--gp-native-title-font-weight, 400);
    }

    .placement-menu .restart-required:disabled {
      opacity: 1;
    }

    .restart-required:disabled .menu-row-text {
      color: var(--gp-icon-muted);
    }

    .update-menu-value {
      display: inline-flex;
      overflow: hidden;
      align-items: center;
      justify-content: flex-end;
      gap: 4px;
      color: var(--gp-icon-muted);
      font-size: 10px;
      font-variant-numeric: tabular-nums;
      font-weight: 350;
      text-align: end;
      text-overflow: ellipsis;
      unicode-bidi: isolate;
      white-space: nowrap;
    }

    .update-menu-value.muted {
      color: var(--gp-icon-muted);
      font-weight: 350;
    }

    .update-menu-value.update-available {
      color: color-mix(in oklab, var(--gp-accent) 62%, var(--gp-icon-muted));
    }

    .update-external-icon {
      display: block;
      width: 9px;
      height: 9px;
      flex: none;
      color: var(--gp-icon-muted);
    }

    .placement-menu button.update-release-notes {
      display: inline-flex;
      width: max-content;
      min-height: 20px;
      align-items: center;
      justify-content: flex-end;
      justify-self: end;
      gap: 4px;
      margin: 0;
      border: 0;
      border-radius: 6px;
      padding: 2px 6px;
      background: var(--gp-hover);
      color: color-mix(in oklab, var(--gp-accent) 62%, var(--gp-icon-muted));
      font-size: 10px;
      font-weight: 350;
    }

    .placement-menu button.update-release-notes:hover:not(:disabled) {
      background: color-mix(in srgb, var(--gp-text) 9%, transparent);
    }

    .update-menu-block-divider {
      height: 1px;
      margin: 2px 0;
      background: var(--gp-line);
    }

    .placement-menu:has(.update-menu-row) button.motion-setting {
      background: transparent;
      color: var(--gp-text);
      font-weight: var(--gp-native-title-font-weight, 400);
    }

    .placement-menu:has(.update-menu-row)
      button[role="menuitemradio"][aria-checked="true"] {
      background: var(--gp-hover);
      color: var(--gp-text);
      font-weight: var(--gp-native-title-font-weight, 400);
    }

    .placement-menu button[role="menuitemradio"] {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .menu-radio-check {
      display: inline-grid;
      width: 11px;
      height: 11px;
      flex: none;
      place-items: center;
    }

    .menu-selection-icon {
      color: currentColor;
    }

    :host(:lang(ml)) .content.has-update-prompt:has(.restart-required),
    :host(:lang(ta)) .content.has-update-prompt:has(.restart-required) {
      padding-top: max(var(--gp-content-padding-top), calc(var(--gp-font-size) * 3.2));
    }

    :host(:lang(ml)) .update-prompt.restart-required,
    :host(:lang(ta)) .update-prompt.restart-required {
      height: auto;
      overflow: visible;
    }

    :host(:lang(ml)) .restart-required .update-state-text,
    :host(:lang(ta)) .restart-required .update-state-text {
      overflow: visible;
      line-height: 1.15;
      text-overflow: clip;
      white-space: normal;
    }

    @keyframes update-dot-breathe {
      0%,
      100% {
        opacity: 0.78;
        transform: scale(0.96);
      }
      50% {
        opacity: 1;
        transform: scale(1.04);
      }
    }

    @media (max-width: 520px) {
      .update-prompt {
        max-width: calc(100vw - 68px);
        gap: 4px;
      }

      .content.has-update-prompt:has(.restart-required) {
        padding-top: max(var(--gp-content-padding-top), calc(var(--gp-font-size) * 5.2));
      }

      .update-prompt.restart-required {
        width: min(100%, calc(100vw - 104px));
        height: auto;
        flex-wrap: wrap;
        align-content: flex-start;
        row-gap: 3px;
        overflow: visible;
        white-space: normal;
      }

      .restart-required .update-state-text {
        overflow: visible;
        max-width: none;
        flex: 1 1 100%;
        line-height: 1.15;
        text-align: end;
        text-overflow: clip;
        white-space: normal;
      }

      .restart-required .update-prompt-actions {
        width: 100%;
        max-width: 100%;
        flex-wrap: wrap;
        justify-content: flex-end;
      }

      .update-action {
        padding-inline: 6px;
      }
    }
`;
