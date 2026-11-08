---
name: manuwright-verify
description: Run ManuWright's deterministic checks before recording a gate PASS or claiming a manuscript step is finished. Use for "verify", "check citations", "check numbers", "gate", "submission check", or before moving to the next phase.
---

# ManuWright verification

Run from the paper folder (the one with `project.json`).

- Whole manuscript, by profile: `manuwright verify --project project.json --profile draft` (then `revision` or `submission`). Report every FAIL or BLOCKED check with its `detail`; fix sources, never the checker.
- Single artifact: `manuwright citations drafts/05_results.md`, `manuwright numbers drafts/05_results.md`, `manuwright abstract ...`, `manuwright crossrefs ...`, `manuwright lint drafts`.
- Section gate ledger: `manuwright verify-all <artifact> --gate review/gates/<gate>.GATE.md --artifact <artifact> --require-check constraint --require-check citation --require-check numbers --require-check logic --verify-hash artifact=<artifact> --cross-check citation=<artifact> --cross-check numbers=<artifact>`.
- Independent semantic review: `manuwright packet --project project.json` builds a local packet. Sending it to another model needs the author's explicit consent.
- A PASS covers only the checks that ran. Never write `status: PASS`, approvals or review receipts that were not actually produced.
