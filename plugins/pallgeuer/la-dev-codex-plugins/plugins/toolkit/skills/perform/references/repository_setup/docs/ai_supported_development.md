# AI-supported repository development

For project configuration, see [Language-agnostic project setup](project_setup_agnostic.md) and [Python project setup](project_setup_python.md). For a new empty or essentially empty repository, follow the [New repository setup recipe](new_repo_recipe.md). With Toolkit installed and enabled, start it in a Plan-mode chat with `$toolkit:perform setup-new-repo`.

AI-supported development works best when the repository carries its own durable feedback. A correction made only in one conversation is easily lost; a correction encoded in a tool, test, or concise instruction improves every later change.

The general rule is to express each requirement at the strongest practical enforcement level. Prefer deterministic, fast, and reusable checks over prose, and prefer prose over relying on someone to remember a prompt.

## Use an enforcement ladder

Apply the first suitable option in this order:

1. **Adopt a standard project-independent tool.** Use established formatters, linters, type checkers, documentation formatters, security scanners, and similar tools as extensively as practical. Tools such as Ruff, ty, and pydocformatter provide precise feedback, require little project-specific explanation, and make many classes of mistakes impossible to merge.
2. **Extract a reusable check or formatter.** If a mechanistic rule is not covered by an existing tool but is useful across projects, implement it once as a focused reusable tool, like this repository's [Markdown table formatter](markdown_tables.md), [pytest working-directory isolation](pytest_isolation.md), and [release checksum generator](release_checksums.md). Expose a checking mode for CI and, where safe, an auto-fixing mode for development. Make the same implementation callable from pytest or pre-commit or miscellaneous code rather than duplicating its logic in each integration.
3. **Encode project-specific contracts in tests.** Use pytest to lock down repository structure, metadata consistency, generated-file freshness, supported combinations, architectural boundaries, documentation invariants, and other project-specific rules that can be evaluated mechanically. For complicated but repeated project-specific checks, build repo-wide parsing and fixing support and exercise that support from the tests.
4. **Write a specification or instruction.** When a requirement depends on judgment or is too difficult to check reliably mechanistically, document it as a project rule. Put a very concise rule in `AGENTS.md`, and if necessary, put any further substantial guidance in a focused specification file linked from `AGENTS.md`, with a clear trigger condition when to read this specification file.
5. **Keep a repeatable AI workflow.** When a recurring development task requires contextual reasoning or original edits, preserve the exact prompt and its operating conditions using [Perform](codex_perform.md), instead of freestyling it every time you need it.
6. **Use review for the remaining judgment.** Run [Loupe](loupe.md) before committing every non-trivial change, and consider using its diff summary line as the future git commit message. Human review remains important for intent, product trade-offs, security-sensitive behavior, and other decisions for which passing checks is necessary but not sufficient. Human review can be done by manually staging all git diff hunks or files one at a time that you accept.

This order is a preference, not an infallible rule. A clear `AGENTS.md` instruction may be the correct choice when enforcement would be fragile, slow, or harder to maintain than the underlying rule.

## Turn corrections into repository memory

Treat repeated AI mistakes as evidence that feedback is missing or is arriving too late. After correcting a problem, ask:

- Can an existing generic tool detect or prevent it?
- Can a small deterministic check or safe auto-fix detect it?
- Is that check project-independent enough to extract and reuse?
- Does a project-specific regression or contract test express the intended behavior?
- If it requires judgment, should it become concise guidance or a repeatable workflow?

Tests become the executable memory of stable design decisions made while steering development. Add them for intentional behavior and important failure modes, including regressions discovered during AI-supported work. Avoid freezing incidental implementation details, exact prose, or broad snapshots unless those outputs are themselves part of the contract. A brittle test can steer later work just as strongly as a useful one, but in the wrong direction.

Run fast checks locally and the complete authoritative suite in CI. Pin or otherwise control tool versions where reproducibility matters, and ensure diagnostics explain what failed and how to repair it. An AI can respond much more reliably to a focused failure than to an undocumented convention or a vague all-purpose test.

## Keep `AGENTS.md` concise and actionable

Add a rule to `AGENTS.md` when an AI has made the mistake more than once, or when a single occurrence was costly or annoying to recover from. Phrase rules as observable instructions with clear scope. Link to a dedicated document when examples, rationale, or exceptions would make the root file unwieldy.

Regularly audit every instruction and linked development guide:

- Could the requirement now be checked mechanistically?
- Will a violation produce feedback that tells the AI how to fix it?
- Is the instruction still correct, unambiguous, and non-duplicative?
- Does it conflict with a tool, test, nearer-scoped instruction, or current repository behavior?

Remove instructions that are obsolete or fully superseded by reliable automation. Do not keep both prose and a check unless the prose helps contributors understand intent or use the check correctly.

## Maintain sticky prompts and workflows

A sticky prompt is a recurring instruction that should survive beyond the current conversation. Make a prompt sticky whenever you ask an AI to restore correctness, alignment, or consistency that future changes could cause to drift again (and that cannot be made into pytests or automated checks instead).

Maintain a small catalogue of these workflows and periodically promote each one to the most durable suitable form:

- Replace verification-oriented workflows with deterministic tools or pytest checks when possible.
- Package project-independent workflows as a shared focused skill (e.g. as part of a plugin marketplace) or as a [Perform](codex_perform.md) action, depending on their complexity and cohesion.
- Package self-contained, project-specific workflows that need no human interaction as project-local skills.
- Keep the remainder in a dedicated Markdown file. For each workflow, record when to run it, its scope and expected outcome, suitable coding and planning reasoning levels, whether the context should be cleared first, and the order of commands when it is a multi-step workflow.

Keep workflows narrow enough that success is verifiable. If a workflow changes files, pair it with explicit checks and require it to summarize the affected scope so that omissions and unexpected expansion are visible.

## Design out drift

Look for facts and decisions represented in more than one place: default values repeated in code and documentation, version lists copied across configuration files, duplicated compatibility claims, generated catalogs, or tables that mirror implementation state.

Prefer one authoritative source and derive the other representations from it. When generation would make the repository harder to understand or maintain, add a focused consistency test instead. For example, a pytest can compare defaults displayed in a Markdown table with the defaults exported by the implementation.

Checks for drift should compare semantics rather than fragile text whenever possible. Reuse the production parser or a shared library when that is safe; otherwise keep the test implementation independent enough that it can detect the same defect rather than reproduce it. Include negative cases and useful failure messages so both humans and AI agents can identify the mismatched sources quickly.

## Apply the loop to every non-trivial change

For each change:

1. State the intended behavior and identify the source of truth.
2. Make the smallest coherent implementation and documentation update.
3. Add or update stable regression and contract checks.
4. Run formatters, linters, type checks, focused tests, and then the appropriate broader suite.
5. Check for new duplicated facts, stale generated content, or other drift risks introduced by the change.
6. Run the applicable sticky workflows that have not yet been automated.
7. Use Loupe to review every non-trivial change before committing, then resolve or consciously reject each actionable finding.

When a review or later failure exposes a recurring problem, feed it back into the ladder. Over time, the repository should need fewer remembered corrections because its tools, tests, specifications, and workflows make the desired development behavior increasingly explicit.

Use temporary markdown documents in a dedicated gitignored directory for intermediate storage of AI plans, progress, ideas, or as a live journal.
