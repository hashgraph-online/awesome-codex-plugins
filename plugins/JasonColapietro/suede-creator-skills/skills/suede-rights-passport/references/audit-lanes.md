# Rights Audit Lanes

Audit mode runs one or more of these lanes before (or instead of) building a
package. State the lanes you run. For a broad request run A, B, C, D in order:
B resolves provenance for C, and C surfaces the splits D needs.

## Shared evidence table

Every lane records each asset, claim, or fact as one row before giving any
recommendation, brief, or routing status:

```text
Item / asset / claim / fact:
Status: confirmed | inferred | unconfirmed | disputed | unknown | not-applicable
Evidence:
Hash or path:
Risk: low | medium | high | unknown
Blocks:
Next action:
```

Severity:

- `high`: blocks registry, licensing language, sync pitch language, royalty
  routing readiness, a published statement, or agent-readable commerce until a
  creator, legal, or rights-holder confirmation exists.
- `medium`: can move with caveats, but needs confirmation before money,
  licensing, registration, or public use.
- `low`: cleanup or documentation that does not block review.
- `unknown`: not enough evidence to rate.

The ship gate is mechanical: any `high` item makes it `blocked`; otherwise any
`unknown` risk or status makes it `unknown`; otherwise `ready-for-review`.

Status promotion is mechanical too. An item becomes `confirmed` only when the
user supplies the evidence (signed split sheet, executed license, registration
record, rights-holder statement). When torn between two statuses, record the
weaker one.

## Coverage check before reporting

- Every asset, contributor, and claim in the source is exactly one row: none
  dropped, none duplicated.
- Every `high` row names the missing document or confirmation behind it.
- Anything you could not rate ships as `unknown`. An omitted row reads as a
  clean row.

If any check fails, say the audit is partial in the ship gate and name what was
missed.

## Audit output

- Lanes run.
- Confirmed facts and missing or unknown facts, in separate piles.
- The evidence table.
- Blockers (the `high` rows) and questions for the creator or rights holder.
- Safe public wording, unsafe claims removed, and do-not-share items.
- Ship gate: `ready-for-review` | `blocked` | `unknown`, plus the next step
  (build the package, run `suede-release-linter`, or `suede-sync-packaging`).
- A plain-language summary a non-lawyer can act on, and the reminder that this
  is organized evidence, not legal clearance.

## Lane A: Rights-gap audit

Identify rights and intake gaps before packaging. Sweep all eight areas:

1. **Ownership**: owner claim, ownership status, transfer status, and unresolved
   confirmations.
2. **Contributors**: writers, producers, performers, engineers, featured
   artists, visual contributors, and managers.
3. **Splits**: percentage totals, missing parties, disputed splits, and payout
   caveats.
4. **Samples**: sample sources, interpolation notes, clearance status, and
   unknowns.
5. **Licenses**: distribution, sync, beat, artwork, stem, remix, and platform
   license notes.
6. **Provenance**: source sessions, masters, stems, artwork, lyrics, metadata,
   and evidence trail. (Hand off to Lane B when this is thin.)
7. **Public context**: public URLs, release history, takedowns, and conflicts.
8. **AI involvement**: which elements used generative AI (vocals,
   instrumentation, composition, lyrics, artwork, post-production), the tool
   and its terms, voice or likeness consent for any cloned or synthetic voice,
   and evidence of human authorship. The US Copyright Office's position (Part 2
   report, January 2025) is that purely AI-generated material is not
   copyrightable and prompts alone are not authorship, so an AI-heavy track
   with no human-authorship evidence is a `high` row for licensing and
   registration.

Run the shared evidence table per item. Output:

```text
Confirmed facts:
Missing facts:
Evidence table:
Blockers:
Questions for creator:
Safe public wording:
Next: build the package | Lane B provenance | Lane C licensing | Lane D routing
```

Do not treat the audit as legal clearance.

## Lane B: Provenance map

Make the origin trail readable without overclaiming what is known.

1. Inventory source materials: sessions, masters, stems, artwork, lyrics,
   videos, documents, metadata files, and public URLs.
2. Separate confirmed facts from inferred facts and unknowns.
3. Capture relative paths and hashes when available.
4. Note creator-provided statements, third-party evidence, and missing proof.
5. Identify provenance conflicts, unclear dates, duplicate files, and files that
   should not be shared publicly.
6. Produce review notes that can feed the package or a licensing brief.

High-risk provenance gaps block registry, licensing, royalty routing,
published statements, or agent commerce until the origin trail is confirmed. Output:

```text
Asset map:
Known origin:
Evidence:
Evidence table:
Unknowns:
Conflicts:
Do-not-share items:
Next questions:
```

## Lane C: Licensing-discussion readiness

Prepare creator materials for licensing review while keeping evidence boundaries
visible. Does NOT claim rights are cleared. This is the brief for a rights
conversation; the supervisor-facing one-sheet is `suede-sync-packaging`.

1. Identify the work, owner claim, contributors, versions, and intended use.
2. Collect rights status, split status, sample status, distribution history,
   public URLs, and restrictions.
3. Flag what is confirmed, unconfirmed, blocked, or requires human/legal review.
4. Write a concise licensing brief with only safe claims.
5. Add questions for the creator, manager, label, or rights holder.
6. Route unresolved provenance to Lane B and unresolved splits to Lane D.

High-risk items block licensing language, sync pitch language, published statements, or
agent-readable commerce until confirmed. Safe copy can say what is known and what
still needs rights-holder review. Output:

```text
Licensing brief:
Confirmed rights facts:
Evidence table:
Open questions:
Restrictions:
Unsafe claims removed:
Next step:
```

## Lane D: Royalty-routing readiness

Summarize whether a project is ready for royalty-routing discussion. Readiness,
not approval. Public-safe. Moves no money.

1. Identify contributors, roles, split percentages, payment destinations, and
   unresolved parties.
2. Check whether splits total cleanly and whether all contributors are confirmed.
3. Separate routing readiness from payout approval. Do not imply money has been
   approved, sent, scheduled, or guaranteed.
4. Note missing tax, wallet, payment, territory, label, publisher, or rights-
   administration facts only at a safe level (never expose sensitive payment
   details).
5. Produce creator questions and a public-safe summary.

High-risk items block routing readiness when contributor identity, role, split
percentage, payment destination, publisher, label, territory, tax, or rights-
administration facts are missing, disputed, or unsafe to expose. Output:

```text
Routing status:
Confirmed splits:
Evidence table:
Missing confirmations:
Payout caveats:
Creator questions:
Safe summary:
Ship gate: ready-for-review | blocked | unknown
```

Source for lane A item 8: U.S. Copyright Office, *Copyright and Artificial
Intelligence, Part 2: Copyrightability* (January 2025),
<https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf>
