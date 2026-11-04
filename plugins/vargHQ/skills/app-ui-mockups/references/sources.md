# Sources: app UI mockups family

Every URL below was opened in this research session (WebFetch, the X tools, or a raw GitHub/unpkg download).
Numbers are shared by all ten reference files. Template slugs used: `amber-booth-console`, `agent-terminal-session`,
`code-slab-3d`, `exploded-ui-panels`, `terminal-command-run`, `team-chat-channel`, `code-editor-walkthrough`,
`phone-message-thread`, `desktop-notification-banner`, `desktop-terminal-window`.

Trademarks: iMessage, macOS, Terminal and SF fonts belong to Apple; Slack and its logo to Slack Technologies (Salesforce);
Visual Studio Code / VS Code and its icon to Microsoft; Claude and Claude Code to Anthropic; Ghostty is an MIT-licensed
open-source project. We build recognisable mockups only: no platform logos, no real accounts, no real people, no fake reviews.

## Practitioners on X

| n | Who | Why they count | Post | What we took | Used by |
|---|---|---|---|---|---|
| 1 | Adam Pietrasiak (@pie6k) | Built Screen Studio, the auto-zoom screen recorder used for many SaaS launch clips | https://x.com/pie6k/status/1586636942879645696 and https://x.com/pie6k/status/1574762885691105281 | Record with the cursor hidden, re-add it with smoothed motion; camera moves about 1 s before a click group; clamp zoom so the backdrop never shows at frame edges; group clicks to cut camera moves | exploded-ui-panels, code-editor-walkthrough, team-chat-channel, desktop-terminal-window |
| 2 | Emil Kowalski (@emilkowalski) | Design engineer at Linear (says so in his post), known for UI animation teaching | https://x.com/emilkowalski/status/1954891053032755560 , reply https://x.com/emilkowalski/status/1954893389679206700 , https://x.com/emilkowalski/status/1970144111261868487 , https://x.com/emilkowalski/status/2102798004281635184 | Never scale in from 0, start at 0.93+; pair with a 125 ms ease-out opacity fade; ease-out for enter and exit; overlay and panel durations must match; ease-out felt less abrupt than a spring on a Linear dialog | all ten (entrance rules) |
| 3 | Steve Schoger (@steveschoger) | Co-author of Refactoring UI; designs marketing templates | https://x.com/steveschoger/status/1795585777864184025 | Marketing shots use a fully designed, believable "fake UI" for a product that does not exist; worth designing the whole surface | exploded-ui-panels, team-chat-channel |
| 4 | Om Patel (@om_patel5) | Made a launch video by agent and wrote up the process | https://x.com/om_patel5/status/2110398086438584391 | A real screen recording came out dark and busy, the cleaner rebuilt UI won ("dont let authentic beat clear"); check frames halfway through each transition | all ten (fake UI vs recording) |
| 5 | Bohdan Motion (@bohdanmotion) | Motion designer posting product 3D UI reveals | https://x.com/bohdanmotion/status/2106544538231640442 | Reference for a custom 3D UI reveal that resolves into a logo (look only) | exploded-ui-panels |

## Articles, docs and source code

| n | Name / author | URL | What we took | Used by |
|---|---|---|---|---|
| 10 | Dhakal, Feit, Kristensson, Oulasvirta, CHI 2018 (EurekAlert release) | https://www.eurekalert.org/news-releases/569762 | 136M keystrokes, 168k typists: average 52 WPM, fastest about 120 WPM, fast typists roll over 40–70% of keys | typing in all terminal/editor/chat templates |
| 11 | Brysbaert 2019 meta-analysis (BPS Research Digest) | https://www.bps.org.uk/research-digest/most-comprehensive-review-date-finds-average-persons-reading-speed-slower | Adults read about 238 wpm (190 studies) | chat and caption holds |
| 12 | Netflix English (USA) Timed Text Style Guide | https://partnerhelp.netflixstudios.com/hc/en-us/articles/217350977-English-USA-Timed-Text-Style-Guide | 20 cps max for adult content, 17 cps for children, 42 characters per line | reading-time formula |
| 13 | Netflix Timed Text Style Guide: General Requirements | https://partnerhelp.netflixstudios.com/hc/en-us/articles/215758617-Timed-Text-Style-Guide-General-Requirements | Minimum event 5/6 s, maximum 7 s | reading-time formula |
| 14 | Charm VHS (MIT) source: vhs.go, style.go, draw.go, video.go | https://github.com/charmbracelet/vhs | Defaults: TypingSpeed 50 ms/char, FontSize 22, LineHeight 1.0, Padding 60, 1200×600, 50 fps, window bar 30 px, dots #FF4F4D / #FEBB00 / #00CC1D, bg #171717, fg #dddddd | terminal-command-run, desktop-terminal-window, agent-terminal-session |
| 15 | VHS best-practice skill (marcfargas/skills 0.5.1) | https://cdn.jsdelivr.net/npm/@marcfargas/skills@0.5.1/vhs/SKILL.md | TypingSpeed 25–40 ms (50 ms feels slow), Sleep 3 s after quick commands and 5 s after long ones, demos under 30 s, PlaybackSpeed 2.0 to compress | terminal templates |
| 16 | Thorsten Ball, "How to Demo" (Register Spill newsletter) | https://thorstenball.com/how-to-demo | Record 1080p, bump the font size "and once more", record only the terminal, know where the viewer looks on every frame, show before/after | terminal and editor templates |
| 17 | Ghostty (MIT) Config.zig and font/embedded.zig | https://github.com/ghostty-org/ghostty | Defaults: background #282C34, foreground #FFFFFF, font-size 13 pt on macOS, window padding 2 px, block cursor that blinks, transparent macOS titlebar, embedded JetBrains Mono | agent-terminal-session, terminal-command-run |
| 18 | Claude Code docs, Interactive mode | https://code.claude.com/docs/en/interactive-mode | Shift+Tab cycles permission modes (Manual, acceptEdits, plan…); Ctrl+T task list shows up to five tasks; "Esc to cancel" style status lines | agent-terminal-session |
| 19 | Claude Code docs, Settings | https://code.claude.com/docs/en/settings | While Claude works it shows a spinner with a one-line tip under it | agent-terminal-session |
| 20 | Anthropic brand-guidelines skill | https://github.com/anthropics/skills/blob/main/skills/brand-guidelines/SKILL.md | Dark #141413, Light #faf9f5, Orange #d97757, Blue #6a9bcc, Green #788c5d | agent-terminal-session |
| 21 | VS Code theme-defaults: 2026-dark.json, 2026-light.json, dark_plus.json (MIT) | https://github.com/microsoft/vscode/tree/main/extensions/theme-defaults/themes | Exact workbench and token colors for Dark 2026 / Light 2026 | code-editor-walkthrough |
| 22 | Visual Studio Code brand guidelines | https://code.visualstudio.com/brand | Name and icon are Microsoft trademarks; don't use them to promote your own video or channel; don't recolor or lock up the icon | code-editor-walkthrough |
| 23 | Microsoft CodeTour (MIT) | https://github.com/microsoft/codetour | A walkthrough = steps anchored to file+line, markdown description in a comment thread, Previous/Next navigation | code-editor-walkthrough |
| 24 | Code Hike, token transitions docs (Rodrigo Pombo's code-walkthrough library) | https://codehike.org/docs/code/token-transitions | Token-level FLIP-style transitions via WAAPI, max transition 900 ms, fill both | code-editor-walkthrough, code-slab-3d |
| 25 | Dracula theme spec + VS Code repo license (MIT) | https://spec.draculatheme.com/ , https://github.com/dracula/visual-studio-code | Palette and token mapping | code-slab-3d, terminal templates |
| 26 | GitHub Primer primitives 10.3.4 (dark, dark-dimmed) + github-vscode-theme (MIT) | https://unpkg.com/@primer/primitives@10.3.4/dist/css/functional/themes/dark.css , https://unpkg.com/@primer/primitives@10.3.4/dist/css/functional/themes/dark-dimmed.css , https://github.com/primer/github-vscode-theme | GitHub Dark and Dimmed backgrounds and syntax colors | code-slab-3d |
| 27 | Atom one-dark-syntax colors.less (MIT) | https://github.com/atom/one-dark-syntax | One Dark HSL palette (converted to hex) | code-slab-3d |
| 28 | Carbon (MIT) lib/constants.js | https://github.com/carbon-app/carbon | Code-image defaults: padding 56 px, shadow offset 20 px blur 68 px, 14 px font, 133% line height, width 680 | code-slab-3d |
| 29 | ray.so by Raycast (MIT) padding.ts, font.ts | https://github.com/raycast/ray-so | Padding options 16/32/64/128 (default 64); default font JetBrains Mono | code-slab-3d |
| 30 | Apple HIG, Notifications | https://developer.apple.com/design/human-interface-guidelines/notifications | Concise; title-style title, no ending punctuation; sentence-case complete-sentence body; system draws the app icon at the leading edge; don't put the app name in the text | desktop-notification-banner |
| 31 | Apple HIG, Typography (macOS built-in text styles) | https://developer.apple.com/design/human-interface-guidelines/typography | macOS Body 13/16 pt, Headline 13/16 bold, Callout 12/15, Subheadline 11/14 | desktop-notification-banner, desktop-terminal-window |
| 32 | Apple HIG, Motion | https://developer.apple.com/design/human-interface-guidelines/motion | Brief, precise feedback motion; realistic motion that follows expectations (a view that slid down leaves the same way) | desktop-notification-banner |
| 33 | Samuel Kraft, "iOS chat bubbles in CSS" | https://samuelkraft.com/blog/ios-chat-bubbles-css | Sent #0b93f6 / received #e5e5ea, radius 25 px, padding 10×20, line-height 24, max-width 255 (of 450), 15 px between groups, 2 px within a group, tail only on last bubble of a run | phone-message-thread |
| 34 | Apple Support, React with Tapbacks (Messages for Mac) | https://support.apple.com/en-euro/guide/messages/react-with-tapbacks-icht504f698a/14.0/mac/15.0 | Six classic Tapbacks (heart, thumbs up, thumbs down, Ha Ha, !!, ?) plus emoji; one Tapback per message per person | phone-message-thread |
| 35 | Apple Community doc, How iMessage read receipts work | https://discussions.apple.com/docs/DOC-250008552 | "Delivered" under the latest sent bubble, then "Read" + time; never in group chats | phone-message-thread |
| 36 | Slack media kit + brand colors (brandpalettes) | https://slack.com/media-kit , https://brandpalettes.com/slack-logo-color-codes/ | Trademark terms; aubergine #4A154B, blue #36C5F0, green #2EB67D, yellow #ECB22E, red #E01E5A | team-chat-channel |
| 37 | DEV Community, customizing Slack fonts | https://dev.to/masayoshi644/how-to-customize-slack-fonts-using-stylus-for-improved-readability-706 | Slack's web app ships a custom Lato build named "Slack-Lato" (Lato itself is OFL) | team-chat-channel |
| 38 | Slack developer docs, Unfurling links | https://docs.slack.dev/messaging/unfurling-links-in-messages | Classic unfurls are built from OpenGraph / Twitter Card metadata of the link | team-chat-channel |
| 39 | Wikipedia, Monochrome monitor | https://en.wikipedia.org/wiki/Monochrome_monitor | Amber screens use P3 phosphor; amber, green (P1), white (P4); 1960s–80s | amber-booth-console |
| 40 | "What color are phosphors?" (Obsidian notes, cites Patrick Jankowiak's CRT phosphor research) | https://publish.obsidian.md/xybre/permalink/e397c38e-aa6f-45eb-831f-f02a3836abc4 | P3 peaks at 602 nm → #ffb700 / #fa9300 / #f67800 depending on conversion | amber-booth-console |
| 41 | cool-retro-term (GPL-3, parameter ideas only) ApplicationSettings.qml | https://github.com/Swordfish90/cool-retro-term | "Default Amber" profile: font #ff8100 on #000000, bloom 0.6, burn-in 0.3, flicker 0.1, jitter 0.2, static noise 0.1, curvature 0.2, glowing line 0.2 | amber-booth-console, desktop-terminal-window (retro option) |
| 42 | Pushing Pixels interview with David Sheldon-Hicks (Territory Studio founder; screen graphics for Prometheus, Guardians of the Galaxy) | https://www.pushing-pixels.org/2014/08/07/the-craft-of-screen-graphics-and-movie-user-interfaces-interview-with-david-sheldon-hicks-of-territory-studio.html | Decide what content flows through a screen before styling it; research real systems; screens can be "feel" more than readable data; support the story, don't hijack it | amber-booth-console, exploded-ui-panels |
| 43 | Wikipedia, Isometric projection | https://en.wikipedia.org/wiki/Isometric_projection | True isometric = 45° about vertical, then ≈35.264° about horizontal | exploded-ui-panels |
| 44 | Emil Kowalski, "Great animations" | https://emilkowal.ski/ui/great-animations | UI animations usually under 300 ms; animate only transform and opacity; ease-out for snappy feedback | all ten |
| 45 | Screen Studio guide, Animations | https://screen.studio/guide/animations | "Focused" screen animation stabilizes quickly so text is easy to read; motion blur is set separately for cursor, zoom and pan | exploded-ui-panels, code-editor-walkthrough |
| 46 | remotion-bits TypeWriter reference | https://remotion-bits.pages.dev/docs/reference/typewriter | 3 frames/char, delete 2 frames/char, pause after typing 30 frames, cursor blink 30-frame cycle, seeded error simulation with 5-frame correction | terminal, editor, chat templates |
| 47 | GSAP docs, Eases | https://gsap.com/docs/v3/Eases/ | Ease names; default ease power1.out | all ten |
| 48 | Steve Lemuel, Raycast spec teaser (Contra case study) | https://contra.com/p/llNMeeMX-raycast-kinetic-product-motion | Rebuilt the UI in Figma to the brand's design system, animated in Jitter with fast "instant" easing, 15 s, hook in the first 2 s, one sound cue per shortcut | exploded-ui-panels, terminal-command-run |
| 49 | Google Fonts METADATA (google/fonts repo) | https://github.com/google/fonts | OFL confirmed for Inter, Lato, JetBrains Mono, IBM Plex Mono, IBM Plex Sans, Geist Mono, Fira Code, VT323, Share Tech Mono | all ten |
| 50 | Remotion Code Hike template | https://www.remotion.dev/templates/code-hike | Snippet-to-snippet transitions with Code Hike in Remotion | code-editor-walkthrough, code-slab-3d |

## Building blocks (starting values, not expert sources)

| n | Block | URL | Values we start from |
|---|---|---|---|
| 60 | HyperFrames `native-notification-pop` | https://github.com/heygen-com/hyperframes/tree/main/registry/components/native-notification-pop | Underdamped spring ω 15, ζ 0.74: first contact 0.31 s, ~3% overshoot, settled ~0.7 s; exit 0.45 s; blur 3.2cqmin saturate 140% |
| 61 | HyperFrames `chat-message` / `chat-thread` / `typing-indicator` | https://github.com/heygen-com/hyperframes/tree/main/registry/components/chat-message | Bubble enters at scale 0.75, alpha 0.6 → 1, 0.12 s power2.out from the sender's corner; dark-mode sent #0a80f8, received #242428 |
| 62 | HyperFrames `notes-typing` | https://github.com/heygen-com/hyperframes/tree/main/registry/components/notes-typing | Cycled key gaps 33–200 ms (mean ≈ 85 ms), 0.85 s pause before a new line |
| 63 | HyperFrames `cursor-zoom-follow` | https://github.com/heygen-com/hyperframes/tree/main/registry/components/cursor-zoom-follow | Zoom 1.8 (1.2–2.6), camera power3.inOut in 0.85 s / out 1.0 s, aim leads toward the next click, press scale 0.96, click ring 12→44 px over 0.2 s |
| 64 | HyperFrames blocks `code-3d-extrude`, `code-snippet-dark-2026`, `code-snippet-apple-terminal-pro`, `code-terminal-run`, `terminal-simulator`, `code-scroll`, `code-highlight`, `macos-notification`, `exploded-stack`, `ui-3d-reveal`, `message-thread-reveal`, `slack-notification-ad`, `thread-message-stack` | https://github.com/heygen-com/hyperframes/tree/main/registry | Descriptions read from each registry-item.json |

## Cinematic analysis

Thin for this family. The one long-form craft interview that applies is [42] (Territory Studio on screen graphics);
Thorsten Ball [16] and Om Patel [4] cover demo-film craft from the maker's side.
