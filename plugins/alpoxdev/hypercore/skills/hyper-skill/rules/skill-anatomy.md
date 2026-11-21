# Skill Anatomy

**Purpose**: Define the minimum shape and responsibility split for a high-quality skill.

## 1. Minimum Anatomy

A skill starts with `SKILL.md` and may include support files only when they improve triggerability, reliability, reuse, or validation.

Recommended shape:

```text
skill-name/
├── SKILL.md
├── SKILL.ko.md
├── rules/
├── references/
├── scripts/
├── assets/
└── agents/
```

| Element | Requirement | Responsibility |
|---|---|---|
| `SKILL.md` | Required | Metadata, trigger, core execution contract, workflow, validation |
| `SKILL.ko.md` | Repo convention | Korean mirror for local/user-facing use |
| `rules/` | Conditional | Reusable policy, decision criteria, validation checklists, anti-patterns |
| `references/` | Conditional | Official summaries, detailed knowledge, schemas, edge cases, long examples |
| `scripts/` | Conditional | Deterministic helpers, validators, formatters, data transforms |
| `assets/` | Conditional | Templates, fixtures, schemas, static output resources |
| `agents/` | Conditional | Runtime metadata only when a runtime consumes it - for example Codex `agents/openai.yaml` (UI text, invocation policy, tool dependencies) |

## 2. Frontmatter

```yaml
---
name: skill-name
description: Use this skill when the user asks to ... Do not use for ...
compatibility: Optional runtime/dependency requirements.
---
```

Rules:

- `name` is lowercase kebab-case and **must match the parent directory name**.
- `description` is trigger guidance, not marketing copy, and states both what the skill does and when to use it.
- `compatibility` is optional and mentions real runtime, network, package, tool, or permission constraints.
- Implementation-specific fields such as tool allowlists are optional and must not replace the core instructions.

## 2a. Portable Core, Documented Extensions

The base states this as `SK-P-3` (Portable core, documented extensions): the six specification fields
carry the contract, and any runtime-only frontmatter is labelled with its runtime and must not be
load-bearing.

In practice: a reader on another runtime must still be able to trigger and run the skill from the six
spec fields and the body alone. When a runtime-only field is used, name its runtime where it appears, and
restate anything it enforces (manual invocation, tool limits, path limits) in the skill's own contract.

| Runtime | Extension | Effect |
|---|---|---|
| Claude Code | `when_to_use` | Appended to `description` in the listing; counts toward the 1,536-character entry cut |
| Claude Code | `argument-hint`, `arguments` | Autocomplete hint and named `$name` substitution |
| Claude Code | `disable-model-invocation`, `user-invocable` | Turns off automatic or manual invocation respectively |
| Claude Code | `allowed-tools`, `disallowed-tools` | Adds or removes tools for the invoking turn only |
| Claude Code | `model`, `effort`, `context`, `agent`, `background` | Model/effort override; `context: fork` runs the skill in a subagent |
| Claude Code | `hooks`, `paths`, `shell` | Session hooks on invocation, path-glob activation limit, inline-shell choice |
| Codex | `agents/openai.yaml` (a file, not frontmatter) | `interface` text and icons, `policy.allow_implicit_invocation`, `dependencies.tools` |

The full field behaviour is in `references/official/anthropic.md` and `references/official/openai.md`.

## 3. Frontmatter Constraints

Every constraint below comes from the specification and is enforced where a gate exists.

| Field | Required | Constraint |
|---|---|---|
| `name` | Yes | 1-64 characters. Lowercase letters, digits, and hyphens only. Must not start or end with a hyphen. Must not contain consecutive hyphens. **Must match the parent directory name** |
| `description` | Yes | 1-1024 characters, non-empty. States what the skill does and when to use it |
| `license` | No | A license name or a reference to a bundled license file |
| `compatibility` | No | **1-500 characters if provided.** Only when environment requirements exist |
| `metadata` | No | A string key-value map for properties the spec does not define |
| `allowed-tools` | No | A space-separated string of pre-approved tools. **Experimental** |

Two notes that are easy to get wrong:

- The `compatibility` lower bound of 1 **is** stated by the specification: "Must be 1-500 characters if
  provided". Treat the field as bounded on both ends.
- `name` matching the parent directory is a **spec requirement**, not a stylistic preference. A rule that
  softens this into a best-effort preference is weaker than the standard it claims to implement.

## 4. Claude-Specific Constraints

Claude adds constraints on top of the specification. A skill that violates these is not portable to it:

- `name` cannot contain XML tags and cannot contain the reserved words **"anthropic"** or **"claude"**.
- `description` cannot contain XML tags.
- Descriptions are written in **third person**. The field is injected into a system prompt, so a
  description that shifts point of view causes discovery problems.
- Gerund-form names (verb + `-ing`) are the recommended convention. Noun phrases and action-oriented
  names are acceptable; vague names such as `helper`, `utils`, or `tools` are not.

Also worth carrying: on the claude.ai upload and Skills API path, only the six standard fields are
allowed and an extra field is a **hard error**, not a silently ignored key. Claude Code itself ignores an
unknown field without an error, so a skill can look fine locally and still fail to upload. A skill that
relies on Claude Code extension fields is a Claude Code skill, not a portable one (SK-P-3).

## 5. What `allowed-tools` Actually Does

State this precisely in both directions, because both halves are easy to get wrong:

- It is a **permissive grant**: Claude Code documents it as the tools Claude can use **without asking
  permission during the turn that invokes the skill**, and the grant clears on the next message. So it
  has a real effect.
- It is **not a restrictive boundary**. It does not stop the agent from using other tools, and it does
  not replace an independent permission or safety gate. The specification labels the field Experimental,
  and a second runtime records it as parsed but not enforced.

The accurate conclusion is therefore neither "it has no effect" nor "it is a security control": it is a
convenience grant, and side-effect gating must be stated in the skill's own contract.

## 6. First-Line Rule and Discovery

**The frontmatter is only read when the opening `---` is the file's first line.** Otherwise the whole
file, `---` markers included, is treated as skill content, and the skill loses its discovery metadata
silently while still being loadable by name.

This is already enforced by both repository gates, so it needs stating rather than new tooling:

- `validate-hyper-skill.sh` resolves frontmatter with an anchor that requires `---` at the start of the
  file, so a blank first line makes the block unfindable and the gate reports `FRONTMATTER_NAME`,
  `FRONTMATTER_DESCRIPTION`, and `FRONTMATTER_TRIGGER`.
- `validate-skills-corpus.sh` reports `FRONTMATTER_MISSING`.

The listing budgets that decide whether a description is seen at all are stated once, in
`rules/trigger-design.md` §6.

Two discovery facts differ by runtime and change how a package is shipped:

- Codex reads `.agents/skills` in every directory from the working directory up to the repository root,
  plus user, admin, and bundled locations; two skills with the same `name` are **not merged** and both
  can appear.
- Claude Code keeps an invoked skill's body in context across later turns and does not re-read the
  file, so an edit made mid-session is not seen until the skill is invoked again in a new session.

## 7. Minimum Core Contract

A non-trivial `SKILL.md` should expose:

- output language contract
- purpose
- routing rule
- instruction contract
- activation examples
- trigger conditions or supported targets
- skill architecture or resource model
- workflow
- support-file read order or navigation cues
- required and forbidden behavior
- validation checklist

The instruction contract should make these discoverable: intent, trigger, scope, authority, evidence, tools, output, verification, and stop condition.

## 8. What Belongs in `SKILL.md`

Keep these in the core skill:

- what the skill does
- when to use it and when not to use it
- what outputs or transformations it should produce
- the high-level workflow
- essential authority, safety, and stop-condition boundaries
- pointers to deeper rules or references

Do not turn the core skill into a full knowledge base. The budgets live in
`rules/progressive-disclosure.md`, which is their canonical statement; this file does not restate them.

## 9. Language and Mirror Pairing

Write canonical skill markdown in English by default, but require generated user-facing artifacts to default to Korean.

Whenever you create or materially update a markdown file inside a skill folder, maintain a Korean sibling translation:

- `SKILL.md` pairs with `SKILL.ko.md`
- `rules/name.md` pairs with `rules/name.ko.md`
- `references/path/name.md` pairs with `references/path/name.ko.md`

Keep headings, section order, links, and examples structurally aligned across the pair unless localization requires minor wording changes. Keep the `## Sources` heading in English in both files, because the parity gate matches that heading literally; translate `###` subheadings and field values freely.

## 10. Quality Gate

- [ ] `SKILL.md` explains the skill without reading every support file.
- [ ] Frontmatter supports discovery and trigger selection.
- [ ] `name` matches the parent directory name exactly.
- [ ] Contract fields are discoverable: intent, trigger, scope, authority, evidence, tools, output, verification, stop.
- [ ] Rules hold policy, not bloated reference detail.
- [ ] References hold detail, not core trigger logic.
- [ ] Scripts/assets exist only when justified and documented.
- [ ] Optional metadata is intentionally present or intentionally omitted.
- [ ] Every runtime-only field is labelled with its runtime, and the skill still reads and triggers correctly without it (SK-P-3).
- [ ] `allowed-tools`, when used, is not presented as a safety boundary.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| The frontmatter field table and every constraint in it, and the required/optional split | <https://agentskills.io/specification> |
| The XML-tag and reserved-word constraints on `name`, the XML-tag constraint on `description`, third-person descriptions, and the gerund naming convention | <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices> |
| The six standard fields, the Claude Code extension list, the hard error for non-spec fields on the upload/API path, Claude Code ignoring unknown fields, the first-line rule, and the in-context lifecycle of an invoked skill | <https://code.claude.com/docs/en/skills> |
| `agents/openai.yaml`, the `.agents/skills` walk, and same-`name` non-merging | <https://learn.chatgpt.com/docs/build-skills> |
| `allowed-tools` as a permissive grant for the invoking turn rather than a restrictive boundary | <https://code.claude.com/docs/en/skills> |
| `allowed-tools` observed as parsed but not established as an enforceable permission boundary | <https://github.com/alpoxdev/hypercore/blob/01be78de5973eb75a616e5156058621a6fabbc97/instructions/cli/jcode/README.md> |
| `SK-P-3` | `instructions/skill/SKILL_AUTHORING.md` |
| The gate that already enforces the first-line rule | `skills/hyper-skill/scripts/validate-hyper-skill.sh` |

### Evidence grade

The frontmatter constraints are `PRIMARY` - the specification states them. The Claude additions, the
extension fields, and the discovery facts are `VENDOR` - each vendor's statement about its own product.
