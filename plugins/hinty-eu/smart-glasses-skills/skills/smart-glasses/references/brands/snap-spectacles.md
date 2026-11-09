# Snap Specs and Spectacles (Lens Studio, Snap OS)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Pointer coverage.

## At a glance
- Display: standalone see-through AR glasses (both eyes). Consumer **Specs** are on pre-order, not shipping yet.
- How your app puts text on it: rung 1, a Lens built in Lens Studio with TypeScript components and a `Text`
  component. A Snap OS browser exists (Snap OS 2.0, with WebXR), but WebSocket support there is not documented.
- Input: hand tracking (`GestureModule.getPinchDownEvent(handType)` or the Spectacles Interaction Kit built on it),
  voice through the ASR module.
- Microphone for your app: yes, through the ASR module, with a permission prompt and a blinking LED when combined with
  internet access (Transparent Permission).
- Speaker: yes.
- Where your code runs: on the glasses (Snap OS). Spectacles Mobile Kit lets a phone app talk to a Lens over BLE
  (documented for Spectacles 2024; not re-checked for Specs).
- Publishing to everyone today: Lenses go through Snap review (2-3 business days, 25 MB limit). Lenses that use
  Experimental APIs cannot be published to a wider audience.
- Test without hardware: Lens Studio Preview panel with Device Type Override = Spectacles (simulates the additive
  display, left, right and centre views, interactive preview).
- Official agent skill: none. Lens Studio has a built-in MCP server for coding agents; community skills below.

## Status (as of 2026-11-08)
- Specs (consumer): "Starting from $2,195.00", "Expected to ship starting Fall 2026", pre-order in the US, UK and
  France ([specs.com](https://www.specs.com/smart-glasses/specs-27)).
- Spectacles (2024) developer kit: its sign-up pages now redirect to specs.com; treat the kit as no longer offered
  (no shutdown notice found).
- Lens Studio 5.24.1 (2026-10-07) targets Specs, "and not Spectacles (2024)"; use 5.15.4 for Spectacles (2024)
  ([download](https://ar.snap.com/download)).

## Getting text on the display
Open a socket from a script component and write into a `Text` component. Use `wss://` or `https://`: plain `ws://`
and `http://` need Experimental APIs and such Lenses cannot be published
([WebSocket](https://developers.snap.com/spectacles/about-spectacles-features/apis/web-socket)).

```ts
@component
export class CaptionLens extends BaseScriptComponent {
  @input internetModule: InternetModule;
  @input caption: Text;

  onAwake() {
    // unverified: written from the docs, not built in Lens Studio
    const ws = this.internetModule.createWebSocket('wss://example.com/ws?room=ABC234');
    ws.onmessage = (e) => {
      if (typeof e.data !== 'string') return;
      const m = JSON.parse(e.data);
      if (m.type === 'caption') this.caption.text = m.text;
      else if (m.type === 'clear') this.caption.text = '';
    };
  }
}
```

Black is transparent on the display. Pin text to the view (head-locked) for captions and keep it short.

## Pitfalls
- Internet access plus microphone or camera in one Lens is allowed only through Transparent Permission (prompt plus
  LED); "Extended Permissions" in the Spectacles app skips prompts for trusted developers only
  ([Transparent Permission](https://developers.snap.com/spectacles/permission-privacy/transparent-permission)).
- `fetch` in Preview returns 404 unless Device Type Override is set to Spectacles.
- localhost does not work on the device; serve over HTTPS (community reports).
- Developer policy: "Functionality should not be locked behind a purchase or paywall"
  ([policy](https://developers.specs.com/developer-policy), effective 2026-06-15). Check this before planning a
  subscription feature.
- Installing a newer Lens Studio can drop support for older hardware; pin the version per device.

## Official resources and community skills
- https://developers.snap.com/spectacles
- https://developers.snap.com/spectacles/about-spectacles-features/apis/internet-access
- https://developers.snap.com/spectacles/permission-privacy/experimental-apis
- https://developers.snap.com/spectacles/get-started/start-building/publishing-lens
- https://developers.snap.com/spectacles/get-started/start-building/preview-panel
- https://developers.snap.com/lens-studio/features/lens-studio-ai/developer-mode (Lens Studio MCP server)
- https://github.com/specs-devs/samples
- Community: https://github.com/rolandsmeenk/LensStudioAgents (AGENTS.md plus 27 skills, last push 2026-03-06,
  no licence file, so read it but do not copy it), https://github.com/zajalist/zajal-skills (MIT, built on the Lens
  Studio MCP, tested with 5.15.4).
