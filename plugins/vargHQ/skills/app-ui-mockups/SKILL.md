---
name: app-ui-mockups
description: >-
  Ten animated UI mockups for product, launch and dev-tool videos, rebuilt as HTML instead of screen
  recordings: phone message thread, team chat channel, coding-agent terminal session, terminal command
  run, desktop terminal window, desktop notification banner, code editor walkthrough, 3D code slab,
  exploded UI panels and an amber CRT console. Presets give typing speed (12-20 characters per second
  with seeded gaps), reading holds from character count, entrance easing and scale, camera lead before
  each action, text size as a share of frame height, and theme colors from MIT theme sources, from
  Charm VHS, Screen Studio, Emil Kowalski, Apple HIG and Netflix timing rules. Use when someone wants
  a fake text or Slack conversation, a terminal or Claude Code demo, a code walkthrough or an exploded
  UI shot in a video. NOT for recording a real screen or for real people's messages presented as
  genuine.
license: MIT
compatibility: >-
  HyperFrames 0.8 (npx hyperframes; brings Chrome, needs Node 22 and ffmpeg) or Remotion 4. No API
  key.
metadata:
  author: vargHQ
  version: "0.1.0"
  varg.cost.typical: "0 credits; renders locally"
  varg.runtime.typical: "minutes per template, mostly render time"
  varg.models: "none"
  varg.outputs: "mp4, webm or mov (alpha) from HyperFrames or Remotion"
  varg.presets: "10 templates, 40 presets"
---

# App UI mockups: chats, terminals, code and notifications for launch videos

Ten UI scenes rebuilt as HTML so they look clean, read at a human pace and render the same every time. Typing, streaming and holds follow measured reading and typing speeds rather than guesses.

## Gates

- **Invented people, real product.** Use invented names and workspaces in chats; never put words in a real person's mouth or show a conversation as genuine when it is not.
- **No platform logos.** UIs are recognisable look-alikes; the platforms' names, logos and UI looks are their owners' trademarks.
- **Free fonts only.** Every font in the presets is OFL or Apache. Swap in the person's brand font only if they have a license for video.
- **Seek-safe.** Every value is a function of timeline time; randomness is seeded by frame. No `Date.now()`, `requestAnimationFrame` or unseeded `Math.random()`.
- **No credits here.** These templates render locally for free. Generated footage, voice or music is the varg-ai skill: call `estimate_cost` and wait for the person's approval before any generation.

## Pick a template

10 templates, 40 presets. Each reference file has the same sections: how the pros do it (every rule cited), presets, timing and numbers, how to build it, mistakes that look amateur, sources. Each JSON file holds the same presets as machine-readable values.

| Template | Use it for | Presets | Files |
|---|---|---|---|
| **Coding-agent terminal session** | One AI coding-agent turn (Claude Code-style) in a terminal: prompt, tool calls, diff, spinner, summary. | Prompt and tool calls, Code edit, Still working, Huge type | [`agent-terminal-session.md`](references/agent-terminal-session.md) · [`json`](assets/presets/agent-terminal-session.json) |
| **Amber booth console** | A retro amber projection-booth touchscreen boots, loads your show, counts down and draws your end card. | Boot, load, end card, Clean amber, Footage to amber CRT | [`amber-booth-console.md`](references/amber-booth-console.md) · [`json`](assets/presets/amber-booth-console.json) |
| **Code editor walkthrough** | A VS Code-style guided tour: scroll to a line, highlight it, open a comment thread per step. | Dark 2026, Light 2026, Editor only (vertical) | [`code-editor-walkthrough.md`](references/code-editor-walkthrough.md) · [`json`](assets/presets/code-editor-walkthrough.json) |
| **3D code slab** | Syntax-highlighted code on a lit, bevelled 3D slab that turns through space and settles face-on. | GitHub Dark, Dimmed, One Dark, Dracula | [`code-slab-3d.md`](references/code-slab-3d.md) · [`json`](assets/presets/code-slab-3d.json) |
| **Desktop notification banner** | A macOS-style notification banner with an app icon that springs in at the top right and tucks back out. | Light, Dark, Stack, Huge (phone) | [`desktop-notification-banner.md`](references/desktop-notification-banner.md) · [`json`](assets/presets/desktop-notification-banner.json) |
| **Desktop terminal window** | An editable classic desktop terminal window (macOS Terminal-style) that types and runs a short session. | Basic (light), Pro (dark), Green retro, Amber retro | [`desktop-terminal-window.md`](references/desktop-terminal-window.md) · [`json`](assets/presets/desktop-terminal-window.json) |
| **Exploded UI panels** | An app screen's layers float apart in 3D around an orbiting camera, then slide home into the finished screen. | Orbit and collapse, Isometric stack, Phone layers | [`exploded-ui-panels.md`](references/exploded-ui-panels.md) · [`json`](assets/presets/exploded-ui-panels.json) |
| **Phone message thread** | A messaging-app conversation (iMessage-style bubbles) that plays out bubble by bubble for hooks, ads and stories. | Two people, Typing (dark), Group chat, Photo, voice memo, link preview, Reactions + read receipt, Huge texts | [`phone-message-thread.md`](references/phone-message-thread.md) · [`json`](assets/presets/phone-message-thread.json) |
| **Team chat channel** | Messages, unfurls, threads and reactions landing in a Slack-style channel for B2B launches and social proof. | Conversation, Link unfurl, Thread, Reactions, Huge type | [`team-chat-channel.md`](references/team-chat-channel.md) · [`json`](assets/presets/team-chat-channel.json) |
| **Terminal command run** | A command typed and run in a modern GPU terminal (Ghostty-style), with output, a progress render or a git log. | Command and output, Render with progress, Git log, Huge type | [`terminal-command-run.md`](references/terminal-command-run.md) · [`json`](assets/presets/terminal-command-run.json) |

## Workflow

1. **Match the request** to a template and one or two presets from the table. Say which and why in one line, and show the person the preset names with their one-line looks before building anything.
2. **Read the reference** for that template, and load its JSON. Take values from the JSON; do not re-guess them.
3. **Build it** the way the reference's "Build it" section says, starting from the named HyperFrames blocks or varg components where it names them. Drive every value from timeline time so any frame renders the same on a re-render.
4. **Fit it to the brand:** swap in the person's colors and fonts only where the reference allows, then re-check contrast and safe zones with the numbers in "Timing and numbers".
5. **Check a draft:** render stills at the key moments (entrance, hold, exit), go through "Mistakes that look amateur", and fix before the final render.


## Rules that hold for every template

1. Rebuild the UI as HTML, don't screen-record: clean surface, deterministic timing.
2. Hold readable UI text clamp(0.6 + chars/15, 1.0, 6.0) s (238 wpm reading, 20 cps subtitle cap).
3. Typing 12–20 cps with seeded uneven gaps (33–200 ms, longer at spaces and before flags); 30 cps for long commands; agent/system text streams 40–80 cps in word bursts.
4. After a command hold 3 s (short output) / 5 s (long); terminal demos under 30 s; speed up long output instead of cutting.
5. Entrances ease-out, <300 ms for UI parts, transform + opacity only, from scale ≥0.93 (chat bubbles 0.75 from the sender's corner), never from 0.
6. Camera moves ~1 s before the action; zoom clamped to UI bounds; settle before text must be read.
7. Desktop UIs drawn at 1.25–1.5x; readable text ≥2.2% of frame height (terminal/code 2.6–3.3%); show only the window.
8. Theme colors from MIT theme sources; never mix palettes (Dracula, GitHub Dark/Dimmed, One Dark, VS Code 2026).
9. OFL stand-ins: Inter for SF Pro, Lato for Slack, JetBrains Mono for SF Mono, VT323 for retro.
10. No platform logos; invented people and workspaces; no invented quotes as real.

## Built from

Charm VHS source + practice guide; Emil Kowalski (@emilkowalski); Adam Pietrasiak (@pie6k, Screen Studio); Netflix Timed Text + Brysbaert; VS Code/Primer/Dracula/One Dark theme sources; Apple HIG; Samuel Kraft; Thorsten Ball ("How to Demo"); David Sheldon-Hicks (Territory Studio).

Every rule in the references cites its source by number. The full list, with links and what was taken from each, is in [`references/sources.md`](references/sources.md). Values marked as house defaults in a reference are our own starting points where no expert published a number.

## Related skills

- [varg-video-edit-library](../varg-video-edit-library/): UI walkthroughs, cursors, device mockups, code and terminal edits.
- `varg-imessage-video` (code2video-templates): a ready iMessage renderer.
- HyperFrames registry (`npx hyperframes catalog --query "…"`): about 450 ready-made blocks; the references name the ones to start from.
