# Native judgment receipt references

A consumer can check caller-selected judge profiles with
`ao provenance verify-judgments`. This is a mechanical reader over the existing
`verdict.v2` contract; Validate remains the semantic author. It neither launches
judges nor chooses a strategy, provider, retry, budget or delivery transition.

Before dispatch or source retrieval, the caller resolves task, source owner,
model/provider and destination authorization. Required diversity cannot grant
access to a denied provider. The native runtime must enforce that policy before
transmission; a local verifier cannot retract an unauthorized dispatch. Pass the
independently authorized providers separately from the required profile file.
The generic reader does not resolve configuration; callers supply its inputs.

## Independent inputs

Freeze the expected subject manifest, immutable acceptance file, author context,
required profiles and authorized provider list outside the candidate's control.
Every required leg must concern that exact subject **and** acceptance. Two valid
PASS verdicts over the same bytes for different purposes are not interchangeable.
For example, factual support cannot stand in for permission to disclose a page.

The required profile file is a strict JSON object:

```json
{"profiles":[{"id":"other-family","runtime":"claude","model":"claude-example","family":"anthropic","effort":""}]}
```

Use an exact model ID, not an alias that can silently resolve to another model.
Supported runtime/family pairs are `codex`/`openai` and `claude`/`anthropic`.
Profile IDs must be distinct. An empty effort imposes no actual-effort requirement.
A nonempty effort requires that exact effort in runtime reporting; a requested
option alone does not prove actual effort. Missing native reporting remains an
honest limitation, even when the model and context can be verified.

## Receipt in existing evidence_refs

The caller/runtime records one immutable receipt in protected non-Git evidence
storage. A verdict cites it through an ordinary top-level `evidence_refs` string:

```text
judgment-receipt:/absolute/private/evidence/receipt.json#sha256=<SHA256-of-exact-receipt-bytes>
```

No model, provider, effort or receipt fields are added to `verdict.v2`. Its own
content-addressed artifact remains unchanged, including FAIL, NOT_PROVEN,
findings, omissions and freshness attestation. There is no receipt-to-verdict
backreference or digest cycle: the verdict binds the receipt's bytes.

The receipt's strict version-1 shape is:

```json
{
  "version": "1",
  "requested": {"id":"other-family","runtime":"claude","model":"claude-example","family":"anthropic","effort":""},
  "subject_manifest_digest": "<expected-subject-manifest-digest>",
  "acceptance_digest": "<SHA256-of-exact-expected-acceptance-bytes>",
  "author_context_id": "<observed-author-context>",
  "transcript": {"path":"/absolute/private/evidence/native.jsonl","start":0,"end":1234,"sha256":"<SHA256-of-exact-selected-native-bytes>"},
  "exit_code": 0,
  "timed_out": false,
  "truncated": false,
  "cleanup_verified": true,
  "omissions": []
}
```

Capture the complete invocation span, including native identity and terminal
events. `start` and `end` are zero-based, end-exclusive byte offsets; both must
be native JSONL line boundaries (the file end may lack a trailing newline).
Hash the exact span, preserving CRLF, whitespace and final-newline presence.
Never select only a favorable response from a run that changed model/context or
terminated unsuccessfully. Record withheld/unread required input, incomplete
output and every other omission. Nonempty omissions cannot satisfy the leg.
Raw thinking content is not needed in reports; metadata span references suffice.

The verifier reopens the transcript and parses native envelope fields. It never
trusts a receipt-authored actual-model string, requested profile echo or JSON
inside assistant/tool text. Claude `assistant.message.model` plus native
`session_id`/`sessionId` supplies the reported identity; `system.init.model`
is a requested configuration echo. Codex `session_meta.payload.model`,
`model_provider`, `id` and optional `reasoning_effort` supply metadata when
present. `turn_context` configuration and model self-description do not establish
actual identity. Codex versions without native model reporting remain
`identity_unverified`; do not guess their model from a command or filename.

Successful native termination requires Claude `result` with `subtype: success`
and `is_error: false`, or Codex `event_msg` with `payload.type: task_complete`.
A saved content-only transcript without a terminal event cannot establish
completion. Exit zero alone, a timed-out partial result or a clean process tree
cannot replace the native terminal event. Native fields attest available runtime
reporting; they do not cryptographically prove provider weights, an untampered
recorder, complete source coverage or context isolation. Caller/runtime freshness
attestation remains necessary alongside observed distinct context identities.

## Verify required coverage

```sh
ao provenance verify-judgments \
  --root "$SUBJECT_ROOT" --manifest "$MANIFEST" --intent "$EXPECTED_INTENT" \
  --author-context-id "$AUTHOR_CONTEXT" --evidence-root "$EVIDENCE_ROOT" \
  --required-profiles "$REQUIRED_PROFILES" --allowed-provider anthropic \
  --verdict "$VERDICT"
```

Repeat `--verdict` for supplied legs and `--allowed-provider` for independently
authorized providers. The existing private non-Git evidence root confines
candidate-selected receipt, transcript and verdict reads. Files must be private
regular files; paths cannot escape the root through symlinks. Reads are bounded
to 16 MiB per file. Malformed/duplicate JSON, altered receipt or transcript bytes,
invalid spans and unsupported helper versions fail closed before being relied on.

The result lists each required leg, the unchanged supplied verdict, parsed native
facts and exact source spans, and any mismatches or missing coverage. Unknown
identity, wrong model/family/required effort, stale subject, wrong acceptance,
reused author/peer context, timeout, truncation or unverified cleanup leaves
`satisfied: false` with exit 1. An unavailable required leg remains missing;
never swap it for another family or remove it without caller authority.
Exit 0 and `satisfied: true` establish mechanical matching of the supplied PASS
legs, not a new semantic judgment or a majority vote. Preserve disagreement.
