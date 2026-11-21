# Contract verification

Every role has a hard-requirement table in its agent file. The role that wrote an artifact does not
decide whether the table is met. Two checks do, in this order.

## 1. Checker

Run the script on the feature folder, naming the artifacts this stage must have written:

```bash
node <boss-skill-dir>/scripts/check-artifacts.mjs .boss/<feature> --require <files> --only <files>
```

`<files>` is the comma-separated list from the table below. The script prints one `PASS` or `FAIL` line
per rule and exits 1 when any rule fails.

The script decides only what a script can decide: the summary is the first section, no placeholder is
left, the PRD has a Given-When-Then scenario, a QA report records an exit code. If `node` is missing,
read `scripts/check-artifacts.mjs` and apply its rules by hand, and say in the report that you did.

## 2. Verifier

Dispatch a fresh subagent with `agents/boss-verifier.md`. Give it:

- the artifact paths
- the path of the role's agent file, for the requirement table and the prohibitions
- the checker output

The verifier must not share context with the agent that wrote the artifact. If the host has no
subagents, do the verifier pass yourself after re-reading the artifact from disk, and say in the report
that verification was not independent.

| Stage     | Artifacts for `--require`      | Role agent file                                     |
| --------- | ------------------------------ | --------------------------------------------------- |
| pm        | `prd.md`                       | `agents/boss-pm.md`                                 |
| architect | `architecture.md`              | `agents/boss-architect.md`                          |
| ui        | `ui-spec.md`                   | `agents/boss-ui-designer.md`                        |
| review    | `tech-review.md,plan.md`       | `agents/boss-tech-lead.md`                          |
| review    | `code-review.md` (diff review) | `agents/boss-tech-lead.md`                          |
| tasks     | `tasks.md`                     | `agents/boss-scrum-master.md`                       |
| dev       | none; verify the code instead  | `agents/boss-frontend.md`, `agents/boss-backend.md` |
| qa        | `qa-report.md`                 | `agents/boss-qa.md`                                 |
| ship      | `deploy-report.md`             | `agents/boss-devops.md`                             |

For `dev` there is no document to check. Give the verifier the task list and the diff, and have it
confirm that each task's tests exist and that the commands in `references/quality-gate.md` Gate 0 exit 0.

## 3. Outcome

| Result                                      | Do                                                                          |
| ------------------------------------------- | --------------------------------------------------------------------------- |
| Checker passes and the verifier says `PASS` | The stage is verified                                                       |
| Any `FAIL`                                  | Send the failing items to the role agent to fix, then run both checks again |
| Still failing after two fix rounds          | Stop. Report the failing requirements. Do not hand over                     |
| The user says to accept a named failure     | Record it as waived and continue                                            |

Do not edit an artifact yourself to make a check pass, and do not weaken a check. A requirement the
verifier marks `UNVERIFIABLE` is not a pass: name it in the final report.

## 4. Record

Append one entry per stage to `.boss/<feature>/verification.md`:

```markdown
## <stage> — PASS | FAIL | WAIVED

- Checker: <n> rules passed, <n> failed
- Verifier: <independent | not independent>

| Requirement | Verdict | Evidence |
| ----------- | ------- | -------- |

Waived: <requirement and the user's words, or "none">
```
