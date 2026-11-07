# Progressive Disclosure

**Purpose**: Keep skills lean while making deeper detail discoverable exactly when needed.

## 1. Three-Stage Loading Model

Design every skill as if agents load it in stages:

| Stage | Loaded content | Design goal |
|---|---|---|
| Discovery | `name`, `description`, path | Correct skill selection |
| Activation | Full `SKILL.md` | Core workflow and execution contract |
| Execution | `rules/`, `references/`, `scripts/`, `assets/` | Detail, deterministic helpers, or output resources only when needed |

The deeper the layer, the more specific and optional the content should become.

The stages cost differently. Metadata is loaded for every installed skill at roughly 100 tokens each,
whether or not it is used; the body loads on activation and should stay under 5,000 tokens; bundled
files cost nothing until read, and a script's code never enters context - only its output does. Some
runtimes also keep an invoked body in context across later turns without re-reading the file, so every
line of the body is a recurring cost and the most important instruction belongs near the top.

## 2. Context Budgets

The two figures below are **different things**, and the difference matters.

| Figure | Status | What it covers |
|---|---|---|
| 500 lines | `PRIMARY` - stated by the specification | The `SKILL.md` body |
| 5,000 tokens | `PRIMARY` - stated by the specification | The `SKILL.md` body |
| 300 lines | **This repository's chosen gate** | Only the files under `instructions/` |

The 300-line value is not a sourced figure. It is this repository's own default, enforced by
`scripts/check-sources.sh` through `MAX_LINES=300`, and that script sets `DOC_SCOPE="instructions"` - so
it checks `instructions/**` and **does not currently cover this skill**. Do not present 300 as a
specification requirement, and do not treat this skill as exempt from the 500-line budget because a
different check happens to scope elsewhere.

Other budget rules:

- Keep each `references/` file focused on one topic.
- Do not build deep reference chains.
- If you created a support file, reference it directly from `SKILL.md`.
- Do not create explanations that did not need a support file.
- Put eval fixtures and prompt templates in `assets/` when they are actually run or copied, rather than in
  a prose reference.

## 3. Keep the Core Lean

The core skill should contain:

- job, trigger, and boundary
- authority, safety, output, verification, and stop-condition summary
- high-level workflow
- gotchas: environment facts that defy reasonable assumptions. Keep them in the core, where the agent
  reads them before meeting the situation; a reference file only helps if the agent already knows to
  open it
- pointers to deeper files with read conditions

Move out:

- long examples
- official source summaries
- schemas and provider-specific details
- variant-specific workflows
- deterministic command logic
- output templates

## 4. Navigation Cues

Do not write vague references like `see references/`.

Weak:

```markdown
For more information, see references/.
```

Better:

```markdown
Read `references/official/openai.md` only when Codex-specific skill behavior changes the rule.
Read `rules/validation-and-iteration.md` before declaring the skill complete.
Run the target package's documented validator when present.
A repository-maintenance gate stays in the repository's policy documents, not in the skill artifact (`rules/self-containment.md`, SK-S-1).
```

State the read condition as a situation the agent can recognize, not as a directory: "Read
`references/api-errors.md` if the API returns a non-200 status code" beats "see `references/` for
details".

## 5. One Level Deep

Prefer support files linked directly from `SKILL.md`. Keep references **one level deep** from the core.

The reason is not tidiness: an agent may partially read a file that is referenced from another referenced
file, previewing it with something like `head -100` rather than reading it whole, and act on an incomplete
picture. A file that `SKILL.md` links directly is read in full. Avoid reference chains where a rule
requires another rule that requires another reference unless the chain is explicitly justified.

## 6. Reference File Structure

**For a reference file longer than 100 lines, put a table of contents at the top.** The same partial-read
behavior that makes deep chains risky also means a reader may see only the opening lines; a table of
contents makes the file's full scope visible even then.

## 7. Split by Need

Move content to:

- `rules/` for repeated policy
- `references/` for detailed knowledge
- `scripts/` for deterministic execution
- `assets/` for output resources
- `agents/` for consumed runtime/UI metadata

## 8. Readback Check

After splitting:

- confirm the core still makes sense on its own
- confirm support files are findable from the core
- confirm no key instruction is duplicated across layers
- confirm every support file has a reason to exist

### Removal test

The questions above ask whether content is *useful*. These decide whether it *earns its place*.

- SK-D-1: For each instruction, ask **"if this were absent, would the agent get it wrong?"** If the answer is no, delete it. If you are not sure, test it rather than keeping it on suspicion.
- SK-D-2: If a task succeeds without the skill, that skill may add no value. A skill that restates what the agent already does reliably is cost without benefit.
- SK-D-3: A skill is not automatically worth keeping because it is well written. A 2026 benchmark found 92 of 98 public skills had no statistically significant effect, and that the harmful ones worked by anchoring the agent on their own template and overriding the task's explicit instructions - so "it always follows my skill" is not evidence of value.

Keep the usefulness questions **and** the removal test. They answer different questions: the first asks
whether a reader can find things, the second whether the thing should be there at all.

## 9. Keep the Loaded Head Stable

Where a runtime re-sends skill names, descriptions, or an invoked body every session, that text is part
of a reused prompt prefix, and an edit to it invalidates the cached reuse. So split by **stability** as
well as by length: stable contract text in `SKILL.md`, fast-moving provider detail, dates, counts, and
version pins in `references/` or at the bottom of a file. The placement rules are in
`rules/resource-placement.md` §8a.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The 500-line and 5,000-token progressive-disclosure budgets, the removal test behind `SK-D-1` and `SK-D-2`, the gotchas placement rule, and the conditional read-cue example | <https://agentskills.io/skill-creation/best-practices> |
| ~100 tokens of metadata per skill, the under-5k-token body, and script output as the only context cost of a script | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview> |
| An invoked skill's body kept in context across later turns without a re-read | <https://code.claude.com/docs/en/skills> |
| The 92-of-98 no-effect result and the template-anchoring failure behind `SK-D-3` | <https://arxiv.org/abs/2603.15401> |
| Splitting by stability and keeping the loaded head stable | `instructions/cache/CACHE.md` §3 |
| The three-stage model (metadata, then full instructions, then referenced files) | <https://agentskills.io/specification> |
| The one-level-deep reference rule and the partial-read reason for it | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> |
| The table-of-contents rule for reference files longer than 100 lines | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> |
| The 300-line repository gate and its scope | `scripts/check-sources.sh` (`MAX_LINES=300`, `DOC_SCOPE="instructions"`) |

### Evidence grade

This file is the **canonical** statement of the disclosure budgets; `rules/skill-anatomy.md` points here
rather than restating them. The 500-line and 5,000-token figures are `PRIMARY` - the specification states
them. The 300-line value is a repository gate, labelled as such and never presented as sourced.
