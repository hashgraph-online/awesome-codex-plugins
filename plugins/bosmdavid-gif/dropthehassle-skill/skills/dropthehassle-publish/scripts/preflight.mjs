#!/usr/bin/env node
// DropTheHassle preflight: is this folder a finished static site that fits the upload limits?
// Node 18+, standard library only, no network, changes nothing on disk.
//
//   node preflight.mjs [folder] [--json]
//
// It mirrors the rules the DropTheHassle CLI and MCP server use to choose a folder (an index.html
// or a TanStack _shell.html at the top, or dist/, build/, out/, .output/public/ or dist/client/ in a project) and the
// server's upload limits. The server still makes the final call on deploy.
// Exit code: 0 ready, 1 not ready (see "blockers"), 2 bad usage.

import fs from 'node:fs';
import path from 'node:path';

const ANON = { bytes: 25 * 1024 * 1024, files: 1000 };
const SIGNED_IN = { bytes: 100 * 1024 * 1024, files: 5000 };
// What the CLI and MCP server leave out when they zip a folder.
const SKIP = new Set(['node_modules', '.git', '.gitignore', '.DS_Store', '.next', '.nuxt', '.svelte-kit',
  '.vercel', '.cache', '.turbo', '.parcel-cache', '__MACOSX', 'bower_components', 'coverage', '.svn',
  '.hg', '.dropthehassle.json']);
// Refused in an upload before the site is claimed.
const FORBIDDEN = new Set(['.exe', '.msi', '.apk', '.dmg', '.scr', '.bat', '.zip', '.rar', '.7z', '.iso']);
const SERVER_HINTS = ['.php', '.py', '.rb'];

const args = process.argv.slice(2);
const asJson = args.includes('--json');
const target = path.resolve(args.find((a) => !a.startsWith('--')) || '.');

const isFile = (p) => { try { return fs.statSync(p).isFile(); } catch { return false; } };
const isDir = (p) => { try { return fs.statSync(p).isDirectory(); } catch { return false; } };
const readJson = (p) => { try { return JSON.parse(fs.readFileSync(p, 'utf8')); } catch { return null; } };
const hasIndex = (d) => isFile(path.join(d, 'index.html'));
// A TanStack Start SPA build has _shell.html as its start page (the server copies it to index.html).
const hasShell = (d) => !isFile(path.join(d, 'index.html')) && isFile(path.join(d, '_shell.html'));
const rel = (p) => { const r = path.relative(process.cwd(), p) || '.'; return r.startsWith('..') ? p : r; };

function framework(dir, pkg) {
  const deps = Object.assign({}, pkg && pkg.dependencies, pkg && pkg.devDependencies);
  let names = [];
  try { names = fs.readdirSync(dir); } catch { /* unreadable */ }
  const has = (prefix) => names.some((n) => n.startsWith(prefix));
  if (deps['@tanstack/react-start'] || deps['@tanstack/solid-start'] || deps['@tanstack/start']) return 'tanstack-start';
  if (deps.nuxt || has('nuxt.config.')) return 'nuxt';
  if (deps.next || has('next.config.')) return 'next';
  if (deps.astro || has('astro.config.')) return 'astro';
  if (deps.vite || has('vite.config.')) return 'vite';
  if (deps['react-scripts']) return 'cra';
  return null;
}

function isDevIndex(dir) {
  let text = '';
  try { text = fs.readFileSync(path.join(dir, 'index.html'), 'utf8').slice(0, 200000); } catch { return false; }
  return /<script\b[^>]*\bsrc\s*=\s*['"][^'"]*(?:\/src\/|\.tsx|\.jsx|\.ts)['"]/i.test(text);
}

const BUILD_HINT = {
  next: "Set output: 'export' in next.config, run the build, then publish out/.",
  nuxt: 'Run `npx nuxi generate` (or the generate script), then publish .output/public/.',
  cra: 'Run `npm install && npm run build`, then publish build/.',
  vite: 'Run `npm install && npm run build`, then publish dist/.',
  astro: 'Run `npm install && npm run build`, then publish dist/.',
  'tanstack-start': 'This is a server app (TanStack Start). Run the whole app on AWS, Google Cloud, DigitalOcean or your own server and connect it with set_backend, or make a static SPA build (dist/client) without its server functions and /api routes. See references/troubleshooting.md, TanStack Start.',
};

function choose(dir) {
  const pkg = readJson(path.join(dir, 'package.json'));
  const fw = framework(dir, pkg);
  const buildScript = !!(pkg && pkg.scripts && typeof pkg.scripts.build === 'string' && pkg.scripts.build.trim());
  const project = buildScript || !!fw;
  if (!project) {
    if (hasIndex(dir)) return { dir, why: 'index.html at the top of the folder' };
    if (hasShell(dir)) return { dir, why: '_shell.html at the top of the folder (a TanStack Start SPA build; DropTheHassle uses it as the start page)', fw: 'tanstack-start' };
    for (const name of ['dist', 'build', 'out', '_site', 'public', 'docs']) {
      if (hasIndex(path.join(dir, name))) return { dir: path.join(dir, name), why: `${name}/ holds index.html` };
    }
    // The dist/ of a TanStack Start SPA build: dist/client/_shell.html next to dist/server/.
    for (const name of ['client', 'dist/client']) {
      if (hasShell(path.join(dir, name))) return { dir: path.join(dir, name), why: `${name}/ is a TanStack Start SPA build (_shell.html)`, fw: 'tanstack-start' };
    }
    const marker = ['server.js', 'app.py', 'main.py', 'index.php', 'wsgi.py', 'manage.py'].find((m) => isFile(path.join(dir, m)));
    if (marker) return { dir, blocker: `No index.html, and ${marker} is here: this is an app that needs a server. DropTheHassle does not run it itself: host it on AWS, Google Cloud, DigitalOcean or your own server, then connect it with set_backend (no site: every path is proxied) or the dashboard's Backend card.` };
    return { dir, blocker: 'No index.html (or _shell.html for a TanStack SPA build) at the top of this folder (or in dist/, build/, out/, _site/, public/ or docs/). Rename the main page to index.html, or point at the folder that has it.' };
  }
  const prefer = { next: 'out', cra: 'build', nuxt: '.output/public', 'tanstack-start': 'dist/client', vite: 'dist', astro: 'dist' }[fw];
  const options = [prefer, 'dist', 'build', 'out', '.output/public'].filter(Boolean);
  for (const name of options) {
    const d = path.join(dir, name);
    if (hasIndex(d) || (name === 'dist/client' && isFile(path.join(d, '_shell.html')))) {
      return { dir: d, why: `${name}/ is the build output of this ${fw || 'project'}`, project: true, fw };
    }
  }
  if (fw === 'tanstack-start') return { dir, blocker: 'TanStack Start source or server build. ' + BUILD_HINT[fw], fw };
  if (hasIndex(dir) && !isDevIndex(dir) && !['next', 'vite', 'astro', 'nuxt'].includes(fw)) {
    return { dir, why: 'index.html at the top of the project', project: true, fw };
  }
  return { dir, blocker: 'This is source code, not a built site. ' + (BUILD_HINT[fw] || 'Run `npm install && npm run build`, then publish the folder it writes (dist/, build/ or out/).'), fw };
}

function scan(dir) {
  const out = { files: 0, bytes: 0, forbidden: [], server: [], biggest: [] };
  (function walk(d, base) {
    let entries = [];
    try { entries = fs.readdirSync(d, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (SKIP.has(e.name) || (e.name.startsWith('.') && e.name !== '.well-known')) continue;
      const abs = path.join(d, e.name);
      const r = base ? `${base}/${e.name}` : e.name;
      if (e.isDirectory()) { walk(abs, r); continue; }
      if (!e.isFile()) continue;
      const size = fs.statSync(abs).size;
      out.files += 1; out.bytes += size;
      const ext = path.extname(e.name).toLowerCase();
      if (FORBIDDEN.has(ext) && out.forbidden.length < 10) out.forbidden.push(r);
      if (SERVER_HINTS.includes(ext) && out.server.length < 10) out.server.push(r);
      out.biggest.push([r, size]);
      out.biggest.sort((a, b) => b[1] - a[1]);
      if (out.biggest.length > 5) out.biggest.length = 5;
    }
  })(dir, '');
  return out;
}

if (!isDir(target)) {
  console.error(`Not a folder: ${target}`);
  process.exit(2);
}

const picked = choose(target);
const report = { folder: rel(target), publish: rel(picked.dir), framework: picked.fw || null, ready: false, blockers: [], warnings: [] };
if (picked.blocker) {
  report.blockers.push(picked.blocker);
} else {
  report.reason = picked.why;
  if (isDevIndex(picked.dir)) report.blockers.push('index.html loads a source file (/src/…, .ts, .tsx or .jsx). That is a dev entry. Build the site and publish the output.');
  const s = scan(picked.dir);
  report.files = s.files;
  report.megabytes = Math.round((s.bytes / 1048576) * 10) / 10;
  if (s.files > SIGNED_IN.files || s.bytes > SIGNED_IN.bytes) {
    report.blockers.push(`Over the signed-in limit (${SIGNED_IN.files} files, 100 MB). Publish only the build folder and move big media elsewhere.`);
  } else if (s.files > ANON.files || s.bytes > ANON.bytes) {
    report.warnings.push(`Over the no-account limit (${ANON.files} files, 25 MB) but within the signed-in one (5,000 files, 100 MB). Deploy with --login, or a token, or make the site smaller.`);
  }
  if (s.forbidden.length) report.warnings.push(`Executable or archive files are refused before the site is claimed: ${s.forbidden.join(', ')}. Remove them from the site folder.`);
  if (s.server.length) report.warnings.push(`Server-side files found (${s.server.join(', ')}). DropTheHassle does not run server code, so they will not execute here. If the site needs them, run them on AWS, Google Cloud, DigitalOcean or your own server and connect it with set_backend.`);
  if (picked.dir === target && isFile(path.join(target, 'package.json'))) report.warnings.push('package.json sits next to index.html, so the whole project folder would be published. Check that this is the finished site, not source.');
  if (s.biggest.length && s.biggest[0][1] > 5 * 1048576) report.warnings.push('Largest files: ' + s.biggest.filter(([, b]) => b > 1048576).map(([n, b]) => `${n} (${(b / 1048576).toFixed(1)} MB)`).join(', '));
  report.ready = report.blockers.length === 0;
}

if (asJson) {
  console.log(JSON.stringify(report, null, 2));
} else {
  console.log(report.ready ? 'READY' : 'NOT READY');
  console.log(`  folder checked: ${report.folder}`);
  console.log(`  would publish:  ${report.publish}${report.reason ? `  (${report.reason})` : ''}`);
  if (report.files !== undefined) console.log(`  size:           ${report.files} files, ${report.megabytes} MB`);
  for (const b of report.blockers) console.log(`  BLOCKER: ${b}`);
  for (const w of report.warnings) console.log(`  warning: ${w}`);
  // Name the folder that was checked: the CLI finds the build output itself, and its link file
  // (.dropthehassle.json) then lives in the project, where a rebuild of dist/ cannot delete it.
  if (report.ready) console.log(`  next: ask the user for their email, then run: npx -y dropthehassle@latest deploy ${JSON.stringify(report.folder)} --email <the user's email>`);
}
process.exit(report.ready ? 0 : 1);
