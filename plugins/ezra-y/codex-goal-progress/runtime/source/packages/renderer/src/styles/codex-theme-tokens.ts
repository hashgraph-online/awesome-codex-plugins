import { css } from "lit";

export const codexThemeTokenStyles = css`
    :host {
      /* Codex host tokens → Goal Progress semantic tokens. */
      --gp-accent: var(
        --color-token-primary,
        var(--color-text-accent, var(--codex-base-accent, var(--gp-fallback-accent)))
      );
      --gp-panel: var(
        --color-token-main-surface-primary,
        var(--codex-base-surface, var(--gp-fallback-panel))
      );
      --gp-panel-raised: var(--codex-base-surface, var(--gp-panel));
      --gp-panel-glass: color-mix(
        in oklab,
        var(--color-background-primary-soft, var(--gp-panel)) 70%,
        transparent
      );
      --gp-panel-glass-compensation: color-mix(
        in oklab,
        var(--color-background-primary-soft, var(--gp-panel)) 14%,
        transparent
      );
      --gp-backdrop-blur: var(--blur-sm, 8px);
      --gp-text: var(
        --color-token-foreground,
        var(--color-token-text-primary, var(--gp-fallback-text))
      );
      --gp-muted: var(--color-token-text-secondary, var(--gp-fallback-muted));
      --gp-icon-muted: var(
        --color-text-foreground-tertiary,
        var(--color-icon-tertiary, var(--gp-muted))
      );
      --gp-line: var(--color-token-border, var(--gp-fallback-line));
      --gp-line-strong: var(--color-token-input-border, var(--gp-fallback-line-strong));
      --gp-track: color-mix(in srgb, var(--gp-text) 12%, transparent);
      --gp-hover: var(
        --color-token-list-hover-background,
        color-mix(in srgb, var(--gp-text) 7%, transparent)
      );
      --gp-control-hover: var(--color-background-button-secondary-hover, var(--gp-hover));
      --gp-focus: var(
        --color-token-focus-border,
        var(--color-ring, var(--gp-accent, var(--gp-fallback-focus)))
      );
      --gp-complete: var(
        --color-text-success,
        var(--color-icon-success, var(--gp-fallback-complete))
      );
      --gp-blocked: var(
        --color-text-error,
        var(--color-icon-error, var(--gp-fallback-blocked))
      );
      --gp-paused: var(--color-text-info, var(--gp-fallback-paused));
      --gp-font-size: var(
        --codex-chat-font-size,
        var(--text-base, var(--gp-fallback-font-size))
      );
      --gp-font-size-sm: max(10px, calc(var(--gp-font-size) - 1px));
      --gp-font-size-xs: max(10px, calc(var(--gp-font-size) - 2px));
      --gp-content-gap: calc(var(--gp-font-size) * 0.642857);
      --gp-content-padding-top: calc(var(--gp-font-size) * 0.714286);
      --gp-content-padding-right: calc(var(--gp-font-size) * 0.857143);
      --gp-content-padding-bottom: calc(var(--gp-font-size) * 0.642857);
      --gp-content-padding-left: calc(var(--gp-font-size) * 0.857143);
      --gp-objective-list-gap: calc(var(--gp-font-size) * 0.5);
      --gp-objective-padding-block: calc(var(--gp-font-size) * 0.571429);
      --gp-objective-padding-inline: calc(var(--gp-font-size) * 0.357143);
      --gp-objective-padding-left: calc(var(--gp-font-size) * 1.571429);
      --gp-objective-column-gap: calc(var(--gp-font-size) * 0.285714);
      --gp-objective-main-inset: calc(var(--gp-font-size) * 0.142857);
      --gp-mini-track-leading-extension: calc(var(--gp-font-size) * 0.928571);
      --gp-objective-percent-shift: calc(var(--gp-font-size) * 0.285714);
      --gp-token-right-shift: calc(
        var(--gp-objective-padding-inline) + var(--gp-objective-percent-shift)
      );
      --gp-control-size: max(24px, calc(var(--gp-font-size) * 1.714286));
      --gp-control-radius: max(10px, calc(var(--gp-font-size) * 0.714286));
    }
`;
