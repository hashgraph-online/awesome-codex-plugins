import { css } from "lit";

export const layoutAndTypographyStyles = css`
    :host {
      display: block;
      min-width: 0;
      color: var(--gp-text);
      color-scheme: light dark;
      font: inherit;
      font-size: var(--gp-font-size);
      letter-spacing: 0;
      contain: layout style;
    }

    *,
    *::before,
    *::after {
      box-sizing: border-box;
      letter-spacing: 0;
    }

    button {
      font: inherit;
    }

    .panel {
      overflow: visible;
      border: 1px solid var(--gp-line);
      border-radius: 14px;
      background-color: var(--gp-panel);
      background-image: linear-gradient(
        180deg,
        var(--gp-panel),
        color-mix(in srgb, var(--gp-panel) 94%, transparent)
      );
      box-shadow: 0 10px 26px var(--gp-panel-shadow);
    }

    .panel.placement-inline {
      border-top-width: 1px;
      border-radius: 0;
      background-color: var(--gp-panel-glass);
      background-image: linear-gradient(
        var(--gp-panel-glass-compensation),
        var(--gp-panel-glass-compensation)
      );
      -webkit-backdrop-filter: blur(var(--gp-backdrop-blur));
      backdrop-filter: blur(var(--gp-backdrop-blur));
      box-shadow: none;
    }

    .panel.phase-preparing,
    .panel.phase-error {
      border-top-width: 1px;
      border-radius: 0;
      background-color: var(--gp-panel-glass);
      background-image: linear-gradient(
        var(--gp-panel-glass-compensation),
        var(--gp-panel-glass-compensation)
      );
      -webkit-backdrop-filter: blur(var(--gp-backdrop-blur));
      backdrop-filter: blur(var(--gp-backdrop-blur));
      box-shadow: none;
    }

    .token {
      flex: none;
      color: var(--gp-muted);
      font-size: max(10px, calc(var(--gp-font-size) - 3px));
      font-variant-numeric: tabular-nums;
      transform: translateX(calc(0px - var(--gp-token-right-shift)));
      unicode-bidi: plaintext;
      white-space: nowrap;
    }

    :host([dir="rtl"]) .token {
      transform: translateX(var(--gp-token-right-shift));
    }

    .current-summary {
      display: flex;
      overflow: hidden;
      align-items: center;
      gap: calc(var(--gp-font-size) * 0.357143);
      margin: 0;
      padding-inline-end: max(
        calc(var(--gp-font-size) * 2.142857),
        calc(
          100% - var(--gp-native-control-start, 100%) +
            var(--gp-font-size) * 2.142857
        )
      );
      color: var(--gp-muted);
      font-size: var(--gp-font-size-xs);
      line-height: 1.35;
      white-space: nowrap;
    }

    .current-leading-icon,
    .overall-leading-icon {
      display: block;
      width: 1.1em;
      height: 1.1em;
      flex: none;
      margin-inline-end: 1.5px;
      fill: none;
      stroke: currentColor;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-width: 1.35;
    }

    .current-leading-icon,
    .overall-leading-icon {
      color: var(--gp-icon-muted);
    }

    .current-leading-icon {
      width: 1.012em;
      height: 1.012em;
      fill: currentColor;
      margin-inline-end: calc(3.7px + 0.088em);
      stroke: none;
      transform: translateX(0.044em);
    }

    .current-summary strong {
      flex: none;
      color: var(--gp-text);
      font-weight: var(--gp-native-title-font-weight, 400);
    }

    .current-summary-text {
      overflow: hidden;
      min-width: 0;
      flex: 1;
      color: var(--gp-icon-muted);
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .completion-footer {
      display: grid;
      min-width: 0;
      flex: none;
      grid-template-columns: auto minmax(0, 1fr) auto;
      align-items: baseline;
      gap: calc(var(--gp-font-size) * 0.285714);
      margin-top: 0;
      padding-inline-end: 0;
      color: var(--gp-muted);
      font-size: max(10px, calc(var(--gp-font-size) - 3px));
      line-height: 1.3;
    }

    .completion-count {
      overflow: hidden;
      min-width: 0;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .footer-actions {
      position: static;
      display: inline-flex;
      min-width: 0;
      align-items: baseline;
      gap: calc(var(--gp-font-size) * 0.428571);
      grid-column: 3;
      margin-inline-start: auto;
      justify-self: end;
      text-align: right;
    }

    .placement-settings {
      position: absolute;
      top: calc(var(--gp-font-size) * 0.428571);
      left: auto;
      right: calc(var(--gp-font-size) * 0.857143);
      bottom: auto;
      display: inline-flex;
      flex: none;
      transform: none;
    }

    .placement-settings-trigger {
      position: relative;
      display: inline-grid;
      width: var(--gp-control-size);
      height: var(--gp-control-size);
      place-items: center;
      border: 0;
      border-radius: var(--gp-control-radius);
      padding: 0;
      background: transparent;
      color: var(--gp-icon-muted);
      cursor: pointer;
      line-height: 1;
    }

    .more-icon {
      display: block;
      width: calc(var(--gp-font-size) * 0.857143);
      height: calc(var(--gp-font-size) * 0.857143);
      fill: currentColor;
    }

    .placement-settings-trigger:hover,
    .placement-settings-trigger:focus-visible,
    .placement-settings-trigger[aria-expanded="true"] {
      background: var(--gp-control-hover);
      color: var(--gp-icon-muted);
      outline: none;
    }

    .placement-menu {
      position: absolute;
      z-index: 20;
      right: 0;
      left: auto;
      top: calc(100% + 6px);
      bottom: auto;
      display: grid;
      width: 180px;
      gap: 2px;
      border: 1px solid color-mix(in srgb, var(--gp-line-strong) 72%, transparent);
      border-radius: 12px;
      padding: 6px;
      background: color-mix(in srgb, var(--gp-panel-raised) 84%, transparent);
      -webkit-backdrop-filter: blur(calc(var(--gp-backdrop-blur) + 6px)) saturate(1.2);
      backdrop-filter: blur(calc(var(--gp-backdrop-blur) + 6px)) saturate(1.2);
      box-shadow:
        0 14px 34px var(--gp-panel-shadow),
        inset 0 1px 0 color-mix(in srgb, var(--gp-text) 7%, transparent);
    }

    .placement-menu-title {
      padding: 4px 8px 3px;
      color: var(--gp-muted);
      font-size: max(9px, calc(var(--gp-font-size-sm) - 2px));
      font-weight: 620;
      line-height: 1.25;
    }

    .placement-menu-divider {
      height: 1px;
      margin: 2px 4px;
      background: var(--gp-line);
    }

    .placement-menu button {
      min-height: 32px;
      border: 0;
      border-radius: 8px;
      padding: 6px 8px;
      background: transparent;
      color: var(--gp-text);
      cursor: pointer;
      font-size: var(--gp-font-size-sm);
      text-align: start;
    }

    .placement-menu button:hover:not(:disabled),
    .placement-menu button:focus-visible,
    .placement-menu button[aria-checked="true"] {
      background: var(--gp-hover);
      outline: none;
    }

    .placement-menu button[aria-checked="true"] {
      color: var(--gp-accent);
      font-weight: 650;
    }

    .placement-menu button.motion-setting {
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--gp-text);
      font-weight: 500;
    }

    .motion-switch {
      position: relative;
      display: inline-flex;
      width: 28px;
      height: 16px;
      flex: none;
      align-items: center;
      border-radius: 999px;
      background: var(--gp-track);
      box-shadow: inset 0 0 0 1px var(--gp-line);
    }

    .motion-switch-knob {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--gp-panel-raised);
      box-shadow: 0 1px 3px var(--gp-panel-shadow);
      transform: translateX(2px);
      transition: transform 160ms ease;
    }

    .motion-switch[data-on="true"] {
      background: var(--gp-accent);
    }

    .motion-switch[data-on="true"] .motion-switch-knob {
      transform: translateX(14px);
    }

    .placement-menu button:disabled {
      cursor: default;
      opacity: 0.45;
    }

    .icon-button {
      display: inline-grid;
      width: calc(var(--gp-font-size) * 2.142857);
      height: calc(var(--gp-font-size) * 2.142857);
      place-items: center;
      border: 0;
      border-radius: var(--gp-control-radius);
      background: transparent;
      color: var(--gp-icon-muted);
      cursor: pointer;
      font-size: var(--gp-font-size-sm);
      line-height: 1;
    }

    .icon-button:hover:not(:disabled) {
      background: var(--gp-control-hover);
      color: var(--gp-text);
    }

    .icon-button:focus-visible {
      outline: 2px solid var(--gp-focus);
      outline-offset: 1px;
    }

    .icon-button:disabled {
      cursor: default;
      opacity: 0.45;
    }

    .content {
      position: relative;
      display: grid;
      gap: var(--gp-content-gap);
      padding:
        var(--gp-content-padding-top)
        var(--gp-content-padding-right)
        var(--gp-content-padding-bottom)
        var(--gp-content-padding-left);
    }

`;
