# Test Plan -- /handover

**Trigger:** `/handover`, `/handover --clear`, `/handover --clear-all` (the `/quiver:handover` forms should also work)

### Case: no flag (save path)

**Setup:**
- Current directory is a git repo with at least one file modification or substantive conversation history.

**Expected behavior:**
1. Skill runs the three `git` shell blocks (`rev-parse`, `status --short`, `diff --stat`); on a non-git directory, prints `> No git repository detected -- skipping branch/commit context.` and continues.
2. Skill produces a Decision Log enumerating meaningful actions; if none, exits with `Handover skipped` and writes nothing.
3. With meaningful work present, skill writes a handover note containing all 8 required sections (Summary, What Was Done, What We Tried / Dead Ends, Bugs & Fixes, Key Decisions, Gotchas, Next Steps, Important Files Map).
4. Skill saves the handover to `.claude/handovers/<timestamp>.md` (filename uses `date '+%Y-%m-%d_%H-%M-%S'` format), prunes the directory to the 3 most recent files, and updates MEMORY.md with a `## Last Handover` block tagged `<!-- handover-sourced -->`.
5. Final confirmation block prints the saved file path, retained filenames, and `MEMORY.md updated: yes`.

**Verification checklist (save path):**
- [ ] Slash menu shows `/handover`, and its argument hint offers `--clear` and `--clear-all`.
- [ ] All 8 section headings are present in the saved file (no section silently omitted).
- [ ] Filename matches `YYYY-MM-DD_HH-MM-SS.md`.
- [ ] Older handovers beyond the 3 most recent are removed.
- [ ] `MEMORY.md` gains a `## Last Handover` block with the `<!-- handover-sourced -->` marker.
- [ ] In an empty/no-progress session, the skill exits cleanly without writing any file.

### Case: `--clear` (delete the newest handover)

**Setup:** `.claude/handovers/` holds 3 timestamp-named `.md` files.

**Expected behavior:**
1. Step 0.5 sets clear-last intent; the skill does not run the save path and writes no handover.
2. Glob lists the 3 files newest-first; the skill prints `Target: <newest filename>` and `Remaining after deletion: 2 handover file(s)`.
3. `AskUserQuestion` is called with `["Yes, delete it", "Cancel"]`.
4. On confirm, only the newest file is removed; the re-list shows the other 2 still present.
5. `MEMORY.md` lines tagged `<!-- handover-sourced -->` are removed and the count is reported; untagged lines are untouched.
6. Output prints `Deleted:` and `Remaining: 2 handover file(s)` with no `{placeholder}` left.

### Case: `--clear-all` (delete every handover)

**Setup:** `.claude/handovers/` holds 3 timestamp-named `.md` files.

**Expected behavior:**
1. Step 0.5 matches `--clear-all` before `--clear` and sets clear-all intent, not clear-last.
2. The skill prints `Files to delete (3):` followed by all 3 filenames — a count with no list is a failure.
3. `AskUserQuestion` is called with `["Yes, delete all", "Cancel"]`.
4. On confirm, `rm -f .claude/handovers/*.md` runs; the re-list reports `Directory clean — 0 handover files.`
5. Output prints `Purged: 3 handover file(s)`, the deleted filenames, and `Status: Clean slate.`

### Case: Cancel (either flag)

**Setup:** `.claude/handovers/` holds at least 1 `.md` file.

**Expected behavior:**
1. The inventory is printed and `AskUserQuestion` is called as above.
2. Selecting `Cancel` prints `Cancelled — no files were deleted.` and stops.
3. No `rm` runs, `MEMORY.md` is not edited, and no output template is printed. Re-listing the directory shows the same files as before the invocation.

**Verification checklist (flags):**
- [ ] `/handover --clear` removes exactly one file (the newest) and leaves the rest.
- [ ] `/handover --clear-all` removes every `.md` file and reports 0 remaining.
- [ ] `--clear-all` is not mis-read as `--clear` despite the substring match.
- [ ] Both flags confirm through `AskUserQuestion` before any `rm`; `Cancel` deletes nothing.
- [ ] Both flags re-list the directory after deleting, and neither prints a raw `{placeholder}`.
- [ ] With a missing or empty `.claude/handovers/`, both flags print the `nothing to delete` line, create no directory, and write nothing.
- [ ] Bare `/handover` with no flag still runs the save path unchanged.

**Known gotchas:**
- The 8 section headings are part of a SYNC contract with `hooks/scripts/pre-compact-handover.sh`. If headings here change, the hook's `PROMPT_PREFIX` must change in lockstep. `tests/hooks/test-handover-sync-contract.sh` is the gate on that.
- Lexicographic prune ordering depends on the timestamp filename format; do not rename existing handovers. Clear Mode's newest-first sort in Step C1 depends on the same format, so `--clear` targets the wrong file if a filename ever drifts from `YYYY-MM-DD_HH-MM-SS.md`.
- `--clear-all` contains `--clear` as a substring. A plain "contains `--clear`" test matches both flags and silently downgrades a purge to a single delete, which reads as success. Step 0.5's precedence rule is the only thing preventing that.
- Clear Mode lists the directory with Glob, not with a `!` shell block. Every `!` block in this repo's skills runs `git`, which is pre-approved in the marketplace sandbox; lesson L1 in `.claude/rules/skill-rules.md` records non-git commands failing there when combined with `||`. The listing also has to happen after Step 0.5 resolves the flag, and `!` blocks run before any step logic.
- The delete paths are why this skill keeps `disable-model-invocation: true`. R10 lets a disabled skill keep its `when-to-use:` and the routing hook drops it from the auto-dispatch block, so no model-initiated invocation can reach `--clear` or `--clear-all`.
