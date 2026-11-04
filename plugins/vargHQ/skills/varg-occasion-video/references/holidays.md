# Holiday and festival greetings

Creators post 1–3 weeks before the day and greetings land on the day itself (X, Oct 2026). Make the greeting early
enough to fix it, and send it on the day.

| Occasion | Next date | What worked last time (X) |
|---|---|---|
| Diwali | 2026-11-08 | Gemini portrait prompt lists (Oct 11–17, 2025); an animated "city of lamps" greeting with a plain end card (38.6k views, 1,744 likes, 280 reposts) |
| Thanksgiving (US) | 2026-11-26 | Weak on X; family-table greetings |
| Christmas | 2026-12-25 | Card and snow-globe prompts peak Dec 4–10 (about 300 bookmarks each); an agent-built app that turns a selfie into a 3D folding card (250k views, 1,245 bookmarks, Dec 25); studio portraits in red scarves (224k views, 796 bookmarks) |
| New Year | 2027-01-01 | "2026" walk-in posters from a selfie, gold-confetti portraits, a violinist on a rooftop above Earth (63.6k views), greetings Dec 31–Jan 1 |
| Lunar New Year | 2027-02-06 | A film director's Seedance short (574k views, 1,273 bookmarks); red-envelope covers |
| Valentine's | 2027-02-14 | Image prompts: selfie sculptures, photo-booth strips (184–361 bookmarks) |
| Eid | about 2027-03-09 (moon) | Doodle-scrapbook selfies (20.4k views, 205 bookmarks); no qualifying video found |
| Halloween | 2027-10-31 | Mostly paid creator-program posts; organic: a costume reveal from your own walk |

## Formats

- **Animated card from a still:** an illustrated card (ink and watercolor, holly border, the greeting hand-lettered)
  or a 3D/clay scene, then a 5–8 s gentle motion (snow falling, lights twinkling, a slow push-in) on `kling_v4` or
  `wan_3`. Cheapest and the most forwarded.
- **Snow-globe keepsake:** the family, a couple or their house as tiny figures inside a globe, snow swirling; a
  still on `gpt_image_2_5`, then a shake-and-settle clip.
- **Lamp-lit story greeting (Diwali, Lunar New Year, Eid):** four to six painted tableaux in warm gold against deep
  blue, a slow procession, a plain end card with the wish. Two 15 s generations on `seedance_2_5`.
- **Family portrait greeting:** the family's photo restyled as a cozy 1990s holiday-film still or a diya-lit
  portrait, then animated (a laugh, a glance, sparklers).
- **A card for every holiday from one portrait:** the agent-built card app (an image model for the cover and the
  inside, Three.js for the fold) is the most bookmarked holiday build of last season; HyperFrames renders the fold
  as a video.

## Prompt templates

Illustrated card still (`gpt_image_2_5`, 5:7 or 9:16):

```
A traditional illustrated {HOLIDAY} greeting card of {SUBJECT}: ink line drawing with soft watercolor and gouache
washes on cream card stock, {BORDER: holly and pine / marigold garland / red paper-cut clouds}, {SCENE DETAILS},
warm muted colors, the hand-lettered greeting "{GREETING}" set into the top of the design, spelled exactly like that.
Classic card layout. Avoid: photorealistic faces, glossy 3D, neon colors, clip-art clutter.
```

Lamp-lit festival greeting (`seedance_2_5`, two 15 s parts plus a 3 s end card):

```
Format: 16:9 (9:16 for messaging), 30 s. Illustrated {FESTIVAL} greeting in a warm painted-animation style,
reverent and calm. References: @image1 = style frame (gold lamplight, deep blue night, painted texture), look only.
Gen 1 (0-15 s): {TABLEAU 1}, {TABLEAU 2}, {TABLEAU 3}, slow drifting camera, lamps lighting one by one.
Gen 2 (15-30 s): {TABLEAU 4}, {TABLEAU 5}, the family together in the warm light.
End card (type, not generated): "{GREETING}, from {SENDER}". Sound: soft {INSTRUMENT}, distant celebration.
No deities, no text in the generated frames.
```

## Care

- Religious imagery draws criticism from traditionalists; one Diwali maker wrote that she was afraid to post. Default
  to lamps, food, lights, flowers and family, and add a story version only when the family asks.
- Brand holiday ads made with AI drew backlash two Decembers running (McDonald's Netherlands pulled its AI
  Christmas ad after about three days in Dec 2025). A family greeting is safe; a brand greeting needs a person in
  the loop and an AI label.
- Never a real brand's holiday truck, bottle or character.
