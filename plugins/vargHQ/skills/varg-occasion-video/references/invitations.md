# Invitations and save-the-dates

The second-largest occasion search after birthdays (851 distinct Google and YouTube suggestions, Oct 2026), led by
"ai wedding invitation video", "save the date video" and "invitation video for whatsapp", with a large share from
India (wedding cards, engagement, mehndi and haldi invites). People send them in WhatsApp groups, so the file must
open fast and read on a phone.

## What a good one does

- **A reveal, then the facts.** An envelope opens or a card unfolds, then the names, date, time and place hold on
  screen for at least 3 seconds ([Studio Bressi's Canva envelope tutorial, 20k views](https://www.youtube.com/watch?v=zdVgWzmh9fI)).
- **Large, clean type for the facts.** Names first, then the date, the city and the venue; one RSVP line. Real type
  layers (HyperFrames, Canva, an editor) beat generated paragraphs. GPT Image 2.5 prints a name line and a date line
  reliably when you quote and spell them.
- **15–30 s, 9:16, under 16 MB** so WhatsApp plays it inline; send the full-quality file as a document too.
- **One look:** pop-up paper, a wax-sealed envelope, watercolor florals, a 3D animated venue, a love-story montage.

## Formats

| Format | How | Credits (typical) |
|---|---|---|
| **Pop-up card that unfolds** (rising: a pop-up book prompt drew 157k views and 926 bookmarks in Sep 2026) | open card still with the words → closed card as an edit → `seedance_2_5` first/last frames | ~22 + 23 + 308 (8 s, audio) |
| **Envelope reveal** | sealed envelope still → open card still → first/last frames, or HyperFrames for the type | ~45 + video |
| **3D animated invitation** (the 3D invitation tutorials have 143k views) | a 3D venue or couple still, a slow orbit on `kling_v4` or `wan_3`, type overlaid | ~25 + 80–100 |
| **Love-story save-the-date** | the couple's photos as era stills, 3–4 shots on `seedance_2_5`, end card with the date | ~300 per 8 s shot |
| **Birthday party invite** | the birthday person's photo in the party theme, balloons and confetti, 10 s, details as type | ~22 + 100 |

## Prompt templates

Open card still (`gpt_image_2_5`, 9:16):

```
Top-down, slightly angled photo of an open handmade pop-up {OCCASION} invitation card on {SURFACE} in soft window
light. Rising out of the center fold: layered {PALETTE} cardstock forming {SCENE: a garden arch of paper roses / a
paper castle / a tiered cake}, {SMALL FIGURES} under it, small paper lanterns on threads. Printed in elegant
{COLOR} serif letters on the flat lower page: "{NAMES}" and below it "{DATE} · {CITY}", spelled exactly like that.
Crisp fold lines, visible paper fibers, soft shadows under each layer. Photorealistic, no other text, no logos.
```

Closed card (edit of the open still, `reference_image` = the open card):

```
The same scene, same table, same light, same props, same camera angle, but the card is now CLOSED, lying flat in the
same position. Plain {COLOR} cover with {SMALL EMBOSSED MOTIF}, no words on the cover. Nothing is popping up.
```

Motion (`seedance_2_5`, files = [closed, open], first_last_frames, 8 s):

```
Locked overhead camera, soft window light, real speed, one continuous shot. 0-2s: the closed card rests on the table.
2-5s: the cover swings open along its fold like a book, slowly and smoothly. 5-8s: the paper scene rises out of the
fold layer by layer, lanterns swing gently, and the printed names and date settle into place and stay perfectly
sharp. Sound: soft paper slide, the snap of cardstock unfolding, a gentle music-box chime. No hands, no extra text.
```

## Checks

- Read the last frame letter by letter against the details the person gave you.
- The date format matches the country (12 June 2027 vs June 12, 2027 vs 12.06.2027).
- No real venue logos or brand names; a famous place as a painted backdrop is fine.

## Skills that help

- `eachlabs/skills` → `wedding-invitation-generation` (invitations, RSVP cards, e-invites in many styles; Eachlabs key).
- `wyx-sg/wedding-invitation-skill` (a bespoke invitation in any language as HTML, rendered locally; nothing leaves
  the machine).
- `aaronyi97/wedding-video-guided-wizard` (a 14-step guided workflow for a couple's story video).
