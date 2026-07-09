# Related Operator Runbooks

Bootstrap touches `.agents/` state and `bd` state (and shell rc files only via PATH hygiene, not hook activation — AgentOps 3.0 is hookless). These runbooks cover the operator-side hygiene that bootstrap assumes is healthy on entry. Read the relevant entry when bootstrap reports an unexpected skip, when the operator's environment looks suspicious, or when handing a fresh host to a new agent.

## Index

### `docs/runbooks/path-rationalization.md`

Audits and cleans shell PATH pollution across `.bashrc`, `.zshrc`, `.zshenv`, `.profile`, `.zprofile`, and `.bash_profile`. Walks through inventory, classification, idempotent prepends, subshell verification, and rollback from a timestamped backup.

**When to read:** The host has accumulated many PATH entries, `which ao` or `which bd` resolves to a stale or temp-dir copy, shells are slow to start, or a previous installer has left `/tmp/*-install` lines in an rc file. Run before bootstrap on a long-lived host where the operator has not pruned PATH in a while.

## Adding a runbook to this list

When a new runbook lands under `docs/runbooks/`, add a sub-section above with a one-paragraph description and an explicit "When to read" line. Keep entries scoped to runbooks bootstrap callers actually need — operational concerns adjacent to repo initialization, host hygiene, or the rc files bootstrap may end up touching.

---

> Pattern adopted from `path-rationalization` (ACFS skill corpus). Methodology only — no verbatim text.
