# Phase A: Split a branch into a stack

Starting point: one branch with all the work, often already a PR. This is the **reference**. The goal is N PRs that can each be reviewed in one sitting, build on their own, and together equal the reference.

Run phase 0 first (`SKILL.md`). If some slices already exist, keep them and resume at the first missing step.

## 1. Pin the reference and the base

```bash
git fetch origin
REF=origin/<reference-branch>
BASE_BRANCH=develop                     # use the project's actual base: main, master, develop, etc.
FORK=$(git merge-base "origin/$BASE_BRANCH" "$REF")
BASE=$(git rev-parse "origin/$BASE_BRANCH") # cut every slice from this pinned commit
git config --local --add stacked-prs.protect "$BASE_BRANCH"
WORK=$(mktemp -d)                              # file lists for this split; not /tmp names other sessions share
git config --local --add stacked-prs.protect <reference-branch>   # safe-push.sh now refuses the reference
```

- Pin `BASE` once and cut every slice from it. If the base moves during the split, keep going from `BASE`, and bring the base in later through normal merges.
- Leave the reference branch and its PR open and unchanged (rule 1).

## 2. Inventory

```bash
git diff --stat $FORK $REF | tail -1
git diff --name-only --no-renames $FORK $REF | cut -d/ -f1-2 | sort | uniq -c | sort -rn | head -30
git diff --name-status -M $FORK $REF | grep '^R'      # renames: keep both halves in one slice
git diff --name-only --diff-filter=D $FORK $REF       # deletions
git diff --name-only --diff-filter=A $FORK $REF       # new files
```

**Files both sides changed.** The base changed these since the fork point. Copying the reference's version of one would undo the base's change, so step 5 applies the reference's change with a three-way merge instead:

```bash
comm -12 <(git -c core.quotePath=false diff --name-only --no-renames $FORK $REF | sort) <(git -c core.quotePath=false diff --name-only --no-renames $FORK $BASE | sort) > $WORK/overlap.txt
git -c core.quotePath=false diff --name-only --no-renames --diff-filter=D $FORK $REF | sort > $WORK/deleted.txt   # what the reference deletes
```

**Files the base added that use code the reference removes.** These break the build after the cutover and need porting:

```bash
git diff --name-only --diff-filter=A $FORK $BASE | xargs grep -l -E '<removed symbol 1>|<removed symbol 2>' 2>/dev/null
```

## 3. Plan slices by layer

Put each file in the lowest layer it can live in. Lower layers are safe to merge alone; higher layers depend on them.

| # | Layer | What makes it safe or reviewable |
|---|---|---|
| 1 | **Libraries and modules with no callers yet** | Nothing calls the changed parts, so behavior is unchanged. Prove it with `git grep` on the base |
| 2 | **Additive API surface** | Only new fields, endpoints, hooks, and types; nothing removed or changed in meaning |
| 3 | **Independent behavior changes the later work needs** | Small and reviewable in isolation, with its own tests |
| 4 | **New code, compiled but unused** | Nothing calls it yet. Every file is in its final form; nothing is temporary |
| 5 | **Cutover** | Call sites switch over and legacy code is removed. Ideally the one slice that changes behavior |
| 6 | **Guards and cleanup** | Lint rules, checks, or deprecations that stop the old APIs coming back |
| 7 | **Review follow-ups** | Larger changes a reviewer asked for, as their own slice on top |

Not every stack needs every layer. Merge layers that would come out tiny, and split one that would be too big to review.

Placement rules:
- **Each file lands once, in its final form.** Avoid temporary shims. If you must split a file, use `git checkout -p`.
- **Tests travel with the code they test.**
- **A replacement ships with the removal of what it replaces,** especially when the two would collide.
- **Deletions go with the cutover**, unless nothing references the deleted code on the base.
- **A rename's delete and add go in the same slice.**
- **Build config** (manifests, project files, CI) goes in the first slice that needs it.
- Leave stray changes out of every slice, such as accidental lockfile churn. List them as differences from the reference.
- **Size:** aim for slices a reviewer can finish in one sitting. For a big cutover, use one commit per area and ask reviewers to go commit by commit, or split it further if the halves each build (`changes.md`).

Write the plan as a numbered list (it goes into PR 1's description) and **agree it with the user before cutting**. Keep each slice's file list in `$WORK/NN.txt`, because step 5 uses those lists. Only files from the reference's own diff (`git -c core.quotePath=false diff --name-only --no-renames $FORK $REF`) belong in a list. Port files the base added (step 2) as a separate, reviewed commit on the slice, not through the list.

## 4. Choose each slice's target and start point

| The slice needs | Target | Start point |
|---|---|---|
| Nothing beyond the base | base | `$BASE` |
| Several independent slices | an integration branch (base + those slices) | the integration branch |
| Exactly one slice | that slice's branch | that branch |
| Can't be built on the current base yet (heavy conflicts the team can't resolve yet) | base | `$FORK`, with lower slices carried along; identify the cutover's own commit range for review |

Independent slices should target the base directly. If the host merges by squash, prefer independent slices and short chains (see `landing.md`).

For any branch carrying copied slices, create the copied-dependency record in `stack-map.md` independently of its PR target. Pin its starting commit and the observed base, record each source slice's tip and original-to-copy commit mapping, and save the tip after copies before adding the cutover's own edits. These pins let later agents find review fixes absent from the copies. Keep the record through landing; do not advance historical pins when branches move.

## 5. Cut the branches

Use one worktree for the whole split: `git worktree add ../<repo>-slices $BASE`.

For each slice, bottom-up, first check whether its branch exists (`stack-detect.sh <ID>`, or `git rev-parse -q --verify origin/<branch>`):
- **Already pushed:** keep it, and never re-cut it. Compare it with the plan (`split-coverage.sh`), and add whatever is missing as a new commit on top.
- **Local only:** the absence of a remote or upstream does not prove a branch was never pushed. Re-cut only when branch history and user context establish that it was never published. If detection says "WAS PUSHED", treat it as pushed. Keep it if it matches the plan, and ask first if it has commits you didn't make.
- **Missing:** cut it as below.

The line-based examples below assume file paths contain no tabs or newlines. If they do, use NUL-delimited Git output and pathspec files instead; do not split paths on whitespace.

Always use **explicit file lists**. Passing a directory to `git checkout` doesn't apply deletions.

```bash
git switch -c feature/<ID>-NN-<slug> --no-track <start-point>     # --no-track: never let a slice track the slice below
L=$WORK/NN.txt                                                    # this slice's files, from the plan
: > $WORK/failed.txt; rm -f $WORK/not-clean.txt

# files only the reference changed: take its version, or delete what it deletes
comm -23 <(sort $L) $WORK/overlap.txt > $WORK/plain.txt
while IFS= read -r f; do
  if git cat-file -e "$REF:$f" 2>/dev/null; then git checkout "$REF" -- "$f"
  elif grep -qxF -- "$f" $WORK/deleted.txt; then git rm -q -- "$f"
  else echo "not in the reference's diff: $f" >> $WORK/failed.txt; fi
done < $WORK/plain.txt

# files both sides changed: apply only the reference's change, as a 3-way merge
comm -12 <(sort $L) $WORK/overlap.txt > $WORK/both.txt
while IFS= read -r f; do
  git diff --binary $FORK $REF -- "$f" | git apply -3 --index 2>/dev/null || echo "$f" >> $WORK/not-clean.txt
done < $WORK/both.txt
git diff --name-only --diff-filter=U                              # conflict markers to resolve
cat $WORK/failed.txt                                              # paths that aren't the reference's
[ -f $WORK/not-clean.txt ] && comm -23 <(sort $WORK/not-clean.txt) <(git diff --name-only --diff-filter=U | sort)   # didn't apply at all

git checkout -p "$REF" -- <file>                                  # only if a file really must be split
<lint/format command>
git status                                                        # no generated drift
git commit -m "feat(<area>): <ID> <what this slice adds>"
```

Handle every line those three commands print before committing:
- **Conflict markers:** resolve each file by keeping both intents, then `git add` it.
- **Not the reference's:** the path was in the list by mistake, so fix the list. Never `git rm` it: it may be a file only the base has.
- **Didn't apply at all:** one side deleted the file and the other changed it. `split-coverage.sh` reports this as `DECIDE`. Ask the user which wins, then either `git rm` the file or keep the base's version and port the reference's change by hand.

- **One feature commit per slice.** Review fixes go on top as separate commits later.
- **The integration branch:** `git switch -c feature/<ID>-stack-base $BASE`, then `git merge --no-ff <slice>` for each independent slice.
- **A slice built from the fork point:** cherry-pick the lower slices' feature commits onto `$FORK` first, recording their source/copy SHAs, then add the slice's own commit. Later fixes to those sources must reach this slice through B4 even when its PR targets the base directly. For rewritten code, record manual ports with their checks in `reconciliation.md`'s log.

## 6. Check the split

1. **Coverage:** `$SKILL/scripts/split-coverage.sh <base> <reference> <slice-1> … <slice-N>`

   | Report | Meaning | Do |
   |---|---|---|
   | `MISSING` | No slice delivers the file | Add it, unless it's a planned exclusion |
   | `INTERMEDIATE` | A slice has a half-way version | Fix it, unless the plan says so |
   | `REVERTS-BASE` | The slice took the reference's version and dropped the base's change | Redo that file with the three-way merge (expected on a slice built from the fork point) |
   | `CHECK` | Both sides changed the file and it was merged by hand | Check the result by eye |
   | `DECIDE` | One side deleted the file and the other changed it | Ask the user which wins |
   | `EXTRA` | A slice changes a file the reference doesn't touch (including deleting or changing a file only the base has) | Remove it, unless it's planned |

   When resuming an older stack whose slices have since merged the base, add `-i`, and treat the rest as hints rather than errors. This skips base-changed paths and reduces coverage; account for relevant skipped/new-base changes through `reconciliation.md` before landing a cutover. Snapshot coverage does not establish that later review fixes or manually ported behavior survive.
2. **The top of the stack equals the reference** on the reference's files, apart from the base's newer changes and the planned differences.
3. **Every slice builds on its own,** if builds are allowed. If not, `git grep` the definitions of the symbols each slice uses, and say which check you ran.
4. **The "safe to merge" claims hold,** checked with `git grep` on the base.
5. Lint passes on every slice.

## 7. Open the PRs

1. Draft every slice's title and description (`pr-descriptions.md`), with each target from step 4.
2. **Check for existing PRs** from each branch, in any state: `gh pr list --state all --head <branch>`, `glab mr list --all --source-branch <branch>`, or the Bitbucket API. If a PR exists, plan to update it instead of creating a duplicate.
3. Run `safe-push.sh` for every branch (integration branch first). Show the user the whole set together: push plans, titles, targets, and descriptions. Wait for approval.
4. Run the approved push commands, then create the PRs bottom-up. Where the host retargets (rule 10), leave "delete branch after merge" on.
   - GitHub: `gh pr create --base <target> --head <branch> --title … --body-file …`
   - GitLab: `glab mr create --target-branch <target> --source-branch <branch> …` (use `--remove-source-branch` only once you've confirmed GitLab retargets).
   - Bitbucket: the REST API or connector; enable `close_source_branch` only when retargeting behavior is verified and no dependent PR will be lost.
5. Fill in the PR links that were placeholders, after approval, and fill in the stack map (`stack-map.md`).

If the plan grows later, update every PR's `[k/N]` title and its "Part k of N" line in one pass, after approval.
