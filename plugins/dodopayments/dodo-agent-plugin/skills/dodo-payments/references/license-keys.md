# License keys

## Contents

- [How license keys work](#how-license-keys-work)
- [Activate, validate and deactivate in your app](#activate-validate-and-deactivate-in-your-app)
- [Wire it into a CLI](#wire-it-into-a-cli)
- [Desktop apps](#desktop-apps)
- [Merchant side: list, revoke, import](#merchant-side-list-revoke-import)
- [License key webhooks](#license-key-webhooks)
- [Common mistakes](#common-mistakes)

## How license keys work

Attach a **License Key** entitlement to a product. On purchase Dodo issues a key, emails it to the customer, and enforces the activation limit (blank means unlimited). Three surfaces:

| Surface | Auth | Use |
|---|---|---|
| `client.licenses.activate / validate / deactivate` | Public, no API key | Your app, CLI or desktop client |
| `client.customers.listEntitlementGrants`, `client.entitlements.grants.*` | API key, server only | List and revoke keys |
| `client.licenseKeyInstances.*` | API key, server only | List activated devices |

Validity follows the purchase automatically:

- One-time purchases use the entitlement's duration.
- Subscription keys have no own expiry. `past_due` keeps them active; `on_hold` and `paused` disable them until recovery; `cancelled` and `expired` disable them; a plan change replaces them.
- A refund of a one-time payment disables the key.

You never disable keys yourself; `validate` reflects the current state.

## Activate, validate and deactivate in your app

The license endpoints are public, so the client takes a placeholder token. Never ship a real API key in an app.

```typescript
// src/license.ts
import DodoPayments from 'dodopayments';

const client = new DodoPayments({ bearerToken: 'public', environment: 'test_mode' }); // 'live_mode' in production

export interface StoredLicense {
  key: string;
  instanceId: string;
  lastValidatedAt: string;
}

const GRACE_DAYS = 30;

export async function activate(key: string, deviceName: string): Promise<StoredLicense> {
  try {
    const instance = await client.licenses.activate({ license_key: key, name: deviceName });
    return { key, instanceId: instance.id, lastValidatedAt: new Date().toISOString() };
  } catch (error) {
    if (error instanceof DodoPayments.APIError && error.status === 422) {
      throw new Error('Activation limit reached. Deactivate another device first.');
    }
    throw error;
  }
}

// Validate on every start. Fail closed, except for a network failure inside the grace period.
export async function isLicensed(license: StoredLicense): Promise<{ valid: boolean; license: StoredLicense }> {
  try {
    const result = await client.licenses.validate({
      license_key: license.key,
      license_key_instance_id: license.instanceId, // also checks this device is still activated
    });
    return { valid: result.valid, license: { ...license, lastValidatedAt: new Date().toISOString() } };
  } catch (error) {
    if (!(error instanceof DodoPayments.APIConnectionError)) return { valid: false, license };
    const days = (Date.now() - new Date(license.lastValidatedAt).getTime()) / 86_400_000;
    return { valid: days < GRACE_DAYS, license };
  }
}

export async function deactivate(license: StoredLicense): Promise<void> {
  await client.licenses.deactivate({
    license_key: license.key,
    license_key_instance_id: license.instanceId,
  });
}
```

Store the key and the instance ID together; deactivation needs both. On an explicit `valid: false`, delete the stored license so the grace period cannot apply.

## Wire it into a CLI

```typescript
// src/cli.ts
import { Command } from 'commander';
import Conf from 'conf';
import os from 'node:os';
import { activate, deactivate, isLicensed, type StoredLicense } from './license';

const store = new Conf<{ license?: StoredLicense }>({ projectName: 'your-cli' });
const program = new Command();

program.command('activate <key>').action(async (key: string) => {
  store.set('license', await activate(key, `${os.hostname()} (${process.platform})`));
  console.log('License activated.');
});

program.command('deactivate').action(async () => {
  const license = store.get('license');
  if (license) await deactivate(license);
  store.delete('license');
});

program
  .command('generate')
  .hook('preAction', async () => {
    const license = store.get('license');
    const result = license ? await isLicensed(license) : { valid: false, license };
    if (!result.valid) {
      store.delete('license');
      console.error('This command needs a license. Run: your-cli activate <key>');
      process.exit(1);
    }
    store.set('license', result.license);
  })
  .action(() => {
    // licensed feature
  });

program.parse();
```

## Desktop apps

Run the same `license.ts` in the Electron main process (store with `electron-store`) and expose `activate` and `isLicensed` to the renderer over IPC. The renderer only collects the key and shows the result. On a 422, show the customer's active devices (from your server, via `client.licenseKeyInstances.list`) so they can deactivate one.

## Merchant side: list, revoke, import

Server only, with your API key.

```typescript
for await (const grant of client.customers.listEntitlementGrants('cus_abc123', {
  integration_type: 'license_key',
  status: 'Delivered',
})) {
  if (!grant.license_key) continue; // null on a manual grant that is still Pending
  console.log(grant.id, grant.license_key.key, grant.license_key.status, grant.license_key.activations_used);
}

for await (const instance of client.licenseKeyInstances.list({ license_key_id: 'lk_abc123' })) {
  console.log(instance.id, instance.name, instance.created_at);
}

// Revoke (manually revoked keys are not re-granted on renewal). Confirm first in live mode.
await client.entitlements.grants.revoke('entg_abc123', { id: 'ent_license_key' });

// Import a key from another system. Dodo does not email imported keys.
await client.licenseKeys.create({
  customer_id: 'cus_abc123',
  product_id: 'pdt_abc123',
  key: 'PREMIUM-AAAA-BBBB-CCCC',
  activations_limit: 5,
});
```

Every key for one entitlement: `client.entitlements.grants.list('ent_...', { status: 'Delivered' })`.

## License key webhooks

Dodo emails keys and changes their state itself; your webhook only mirrors the state in your database. Verify and deduplicate as in [webhooks.md](webhooks.md).

| Webhook | Meaning |
|---|---|
| `entitlement_grant.created` | Grant created. An auto-fulfilled key arrives here with `status: 'Delivered'` and `license_key`; no `.delivered` follows |
| `entitlement_grant.delivered` | An existing grant became `Delivered` later (manual fulfilment, or a revoked grant restored) |
| `entitlement_grant.revoked` | Dodo disabled the key; see `revocation_reason` |
| `entitlement_grant.failed` | Delivery failed; see `error_code` and `error_message` |

```typescript
import DodoPayments from 'dodopayments';

export async function handleLicenseWebhook(event: DodoPayments.UnwrapWebhookEvent) {
  if (
    (event.type === 'entitlement_grant.created' || event.type === 'entitlement_grant.delivered') &&
    event.data.status === 'Delivered' &&
    event.data.license_key
  ) {
    await mirrorGrant(event.data.id, event.data.license_key.key, 'active', event.data.updated_at);
  }
  if (event.type === 'entitlement_grant.revoked') {
    await mirrorGrant(event.data.id, null, 'revoked', event.data.updated_at);
  }
}
```

Webhooks can arrive out of order: in `mirrorGrant`, update the row only when the grant's `updated_at` is newer than the stored one.

## Common mistakes

- Validating once at install and trusting it forever. Validate on each start.
- Failing open on errors. Only a connection error earns the offline grace period.
- Trusting a client-side "licensed" flag for server features. Validate on your server.
- Not storing the instance ID, which deactivation needs.
- Emailing keys or disabling them on cancellation yourself. Dodo does both.
