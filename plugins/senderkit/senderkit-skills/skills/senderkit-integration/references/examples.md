# REST examples

Illustrative, multi-language snippets for the two operations that anchor most
integrations: **send a templated message** and **read its status**. They use raw
HTTP so they stay valid regardless of SDK availability or package naming.

**Before copying these, confirm the live contract.** Fetch
`https://www.senderkit.com/openapi.yaml` and verify the base URL,
paths, headers, field names, and error shapes. These examples reflect the API at
authoring time; the spec is the source of truth.

## Conventions used below

- **Base URL:** `https://api.senderkit.com` (check `servers` in the OpenAPI).
- **Auth:** `Authorization: Bearer $SENDERKIT_API_KEY`. The `sk_live_` / `sk_test_`
  key prefix selects environment — use a `sk_test_` key for development and CI.
- **Idempotency is a header, not a body field:** set `Idempotency-Key` on every
  send that might be retried, with a deterministic value (e.g. `welcome:usr_123`).
- **Sends are asynchronous:** `POST /v1/send` returns `202` with
  `{ id, status, livemode }` where `status` is `"queued"` or `"scheduled"`. A
  returned id is not proof of delivery — poll `GET /v1/messages/{id}`.
- **Template vs raw:** send **either** `template` (+ `vars`) **or** `content`
  (inline raw), never both. Raw email uses `{ channel: "email", to, content: { subject, html, text } }`.
- Keep keys server-side. Never ship `SENDERKIT_API_KEY` to a browser or mobile client.

## curl

```bash
# Send a templated message
curl -sS -X POST https://api.senderkit.com/v1/send \
  -H "Authorization: Bearer $SENDERKIT_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: welcome:usr_123" \
  -d '{
    "template": "welcome",
    "to": "user@example.com",
    "vars": { "name": "Ada" },
    "metadata": { "userId": "usr_123" }
  }'
# -> 202 { "id": "msg_…", "status": "queued", "livemode": false }

# Read status later
curl -sS https://api.senderkit.com/v1/messages/msg_123 \
  -H "Authorization: Bearer $SENDERKIT_API_KEY"
```

## TypeScript / JavaScript

Official SDK (`npm i @senderkit/sdk`) — it attaches the idempotency key for you:

```ts
import { SenderKit } from "@senderkit/sdk";

const senderkit = new SenderKit({ apiKey: process.env.SENDERKIT_API_KEY! });

const { id, status } = await senderkit.send({
  template: "welcome",
  to: "user@example.com",
  vars: { name: "Ada" },
  metadata: { userId: "usr_123" },
});
```

No-dependency `fetch` fallback (edge runtimes, or when avoiding the SDK):

```ts
const res = await fetch("https://api.senderkit.com/v1/send", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.SENDERKIT_API_KEY}`,
    "Content-Type": "application/json",
    "Idempotency-Key": "welcome:usr_123",
  },
  body: JSON.stringify({
    template: "welcome",
    to: "user@example.com",
    vars: { name: "Ada" },
  }),
});

if (!res.ok) {
  const { error } = await res.json();
  throw new Error(`SenderKit ${res.status}: ${error.code} — ${error.message}`);
}
const { id, status } = await res.json();
```

## Python

```python
import os
import httpx  # or: requests

resp = httpx.post(
    "https://api.senderkit.com/v1/send",
    headers={
        "Authorization": f"Bearer {os.environ['SENDERKIT_API_KEY']}",
        "Idempotency-Key": "welcome:usr_123",
    },
    json={
        "template": "welcome",
        "to": "user@example.com",
        "vars": {"name": "Ada"},
        "metadata": {"userId": "usr_123"},
    },
    timeout=10.0,
)
resp.raise_for_status()
message = resp.json()  # {"id": "msg_…", "status": "queued", "livemode": False}
```

## PHP

```php
<?php
$ch = curl_init("https://api.senderkit.com/v1/send");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => [
        "Authorization: Bearer " . getenv("SENDERKIT_API_KEY"),
        "Content-Type: application/json",
        "Idempotency-Key: welcome:usr_123",
    ],
    CURLOPT_POSTFIELDS => json_encode([
        "template" => "welcome",
        "to" => "user@example.com",
        "vars" => ["name" => "Ada"],
        "metadata" => ["userId" => "usr_123"],
    ]),
]);

$body = curl_exec($ch);
$status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($status >= 400) {
    throw new RuntimeException("SenderKit error $status: $body");
}
$message = json_decode($body, true); // ["id" => "msg_…", "status" => "queued", ...]
```

## Ruby

```ruby
require "net/http"
require "json"
require "uri"

uri = URI("https://api.senderkit.com/v1/send")
req = Net::HTTP::Post.new(uri)
req["Authorization"]   = "Bearer #{ENV.fetch('SENDERKIT_API_KEY')}"
req["Content-Type"]    = "application/json"
req["Idempotency-Key"] = "welcome:usr_123"
req.body = {
  template: "welcome",
  to: "user@example.com",
  vars: { name: "Ada" },
  metadata: { userId: "usr_123" },
}.to_json

res = Net::HTTP.start(uri.hostname, uri.port, use_ssl: true) { |http| http.request(req) }
raise "SenderKit error #{res.code}: #{res.body}" if res.code.to_i >= 400

message = JSON.parse(res.body) # {"id"=>"msg_…", "status"=>"queued", "livemode"=>false}
```

## Go

```go
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"time"
)

func main() {
	payload, _ := json.Marshal(map[string]any{
		"template": "welcome",
		"to":       "user@example.com",
		"vars":     map[string]any{"name": "Ada"},
		"metadata": map[string]any{"userId": "usr_123"},
	})

	req, _ := http.NewRequest("POST", "https://api.senderkit.com/v1/send", bytes.NewReader(payload))
	req.Header.Set("Authorization", "Bearer "+os.Getenv("SENDERKIT_API_KEY"))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Idempotency-Key", "welcome:usr_123")

	client := &http.Client{Timeout: 10 * time.Second}
	res, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer res.Body.Close()

	var out struct {
		ID       string `json:"id"`
		Status   string `json:"status"`
		Livemode bool   `json:"livemode"`
	}
	json.NewDecoder(res.Body).Decode(&out)
	if res.StatusCode >= 400 {
		panic(fmt.Sprintf("SenderKit error %d", res.StatusCode))
	}
	fmt.Printf("%s %s\n", out.ID, out.Status)
}
```

## Error handling to mirror in every language

Branch on the documented responses (confirm exact codes in the OpenAPI):

- `400` — validation / `channel_mismatch` / `envelope_not_supported`. Fix the request; do not retry unchanged.
- `401` — bad or revoked key.
- `402` — `message_limit_reached` / `managed_send_limit_reached` (plan quota).
- `404` — template not found, or no published version in live mode. Not retryable.
- `422` — `template_archived`: the template exists but can no longer be sent.
- `429` — rate limited; read `Retry-After` (seconds) and back off before retrying.

Log the stable `error.code`, never the API key or message body.
