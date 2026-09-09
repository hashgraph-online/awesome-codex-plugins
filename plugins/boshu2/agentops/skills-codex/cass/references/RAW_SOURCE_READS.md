# Bounded raw source reads

CASS search, `view` and `expand` locate excerpts. `ao session read-source`
returns explicit raw bytes after checking caller-selected policy; it does not
parse records or replace the existing `ao provenance mine-session` tool-call
contract. Raw bytes include prose, operator corrections, malformed records and
Unicode line/paragraph separators. If a later consumer parses JSONL, split on
the byte `\n`, not Unicode line boundaries, and retain rejected records in raw
coverage accounting.

## Select access before opening bytes

The caller independently supplies the expected native source/project, owner,
task, model and destination. Existing T05 configuration and its native BD 1.2.2
maintenance anchor must resolve successfully. The access-policy reference is an
identity, not permission by its presence. Missing or mismatched context denies
the read; no source content is included in the error.

The resolved `task_policy_ref` selects a `source-read-policy.v1` JSON document.
It binds the same source/project/owner/task/model/destination to exact canonical
file permissions and a measured output profile. The caller, not the source
record or a knowledge candidate, owns this document. For example, replacing
these illustrative identities and paths with the independently authorized ones:

```json
{
  "schema_version": "source-read-policy.v1",
  "source_id": "/native/tracker/.beads",
  "project_id": "native-project-id",
  "owner_scope": "selected-owner",
  "task_ref": "selected-task",
  "model_ref": "selected-model",
  "destination_ref": "selected-destination",
  "files": [
    {"path": "/authorized/source.jsonl", "content_scope": "already-cleared"}
  ],
  "output_profile": {
    "id": "caller-selected-measured-profile",
    "model_ref": "selected-model",
    "destination_ref": "selected-destination",
    "max_serialized_bytes": 2048,
    "observation_ref": "/protected/host-output-observation.json",
    "observation_sha256": "replace-with-the-actual-64-character-lowercase-sha256"
  }
}
```

The example size is illustrative, not a default or a universal safe limit.
Select a limit measured on the actual native tool-result surface and preserve
its observation bytes/digest. The reader verifies the selected observation's
integrity; it does not attest its truth or observe host delivery. Policy and
observation documents have a separate 1 MiB parser resource bound. No source
locator, task, model, destination or profile has an inferred public default.

Allowed `content_scope` values are `synthetic`, `already-cleared` and `restricted`.
Current T05 reports `access_enforcement: not_attested`; restricted source reads
are therefore unavailable. The first two scopes support explicitly authorized
mechanism checks only. A policy label, file permission or worktree cannot supply
the native runtime/OS and egress enforcement owned by T39.

## Read and continue the same frozen prefix

```sh
ao session read-source \
  --file /authorized/source.jsonl \
  --access-policy-ref /protected/access-policy.json \
  --source-id /native/tracker/.beads --project-id native-project-id \
  --owner-scope selected-owner --task-ref selected-task \
  --model-ref selected-model --destination-ref selected-destination \
  --consumer-root /consumer/checkout --native-directory /native/workspace \
  --start-byte 0 --max-bytes 64 --json
```

The first invocation freezes the observed file size as `captured_through`.
Continue with `--start-byte` equal to `next_byte`, and pair
`--through-byte` with `--expect-prefix-sha256` from that result. The expected
hash covers **all bytes in `[0, captured_through)`**, not just the previous
span. Appends after that boundary are allowed. Any changed prefix, including
only an operator correction between identical tool calls, invalidates it.

Pass the previous `file_before.identity` as `--expect-file-identity` to check
replacement across invocations, even when a new file has identical contents.
Without that expectation, the response explicitly says cross-invocation
replacement was not checked. Within each invocation the reader compares the
opened file identity with the path before/after reading, rejects short reads,
and hashes the frozen prefix again to detect concurrent changes. These are
observations, not an atomic snapshot or a lock against a malicious concurrent
writer. Native files remain authoritative; no new source/state store is created.

## Interpret output honestly

`source-read.v1` is one compact JSON document, including a trailing newline.
`start_byte`, `end_byte` and `next_byte` identify the returned half-open span.
`prefix_sha256` hashes the entire frozen prefix; `span_sha256` hashes exactly
the returned bytes. `bytes_base64` is reversible and authoritative. `text_view`
is separately labelled with `text_view_encoding`; invalid or split UTF-8 uses
a replacement view and must never replace the raw bytes for integrity.

The reader checks the **actual serialized document length**, including metadata,
base64 expansion, text escapes and newline. Oversize output emits no source
bytes unless the caller explicitly sets `--allow-oversize`; that override is
recorded and never establishes complete reading. `profile_bound_satisfied`
reports the size comparison, not delivery. JSON is the measured output format;
YAML is rejected rather than silently bypassing its size contract.

Every result reports `host_delivery: host-delivery-unverified`,
`semantic_processing: not-established` and `complete_reading: false`.
`serialized_bytes` records emitted document size, not what a tool wrapper
actually delivered. Preserve the native transcript's actual result and any
truncation/omission markers. Even a successful producer and an observed final
sentinel cannot prove the omitted middle was delivered or processed. T09 owns
later identity-bound coverage/acknowledgement verification; a head-and-tail
read still leaves the middle unread.
