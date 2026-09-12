
<skill id="refactor">

<prerequisite>
AgentDB read-start has run. Check for prior refactor attempts on same code.
</prerequisite>

<reference>
Skill-specific: skills/build/reference/refactor-research.md
General: reference/architecture-research.md
</reference>

<flow>

1. **Baseline** — run full test suite. (gate: all tests green before touching anything)
2. **Scope audit** — grep/glob every instance of the target symbol/pattern across the codebase. List them ALL before changing ANY.
3. **Count files** → determine tier. 1-2 files: execute directly. 3-5 files: write one-paragraph plan. 6+ files: CONFIRM handshake.
4. **Define success** — write down EXACTLY what changes. Anything outside that list is scope creep → separate contract.
5. **Check coverage** — if target code has no tests: generate JiT behavioral tests FIRST (see step 6), run them green, then proceed.
6. **JiT tests (when needed)** — ask Claude to generate behavioral tests for current code (what it *does*, not how). Run green. These are disposable; delete after if not worth keeping. (gate: JiT tests pass before refactor starts)
7. **Execute — one transformation per commit:**
   - Extract function: only at 3+ repetitions (Rule of Three)
   - Inline: wrapper with exactly one call site → inline it
   - Rename: state full scope explicitly — ALL files, imports, tests, docs (Opus follows literally; ambiguous scope = partial refactor)
   - Move: code in wrong module → move to correct location
   - Simplify conditional: nested if/else → guard clauses / early return
   - Remove dead code: unused code → delete (no "just in case")
8. **Agentic safety checks** (after each transformation):
   - Phantom abstraction: abstraction with one call site → inline, wait for second use
   - Comment drift: audit every comment for accuracy — stale comments worse than none
   - Parallel agent artifacts: if multiple agents touched the file, check `git log` for overlapping changes
   - Scope creep: diff changes against the defined list from step 4; extras → revert + new task
   - AI behavior drift: AI rewrites change edge-case behavior even when asked to preserve it. After any AI-assisted refactor, run the original input set (or quick property tests) against both versions. Functional equivalence on happy paths does not imply equivalence on edges. <!-- Updated 2026-06-18: https://www.sitepoint.com/debugging-ai-claude-code-vs-traditional-methods/ -->
9. **Verify** — run full test suite. (gate: all tests green after each commit; red = stop, revert last change)
10. **Metrics** — measure before/after: cyclomatic complexity, function length, duplication. Successful refactor reduces complexity 15-25%. No improvement = shuffled, not simplified.
11. **Commit** — one logical change per commit. Format: `refactor(scope): description`. File must end shorter or justify growth in commit body.

</flow>

<anti_patterns>
<block id="big_bang">Large refactors in one commit. Impossible to review or revert.</block>
<block id="no_tests">Refactoring without test coverage. You can't verify behavior preservation.</block>
<block id="feature_mixing">Adding features during refactor. Separate concerns, separate commits.</block>
<block id="premature_abstraction">Abstracting before you have 3 concrete examples. Wait for patterns to emerge.</block>
<block id="refactor_while_there">"While I'm here, I'll also..." No. Separate contract.</block>
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"refactor","type":"<extract|inline|rename|simplify>","files_touched":<N>,"tests_status":"green","behavior_changed":false}'

Record what was refactored and verify tests remained green throughout.
</on_complete>

</skill>
