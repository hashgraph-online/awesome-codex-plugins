# Design Application Boundaries Workflow

## Steps

1. [ ] List commands as user actions, not package names.
2. [ ] Identify core rules and every external effect.
3. [ ] Draw command adapter → application action → port → adapter dependencies.
4. [ ] Define the smallest consumer-owned interfaces needed for difficult effects.
5. [ ] Choose packages based on cohesive ownership and allowed imports.
6. [ ] Build dependencies in one composition root with explicit lifecycle cleanup.
   - Record each dependency's owner, sharing model, cleanup, and test seam.
   - Separate SQL pool ownership from use-case transaction ownership.
   - Choose a domain client, narrow operation interface, or concrete
     `*http.Client` deliberately.
7. [ ] Define a bootstrap path so help, version, completion, output mode, and
       config-location flags do not require full config or remote dependencies.
8. [ ] Separate validated configuration from mutable application state.
9. [ ] Test core logic, adapters, command wiring, and one assembled binary flow.

## Common Mistakes

| Mistake | Corrective action |
|---|---|
| Copying a large template | Start with current seams and add only justified layers |
| Global clients in `init` | Construct in the composition root |
| Command methods contain domain rules | Move rules inward and return typed results |

## Exit Criteria

- [ ] Dependency direction is acyclic and visible from constructors.
- [ ] CLI framework and infrastructure can change without rewriting core behavior.
