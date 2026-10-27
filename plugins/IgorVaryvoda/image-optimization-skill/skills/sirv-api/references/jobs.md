# Sirv API - Async Jobs Reference

Async jobs return a job ID. Poll the status endpoint until `progress` reaches 100.

## Spin to Video

Convert 360 spin to MP4 video.

**Start job:**
```bash
curl -X POST "https://api.sirv.com/v2/files/spin2video" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "/spins/product.spin",
    "options": {
      "width": 1920,
      "height": 1080,
      "loops": 1
    }
  }'
```

**Options:**
- `width`, `height`: Video dimensions
- `loops`: Number of rotation loops
- `fps`: Frames per second

**Response:** `{"filename": "/spins/product.mp4"}`

---

## Video to Spin

Convert video to 360 spin.

**Start job:**
```bash
curl -X POST "https://api.sirv.com/v2/files/video2spin" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "/videos/turntable.mp4",
    "options": {
      "framesPerRow": 36
    }
  }'
```

**Options:**
- `framesPerRow`: Frames to extract per row
- `rows`: Number of rows (for multi-row spins)

**Response:** `{"filename": "/videos/turntable.spin"}`

---

## Create ZIP Archive

Create ZIP from multiple files.

**Start job:**
```bash
curl -X POST "https://api.sirv.com/v2/files/zip" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filenames": [
      "/images/photo1.jpg",
      "/images/photo2.jpg",
      "/images/photo3.jpg"
    ],
    "zipFilename": "/downloads/photos.zip"
  }'
```

**Response:** `{"id": "job_id"}`

**Poll status:**
```bash
curl "https://api.sirv.com/v2/files/zip?id=job_id" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "progress": 100,
  "result": {
    "filename": "/downloads/photos.zip",
    "size": 1234567
  }
}
```

---

## Batch Delete

Delete multiple files in one operation.

**Start job:**
```bash
curl -X POST "https://api.sirv.com/v2/files/batch/delete" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filenames": [
      "/old/file1.jpg",
      "/old/file2.jpg",
      "/old/file3.jpg"
    ]
  }'
```

**Response:** `{"id": "job_id"}`

**Poll status:**
```bash
curl "https://api.sirv.com/v2/files/batch/delete?id=job_id" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "progress": 100,
  "result": {
    "deleted": 3,
    "failed": 0
  }
}
```

---

## 3D Model to GLB

Convert 3D models (OBJ, USD, USDZ, FBX) to GLB format.

**Start job:**
```bash
curl -X POST "https://api.sirv.com/v2/files/3d/model2GLB" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/models/product.obj"}'
```

**Response:** `{"id": "job_id"}`

**Poll status:**
```bash
curl "https://api.sirv.com/v2/files/3d/model2GLB?id=job_id" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 360 Spin Exports for Retailers

Export spins in retailer-specific formats.

### Amazon
```bash
curl -X POST "https://api.sirv.com/v2/files/spin2amazon" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/spins/product.spin", "asin": "B01234ABCD"}'
```

### Walmart
```bash
curl -X POST "https://api.sirv.com/v2/files/spin2walmart" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/spins/product.spin", "gtin": "012345678901"}'
```

### Home Depot
```bash
curl -X POST "https://api.sirv.com/v2/files/spin2homedepot" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/spins/product.spin", "omsid": "123456789"}'
```

### Lowe's
```bash
curl -X POST "https://api.sirv.com/v2/files/spin2lowes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "/spins/product.spin", "barcode": "012345678901"}'
```

---

## Polling Pattern

```javascript
async function waitForJob(endpoint, jobId, token) {
  while (true) {
    const response = await fetch(`https://api.sirv.com${endpoint}?id=${jobId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const data = await response.json();

    if (data.progress >= 100) {
      return data.result;
    }

    // Wait 1 second before next poll
    await new Promise(r => setTimeout(r, 1000));
  }
}

// Usage
const { id } = await startZipJob(filenames);
const result = await waitForJob('/v2/files/zip', id, token);
console.log('Output:', result.filename);
```
