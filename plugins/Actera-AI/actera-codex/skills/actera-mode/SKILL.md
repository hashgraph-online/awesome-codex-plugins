---
name: actera-mode
description: Switch Actera between Monitoring and Enforcing, or choose what happens when Actera cannot evaluate a tool call.
---

The Actera plugin's command line is `bin/actera-hook.mjs` in the plugin folder, two levels above the folder that holds this `SKILL.md`. Run it with Node.js using its absolute path.

If the person did not say what they want, ask them, saying which answer is the default:

- **Mode**: `monitoring` (default) records each tool call and its policy result without blocking anything. `enforcing` blocks the tool calls a policy denies and holds the ones that need approval until a reviewer decides in Actera, Slack or email.
- **When Actera cannot evaluate**, which applies only in Enforcing: `block` (default, fail closed) or `allow` (fail open). Explicit denials and required approvals stay enforced either way.

Then run `node "<plugin folder>/bin/actera-hook.mjs" mode <monitoring|enforcing>` and, if they chose it, `node "<plugin folder>/bin/actera-hook.mjs" evaluation-failure <block|allow>`. Each prints the resulting settings. The change applies to the next tool call; no restart is needed.

Assigning policies happens on the agent's page in Actera and never changes this mode. Do not edit the plugin's state folder yourself.
