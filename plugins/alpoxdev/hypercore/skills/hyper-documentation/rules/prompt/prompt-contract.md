# Prompt Contract

**Purpose**: Define the field set and authority split of a durable prompt contract. **Read when**: creating or materially refactoring one.

Treat every durable prompt as an execution contract, not a persona paragraph.

## Required Contract Fields

| Field | Purpose |
|---|---|
| Intent | The real user outcome, success state, and failure state. |
| Trigger | When the prompt should be used and when it should not be used. |
| Scope | Allowed actions, owned artifacts, non-goals, and side-effect limits. |
| Authority | Instruction priority and conflict handling. |
| Evidence | Which context, files, sources, evals, and ledgers support claims. |
| Tools | Allowed tools, required gates, and forbidden side effects. |
| Output | Shape, language, required fields, forbidden formats, and destination. |
| Verification | Tests, evals, source checks, readback checks, and review gates. |
| Stop condition | Observable completion criteria and blocker conditions. |

## Authority Shape

Authority is ordered, and the order is published rather than invented. The current vendor spec orders Root, System, Developer, User, Guideline, and then no authority by default for assistant and tool messages, quoted text, file attachments, and other untrusted data. A prompt artifact does not restate that hierarchy. It declares where its own rules sit in it.

- Mark which rules are the artifact's developer-level instructions, binding on every run, and which are advisory defaults the user may override. A rule meant to bind must not be phrased as a preference, and a lower layer must not silently override a higher one.
- Treat assistant and tool messages, quoted text, attachments, retrieved pages, and delegated summaries as data with no authority. Instruct the prompt to analyze them, not to obey them.
- Deliver untrusted material in a labeled, parseable block (YAML, JSON, or XML) so a quote or a tag inside it cannot break out into instruction position.

A source does not become trustworthy by being familiar. A repository `AGENTS.md` outranks a downloaded file because of its path and review history, not because a reader recognized it.

## Stable Prefix And Volatile Tail

A reusable prompt is read many times, so the part that never changes goes first and the part that changes every turn goes last.

- The contract (identity, scope, authority, evidence rules, output schema, verification) is the stable prefix. The date, the current task, the target environment, and per-turn inputs belong in the tail appended after it.
- A stable prefix is not a stored prefix. On a chained conversation the runtime does not resend the earlier instructions: the OpenAI Responses API applies its `instructions` parameter to the current response only, and the instructions used on previous turns are not present in the context once state is chained. Anything that must survive every turn belongs in the project instruction files the runtime re-injects, not in a turn-1 message.
- Compaction can drop what the tail depends on. A constraint stated once in the conversation may not survive a summary, so a rule that must outlive the summary belongs in a file the next step re-reads.
- Place the cacheable boundary after the last block that is identical across requests. Where the provider bills writes, content after that boundary is processed at the normal input rate instead of being written to the cache.

## Long-Context Layout

When the prompt carries documents, code, or many materials, layout is part of the contract.

1. Put the material first and the question, instructions, and output format last. Both major vendors document this order, and Anthropic reports that a query at the end "can improve response quality by up to 30 percent in tests."
2. Give each block an id and a source, and require the answer to name the ids it used. Where the corpus is large, ask for a short evidence extract first and the final answer from that extract.
3. Keep the block count low. A handful of large, labeled documents beats many small fragments, because each fragment adds boundary text that carries no evidence.
4. Do not treat ordering as a substitute for selection. Context size is a quality variable, not only a cost variable: measured across model families, longer input degrades accuracy even when task difficulty is held fixed.
5. Express output shape in the instructions, an example, or a schema. Do not seed a prefilled assistant turn: on current Claude models a prefilled last assistant message returns a 400 error, so an artifact that depends on one breaks on a model upgrade.

## Reasoning Visibility

Do not require hidden chain-of-thought, private reasoning transcripts, or internal scratchpad disclosure. Ask for concise public rationale, assumptions, decision criteria, and verification evidence.

## Prompt Shape

A prompt pack should contain identity, variables, context packet, examples, constraints, output schema, eval cases, and version note. Use exact schema keys when downstream tools depend on them. Aim for the minimal set of information that fully outlines the expected behavior; minimal means every sentence carries a signal, not that the document is short.

## Sources

> Checked 2026-11-03 against the repository instruction base; the one vendor page listed was opened the same day.

| Claim | Source | Checked |
|---|---|---|
| Contract fields, authoring order, authority levels, the dynamic tail, long-context ordering, and the prefill rule | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| Stable prefix, cache boundary, and write-versus-read cost | `instructions/cache/CACHE.md` | 2026-11-03 |
| Context size as a quality variable and the minimal-set sizing rule | `instructions/context-engineering/references/core-principles.md` | 2026-11-03 |
| Long documents first, queries last, and prefilled responses returning a 400 error on Claude 4.6 and later | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-11-03 |

The contract rules restate the repository base. The vendor page was opened directly for the ordering claim and the prefill status, because both change what a generated prompt may contain.
