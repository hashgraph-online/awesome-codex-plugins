---
name: create-pr
description: "Create a GitHub pull request from the current branch. Use when the user says 'create a pr', 'open pr', 'push and open a pr', 'create pull request', or wants to open a PR from their branch."
argument-hint: "[--draft] [--base <branch>]"
when-to-use: "user wants to open a pull request from the current branch -- '/create-pr', 'create a PR', 'open a pull request', 'push and make a PR'"
---

# Gather Context

```
!`git rev-parse --is-inside-work-tree 2>/dev/null || echo "NO_GIT"`
```

```
!`git status --short 2>/dev/null || echo "NO_GIT"`
```

```
!`git branch --show-current 2>/dev/null || echo "NO_GIT"`
```

```
!`git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "NO_DEFAULT_BRANCH"`
```

```
!`git log --oneline -10 2>/dev/null || echo "NO_GIT"`
```

```
!`git remote -v 2>/dev/null || echo "NO_REMOTE"`
```

---

# Instructions

## Step 0 -- Validate Environment

Silently evaluate the gather-context output. Stop with a clear message on the first failure:

1. If any git block returned `NO_GIT` -> print: `> No git repository detected. /create-pr requires a git repo.` **Stop here.**
2. If `git remote -v` returned `NO_REMOTE` or is empty -> print: `> No remote configured. Add one with \`git remote add origin <url>\`.` **Stop here.**
3. If `git status --short` is not empty -> print: `> You have uncommitted changes. Commit them first -- you can use \`/quiver:commit\`.` **Stop here.**

---

## Step 1 -- Detect Base Branch

Determine the base branch using this priority order. Use the first that resolves:

1. If `$ARGUMENTS` contains `--base <value>`, use that value as the base branch.
2. If `git rev-parse --abbrev-ref origin/HEAD` did not return `NO_DEFAULT_BRANCH`, strip the `origin/` prefix and use the result.
3. Try `main` -- run `git rev-parse --verify origin/main 2>/dev/null`. If it succeeds, use `main`.
4. Try `master` -- run `git rev-parse --verify origin/master 2>/dev/null`. If it succeeds, use `master`.
5. Try `develop` -- run `git rev-parse --verify origin/develop 2>/dev/null`. If it succeeds, use `develop`.
6. If none resolved, ask the user: "Could not detect the base branch. What branch should this PR target?" via `AskUserQuestion`.

**After resolving the base branch:**

Check if the current branch (from `git branch --show-current`) equals the base branch. If so -> print: `> You are on the base branch (\`{base}\`). Create a feature branch first.` **Stop here.**

Check commits ahead: run `git log --oneline {base}..HEAD`. If output is empty -> print: `> No commits ahead of \`{base}\`. Nothing to create a PR for.` **Stop here.**

---

## Step 2 -- Push If Needed

Before creating the PR, ensure the branch is pushed to the remote:

1. Check upstream: `git rev-parse --abbrev-ref @{upstream} 2>/dev/null`
2. If upstream exists -> `git push`
3. If no upstream -> `git push -u origin {branch}`

If push fails, show the error verbatim and **stop here.**

---

## Step 3 -- Generate PR Title & Body

Gather the change:
- `git log --oneline {base}..HEAD` -- all commits on this branch
- `git diff --stat {base}..HEAD` -- files changed summary
- `git diff {base}..HEAD` -- **full diff**

Then look for a repository PR template with the Read tool (`.github/PULL_REQUEST_TEMPLATE.md`, `.github/pull_request_template.md`, `docs/PULL_REQUEST_TEMPLATE.md`, or `PULL_REQUEST_TEMPLATE.md` at the root). Do this here with the Read tool, not in a `!` block -- the lookup is conditional and those blocks run before any step logic. If a template exists, its sections are the body's structure and the rules below only decide how much goes in each. A section the template asks for and the change has nothing to say about gets one line saying so, not padding. If none exists, build the body from the rules below.

**Title rules:**
- Concise, imperative mood, no period
- <= 72 characters
- Single commit: use its subject line. Multiple commits: summarize the overall theme.

**Body rules:**

The body has one reader: someone who has to approve this diff and was not in this conversation. Anything that does not help that person decide is padding, and padding on a small PR is worse than no description -- it buries the one thing that mattered.

**1. Work out what this reviewer needs, then write only that.** Before drafting, answer three questions against the change in front of you. Each answer that exists becomes body text. An answer that does not exist contributes nothing, and no heading stands in for it.

1. **Why** -- what the change is for, which the diff cannot show. Almost always answerable.
2. **The trap** -- what the reviewer would get wrong, miss, or argue with if nobody told them: an ordering that matters, an alternative already tried and rejected, a breaking edge, a file that looks unrelated and is not.
3. **The ask** -- what the reviewer has to do that CI will not do for them.

Length is the length of those answers. There is no quota and no target. A rename answers the first question in a sentence and has nothing for the other two, so its body is a sentence. A change that rewires authentication answers all three and earns every word it takes. Judge by what the reviewer has to hold in their head, not by how many lines changed: 400 lines of a regenerated lockfile is the sentence, 20 lines moving a permission check is not.

Never ship a body that is a single sentence with no motivation, and never ship one that narrates the diff the reviewer already has. A body that keeps going after the three answers are given is not thorough -- it is unread. The reviewer skims, the detail that mattered is buried in what surrounds it, and a wall of generated prose is the thing people point at when they say a PR was written by a machine.

**2. Sections carry the answers; they are not slots to fill.** Include a section when it carries an answer you actually have, and drop the heading entirely otherwise -- a thin paragraph under an unearned heading is the padding this rule exists to prevent.

| Section | Carries | Include when |
|---------|---------|--------------|
| `## Summary` | Why | The body has headings at all. It comes first. |
| `## Changes` | Why, per area | The diff touches several areas and the file list does not tell a reviewer what each one does. One line per area, never per hunk. |
| `## How it works` | The trap | There is control flow, ordering, or an algorithm a reviewer cannot follow from the diff. |
| `## Design decisions` | The trap | A real alternative was rejected and a reviewer would otherwise propose it. Only the ones they would argue with -- never a log of every choice made while building, and never invented to fill the section. |
| `## Risks` | The trap | Breaking change, migration, data change, feature flag, or a rollback that is not trivial. |
| `## Test plan` | The ask | The reviewer has to do something themselves: manual steps, a runtime check, a device or environment CI does not cover. When the diff adds tests and CI runs them, one sentence naming the command replaces the checklist. Never a checkbox for "code compiles", "tests pass", or "reviewed the diff". |

**3. Calibrate against these.** The three sizes are not tiers to assign a change to -- they are what the three questions produce when a change has one answer, one answer plus a detail, or all three.

A dependency bump, one answer:

```
Bumps `requests` to 2.32.4 for CVE-2024-35195. The three call sites in `client.py` use the same API and are unchanged.
```

One behavior change across a few files:

```
## Summary
Upload retries fired on 4xx as well as 5xx, so a file the server rejected was re-sent three times before the error surfaced. The predicate now checks the status class; backoff is unchanged.
```

Nothing here answers the trap or the ask -- no ordering to explain, no alternative a reviewer would propose, nothing to run by hand.

A new subsystem plus the problems it surfaced, all three answers:

```
## Summary
Adds a behavior eval for the review command: a fixture repo with three planted defects and three baits, a real review run against it, and a grader over the report. Four runs while building it found two real problems, both fixed here.

## Changes
- `tests/eval/` -- runner, fixture builder, expectations.
- `agents/review/security-audit.md` -- the severity rubric mixed a category test with a reachability test, so an unreachable sink flapped between High and Critical between runs. A reachability paragraph settled it; the two runs after it agreed.
- Docs -- `/review` and `/design` resolve to bundled commands, not to this plugin, so user-facing text now names them with the plugin prefix.

## Test plan
`bash tests/eval/run-review-golden.sh` -- spends real API credit, so it sits outside the glob CI discovers and is run by hand before a release.
```

Every other choice that went into building that eval is absent on purpose.

**4. Where the motivation comes from.** In order: what the user said in this conversation; the plan, spec, review report, or issue the branch was built from (`.claude/plans/`, `.claude/reports/`, a linked issue); then the commit messages; then the diff. The diff is last because it only ever answers *what*. If none of the first three carry a motivation, state what the change does and stop -- do not manufacture a rationale.

**5. The user's instructions outrank everything above.** Anything the user asked for in this invocation or earlier in the conversation -- shorter, longer, a section they want, a number they want quoted, an issue to link, a reviewer to address -- wins over every rule here.

**6. Do not write:**
- Filler openers -- "This PR introduces", "This pull request aims to", "In this change we".
- A restatement of the files-changed list GitHub already renders.
- Line-by-line narration of the diff. The diff is attached.
- Speculative follow-ups, "future improvements", or what you chose not to do, unless the user asked for them.
- Praise for the change, emoji headings, or a closing paragraph that repeats the Summary.
- A measurement, a cost figure, or a date the reviewer does not need in order to approve the diff. It belongs in the code or in the file that records it.
- AI attribution of any kind.

**7. Read it back as the reviewer before you print it.** Go through the draft one sentence at a time and ask what the reviewer does with that sentence. A sentence they would skip comes out, and a section whose sentences all come out goes with it. Cut, do not compress: rewording the same content shorter keeps every idea and removes only the words that made them readable.

**Language rule:** the title and body are always written in English, regardless of the conversation language. Only use another language if the user explicitly asks for it in this invocation. A PR is a repository artifact read by people who were not in this conversation.

**Structure rule:** when the body has headings at all, the sections follow in table order. A body of one or two sentences has no headings -- do not put a `## Summary` heading above a single sentence.

---

## Step 4 -- Present & Execute

### Flag: `--draft`

If `$ARGUMENTS` contains "draft", skip the `AskUserQuestion` step. Show the generated title and body, then immediately execute `gh pr create --draft --title "{title}" --body "..." --base {base}`.

### Default (no flag)

Two steps, both mandatory: print the preview, then ask. Do not paste the body into the `AskUserQuestion` question field -- that field is rendered as a single truncated line by some Claude Code surfaces, so a multi-line body is cut off or dropped entirely and the user is asked to approve something they cannot read.

**Step 4a -- print the preview** as normal chat output:

> **PR Title:** {title}
> **Base:** `{base_branch}` <- `{current_branch}`

Then the body verbatim inside a fenced ```markdown block, so the user sees exactly what `gh pr create` will receive.

**Step 4b -- ask, and wait for the answer:**

- **Question:** `"Create this PR?"` -- one short line. No newlines, no body text, no ANSI escape codes.
- **Header:** "Pull Request"
- **Options:**
  1. **Create PR** -- "Create pull request"
  2. **Create as Draft** -- "Create as draft pull request"
  3. **Edit** -- "Revise the title or description"
  4. **Cancel** -- "Abort without creating PR"

Printing the preview is not approval. It is only the readable copy of what the prompt is about, and it exists because the prompt cannot display it. Never run `gh pr create` without an answer from this `AskUserQuestion`. The user asking for a PR in their message is not the answer either -- that is what put the skill on this step. `--draft` is the only path that skips the prompt.

---

### Execution

**On "Create PR":**

```
gh pr create --title "{title}" --body "$(cat <<'EOF'
{body}
EOF
)" --base {base_branch}
```

**On "Create as Draft":**

Same command with `--draft` appended.

**On "Edit":** Ask what to change, revise the title or body, and re-present the `AskUserQuestion`.

**On "Cancel":**

> **PR creation cancelled.**

**Stop here.**

---

## Step 5 -- Output

After successful PR creation, display:

> **PR Created:** {pr_url}
> **Title:** {title}
> **Branch:** `{current_branch}` -> `{base_branch}`
> **Commits:** {count}
> **Files changed:** {count}

Extract the PR URL from the `gh pr create` output (it prints the URL to stdout).

---

# Error Handling

If `gh pr create` fails, show the error verbatim and suggest the user check:
- GitHub CLI authentication (`gh auth login`)
- Remote repository permissions
- Whether a PR already exists for this branch (`gh pr list --head {branch}`)

Never retry automatically.
