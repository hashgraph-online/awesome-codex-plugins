// Formatting of Telegram's own values. node --test (Node >= 22.18 strips the types).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  formatGrams, formatStarBalance, formatStars, giftNameColor, giftVars, gramsText, limitedLeft, rarityPercent,
  rarityTier, rgb, starsText, toNanograms,
} from './tg-values.ts';

test('Stars are whole, grouped numbers; the plain-text form carries the sign', () => {
  assert.equal(formatStars(1250, 'en'), '1,250');
  assert.equal(starsText(250, { locale: 'en' }), '⭐ 250');
  assert.equal(starsText(250, { period: 'month', locale: 'en' }), '⭐ 250 / month');
  assert.throws(() => formatStars(2.5));
});

test('a Stars balance shows nanostars as two decimals, truncated', () => {
  assert.equal(formatStarBalance(12, 0, 'en'), '12');
  assert.equal(formatStarBalance(12, 999_999_999, 'en'), '12.99');
  assert.equal(formatStarBalance(0, -500_000_000, 'en'), '-0.5');
  assert.throws(() => formatStarBalance(1, 1_000_000_000));
});

test('grams: exact from nanograms, truncated, grouped, signed', () => {
  assert.equal(formatGrams('12500000000', { locale: 'en' }), '12.5');
  assert.equal(formatGrams('1000000000000', { locale: 'en' }), '1,000');
  assert.equal(formatGrams('-41299999', { locale: 'en' }), '-0.0412');
  assert.equal(formatGrams('999999999', { locale: 'en' }), '0.9999');          // never rounds up to 1
  assert.equal(formatGrams('1', { maxFraction: 9, locale: 'en' }), '0.000000001');
  assert.equal(formatGrams('-1', { locale: 'en' }), '0');                      // no "-0"
  assert.equal(formatGrams(123456789012345678901234n, { maxFraction: 2, locale: 'en' }), '123,456,789,012,345.67');
  assert.equal(formatGrams('1500000000', { locale: 'de' }), '1,5');
  assert.equal(gramsText('2000000000', { locale: 'en' }), '2 GRAM');
  assert.equal(formatGrams('2500000000', { signed: true, locale: 'en' }), '+2.5');
  assert.equal(formatGrams('0', { signed: true, locale: 'en' }), '0');
  for (const bad of ['1.5', '1e9', ' 1', '', '0x10']) assert.throws(() => formatGrams(bad), bad);
});

test('user input to nanograms', () => {
  assert.equal(toNanograms('1.25'), 1_250_000_000n);
  assert.equal(toNanograms('0,5'), 500_000_000n);
  assert.equal(toNanograms('3'), 3_000_000_000n);
  for (const bad of ['-1', '1e3', '0.0000000001', 'abc', '', '1.2.3']) assert.equal(toNanograms(bad), null, bad);
});

test('rarity as Telegram shows it', () => {
  assert.equal(rarityPercent(12), '1.2%');
  assert.equal(rarityPercent(150), '15%');
  assert.equal(rarityPercent(1), '0.1%');
  assert.equal(rarityPercent(0), null);
  assert.equal(rarityTier('legendary'), 'Legendary');
  assert.equal(rarityTier('mythic'), 'Mythic');           // a future tier keeps its word
  assert.equal(rarityTier('<b>x</b>'), null);
  assert.equal(rarityTier(undefined), null);
});

test('gift colours from API integers', () => {
  assert.equal(rgb(0x0a1b2c), '#0a1b2c');
  assert.throws(() => rgb(-1));
  assert.throws(() => rgb(0x1000000));
  assert.deepEqual(giftVars({ center_color: 0x5b8a72, edge_color: 0x2f4f3f, text_color: 0xffffff, symbol_color: 0x1e3329 }), {
    '--gift-center': '#5b8a72', '--gift-edge': '#2f4f3f', '--gift-text': '#ffffff', '--gift-symbol': '#1e3329',
  });
  assert.equal(Object.keys(giftVars({ center_color: 1, edge_color: 2, text_color: 3 })).length, 3);
  const colors = { light_theme_main_color: 0x2a7f62, light_theme_other_colors: [], dark_theme_main_color: 0x7fd1b0, dark_theme_other_colors: [] };
  assert.equal(giftNameColor(colors, 'dark'), '#7fd1b0');
  assert.equal(giftNameColor(colors, 'light'), '#2a7f62');
});

test('limited counter', () => {
  assert.deepEqual(limitedLeft(142, 5000, 'en'), { text: '142 of 5,000 left', ratio: 142 / 5000 });
  assert.equal(limitedLeft(0, 10).text, 'Sold out');
  assert.throws(() => limitedLeft(11, 10));
});
