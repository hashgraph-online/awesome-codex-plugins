---
name: presigned-uploads
description: Use when large files should be uploaded through presigned object-storage URLs before Kreuzberg Cloud starts extraction.
license: MIT
---

# Presigned uploads

Use presigned uploads for large documents or batches where sending file bytes in a normal API request would be inefficient.

Confirm with the user before uploading local files to remote storage.

## Flow

```text
1. Request upload slots for the intended files.
2. Upload each file directly to its temporary object-storage URL.
3. Confirm the batch so Kreuzberg Cloud starts extraction.
4. Track the returned job identifiers.
```

The temporary upload URLs expire. Upload promptly and do not log or store the URLs in shared artifacts.

## When to use it

- a single file is large
- a batch would create a large request body
- base64 encoding would waste time or memory
- direct object-storage transfer is more reliable than buffering locally

## When not to use it

For small files, the normal extraction submit workflow is simpler. For confidential files where remote processing is not allowed, use local extraction instead.
