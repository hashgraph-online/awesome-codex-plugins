---
name: reverse-engineer
description: 'Tear down a competitor''s repo or product into a feature inventory and adoption choices. Use when: comparing us to another tool or asking what to steal.'
practices:
- legacy-code-seams
- ddd-bounded-context
- adr
hexagonal_role: supporting
consumes: []
produces:
- '.agents/scratch/reverse-engineer/*/'
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
metadata:
  dependencies: []
  capabilities: [reverse_engineer]
  effects: [clone_upstream_repo, authorized_binary_execution, write_teardown_artifacts]
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  internal: false
output_contract: validated phase-1 teardown directory, followed by a caller-authored and validated phase-2 steal-map.md
---
# Reverse Engineer

Reverse-engineer an external system into two things: a **teardown** (the
evidence: feature inventory, machine-checkable registry and specs, optionally a
security audit) and a **steal-map** (the decision: what to adopt into our
surfaces and what to leave behind). A decision row that must cite evidence can
be re-checked by anyone; a decision made from impressions cannot be re-checked
by its own author. Deciding from a competitor's README is the failure this
skill exists to prevent.

## ⚠️ Constraints — Hard Guardrails (MANDATORY)

- Only operate on code/binaries you own or have **explicit written authorization** to analyze — this matters because unauthorized teardown is the legal/IP line.
- Do not provide steps to bypass protections/ToS or to extract proprietary source/system prompts.
- Do not output reconstructed proprietary source or embedded prompts (index only; redact in reports) — to prevent reproducing protected IP.
- Redact secrets/tokens/keys if encountered; run the secret-scan gate over outputs to prevent credential leakage.
- Always separate **docs say** vs **code proves** vs **hosted/control-plane**.

## Evidence rules

- **Tag every capability by its source.** `code`: their source, binary or
  teardown registry shows it; cite the file:line or registry entry and record
  what the code actually does, which is often narrower than the claim. `docs`:
  a README, doc page or announcement says it; unverified. `hosted`: a service
  or control plane you cannot inspect.
- **No code access, no steal.** With only docs, a README or a landing page,
  every row about their implementation is `docs` and unverified. It can be
  `gap`, `park` or `reject`, never `steal`.
- **Prove our side on the live tree.** A `have` row cites our file. Every
  "missing" row carries the search that proved it (command and scope). Check
  what our current stack already offers before calling anything missing.
- **Independently checked, not self-report.** Facts on how they implement a
  capability come from code, cross-checked by a fresh reader, never from one
  context's summary. Model family is optional metadata, not a trust requirement.
- **The steal is the pattern, not the platform.** Their robustness is usually
  one idea (unification, a gate, a reconcile loop). Re-express it in our
  primitives; never vendor their runtime or storage engine.

## Phase 1 — teardown

With an authorized clone or binary, the script clones (pinned), scans the
CLI/config/artifact surface, writes the inventory, registry and specs, and
validates the teardown:

```bash
python3 skills/reverse-engineer/scripts/reverse_engineer.py <product> --mode=repo \
  --upstream-repo="https://github.com/org/repo.git" --upstream-ref=v1.0.0 \
  --output-dir=".agents/scratch/reverse-engineer/<product>/"
```

Binary mode requires `--authorized`; use the bundled demo fixture if you lack
authorization for a real binary. Flags, output inventory, earlier output paths,
fixtures and the self-test are in [the invocation reference](references/invocation.md).

Without code access (only a README, docs site or landing page), skip the
script: build the inventory and steal-map by hand with each row tagged `docs`
or `hosted`, and say that no teardown validator ran. When the code is readable
but the script cannot run on it, read the code directly and cite `file:line`
for each `code` row; the validator gap still gets reported.

## Phase 2 — steal-map

Map each capability onto **our** surfaces in
`.agents/scratch/reverse-engineer/<product>/steal-map.md`. The script stops
after validating Phase 1; it cannot truthfully decide whether our live tree
has, lacks, or should adopt a capability. The caller authors the map from the
registry plus a fresh read of our repository. A missing or malformed map is an
incomplete skill result, not a script success relabelled as a decision.

| Their capability | Our surface today | Verdict |
|---|---|---|
| `<feature>` (code: `<registry entry>`, or docs, or hosted) | `<our file / skill / CLI>`, or "none" plus the search that proved it | **have** / **gap** / **steal** / **park** / **reject** |

Each row gets exactly one verdict:

- **have** — our live tree already does it; cite the file and confirm it still holds.
- **steal** — we lack it, `code` evidence shows how they do it, and it advances
  our core. Take the pattern, re-expressed in our primitives.
- **gap** — we lack it and would want it if it holds up, but steal is not
  earned: their mechanism is `docs` or `hosted` only, or its value to our core
  is unshown. Name the evidence that would decide it.
- **park** — real, but deliberately not ours to build now: substrate we
  delegate (for AgentOps, ADR-0009 keeps scheduling, supervision and queues
  external) or downstream of a bet we have not made. Name it, don't build it.
- **reject** — conflicts with our doctrine (e.g. a completion edge with no check
  behind it, where we require checks and CI, plus one fresh judgment for a
  costly mistake).

When two seem to fit, reject beats park, and park beats steal or gap; between
steal and gap, the evidence rules decide.

## Route one-way-door adoptions into planning

If adopting a steal is a **one-way door** (an architecture fork, a new bounded
context, a storage or data migration), do not decide it here. Hand the
steal-map to Plan. Dueling Idea Genies or Premortem may challenge the choice as
advisory evidence. Plan alone shapes the selected option in the existing intent
source; neither strategy grants readiness or continuation authority.

## Validation

After authoring `steal-map.md`, validate the complete output with
`$output_dir`, `$security_audit`, `$sbom`, and `$upstream_ref_set` (each
numeric flag `0|1`):

```bash
bash skills/reverse-engineer/scripts/validate-output.sh \
  --output-dir "$output_dir" --phase complete \
  --security-audit "$security_audit" --sbom "$sbom" \
  --upstream-ref-set "$upstream_ref_set"
```

Give the validated `steal-map.md` to Plan for one-way-door candidates; ordinary
`have`, `park`, and `reject` rows remain evidence-backed terminal decisions.

## Quality Rubric

- [ ] With an upstream ref, `feature-registry.yaml` and `clone-metadata.json` record the resolved commit.
- [ ] Every row tags `code`/`docs`/`hosted` and cites teardown evidence **and** our matching surface, or "none" with the search that proved it.
- [ ] Verdicts use the full set — `have`/`gap`/`steal`/`park`/`reject` — and no `docs` or `hosted` row is `steal`.
- [ ] One-way-door adoptions are supplied to Plan, not decided here.
- [ ] Secret-scan gate passed over all outputs; no proprietary source/prompts reproduced.
- [ ] The complete-output validator exits 0 before handoff, or the report says it did not run (docs-only mode).

| Problem | Cause | Solution |
|---|---|---|
| Steal-map is all "steal" | Skipped the park/reject rules | Substrate we delegate is **park**; doctrine conflicts are **reject** — not everything novel is worth adopting. |

## See Also

- [plan](../plan/SKILL.md) — shape selected steals in the existing intent source
- [idea-genie](../idea-genie/SKILL.md) — optional advisory challenge (duel mode)
- [premortem](../premortem/SKILL.md) — optional advisory challenge of the exact plan
- [research](../research/SKILL.md) — general exploration; this is its external-system specialization

## Reference Documents

- [references/invocation.md](references/invocation.md) — flags, outputs, earlier output paths, fixtures, self-test, script troubleshooting
- [references/reverse-engineer.feature](references/reverse-engineer.feature) — executable spec: repo-mode feature catalog + code map, binary-mode security audit, durable spec artifacts
