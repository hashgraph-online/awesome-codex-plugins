# Follow tap prompt

A creator card with a Follow button that a cursor clicks or a finger taps, flipping it to "Following", in the visual language of a platform (TikTok, Instagram, Twitch or X-style). Used as a creator sign-off or mid-roll ask in 9:16, 1:1 or 16:9; about 5 s.

## How the pros do it
- Ask for the follow once the viewer has had a reason to care, not in the intro: intro asks for subscribe/like/comment show up as a retention drop [32]; YouTube's own advice is to ask at the end [33]. Default the prompt to the last 25% of the video or right after the payoff beat.
- Tie the ask to what they get ("Follow for part 2", "Follow for one recipe a day"); generic asks under-perform content-specific ones [37][38].
- Keep it simple and placed where it does not interrupt the content [34]: a card in the upper-middle or lower safe area, never over the face or product.
- The card must sit in the universal 9:16 box (x 120–888, y 288–1248, and x ≤ 780 below y 840) so the real platform's own Follow button and rail do not double up on screen [1][4][5].
- Use the platform's accent only on the button: TikTok-style red #FE2C55 [16]; Twitch purple #9147FF [15]; YouTube Red #FF0033 for a subscribe-style variant [14]. Instagram-style blue and X-style black/white were not published in sources we opened; sample from a current screenshot and keep the value in the preset (we ship `#0095F6` as an unverified starting value).
- Show the state change, because the change is the message: filled "Follow" → outlined/neutral "Following" with a check, 150–250 ms colour cross-fade [26].
- The cursor is a pointing device, so make it readable at phone size: oversized arrow (~3.5× macOS size) whose tip lands on the button, clicks, then moves just below so the result stays visible [40].
- Do not fake follower counts or show real people's handles without permission; buying or faking social indicators for commercial influence is covered by the FTC rule [21].
- Logos and UI looks belong to the platforms; Instagram requires permission for its interface in commercials [17]. Default to "-style" cards with your own avatar and name.

## Presets
| Preset | Look | Key values |
|---|---|---|
| `follow-tap-prompt.tiktok-style` | Dark card, round avatar, red Follow pill, finger tap | button #FE2C55, text #FFFFFF, card #000000 @70%, TikTok Sans 700 |
| `follow-tap-prompt.instagram-style` | White card, avatar ring, blue Follow, cursor click | button #0095F6 (unverified), card #FFFFFF, Inter 600; gradient ring is a generic pink→orange, not Instagram's asset |
| `follow-tap-prompt.twitch-style` | Dark card, purple Follow with heart, cursor click | button #9147FF, card #18181B @90% (house), Inter 700 |
| `follow-tap-prompt.x-style` | Black pill on white card or white pill on black card | black/white only, Inter 700, follower count optional |

## Timing and numbers (5 s = 150 f at 30 fps)
- 0.00–0.45 s: card rises 48 px and fades in, `cubic-bezier(0.05,0.7,0.1,1)` (14 f) [26].
- 0.45–1.20 s: cursor enters from off-frame bottom-right along a slight arc, `power2.inOut`, 0.7 s.
- 1.30 s: press — button scale 1→0.94 in 3 f, cursor scale 1→0.9; release 4 f with `back.out(1.7)` [27].
- 1.40 s: state flip, fill cross-fade 0.2 s (6 f), label swap with 8 px vertical slide; optional count +1 roll.
- 1.6–4.3 s: hold (≥2.5 s readable). Cursor parks 40 px below the button.
- 4.3–4.55 s: card exits down 32 px + fade, `cubic-bezier(0.3,0,0.8,0.15)` (8 f).
- Card at 1080×1920: 660×176 px (≤660 so it clears the right rail below y 840), radius 32 px, avatar 112 px, name 40 px/700, handle 30 px/400 @70% opacity, button 200×72 px radius 36 px (TikTok/IG) or 12 px (X-style uses full pill). Default centre y = 740 (39%), so the whole card sits above y 840 and inside x 120–888; a card placed lower must stay ≤660 px wide and left of x 780.
- 16:9: card 560×136 at bottom-left, 96 px margins.
- Tap variant: finger dot 56 px white @85% with 2 px shadow, ripple ring 0→2.2× over 0.4 s, opacity 0.35→0.
- Sound: soft click at the press frame, 6–10 dB under VO (house default).

## Build it
1. HyperFrames: `tiktok-follow` and `instagram-follow` blocks (profile card + follow button), `x-follow-card` component; cursor from `oversized-cursor` or `magnetic-cursor` [40].
2. Timeline: card `from` → cursor `to` along `motionPath` (or two tweens x/y with different eases for an arc) → press → `set` label at flip time (seek-safe; avoid `onComplete` text swaps) → hold → exit.
3. Remotion: compute cursor position with `interpolate(frame, [36, 60], [start, end], {easing: Easing.bezier(0.45,0,0.55,1)})`; flip state with `frame >= 42`.
4. Params: `platform`, `name`, `handle`, `avatarUrl`, `buttonLabel`, `followedLabel`, `inputDevice: cursor|tap`, `safeZone`.

## Mistakes that look amateur
- Small system cursor that vanishes on phones → 3.5× cursor with dark outline [40].
- Button flips before the click lands → flip 2–3 frames after the press bottom.
- Card overlapping the real TikTok follow "+" on the avatar rail → keep x ≤ 780 below y 840 [1].
- Using a real creator's face/handle without permission, or a fake 1.2M followers → own assets, real numbers [21].
- Follow ask in the first 3 s → move it after the payoff [32][33].
- Platform logo glued onto the card → leave logos out; colour and shape already read as the platform [17].

## Sources
[1] TikTok safe-zone template · [4] Meta Reels specs · [5] Google vertical safe zone · [14] YouTube brand colour · [15] Twitch tokens · [16] TikTok tokens · [17] Meta Instagram brand · [21] FTC fake reviews and indicators rule · [26] Material 3 motion · [27] GSAP source · [32] Paddy Galloway · [33] YouTube Creators · [34] Nick Nimmin · [37] Dara Denney · [38] jack friks · [40] HyperFrames registry.
