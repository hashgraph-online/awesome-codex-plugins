---
name: validate
description: Freshly judge exact subject content against
---
# Validate

Independently judge one exact subject against the acceptance in its existing
bead or caller source, write one durable verdict, and stop. Validate is the sole
verdict writer. It never asks the model to reconstruct Plan or Candidate
packets.

## Preconditions

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

## Workflow

1. Recompute and compare `subject-manifest.v1` using
   `python3 skills/validate/scripts/validate.py manifest`. The helper uses only
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
   Judge every acceptance criterion and record criterion-level results,
   findings, evidence references, `checked`, and `not_checked`.
5. Choose exactly one semantic result: `PASS`, `FAIL`, or `NOT_PROVEN`. PASS
   requires distinct identities, explicit freshness, nonempty checked scope,
   top-level evidence, and evidence for every criterion.
6. Persist canonical `verdict.v2` with `store-verdict --draft <draft.json>
   --intent-source <resolved-intent> --subject-manifest <manifest.json>
   --author-context-id <id> --scope-result <PASS|FAIL|NOT_PROVEN>`. The helper
   snapshots the exact resolved intent under
   `<workspace>/.agents/ao/intents/sha256/<digest>.intent`, then computes and
   injects intent and subject digests. Identity and changed-path facts come from
   runtime-derived manifests and receipts, not model transcription. Verdict
   storage defaults to `<workspace>/.agents/ao/verdicts/sha256/<digest>.json`;
   callers may provide `verdict_dir`.
7. Return the artifact path and digest. Stop.

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
