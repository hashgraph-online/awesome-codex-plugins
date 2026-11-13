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
  diff to code.impact for blast radius).
disable-model-invocation: true
---

# loom-code — the indexed answer before the grep reflex

Loom holds a compiler-grade index of this codebase (symbols, call graph,
tests, PR history), served as MCP tools. One call replaces a grep plus
several whole-file reads and returns what grep cannot see: resolved callers,
blast radius, the tests that reach a function. The `loom-code-shunt` hook
enforces the substitutions mechanically (a symbol grep or a bulk read in an
indexed repo is denied with the answer or the tool to call).

## The tools (MCP names)

| Question | Call |
|---|---|
| where is X defined / its signature and doc | `loom_code_symbol` (`name`) |
| who calls X | `loom_code_callers`, or `loom_code_symbol` with `uses_brief: true` |
| a concept with no greppable keyword ("where do we retry s3 uploads") | `loom_code_search` |
| an exact literal or error string | `loom_code_grep` (each hit with its enclosing symbol) |
| what is in a file | `loom_code_outline` (`path`) — then read one span |
| the function around a `path:line` | `loom_code_symbol` with `name="src/F.cpp:123"`, or `loom_code_enclosing` |
| how does X work, in prose, with citations | `loom_code_ask` |
| a bundle for a task (symbols, callers, tests, history) | `loom_code_context_pack` |

Pass `namespace` when the session primer names it. The MCP code tools infer
`org` from the token. For your own UNCOMMITTED files, grep. In a repository
the index does not cover, grep —
the abstentions will tell you.

## Reading a result

- `abstain: true` is an answer ("nothing relevant"); do not retry with
  synonyms more than once — grep instead.
- `as_of` names the indexed commit. Line numbers are that commit's; when the
  session primer says your checkout is behind, report them as the index's.
- Caller and impact counts are floors: dynamic dispatch is invisible to any
  static tier. A structural claim ("nothing calls X") needs `loom_code_callers`
  evidence, not a hunch.

## Stop rules

- One clear hit plus one focused read of the returned span is enough; do not
  chain callers + impact + history as a ritual.
- If two loom calls in a row did not move you forward, grep.

The full substitution table (impact, test_gate, pr_check, trace, verify,
outline, grep neighbours) and the verification gate are in `reference.md`
beside this file; open it only when one of those rows is what you need.
