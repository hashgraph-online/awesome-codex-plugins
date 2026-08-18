---
name: validate
description: 'Freshly judge exact subject content against Triggers: "validate", "independently validate", "vibe".'
---
# Validate

Independently judge one exact subject against the acceptance in its existing
bead or caller source, return one semantic result, and stop. Validate is the
sole `verdict.v2` writer when persistence is requested. It never asks the model
to reconstruct Plan or Candidate packets.

## Preconditions

- The subject is a nonempty implementation candidate: the manifest lists at
  least one entry, and `store-verdict` refuses an empty one. Plans, audits,
  reviews, and other control artifacts are not completion subjects unless the
  caller explicitly requested document review.
- The intent source is available as a caller-owned artifact or runtime-owned
  content-addressed snapshot; its acceptance digest is derived automatically.
- The subject manifest still matches the subject.
- Author and validator context IDs are explicit.
- Freshness is explicitly attested with `source: runtime | caller` and an
  attester identity.

Missing, colliding, or unattested identities produce `NOT_PROVEN`. This is a
declared trust fact, not cryptographic proof that contexts were isolated.

## Cross-model fresh validator (caller-elected)

A caller may request that the fresh validator run on a different model than
the author. Dispatch via the controller-session recipe in
the `agent-native` model-dispatch recipe (`codex-exec` and/or `ntm`,
probed at runtime). Record author and validator `model_identity` in evidence
refs and freshness attestation notes — do not change `verdict.v2` schema. If
the requested validator model has no live adapter, disclose the unsatisfied
diversity request and proceed same-model; never invoke `claude -p` /
`claude --print`. Single fresh validator remains the default shape.

## Mutating-check quarantine

Before running any acceptance-listed command, classify it as read-only or
subject-mutating. Regen scripts, sync scripts, formatters, and anything with
`--force` are subject-mutating until proven otherwise. Never run a
subject-mutating check against an uncommitted subject: on 2026-07-15,
`scripts/test-ci-deterministic-gates.sh` regenerated `skills-codex/` from HEAD
mid-validation and destroyed the uncommitted subject, forcing `NOT_PROVEN`
(verdict `b6e759dd...cb6a`); only restoring the subject and revalidating in a
fresh context produced the PASS (`e9b6cdb8...37b9`). If a mutating check is
genuinely required by acceptance, run it against a disposable copy or a
committed subject, never the judged working tree.

## Scope disclosure

`not_checked` has exactly one meaning: **in-scope acceptance surface this
validation did not verify**. PASS asserts that the whole declared acceptance
surface was verified, so a PASS carries no `not_checked` entries; the helper
refuses one and records a `validate.integrity` finding.

That rule never pays for deleting an honest caveat, because every kind of scope
limit has a home that survives inside a PASS:

| Scope limit | Home | Example |
|---|---|---|
| A criterion proven by a bounded check | `criteria[].reason` on that criterion | "proven by the unit suite; the full integration matrix was not replayed" |
| A declared non-goal or out-of-scope area | the intent source's non-goals, optionally restated as an evidence-backed boundary criterion in `criteria` | "`cli/**` is a declared non-goal; the diff proves it untouched" |
| Residual risk or judgment caveat | the caller-facing report | "the migration path is untested against pre-3.0 stores" |
| Acceptance that genuinely went unverified | `not_checked`, and the result is `NOT_PROVEN` rather than PASS | "criterion 3 needs hardware this context cannot reach" |

Emptying `not_checked` to obtain PASS is a contract violation, not a
workaround. If acceptance really went unverified, the honest result is
`NOT_PROVEN`. If the entry was never acceptance in the first place, it belongs
in one of the other homes, where it stays visible in the stored artifact
instead of being deleted.

## Helper commands

The helper ships beside this file. Invoke it through this skill's own
directory rather than a checkout-relative path: `$SKILL_DIR` is the directory
containing this `SKILL.md` — `skills/validate/` in a repository checkout,
`.agents/skills/validate/` in an installed runtime.

| Command | Required | Optional |
|---|---|---|
| `manifest` | `--root <dir>`, `--include <path>` (repeatable, at least one) | `--exclude <path-or-glob>` (repeatable), `--base-manifest <file>`, `--git-metadata-json <json>`, `--output <file>` |
| `verify-manifest` | `--root <dir>`, `--manifest <file>` | `--base-manifest <file>` |
| `snapshot-intent` | `--source <file>` (`-` reads stdin) | `--workspace <dir>`, `--intent-dir <dir>` |
| `digest` | `<json-file>` positional | none |
| `store-verdict` | `--draft`, `--intent-source`, `--subject-manifest`, `--author-context-id`, `--validator-context-id`, `--freshness-source <runtime\|caller>`, `--freshness-attester-id`, `--scope-result <PASS\|FAIL\|NOT_PROVEN>` | `--workspace <dir>`, `--verdict-dir <dir>` |

```sh
python3 "$SKILL_DIR/scripts/validate.py" manifest \
  --root . --include skills/validate --exclude '**/*.log' --output manifest.json
```

## Workflow

1. Recompute and compare `subject-manifest.v1` with the `manifest` command
   above (`--root` plus at least one `--include`). The helper uses only
   filesystem content; Git commit/tree IDs are optional metadata. Derive the
   manifest at the start of validation and re-derive it at the end; any
   mismatch between the two is subject mutation and returns `NOT_PROVEN`.
2. Confirm the intent-source digest has not changed since implementation. If
   the subject changed or complete changed-path coverage cannot be derived,
   return `NOT_PROVEN`.
3. Adjudicate the actual diff, not a declared path list: compare
   runtime-derived actual changed paths against the intent's scope classes. A
   proven out-of-scope path returns `FAIL`; incomplete scope evidence returns
   `NOT_PROVEN`.
4. Inspect the exact subject and factual evidence. Reported exit codes are
   claims, not evidence: re-execute the claimed proofs that bear on acceptance
   (see the freshness rules below for when a digest-bound receipt suffices).
   If the subject changes a test, gate, fixture, golden, tolerance, suppression,
   or acceptance source, determine whether the original intent requires that
   change and whether green came from implemented behavior rather than a
   weakened oracle. Green obtained by weakening acceptance is `FAIL`, not
   evidence of completion.
   Judge every acceptance criterion and record criterion-level results,
   findings, evidence references, `checked`, and any acceptance surface that
   went unverified in `not_checked` (see Scope disclosure).
5. Choose exactly one semantic result: `PASS`, `FAIL`, or `NOT_PROVEN`. Return
   it with criterion results, findings, evidence references, `checked`,
   `not_checked`, the acceptance and subject identities, distinct author and
   validator context IDs, and the freshness attestation. PASS requires distinct
   identities, explicit freshness, nonempty checked scope, top-level evidence,
   evidence for every criterion, and an empty `not_checked`; route bounded
   proofs, declared non-goals, and residual risk to the homes named in Scope
   disclosure rather than deleting them or downgrading a proven result.
6. Only when the caller requests machine-readable evidence or a declared
   downstream consumer requires it, persist canonical `verdict.v2` with the
   helper's
   `store-verdict --draft <draft.json> --intent-source <resolved-intent>
   --subject-manifest <manifest.json> --author-context-id <id>
   --validator-context-id <id> --freshness-source <runtime|caller>
   --freshness-attester-id <id> --scope-result <PASS|FAIL|NOT_PROVEN>`. The
   helper snapshots the exact resolved intent under
   `<workspace>/.agents/ao/intents/sha256/<digest>.intent`, then computes and
   injects intent and subject digests plus author, validator, and freshness
   facts. Identity and changed-path facts come from runtime-derived inputs and
   receipts, not model transcription. Storage defaults to
   `<workspace>/.agents/ao/verdicts/sha256/<digest>.json`; callers may provide
   `verdict_dir`.
7. Return the semantic result and, when persisted, the artifact path and digest.
   Stop.

The digest is SHA-256 over canonical JSON with `artifact_digest` omitted. Writes
use a same-directory temporary file, flush, fsync, and atomic rename. Identical
existing content is idempotent success; conflicting content is an integrity
failure represented by `NOT_PROVEN`.

## Freshness without duplication

Fresh validation means independent judgment over the exact subject. It does not
require mechanically replaying every author command. Verify intent identity,
scope, evidence digests, and every acceptance criterion; independently rerun
the risk-critical, uncertain, or insufficiently evidenced checks. A
digest-bound deterministic receipt may prove routine facts. Replay an expensive
full suite only when acceptance requires that result or the supplied receipt
cannot establish it.

## Boundary

Validate emits no WARN, confidence, disposition, briefing learning, owner,
next action, repair, retry, replan, helper, escalation, tracker, Git, release,
closure, or delivery state. Generic provenance may record a verdict later, but
ledger availability cannot change its validity.
