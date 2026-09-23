import { css } from "lit";

export const stateStyles = css`
    .state {
      position: relative;
      display: grid;
      min-height: calc(var(--gp-font-size) * 8);
      place-items: center;
      padding: calc(var(--gp-font-size) * 1.285714);
      text-align: center;
    }

    .state-symbol {
      position: relative;
      display: grid;
      width: 30px;
      height: 30px;
      place-items: center;
      margin: 0 auto 12px;
      border: 1px solid var(--gp-line-strong);
      border-radius: 50%;
      color: var(--gp-muted);
      font-size: 13px;
      font-weight: 720;
    }

    .state-symbol.preparing {
      width: 22px;
      height: 22px;
      border: 2px solid color-mix(in srgb, var(--gp-icon-muted) 22%, transparent);
      border-top-color: var(--gp-accent);
      border-right-color: color-mix(in srgb, var(--gp-accent) 72%, var(--gp-icon-muted));
      background: transparent;
      box-shadow: none;
      animation: spin 1.1s linear infinite;
      backface-visibility: hidden;
      contain: strict;
      will-change: transform;
    }

    .state-symbol.preparing::after {
      content: none;
    }

    .state-title {
      color: var(--gp-text);
      font-size: max(10px, calc(var(--gp-font-size) - 2px));
      font-weight: 690;
      line-height: 1.35;
    }

    .state-copy {
      max-width: calc(var(--gp-font-size) * 25.714286);
      margin-top: calc(var(--gp-font-size) * 0.357143);
      color: var(--gp-muted);
      font-size: max(9px, calc(var(--gp-font-size) - 4px));
      line-height: 1.5;
    }

    .phase-error .state {
      display: flex;
      min-height: 36px;
      align-items: center;
      justify-content: flex-start;
      gap: 4px;
      padding: 4px 8px 4px 12px;
      color: var(--gp-muted);
      font-size: var(--gp-font-size-sm);
      line-height: 1.35;
      text-align: start;
    }

    .error-summary {
      overflow: hidden;
      min-width: 0;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .state-actions {
      display: flex;
      flex: none;
      align-items: center;
      gap: 2px;
      margin-inline-start: auto;
    }

    .retry-button {
      min-height: 24px;
      border: 0;
      border-radius: var(--gp-control-radius);
      padding: 2px 6px;
      background: transparent;
      color: var(--gp-accent);
      cursor: pointer;
      font: inherit;
    }

    .retry-button:hover,
    .retry-button:focus-visible {
      background: var(--gp-control-hover);
    }

    .retry-button:focus-visible {
      outline: 2px solid var(--gp-focus);
      outline-offset: 1px;
    }

    .panel.phase-error.placement-floating .state {
      position: absolute;
      z-index: 1;
      bottom: var(--gp-floating-stack-lift, 0px);
      left: var(--gp-floating-chip-center, 50%);
      width: min(280px, calc(100% - 20px));
      border: 1px solid var(--gp-line);
      border-radius: 15px;
      background: var(--gp-panel-glass);
      box-shadow: none;
      pointer-events: auto;
      transform: translateX(-50%);
    }

    .sr-only {
      position: absolute;
      overflow: hidden;
      width: 1px;
      height: 1px;
      clip: rect(0, 0, 0, 0);
      clip-path: inset(50%);
      white-space: nowrap;
    }

`;
