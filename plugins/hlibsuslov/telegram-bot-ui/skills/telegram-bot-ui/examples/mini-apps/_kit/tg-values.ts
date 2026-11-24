// Values Telegram renders itself: Telegram Stars, grams (the TON blockchain's coin, renamed from Toncoin to Gram
// in June 2026), gift colours and rarity. Pure functions, no DOM. Rules: references/mini-apps/telegram-elements.md.

const NANO = 1_000_000_000n;

/** Whole Stars as the number Telegram shows: grouped, no decimals ("1,250"). Prices in Stars are integers [API]. */
export function formatStars(amount: number, locale?: string): string {
  if (!Number.isSafeInteger(amount)) throw new RangeError(`Stars amount must be an integer, got ${amount}`);
  return new Intl.NumberFormat(locale, { maximumFractionDigits: 0 }).format(amount);
}

/** A Stars balance with its nanostar part (StarAmount): at most two decimals, truncated so it never shows more than
 *  the user has. `nanostars` is -999999999..999999999 and has the sign of the whole (API). */
export function formatStarBalance(amount: number, nanostars = 0, locale?: string): string {
  if (!Number.isSafeInteger(amount) || !Number.isSafeInteger(nanostars) || Math.abs(nanostars) >= 1e9) {
    throw new RangeError('StarAmount: integer amount and nanostar_amount within ±999999999');
  }
  const cents = Math.trunc(nanostars / 1e7); // hundredths, toward zero
  const value = amount + cents / 100;
  return new Intl.NumberFormat(locale, { minimumFractionDigits: 0, maximumFractionDigits: cents ? 2 : 0 }).format(value);
}

/** Plain text for places that take no markup (MainButton, popups, bot messages): "⭐ 250", "⭐ 250 / month". */
export function starsText(amount: number, opts: { period?: string; locale?: string } = {}): string {
  return `⭐ ${formatStars(amount, opts.locale)}${opts.period ? ` / ${opts.period}` : ''}`;
}

/** Nanograms (a decimal string from the API, or a bigint) to a display number. Truncates, never rounds up;
 *  `maxFraction` 0-9 (default 4), trailing zeros dropped: "12.5", "-0.0412", "1,000"; `signed` adds "+" (transfers). */
export function formatGrams(nano: string | bigint, opts: { maxFraction?: number; locale?: string; signed?: boolean } = {}): string {
  const v = typeof nano === 'bigint' ? nano : parseNanoString(nano);
  const max = opts.maxFraction ?? 4;
  if (!Number.isInteger(max) || max < 0 || max > 9) throw new RangeError('maxFraction is 0-9');
  const neg = v < 0n;
  const abs = neg ? -v : v;
  const whole = abs / NANO;
  const frac = (abs % NANO).toString().padStart(9, '0').slice(0, max).replace(/0+$/, '');
  const parts = new Intl.NumberFormat(opts.locale, { maximumFractionDigits: 1, minimumFractionDigits: 1 }).formatToParts(1.5);
  const point = parts.find((p) => p.type === 'decimal')?.value ?? '.';
  const grouped = new Intl.NumberFormat(opts.locale, { maximumFractionDigits: 0 }).format(whole);
  const text = frac ? `${grouped}${point}${frac}` : grouped;
  if (!whole && !frac) return text;
  return neg ? `-${text}` : opts.signed ? `+${text}` : text; // the same minus Intl.NumberFormat writes
}

/** "12.5 GRAM": the amount with the coin's ticker. The API's currency code stays "TON" (the network's name). */
export function gramsText(nano: string | bigint, opts: { maxFraction?: number; locale?: string; signed?: boolean } = {}): string {
  return `${formatGrams(nano, opts)} GRAM`;
}

/** User input ("1.25", "1,25", "0.5") to nanograms. Null for anything else: no exponent, sign, or 10th decimal. */
export function toNanograms(input: string): bigint | null {
  const m = /^\s*(\d{1,12})(?:[.,](\d{1,9}))?\s*$/.exec(input);
  if (!m) return null;
  return BigInt(m[1]) * NANO + BigInt((m[2] ?? '').padEnd(9, '0'));
}

function parseNanoString(s: string): bigint {
  if (!/^-?\d{1,30}$/.test(s)) throw new RangeError(`not a nanogram amount: ${JSON.stringify(s)}`);
  return BigInt(s);
}

/** rarity_per_mille as Telegram shows it: "1.2%", "0.3%", "15%". Null for 0 (crafted models carry a tier instead). */
export function rarityPercent(perMille: number): string | null {
  if (!Number.isInteger(perMille) || perMille < 0 || perMille > 1000) throw new RangeError('rarity_per_mille is 0-1000');
  if (perMille === 0) return null;
  return `${(perMille / 10).toFixed(perMille % 10 ? 1 : 0)}%`;
}

export type CraftedRarity = 'uncommon' | 'rare' | 'epic' | 'legendary';
const TIERS: readonly CraftedRarity[] = ['uncommon', 'rare', 'epic', 'legendary'];

/** UniqueGiftModel.rarity (9.4) to a label; unknown future tiers fall back to the raw word, capitalised. */
export function rarityTier(rarity: string | undefined): string | null {
  if (!rarity) return null;
  const known = (TIERS as readonly string[]).includes(rarity);
  return known || /^[a-z]{1,20}$/.test(rarity) ? rarity[0].toUpperCase() + rarity.slice(1) : null;
}

/** An RGB integer from the API (0xRRGGBB) to a CSS hex colour. */
export function rgb(int: number): string {
  if (!Number.isInteger(int) || int < 0 || int > 0xffffff) throw new RangeError(`not an RGB integer: ${int}`);
  return `#${int.toString(16).padStart(6, '0')}`;
}

export interface GiftBackground { center_color: number; edge_color: number; text_color: number }
export interface UniqueGiftBackdropColors extends GiftBackground { symbol_color: number }

/** CSS custom properties for .tma-gift: the regular gift's background (9.3) or a unique gift's backdrop. */
export function giftVars(c: GiftBackground | UniqueGiftBackdropColors): Record<string, string> {
  const vars: Record<string, string> = {
    '--gift-center': rgb(c.center_color), '--gift-edge': rgb(c.edge_color), '--gift-text': rgb(c.text_color),
  };
  if ('symbol_color' in c) vars['--gift-symbol'] = rgb(c.symbol_color);
  return vars;
}

export interface UniqueGiftColors {
  light_theme_main_color: number; light_theme_other_colors: number[];
  dark_theme_main_color: number; dark_theme_other_colors: number[];
}

/** The colour a unique gift gives its owner's name (UniqueGiftColors, 9.3), for the current scheme. */
export function giftNameColor(c: UniqueGiftColors, scheme: 'light' | 'dark'): string {
  return rgb(scheme === 'dark' ? c.dark_theme_main_color : c.light_theme_main_color);
}

/** A limited gift's counter: "142 of 5,000 left" and the share left for a progress bar. */
export function limitedLeft(remaining: number, total: number, locale?: string): { text: string; ratio: number } {
  if (!Number.isSafeInteger(remaining) || !Number.isSafeInteger(total) || total <= 0 || remaining < 0 || remaining > total) {
    throw new RangeError('remaining_count 0..total_count');
  }
  const n = new Intl.NumberFormat(locale);
  return { text: remaining ? `${n.format(remaining)} of ${n.format(total)} left` : 'Sold out', ratio: remaining / total };
}
