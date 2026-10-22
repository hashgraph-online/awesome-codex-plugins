# Dodo Payments Webhook Integration: Common Mistakes


### 1. Signing only the payload or `timestamp.payload`

**Wrong:**
```typescript
const signed = crypto.createHmac('sha256', secret)
  .update(payload)
  .digest('base64');

// or
const signed = crypto.createHmac('sha256', secret)
  .update(`${timestamp}.${payload}`)
  .digest('base64');
```

**Correct:** The signed message is `webhook-id.webhook-timestamp.raw_body`, all three parts joined by periods. Use the SDK helper to avoid this entirely.

### 2. Re-serializing the parsed body

**Wrong:**
```typescript
const body = await req.json();
const signed = JSON.stringify(body); // Reordered, reformatted, breaks signature
```

**Correct:** Always use the raw bytes:
```typescript
const body = await req.text(); // or req.body.toString() in Express
// Pass body directly to unwrap() or webhook.verify()
```

### 3. Naive comma-splitting of the signature header

**Wrong:**
```typescript
const sig = signature.split(',')[1]; // Assumes exactly one comma
```

The header is versioned and can contain multiple values. Use the SDK helper.

### 4. `timingSafeEqual` throwing on length mismatch

**Wrong:**
```typescript
crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(provided));
// Throws if lengths differ; doesn't return false
```

**Correct:** Use the SDK helper, which handles this safely.

### 5. Granting access from `return_url` instead of verified webhooks

**Wrong:**
```typescript
// User visits return_url after checkout; you grant access
app.get('/checkout/return', (req, res) => {
  grantAccess(req.query.customer_id); // Unverified!
});
```

**Correct:** Grant access only after receiving and verifying a webhook:
```typescript
const event = client.webhooks.unwrap(rawBody, { headers });

if (event.type === 'payment.succeeded') {
  grantAccess(event.data.customer.customer_id);
}
```

### 6. Doing slow work before responding 2xx

**Wrong:**
```typescript
app.post('/webhook', async (req, res) => {
  const unwrapped = client.webhooks.unwrap(...);
  
  // Slow database writes, email sends, etc.
  await db.payment.create(...);
  await sendEmail(...);
  
  res.json({ received: true }); // Dodo times out after 30s
});
```

**Correct:** Durably enqueue first, then respond immediately. Return non-`2xx` if persistence fails so Dodo retries:
```typescript
app.post('/webhook', async (req, res) => {
  const unwrapped = client.webhooks.unwrap(...);

  try {
    await queue.add('process-event', unwrapped); // Durable write
    return res.json({ received: true });
  } catch (error) {
    console.error('Failed to persist webhook', error);
    return res.status(503).json({ error: 'Webhook persistence failed' });
  }
});
```

### 7. Acknowledging before durable persistence

**Wrong:**
```typescript
res.json({ received: true });
await queue.add('process-event', unwrapped); // A crash can lose an acknowledged event
```

**Correct:** Verify the signature, durably insert or enqueue the event, and only then return `2xx`. If persistence fails, return non-`2xx` so Dodo retries.

### 8. Committing an idempotency claim before fulfillment

**Wrong:**
```typescript
const claim = await db.webhookLog.createMany({
  data: [{ webhookId }],
  skipDuplicates: true,
});
if (claim.count === 0) return;

await grantSubscriptionEntitlements(event.data); // A failure leaves the claim behind
```

The retry sees the existing claim and skips fulfillment, permanently dropping the event.

**Correct:** Commit the claim and all durable fulfillment changes in one transaction. A failure rolls both back, so the retry can claim the event again:
```typescript
const event = client.webhooks.unwrap(rawBody, { headers });

await db.$transaction(async (tx) => {
  const claim = await tx.webhookLog.createMany({
    data: [{ webhookId, eventType: event.type }],
    skipDuplicates: true,
  });
  if (claim.count === 0) return;

  if (event.type === 'subscription.active') {
    await grantSubscriptionEntitlements(event.data, tx);
  }
});
```

Use a transactional outbox for email or other external effects that must follow the database commit.

---
