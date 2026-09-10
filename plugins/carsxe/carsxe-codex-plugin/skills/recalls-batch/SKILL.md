---
name: recalls-batch
description: Submit and retrieve bulk safety-recall checks for many VINs using the CarsXE Recalls Batch API. Use this when the user wants to check recalls for a fleet, inventory list, CSV of VINs, or more than a handful of vehicles at once.
license: MIT
version: 1.0.0
author: CarsXE
---

When the user wants bulk recall checks (many VINs, a fleet, a CSV, or a spreadsheet):

1. **Submit** — POST at least one of `vins`, `csv`, or `csvUrl` (max 10,000 unique VINs):
   ```
   POST https://api.carsxe.com/v1/recalls-batch/submit?key={CARSXE_API_KEY}&source=codex_plugin
   Content-Type: application/json
   {"vins":["..."],"csv":"...","csvUrl":"...","webhookUrl":"..."}
   ```
   Include only provided fields. `csvUrl` must be HTTPS and hosted on an allowed provider (Google Sheets, GCS, S3, Dropbox, Azure Blob, DigitalOcean Spaces, Box). Max file size: 5 MB.
   Return `batchId`, `status`, `totalVins`, `processedVins`, `hitCount`, and timestamps.
2. **Status** — poll until `completed`, `partial`, or `failed` (every 30–60 seconds; full processing often takes 30–60 minutes unless all VINs are cached):
   ```
   GET https://api.carsxe.com/v1/recalls-batch/status?key={CARSXE_API_KEY}&batchId={BATCH_ID}&source=codex_plugin
   ```
   Present status (`uploading` | `processing` | `completed` | `partial` | `failed`), progress (`processedVins` / `totalVins`), `hitCount`, `hitRate`, and `errorMessage` if failed.
3. **Results** (JSON) once complete:
   ```
   GET https://api.carsxe.com/v1/recalls-batch/results?key={CARSXE_API_KEY}&batchId={BATCH_ID}&source=codex_plugin
   ```
   Present job summary, then each VIN: `hasRecalls`, `recallCount`, and recall titles / NHTSA numbers / remedy status. HTTP 409 means the batch is still processing.
4. **Download** (CSV) if the user wants a file:
   ```
   GET https://api.carsxe.com/v1/recalls-batch/download?key={CARSXE_API_KEY}&batchId={BATCH_ID}&source=codex_plugin
   ```
   This returns `text/csv`, not JSON.
5. For a single VIN use `vehicle-recalls` (`/v1/recalls`). For year/make/model with no VIN use `recalls-ymm` (`/v1/recalls-ymm`).
6. If the API key is missing, tell the user to set the `CARSXE_API_KEY` environment variable (see AGENTS.md).
