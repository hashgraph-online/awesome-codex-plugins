# Simulated pick

One fresh agent writes search words, then three fresh judges pick. Before starting, tell the user the count, because it spends their quota: `4 fresh agents, 5 prompts each`.

## Prompts

The same five in every run:

- Must-win control, the plugin's core job in plain words, narrowed to what no competitor in the catalogue claims: `Which apps can I connect to <assistant> to <job>? Suggest a few I could install.`
- Must-lose control, the same wording with a competitor's core job that this plugin doesn't do.
- Three target prompts from step 1, in their own words. Prefer sourced ones, and include one that asks for the outcome and names no app.

## Fresh context

An agent sees no repo, no context file and nothing that marks the user's plugin. Take the first route you have:

| Route | How |
|---|---|
| Claude Code in a shell | From an empty directory: `claude -p --tools "" --setting-sources "" < /path/to/prompt.txt`. Those flags keep out `~/.claude/CLAUDE.md`, which plain `claude -p` loads. |
| Codex in a shell | From an empty directory: `codex exec --skip-git-repo-check --ephemeral -s read-only - < /path/to/prompt.txt`. `~/.codex/AGENTS.md` still loads. |
| Subagent | Give it only the prompt, and tell it to read no files. It can still inherit the repo's instruction file. |
| None of these | Run inline and open the report with `Degraded: judge saw the repo`. |

Use the same `Degraded:` line when an instruction file that loaded names the plugin.

## Search words

Give one fresh agent the five prompts and no listings, so its words can't echo them:

> For each numbered message a user might send, write only the words you would search an app store with. One line each: `<number> | <words>`.

Assistants add competitor brand names and task words, so record both. An assistant's search also differs from the store's: it can add brand and task words to the query and find apps the store's search for the same words missed, so the two result sets overlap only in part (OpenApps, observed).

Check the plugin's listing against these words, as step 3 did against the prompts. A missing task word is a fix. Brand names show who the assistant expects and stay out of the fixes, because ChatGPT's rules bar comparisons in a subtitle or description (https://developers.openai.com/plugins/plugin-guidelines.md).

## Picks

Give three fresh judges the five prompts and a catalogue, shuffled again for each judge. Each entry has the name, subtitle and whole long description from `listings_versions`, plus full tool text where the server is open. Shortened entries change the picks, so say so if you shorten any. The user's plugin gets the same treatment as every other entry and carries no mark.

> You are an assistant deciding what to suggest to a user. Use only the catalogue below. For each numbered message, name the one entry you would suggest first, or NONE if you would answer directly or use a built-in tool, and give your reason in one sentence. One line each: `<number> | <entry or NONE> | <reason>`.

A judge answering five messages can mix them up. Read each reason, and rerun any judge whose reason answers a different message.

Report picks per prompt as k of 3 for each entry and for NONE, with the leading pick's reason. Leave percentages out: three runs can't carry them.

## Reading the result

A control fails when the plugin lands on the wrong side in 2 or more of 3 runs. If either fails, the report leads with `This simulation is not informative for this set`, and no fix rests on the picks.

When a competitor that took picks has a `Pressures the model` fail, report it apart from the picks: `<competitor>'s simulated wins may come from the imperative in its tool text and may not carry over to real hosts.`

## Check against the real assistant

Ask the user to try the three target prompts in the real assistant and paste what it suggested: a regular signed-in ChatGPT chat with no apps connected and memory off, or a Claude incognito chat.

A prompt agrees when the simulated leading pick is among the suggestions, or when both suggest nothing. Report `Real answer agreed on <k> of 3`, or `Not checked against the real assistant` when nothing comes back. Apps the assistant named that aren't in the catalogue are competitors to add next time.

## Label

Print this above the picks: `Simulated with <model>, 3 runs, against listings we chose. Not ChatGPT's or Claude's real search or ranking.`

Print beside it what a simulation can't tell you: which apps the real search returns, retention, installs and signed-in context.
