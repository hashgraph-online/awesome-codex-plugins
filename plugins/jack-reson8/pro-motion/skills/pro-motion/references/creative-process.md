# How the ideas were found (process, not cases)

Read at step 1 (campaign brain) and at web-craft W0 step 3, before any style frame. Output: `docs/idea-trail.md` in the project with the eight moves below filled in. Cases and modules show *what* worked; this file is *how to get there next time*, for a different product. Every move came from the tutti.pics site (2026-10-24/25), where round 1 was "web 感太重" and round 2 was "非常好了，这回真的很好".

## The eight moves (write each one down; a blank move means the idea isn't ready)
1. **Purpose in one line, in the viewer's terms.** Not "showcase features" but "in 3 seconds she sees an ordinary photo become a great one and thinks 我去还能这样". Every later choice is checked against this line.
2. **Find the product's verb.** What does the product physically *do* in one gesture? Tutti: flash → poster; punch holes; hand over a 6-character code. The verb becomes the page's transition, the film's cut, the share card's reason to exist. A page that describes the product instead of letting the verb happen is a brochure.
3. **Axes before answers.** ≥6 different idea axes; the user's own example fills at most one. Tutti v3: scroll story (user's), effect-as-transition, the code as protagonist, page-is-a-camera, clothesline, visitor-as-protagonist, one-switch-flips-all. Write one representative per axis, then pick.
4. **Steal a mechanism from outside the category, a look from inside the user's taste.** The look came from the reference the user loved (Lapse: layer sandwich). The mechanism came from somewhere unrelated (Shopify's Boring/Not boring switch → one flash flips the whole poster; Kelvin's colour-block cuts → one slab per feature). Never take both from the same source.
5. **Turn every product noun into a page mechanism.** Make a table: noun → what the page lets you *do* with it. Tutti: share code → code page that never 404s + code-only poster (media hijack); template → poster state; failure → fake-broken 404; "new every day" → today's opening look; export → save = share card with the code; waitlist → visible rank, +5 per friend. Nouns with no row are features you are only describing.
6. **Beat the reference on the axis it can't move.** The reference is static art (Lapse = PNGs). Ask: what can a live page do that the reference can't? Finger pushes the type; the product's own action is the transition; the visitor's own photo becomes the subject. That gap is the "我去还能这样".
7. **Fuse to ≤3 interlocking mechanisms**, and say how they lock: v2 = live type wall × flash-to-flip × your photo; each one makes the other two better (your photo is worth flipping through; the flip shows the wall is alive). Everything else becomes a local detail of one section, or is cut.
8. **Derive before you build.** For each kept mechanism write 3 variants by changing one parameter (trigger: tap / scroll / tilt; medium: page / poster / sticker / avatar; who acts: visitor / friend / stranger). The code-only poster came from "code" × "medium = printed poster". Keep the variants list: it is next month's campaign.

## Tests before showing anything
- Remove the logo: is it still recognisably *this* product doing *its* verb?
- Count sentences that describe the product. Each one is a missed demonstration.
- Can a 15-year-old say what to do in 3 seconds without reading? (Jack: "让用户感到容易理解并且有趣"; novelty is allowed, puzzles are not.)
- Is anything drawn in code that a designer would have drawn? Replace with real output or cut.
- Kill list: write what you dropped and why (round 1: paper margins, code-drawn shutter, broken-image glyph); the next session reads it before ideating.

## Where the process lives in the files
`docs/idea-trail.md` (moves 1–8 + kill list) → `technique-sheets.md` (refs decoded) → `style-frames.md` (Register, frames, Core gap, Picked) → code. `web_gate.py --ship` checks the last three; this file is checked by reading `idea-trail.md` at the review.
