# Agent Template — Validation Checklist

Goal: validate final target/minus sets before clustering.

Checks:
1. No lexical conflicts: minus vs target.
2. No semantic conflicts: minus blocks relevant B2B analog/synonym.
3. Scope correctness: campaign/adgroup level.
4. No duplicates and no contradictory entries.
5. Production candidate is `SAFE_ONE_TOKEN` or exactly two-word inseparable `SAFE_SHORT_MASK`; it must not equal any full source query, including one- or two-word queries.
6. Every SQR/Wordstat candidate has `blocked_intent`, minimal safe scope, `source_query_examples`, `reduction_reason`, `protected_check=PASS`, `target_conflict_check=PASS` and a manual user decision.
7. `PHRASE_MINUS`, `ADD_NEGATIVE_PHRASE`, `params.phrase`, missing lineage and unapproved candidates are blocked.

Pass condition:
- `conflicts_with_target = 0`
- no `risk_blocking=high` unresolved.
- every row moved to a write pack has `decision=approved`, and the pack checksum is verified by `direct_write_gate.py`.
