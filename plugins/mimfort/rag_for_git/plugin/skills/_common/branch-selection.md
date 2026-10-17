Branch selection for code search (shared):

- Determine the current git branch: `git branch --show-current`.
- If it is in `REVIEW_BRANCHES` (the tracked branches list), pass it as the
  `branch` parameter — the search uses that branch's index.
- If the user explicitly named a branch, use that one instead.
- Otherwise omit `branch` entirely — the server uses the primary branch (the
  first entry in `REVIEW_BRANCHES`).
- Pass the same `branch` to the graph tools (`callers` / `related_symbols` /
  `definition`) — identically (or omit it identically).
