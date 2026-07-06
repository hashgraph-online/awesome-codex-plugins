---
name: auth
description: Set and save the CarsXE API key. Use this when the user provides a CarsXE API key, asks to configure the plugin, or when the session starts without a key loaded.
license: MIT
---

When the user provides a CarsXE API key or asks to configure the plugin:

1. Validate the key against the CarsXE API:
   ```
   GET https://api.carsxe.com/v1/auth/validate?key=<USER_PROVIDED_KEY>&source=codex_plugin
   ```
   - If valid: proceed to step 2.
   - If invalid: tell the user "That API key is invalid. Please check your key at https://api.carsxe.com/dashboard/developer" and stop.

2. Persist the validated key for future sessions by writing it to the plugin config file using Node.js:
   ```
   node -e "
     const fs = require('fs');
     const os = require('os');
     const path = require('path');
     const dir = process.env.PLUGIN_DATA || process.env.CLAUDE_PLUGIN_DATA || path.join(os.homedir(), '.carsxe');
     fs.mkdirSync(dir, { recursive: true });
     fs.writeFileSync(path.join(dir, 'config.json'), JSON.stringify({ api_key: process.env.CARSXE_KEY_INPUT }));
     console.log('Saved to ' + path.join(dir, 'config.json'));
   " --env CARSXE_KEY_INPUT=<USER_PROVIDED_KEY>
   ```
   This uses an environment variable to pass the key to the script, avoiding inline credential exposure.

3. Set `CARSXE_API_KEY` for the current session so all skills work immediately without restarting:
   - Run the appropriate shell command for the user's platform to export `CARSXE_API_KEY` with the validated value.

4. Confirm:
   > "CarsXE API key validated and saved. Future sessions will load it automatically."

**Verify only:** If the user asks to verify their current key without changing it, call the validate endpoint with the existing `CARSXE_API_KEY` value and report the result.
