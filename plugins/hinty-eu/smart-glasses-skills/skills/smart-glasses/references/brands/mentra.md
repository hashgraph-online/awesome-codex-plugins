# MentraOS (Miniapp SDK)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Pointer coverage.

## At a glance
- What it is: an open-source glasses OS and phone app (Apache-2.0, `Mentra-Community/MentraOS`) that drives several
  brands: Even Realities G1 and G2, Vuzix Z100, Mentra Live (camera glasses, no display), plus NIMO in the display
  docs ([quickstart](https://docs.mentraglass.com/app-devs/getting-started/quickstart.md)).
- Display: depends on the glasses. Design for 500x220; G2 is 576x288, NIMO 500x220, G1 640x200 and Z100 640x480 get
  text only ([layouts](https://docs.mentraglass.com/app-devs/core-concepts/display/layouts.md)).
- How your app puts text on it: rung 1, a miniapp that runs inside the Mentra phone app. Rung 4 also works: MentraOS
  mirrors phone notifications with per-app preferences.
- Input: `session.input.onButtonPress` (short, long) and `session.input.onTouch` (single, double, triple tap, long
  press, swipe up and down), depending on the glasses.
- Microphone for your app: yes, `session.mic.onAudioChunk` (PCM or LC3) and `session.mic.onVoiceActivity`, with the
  `MICROPHONE` manifest permission; `session.transcription` for built-in transcription.
- Speaker: the phone or the glasses' audio, depending on the model.
- Phones: Android and iOS (the miniapp's background script runs in the Mentra app).
- Publishing to everyone today: **no**. "There is currently no way to distribute a miniapp built with the Miniapp
  SDK" ([distribution](https://docs.mentraglass.com/app-devs/getting-started/distribution.md), read 2026-11-08). The
  packaged ZIP is for a future store workflow.
- Test without hardware: a miniapp runs without glasses, "the display just won't have anywhere to draw". No
  documented simulator for app developers. The native Bluetooth SDK has a `connectSimulated()`, but it is `internal`
  on Android and not public on iOS (only the React Native module exposes it), and its simulated glasses only log the
  calls; a public, scriptable version is requested in [#4931](https://github.com/Mentra-Community/MentraOS/issues/4931)
  (open, 2026-10-23).
- Official agent skill: none. Official docs MCP server and `llms.txt` exist (below).

## Status (as of 2026-11-08)
- `@mentra/miniapp` 3.3.0 (2026-10-31) is the current SDK, in beta; APIs may change. The old cloud SDK
  (`@mentra/sdk`, `AppServer`, `session.layouts.showTextWall`) is legacy and cloud apps no longer run.
- Install for testing only: the CLI serves a QR code on your local network that the Mentra app scans.
- Mentra Live costs $449 and has no display, so for that model only rung 5 (voice) applies.
- Using an Even G2 through MentraOS means the user pairs the glasses to the Mentra app instead of the Even app, so
  this is an opt-in path for a minority of owners (community reports).

## Getting text on the display
The background script owns the session; `session.display.render()` replaces the whole frame with text, image and rect
elements and reports whether it was displayed or blocked by another app:

```ts
import { registerMiniapp } from '@mentra/miniapp/background';

registerMiniapp(async (session) => {
  const show = (text: string) =>
    session.display.render([
      { type: 'text', id: 'caption', box: { x: 0, y: 120, w: 500, h: 100 }, text,
        style: { maxLines: 3, overflow: 'ellipsis' } },
    ]);
  // unverified: names follow the current docs, not compiled against 3.3.0
  session.input.onTouch('single_tap', () => show('Tap received'));
  show('Ready');
});
```

The background layer is a bare JS engine (JavaScriptCore on iOS, QuickJS on Android) with `fetch`, a native
`WebSocket`, timers and `localStorage`, but no `window`, DOM or `XMLHttpRequest`, so use plain WebSocket code rather
than libraries that expect a browser
([two-layer architecture](https://docs.mentraglass.com/app-devs/core-concepts/two-layer-architecture.md)).

## Pitfalls
- On G2, double tap may open the native dashboard (from earlier notes, not confirmed on today's docs); prefer single
  tap and swipes for your actions.
- Button events need a `BUTTON` hardware requirement in the miniapp manifest, and glasses may send gesture strings
  other than the documented six, so treat `kind` as an open string.
- The miniapp shares the microphone with the Mentra assistant and cannot suppress it
  ([#3893](https://github.com/Mentra-Community/MentraOS/issues/3893)).
- CLI on Windows: the QR code can point to a WSL or Tailscale address the phone cannot reach, and hot reload may not
  work ([#3889](https://github.com/Mentra-Community/MentraOS/issues/3889),
  [#3888](https://github.com/Mentra-Community/MentraOS/issues/3888)).

## Official resources
- https://docs.mentraglass.com/llms.txt
- Docs MCP for Claude Code: `claude mcp add --transport http mentraos-docs https://docs.mentraglass.com/mcp`
  ([AI IDE integration](https://docs.mentraglass.com/app-devs/getting-started/ai-ide-integration.md))
- https://docs.mentraglass.com/app-devs/core-concepts/input.md
- https://docs.mentraglass.com/app-devs/core-concepts/microphone/audio-chunks.md
- https://www.npmjs.com/package/@mentra/miniapp
- https://github.com/Mentra-Community/MentraOS
