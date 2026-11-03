# Board patterns

Seven layouts we built for real review rounds, what each is for, and what the reviewers actually used on them.
`templates/board.html` covers patterns 1 and 2 out of the box (grid and list view); the others are sections you
add to a copy of it, or small pages of their own in the same style.

## What reviewers actually used

From the review rounds behind this skill:

- **Numbers and timecodes.** Notes came back as "D1 and D2 should be one scene", "remove F3", "at 0:23 show the
  hero a little longer", "0:29 the helmet glitch, regenerate", "0:31 artifact" plus a screenshot. Put the ID
  and the time range on every frame, large.
- **A status and a note per frame.** "Needs fix" plus a short note was the most used control. Approve and
  reject are mostly implicit; make them one click anyway so the summary counts are right.
- **The references per shot.** A reviewer read the ref list and asked "does image3 even appear in these
  scenes?", which caught a reference that would have dragged an off-screen character in. Show the anchors each
  frame was made from.
- **Copy buttons.** Identity blocks, look lines and prompts were copied out of boards and reused. Long prompts
  stay collapsed behind a Copy button; nobody read them inline.
- **The overview strip.** The row of all frames at the top ("the film in six frames") is where the first
  reaction comes from: story order, variety of shot sizes, whether the look holds.
- **Before/after pairs.** On a look-fix board, pairs of the same shot before and after the new rules convinced
  faster than any paragraph.
- **HTML, not chat.** The requests were for HTML pages and artifacts with everything on one page, and an
  approval page at the end of a task. A board is a page the reviewer opens, scrolls and answers; a chat message
  of image links is not.
- **Fewer options.** When a board offered too many directions at once, the reviewer asked to cut it down to
  the most important ones. Two or three options per open question; one still per settled shot.
- **Nothing lost on a rebuild.** When a board was restructured, the reviewer asked for the earlier research
  and data to be put back below the new content. Move old sections down; do not drop them.
- **English for prompts and sheets** (asked mid-project). The board's own words can follow the reviewer's
  language.

Delivery: a local HTML file opened with `open board.html`, or, when your Claude can publish pages (claude.ai
artifacts), a private link. The template keeps notes in the viewer's browser and exports them with Copy
feedback; a published artifact with a shared database can sync notes between reviewers instead.

## 1. Contact-sheet storyboard (default)

For: one still per shot, approve before animation. `templates/board.html` in grid view.

- Header: project, round, date, frame count, aspect, length, stills and credits so far.
- Strip of all frames with a status dot each.
- Look panel (look line with Copy, palette swatches) and anchor cards.
- Frames in film order: number, title, time, act, still or variants, shot spec, action line, refs, QA note,
  prompt, status, note.
- Copy feedback → Markdown with counts, one line per frame, notes indented, overall notes.

## 2. Shot log with music (list view + audio)

For: music videos and anything cut to a beat, where the reviewer judges stills against the track.

- Set `"audio": "bgm.mp3"` in the board JSON and give every frame `start` and `end` in seconds.
- Use `?view=list`: one row per shot, still on the left, log on the right.
- The player sits in the sticky bar; "Play from here" on each frame jumps the track there; the frame under the
  playhead is outlined while it plays.
- Mark which shots are generated and which are drawn in code. On our music-video board each row carried an
  "AI video" or "code" chip, and code-built shots showed a dashed "drawn in code" card instead of a still. Put
  this in `spec.move` or the action line, or use `sketch: "card"` for code shots.
- Lyric or VO line per shot as the action line; the reviewer reads it against the picture.

## 3. Reference board / moodboard

For: locking the look, cast and places before key frames. Sections, top to bottom:

1. **Direction**: four to six short rules, each a bold line plus one sentence ("Quiet, then loud", "Readable
   with the sound off", "Specific, never glossy"). This is what the stills are judged against.
2. **Characters**: each as a frozen card (model sheet) plus its identity block in a copyable box and a "do not
   change between shots" list. Tell the reader: pass these cards as references in every prompt; never
   re-describe the outfit.
3. **Atmosphere and locations**: one master plate per place, ideally the same place in each look it appears in
   (day and night, natural and stylised), with the same objects in the same spots.
4. **Key frames, shot by shot**: time, title, still, the refs it was built from, and a build plan line per shot:
   "video: image-to-video from this still, 5 s, locked camera" or "build: in code, no generation" or
   "composite: plate generated, label tracked on in the edit".
5. **Palette** sampled from the approved frames, with names and hex values and where each colour is allowed.
6. **Type**: the faces for titles and labels, chosen on purpose (no default fonts).
7. **Test of the hardest move**: one short video test of the riskiest camera move, before committing the rest.
8. **Prompt pack**: every prompt with Copy.

Per image card: ID, role ("Shot 4: the reveal, product large, label area blank"), a verdict chip **use** or **fix** with the
reason ("head sits mid-frame; the brief wants it in the upper two thirds"), the refs it was made from, the prompt
in a collapsed block, a full-resolution link, and a Copy URL button. Keep superseded attempts on the board with
a "superseded" tag instead of deleting them; the history explains the choice.

Header line: number of images, credits spent, where the files are.

## 4. Look-fix plan ("why it looks like slop")

For: a rough cut or a board that the reviewer called generic or AI-looking.

1. **Verdict** in two sentences: what is right, what is wrong.
2. **Diagnosis cards**: one card per tell, each named plainly and backed by evidence from the frames, checked
   one frame per second of every clip ("one character cloned three times", "golden hour in every shot", "a
   stock-photo person", "a product render", "default type, no sound", "the same weightless float camera
   everywhere").
3. **Before/after pairs**: the same subject regenerated with the new brief on the same model, labelled "Before ·
   glossy CG" / "After · filmed look". Four pairs are enough and cost under 100 credits on `gpt_image_2_5`.
4. **Grade-only test**: one frame graded (saturation, balance, grain, vignette) next to the original, to show how
   little grading alone fixes.
5. **Rules**: each rule as a card with a tag (Camera, Light, Objects, Places, People, Format, Workflow, Type) and
   one sentence.
6. **Identity and location blocks** with Copy, plus continuity anchors (each appears in at least two shots) and
   an Avoid line.
7. **Rebuild plan**: a table of time, shot, one-line intent and the full prompt with Copy, one main motion per
   shot.
8. **Order of work** and the cost to regenerate, in credits.

## 5. Asset pack (plan without generating)

For: "show me the set of references you will pass and write the prompt; don't generate."

One card per planned generation: the reference images in order with their roles (`@image1` = character sheet,
`@image2` = location master), the prompt, model, duration or size, and the estimated credits from
`estimate_cost`. Nothing is generated until the reviewer approves the pack. This is where wrong references get
caught cheaply; check that every reference is visible in that shot.

## 6. Casting and anchors board

For: a new character, product or place.

- The same character from two image models side by side (a casting test); pick one model for the whole job.
- The model sheet (front, three-quarter, profile, back, face close-up) with the identity block next to it.
- A faces contact sheet: the face crop from every key frame in one row, to compare identity at a glance. We used
  one when a character had to change age across a whole set.
- For products: the real packshot as the sheet; for vehicles and props, a person next to it for scale.

## 7. UI mockup page

For: a product screen, a widget or an app flow mocked up before it is built (not a video).

- Live HTML emulations of the host the UI will live in (a chat app, a dashboard, a phone), not screenshots.
- A host or theme switcher at the top that re-themes every mockup on the page at once, so light and dark and
  each host are checked together.
- One section per user task, each with its mockup and a line on what the user is trying to do.
- Mark sample numbers and balances as examples; use real assets (real previews, real names of real features)
  wherever they exist, so the mockup does not promise things that are not there.
- Build it as its own page or artifact; never edit the production app to show a mockup.
- For a UI that will appear inside a video, use the device templates (`app-ui-mockups`, `imessage-video`,
  `iphone-duo-fold`, `apple-notes-video`) and put their stills on a storyboard board.

## Filling the template from a script

Keep the shot list as `storyboard.json` and regenerate the board from it, so a new round is one command:

```python
import base64, json, pathlib, re, subprocess

TEMPLATE = pathlib.Path("board.html")                 # a copy of templates/board.html
data = json.loads(pathlib.Path("storyboard.json").read_text())   # same shape as the board JSON
pathlib.Path("thumbs").mkdir(exist_ok=True)

for f in data["frames"]:
    for v in f["variants"]:
        src = v.get("file")                           # local full-res still, e.g. stills/03a.png
        if not src:
            continue
        thumb = f"thumbs/{pathlib.Path(src).stem}.jpg"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                        "-vf", "scale=480:-2", "-q:v", "5", thumb], check=True)
        v["img"] = "data:image/jpeg;base64," + base64.b64encode(open(thumb, "rb").read()).decode()

page = TEMPLATE.read_text()
blob = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
page = re.sub(r'(<script type="application/json" id="board-data">)(.*?)(</script>)',
              lambda m: m.group(1) + "\n" + blob + "\n" + m.group(3), page, count=1, flags=re.S)
pathlib.Path("boards").mkdir(exist_ok=True)
pathlib.Path("boards/storyboard.html").write_text(page)
```

Keep full-resolution links in the frame data (a `url` next to each variant, or in the prompt block) so nobody
has to dig for the original file.
