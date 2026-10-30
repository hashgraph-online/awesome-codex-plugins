# threat-model.md template

Use these sections in this order. Replace bracketed text. Delete guidance lines. Keep threat IDs (`T1`, `T2`, ...) stable across revisions; when a threat is removed, mark it "withdrawn" with a reason instead of reusing its number.

---

```markdown
# Threat model: [subject]

Status: [draft | reviewed | superseded by ...]
Last updated: [YYYY-MM-DD] against commit [short hash]
Plan: [relative link, or "none"]

## Scope

In scope: [components, endpoints, agents, stores]

Out of scope: [items, each with a reason]

Security goals:
- [actor] must not be able to [action] on [asset].

## Data flow

[Mermaid flowchart. Trust zones as subgraphs. Label edges with the data that moves. Mark boundary-crossing edges.]

Boundary crossings:
| ID | From | To | Data | Control at crossing (file:line or "none") |
| --- | --- | --- | --- | --- |

## Assets

| Asset | Sensitivity | Lives at | Legitimate readers / writers |
| --- | --- | --- | --- |

## Entry points

| Entry point | Who controls the data | Reaches | Agent-specific? |
| --- | --- | --- | --- |

## Attackers

| Attacker | Starting position | Can | Cannot |
| --- | --- | --- | --- |

## Threats

| ID | Threat | Likelihood | Impact | Status |
| --- | --- | --- | --- | --- |
| T1 | [one line] | [H/M/L] | [H/M/L] | [open / mitigated / accepted] |

### T1: [title]

Category: [STRIDE letter and/or agent threat name]

Abuse path:
1. [attacker] [does what] at [entry point, file:line]
2. [hop, file:line]
3. [asset reached and effect]

Likelihood: [H/M/L], because [reason].
Impact: [H/M/L], because [reason].

Mitigation: [the change, and the point on the path it breaks]

Proof: [test kind]: [one-sentence assertion]. Location: [test path, or "to be written in plan step N"].

[Repeat for each threat at medium or above.]

## Accepted risks

- [T#]: [one line on why it is accepted and who accepted it]

## Gaps

- [anything not mapped, and why]

## Open questions

- [question, and who can answer it]
```
