# Data Integration Patterns

Use this reference when wiring Sealos identity into an app's own business data.

## Core principle

Sealos provides runtime identity. Your app still owns its own database, business rules, and APIs.

For most apps:

1. Use `session.user.id` as the stable application user key.
2. Store display fields such as `name` and `avatar` as convenient denormalized data.
3. Keep business records in your own tables.

## Recommended user mapping

Persist a user record that mirrors the most useful Sealos fields:

1. `id`
2. `name`
3. `avatar`
4. `k8sUsername`
5. `nsid`

This makes later joins, ownership checks, and display logic simpler.

## Common schema patterns

### Pattern A: App users + records

Use when the app has reusable user profiles plus separate business entities.

Example:

1. `users`
2. `posts`
3. `votes`
4. `projects`
5. `records`

### Pattern B: Single-purpose table

Use when the app is simple and only needs one business table keyed by user.

Good for:

1. surveys
2. feature flags
3. profile preferences
4. user-scoped settings

## API pattern

Typical write flow:

1. Read `session.user` in the client.
2. Send the relevant identity fields plus the business payload to your API route.
3. Upsert the user row.
4. Insert or upsert the business row.

Typical read flow:

1. Query business data from the server.
2. Order and limit for the UI.
3. Return a display-ready response.

When creating starter code, prefer a business-neutral route shape over a demo-specific endpoint.

## Guardrails

1. Do not hardcode database connection strings.
2. Do not make the whole backend depend on raw Sealos session objects.
3. Keep Sealos fields narrow and intentional.
4. If authentication requirements become stricter, move validation into the server later without changing the core data model.
