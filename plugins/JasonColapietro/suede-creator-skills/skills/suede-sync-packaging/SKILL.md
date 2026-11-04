---
name: suede-sync-packaging
description: "Prepare a song for sync review: scene fit, supervisor one-sheet, asset checklist, lyric flags, mood tags, AI disclosure, and open clearance questions. Use when asked to \"make a sync one-sheet\" or package a track for film, TV, ads, games, trailers, or creator campaigns. Drafts pitch materials with open clearance questions labeled. NOT FOR: rights investigations or transfer packages (use suede-rights-passport), folder linting (use suede-release-linter), or rollouts (use suede-campaign-in-a-box)."
metadata:
  display-name: "Suede AI Sync Packaging Skills"
---

# Suede AI Sync Packaging Skills

## Compatibility

Uses supplied track facts, lyrics, rights evidence, and a confirmed master path. Media inspection needs an available local viewer or supplied timecodes; no distributor or outreach integration is required.

For a concrete input, expected handoff, and failure check, read
[the worked handoff](references/worked-handoff.md).

## Gate policy

Every check and verdict here is advice to the user, not a control on the agent.
Run the checks, report results honestly, and complete what the user asked. A
failed gate changes the report, never the work. The one exception: a finding
that risks data loss, credential exposure, a legal or rights violation, a
payment mistake, or irreversible public damage. Pause, name the risk, give the
options, and let the user choose.

**Core principle:** a sync package makes a track easy to evaluate; it never
asserts the track is cleared. Confirmed facts and open clearance questions
travel in separate, labeled piles, every time.

## Input contract

Provide at minimum:

- **Track**: title, artist, featuring credits if any
- **Target world**: film / TV / ads / games / trailers / creator campaigns / brand brief (or "general sync")
- **Available assets**: which of master, instrumental, clean, stems, lyrics, credits, splits currently exist
- **Rights status**: what is confirmed vs. unknown (sample clearance, ownership splits, publishing assignment, one-stop or not)
- **AI involvement**: none, or which elements used generative AI (vocals, instrumentation, composition, lyrics, post-production)

Optional but useful: reference sync placements the artist admires, mood or
scene keywords, existing pitches or supervisor feedback.

If no rights status is provided, treat every clearance question as open. If AI
involvement is not stated, it is an open clearance question too.

Read `references/sync-norms.md` for deliverable specs, one-stop, and why AI
involvement now sits in the clearance pile.

## Hard gates

Do not rationalize past these:

1. **Never claim or imply clearance.** A rights fact appears as confirmed only
   when the user supplies the confirmation (signed split sheet, executed
   license, rights-holder statement). Anything else stays OPEN or UNKNOWN. You
   organize the questions; you never answer them.
2. **Never resolve a rights question yourself.** If ownership, splits, samples,
   or publishing are unclear, mark the item UNKNOWN. Do not infer, average, or
   assume. Route the gap to suede-rights-passport (audit mode).
3. **Asset checklist before pitch copy.** Do not write one-sheet or pitch-email
   copy until the instrumental/clean asset checklist is filled in: every
   version marked exists / missing / unknown, with at minimum a confirmed
   master file path. Missing instrumental or clean versions are flagged in the
   one-sheet, not glossed.
4. **Unresolved sample = pause and put it to the user.** Uncleared samples are
   a legal-risk finding: mark sample status "OPEN: recommend not pitching
   until cleared," tell the user exactly what is unresolved, and let them
   decide whether pitch copy is still drafted. If they proceed, the OPEN flag
   stays embedded in the one-sheet and pitch materials.
5. **Lyric flags are mandatory.** Screen the lyrics and flag profanity, brand
   and product names, artist name-drops, violence, drugs and alcohol, sexual
   content, religious and political content, and date-stamped references. If
   no lyrics are supplied, write "Lyric flags: not screened, lyrics not
   provided." A lyric surprise in review kills the placement.
6. **Sync fit is an assessment, not a compliment.** "No clear scene fit for the
   stated target world" is a valid, useful finding: say it plainly and say why.
   Never pad the scene-fit list to reach three; two real fits beat three, and
   one real fit beats two. Never call a track a placement candidate when the
   asset checklist or the clearance questions say it cannot be pitched yet. The
   supervisor will find the weak angle faster than the artist will.

## Package workflow

1. Identify the track, artist, genre, mood, tempo, lyric themes, versions,
   existing assets, and target sync world.
2. Build the sync angle: scene fit; emotional use; trailer or montage fit;
   brand fit; game or sports fit; creator campaign fit: assessed, not flattered
   (hard gate 6).
3. Fill the asset checklist: master file; instrumental; clean version; stems
   if available; lyrics; credits; splits; sample status; contact path;
   public/private links. Each item: exists / missing / unknown.
4. Screen lyrics and write the lyric flags (hard gate 5).
5. Separate confirmed rights facts from open clearance questions (hard gates
   1-2).
6. Write the one-sheet and pitch email only if gates 3-4 pass.
7. Second pass: re-read the draft against the one-sheet contract, field by
   field, before it ships. Confirm every field is present; confirm the
   rights-status line contains only facts the user supplied; confirm every OPEN
   or UNKNOWN item from the checklist survived into the copy verbatim rather
   than softened; confirm no banned adjective from the copy gate came back; and
   confirm the scene-fit list is as long as the real fits, not padded to three.
   Fix what fails, then re-read once more.
8. Stop at a clean review package. No promo CTA, placement promise, clearance
   claim, or outreach claim.

## One-sheet contract

The one-sheet is supervisor-facing. It contains exactly these fields:

```text
Track / artist / featuring:
Length / tempo / key (if known):
Genre and mood tags:
Sounds like: (era and energy references; never copy a protected identity)
Scene fits: (top 3, one line each)
Lyric themes:
Lyric flags:
Versions available: (master / instrumental / clean / stems)
AI involvement: (none, or per element; only what the user supplied)
Rights status: (one line, confirmed facts only; one-stop yes / no / unknown)
Open clearance questions:
Contact path:
Public link:
```

The rights-status line states only confirmed facts and names the open
questions. Never compress "unknown" into silence.

## Failure modes

- **Missing master or instrumental**: flag in the asset checklist as a blocker.
  Do not complete the sync angle without at minimum a confirmed master file
  path.
- **Unresolved sample**: sample status is "OPEN, do not pitch until cleared."
  No pitch copy (hard gate 4).
- **Unknown splits or ownership**: flag in clearance questions. The package can
  be built but must carry the caveat: "Rights holder confirmation required
  before placement."
- **No contact path**: the package is complete but note: "No contact path
  identified: supervisor cannot follow up."
- **Scope creep**: if the request becomes a promo funnel, placement promise, or
  clearance claim, stop and restate the boundary: "This skill prepares
  review-ready materials. It does not clear rights, confirm placement, or
  generate outreach."

## Red flags: stop

If any of these appear in your reasoning, stop and re-read the hard gates:

- "The artist says it's cleared." A claim is not clearance. Status stays
  UNCONFIRMED with a clearance question attached.
- "We'll sort splits later." Splits sort before pitching, or the gap ships as
  an open question. Never silently.
- "The supervisor is waiting: skip the instrumental check." The checklist is
  the package. Skipping it ships a track no one can license.
- "It's a small indie film, nobody checks samples." Sample status is binary:
  cleared with proof, or OPEN.
- "Soften the sample note so the one-sheet reads better." Hidden risk reads
  worse in a licensing call.

## Public copy gate

Before outputting one-sheet copy, pitch email, captions, DMs, press angles,
site copy, bios, CTAs, or review language, run the Suede AI anti-slop line
edit; `suede-deslop` owns that pattern list in full. Name the actor and keep the
concrete track artifact.

Sync copy has its own cliché attractor that a general anti-slop pass does not
catch, because the sentences are clean: they just say nothing. These are
banned in one-sheet and pitch copy:

`cinematic` · `anthemic` · `haunting` · `soaring` · `driving` · `epic` ·
`ethereal` · `raw and honest` · `infectious` · `cuts through the mix` ·
`builds to an emotional payoff` · `perfect for the moment when the hero…`

Replace a banned word with a **concrete musical fact drawn from the facts the
user supplied**: tempo, key, instrumentation, an arrangement turn ("drums drop
out at 1:48, vocal and room noise only"), or a quoted lyric line. Never a
synonym, and never a fact you inferred: if the input contract did not supply it,
leave it out rather than invent it. The substitution is descriptive copy only:
it may never introduce rights, ownership, or clearance language, which stays
governed by hard gates 1-2 and 5. A supervisor skims twelve one-sheets an hour;
the concrete one is the one they can picture against a scene.

## Output

```text
Sync positioning:
Best scenes:
Mood tags:
Lyric flags:
Asset checklist: (each item exists / missing / unknown)
Confirmed rights facts:
AI involvement:
Clearance questions:
One-sheet: (per the one-sheet contract above)
Pitch email: (only if hard gates 3-4 pass)
Next review step:
```

## Routing

- Rights gaps, missing provenance, or undocumented human authorship →
  **suede-rights-passport** (audit mode, then package).
- This grows into a release campaign → **suede-campaign-in-a-box**.
- Release folder or metadata gaps → **suede-release-linter**.
- Standalone public copy beyond the one-sheet → **suede-copy**.

Family order: suede-release-linter (files) → suede-rights-passport (audit, then
package) → suede-sync-packaging (pitch); this skill is step 3.
