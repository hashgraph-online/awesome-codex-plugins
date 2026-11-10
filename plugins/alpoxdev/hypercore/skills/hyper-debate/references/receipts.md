# Receipts

Read this before the first dispatch and whenever a returned receipt must be validated. It owns the exact shape of every receipt, the ledger, and the approval record.

Every receipt is a JSON file written under `.hyper/debate/<slug>/`, one per perspective per round. The assignment includes the round's schema verbatim so the perspective never guesses.

## Contents

1. Common rules
2. Round 1 receipt
3. Round 2 receipt
4. Round 3 receipt
5. Ledger
6. Approval record
7. Validation checklist

## 1. Common Rules

- One file per perspective per round: `round1/<perspective>.json`, `round2/<perspective>.json`, `round3/<perspective>.json`.
- The perspective ids are exactly `skeptic`, `validator`, `researcher`, `architect`, `creative`.
- Every receipt names its `perspective` and its `round`. A receipt whose identity does not match the assignment is invalid, even when its content is good.
- Every nested object disallows additional properties. Extra keys mean the perspective invented a field; reject the receipt.
- A citation is one of: `path:line`, an official URL, `user: <quoted statement>`, or `no evidence found`. A fabricated citation invalidates the finding.
- Prose inside a receipt is Korean by default; ids, verdicts, and field names stay English.

## 2. Round 1 Receipt

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [1]},
    "findings": {
      "type": "array", "minItems": 3, "maxItems": 7,
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "claim": {"type": "string"},
          "evidence": {"type": "array", "minItems": 1, "items": {"type": "string"}}
        },
        "required": ["id", "claim", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "findings"], "additionalProperties": false
}
```

Check on return: 3-7 findings, ids prefixed with the perspective, at least one evidence string per finding, and no duplicate id across the run.

## 3. Round 2 Receipt

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [2]},
    "critiques": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "targetFindingId": {"type": "string"},
          "verdict": {"type": "string", "enum": ["ATTACK", "STANDS"]},
          "reason": {"type": "string"},
          "evidence": {"type": "array", "minItems": 1, "items": {"type": "string"}}
        },
        "required": ["targetFindingId", "verdict", "reason", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "critiques"], "additionalProperties": false
}
```

Check on return, per receipt: exactly one judgment for every finding belonging to the other four perspectives, no unknown target id, no self-judgment, and a nonempty reason on every `STANDS`.

## 4. Round 3 Receipt

```json
{
  "type": "object",
  "properties": {
    "perspective": {"type": "string", "enum": ["skeptic", "validator", "researcher", "architect", "creative"]},
    "round": {"type": "integer", "enum": [3]},
    "responses": {
      "type": "array", "minItems": 3, "maxItems": 7,
      "items": {
        "type": "object",
        "properties": {
          "findingId": {"type": "string"},
          "verdict": {"type": "string", "enum": ["DEFEND", "REFINE", "CONCEDE"]},
          "survivingClaim": {"type": ["string", "null"]},
          "reason": {"type": "string"},
          "evidence": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["findingId", "verdict", "survivingClaim", "reason", "evidence"], "additionalProperties": false
      }
    }
  },
  "required": ["perspective", "round", "responses"], "additionalProperties": false
}
```

Check on return: one response per own finding, a nonempty `survivingClaim` and nonempty `evidence` for `DEFEND` and `REFINE`, and a null `survivingClaim` for `CONCEDE`. The `reason` addresses every attack recorded against that finding.

## 5. Ledger

`.hyper/debate/<slug>/ledger.json` is a single JSON object. It is written incrementally, not once at the end.

```json
{
  "request": {"verbatim": "", "optIn": "", "scope": [], "outcome": ""},
  "slug": "",
  "mode": "full | bundle-only | review",
  "execution": "parallel | sequential",
  "reduced": false,
  "reducedReason": null,
  "grounding": [{"path": "", "note": ""}],
  "waves": [
    {"round": 1, "perspectives": [{"id": "skeptic", "job": "", "attempt": 1, "receipt": "round1/skeptic.json"}]}
  ],
  "findings": [
    {
      "id": "skeptic-1",
      "perspective": "skeptic",
      "claim": "",
      "evidence": [""],
      "critiques": [{"by": "validator", "verdict": "ATTACK", "reason": ""}],
      "response": {"verdict": "REFINE", "survivingClaim": "", "reason": ""},
      "decision": "keep | refine | open-question | drop",
      "decisionReason": ""
    }
  ],
  "surviving": {"skeptic": 0, "validator": 0, "researcher": 0, "architect": 0, "creative": 0},
  "dropped": {"skeptic": 0, "validator": 0, "researcher": 0, "architect": 0, "creative": 0},
  "openQuestions": [{"question": "", "why": "", "gates": []}],
  "approval": {"requestedAt": "", "request": "", "decidedAt": null, "decision": null},
  "terminal": "planned | awaiting-approval | reduced-planned | declined | blocked",
  "notes": []
}
```

## 6. Approval Record

The approval request and its answer live in the ledger under `approval`, and the presented text is saved at `.hyper/debate/<slug>/approval.md` so the reader can see exactly what was approved.

```markdown
# <slug> - Approval

## Decisions presented
- <decision>

## Risks and mitigations
- <risk> -> <mitigation>

## Open questions
- <question> -> <who must decide>

## Asked
<the exact question put to the user>

## Decision
<the user's answer, verbatim, or `no answer`>
```

An empty or missing `## Decision` body means no approval.

## 7. Validation Checklist

Before advancing past any round:

- [ ] Five receipts exist for the round, one per perspective.
- [ ] Each receipt's `perspective` and `round` match its filename and the assignment.
- [ ] No receipt carries a key outside its schema.
- [ ] Round 1: 3-7 findings each, every finding cited, ids unique across the run.
- [ ] Round 2: full coverage of other-perspective findings, no self-judgment, no unknown id, a reason on every `STANDS`.
- [ ] Round 3: one response per own finding, evidence on every `DEFEND`/`REFINE`, a null claim on every `CONCEDE`, every attack addressed.
- [ ] The ledger records the wave identities, attempts, and receipt paths.

## Sources

> Checked 2026-11-10.

| Claim | Source |
|---|---|
| The round-1, round-2, and round-3 receipt schemas | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (mechanism reference, re-authored) |
| Coverage over schema as the round-2 check, and the own-finding check in round 3 | `dbc-hbin/omp-ulw@74df40f hyperplan/references/rounds.md` (mechanism reference, re-authored) |
| The ledger fields, the approval record, and the validation checklist | this package's chosen design, 2026-11-10 (issue #26) |

### Evidence grade

`LOCAL` - the schemas are re-authored from a repository with no license; no text or code is copied. The ledger, approval record, and checklist are this package's design.
