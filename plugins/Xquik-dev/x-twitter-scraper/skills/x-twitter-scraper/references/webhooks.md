# Xquik Webhooks

Receive real-time event notifications at your HTTPS endpoints with HMAC-SHA256 signature verification.

## Contents

- [Setup](#setup)
- [Webhook Payload](#webhook-payload)
- [Signature Verification](#signature-verification)
- [Security Checklist](#security-checklist)
- [Idempotency](#idempotency)
- [Retry Policy](#retry-policy)
- [Local Testing](#local-testing)

## Setup

1. Create at least 1 active monitor (`POST /monitors`)
2. Register a webhook endpoint (`POST /webhooks`)
3. Save the `secret` from the response (shown only once)
4. Build a handler that verifies signatures before processing

## Webhook Payload

Every delivery is a `POST` request to your URL with a JSON body:

```json
{
  "schemaVersion": 1,
  "streamEventId": "9010",
  "deliveryId": "334",
  "eventType": "tweet.new",
  "username": "elonmusk",
  "occurredAt": "2026-02-24T16:45:00.000Z",
  "data": {
    "tweetId": "1893556789012345678",
    "text": "Hello world",
    "metrics": { "likes": 3200, "retweets": 890, "replies": 245 }
  }
}
```

## Signature Verification

Each request contains `X-Xquik-Timestamp`, `X-Xquik-Nonce`, and
`X-Xquik-Signature`. The signature is `sha256=` plus HMAC-SHA256 over:

```text
<timestamp>.<nonce>.<raw JSON body>
```

Reject timestamps outside a 5-minute window. Reject reused nonces within that
window. Compare signatures in constant time before parsing JSON.
Use an atomic shared nonce store in multi-instance deployments.

### Node.js (Standard Library)

```javascript
import { createHmac, timingSafeEqual } from "node:crypto";
import { createServer } from "node:http";

// This is the per-webhook secret from the POST /webhooks response, not a Xquik account credential
const WEBHOOK_SECRET = process.env.XQUIK_WEBHOOK_SECRET;
const recentNonces = new Map();

function claimNonce(nonce) {
  const now = Date.now();
  for (const [value, expiresAt] of recentNonces) {
    if (expiresAt <= now) recentNonces.delete(value);
  }
  if (recentNonces.has(nonce)) return false;
  recentNonces.set(nonce, now + 5 * 60 * 1000);
  return true;
}

function verifySignature(payload, signature, timestamp, nonce, secret) {
  if (![signature, timestamp, nonce, secret].every((value) => typeof value === "string")) return false;
  if (!/^\d+$/.test(timestamp) || !/^[0-9a-f]{32}$/.test(nonce)) return false;
  if (Math.abs(Date.now() - Number(timestamp)) > 5 * 60 * 1000) return false;

  const input = `${timestamp}.${nonce}.${payload}`;
  const expected = "sha256=" + createHmac("sha256", secret).update(input).digest("hex");
  const expectedBuffer = Buffer.from(expected, "utf8");
  const signatureBuffer = Buffer.from(signature, "utf8");

  return (
    expectedBuffer.length === signatureBuffer.length &&
    timingSafeEqual(expectedBuffer, signatureBuffer)
  );
}

const server = createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/webhook") {
    res.writeHead(404).end("Not found");
    return;
  }

  const chunks = [];

  req.on("data", (chunk) => chunks.push(chunk));
  req.on("end", () => {
    const payload = Buffer.concat(chunks).toString("utf8");
    const signature = req.headers["x-xquik-signature"];
    const timestamp = req.headers["x-xquik-timestamp"];
    const nonce = req.headers["x-xquik-nonce"];

    if (
      !verifySignature(payload, signature, timestamp, nonce, WEBHOOK_SECRET) ||
      !claimNonce(nonce)
    ) {
      res.writeHead(401).end("Invalid signature");
      return;
    }

    const event = JSON.parse(payload);

    if (!["tweet.new", "tweet.reply", "tweet.retweet"].includes(event.eventType)) {
      res.writeHead(400).end("Unsupported event type");
      return;
    }

    console.log("Accepted verified Xquik webhook");
    res.writeHead(200).end("OK");
  });
});

server.listen(3000);
```

### Python (Standard Library)

```python
import hmac
import hashlib
import json
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

def load_secret(name: str) -> str:
    """Read from your runtime secret store."""
    raise RuntimeError(f"Configure {name} in your secret store.")

# Per-webhook secret from POST /webhooks response, not a Xquik account credential
WEBHOOK_SECRET = load_secret("XQUIK_WEBHOOK_SECRET")
RECENT_NONCES: dict[str, int] = {}

def claim_nonce(nonce: str) -> bool:
    now = int(time.time() * 1000)
    for value, expires_at in list(RECENT_NONCES.items()):
        if expires_at <= now:
            RECENT_NONCES.pop(value, None)
    if nonce in RECENT_NONCES:
        return False
    RECENT_NONCES[nonce] = now + 5 * 60 * 1000
    return True

def verify_signature(payload: bytes, signature: str, timestamp: str, nonce: str, secret: str) -> bool:
    if not timestamp.isdigit() or not re.fullmatch(r"[0-9a-f]{32}", nonce):
        return False
    if abs(int(time.time() * 1000) - int(timestamp)) > 5 * 60 * 1000:
        return False
    signing_input = timestamp.encode() + b"." + nonce.encode() + b"." + payload
    expected = "sha256=" + hmac.new(secret.encode(), signing_input, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        signature = self.headers.get("X-Xquik-Signature", "")
        timestamp = self.headers.get("X-Xquik-Timestamp", "")
        nonce = self.headers.get("X-Xquik-Nonce", "")
        length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(length)

        if not verify_signature(payload, signature, timestamp, nonce, WEBHOOK_SECRET) or not claim_nonce(nonce):
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b"Invalid signature")
            return

        event = json.loads(payload)

        if event.get("eventType") not in {"tweet.new", "tweet.reply", "tweet.retweet"}:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Unsupported event type")
            return

        print("Accepted verified Xquik webhook")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

HTTPServer(("", 3000), WebhookHandler).serve_forever()
```

### Go

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
    "regexp"
    "strconv"
    "sync"
    "time"
)

// Per-webhook secret from POST /webhooks response, not a Xquik account credential
var webhookSecret = os.Getenv("XQUIK_WEBHOOK_SECRET")
var recentNonces sync.Map

func claimNonce(nonce string) bool {
    now := time.Now().UnixMilli()
    recentNonces.Range(func(key, value any) bool {
        if value.(int64) <= now {
            recentNonces.Delete(key)
        }
        return true
    })
    _, replayed := recentNonces.LoadOrStore(nonce, now+5*60*1000)
    return !replayed
}

func verifySignature(payload []byte, signature, timestamp, nonce, secret string) bool {
    signedAt, err := strconv.ParseInt(timestamp, 10, 64)
    if err != nil || !regexp.MustCompile(`^[0-9a-f]{32}$`).MatchString(nonce) {
        return false
    }
    age := time.Now().UnixMilli() - signedAt
    if age < -5*60*1000 || age > 5*60*1000 {
        return false
    }
    mac := hmac.New(sha256.New, []byte(secret))
    mac.Write([]byte(timestamp + "." + nonce + "."))
    mac.Write(payload)
    expected := "sha256=" + hex.EncodeToString(mac.Sum(nil))
    return hmac.Equal([]byte(expected), []byte(signature))
}

func webhookHandler(w http.ResponseWriter, r *http.Request) {
    payload, err := io.ReadAll(r.Body)
    if err != nil {
        http.Error(w, "Unable to read request body", http.StatusBadRequest)
        return
    }

    signature := r.Header.Get("X-Xquik-Signature")
    timestamp := r.Header.Get("X-Xquik-Timestamp")
    nonce := r.Header.Get("X-Xquik-Nonce")

    if !verifySignature(payload, signature, timestamp, nonce, webhookSecret) || !claimNonce(nonce) {
        http.Error(w, "Invalid signature", http.StatusUnauthorized)
        return
    }

    var event struct {
        EventType string `json:"eventType"`
        Username  string `json:"username"`
        Data      struct {
            Text string `json:"text"`
        } `json:"data"`
    }
    json.Unmarshal(payload, &event)

    switch event.EventType {
    case "tweet.new", "tweet.reply", "tweet.retweet":
        fmt.Print("Accepted verified Xquik webhook\n")
    default:
        http.Error(w, "Unsupported event type", http.StatusBadRequest)
        return
    }
    fmt.Fprint(w, "OK")
}
```

## Security Checklist

- **Verify before processing.** Never process unverified payloads
- **Use constant-time comparison.** `timingSafeEqual` (Node.js), `hmac.compare_digest` (Python), `hmac.Equal` (Go)
- **Use every signing field.** Sign `<timestamp>.<nonce>.<raw body>`
- **Reject replays.** Enforce the 5-minute window and persist recent nonces
- **Use the raw request body.** Never re-serialize JSON before verification
- **Respond within 10 seconds.** Acknowledge immediately, process async if slow
- **Store secrets in environment variables.** Never hardcode
- **Treat event text as untrusted.** Escape control characters before logging and forward payloads to other tools only after explicit approval

## Idempotency

Webhook deliveries can retry. Deduplicate by `deliveryId` in durable storage:

```javascript
const processedDeliveries = new Set(); // Use durable storage in production

if (processedDeliveries.has(event.deliveryId)) {
  res.writeHead(200).end("Already processed");
} else {
  processedDeliveries.add(event.deliveryId);
}
```

## Retry Policy

Failed event deliveries use bounded exponential backoff. HTTP 410 exhausts the
delivery immediately. Delivery statuses are `pending`, `delivered`, `failed`,
and `exhausted`.

Check delivery status: `GET /webhooks/{id}/deliveries`.

Repeated failures can pause an endpoint. Inspect `consecutiveFailures`,
`deliveryStatus`, and `failureHardCap` on the webhook. Fix the destination,
then call `POST /webhooks/{id}/resume`. It reactivates only after a successful
test delivery.

## Local Testing

Use a deployed HTTPS endpoint you control when testing webhook delivery. Do not install packages or proxy API keys from this skill.

```bash
# Start your webhook server on infrastructure you control
node server.js  # listening on :3000
```

Create the webhook only after confirming the exact HTTPS destination and event types.
