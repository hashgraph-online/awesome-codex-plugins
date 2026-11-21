---
name: wiring-contract
description: "Derive this project's own integration conventions from what the code already does, draft them as a wiring contract, and hold new work to it. Closes the built-but-not-wired gap at L3 (walking skeleton) — a mechanism that ships and is never called reads green in every other check."
metadata:
  instruction_budget: "38"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Wiring Contract

Answer one question for this project and then keep answering it automatically: **when something is built here, what does it have to be connected to before it counts as done?**

The failure is not carelessness, it is structural. A model's context makes it unable to see whether the element it just generated is referenced anywhere else, so plausible-but-unreferenced code is the *expected* output. Across 304,362 verified AI-authored commits in 6,275 repositories, "unused variables or parameters" is the second most frequent issue class, and "undefined variable or reference" — writer and reader disagreeing about a name or path — is the most common runtime bug category. It does not wash out: AI-authored code survives **longer** than human-written code (53.9% vs 69.3% line death rate), so an orphan is *less* likely to be cleaned up than a human's.

Every ordinary signal misses it. Tests pass, coverage rises, lint is clean, review approves — because each of those verifies a thing **against itself**, and wiring is a property of a **pair**.

## When to Use

- **At L3, before implementation** — the walking-skeleton obligation (G-V13). A design is not complete until its joins are named.
- On an existing project, once, to discover what conventions it already has.
- After a structural change (new directory, new layer, a move) — **regenerate**, never hand-edit.
- When `check_wiring_contract.py` reports UNGOVERNED files you did not expect.

## Workflow

### 1. Detect — read the repo's own majority convention

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_wiring_contract.py" --root . --detect
```

This proposes a rule only where the repo **already** behaves that way, and records the evidence:

```yaml
- id: wc-002
  pattern: "scripts/*.py"
  obliges:
    - referenced_by: ["**/*"]
  detected_from: "18 of 20 files already satisfy this"
  confidence: 0.90
```

A rule without observed support is a preference, not a contract. Two obligation types exist and that is deliberate — `referenced_by` (something outside the file references it, by import, invocation, path, or a glob that matches it) and `sibling_reference` (a same-directory barrel or registry lists it). Nine specific obligations rot; two general ones that always run do not.

### 2. Review with the human — this is a draft, not a finding

Present the proposal and ask, per rule, in plain language: *"18 of 20 scripts here have a caller. Should that be required?"* Watch for two failure shapes:

- **A majority that is an accident.** Four files in a directory that happen to be referenced does not make referencing them a rule. Ask what the directory is *for*.
- **A convention the detector cannot see.** Files invoked by reflection, by a registry built at runtime, or by a config string are wired and will look orphaned. These need an exemption **with a reason** — and "it is hard to check" is not one.

Write the confirmed contract to `.claude/harness/wiring-contract.yml`. Per the evidence-writes rule, the contract is a **human-confirmed draft**, never written unattended.

### 3. Enforce — and put it where the agent will feel it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_wiring_contract.py" --root .
```

Per **G-V14**, add this to the command run after *every change*, not only to CI. Agents respond to automated signals far more reliably than to documentation: a failing command gets fixed, a guardrail paragraph in the context window may not be read at all.

### 4. Read the UNGOVERNED count — it is the load-bearing number

Files matching no rule are listed with a count. **Zero violations across a governed subset is not zero violations.** A clean report beside 300 ungoverned files describes the health of a fraction while implying the whole — the precise false green this skill exists to end. Either extend coverage or state why those files are outside it.

## Output

- Creates/updates: `.claude/harness/wiring-contract.yml` (human-confirmed)
- Reports: violations, and the ungoverned count
- Feeds: `/mycelium:definition-of-done` (G-V14 verification block), `/mycelium:bvssh-check` (CALMS Automation `wiring_integrity`)

## Theory Citations

- **Cockburn — walking skeleton**: "a tiny implementation of the system that performs a small end-to-end function… it should link together the main architectural components." Wiring exists before features.
- **Hunt & Thomas — tracer bullets**: the same instinct, framed as end-to-end feedback first.
- **Ford, Parsons, Kua — architecture fitness functions**: objective, continuously-executed measures of properties the design must preserve. This check is one, and belongs in the pipeline rather than in a review checklist.

## Deliberately NOT a catalogue

Mycelium does not ship a list of integration points to check. A sibling project hand-listed 4 component and 9 plugin integration points; such a list is stale the moment someone adds the tenth, and hand-enumerated scope is the origin of this entire failure family. The rules here are derived from the project in front of you, and regenerated when it changes.
