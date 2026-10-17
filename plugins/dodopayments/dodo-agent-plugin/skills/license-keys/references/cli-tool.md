# Dodo Payments License Keys: CLI Tool Integration


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
const client = new DodoPayments({ bearerToken: 'public', environment: 'test_mode' }); // public endpoints: placeholder token; use 'live_mode' in production

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
      license_key_instance_id: license.instanceId,
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
