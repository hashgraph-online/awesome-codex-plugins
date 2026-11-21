---
name: savings
description: Show how many input tokens the LLMSlim proxy kept out of Claude Code's requests.
disable-model-invocation: true
argument-hint: "[days]"
allowed-tools: Bash(llmslim proxy stats*), Bash(uvx --from llmslim[proxy]==0.12.0 llmslim proxy stats*)
---

Run `llmslim proxy stats`, adding `--days $ARGUMENTS` if the user gave a number of days. If `llmslim` isn't on the
PATH, run `uvx --from "llmslim[proxy]==0.12.0" llmslim proxy stats` instead.

Report the numbers as the command prints them: requests changed, outputs compressed and how often they were replayed,
input tokens before and after, and tokens not sent. Don't turn them into a dollar figure unless the user gives their
price per million input tokens; then rerun with `--price-per-mtok <price>`. Note that this estimate is before any
prompt-caching discount, so the billed saving is smaller when most of those tokens would have been cache reads.

If every number is zero, Claude Code probably wasn't started with `llmslim wrap claude`. Point the user to
`/llmslim:wrap-claude`.
