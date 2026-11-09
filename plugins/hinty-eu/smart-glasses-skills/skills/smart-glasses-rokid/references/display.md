# Display: custom views, text layout, live updates

Last checked: 2026-11-08. Verification: docs-only. The JSON rules come from the CXR-L 1.1.x docs and Rokid's
`CxrlSample`; sizes and behaviour on the glasses come from press specs and community projects, as marked.
The code below is ours, written for this skill, not compiled here.

## What the display is

| Item | Value | Source |
|---|---|---|
| Panel | dual monochrome green micro-LED with waveguides, one per eye, 1500 nits | press: [Tom's Guide](https://www.tomsguide.com/computing/smart-glasses/rokid-glasses-review), [heise](https://heise.de/-10623624) |
| Resolution | press: 480x398 per eye, 23 degree field of view; retailers also print 480x400 or 480x640 and 30 degrees | conflicting, unverified |
| What Android sees | a 480x640 portrait display at 240 dpi (`wm size` on firmware 1.25, community); GlassKit's emulator profile is `glass_480x640` | community |
| Colour | green only. Black pixels are off, so black is transparent to the wearer | docs + community |
| Orientation | portrait-native; on-glasses apps must lock portrait or they render sideways | community, [fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses) |

Practical reading: design for **480 px (320 dp) of width**, keep content centred vertically, and do not count on
the full 640 px height being visible until you have looked through a real pair. The press figure of 398 visible
rows suggests the top and bottom are cut.

The successor Rokid Glasses 2 (announced in China on 2026-10-27, on sale there from 2026-11-11, press) lists 480x380
and 25 degrees. Same width, so layouts that fit the
first model should fit; untested.

## Custom view JSON

A `CUSTOM_VIEW` session shows one view tree that you pass as `SessionConfig.viewData` and then change with
`CxrSession.customViewUpdate(json)`.

Node shape: `{"type": <type>, "props": {...}, "children": [...]}`.

- Types: `LinearLayout`, `RelativeLayout`, `TextView`, `ImageView`.
- `id` lives **inside** `props` and must be unique. Rokid's sample validates ids against `[a-zA-Z0-9_]+`.
- Props listed in the 1.1 docs: `layout_width`, `layout_height` (`match_parent`, `wrap_content`, a number or
  `"NNdp"`), `id`, `orientation`, `gravity`, `padding`, `paddingTop`, `paddingBottom`, `backgroundColor`
  (`#AARRGGBB`), `marginBottom`, `marginStart`, `layout_alignParentStart`, `layout_centerVertical`,
  `layout_toEndOf`, `text`, `textSize` (`"NNsp"`), `textColor` (`#AARRGGBB`), `textStyle`
  (`normal`, `bold`, `italic`, `bold_italic`), and for `ImageView` `name`, `width`, `height`.
- The docs flag other keys (`marginTop`, `layout_above`, `layout_below`, `scaleType`) as "verify on a real device".
  Community projects used `marginTop` and `paddingStart`/`paddingEnd` successfully.
- **Send compact single-line JSON.** A comment in Rokid's sample says multi-line indented JSON makes the view fail
  silently. `org.json.JSONObject.toString()` is compact.
- Build JSON with a JSON library, not string concatenation, so quotes and newlines in user text are escaped.
- The docs recommend `textSize` of 16 or more.

Updates: a JSON **array** of `{"action":"update","id":"<id>","props":{...}}`. Only the props you send change;
items apply in order. Clearing is an update with `"text":""`.

## A two-line text card

Title small and dim, body large and bright. Everything else is black, which the wearer sees as nothing.

```kotlin
import org.json.JSONArray
import org.json.JSONObject

object TextCard {
    private const val BRIGHT = "#FF00FF00"
    private const val DIM = "#FF00B000"

    private fun text(id: String, value: String, size: String, color: String, bold: Boolean) = JSONObject()
        .put("type", "TextView")
        .put("props", JSONObject()
            .put("id", id)
            .put("layout_width", "match_parent")
            .put("layout_height", "wrap_content")
            .put("gravity", "center")
            .put("text", value)
            .put("textSize", size)
            .put("textColor", color)
            .apply { if (bold) put("textStyle", "bold") })

    /** Initial tree for SessionConfig.viewData. */
    fun view(title: String, body: String): String = JSONObject()
        .put("type", "LinearLayout")
        .put("props", JSONObject()
            .put("id", "root")
            .put("layout_width", "match_parent")
            .put("layout_height", "match_parent")
            .put("orientation", "vertical")
            .put("gravity", "center")
            .put("padding", "16dp")
            .put("backgroundColor", "#FF000000"))
        .put("children", JSONArray()
            .put(text("title", clean(title), "18sp", DIM, bold = false))
            .put(text("body", clean(body), "24sp", BRIGHT, bold = true)))
        .toString()

    /** Incremental update for CxrSession.customViewUpdate. */
    fun update(title: String, body: String): String = JSONArray()
        .put(JSONObject().put("action", "update").put("id", "title").put("props", JSONObject().put("text", clean(title))))
        .put(JSONObject().put("action", "update").put("id", "body").put("props", JSONObject().put("text", clean(body))))
        .toString()

    private fun clean(s: String) = s.replace(Regex("\\s+"), " ").trim().take(240)
}
```

Device-tested layouts in the community, for comparison: a weather app with nine `TextView`s at `30sp` and colour
`#FF40FF5E` ([G0aT-Shen/RokidGlasses-Weather-for-Android](https://github.com/G0aT-Shen/RokidGlasses-Weather-for-Android),
client-l 1.0.4) and a document-scan relay with `34sp` text and three `\n`-joined lines in one `TextView`
([TroroOrosi/rokid-docscan-starter](https://github.com/TroroOrosi/rokid-docscan-starter), Global Hi Rokid).

## How much text fits

None of these numbers was measured on glasses; treat them as starting points and confirm on a device.

- 240 dpi means 1 dp = 1.5 px, so 480 px is 320 dp. With 16 dp padding on each side, 288 dp is left for text.
- Latin text averages roughly half an em per character. At 24sp that is about 22-24 characters per line, at 28sp
  about 18-20, at 18sp about 30.
- For captions, three lines of 24sp body text plus an optional title is a sensible default
  (`lines: 3, cols: 22` in the shared caption protocol).
- Cut text yourself: keep the **last** lines that fit for captions, the **first** lines for answers or hints.
- Scripts: Japanese and other CJK text has been shown on Global units by community projects. Arabic and other
  right-to-left scripts are an open question ([rokid/community #20](https://github.com/rokid/community/issues/20)).
  Emoji: assume they do not render. For other Latin and Cyrillic text, the glasses use Android system fonts;
  check your languages on a device.

## Live updates

- Keep one pending text and send at most a few updates per second; the newest partial result replaces anything not
  yet sent. A 250 ms timer is a reasonable default. An iOS community test reports incremental updates staying smooth
  at about 8 per second ([fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)).
- `customViewUpdate` returns a `SessionResult`. Success means "sent", not "drawn".
- Two Android community projects on Global Hi Rokid report that an update can return success without redrawing
  ([ARDings/RokidAIGlassesUnityBridge](https://github.com/ARDings/RokidAIGlassesUnityBridge) on client-l 1.0.1,
  [TroroOrosi/rokid-docscan-starter](https://github.com/TroroOrosi/rokid-docscan-starter) on Hi Rokid G1.12 and
  G1.13). Another streams text continuously with updates
  ([conclean/RokidGlassesReader](https://github.com/conclean/RokidGlassesReader), client-l 1.0.4). Nothing on the
  phone tells you a redraw failed, so add a remote switch:
  1. `UPDATE` (default): `customViewUpdate`.
  2. `RECREATE`: `close()`, then a new session whose `viewData` already holds the new text. Slower, flickers.
  3. Direct binding with close and reopen, as the DocScan relay does. Undocumented contract; last resort.
- Re-send the latest text in `onSessionStarted` and `onSessionResumed`; updates during `Paused` are rejected.

## Teleprompter-like flows

Hi Rokid has a built-in teleprompter for end users (copy sent from the app, "smart scroll" that follows speech or
constant speed, stop with a double tap; [Rokid FAQ](https://global.rokid.com/pages/faq)). Third-party apps cannot feed
it: the matching teleprompter, translation and AI scenes are CXR-M features (business only). With CXR-L you build it:

- Hold the script on the phone. Show a window of 3-4 lines and move the window, do not send the whole script.
- Advance by time, by phone-side speech recognition of the wearer's voice (the glasses microphone is good for this,
  see [audio.md](audio.md)), or by a button on the phone. Taps on the glasses do not reach a `CUSTOM_VIEW` app.
- Show progress cheaply, for example a dim title line `12/40`.
- If the wearer needs to scroll with the touchpad, that is a `CUSTOM_APP` with your own glasses APK
  ([input.md](input.md)).

## Persistence, screen and brightness

- The view stays until you close the session, the wearer exits it (`onSessionClosed(GLASSES_EXIT)`), or the Rokid
  assistant takes over (`onSessionPaused(AI_ASSIST)`, then `onSessionResumed`).
- Community notes say the glasses turn the screen off after about 20 s by default. Whether an open view or an update
  keeps it on is unverified. Listen to `IGlassesEventListener.onScreenOff` / `onScreenOn`.
- `setGlassBrightness(0..100)` exists; the result only means the command was sent. Leave brightness to the wearer.
- Images: `ImageView` nodes reference icons by `name`; icon data goes in `SessionConfig.viewIconData` (format in the
  CXR-L docs). An iOS community test found the icon side channel timing out
  ([fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)). Prefer text.

## What it cannot show

No video, no free-form drawing, no colour, no per-character styling beyond the `TextView` props. For anything
richer, write an app that runs on the glasses (GlassKit, bare-metal docs) or use `CUSTOM_APP`.
