# Stage Handoff

> Give each stage a precise request, check its saved artifact on disk, and pass that artifact forward until the last stage proves completion.

## 1. Stage Contracts

Load each stage skill through the runtime's skill mechanism (or read its `SKILL.md` where skills are plain files) and follow it from its first phase. The stage owns everything inside its run.

| Stage | Request passed to the stage | Artifact that must exist before the next stage | Passed forward |
|---|---|---|---|
| `hyper-research` | The question the job depends on, with the decision it must support ("which state library fits this repo, to adopt it next"); for web-sourced research also "for each source a plain fetch cannot read, load `hyper-browsing` for that one source and record its provenance label and report path in `sources.md`" | `.hyper/research/[NN].<slug>.md`, plus every `.hyper/browsing/<slug>/report.md` its `sources.md` cites | Report path and its recommendation line |
| `hyper-issue` | `--from-hyper`, the items to register, the issue numbers, or the selection condition, plus the tracker, the repository, and any user restriction such as draft-only; "register each issue in English with its `hyper:` block, write the lane manifest, and do not start another `hyper` run" | The registered issues re-read from the tracker, and `.hyper/issues/<slug>/batch.md` | The issue numbers with URLs and the manifest path; `hyper-plan` receives "plan one wave per group of at most four lanes from the manifest's Lane table; each lane is one parallel lane with its issues in order; each issue's `verify` is its row's gate; the list is fixed" |
| `hyper-seo` | The target, plus `recommend` as the allowed action in a Build job, or the user's own mode in a Report job | The report under `.hyper/seo/<slug>/` | Report path and its critical and warning findings |
| `hyper-google-analytics` | The user's request unchanged, the site URL or property ID from the request, the mode words, and every upstream artifact path | `.hyper/google-analytics/<slug>/report.md` with its final state line naming the mode's terminal result (`audited`, `installed`, `changed`, `reported`, `fixed`, `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, or `handoff`) | The changed paths when `hyper-git` follows, and the report path with its findings by severity |
| `hyper-google-tagmanager` | The user's request unchanged, the container ID and site URL from the request, the mode words, and every upstream artifact path | `.hyper/gtm/<slug>/report.md` with its `결과:` line naming `verified`, `partial`, `proposed`, `exhausted`, or `blocked` | The changed paths when `hyper-git` follows, and the report path with its proposed approval-gated actions |
| `hyper-architecture` | In a Build job: "architecture audit only; report findings with file paths; do not edit", plus the target paths. As the last stage: the user's request unchanged | Its routing line plus findings, copied into the workflow record's stage notes, because the stage saves no file of its own in audit mode | The stage-notes section path and the findings |
| `hyper-database` | Before a plan or mass stage: "review only; report findings, the design brief, or the engine choice with file paths; do not edit", plus the target paths and every upstream artifact path. As the last stage: the user's request unchanged, plus every upstream artifact path | `.hyper/database/<slug>/report.md`; as the last stage its verification section lists each check as run with its output or `not run` with the reason | Report path and its critical and high findings |
| `hyper-mcp` | Before a plan or mass stage: "audit only; report findings with file paths; do not edit", plus the target paths and every upstream artifact path. As the last stage: the user's request unchanged, plus every upstream artifact path | `.hyper/mcp/<slug>/report.md`; as the last stage its verification table also lists the MCP Inspector run in the era the target claims | Report path and its critical and high findings |
| `hyper-decision` | Before a plan or mass stage: "`design` or `audit` mode only; write the decision contract or the read-only audit table with file paths, the route tier per call, and whether each route returns probabilities; do not edit the audited code", plus the target paths and every upstream artifact path. As the last stage: the user's request unchanged, plus every upstream artifact path | The artifacts under `.hyper/decision/<topic>/` (or the path the user gave) and the stage's report naming every path written, the mode, the fit-gate verdict, the route and tier, and, for every request file, the `check-decision-request.sh` exit code for its route or a note that the manual checklist was applied | The contract or audit path and its decision rows when `hyper-plan` follows; the changed paths when `hyper-git` follows |
| `hyper-design` | Before a plan or mass stage: "report only; write the design brief for a new interface, or audit the existing one; do not edit", plus the target paths and every upstream artifact path. As the last stage: the user's request unchanged, plus every upstream artifact path | `.hyper/design/<slug>/brief.md` (brief-only) or `.hyper/design/<slug>/report.md`; as the last stage the report passes the stage's report validator and records the craft-floor result and the review mode | Brief or report path and its P0 and P1 findings |
| `hyper-frontend` | Before a plan or mass stage: "`verify` mode only; report what breaks in a real browser with file paths and the capture matrix; do not edit", plus the target paths and every upstream artifact path. After `hyper-design` in `brief-only` mode: the user's request unchanged plus the brief path as the look to build inside. As the last stage: the user's request unchanged, plus every upstream artifact path | `.hyper/frontend/<slug>/report.md` ending in one `Result:` line (`delivered`, `delivered_unverified`, `awaiting_input`, or `blocked`), with the scroll ownership, the state matrix, and each claim labeled `static`, `rendered`, or `not verified` | The changed paths when `hyper-git` follows; the report path and its findings when `hyper-plan` follows |
| `hyper-feedback` | The user's request unchanged with the quoted feedback text, its author or relay path, the user's constraints, and every upstream artifact path | `.hyper/feedback/<slug>/report.md` with every item's status and its verification section (commands with output, the residue-sweep result), plus `.hyper/feedback/<slug>/brief.md` when the run ended `handoff` | The changed paths when `hyper-git` follows; the brief path and the delivery flag when `hyper-plan` is added |
| `hyper-debug` | The user's request unchanged with the failure evidence (trace excerpt, failing command or test name, observed versus expected output), whether a fix was asked for, the user's constraints, and every upstream artifact path | `.hyper/debug/<slug>.md` ending in one `Result:` line (`confirmed`, `fixed`, `handoff`, `unconfirmed`, `awaiting_input`, or `blocked`), with the reproduction, the toggle proof for a confirmed cause, and, for `fixed`, the red-to-green command output | The changed paths when `hyper-git` follows; the journal path and the delivery flag when `hyper-plan` is added |
| `hyper-data` | The user's request unchanged with the question, the dataset paths, the reader's time zone when the request names one, and every upstream artifact path | `.hyper/data/<slug>/report.md` ending in one `Result:` line (`answered`, `prerequisite_missing`, `awaiting_input`, or `blocked`), with the answer first and, for `answered`, the query, row counts, timing, and input digest | - |
| `hyper-imagegen` | The user's request unchanged, the supplied edit source or reference path when one exists, and every upstream artifact path | One terminal line (`generated_verified`, `generated_caveated`, `prompt_saved`, `awaiting_input`, or `blocked`) with its evidence: the runtime's returned-image record, or the relative path and digest of the file under `.hyper/imagegen/<topic>/` | - |
| `hyper-plan` | The user's original request, every upstream artifact path as required reading, the delivery flag, and `--plan-only` or the approval hold when the user said so | `.hyper/plans/<slug>.md` with a `## Handoff` section | Nothing: the stage continues into `hyper-execute` itself |
| `hyper-execute` | The plan slug and the delivery flag | `.hyper/execute/<slug>/state.json` with `status` of `complete` and the printed completion block | - |
| `hyper-mass` | The goal, its success criteria, and every upstream artifact path | `.hyper/mass/<run-key>/run.jsonl` ending in a `run.settled` event with `status` of `completed` | - |
| `hyper-loop` | The user's request unchanged with its goals and their criteria, the loop slug when resuming, the user's constraints, and every upstream artifact path | `.hyper/loop/<slug>/final-gate.json` with `status` of `complete`, `blocked`, or `paused`, and, for `complete`, a `verify-loop-state.sh --final` run that exits 0 | The changed paths when `hyper-git` follows |
| `hyper-skill` | The user's original request, the target `skills/<name>/` path when it exists, and every upstream artifact path as required reading | `skills/<name>/SKILL.md` and `SKILL.ko.md`, plus the stage's validator run reporting zero errors in its validation handoff | The changed paths, when `hyper-git` follows |
| `hyper-documentation` | The user's original request, the target path when it exists, and every upstream artifact path as required reading | The created or updated artifact at the requested path, plus the selected mode's validation handoff and, for a machine-readable prompt artifact, its parse result | The changed paths, when `hyper-git` follows |
| `hyper-git` | The mode (commit, or workflow for a pull request or a whole-branch merge), the changed paths from the previous stage as the commit scope, the target branches in the user's order, and the user's limits ("커밋만", "main 빼고") unchanged | Each commit SHA it reports found on every remote target (`git fetch origin <target>`, then `git branch -r --contains <sha>` or `git cherry origin/<target> <branch>` with no `+` lines), or the pull request URL with its state from `gh pr view` | - |
| `hyper-deploy` | The user's request unchanged, the environment name words ("staging", "프로덕션", "preview"), every upstream artifact path as required reading, and the execution completion block when it follows a plan stage | `.hyper/deploy/<slug>/report.md` with its `Result` line naming one of `ready`, `unproven`, `deployed`, `changed`, `fixed`, `exhausted`, `stopped-for-approval`, `blocked`, or `handoff`, and the evidence behind it | Nothing: it is the last stage of the chain |

Rules for every hand-off:

- Read the artifact from disk before marking the stage done. A stage's claim in chat without the file is a failed hand-off.
- A `hyper-git` stage starts only after the previous stage's completion evidence passed; a failed validator never reaches delivery.
- Pass upstream artifacts by path, and add at most three lines of the conclusion that the next stage needs. Do not paste whole reports.
- Pass the user's constraints (scope limits, excluded paths, "커밋하지 말고") to every stage unchanged.
- A `hyper-deploy` stage that follows a plan stage starts only after the execution completion block, so it receives the completion block as part of its request and deploys the delivered result rather than a tree still under change.

Companion rules for `hyper-browsing` inside a `hyper-research` stage:

- Load it through the runtime's skill mechanism like a stage skill, for one blocked source at a time, and pass the source URL, the research question it serves, and whether a dated copy is acceptable for that claim.
- Its `blocked` and `needs_user` terminals do not stop the chain: the research stage records the source as inaccessible and continues with other channels. The chain stops only when the research stage itself stops.
- A `sources.md` row that cites a browsing report whose file is missing fails the research hand-off like a missing artifact.
- When no `hyper-browsing` skill is installed, the research stage records blocked sources as inaccessible, and the closing report names `npx skills add alpoxdev/hypercore --skill hyper-browsing`.

## 2. The Plan-to-Execute Step

`hyper-plan` continues into `hyper-execute` in the same session when its own conditions hold. This skill never starts that execution itself.

After the plan stage returns, read the plan's `## Handoff` lines:

| `Auto-execute` value | Meaning | Next action |
|---|---|---|
| `yes` | Execution ran inside the plan stage | Check `.hyper/execute/<slug>/state.json`; `complete` finishes the chain, `active` or `paused` means execution is still running or stopped and its own report decides |
| `no (plan only requested)` or `no (approval requested)` | The user asked to stop after the plan | Finish the chain as a Report job |
| any other `no (...)` | The plan stage hit a hard stop | Stop the chain with that reason (§5) |

## 3. Workflow Record

Write `.hyper/workflows/<slug>.md` before the first stage. `<slug>` is a short kebab-case name of the job; add `-2`, `-3` when the file exists for a different job. Keep it in Korean except for paths, skill names, and flags.

```markdown
# <job title>

- 요청: <the user's request, verbatim>
- 작업 종류: build | report | resume
- 전달: local | make-pr | ship | plan-only | git:<mode> <targets>
- 상태: running | done | stopped
- 정지 사유: <reason, or 없음>

## 단계

| # | 단계 | 선택 근거 | 상태 | 산출물 |
|---|---|---|---|---|
| 1 | hyper-architecture | "폴더 구조 리팩토링" + package.json `next` | done | 단계 메모 1 |
| 2 | hyper-plan | 여러 파일 변경 | running | .hyper/plans/<slug>.md |

## 단계 메모

### 1. hyper-architecture
<routing line and findings with file paths>
```

Stage status values: `pending`, `running`, `done`, `skipped`, `stopped`. Update the row when a stage starts and when it ends, before printing the status line.

## 4. Stage Results

| Stage result | Action |
|---|---|
| Artifact exists and the stage reports success | Mark `done`, print `<#>/<total> <stage> 완료 - <artifact>`, start the next stage |
| `hyper-architecture` stops with an unsupported stack while it is an upstream stage | Mark `skipped` with the reason; continue, because its output was advisory evidence |
| A stage stops because the request is a different output shape | Re-route once (§6) |
| `hyper-imagegen` ends `awaiting_input` | Relay its one question unchanged and mark `stopped`; on the answer, resume at the same stage |
| `hyper-feedback` ends `handoff` | Mark `done`, add `hyper-plan` as the next stage with `brief.md` as required reading and the user's delivery flag, and drop a planned `hyper-git` stage |
| `hyper-feedback` ends `awaiting_input` | Relay its one question unchanged and mark `stopped`; on the answer, resume at the same stage |
| `hyper-feedback` ends `exhausted` | Mark `stopped` with the failing command and its output; a `hyper-git` stage does not start |
| `hyper-debug` ends `handoff` | Mark `done`, add `hyper-plan` as the next stage with `.hyper/debug/<slug>.md` as required reading and the user's delivery flag, and drop a planned `hyper-git` stage |
| `hyper-debug` ends `unconfirmed` | Mark `done` with the `Assumption:` line and its confirming check; a `hyper-git` or `hyper-plan` stage does not start, because nothing was proven to fix |
| `hyper-debug` ends `awaiting_input` | Relay its one question unchanged and mark `stopped`; on the answer, resume at the same stage |
| `hyper-data` ends `awaiting_input` or `prerequisite_missing` | Relay its one question, or the missing engine with its install command, unchanged and mark `stopped`; on the answer or after the install, resume at the same stage |
| `hyper-loop` ends `blocked` or `paused` | Mark `stopped` with the goal and the failure signature or the pause reason from `final-gate.json`; a `hyper-git` stage does not start, and "이어서" resumes the loop from `.hyper/loop/<slug>/` |
| `hyper-frontend` ends `delivered_unverified` | Mark `done` and carry the missing browser capability from the report into the closing report as a caveat; a `hyper-git` stage follows only on the user's delivery words |
| `hyper-frontend` ends `awaiting_input` | Relay its one question unchanged and mark `stopped`; on the answer, resume at the same stage |
| `hyper-frontend` ends `blocked` | Mark `stopped` with the failing capture and its evidence from the report; a `hyper-git` or `hyper-plan` stage does not start |
| `hyper-google-analytics` ends `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, or `handoff`, or `hyper-google-tagmanager` ends `proposed`, `exhausted`, or `blocked` | Mark `stopped` with the proposed approval-gated actions, the failing check, or the blocker from the report; a `hyper-git` or `hyper-deploy` stage does not start, and "이어서" resumes at the same stage after the approval or the fix |
| A stage stops for a user decision, a credential, a conflict, or a failed gate | Mark `stopped` and end the chain (§5) |
| The stage skill is not installed or cannot be loaded | Mark `stopped`; report the chain and `npx skills add alpoxdev/hypercore --skill <stage>` |

Never edit the stage's artifact to make it pass, never re-run a stopped stage with weaker inputs, and never continue past a stop that is not listed as a skip.

## 5. Stop Reporting

When the chain ends early, print in Korean:

1. the route line with each stage's final status
2. the stopped stage, its own reason in one line, and the one thing the user can do to unblock it
3. the record path, so a later "이어서" resumes from it

## 6. Re-Route and Resume

- Re-route: when a stage says the request is a different output shape (the plan stage reports that the job is really research), rebuild the chain from that evidence with `rules/workflow-routing.md`, record both chains, and continue. A second shape mismatch stops the run.
- Resume: on "이어서" / "resume", read the newest record whose `상태` is `running` or `stopped`, confirm the stopped stage's blocker is gone, and restart at the first stage that is not `done` or `skipped`. With no record, an open execution state routes to `hyper-execute` alone.

## 7. Closing Report

Report in Korean: the final chain with statuses, each artifact path, the last stage's completion evidence (the execution completion block, the mass run's verification result, the loop's `final-gate.json` with its `--final` exit code, the skill validator result, the issue record's number and URL with the manifest path, the documentation mode's validation handoff, the database report's verification section, the MCP report's verification table, the decision stage's report with every path written and the offline request-checker exit code, the GA report's `Result` line with its collection proof, the GTM report's `결과:` line with its tag-firing proof, the UI report's validator result and craft-floor line, the feedback report's item table with its residue-sweep result, the debug journal's `Result` line with its toggle proof, the data report's `Result` line with its row counts and input digest, the image stage's terminal with its path, digest, and inspection record, the Git delivery's commit SHAs found on each remote target, the deploy report's `Result` line with the deployment ID and terminal state, or the report path), the delivery result (local commits, PR URL, or merge), every companion access report with its terminal, and every skipped or stopped stage with its reason.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The stage artifact paths and state values (`.hyper/research/`, `.hyper/seo/<slug>/`, `.hyper/google-analytics/<slug>/report.md` and its ten terminal values, `.hyper/gtm/<slug>/report.md` and its five results, `.hyper/database/<slug>/report.md`, `.hyper/mcp/<slug>/report.md`, `.hyper/decision/<topic>/` and its checker routes, `.hyper/design/<slug>/brief.md` and `report.md`, `.hyper/frontend/<slug>/report.md` and the frontend stage's four terminals, `.hyper/feedback/<slug>/report.md` and `brief.md` with the feedback stage's run terminals, `.hyper/debug/<slug>.md` and the debug stage's six terminals, `.hyper/loop/<slug>/final-gate.json` and its three statuses, `.hyper/data/<slug>/report.md` and the data stage's four terminals, `.hyper/imagegen/<topic>/` and the image stage's five terminals, `.hyper/deploy/<slug>/report.md` and its nine result values, `.hyper/plans/<slug>.md`, `state.json` `status`, `run.settled`, `skills/<name>/SKILL.md`, the documentation artifact paths, the Git delivery's remote-branch checks) | each stage skill's own `SKILL.md` and references in this repository, 2026-11-09 |
| The plan stage's `## Handoff` lines and its auto-continue into execution | the plan skill's handoff rule in this repository, 2026-11-06 |
| The architecture stage stops on an unsupported stack and reports the install command for a missing skill | the architecture skill's stack-detection rule in this repository, 2026-11-06 |
| Hand-off through saved artifacts and durable state rather than chat | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| The workflow record shape, the skip rule, and the single re-route | this package's chosen design, not a validated optimum |
| The `hyper-browsing` companion rules: one blocked source per call, non-stopping terminals, and the missing-report check | this package's chosen design, not a validated optimum |
