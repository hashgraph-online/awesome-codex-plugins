# Durable note policy

## Promote

Promote information that will materially help a future contributor understand, operate, or continue the project:

- accepted decisions with rationale and consequences;
- confirmed requirements, constraints, and conventions;
- current architecture and verified system behaviour;
- discoveries and resolved root causes;
- reusable procedures;
- known risks and limitations;
- current priorities, blockers, and next steps;
- stable project references.

## Do not promote

- exploratory discussion and unselected alternatives;
- transient tool output;
- failed attempts without a reusable lesson;
- repeated existing knowledge;
- speculative inferences;
- temporary status that no longer affects future work;
- secrets or unnecessarily sensitive data.

## Classification

| State | Meaning | Default action |
|---|---|---|
| confirmed | Explicitly established or marked by the user | Promote after duplicate and conflict checks |
| inferred | Strongly implied but not confirmed | Ask for approval |
| tentative | Idea, option, or experiment | Session summary only |
| duplicate | Already represented accurately | Do nothing |
| superseded | Previously valid knowledge has been replaced | Link old and new notes; require approval |
| conflict | Contradicts existing durable knowledge | Stop and ask |
| sensitive | Credential or inappropriate durable data | Exclude and warn safely |

For a conflict candidate, preserve both sides in review metadata: the concise existing claim and evidence, the proposed claim and evidence, links to relevant notes, and an initially `undecided` resolution. Valid reviewed resolutions are `keep-existing`, `accept-proposed`, `merge`, and `supersede`. Never infer a resolution from recency alone. For `merge`, record the exact combined wording before approval. For `supersede`, record the replacement wording and preserve historical linkage from the old note to its replacement. Do not apply a resolution whose resulting durable text or target links remain ambiguous.

## Review mode

Default to review mode:

- explicit markers may be promoted after safety and conflict checks;
- confirmed unmarked facts are proposed at wrap-up;
- inferences always require approval;
- conflicts, deletion, and supersession always require approval.

## Provenance

Durable notes may record the date and a short human-readable source label such as `Codex work session`. Do not store internal session IDs, trace IDs, transcript paths, or machine-specific metadata in published-vault content.

## Secret handling

Never save passwords, API keys, access tokens, private keys, cookies, MFA codes, or authentication secrets. If the conversation contains one, do not repeat it. Record only a safe operational fact when genuinely useful, such as "rotate the exposed credential."
