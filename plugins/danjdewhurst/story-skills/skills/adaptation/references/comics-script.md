# Comics And Graphic Novel Script

A comics script is instructions to an artist and a letterer. It is read by
collaborators, not the public, so clarity beats style. There is no single
industry standard; the full-script format below is widely used and easy to
adapt to an artist's preferences.

## Methods

- **Full script:** the writer specifies every page, panel, caption, and
  balloon. Use it by default.
- **Plot-first ("Marvel method"):** the writer gives a page-by-page plot,
  the artist draws, and the writer scripts dialogue to the finished art.
  Only with an artist who wants it.

## Length

- A single comic issue runs about 20-24 story pages; a graphic novel
  anywhere from about 60 to 200+ pages. Ask the artist or publisher for
  the target.
- A prose novel rarely fits one graphic novel whole. Budget pages per
  chapter before scripting, as with a screenplay scene list.

## Page Plan

Save `adaptations/comics/page-plan.md` first:

```markdown
---
type: page-plan
story: {story-id}
pages: 22
updated: YYYY-MM-DD
---

# Page Plan: {Title}, {Issue or Part}

| Page | Side | Source scene | What happens | Panels | Turn reveal |
|------|------|--------------|--------------|--------|-------------|
| 1 | right | chapter-01-scene-01 | Establish the harbor at night | 4 | - |
| 2 | left | chapter-01-scene-01 | Mara sees the second light | 5 | yes |
```

Page 1 is usually a right-hand page, so even pages are left-hand pages.
The reader sees a left page only after turning, so big reveals go on the
**left (even) page**. A right-hand page ends on the question.

## Script Format

Save as `adaptations/comics/{issue-or-part}.md`:

```markdown
# {Title} #1: "{Issue title}"

## PAGE ONE (4 panels)

**Panel 1.** Wide establishing shot. The harbor wall at night, waves
breaking white. A lantern moves along the top of the wall: MARA, small in
frame.

CAPTION: Every night for eleven years.

**Panel 2.** Close on Mara's hand, gloved, gripping wet stone.

SFX: KSSHH

**Panel 3.** Medium. Mara reaches the top and stands, lantern raised.

MARA: Every single night.

**Panel 4.** Over Mara's shoulder, looking down at black water. Nothing
there. Yet.

## PAGE TWO (5 panels)

**Panel 1.** Same angle as page 1, panel 4. A second light glows on the
water, exactly where her lantern's reflection should be, but her lantern
is behind her.

MARA (small): No.
```

Conventions:

- Page headings in words (PAGE ONE) with the panel count, so the artist
  can see the layout budget at a glance.
- One panel = one moment. A panel cannot show two actions in sequence.
- Describe what the artist must draw: shot, who, where, action, emotion,
  essential props. Leave composition to the artist unless it is plot.
- Balloon labels: `CAPTION`, `CHARACTER`, `CHARACTER (OFF)` for off-panel,
  `CHARACTER (WHISPER)`, `CHARACTER (SMALL)`, `CHARACTER (BURST)` for a
  shout, `CHARACTER (THOUGHT)`, `SFX`. Number balloons if a panel has
  several from one character.
- Put the source scene id in an HTML comment under each page heading
  (`<!-- source: chapter-01-scene-01 -->`), so revisions trace back to
  the book without the artist seeing it in print.

## Pacing

- About 4-6 panels per page is a common average. Fewer, bigger panels
  slow the pace and add weight; more panels speed it up or compress time.
- Splash pages (one panel, whole page) for the biggest moments only.
- Keep words down: roughly 25 words per balloon and around 200 words per
  page are common ceilings before art gets crowded. Cut prose interiority
  to what a caption can carry, or show it.
- Silent panels let the art work; the pause between panels (the gutter)
  is where the reader fills in action.

## Checks

- [ ] Page count matches the target
- [ ] Every panel has one drawable moment
- [ ] Reveals fall on left-hand (even) pages
- [ ] Word counts per balloon and page within the artist's or letterer's
      limits
- [ ] Characters' look and props consistent with the character and
      artifact files
