---
name: blob-storage
description: Use when a val needs simple key/value persistence — JSON documents, cached responses, uploaded files, or binary assets. Covers the std/blob API, listing and deleting keys, account-global or val scoping, and storage limits.
triggers: [blob, storage, kv, key-value, persistence, cache, store, upload, file, json, asset, binary]
---

# Blob Storage

Val Town provides built-in key/value blob storage via the `std/blob` module. Reach for it whenever a val needs to persist simple values — JSON documents, cached API responses, uploaded files, or binary assets — keyed by a string. For relational or structured data you query with SQL, prefer `std/sqlite` instead.

## Scoping: account-global or per-val depending on import

There are two exports of the blob utility: `global.ts`, which is scoped to the user account, and `main.ts`, which is scoped to the val itself. Prefer the `main.ts` interface and val scoping for new vals.

Here is the scoped import:

```ts
/**
 * Importing from `main.ts` provides an interface to val-scoped blobs.
 */
import { blob } from "https://esm.town/v/std/blob/main.ts";
```

Here are the global imports:

```ts
/**
 * Importing from `global.ts` provides a blob interface that is scoped
 * to your account.
 */
import { blob } from "https://esm.town/v/std/blob/global.ts";
/**
 * This entrypoint is also available as `v/std/blob`. This is common
 * in older vals.
 */
import { blob } from "https://esm.town/v/std/blob";
```

The scoped & global `blob` interfaces have the same methods.

Scoped & global blobs are stored separately: you cannot access global blobs with the scoped interface or vice versa.

## Basic usage (JSON)

```ts
import { blob } from "https://esm.town/v/std/blob/main.ts";

await blob.setJSON("config", { theme: "dark", count: 0 });

const config = await blob.getJSON("config");
// config = { theme: "dark", count: 0 }, or undefined if the key doesn't exist
```

`getJSON` returns `undefined` when the key is missing, so guard before using the result:

```ts
const config = (await blob.getJSON("config")) ?? { theme: "light", count: 0 };
```

## Raw and binary data

Use `set`/`get` for strings, binary, or any `BodyInit`. `get` returns a standard `Response`, so use its body helpers (`.text()`, `.json()`, `.arrayBuffer()`, `.blob()`):

```ts
await blob.set("logo.png", imageBytes); // string | BodyInit (Blob, ArrayBuffer, ReadableStream, …)

const res = await blob.get("logo.png");
const bytes = await res.arrayBuffer();
```

Unlike `getJSON`, `get` **throws** `ValTownBlobNotFoundError` if the key doesn't exist — wrap it in `try/catch` when the key may be absent.

## Listing, deleting, copying

```ts
const entries = await blob.list("user_"); // optional key prefix filter
// entries = [{ key, size, lastModified }, …]

for (const { key } of entries) {
  await blob.delete(key);
}

await blob.copy("config", "config.bak"); // duplicate under a new key
await blob.move("draft", "published");   // rename / relocate
```

`list(prefix?)` returns an array of `{ key: string; size: number; lastModified: string }` — objects, not bare key strings.


## Limits

- **Key length:** up to 512 characters.
- **Total storage:** 10 MB on the free plan, 1 GB on Pro — shared across all blobs in the account.
- Store large or structured datasets in `std/sqlite` rather than as one giant blob.

## Reading/writing blobs via tools

When using the `storeBlob`, `readBlob`, `listBlobs`, or `deleteBlob` tools against a val owned by an organization (not your personal account), pass the org handle as the `org` parameter so the call hits that organization's blob storage. Example: `{ key: "myapp:config", org: "some-org" }`. This only matters for the tool calls — code inside the val reads and writes its owning account's storage automatically. Note `storeBlob` accepts UTF-8 text up to 100 KB; write larger or binary blobs from code with `blob.set`.

## Rules

- Treat keys as a flat namespace. Use prefixes (`feature:subkey`) for organization and to scope `list`.
- `getJSON` returns `undefined` for missing keys; `get` throws `ValTownBlobNotFoundError`. Handle the absent case accordingly.
- Don't store secrets in blobs — use environment variables for credentials.

## Reference

Full API docs: https://docs.val.town/std/blob/
