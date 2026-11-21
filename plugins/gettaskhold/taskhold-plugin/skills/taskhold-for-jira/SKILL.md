---
name: taskhold-for-jira
description: Hand Jira issues to coding agents and report their progress, using the Taskhold for Jira tools on Atlassian's MCP server. Use when someone asks to "give this Jira issue to the agents", "hand ABC-123 to Claude Code", "how is the agent doing on ABC-123", "what are my agents working on", or wants a Jira issue picked up by a coding agent session.
---

# Taskhold for Jira

Taskhold for Jira is a Forge app. Its three tools reach you through Atlassian's MCP server, under the
app's own endpoint:

```
https://mcp.atlassian.com/forge/069ba455-c262-45b8-a6b0-b92b8b48f19f
```

Add that URL as a remote MCP server in your client (Claude Code: `claude mcp add --transport http
taskhold-jira <url>`), then sign in to Atlassian when asked and pick the Jira site. A site admin has to
turn the app's tools on once: Atlassian Administration > Apps > Sites > (the site) > Connected apps >
Taskhold for Jira > View app details > Tools > "Expose tools to MCP-compatible apps" > Enable tools.

Each person also connects their Taskhold account once, by pasting a Taskhold API key into the
"Taskhold" section of any Jira issue. Until then every tool answers with a short message saying so;
pass that message on.

## Tools

Tool names can carry an environment suffix (for example `agent-progress_development` on a development
install); match on the start of the name.

| Tool | Use it to | Inputs |
|------|-----------|--------|
| `hand-to-agents` | Put a Jira issue on the person's Taskhold list, where their coding agents pick it up | `issueKey` (ABC-123), optional `project` (Taskhold project, defaults to the Jira project's name), optional `note` for the agent |
| `agent-progress` | Report how the agent task for an issue is going | `issueKey` |
| `open-agent-tasks` | List what the agents are on or will pick up next | optional `project` |

## How to use them

1. Confirm the issue key with the person before `hand-to-agents`. Handing the same issue over twice
   doesn't make a second task; the tool returns the existing task's state.
2. After handing over, tell the person where it went (the `taskUrl`) and that the next agent session
   checking the list picks it up.
3. For progress, quote what `agent-progress` returns: status, steps done, percent, which agent, and
   the summary once it's done. Don't fill in steps or percentages it didn't return.
4. If the task is waiting on a question, quote the question and give the `taskUrl`. Answers are given
   by the person on Taskhold; neither you nor the app can answer for them.
5. If a tool returns `{ "error": "..." }`, repeat the message plainly. It already says what to do
   (connect a key, choose a plan, check the issue key).

## Working the task yourself

If you are also the coding agent (for example Claude Code with the Taskhold MCP server connected at
`https://taskhold.com/api/mcp`), the handed-over issue is a normal Taskhold task titled
`ABC-123: summary`, with the issue link and description in it. Pick it up with `taskhold_begin`, plan
steps, tick them off, and finish with `taskhold_complete` and a summary. The Jira panel shows each step
as it changes, and the person can post your summary to the issue as a comment.
