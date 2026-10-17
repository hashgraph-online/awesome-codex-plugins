---
name: devin-prompting
description: Internal guidance for composing Devin prompts for coding, review, diagnosis, and research tasks inside the Devin Claude Code plugin
user-invocable: false
---

# Devin Prompting

Use this skill when `devin:devin-rescue` needs to hand a task to Devin.

Prompt Devin like an operator, not a collaborator. Keep prompts compact and block-structured with XML tags. State the task, the output contract, the follow-through defaults, and the small set of extra constraints that matter.

Core rules:
- Prefer one clear task per Devin run. Split unrelated asks into separate runs.
- Tell Devin what done looks like. Do not assume it will infer the desired end state.
- Add explicit grounding and verification rules for any task where unsupported guesses would hurt quality.
- Prefer better prompt contracts over escalating permission modes or adding long natural-language explanations.
- Use XML tags consistently so the prompt has stable internal structure.

Default prompt recipe:
- `<task>`: the concrete job plus the relevant repository or failure context.
- `<output_contract>`: exact shape, ordering, and brevity requirements for the final answer.
- `<default_follow_through_policy>`: what Devin should do by default instead of asking routine questions.
- `<verification_loop>`: required for debugging, implementation, or risky fixes — Devin should run the test or repro before declaring done.
- `<grounding_rules>`: required for review, research, or anything that could drift into unsupported claims.
- `<action_safety>`: for write-capable tasks — stay narrow, no unrelated refactors, no new dependencies unless asked.

Know the runtime limits:
- `devin -p` is a single turn — Devin cannot ask questions mid-run. The prompt must carry everything it needs.
- In `accept-edits` mode (the default for `--write`), file edits auto-approve but shell commands are rejected — Devin cannot run tests or builds in that mode. If the task genuinely needs command execution, the caller must pass `--permission-mode dangerous` or `--sandbox`.
- In `normal` mode, only read-only tools work — good for diagnosis and research.
- In `autonomous` mode (`--sandbox`), commands run inside an OS sandbox; edit-tool writes are rejected. Good for safe read-only investigation that still needs `git`, `grep`, or test runners.

How to choose prompt shape:
- Use the built-in `review` or `adversarial-review` commands when the job is reviewing local git changes. Those prompts already carry the review contract.
- Use `task` when the task is diagnosis, planning, research, or implementation and you need to control the prompt directly.
- Use `task --resume` for follow-up instructions on the same Devin thread. Send only the delta instruction instead of restating the whole prompt unless the direction changed materially.

Working rules:
- Prefer explicit prompt contracts over vague nudges.
- Do not escalate permission mode first. Tighten the prompt and verification rules before reaching for `dangerous`.
- Keep claims anchored to observed evidence. If something is a hypothesis, say so.
- Front-load the files and symptoms that matter: Devin starts cold, so name the entry points.

Prompt assembly checklist:
1. Define the exact task and scope in `<task>`.
2. Choose the smallest output contract that still makes the answer easy to use.
3. Decide whether Devin should keep going by default or stop for missing high-risk details.
4. Add verification, grounding, and safety tags only where the task needs them.
5. Remove redundant instructions before sending the prompt.
