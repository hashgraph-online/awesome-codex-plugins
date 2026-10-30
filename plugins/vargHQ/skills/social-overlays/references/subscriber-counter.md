# Follower counter and goal bar

A creator card whose subscriber/follower number rolls up to a milestone, or a goal bar that fills toward a target ("Road to 100K"). For milestone posts, channel trailers, recap videos and stream overlays. 9:16, 1:1, 16:9; about 3 s.

## How the pros do it
- Format numbers the way the platform does, or the card looks fake: above 1,000, YouTube shows the public count rounded **down** to 3 significant figures, in the UI and the API; only the owner sees the exact number in Studio [13][12]. 1,234 → 1.23K, 12,345 → 12.3K, 123,456 → 123K, 1,234,567 → 1.23M. Below 1,000 show the exact count.
- Truncate, don't round: 4,299 must never display as 4.3K [12].
- Count to a real number. Faking follower/view counts to show commercial influence is banned by the FTC rule [21]; milestone videos should use the creator's real figure (screenshot from their dashboard as input).
- The count-up needs a settle beat: ease out hard (fast start, long slow finish) and land with a small scale pulse so the eye registers the final number [40].
- Use tabular numerals so digits don't shift width while counting (`font-variant-numeric: tabular-nums`; Inter and Roboto support it).
- Abbreviation steps during the roll: switch format at thresholds (999 → 1.00K) rather than rolling through thousands of exact values; the platform never shows "1,000" style for big channels [13].
- Goal bar: show "current / target" and the percent; fill with the same ease as the number so they finish together.
- Colours: YouTube Red #FF0033 / Almost Black #212121 / White for a YouTube-style card [14]; Twitch purple #9147FF [15]; TikTok red #FE2C55 [16]. No platform logos.
- Keep inside the 9:16 safe box (x 120–888, y 288–1248) [1][4][5].

## Presets
| Preset | Look | Key values |
|---|---|---|
| `subscriber-counter.channel-counter` | Avatar + channel name + big number "123K subscribers" rolling up | number Inter 800 120 px tabular, label 34 px @65%, roll 1.6 s `expo.out` |
| `subscriber-counter.milestone-pop` | Number rolls, lands, confetti-free ring pulse + "100K!" | ring #FF0033 scale 1→1.6 opacity .5→0, 0.6 s |
| `subscriber-counter.goal-bar` | "Road to 100K" label, bar fills, "87.4K / 100K · 87%" | bar 720×28 px radius 14, track #FFFFFF @20%, fill accent, 1.8 s `power3.out` |
| `subscriber-counter.stream-goal` | Compact Twitch-style follower goal for 16:9 corner | fill #9147FF, card #18181B @85% (house), Inter 700 |

## Timing and numbers (3 s = 90 f)
- 0.00–0.35 s: card in (scale 0.96→1, fade), `cubic-bezier(0.05,0.7,0.1,1)` [26].
- 0.25–1.85 s: count from `start` to `end` over 1.6 s with `expo.out` (GSAP) or `Easing.out(Easing.exp)` (Remotion); 80% of the change happens in the first ~40% of the time.
- 1.85 s: landing pulse scale 1→1.06→1, 0.25 s, `power2.out`; SFX tick or soft "ding" on this frame (house).
- Hold to 2.8 s minimum 0.9 s of final value; for milestone videos extend hold to ≥ 1.5 s.
- Display format each frame: `fmt(n) = n < 1000 ? n : truncate to 3 sig figs + K/M/B` [13].
- Sizes at 1080×1920: card 840×360 px radius 40 px; avatar 120 px; number 112–128 px/800 (≈6% of height); label 34 px. Goal bar 720×28 px. At 1920×1080: number 96 px, card 760 px wide.
- Bar fill and number driven by the same progress value p ∈ [0,1].

## Build it
1. HyperFrames: `count-up` (eases between values, lands with a restrained scale pulse), `apple-money-count` for a money-style roll, `x-follow-card` for card + follower motion [40].
2. GSAP: tween a proxy `{v: start}` to `end` on the paused timeline; in `onUpdate` write `fmt(Math.floor(proxy.v))`. HyperFrames seeks the timeline, so the DOM is correct on any frame.
3. Remotion: `const v = interpolate(frame, [8, 56], [start, end], {easing: Easing.out(Easing.exp), extrapolateRight:'clamp'})`.
4. `fmt` helper (3 significant figures, truncated): `const p = Math.floor(Math.log10(n)/3); const s = n / 1000**p; const digits = s >= 100 ? 0 : s >= 10 ? 1 : 2; const t = Math.floor(s * 10**digits) / 10**digits; return t.toFixed(digits) + ['','K','M','B'][p];` (tested: 1234 → 1.23K, 4299 → 4.29K, 12345 → 12.3K, 1234567 → 1.23M). Whether trailing zeros show ("1.00K" vs "1K") was not documented in the sources we opened; default `stripZeros: true` (use `String(parseFloat(t.toFixed(digits)))` for the number part: 1.00 → "1", 1.50 → "1.5", 100 stays "100") and match a current screenshot.
5. Params: `start`, `end`, `label`, `goal?`, `platformStyle`, `avatarUrl`, `name`.

## Mistakes that look amateur
- "1,234,567 subscribers" on a YouTube-style card → 1.23M [13].
- Rounding up (4.3K for 4,299) → truncate [12].
- Linear count that stops dead → `expo.out` + landing pulse [40].
- Digits jittering sideways → tabular numerals.
- Invented milestone numbers in a sponsored post → real numbers only [21].
- Bar and number finishing at different times → one shared progress value.

## Sources
[1] TikTok safe-zone template · [4] Meta Reels specs · [5] Google vertical safe zone · [12] Tubefilter (2019 abbreviated counts) · [13] Rival IQ (3 sig figs, rounded down) · [14] YouTube brand colours · [15] Twitch tokens · [16] TikTok tokens · [21] FTC rule · [26] Material 3 motion · [40] HyperFrames registry.
