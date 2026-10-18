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

Use the official ElevenLabs MCP's available account and rights information and the current
terms to record the plan and permitted use at generation time. If the MCP does not expose a
fact, record it as unknown; do not infer a commercial licence from a successful generation.
An account upgrade does not retroactively change the terms of earlier output.

## What never goes in

- A real person's name, voice or likeness, or "in the style of" a real artist.
- Lyrics the person does not have the rights to (someone else's song).
- A key, token or password, anywhere in the studio.

## Receipts

Before a paid call, record the approved budget and the official tool's quote, if available.
Keep the accepted request ID so polling or downloading an existing job does not submit it again.
Save the output and a normalized receipt with `homie-studio media import`, which records the
provider, tool, model, request ID, prompt, style revision, rights source and date, cost, file
hash and consumer in `media/provenance.json`.

Distinguish provider-reported actual cost from an estimate; use unknown when neither is exposed.
Do not infer job cost from changes in the account balance. Never save raw authentication data,
signed download URLs or an unfiltered MCP response in the studio.
