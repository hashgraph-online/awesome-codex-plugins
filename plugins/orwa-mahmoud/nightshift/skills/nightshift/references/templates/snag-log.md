# Snag Log

> Findings ledger across runs. Read this before reporting findings; dedupe against ALL seen — fixed
> AND rejected — so no cycle re-reports an earlier one. Append dispositions after acting.
> A bug found on a shift is fixed on that shift and recorded here with the fix as its disposition;
> it is never staged for later or left for the owner to decide. Only a fix that would change
> behaviour users rely on becomes a decision in `parking-lot.md`, with the default chosen and
> applied.

**Each entry** is one `- ` bullet below the rule: `finding · evidence · disposition · date`. Wrapped
and indented lines belong to the bullet. Archive files only bullets: text written as a paragraph
stays here for good, and Doctor names it.

**Dispositions:** `fixed`, `ignored`, `answered`, `rejected-because`, `accepted-tradeoff`.
Write `fixed in <commit>`, or the disposition followed by its reason. An entry with no disposition
is open and waits for the owner; Archive files an entry once it carries one.

Read live entries first. A `Filed:` line points at filed history — follow it and search that file
by topic or identifier; do not open every archive. Historical dispositions are evidence, not a
fresh authorization. A broken pointer is reported here; never guess or delete history.

---

(empty — the first walkthrough appends here)
