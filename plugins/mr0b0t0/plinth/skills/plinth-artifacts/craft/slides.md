# Craft: decks (type slides)

How to make a deck that presents well. Most of this guide is about Markdown decks, where Plinth
chooses each slide's layout, type sizes and colors from what the slide holds, so what you control
is the story, what goes on each slide and which kind of slide it is. An HTML deck (`deck.json`),
where you lay out every slide yourself, has its own section at the end; the outline, one idea per
slide, numbers and notes apply to both.

## Outline first

- Write every slide title before any slide, in one style: short topic titles ("Market", "Team"), or
  action titles that each make a point ("Asia is our largest market"). Read the titles alone: they
  should tell the story.
- Share the outline (titles only) in your reply as you build. Wait for approval only when the
  request was unclear.
- A title introduces its slide; it is not the punchline. Avoid dramatic or faux-insight titles
  ("The magic moment", "It's not X. It's Y.").

## One idea per slide

- One point per slide; two short slides beat one crowded one. A slide that needs more than about
  six bullets, or a table of more than about eight rows, is two slides.
- Bullets are short phrases, mostly one line each. The explanation goes in the slide's `Note:`,
  which the presenter sees, not on the slide.
- Fit the length to the time: about one slide a minute for a talk.

## A type scale, by heading level

Plinth sets sizes by heading level, so use each level the same way on every slide:

- `#` only for the title slide (and a closing slide), with one or two short lines under it.
- `##` for the title of every other slide.
- `###` for a column's heading (after `|||`) or a group inside a slide. Never `####`.
- Body text and bullets are one size throughout. Bold a word or two for emphasis, never a whole
  bullet.

## Rhythm: vary the kind of slide

A deck has one theme, so vary the kinds of slide on purpose, the way a designed deck varies its
background tones:

- **Open and close** with a title slide: `#` and a line under it.
- **Section slides**, a `##` heading alone on its slide, between the parts of the story. Plinth sets
  them large with the accent bar.
- **One statement slide** (two at most) for the sentence or number you want people to remember: a
  `##` heading alone that is the statement itself ("Churn fell to 2%").
- In between, content slides: a heading with bullets, a heading with an image, two or three columns
  (`|||`) for before and after or options side by side, a table.
- Slides of the same kind are built the same way, so the heading stays in one place as people flip
  through.

## Vertical space

A 16:9 slide is a fixed 1280 by 720 canvas (4:3 is 1024 by 768) and never scrolls. Text that does
not fit shrinks in steps down to 55%, and past that it is cut. Plan so nothing shrinks:

- Under a `##` title a slide holds about ten lines of body text. Columns hold the same number of
  lines in a narrower measure, so their bullets wrap sooner.
- A table holds about eight rows plus its header. Split a longer one, or put it in a doc and link it.
- An image under a heading is shown at most 400 px tall; an image alone on its slide, with or
  without a heading, fills the slide.
- Plinth warns `slide_dense` past 14 lines or 900 characters on a slide: split the slide, or move
  the detail into its notes.

## Contrast and images

- Plinth's themes keep slide text readable; your images must be readable too. Text in a chart or
  diagram image needs 4.5:1 contrast against the image's background (3:1 for large labels and for
  the chart's marks), and labels at least about 24 px at the size the slide shows them.
- With `theme: auto` the deck follows each viewer's light or dark scheme. When your images are drawn
  for one background, set `theme: light` or `theme: dark` to match them, or give each image its own
  background.
- Make images at the slide's size or twice it, never a screenshot of a page with small text.

## Numbers and notes

- Never invent a statistic. Every number on a slide comes from the person or a source you read;
  name the source in a short line on the slide or in its notes.
- Add speaker notes when asked, or when someone else will present. Write them as what the presenter
  will say, in full sentences. Anyone who can open the deck can read the notes, so nothing private
  goes there.

## Changing a deck

- Change only what was asked: the other slides, their order and their wording stay as they are.
  Suggest broader changes in your reply.

## HTML decks (deck.json)

In an HTML deck you are the designer: every slide is a fixed 1920 by 1080 page (1440 by 1080 at
4:3), laid out like a poster, and nothing chooses sizes or colors for you. Think of a consultant's
boardroom deck: clear, in order, readable from the back of the room, each slide making sense alone.

### Commit to a system first

- Say the system before you write slides: one layout per kind of slide (title, section, content,
  image, statement), the palette as a few hex colors (a dark, a light, one accent), and the faces
  in `deck.json` (at most 4 families).
- Pick four or five font sizes and reuse them everywhere. Eyebrow labels at 24 to 28 px in
  capitals with letter spacing and the accent color; headings that make statements; 40 to 48 px
  for agenda-level points; 28 to 32 px for sentences. Nothing under 24 px: if the text only fits
  smaller, there is too much of it.
- A size the person gives in points is twice that in pixels (36 pt is 72 px), as the .pptx reads it.
- Put the shared rules in `deck.css` (the faces, the palette as `:root` variables, one class per
  kind of slide) and keep each slide's own markup small.

### Margins, width and height

- The standard margin is 128 px on every side, which is the section's default padding. Pinned
  boxes start 128 px from an edge unless there is a reason not to.
- Inside the margins the flow is 1664 px wide, too wide for sentences: keep body text in a column
  of about 800 to 1000 px, and display lines to about 1400 px.
- The height inside the margins is 824 px, and a slide never shrinks to fit: what holds too much
  runs off the canvas and is cut, so do the arithmetic. A two-line 96 px heading takes about 210
  px, a gap 48 px, a table row about twice its font size per line of text (about 70 px at 32 px).
  Nine such rows do not fit under that heading: use 24 to 28 px for the table, or split the slide.
- Never give a text box a fixed height smaller than its text; leave the height out.
- A footer (a source line, a logo, a page number) is one pinned 24 px row 64 px above the bottom
  edge, in the same place on every slide that has one; give those slides 160 px of bottom padding
  so the flow stops above it.

### Flow first, pin on purpose

- Most boxes flow: the section is a flex column with a gap, cards are flex rows of equal columns,
  a matrix is one grid so its rows line up. Pin (absolute position) only what flow cannot do: a
  source line on the bottom edge, a badge over a corner, a full-bleed picture behind everything
  (listed first, so the rest paints over it), a box that moves between slides with the magic
  transition.
- Labels over a picture are real text pinned inside a positioned box that holds the image, never
  words drawn inside the image: images do not use the deck's fonts, and the .pptx cannot edit them.
- A chart's bars stand on one baseline: a track of fixed height with the bars bottom-aligned in it,
  one scale for the whole slide, values above and labels below.
- Keep nesting shallow: a plain grouping box costs nothing, but past three levels the slide wants
  splitting. The format allows at most 15 nested boxes, 200 boxes and 24 pinned children of one box
  a slide.

### Compose each slide

- Set the background of every slide on purpose: the dark color to open and close, the light one for
  the content, the accent for the one statement slide people should remember.
- Vary the slides: full-bleed pictures, big numbers (160 to 200 px, with a 28 to 32 px caption),
  quotes, tables, card rows, diagrams. Turn text into structure wherever it can be.
- Slides of one kind are built the same way: the heading at the top margin, at the same height on
  every content slide, so it stays put as people page. Spread a content slide's body down the
  slide (space between its blocks, or a spacer before the last row) rather than centering the
  column, which moves the heading. Center only a slide with no heading over its body (a statement,
  a quote, a closing line).
- A statement slide with open space below it is finished; a content slide whose column stops at
  60% of the height is not.
- Fragments (steps that wait for a click) and animations are for a point that lands in steps, not
  for every slide. The plain rule is the finished look: it is what print, the overview, thumbnails
  and the .pptx show.

### Notes and size

- Speaker notes are one plain-text aside, the last thing in the slide, at most 4,000 characters.
  When the person asks for notes, the notes carry the script in full sentences and the slides carry
  pictures, figures and one-line headlines.
- Keep a deck to about 50 slides. Its weight is its images: name each by its path, and reuse one
  file instead of several crops of it.
- To change one slide, send only that slide's file (and the index when the order changes); the
  rest of the deck stays as it is.
