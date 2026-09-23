import { css } from "lit";

export const placementStyles = css`
    :host([placement="floating"]) {
      height: 0;
      contain: style;
      overflow: visible;
      pointer-events: none;
    }

    .panel.placement-floating {
      overflow: visible;
      border: 0;
      background: transparent;
      box-shadow: none;
    }

    .floating-shell {
      position: relative;
      width: 100%;
      height: 0;
      overflow: visible;
      pointer-events: none;
    }

    .floating-chip {
      position: absolute;
      z-index: 1;
      bottom: var(--gp-floating-stack-lift, 0px);
      left: var(--gp-floating-chip-center, 50%);
      display: block;
      width: min(170px, calc(100% - 20px));
      min-height: 36px;
      overflow: hidden;
      border: 1px solid var(--gp-line);
      border-radius: 15px;
      padding: 0;
      background-color: var(--gp-panel-glass);
      background-image: linear-gradient(
        var(--gp-panel-glass-compensation),
        var(--gp-panel-glass-compensation)
      );
      -webkit-backdrop-filter: blur(var(--gp-backdrop-blur));
      backdrop-filter: blur(var(--gp-backdrop-blur));
      box-shadow: none;
      cursor: ew-resize;
      pointer-events: auto;
      touch-action: none;
      transform: translateX(-50%);
      user-select: none;
    }

    .floating-chip:focus-visible {
      outline: 2px solid var(--gp-focus);
      outline-offset: 2px;
    }

    .floating-chip .overall {
      width: 100%;
      border: 0;
      min-height: 36px;
      padding: 0 8px;
    }

    .floating-chip .overall.compact {
      padding: 0 8px;
    }

    .floating-chip .overall-rail {
      grid-template-columns: minmax(64px, 1fr) auto 24px;
      gap: 6px;
    }

    .floating-chip .overall-label {
      display: none;
    }

    .floating-chip .overall-track {
      overflow: visible;
      height: 6px;
      border-radius: 999px;
      background: var(--gp-track);
      box-shadow: none;
      transform: none;
    }

    .floating-chip .overall-fill,
    .floating-chip .frontier {
      box-shadow: none;
    }

    .floating-chip .frontier {
      width: 13px;
      height: 13px;
      background: var(--gp-frontier);
      opacity: 1;
    }

    .floating-chip .overall-percent {
      font-size: var(--gp-font-size);
    }

    .floating-chip .icon-button {
      position: static;
      width: 24px;
      height: 24px;
      border: 0;
      border-radius: 10px;
      background: transparent;
      transform: none;
    }

    .floating-chip .collapse-toggle {
      position: relative;
      inset: auto;
    }

    .floating-panel {
      position: absolute;
      z-index: 2;
      bottom: calc(
        44px + var(--gp-floating-stack-lift, 0px) + var(--gp-floating-panel-lift, 0px)
      );
      left: var(--gp-floating-panel-center, 50%);
      width: min(620px, calc(100% - 20px));
      overflow: visible;
      border: 1px solid var(--gp-line);
      border-radius: 14px;
      background-color: var(--gp-panel-glass);
      background-image: linear-gradient(
        var(--gp-panel-glass-compensation),
        var(--gp-panel-glass-compensation)
      );
      -webkit-backdrop-filter: blur(var(--gp-backdrop-blur));
      backdrop-filter: blur(var(--gp-backdrop-blur));
      box-shadow: none;
      cursor: ew-resize;
      pointer-events: auto;
      touch-action: none;
      transform: translateX(-50%);
      user-select: none;
    }

    .floating-panel .content {
      gap: var(--gp-objective-list-gap);
      padding: var(--gp-font-size);
    }

    .floating-panel button,
    .floating-chip button,
    .floating-panel [role="menu"],
    .floating-panel .objective-list {
      cursor: auto;
      touch-action: auto;
      user-select: auto;
    }
`;
