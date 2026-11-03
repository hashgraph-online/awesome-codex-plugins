---
name: varg-mockups
description: >-
  Mock up a video before paying for it: one self-contained HTML board (storyboard board, moodboard, reference
  board, look test, plan page, contact sheet) with numbered frames, shot specs, prompts, approve / needs-fix /
  reject and a note per frame, side-by-side variants and feedback copied as Markdown; stills made on varg (Nano
  Banana 2.1, GPT Image 2.5) that do not look like AI slop and stay consistent (character sheets, environment
  master first, same lens and light); device and app UI mockups (iMessage chat, Apple Notes, iPhone fold, phone
  stamp carousel, terminals, code editors). Use for "mock up", "mock up a look", "mockup", "storyboard board",
  "moodboard", "reference board", "look test", "stills for approval", "key frames to approve", "shot board",
  "phone mockup", "app UI mockup", "screen mockup", or stills that look like AI slop or drift between shots.
  Not for final video clips (varg-video-prompting) or 3D camera blocking (threejs-animatic).
license: MIT
metadata:
  author: vargHQ
  version: "1.0.0"
compatibility: >-
  Boards are plain HTML (any browser; Chrome for the headless screenshot check). Stills need the varg MCP
  (https://mcp.varg.ai/mcp) or a VARG_API_KEY. Device templates need Bun or Python 3, ffmpeg and Chrome, and use
  no credits.
---

# varg mockups: approve cheap stills before expensive video

A mockup is anything the reviewer can react to in a minute instead of after a render. In our sessions it was
three things, in this order of how often we used them:

1. **A review board**: one HTML page of numbered stills (storyboard, moodboard, reference board, look test, plan
   page) with a status and a note per frame. Built before any video is generated.
2. **Mockup stills on varg**: look tests, character and location cards, key frames. Cheap images that lock the
   look, the cast and the geography.
3. **Device and UI mockups inside the video**: a phone chat, a typed note, an app in a phone, terminals and
   editors. Rendered locally from templates, no credits.

The board is the core. Stills feed it; device mockups appear on it as stills before they are rendered as video.

## Why stills first

- A 5 s `seedance_2_5` clip at 720p costs about 210 credits. A `nano_banana_2_1` still costs about 6-8 credits
  and a `gpt_image_2_5` high-quality still about 23 (prices: the `varg-ai` skill, `references/models.md`). One
  wasted clip pays for 9-35 stills.
- A board of stills gets a reaction in minutes; an animated cut takes a render to judge and another to change.
  Our reviewers' own rule: to iterate faster, make the still slides first, then lay texture and motion on top.
- Order of work that held up: words and timing (script, beat sheet or music grid) → anchors → stills on a
  board → approval → animate one main motion per shot → one grade over everything → type and graphics last, in
  code.
- Never start a video generation for a shot whose still is not approved. Before any spend, price it
  (`estimate_cost`, or `plan_batch` for many stills) and say the total in credits.

## The board workflow

1. **Shot list.** One row per shot: number, time range, shot size, action, place, who is in it, and why the shot
   exists. Cut shots that have no job: a reviewer removed a whole scene as "not clear why it's needed".
   If the person sent a reference clip or images, stay close to it; "make the storyboard closer to the original"
   was the correction when we drifted.
2. **Anchors first** (see Consistency): character sheet per person, location master per place, product sheet
   per product. Approve these as a small board of their own when the cast or set is new.
3. **Look test.** Before the full set, make 2-4 test frames of the hardest shots, or one frame in two or three
   looks. Pick the image model here (a casting test across two models) and stick to it. When the cheaper model
   kept disappointing, the reviewer asked for the top model (`gpt_image_2_5`) for the hero stills.
4. **Generate one still per shot** from the anchors. Use `plan_batch` for the whole set (prices it, charges
   nothing), then `run_batch` after the go. Make two variants only for shots that are genuinely open; label
   them A and B and show them side by side.
5. **Self-QA every still before anyone sees it** (checklist below). Regenerate or mark "needs fix" with the
   reason yourself. "Still bad, look at s1 s2 s3 yourself: they're different and full of artifacts" is the
   message you want to never receive.
6. **Build the board** from `templates/board.html`: copy it, fill only the JSON block (frames, spec, refs,
   variants with model, credits and prompt, your QA note and suggested status). Embed thumbnails, link full-res
   (see Gotchas for sizes).
7. **Screenshot the board and look at it** before handing it over:
   `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars --screenshot=board.png --window-size=1400,1000 --virtual-time-budget=3000 "file:///abs/path/board.html?theme=light"`
   then read the PNG. Also try `?theme=dark` and `?view=list`. Headless Chrome will not go narrower than 500 px;
   check phone width by loading the board in a 390 px wide iframe.
8. **Hand it over and stop.** Say what is on it, what you already flagged, and what it cost. Wait for the notes.
   Do not animate "while they look".
9. **Apply notes to the noted frames only.** Bump `round`, regenerate just those frames, keep replaced stills in
   a `retired/` folder (never delete paid images), and say which frames changed.
10. **After approval**, animate from the approved stills. If some clips are not back yet, cut an animatic with
    the approved still and a slow push in their place, so the cut always plays end to end.

If the person asks to see the plan without spending ("show me the set of refs you will pass and write the
prompt, don't generate"), make the same board with the planned refs and prompts per shot and no new images.

## What goes on a board

Per frame (the template does all of this):
- A big number and a title (`01: The hook`), the time range, the act.
- The still, or variants side by side with a Pick button and a compare view.
- A shot spec: shot size, lens, camera move, light, place, cast.
- One or two lines of what happens in the frame (the action, not adjectives).
- The anchors it was made from (`ref A1 sheet`, `ref L1 master`). Reviewers check these: "does image3 even
  appear in these scenes?" caught a wrong reference.
- The prompt, collapsed, with a Copy button; the model and its credits.
- Your QA note ("Check: two arms on the handlebar plus a third hand") and a suggested status.
- Status: To review, Approve, Needs fix, Reject. A note box. Both saved in the viewer's browser.

Per page: a strip of all frames at the top (the film in N frames), the look line and palette with a Copy button,
the anchor cards, filters by status, a guides toggle (thirds and an 8% safe area, for checking room for titles),
Copy feedback (Markdown the reviewer pastes back into the chat), Print (a clean three-up contact sheet with
statuses and notes), light and dark themes, phone layout. Optional: an `audio` file gives a player and a "Play
from here" button per frame, which reviewers used to judge stills against the music.

Board rules from the reviews:
- Little text. Specs in a compact grid, prompts collapsed, long reasoning out of the board. Copy buttons
  instead of printed commands.
- Every thumbnail behaves the same way (opens the zoom). No frame that does something different from its
  neighbours.
- IDs and timecodes everywhere: reviewers answer with "D1 and D2 should be one scene", "remove F3", "at 0:23
  show the hero longer", "0:31 artifact" plus a screenshot.
- Prompts and sheets in English (the reviewer asked for this mid-project); the board's own words in the
  reviewer's language.
- One board per round, with the round number in the header. Never mix notes from two rounds.

More layouts (reference board, look-fix plan, asset pack, shot log with music, UI mockup page):
`references/board-patterns.md`.

## Stills that do not look like AI slop

What the reviewers called slop: a character that came out as a generic stock man ("make him a bit younger, he
came out AI slop"), a stretch of shots that did not match each other, glossy renders, and meme packaging. What
fixed it was the brief, not the grade: a grade-only test (lower saturation, cooler balance, grain, vignette)
helped about 10%; changing what we asked for did the rest.

- **Footage someone filmed, not a nice picture.** Name the camera and its operator's flaws: handheld news
  camcorder, phone at arm's length, a disposable camera with on-camera flash, autofocus that breathes, a late
  reframe. "Realistic, 8k, cinematic" says nothing.
- **Kill golden hour.** Pick one physical light for the whole film (overcast after rain, one practical lamp, a
  shop window spill) and repeat it in every prompt. Ban sunset glow, teal-orange, lens flares, fake HDR.
- **Wear on every object.** Scuffs, dust, fingerprints, drips, dents, uneven shine. Pristine reads as a product
  render.
- **One specific, ordinary, lived-in place** with its clutter listed. "Every prop looks unused" is the classic
  complaint. Avoid picture-perfect lawns and showroom interiors.
- **Behaviour, not pose.** Catch people mid-task, not looking at the camera, no posed gestures. A stoic
  character who never reacts carries deadpan well.
- **Distinctive faces.** Describe someone specific: age, asymmetry, one signature detail. Generic "rugged,
  stubble" prompts came out looking like famous actors; re-check every face, and compare faces across shots on
  one contact sheet. Hiding the face (helmet, goggles, hood, back to camera) removes the thing models drift on.
- **One subject per generation when they must differ.** One prompt asking for five different characters in one
  frame returned one design cloned five times. Generate each as its own still, each from its own real-world
  reference, so the silhouettes differ.
- **No text from the model.** Titles, labels, logos, UI and numbers are added in code later. Leave a blank,
  lit surface where a label will go. Models invent brand logos on clothes; fix with an edit pass that says
  "remove only the logos, change nothing else".
- **No meme packaging unless asked.** Huge outlined words and saturated thumbnail colours were rejected as "a
  meme"; a jokey tagline was cut as cringe. A cinematic orange-teal house style was not approved either.
  Premium, quiet, specific.
- **Palette rules that worked:** decide light and dark first, then hue; two or three hue families plus
  neutrals, one saturated spot where the eye should go; natural skin; lifted blacks, soft highlights, light
  grain; a colour script per act. Bake the palette into the stills: the video model kept it and no grade was
  needed.

Prompt templates and filled examples: `references/still-prompts.md`.

## Consistency

- **Anchors before shots.** Character sheet: front, three-quarter, profile and back plus a face close-up, flat
  grey background, no text. Write an identity block once (face, hair, build, every garment, props, behaviour)
  plus a short "do not change between shots" list, and paste it verbatim into every prompt. Point at the card;
  never re-describe the outfit differently later.
- **Environment master first.** For several shots in one place, first make one wide, empty establishing plate
  with the layout written as numbered elements ("1 door on the left wall, 2 window behind the desk, 3 red chair
  in front of the window"). Then each shot: master as the first reference, plus where the camera stands in that
  layout and what it looks toward. Shots generated one by one disagreed on how many people were in the scene
  and where they stood.
- **When even the master drifts, block it in 3D.** An environment image still let both top image models
  re-invent the layout per camera. A three.js blockout in real metres, rendered per camera and passed as the
  first file of an image edit ("keep the camera and geometry exactly; grey blocks are brick walls…") held it.
  Give blockout people a head, arms and legs. See `threejs-animatic` and `varg-previz`.
- **Wide and close of the same moment → one master scene.** Generate the close-up from the master ("same room,
  closer angle"), never from scratch. The reviewer asked for exactly this after adjacent wide and close shots
  disagreed.
- **Continuity anchors.** Pick two or three props or marks that recur (a cracked tile, a crack in the glass, a
  parked bike) and check them in every frame. A reviewer caught a cockpit console that changed between shots; the
  fix was regenerating those shots from the master with the console described item by item.
- **Only the references that are in frame.** A sheet of a character who is off-screen drags them into the shot.
  Crop sheets so you can pass only the column you need.
- **When a sheet is a reference, say "create a new image, not a sheet"**, and give every reference a role:
  "@image1 is the pilot's character sheet: same face, hair and headset."
- **Change a person by editing the existing frame**, not by regenerating it: composition and light stay.
- **Same lens family and one look line** across the set; keep weather and light in each shot's own prompt.
- **After a story rewrite, old stills are stale.** Do not reuse them as references.

Deeper material: `varg-consistent-characters` (cast and location cards, composites approved as stills),
`varg-character-design` (memorable characters), `varg-previz` (`references/character-sheets.md`: anchor table
and the still QA checklist).

## Still QA checklist (before a still goes on the board)

1. Count people: exactly the people the shot names. Count arms and hands: every visible hand belongs to a body
   in frame (we got a stranger's hand, hands over an empty seat, and a third arm).
2. Scale against the sheets: a person next to the vehicle, the product in a hand. One frame had the pilot as
   big as the ship.
3. Identity: right face, right outfit, right product shape and colour; no wrong object swapped in (a different
   vehicle in the background than the one the shot names).
4. Orientation: bodies and objects point the way the story needs relative to the frame and the set.
5. Continuity anchors present and unchanged.
6. No text, letters, logos, watermarks; no letterbox bands or borders.
7. Framing leaves room for titles where the edit needs them (turn on Guides).
8. Aspect ratio and size are what you asked for.

## Device and UI mockups in video

All of these render locally with no credits. Each has a still mode: show the still on the board first, render
the video after the go.

| The person wants | Use | Still first |
|---|---|---|
| A text conversation as an iPhone iMessage screen recording | `imessage-video` | `bun render.ts chat.json --still last` |
| Any text typed live in iPhone Notes | `apple-notes-video` | render a short note first |
| Their app screens on a foldable iPhone, 3D fold | `iphone-duo-fold` | `bun render.ts --screen app.png --still 2.4` |
| Posters or covers swiping in a phone as perforated stamps | `stamp-carousel` | `python3 engine/render.py images --still 31 -o frame.png` |
| Chat thread, team chat, terminal, coding-agent session, code editor, notification, 3D code slab, exploded UI | `app-ui-mockups` | preset preview frame |
| How a catalog, registry or marketplace works | `card-catalog-explainer` | config preview |
| CTA pills, stickers, comment and review cards over footage | `social-overlays` | |
| Lower thirds, title cards, show opens | `title-design` | |

`imessage-video`, `apple-notes-video`, `iphone-duo-fold`, `stamp-carousel` and `card-catalog-explainer` are templates in
[github.com/vargHQ/code2video-templates](https://github.com/vargHQ/code2video-templates), one folder each with its own
`SKILL.md`; clone the repo and the agent picks the template from its `AGENTS.md`.

Rules for device mockups:
- Invented people and conversations only, never real people's messages presented as genuine. Fiction and ads.
- No platform logos. Keep the phone front-facing in demos; a back view can show the maker's logo.
- Screen content is a flat, front-facing image or HTML at the screen's exact aspect: make it in code (HTML)
  when it carries text, or as a still on varg when it is a picture.
- UI text, numbers and labels on screens always come from code, never from an image model.

**UI design mockups as pages** (a product screen or a widget, not a video): build a live HTML emulation of the
host it will run in, with a switcher that re-themes every mockup on the page; mark sample numbers as examples;
use real previews where they exist; build it as a separate page and never edit the real app for a mockup.
Details: `references/board-patterns.md`.

## Gotchas

- **Independent generations add extras.** Each still generated on its own invented things: an extra hand, a
  second orange button, a figure the size of a ship. Anchors and masters fix most of it; the checklist catches
  the rest.
- **Cap retries.** One shot failed three times in a row (an extra button twice, three arms once). After two or
  three failed rerolls, change the approach (edit pass on the best take, a different framing, composite the
  difficult element in code) and flag it on the board instead of burning credits.
- **References are copied, including their mistakes.** A blockout with arms raised behind the head came back
  as a person with arms behind the head; a pose in the reference wins over the prompt. Fix the reference.
- **Orientation phrases.** Models kept laying a figure parallel to a line it was meant to cross. Describe it
  relative to the frame: "vertical in the frame, crossing both lines like a ladder rung", or remove the figure
  and add it back with an edit.
- **Do not describe empty bands.** "Keep the top fifth calm" drew a band. Write "full-bleed, no borders" and
  leave title room with composition ("subject in the lower two thirds").
- **Safety filters reject violent wording** ("screaming", "about to be hit", "teeth bared"). Rephrase as
  tension or slapstick. In our runs refused jobs were not charged; confirm with `get_job_cost`.
- **Check the output aspect ratio of every still.** Some option combinations silently ignored `aspect_ratio`;
  the same request without extra provider options came back right.
- **Reference images at least 300 px on the short side**; pad crops onto a flat background instead of
  upscaling.
- **Board size.** Embed thumbnails as JPEG about 432-640 px wide (`ffmpeg -i in.png -vf scale=480:-2 -q:v 5
  thumb.jpg`, then base64) and link the full-resolution file. A 36-frame board with embedded thumbnails was
  2.7 MB and opened instantly.
- **Downloading varg outputs:** use `curl`. Python's default urllib user agent got 403 from the file host.
- **Do not add what nobody asked for.** Extra opening titles were the first note on one cut ("why did you add
  texts at the start?"). Product and model names shown on screen must be current and real; never invent a
  version number.
- **Listen to every test clip.** A video model returned its own speech-like soundtrack on a clip that was meant
  to be silent. Strip audio you did not ask for (`ffmpeg -i in.mp4 -an -c:v copy out.mp4`).
- **Labels and paths stay in code.** A video model will not hold an exact path or keep a label readable; draw
  callouts, tracked labels and leader lines in HTML over the generated plate.

## Related skills

`varg-video-prompting` (prompting the video step), `threejs-animatic` and `varg-previz` (3D blocking and
camera approval), `varg-consistent-characters`, `varg-character-design`, `varg-ai` (models, prices, MCP and
API), `app-ui-mockups`, `imessage-video`, `apple-notes-video`, `iphone-duo-fold`, `stamp-carousel`,
`title-design`, `social-overlays`.
