# Stack map template

Fill this in when you plan the split (phase A), and keep it up to date as branches move. Keep it in your notes or scratchpad. Don't commit it to the repo unless the team wants it there.

```markdown
Ticket / epic: <ID>
Host: <GitHub | GitLab | Bitbucket>, merges by <merge commit | squash | rebase>, retargets on merge-and-delete: <yes | no | unchecked>
Base: <main, master, develop, or the project's integration branch>
Reference: <branch> (#<n>, open, unchanged)
Reference tip: <sha>     Fork point: <sha>     Pinned base for cutting: <sha>
Integration branch: <name or "none"> = base + PRs <…>

| # | Branch | PR | Targets | Start point | Other PRs target it? | Layer / owns |
|---|--------|----|---------|-------------|----------------------|--------------|
| 1 | feature/<ID>-01-<slug> | <link> | develop | develop | via stack-base | modules, no callers |
| 2 | feature/<ID>-02-<slug> | <link> | develop | develop | via stack-base | additive API |
| 3 | feature/<ID>-03-<slug> | <link> | feature/<ID>-stack-base | stack-base | **yes: PR 4** | compiled but unused |
| 4 | feature/<ID>-04-<slug> | <link> | feature/<ID>-03-<slug> | PR 3 | no | cutover |

Copied dependencies: <none, or complete the record below>
Cutover branch: <branch>
Cutover starting commit before copies: <sha>
Base tip observed when copies were made: <sha>
Tip after copies, before the cutover's own edits: <sha>

| Source slice / PR | Source tip when copied | Original commit SHA | Copied commit SHA on cutover | Landed base SHA, when known |
|-------------------|------------------------|---------------------|------------------------------|-----------------------------|
| <slice / link> | <sha> | <sha> | <sha> | <sha or not landed> |

Reconciliation: <not needed, or porting-log location>
Last checked: base <sha>, cutover <sha>; unresolved items <…>
Working worktree: <path>
```

The "Other PRs target it?" column lists the PRs to check right after that branch merges (rule 10): are they still open, and retargeted?

Copied dependencies are separate from PR targets. A cutover targeting the base can still need every later fix to its copied slices. Record one mapping per copied commit, including later cherry-picks; preserve the original baseline and append updates. Record manual ports in the porting log rather than inventing a copied SHA. A source branch's deletion or squash landing does not remove the dependency.

When resuming without a map, reconstruct these facts from available commits, patches and landing evidence. Mark missing facts **unknown**; do not guess from commit subjects or replace the original baseline with today's base. Unresolved provenance must remain visible in the readiness report. Use `reconciliation.md` to account for later source/base changes and record verification against exact tips.

## Finding the stack when nobody wrote it down

| Host | Command |
|---|---|
| GitHub | `gh pr list --state all --search "<ID>" --json number,title,state,headRefName,baseRefName` |
| GitLab | `glab mr list --all --search "<ID>"`, or the MRs API (`source_branch`, `target_branch`, `state`) |
| Bitbucket | The REST API or the team's MCP tool (`source.branch.name`, `destination.branch.name`, `state`) |

The `[k/N]` in titles, or the branch numbers (`-01-`, `-02-`, …), give the order.

## Checking branches against their targets

```bash
$SKILL/scripts/stack-status.sh feature/<ID>-01-<slug>:develop feature/<ID>-04-<slug>:feature/<ID>-03-<slug>
```

## Finding which slice owns some lines

Start from the branch the comment is on, with the line numbers as that PR shows them. Pin its tip, then inspect the relevant hunks:

```bash
B=$(git rev-parse origin/<branch>); FILE=path/to/file; LINES=120,160
git blame -L "$LINES" "$B" -- "$FILE"
git show <blamed-sha> -- "$FILE"
git show <original-source-sha> -- "$FILE"   # from the copied-dependency map
```

`git blame` identifies the last recorded change to surviving lines, not their complete intent or the history of deleted lines. Use the source-to-copy map and actual patches to establish ownership; inspect parent versions and rename/deletion history when needed. Matching subjects are only leads: subjects can repeat or change, and a non-match does not prove the change came from the base. Right after a split, `split-coverage.sh -v` also lists each file's first owning slice; a file can contain hunks with different owners.

In zsh, split command output into an array (`B=($(…))`) before passing a branch list to a script, because zsh doesn't split `$var` into words.
