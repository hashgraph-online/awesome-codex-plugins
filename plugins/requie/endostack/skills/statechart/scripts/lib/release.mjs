// The pinned TLA+ tools release and its download. Downloading uses Node's
// built-in fetch with no subprocess and no access to the caller's environment.
// Behind a proxy that fetch can't pass, the install hint tells the user how to
// download the jar themselves and point TLA2TOOLS at it.

import fs from 'node:fs';

export const TLA2TOOLS_VERSION = '1.7.4';
export const TLA2TOOLS_URL = `https://github.com/tlaplus/tlaplus/releases/download/v${TLA2TOOLS_VERSION}/tla2tools.jar`;
export const TLA2TOOLS_SHA256 = '936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88';

export const INSTALL_HINT = [
  'Install the toolchain yourself and point the command at it:',
  '  1. Install Java 11 or later (for example a Temurin build from https://adoptium.net).',
  `  2. Download ${TLA2TOOLS_URL}`,
  '  3. export TLA2TOOLS=/path/to/tla2tools.jar  (and JAVA=/path/to/java if java is not on PATH)',
].join('\n');

// Writes the jar to `${dest}.<pid>.part` and returns that path. The caller
// verifies the checksum before moving it into place.
export async function downloadJar(dest) {
  const tmp = `${dest}.${process.pid}.part`;
  const res = await fetch(TLA2TOOLS_URL, { redirect: 'follow' });
  if (!res.ok) throw new Error(`HTTP ${res.status} from ${TLA2TOOLS_URL}`);
  fs.writeFileSync(tmp, Buffer.from(await res.arrayBuffer()));
  return tmp;
}
