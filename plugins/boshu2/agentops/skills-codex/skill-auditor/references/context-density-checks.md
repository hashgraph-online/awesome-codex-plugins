# Advisory Context Density Checks

This reference defines the skill-auditor density block. It is report-only.
It helps reviewers find skill prose that does not carry one of the six Context
Density Rule fields before that prose is passed into a fresh context session.

## Fields

| Field | Meaning | Advisory signals |
|---|---|---|
| `intent` | What behavior or capability the skill is trying to produce | intent, goal, behavior, capability |
| `boundary` | Where the work starts/stops | boundary, bounded context, write scope, non-goal |
| `evidence` | How the skill knows work is true or complete | evidence, test, verdict, validation, acceptance |
| `decision` | Why this approach was chosen | decision, rationale, why, because, chosen |
| `constraint` | Limits, safety rails, and non-negotiables | constraint, guardrail, limit, scope |
| `next_action` | The next command, artifact, or handoff | next action, next steps, completion marker |

## Behavior

- Missing fields produce `density.status: "warn"`.
- Missing fields do not change the aggregate audit verdict.
- Missing fields are not CI failures.
- False positives should be recorded as findings or bead notes before any check
  is promoted.
- This check does not satisfy execution-packet enforcement. The packet-boundary
  invariant is owned by `soc-2c1p.1`.

## Runnable Examples

```bash
bash skills/skill-auditor/scripts/audit.sh skills/discovery
bash skills/skill-auditor/scripts/audit.sh skills/plan
bash skills/skill-auditor/scripts/audit.sh skills/crank
bash skills/skill-auditor/scripts/audit.sh skills/validation
```

The expected result is a JSON `density` object with six `fields[]` entries. The
field count is the contract; the individual pattern matches are advisory.
