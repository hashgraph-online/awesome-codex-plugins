# Swagger Extraction Output Format

Use this reference when the default Markdown from `scripts/extract_swagger_docs.mjs` needs manual refinement.

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

Auth is rendered from `securitySchemes` / `securityDefinitions`. If no auth requirement is documented for the endpoint, say so directly.

#### cURL

Use the documented method, URL, content type, auth headers, and an inferred sample body.

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
- If a response/request schema omits `type`, `properties`, and `$ref` but provides `example`, infer a readable field list from the example instead of rendering only `any`.
- Infer sample request bodies from schema defaults, examples, enums, and primitive types when rendering integration examples.
- Stop expanding recursive or very deep schemas and show the referenced name instead.
- Preserve enum values and default values when present.
- For arrays, show the item type.

## Manual Cleanup Rules

- Keep endpoint paths and HTTP methods exact.
- Translate user-facing headings when the user requests Chinese output.
- Avoid adding business meaning that is not present in `summary`, `description`, parameter descriptions, or schemas.
- If schema names are unclear, preserve the original schema/component name instead of guessing.
