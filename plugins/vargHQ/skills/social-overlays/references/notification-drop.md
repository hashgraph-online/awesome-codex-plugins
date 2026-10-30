# Notification drop

A phone notification banner (iOS/Android-style system banner) or a game-style "achievement unlocked" toast drops in over footage to land a beat: an order, a payment, a message, a milestone. 9:16, 1:1, 16:9; about 3 s.

## How the pros do it
- Write it like a real notification: short title, title-style capitalisation, no ending punctuation; body in sentence case, complete and short; don't repeat the app name in the text because the system shows the icon and name [31].
- Prefer a specific, useful title (headline, event, subject) over a generic "New message" [31]. In ads the title is the payoff: "Order shipped", "Payment received: $1,240".
- Never show private data from a real person; Apple's marketing rules ask for fictional account information in screen content [24], and the HIG warns against sensitive content in notifications [31].
- In App Store-style marketing Apple shows a single push notification on the lock screen and the notification must open the app it belongs to [24]. One banner per beat reads clean; stacks are a deliberate "pile-up" effect, not the default.
- A notification is a sound moment: Apple suggests a short, distinctive, professionally produced sound [31]. Sync the SFX to the banner's landing frame.
- System banners live at the top of the phone, but a vertical video's top band is covered by platform UI: TikTok 240 px [1], Shorts 288 px [5], Reels 14% [4]. Drop the banner to y ≈ 300–340, or show it inside a phone mockup where the phone's own top is in the safe box.
- Motion: fast arrival, soft overshoot, then rest; the HyperFrames `native-notification-pop` component is built on that interruptible-spring profile [40]. Exit upward, faster than the entry [26].
- Achievement toast: icon disc first, then the text slides out of it; it is a reward beat, so allow a slightly bigger overshoot and a sparkle, but keep it under 0.6 s to settle.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `notification-drop.ios-banner` | Light frosted rounded banner, app icon, bold title, 1–2 body lines, "now" | bg #F5F5F7 @78% + blur 30 px (house), radius 40 px, Inter 600/400, spring in 0.45 s |
| `notification-drop.dark-banner` | Dark frosted variant for bright footage | bg #1C1C1E @72% + blur 30 px (house), text #FFFFFF / #EBEBF5 @60% |
| `notification-drop.android-style` | Flatter card, smaller radius, app name row on top | radius 28 px, Roboto 500/400, emphasized decelerate 0.4 s |
| `notification-drop.achievement` | Dark pill, round trophy icon pops then text slides out | pill #111111 @90%, icon disc 96 px in accent, `back.out(2)` icon, text slide 0.3 s |

## Timing and numbers (3 s = 90 f)
- 0.00–0.45 s: banner from y−140 px (above its rest) to rest, spring (Remotion `{damping:16, stiffness:210, mass:1}`, or GSAP `back.out(1.4)` over 0.45 s) [27][30]. Opacity 0→1 in the first 0.15 s.
- SFX on the frame the banner first reaches rest (~frame 10–12).
- Hold 0.45–2.55 s (≥2 s readable for ≤12 words at 5–10 words/s) [3].
- 2.55–2.80 s: exit up 140 px + fade, `cubic-bezier(0.3,0,0.8,0.15)` (7–8 f) [26].
- Achievement: icon pops 0→1 in 0.25 s `back.out(2)`, pill width expands from icon width to full in 0.3 s `power3.out` starting +0.15 s, text fades in +0.1 s after.
- Sizes at 1080×1920 (full-frame overlay): banner 960×184 px, x centred (60 px margins), rest y = 320; icon 88 px radius 20 px; title 36 px/600; body 34 px/400; "now" 28 px @55%. Inside a phone mockup scale to the phone's width (banner ≈ 94% of phone screen width).
- 16:9: banner 760×150 top-right at 48 px margins (macOS style), or centred top in a phone mockup.

## Build it
1. HyperFrames: `native-notification-pop` (iOS or macOS, spring, blur), `macos-notification`, `notification-stack`/`notification-pileup`/`notification-cascade` for stacks, `liquid-glass-notification` and `ios26-liquid-glass` for glass looks; phone frame via `vfx-iphone-device` [40].
2. Blur behind the banner: `backdrop-filter: blur(30px) saturate(180%)`. Verify one rendered frame; if the renderer drops backdrop-filter, pre-blur a copy of the footage and mask it to the banner shape.
3. GSAP: `tl.fromTo(banner, {y:-140, autoAlpha:0}, {y:0, autoAlpha:1, duration:0.45, ease:"back.out(1.4)"}, 0)` then `.to(banner, {y:-140, autoAlpha:0, duration:0.25, ease:"power2.in"}, 2.55)`.
4. Remotion: `const s = spring({frame, fps, config:{damping:16, stiffness:210}}); translateY = interpolate(s,[0,1],[-140,0])`.
5. Params: `appIconUrl`, `appName`, `title`, `body`, `timeLabel`, `theme`, `sound`, `inPhone`.

## Mistakes that look amateur
- Banner hidden under TikTok/Shorts top UI → rest y ≥ 300 [1][5].
- "Notification: You have a new notification!" → specific title, no app name repeated, no "!" [31].
- Real customer name and amount from a screenshot → fictional data [24].
- Linear slide with no settle → spring with soft overshoot [30].
- Six banners stacked as the default → one per beat; stack only as a deliberate pile-up.
- Using Apple/Xbox/PlayStation logos or their exact system sounds → own icon, own SFX.

## Sources
[1] TikTok safe-zone template · [3] TikTok creative best practices · [4] Meta Reels specs · [5] Google vertical safe zone · [24] Apple App Store marketing guidelines · [26] Material 3 motion · [27] GSAP source · [30] Remotion spring · [31] Apple HIG Notifications · [40] HyperFrames registry.
