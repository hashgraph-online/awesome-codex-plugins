---
name: sirv-api
description: Sirv REST API integration for image and file management. Use when working with Sirv CDN, uploading/downloading files to Sirv, managing image metadata, searching files, creating 360 spins, converting videos, or any Sirv API operations. Covers authentication, file operations, metadata, search queries, async jobs, and account management.
---

# Sirv REST API

Base URL: `https://api.sirv.com`

## Official Sources First

Check current Sirv docs before changing endpoint fields, path escaping, metadata field names, or pagination behavior:

- `https://apidocs.sirv.com/`
- `https://sirv.com/help/articles/search-files-with-the-api/`
- `https://sirv.com/help/articles/add-meta-with-the-api/`
- `https://sirv.com/help/articles/sirv-api/`

## Authentication

All requests require a Bearer token from `/v2/token`:

```bash
curl -X POST https://api.sirv.com/v2/token \
  -H "Content-Type: application/json" \
  -d '{"clientId": "YOUR_CLIENT_ID", "clientSecret": "YOUR_CLIENT_SECRET"}'
```

Response:
```json
{"token": "eyJhbG...", "expiresIn": 1200, "scope": ["account:read", ...]}
```

Use token in subsequent requests:
```bash
curl https://api.sirv.com/v2/account \
  -H "Authorization: Bearer eyJhbG..."
```

Tokens expire in 20 minutes. Request a new one before expiry.

## Debugging Workflow

1. Identify the exact endpoint and method in play.
2. Reproduce or inspect the request body, query string, and response body.
3. Compare the request shape against the official docs before patching code.
4. Separate auth/token failures from Sirv payload/query failures.
5. Preserve upstream status and useful Sirv error detail when surfacing failures.
6. Add a focused regression test or fixture for the exact endpoint/query that failed.

## Operational Rules

- URL-encode file and folder paths in query strings, especially `/` as `%2F`.
- Refresh tokens in long-running scripts; do not assume a token survives a bulk migration.
- Check `/v2/account/limits` before bulk search/upload/delete jobs.
- Use `/v2/files/fetch` to import remote originals directly into Sirv when source URLs are stable.
- Preserve catalog context with metadata after upload: title, description, tags, product fields, and approval state.
- Search returns up to 100 results per page. Use `from` for normal pagination and scrolling search for more than 1000 results.
- Scrolling search is a point-in-time snapshot and is cached for about 20 minutes; download results promptly.
- Escape search special characters in paths: `{ } / \ ! space`.

## Quick Reference

### File Operations

| Operation | Method | Endpoint | Key Params |
|-----------|--------|----------|------------|
| Upload | POST | `/v2/files/upload` | `?filename=/path/file.jpg` + binary body |
| Download | GET | `/v2/files/download` | `?filename=/path/file.jpg` |
| Delete | POST | `/v2/files/delete` | `?filename=/path/file.jpg` |
| Copy | POST | `/v2/files/copy` | `?from=/a.jpg&to=/b.jpg` |
| Rename/Move | POST | `/v2/files/rename` | `?from=/a.jpg&to=/b.jpg` |
| Create folder | POST | `/v2/files/mkdir` | `?dirname=/new-folder` |
| List directory | GET | `/v2/files/readdir` | `?dirname=/folder` |

### Metadata Operations

| Operation | Method | Endpoint |
|-----------|--------|----------|
| Get all meta | GET | `/v2/files/meta?filename=/path` |
| Set meta | POST | `/v2/files/meta?filename=/path` |
| Get/Set title | GET/POST | `/v2/files/meta/title?filename=/path` |
| Get/Set description | GET/POST | `/v2/files/meta/description?filename=/path` |
| Get/Add/Delete tags | GET/POST/DELETE | `/v2/files/meta/tags?filename=/path` |
| Get/Set product | GET/POST | `/v2/files/meta/product?filename=/path` |

### Async Jobs (return job ID, poll for progress)

| Operation | Start | Poll |
|-----------|-------|------|
| Spin to video | POST `/v2/files/spin2video` | Returns filename directly |
| Video to spin | POST `/v2/files/video2spin` | Returns filename directly |
| Create ZIP | POST `/v2/files/zip` | GET `/v2/files/zip?id=` |
| Batch delete | POST `/v2/files/batch/delete` | GET `/v2/files/batch/delete?id=` |
| 3D to GLB | POST `/v2/files/3d/model2GLB` | GET `/v2/files/3d/model2GLB?id=` |

## When to Read Reference Files

- **File operations** (upload, download, copy, delete, directory listing): See [files.md](references/files.md)
- **Metadata & search** (meta fields, search query syntax, product data): See [metadata.md](references/metadata.md)
- **Async jobs** (video conversion, ZIP, batch ops): See [jobs.md](references/jobs.md)
- **Account & stats** (usage, billing, events, settings): See [account.md](references/account.md)

## Common Patterns

### Upload an image
```javascript
const token = await getToken();
await fetch('https://api.sirv.com/v2/files/upload?filename=/images/photo.jpg', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'image/jpeg'
  },
  body: imageBuffer
});
```

### Search for recent images
```javascript
await fetch('https://api.sirv.com/v2/files/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'extension:.jpg AND mtime:[now-7d TO now]',
    size: 50
  })
});
```

### Search a folder with escaped path
```javascript
await fetch('https://api.sirv.com/v2/files/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'dirname.paths:\\/products AND extension:.jpg',
    size: 100
  })
});
```

### Create ZIP archive (async)
```javascript
// Start job
const { id } = await fetch('https://api.sirv.com/v2/files/zip', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
  body: JSON.stringify({
    filenames: ['/images/photo1.jpg', '/images/photo2.jpg'],
    zipFilename: '/downloads/photos.zip'
  })
}).then(r => r.json());

// Poll until complete
let progress = 0;
while (progress < 100) {
  const status = await fetch(`https://api.sirv.com/v2/files/zip?id=${id}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  progress = status.progress;
  await new Promise(r => setTimeout(r, 1000));
}
```

## Red Flags

- Changing Sirv request syntax from memory instead of current docs.
- Flattening Sirv 400/401/403/429/5xx responses into a generic local error.
- Treating search field names, path escaping, or page-size limits as generic Lucene behavior.
- Fixing token acquisition and request body shape in the same step without proving which boundary failed.
- Hiding the exact Sirv path, folder, tag, or payload involved in a failure.

## Verification

- Reproduce the failing request with the exact folder, tag, file path, or payload.
- Confirm file paths are URL-encoded in query strings and escaped in search syntax where required.
- Confirm page size, pagination, or scrolling matches Sirv's documented behavior.
- Verify imported/uploaded files with `stat`, `meta`, `readdir`, or `search`.
- Re-run the relevant integration/route test when this skill is used in a codebase.
