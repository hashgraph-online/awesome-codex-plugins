# Reach (blast-radius tier)

> Bounded context: **BC1 Corpus**. Ubiquitous-language term introduced by ag-bsf6
> (epic ag-lhu0, memory-system re-architecture).

**Reach** is the *blast-radius* of a knowledge entry — how many agents pay the
token cost of carrying it. It is **orthogonal to maturity**: maturity answers
*"is this true?"*; reach answers *"how widely is it injected?"*. An entry has
exactly one reach tier:

| Reach | Meaning | Cost model |
|-------|---------|------------|
| `bead` | per-bead working context; lives on the bead, dies on close | blast radius = 1 work item |
| `pull` | queried on demand via `ao corpus inject --query` | **default**; paid per use |
| `always` | auto-injected at `ao session bootstrap` for every session | paid every session — kept tiny |

**Default is `pull`.** An entry with no `reach:` frontmatter is read as `pull`
(see `SanitizeReach`, `cli/internal/search/learnings.go`).

**`always` is computed, never authored.** A learning may not set `reach: always`
by hand. The `always` tier is a *projection* of `maturity == established` ∩
*canon-promoted* (the verification-earned team canon) — the anti-self-certification
invariant (ag-oqha). The T2 always-set is hard-capped at 1200 tokens at session
bootstrap (ag-11bi). This keeps the always-on injection cost bounded and earns its
place by verification rather than assertion.

Relates to: [[citation]] (use signals feed promotion), [[anti-pattern]]
(canon-promoted high-severity anti-patterns are `always`-eligible guardrails),
[[context-density-rule]] (reach is the per-entry expression of the density budget).
