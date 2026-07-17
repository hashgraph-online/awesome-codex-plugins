---
name: bootstrap
description: Initialize minimal AgentOps documentation
---
# Bootstrap — minimal project setup

Bootstrap fills only missing AgentOps entry documents and the default durable
verdict directory. It does not initialize Git, install hooks, create tracker
state, start runtimes, or impose a delivery workflow.

Never-overwrite is what makes bootstrap safe to run on any repository: a setup
step that can only add is idempotent by construction, while one that can
replace must first prove it understands what it is replacing.

Named failure mode — **scaffold sprawl**: creating files the caller never
requested because a "complete" setup feels more helpful than a minimal one.

Anti-pattern: inferring product intent from directory names and READMEs to
avoid asking the caller. Corrective: ask for the missing content; a wrong
PRODUCT.md written confidently is worse than a question.

## Procedure

1. Inspect the target directory and report which canonical files already exist.
2. Ask the caller for missing product intent or goal content when it cannot be
   inferred safely.
3. Create only missing, explicitly requested files. Never overwrite an existing
   document.
4. Create `.agents/ao/verdicts/sha256/` when durable local verdict storage is
   requested.
5. Validate filesystem existence and report created, skipped, and failed paths.
6. Stop.

Typical documents are `PRODUCT.md`, `GOALS.md`, `AGENTS.md`, and a README section
that explains the one-pass loop. Repositories remain free to use their own Git,
CI, tracker, release, and deployment policies.

## Non-goals

- installing or invoking `ao`, `br`, `bd`, NTM, Agent Mail, or another runtime;
- creating `.git`, worktrees, branches, commits, hooks, or CI workflows;
- choosing work or claiming that repository setup is complete beyond the paths
  actually inspected;
- running RPI automatically.

## Output

Return target path, requested files, created files, existing files left intact,
failed writes, and validation observations. Do not include a next action.

## References

- [Goals](../goals/SKILL.md)
- [Product](../product/SKILL.md)
- [Documentation](../doc/SKILL.md)
- [Examples](references/examples.md)
