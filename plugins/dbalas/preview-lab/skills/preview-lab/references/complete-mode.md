# Complete mode (beta)

Same flow as visual mode, plus: you review the screens yourself and attach `recommendations` to each item. The user ticks the ones to apply. This is a **visual UX and UI review**: judge what the screenshots show, and use the code only to confirm a value (a color, a size, a token), never to raise issues that cannot be seen.

## How to review

Capture first, review second: `add` the items with their `capture` recipes, look at the shots, then `add` the recommendations as `{ "id", "recommendations" }` per item (see below).

1. **Look at every shot at full size.** Read the PNG files you captured (`<lab>/shots/`), not the thumbnails or your memory of the code.
2. **Compare views of the same item.** Mobile against desktop, light against dark. What breaks, disappears or gets cramped at one size, or turns unreadable in one scheme?
3. **Compare items with each other.** The same component, spacing or wording should look and read the same on every screen of the flow.
4. **Confirm with the code.** Check the real values before you write a number: colors (`pl.mjs contrast <fg> <bg>` gives the WCAG ratio; take colors from the code, since pl cannot sample pixels), font sizes, spacing, tokens versus hard-coded values. One exception to "only what you can see": accessibility gaps of an element that is on screen, confirmed in the code (an input without a label, an image without alt text, an icon button without a name).
5. **Check the last round.** Read the previous round in `<lab>/manifest.json` → `history`. Do not suggest again what the user declined (the feedback lists it as `Declined`), unless the screen got worse.

## What to look for

| type | Look for |
|---|---|
| `ux` | One obvious primary action per screen; clear hierarchy (what to read first); feedback after actions; empty, error and loading states; dead ends; needless steps or fields; destructive actions without confirmation. |
| `ui` | Alignment to a grid; a consistent spacing scale; type scale and line length (45–75 characters for body text); visual weight and balance; density for each viewport; icons consistent in style and size. |
| `a11y` | Text contrast at least 4.5:1 (3:1 for large text and for UI parts such as borders and icons); touch targets at least 24×24 px (44 px on mobile); a visible focus style; meaning that is not carried by color alone; labels on inputs; text that stays readable when zoomed. |
| `responsive` | Overflow, clipping or horizontal scroll; text or buttons that wrap badly; content hidden or reordered at one size; tap targets that become too small; images that crop the subject. |
| `consistency` | The same element styled differently across screens (buttons, cards, headings, empty states); mixed wording for the same action; patterns that differ from the rest of the app. |
| `branding` | Colors, fonts, radii, imagery and tone compared with the brand used for the lab; hard-coded values where a design token exists. |
| `copy` | Unclear labels and buttons ("Submit", "OK"); jargon; inconsistent capitalization; truncated or overflowing text; strings likely to break in longer languages. |
| `perf` | Only symptoms you can see: layout shift, oversized images, blank or skeleton areas in the shot. |

## How to write one

```json
{ "id": "r1", "type": "a11y", "severity": "high",
  "text": "'Apply' button: white on #34d399 is 1.9:1 → use the brand green #047857 (5.5:1).",
  "area": { "x": 62, "y": 40, "w": 30, "h": 6 }, "shot": "mobile" }
```

- **One sentence: element, problem, fix.** `"<element>: <what is wrong, with the measured value> → <the change>"`. The agent that applies it must not need to guess.
- **Measured, not vague.** Give the ratio, the size, the gap or the token.
- **Point at it.** Add `area` (`x, y, w, h` in % of the whole shot image, from its top-left corner; pixel density does not matter) whenever the issue is in one place. It is drawn on the first view, or on the view named by `shot` (its label, for example `"mobile dark"`).
- **Severity.**
  - `high`: blocks a task, fails accessibility (contrast, target size, missing label) or breaks the layout.
  - `medium`: noticeable friction or inconsistency that most users would hit.
  - `low`: polish.
- **0 to 5 per item, most severe first.** If a screen is fine, give it none: an empty list is a good result.
- **Say it once.** An issue repeated on several screens goes on the most representative item (with its `area` there), ending with "Also on: cart, payment".
- **Stay in scope.** Skip backend, performance you cannot see, personal taste with no principle behind it, and anything that contradicts the brand guidelines.

## Example items JSON

```json
{ "mode": "complete", "items": [ { "id": "cart", "title": "Cart", "capture": { "…": "…" },
  "recommendations": [
    { "id": "r1", "type": "a11y", "severity": "high", "text": "Remove (×) icon: 16×16 px target → pad it to 44×44 px on mobile.", "area": { "x": 86, "y": 31, "w": 8, "h": 4 } },
    { "id": "r2", "type": "copy", "severity": "low", "text": "'Proceed' button → 'Go to payment': say where it leads." } ] } ] }
```

Set `"mode": "complete"` at the top level so the lab shows the beta badge. To add recommendations to items that are already in the lab, send only `{ "id", "recommendations" }` for each. `pl.mjs add` rejects malformed ones (unknown type or severity, missing text, duplicate ids, an area outside 0–100) and changes nothing.

## In the lab

- Recommendations are listed under the verdict, most severe first, as cards with a severity stripe, the type and the text. Those with an `area` carry a number (R1, R2…) that matches a dashed marker on the screenshot; hovering one lights up the other. The grid card shows how many there are, in the color of the most severe one.
- The user ticks the ones to apply, or uses **Apply all**. Ticking one sets the item to Changes.
- The feedback lists them as `- Apply rec r1 [a11y/high]: text`, and those left unticked on items marked Changes as `- Declined recs: r2, r3` (an approved item leaves the lab, so its recommendations do not matter). Apply exactly the accepted ones.

## Next round

`pl.mjs round` archives the recommendations with their round and removes them from the items, because they described the old screens. Look at the new shots again and write fresh ones, skipping what was declined.
