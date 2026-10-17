---
name: code-navigation
description: "CodeGraph-first code navigation with LSP and grep fallback. Provides agents with a reusable strategy for semantic code exploration -- codegraph tools when available, LSP goToDefinition/findReferences/documentSymbol otherwise, grep as last resort."
user-invocable: false
---

# Code Navigation

Reference skill for agents that search the broader codebase. Defines when to use LSP vs Grep/Glob and how to handle fallback.

## Navigation Hierarchy

Three tiers, highest precision first. Use the highest available tier for each operation.

| Tier | Tools | Available When | Best For |
|------|-------|---------------|----------|
| CodeGraph | `codegraph_search`, `codegraph_context`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact`, `codegraph_node` | `.codegraph/` exists in project root | Symbol lookup, task-relevant files, call chains, change impact |
| LSP | `goToDefinition`, `findReferences`, `documentSymbol` | Language server installed | Definition jump, reference finding, file structure |
| Grep/Glob/Read | Pattern matching + file reads | Always | File discovery, text patterns, config files, non-code content |

## CodeGraph Operation Catalog

Six semantic operations. For file discovery and text patterns, use Grep/Glob regardless of CodeGraph.

| Operation | Use When |
|-----------|----------|
| `codegraph_search` | Find symbols by name (functions, classes, types) |
| `codegraph_context` | Get relevant code context for a task description |
| `codegraph_callers` | Find what calls a function |
| `codegraph_callees` | Find what a function calls |
| `codegraph_impact` | Assess what is affected by changing a symbol |
| `codegraph_node` | Get details and source code for a specific symbol |

## LSP Operation Catalog

Three semantic operations where LSP outperforms grep. For everything else, use Grep/Glob/Read directly.

| Operation | Use When | Grep Fallback |
|-----------|----------|---------------|
| `goToDefinition` | Find where a function, class, or type is defined | Grep for `function {name}`, `class {name}`, `def {name}`, `const {name}` |
| `findReferences` | Find all callers or consumers of a symbol | Grep for the symbol name (noisier -- includes comments, strings, partial matches) |
| `documentSymbol` | Get a structural overview of a file's exports and symbols | Read the file and parse manually |

**Not covered by this skill** (Grep/Glob is already sufficient):
- File discovery -- use Glob
- Text pattern matching -- use Grep
- Content reading -- use Read

## Agent Instructions Block

Agents that search the broader codebase should include this block in their prompt. The dispatching skill passes `codegraph_available: true|false` and `lsp_available: true|false` as part of the agent's context.

```
## Code Navigation Strategy

You have been provided `codegraph_available` and `lsp_available` flags in your context.

**When `codegraph_available: true`:**
- First, load codegraph tool schemas by calling ToolSearch with query `"select:mcp__codegraph__codegraph_search,mcp__codegraph__codegraph_context,mcp__codegraph__codegraph_callers,mcp__codegraph__codegraph_callees,mcp__codegraph__codegraph_impact,mcp__codegraph__codegraph_node"`. Codegraph tools are deferred and cannot be called without this step.
- For finding symbols by name: use codegraph_search first.
- For understanding what code is relevant to a task: use codegraph_context first.
- For finding callers of a function: use codegraph_callers first.
- For finding what a function calls: use codegraph_callees first.
- For assessing change impact: use codegraph_impact first.
- For getting source code of a specific symbol: use codegraph_node.
- If codegraph returns insufficient results, fall through to LSP (if available) then grep.
- For file discovery and pattern matching: always use Grep/Glob regardless of codegraph.

**When `codegraph_available: false` and `lsp_available: true`:**
- For finding where a function/class/type is defined: use LSP goToDefinition first.
- For finding all callers or consumers of a symbol: use LSP findReferences first.
- For getting a structural overview of a file: use LSP documentSymbol first.
- If LSP returns empty or unhelpful results for any operation, inform the user:
  "LSP returned no results for {operation} on `{symbol}` -- falling back to grep-based search."
  Then use the grep equivalent from the catalog above.
- For file discovery and pattern matching: always use Grep/Glob regardless of LSP availability.

**When both unavailable:**
- Use Grep, Glob, and Read for all code navigation.
```

## Skill-Level Navigation Detection

Skills that dispatch code-exploration agents (`/plan`, `/quiver:review`) run this detection once before agent dispatch. Results are passed as `codegraph_available` and `lsp_available` flags to `quiver:code-navigator` and other agents that search the codebase.

### CodeGraph Detection Flow

1. Check if `.codegraph/` directory exists at project root.
2. If exists: set `codegraph_available=true`.
3. If not: set `codegraph_available=false`. No user prompt -- CodeGraph is a passive enhancement.
4. Pass `codegraph_available` alongside `lsp_available` to all dispatched agents.

### LSP Detection Flow

1. **Check project memory** for cached LSP preference.
   - If `lsp_confirmed` found: set `lsp_available=true`, skip to step 4.
   - A negative result is never cached (see step 3), so nothing else short-circuits here.

2. **Attempt an LSP probe.**
   - Try a lightweight LSP call (e.g., `documentSymbol` on any source file from the project root).
   - If LSP responds with results: set `lsp_available=true`, cache `lsp_confirmed` in project memory, skip to step 4.

3. **LSP not available -- continue with grep.**
   - Set `lsp_available=false`.
   - Detect the project language from manifest files (`package.json`, `Gemfile`, `requirements.txt`, `pubspec.yaml`, `go.mod`, `Cargo.toml`, `Package.swift`, etc.) and print one line naming the recommended server from the table below:

     `> LSP not available; using grep. Install {recommended_server} for {language} to enable go-to-definition and find-references.`

   - No `AskUserQuestion`. LSP is an enhancement, and a question here stops every skill that runs detection, including one another skill invoked with no user at the prompt. Do not cache the negative result: the probe is a single call, and a server installed later is picked up by the next run.

4. **Pass `lsp_available` flag** to all dispatched agents as part of their context.

### Language Server Recommendations

| Language | Recommended Server | Install Command |
|----------|-------------------|-----------------|
| TypeScript/JavaScript | typescript-language-server | `npm install -g typescript-language-server typescript` |
| Python | pyright | `npm install -g pyright` or `pip install pyright` |
| Go | gopls | `go install golang.org/x/tools/gopls@latest` |
| Rust | rust-analyzer | Install via rustup or IDE extension |
| Swift | sourcekit-lsp | Included with Xcode |
| Dart/Flutter | dart language-server | Included with Dart SDK |
| Ruby | solargraph | `gem install solargraph` |
| Java/Kotlin | jdtls | Install via IDE or manually |

### Memory Caching

LSP preference is stored in project memory:

- **File:** `lsp_preference.md` in the project's auto-memory directory
- **Content:** `lsp_confirmed`, which language server responded, date cached. Only a successful probe is written; an absent server is re-probed on every run.
- **Lifetime:** Persists across sessions. User can reset by saying "forget LSP preference" or by removing the file; installing a server needs no reset.

## For Agent Authors

If your agent searches the broader codebase (beyond files it already knows about), reference this skill:

1. Add the **Code Navigation Strategy** block from above to your agent's prompt.
2. Ensure the dispatching skill passes `codegraph_available` and `lsp_available` context to your agent.
3. Your agent does NOT need to handle LSP detection -- that is the skill's responsibility.

## Locate vs Map

Two agents serve code navigation. Pick by output need:

| Job | Agent | Output |
|-----|-------|--------|
| Where is X defined / what calls Y / list uses of Z / map a directory / verify a path | `quiver:code-locator` | Compressed `path:line -- symbol -- note` table |
| Conventions, patterns, planning context, feature impact | `quiver:code-navigator` | Structured file:role:pattern report with Key Conventions and Gaps |

Both agents use the tier strategy from this skill (codegraph -> LSP -> grep). `code-locator` runs on `haiku` and refuses convention extraction; `code-navigator` runs on `inherit` and emits the full map `/plan` consumes.
