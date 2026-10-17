# Conversion routing — from authored sources to native documents

Reference data for the `convert` and `verify` gates of `skills/_shared/tracks/import.md`. The skill's LLM does the extraction and the composition; this file is the contract it follows. Contract: `import-conversion-and-staging.spec`. Source records and verdicts: `skills/init/lib/sources.md`.

The unit of work is the **target document**, not the source file. A converted corpus follows the structure of Archcore — one document per topic, of the type that fits the content — never the structure of the files it came from.

## How to find it

The kind signals below are **non-exhaustive** examples. Classify a passage by what it does for its reader — obliges, explains a choice, gives steps, fixes a boundary, lists facts, states an intent — and emit a unit only on **positive evidence** that the passage records knowledge about this repository. Prefer omission over a guess.

## Step 1 — read and strip

1. Read the body of each `convert` or `mine` source only after the plan confirm.
2. Strip every archcore managed block (`<!-- archcore:start -->` … `<!-- archcore:end -->`), YAML frontmatter, tables of contents, badges, and link-only lists.
3. In a `mine` source, drop the passages of a skip class (`skills/init/lib/sources.md`) and keep the rest.
4. For a confirmed L4 `reference` target, compose the site `doc` from its path, publish tool, and discovered topics. Do not read skipped page bodies.

## Step 2 — extract knowledge units

A knowledge unit is the smallest passage that stands alone as one piece of knowledge. Record for each unit:

| Field | Content |
|---|---|
| `kind` | one of the eight kinds below |
| `topic` | the subject in two to five words — a module, a concern, a decision |
| `scope_paths` | the code paths the unit governs or describes; from `globs:`, from paths in the text, or empty |
| `source_spans` | source path plus heading or line range, one or more |

| Kind | Signals | Target type |
|---|---|---|
| `rule` | imperatives and prohibitions (`use`, `never`, `always`, `must`, `avoid`, `prefer`); a list of conventions | `rule` |
| `decision` | a choice with its reason (`we chose … because`, `X over Y`, `instead of`); a Context → Decision → Consequences shape | `adr` |
| `proposal` | a change still open for acceptance (`proposed`, `RFC`, `should we`) | `rfc` |
| `procedure` | ordered steps a person performs — setup, release, recovery | `guide` |
| `contract` | behavior a consumer relies on — an API, a schema, a protocol, a module boundary | `spec` |
| `reference` | descriptive facts — glossary, layout, inventory, ownership | `doc` |
| `intent` | something wanted and not built — a roadmap item, a wish | `idea` |
| `example` | concrete Given/When/Then cases or input→output tables that illustrate a contract | `scenario` — only when its `spec` is a row of the same plan and `skills/_shared/actor-subject-compatibility.md` returns `yes`; otherwise the examples go to that `spec` (Conformance, ≤ 5 lines) or to a `doc` |

A rule file of L1 is one `rule` unit unless its body plainly holds a second kind.

## Step 3 — cluster

1. Group units from **all** sources by `topic` and `kind`. Two sources on one convention give one cluster with two spans.
2. When units in a cluster disagree, or a unit contradicts the code, move the disagreement to the **conflicts list** — both statements, both spans — and keep it out of the target. The import never picks a side.
3. When a unit restates what a Tier-1 seed fact extracts — run commands, directory layout, stack — follow "Overlap with seed facts" in `skills/init/lib/sources.md`: the unit becomes evidence for that fact, not a cluster.
4. When one `topic` holds two kinds, make one cluster per kind and plan a relation between the targets (Step 6).
5. A cluster is one row of the import plan: target type, title, directory, spans, wave.

## Step 4 — fit the type

Load the content contract of the target type before composing: `skills/_shared/rule-contract.md`, `skills/_shared/adr-contract.md`, `skills/_shared/spec-contract.md`, `skills/_shared/guide-contract.md`, and `skills/_shared/precision-rules.md` for every type.

When a cluster cannot fill a mandatory section of its type, the type changes; the content is never padded:

| Missing | The cluster becomes |
|---|---|
| a `decision` with no recorded reason or no rejected option | a `rule` when it obliges, otherwise a `doc` |
| a `contract` with no observable behavior, only description | a `doc` |
| a `procedure` with no ordered steps | a `doc` |
| a `rule` with no recorded reason — the usual case for an agent-instruction file | still a `rule`; Step 5.4 binds its Rationale |
| a `proposal` that the code shows as already built | a `decision` cluster, under the row above when the reason is missing |

A commit message from L5 may supply the reason of a `decision`; cite the commit hash in Context.

## Step 5 — compose

1. **Rewrite, do not copy.** State the knowledge in the form of the type contract: one requirement per numbered clause with one modal in a `rule` or `spec`, claims with evidence in an `adr` or `doc`, imperative steps in a `guide`. Remove the source's framing, its history, and its address to the agent ("you are a…").
2. **Keep the obligation.** Rewriting changes form, never strength or condition. Map the source wording by this table and no other: `must`, `always`, `require`, a bare imperative ("Wrap errors with…") → `MUST`; `never`, `do not`, `don't` → `MUST NOT`; `should`, `prefer`, `recommended` → `SHOULD`; `avoid`, `should not` → `SHOULD NOT`; `may`, `can`, `optional` → `MAY`. A condition in the source (`unless`, `when`, `if`) stays a condition in the clause. A scope the type contract requires and the source omits (the paths a `rule` applies to) comes from the code, and the closing report lists each added scope.
3. **Invent no reason.** A Rationale, a Context, or a Consequences sentence states only what a source span says or what you verified in the repository in this run — a lint rule in a config file, a test, a call site. Verify before you write: a named function, flag, tool version, or mechanism MUST be found by a search of the repository first. WHEN the source gives no reason and the repository shows none, write the one fact you have ("Enforced by `forbidigo` in `@.golangci.yaml`") or mark the sentence `[assumption]`. A plausible mechanism you did not find is a fabrication, and it reads as authored knowledge.
4. **Ground every claim.** Cite code as `@path/to/file` and check that each cited path exists. A statement the code contradicts goes to the conflicts list. A statement the code cannot confirm keeps an `[assumption]` marker.
5. **No import mark.** A target carries no `imported` tag, no `source:` tag, no pointer line naming a source file, no `imported-` filename prefix, and no `imported/` directory. No umbrella document stands for a source file. The source-to-target map lives only in the import plan.
6. **Place it as a native document.** Directory by domain or topic, the same directories the code seed uses (`conventions/` for a repo-wide `rule`, the domain directory for a domain topic). Filename from the topic. Tags from the project's existing tags, plus the domain tag when the seed uses one.
7. **Status `draft`** in every case. An L2 record marked accepted in its source is still created as `draft`; the user accepts it.
8. **Line caps.** No target exceeds 200 lines; a `spec` stays within the cap of `spec-contract.md`. An over-cap cluster splits by sub-topic; evaluate links between the parts in Step 6 — decompose, never truncate (`decompose-over-truncate.adr`).
9. **Dedupe against the corpus.** Before `create_document`, call `search_documents` on the topic. When a local document already covers the cluster, set the row to `dropped` with the reason, or plan an `update_document` that the row shows as an update.

## Step 6 — relations

Evaluate these candidates through `skills/_shared/relation-authoring.md` after
reading the composed targets. Shared source material alone does not justify
every pair. Preserve the links needed to read a split subject as a whole.

| From | Edge | To | Condition |
|---|---|---|---|
| `rule` | `implements` | `adr` | the rule enforces that decision |
| `guide` | `related` | `rule` or `spec` | the steps operate what the target governs |
| `spec` | `implements` | `adr` | the decision fixed the boundary |
| `rfc` | `extends` | `adr` | the proposal amends that decision |
| target | `related` | a seed fact (stack rule, data-model, entry points) | a named statement in the target uses that fact |
| split part | `related` | another part | a shared boundary or reading sequence requires both parts |

WHEN a `search_documents` result carries `source_kind: "global"`, load `skills/_shared/globals.md`: a global document never counts as covering a cluster in Step 5.9, and `add_relation` never targets one. WHEN no result is global, proceed as usual. Skip an edge when an endpoint was not created.

## Fidelity check (used by `verify`)

For each target `rule` and `adr`, walk its normative statements and compare each with its `source_spans`:

1. The modal matches the source wording under the table of Step 5.2.
2. Every condition of the source statement is present.
3. No statement exists in the target that no span supports.
4. No obligation of the spans is missing from the target, unless the conflicts list or a `skip` class holds it.
5. Every factual sentence outside the normative clauses — Rationale, Context, Consequences, Enforcement — traces to a span or to a repository search you ran. Re-run the search for each named identifier, tool, and version; a name with zero hits is a departure.

Report each departure with the target path, the clause number, and the span. A target with a departure stays `draft` and is named in the closing report; the check changes no document by itself.
