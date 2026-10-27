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

Reverse-engineer an external system into two things: a **teardown** (feature
inventory, a registry of where to read, CLI and contract specs, optionally a
security audit) and a **steal-map** (the decision: what to adopt into our
surfaces and what to leave behind). A decision row that must cite evidence can
be re-checked by anyone; a decision made from impressions cannot be re-checked
by its own author. Deciding from a competitor's README is the failure this
skill exists to prevent.

## ⚠️ Constraints — Hard Guardrails (MANDATORY)

- Only operate on code/binaries you own or have **explicit written authorization** to analyze — this matters because unauthorized teardown is the legal/IP line.
- Do not provide steps to bypass protections/ToS or to extract proprietary source/system prompts.
- Do not output reconstructed proprietary source or embedded prompts (index only; redact in reports) — to prevent reproducing protected IP.
- Redact secrets/tokens/keys if encountered. The output validator runs this skill's `scripts/security/scan_secrets.sh` over the whole output dir in every phase; a hit fails it until you redact.
- Always separate **docs say** vs **code proves** vs **hosted/control-plane**.

## Evidence rules

- **Tag every capability by its source.** `code`: their source or binary
  shows it; cite the file:line (for a binary, the teardown output line) you
  opened and record what the code actually does, which is often narrower than
  the claim. `docs`: a README, doc page or announcement says it; unverified.
  `hosted`: a service or control plane you cannot inspect.
- **The registry is an index, not evidence.** It lists where to read. In repo
  mode its groups start `impl: unclassified` (binary mode writes `client` groups
  anchored to `binary-symbols.txt`, still not `code` evidence); `client` or
  `mixed` needs anchors, and `control-plane` means `hosted`. A registry entry
  alone never makes a row `code`.
- **No code access, no steal.** With only docs, a README or a landing page,
  every row about their implementation is `docs` and unverified. It can be
  `gap`, `park` or `reject`, never `steal`.
- **Prove our side on the live tree.** A `have` row cites our file. Every
  "missing" row carries the search that proved it (command and scope). Check
  what our current stack already offers before calling anything missing.
- **Re-open before a steal.** Re-open each cited file before marking `steal`;
  a summary from memory is not evidence.
- **The steal is the pattern, not the platform.** Their robustness is usually
  one idea (unification, a gate, a reconcile loop). Re-express it in our
  primitives; never vendor their runtime or storage engine.

## Phase 1 — teardown

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/reverse-engineer`. Replace
`<skill-dir>` with that absolute path before running a command. The working
directory stays the user's repository. If the host did not show where this
skill is installed, use the directory of the SKILL.md you read. If you cannot
determine it, do not guess a path or run a same-named script from the current
repository; say the bundled script is unavailable and build the inventory and
steal-map by hand as in docs-only mode below.

With an authorized clone or binary, the script clones (pinned), scans the
CLI/config/artifact surface, writes the inventory, registry and specs, and
validates the teardown:

```bash
python3 "<skill-dir>/scripts/reverse_engineer.py" <product> --mode=repo \
  --upstream-repo="https://github.com/org/repo.git" --upstream-ref=v1.0.0 \
  --output-dir=".agents/scratch/reverse-engineer/<product>/"
```

The clone lands in `.tmp/<product>/` under the current directory unless
`--local-clone-dir` names another place; keep it out of your commits. Binary
mode requires `--authorized`; without authorization for a real binary, run
`bash "<skill-dir>/scripts/self_test.sh"`, which builds a demo binary (needs Go). Flags, the full
output list, fixtures and tests are in [the invocation reference](references/invocation.md).

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
teardown, the code it points to, and a fresh read of our repository. A missing or malformed map is an
incomplete skill result, not a script success relabelled as a decision.

| Their capability | Our surface today | Verdict |
|---|---|---|
| `<feature>` (code: `<file:line>`), (docs) or (hosted) | `<our file / skill / CLI>`, or "none" plus the search that proved it | **have** / **gap** / **steal** / **park** / **reject** |

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

## Validation and handoff

After authoring `steal-map.md`, validate the complete output with
`$output_dir`, `$security_audit`, `$sbom`, and `$upstream_ref_set` (each
numeric flag `0|1`):

```bash
bash "<skill-dir>/scripts/validate-output.sh" \
  --output-dir "$output_dir" --phase complete \
  --security-audit "$security_audit" --sbom "$sbom" \
  --upstream-ref-set "$upstream_ref_set"
```

It fails any table row without a source tag or one of the five verdicts, and
any `steal` without `code` evidence; with an upstream ref it requires the
resolved commit in `clone-metadata.json`. It must exit 0 before handoff, or the
report says it did not run (docs-only mode).

If adopting a steal is a **one-way door** (an architecture fork, a new bounded
context, a storage or data migration), do not decide it here: hand the
validated steal-map to [Plan](../plan/SKILL.md), which shapes the selected
option in the existing intent source. [Idea Genie](../idea-genie/SKILL.md) duel
mode or [Premortem](../premortem/SKILL.md) may challenge it as advisory
evidence; neither grants readiness or continuation authority. Ordinary `have`,
`park` and `reject` rows are evidence-backed terminal decisions.

For general exploration rather than one external system, use
[Research](../research/SKILL.md). The scenarios in
[reverse-engineer.feature](references/reverse-engineer.feature) document the
behavior; this skill's `scripts/validate.sh` and `scripts/self_test.sh` check it.
