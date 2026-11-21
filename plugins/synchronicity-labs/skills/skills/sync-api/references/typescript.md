# TypeScript integration

`npm i @sync.so/sdk`. Node 18+, server-side only.

```typescript
import { randomUUID } from "node:crypto";
import { readFile, stat, writeFile } from "node:fs/promises";
import { basename } from "node:path";
import { SyncClient, SyncError } from "@sync.so/sdk";

const API = "https://api.sync.so/v2";
const apiKey = process.env.SYNC_API_KEY;
if (!apiKey) throw new Error("Set SYNC_API_KEY");
const sync = new SyncClient({ apiKey });

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "x-api-key": apiKey!, "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

/** Upload a local file into sync. storage and return its asset ID. */
export async function upload(path: string, type: "VIDEO" | "AUDIO" | "IMAGE", contentType: string): Promise<string> {
  const { size } = await stat(path);
  const target = await api<{ uploadUrl: string; url: string }>("/assets/upload", {
    method: "POST",
    body: JSON.stringify({ fileName: basename(path), contentType, size }),
  });
  // The presigned upload URL must not receive the API key.
  const put = await fetch(target.uploadUrl, { method: "PUT", headers: { "Content-Type": contentType }, body: await readFile(path) });
  if (!put.ok) throw new Error(`upload failed: ${put.status}`);
  const asset = await api<{ id: string }>("/assets", { method: "POST", body: JSON.stringify({ url: target.url, type }) });
  return asset.id;
}

export async function estimateUsd(model: string, seconds: number): Promise<number> {
  const est = await api<{ estimatedGenerationCost: number }>("/generations/estimate", {
    method: "POST",
    body: JSON.stringify({ model, duration: seconds }),
  });
  return est.estimatedGenerationCost;
}

interface Job {
  videoAssetId: string;
  audioAssetId: string;
  idempotencyKey: string; // stored with the job before the first create
  webhookUrl?: string;
}

export async function startLipsync(job: Job): Promise<string> {
  for (;;) {
    try {
      const generation = await sync.generations.create(
        {
          model: "sync-3",
          input: [
            { type: "video", assetId: job.videoAssetId },
            { type: "audio", assetId: job.audioAssetId },
          ],
          options: { sync_mode: "bounce" },
          webhookUrl: job.webhookUrl,
        },
        { headers: { "Idempotency-Key": job.idempotencyKey } },
      );
      return generation.id;
    } catch (err) {
      if (!(err instanceof SyncError)) throw err;
      const body = (err.body ?? {}) as { retryAfterSeconds?: number; generationId?: string };
      if (err.statusCode === 429) {
        await new Promise((r) => setTimeout(r, (body.retryAfterSeconds ?? 20) * 1000));
        continue; // same key, so no duplicate generation
      }
      if (err.statusCode === 409 && body.generationId) return body.generationId;
      throw err;
    }
  }
}

/** Polling fallback. Prefer a webhook in production. */
export async function waitFor(generationId: string): Promise<string> {
  for (;;) {
    const gen = await api<{ status: string; outputUrl?: string; error?: string; errorCode?: string }>(
      `/generate/${generationId}?wait=true&timeout=10`,
    );
    if (gen.status === "COMPLETED") return gen.outputUrl!;
    if (gen.status === "FAILED" || gen.status === "REJECTED") throw new Error(`${gen.status}: ${gen.errorCode} ${gen.error}`);
    await new Promise((r) => setTimeout(r, 2000));
  }
}

const JOB_FILE = "lipsync-job.json"; // stands in for a row in your database

/** Save the asset IDs and the idempotency key before creating, so a restart can't pay twice. */
async function loadOrCreateJob(): Promise<Job & { generationId?: string }> {
  try {
    return JSON.parse(await readFile(JOB_FILE, "utf8"));
  } catch {
    const job: Job = {
      videoAssetId: await upload("talk.mp4", "VIDEO", "video/mp4"),
      audioAssetId: await upload("new-take.wav", "AUDIO", "audio/wav"),
      idempotencyKey: randomUUID(),
    };
    await writeFile(JOB_FILE, JSON.stringify(job));
    return job;
  }
}

async function main() {
  const job = await loadOrCreateJob();
  if (!job.generationId) {
    console.log("Estimated cost: $" + (await estimateUsd("sync-3", 12)).toFixed(2));
    job.generationId = await startLipsync(job);
    await writeFile(JOB_FILE, JSON.stringify(job));
  }
  // After a restart this polls the saved generation instead of creating another one.
  console.log("Output:", await waitFor(job.generationId));
}

if (import.meta.url === `file://${process.argv[1]}`) main();
```

## Variations

- **Script instead of audio:** `{ type: "text", provider: { name: "elevenlabs", voiceId: "<voiceId>", script: "Hello!" } }` in place of the audio input. List voices with `GET /v2/voices`.
- **Image input, `dubParams`, `projectId`:** if your installed SDK version doesn't type them yet, `POST` the same JSON body to `/generate` with the `api()` helper and an `Idempotency-Key` header.
- **Next.js:** call these from a Route Handler or server action and return the generation ID. The browser polls your route, or your webhook route updates the job.
