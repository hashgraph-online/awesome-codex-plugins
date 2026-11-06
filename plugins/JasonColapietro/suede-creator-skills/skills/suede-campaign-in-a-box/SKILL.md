---
name: suede-campaign-in-a-box
description: "Suede AI Campaign in a Box Skills. Use when asked to \"plan a release campaign\" for a song, era, show or catalog: select a lane and build announce, tease, launch and follow-up assets with rights gaps and fan actions. NOT FOR: isolated copy (suede-copy), sync packages (suede-sync-packaging), rights resolution (suede-rights-passport), or software releases (suede-launch-packaging)."
metadata:
  display-name: "Suede AI Campaign in a Box Skills"
  version: 1.0.0
---

# Suede AI Campaign in a Box Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Works from artist/release context, rights records and available media; file tools for packages and calendar drafts. Rendering or publication requires the relevant existing tools and separately authorized accounts.

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

The all-in-one artist campaign skill: it turns a song, release, era, catalog
moment, show, or drop into a complete campaign an artist can actually execute.
Every campaign capability lives here as a labeled lane. Pick the lane you need,
or run the full package that stitches them together.

**Core principle:** you organize and prepare. You do not clear rights, confirm
ownership, approve payouts, write to any registry, secure placements,
manufacture cosigns, or guarantee that anything will go viral or sell. Say what
to test; never promise the result.

## Pick the lane (router)

Read the request and route to the lane that fits. You can chain lanes: most
real campaigns use several. If the request is "do the whole rollout," run
**Lane 0 (Full Campaign Package)** and pull the other lanes in as sections.

| If the user wants... | Go to lane |
|---|---|
| The whole rollout packaged: announce, teaser, release week, post-drop, fan proof, catalog afterlife | **0. Full Campaign Package** |
| The artist to feel recognizable before any bio/campaign/site is written, identity, world, voice, anti-references, fan promise | **1, Identity Forge** |
| A release turned into a recognizable world: visual language, symbols, color, wardrobe, content behavior, rollout tone | **2. Era Builder** |
| One track expanded into a creative universe: scenes, characters, imagery, captions, drop ideas, mechanics | **3. Song To Universe** |
| The 5-15 second moments that people clip, duet, remix, chant, or share | **4. Hook Hunter** |
| A memorable launch moment: stunt, fan mission, puzzle, timed drop, geo clue, unlock, collector action, street-team mechanic | **5. Release Stunt Lab** |
| Repeatable fan behavior: phrases, gestures, comments, unlock actions, live moments, collector rituals, trackable tasks | **6. Fan Rituals** |
| Visual direction: visualizer, lyric video, canvas loop, stage loop, cover motion, AI video prompts, teaser edits, scene boards | **7. Visualizer Director** |
| Merch and physical/collector objects beyond generic logo shirts, tied to lyrics, lore, and fan behavior | **8. Merch Object Lab** |
| A live set shaped like a show: arc, intros, transitions, crowd moments, visual cues, encore, talk breaks, merch tie-ins | **9. Setlist Theater** |
| Old songs, demos, takes, covers, stems, live clips, unreleased folders, anniversaries, or forgotten assets revived | **10. Catalog Resurrection** |
| Collaborator, remixer, producer, visual artist, venue, brand, or creator matchmaking with outreach angles | **11. Collab Matchmaker** |

Default starting order when identity is fuzzy: Lane 1 → Lane 2 → (Lane 3 if it
is one song) → hooks/stunts/rituals/visuals/merch/live as needed → Lane 0 to
package. If the artist already has a clear world, jump straight to the lane the
request names.

## Multi-agent vs single-agent (ask up front)

This skill can run as a coordinated multi-agent team: one agent per lane, plus
a packager that reconciles them into one campaign. Before spawning any fleet,
ASK: "Run this as a multi-agent team (more thorough, may use more tokens) or as
a single agent (faster, one pass)?" Never silently spawn a fleet. If the user
does not choose, default to single-agent and offer to escalate. In multi-agent
mode, keep one shared identity/era spine so the lanes do not contradict each
other, and have the packager resolve conflicts before output.

**Model and cap, state both on the same ask.** A spawned agent inherits the
session model unless the dispatch names one, so name the model explicitly on
every lane dispatch (do not let it default). Cap concurrent lane agents at
**4**. Twelve lanes plus a packager is 13 agents; run them in waves of 4 or
fewer, or ask first. Going past 4 requires naming the model and the rough cost
in the same question and getting an answer before launching: an inherited
session model is not an answer.

---

## Lane Playbooks

The twelve lane playbooks are in `references/lanes.md`. Pick the lane with the
router above, then read only that lane's section. The Public Copy Gate and
evidence boundaries below apply to every lane and stay here.

## Public Copy Gate (applies to every lane)

Before outputting captions, emails, DMs, press angles, site copy, bios, one
sheets, CTAs, or pitch language, run the Suede AI anti-slop line edit (`suede-deslop`). Name the
actor, preserve the concrete artist/release artifact, cut throat-clearing,
negative listing, fake intensity, lazy extremes, passive actor-hiding,
pull-quote slogans, generic AI phrasing, unsupported claims, and em dashes.

## Evidence boundaries (non-negotiable, every lane)

These lanes organize and prepare campaign material. They do NOT:

- clear rights, confirm ownership, or resolve sample/contributor/clearance
  questions: flag stale or uncertain rights, samples, contributors, and
  likeness instead of asserting they are cleared;
- confirm ownership or write anything to a registry;
- approve, route, or guarantee payouts, payments, or fulfillment;
- secure placements, sync, endorsements, partnerships, or cosigns: never imply
  partnership, endorsement, or access that is not confirmed;
- invent streams, press, traction, biography, or cultural status;
- promise virality, sales, or any outcome: say why something might work and
  what to test;
- use fake hype, fake scarcity, manipulative claims, or unsafe fan behavior;
- copy another artist's protected identity or assets; no competitor product
  names.

Branded visual output (Lane 7 visualizers, cover motion, teaser edits; Lane 8
merch objects) uses only the approved Suede S mark file named in
`suede-launch-packaging`: never redraw, trace, recolor, or generate a
replacement. If that file is unavailable, block the branded visual and request
it rather than substituting artwork.

Never resolve a rights question in-lane. When any lane touches ownership,
samples, contributors, splits, likeness, or clearance, mark the item UNKNOWN or
UNCONFIRMED and route it to `suede-rights-passport` (audit mode): the campaign plans around
the gap, never over it. When facts are unknown, mark them unknown. Keep safety,
venue, privacy, payment, and platform-rule constraints visible in the output.

## Red flags: stop

If any of these appear in your reasoning, stop and re-read the evidence
boundaries:

- "The artist says the sample is cleared." A claim is not clearance. Mark it
  UNCONFIRMED and route to `suede-rights-passport`.
- "Imply the collab or placement is confirmed so the outreach lands harder."
- "Say 'only 500 made'; scarcity sells." Not unless the cap is real.
- "Write 'as seen in'; press will probably come." Invented traction.
- "Promise this hook goes viral; it scores high." Say why it might work and
  what to test. Never promise the result.

## How to close

End with the relevant lane Output block(s). When the work produces a final
explanation the artist will act on (a full campaign package, a pitch), lead
with a **Simple explanation (plain, for a 10-year-old)**: one plain paragraph
covering what this campaign is, what the fan is asked to do, and what happens
next; no jargon, no hype, no industry words. Then give the normal breakdown:
the lane Output blocks, the build-next CTA, and any flagged rights/safety gaps.

## Routing

- Rights, sample, split, AI-authorship, or clearance gaps surfaced in any lane
  → **suede-rights-passport** (audit mode, then package).
- Release page, artist site, or lyric/credits page needs to rank in search or
  get cited in AI answers → **suede-seo-audit** for the page, **suede-ai-seo**
  for AI-answer visibility.
- An app tie-in (lesson app, companion app) needs a store listing →
  **suede-aso**.
- Track pitched for film/TV/ads/games → **suede-sync-packaging**.
- Release folder and metadata readiness → **suede-release-linter**.
- Standalone conversion copy outside this campaign → **suede-copy**.
