# Swagger Extraction Output Format

Use this reference for complete exports or when the default extractor output
needs refinement. Focused questions need only the relevant endpoint/type details.

## Export Contract

A full Markdown export includes title, version, active source, counts, documented
base URLs and security schemes, module list, endpoint index, per-endpoint details,
and reusable type definitions. Each endpoint preserves method, path, summary,
operation ID, parameter locations, body content types, and all documented response
statuses/descriptions/schemas. Report default deprecated-endpoint exclusion and
any unresolved schemas. JSON output should retain the same relevant contract data.

## Markdown Shape

```markdown
# API Documentation Summary

- Source: ...
- Title: ...
- Version: ...
- Modules: ...
- Endpoints: ...
- Types: ...
- Base URLs: ...
- Security Schemes: ...

## Module List

| Module | Endpoints | Methods |
|---|---:|---|

## Endpoint Index

### Tag Name

| Method | Path | Summary |
|---|---|---|

## Endpoint Details

### GET /example

- Tag: Example
- Summary: Example summary
- Operation ID: exampleOperation

#### Request

Path/query/header/cookie parameters are grouped by location. Request bodies list content type and schema.

#### Response

Each status code shows description, content type, and response schema.

## Integration Guide

### POST /example

- Request URL: `POST https://api.example.com/example`
- Summary: Example summary

#### Auth

Auth is rendered from `securitySchemes` / `securityDefinitions` and documented
operation/global security requirements. If none is documented, say so; this does
not establish that the deployed endpoint is public.

#### cURL

Use the documented method, URL, content type, placeholder auth headers, and an
explicitly illustrative sample body. An URL assembled from the first documented
server is an example target; it does not select the user's deployment environment.

#### fetch

Use the documented method, URL, headers, and an inferred sample body.

## Type Definitions

| Type | Kind | Description |
|---|---|---|

### ExampleDto

- Type: `object`
- object
  - `field`: string required
```

## Schema Formatting Rules

- Prefer readable field lists over raw JSON Schema dumps.
- Show `required` next to required object properties.
- Resolve local `$ref` values when possible.
- Resolve legacy `originalRef` schema references when present.
- In `document` and `types` mode, include reusable schemas/models/DTOs from `components.schemas` or Swagger 2 `definitions`.
- If a response/request schema omits `type`, `properties`, and `$ref` but provides
  `example`, render an inferred field list and label its example-only provenance;
  do not treat sample presence as requiredness or a complete field inventory.
- Infer sample request bodies from schema defaults, examples, enums, and primitive types when rendering integration examples.
- Stop expanding recursive or very deep schemas and show the referenced name instead.
- Preserve enum values and default values when present.
- For arrays, show the item type.
- Preserve documented composition, nullability, and constraints in manual
  explanations. If the rendered export loses a detail needed by the user,
  consult the raw spec and report the extractor limitation.

## Manual Cleanup Rules

- Keep endpoint paths and HTTP methods exact.
- Translate user-facing headings when the user requests Chinese output.
- Avoid adding business meaning that is not present in `summary`, `description`, parameter descriptions, or schemas.
- If schema names are unclear, preserve the original schema/component name instead of guessing.
