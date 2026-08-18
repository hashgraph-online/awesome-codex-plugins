# {Name of the project}

## Principles to always follow

Reason from first principles. Keep the smallest clear solution that preserves the requested result, maintainability, and quality.
Remove and simplify everything a model knows by its training, keep everything is team/company-specific, conventions and non-obvious facts.

- Use the `development-skills` plugin for project work. If it is unavailable, tell the user how to install it.
- Inspect before deciding. For consequential work, agree on the result and its proof, then record the plan and decision chronicle before implementation.
- Follow this project's established patterns. Add a dependency, abstraction, file, or rule only when removing it would cause a real failure.
- Fix root causes and verify with fresh evidence. Never hide a failure with skipped checks, swallowed errors, or unsupported claims; state what remains unobserved.
- Store durable discoveries in the repository: brief critical facts here, deeper topic rules in `.agents/rules/`, decisions in `docs/chronicles/`, and procedures in `docs/plans/`.
- Keep `AGENTS.md` under 70 lines, shared artifacts in English, and personal machine facts in ignored local files.
- Explain the work in simple, clear words without assuming project knowledge or omitting relevant facts.
