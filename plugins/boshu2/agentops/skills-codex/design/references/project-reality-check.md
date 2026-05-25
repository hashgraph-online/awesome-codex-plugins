# Project Reality Check

Use this reference before a design decision turns into discovery or implementation work.

## Reality Questions

Answer these before scoring the normal alignment matrix:

1. What user or operator pain does this remove?
2. What evidence says the pain is real?
3. What would make this the wrong thing to build now?
4. What smaller proof would validate the direction?
5. What existing AgentOps surface already solves part of this?
6. What failure would make us stop rather than continue investing?

## Output Addendum

Add this block to the design artifact when the project direction is uncertain:

```markdown
## Reality Check

| Question | Answer | Evidence |
|---|---|---|
| Pain removed | <answer> | <source> |
| Smallest proof | <answer> | <source> |
| Stop condition | <answer> | <source> |
```

## Decision Rule

If the smallest proof is cheaper than the proposed implementation, run the proof first. If the pain or evidence cannot be named, return WARN or FAIL instead of inventing scope.

---

**Source:** Adapted from an external skill corpus / `reality-check-for-project`. Pattern-only, no verbatim text.
