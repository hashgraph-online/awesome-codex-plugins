# Research

Research only facts that can change design, scope, risk, or tests.

- Search local code, manifests, tests, config, and CI first with `rg`.
- For libraries, APIs, CLIs, SDKs, or cloud services, follow repo instructions
  and use current official documentation.
- Record `evidence -> implication -> plan change`; omit generic summaries.
- Keep findings in `codex-plan.md` unless they need independent provenance or
  may be reused. Only then create `codex-research.md`.
- If agents help, they return concise findings. One parent writer owns shared
  artifacts.

Stop when remaining unknowns cannot change implementation. Ask the user only
when a material product or risk decision cannot be resolved from evidence.
