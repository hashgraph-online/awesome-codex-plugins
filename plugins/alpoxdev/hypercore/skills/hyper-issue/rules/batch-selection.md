# Batch Selection

Use this rule when a selection condition, issue numbers, or a batch is named. It owns the fixed list, the query or the number expansion, dedupe, the lane grouping, the manifest write, and the hand-off to `hyper`.

## 1. Freeze The List

1. Turn the user's words into one complete query. Keep every term they gave; add only the repository scope and the open-state filter.
2. Collect the complete result: every page, pull requests excluded, and the total checked against the number of rows returned.
3. Stop on a capped, partial, or failed collection. Report the limitation; never silently narrow the query or take the first page.
4. Deduplicate by repository and issue number, and keep first-occurrence order as the canonical order.
5. The list is frozen at this point. Later discoveries are reported as new candidates for the next batch, never added here.

An empty complete result ends the batch with no lanes and no manifest beyond a one-line note.

## 1b. Freeze The List From Numbers

When the user names issue numbers instead of a query, the numbers are the list.

1. Expand every form to explicit numbers, inclusive: `#1~3`, `#1-3`, `#1..3`, and `1~3번` become `1, 2, 3`; `#1, #4, #7` and `#1 #4` stay as written. Mixed forms combine (`#1~3, #7` is `1, 2, 3, 7`).
2. A range whose end is lower than its start, or one that expands past 50 numbers, is reported as the blocker and no list is frozen.
3. Read each number once from the tracker (number, title, state, body, labels, and whether it is a pull request).
4. Keep a number only when it is an open issue. Record each excluded number with its reason: `pull request`, `closed`, `not found`, or `read failed`. A read failure is retried once after a tracker read confirms the outage; it is never treated as "not found".
5. Keep the user's order after expansion as the canonical order, deduplicated. The list is frozen once every number has a kept or excluded outcome.
6. A kept issue whose body lacks the `hyper:` block or a required section is completed in English by `rules/issue-contract.md` as an update of that issue, with one write and one re-read. Under `--no-write`, or when the update fails, re-derive the write set from its `## Scope` and mark the row `block: missing` instead.

A list with no kept issue ends the batch with a one-line note listing every excluded number and its reason.

## 2. Re-derive The Graph

The `hyper:` blocks are the input; the edges are computed, never trusted blindly.

1. Read each issue's `hyper:` block. An issue with no block is a gap: re-derive its write set from its `## Scope` and mark the manifest row `block: missing`.
2. Build `touches` overlap edges: two issues whose `touches` share a path or one glob covers the other's path.
3. Merge with the declared `depends_on` and `conflicts_with` edges.
4. A cycle among issues is a blocker. Report it with the issue numbers and stop that component; do not invent an ordering.

## 3. Group Lanes

A lane is one write set processed in a fixed order. Lanes run in parallel; the issues inside a lane run in order.

1. Connected components of the overlap graph become lanes. An issue with no edge is its own lane.
2. Order each lane topologically. Two issues with no path between them go in declaration order, lower issue number first.
3. Cap the lane count at the local concurrency limit, defaulting to four. Excess lanes queue and their issues keep their lane order.
4. Prefer the issue `lane_hint` for the lane name when it is unique; otherwise use `<lowest-issue-number>-<short-slug>`.

Do not merge two lanes to reduce their count. Do not put two issues that share a path in different lanes.

## 4. The Manifest

Write `.hyper/issues/<slug>/batch.md` from `references/batch-manifest.md`. It carries:

- the exact query and the collection completeness evidence, or the numbers as written and their expansion
- the canonical fixed list with number, title, class, lane, size, and verify command
- the lane table with each lane's order and union of written paths
- the blockers: excluded numbers, missing `hyper:` blocks, cycles, and issues needing a split
- the handoff line the next stage reads, naming whether `hyper` is loaded next

## 5. What The Batch Does Not Do

- It never implements, branches, commits, or pushes; after the hand-off those belong to the stages `hyper` runs.
- It never reopens a closed issue or adopts an existing branch as its own.
- It never adds an issue to the frozen list because the implementation turned out to be easy.
- It never removes an issue because it looks blocked; it records the blocker.

## 6. Hand-Off To `hyper`

The hand-off applies when the trigger table in `SKILL.md` says so: issue numbers by default, or a record or selection condition with work words. It never applies with `--from-hyper`, `--no-run`, `--draft-only`, or when no kept issue exists.

1. Confirm the manifest exists on disk and at least one lane is runnable. A batch whose every lane is blocked ends at the manifest with the blockers reported.
2. Load the installed `hyper` skill by name in the same session. Pass this request, filled in, in English:

   ```text
   Implement the issue batch fixed in .hyper/issues/<slug>/batch.md.
   - Issue stage: done by hyper-issue; the manifest is the fixed input and its list must not change.
   - Lanes: run each lane in the manifest's Lane table as one parallel lane, and its issues in the listed order.
   - Gates: each issue's verify command is its acceptance check; a blocked lane does not stop the other lanes.
   - Delivery: <the user's delivery words unchanged, or "local">.
   - Pull requests, when opened, carry `Closes #<n>` for every issue they finish.
   ```

3. Record the hand-off in the manifest's `## 핸드오프` section: `다음 단계: hyper (넘김)` and the time.
4. This skill's run ends at the hand-off. It does not wait on, re-check, or re-enter the `hyper` run; the closing report belongs to `hyper`.
5. When the `hyper` skill is not installed or cannot be loaded, stop at the manifest and report `npx skills add alpoxdev/hypercore --skill hyper`.

## Sources

> Checked 2026-11-07.

|Claim|Source|
|---|---|
|A fixed canonical list collected once, with later discoveries excluded, and a complete collection required before dispatch|[kdy1-scripts slop-fix-batch](https://github.com/kdy1/kdy1-scripts)|
|Dependency components become one stack; independent components start separately|same, `references/construction.md`|
|Declared `conflicts_with` plus a single owner for shared files|[automazeio/ccpm](https://github.com/automazeio/ccpm)|
|Conflicts are frequent between concurrent agent changes, and roughly 42% are structural|[AI Agent PRs on GitHub](https://arxiv.org/abs/2607.04697)|
|Cap the fan-out and declare the join shape|`instructions/graph-engineering/GRAPH_ENGINEERING.md`|
|Issue numbers as a batch trigger and the automatic lane hand-off to `hyper`|user instruction, 2026-11-07|

### Evidence grade

`LOCAL` - the lane cap, the number expansion, the 50-number bound, the manifest fields, and the hand-off request are this package's design. The freeze rule and the component grouping are adapted from the named prior art.
