# The laptop shot: a hand with a pen walks through the screens

Beats 2-4 of the reel, about 40 of its 60 seconds: a MacBook on a black-and-white zigzag tablecloth, filmed from above at an angle on a phone; a right hand holds a thick marker (the cap end is a colored band) and points at each number or button as the voice names it. Each shot lasts 1.5-4 s and cuts on the word. A reel has 15-25 of these shots over 6-10 different screens.

## 1. Capture the screens first

Whatever path you take, you need the real screens as images:

| Screen | What must be readable |
|---|---|
| Research / supplier page | Product photo, **product cost**, shipping cost, the demand chart |
| Store product page | Product, **sell price** (and compare-at price), Add to cart |
| Demand / trend chart | A line going up |
| Tool home pages for each step | Logo, headline ("Your #1 dropshipping product research tool") |
| The "generate / import store" dialog | The one-click button |
| The AI ad tool | "Paste your link" box, then the generated videos |
| Instagram profile / reel grid | The product videos, link in bio |
| Order or fulfilment page | "Fulfilled by …", order list |
| Flow graphic | Logos with arrows: TikTok · Instagram · Facebook → Shopify (make it in any slide tool) |

How: browser at 125-150 % zoom so the key numbers are big, light mode, hide bookmarks bar, `Cmd+Shift+4` (Mac) or `Win+Shift+S`, 16:10 crop. Use your real store and real prices: viewers pause on these frames. Don't add fake review counts or fake sales numbers.

## 2. Pick the path

| | Film it for real | Full AI on varg |
|---|---|---|
| Looks | 100 % real; this is how the originals are made | Close to real at phone resolution (tested, below) |
| Needs | Laptop, phone, tripod or a steady hand, a patterned tablecloth, a marker | Only the screenshots |
| Time | ~30 min for all screens | ~5 min of work per shot + 3-5 min render |
| Cost | Free | One desk photo ~22 credits, then ~79 credits per 5 s shot on `kling_v4`; 9 shots per reel → ~730 credits, and the shared screens (landing, settings, ad tool, flow) are reused across reels |
| Breaks when | Moiré and glare on the screen | The pen can briefly blur text it passes over; a hand can go wrong |

Mixed is common: film the laptop shots for real (cheap, real), AI only for the hook and the ending.

### Film it for real

- Phone on a tripod or a gooseneck clamp above the laptop at ~45°, screen filling the upper two-thirds of a 9:16 frame, keyboard visible at the bottom. Same angle for every shot.
- Screen brightness at max, room lights dimmed a bit; tap-and-hold on the screen to lock focus and exposure (AE/AF lock). If you see moiré waves, move the phone slightly back or defocus a hair. If you see rolling bands, film at 30 fps (or 25 fps in 50 Hz countries).
- One take per screen: point at each item for 1-2 s in the order the script names them. Cut on the words in the edit.
- A patterned tablecloth (the zigzag in all the originals) and a real marker make it look like a desk, not a studio.

### Full AI: same desk, same app, pixel for pixel (tested 2026-10-28)

**Rule: never let an image model draw the app's screen.** In the first version of this skill each laptop frame came out of `gpt_image_2_5` from a screenshot. The model redrew the UI every time: the logo, sidebar, fonts and layout changed from shot to shot, and viewers notice. The fix is to put the real screenshot on the screen yourself, and only let the video model add the hand.

**Step A: one desk photo with a green screen (once, reused for every shot and every reel).**

```
Vertical 9:16 iPhone photo looking down at an angle at an open silver MacBook Pro on a table covered
with a black-and-white zigzag patterned tablecloth. The laptop screen is lit and shows a perfectly flat,
uniform, pure chroma-key green (#00FF00) full-screen image, edge to edge inside the display bezel, no
reflections, no glare, no text. The whole screen is visible, upper two-thirds of the frame; the
keyboard and trackpad are visible at the bottom. No hands, no people, no pen. Indoor evening light,
realistic phone photo, slight lens vignette.
```
`gpt_image_2_5`, 9:16, quality high → `plate.png`.

**Step B: real screenshots, one size.** Your real store and tool pages, or the bundled demo app (`assets/demo-app.html`: a research tool, store page, orders, settings, an AI ad tool and the flow graphic in one consistent design; product data from the URL). Same viewport and zoom for all of them:

```bash
node scripts/screenshot.mjs screens/ \
  "product|file://$PWD/assets/demo-app.html?screen=product&name=Heated%20Neck%20Massager&img=https://…/massager.png&cost=9.80&ship=3.90&price=49.99" \
  "store|file://$PWD/assets/demo-app.html?screen=store&name=Heated%20Neck%20Massager&img=…&price=49.99&store=KNEADLY" \
  "home|file://$PWD/assets/demo-app.html?screen=home" …
```
Make the key numbers big: 40+ px at a 1440 px wide page, or they won't read at 720p.

**Step C: put each screenshot on the green screen.**

```bash
node scripts/screen-on-laptop.mjs plate.png frames/ screens/*.png
```
It finds the four corners of the green screen, warps each screenshot onto it in perspective with ffmpeg, keys the green out of the desk photo, and writes `frames/<name>.jpg` at 2x. Every frame has the same desk, the same laptop and the exact same UI.

**Step D: animate. The model only adds the hand.** Image-to-video on `kling_v4`, 5 s, 9:16, 720p, one frame per call:

```
Phone on a tripod above a laptop, camera completely locked, no zoom, no camera movement. The laptop
screen content stays exactly the same and perfectly static the whole time, every word and number
unchanged. A right hand holding a thick black marker pen with a green cap enters from the bottom right
and the pen tip points at <ITEM 1>, pauses, then moves to <ITEM 2>, then <ITEM 3>. Natural relaxed
hand motion, the pen never touches the screen. No text appears, no subtitles.
```

The shots one reel needs (9 clips, 4 of them shared across products):

| Clip | Screen | Pen path |
|---|---|---|
| `productA` | research product page | photo → product cost → sell price |
| `productB` | same page | profit → demand chart → "Generate my store" |
| `store` | store product page | price → Add to cart |
| `orders` | orders | down the "Customer paid" column → Shipped |
| `ads` | AI ad tool results (thumbnails = frames of your hook clips) | thumbnails left to right → headline |
| `home` (shared) | tool landing page | headline → Start for free |
| `settings` (shared) | store launch checklist | free shipping → payments → Launch |
| `adpaste` (shared) | AI ad tool, paste link | input → Generate |
| `flow` (shared) | TikTok · Reels · Shorts → your store | each platform → the arrow → store |

Tested 2026-10-28: 24 such clips on `kling_v4` for four products. In every one the hand entered naturally and the screen stayed pixel-identical; the cuts between screens read as one continuous take on one desk.

**Older notes (frames drawn by `gpt_image_2_5`, 2026-10-27), still true for any image-to-video shot of a screen:**
- **Verbs matter.** "The pen circles the price" made Seedance *draw* a red ink circle on the screen. Use "points at", "hovers over", "moves to", "taps the air in front of".
- Text the pen passes over can blur for a few frames. Keep the pen path next to the key numbers, not across them.

**Seedance 2.5 or Kling 4?** We ran the same first frame and prompt on both (5 s, 720p, 2026-10-27):

| | `seedance_2_5` | `kling_v4` |
|---|---|---|
| Price | 193 credits | 79 credits |
| Screen text | Big numbers sharp, small grey text slightly soft | All text sharp and static |
| Pen path | Followed it | Followed it more exactly: $4.47 → $24.99 → $20.52 → down the chart |
| Camera | Eased back a little | Steadier |
| Problem | Took a verb like "circles" literally (drew on the screen) | Invented a small extra button in a corner of the screen for 2 s |

Both are usable. Start with `kling_v4` (less than half the price) and switch to `seedance_2_5` for a shot Kling gets wrong. Check the corners of the screen for invented UI.

## 3. Cut it to the voice

One shot per voiceover phrase; cut when the next number or tool name is spoken, not on a fixed beat. `scripts/guide-edl.mjs` does this from the word timings. A 5 s generated shot usually gives two usable cuts (pen on item 1, pen on item 2). Slight zoom-ins (105-110 %) on alternate cuts hide that two cuts came from one clip.
