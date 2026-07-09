# NTM Robot Mode

Use this file when you need the deeper, structured automation side of NTM.

## Contents

- [Output Formats](#output-formats) — `--robot-format`, env fallbacks, verbosity
- [Start Here](#start-here) — discovery, capabilities, schema
- [Canonical Operator Loop](#canonical-operator-loop)
- [Attention Feed](#attention-feed) — snapshot, events, digest, wait, overlay
  - [Attention Profiles](#attention-profiles)
  - [Wait Conditions](#wait-conditions)
- [Core Robot Actions](#core-robot-actions) — send, ack, tail, inspect
  - [Safe Restart Pattern](#safe-restart-pattern)
  - [Assignment and Routing](#assignment-and-routing)
  - [Context and Health](#context-and-health)
  - [Files, Replay, Support](#files-replay-support)
- [Beads, Mail, and CASS](#beads-mail-and-cass)
- [Human-Friendly Robot Views](#human-friendly-robot-views)
- [Full `--robot-*` Flag Index](#full---robot--flag-index) — grouped with `root.go` line refs
  - [Discovery / docs](#discovery--docs)
  - [State / snapshots / formats](#state--snapshots--formats)
  - [Events / attention](#events--attention)
  - [Pane inspect / tail / watch](#pane-inspect--tail--watch)
  - [Activity / health / diagnose](#activity--health--diagnose)
  - [Control / mutate](#control--mutate)
  - [Sessions / spawn / controller](#sessions--spawn--controller)
  - [Assign / route / distribute](#assign--route--distribute)
  - [Work / beads / bv](#work--beads--bv)
  - [Pipeline](#pipeline)
  - [Mail / coordination](#mail--coordination)
  - [CASS](#cass)
  - [Ensemble / modes](#ensemble--modes)
  - [Monitor / tools / bundle](#monitor--tools--bundle)
  - [Palette / recipes / setup / profile](#palette--recipes--setup--profile)
  - [Integrations](#integrations)

---

## Output Formats

| Flag | Meaning |
| --- | --- |
| `--robot-format=json` | Full JSON output |
| `--robot-format=toon` | More token-efficient structured output (prefer when context is tight) |
| `--robot-format=auto` | Auto-select current default |

Env fallbacks honored (in order): `NTM_ROBOT_FORMAT`, `NTM_OUTPUT_FORMAT`, `TOON_DEFAULT_FORMAT`.

Note: `--robot-output-format` is a **deprecated** alias — always use `--robot-format`.

Verbosity: `--robot-verbosity=terse|default|debug` (env `NTM_ROBOT_VERBOSITY`).

## Start Here

```bash
ntm --robot-help
ntm --robot-capabilities                 # machine-discoverable API schema (prefer this over --help)
ntm --robot-docs=quickstart              # topics: quickstart | commands | examples | exit-codes
ntm --robot-schema=all                   # JSON Schema for every robot response type
ntm --robot-status
ntm --robot-snapshot
ntm --robot-plan
ntm --robot-dashboard
ntm --robot-markdown --md-compact
ntm --robot-terse
```

`--robot-capabilities` is the canonical schema/discovery surface. Prefer it over
parsing human help text. `--robot-schema=all` lets you validate parsed responses.

## Response and Freshness Contract

Robot output is meant to be parsed mechanically:

- Treat `success=false` plus `error_code` as the control signal; do not scrape prose.
- Required list fields should be present as empty arrays when checked-and-empty.
- Optional fields are omitted when irrelevant; do not expect `null`.
- `timestamp`, `schema_version`, and `output_format` are part of the envelope on
  the newer surfaces.
- For derived views, read `sources` / `degraded_sources` warnings before acting.

Decision rule:

| Source status | Operator posture |
| --- | --- |
| fresh / healthy | Safe to act on the derived recommendation |
| stale but available | Act only if low-risk; annotate the stale source |
| degraded / unavailable | Prefer non-mutating previews; fall back to native tools (`br`, `bv`, mail MCP) |
| contradictory sources | Re-bootstrap with `--robot-snapshot`, then inspect the native source |

Do not turn a degraded source into a hard stop by default. NTM is designed to remain
useful when CASS, Agent Mail, or BV are partially unavailable, but mutating commands
should be held to a higher proof threshold.

## Canonical Operator Loop

```text
1. Bootstrap with ntm --robot-snapshot
2. Read latest cursor / attention summary
3. Tend with ntm --robot-attention or ntm --robot-wait
4. Act with ntm --robot-send, ntm send, ntm assign, ntm mail, or ntm locks
5. Repeat

If the cursor expires, re-run --robot-snapshot.
```

## Attention Feed

| Command | Purpose |
| --- | --- |
| `--robot-snapshot` | Bootstrap unified state plus attention summary and cursor handoff |
| `--robot-events` | Raw replay since a cursor |
| `--robot-digest` | Non-blocking attention-feed summary |
| `--robot-attention` | Wait-then-digest tending command |
| `--robot-overlay` | Human handoff / overlay actuator |
| `--robot-wait` | Wait for pane or attention conditions |

Example flow:

```bash
ntm --robot-snapshot
ntm --robot-events --since-cursor=42 --events-limit=50 --events-category=agent
ntm --robot-digest --profile=minimal
ntm --robot-attention --attention-cursor=42
ntm --robot-overlay=myproject --overlay-no-wait
```

### Attention Profiles

| Profile | Flag | Behavior |
| --- | --- | --- |
| `operator` | `--profile=operator` | Default operator-focused blend |
| `debug` | `--profile=debug` | Full verbosity |
| `minimal` | `--profile=minimal` | Only the most urgent items |
| `alerts` | `--profile=alerts` | Alert-centric view |

Explicit filters override profile defaults.

### Wait Conditions

Flag: `--wait-until` (alias `--condition`). Canonical set from `--robot-capabilities`:

Pane-oriented:

- `idle`
- `complete`
- `generating`
- `healthy`
- `stalled`
- `rate_limited`

Attention-oriented:

- `attention`
- `action_required`
- `mail_pending`
- `mail_ack_required`
- `context_hot`
- `reservation_conflict`
- `file_conflict`
- `session_changed`
- `pane_changed`

**Deliberately unsupported:** `bead_orphaned`. NTM refuses to emit this because abandonment
cannot be proven from observable pane/session state alone — emitting it would invent
conclusions from insufficient data. Do not try to wait on it; the command will reject.

Example:

```bash
ntm --robot-wait=myproject --wait-until=idle --timeout=5m
ntm --robot-wait=myproject --wait-until=action_required --attention-cursor=42
ntm --robot-wait=myproject --wait-until=mail_pending --attention-cursor=42
ntm --robot-wait=myproject --wait-until=reservation_conflict --attention-cursor=42
```

## Core Robot Actions

```bash
# Send and watch for response
ntm --robot-send=myproject --panes=2 --msg="Fix auth" --type=claude
ntm --robot-ack=myproject --timeout=30s                 # --ack-timeout/--ack-poll are deprecated aliases

# Inspect without retiling
ntm --robot-tail=myproject --panes=2 --lines=50
ntm --robot-inspect-pane=myproject --inspect-index=2
ntm --robot-inspect-session=myproject
ntm --robot-inspect-agent=myproject:2
ntm --robot-inspect-work=br-123
ntm --robot-inspect-coordination=<agent>
ntm --robot-inspect-quota=<provider>/<account>
ntm --robot-inspect-incident=<incident-id>
```

### Safe Restart Pattern

Raw `--robot-interrupt` is honest but blunt. Prefer the polite-probe-then-act pair:

```bash
# 1. Probe first
ntm --robot-is-working=myproject --panes=2,3        # returns structured working/idle state
ntm --robot-probe=myproject --panes=2                # responsiveness probe
ntm --robot-diagnose=myproject                       # comprehensive health + recommendations

# 2. Act with smart defaults that refuse to interrupt working agents
ntm --robot-smart-restart=myproject --panes=2        # safe — checks --robot-is-working first
ntm --robot-restart-pane=myproject --type=claude --dry-run

# 3. Only use raw interrupt when you've decided to override
ntm --robot-interrupt=myproject --panes=2 --msg="Stop and reconsider."
```

### Assignment and Routing

```bash
ntm --robot-assign=myproject --strategy=dependency
ntm --robot-bulk-assign=myproject --from-bv           # one-shot: assign bv top picks to idle agents
ntm --robot-route=myproject --strategy=affinity
```

### Context and Health

```bash
ntm --robot-context=myproject                         # context-window usage per agent (anticipate rotation)
ntm --robot-agent-health=myproject
ntm --robot-health=myproject
ntm --robot-health-oauth=myproject
ntm --robot-health-restart-stuck=myproject
ntm --robot-monitor=myproject --interval=30s
ntm --robot-metrics=myproject --metrics-period=1h
```

### Files, Replay, Support

```bash
ntm --robot-files=myproject --files-window=6h
ntm --robot-replay=myproject --replay-id=<id>
ntm --robot-support-bundle=myproject
ntm --robot-save=myproject
ntm --robot-restore=/path/to/snapshot.json
```

## Beads, Mail, and CASS

```bash
ntm --robot-beads-list --beads-status=open
ntm --robot-bead-show=br-123
ntm --robot-bead-claim=br-123 --bead-assignee=agent1
ntm --robot-bead-create --bead-title="..." --bead-type=task --bead-priority=2
ntm --robot-bead-close=br-123 --bead-close-reason="Completed"
ntm --robot-watch-bead=myproject                   # stream bead activity for a session

ntm --robot-mail                                    # machine-readable mail digest
ntm --robot-mail-check --mail-project=myproject --urgent-only
ntm --robot-context-inject=myproject                # inject mail + work context into panes

ntm --robot-cass-status
ntm --robot-cass-search="authentication error"
ntm --robot-cass-insights
ntm --robot-cass-context=<task-description>
```

Graph-aware triage (wraps bv):

```bash
ntm --robot-triage --triage-limit=10
ntm --robot-plan
ntm --robot-graph
ntm --robot-forecast=all
ntm --robot-impact=<path>
ntm --robot-search=<query>
ntm --robot-label-health
ntm --robot-label-flow
ntm --robot-label-attention
ntm --robot-file-beads=<path>      ntm --robot-file-hotspots      ntm --robot-file-relations=<path>
```

These are useful when a script or agent needs structured access to work state,
coordination state, or past-session search.

## Human-Friendly Robot Views

When JSON is too heavy but you still need automation-friendly output:

```bash
ntm --robot-markdown
ntm --robot-markdown --md-compact
ntm --robot-terse
```

Use `--robot-terse` for operator summaries. Use `--robot-markdown` when a human
or another model benefits from lower-token tables instead of raw JSON.

## Full `--robot-*` Flag Index

Grouped by purpose. All flag definitions live in `/dp/ntm/internal/cli/root.go` in the
range `3127-3612`. Token after each line = source-file line number.

### Discovery / docs

- `--robot-help` `3127`
- `--robot-status` `3128`
- `--robot-version` `3129`
- `--robot-capabilities` `3130`
- `--robot-docs=<topic>` `3131` — `quickstart|commands|examples|exit-codes`
- `--robot-schema=<type>` `3294` — `all` dumps every schema
- `--robot-default-prompts` `3426`

### State / snapshots / formats

- `--robot-snapshot` `3133`
- `--robot-terse` `3357`
- `--robot-markdown` / `--md-compact` `3366`
- `--robot-dashboard` `3193`
- `--robot-format=json|toon|auto` `3360`
- `--robot-output-format` `3363` (DEPRECATED)
- `--robot-verbosity=terse|default|debug` `3224`
- `--robot-limit N` / `--robot-offset N` `3222-3223`

### Events / attention

- `--robot-events --since-cursor=N --events-limit=M` `3135`
- `--robot-attention` `3146`
- `--robot-digest` `3147`
- `--robot-alerts` `3520`
- `--robot-dismiss-alert=<id>` `3510`
- `--robot-overlay` `3216`

### Pane inspect / tail / watch

- `--robot-tail=<session> --panes=N,M --lines=L` `3153`
- `--robot-watch-bead=<session>` `3154`
- `--robot-errors=<session>` `3156`
- `--robot-inspect-pane=<session> --inspect-index=N --inspect-lines=L --inspect-code` `3487`
- `--robot-inspect-session=<session>` `3491`
- `--robot-inspect-agent=<session:pane>` `3492`
- `--robot-inspect-work=<bead-id>` `3493`
- `--robot-inspect-coordination=<agent>` `3494`
- `--robot-inspect-quota=<provider/acct>` `3495`
- `--robot-inspect-incident=<id>` `3496`

### Activity / health / diagnose

- `--robot-activity=<session>` `3449`
- `--robot-is-working=<session> --panes=N,M` `3160`
- `--robot-agent-health=<session>` `3162`
- `--robot-health[=<session>]` `3272`
- `--robot-health-oauth=<session>` `3273`
- `--robot-health-restart-stuck=<session> --stuck-threshold=<dur>` `3276`
- `--robot-diagnose=<session> [--diagnose-fix]` `3285`
- `--robot-context=<session>` `3194`
- `--robot-logs=<session>` `3280`

### Control / mutate

- `--robot-send=<session> --panes=N --msg="..."` `3248`
- `--robot-ack=<session> --timeout=30s` `3308`
- `--robot-interrupt=<session> --panes=N --msg="..."` `3340`
- `--robot-smart-restart=<session> --panes=N [--force] [--hard-kill]` `3165`
- `--robot-restart-pane=<session> --type=claude --panes=N --dry-run` `3348`
- `--robot-probe=<session> --panes=N` `3351`
- `--robot-save=<session>` `3374`
- `--robot-restore=<path>` `3378`
- `--robot-switch-account=<provider[:acct]>` `3556`

### Sessions / spawn / controller

- `--robot-spawn=<session> --spawn-cc=N ...` `3314`
- `--robot-controller-spawn=<session>` `3334`
- `--robot-agent-names=<session>` `3331`

### Assign / route / distribute

- `--robot-assign=<session> --strategy=<s>` `3259`
- `--robot-bulk-assign=<session> --from-bv` `3264`
- `--robot-route=<session> --strategy=<s>` `3467`

### Work / beads / bv

- `--robot-plan` `3132`
- `--robot-graph` `3190`
- `--robot-triage --triage-limit=N` `3191`
- `--robot-suggest` `3228`
- `--robot-forecast=<id|all>` `3227`
- `--robot-impact=<path>` `3229`
- `--robot-search=<query>` `3230`
- `--robot-label-attention` `3233`
- `--robot-label-flow` `3235`
- `--robot-label-health` `3236`
- `--robot-file-beads=<path>` `3239`
- `--robot-file-hotspots` `3241`
- `--robot-file-relations=<path>` `3243`
- `--robot-beads-list` `3526`
- `--robot-bead-claim=<id> --bead-assignee=<a>` `3534`
- `--robot-bead-create --bead-title=<t> --bead-type=<t> --bead-priority=<n>` `3535`
- `--robot-bead-show=<id>` `3536`
- `--robot-bead-close=<id> --bead-close-reason=<r>` `3537`

### Pipeline

- `--robot-pipeline-run=<file> --pipeline-session=<s>` `3473` (run)
- `--robot-pipeline=<run-id>` `3474` (**status**)
- `--robot-pipeline-list` `3475`
- `--robot-pipeline-cancel=<run-id>` `3476`

### Mail / coordination

- `--robot-mail` `3298`
- `--robot-mail-check --mail-project=<project> [filters]` `3612`
- `--robot-context-inject=<session>` `3604`

### CASS

- `--robot-cass-status` `3383`
- `--robot-cass-search=<q>` `3384`
- `--robot-cass-insights` `3385`
- `--robot-cass-context=<task>` `3386`

### Ensemble / modes

- `--robot-ensemble-modes` `3195`
- `--robot-ensemble-presets` `3196`
- `--robot-ensemble=<session>` `3197`
- `--robot-ensemble-spawn=<session> --preset --question` `3198`
- `--robot-ensemble-suggest=<question>` `3209`
- `--robot-ensemble-stop=<session>` `3211`

### Monitor / tools / bundle

- `--robot-monitor=<session> --interval=30s` `3172`
- `--robot-support-bundle[=<session>]` `3182`
- `--robot-files[=<session>] --files-window=<dur>` `3483`
- `--robot-metrics[=<session>] --metrics-period=<dur>` `3498`
- `--robot-replay=<session> --replay-id=<id>` `3501`
- `--robot-diff=<session> --since=<dur>` `3516`
- `--robot-summary=<session> --since=<dur>` `3548`
- `--robot-history=<session>` `3441`
- `--robot-tokens` `3433`
- `--robot-wait=<session> --wait-until=<cond>` `3453`

### Palette / recipes / setup / profile

- `--robot-palette` `3505`
- `--robot-recipes` `3291`
- `--robot-setup` / `--robot-acfs-status` `3304-3305`
- `--robot-profile-list` / `--robot-profile-show=<name>` `3429-3430`

### Integrations

See `INTEGRATIONS.md` for DCG, SLB, CAAM, RCH, RANO, quota, ru, giil, JFP, MS, XF.
