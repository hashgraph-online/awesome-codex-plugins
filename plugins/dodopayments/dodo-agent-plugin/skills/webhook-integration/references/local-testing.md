# Dodo Payments Webhook Integration: Local Testing


### Dashboard test tool

1. Go to **Developer → Webhooks → [your endpoint] → Testing**
2. Select an event type
3. Click **Send Example**
4. Verify your endpoint returns `200` and the signature verifies

### CLI: Live forwarding

Forward real test-mode events to localhost:

```bash
dodo wh listen http://localhost:3000/webhook
```

This creates a test webhook, opens a WebSocket relay, and forwards events with the original `webhook-id`/`webhook-signature`/`webhook-timestamp` headers to your local URL. Requires a test-mode API key. The relay and CLI parse and **re-serialize** the JSON body, so if it differs byte-for-byte from the original (for example number formatting), signature verification fails even though the headers are intact - that is a relay artifact, not a bug in your verifier. The URL argument is required in direct mode — bare `dodo wh listen` only works as `/wh listen` inside the TUI.

### CLI: Unsigned mock events

Generate realistic unsigned payloads for testing without signature verification:

```bash
dodo wh trigger payment.success http://localhost:3000/webhook
```

Use `unsafeUnwrap()` only for these unsigned payloads. Both arguments are required in direct mode.

Trigger names are not always the payload `type`: `payment.success` sends `type: "payment.succeeded"`, `refund.success` sends `refund.succeeded`, and `licence.created` sends `license_key.created`. Your handler must switch on the payload types. `subscription.past_due` and `subscription.unpaused` cannot be triggered.

### Tunnel

Expose localhost with ngrok and register the HTTPS URL in the dashboard:

```bash
ngrok http 3000
# Register https://xxxx.ngrok.io/webhook in the dashboard
```

---
