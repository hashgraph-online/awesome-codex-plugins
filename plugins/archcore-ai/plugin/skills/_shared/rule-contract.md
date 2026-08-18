# Rule Content Contract

Plugin runtime asset. Loaded before composing any `rule`:
`decide` (standard cascade in `skills/decide/references/continuations.md`),
`init` (Tier-2 cross-cutting rules, per `magic-first-day-init.adr`). Companion to
`skills/_shared/precision-rules.md` — its forbidden lexicon (Rule 1), imperative-voice
mandate (Rule 2), and no-cross-document-section rule (Rule 5) all bind here.

## What a rule is

A **team-wide normative constraint** on how code, docs, or process MUST behave, applying
across many files or situations — not a one-off. A rule exists so that an agent editing a
matching file is told the binding constraint *before* writing, and so push-mode injection
(the CLI's code-alignment PreToolUse hook) can surface it against the changed paths. One primary constraint
per rule document. Distinguished from:

- a `spec` — the normative behavior of one subject others rely on (an interface/schema
  boundary, or a feature/subsystem), not a cross-cutting practice;
- an `adr` — records *why* a choice was made; a rule states *what is now binding*.

A rule that cannot be checked, or that only restates a language/linter default, is not
worth writing.

## When NOT to write a rule

- A one-off preference for a single file or PR → fix it in review, write no rule.
- The reasoning / tradeoff behind a choice → `adr` (then a rule MAY `implements` it).
- The contract of one interface, schema, or protocol → `spec`.
- Sequential how-to ("first do X, then Y") → `guide`.
- Non-normative reference (registry, table, glossary) → `doc`.
- A constraint already enforced by the compiler/linter with no added intent → omit.

## Mandatory sections

Align with the `create_document` `rule` template (`Rule`, `Rationale`, `Examples`,
`Enforcement`):

1. **Rule** — one or more numbered imperative statements in RFC 2119
   (`MUST` / `MUST NOT` / `SHOULD` / `MAY`). Each MUST be **falsifiable** (a reviewer can
   point to a violating line) and **code-grounded** (names a real path, glob, identifier,
   or API). Each statement MUST make its **applies-to scope** explicit — the paths/globs
   (`src/**/*.tsx`) or named situation ("any function that opens a DB connection") it
   governs — so injection can target it. Narrative voice ("we should", "следует") is
   forbidden in this section (precision Rule 2). Keep a statement at or under 25 words
   and put the trigger before the response (precision Rule 7).
2. **Rationale** — WHY, 1–3 lines. Cite the incident, limit, or authority that justifies
   the constraint. No hand-waving; no restating the rule.
3. **Examples** — a `Good` and a `Bad` block. Code blocks ARE allowed and expected here
   (precision Rule 6): the violating vs. compliant form is the artifact. The Bad block
   MUST be a realistic violation, not a strawman.
4. **Enforcement** — how the rule is checked: a named hook, lint rule, CI step, or test
   (with its identifier), or `manual review` if none exists. Name the verifier per
   directive where they differ.

## Forbidden in the body

- Burying rationale inside a `MUST` statement — move *why* to **Rationale**.
- Vague lexicon (`appropriate`, `robust`, `properly`, `as needed`, …) anywhere
  (precision Rule 1).
- A section enumerating other `.archcore/` documents (`## Related Rules`,
  `## References`) — cross-document links live in the relation graph via
  `mcp__archcore__add_relation` (precision Rule 5). The body MAY cite `@path/to/file`,
  commits, runbooks, and the rule's own enforcement artifacts.

## Enforcement

The Archcore CLI reports the mechanical part of this contract in the post-tool-use
hook: the mandatory sections, two modals in one numbered statement, a condition
placed after the obligation, a statement past 25 words, an open-ended list, an
Enforcement section naming no verifier, and a Rule section naming no path or glob
anywhere. A CLI that predates a check reports nothing for it, and no version
blocks a write.

The scope check is deliberately document-level. This contract accepts a **named
situation** as scope, which is prose that no pattern finds — asking each statement
for a machine-readable anchor reported four rules in five, nearly all of which do
state their scope, in a sentence. What the hook decides instead is narrower and
true: a rule that names no file target anywhere cannot be matched to an edited
path in push mode. Whether a *particular* statement carries its scope stays with
review.

## Rationale

RFC 2119 statements + Good/Bad examples + a named verifier make a rule *checkable*: a
reviewer or hook can decide conformance without re-litigating intent. The explicit
applies-to scope is what lets the code-alignment hook match a rule to an edited file in
push mode — a rule with no scope cannot be injected and silently never fires.

## Examples

### Good

````markdown
## Rule
1. Every function that acquires a pool connection (`pool.acquire`, `pg.connect`) MUST
   release it in a `finally` block before returning. Applies to `src/**/*.ts`,
   excluding `src/**/*.test.ts`.

## Rationale
The pool caps at 20 connections; a leaked connection 503s the gateway once exhausted
(incident 2024-02, runbook `@docs/runbooks/db-pool.md`).

## Examples
### Good
```ts
const c = await pool.acquire();
try { return await c.query(sql); } finally { c.release(); }
```
### Bad
```ts
const c = await pool.acquire();
return await c.query(sql); // leaked on the return path
```

## Enforcement
`eslint-plugin-archcore/no-unreleased-connection` (CI, blocking); manual review for
dynamically-named acquires.
````

### Bad

````markdown
## Rule
We should always handle connections properly and avoid leaks where appropriate.

## Enforcement
Be careful.
````

(Narrative voice instead of `MUST` (Rule 2); vague `properly` / `appropriate` (Rule 1);
no applies-to scope, so it cannot be injected; no Good/Bad code; unenforceable. Either
rewrite as a falsifiable `MUST` with a scope and a named check, or — if it is a one-off —
fix it in review and write no rule.)
