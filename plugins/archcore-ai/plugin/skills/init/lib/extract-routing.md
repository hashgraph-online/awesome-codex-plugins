# Extract-mode routing rules

Reference data for `/archcore:init` agent-instruction import, extract mode (Phase B plans, Phase E creates). Extract is the **default** for `modular-rule` files (`.cursor/rules/*.mdc` and equivalents — see `lib/agent-files.md` file classes) and an **opt-in** for `aggregate` files (whose default is `link`).

The skill's LLM does the classification; this file is the spec it follows.

## Block splitting

1. Split the source file into candidate blocks:
    - **Headings (H1 / H2 / H3)** — each heading starts a new block that runs until the next heading of the same or higher level.
    - **Horizontal rules (`---`, `***`, `___`)** — treated as block separators.
    - **Frontmatter** — ignored. Do not create a document from the frontmatter block.

2. Drop blocks that have no actual content (heading-only, whitespace-only, just a list of links).

3. If the source file has **no headings at all**, treat the whole body as a single block.

**Modular-rule files are one rule by design.** For a `modular-rule` source (a `.cursor/rules/*.mdc`, `.github/instructions/*.md`, etc.) of **≤ 200 lines**, do NOT block-split — treat the whole body (after frontmatter strip) as a single block, yielding exactly one document. A Cursor/Copilot rule file is authored as one cohesive rule; splitting it by its Good/Bad/Rationale sub-headings would shatter one convention into fragments. Only block-split a modular-rule file when it exceeds 200 lines, first by its H2 headings. **If a resulting block itself exceeds 200 lines, recursively split it by H3 headings — or, absent H3s, into ≤ 200-line paragraph groups — so no extracted document ever exceeds the 200-line cap**, whatever the source file's heading structure. Aggregate files always block-split, under the same recursive cap.

## Per-block classification

For each surviving block, pick exactly one route. If multiple routes match, the first match wins (top of list = highest priority).

### Route 1: Rule

Criteria (any hit — inclusive OR):

- Block contains at least one **imperative sentence** — a sentence whose first word (after optional list-marker like `-` / `*` / `1.`) is an imperative verb: `use`, `do not`, `don't`, `never`, `always`, `must`, `should`, `avoid`, `prefer`, `require`, `enforce`, `write`, `code`, `style`.
- Block contains ≥ 3 bullet points that each look like a standard / convention (short declarative line, often starting with a verb or a noun phrase like `API handlers …`, `Tests …`, `Commit messages …`).

Produce: one `rule` document per block.

Title: derive in priority order — (1) the source file's YAML frontmatter `description:` value, if present and non-empty (Cursor/Copilot rule files carry the rule's intent there, and it is the closest analogue to an archcore `title`); (2) the block's heading, if present; (3) a short summary of the first imperative sentence, sentence-case, no trailing period. Examples: *"Enforce App Router exclusivity"* (from frontmatter), *"Prefer function components"* (from heading), *"API handlers live in src/api/handlers"* (from sentence).

Body: reproduce the block's content verbatim (modulo leading `>` pointer and preserving the existing list structure). Do not rewrite the rule — the user wrote it this way deliberately.

Filename slug: derive from the title (lowercase, hyphen-separated). Prefix with `imported-` for clarity. Example: `imported-prefer-function-components`.

Directory: `conventions/` — imported conventions live alongside native rules so `/archcore:context` surfaces them as rules, not as buried imports; the `imported` + `source:<slug>` tags plus the pointer line carry provenance.

Status: `draft` (not `accepted`) — extracted rules are heuristic-derived and the user should review before accepting.

Tags: `imported`, `source:<source-slug>`. No additional tags.

### Route 2: ADR (decision)

**`/archcore:init` depth gate:** in init this route fires only at **`deep`** depth (per `SKILL.md` → Depth axis: "Authored decisions → ADR: deep only" — ADR extraction is the highest-risk synthesis). At `light`/`standard` — including an opt-in `edit → extract` of an aggregate file — a block that would match Route 2 is downgraded to **Route 3 (doc)** instead; never create an `adr` outside `deep`.

Criteria (any hit):

- Block contains phrases like `we chose <X> because`, `we decided <X>`, `we picked <X>`, `<X> over <Y>`, `rather than <Y>`, `instead of <Y>`.
- Block has a structure resembling the classic ADR shape (Context → Decision → Consequences) even if the headings use different wording.

Produce: one `adr` document per block.

Title: derive from the heading, or from the first "we chose" sentence (sentence-case, no trailing period).

Body: split the extracted block content into the ADR required sections. Best-effort:

- **Context** — any prose that precedes the "we chose" sentence, or the preceding paragraph.
- **Decision** — the "we chose" / "we decided" sentence itself.
- **Alternatives Considered** — anything mentioning the rejected option (`over <Y>`, `instead of <Y>`).
- **Consequences** — if the source has no explicit consequences, leave the section with a single-line placeholder: *"Derived from `<source-path>`; review and fill in."*

Filename slug: `imported-<title-slug>`. Directory: `imported/`. Status: `draft`. Tags: `imported`, `source:<source-slug>`.

### Route 3: Doc (reference / overview)

Default route if Routes 1 and 2 do not match.

Criteria (any match is sufficient — this is the catch-all):

- Block is purely descriptive — explains how something works, lists facts, gives examples without imperatives.
- Block is a glossary, stack summary, file layout description, or reference table.

Produce: one `doc` document per block.

Title: derive from the heading, or `Imported: <first-3-words-of-block>` if no heading.

Body: pointer line + blank line + verbatim block content (modulo heading de-leveling — see below).

Filename slug: `imported-<title-slug>`. Directory: `imported/`. Status: `draft`. Tags: `imported`, `source:<source-slug>`.

## Heading de-leveling

If the source block was under an H2 in the source file and is now a standalone document, its internal H3s should stay H3s (not promoted to H2s). Leave heading levels as they are in the source — we're not reformatting, just relocating.

## Umbrella document

Before creating any extracted documents, create the umbrella `doc` for the source file (see `lib/agent-files.md` → "Umbrella document for extract mode"). Every extracted document gets a `related` edge from itself **to** the umbrella (source-to-umbrella, not the reverse).

## Limits

- Never emit more than **10 documents per source file** in extract mode. If a source file would yield more, cap at 10 and warn the user: *"Source file yielded more than 10 extractable blocks. Keeping first 10; remaining blocks will need manual import."*
- Skip any block shorter than **120 characters** (after trimming). Too short to be a meaningful rule/doc/adr.

## Safe fallback

If classification is ambiguous for a block (none of Routes 1/2/3 fit cleanly), default to **Route 3 (doc)**. Never skip a block silently in extract mode; if it's not trivially short, something gets produced. `status: draft` means nothing goes to the "accepted canon" until the user reviews.
