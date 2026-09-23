# Actor-Subject Vocabulary — Engine Compatibility

Runtime contract for `plan`, `document`, and `review` when the actor-subject
types `scenario` and `journey` are in play. Load this file before the first
document search or write that could name either type. The research vocabulary
keeps its own gate in `skills/_shared/research-compatibility.md`; the two files
are independent, and a request that engages both runs both probes.

## Version probe

1. Run the probe once per invocation, before the first MCP call that would name
   `scenario` or `journey`, when any of these holds: the request or a named type
   names `scenario` or `journey`; the route engages the illustrate instrument
   (`skills/_shared/delta-routing.md`); a grounding result is a `scenario` or
   `journey` document. Otherwise, skip the probe and keep the legacy vocabulary;
   topic search without a type filter still returns documents of both types.
2. If the executor has a shell tool, run the helper below and resolve the
   executing skill's directory in the same shell call. Do not compare versions
   in prose.
3. If the executor has no shell tool and the calling skill supplied a probe
   result, use that result.
4. If the executor has no shell tool and no result is available, return
   `needs-vocabulary-probe` to the caller. The caller runs the helper and
   resumes the task with its result.
5. Before delegating scenario or journey work, the calling skill supplies the
   current invocation's probe result and the absolute plugin root. This handoff
   does not change the agent's tool permissions.
6. Do not infer version support, or an unsupported CLI, from missing handoff
   data or from a document's contents.

```sh
actor_subject_skill_dir="${CLAUDE_SKILL_DIR:-<absolute dir of the executing SKILL.md>}"
"$actor_subject_skill_dir/../../bin/cli-gte" 0.8.4
```

The minimum is CLI `0.8.4`, the published release that adds the actor-subject
vocabulary: <https://github.com/archcore-ai/cli/releases/tag/v0.8.4>.

| Result | Allowed vocabulary |
|---|---|
| `yes` | Add `scenario` and `journey` to type filters; allow both types, the `sdd.illustrate` gate, and a `scenario` named in the subject of `document code`. |
| `no` or `__NO_CLI__` | Keep legacy type filters; the illustrate instrument is dropped from the package; the two entries write nothing. |

## Fallback

1. If the probe does not return `yes` and the request's subject names `scenario` or
   `journey`, report the required version and exit without a document write.
2. If the probe does not return `yes` and the route engages the illustrate
   instrument, drop the instrument and report once:
   "Scenario and journey require Archcore CLI 0.8.4; skipping actor-subject documents."
3. If a scenario or journey artifact already exists, report the required
   version and exit without rewriting it; the fallback never converts an
   existing artifact to another type.
4. If the server rejects `scenario` or `journey` after a successful probe,
   report the mismatch and stop the affected operation. Do not retry with a
   different document type.

An unavailable MCP server follows the calling skill's existing recovery path.
The PATH probe identifies the binary a new server would run; a server started
before an upgrade keeps the old engine until restarted.

## Shared repositories

This vocabulary adds no relation value, so an older engine still reads a corpus
that holds `.scenario.md` and `.journey.md` files: it skips those files in the
scan and reports an invalid type in `status`. Before adding either type to a
shared repository, report that teammates on an older CLI will not see those
documents. The local probe cannot verify teammates' versions. No downgrade
conversion is provided.
