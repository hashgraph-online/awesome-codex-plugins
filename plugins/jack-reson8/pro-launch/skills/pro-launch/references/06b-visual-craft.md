# 06b Visual craft: style frames from real frames, real renders and type

Read this at the start of phase 6, **before** any style preview or UI code. Outputs: `refs/frames/*_sheet.jpg`, `docs/technique-sheets.md`, `docs/style-frames/` (frames + `-vs-ref` comparisons + `pick.jpg`), and `docs/style-frames.md` with a `Picked:` line. `phase_gate.py <proj> ui` fails until all of these exist.

Why this exists: in pro-motion the launch/brand films Jack praised came from one method. The tooling didn't matter. Real frames of named references, a technique sheet per reference, 3 divergent style frames before building, and frames **composited from the app's real renders plus deliberate type**, never code-drawn art. Product UI in pro-launch skipped those steps (memory → one direction → build → self-check), and Jack said pro-launch "做不出这么好看的产品"（转述）. Each step below replaces one of those skips.

## V0 · Read what is already known (2 min, no images)
- Project `CLAUDE.md` red lines. For Tutti: no pop, Y2K, Memphis, vaporwave, Showa, neon doodle sticker collage; faces stay clear; only add, never repaint.
- `~/.claude/style-library/styles.md`: grep families **K (App UI · 苹果克制)** and **L (动效)** plus the project name. Reuse entries; don't re-derive them.
- The product's **latest real renders**: simulator screenshots, template outputs, icon. If there are none, render them first (`xcrun simctl io booted screenshot`, or the app's own export). Every frame below is built from these.
- Output: the header of `docs/technique-sheets.md` lists the red lines checked and the style-library entries reused.

## V0.5 · Register: restraint or stylized (decide before V1, write `Register:` in style-frames.md)
Look at the references the **user** liked (not the ones you like). If they are full-bleed, saturated, type-as-material, real objects cut out over a slab of colour (Lapse, record sleeves, zines), the register is **风格化** and V4's Apple restraint does not apply; use V4s. If they are white stages, one product shot, SF-type hierarchy, the register is **克制** and V4 applies. Mixing them is how the 2026-10-24 Tutti site came out as "paper margins + small photo + captions" = "web 感重": restraint layout dressed in doodle fonts.

## V1 · Real frames, not memory
Pick 6–10 references across media (Apple keynote / "Shot on iPhone" films, award-winning apps, game UI, editorial print, anime OP), plus ≥1 that is **not** a screen product. Then:
```bash
python3 scripts/ref_frames.py "https://www.youtube.com/watch?v=<id>" --name apple-hello      # yt-dlp+ffmpeg → 24 frames; login wall → 4 public ytimg thumbs
python3 scripts/ref_frames.py <behance-cdn-url> <url> ... --name behance-x                  # list CDN urls from an open tab via javascript tool (curl on the page is blocked)
/usr/bin/python3 scripts/appstore_refs.py "App A" --country jp                               # App Store art (existing script)
```
- YouTube now asks yt-dlp to sign in; the script falls back to `i.ytimg.com/vi/<id>/{maxresdefault,hq1,hq2,hq3}.jpg` by itself. 4 real frames beat 24 imagined ones. Don't keep retrying the login.
- **3-second test, then rank.** For each reference, ask the image reader: "can a stranger tell what this product does in 3 seconds, and is the content real output or just a logo?". Rank the references on that. The top ones set the direction axes, so the directions don't come from whichever looked prettiest. In 2026-10, 12 of 17 popular GitHub share images were logo-only and failed. Only Supabase (headline plus real UI) and Firecrawl (input → output) passed, and both shaped the accepted directions. For a product nobody knows yet, comprehension beats brand.
- Bulk-pull real share images of popular repos: GraphQL `repository{usesCustomOpenGraphImage openGraphImageUrl}` for ~30 repos in one query, keeping the custom ones.
- **You don't read the sheets in the main session.** Send a Haiku subagent the paths plus the technique-sheet fields below. It returns text, one line per frame. You read the text.

## V2 · Technique sheet per reference (`docs/technique-sheets.md`)
One block per reference, every field filled (empty = not done):
```
### <ref id> · <work name> (<studio/brand, year>) · sheet: refs/frames/<name>_sheet.jpg
- hero: what single thing owns the screen, and its share of the frame (%)
- type scale: largest vs smallest size (ratio), weights used, alignment
- whitespace: % of frame empty; where the empty space sits
- palette rule: base / ink / the one accent and when it appears
- depth & material: shadow, glass, real reflections, or flat
- real UI moment: lock screen / notification / Dynamic Island / share sheet / none
- motion / transition device (if video): how one screen becomes the next
- signature move: the one thing nobody else does
- borrow: <technique> · refuse: <what counts as copying>
```
Compared with 03's reverse-prompt card, this sheet measures **composition** (hero share, scale ratio, emptiness), which is where "好看" came from. Run `ref_archive.py` cards too; these two don't replace each other.

## V3 · Three divergent style frames (`docs/style-frames.md` + images)
1. Write 3 directions. Each one is `name · paired reference (from V2) · 2–3 borrowed techniques · which real renders it uses`. Rules:
   - If one familiar label ("pop", "flat", "clean SaaS", "glassmorphism") can describe a direction, it isn't new enough. Replace it.
   - **≥1 of the 3 must be product-native**: it turns one of the product's own features into the visual idea (Tutti: "the punched star hole IS the window to the next look"). In the accepted Tutti review, 6 of 9 ideas were tagged 补充 (product-native) and 3 were 果味 (Apple-derived). Tag each direction `[ref-derived]` or `[product-native]`.
   - Map directions to what the product *does*: if every item in a family is a transformation (AI tone → human tone, music → film, link → Markdown), "before → after" is the native structure.
   - **Prove each direction on two opposite cases** before showing it, e.g. a text-only product and a visual one. A direction that works for only one of them can't be a series system.
   - Directions must differ in **structure** (white stage vs full-bleed grid vs dark light-columns), not only in colour.
2. Build each frame with `scripts/style_frame.py frame spec.json`. Start from `assets/style-frame-spec.example.json`, which holds three structurally different frames (white stage, lock screen + notification, dark light-columns), and swap in the project's renders. Use real renders as `image`/`grid`/`pills` layers, type as `text` layers, and system chrome (`island`, `clock`, `notif`) when the screen lives on the lock screen or in notifications. **No code-drawn mascots, icons, illustrations or textures.** If a frame needs art that doesn't exist yet, generate it (07 / Codex) or leave the space empty.
3. Use a different subject or photo per frame. The same person in every frame read as repetitive. Mix full-body, half-body, pet, object and scenery.
4. Compare each frame with its reference. The "where it falls short" lines are burned into the image:
   ```bash
   python3 scripts/style_frame.py compare --ref refs/frames/apple-hello/…jpg --frame docs/style-frames/A.jpg \
     --label "Apple · Hello, MacBook Neo" --short "…" --short "…" --short "…" --out docs/style-frames/A-vs-ref.jpg
   python3 scripts/style_frame.py sheet docs/style-frames/A.jpg B.jpg C.jpg --out docs/style-frames/pick.jpg
   ```
   **Core-gap gate:** if any line is about structure or stylization register ("ref is a full-bleed key visual, ours is a page layout"; "ref's type is image material, ours is captions"), the frame is not shown. Rebuild from the technique sheet first. On 2026-10-24 three Tutti site frames were sent with three core-gap lines each; Jack: "差距也太大了吧，完全不是一个事情".
   `compare` refuses fewer than 3 lines or any N/10 score. Lines are element-level ("ref's hero fills ~55%, our card 38%"; "ref uses one weight, we mix Medium+Heavy").
5. Show Jack a review page (HTML, or open `pick.jpg` + the three `-vs-ref` images in the file pane). Use 2–4 options plus your recommendation, per the taste-question rule. Template H in `assets/templates.md`.
6. Write `Picked: <A|B|C|mix: …>` in `docs/style-frames.md`. **Until that line exists, write no UI code** (gate). A mix ("B's opening + D's transition") counts.

## V4s · Stylized register (Register: 风格化)
- [ ] **One key visual owns ≥90% of the screen**, full-bleed: no paper margins, no cards, no page sections in the first screen.
- [ ] **Type is material**, not captions: set huge, warped/stacked/repeated, behind or around the real subject; the slogan *is* the background.
- [ ] **A real object or person cut out in front** (≥40% height), cropped by an edge; the depth sandwich ground → type → subject → grain is visible.
- [ ] **One saturated ground** per state plus one ink and one glow; colour changes with state, not inside a state.
- [ ] **Grain or print texture over everything**, animated if the page moves.
- [ ] **One action** in the first screen; everything else is a small text link.
- [ ] **Nothing code-drawn** that a designer would have drawn (icons, blobs, mascots, clotheslines, broken-image glyphs). Shapes made by the effect itself (holes, warps, flashes) are fine.

## V4 · Apple-style restraint (Register: 克制; check every frame and every built screen)
Each line came from what made the accepted frames work:
- [ ] **One hero per screen** that takes ≥40% of the frame. Everything else supports it or goes.
- [ ] **Big type scale**: largest:smallest ≥ 4:1 (accepted Tutti frame A: 190pt vs 44pt). At most 2 weights. Short lines like "Hello", "One photo. Twelve of you."
- [ ] **Whitespace ≥ 35%** on stage-type screens. Empty space beats an extra element.
- [ ] **One accent** per screen. The base is near-white `#F5F5F7`, near-black `#0A0A0C`, or one full-bleed brand colour used as a slam.
- [ ] **Real product output is the content**: real renders/screenshots, never placeholders or drawn stand-ins.
- [ ] **A real system moment** where it fits: lock screen, notification, Dynamic Island, share sheet, widget. This is how Apple makes UI feel native in films, and it makes our frame read as "an iPhone app" rather than "a web page".
- [ ] **Subjects vary** across frames and screens; no repeated photo.
- [ ] Words ≤ 12 per frame; the picture carries the meaning.

## V4b · Real-object metaphors (D36): use them widely, but only the kind nobody has to learn
The hanger in Tutti worked (photos you just shot hang on a cord; take one down to use it) and the user asked for the approach everywhere. The "print-bed editor / ink-dab colour picker / press-to-print" were rejected two days earlier. The difference is learnability, so the gate is:
- [ ] **Named without words**: a 15–25-year-old can say what the object is from the drawing alone.
- [ ] **Behaves like the real thing**: every gesture is something the real object affords (hang, take down, slide along, lift). Anything the real object can't do is cut.
- [ ] **One job per object**, and no two objects on one screen compete for the same job (a tab bar stacked on top of a hanger = clutter; pick one).
- [ ] **Still the brand's drawing**: marker lines and cut paper, never 3D skeuomorphic shading.
- [ ] **≤3 kinds of object per screen**; every object has an empty, a full and a failed state.
- [ ] Keep a project table `scene → object → behaviour → sound/haptic → state` and take one row per build step; each built object gets a screenshot plus one line "does it read as the real thing without learning", no score.

## V5 · Hand-off to the build loop (06)
Turn the picked frame into the style bible's tokens (04): colours, type sizes and weights, hero share, corner radius, shadow. Each later `ui-log.md` version compares its **screenshot against both the picked style frame and the original reference** with the same `compare` command, so the build can't drift away from what was picked.

## Pitfalls already paid for
- yt-dlp on YouTube: "Sign in to confirm you're not a bot". Use the ytimg thumbnail fallback (automatic). Vimeo also needs login; look for a YouTube mirror.
- Behance and YouTube pages block curl, but their CDNs (`mir-s3-cdn-cf.behance.net`, `i.ytimg.com`) don't.
- python.org Python on macOS lacks CA certs (`CERTIFICATE_VERIFY_FAILED`), so the scripts download through `curl`.
- The in-app browser asks for permission on every new site. Prefer the shell scripts for frames.
- Simulator renders are small (Tutti templates were 540×720). Scale them up at most ~2× in a frame, or render at @3x first. Blurry content looks cheap at once.
- SF Pro is variable: `set_variation_by_name("Heavy")`. Hiragino Sans GB stops at W6, so a Chinese headline looked thin next to SF Heavy. `style_frame.py` uses Noto Sans SC (OFL, variable 100–900, curl line in its header) when installed. Match the weight across scripts before judging the frame. Check that each language renders and that no glyph shows as tofu.
- On a lock-screen frame the clock covered the subject's eyes (test frame B). Choose a wallpaper or render whose face sits below the top ~35%, or crop it there. Faces stay clear (Tutti red line).
- `pills` and `grid` centre-crop. Template renders with text or borders near the edge came out with clipped fragments (column 4's half word). Choose renders whose subject is centred, or pre-crop them.
- Stills hide motion. When a reference is a video and the transition matters, grab dense frames (8 fps) of that moment rather than judging from the 24-frame sheet.
- Reading images in the main session burns the budget. A Haiku subagent reads them and returns one line per image. Look yourself only at the final pick board, scaled down (`sips -Z 1200`).
