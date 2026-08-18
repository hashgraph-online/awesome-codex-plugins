---
name: license-keys
description: Guide for implementing license key management with Dodo Payments - activation, validation, and access control for software products.
---

# Dodo Payments License Keys

License keys authorize access to your digital products. Use them for software licensing, per-seat controls, and gating premium features.

## When to use this skill

- Implementing end-user license activation and validation flows
- Building merchant dashboards to manage customer license keys
- Handling license expiry, activation limits, and subscription-linked revocation
- Integrating license checks into desktop apps, CLIs, or web services
- Reacting to license lifecycle webhooks

## Core concepts

**License Key Entitlements** deliver keys when a product is purchased. The entitlement config supplies activation limits, optional duration, and fulfillment mode (auto or manual).

**Three distinct resources:**

1. **`client.licenses.*`** — end-user activation flow (public, no API key required)
   - `activate()` — activate a key on a device
   - `validate()` — check if a key is valid
   - `deactivate()` — free an activation slot

2. **`client.licenseKeys.*`** — merchant-side key management (requires API key)
   - `list()`, `retrieve()`, `create()`, `update()` — manage keys for your customers

3. **`client.licenseKeyInstances.*`** — per-device activation instances (requires API key)
   - `list()`, `retrieve()`, `update()` — track active devices per key

**Activation limits:** blank/null means unlimited; otherwise it's the maximum concurrent activations. Attempting to activate beyond the limit returns `422`.

**Expiry semantics:**
- One-time-payment keys honor the entitlement duration.
- Subscription-issued keys have no independent expiry; validity follows subscription state. On hold disables them temporarily. An immediate cancellation disables them permanently, but when `cancel_at_next_billing_date` is set, keep them active until the subscription reaches the end of its term.
- Imported keys use nullable `expires_at`; null means perpetual.

---

## End-User Activation Flow

### Activate a license key

```typescript
import DodoPayments from 'dodopayments';

// No API key needed for public endpoints
const client = new DodoPayments();

async function activateLicense(licenseKey: string, deviceName: string) {
  try {
    const response = await client.licenses.activate({
      license_key: licenseKey,
      name: deviceName, // e.g., "John's MacBook Pro"
    });

    return {
      success: true,
      instanceId: response.id,
      customerId: response.customer.customer_id,
      productId: response.product.product_id,
    };
  } catch (error: any) {
    if (error.status === 422) {
      return { success: false, error: 'Activation limit reached' };
    }
    return { success: false, error: error.message || 'Activation failed' };
  }
}
```

Response includes `id` (instance ID), `business_id`, `name`, `license_key_id`, `created_at`, customer details, and product details.

### Validate a license key

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments();

async function validateLicense(licenseKey: string) {
  try {
    const response = await client.licenses.validate({
      license_key: licenseKey,
    });

    return { valid: response.valid };
  } catch (error) {
    return { valid: false };
  }
}
```

Optional: pass `license_key_instance_id` to validate a specific instance.

### Deactivate a license

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments();

async function deactivateLicense(licenseKey: string, instanceId: string) {
  try {
    await client.licenses.deactivate({
      license_key: licenseKey,
      license_key_instance_id: instanceId,
    });

    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
}
```

---

## Merchant-Side Key Management

### List customer license keys

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

async function listCustomerKeys(customerId: string) {
  const keys = await client.licenseKeys.list({
    customer_id: customerId,
  });

  return keys.items.map(key => ({
    id: key.id,
    key: key.key,
    status: key.status,
    expiresAt: key.expires_at,
    activationsUsed: key.instances_count,
    activationsLimit: key.activations_limit,
  }));
}
```

### Retrieve a single license key

```typescript
const key = await client.licenseKeys.retrieve('lk_abc123');

console.log({
  id: key.id,
  key: key.key,
  status: key.status,
  expiresAt: key.expires_at,
  activationsUsed: key.instances_count,
  activationsLimit: key.activations_limit,
});
```

### Update a license key

```typescript
// Disable a key or adjust its activation limit
await client.licenseKeys.update('lk_abc123', {
  disabled: true,
  // or adjust activations_limit
  activations_limit: 10,
});
```

### Create a license key (manual issuance)

```typescript
const newKey = await client.licenseKeys.create({
  customer_id: 'cus_abc123',
  key: 'PREMIUM-AAAA-BBBB-CCCC',
  product_id: 'pdt_abc123',
  activations_limit: 5,
  expires_at: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString(),
});

console.log(newKey.key); // The actual license key string
```

---

## List Activation Instances

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// List all instances for a specific license key
for await (const instance of client.licenseKeyInstances.list({
  license_key_id: 'lk_abc123',
})) {
  console.log({
    id: instance.id,
    name: instance.name,
    createdAt: instance.created_at,
  });
}
```

Optional query fields: `page_size` (default 10, max 100), `page_number` (default 0), `license_key_id`, and `grant_id`.

---

## Desktop App Integration

### Electron app example

```typescript
// main/license.ts
import Store from 'electron-store';
import DodoPayments from 'dodopayments';
import os from 'os';

const store = new Store();
const client = new DodoPayments();

interface LicenseInfo {
  key: string;
  instanceId: string;
  activatedAt: string;
}

export async function activateLicense(licenseKey: string): Promise<boolean> {
  try {
    const deviceName = `${os.hostname()} - ${os.platform()}`;

    const response = await client.licenses.activate({
      license_key: licenseKey,
      name: deviceName,
    });

    const licenseInfo: LicenseInfo = {
      key: licenseKey,
      instanceId: response.id,
      activatedAt: new Date().toISOString(),
    };

    store.set('license', licenseInfo);
    return true;
  } catch (error) {
    console.error('Activation failed:', error);
    return false;
  }
}

export async function checkLicense(): Promise<boolean> {
  const license = store.get('license') as LicenseInfo | undefined;

  if (!license) {
    return false;
  }

  try {
    const response = await client.licenses.validate({
      license_key: license.key,
    });

    return response.valid;
  } catch (error) {
    // If offline, trust local license with a grace period
    const activatedAt = new Date(license.activatedAt);
    const daysSinceActivation = (Date.now() - activatedAt.getTime()) / (1000 * 60 * 60 * 24);

    // Allow 30-day offline grace period
    return daysSinceActivation < 30;
  }
}

export async function deactivateLicense(): Promise<boolean> {
  const license = store.get('license') as LicenseInfo | undefined;

  if (!license) {
    return true;
  }

  try {
    await client.licenses.deactivate({
      license_key: license.key,
      license_key_instance_id: license.instanceId,
    });

    store.delete('license');
    return true;
  } catch (error) {
    console.error('Deactivation failed:', error);
    return false;
  }
}
```

### React component for license input

```tsx
// components/LicenseActivation.tsx
import { useState } from 'react';

interface Props {
  onActivated: () => void;
}

export function LicenseActivation({ onActivated }: Props) {
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleActivate = async () => {
    setLoading(true);
    setError(null);

    try {
      const success = await window.electronAPI.activateLicense(licenseKey);

      if (success) {
        onActivated();
      } else {
        setError('Invalid license key. Please check and try again.');
      }
    } catch (err) {
      setError('Activation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="license-form">
      <h2>Activate Your License</h2>
      <p>Enter your license key to unlock all features.</p>

      <input
        type="text"
        value={licenseKey}
        onChange={(e) => setLicenseKey(e.target.value)}
        placeholder="XXXX-XXXX-XXXX-XXXX"
        disabled={loading}
      />

      {error && <p className="error">{error}</p>}

      <button onClick={handleActivate} disabled={loading || !licenseKey}>
        {loading ? 'Activating...' : 'Activate License'}
      </button>
    </div>
  );
}
```

---

## CLI Tool Integration

### Node.js CLI example

```typescript
// src/license.ts
import Conf from 'conf';
import DodoPayments from 'dodopayments';
import { machineIdSync } from 'node-machine-id';

interface StoredLicense {
  key: string;
  instanceId: string;
  machineId: string;
}

interface CliStore {
  license?: StoredLicense;
}

// Typing the store keeps `config.get('license')` strongly typed at every call site.
const config = new Conf<CliStore>({ projectName: 'your-cli' });
const client = new DodoPayments();

export async function activate(licenseKey: string): Promise<void> {
  const machineId = machineIdSync();
  const deviceName = `CLI - ${process.platform} - ${machineId.substring(0, 8)}`;

  try {
    const response = await client.licenses.activate({
      license_key: licenseKey,
      name: deviceName,
    });

    config.set('license', {
      key: licenseKey,
      instanceId: response.id,
      machineId,
    });

    console.log('License activated successfully!');
  } catch (error: any) {
    if (error.status === 422) {
      console.error('Activation limit reached. Deactivate another device first.');
    } else {
      console.error('Activation failed:', error.message);
    }
    process.exit(1);
  }
}

export async function checkLicense(): Promise<boolean> {
  const license = config.get('license');

  if (!license) {
    return false;
  }

  try {
    const response = await client.licenses.validate({
      license_key: license.key,
    });

    return response.valid;
  } catch {
    return false;
  }
}

export async function deactivate(): Promise<void> {
  const license = config.get('license');

  if (!license) {
    console.log('No active license found.');
    return;
  }

  try {
    await client.licenses.deactivate({
      license_key: license.key,
      license_key_instance_id: license.instanceId,
    });

    config.delete('license');
    console.log('License deactivated.');
  } catch (error: any) {
    console.error('Deactivation failed:', error.message);
  }
}

export function requireLicense() {
  return async () => {
    const valid = await checkLicense();
    if (!valid) {
      console.error('This command requires a valid license.');
      console.error('Run: your-cli activate <license-key>');
      process.exit(1);
    }
  };
}
```

### CLI commands

```typescript
// src/cli.ts
import { Command } from 'commander';
import { activate, deactivate, checkLicense, requireLicense } from './license';

const program = new Command();

program
  .command('activate <license-key>')
  .description('Activate your license')
  .action(activate);

program
  .command('deactivate')
  .description('Deactivate license on this device')
  .action(deactivate);

program
  .command('status')
  .description('Check license status')
  .action(async () => {
    const valid = await checkLicense();
    console.log(valid ? 'License: Active' : 'License: Not activated');
  });

program
  .command('generate')
  .description('Generate something (requires license)')
  .hook('preAction', requireLicense())
  .action(async () => {
    // Premium feature
  });

program.parse();
```

---

## Webhook Integration

### Handle license key delivery

When a product with licensing enabled is purchased, an `entitlement_grant.delivered` webhook fires with the license key details:

Persist a local license-to-subscription association during fulfillment. Cancellation handling must query that association by `subscription_id`; filtering only by customer would also revoke keys for unrelated products or subscriptions.

```typescript
// app/api/webhooks/dodo/route.ts
import { NextRequest, NextResponse } from 'next/server';
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
});

export async function POST(req: NextRequest) {
  try {
    const body = await req.text();
    const event = client.webhooks.unwrap(body, {
      headers: {
        'webhook-id': req.headers.get('webhook-id') || '',
        'webhook-signature': req.headers.get('webhook-signature') || '',
        'webhook-timestamp': req.headers.get('webhook-timestamp') || '',
      },
    });

    if (event.type === 'entitlement_grant.delivered') {
      const { customer_id, id, license_key } = event.data;

      // Delivered grants for other entitlement types do not include a license key.
      if (!license_key) {
        return NextResponse.json({ received: true });
      }

      // Store in your database
      await prisma.license.create({
        data: {
          externalId: id,
          key: license_key.key,
          customerId: customer_id,
          expiresAt: license_key.expires_at ? new Date(license_key.expires_at) : null,
          activationsLimit: license_key.activations_limit,
          status: 'active',
        },
      });

      // Send email with activation instructions
      await sendLicenseEmail(customer_id, license_key.key);
    }

    if (event.type === 'subscription.cancelled' || event.type === 'subscription.expired') {
      const { subscription_id, cancel_at_next_billing_date } = event.data;

      // End-of-period cancellation keeps access active until the term expires.
      if (event.type === 'subscription.cancelled' && cancel_at_next_billing_date) {
        return NextResponse.json({ received: true });
      }

      // Query your persisted license-to-subscription mapping.
      const licenseKeyIds = await getLicenseKeyIdsForSubscription(subscription_id);

      for (const licenseKeyId of licenseKeyIds) {
        await client.licenseKeys.update(licenseKeyId, {
          disabled: true,
        });
      }
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 401 });
  }
}
```

**Webhook events:**

- `entitlement_grant.delivered` — license key issued (current, recommended)
- `entitlement_grant.revoked` — license key revoked
- `license_key.created` — legacy event (still fires, but use `entitlement_grant.*` for new integrations)
- `subscription.cancelled` — disable only this subscription's keys for immediate cancellation
- `subscription.expired` — disable this subscription's keys when its term ends

---

## Common Mistakes

### 1. Validating only at install time

Don't validate once and trust forever. Validate periodically (e.g., weekly) to catch revoked or expired keys.

```typescript
// Bad: validate once
if (await validateLicense(key)) {
  store.set('trusted', true);
}

// Good: validate on each startup
const isValid = await validateLicense(key);
if (!isValid) {
  // Fail closed
  process.exit(1);
}
```

### 2. Not handling activation-limit errors

When a user hits the activation limit, they need a clear path to deactivate an old device.

```typescript
try {
  await client.licenses.activate({ license_key: key, name: deviceName });
} catch (error: any) {
  if (error.status === 422) {
    // Show UI: "You've reached your activation limit. Deactivate a device first."
    // Provide a list of active instances so they can choose which to remove.
  }
}
```

### 3. Trusting client-side validation alone

Always validate on your server before granting access to sensitive features.

```typescript
// Bad: trust the client
if (localStorage.getItem('license_valid')) {
  showPremiumFeature();
}

// Good: validate server-side
const response = await fetch('/api/validate-license', {
  method: 'POST',
  body: JSON.stringify({ licenseKey }),
});
const { valid } = await response.json();
if (valid) {
  showPremiumFeature();
}
```

### 4. Hardcoding license keys

Never embed keys in client code or version control.

```typescript
// Bad
const LICENSE_KEY = 'PRO-AAAA-BBBB-CCCC-DDDD';

// Good
const licenseKey = process.env.DODO_LICENSE_KEY;
// or read from user input / secure storage
```

### 5. Not storing the instance ID

The instance ID is required for deactivation. Store it alongside the key.

```typescript
// Bad: only store the key
store.set('license_key', key);

// Good: store both
store.set('license', {
  key,
  instanceId: response.id,
  activatedAt: new Date().toISOString(),
});
```

### 6. Failing open on validation errors

If validation fails (network error, server down), fail closed. Don't grant access.

```typescript
// Bad: assume valid if offline
try {
  const valid = await validateLicense(key);
  return valid;
} catch {
  return true; // WRONG: grants access on error
}

// Good: fail closed, with optional grace period
try {
  const valid = await validateLicense(key);
  return valid;
} catch {
  // Only trust local cache if within grace period
  const lastValidated = store.get('last_validated_at');
  const daysSince = (Date.now() - lastValidated) / (1000 * 60 * 60 * 24);
  return daysSince < 30;
}
```

---

## Resources

- [License Keys Guide](https://docs.dodopayments.com/features/license-keys)
- [Activate License API](https://docs.dodopayments.com/api-reference/licenses/activate-license)
- [Validate License API](https://docs.dodopayments.com/api-reference/licenses/validate-license)
- [Deactivate License API](https://docs.dodopayments.com/api-reference/licenses/deactivate-license)
- [License Key Instances API](https://docs.dodopayments.com/api-reference/licenses/get-license-key-instances)
- [Entitlement Grant Webhooks](https://docs.dodopayments.com/developer-resources/webhooks/intents/entitlement-grant)
- [Webhook Verification](https://docs.dodopayments.com/developer-resources/webhooks/verification)
