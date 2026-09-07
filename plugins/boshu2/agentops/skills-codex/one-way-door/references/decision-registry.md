# Decision registry (layer 1, primary)

Declared reversibility for decisions AgentOps skills raise repeatedly. A row here
outranks every inferred signal, because the classification survives rewording.

**Adding a row.** Pick a stable id `<skill>-<what-it-decides>`. Declare `door`.
State `undo_cost` concretely — what specifically cannot be recovered — not a
category. A row whose `undo_cost` reads "data loss" is not yet a row; say which
data and why a restore does not cover it.

**Scope.** This registry covers decisions raised *by AgentOps skills*. Consumer
repositories declare their own; nothing here assumes a particular deploy
pipeline, tracker, or branch policy.

| id | skill | door | undo_cost |
|---|---|---|---|
| `plan-acceptance-change` | plan | two-way | Acceptance is caller-owned text; edit it again |
| `plan-scope-widen` | plan | two-way | Narrowing scope later costs one re-plan |
| `plan-write-scope-expand` | plan | one-way | Work already written outside the original scope cannot be un-attributed to the experiment; the subject identity changes |
| `implement-abandon-red` | implement | two-way | The failing test stays in the tree |
| `implement-subject-mutation` | implement | one-way | A subject mutated mid-experiment invalidates every prior check against it; the run restarts, not resumes |
| `validate-persist-verdict` | validate | one-way | A persisted `verdict.v2` is standalone evidence a downstream consumer may already have read |
| `validate-override-not-proven` | validate | one-way | Recording PASS over NOT_PROVEN destroys the distinction the corpus is built on |
| `validate-disclose-not-checked` | validate | two-way | Adding a disclosure is always safe; the answer is disclose |
| `council-adopt-panel-over-caller` | council | one-way | See the user challenge packet — never auto-decided at any confidence |
| `premortem-proceed-with-named-risk` | premortem | two-way | The risk stays named in the report either way |
| `rpi-second-control-artifact` | rpi | one-way | A second control artifact with no implementation evidence ends the run by contract; continuing past it spends the run |
| `skill-retire` | skill-builder | one-way | Downstream callers pinning the slug break; the trigger surface is claimed by nothing |
| `skill-catalog-regen` | skill-builder | two-way | Regenerate again from source |
| `dcg-authorize-blocked-command` | dcg | one-way | The guard exists because the command is not recoverable; authorizing it is the action |
| `agent-mail-break-reservation` | agent-mail | one-way | Another lane's in-flight edit is overwritten and that lane has no signal it happened |
| `swarm-dispatch-packet` | swarm | two-way | An undispatched packet can be redispatched; a dispatched one is bounded by its own write scope |
| `handoff-overwrite-artifact` | handoff | two-way | Prior handoff content is in git history |

## Unregistered decisions

Decisions raised without a row fall to layer 2 (effect class) and layer 3
(patterns). When the same ad-hoc decision appears three times across sessions,
promote it to a row here rather than widening a pattern — a pattern that grows to
cover one specific decision starts firing on unrelated ones.
