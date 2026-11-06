#!/usr/bin/env node
import { readFile, stat } from 'node:fs/promises';
import { parsePage, runAudit, renderAudit } from './lib/audit.mjs';
import { createMetadataSnapshot, compareMetadataSnapshots, renderMetadataDrift } from './lib/metadata-drift.mjs';
import { clusterSerpOverlap, renderSerpOverlap } from './lib/serp-overlap.mjs';
import { writeOfflineReports } from './lib/offline-reports.mjs';

const help = `Offline SEO review, Node 22+, no dependencies or network calls.
  node scripts/seo-review.mjs audit --input pages.json --out NEW_DIR [--merchant]
  node scripts/seo-review.mjs drift --before baseline.json --after current.json --out NEW_DIR
  node scripts/seo-review.mjs serp-clusters --input serp.json --context "engine/locale/device/period" --out NEW_DIR [--depth 10] [--threshold 0.3]
Audit always captures metadata-snapshot.json; supplied inventories are partial.
Output must be new and outside the working directory or in its reports/ subtree.
`;
function options(argv) {
  if (!argv.length || argv.includes('--help') || argv.includes('-h')) return { help: true };
  const result = { command: argv[0] };
  const allowed = { audit: ['input','out','merchant'], drift: ['before','after','out'], 'serp-clusters': ['input','context','depth','threshold','out'] }[result.command];
  if (!allowed) throw new Error('Unknown command');
  for (let i = 1; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, '');
    if (argv[i] !== `--${key}` || !allowed.includes(key) || key in result) throw new Error(`Invalid or duplicate option: ${argv[i]}`);
    if (key === 'merchant') result[key] = true;
    else {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`Missing value: --${key}`);
      result[key] = value;
    }
  }
  const required = result.command === 'drift' ? ['before','after','out'] : result.command === 'audit' ? ['input','out'] : ['input','context','out'];
  for (const key of required) if (!result[key]) throw new Error(`Missing --${key}`);
  return result;
}
async function jsonFile(filename) {
  if ((await stat(filename)).size > 25_000_000) throw new Error('Offline input exceeds 25 MB');
  const bytes = await readFile(filename);
  if (bytes.length > 25_000_000) throw new Error('Offline input exceeds 25 MB');
  return JSON.parse(bytes.toString('utf8'));
}
const json = (value) => JSON.stringify(value, null, 2) + '\n';
async function main() {
  const o = options(process.argv.slice(2));
  if (o.help) { process.stdout.write(help); return; }
  let files;
  if (o.command === 'audit') {
    const input = await jsonFile(o.input);
    const origin = new URL(input.origin);
    if (!/^https?:$/.test(origin.protocol) || origin.origin !== input.origin || origin.username || origin.password) throw new Error('Supply an HTTP(S) origin without path or credentials');
    if (!Array.isArray(input.pages) || !input.pages.length || input.pages.length > 1000) throw new Error('Supply 1 through 1000 HTML pages');
    const seen = new Set();
    const pages = input.pages.map((p) => {
      const url = new URL(p.url);
      if (url.origin !== origin.origin || url.href !== p.url || url.hash || url.username || url.password || seen.has(url.href)) throw new Error('Invalid, duplicate or foreign page URL');
      seen.add(url.href);
      if (typeof p.html !== 'string' || Buffer.byteLength(p.html) > 2_000_000) throw new Error('Each page requires HTML of at most 2 MB');
      return parsePage(p.html, url.href);
    });
    const snapshot = createMetadataSnapshot(pages, { origin: origin.origin, sourceKind: 'supplied', complete: false });
    const report = runAudit(pages, { merchant: o.merchant });
    files = { 'seo-audit.json': json(report), 'seo-audit.md': renderAudit(report), 'metadata-snapshot.json': json(snapshot) };
  } else if (o.command === 'drift') {
    const report = compareMetadataSnapshots(await jsonFile(o.before), await jsonFile(o.after));
    files = { 'seo-drift.json': json(report), 'seo-drift.md': renderMetadataDrift(report) };
  } else {
    const report = clusterSerpOverlap(await jsonFile(o.input), { context: o.context, depth: o.depth === undefined ? 10 : Number(o.depth), threshold: o.threshold === undefined ? 0.3 : Number(o.threshold) });
    files = { 'serp-clusters.json': json(report), 'serp-clusters.md': renderSerpOverlap(report) };
  }
  const destination = await writeOfflineReports(o.out, files, process.cwd());
  process.stdout.write(`No requests or provider calls. Output: ${destination}\n`);
}
main().catch((error) => { process.stderr.write(`${error.message}\n`); process.exitCode = 1; });
