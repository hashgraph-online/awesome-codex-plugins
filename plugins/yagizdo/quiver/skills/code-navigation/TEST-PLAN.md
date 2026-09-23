# Test Plan -- code-navigation

**Trigger:** Reference skill -- not directly invoked. Used by the `plan`, `review`, and any agent skill that searches the broader codebase.

**Setup:**
- A consumer skill (e.g. `plan` or `review`) loads in a Claude Code session.
- An LSP server is optionally installed for the project's primary language.

**Expected behavior:**
1. Consumer skills run a single navigation detection per session (CodeGraph + LSP) and pass both `codegraph_available` and `lsp_available` flags to every agent prompt that searches the codebase.
2. Agents that include the Code Navigation Strategy block use LSP `goToDefinition` / `findReferences` / `documentSymbol` first when `lsp_available: true`, falling back to grep on empty results.
3. With `lsp_available: false`, agents use Grep / Glob / Read for all navigation.
4. A successful LSP probe is cached as `lsp_confirmed` in project memory at `lsp_preference.md` and reused across sessions; a failed probe prints one line, asks nothing, and caches nothing.

**Verification checklist:**
- [ ] `/plan` and `/quiver:review` both run navigation detection (CodeGraph + LSP) exactly once before agent dispatch (not per agent).
- [ ] At least one dispatched agent prompt contains the literal phrase `lsp_available:` in the agent context.
- [ ] When LSP returns empty results, the agent prints a fallback notice before running grep.
- [ ] Project memory ends up with `lsp_preference.md` after the first detection run that finds a server; a run without one writes nothing and asks nothing.
- [ ] `codegraph_available` flag detected and passed to agents when `.codegraph/` exists.
- [ ] When `.codegraph/` does not exist, `codegraph_available` is false and behavior is unchanged.
- [ ] Locate jobs (where is X / what calls Y / list uses / verify paths) dispatch `quiver:code-locator`; map/convention jobs dispatch `quiver:code-navigator`.

**Known gotchas:**
- A confirmed LSP is cached per project; switching to a different server requires `forget LSP preference` or manual `lsp_preference.md` removal. An absent server is never cached, so installing one later needs no reset.
- Detection is the dispatching skill's responsibility, not the agent's; new agents should NOT re-implement it.
