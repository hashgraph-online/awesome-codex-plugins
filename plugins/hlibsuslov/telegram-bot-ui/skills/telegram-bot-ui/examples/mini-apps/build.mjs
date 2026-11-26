// Builds the browser files of the no-dependency examples: strips TypeScript types with Node's own
// module.stripTypeScriptTypes (Node >= 22.18) and rewrites relative ".ts" imports to ".js".
// Output goes next to each app in dist/ (git-ignored). No bundler, no packages.
//   node build.mjs           # build every app listed in APPS
//   node build.mjs --check   # exit 1 if a dist file is missing or older than its source
import { stripTypeScriptTypes } from 'node:module';
import { mkdirSync, readFileSync, statSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
// app folder -> { source file: output name }
const APPS = {
  vanilla: { 'vanilla/app.ts': 'app.js', '_kit/tma.ts': 'tma.js' },
  portfolio: { 'portfolio/app.ts': 'app.js', '_kit/tma.ts': 'tma.js' },
  gallery: { 'gallery/app.ts': 'app.js', '_kit/tma.ts': 'tma.js', '_kit/tg-values.ts': 'tg-values.js' },
  catalog: { 'catalog/app.ts': 'app.js', '_kit/tma.ts': 'tma.js' },
  rework: { 'rework/app.ts': 'app.js', '_kit/tma.ts': 'tma.js', '_kit/tg-values.ts': 'tg-values.js' },
  paywall: { 'paywall/app.ts': 'app.js', '_kit/tma.ts': 'tma.js' },
};
const KIT_IMPORT = /from\s+['"]\.\.\/_kit\/([\w-]+)\.ts['"]/g;

function build(check) {
  let stale = 0;
  for (const [app, files] of Object.entries(APPS)) {
    if (!existsSync(join(here, app))) continue;
    for (const [src, out] of Object.entries(files)) {
      const from = join(here, src);
      const to = join(here, app, 'dist', out);
      if (check) {
        if (!existsSync(to) || statSync(to).mtimeMs < statSync(from).mtimeMs) {
          console.log(`stale: ${relative(here, to)}`);
          stale++;
        }
        continue;
      }
      const js = stripTypeScriptTypes(readFileSync(from, 'utf8'), { mode: 'strip' })
        .replace(KIT_IMPORT, "from './$1.js'");
      mkdirSync(dirname(to), { recursive: true });
      writeFileSync(to, `// Built by build.mjs from ${src}. Do not edit.\n${js}`);
      console.log(`built ${relative(here, to)}`);
    }
  }
  return stale;
}

process.removeAllListeners('warning'); // stripTypeScriptTypes is marked experimental in Node 22-24
const check = process.argv.includes('--check');
const stale = build(check);
if (check && stale) process.exit(1);
