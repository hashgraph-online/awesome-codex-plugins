---
name: kin
description: How to use Kin's MCP tools (search, describe, read, execute, feedback) and read their answers. Use when the person asks to read or change something in a service they connected in Kin, such as GitHub, Notion or Linear.
---

# Using Kin

Kin connects the person's accounts at other services. For each account and action the person sets a rule: Allow, Ask me or Block. Kin applies the rule on its server when the action runs, so these notes only cover how to make the calls and read the answers.

## Find the action

- Call `search` with the task in plain words, such as "list open issues in GitHub". It returns only the actions the person's rules allow, and each match names the tool that runs it: `read` or `execute`.
- A match that includes `inputSchema` can run right away. Call `describe` (up to 5 `actionIds` at once) when you need an action's input schema, its current version, or whether it needs the person's approval.
- `noMatch` means nothing the person connected clearly does the task. Tell them. `suggestions` are services they could connect; mention them, and connect one only if the person asks.

## Run it

- Run reads with `read`.
- Run changes with `execute`. Give each new change a new `requestKey` and a one-sentence `reason` that says why, in your own words. The person sees the reason when they review the call and in Kin's activity log.
- The same `requestKey` never runs a change twice. Reuse a key only to get the outcome of the change it started.

## Read the answer

- `approval_required`: the change is waiting for the person in Kin. Tell them, and include the `reviewUrl`. Once they decide, make the same call with the same `requestKey` to get the outcome.
- `running`: the person approved it and it is still running. Make the same call again to check on it.
- `denied`: the person's rule does not allow this. Tell them what was refused. `error.message` says why.
- `paused`: the person paused AI access in Kin. Stop and tell them.
- `unknown`, or `timed_out` for a change: it may have happened. Check before you try again with a new key.
- `trimmed`: the result was too long and was cut. `trimmed.next` reads the rest.
- `ambiguity`: more than one connected account fits. See the `kin-accounts` skill.

## Feedback

Call `feedback` only when a search match or a call was wrong, or notably useful. It tunes search ranking and never changes permissions. Routine successes need none.
