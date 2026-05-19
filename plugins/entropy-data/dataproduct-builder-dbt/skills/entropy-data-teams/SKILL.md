---
name: entropy-data-teams
description: List the teams configured in Entropy Data so the user can pick one as the owner (`team.name` in ODPS) of a data product. Useful when bootstrapping a new data product, integrating an existing dbt project, or just exploring who owns what. Trigger when the user asks "what teams are there", "who can own this data product", "list teams in Entropy Data", or when another skill needs to fill in `TEAM_NAME` and the user does not already know it.
---

# List Entropy Data teams

Print the teams configured in Entropy Data and — if invoked from another skill — return the chosen team so the caller can fill in `TEAM_NAME` (for ODPS) without re-prompting the user.

## How to run this skill

> `${PLUGIN_ROOT}` below refers to the root of this plugin — the directory that contains `skills/`. On Claude Code it is set automatically as `${CLAUDE_PLUGIN_ROOT}` — use that. On any other agent (Codex, Copilot CLI, etc.) it is unset; resolve it as `../..` relative to **this `SKILL.md` file's directory** (i.e. the grandparent of `skills/<this-skill>/`).

### Plan announcement (before Step 0)

Before running Step 0, print this plan to the user verbatim:

> Running **entropy-data-teams**. I'll:
> 1. Pre-checks: verify the `entropy-data` CLI is installed and a connection is configured.
> 2. Fetch all teams from Entropy Data (paginated).
> 3. Apply any filter you mentioned (substring on id/name/description, or type/tag match).
> 4. Show the team list as a Markdown table.
> 5. If invoked as a sub-step by another skill, ask you to pick one and return both `team.id` and `team.name` to the caller.

Then proceed.

### Step 0 — Pre-checks

- `entropy-data --version` is on PATH. If not, surface the install line from the README and stop.
- A connection / API key is configured. If `entropy-data connection list` is empty, tell the user to run `entropy-data connection add ...` first; do not try to authenticate on their behalf.

### Step 1 — Fetch teams

Run:

```
entropy-data teams list -o json
```

The response is a JSON array. Each team has at least: `id`, `name`, `type`, `description`, `members[]`, `tags[]`, `links{}`, `custom{}`.

**Pagination**: `teams list` accepts `--page <n>` (0-indexed). If the response has the same length as the configured page size, fetch the next page and merge until you get a short or empty page. Keep the merged list as `TEAMS`.

If the call fails with auth errors, surface the CLI error and stop — do not retry silently.

### Step 2 — Filter (optional)

If the user gave a hint ("show me platform teams", "find a team for finance"), filter `TEAMS` by:

- substring match on `id`, `name`, or `description`, **or**
- exact match on `type`, **or**
- substring match on any value in `tags[]`.

If the filter eliminates everything, show the full list and tell the user the filter matched nothing.

### Step 3 — Show the list

Print a Markdown table with one row per team. Columns:

| Column | Source |
|---|---|
| `id` | `id` |
| Name | `name` |
| Type | `type` |
| Members | `members.length` |
| Description | first 80 chars of `description` |

Sort by `id` for stable output. If the list is longer than ~30 rows, page it — show 30 and ask whether to continue.

### Step 4 — Optional detail

If the user asks about a specific team, run:

```
entropy-data teams get <id> -o json
```

and pretty-print the full record (members with roles, links, custom fields). Do not store this anywhere — the source of truth is the platform.

### Step 5 — Return value (when invoked as a sub-step)

If this skill was called by another skill that needs a team for `TEAM_NAME`:

1. After Step 3, ask the user to pick one: *"Which team should own this data product? Reply with the `id` from the table above."*
2. Validate the reply against `TEAMS` — if it does not match, list the closest 3 by string similarity and ask again.
3. Return both `team.id` and `team.name` to the caller. The caller decides which one to write into the ODPS file.

If invoked directly by the user (not as a sub-step), stop after Step 3/4 — do not modify any local file.

## When other skills should call this

- **`dataproduct-bootstrap`** Step 2: when batching parameters, if the user does not provide `TEAM_NAME`, offer to invoke `entropy-data-teams` instead of asking for a free-text string.
- **`entropy-data-sync`** Step 3: same — if the project doesn't already have a `team.name` in `<id>.odps.yaml` and the user can't recall the team id, offer `entropy-data-teams`.

A free-text team name is still acceptable (the ODPS schema doesn't enforce that the name matches a registered team), but a value picked from this list is preferred because it stays consistent with the Entropy Data UI and team-scoped views.

## Constraints

- **Read-only.** This skill must not create, update, or delete teams. If the user asks "create a new team", point them at `entropy-data teams put` and stop.
- **Do not modify files.** Even when invoked as a sub-step, return the choice to the caller; the caller decides whether and where to write it.
- **Do not cache.** Always re-fetch from the CLI — team lists change as orgs evolve, and a stale cache is worse than a fresh round-trip.
- **Do not pretty-print secrets.** Some `custom` fields may contain emails or channel identifiers; show them as-is (the data is already in the platform), but do not log them to a separate file.
