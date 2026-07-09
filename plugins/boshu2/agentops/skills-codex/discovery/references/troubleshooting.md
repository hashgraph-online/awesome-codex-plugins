# Discovery Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Pre-mortem retries hit max | Plan has unresolvable risks | Review findings in `.agents/council/*pre-mortem*.md`, refine goal, re-run `/discovery` |
| No epic ID after plan | br unavailable and TaskList empty | Check tracking mode, verify `/plan` produced output |
| Brainstorm loops without advancing | Goal too vague for automated clarification | Use `--interactive` or provide a specific goal |
| ao search returns nothing | No prior sessions on this topic | Normal — proceed without history context |
