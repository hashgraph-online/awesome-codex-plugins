---
name: install-memory
description: Use when the owner asks to add vidbyte-memory to a repo, or to repair a partial install. Runs the installer, which copies the memory protocol into the repo without overwriting anything and wires the Stop hook for each coding agent it finds, then fills the Task section with the owner and runs the tests.
---

# Install memory

## Goal

A repo the owner already works in gains the whole memory protocol in one step, with nothing of theirs overwritten. From the next request on, the agent starts by reading memory, every correction becomes a fact and a test, and the guard enforces the guarantees in every coding agent the owner uses on that repo. The install is visible and reversible: every file it touched is listed, and every file it changed has a backup.

## Objective

Run the installer on the target repo, show the owner the plan before writing, apply it, and leave the repo with a filled Task section, a passing test suite and a commit that records the install. Report what was written, which agents were wired, which existing files were kept, and any step the owner must take by hand.

## Tasks

1. Find the installer. When this skill was loaded from the vidbyte-memory plugin or a clone, it is `scripts/install.py` two folders above this file. Otherwise clone the release this skill shipped with into a temporary folder outside the repo, `git clone --depth 1 --branch v0.3.0 https://github.com/cerredz/vidbyte-memory <tmp>`, and use `<tmp>/scripts/install.py`, so the owner can read the script before it runs and the install is the reviewed release, not whatever `main` holds today. Run it as `python <installer> --target <repo>` from then on.
2. Run it with `--dry-run --target <repo>` and show the owner the plan: the files it would create, the agents it detected and why, and any existing files it would keep.
3. If the plan lists a conflict on a file the memory needs (its tests helpers, its integrity test, the guard or the footprint script), stop and ask the owner how to resolve it before going on.
4. Run it again without `--dry-run`.
5. Ask the owner for the recurring task this repo serves, then replace the paragraph in the `## Task` section of `AGENTS.md` with it: what is produced, for whom, from what inputs, and where it goes. If the installer moved the old instructions to `AGENTS.previous.md`, keep that file and the pointer to it.
6. Run `python -m pytest -q tests`. Fix what the install caused; report anything that was already failing in the owner's own tests.
7. Commit with `python scripts/footprint.py --commit --title "install vidbyte-memory"`.

## Instructions

- **Never overwrite the owner's files.** The installer keeps every existing file and lists the ones that differ from the template; leave them as they are unless the owner says otherwise. A backup named `<file>.vidbyte-memory-backup` sits next to every file it edited, such as `.claude/settings.json` or `CLAUDE.md`.
- **Wire only the agents the owner uses.** Detection looks at the repo, the home folder and PATH. When the owner names their agents, pass them with `--agents`, so the repo does not collect hook files for tools nobody runs.
- **Tell the owner about steps an agent cannot take.** Codex skips project hooks until the owner trusts them with `/hooks`; Grok Build needs `/hooks-trust`; Hermes loads project skills after `hermes skills trust`. The installer prints these as notes; repeat them in the report.
- **The guard is the enforcement.** After the install, `scripts/guard.py` blocks the end of a turn while tests fail, feedback is pending or memory is uncommitted, in every agent whose hook was wired. In other agents the checklist in `AGENTS.md` is the same contract, kept by hand.

## Checklist

- [ ] **The owner saw the dry-run plan before anything was written.** The report quotes the number of files and the agents wired.
- [ ] **No existing file was overwritten.** Every kept file is listed, and every edited file has a backup.
- [ ] **The `## Task` section of `AGENTS.md` describes the owner's recurring task.** The template's placeholder paragraph is gone.
- [ ] **`python -m pytest -q tests` passes, or the report names each failure and whether the install caused it.**
- [ ] **The install is committed**, and `.vidbyte-memory/install.json` lists what was written.

## Output

A short report: the repo, the files written (count and the notable ones), the agents wired and why each was detected, the files kept because they already existed, the hand steps left for the owner (hook trust, conflicts), the test result, and the commit.

## Runtime behavior

- Loaded only when the owner asks to add memory to a repo or to repair an install; it is not part of the per-request protocol.
- The installer is idempotent: running it again creates only what is missing, so it also repairs a partial install.
- When the owner asks to remove the memory, run `python scripts/install.py uninstall --dry-run`, show the plan, then run it without `--dry-run`. It deletes what the install created, restores edited files from their backups, takes the guard hook out of agent settings the owner edited since, and keeps memory the agent wrote unless the owner asks for `--force`.
- Uses `scripts/install.py`, which needs Python 3.9 or later and nothing outside the standard library.
