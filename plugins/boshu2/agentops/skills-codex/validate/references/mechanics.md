# Validate mechanics

Loaded by `SKILL.md` at the manifest step (helper commands), at cross-family
dispatch (adapters), and at scope disclosure (the homes table). `$SKILL_DIR`
is the directory containing `SKILL.md`: `skills/validate/` in a repository
checkout, `.agents/skills/validate/` in an installed runtime.

## Helper commands

Installed mechanics run through `ao provenance` (evidence helper version 1),
using `subject-manifest.v1` and `verdict.v2` unchanged. A fresh Validate agent
supplies the semantic result; Go computes identities, verifies structure and
stores the supplied result. No Python interpreter runs on this path.

| Command | Required | Optional |
|---|---|---|
| `manifest` | `--root <dir>`, `--include <path>` (repeatable) | `--exclude <path-or-glob>` (repeatable), `--base-manifest <file>`, `--git-metadata-json <json>`, `--out <relative-file>` with `--evidence-root <dir>` |
| `verify-manifest` | `--root <dir>`, `--manifest <file>` | `--base-manifest <file>` |
| `snapshot-intent` | `--source <file>` (`-` reads stdin), `--evidence-root <dir>` | none |
| `digest` | `<json-file>` positional | `--json` |
| `store-verdict` | `--root`, `--evidence-root`, `--draft`, `--intent-source`, `--subject-manifest`, `--author-context-id`, `--validator-context-id`, `--freshness-source <runtime\|caller>`, `--freshness-attester-id`, `--scope-result <PASS\|FAIL\|NOT_PROVEN>` | `--base-manifest <file>` |
| `verify-verdict` | `--verdict <digest.json>` | none |
| `verify-subject` | `--root <dir>`, `--manifest <file>`, `--verdict <digest.json>`, `--intent <file>` | `--base-manifest <file>` |

Every leaf accepts `--helper-version 1`; an incompatible version fails before
mutation. Evidence operations emit JSON by default except `digest`, which prints
the digest; `--json` requests JSON explicitly and global `--output`/`-o` selects
JSON or YAML formatting. Conflicting explicit formats fail before any write.
Exit 0 means the mechanical operation completed. Invalid input, failed
verification or filesystem errors exit 1. A stored `FAIL` or `NOT_PROVEN` may
complete storage successfully; that exit status never means semantic PASS.
`--dry-run` rejects evidence writes before mutation. `ao capabilities` carries
the actual family and leaf argument, output, effect and exit contracts.

```sh
ao provenance manifest --root . --include skills/validate \
  --exclude '**/*.log' --evidence-root "$EVIDENCE_ROOT" --out manifest.json
```

`manifest` uses only filesystem content. Symlinks bind target bytes without
following directory symlinks; executable bits and deletions bind identity.
Optional Git metadata is descriptive and excluded from identity. Unknown fields,
duplicate JSON keys, malformed paths and canonical digest mismatches fail closed.
`verify-manifest` recomputes identity and requires the matching base for deletions.
Version 1 retains the reference's asymmetric root rule: live files and symlinks
use literal include roots, while deletion selection and structural membership
use the historical filename-pattern match against the base. Verification still
requires that exact base and recomputes the complete manifest.

`store-verdict` verifies a nonempty manifest against the current subject before
storage, binds exact intent bytes and explicit runtime identities/freshness/scope,
and validates the resulting artifact using the same strict reader as `ao status`.
Author/judge collision, missing runtime facts, incomplete scope or a PASS with
unverified acceptance cannot persist an admitted PASS. Proven scope failure
forces FAIL; integrity gaps retain NOT_PROVEN with `validate.integrity` findings.
The caller still owns deriving complete changed-path coverage and freshness;
these helper inputs are attestations, not independently discovered runtime facts.

The artifact digest is SHA-256 over canonical JSON with `artifact_digest`
omitted. A synced private temporary file is atomically published without
replacing an existing address; directory durability uses the shared storage
barrier. Identical existing bytes are idempotent. Conflicting verdict bytes
remain intact and produce a separate NOT_PROVEN integrity artifact. Intent
snapshot collisions fail. Explicit manifest outputs likewise never overwrite
different existing bytes. Existing standalone proof is preserved by its owner.

## Compatibility mapping and explicit evidence routing

The old `validate.py` commands map to the same names under `ao provenance`.
`manifest`, `verify-manifest` and `digest` keep their identity contracts.
Python's manifest `--output` maps to Go's `--out`, a relative file within explicit
`--evidence-root`. AO's existing global `--output`/`-o` remains the output format;
it never names a destination file.
`snapshot-intent` replaces `--workspace`/`--intent-dir` defaults with a required
`--evidence-root`. `store-verdict` replaces `--workspace`/`--verdict-dir` with that
same explicit root and adds required `--root` to verify current subject bytes.
Its other runtime-fact flags retain their meanings. Unsupported legacy flags
fail before storage; no wrapper silently uses the old workspace default.

The evidence root must already exist outside ordinary, bare and linked Git
repositories, including symlink aliases. All output branches are checked before
any directory or temporary-file write. Intents go under
`<root>/intents/sha256/<digest>.intent`, verdicts under
`<root>/verdicts/sha256/<digest>.json`, and explicit manifest outputs stay under
that same root. Missing or invalid roots fail with no workspace fallback.
The guard also rejects split common storage exposing `objects` and `refs` even
when `HEAD` lives elsewhere. Before writes it resolves active `GIT_DIR`,
`GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`,
`GIT_WORK_TREE`, and the parent of `GIT_INDEX_FILE`. `GIT_DIR` must resolve to a
directory; its optional `commondir` pointer is followed when `GIT_COMMON_DIR` is
not supplied. Known common-directory `objects`, `refs` and `logs` symlinks are
resolved too. Relative environment paths are relative to the invocation's
working directory; a relative `commondir` pointer is relative to `GIT_DIR`.
Alternate environment paths support Git's C-quoted path-list syntax.

Every storage caller (`snapshot-intent`, `manifest --out`, `store-verdict`)
accepts repeatable `--exclude-git-root <existing-dir>` for additional caller-known
Git storage. It is passed through every preflight and publication check. A root
that contains or is contained by a declared boundary is rejected, including
canonical aliases. Missing, malformed or denied required bindings/exclusions
fail before any write; the helper never initializes a replacement directory.
A not-yet-created `GIT_INDEX_FILE` requires an existing resolvable parent, which
is excluded as a directory. Fixed Git path bindings are environment inputs, not
AO configuration resolution, and require no Git executable.

An unmarked directory referenced by an unrelated repository cannot prove the
absence of Git storage through ancestry alone. There is no universal reverse
lookup of repository configuration or alternates files: callers must supply
known external storage roots not represented by the active bindings. Missing
knowledge remains a caller boundary, not a claim that all possible external Git
references were discovered. The guard does not establish runtime authorization.

Destination descendants cannot be symlinks. The guard is a filesystem check;
native access controls still own confidentiality and hostile concurrent writers.

For CDLC knowledge/disclosure review, the caller resolves the protected external
`context.evidence_root` and passes it explicitly. These generic helpers do not
read configuration; T11 owns routing through T05. Drafts, manifests, receipts
and diagnostics also belong in that protected destination by caller policy.
Standalone product-proof placement remains explicitly caller-selected.

`verify-subject` compares current subject identity and the supplied verdict to
an independently supplied immutable `--intent`. Use distinct expected acceptance
for factual-support and destination-disclosure review; require every selected
leg to bind both identities. Pin any required profile version and policy in
those immutable bytes. No format-specific `--profile` validator is advertised;
structural validity, semantic factual support, destination permission and later
usefulness remain separate questions. The candidate cannot choose its own
expected policy. Evidence references remain declared strings, not verified
citations. Read permission does not authorize model transmission or Git ingestion.

## Developer-only reference checks

`tests/validate.py` retains the independent Python reference mechanics;
`tests/test_validate.py` and `tests/check_contract_corpus.py` keep their schema
and cross-language coverage. Run `bash skills/validate/tests/validate.sh` and
`bash scripts/check-verdict-contract-corpus.sh` in the development environment.
The installed `scripts/validate.sh` only checks the skill's contract text.
`tests/test_evidence_cli.py`, with an explicit source-built `AO_BIN`, exercises
candidate evidence operations with an empty runtime PATH. RPI/swarm Python
modules remain developer references; native skill execution does not invoke them.

## Proportionate fresh checks

Apply the owning skill's fresh same-family default. Risk sizes evidence depth;
only caller selection requires a different model family. Preserve an explicitly
requested leg until the caller changes it. Every mode retains exact subject,
full acceptance, evidence for every criterion, and the empty-`not_checked` bar.

Reuse existing digest-bound check receipts when their subject, inputs, tool
identity, and claimed criterion still match. Rerun the fast discriminating
check for a changed or uncertain criterion; rerun broader checks when the change
invalidates their receipts or acceptance explicitly requires them. A new receipt
label, changed digest, reduced finding count, or repeated review is not useful
progress without evidence that a named acceptance gap closed. Reuse the current
findings/evidence fields for causal comparisons; create no progress ledger.

## Cross-family adapters

Use the single [agent-native model-dispatch recipe](../../agent-native/references/model-dispatch.md)
for caller selection, host authorization and bounded invocation. The fresh
same-family leg and any explicitly selected cross-family leg receive independent
initial inputs. Time bounds come from the caller or native deadline, with no
fixed ten-minute cap. A judge reads and judges; it never mutates the subject. Record
actual author/judge model and context identities in protected evidence refs
and freshness attestation notes; the `verdict.v2` schema is unchanged.
Transport, output, exit and process completion are facts, not semantic PASS.

## Where each scope limit lives inside a PASS

| Scope limit | Home | Example |
|---|---|---|
| A criterion proven by a bounded check | `criteria[].reason` on that criterion | "proven by the unit suite; the full integration matrix was not replayed" |
| A declared non-goal or out-of-scope area | the intent source's non-goals, optionally restated as an evidence-backed boundary criterion in `criteria` | "`cli/**` is a declared non-goal; the diff proves it untouched" |
| Residual risk or judgment caveat | the caller-facing report | "the migration path is untested against pre-3.0 stores" |
| Acceptance that genuinely went unverified | `not_checked`, and the result is `NOT_PROVEN` rather than PASS | "criterion 3 needs hardware this context cannot reach" |
