---
name: graymatter-analytics
description: Use when GrayMatter should support analytics work by retrieving durable context, checking retrieval receipts, loading the live api-docs schema, and helping create user/workspace-specific semantic layers without assuming tenant business objects exist.
---

# GrayMatter Analytics

Use this skill when a user wants analytics, KPI, report, dashboard, or semantic-context work to use GrayMatter as the product surface for memory, retrieval, receipts, and live schema awareness.

## Core Rule

`/v1/api-docs` is the source of truth for the current RBAC-visible schema.

GrayMatter helpers may expect GrayMatter product surfaces such as memory, retrieval, receipts, status, and schema introspection when the plugin is installed and authenticated. They must not assume business objects such as `Invoice`, `UserPreference`, `StrategicPriority`, `KeyMetric`, `Customer`, `Workflow`, or `Application` exist until the current `/v1/api-docs` says they exist for this account.

## Start Here

1. Ensure GrayMatter is activated or at least check status with the available GrayMatter tool or script.
2. Retrieve relevant durable context through GrayMatter memory or retrieval receipts.
3. Load or refresh `/v1/api-docs` before using business objects, fields, relationships, or actions.
4. Map the user question to only the object families and paths present in the live schema.
5. If schema or retrieval evidence is missing, stale, partial, or conflicting, say so and ask for the smallest useful fallback.

## Source Order

1. Live `/v1/api-docs` for schema, paths, components, fields, relationships, and actions.
2. GrayMatter retrieval receipt for memory-backed answers, including its answer policy and coverage status.
3. Live GrayMatter memory read/query when receipts are unavailable.
4. User-provided sources such as SQL, dashboards, docs, exports, screenshots, repository files, or local semantic layers.
5. Local fallback files only when GrayMatter is unavailable or the user explicitly wants local-only work.

## Business Object Rules

- Treat object families outside the GrayMatter core as conditional.
- Verify both the path/component and the specific field or relationship before using it in analysis.
- When an expected object family is missing, use the closest live schema object only if it is semantically appropriate and say why.
- Do not synthesize unavailable schema objects from examples, docs, memories, or another user's tenant.
- For high-stakes analytics, refresh schema and retrieve source evidence during the workflow, even when saved context exists.

## Normalized Context Rules

Analytics quality depends on graph traversal, filters, and retrieval receipts seeing structured fields rather than blobs.

- Do not write analytics context by stuffing metadata into `MemoryEntry.text` or `ContentData.contentData`.
- Use `MemoryEntry.text` only for the concise durable fact, decision, todo, preference, handoff, or artifact summary.
- Use `sourceChannel`, `metadata`, tags, and explicit relationships for scope, provenance, workspace, workflow, dashboard, artifact, and agent identifiers.
- Use `ContentData` only for content artifacts or overflow detail; set or preserve `contentType`, `category`, `status`, `tags`, and JSON `metadata`.
- Never send audit fields such as `ownerId`, `ownerID`, `createdDate`, `lastModifiedDate`, or `lastAccessedDate` in create/update payloads.
- Before creating or updating a non-memory object, confirm the object and fields exist in `/v1/api-docs`; prefer the first-class business object over a generic memory or content record.
- When answering from memory or semantic retrieval, prefer retrieval receipts and respect their coverage, freshness, confidence, provenance, and answer policy.

## Semantic Layers

GrayMatter can help create workspace-specific semantic layers, but shared plugin skills must stay generic.

Use `references/semantic-layer-template.md` when a user wants reusable analytics context. The layer should be generated from that user's live schema and supplied sources, then stored in the user's workspace or skill directory. Do not ship customer-specific metrics, private MemoryEntry content, local absolute paths, or workspace decisions as a universal GrayMatter layer.

## Answering Rules

- Obey retrieval receipt policies such as retry, clarify, deny, low confidence, stale context, partial coverage, or conflicting context.
- Keep raw credentials, tokens, private personal fields, row-level customer data, and long private memory bodies out of generated artifacts.
- Separate product capability from tenant availability: GrayMatter may support schema-aware analytics, but the current tenant's `/v1/api-docs` decides what can be analyzed.
- Prefer precise source gaps over confident guesses.
