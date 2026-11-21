# Phone message thread

A text conversation that plays out bubble by bubble on a phone-style messaging screen (iMessage-like blue/grey bubbles), with typing dots, reactions, read receipts, a link card or a photo. Used for story hooks, ads ("the text that changed everything"), testimonials told as chats and founder stories. Native 9:16 (phone fills the frame); 16:9 and 1:1 show the phone or the thread panel centred. Typical length 7–25 s.

iMessage and the Messages UI belong to Apple. Build a look-alike, never the Apple logo, never a real person's name, number or photo, never a fabricated review presented as real.

## How the pros do it
- Time every bubble by its length, not by a fixed beat: adults read about 238 wpm and subtitle guides cap adult reading at 20 characters per second, with a 5/6 s minimum on screen. On a busy phone UI use 15 cps: hold = 0.6 s + characters ÷ 15, clamped to 1.0–6 s. [11][12][13]
- Group consecutive messages from one sender: 2 px gap inside a run, about 15 px between runs, and draw the tail only on the last bubble of a run. [33]
- Sent bubbles are blue with white text (#0b93f6 in a well-known CSS recreation), received are light grey #e5e5ea with black text; radius about 25 px at a 450 px-wide thread, bubble max-width about 57% of the thread width. Dark mode: sent #0a80f8, received #242428. [33][61]
- A bubble grows in from its sender's corner (scale 0.75 → 1, opacity 0.6 → 1, 0.12 s power2.out), never from scale 0 and never as a plain fade. [61][2]
- Before every incoming bubble show the three-dot typing indicator; it is the beat that makes the viewer wait. Hold it 0.6–1.6 s (longer before a punchline), then swap it for the bubble in place. [61]
- Reactions: the six classic Tapbacks are heart, thumbs up, thumbs down, Ha Ha, !! and ?; one Tapback per message per person; it pops onto the bubble's top corner. [34]
- Read receipts: "Delivered" sits under your most recent sent bubble and turns into "Read" + time; group chats never show them, so don't put "Read" in a group-chat preset. [35]
- Rebuild the UI rather than screen-record a phone: a clean rebuilt UI reads better than a dark, busy recording. Check frames halfway through each scroll and bubble entrance. [4]
- When the thread outgrows the screen, scroll the whole stack up by exactly the new bubble's height plus gap, with the same 0.25–0.35 s ease as the entrance, so the newest bubble lands in the same place every time. [61]

## Presets
| Preset | Look | Key values |
|---|---|---|
| `phone-message-thread.two-people` | Light mode, 1:1 chat, 6–8 bubbles | hold = 0.6 + chars/15 s, typing dots 0.9 s, bubble in 0.12 s power2.out, sent #0b93f6, received #e5e5ea |
| `phone-message-thread.dark-typing` | Dark mode, long typing waits for suspense | bg #000000, sent #0a80f8, received #242428, typing dots 1.2–1.6 s before each reply |
| `phone-message-thread.group` | Group chat with names above received bubbles, no read receipts | sender name 11/13 caption grey #8e8e93 above first bubble of each run, avatar 28 px at run end |
| `phone-message-thread.media` | Photo, voice memo and link card bubbles | photo radius = bubble radius, link card = image 16:9 + title + grey domain, voice memo waveform 24 bars |
| `phone-message-thread.reactions-receipt` | Ends on a Tapback and "Read 9:41" | Tapback pop 0.18 s back.out(2.2) scale 0.6→1, receipt fades in 0.2 s 0.3 s after last sent bubble |
| `phone-message-thread.huge-text` | Oversized bubbles for 9:16 ads | bubble text 5.2% of frame height, max 3 lines, max-width 78% of frame width |

## Timing and numbers
- Reading hold per bubble: `hold_s = clamp(0.6 + chars/15, 1.0, 6.0)`; emoji-only bubble 0.8 s. At 30 fps a 40-character bubble holds 3.3 s ≈ 99 frames. [11][12][13]
- Bubble entrance 0.12 s (4 frames) power2.out, scale 0.75 → 1, transform-origin at the sender's bottom corner. Scroll 0.3 s power2.inOut. [61]
- Typing indicator: three 8 px dots (at 1080 px frame width: 14 px), 0.6 s loop, each dot 0.2 s out of phase, opacity 0.35 → 1. Indicator hold 0.6–1.6 s.
- Tapback: lands 0.3–0.5 s after the bubble it reacts to; 0.18 s back.out.
- Text size: 16:9 thread panel = 3.2% of frame height; 9:16 = 3.6% (normal) or 5.2% (huge). Line-height 1.3. Bubble padding 0.55em × 0.9em.
- Safe zones 9:16: keep bubbles inside x 6–94%, y 14–80% (top status bar and bottom app UI of social platforms). 16:9: thread panel max 42% of frame width, centred or right third.
- Fonts: SF Pro is Apple-licensed and not for this use; use Inter (OFL-1.1) 400/600, or Lato (OFL) for a softer look.
- Status bar: a fixed time (never a live clock), full battery, no carrier name.

## Build it
1. Start from HyperFrames `chat-thread` (full scene: status bar, header pill, real tails, receipt, link card, typing dots) or `message-thread-reveal` (9:16, 25.8 s full ad). Atoms: `chat-message`, `typing-indicator`. Install: `npx hyperframes add chat-thread`.
2. Describe the script as data: `[{from:"them", text, typingBefore:1.0}, {from:"me", text}, {react:"heart", on:3}]`. Compute every start time once from the reading formula; never use timers.
3. One paused GSAP timeline: for each message add typing dots (fromTo opacity), then the bubble (fromTo scale/opacity from its corner), then a stack `y` tween when the content height exceeds the viewport.
4. Measure bubble heights at mount (they wrap), store them, and drive the scroll from stored numbers so seeks are deterministic.
5. Remotion: same data; `interpolate(frame, [start, start+4], [0.75,1], {extrapolateRight:'clamp', easing: Easing.out(Easing.quad)})` per bubble.

## Mistakes that look amateur
- Every bubble on the same 1 s beat → time by length; long texts need 3–5 s. [12]
- Bubbles that scale from 0 or slide in from off-screen → grow 0.75 → 1 from the sender's corner. [2][61]
- A tail on every bubble in a run, or equal gaps everywhere → tail only on the last of a run; 2 px inside a run, ~15 px between. [33]
- "Read" receipts in a group chat, or a receipt under a received bubble → receipts only under your latest sent bubble, 1:1 only. [35]
- Scrolling by an arbitrary amount so new bubbles land in different places → scroll by the new bubble's measured height + gap.
- Real names, real phone numbers or the Apple logo → invented first names, no logos.
- Last bubble cut before it can be read → final hold ≥ the reading formula + 1 s before the end card.

## Sources
[2] Emil Kowalski (@emilkowalski) — scale 0.93+, never from 0 — https://x.com/emilkowalski/status/1954891053032755560
[4] Om Patel (@om_patel5) — rebuilt clean UI beat a real recording — https://x.com/om_patel5/status/2110398086438584391
[11] Brysbaert 2019 via BPS — 238 wpm — https://www.bps.org.uk/research-digest/most-comprehensive-review-date-finds-average-persons-reading-speed-slower
[12] Netflix Timed Text Style Guide (English USA) — 20 cps adult max — https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide
[13] Netflix General Requirements — 5/6 s min, 7 s max — https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements
[33] Samuel Kraft — iOS chat bubbles in CSS: colors, radius, grouping, tails — https://samuelkraft.com/blog/ios-chat-bubbles-css
[34] Apple Support — Tapbacks — https://support.apple.com/en-euro/guide/messages/react-with-tapbacks-icht504f698a/14.0/mac/15.0
[35] Apple Community — read receipts — https://discussions.apple.com/docs/DOC-250008552
[61] HyperFrames chat-message / chat-thread — entry 0.75→1 in 0.12 s, dark colors — https://github.com/heygen-com/hyperframes/tree/main/registry/components/chat-message
