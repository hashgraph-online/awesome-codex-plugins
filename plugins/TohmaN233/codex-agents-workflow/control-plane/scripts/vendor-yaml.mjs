import { build } from 'esbuild';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const output = join(root, 'lib', 'vendor'); await mkdir(output, { recursive: true });
const result = await build({ absWorkingDir: root, tsconfigRaw: {}, stdin: { contents: "export { parseDocument } from './node_modules/yaml/browser/index.js';", resolveDir: root, sourcefile: 'yaml-entry.mjs' },
  bundle: true, platform: 'node', format: 'esm', target: 'node20', minify: true, write: false, legalComments: 'inline',
  banner: { js: '// Generated from yaml@2.9.0 by scripts/vendor-yaml.mjs. ISC license: yaml.LICENSE.' },
});
const bytes = result.outputFiles[0].contents;
await writeFile(join(output, 'yaml.mjs'), bytes);
await writeFile(join(output, 'yaml.LICENSE'), await readFile(join(root, 'node_modules', 'yaml', 'LICENSE')));
await writeFile(join(output, 'yaml-source.json'), JSON.stringify({ name: 'yaml', version: '2.9.0', license: 'ISC',
  repository: 'https://github.com/eemeli/yaml', bundled_sha256: createHash('sha256').update(bytes).digest('hex'),
  build: 'esbuild@0.28.2; node20; esm; minify',
}, null, 2) + '\n');
