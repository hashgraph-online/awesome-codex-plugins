Reviewer grounding (optional, fail-open):

When the reviewer MCP server is connected AND its base index is fresh, prefer the
session-less reviewer tools over raw grep/Read to ground cross-file facts — but only
where it pays. When reviewer is absent or the index is stale, silently fall back to
grep/Read; the standalone baseline is unchanged.

- Freshness check (once): `reviewer status <repo-path> --branch <branch> --json`.
  `drift == 0` -> fresh, use the tools; `drift > 0` -> stale, note it and keep going on
  the stale index (do NOT reindex mid-task); `drift == null` or the command fails ->
  no index, fall back to grep/Read.
- Tools: `search_codebase(repo, query, branch?)` — find relevant code by description;
  `callers(repo, node_id, branch?)` — blast-radius: who calls a symbol whose signature
  you are about to change; `related_symbols(repo, node_id, branch?)` — graph neighbours;
  `definition(repo, symbol, branch?)` — where a symbol is defined. `node_id` is `path#fqn`;
  `search_codebase` snippets are headed by it, so feed that id to the graph tools.
- Targeted, not everywhere: skip grounding for small or familiar edits and for files
  already in context — grep is cheaper and Voyage is rate-limited (3 RPM / 10K TPM).
  Reach for reviewer when a change crosses files or touches a shared signature.
- Honesty about freshness: the base index tracks the target branch (base:<branch>),
  NOT your working tree; there is no working-tree overlay for local WIP. Grounding is
  reliable for facts about existing code (planning, callers of an unchanged symbol);
  it is blind to symbols you just edited locally — verify those with Read.
