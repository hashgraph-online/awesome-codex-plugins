# Refactoring

Change code structure (rename, extract, inline, deduplicate, move) while everything callers can observe stays the same. You hold the behavior contract fixed while the shape changes.

Use this for a small to moderate structural change where behavior must stay identical. New behavior goes to [Feature](feature.md), and wrong behavior goes to [Bug fix](bug-fix.md). Broad work across many call sites goes to the `figure-it-out` skill ([../../figure-it-out/SKILL.md](../../figure-it-out/SKILL.md)). An intentional redesign is allowed, but call it a redesign and route it to Feature.

Inputs: the code area and the structural outcome wanted.

## Steps

0. **Keep scope clean.** If you find a missing capability or a real defect along the way, split it off. Ship the structure-only change first, checked against the locked behavior, and handle the other item separately. Report any security defect you find to the user at once, with its location.

1. **Lock behavior before moving anything.** Run the `how` skill ([../../how/SKILL.md](../../how/SKILL.md)) on the subsystem to learn what it promises. Capture what the code does today, using whichever fits: a characterization test, a snapshot, or a harness that compares old and new output. Where the area has no tests, write this capture before anything else. A passing type checker or linter is not a lock. If the code sits on a trust boundary (input parsing, authorization checks, escaping, session handling), the lock must include the rejection cases: malformed input, missing permissions, and hostile values. A happy-path-only lock lets a refactor drop a guard unnoticed.

2. **Name the missing structure.** Use [principle-model-the-domain](../../principle-model-the-domain/SKILL.md) to find what is absent: a state machine, a typed model, a registry, a reducer, a boundary, or a better-fitting collection. Leave plain, contained code alone. A valid reshape removes branches or impossible states. One that only adds indirection does not count.

3. **Describe the destination.** Sketch the modules, types, and call graph as if you were writing the code fresh today ([principle-foundational-thinking](../../principle-foundational-thinking/SKILL.md), [principle-redesign-from-first-principles](../../principle-redesign-from-first-principles/SKILL.md)). When the destination spans more than one function boundary, run the `architect` skill ([../../architect/SKILL.md](../../architect/SKILL.md)) to explore shapes in parallel before you move code.

4. **Delete, then build.** Before you add any new structure, clear out what is not needed: delete unused code, fold wrappers that have only one caller into that caller, remove repeated validation while keeping the check at the system's outer edge, and fix references that point at things no longer there ([principle-subtract-before-you-add](../../principle-subtract-before-you-add/SKILL.md)). Ship the smallest change that reaches the destination ([principle-laziness-protocol](../../principle-laziness-protocol/SKILL.md)). Speculative cleanup gets reverted.

5. **Move in small steps, each keeping the lock green.** If an API's shape changes, move all of its callers to the new form and remove the old API within one pass. Add no compatibility shim and leave no window in which both versions exist ([principle-migrate-callers-then-delete-legacy-apis](../../principle-migrate-callers-then-delete-legacy-apis/SKILL.md)). Confirm each rename by searching the codebase, since renames miss occurrences in strings, docs, config keys, and back-references. Hand rote edits to a subagent on the feature-and-refactoring role from `~/.endostack/models.toml` (default `fast`; `strong` for the hardest reshapes), with effort and speed per the router's subagent rules. Give it an exact scope: which files, which names move, which behavior must hold. Read every diff it returns.

6. **Prove behavior did not change** on the real artifact; compiling proves nothing ([principle-prove-it-works](../../principle-prove-it-works/SKILL.md)). Larger reshapes need an equivalence proof: a script that compares old and new output, a replay of recorded outputs through the new code, or a short end-to-end run on the relevant surface through its control skill.

7. **Decide whether it stays.** The change succeeds only if the code is easier to read and trace ([principle-minimize-reader-load](../../principle-minimize-reader-load/SKILL.md)): fewer layers, less hidden state, smaller mutation scope. If nothing got easier to follow, revert it.

8. **Rewrite history into a few ordered commits:** removals first, then the reshape, then any trailing cleanup, each slice passing before the next ([principle-sequence-verifiable-units](../../principle-sequence-verifiable-units/SKILL.md)). Use non-interactive git where interactive rebase is unavailable. Then follow [Opening a PR](opening-a-pr.md).

Done means the lock still passes, equivalence holds on the real artifact, and reader load measurably dropped. Otherwise revert.

**Reply** with what structure changed, which lock you checked against, the equivalence evidence, how reader load changed (layers removed, branches removed, wrappers inlined), what shipped and what was reverted, and an explicit statement that behavior was not extended.
