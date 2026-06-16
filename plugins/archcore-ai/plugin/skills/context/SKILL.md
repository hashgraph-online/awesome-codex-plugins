---
name: context
argument-hint: "[file, directory, topic, or --git-changes; leave empty for current-focus pickup]"
description: "Surface the rules, ADRs, specs, patterns, and reference docs that apply to a code area before changing it — or recap project focus when picking up work. Use for 'what rules apply to X', 'before I touch Y', 'what governs my current changes' (--git-changes), 'pick up where we left off'. With uncommitted changes in play you MAY run --git-changes once per task to load the rules for what you've touched (not per-edit). Not for creating docs, planning, or audits."
---

# /archcore:context

Pull-mode project context. Surfaces the rules, decisions, specs, and patterns that apply to a code area before you change it — or recaps current focus when picking up work.

_Not related to the AI context window or session state — this is about the `.archcore/` knowledge base._

## When to use

- "What rules apply to `src/payments/`?"
- "Before I refactor the auth module, show me what I should know"
- "Show me the decisions for `src/api/`"
- "What rules apply to my current changes / what I just edited?" → `--git-changes`
- "Pick up where we left off"
- "What was I working on in payments?"
- "Where is the checkout work right now?"
- "Load project context"

**Not context:**
- Creating documentation → `/archcore:capture`, `/archcore:decide`
- Planning a feature → `/archcore:plan`
- Detecting stale docs → `/archcore:audit --drift`
- Health audit, counts, or status breakdown → `/archcore:audit` (`--deep` for the full audit)

## Routing table

Classify `$ARGUMENTS` into one mode:

| Signal | Mode |
|---|---|
| Exactly `--git-changes` | **git-changes** |
| Mentions current work: "my changes", "before I commit", "staged", "uncommitted", "what I changed/edited" | **git-changes** |
| Empty or whitespace only | **pickup** |
| Contains `/`, OR matches an existing repo directory | **path** |
| Otherwise | **topic** |

The bare words `changes` or `git` (no leading `--`) stay **topic** — only the exact flag `--git-changes` or the natural-language signals above switch to git-changes mode, which takes its scope from the working tree (Step 2) and falls back to an empty state when git is unavailable.

**Proactive use.** `--git-changes` is the one mode the agent MAY invoke without the user asking: when there are already uncommitted changes and you keep working over them, run it **once per task** to load the rules for what you've touched, then reuse that result. Do NOT re-run it per edit, and do NOT run it on a clean tree (it returns nothing). Every other mode is user-driven.

## Execution

### Step 1: Classify

Determine mode from `$ARGUMENTS` per routing table.

### Step 2: Query

**Git-changes mode:**

Resolve the scope from the working tree, running the resolver once via Bash:

```sh
"${CLAUDE_SKILL_DIR}/../../bin/git-scope" --git-changes
```

`${CLAUDE_SKILL_DIR}` is this skill's own directory (`skills/context/`), set by Claude Code for Bash calls during skill execution; the resolver lives two levels up at the plugin root. On a host that does not set it, resolve `bin/git-scope` relative to this skill file (two directories up). Parse stdout:

- A lone sentinel (`__CLEAN__`, `__NOT_REPO__`, `__NO_GIT__`, `__USAGE__`) → render the matching empty state (Step 6) and stop.
- Otherwise each plain line is a directory; `__TOTAL__ <M>` is the raw directory count for cap reporting.

For each directory, call in parallel `mcp__archcore__search_documents(path_ref="<dir>", limit=10, sort="relevance")` — a smaller limit than path mode, because results aggregate across directories and each matched document carries its full relation graph; a large limit times N directories floods the context. Merge the result sets, dedupe by document path, and tag each result with the directory that surfaced it (used as `via` in Step 5). Then proceed through Steps 3–5 unchanged.

**Ambiguity:** if the mode came from a natural-language signal (not an explicit flag) and the resolver returns `__CLEAN__`, ask one `AskUserQuestion` — "Working tree is clean; did you mean a specific path or topic?" — and reclassify on the answer. An explicit `--git-changes` skips the question and shows the clean empty state.

**Path mode:**

Normalize the argument: trim whitespace, convert `\` to `/`, strip trailing `/`.

Call `mcp__archcore__search_documents(path_ref="<normalized>", limit=50, sort="relevance")`.

**Topic mode:**

Call `mcp__archcore__search_documents(content="<argument>", limit=50, sort="relevance")`.

Topic search is strict substring — singular/plural and near-synonyms do not match. If the first call returns empty, retry once with a shorter or alternate phrasing of the same term before falling through to the empty state.

**Pickup mode:**

Call in parallel:
- `mcp__archcore__search_documents(types=["plan", "idea"], status="draft", limit=10, sort="mtime")`
- `mcp__archcore__search_documents(types=["adr", "rule"], status="accepted", mtime_after="30d", limit=10, sort="mtime")`

If the recent-accepted call returns empty, retry once with `mtime_after="90d"`.

### Step 3: Group

**Path and topic modes** — group results by type:

| Section | Types included |
|---|---|
| Rules | `rule` |
| Decisions | `adr` |
| Specs | `spec` |
| Patterns | `cpat` |
| Reference | `doc`, `rfc`, orphan `guide` (any `guide` not inlined by Step 4) |
| In Progress | `plan` or `idea` with status `draft` |

Drop remaining types — accepted `plan`/`idea`, `task-type`, and vision/requirements (`prd`, `mrd`, `brd`, `urd`, `brs`, `strs`, `syrs`, `srs`). Results are already sorted by `search_documents` (specificity → type priority → mtime); keep the top 5 per section. Inside Reference the same sort applies, so `rfc` (typeRank 3) outranks `guide` (6) and `doc` (17) when specificity ties.

**Pickup mode** — three fixed sections:
- **In Progress** — results from the drafts call
- **Recent Decisions** — `adr` results from the recent-accepted call
- **Recent Rules** — `rule` results from the recent-accepted call

### Step 4: Guide routing

For each item in the Rules, Decisions, or Specs sections, inspect its `incoming_relations`. If a relation of type `implements` or `related` points from a `guide`, inline that guide as an indented bullet under the parent. Skip a guide that is already inlined under a sibling in the same section. Track the set of guide paths inlined this way — any `guide` present in the search results but **not** in this set is an "orphan guide" and is routed to the Reference section in Step 3 instead of being dropped.

### Step 5: Render

```
## Rules (N)
- **<title>** [rule · <status> · <match.kind>]
  `<path>`
  > <excerpt>
  - 📖 **<guide title>** [guide · <status>]

## Decisions (N)
- **<title>** [adr · <status> · <match.kind>]
  `<path>`
  > <excerpt>

## Specs (N)
...

## Patterns (N)
...

## Reference (N)
- **<title>** [<type> · <status> · <match.kind>]
  `<path>`
  > <excerpt>

## In Progress (N)
⚠️  **<title>** [plan · draft]
  `<path>`
  > <excerpt>

_Classified as: <mode>._
```

**Do NOT emit a section header if its group is empty.** The classification footer is always emitted.

**Git-changes mode — two render additions:**

- Under each item add a `  _via: <dir>_` line naming the changed directory that surfaced it (on multiple matches, the most specific dir).
- Replace the footer with `_Classified as: git-changes — <D> dirs._` (append ` (capped at 20 of <M>)` when `__TOTAL__` exceeds 20).

If all sections are empty, fall through to Step 6.

### Step 6: Empty state

- Call `mcp__archcore__list_documents(limit=1)`. If the knowledge base is empty → "No documents indexed yet. Run `/archcore:capture` or `/archcore:decide` to seed `.archcore/`."
- Otherwise → "No documents reference `<scope>`. Consider using `@<scope>` in a rule or ADR so future work in this area surfaces the context automatically."

**Resolver sentinels:**
- `__CLEAN__` → "Working tree is clean — no staged, unstaged, or untracked changes to scope."
- `__NOT_REPO__` / `__NO_GIT__` → "Git scope unavailable here — pass a path or topic instead."
- Resolver returned directories but no documents matched → use the "No documents reference …" message above, scoped by the directory list.

## Result

A grouped markdown surface of the rules, ADRs, specs, patterns, reference docs (`doc`, `rfc`, orphan `guide`), and in-progress work that applies to the requested scope — or a pickup summary of draft work + recent accepted decisions and rules when called with no argument. With `--git-changes`, the scope is derived from the working tree (staged, unstaged, and untracked changes) and the footer reports the directory count. A classification footer identifies which mode was chosen.
