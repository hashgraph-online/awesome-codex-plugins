# Split Heuristics

Prefer a split when a component has its own purpose, risks, files, tests, or
decision space. Avoid splitting work that can only be understood or implemented
as one small unit.

Good split signals:

- separate user workflows or personas
- separate service, package, module, or deployment boundary
- integration with a distinct external system
- data model or migration work that must land before features
- security, billing, auth, permissions, or compliance risk
- enough ambiguity to justify its own research and interview pass

Bad split signals:

- only a handful of mechanical edits
- artificial frontend/backend split when behavior must be planned together
- generic "utils" bucket without clear ownership
- one split that cannot be tested until several later splits exist

Create dependency layers:

1. foundations: schemas, migrations, shared contracts
2. core behavior: domain logic and services
3. interfaces: API, UI, CLI, integrations
4. hardening: observability, migration, performance, release work

If the whole project is already focused, create one split named
`01-{project-name}` and explain why.
