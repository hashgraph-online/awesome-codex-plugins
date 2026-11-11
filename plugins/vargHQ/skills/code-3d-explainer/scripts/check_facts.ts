#!/usr/bin/env bun
// check_facts.ts: every word on screen must come from the approved fact sheet.
//
//   bun scripts/check_facts.ts <factsheet.md> <labels.json>
//
// Reads the "On-screen claims" table of the fact sheet (columns: ID | Part | On screen | Claim | Source) and the
// per-frame text that capture.ts --labels recorded from the real render. Then:
//   FAIL  a text was shown that is not in the "On screen" column, word for word (whitespace-normalised)
//   FAIL  a shown claim has no source (a "—" source is allowed only for titles marked "(title, no claim)")
//   FAIL  the sheet is not approved: no "Status: **approved" line, or the Critic log has no VERDICT: PASS...
//   WARN  a row of the sheet never appeared on screen (dead row, or a label that never rendered)
// Rows whose "On screen" cell is a pattern in backticks with <n> (e.g. `<n> µm`) match any number there:
// that is how a computed scale bar is declared.
import { readFile } from 'node:fs/promises';

const [sheetPath, labelsPath] = Bun.argv.slice(2);
if (!sheetPath || !labelsPath) { console.log('usage: bun scripts/check_facts.ts <factsheet.md> <labels.json>'); process.exit(1); }
const md = await readFile(sheetPath, 'utf8');
const L = JSON.parse(await readFile(labelsPath, 'utf8'));
const norm = (s: string) => s.replace(/\s+/g, ' ').trim();

// parse the On-screen claims table
const sec = md.split(/^## /m).find(s => /^On-screen claims/i.test(s));
if (!sec) { console.log('FAIL  no "## On-screen claims" section in the fact sheet'); process.exit(1); }
const rows = sec.split('\n').filter(l => /^\|/.test(l) && !/^\|\s*-/.test(l)).slice(1).map(l => l.split('|').slice(1, -1).map(c => c.trim()));
type Row = { id: string; screen: string; claim: string; source: string; re?: RegExp };
const sheet: Row[] = rows.filter(r => r.length >= 5).map(([id, , screen, claim, source]) => {
  const pats = [...screen.matchAll(/`([^`]+)`/g)].map(m => m[1]).filter(p => p.includes('<n>'));
  const re = pats.length ? new RegExp('^(' + pats.map(p => p.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace('<n>', '\\d+(?:\\.\\d+)?')).join('|') + ')$') : undefined;
  return { id, screen: norm(screen), claim, source, re };
});

const shown = new Map<string, { first: number; id: string }>();
for (const f of L.frames) for (const it of f?.items || []) if (it.opacity >= 0.05) for (const t of [...it.text, ...(it.ui || [])]) { const k = norm(t); if (!shown.has(k)) shown.set(k, { first: f.t, id: it.id }); }

let fail = 0; const used = new Set<string>();
for (const [text, { first, id }] of shown) {
  const row = sheet.find(r => r.screen === text) || sheet.find(r => r.re?.test(text));
  if (!row) { fail++; console.log(`FAIL  not in the fact sheet: "${text}" (${id}, first at ${first.toFixed(2)} s)`); continue; }
  used.add(row.id);
  const noSource = !row.source || /^[—-]$/.test(row.source);
  if (noSource && !/no claim/i.test(row.claim)) { fail++; console.log(`FAIL  ${row.id} "${text}" has no source`); }
}
for (const r of sheet) if (!used.has(r.id)) console.log(`WARN  ${r.id} never on screen: "${r.screen}"`);
const approved = /Status:\s*\*\*approved/i.test(md);
const verdict = (md.split(/^## Critic log/m)[1] || '').match(/VERDICT:\s*([A-Z ]+)/);
if (!approved) { fail++; console.log('FAIL  the sheet has no "Status: **approved" line'); }
if (!verdict || !/^PASS/.test(verdict[1].trim())) { fail++; console.log(`FAIL  the critic log has no passing VERDICT (found: ${verdict ? verdict[1].trim() : 'none'})`); }
console.log(`${shown.size} distinct on-screen texts, ${sheet.length} sheet rows, critic: ${verdict ? verdict[1].trim() : 'none'}: ${fail ? `${fail} FAIL` : 'all on-screen text is sourced and approved'}`);
process.exit(fail ? 1 : 0);
