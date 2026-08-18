---
name: review
description: Audit the debt registry, rank survivors by churn × Fowler quadrant, surface a top-N list, then walk paydown on user follow-up. Use when the user asks to review debt, see what to pay down, work through entries, or invokes $review. Stale entries drop with "drop A,B,C".
---

# review — audit + (on follow-up) walk paydown

Two modes. First turn: print the audit and stop. On a user follow-up ("fix the top one," "walk these," "do A," "pay some down"), apply the rubric below.

## First turn: print the audit

Run the bundled `review.py` (it lives in this skill's `scripts/` directory — reference it with the relative path; Codex resolves it against the skill root):

```bash
python3 scripts/review.py
```

Optional: `--top N` to surface more than the default 3 candidates.

**Re-emit the helper's stdout verbatim in a fenced code block.** Codex may collapse long bash outputs — if you don't print it yourself, the user might not see it. Copy exactly: no preamble, no summary, no "want me to fix the top one?" The fenced block preserves column alignment.

Then stop. The user picks the next move.

## Paydown mode (only on user follow-up)

Work through requested entries one at a time. Confirm before each fix. Never auto-batch. Never auto-commit.

For each entry, read the registry file, the hotspot, and adjacent tests. Apply this rubric:

- **Already fixed?** If the marker/symptom the entry describes no longer appears in the hotspot file, say so and add the entry's letter to the drop list. Don't re-fix.
- **Cold area?** Churn=0 since `created:` and age >90d → propose deferring. ~20% of files generate ~80% of debt-related rework; don't pay down vanity refactors.
- **Prudent-deliberate with payoff_trigger not met?** Honor the trigger. Skip with a one-line "trigger not met: <quote>."
- **Fix candidate?** Propose the smallest change that resolves the entry. Improvement, not perfection — don't refactor surrounding code.

### When you fix

- **Read the repo first.** Check the test framework, adjacent tests, the cached feedback commands. Adapt to what exists; don't impose a new style.
- **TDD where tests exist.** Write a failing test that pins the deferral, then make it pass. Don't weaken or delete existing tests to make a fix pass.
- **No tests in this area?** Surface that and ask: write one, or fix without?
- **Explain why this resolves the entry.** Cite the entry's `payoff_trigger` or body — don't commit code you can't explain.
- **Risky fix?** Auth, payments, migrations, public APIs, or `ai_authored: true` → run a fresh-context review of the diff before suggesting commit. Fresh-context review catches what the writer's motivated reasoning misses.
- **Don't commit.** Show the diff. The user runs the gates, drops the entry with `drop A`, and commits.

### Pacing

Aim for 3–10 entries per session — continuous paydown outperforms stop-the-world batches. If the user says "do them all," push back once: unsupervised AI cleanup measurably increases duplicate blocks and short-term churn. If they insist, still one-at-a-time with diffs surfaced.

## Speak plainly

The frontmatter uses a research taxonomy (`quadrant`, `category`) for ranking and grounding — it is not user-facing vocabulary. When you talk about an entry, describe it in plain words; never say "prudent-inadvertent", "reckless-deliberate", "code_rot", etc. to the user. Use the entry's body and a plain phrase (e.g. "a planned tradeoff", "a shortcut you knew about", "came up later") instead. The `review.py` output is already translated — match its tone.

## Don't

- Don't ask the user to confirm before running `review.py`.
- Don't paraphrase the helper's stdout. Copy it verbatim into the fenced code block.
- Don't enter paydown mode on the first turn. Stop after the report. Wait for the user's intent.
- Don't auto-commit. Ever.
