---
name: loom-code
description: >
  Use the moment you are about to grep, glob, or open files to answer a
  question about a loom-indexed codebase — "where is X", "how does X work",
  "who calls Y", "is it safe to change Z", "what does this stack trace
  touch". The tell is linguistic: if you just thought "let me search the
  codebase", "let me grep for that", or "let me read a few files", that
  sentence is the trigger — code.grep covers exact literals too. NOT for
  repos loom hasn't indexed (a code.search that abstains on everything is
  the tell), and NOT for your own uncommitted files (grep those; pass your
  diff to code.impact for blast radius). NOT for LOCAL-FIRST sessions.
---

# loom-code — the indexed answer before the grep reflex

If the startup primer says LOCAL-FIRST, use local grep/Read; the code guard
stands down. Use Loom only when asked about upstream, naming the indexed commit.

Loom indexes this codebase (symbols, call graph,
tests, PR history), served as MCP tools. Choose the operation that answers the question; do not call tools just to
show use. Static callers and impact can be lower bounds. Follow this routing even
without hooks. A hook may supply evidence or redirect a local lookup; reuse that
evidence when it answers the question.

If a hook or the current prompt already supplied sufficient evidence, use it
without repeating the lookup. Skip code retrieval for memory-only questions,
ordinary chat and self-contained tasks. Use memory tools for saved decisions.
If the needed code tool is deferred, use client tool discovery (ToolSearch in
Claude Code). A definition does not supply its callers. Retrieve the missing
evidence, then stop. Quoting an identifier or error in a code question does not
make it a literal-search request.

## The tools (MCP names)

| Question | Call |
|---|---|
| where is X defined / its signature and doc | `loom_code_symbol` (`name`) |
| what could changing X affect | `loom_code_impact` (`name`, or the current diff) |
| who calls X | `loom_code_callers`, or `loom_code_symbol` with `uses_brief: true` |
| a concept with no greppable keyword ("where do we retry s3 uploads") | `loom_code_search` |
| an exact literal or error string | `loom_code_grep` (each hit with its enclosing symbol) |
| what is in a file | `loom_code_outline` (`path`) — then read one span |
| the function around a `path:line` | `loom_code_symbol` with `name="src/F.cpp:123"`, or `loom_code_enclosing` |
| how does X work, in prose, with citations | `loom_code_ask` |
| a bundle for a task (symbols, callers, tests, history) | `loom_code_context_pack` |

Pass `namespace` when the session primer names it. The MCP code tools infer
`org` from the token. Grep UNCOMMITTED or unindexed files; abstention permits local fallback.

## Reading a result

- `abstain: true` is an answer ("nothing relevant"); do not retry with
  synonyms more than once — grep instead.
- `as_of` names the indexed commit. Line numbers are that commit's; when the
  session primer says your checkout is behind, report them as the index's.
- Caller and impact counts are floors: static evidence may miss dynamic calls.
  A structural claim ("nothing calls X") needs `loom_code_callers`
  evidence, not a hunch.

## Stop rules

- Read a returned span only to close a specific evidence gap; do not
  chain callers + impact + history as a ritual.
- If two loom calls in a row did not move you forward, grep.

The full substitution table (impact, test_gate, pr_check, trace, verify,
outline, grep neighbours) and the verification gate are in `reference.md`
beside this file; open it only when one of those rows is what you need.
