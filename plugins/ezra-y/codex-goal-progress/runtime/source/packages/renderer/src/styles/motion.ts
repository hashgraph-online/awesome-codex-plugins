import { css } from "lit";

export const motionStyles = css`
    :host([motion-paused]) *,
    :host([motion-paused]) *::before,
    :host([motion-paused]) *::after {
      animation-play-state: paused !important;
    }

    :is(.phase-paused, .phase-blocked) *,
    :is(.phase-paused, .phase-blocked) *::before,
    :is(.phase-paused, .phase-blocked) *::after {
      animation-play-state: paused !important;
    }

    :host([motion-paused]) .particle,
    :host([motion-paused]) .sparkle {
      display: none;
    }

    :host([motion-paused]) .mini-fill::after,
    :host([motion-paused]) .overall-fill::before {
      animation: none !important;
      opacity: 0 !important;
    }

    @keyframes spin {
      from {
        transform: rotate(0deg) translateZ(0);
      }
      to {
        transform: rotate(360deg) translateZ(0);
      }
    }

    @keyframes loading-shimmer {
      from {
        background-position:
          100% center,
          0 0;
      }
      to {
        background-position:
          0% center,
          0 0;
      }
    }

    @keyframes mini-sweep {
      0%,
      60% {
        opacity: 0;
        transform: translateX(-180%) skewX(-18deg);
      }
      65% {
        opacity: 0.22;
      }
      79% {
        opacity: 0.62;
      }
      94%,
      100% {
        opacity: 0;
        transform: translateX(520%) skewX(-18deg);
      }
    }

    @keyframes overall-sweep {
      0%,
      48% {
        opacity: 0;
        transform: translateX(-85%);
      }
      56% {
        opacity: 0.18;
      }
      72% {
        opacity: 0.62;
      }
      88%,
      100% {
        opacity: 0;
        transform: translateX(85%);
      }
    }

    @keyframes particle-drift {
      0% {
        opacity: 0;
        transform: translate3d(-8px, 2px, 0) scale(0.55);
      }
      12% {
        opacity: 0.28;
      }
      45% {
        opacity: var(--opacity);
        transform: translate3d(calc(var(--drift) * 0.48), -1px, 0) scale(1);
      }
      82% {
        opacity: 0.24;
      }
      100% {
        opacity: 0;
        transform: translate3d(var(--drift), -3px, 0) scale(0.72);
      }
    }

    @keyframes sparkle-twinkle {
      0%,
      62%,
      100% {
        opacity: 0;
        transform: translateY(2px) scale(0.65);
      }
      72% {
        opacity: 0.25;
      }
      82% {
        opacity: 0.8;
        transform: translateY(-2px) scale(1);
      }
      91% {
        opacity: 0.12;
        transform: translateY(-5px) scale(0.75);
      }
    }

    @media (prefers-reduced-motion: reduce) {
      *,
      *::before,
      *::after {
        scroll-behavior: auto !important;
        transition: none !important;
        animation: none !important;
      }

      .particle,
      .sparkle {
        display: none;
      }

      .frontier {
        box-shadow: 0 0 0 2px var(--gp-reduced-frontier);
      }

      .status.active,
      .objective-row[data-status="active"] .objective-name {
        background: none;
        color: var(--gp-muted);
        -webkit-text-fill-color: var(--gp-muted);
      }

    }
`;
