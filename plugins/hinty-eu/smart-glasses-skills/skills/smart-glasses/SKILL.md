---
name: smart-glasses
description: Build apps for smart glasses and AI glasses across brands - Even Realities G2 (Even Hub), Meta Ray-Ban Display (Wearables Device Access Toolkit and Web Apps), Rokid Glasses, Vuzix Z100, audio-only glasses such as Ray-Ban Meta and Oakley Meta, USB-C display glasses such as XREAL and VITURE, and standalone Android glasses such as RayNeo X3 Pro, with pointers for Android XR, MentraOS, Brilliant Labs and Snap Spectacles. Use when the user wants to choose which glasses to build for or ship on, show text or a HUD on glasses, fall back when there is no SDK, handle input from taps, rings or touchpads, play speech or hints through glasses speakers, capture audio, test a glasses app without owning the glasses, or check whether a glasses app can be published today. Use it even for quick questions about glasses platforms, because SDKs and store rules change monthly and model memory is often out of date. Not for VR or MR headsets such as Meta Quest or Apple Vision Pro, and not for regular phone UI.
license: Apache-2.0
metadata:
  version: "1.0.1"
  last-updated: "2026-11-09"
---

# Smart glasses apps, across brands

Use this skill as the map. It answers cross-brand questions directly and sends you to the right reference file or to
the vendor's own skill for SDK detail. Facts change monthly in this market: every file carries a "Last checked" date,
and the platform table in `references/platforms.md` gives a source and a confidence tag for every cell.

Nothing in this skill has been tested on real glasses yet. Brand files say how each claim was verified
(`docs-only`, `compiles`, `simulator`). Treat `docs-only` code as a strong starting point, not as proven.

## How to work with this skill

1. **Pin down the target.** If the user has not named the glasses, or named several, read
   [references/choose-target.md](references/choose-target.md) and ask only the questions it lists. If you cannot ask
   (CI, headless runs), state your assumptions and continue. When you recommend glasses, go through each option in
   choose-target.md's "ship this month" list and give one line on why it is in or out.
2. **Read the brand file** for each target in `references/brands/` (table below). It tells you how text gets onto the
   display, what input and audio exist, how to test, and whether you can publish today.
3. **Pick the rung of the display-text ladder** (next section). If the app must work on more than one brand, build
   against one small interface and add one adapter per rung, as in
   [references/display-text-ladder.md](references/display-text-ladder.md).
4. **Design for the screen and the input** with [references/ui-small-screens.md](references/ui-small-screens.md) and
   [references/input.md](references/input.md).
5. **Get audio right before you ship** with [references/audio-routing.md](references/audio-routing.md), especially if
   you capture speech or speak into the user's ear.
6. **Test without hardware** first: [references/testing-without-hardware.md](references/testing-without-hardware.md).
7. **Check publishing** before you promise a launch date: [references/publishing.md](references/publishing.md).
8. When something fails, start from the symptom in [references/troubleshooting.md](references/troubleshooting.md).

## The display-text ladder

Most glasses apps need one thing: put a few lines of text in front of the user. There are five ways, from richest to
most universal. Prefer the highest rung the user's glasses support, and fall back down the ladder at runtime.

| Rung | How | Works with | Trade-off |
|---|---|---|---|
| 1. Vendor SDK | Your phone app or plugin draws on the display through the vendor API | Even G2, Meta Ray-Ban Display, Rokid, Vuzix Z100, Android XR (preview), Brilliant Labs | Full control; each SDK is different and some cannot be published yet |
| 2. Web app on the glasses | A web page runs on the glasses or in their browser and gets text from your server | Meta Ray-Ban Display Web Apps, Chrome on INMO Air3, a browser you sideload on RayNeo X3 Pro (none built in), any second screen | One codebase; needs a server and a network on the glasses |
| 3. USB-C external display | The phone treats the glasses as a second monitor | XREAL, VITURE, RayNeo Air and similar | No vendor SDK; tinted lenses and a cable suit watching, not walking around |
| 4. Mirrored notification | Post a normal phone notification; the companion app shows it on the glasses | Most display glasses (per-brand quirks) | No SDK and no store review; short text, timing you do not control |
| 5. Voice in the ear | Text-to-speech over Bluetooth audio | Every pair with speakers, including Ray-Ban Meta and Oakley Meta | Works on the best-selling glasses; no display at all |

## Brands at a glance

| Glasses | Best rung | Publish to everyone today (2026-11-08) | Read |
|---|---|---|---|
| Even Realities G2 | 1 (Even Hub plugin) | Yes, Even Hub store with manual review | [brands/even-g2.md](references/brands/even-g2.md) |
| Meta Ray-Ban Display | 1 (DAT Display) or 2 (Web App) | No: DAT is limited to Beta channel testers, Web Apps run in Developer Mode | [brands/meta-display.md](references/brands/meta-display.md) |
| Rokid Glasses | 1 (CXR-L from an Android phone) | Yes, through your own store listing | [brands/rokid.md](references/brands/rokid.md) and the `smart-glasses-rokid` skill |
| Vuzix Z100 | 1 (Ultralite SDK, Android and iOS) | Yes, as a normal app; hardware no longer sold, existing owners only | [brands/vuzix-z100.md](references/brands/vuzix-z100.md) and the `smart-glasses-vuzix` skill |
| Ray-Ban Meta, Oakley Meta | 5 (voice), DAT for camera and mic | Audio app yes; DAT Beta testers only | [brands/meta-audio-glasses.md](references/brands/meta-audio-glasses.md) |
| XREAL, VITURE, RayNeo Air | 3 (external display) | Yes | [brands/usb-c-displays.md](references/brands/usb-c-displays.md) |
| RayNeo X3 Pro, INMO Air3 | 2 (Chrome on Air3, a sideloaded browser on RayNeo) or an APK on the glasses | RayNeo by sideload, INMO Air3 through Google Play | [brands/standalone-android-glasses.md](references/brands/standalone-android-glasses.md) |
| Any display glasses without an SDK | 4 (notification) | Yes | [brands/notification-glasses.md](references/brands/notification-glasses.md) |
| Android XR glasses | 1 (projected activity + Glimmer, alpha) | Audio glasses on Google Play; display glasses not on sale yet | [brands/android-xr.md](references/brands/android-xr.md) |
| MentraOS | Miniapp (beta SDK) | No, miniapps cannot be distributed yet | [brands/mentra.md](references/brands/mentra.md) |
| Brilliant Labs Halo, Frame | 1 (Lua over BLE) | Yes, your own host app | [brands/brilliant-labs.md](references/brands/brilliant-labs.md) |
| Snap Specs (Spectacles) | Lens (Lens Studio) | Snap review; no experimental APIs | [brands/snap-spectacles.md](references/brands/snap-spectacles.md) |

The full table with display, input, microphone, phones and testing columns, each cell sourced and dated, is in
[references/platforms.md](references/platforms.md).

## Use the vendor's skill for SDK detail

Some vendors publish their own agent skills. They are better than this skill on their own SDK, so install them when
you go deep on one brand, and keep this skill for cross-brand decisions:

- Even Realities G2: `npx skills add even-realities/everything-evenhub`
- Meta Wearables Device Access Toolkit: `npx skills add meta/meta-wearables-dat-android` and
  `npx skills add meta/meta-wearables-dat-ios`
- Android XR display glasses (Jetpack Compose Glimmer):
  `npx skills add android/skills --skill display-glasses-with-jetpack-compose-glimmer` (and `--skill projected-hardware`).
  skills.sh documents the full-URL form, `npx skills add https://github.com/android/skills --skill <name>` (checked
  2026-11-09); Google's own CLI and plugin commands are in [brands/android-xr.md](references/brands/android-xr.md)
- Rokid and Vuzix have no official skill: use `smart-glasses-rokid` and `smart-glasses-vuzix` from this repository.

## Live captions, translation and hints

If the app turns speech into text on the glasses (subtitles, a translator, a teleprompter that follows the speaker, an
assistant that whispers hints), use the `smart-glasses-live-captions` skill. It covers where to capture audio,
streaming speech-to-text options, fitting partial results to each display, latency and non-Latin scripts.

## Rules that save days

- **Check publishing first.** Some platforms let you build and test but not ship to the public. Read
  [references/publishing.md](references/publishing.md) before you commit to a platform.
- **Assume the phone does the work.** On most glasses your code runs on the phone (or in the companion app) and the
  glasses are a display and a sensor bundle over Bluetooth. Keep heavy work, networking and speech-to-text there.
- **Send less, less often.** Bluetooth links are slow. Send short text, update SDK text in place, and batch updates.
  Notifications are the exception: post a new one per message (see `notification-glasses.md`).
- **Black is transparent.** On see-through displays, black pixels are invisible and white backgrounds glare. Light text
  on black, few lit pixels.
- **Do not trust one source for market facts.** When a fact here matters for a decision (a publishing date, a
  supported country, a price), follow its link and check the date.
