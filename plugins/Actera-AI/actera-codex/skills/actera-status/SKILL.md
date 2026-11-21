---
name: actera-status
description: Show the Actera connection, mode, evaluation-failure behavior, whether the hooks run, and report delivery.
---

The Actera plugin's command line is `bin/actera-hook.mjs` in the plugin folder, two levels above the folder that holds this `SKILL.md`. Run `node "<plugin folder>/bin/actera-hook.mjs" status` with its absolute path.

Summarize in plain language:

- Whether Actera is connected, and to which agent.
- The mode (`settings.modeName`) and the evaluation-failure choice (`settings.evaluationFailureName`). In Monitoring, tool calls always continue and the failure choice applies only in Enforcing.
- Whether the hooks run. If `hooksNeedAttention` is present, say exactly that: no Actera hook has run in Codex yet, so the person should open `/hooks` in Codex, trust the Actera hooks and start a new session. Otherwise give the time and event of `lastHook`.
- Whether held calls can be reviewed in Codex: `reviewerLinked` is true once the person linked Codex to their Actera account. If false, the next held call offers to link it. Actera still checks on each review that they may approve it.
- Reports waiting to be sent: `queue.executionReports` are tool outcomes and `queue.decisionRetries` are policy checks Actera could not receive yet, with the oldest pending age. The hooks send them on the next tool call. Report `lastError` if present, without claiming it proves Actera is down.

`$actera-mode` changes the mode. Do not edit the plugin's state folder yourself.
