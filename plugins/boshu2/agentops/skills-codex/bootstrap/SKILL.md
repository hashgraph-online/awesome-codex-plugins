---
name: bootstrap
description: 'Initialize explicitly requested, missing AgentOps documentation and optional verdict storage without taking over repository workflow. Triggers: "bootstrap AgentOps", "initialize AgentOps docs".'
---
# Bootstrap — minimal project setup

Bootstrap fills only explicitly requested, missing AgentOps entry documents and,
when requested, the durable verdict directory. It does not initialize Git,
install hooks, create tracker state, start runtimes, or impose a delivery
workflow.

Never-overwrite is what makes bootstrap safe to run on any repository: a setup
step that can only add is idempotent by construction, while one that can
replace must first prove it understands what it is replacing.

Named failure mode — **scaffold sprawl**: creating files the caller never
requested because a "complete" setup feels more helpful than a minimal one.

Anti-pattern: inferring product intent from directory names and READMEs to
avoid asking the caller. Corrective: ask for the missing content; a wrong
PRODUCT.md written confidently is worse than a question.

## Prompt

```text
Bootstrap missing AgentOps docs for fleet-router (ao is installed). Create only PRODUCT.md and GOALS.md since they're missing; AGENTS.md already exists, so leave it untouched. Also create .agents/ao/verdicts/sha256/. Report created, skipped, and failed paths.
```

## It's working if

- The report lists `PRODUCT.md` and `GOALS.md` as created and `AGENTS.md` as skipped because it already exists.
- A path collision with an existing document, e.g. `AGENTS.md` already present, gets reported as skipped rather than overwritten.
- `.agents/ao/verdicts/sha256/` gets created only when the caller explicitly requested durable verdict storage.
- The report ends with created, skipped, and failed paths only, carrying no next action and no `git` command.

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
that explains the RPI traversal. Generated product copy starts from the
operations-layer category and preserves the ownership boundary. Repositories
remain free to use their own Git, CI, tracker, release, and deployment
policies.

**Naming.** Three surfaces share the word "bootstrap"; they are distinct. This
skill authors missing entry documents. `ao init` is the CLI command that creates
the local evidence and verdict directories (`.agents/ao/**`). `ao session
bootstrap` is a read-only session command that reports which local orientation
files are present. This skill invokes neither.

For selected CDLC, the caller resolves existing external storage through the
[context-routing reference](references/context-routing.md). Bootstrap never
creates a consumer project config or replacement knowledge/withdrawal source.
New CDLC proof uses the explicitly selected external evidence root; the local
verdict-directory recipe above applies to caller-requested standalone proof.

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

- [Fitness](../fitness/SKILL.md)
- [Product](../product/SKILL.md)
- [Documentation](../doc/SKILL.md)
- [Examples](references/examples.md)
- [External context routes](references/context-routing.md)
