# Extractor Usage

Resolve `<skill-dir>` to the absolute directory containing `SKILL.md`. These
commands document the existing interface; use only the options the task needs.
Run `node "<skill-dir>/scripts/extract_swagger_docs.mjs" --help` for all flags.

## Configuration And Cache

For repeated queries, use an explicitly selected project config based on
`swagger.config.example.json`. Replace its placeholder URL and remove unused
placeholder auth headers. Do not create a config for a one-off URL query.

```bash
node "<skill-dir>/scripts/extract_swagger_docs.mjs" --config ./swagger.config.json --mode modules
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --cache swagger-spec-cache.json --mode modules
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --cache swagger-spec-cache.json --refresh-cache --mode modules
```

Supported config fields are `swaggerUrl` (or `url`), `headers`, `token`, and
`cachePath` (or `cache`). `token` is the complete Authorization header value,
including a scheme such as `Bearer` when required. Configured local paths resolve
relative to the config file. CLI URL/cache/header options override their config
counterparts; header names are case-insensitive.

Use a cache associated with the confirmed source. Identify cached results as a
snapshot; use `--refresh-cache` when current documentation matters. Do not infer
live server behavior from a cached specification.

## Filters And Output

```bash
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode endpoints --tag "用户管理"
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode endpoints --details --path "/v1/runs"
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode endpoint --path "/api/user/list" --method GET
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode types --type "CreateRun"
node "<skill-dir>/scripts/extract_swagger_docs.mjs" "<source>" --mode document --format json --output swagger-api.json
```

`endpoint` and `api` are aliases for endpoint details. Verify the returned
method/path when an exact match is needed. `--search` supports a small synonym
map, not arbitrary semantic search; inspect candidate descriptions.

Without `--output`, stdout is the requested Markdown/JSON. With `--output`, the
script writes the artifact and prints its path, mode, format, source count,
module count, endpoint count, and type count. Inspect the file before claiming
the export is complete. Deprecated endpoints are excluded by default; use
`--include-deprecated` when requested and disclose the default exclusion on a
full export. `--no-types` deliberately omits type definitions and is inappropriate
for a requested complete schema export.

## Authentication And Discovery

`--header "Name: value"` is repeatable. Avoid literal credentials in exposed
command history/output; use existing authorized configuration and redact secrets
when presenting a command or source. Documentation auth headers are not evidence
of the API's own authentication contract.

The extractor recognizes UI config, embedded `swaggerDoc`, common spec paths,
and `swagger-resources`. If a reachable UI cannot be resolved, inspect its HTML,
referenced scripts, or network requests for `url`, `urls`, `configUrl`, `spec-url`,
`openapi`, `swagger.json`, or `api-docs`. Retry a direct URL supported by that
evidence. Use `--verbose` only when discovery diagnostics help and redact secrets
from any reported attempted URLs.

If the provided URL fails to fetch or times out, report that failure instead of
starting unrelated discovery. If auth is unavailable, an exported local JSON/YAML
spec can supply read-only evidence. JSON uses Node built-ins; YAML needs the
optional `yaml` package. Report unsupported or unresolved schema features rather
than claiming the extractor recovered a complete contract.
