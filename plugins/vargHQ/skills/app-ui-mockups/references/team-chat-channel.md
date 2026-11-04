# Team chat channel

Messages landing in a workplace chat channel (Slack-like): avatar, bold name, timestamp, message text, link unfurl, emoji reaction pills, a "N replies" thread link. For B2B launch videos ("your team asked for this"), bot/integration demos and social proof told as channel traffic. 16:9 shows the full desktop app (sidebar + channel); 9:16 and 1:1 crop to the message column only. Typical length 8–12 s.

Slack, its logo and its UI are trademarks of Slack Technologies; this is a look-alike mockup. Use invented people and invented workspaces, no Slack logo, and do not present invented messages as real customer quotes.

## How the pros do it
- Rebuild the UI instead of recording the real app: designers build complete, believable "fake UI" for marketing, and a clean rebuilt surface beats a dark, busy capture. [3][4]
- Read-time rules decide the beat: hold each message for 0.6 s + characters ÷ 15 (min 1.0 s); a channel message has more chrome (name, time, avatar) than a subtitle, so stay well under the 20 cps adult subtitle limit. [11][12][13]
- New messages appear at the bottom and push the column up; make the push and the entrance one motion (0.25–0.35 s ease-out) so the eye stays on the newest line. [2][44]
- Enter with a small scale/opacity move (0.97 → 1 or y 12 px → 0, opacity 0 → 1) instead of a big slide: UI motion should be short, ease-out and limited to transform and opacity. [2][44]
- Link unfurls are built from the page's OpenGraph data: site name, bold title, short description, optional image; they appear a beat after the message text (0.3–0.5 s), as the real crawl does. [38]
- Use the brand palette for accents only: aubergine #4A154B is the brand anchor; accent blue #36C5F0, green #2EB67D, yellow #ECB22E, red #E01E5A. The Slack app uses a custom Lato build ("Slack-Lato"); Lato itself is OFL. [36][37][49]
- Guide the eye: zoom the camera toward the message that matters (1.3–1.6×) with the camera starting about 1 s before the beat, and never let the zoom show the backdrop at the frame edge. [1][63]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `team-chat-channel.conversation` | 4–6 messages from 3 people in #launch | hold = 0.6 + chars/15 s, entrance 0.3 s power2.out y 12 px, avatar 36 px radius 8 px, name 15 px 900, text 15 px/22 px |
| `team-chat-channel.link-unfurl` | One message + rich unfurl card | unfurl 0.35 s after text, 4 px left bar #DDDDDD, title 15 px 700 link blue #1264A3, image max 360 px wide |
| `team-chat-channel.thread` | Parent message + side thread panel opening | thread panel slides in x 40 px → 0, 0.35 s power3.out; "3 replies" link with 3 stacked 20 px avatars |
| `team-chat-channel.reactions` | Emoji pills pop under a message and count up | pill 24 px tall, radius 12 px, pop 0.18 s back.out(2), count ticks every 0.12 s |
| `team-chat-channel.huge-type` | Message column only, giant text for 9:16 | text 4.4% of frame height, avatar 7% of frame width, column 88% of frame width |

## Timing and numbers
- Message hold `clamp(0.6 + chars/15, 1.0, 6.0)` s; reactions arrive 0.4–0.8 s after their message; a 10 s clip fits 4–5 messages plus one reaction burst. [11][12]
- Entrance 0.3 s (9 frames) power2.out; column push = same duration and ease; reactions back.out(2) 0.18 s. [2][44]
- Desktop layout at 1920×1080 (scale ×1.25 of a 1536 px app window for legibility): sidebar 22% width, bg #4A154B (brand aubergine used as the mockup sidebar), channel bg #FFFFFF, text #1D1C1D, timestamp #616061 13 px, hover row #F8F8F8. Dark variant: bg #1A1D21, text #D1D2D3.
- Text 15 px/22 px at app scale → 18–20 px at 1080p; never below 2.2% of frame height for anything the viewer must read.
- Fonts: Lato 400/700/900 (OFL-1.1) as the stand-in for the app's custom Lato build; emoji: Noto Color Emoji (OFL) to avoid Apple emoji licensing.
- 9:16 safe area: column inside x 5–95%, y 12–82%.

## Build it
1. Start from HyperFrames `thread-message-stack` (editable incoming/outgoing stack, 16:9) for the column, `slack-notification-ad` (9:16 lock-screen escalation) for the notification-pile variant, and `cursor-zoom-follow` for the push-in. `npx hyperframes add thread-message-stack`.
2. Write messages as data: `{user, avatarColor, time, text, unfurl?, reactions?, replies?}`; generate initials avatars (no real photos).
3. One paused timeline: per message tween the column `y` and the new row's opacity/y in the same 0.3 s window; schedule unfurl and reactions as relative offsets.
4. Camera: wrap the app in a stage div and tween `scale`/`x`/`y` (power3.inOut, 0.8–1.0 s) to the message rectangle measured at mount; clamp so edges stay inside the app.
5. Remotion: `spring({fps, frame: frame - start, config: {damping: 200}})` for the row, `interpolate` for column y.

## Mistakes that look amateur
- Real workspace names, real people or the Slack logo → invented workspace, initials avatars, no logo. [36]
- Messages that all hold 1 s → time by length; the viewer must finish reading before the next push. [12]
- Unfurl appearing in the same frame as the text → 0.3–0.5 s later, as a crawl would. [38]
- Bouncy springs on every row → ease-out for rows, keep bounce for reactions only. [2]
- Whole desktop at 1:1 scale in a 9:16 crop → crop to the column and enlarge text to ≥ 2.2% of frame height. [16]
- Zooming into an edge so the backdrop shows → clamp the camera to the app bounds. [1]

## Sources
[1] Adam Pietrasiak (@pie6k), Screen Studio — camera leads the click, clamp zoom at edges — https://x.com/pie6k/status/1586636942879645696 , https://x.com/pie6k/status/1574762885691105281
[2] Emil Kowalski (@emilkowalski) — ease-out enter/exit, start ≥ 0.93 scale — https://x.com/emilkowalski/status/1970144111261868487
[3] Steve Schoger (@steveschoger) — designing full fake UI for marketing — https://x.com/steveschoger/status/1795585777864184025
[4] Om Patel (@om_patel5) — clean beats "authentic" — https://x.com/om_patel5/status/2110398086438584391
[11] Brysbaert 2019 via BPS — https://www.bps.org.uk/research-digest/most-comprehensive-review-date-finds-average-persons-reading-speed-slower
[12] Netflix English Timed Text Style Guide — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[13] Netflix General Requirements — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements
[16] Thorsten Ball, How to Demo — bump font size, know where the viewer looks — https://thorstenball.com/how-to-demo
[36] Slack media kit; Slack brand hex values — https://slack.com/media-kit , https://brandpalettes.com/slack-logo-color-codes/
[37] DEV Community — Slack-Lato — https://dev.to/masayoshi644/how-to-customize-slack-fonts-using-stylus-for-improved-readability-706
[38] Slack docs — unfurls from OpenGraph — https://docs.slack.dev/messaging/unfurling-links-in-messages
[44] Emil Kowalski, Great animations — https://emilkowal.ski/ui/great-animations
[49] Google Fonts metadata (Lato OFL) — https://github.com/google/fonts
[63] HyperFrames cursor-zoom-follow — https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-zoom-follow
