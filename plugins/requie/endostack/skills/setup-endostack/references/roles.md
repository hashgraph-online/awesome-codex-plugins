# Values, budget, and file layout

## Roles

The key table with defaults is in [../SKILL.md](../SKILL.md), step 2. Eighteen role keys plus `budget`.

## Values

- `"strong"`, `"standard"`, `"fast"`: a tier, resolved to a concrete model at spawn time through `docs/agents/<agent>.md`.
- `"inherit"`: use the chat's model. Pass no model. `"auto"` is read as an alias of `"inherit"`; setup always writes `"inherit"`.
- Any other string: a model name this agent accepts, as detected in step 1 or supplied by the user.

Panel lists can mix all three, for example `["strong", "inherit", "some-model-name"]`.

## Budget

| `budget` | Effort applied |
| --- | --- |
| `"unlimited"` | maximum |
| `"large"` | high |
| `"medium"` | medium |
| `"small"` | low |

## File layout

```toml
# endostack model config, written by /setup-endostack.
# Each key below overrides one endostack role's default model.
# Delete a key to restore that role's default.
# "inherit" runs the role on the chat's own model; in a panel list it still adds a seat.
# Budget: large (high reasoning effort)

budget = "large"

feature = "fast"
bug-fix = "fast"
perf = "fast"
hillclimb = "fast"
judgment = "strong"
hardest = "strong"
how-explorer = "fast"
how-explainer = "strong"
why-investigator = "fast"
why-synthesizer = "strong"
recall-miner = "fast"
reflect-tooling = "fast"
reflect-judgment = "strong"
arena-runners = ["strong", "fast"]
arena-judges = ["strong", "fast"]
swarm-workers = "fast"
architect-runners = ["strong", "fast"]
interrogate-reviewers = ["strong", "fast"]
```

On an agent with no per-subagent model choice, write every role as `"inherit"` and keep the panel lists at the length the user wants, for example `interrogate-reviewers = ["inherit", "inherit"]`.
