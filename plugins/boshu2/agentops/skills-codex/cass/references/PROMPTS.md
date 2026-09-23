# Example Discovery Prompts

> Adapt these examples to an authorized source scope and a bounded question. Reuse counts do not establish success; inspect source roles, outcomes and corrections.

## Contents

- [Discovery Openers](#discovery-openers)
- [Compile-A-File Prompts (Aggregation Tasks)](#compile-a-file-prompts-aggregation-tasks)
- [Subagent Mining](#subagent-mining)
- [Cross-Machine Recall](#cross-machine-recall)
- ["What Worked Last Time?"](#what-worked-last-time)
- [Decision Archaeology](#decision-archaeology)
- [Recurring Candidates](#recurring-candidates)
- [Cost & Usage Reports](#cost--usage-reports)
- [Sentinel Phrases (Triggers for /cass)](#sentinel-phrases-triggers-for-cass)
- [Anti-Templates](#anti-templates)

---

## Discovery Openers

```
read AGENTS.md and use /cass to find the session history with codex for this project
```

```
Use /cass to search session history for context on issues that were closed but never actually fixed.
```

```
i distinctly recall making a project called <NAME> ; can you look on /cass for what happened with it
```

```
read AGENTS.md ; /cass-session-search use cass to see how I used <TOOL> for <PROJECT>
```

```
Reread AGENTS.md so it's still fresh in your mind. Use /cass to search the project sessions history for ...
```

---

## Compile-A-File Prompts (Aggregation Tasks)

```
read AGENTS.md. I need you to use /cass to compile a file LIST_OF_INPUT_MESSAGES.md that contains all the user prompts for project X, in chronological order.
```

```
Use cass to extract every "first read ALL of AGENTS.md" prompt across this workspace and group by week.
```

---

## Subagent Mining

```
Use cass to find up to three relevant subagent sessions in the last 30 days
where the prompt mentions <TASK>. Verify the message roles and native
relationships; show cited excerpts and disclose missing or mismatched sources.
```

Implementation:
```bash
cass search "<TASK>" --workspace /path --days 30 --mode lexical --json --fields minimal --limit 20
cass pack "<TASK>" --workspace /path --days 30 --mode lexical --json \
  --limit 20 --max-sessions 3 --max-evidence 6 --max-tokens 4000
# Follow a selected candidate's actual locator; there is no fixed prompt line.
cass expand /path/from/selected-hit.jsonl --line LINE --context 3 --json
```

---

## Cross-Machine Recall

```
Search cass on css, csd, ts1, and ts2 for any mention of <KEYWORD> and dedup by source_path.
```

(For execution see SKILL.md → "Cross-Machine Search" or the `REMOTE_SOURCES.md` reference, Approach C — load it explicitly with the Read tool when you need the full recipe.)

---

## "What Worked Last Time?"

```
Use cass to find a recent run of <TASK>. Inspect intent, outcome and later
corrections before calling it successful. Show enough source context to judge
whether it applies now; only resume a verified native session when requested.
```

```bash
cass pack "<TASK>" --workspace /repo --mode lexical --json \
  --limit 20 --max-sessions 3 --max-evidence 6 --max-tokens 4000
```

A relevance-ranked first hit is not necessarily recent or successful. Check
returned timestamps and source records. Use [RESUME.md](RESUME.md) only for a
selected resume request.

---

## Decision Archaeology

```
When did we decide NOT to support <X>? Use cass with terms like "EXCLUDE", "out of scope", "skip for now".
```

```
Find the earliest session where we discussed adopting <LIBRARY>, and the conversation that finalized the choice.
```

---

## Recurring Candidates

```
Within this project, find recurring prompts relevant to <TASK>. Review up to
three episodes for intent, outcome and corrections. Include a competing
explanation or counterexample; do not infer success from repetition.
```

```bash
cass search "<TASK>" --workspace /path --mode lexical --json --fields summary --limit 20
```

See [PATTERNS.md](PATTERNS.md#pattern-detection) for limited hit counts. Titles
and repeated indexed hits are not counts of distinct user messages. Check native
roles and observed results before proposing reuse; rule changes need separate
authority and later task evidence is needed to establish usefulness.

---

## Cost & Usage Reports

```
What did I spend on Claude API across all projects last month? Break down by model.
```

```bash
# Per-model token totals (`cass analytics tokens` is time-only; use `models` for per-model)
cass analytics models --json | jq '.data.by_api_tokens.rows[0:10]'
```

```
Which agent is doing most of the tool-calling? Pull the top 10 over the last 60 days.
```

---

## Sentinel Phrases (Triggers for /cass)

These literal phrases are reliable triggers for the skill in this user's vocabulary:

- "Use /cass to ..."
- "use cass to find ..."
- "look on /cass for ..."
- "session history" + "<TASK>"
- "find that prompt"
- "what did I ask"
- "scope archaeology"
- "what worked last time"

When the caller requests this work, use the [bounded discovery workflow](../SKILL.md#discovery-workflow) within the authorized scope. Ordinary work has no mandatory history step.

---

## Anti-Templates

These prompts trigger /cass but produce *poor* results — rewrite them before executing:

| Bad prompt | Why bad | Better |
|------------|---------|--------|
| "Search cass for everything about X" | unbounded; will return 10k hits | Add `--workspace /repo` and `--days 30` |
| "Find all sessions" | no filter; useless | Pick a keyword OR an aggregate (`--aggregate agent,date`) |
| "What's in the index?" | not actionable | `cass status --json` + `cass search "*" --aggregate workspace --limit 1 --json` |
| "Re-extract all my prompts" | an indexed sample does not prove full source coverage | Select a scope and budget; use CASS pack/view/expand and verify native roles, reporting unread or unavailable portions |
