# Sirv API - File Operations Reference

## Upload File

**POST** `/v2/files/upload?filename={path}`

Upload binary file data. Path must start with `/`.

```bash
curl -X POST "https://api.sirv.com/v2/files/upload?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: image/jpeg" \
  --data-binary @photo.jpg
```

**Parameters:**
- `filename` (required): Destination path, max 1024 chars, must start with `/`

**Content-Type:** Set to file's MIME type (image/jpeg, image/png, etc.)

---

## Download File

**GET** `/v2/files/download?filename={path}`

Returns binary file content.

```bash
curl "https://api.sirv.com/v2/files/download?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN" \
  -o photo.jpg
```

---

## Delete File

**POST** `/v2/files/delete?filename={path}`

Delete a single file or empty folder.

```bash
curl -X POST "https://api.sirv.com/v2/files/delete?filename=/images/old.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

For batch deletion, see [jobs.md](jobs.md).

---

## Copy File

**POST** `/v2/files/copy?from={source}&to={destination}`

```bash
curl -X POST "https://api.sirv.com/v2/files/copy?from=/images/a.jpg&to=/backup/a.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Rename/Move File

**POST** `/v2/files/rename?from={source}&to={destination}`

```bash
curl -X POST "https://api.sirv.com/v2/files/rename?from=/images/old.jpg&to=/images/new.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Create Folder

**POST** `/v2/files/mkdir?dirname={path}`

```bash
curl -X POST "https://api.sirv.com/v2/files/mkdir?dirname=/new-folder" \
  -H "Authorization: Bearer $TOKEN"
```

---

## List Directory

**GET** `/v2/files/readdir?dirname={path}`

Returns up to 100 items per page.

```bash
curl "https://api.sirv.com/v2/files/readdir?dirname=/images" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "contents": [
    {
      "filename": "/images/photo.jpg",
      "mtime": "2024-01-15T10:30:00Z",
      "contentType": "image/jpeg",
      "size": 245678,
      "isDirectory": false
    }
  ],
  "continuation": "token_for_next_page"
}
```

**Pagination:** If `continuation` is present, fetch next page:
```bash
curl "https://api.sirv.com/v2/files/readdir?dirname=/images&continuation=token_for_next_page" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Get File Info/Stats

**GET** `/v2/files/stat?filename={path}`

```bash
curl "https://api.sirv.com/v2/files/stat?filename=/images/photo.jpg" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "filename": "/images/photo.jpg",
  "size": 245678,
  "mtime": "2024-01-15T10:30:00Z",
  "ctime": "2024-01-10T08:00:00Z",
  "contentType": "image/jpeg",
  "isDirectory": false
}
```

---

## Fetch Remote File

**POST** `/v2/files/fetch`

Import file from external URL.

```bash
curl -X POST "https://api.sirv.com/v2/files/fetch" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.jpg",
    "filename": "/imported/image.jpg"
  }'
```

**Options:**
- `url`: Source URL
- `filename`: Destination path
- `auth`: Optional HTTP auth credentials
- `wait`: Wait for completion (boolean)

---

## Generate Signed URL

**POST** `/v2/files/jwt`

Create JWT-protected URL for secure file access.

```bash
curl -X POST "https://api.sirv.com/v2/files/jwt" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "/private/photo.jpg",
    "expiresIn": 3600
  }'
```

**Response:**
```json
{
  "url": "https://yourcdn.sirv.com/private/photo.jpg?jwt=eyJhbG..."
}
```

---

## TUS Upload (Large Files)

For large files, use tus.io resumable uploads.

**GET** `/v2/files/tus`

List available tus upload endpoints.

**POST** `/v2/files/tus`

Generate tus upload URL.

```bash
curl -X POST "https://api.sirv.com/v2/files/tus" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/large/video.mp4", "expiresIn": 86400}'
```
