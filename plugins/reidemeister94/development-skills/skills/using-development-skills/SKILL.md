---
name: using-development-skills
description: Read at session start to route development work through the direct or full development loop on Claude Code and Codex.
---

# Using development-skills

Skip this router for a bounded subagent task. Read the [development loop](../../shared/development-loop.md). Resume an active plan at its recorded step; otherwise choose:

<WRITING-GATE>
Before the first natural-language output of a task, read and apply the [writing contract](../../shared/writing.md). It covers chat and every text file. Explain for a person with little project knowledge, then keep the exact detail an agent needs.
</WRITING-GATE>

<INTERACTION-GATE>
On Claude Code, call `AskUserQuestion` whenever the user must choose among options.
On Codex, ask one concise question in chat.
</INTERACTION-GATE>

<STANDARDS-GATE>
Before the first codebase mutation, apply the development loop's Standards gate. Discover and apply relevant project and reference sources and established local patterns. State the selected source paths with the chosen path. A Full plan records the same paths.
</STANDARDS-GATE>

Direct applies only when the result, forced solution, and proof are clear. The change must be reversible and carry no business or design choice. Weighing more than one viable approach is a design choice.

Full applies to everything else. Inspect first, run `brainstorming`, and agree on the result and proof.
Use `create-test` for test work or business, integration, KPI, and probabilistic proof. Use `best-practices` when current external evidence can change a decision.

Then write the plan and chronicle.

In chat, cover result, checks, what is out of scope, approach, files, and risks. Offer the conversation-language equivalents of `Approve / Edit / Cancel / Chat about`, then stop. Only `Approve` after that presentation permits implementation; the original request does not.

After approval, implement, verify, explain concepts worth transferring, and review.

<PATH-GATE>
State the chosen path and why before the first mutating action; a silent classification is a skipped gate.
A requested review or audit delivers findings, then stops. Edits begin only after explicit approval of those findings. “Review and improve” authorizes the category, not the changes.
An approval gate you cannot reach (user away, autonomous run) is a stop, not a bypass: deliver findings; never downgrade Full to Direct.
</PATH-GATE>

<PLAN-MODE-HANDOFF>
Native Plan mode changes permissions, not the loop. Complete Decide and Define the proof there. After `ExitPlanMode`, or after Codex leaves Plan mode, resume Full at Express.

Create or update the repository plan and chronicle in completed tool calls before product or plugin edits. Never combine them in one patch. Record `Current step: Implement`, then complete Implement, Verify, Explain diff, and Review.
</PLAN-MODE-HANDOFF>

<EXPLAIN-DIFF-GATE>
At Full-path Explain diff, first invoke `development-skills:explain-diff` through the skill mechanism. Do not imitate it from this router.

After Verify and before Review:

- a business, architectural, lifecycle, trade-off, or failure-mode concept exists → enter Explain diff;
- no concept is worth transferring → state that briefly and continue.

This gate does not affect Direct.
</EXPLAIN-DIFF-GATE>

Translate older Claude Code tool names on Codex with [codex-tools.md](references/codex-tools.md).
