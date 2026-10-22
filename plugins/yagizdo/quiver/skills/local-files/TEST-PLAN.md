# Test Plan -- local-files

**Trigger:** Reference skill -- not directly invoked. Read at the write step of each skill listed in its `## Directories` table.

**Setup:**
- A git repository with a commit and no `.claude/` directory.
- A second git repository where `.claude/plans/` already holds a committed file.
- A directory that is not a git repository.

**Expected behavior:**
1. In the first repository, the first `/plan` run appends `.claude/plans/` to the file `git rev-parse --git-path info/exclude` prints and prints `> Keeping .claude/plans/ out of git (added to .git/info/exclude).`; `git status --short` then shows no `.claude/plans/` entry.
2. A second `/plan` run in the same repository prints nothing about the directory and adds no second line.
3. In the second repository, the plan is written and the exclude file is not touched.
4. Outside git, the plan is written and nothing else happens.

**Verification checklist:**
- [ ] First write in a fresh repository appends exactly one `.claude/plans/` line and prints the keep-local line once.
- [ ] Lines already in the exclude file before the run are still there after it, in the same order.
- [ ] A second run adds no duplicate line and prints nothing.
- [ ] A directory with tracked files is left alone; the exclude file is unchanged.
- [ ] With `.claude/*` and `!.claude/plans/` in `.gitignore`, two runs leave exactly one `.claude/plans/` line and print the keep-local line once.
- [ ] A project whose `CLAUDE.md` says to track `.claude/plans/` is left alone.
- [ ] Run from a linked worktree, the line lands in the shared exclude file and `git check-ignore -q .claude/plans/x` exits 0 in the main checkout too.
- [ ] Outside a git repository nothing is created besides the written file.

**Known gotchas:**
- `git check-ignore` exits 1 for a path that is not ignored and 128 on an error such as running outside a repository; check for a repository first so 128 is never read as "not ignored".
- `git check-ignore` reports nothing for a path that is already tracked, even when a pattern matches it. That is why the tracked-files check runs first.
- In a linked worktree `.git` is a file, not a directory; `git rev-parse --git-path info/exclude` resolves to the shared git directory, so never build the path by hand.
