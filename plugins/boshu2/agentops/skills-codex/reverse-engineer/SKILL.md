---
name: reverse-engineer
description: Reverse-engineer an authorized repo, binary
---
# Reverse Engineer

Reverse-engineer an external system into two things: a **mechanically-verifiable teardown** (feature inventory + registry + specs, optionally a security audit) and a **steal-map** — what to adopt into our surfaces, what to leave behind. The teardown is the evidence; the steal-map is the decision. Separating them works because a decision row that must cite a registry entry can be re-checked by anyone, while a decision made from impressions cannot be re-checked by its own author. The original failure mode this skill exists to prevent: reading a competitor's README and "deciding" from vibes.

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

- **Independently checked, not self-report.** Get facts on *how* they implement
  each capability from code, cross-checked by a fresh reader — never from a
  README or one context's summary. Model family is optional metadata, not a
  trust requirement.
- **Probe the real state, don't argue from stale.** Re-verify our side against the live tree before calling something a gap; every "X is missing" carries the search that proved it.
- **The steal is the pattern, not the platform.** Their robustness is usually one idea (unification, a gate, a reconcile loop). Steal the idea; leave the scaffolding.

## Route one-way-door adoptions into planning

If adopting a steal is a **one-way door** (an architecture fork, a new bounded
context, or a migration), do not decide it here. Hand the steal-map to Plan.
Dueling Idea Genies or Premortem may challenge the choice as advisory
evidence. Plan alone shapes the selected option in the existing intent source;
neither strategy grants readiness or continuation authority.

## Invocation Contract

Required: `product_name`. Common flags: `--mode=repo|binary|both`, `--upstream-repo`, `--upstream-ref` (pins the clone, records the resolved SHA in `clone-metadata.json`), `--output-dir` (default `.agents/research/<product>/`), `--security-audit`, `--authorized` (mandatory for binary mode — refuses without it). Full list: `python3 skills/reverse-engineer/scripts/reverse_engineer.py --help`.

## Output Specification

Phase-1 teardown under `output_dir/`: `feature-inventory.md`, `feature-registry.yaml`, `feature-catalog.md`, `spec-architecture.md`, `spec-code-map.md`, `spec-clone-vs-use.md`, `spec-clone-mvp.md`, plus `spec-cli-surface.md` only when a CLI is detected and `clone-metadata.json` only when `--upstream-ref` is supplied. Security mode adds `output_dir/security/`: `threat-model.md`, `attack-surface.md`, `dataflow.md`, `crypto-review.md`, `authn-authz.md`, `findings.md`, `reproducibility.md`, `validate-security-audit.sh`. Phase-2: `steal-map.md`.

- **Artifact directory:** the exact `--output-dir`, defaulting to
  `$REPO/.agents/research/<product>/`.
- **Filename convention:** the fixed phase-1 and phase-2 names above; security
  files live only in the `security/` child directory.
- **Serialization/schema format:** registry is YAML, clone metadata is one JSON
  object, and inventories/specs/steal-map are nonempty Markdown files.
- **Validator command:** with `$output_dir`, `$security_audit`, `$sbom`, and
  `$upstream_ref_set` (each flag `0|1`) set:

  ```bash
  set -euo pipefail
  required=(feature-inventory.md feature-registry.yaml feature-catalog.md spec-architecture.md spec-code-map.md spec-clone-vs-use.md spec-clone-mvp.md analysis-root-path.txt validate-feature-registry.py steal-map.md)
  for name in "${required[@]}"; do
    test -f "$output_dir/$name"
    test ! -L "$output_dir/$name"
    test -s "$output_dir/$name"
  done
  test -f "$output_dir/docs-features.txt"
  test ! -L "$output_dir/docs-features.txt"
  test ! -L "$output_dir/spec-cli-surface.md"
  if [[ -e "$output_dir/spec-cli-surface.md" ]]; then
    test -f "$output_dir/spec-cli-surface.md"
    test -s "$output_dir/spec-cli-surface.md"
  fi
  python3 "$output_dir/validate-feature-registry.py"
  if [[ "$upstream_ref_set" == 1 ]]; then
    test -f "$output_dir/clone-metadata.json"
    test ! -L "$output_dir/clone-metadata.json"
    jq -e 'type == "object"' "$output_dir/clone-metadata.json" >/dev/null
  else
    [[ "$upstream_ref_set" == 0 ]]
  fi
  grep -Fqx '| Their capability | Our surface today | Verdict |' "$output_dir/steal-map.md"
  if [[ "$security_audit" == 1 ]]; then
    test -x "$output_dir/security/validate-security-audit.sh"
    if [[ "$sbom" == 1 ]]; then
      "$output_dir/security/validate-security-audit.sh" "$output_dir" --sbom
    else
      [[ "$sbom" == 0 ]]
      "$output_dir/security/validate-security-audit.sh" "$output_dir" --no-sbom
    fi
  else
    [[ "$security_audit" == 0 ]]
    [[ "$sbom" == 0 ]]
  fi
  ```
- **Downstream handoff:** give the validated `steal-map.md` to Plan for
  one-way-door candidates; ordinary `have`, `park`, and
  `reject` decisions remain evidence-backed terminal rows.

## Reproducibility + fixtures

`--upstream-ref` pins the clone (fetch `FETCH_HEAD`, record SHA) so contracts can be committed as golden fixtures and diffed across runs. Regression test: `bash skills/reverse-engineer/scripts/repo_fixture_test.sh`. To update a fixture when contracts legitimately change, re-run with the new pinned ref, copy the contract files into `fixtures/<product>/`, and commit.

## Self-Test (acceptance)

```bash
bash skills/reverse-engineer/scripts/self_test.sh
```

Must show: feature inventory generated, registry generated, registry validator exits 0; in security mode `validate-security-audit.sh` exits 0 and the secret scan passes.

## Examples

### Reverse-engineer an OSS CLI (repo mode) → steal-map

Run the skill for `cc-sdd` with `--mode=repo --upstream-repo="https://github.com/gotalab/cc-sdd.git" --upstream-ref=v1.0.0`. It clones the pinned source, scans the surface, writes inventory/registry/specs, and maps each feature onto our surfaces (`have`, `gap`, `steal`, `park`, or `reject`) in `steal-map.md`. Supply selected steals to Plan.

### Binary analysis with security audit

Run the skill for `ao` with `--authorized --mode=binary --binary-path="$(command -v ao)" --security-audit`. It performs authorized static analysis plus the security suite under `output_dir/security/`; the secret-scan check must pass.

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
- [ ] Facts on *how* they implement come from code and a fresh independent check — not a README.
- [ ] One-way-door adoptions are supplied to Plan, not decided here.
- [ ] Secret-scan gate passed over all outputs; no proprietary source/prompts reproduced.

## See Also

- [plan](../plan/SKILL.md) — shape selected steals in the existing intent source
- [idea-genie](../idea-genie/SKILL.md) — optional advisory challenge (duel mode)
- [premortem](../premortem/SKILL.md) — optional advisory challenge of the exact plan
- [research](../research/SKILL.md) — general exploration; this is its external-system specialization

## Reference Documents

- [references/reverse-engineer.feature](references/reverse-engineer.feature) — executable spec: repo-mode feature catalog + code map, binary-mode security audit, durable spec artifacts
