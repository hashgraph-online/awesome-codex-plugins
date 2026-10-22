# Environment example drift — finite — reconcile a root `.env.example` with literal config reads

Use when a project keeps a root `.env.example` and the owner wants its variable names compared with the configuration the code actually reads. The owner wakes to a small, evidence-backed template diff and a list of anything that needs their judgment. Typical time: 1–2 hours.

Supported on repositories with a tracked root `.env.example` and environment-variable names that can be found literally in the project's source or configuration. Use repository mode and the project's existing checks. If the template is absent, variable names are assembled dynamically, or the source of truth is unclear, record the limitation and stop that part of the review. Never select this entry in artifact mode; do not `git init` a notes folder.

Write the work receipt from `receipts/cycle-specialist-evidence.md` using `mode: env-example-drift`. Record commands and source paths actually read, findings or `unavailable`, and skipped surfaces. Unparsed projection or search output is `unavailable`, never an empty result or "no findings".

```text
- [ ] **Environment example drift — reconcile the root template with literal configuration reads.**
  - Discovery: confirm that the root `.env.example` is tracked. Use a name-only projection to inventory its variables, then use the project's existing search and configuration conventions to find literal environment-variable reads in tracked source and configuration. If checking placeholder style, expose only whether each right-hand side is empty or non-empty. Do not inspect real environment files or display template values.
  - Compare each template name with its in-repository references and each literal reference with the template. Record file paths, line references, variable names, and dispositions (`matched`, `added`, or `parked`) in the work receipt; never record right-hand-side values.
  - Add a missing name only when tracked code or project documentation proves it is required and the template's existing convention can be established without exposing right-hand-side text. Leave the value empty only when empty values are the established placeholder convention. Otherwise park it for the owner.
  - Treat optional names, dynamically assembled lookups, and names that may be consumed by deployment systems outside the repository as uncertain. Never remove a template name just because a local search found no reference; park it with the reason and evidence instead.
  - Never reveal, copy, or record right-hand-side contents from `.env.example`. Never read, display, copy, or record values from `.env`, `.env.local`, process environments, secret stores, or deployment settings. Never run the application against real credentials or add, guess, or expose a credential.
  - Never change application code, runtime defaults, deployment configuration, or hosted settings. This shift only reconciles the example template; owner decisions and ambiguous references stay parked.
  - A finding already recorded in `snag-log.md` is a `duplicate` that links to the existing record and carries forward its disposition. Preserve closed canonical dispositions (`fixed`, `ignored`, `answered`, `rejected-because`, or `accepted-tradeoff`); keep matching open snags linked and open. Duplicates are not new owner decisions and do not require a fresh disposition.
  - Ends when every template name and every discovered literal reference has an evidence-linked disposition, every uncertain case is parked with a reason, and a second name-only comparison agrees with the receipt.
  - Verify: run the project's existing lint/test gate and `git diff --check`; repeat the same name-only comparison after edits. The item gate must be green at every commit.
```
