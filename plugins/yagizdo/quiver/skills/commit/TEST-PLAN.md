# Test Plan -- /commit

**Trigger:** `/commit` or `/commit --push` (and `/quiver:commit` should also work)

**Setup:**
- Current directory is a git repo with at least one staged change (`git diff --cached` is non-empty).

**Expected behavior:**
1. Skill runs the four git shell blocks; on a non-git directory it prints `> No git repository detected. /commit requires a git repo.` and stops.
2. With nothing changed, skill tells the user there's nothing to commit. With unstaged-only changes, skill tells the user to stage first.
3. With staged changes, skill drafts a Conventional Commits message (type/scope/subject), prints it to chat in a fenced block, then asks via `AskUserQuestion` with a one-line question and `Commit / Commit & Push / Edit / Cancel`.
4. With `--push` argument, skill skips the prompt and runs commit then push (`git push` if upstream exists, `git push -u origin <branch>` otherwise).
5. On failure, skill shows the error verbatim and exits without retrying or adding `--no-verify`.

**Verification checklist:**
- [ ] Slash menu shows `/commit`.
- [ ] Generated commit message starts with a valid type (`feat`, `fix`, `docs`, etc.) and a subject ≤72 chars.
- [ ] No `Co-authored-by` or AI-attribution footers appear in the commit.
- [ ] The full commit message is visible in the chat stream before the prompt appears; the `AskUserQuestion` question is a single short line containing no message text.
- [ ] `git commit` runs only after the prompt is answered -- printing the message and committing in one uninterrupted turn is a failure, even when the user's message asked for a commit.
- [ ] `--push` path commits and pushes without prompting.

**Known gotchas:**
- Splitting the message out of the question field removes what used to force the prompt: when the message lived inside the question, the skill could not show it without asking. With the two separated, the printed message looks like a confirmation on its own and the prompt gets skipped. The guard paragraph under the options is why the skip is called out there.
- The `AskUserQuestion` question field is rendered single-line and truncated on some surfaces, and ANSI escape codes print literally (`\x1b[2m` shows up as `@[2m`). Keep the question to one short plain-text line and put the message in the chat stream.
- Pushing without an upstream requires `git push -u origin <branch>`; do not silently fall back to `git push` when no upstream is configured.
