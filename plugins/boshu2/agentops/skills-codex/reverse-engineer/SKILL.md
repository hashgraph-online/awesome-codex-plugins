---
name: reverse-engineer
description: Reverse-engineer an authorized repo, binary
---
# $reverse-engineer

Reverse-engineer an external system into two things: a **mechanically-verifiable teardown** (feature inventory + registry + specs, optionally a security audit) and a **steal-map** — what to adopt into our surfaces, what to leave behind. The teardown is the evidence; the steal-map is the decision. The original failure mode this skill exists to prevent: reading a competitor's README and "deciding" from vibes.

**Triggers:** "reverse-engineer X", "tear down Y", "what should we steal from Z", "evaluate competitor/upstream", "should we fork/adopt/build-native".

## ⚠️ Constraints — Hard Guardrails (MANDATORY)

- Only operate on code/binaries you own or have **explicit written authorization** to analyze — this matters because unauthorized teardown is the legal/IP line.
- Do not provide steps to bypass protections/ToS or to extract proprietary source/system prompts.
- Do not output reconstructed proprietary source or embedded prompts (index only; redact in reports) — to prevent reproducing protected IP.
- Redact secrets/tokens/keys if encountered; run the secret-scan gate over outputs to prevent credential leakage.
- Always separate **docs say** vs **code proves** vs **hosted/control-plane**.

## Phase 1 — Mechanical teardown (the script)

Produce evidence, not vibes. The script clones (pinned), scans CLI/config/artifact surface, and writes a feature inventory + machine-checkable registry + spec set.

```bash
python3 skills/reverse-engineer/scripts/reverse_engineer.py <product> --mode=repo \
  --upstream-repo="https://github.com/org/repo.git" --upstream-ref=v1.0.0 \
  --output-dir=".agents/research/<product>/"
```

Binary mode requires `--authorized` (see Invocation Contract + Self-Test). Use the bundled demo fixture if you lack authorization for a real binary.

## Phase 2 — The steal-map (the decision)

Map each capability the teardown found onto **our** surfaces. This is the part that turns research into a decision. Emit `.agents/research/<product>/steal-map.md` with a table; every row cites the teardown evidence **and** the matching surface in our repo.

| Their capability | Our surface today | Verdict |
|---|---|---|
| `<feature>` | `<our file / skill / CLI, or "none">` | **have** / **gap** / **steal** / **park** / **reject** |

Verdict rules (hard-won — apply them, do not skip):

- **steal** — we lack it and it advances our core. Steal the *pattern*, not the storage engine: re-express in our primitives, never vendor their runtime.
- **park** — real, but it's substrate we deliberately delegate (e.g. orchestration per ADR-0009) or downstream of an unproven bet. Name it, don't build it.
- **reject** — it conflicts with our doctrine (e.g. a self-reported completion edge where we require a verdict — "no verdict = not done").
- **have** — we already do this; confirm it still holds, move on.
- **gap** — we should have it and don't. These are the steal candidates.

Discipline that makes the map trustworthy:

- **Validated cross-family, not self-report.** Get facts on *how* they implement each capability from their code, cross-checked by an independent (cross-family) reader — never from their README or one model's summary.
- **Probe the real state, don't argue from stale.** Re-verify our side against the live tree before calling something a gap; every "X is missing" carries the search that proved it.
- **The steal is the pattern, not the platform.** Their robustness is usually one idea (unification, a gate, a reconcile loop). Steal the idea; leave the scaffolding.

## Route one-way-door adoptions into the duel

If adopting a steal is a **one-way door** (an architecture fork, a new bounded context, a migration), do not decide it here. Hand the steal-map to **`$discovery`** (its mixed-model fanout duel) or **`$council`** — ≥3 opposed theses + a cross-family voice winnow to the smallest first slice. This skill produces the *map*; the duel picks the *route*.

## Invocation Contract

Required: `product_name`. Common flags: `--mode=repo|binary|both`, `--upstream-repo`, `--upstream-ref` (pins the clone, records the resolved SHA in `clone-metadata.json`), `--output-dir` (default `.agents/research/<product>/`), `--security-audit`, `--authorized` (mandatory for binary mode — refuses without it). Full list: `python3 skills/reverse-engineer/scripts/reverse_engineer.py --help`.

## Outputs (MUST be generated)

Phase-1 teardown under `output_dir/`: `feature-inventory.md`, `feature-registry.yaml`, `feature-catalog.md`, `spec-architecture.md`, `spec-code-map.md`, `spec-cli-surface.md`, `spec-clone-vs-use.md`, `spec-clone-mvp.md`, `clone-metadata.json` (pinned-ref provenance). Security mode adds `output_dir/security/`: `threat-model.md`, `attack-surface.md`, `dataflow.md`, `crypto-review.md`, `authn-authz.md`, `findings.md`, `reproducibility.md`, `validate-security-audit.sh`. Phase-2: `steal-map.md`.

## Reproducibility + fixtures

`--upstream-ref` pins the clone (fetch `FETCH_HEAD`, record SHA) so contracts can be committed as golden fixtures and diffed across runs. Regression test: `bash skills/reverse-engineer/scripts/repo_fixture_test.sh`. To update a fixture when contracts legitimately change, re-run with the new pinned ref, copy the contract files into `fixtures/<product>/`, and commit.

## Self-Test (acceptance)

```bash
bash skills/reverse-engineer/scripts/self_test.sh
```

Must show: feature inventory generated, registry generated, registry validator exits 0; in security mode `validate-security-audit.sh` exits 0 and the secret scan passes.

## Examples

### Reverse-engineer an OSS CLI (repo mode) → steal-map

`$reverse-engineer cc-sdd --mode=repo --upstream-repo="https://github.com/gotalab/cc-sdd.git" --upstream-ref=v1.0.0` → clones pinned, scans surface, writes inventory/registry/specs, then you map each feature onto our surfaces (have/gap/steal/park/reject) in `steal-map.md` and route one-way-door steals to `$discovery`.

### Binary analysis with security audit

`$reverse-engineer ao --authorized --mode=binary --binary-path="$(command -v ao)" --security-audit` → static analysis (metadata, linked libs, embedded-archive signatures, index only) plus the security suite under `output_dir/security/`; the secret-scan gate passes.

## Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| Refuses binary analysis | Missing `--authorized` | Add `--authorized` (explicit written authorization required). |
| No `clone-metadata.json` | `--upstream-repo` not passed | Pass `--upstream-repo` (and optionally `--upstream-ref`). |
| Fixture diff fails | Upstream changed / stale golden | Re-run pinned, refresh `fixtures/`, commit. |
| `spec-cli-surface.md` missing | No Node/Python/Go CLI detected | Surface is documented in `spec-code-map.md` instead. |
| Steal-map is all "steal" | Skipped the park/reject rules | Substrate we delegate is **park**; doctrine conflicts are **reject** — not everything novel is worth adopting. |

## Quality Rubric

- [ ] Every steal-map row cites teardown evidence **and** our matching surface (or "none").
- [ ] Verdicts use the full set — `have`/`gap`/`steal`/`park`/`reject` — not everything marked "steal".
- [ ] Facts on *how* they implement come from their code, cross-checked cross-family — not a README.
- [ ] One-way-door adoptions are routed to `$discovery` or `$council`, not decided here.
- [ ] Secret-scan gate passed over all outputs; no proprietary source/prompts reproduced.

## See Also

- [discovery](../discovery/SKILL.md) — mixed-model fanout duel; route one-way-door steals here
- [council](../council/SKILL.md) — multi-judge fork decision for irreversible adoptions
- [research](../research/SKILL.md) — general exploration; this is its external-system specialization

## Reference Documents

- [references/reverse-engineer.feature](references/reverse-engineer.feature) — executable spec: repo-mode feature catalog + code map, binary-mode security audit, durable spec artifacts
