# Smart Glasses Skills

[![skills.sh](https://skills.sh/b/hinty-eu/smart-glasses-skills)](https://skills.sh/hinty-eu/smart-glasses-skills)
[![CI](https://github.com/hinty-eu/smart-glasses-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/hinty-eu/smart-glasses-skills/actions/workflows/ci.yml)
[![License: Apache-2.0 and CC BY 4.0](https://img.shields.io/badge/license-Apache--2.0%20%2B%20CC%20BY%204.0-blue)](#license)

Agent skills that teach coding agents to build apps for smart glasses from every major brand.

Agent Skills are folders with a `SKILL.md` file (instructions plus optional reference files) that a coding agent loads
when a task matches; the format is defined in the [Agent Skills specification](https://agentskills.io/specification).

```bash
npx skills add hinty-eu/smart-glasses-skills
```

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI and other agents that read Agent Skills.
Plugin installs for each tool are under [Install for other agents](#install-for-other-agents).

![The live-captions example on two targets. Left: the Even Realities G2 official simulator shows the demo captions in green on a 576x288 canvas. Right: the web app in a 600x600 browser window shows the same captions in white with Repeat, Skip and Hide buttons.](docs/images/live-captions.png)

Version 1.0.1, released 2026-11-09. Vendor facts were checked against their sources on 2026-11-08 and 2026-11-09.
Nothing has been tested on real glasses yet, and every file says how it was verified.

## What your agent gets

- Which glasses to build for and what can ship this month, across 12 platforms, with a source and a date for every
  fact.
- The display-text ladder: five ways to put text in front of the wearer (vendor SDK, web app on the glasses, USB-C
  display glasses as an external display, a phone notification the glasses mirror, voice in the ear), and one adapter
  per rung when an app targets several brands.
- Input (taps, rings, touchpads, Neural Band), audio routing, small-screen UI, testing without hardware, publishing
  rules and troubleshooting by symptom.
- Full guides for Rokid Glasses (CXR-L) and Vuzix Z100 (Ultralite SDK), which have no official agent skill.
- Live captions end to end: choosing speech-to-text, turning partial and final results into lines that fit each
  display, a latency budget, and non-Latin scripts.
- A runnable live-captions example with one server and four targets (web, Even Hub, Android, iOS).
- For Even Realities, Meta and Google, which ship their own skills: what matters for cross-brand decisions, and the
  command that installs the vendor's skill.

Not covered: VR and MR headsets such as Meta Quest or Apple Vision Pro, and regular phone UI.

## Why this exists

This market changes monthly, and agents answer from memory. In our evaluation we gave agents 11 realistic developer
requests, once with these skills and once without. Without them, agents:

- recommended Rokid's CXR-M SDK, which is business-only and cannot run next to the Hi Rokid app;
- suggested Even G1 or MentraOS as fallbacks, although G1 is no longer sold and MentraOS cannot distribute apps yet;
- described Meta's toolkit as "camera and audio, display coming later", and missed that publishing to all users is
  not open and that the App Store blocks DAT apps (MFi);
- wrote SDK calls from memory and left the glasses side as a stub;
- mapped Rokid taps to `onKeyDown` in the phone app, although taps on the glasses do not reach phone apps;
- told the developer to "check UTF-8" or "load a custom font" for Arabic on Even G2, although apps cannot ship fonts;
- built a fake SDK plus Playwright for CI instead of using the Even simulator's automation API;
- guessed Meta error codes from their names;
- suggested USB-C display glasses for iPhone without saying they need an iPhone 15 or later with DisplayPort output,
  which rules out iPhone 16e, 17e and Air.

Facts in this list are as of 2026-11-08. The skills hand the agent these facts with their sources and dates, so it
does not have to guess.

## Skills

| Skill | Use it when |
|---|---|
| [`smart-glasses`](skills/smart-glasses/SKILL.md) | Start here: choosing glasses, text on any display, input, audio, testing without hardware, publishing. It routes to the other skills and to vendor skills. |
| [`smart-glasses-live-captions`](skills/smart-glasses-live-captions/SKILL.md) | Captions, translation, a teleprompter or real-time hints on glasses, or captions that lag, flicker or wrap badly. |
| [`smart-glasses-rokid`](skills/smart-glasses-rokid/SKILL.md) | A phone app that puts text on Rokid Glasses or reads their microphone (CXR-L through Hi Rokid). |
| [`smart-glasses-vuzix`](skills/smart-glasses-vuzix/SKILL.md) | Vuzix Z100 or Mentra Mach1 from Android or iOS with the Ultralite SDK, for existing owners (neither is sold any more). |

To install one skill only: `npx skills add hinty-eu/smart-glasses-skills --skill smart-glasses-rokid`.

## Platforms

The full table, with microphone, input, phones and testing columns and a source for every cell, is in
[`skills/smart-glasses/references/platforms.md`](skills/smart-glasses/references/platforms.md). Tags: O official,
S community, P press, ? unverified.

<!-- platforms:start columns=display,text,publish -->
| Glasses | Display | Text from your app | Publish to everyone today | Checked |
|---|---|---|---|---|
| Even Realities G2 | 576x288 per eye, green; text 5 levels, images 16 [O](https://hub.evenrealities.com/docs/build/display) | Even Hub plugin: web app run by the Even phone app [O](https://hub.evenrealities.com/docs/get-started/architecture) | Yes, Even Hub store, manual review, no paid apps yet [O](https://hub.evenrealities.com/docs/reference/faq) | 2026-11-08 |
| Meta Ray-Ban Display + Neural Band | 600x600, full colour, right eye only, ~20 deg FOV [O](https://wearables.developer.meta.com/docs/develop/dat/display-overview/) | DAT Display API from a phone app, or a Web App [O](https://wearables.developer.meta.com/docs/develop/dat/display-overview/) | No: DAT Beta channel testers only; Web Apps via Dev Mode [O](https://github.com/meta/meta-wearables-dat-android/discussions/229) | 2026-11-08 |
| Rokid Glasses | Monochrome green micro-LED, both eyes, ~480 px wide [P](https://www.tomsguide.com/computing/smart-glasses/rokid-glasses-review) | CXR-L custom view from your phone app, or notifications [O](https://developerdoc.rokid.com/sdk?lang=zh) | Yes, your own store listing; no Rokid review in the docs [O](https://developerdoc.rokid.com/sdk?lang=zh) | 2026-11-08 |
| Vuzix Z100 | 640x480, monochrome green, right eye [O](https://support.vuzix.com/docs/display-process) | Ultralite SDK in your phone app, or mirrored notifications [O](https://github.com/Vuzix/ultralite-sdk-android) | App stores yes; hardware discontinued, existing owners only [S](https://extentos.com/docs/ecosystem/platforms/vuzix) | 2026-11-08 |
| Ray-Ban Meta, Oakley Meta, Ray-Ban Meta Audio | None (open-ear speakers, mics; camera except Audio) [O](https://wearables.developer.meta.com/docs/develop/dat/getting-started-toolkit/) | None; voice in the ear (TTS over Bluetooth A2DP) [O](https://wearables.developer.meta.com/docs/develop/dat/microphones-and-speakers/) | Bluetooth audio app: yes; DAT: Beta channel testers only [O](https://github.com/meta/meta-wearables-dat-android/discussions/229) | 2026-11-08 |
| USB-C display glasses (XREAL, VITURE, RayNeo Air) | External monitor over USB-C DP Alt Mode, tinted [O](https://tutorials.xreal.com/docs/glasses/one-series/first-use/connect-device) | Android Presentation, iOS external display scene [O](https://developer.android.com/reference/android/app/Presentation) | Yes, your normal app store listing, no vendor step [O](https://www.rayneo.com/pages/product-compatibilities) | 2026-11-08 |
| Standalone Android glasses (RayNeo X3 Pro, INMO Air3) | X3 Pro 640x480 colour, both eyes; Air3 1080p [O](https://rayneo.gitbook.io/rayneo-devdoc/x-xi-lie/she-ji-gui-fan.md) | Web page in a browser on the glasses, or your APK [O](https://rayneo.gitbook.io/rayneo-devdoc/x-xi-lie/she-bei-jie-shao) | RayNeo: sideload via ADB; Air3: Google Play [O](https://rayneo.gitbook.io/rayneo-devdoc/chang-jian-wen-ti/adb-tiao-shi/adb-zhi-ling.md) | 2026-11-08 |
| Any display glasses via phone notifications (no SDK) | Title plus 1-3 lines for a few seconds, per brand [?](https://support.evenrealities.com/hc/en-us/articles/14274501482639-Notifications) | Post a normal notification; companion app mirrors it [O](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/notifications/behavior) | Yes, no store review; user enables your app per brand [O](https://developer.android.com/develop/xr/jetpack-xr-sdk/glasses/notifications/behavior) | 2026-11-08 |
| Android XR display and audio glasses | Display glasses: none on sale yet [P](https://developer.android.com/develop/xr/devices) | Projected activity + Compose Glimmer (alpha) [O](https://developer.android.com/jetpack/androidx/releases/xr-glimmer) | Audio glasses: Google Play; display: not yet [O](https://developer.android.com/develop/xr/package-and-distribute) | 2026-11-08 |
| MentraOS (Even G1/G2, Vuzix Z100, Mentra Live) | Per glasses; design for 500x220 text [O](https://docs.mentraglass.com/app-devs/core-concepts/display/layouts.md) | Miniapp: session.display.render (beta SDK) [O](https://docs.mentraglass.com/app-devs/core-concepts/display/layouts.md) | No: miniapps cannot be distributed yet [O](https://docs.mentraglass.com/app-devs/getting-started/distribution.md) | 2026-11-08 |
| Brilliant Labs Halo (and Frame) | Halo: colour, 256x256 round area; Frame 640x400 [O](https://docs.brilliant.xyz/llms-full.txt) | Lua sent over BLE from your host app [O](https://docs.brilliant.xyz/llms-full.txt) | Yes, ship your own host app; no store [O](https://docs.brilliant.xyz/llms-full.txt) | 2026-11-08 |
| Snap Specs (Spectacles) | Standalone AR, both eyes; Specs not shipping yet [O](https://www.specs.com/smart-glasses/specs-27) | Lens in Lens Studio 5.24.1 (TypeScript, Text) [O](https://ar.snap.com/download) | Snap review 2-3 days; no Experimental APIs [O](https://developers.snap.com/spectacles/get-started/start-building/publishing-lens) | 2026-11-08 |
<!-- platforms:end -->

## Examples

[`examples/live-captions`](examples/live-captions/) has one small Node server that produces captions and four
targets that show them. All of them speak the same WebSocket protocol, so you can copy only the target you need.

| Target | Folder | Verified | Date |
|---|---|---|---|
| Caption server: demo script, browser microphone, optional streaming speech-to-text | `server/` | ran locally on Node 22 | 2026-11-08 |
| Web app for glasses browsers, Meta Web Apps and second screens | `web-glasses/` | `browser` (headless Chromium) | 2026-11-09 |
| Even Realities G2 plugin (Even Hub) | `even-hub/` | `simulator` (official Even Hub simulator 0.9.5, 15 of 15 checks) | 2026-11-09 |
| Android: Rokid, Vuzix, Meta DAT, USB-C display, notification, voice | `android/` | `compiles` | 2026-11-08 |
| iOS: Vuzix, external display, notification, voice | `ios/` | `compiles` (CI, unsigned) | 2026-11-09 |

Run the demo with Node 20 or later:

```sh
cd examples/live-captions/server && npm install
node server.mjs --demo        # prints a 6-character room code, for example K7MPQ4
```

Then open `http://localhost:8787/?room=K7MPQ4` with your code. The
[example README](examples/live-captions/README.md) covers the protocol and every target.

## How we verify

- Every platform fact lives in [`data/platforms.json`](data/platforms.json) with a source URL, the date it was
  checked and a confidence level (`official`, `community`, `press`, `unverified`). The tables are generated from it,
  and CI fails when they drift.
- Every brand file, skill and example states how it was verified, with a date: `hardware` (ran on the glasses),
  `simulator` (ran in the vendor's simulator), `browser` (ran in a desktop browser), `compiles` (builds, never ran)
  or `docs-only` (written from documentation). Code that uses an API we could not confirm carries an
  `// unverified` comment.
- Nothing has run on real glasses yet (as of 2026-11-09). If you own a pair and ran an example or followed a skill,
  please send a
  [Hardware verification report](https://github.com/hinty-eu/smart-glasses-skills/issues/new?template=hardware-verification.yml)
  with the glasses model and firmware, the phone and companion app versions, what you tested and what happened. That
  is how a fact moves from `docs-only` to `hardware`.
- Vendor documentation and SDK code are described in our own words and linked, never copied. Several vendor licences
  forbid redistribution.
- CI checks skill frontmatter, file limits and style, regenerates the tables, validates the Claude Code plugin,
  installs every skill with `npx skills`, scans for secrets, and builds the Android and iOS examples.

## Evaluation

<!-- results:start -->
We gave a coding agent 11 real developer requests ([evals/](evals/)), with these skills and without, and graded the
answers blind against checklists built from official vendor documentation. Released version (run 2):

| | With the skills | Without |
|---|---|---|
| Average checklist score | **89%** | 39% |
| Answers that pass (70% or more, no critical error) | **10 of 11** | 0 of 11 |
| Critical errors, such as building on a business-only SDK or a store that cannot distribute apps | **0** | 2 |

Run 1, before we fixed the gaps it exposed: 84% vs 38%. Claude Code 2.1.318 with the `sonnet` model, no web access in
either arm, graded by Claude Opus 5.5 on 2026-11-09. Trigger test on 40 prompts: no false triggers on 20 near misses
(Meta Quest, Vision Pro, Wear OS...); 17 of 20 hits after sharpening the descriptions (13 before), the 3 misses went to
Even's own official skill. Method, per-task scores, both runs and raw answers: [evals/RESULTS.md](evals/RESULTS.md).
<!-- results:end -->

## Install for other agents

`npx skills add hinty-eu/smart-glasses-skills` works for every agent below. It asks which agents to install for;
pass `-a <agent>` to choose without the prompt, and `-g` to install for your user instead of the current project.

<details>
<summary>Claude Code</summary>

As a plugin, add the marketplace, then install:

```
/plugin marketplace add hinty-eu/smart-glasses-skills
/plugin install smart-glasses-skills@hinty-eu
```

The same from a terminal: `claude plugin marketplace add hinty-eu/smart-glasses-skills`, then
`claude plugin install smart-glasses-skills@hinty-eu`. The CLI also takes one step:
`claude plugin install smart-glasses-skills --marketplace hinty-eu/smart-glasses-skills`.

Skills only, into `.claude/skills/`:

```bash
npx skills add hinty-eu/smart-glasses-skills -a claude-code
```

</details>

<details>
<summary>Codex</summary>

Skills only, into `.agents/skills/`:

```bash
npx skills add hinty-eu/smart-glasses-skills -a codex
```

As a plugin, add the marketplace, then open `/plugins` in a Codex session, pick the Smart Glasses Skills
marketplace, install `smart-glasses-skills` and start a new session:

```bash
codex plugin marketplace add hinty-eu/smart-glasses-skills
```

</details>

<details>
<summary>Cursor</summary>

Skills only, into `.agents/skills/`:

```bash
npx skills add hinty-eu/smart-glasses-skills -a cursor
```

As a local plugin, clone the repository into `~/.cursor/plugins/local/smart-glasses-skills` and run
**Developer: Reload Window**. Team admins can add it for the whole team under Dashboard > Plugins & MCPs >
Team Marketplaces > Add Marketplace > Import from Repo.

</details>

<details>
<summary>GitHub Copilot</summary>

Skills only, into `.agents/skills/`:

```bash
npx skills add hinty-eu/smart-glasses-skills -a github-copilot
```

As a Copilot CLI plugin:

```bash
copilot plugin marketplace add hinty-eu/smart-glasses-skills
copilot plugin install smart-glasses-skills@hinty-eu
```

</details>

<details>
<summary>Gemini CLI</summary>

As an extension, which loads the skills from `skills/` and `AGENTS.md` as context:

```bash
gemini extensions install https://github.com/hinty-eu/smart-glasses-skills
```

Skills only, into `.agents/skills/`:

```bash
npx skills add hinty-eu/smart-glasses-skills -a gemini-cli
```

</details>

Agents that do not load skills can read [`AGENTS.md`](AGENTS.md), which points to each skill file.

## What these skills do, send and download

The skills are plain Markdown files that your agent reads. They do not run code on install, send data anywhere or
download anything. The examples in `examples/` are small apps you build yourself; each one says what it connects to.

## Related projects

- [even-realities/everything-evenhub](https://github.com/even-realities/everything-evenhub): Even Realities' official skills for Even Hub plugins on G2.
- [meta/meta-wearables-dat-android](https://github.com/meta/meta-wearables-dat-android) and [meta/meta-wearables-dat-ios](https://github.com/meta/meta-wearables-dat-ios): Meta's Device Access Toolkit SDKs with official agent skills.
- [android/skills](https://github.com/android/skills): Google's official Android skills, including Android XR display glasses with Jetpack Compose Glimmer.
- [hkust-spark/xg-glass-sdk](https://github.com/hkust-spark/xg-glass-sdk): one API for camera, microphone, display and audio across several glasses brands.
- [extentos/smart-glasses-ecosystem](https://github.com/extentos/smart-glasses-ecosystem): a sourced, dated capability map of smart-glasses platforms and devices.

## Contributing

Hardware verification reports help most, then corrections with a source. [CONTRIBUTING.md](CONTRIBUTING.md) has the
rules (a source and a date for every fact, your own words, plain hyphens) and the checks to run before a pull
request. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Report security problems as described in
[SECURITY.md](SECURITY.md).

## Who maintains this

Built and maintained by the team behind [Hinty Voice Assistant](https://www.hinty.eu/assistant/smart-glasses).

## License

Code and skills: [Apache-2.0](LICENSE). Data in `data/`: [CC BY 4.0](LICENSE-DATA). Vendor names are used only to
identify products; the project is not affiliated with any vendor. See [TRADEMARKS.md](TRADEMARKS.md).
