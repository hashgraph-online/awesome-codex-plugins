# Precision Rules — Forbidden Lexicon and Authoring Conventions

Plugin runtime asset. Loaded by the `plan`, `document`, `review`, and `init`
skills before composing any document, together with the produced type's
content contract. See also `skills/_shared/adr-contract.md`.

The forbidden lexicon in Rule 1 and the line form in Rule 7 mirror the canon the
Archcore CLI ships in its document templates and measures in its post-tool-use
hook. This file exists to reach the agent **before** it composes; the hook
reports **after** it writes. When the two disagree, the CLI is right and this
file is corrected — one canon with two owners is two canons.

## Rules

1. **Forbidden vagueness lexicon.** New documents and updates MUST NOT introduce
   these words: `appropriate`, `robust`, `scalable`, `modern`, `best practices`,
   `various`, `as needed`, `optimal`, `efficient`, `flexible`, `convenient`,
   `seamless`, `streamlined`, `world-class`, `cutting-edge`, `оптимальный`,
   `удобный`, `правильный`, `надёжный`, `гибкий`, `современный`, `передовой`,
   `эффективный`, `масштабируемый`. Replace with a concrete fact, version,
   threshold, or measured outcome. The hook reads the whole document rather than
   the added lines, so editing an older document also surfaces the occurrences
   that predate the edit.

2. **Imperative phrasing in normative sections.** Documents of type `rule`,
   `spec`, and any contract document MUST use `MUST` / `MUST NOT` / `MAY` for
   prescriptive statements. Narrative phrasing ("we should", "it is recommended",
   "следует") is forbidden in those sections. Other sections (Rationale,
   Examples, Context) MAY use narrative voice.

3. **`[assumption]` marker.** When a technical claim cannot be grounded in
   existing code, prior measurement, or external authority, it MUST be marked
   `[assumption]` inline at the start of the claim or sentence. Vision-stage
   documents (idea, prd, plan, mrd, brd, urd) MAY contain many such markers;
   decision-stage documents (adr, spec, rule) SHOULD contain few.

4. **Falsifiable claims.** Performance, scale, reliability, and behavior claims
   MUST include a measured value with units and a measurement context
   (`p99 < 200ms at 1000 rps, load profile L2`) OR be marked `[assumption]`.
   Adjective-only claims (`fast`, `scalable`, `low-latency`) without a
   measurement are forbidden.

5. **No cross-document body sections.** Documents MUST NOT contain a body
   section that enumerates other `.archcore/` documents — for example
   `## Related Documents`, `## Related Resources`, `## Related Materials`,
   `## References` listing ADRs/RFCs/rules/guides, or `### Related Artifacts`
   listing archcore docs. Cross-document links live exclusively in the
   relation graph, managed by `mcp__archcore__add_relation` and queried via
   `mcp__archcore__list_relations`.

   The body MAY cite:
   - source code via `@path/to/file` notation (`@internal/mcp/server.go`)
   - commits, PRs, dashboards, metrics, runbooks
   - external authorities (RFCs, papers, vendor docs, blog posts)
   - the document's own enforcement artifacts (lint rules, CI checks)

   Rationale: the relation graph is the single source of truth for
   cross-document links. Duplicating them in body markdown causes drift when
   relations change, hides structure that callers can already query, and
   pollutes prose with plumbing that belongs in metadata.

## Examples

### Good

- "PostgreSQL 16.2 on RDS db.r7g.xlarge — chosen because the team needs
  `pg_advisory_lock` (used in the scheduler module's distributed-lock helper)."
- "Authentication MUST verify JWT signature using ES256. [assumption] Token
  rotation will be 24h pending security review."
- "Reduces p99 latency from 4.2s to <80ms under load profile L2 (Grafana
  dashboard #42, 2024-03-15)."
- "MUST NOT call this function from within a transaction — it acquires its
  own connection."
- "Implementation lives in `@internal/mcp/server.go`; conformance tests in
  `@internal/mcp/server_test.go`."

### Bad

- "Chose a robust, scalable database appropriate for our needs."
- "Authentication should be reliable and modern."
- "Significantly improves performance under load."
- "It is recommended to use the helper for convenience."
- A `## Related Documents` section listing `.archcore/auth/popup/architecture.doc.md`
  and `.archcore/auth/popup/component-interaction.rule.md` — those links
  belong in the relation graph (`mcp__archcore__add_relation`), not in the
  body.

6. **Architect voice: expert, concise, precise, argued.** Documents are
   decision records and context maps — not implementation walkthroughs. The
   target quality is: a senior engineer reads it in 30 seconds and knows
   *why* this exists, *what* was decided, and *what it costs*. Verbose
   AI-padded prose that restates the obvious is a defect.

   **Use freely:**
   - `@path/to/file` references, commit hashes, PR links, issue numbers
   - Inline code for identifiers, function names, type names, version strings,
     CLI flags — anything that names a concrete artifact
   - Measurements, thresholds, SLOs, dates — exact values beat adjectives

   **Avoid:**
   - Pasting function bodies or multi-line code blocks where a `@reference`
     would suffice — the source file is readable; the document is not its copy
   - Filler phrases ("This document describes...", "In summary, we can see...")
   - Generic implementation detail that adds no architectural signal

   **Code blocks belong** in types where the exact textual format IS the
   artifact: `rule` (Good/Bad examples), `guide` (terminal steps), `cpat`
   (Before/After). Also appropriate in any type when the user explicitly
   requests them or when the format itself is normative (wire protocol,
   config schema, CLI interface).

   This default applies to: `adr`, `rfc`, `doc`, `prd`, `idea`, `plan`, `mrd`,
   `brd`, `urd`, `brs`, `strs`, `syrs`, `srs`.

7. **Line form follows the document type.** Two profiles cover every type: one
   constrains the sentence, one constrains the structure. Both apply everywhere;
   the type decides which half binds.

   **Normative types** — `spec`, `rule`, `guide`, `task-type`, `brs`, `strs`,
   `syrs`, `srs`. One requirement per numbered clause, one uppercase BCP 14
   modal, an active-voice obligated subject, and the trigger before the response
   (`WHEN <trigger>, the <actor> MUST <response>`; unwanted conditions as
   `IF <condition>, THEN ...`). A graded clause stays at or under **25 words**; a
   procedure step stays at or under **20 words** and carries no modal, because a
   step is an action to take rather than an obligation that holds.

   **Claim-recording types** — `adr`, `rfc`, `doc`, `prd`, `plan`, `idea`, `rnd`,
   `cpat`, `mrd`, `brd`, `urd`. A numbered clause MUST NOT carry a BCP 14 modal.
   State the claim with its evidence — `@path/to/file`, a measurement, a commit —
   or mark it `[assumption]`. An obligation that belongs to one of these
   documents belongs in a linked `spec` or `rule` instead.

8. **No open-ended list and no ambiguous alternative in a requirement.** `etc.`,
   `и т.д.`, and `and/or` leave the reader to guess where the obligation ends or
   which branch binds. State the last member, or name the property that decides
   membership.

## Enforcement

- The CLI's PostToolUse hook (`archcore hooks <host> post-tool-use`, launched
  via the plugin's `bin/post-tool-use`) reports the mechanical half: the
  forbidden lexicon, the mandatory sections of each type, a heading another type
  owns, the line form and word metrics of Rule 7, the open-ended lists of Rule 8,
  and the per-type notation each content contract names. Findings are emitted as
  `additionalContext`. The hook never blocks (always exits 0), and a CLI that
  predates a check reports nothing for it — this one sentence is the canonical
  statement; the per-type content contracts do not restate it.
- The hook reads the whole document rather than the added lines, so an edit to an
  older document surfaces that document's existing findings too.
- Rules 3, 4, and 6 carry no automated check. A program finds a missing marker;
  it does not decide whether a claim needed one.
- Skills load this asset and the relevant contract before composition.
