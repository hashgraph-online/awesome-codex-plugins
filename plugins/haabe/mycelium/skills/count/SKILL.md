---
name: count
description: Print your own north-star row from your own record, and nothing else. Reads .claude/harness/decision-log.md, the canvas and the hook logs in this project; prints one line (decisions before the first source file, of which citing outside evidence, kills before code, sessions). Sends nothing anywhere. Opt-in; paste the line where you like or not at all.
metadata:
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Count: your own row, from your own record

Mycelium's north star is a hypothesis (dogfood DL-1177, 2026-09-07): a builder who makes at least
one build-or-kill decision on evidence from outside their own head, before their project's first
source file, is the builder who comes back and later says the brief changed what they built. There
is no telemetry by design (PRIVACY.md). This command is the opt-in half: it reads your repository
and prints one line. It writes nothing and sends nothing.

## Run

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/count_builder_row.py" --project-dir .
```

Output, one line plus what it means:

```
mycelium row | first source file 2026-06-02 | decisions before it 4 (of 31 dated) | citing outside evidence 2 (lexical proxy, upper bound) | kills before code 1 | sessions 12
```

## What the numbers are, and which are proxies

- **first source file**: the first commit that added a code file outside `.claude/` and `docs/`. Without git, or before any such file, it reads `unknown` and nothing is "before" it.
- **decisions before it**: dated entries in your decision log on or before that day.
- **citing outside evidence**: an entry carrying a URL, an `external_*` source class, a `(per ...)` citation or an interview word. **A lexical proxy and an upper bound**: the unit asks for a person in the pipeline or a fact about the market, and a link to your own notes matches too. Read the entries if the number matters.
- **kills before code**: cycle rows killed or archived, and archived solutions, dated on or before that day.
- **sessions**: distinct session ids in the read-log and change-log the hooks write.

The discovery-layer condition (L0 to L2) is not applied, because decision-log entries carry no
scale and guessing one would manufacture the count. Say so if you paste the line.

## Rules

- Never write the line into a canvas or a decision log on the builder's behalf; the row is theirs.
- Never call out. The maintainer's proxy sheet gains rows only from what people choose to paste (an issue on the framework repo, a message, nothing).
- If the line is 0 across the board, that is a real answer about the record, not a failure of the builder: it means the decisions were made after the first source file, or were not logged. Say which, from the `first source file` date and the `of N dated` count.
