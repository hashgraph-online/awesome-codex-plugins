---
name: deja-reflect
description: End-of-session reflection and memory curation with deja-vu. Review what was decided, what commands broke and what repaired them, and record durable project rules or decisions with deja remember so the next session starts with them.
metadata:
  openclaw:
    homepage: https://vshulcz.github.io/deja-vu/
    requires:
      bins:
        - deja
    install:
      - kind: brew
        formula: deja-vu
        bins: [deja]
      - kind: node
        package: "@vshulcz/deja-vu"
        bins: [deja]
---

Run an end-of-session reflection over the current task and record only durable, non-obvious project facts in deja-vu.

## Workflow

1. **Inspect what was already recorded or hit in this project:**
   - Run `deja notes` to check existing promoted decisions so you do not duplicate or contradict an active rule. (If `deja` is not on PATH, run `npx -y @vshulcz/deja-vu ...`.)
   - Run `deja friction` to see recurring command failures across sessions.
2. **Distill durable findings from this session:**
   - Keep: architectural invariants, required flags/commands that were non-obvious, rejected approaches and why they failed, user-stated project rules.
   - Skip: anything already obvious from reading the code, temporary debugging steps, or one-off typos.
3. **Confirm with the user before writing:**
   - Present the 1–3 concise one-line facts you propose to store.
   - Once confirmed, store each via the `deja` MCP tool (`mode: "remember"`) or in the shell:
     ```bash
     deja remember "<concise self-contained decision and why>" --tag <topic>
     ```
   - If an older note was superseded by today's work, mark it with `deja promote <id> --state superseded --note "<what replaced it>"`.
