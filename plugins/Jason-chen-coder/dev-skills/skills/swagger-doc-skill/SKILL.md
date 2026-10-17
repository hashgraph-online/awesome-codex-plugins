---
name: swagger-doc-skill
description: >
  Query Swagger/OpenAPI sources for modules, endpoints, request/response fields,
  reusable schemas and DTOs, or export Markdown/JSON API documentation. Use with
  Swagger UI, Knife4j, FastAPI docs, Redoc, OpenAPI JSON/YAML, and Swagger 2.0
  URLs or local specifications, including endpoint integration lookups.
---

# Swagger Doc Skill

Read `references/dev-baseline.md` once per task. Use the bundled Node.js extractor
for consistent discovery, schema resolution, and exports. Resolve `<skill-dir>`
to the absolute directory containing this `SKILL.md`.

## Document Source

1. Use the docs URL, local specification, or config path provided in this request.
2. Reuse an unambiguous source already confirmed in this chat for follow-ups.
3. If several sources remain plausible, ask which one applies. If none is
   available, ask for a Swagger/OpenAPI URL, local spec, or config path.

Do not inherit Swagger sources across chats. Do not guess documentation URLs,
scan unrelated hosts, or invent endpoints. If the task is about an SDK without
an OpenAPI source, use its official documentation workflow instead.

The script only reads config files when `--config <path>` is passed explicitly.
Do not rely on shared defaults or persist chat URLs, tokens, or headers into the
skill's configuration. Keep credential-bearing project configs untracked.
Do not expose secret values in commands shown to the user, logs, or documents.
State the active source with the result, redacting URL credentials or tokens.

## Query Workflow

Choose the smallest output that answers the request:

| Intent | Script mode and filters |
|---|---|
| Modules/tags/controllers | `--mode modules` |
| Endpoint list | `--mode endpoints`; narrow with `--tag`, `--method`, `--path`, `--search` |
| One endpoint's request/response | `--mode endpoint --path <path> --method <METHOD>` |
| Feature integration | Find candidates with `endpoints`, then use `integration` with the matched method/path |
| Reusable types/models/DTOs | `--mode types`; narrow with `--type` or `--search` |
| Full export | `--mode document --output <file.md>`; add `--format json` for JSON |

```bash
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<docs-url-or-local-spec>" --mode modules
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode endpoints --search "登录"
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode integration --path "/api/user/login" --method POST
node "<skill-dir>/scripts/extract_swagger_docs.mjs" --config ./swagger.config.json --mode document --output swagger-api.md
```

For a UI page, let the extractor discover its backing specification. Review the
requested result against the extracted methods, paths, and schemas. Output size
should follow the request: a single field question does not need a full export.

For feature lookup, `--search` includes common Chinese/English intent synonyms.
Use endpoint descriptions and the user's context to narrow candidates. Ask only
when materially different candidates remain plausible; multiple text matches
alone do not require a question. If no match exists, try a few relevant adjacent
terms, then report the gap. Integration guidance requires an endpoint actually
present in the confirmed spec.

## Output And Verification

Preserve exact HTTP methods, paths, schema names, required fields, enum/default
values, content types, response statuses, base URLs, and documented auth.
Resolve local `$ref` and legacy `originalRef` where possible. Full exports include
reusable `components.schemas` / Swagger 2 `definitions`, not just endpoint
summaries. Mark unresolved references and recursive expansion limits.

Generated request examples and fields inferred from examples are illustrations,
not additional contract guarantees. Missing auth documentation does not prove
that the deployed endpoint is public. Do not execute generated API calls merely
to verify documentation.

For full exports, check source/module/endpoint/type counts, required sections,
and unresolved schemas. For focused queries, verify the selected endpoint or
type and its relevant fields. A successful extraction proves what the source
documents, not production behavior or server reachability.

Read [references/output-format.md](references/output-format.md) for full export
sections, schema formatting, and integration-example requirements. Read
[references/extractor-usage.md](references/extractor-usage.md) for config, cache,
headers, detailed command options, and discovery failures.

## Runtime And Failures

JSON specs and Swagger UI extraction use Node.js built-ins. Direct YAML input
requires the optional `yaml` package; if unavailable, use an available JSON
export or report the dependency and request the missing source as needed.

If a reachable docs page cannot be resolved, inspect its configuration/network
for a direct spec and retry that evidenced URL. If the input URL itself times
out or fails to fetch, report the failure instead of probing many fallback paths.
For authentication failures, use existing authorized access or request an export
or suitable credential mechanism. Keep partial results and unresolved items
explicit; never fill missing schemas or endpoint meaning from memory.

## SDD Evidence Contract

Use the active source, exact method/path, request shape, and response schema as
evidence for an existing spec or plan. Cite the endpoint and source in a handoff.
Report conflicts with a plan, generated client, or local DTO explicitly.
Documentation lookup alone does not authorize editing SDD artifacts or clients;
make those changes when they are part of the user's requested implementation.

## Multi-Agent Profile

Recommended agent_type: explorer

Delegate only when available and useful for a bounded, independent extraction.
Provide the confirmed source and requested endpoint/type or export scope.
The worker inherits source isolation and secret handling above and returns the
active source, requested result/file, verification command, and relevant counts
or unresolved schemas. It does not infer endpoints or expand into API writes.

When running from this repository, use `../../docs/multi-agent-policy.md` as
the extended policy. Standalone installs rely on this profile and do not require
that repository file.
