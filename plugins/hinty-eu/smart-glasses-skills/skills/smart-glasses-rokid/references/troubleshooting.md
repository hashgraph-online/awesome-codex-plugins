# Troubleshooting

Last checked: 2026-11-08. Verification: docs-only. Each entry says where it comes from. "Our reading" means we
inspected the published 1.1.2 artifact; nothing here was reproduced on hardware.

Log tags worth capturing while debugging (`adb logcat -s ...`): your own tag, `CxrSessionV1_1`,
`CxrSessionManagerV1_1`, `CXRLink`, `AuthorizationHelper` (tag names from our notes on the 1.1.2 binary).
Do not ship or post full logcat dumps: debug builds of the SDK log the auth token.

## Authorisation and connection

| Symptom | Likely cause | Fix |
|---|---|---|
| `requestAuthorization` never calls back | no compatible Hi Rokid installed; the SDK swallows the failed activity start (our reading) | call `checkRokidAppCompatibility()` first; add your own timeout and show "install or update Hi Rokid" |
| Auth fails with `NOT_AUTHENTICATED` | the user is not signed in to Hi Rokid | ask the user to open Hi Rokid and sign in |
| Auth fails with `OPERATION_CANCELLED` | the user declined, or dismissed the "unverified app" confirmation ([ARDings bridge](https://github.com/ARDings/RokidAIGlassesUnityBridge)) | explain the prompt in onboarding, retry on a button press |
| Consent screen shows but the result never reaches your code | `onActivityResult` not forwarded to `parseAuthorizationResult` | forward every activity result while authorising (Rokid's sample does) |
| Worked yesterday, `connect` fails after the app restarted | token stored but the Global/China choice is per process | call `requestAuthorization` again (silent) before `connect` |
| `onConnectResult(false, BT_NOT_CONNECTED)` or `LINK_NOT_READY` | glasses paired in Android settings but not connected in Hi Rokid | open Hi Rokid, connect the glasses there |
| `create()` throws `IllegalStateException` | a previous session is still alive | `close()` the old session and wait for `onSessionClosed` before creating a new one |
| `create()` throws `UnsatisfiedLinkError` | x86 or x86_64 device or emulator; native libs are ARM only | test on an ARM phone; gate the feature on `Build.SUPPORTED_ABIS` |
| Release build crashes in the SDK, debug works | R8 renamed classes used from native code | add the keep rules in [setup.md](setup.md#r8-and-logging) |
| Your release logs are empty | the SDK's consumer rules strip `Log.d` and `Log.v` app-wide | log with `Log.i` |
| Stuck "connecting" on Global Hi Rokid with a community wrapper | Hi Rokid G1.12+ rejects the bind without the `auth_package` extra ([claude-mobile-hud #4](https://github.com/TakanariShimbo/claude-mobile-hud/issues/4), [CxrGlobal #1](https://github.com/TakanariShimbo/CxrGlobal/issues/1)) | use the official client-l 1.1.2 (it sends the extra), or the Anezium fork |
| Both Hi Rokid builds on one phone, the wrong one is used | the SDK prefers a compatible China build (our reading) | uninstall the unused build, or bind explicitly as described in setup.md |
| First `CUSTOM_VIEW` session times out with `LINK_TIMEOUT` | bug in client-l 1.1.0 and 1.1.1 (fixed in 1.1.2, Rokid changelog) | upgrade to 1.1.2 |
| Link drops after a while in the background | the phone killed Hi Rokid or your app (Rokid docs: check that the AI App is still running) | ask the user to exempt both apps from battery optimisation; run your app as a foreground service while active |
| iOS: authorised before, `.notAuthenticated` after relaunch | stored auth is not restored ([rokid/community #19](https://github.com/rokid/community/issues/19), open) | run `authenticate` on every launch; it is silent for an approved app |
| iOS: `Unable to resolve module dependency: 'RGCoreKit'` | built the `.xcodeproj` or a simulator target ([fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)) | build the `.xcworkspace` for a device |

## Display

| Symptom | Likely cause | Fix |
|---|---|---|
| Session starts, nothing visible | multi-line JSON, missing `type` or `props.id`, or dark text on black | send compact JSON with `org.json`; black background, bright green text |
| `customViewUpdate` returns success, glasses keep the old text | reported on some Global Hi Rokid builds ([ARDings bridge](https://github.com/ARDings/RokidAIGlassesUnityBridge), [DocScan relay](https://github.com/TroroOrosi/rokid-docscan-starter)) | switch to recreating the session with the new `viewData`; see [display.md](display.md#live-updates) |
| Update fails with `SESSION_PAUSED` | the Rokid assistant is in front | keep the text, re-send in `onSessionResumed` |
| Update fails with `SESSION_NOT_STARTED` | called before `onSessionStarted` | queue the text, send it on start |
| View disappears and the session closes with `GLASSES_EXIT` | the wearer left your view | stop, show state on the phone, reopen on a user action |
| Text cut off at the top or bottom | visible area smaller than the 480x640 Android display | centre content vertically, fewer lines |
| Text broken by quotes or newlines | JSON built with string concatenation (the official sample's helper does not escape quotes) | build JSON with a library |
| Arabic or Hebrew text looks wrong | RTL support unknown ([rokid/community #20](https://github.com/rokid/community/issues/20)) | test; fall back to the phone for RTL languages |
| Screen goes dark after about 20 s | default screen-off timeout (community notes) | listen to `onScreenOff`; whether updates wake it is unverified |

## Microphone

| Symptom | Likely cause | Fix |
|---|---|---|
| `startAudioStream()` fails | `MICROPHONE` scope not granted, or session not `Started` | authorise with `GlassPermission.MICROPHONE`; start after `onSessionStarted` |
| Audio stops while the Rokid assistant runs | the session is paused | expected; it resumes with the session |
| Recording sounds like noise | wrong sample rate or byte order in your pipeline | treat it as 16 kHz mono 16-bit little-endian; save a WAV and listen |
| Stream stops with the phone locked | Hi Rokid or your process paused by the OS (photo callbacks reported to stop after phone sleep, [DocScan relay](https://github.com/TroroOrosi/rokid-docscan-starter)) | foreground service; test the locked-phone case explicitly |

## Glasses-side apps (CUSTOM_APP)

| Symptom | Likely cause | Fix |
|---|---|---|
| APK install from the phone stops working after a glasses update | firmware change ([Rokid-APKs #2](https://github.com/Anezium/Rokid-APKs/issues/2), YodaOS 1.19.009) | log firmware and Hi Rokid versions; keep a manual install path |
| Small custom commands go silent after a few minutes | glasses app idle (iOS community test, [fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)) | relaunch or wake the glasses app before sending; do not build critical flows on it |
| Glasses-to-phone messages arrive without payload | reported on iOS in the same test | move return data over HTTPS from the glasses |
| On-glasses app renders sideways | landscape activity | lock `screenOrientation="portrait"` |

## Wrong information you will find

- "The official SDK only works with the Chinese app." True for client-l 1.0.1 and 1.0.2; 1.0.3 and later support
  Global Hi Rokid.
- "minSdk 31" and `CxrLink(context, CXRSessionType.CUSTOMVIEW)`: the 1.0.x API, still in old blog posts and
  community mirrors. 1.1.x uses `CxrSessionManager` and minSdk 28.
- "Use CXR-M for teleprompter text": CXR-M is business only and cannot run next to Hi Rokid on the same phone.
- Community documentation mirrors of the Rokid docs exist; some of their API tables do not match 1.1.2. Prefer
  Rokid's own pages.

## Where to ask

Rokid's public tracker is [github.com/rokid/community/issues](https://github.com/rokid/community/issues) (a few CXR
issues from 2026, no Rokid replies on them as of 2026-11-08). Business and SDK access: `Glasses.BD@rokid.com`.
The community index [Anezium/awesome-rokid](https://github.com/Anezium/awesome-rokid) lists working projects to
compare with.
