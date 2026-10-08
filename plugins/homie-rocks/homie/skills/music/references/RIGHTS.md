# Plans, rights and receipts

## What ElevenLabs allows (read 2026-09-29)

From ElevenLabs' help centre, "Can I publish the content I generate on the platform?":

- **Free plan:** no commercial licence. Nothing made on it may be used commercially (ads, sales,
  monetised channels, a paid game). If it is published at all, it credits ElevenLabs by naming
  "Eleven Music".
- **Paid plans (Starter and up):** a commercial licence is included, except for Beta services,
  provided the person has the rights to what they put in (their lyrics, their references) and
  follows the Terms of Service and the Prohibited Use Policy.

Terms change: when a person is about to publish commercially, read the current page
(https://help.elevenlabs.io/hc/en-us/articles/13313564601361) and say what it says today.

## The plan at render time is what counts

`render` reads the plan before it sends anything and writes it into the render's receipt and
into the manifest entry (`rights.plan`, `rights.commercial`, `rights.attribution`). The song page
shows it in plain words. A render made on the free plan stays under free-plan terms after an
upgrade: to use it commercially, render it again on the paid plan.

## What never goes in

- A real person's name, voice or likeness, or "in the style of" a real artist.
- Lyrics the person does not have the rights to (someone else's song).
- A key, token or password, anywhere in the studio.

## Receipts

Every paid call leaves three records:

- `music/<slug>/budget.json`: the cap the person agreed to, who agreed, and every call with its
  cost;
- `music/receipts.jsonl`: one line per call (provider, model, the song id, credits quoted and
  measured, the plan and rights, the file it made);
- optionally a team ledger: set `HOMIE_SPEND_LEDGER=<file>` (and `HOMIE_SPEND_ATTRIBUTION`) and
  each call is also appended there.

Credits are measured off the account (used before and after the call). Another job spending on
the same account at the same moment shows up in that number; the receipt keeps the quote beside
it.
