# Test Plan -- /create-pr

**Trigger:** `/create-pr` (or `/create-pr --draft`, `/create-pr --base develop`); `/quiver:create-pr` should also work.

**Setup:**
- Current directory is a git repo with a remote configured, the working tree is clean, and the current branch has at least one commit ahead of the base branch.
- `gh` CLI is installed and authenticated.

**Expected behavior:**
1. Skill runs the six git shell blocks and stops with a clear message if any of: not a git repo, no remote, dirty working tree.
2. Skill resolves the base branch via the priority order (`--base` flag > `origin/HEAD` > `main` > `master` > `develop` > prompt).
3. Skill pushes the branch (`git push` with upstream, otherwise `git push -u origin <branch>`).
4. Skill builds a title (<= 72 chars, imperative mood) and a body sized by the Step 3 questions, carrying only the sections that answer one of them, prints both to chat (body in a fenced block), then asks via `AskUserQuestion` with a one-line question and `Create PR / Create as Draft / Edit / Cancel`.
5. With `--draft`, skill skips the prompt and runs `gh pr create --draft ...`.
7. When the repository has a `PULL_REQUEST_TEMPLATE.md`, the body follows that template's sections instead of the Step 3 section list.
6. Final output shows the PR URL parsed from `gh` stdout.

**Verification checklist:**
- [ ] Slash menu shows `/create-pr`.
- [ ] Skill stops cleanly with a single explanatory line on `NO_GIT`, `NO_REMOTE`, dirty tree, base-branch ambiguity, or zero commits ahead.
- [ ] Body uses HEREDOC formatting in the actual `gh pr create` invocation.
- [ ] Title and body are in English even when the conversation is in another language.
- [ ] A one-file mechanical change (typo, version bump) produces 1-2 sentences with no headings, no `## Changes`, and no `## Test plan`.
- [ ] A multi-theme change produces `## Summary` first, then only the sections that carry an answer, and stops when the answers run out.
- [ ] No section appears with nothing behind it -- no `## Test plan` holding "tests pass", no `## Design decisions` describing a choice nobody made.
- [ ] `## Design decisions` carries only the alternatives a reviewer would propose, not a log of every choice made while building.
- [ ] An instruction the user gave in the conversation ("keep it short", "mention the benchmark") is honored over every rule in Step 3.
- [ ] A repository PR template, when present, wins over the Step 3 section list.
- [ ] The full body is visible in the chat stream before the prompt appears; the `AskUserQuestion` question is a single short line containing no body text.
- [ ] `gh pr create` runs only after the prompt is answered -- printing the preview and creating the PR in one uninterrupted turn is a failure, even when the user's message asked for a PR.
- [ ] No AI-attribution lines appear in the title or body.
- [ ] `--base <branch>` overrides every other base-branch source.

**Known gotchas:**
- Splitting the preview out of the question field removes what used to force the prompt: when the body lived inside the question, the skill could not show it without asking. With the two separated, the printed preview looks like a confirmation on its own and the prompt gets skipped. Step 4b is the guard, and it is why the skip is called out there in its own paragraph.
- The `AskUserQuestion` question field is rendered single-line and truncated on some surfaces, and ANSI escape codes print literally (`\x1b[2m` shows up as `@[2m`). Keep the question to one short plain-text line and put the preview in the chat stream.
- `gh pr create` exits non-zero when a PR already exists; the skill must surface the error and suggest `gh pr list --head <branch>` rather than retrying.
- Bitbucket and Azure DevOps are not supported by `gh`; the user must run a platform-specific tool manually for those.
- The section gates fail in one direction only: a skipped section is a short PR body, an unearned one is noise a reviewer has to read past on every future PR. When a gate is genuinely ambiguous, drop the section -- the reviewer has the diff, and the Edit option in Step 4b is there for the case where they wanted it.
- The PR template lookup is a Read tool call inside Step 3, not a `!` block. Those blocks run before any step logic, so a template read there would fire on every invocation including the ones that stop at Step 0, and R3 forbids the conditional logic the lookup needs.
