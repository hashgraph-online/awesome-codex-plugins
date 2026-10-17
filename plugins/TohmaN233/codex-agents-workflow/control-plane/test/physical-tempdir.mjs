import { realpathSync } from 'node:fs';
import { tmpdir as osTmpdir } from 'node:os';

// macOS /var -> /private/var and Windows RUNNER~1 are environment aliases.
// Fixtures choose the physical directory explicitly; production link checks stay
// strict, and dedicated tests still exercise links and short-path inputs.
// The native API expands Windows 8.3 spellings; JS realpathSync preserves them.
export const tmpdir = () => realpathSync.native(osTmpdir());
