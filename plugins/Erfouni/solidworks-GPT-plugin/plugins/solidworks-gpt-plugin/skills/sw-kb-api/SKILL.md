---
name: sw-kb-api
description: Query the SolidWorks knowledge-base catalog for categories, matching parts, complete published instructions, macros, known API errors, and lessons. Use after sw-pre-start and before any SolidWorks modeling or API work, for every part, assembly, drawing, repair, or model reproduction request.
---

# SolidWorks KB Lookup

Run `$sw-pre-start` first. Complete this lookup before CAD work.

Set `KB_HOST` from `SW_KB_HOST`; default to
`https://sw-plugin.ideep.org`. Use quoted `curl` shell calls only. Runtime
endpoints are public and use camelCase JSON.

## 1. Check health

```text
curl -sS "{KB_HOST}/health"
```

If unreachable, tell the user `Knowledge base is offline - proceeding without
KB lookup`, record the outage for session feedback, and continue from verified
engineering knowledge. Do not abort the CAD task.

## 2. Match a category

```text
curl -sS "{KB_HOST}/api/categories"
```

Fuzzy-match the requested component against category `name` or `slug`. Save the
matching `id` as `categoryId`. If nothing matches, continue to the free-text
fallback in Step 4.

## 3. Match a part inside the category

```text
curl -sS "{KB_HOST}/api/parts?categoryId={categoryId}&pageSize=100"
```

Optionally add a URL-encoded `q` parameter. Match active items by exact or close
`partNumber`, then by `name`. Save the best `id` as `partId`.

## 4. Load complete part detail

When `partId` is known:

```text
curl -sS "{KB_HOST}/api/parts/{partId}"
```

Otherwise search globally:

```text
curl -sS "{KB_HOST}/api/parts?q={encoded-name-or-number}&pageSize=20"
```

Fetch the best match's detail. Read every published `instructions`, `macros`,
`knownErrors`, and `lessons` item rather than relying on list summaries.

## 5. Apply the result

For a part with instructions:

- follow published instructions as the primary build guide;
- use a complete `isTemplate: false` macro directly after replacing only
  declared `parameters` with user values;
- adapt an `isTemplate: true` macro to the current part;
- read all known errors before using any listed `swFeature` and apply resolved
  fixes proactively;
- treat every lesson `prevention` as an active constraint;
- tell the user which part was found and how many macros are being used.

For a catalog part without instructions, apply its errors and lessons, explain
that no published build guide exists, and build from verified knowledge.

When no part matches, explain that the part is not yet in the KB, load the
global safeguards below, and build from scratch. Do not promise that feedback
will be sent; submission still requires consent.

## 6. Load global safeguards

Always run both calls, even if no part matched:

```text
curl -sS "{KB_HOST}/api/errors"
curl -sS "{KB_HOST}/api/lessons"
```

Before every SolidWorks API call, cross-reference the method against global and
part-specific errors. When `isResolved` is true, apply `resolution` before the
call. Apply lesson `prevention` fields as rules, prioritizing critical and high
severity.

## Cache and failures

Cache categories and global errors or lessons once per Codex task. Cache each
part detail once per build. Refresh only when the user explicitly requests it
or the task changes to a different part.

- `200`: use the data.
- `404`: treat the resource as absent and continue.
- `422`: correct or simplify the query, then try the free-text fallback once.
- `5xx` or timeout: record the outage and continue without KB data.
