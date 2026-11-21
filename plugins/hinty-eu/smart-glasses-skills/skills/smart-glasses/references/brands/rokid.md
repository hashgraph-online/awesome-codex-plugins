# Rokid Glasses (CXR-L SDK through Hi Rokid)

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet).

This is the cross-brand summary. For depth (setup, full code, display JSON, audio, input, troubleshooting) use the
`smart-glasses-rokid` skill in this repository: `npx skills add hinty-eu/smart-glasses-skills --skill smart-glasses-rokid`.

## At a glance
- Display: monochrome green micro-LED waveguides for both eyes, black is transparent. Press: 480x398,
  23 degrees, 1500 nits; Android on the glasses reports a 480x640 portrait display. Design for 480 px of width.
- How your app puts text on it: rung 1 (CXR-L `CUSTOM_VIEW` from your phone app), rung 4 (phone notification mirrored
  by Hi Rokid, Android and iPhone), rung 5 (text-to-speech through the glasses speakers).
- Input: taps on your custom view do not reach the phone (community tests). You get pause, resume, close, wearing and
  screen events. Touchpad gestures need an APK on the glasses.
- Microphone for your app: yes, CXR-L audio stream, PCM 16 kHz mono 16-bit.
- Speaker: yes, the glasses play phone audio over Bluetooth.
- Phones / where your code runs: your Android app (Maven `com.rokid.cxr:client-l:1.1.2`, minSdk 28, ARM only) or iOS
  app (`RGCxrClient` 1.1.1 on CocoaPods trunk, 1.1.1.1 in Rokid's sample project); every call goes through the Hi
  Rokid app, Global (`com.rokid.sprite.global.aiapp`) or China (`com.rokid.sprite.aiapp`) build.
- Publishing to everyone today: yes, as your own app on Google Play or the App Store; the CXR-L docs describe no Rokid
  review, and the user approves you in Hi Rokid (as of 2026-11-08, [SDK overview](https://developerdoc.rokid.com/sdk?lang=zh)).
  Android needs no app key or registration. iOS: the CXR-L page "iOS: SDK import" (v1.2, 2026-09-08, re-read
  2026-11-09) requires a registered Rokid developer account plus bundle ID and URL scheme; one community iOS project
  reports auth worked without registration (unverified).
- Test without hardware: no CXR-L simulator; fake the session. AIUI Studio's web simulator covers AIUI agents only.
- Official agent skill: none for CXR-L. For AIUI agents on the glasses: `npx skills add yodaos-project/aiui`.

Market context: Rokid says Counterpoint ranks it first among AI glasses with a display in H1 2026 with 41% of
shipments (Rokid press release, 2026-09-29); Counterpoint has not published that table itself
([MIXED, 2026-10-03](https://mixed-news.com/en/?p=35020)). Display models were about 4% of all AI glasses shipped in
that half year. Rokid announced Rokid Glasses 2 (480x380, 25 degrees) and the full-colour Rokid Color in China on
2026-10-27; Glasses 2 goes on sale there on 2026-11-11, with no sale date outside China (press:
[Notebookcheck, 2026-10-28](https://www.notebookcheck.net/Rokid-Glasses-2-launch-with-upgraded-design-bigger-battery-and-Dolby-Audio-support.1435436.0.html);
reports expect global versions at CES 2027). CXR-L support for either is unverified.

## Getting text on the display
1. **CXR-L `CUSTOM_VIEW`** (best on Android): authorise in Hi Rokid, create a session with a compact JSON view tree
   (`LinearLayout`, `TextView`, ids inside `props`), `connect(token)`, wait for `onSessionStarted`, then
   `customViewUpdate` with an array of `{"action":"update","id":...,"props":{"text":...}}`. Coalesce to a few
   updates per second. Some Global Hi Rokid builds reportedly ack updates without redrawing; keep a
   recreate-the-session fallback.
2. **Phone notification** (no SDK, works for iPhone apps too): short title and one sentence. Old notifications can
   replay for up to a minute when the glasses go back on (review). Not for live captions.
3. **CXR-L `CUSTOM_APP` + your glasses APK (CXR-S)**: full control and input from the touchpad, much more work.
4. Not phone-driven: apps that run on the glasses ([RealComputer/GlassKit](https://github.com/RealComputer/GlassKit))
   and AIUI agents in the Hi Rokid Agent Store.

## Input
Phone buttons for repeat, skip and hide. `AiInterceptMode.BLOCK_AI` turns the AI key into one `onAiWake()` signal
(experiment). Real gestures only in a glasses-side app.

## Audio
Glasses microphone through CXR-L for the wearer's voice; phone microphone for the other person. Spoken output is
normal phone media audio.

## Testing without hardware
Unit-test the JSON builders and line fitting; run the app against a fake session. x86 emulators cannot load the
SDK's native libraries.

## Publishing and distribution
Your own store listing. Hi Rokid may ask the user to trust an "unverified" app once (community). On iOS, plan for the
Rokid developer account the CXR-L docs ask for until someone confirms it is not needed. CXR-M, which has
Rokid's teleprompter and translation scenes, is business only and cannot run next to Hi Rokid.

## Pitfalls
- Re-authorise after every process start: the Global/China choice is made per process.
- The SDK's R8 rules strip your `Log.d` / `Log.v` in release builds.
- Many blog posts and community doc mirrors describe the old 1.0.x `CxrLink` API.
- Rokid publishes no licence for CXR-L: link to the docs, depend on Maven, never copy SDK files or samples.

## Official resources
- SDK overview: https://developerdoc.rokid.com/sdk?lang=zh
- Maven: https://maven.rokid.com/repository/maven-public/
- Issues: https://github.com/rokid/community/issues
- AIUI: https://github.com/yodaos-project/AIUI
