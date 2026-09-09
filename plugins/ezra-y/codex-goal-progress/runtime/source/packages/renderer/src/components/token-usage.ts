import { html, nothing } from "lit";
import type { GoalProgressViewModel } from "../../../contracts/src/index.js";
import type { GoalProgressMessages } from "../locale.js";

type GoalProgressTokenView = NonNullable<GoalProgressViewModel["token"]>;

function formatTokenCount(value: number, locale: string): string {
  if (value < 1_000) {
    return new Intl.NumberFormat(locale).format(value);
  }
  const scale = value < 1_000_000 ? 1_000 : 1_000_000;
  const suffix = value < 1_000_000 ? "K" : "M";
  return `${new Intl.NumberFormat(locale, {
    maximumFractionDigits: 1,
  }).format(value / scale)}${suffix}`;
}

function tokenLabel(
  token: GoalProgressTokenView,
  messages: GoalProgressMessages,
  locale: string,
): string {
  if (token.unavailable === true) {
    return messages.tokenUnavailable;
  }
  if (token.inputTokens !== undefined && token.outputTokens !== undefined) {
    return messages.tokenInputOutput(
      formatTokenCount(token.inputTokens, locale),
      formatTokenCount(token.outputTokens, locale),
    );
  }
  return messages.tokenTotal(formatTokenCount(token.used, locale));
}

export function renderTokenUsage(
  token: GoalProgressTokenView | undefined,
  messages?: GoalProgressMessages,
  locale = "en",
) {
  return token
    ? html`<span
        class="token"
        data-testid="token"
        ?data-stale=${token.stale === true}
        ?data-unavailable=${token.unavailable === true}
        >${messages ? tokenLabel(token, messages, locale) : token.label}</span
      >`
    : nothing;
}
