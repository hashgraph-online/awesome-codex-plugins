# Auto-drafted Learnings — F5.4 Feedback Compiler

The `cli/internal/feedbackcompiler` package writes **draft** learning files to
`docs/learnings/` automatically when the verdict ledger records a fail->pass
transition for a directive. These drafts are distinct from forge's
transcript-mined candidates:

| Source | Written to | Status |
|--------|-----------|--------|
| Forge (transcript mining) | `.agents/learnings/` | provisional |
| Feedback compiler (ledger transitions) | `docs/learnings/` | **draft** |

## Promotion rule

Auto-drafted files carry `status: draft` and `directive_id` in their
frontmatter (per ADR-0005 §2.6). A human must review and promote them — the
compiler never auto-promotes. Filename pattern:
`YYYY-MM-DD-auto-<directive-slug>-fail-to-pass.md`.

## Idempotency

If a draft for a transition already exists the compiler skips it. Running the
compiler again after promotion is safe.

## Implementation

- Package: `cli/internal/feedbackcompiler/`
- Reads: `.agents/goals/verdict-ledger.json` (via `cli/internal/verdictledger`)
- Writes: `docs/learnings/YYYY-MM-DD-auto-<slug>-fail-to-pass.md`
- Bead: soc-58nt.5.4
