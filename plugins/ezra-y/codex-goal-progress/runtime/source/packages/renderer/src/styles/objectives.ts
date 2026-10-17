import { css } from "lit";

export const objectiveStyles = css`
    .objective-scroll-shell {
      position: relative;
    }

    .objective-list {
      --gp-objective-row-height: max(41px, calc(var(--gp-font-size) * 2.925));
      display: grid;
      max-block-size: calc(
        var(--gp-objective-row-height) * 3 + var(--gp-objective-list-gap) * 2
      );
      gap: var(--gp-objective-list-gap);
      overflow-x: hidden;
      overflow-y: auto;
      overscroll-behavior: contain;
      scrollbar-width: none;
    }

    .objective-list::-webkit-scrollbar {
      width: 0;
    }

    .objective-list:focus-visible {
      border-radius: 6px;
      outline: 2px solid var(--gp-focus);
      outline-offset: -2px;
    }

    .scroll-indicator {
      position: absolute;
      z-index: 8;
      top: 4px;
      right: 1px;
      bottom: 4px;
      width: 4px;
      border-radius: 999px;
      background: transparent;
      opacity: 0;
      pointer-events: none;
      transition: opacity 180ms ease;
    }

    .scroll-indicator.visible {
      opacity: 1;
    }

    .scroll-thumb {
      position: absolute;
      top: 0;
      right: 0;
      width: 4px;
      min-height: 24px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--gp-muted) 55%, transparent);
      transform: translateY(var(--thumb-offset));
    }

    .objective-row {
      --gp-objective-row-bg: color-mix(in srgb, var(--gp-text) 3.5%, transparent);
      --gp-objective-copy-size: max(10px, calc(var(--gp-font-size) - 3px));
      --gp-objective-status-size: var(--gp-objective-copy-size);
      --gp-objective-marker-size: calc(var(--gp-objective-status-size) * 4.4);
      --gp-objective-percent-width: 5ch;
      display: grid;
      min-height: var(--gp-objective-row-height, 44px);
      grid-template-columns:
        var(--gp-objective-marker-size)
        minmax(0, 1fr)
        var(--gp-objective-percent-width);
      align-items: start;
      gap: var(--gp-objective-column-gap);
      border-radius: 8px;
      padding:
        var(--gp-objective-padding-block)
        var(--gp-objective-padding-inline)
        var(--gp-objective-padding-block)
        var(--gp-objective-padding-left);
      background: var(--gp-objective-row-bg);
    }

    .objective-row:hover {
      background: var(--gp-hover);
    }

    .objective-row[data-status="active"] {
      --gp-objective-row-bg: color-mix(in srgb, var(--gp-text) 6%, transparent);
    }

    .objective-row > div:first-child {
      position: relative;
      display: grid;
      width: var(--gp-objective-marker-size);
      height: calc(var(--gp-objective-copy-size) * 1.25);
      align-items: center;
      justify-items: start;
    }

    .status-index {
      position: absolute;
      top: 0;
      left: calc(0px - var(--gp-mini-track-leading-extension));
      color: var(--gp-muted);
      font-family: inherit;
      font-size: var(--gp-objective-status-size);
      font-variant-numeric: tabular-nums;
      font-weight: 560;
      line-height: 1.25;
      direction: ltr;
      unicode-bidi: isolate;
      white-space: nowrap;
    }

    .status {
      position: relative;
      display: block;
      width: var(--gp-objective-marker-size);
      height: auto;
      border: 0;
      border-radius: 0;
      background: transparent;
      color: var(--gp-muted);
      font-size: var(--gp-objective-status-size);
      font-weight: 560;
      line-height: 1.25;
      text-align: left;
      white-space: nowrap;
    }

    .status.completed {
      color: var(--gp-muted);
      box-shadow: none;
    }

    .status.pending {
      opacity: 0.5;
    }

    .status.blocked {
      color: var(--gp-blocked);
    }

    .status.active,
    .objective-row[data-status="active"] .objective-name {
      --gp-loading-spread: calc(var(--gp-objective-status-size) * 1.4);
      --gp-loading-base: var(--gp-muted);
      --gp-loading-shimmer: color-mix(in srgb, var(--gp-muted) 50%, var(--gp-text));
      background-image:
        linear-gradient(
          90deg,
          transparent calc(50% - var(--gp-loading-spread)),
          var(--gp-loading-shimmer) 50%,
          transparent calc(50% + var(--gp-loading-spread))
        ),
        linear-gradient(var(--gp-loading-base), var(--gp-loading-base));
      background-position:
        100% center,
        0 0;
      background-repeat: no-repeat, no-repeat;
      background-size:
        250% 100%,
        auto;
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      -webkit-text-fill-color: transparent;
      animation: loading-shimmer 3.2s linear infinite;
      will-change: background-position;
    }

    :is(.phase-paused, .phase-blocked)
      :is(.status.active, .objective-row[data-status="active"] .objective-name) {
      background-image: none;
      color: var(--gp-muted);
      -webkit-text-fill-color: currentColor;
      animation: none;
      will-change: auto;
    }

    .phase-blocked .status.active {
      color: var(--gp-blocked);
    }

    .objective-main {
      min-width: 0;
      margin-inline-start: var(--gp-objective-main-inset);
    }

    .objective-line {
      display: flex;
      min-width: 0;
      align-items: center;
    }

    .objective-name {
      overflow: hidden;
      min-width: 0;
      color: var(--gp-icon-muted);
      font-size: var(--gp-objective-copy-size);
      line-height: 1.25;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .optional-badge {
      flex: none;
      margin-left: 6px;
      color: var(--gp-muted);
      font-size: max(9px, calc(var(--gp-font-size-sm) - 2px));
      line-height: 1.3;
    }

    .optional-list {
      display: grid;
      gap: 8px;
      margin-top: var(--gp-objective-padding-block);
    }

    .mini-track {
      overflow: hidden;
      height: 3px;
      margin-top: 8px;
      margin-inline-start: calc(
        0px - var(--gp-objective-marker-size) - 4px - var(--gp-objective-main-inset) -
          var(--gp-mini-track-leading-extension)
      );
      margin-inline-end: calc(0px - var(--gp-objective-percent-width));
      border-radius: 999px;
      background: var(--gp-track);
    }

    .mini-fill {
      position: relative;
      display: block;
      overflow: hidden;
      height: 100%;
      border-radius: inherit;
      background: linear-gradient(
        90deg,
        var(--gp-grad-a),
        var(--gp-grad-b) 52%,
        var(--gp-grad-c)
      );
      box-shadow: 0 0 8px var(--gp-mini-glow);
      transition: width 420ms ease;
    }

    .mini-fill::after {
      position: absolute;
      inset: -2px auto -2px -38%;
      width: 34%;
      background: linear-gradient(90deg, transparent, var(--gp-sweep), transparent);
      content: "";
      opacity: 0;
      transform: translateX(-180%) skewX(-18deg);
      animation: mini-sweep 5.8s cubic-bezier(0.45, 0, 0.25, 1) infinite;
      animation-delay: var(--sweep-delay);
    }

    .empty-objectives {
      display: grid;
      min-height: 72px;
      place-items: center;
      color: var(--gp-muted);
      font-size: var(--gp-font-size-sm);
      text-align: center;
    }

    .notice {
      margin: 1px 0;
      padding: 2px 0;
      color: var(--gp-muted);
      font-size: max(9px, calc(var(--gp-font-size-sm) - 2px));
      line-height: 1.4;
    }

    .objective-percent {
      width: 100%;
      min-width: 0;
      color: var(--gp-icon-muted);
      font-size: var(--gp-objective-copy-size);
      font-variant-numeric: tabular-nums;
      font-weight: 600;
      line-height: 1.25;
      direction: ltr;
      text-align: right;
      transform: translateX(calc(0px - var(--gp-objective-percent-shift)));
      unicode-bidi: isolate;
      white-space: nowrap;
    }

    :host([dir="rtl"]) .objective-row > div:first-child {
      justify-items: end;
    }

    :host([dir="rtl"]) .status-index {
      right: calc(0px - var(--gp-mini-track-leading-extension));
      left: auto;
    }

    :host([dir="rtl"]) .status {
      text-align: right;
    }

    :host([dir="rtl"]) .objective-percent {
      text-align: left;
      transform: translateX(var(--gp-objective-percent-shift));
    }

`;
