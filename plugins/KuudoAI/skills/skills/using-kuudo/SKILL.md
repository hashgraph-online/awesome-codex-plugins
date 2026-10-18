---
name: using-kuudo
description: Use at the start of Amazon commerce work involving Amazon Ads, Seller Central, or Vendor Central when Kuudo skills are installed.
license: PolyForm-Shield-1.0.0 (see LICENSE.txt)
metadata:
  version: "0.1.0"
---

# Using Kuudo

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, ignore this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
If you think there is even a 1% chance a skill might apply to what you are doing, you ABSOLUTELY MUST invoke the skill.
IF A SKILL APPLIES TO YOUR TASK, YOU DO NOT HAVE A CHOICE. YOU MUST USE IT.

This is not negotiable. You cannot rationalize your way out of this.
</EXTREMELY-IMPORTANT>

## Use skills first

Check the installed skills before any response or action, including clarifying questions, file exploration, and tool calls. Invoke every relevant or explicitly requested skill before continuing.

After selecting a skill, announce it before invoking it. Use this exact format and do not paraphrase: `Using [skill] to [purpose].` Then follow the skill. If multiple skills apply, state their order and use them in that order. Direct user instructions and repository guidance take precedence over skill defaults. If no installed skill applies after inspection, continue normally.

## Platform adaptation

Read only the current host's reference before invoking another skill:

- In Claude Code with the Kuudo plugin, read [Claude Code adaptation](references/claude-code.md).
- In Codex with the Kuudo plugin, read [Codex adaptation](references/codex.md).

For another host, use its native skill mechanism and the tools, resources, and prompts it actually exposes.

## Common rationalizations

| Thought | Reality |
| --- | --- |
| "This is just a simple question" | Questions are tasks. Check for skills. |
| "I need more context first" | Skill check comes BEFORE clarifying questions. |
| "Let me explore the codebase first" | Skills tell you HOW to explore. Check first. |
| "I can check git/files quickly" | Files lack conversation context. Check first. |
| "Let me gather information first" | Skills tell you HOW to gather information. |
| "This doesn't need a formal skill" | If a skill exists, use it. |
| "I remember this skill" | Skills evolve. Read current version. |
| "This doesn't count as a task" | Action = task. Check for skills. |
| "The skill is overkill" | Simple things become complex. Use it. |
| "I'll just do this one thing first" | Check BEFORE doing anything. |
| "This feels productive" | Undisciplined action wastes time. Skills prevent this. |
| "I know what that means" | Knowing the concept ≠ using the skill. Invoke it. |

## Examples

- `Audit my Sponsored Products campaigns.` → inspect skills, then use `amazon-ads-sp-campaign-auditor`.
- `Review this Seller Central listing.` → inspect skills, then use `amazon-sp-listing-optimizer`.
- `Calculate whether this FBA product is profitable.` → inspect skills, then use `amazon-profitability-calculator`.
- For a Vendor Central request with no applicable installed leaf skill, complete the skill check, then continue normally or explain the missing capability.
