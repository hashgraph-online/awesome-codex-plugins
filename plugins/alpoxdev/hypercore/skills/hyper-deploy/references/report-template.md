# Report Template

Use this reference when writing `.hyper/deploy/<slug>/report.md`. Keep the `##` headings in English; write the prose in Korean.

## Template

```markdown
# <run title>

- Mode: preflight | setup | deploy | change | diagnose
- Target: <railway | cloudflare | docker-image | compose | vps> (<deciding file>)
- Identity: <project / environment / service, Worker and env, image repo:tag, or host and Compose project>
- Environment: <name> (production: yes | no)
- CLI: <binary> <version from --version>
- Result: ready | unproven | deployed | changed | fixed | exhausted | stopped-for-approval | blocked | handoff

## Evidence

- `<path>:<line>` - <what it shows>
- `<command>` -> <trimmed output, secrets redacted>

## Readiness

`PRE_DEPLOY_SUMMARY executed=<n> skipped=<m>` from `bash skills/hyper-deploy/scripts/deploy-check.sh`, exit <code>. Skipped gates: <name - reason>.

## Actions

| # | Command | Tier | Result |
|---|---|---|---|
| 1 | `<command>` | proceed / named environment / approved | <state or output line> |

## Diagnosis

| Symptom | Log or state line | Cause | Fix | Before | After |
|---|---|---|---|---|---|

## Terminal State

- Deployment: <ID or version> -> <state>
- Health: <check and result>
- Runtime log window: <bounded window and fatal-error count>

## Proposed, Not Run

- `<exact command>` - <what it changes>, <what it does not restore>, <why it is proposed>

## Gaps And Risks

- <missing CLI, missing credential, `not run` checks, unresolved cause, volatile fact re-checked or not>
```

## Rules

- Omit a section only when the mode cannot produce it, and write `none` when it can but nothing happened.
- Every command in `## Actions` ran in this session.
- Redact tokens, secrets, and connection strings, and say what was redacted.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The report fields and the result values | this package's design, 2026-11-07 |
| A report that records what was tested, what was observed, and what was omitted | `instructions/harness-engineering/references/evidence-and-recovery.md` |

### Evidence grade

`LOCAL` - the template is this package's own.
