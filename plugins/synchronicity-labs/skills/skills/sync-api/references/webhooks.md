# sync. webhooks

Pass `webhookUrl` (an `https://` URL that's publicly reachable) when creating a generation. When the generation reaches a final status, sync. sends a `POST` with the generation as JSON: `id`, `status`, `outputUrl`, `error`, `errorCode`, `model`, `input` and `options`.

## Verify every request

Each request carries `Sync-Signature: t=<unix seconds>,v1=<hex>`. `v1` is the HMAC-SHA256 of `"<t>.<raw body>"`, keyed with the organization's webhook secret (`whsec_…`, from https://sync.so/settings/webhooks or `GET /v2/organizations/webhook/secret`). Verify against the raw bytes before parsing JSON, compare in constant time, and reject old timestamps.

```typescript
// Next.js App Router: app/api/sync-webhook/route.ts
import { createHmac, timingSafeEqual } from "node:crypto";

const SECRET = process.env.SYNC_WEBHOOK_SECRET!;
const TOLERANCE_SECONDS = 300;

function verify(raw: string, header: string | null): boolean {
  const match = header?.match(/^t=(\d+),v1=([0-9a-f]+)$/);
  if (!match) return false;
  const [, t, received] = match;
  if (Math.abs(Date.now() / 1000 - Number(t)) > TOLERANCE_SECONDS) return false;
  const expected = createHmac("sha256", SECRET).update(`${t}.${raw}`).digest("hex");
  return received.length === expected.length && timingSafeEqual(Buffer.from(received), Buffer.from(expected));
}

export async function POST(req: Request) {
  const raw = await req.text();
  if (!verify(raw, req.headers.get("sync-signature"))) return new Response("invalid signature", { status: 400 });
  const event = JSON.parse(raw) as { id: string; status: string; outputUrl?: string; errorCode?: string };
  // Look the job up by event.id; ignore it if it's already final (deliveries can repeat).
  // Queue the slow work (downloading outputUrl, notifying the user) and answer right away.
  return new Response("ok");
}
```

```python
# Flask
import hashlib, hmac, os, re, time
from flask import Flask, request

app = Flask(__name__)
SECRET = os.environ["SYNC_WEBHOOK_SECRET"].encode()

def verify(raw: bytes, header) -> bool:
    match = re.fullmatch(r"t=(\d+),v1=([0-9a-f]+)", header or "")
    if not match or abs(time.time() - int(match[1])) > 300:
        return False
    expected = hmac.new(SECRET, match[1].encode() + b"." + raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(match[2], expected)

@app.post("/sync-webhook")
def sync_webhook():
    if not verify(request.get_data(), request.headers.get("Sync-Signature")):
        return "invalid signature", 400
    event = request.get_json()
    # Update the job for event["id"] if it isn't final yet; do slow work in a background job.
    return "ok", 200
```

## Make the handler robust

- **Answer `2xx` fast**, within a few seconds, and do downloads and notifications in a background job.
- **Expect duplicates.** Treat the generation `id` as the key: a job that's already final ignores the event. Every delivery attempt also carries a `Sync-Delivery-Id` header that stays the same across retries.
- **Don't rely on webhooks alone.** If your endpoint was down, a delivery can be missed. Run a periodic job that polls `GET /v2/generate/{id}` for jobs that have been pending too long.
- **Local testing:** expose your dev server with a tunnel such as ngrok, and pass that URL as `webhookUrl`.
