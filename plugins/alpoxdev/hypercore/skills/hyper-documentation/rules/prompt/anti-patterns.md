# Anti-Patterns

**Purpose**: List the failure modes a prompt artifact must not ship with. **Read when**: before finalizing any prompt artifact.

- Persona-only prompts with no success criteria, scope, authority, output contract, or verification.
- Prompts that ask for hidden chain-of-thought or private scratchpad disclosure.
- Source text treated as instructions when it should be evidence.
- Retrieved prompt injection copied into the final prompt as authority.
- Retrieved text pasted verbatim into a ledger, notes file, or memory instead of a distilled, attributed claim.
- A prompt that depends on a prefilled assistant turn to force its output shape.
- Volatile values (dates, the current task, per-turn state) inside the stable prefix, or a constraint that must survive a summary stated only in the conversation.
- Eval cases that can pass even when the prompt ignores the user's real task.
- Output schemas described only in prose when a downstream parser needs fields.
- Prompt packs with no variables, context packet, examples, eval cases, or version note.
- Optimization claims made without a baseline and a rerun of the same cases.
- A gate decided from a single run of non-deterministic behavior, or `pass^k` claimed from a `pass@k` result.
- A candidate that edits the case set, judge, guards, or evidence log, or a rising score accepted while guard coverage shrinks.
- Broad safety refusals that block normal use instead of gating specific side effects.
- Prompt artifacts that cite global or home directories as project authority.

## Sources

> Checked 2026-11-03 against the repository instruction base.

| Claim | Source | Checked |
|---|---|---|
| Prompt-authoring and contract anti-patterns | `instructions/context-engineering/references/prompt-authoring.md`, `instructions/context-engineering/CONTEXT_ENGINEERING.md` | 2026-11-03 |
| Retrieval, persistence, and memory anti-patterns | `instructions/sourcing/references/retrieval-safety.md` | 2026-11-03 |
| Single-run gating and guard tampering | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/autoresearch/AUTORESEARCH.md` | 2026-11-03 |
| Keep the loaded head stable and volatile values out of it | `instructions/cache/CACHE.md` | 2026-11-03 |

No external URL is cited in this file; every rule is a restatement of the repository base above.
