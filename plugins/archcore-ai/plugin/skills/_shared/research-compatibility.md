# Research Vocabulary — Engine Compatibility

Runtime contract for `plan`, `document`, and the research track. Load this file
before the first document search that could name `research` or `evidence`.

## Version probe

1. Run the probe once per invocation, before the first MCP call that would name `research` or `evidence`, when any of these holds: the request or a named type names `research` or `evidence`; the route engages the research instrument; a grounding result is a `research` or `evidence` document. Otherwise, skip the probe and keep the legacy vocabulary; topic search without a type filter still returns documents of the new types.
2. If the executor has a shell tool, run the helper below and resolve the executing skill's directory in the same shell call. Do not compare versions in prose.
3. If the executor has no shell tool and the calling skill supplied a probe result, use that result.
4. If the executor has no shell tool and no result is available, return `needs-vocabulary-probe` to the caller. The caller runs the helper and resumes the task with its result.
5. Before delegating research or evidence work, the calling skill supplies the current invocation's probe result and the absolute plugin root. This handoff does not change the agent's tool permissions.
6. Do not infer version support, or an unsupported CLI, from missing handoff data or from a document's contents.

```sh
research_skill_dir="${CLAUDE_SKILL_DIR:-<absolute dir of the executing SKILL.md>}"
"$research_skill_dir/../../bin/cli-gte" 0.8.3
```

The minimum is CLI `0.8.3`, the published release that adds the research
vocabulary: <https://github.com/archcore-ai/cli/releases/tag/v0.8.3>.

| Result | Allowed vocabulary |
|---|---|
| `yes` | Add `research` and `evidence` to type filters; allow both types and `supports`, `contradicts`, `supersedes`. |
| `no` or `__NO_CLI__` | Keep legacy type filters and only `related`, `implements`, `extends`, `depends_on`. |

## Fallback

1. If the probe does not return `yes`, route a new investigation through the legacy `rnd` path.
2. If an investigation takes the fallback, report once: "Research vocabulary requires Archcore CLI 0.8.3; using rnd and legacy relations."
3. Keep materials under Approach → Inputs of the fallback `rnd`.
4. If the explicit type is `evidence`, report the required version and exit without a document write.
5. If a new-type artifact already exists, report the required version and exit without rewriting or converting that artifact.
6. If the fallback lacks a supported recommendation, keep the `rnd` incomplete and report the unmet conclude check.

The fallback never invents a recommendation or substitutes `doc` for `evidence`.
An unavailable MCP server follows the calling skill's existing recovery path.
If the server rejects a new enum after a successful probe, report the mismatch
and stop the affected operation. Do not retry with a different document type.

## Shared repositories

Older engines reject manifests containing the new relation values. Before
adding these values to a shared repository, report that every CLI reading its
manifest needs the vocabulary release. The local probe cannot verify teammates'
versions. No downgrade conversion is provided.
