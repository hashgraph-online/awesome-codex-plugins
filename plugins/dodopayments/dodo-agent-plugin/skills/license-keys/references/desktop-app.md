# Dodo Payments License Keys: Desktop App Integration


### Electron app example

```typescript
// main/license.ts
import Store from 'electron-store';
import DodoPayments from 'dodopayments';
import os from 'os';

const store = new Store();
const client = new DodoPayments({ bearerToken: 'public', environment: 'test_mode' }); // public endpoints: placeholder token; use 'live_mode' in production

interface LicenseInfo {
  key: string;
  instanceId: string;
  activatedAt: string;
  lastValidatedAt?: string; // last time the server confirmed the license (absent on records saved before it was added)
}

export async function activateLicense(licenseKey: string): Promise<boolean> {
  try {
    const deviceName = `${os.hostname()} - ${os.platform()}`;

    const response = await client.licenses.activate({
      license_key: licenseKey,
      name: deviceName,
    });

    const now = new Date().toISOString();
    const licenseInfo: LicenseInfo = {
      key: licenseKey,
      instanceId: response.id,
      activatedAt: now,
      lastValidatedAt: now,
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
      license_key_instance_id: license.instanceId,
    });

    if (!response.valid) {
      // An explicit "invalid" from the server (revoked key, deactivated
      // instance) ends the license: drop the cache so a later offline start
      // cannot fall back to the grace period.
      store.delete('license');
      return false;
    }
    store.set('license', { ...license, lastValidatedAt: new Date().toISOString() });
    return true;
  } catch (error) {
    // Only a connection failure (offline, DNS, timeout) earns the grace period.
    // Any other API error - a revoked key, a deactivated instance - is a real
    // answer from the server, so fail closed.
    if (!(error instanceof DodoPayments.APIConnectionError)) {
      return false;
    }

    // Trust the cached result only within a grace period measured from the
    // LAST SUCCESSFUL validation, not from activation - otherwise a key revoked
    // yesterday keeps working offline for 30 days after activation, and an old
    // activation gets no grace at all.
    // Records saved before lastValidatedAt existed fall back to activatedAt
    // until their first successful validation.
    const lastValidated = new Date(license.lastValidatedAt ?? license.activatedAt);
    const daysSinceValidation = (Date.now() - lastValidated.getTime()) / (1000 * 60 * 60 * 24);

    // Allow 30-day offline grace period
    return daysSinceValidation < 30;
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
