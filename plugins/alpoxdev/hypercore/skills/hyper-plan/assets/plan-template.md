# <slug> - Work Plan

## TL;DR

- What you get: <the outcome in one line>
- Why this approach: <the evidence-backed reason>
- What it will not do: <the refused additions>
- Effort: <Quick | Short | Medium | Large | XL>
- Risk: <concrete risks, including a dirty worktree when present>
- Decisions made for you: <each adopted default and its reversibility>

## Scope

### Affected user and ideal state

Affected user: <who>, today <how they use it>, after <how they use it>.

| ID | Property or gap | Why it matters |
|---|---|---|
| IS-1 | <property of the state where nothing snags or regresses> | <reason> |
| GAP-1 | <difference between that state and today> | <reason> |

### Must have

- <required outcome>

### Must NOT have

- <addition the plan refuses>

## Verification strategy

<test levels, exact commands, real-surface checks, adversarial classes that apply>

## Execution strategy

### Wave 1

- Todos <numbers>

| Todo | Depends on | Wave | Write scope |
|---|---|---|---|
| 1 | none | 1 | <paths> |

## Todos

- [ ] 1. <title>
  Wave: 1
  Depends on: none
  Write scope: <exact paths or globs>
  References: <paths with line anchors, documentation URLs>
  Acceptance: <literal command and expected result>
  QA happy: <tool, exact invocation, binary observable>; evidence: <path>
  QA failure: <tool, exact invocation, binary observable>; evidence: <path>
  Commit: <message in the repository's convention>
  Tier: <low | medium | high> - <one-line reason>

## Final verification wave

- [ ] F1. Plan compliance audit
- [ ] F2. Code quality review
- [ ] F3. Real-surface QA
- [ ] F4. Ideal-state fidelity (every IS row, 1:1)

## Commit strategy

<one commit per todo, message convention, evidence handling, wave landing>

## Success criteria

| IS row | Delivering todo(s) | Proving QA | Evidence path |
|---|---|---|---|
| IS-1 | 1 | <check> | <path> |

## Handoff

- Auto-execute: <yes | no (reason)>
- Delivery: <local | make-pr | ship>
- Plan-only requested: <yes | no>

<!-- Copy to .hyper/plans/<slug>.md, replace every <placeholder>, and keep the headings verbatim. -->
