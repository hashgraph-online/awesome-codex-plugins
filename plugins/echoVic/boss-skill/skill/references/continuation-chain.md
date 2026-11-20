# Stage modes and the continuation chain

## Stage order

```
pm → architect → ui → review → tasks → dev → qa → ship
```

## Two modes

Every stage procedure in `commands/<stage>.md` runs in one of two modes.

| Mode     | When                                                               | After the stage is verified             |
| -------- | ------------------------------------------------------------------ | --------------------------------------- |
| Stage    | The user invoked one stage (`/boss:review`, "run Boss QA on this") | Report, name the next entry, stop       |
| Pipeline | The full pipeline, or a stage invoked with `--continue`            | Go to the next stage in the table below |

Stage mode is the default. A stage invoked with `--stop-after <stage>` runs in pipeline mode up to and
including that stage.

A stage is verified when the checker and the verifier both pass (`references/contract-verification.md`).
An unverified stage never hands over to the next one.

## Next stage

| Stage     | Next      | Skipped when                        |
| --------- | --------- | ----------------------------------- |
| pm        | architect | never                               |
| architect | ui        | `--skip-ui` goes straight to review |
| ui        | review    | never                               |
| review    | tasks     | never                               |
| tasks     | dev       | never                               |
| dev       | qa        | never                               |
| qa        | ship      | never                               |
| ship      | end       | never                               |

## Stop conditions (pipeline mode)

Stop, report what exists on disk, and name the next entry when any of these holds:

1. The user says to stop, or to do only this step.
2. The stage named by `--stop-after` is verified.
3. A stage fails verification after two fix rounds, and the user has not waived the failure.
4. A stage cannot produce its artifact.
5. `ship` needs a yes for an action outside the working tree and the user has not given it.
6. `ship` is done.

## Inputs each stage needs

Check the inputs before a stage starts.

| Stage     | Needs                            | When it is missing                                                    |
| --------- | -------------------------------- | --------------------------------------------------------------------- |
| pm        | the user's request               | Ask the user                                                          |
| architect | `prd.md`                         | Use the request the user stated directly                              |
| ui        | `prd.md`                         | Use the request the user stated directly                              |
| review    | `architecture.md`                | Review the code path given, or the current branch's diff              |
| tasks     | `plan.md`                        | Fall back to `tech-review.md` and `architecture.md`, then the request |
| dev       | `tasks.md` and `architecture.md` | Use `prd.md`, then the request the user stated directly               |
| qa        | runnable code                    | Without a PRD, test the user's description or the current branch diff |
| ship      | `qa-report.md`                   | Warn that QA has not run; continue only if the user says so           |

When a stage works from the user's request in place of an upstream artifact, say so in the artifact.

## Artifacts

Everything goes under `.boss/<feature>/`.

| Artifact                       | Stage     |
| ------------------------------ | --------- |
| `prd.md`                       | pm        |
| `architecture.md`              | architect |
| `ui-spec.md`, `ui-design.json` | ui        |
| `tech-review.md`, `plan.md`    | review    |
| `code-review.md`               | review    |
| `tasks.md`                     | tasks     |
| `qa-report.md`                 | qa        |
| `deploy-report.md`             | ship      |
| `verification.md`              | any stage |

## Options shared by every entry

| Option                 | Effect                                                    |
| ---------------------- | --------------------------------------------------------- |
| `--continue`           | Pipeline mode from this stage to `ship`                   |
| `--stop-after <stage>` | Pipeline mode from this stage through the named stage     |
| `--skip-ui`            | Skip the UI stage                                         |
| `--quick`              | Skip routine clarification                                |
| `--lang <code>`        | Artifact language; the default is the user's own language |
