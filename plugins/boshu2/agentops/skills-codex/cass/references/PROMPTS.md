# Mined Gold-Standard Prompts

> **Source:** Real prompts from this user's session corpus that have been *re-used 5+ times*. These are tested, working entry points to cass — copy/paste, then adapt the keyword.

## Contents

- [Discovery Openers](#discovery-openers)
- [Compile-A-File Prompts (Aggregation Tasks)](#compile-a-file-prompts-aggregation-tasks)
- [Subagent Mining (Line 2 = THE Prompt)](#subagent-mining-line-2--the-prompt)
- [Cross-Machine Recall](#cross-machine-recall)
- ["What Worked Last Time?"](#what-worked-last-time)
- [Decision Archaeology](#decision-archaeology)
- [Ritual Detection](#ritual-detection)
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

## Subagent Mining (Line 2 = THE Prompt)

```
Use cass to find all subagent sessions in the last 30 days where the prompt mentions "deep dive" — give me the line-2 text from each.
```

Implementation:
```bash
cass search "deep dive" --workspace /path --json --fields minimal --limit 50 \
  | jq -r '[.hits[] | select(.source_path | contains("subagent"))] | unique_by(.source_path) | .[].source_path' \
  | xargs -I{} sh -c 'echo "=== {} ==="; sed -n "2p" "{}" | jq -r ".message.content"' 
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
Use cass to find the most-recent successful run of <TASK> and resume that session.
```

```bash
HIT=$(cass search "<TASK>" --workspace /repo --json --fields summary --limit 1 \
        | jq -r '.hits[0].source_path')
cass resume "$HIT" --shell
```

---

## Decision Archaeology

```
When did we decide NOT to support <X>? Use cass with terms like "EXCLUDE", "out of scope", "skip for now".
```

```
Find the earliest session where we discussed adopting <LIBRARY>, and the conversation that finalized the choice.
```

---

## Ritual Detection

```
What prompts have I used 10+ times across all my agent sessions? Surface the top 20.
```

```bash
cass search "*" --workspace /path --json --limit 500 \
  | jq '[.hits[] | select(.line_number <= 3) | .title[0:80]]
        | group_by(.) | map({prompt: .[0], count: length})
        | sort_by(-.count) | .[0:20]'
```

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

When you hear any of these, jump straight to the [Two-Step Bootstrap](../SKILL.md#two-step-bootstrap-replaces-always-first) and start mining.

---

## Anti-Templates

These prompts trigger /cass but produce *poor* results — rewrite them before executing:

| Bad prompt | Why bad | Better |
|------------|---------|--------|
| "Search cass for everything about X" | unbounded; will return 10k hits | Add `--workspace /repo` and `--days 30` |
| "Find all sessions" | no filter; useless | Pick a keyword OR an aggregate (`--aggregate agent,date`) |
| "What's in the index?" | not actionable | `cass status --json` + `cass search "*" --aggregate workspace --limit 1 --json` |
| "Re-extract all my prompts" | duplicates work cass already does | `cass search "*" --json --limit 500 \| jq '... select(.line_number <= 3)'` |
