import { css } from "lit";

export const colorTokenStyles = css`
    :host {
      /* Standalone fallback layer. Codex token names belong in codex-theme-tokens.ts only. */
      --gp-fallback-panel: rgba(255, 255, 255, 0.96);
      --gp-fallback-line: rgba(52, 59, 70, 0.14);
      --gp-fallback-line-strong: rgba(52, 59, 70, 0.24);
      --gp-fallback-text: #242933;
      --gp-fallback-muted: #69717e;
      --gp-fallback-complete: #23856d;
      --gp-fallback-blocked: #b2532e;
      --gp-fallback-paused: #3b6baf;
      --gp-fallback-accent: #8f5ce7;
      --gp-fallback-font-size: 14px;
      --gp-on-status: #ffffff;

      /* Component decoration derived from the semantic layer. */
      --gp-grad-a: color-mix(in oklab, var(--gp-accent) 78%, var(--gp-text));
      --gp-grad-b: var(--gp-accent);
      --gp-grad-c: color-mix(in oklab, var(--gp-accent) 76%, var(--gp-panel));
      --gp-grad-d: color-mix(in oklab, var(--gp-accent) 68%, var(--gp-panel-raised));
      --gp-glow: color-mix(in srgb, var(--gp-accent) 30%, transparent);
      --gp-soft-glow: color-mix(in srgb, var(--gp-accent) 18%, transparent);
      --gp-panel-shadow: color-mix(in srgb, var(--gp-text) 6%, transparent);
      --gp-track-shadow: color-mix(in srgb, var(--gp-text) 9%, transparent);
      --gp-mini-glow: color-mix(in srgb, var(--gp-accent) 12%, transparent);
      --gp-sweep: rgba(255, 255, 255, 0.72);
      --gp-sweep-soft: rgba(255, 255, 255, 0.18);
      --gp-sweep-strong: rgba(255, 255, 255, 0.5);
      --gp-sweep-faint: rgba(255, 255, 255, 0.12);
      --gp-particle: color-mix(in oklab, var(--gp-panel-raised) 82%, white);
      --gp-particle-glow: rgba(255, 255, 255, 0.76);
      --gp-particle-color-glow: color-mix(in srgb, var(--gp-accent) 38%, transparent);
      --gp-frontier-border: color-mix(in oklab, var(--gp-accent) 84%, var(--gp-text));
      --gp-frontier: color-mix(in oklab, var(--gp-panel-raised) 88%, white);
      --gp-frontier-ring: color-mix(in srgb, var(--gp-accent) 14%, transparent);
      --gp-frontier-glow: color-mix(in srgb, var(--gp-accent) 54%, transparent);
      --gp-frontier-shadow: color-mix(in srgb, var(--gp-text) 18%, transparent);
      --gp-sparkle: #ffffff;
      --gp-sparkle-glow: rgba(255, 255, 255, 0.86);
      --gp-sparkle-color-glow: color-mix(in srgb, var(--gp-accent) 52%, transparent);
      --gp-sparkle-ray: rgba(255, 255, 255, 0.9);
      --gp-reduced-frontier: rgba(255, 255, 255, 0.14);
    }

    :host([theme="dark"]) {
      --gp-fallback-panel: rgba(37, 40, 47, 0.98);
      --gp-fallback-line: rgba(218, 223, 232, 0.13);
      --gp-fallback-line-strong: rgba(218, 223, 232, 0.24);
      --gp-fallback-text: #f0f2f5;
      --gp-fallback-muted: #a5adb9;
      --gp-fallback-complete: #55b99b;
      --gp-fallback-blocked: #e18a62;
      --gp-fallback-paused: #82afe9;
      --gp-frontier-border: rgba(255, 255, 255, 0.78);
      --gp-frontier: color-mix(in oklab, var(--gp-panel-raised) 88%, white);
    }

    @media (prefers-color-scheme: dark) {
      :host(:not([theme="light"])) {
        --gp-fallback-panel: rgba(37, 40, 47, 0.98);
        --gp-fallback-line: rgba(218, 223, 232, 0.13);
        --gp-fallback-line-strong: rgba(218, 223, 232, 0.24);
        --gp-fallback-text: #f0f2f5;
        --gp-fallback-muted: #a5adb9;
        --gp-fallback-complete: #55b99b;
        --gp-fallback-blocked: #e18a62;
        --gp-fallback-paused: #82afe9;
        --gp-frontier-border: rgba(255, 255, 255, 0.78);
        --gp-frontier: color-mix(in oklab, var(--gp-panel-raised) 88%, white);
      }
    }
`;
