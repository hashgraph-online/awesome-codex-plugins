# Self-Containment

**Purpose**: Keep a skill usable from its own folder alone, so no other skill has to be installed, invoked, or present for the skill to work.

A skill is a distribution unit. If it points at another skill - by name, by path, or by requiring that skill's command to run - then a reader who installs only this skill gets a dangling instruction. The fix is never "install the neighbor too"; it is to bring what is needed into this folder or to describe the boundary without naming the neighbor.

## 1. Normative Rules

- SK-S-1: A skill is whole with its own folder. It must not require another skill's installation, invocation, path, or documents. When content from elsewhere is genuinely needed, copy it into this skill's own `references/` as a local snapshot instead of pointing at the other artifact. A repository-maintenance command that contains another skill's path is a representative case: it does not belong in the skill artifact at all, because repository policy documents own it.
- SK-S-2: Describe boundaries by output shape, not by neighbor name. "Use this skill when the output is a reusable skill folder; general documents, runbooks, prompts, and plans are out of scope" keeps the trigger boundary intact without naming another skill. Naming a neighbor creates a reference the reader cannot resolve.
- SK-S-3: A user instruction is the only exception. When the user explicitly asks for a cross-skill reference, run the check with `--allow <sibling-name>` for that name, keep the finding visible as a warning, and record the instruction in the task record. The exception never becomes the default.

## 2. Detection Rules

`skills/hyper-skill/scripts/validate-hyper-skill.sh` carries `checkSelfContainment`, which scans a package's text files for:

- a hyphenated sibling skill name as a bare or backticked token, with boundaries that exclude longer identifiers, so an extended name is not misread as its prefix;
- any sibling skill name in `$<name>` invocation form;
- any sibling skill name as a `skills/<name>/` path segment.

Sibling names come from the directories beside the package root; a directory counts only when it carries a `SKILL.md`. In the default mode the check reports errors for a package that adopts this contract and warnings for any other package. `--require-self-containment` promotes findings to errors regardless of package name, which is the mode to use on a skill this authoring skill has just produced, and it also widens the path rule: any `skills/<name>/` path other than the package's own is reported even when that skill is not installed beside this package, so a standalone or moved package is still caught. The `$<name>` form stays sibling-based in both modes, because vendor runtime built-ins use the same syntax. `--allow <sibling-name>` (repeatable) records a user-directed exception.

## 3. Limitations

- A single-word sibling name is not detectable as prose or in backticks, because it is indistinguishable from an ordinary word that also appears as a capability name. Only its `$<name>` and `skills/<name>/` forms are detected. Authors avoid the prose form by hand.
- Detection reads text, so it cannot see a reference that is assembled at run time from fragments.
- The check proves the absence of the shapes it knows. It does not prove that the skill works alone; that still needs the skill to be read and run on its own.

## Sources

> Links checked 2026-09-21.

| Claim | Source |
|---|---|
| The self-containment requirement, the output-shape boundary rule, and the user-instruction-only exception | user instruction, 2026-09-21 |
| The detection rules, the `--require-self-containment` and `--allow` flags, and the sibling-name discovery | `skills/hyper-skill/scripts/validate-hyper-skill.sh` |
| One canonical home per rule and a lean core, which is why this rule lives in one file instead of being restated in the core | `rules/progressive-disclosure.md` |

### Evidence grade

`LOCAL` - this rule states repository policy and a user instruction. It is not an external claim, and no vendor source is cited for it.
