#!/usr/bin/env node
// MiniAPI helper for agents. Node 18+, no packages to install.
// Commands:
//   models                      list models and starting prices (public, no key)
//   model <id>                  one model's settings and prices (public, no key)
//   balance                     your balance (needs MINIAPI_KEY)
//   quote <id> '<json>'         the price of one job, free, nothing runs
//   run <id> '<json>' [--yes] [--out <folder>]
//                               quote, then submit only with --yes, wait, download the file
//   status <id> <request_id>    the state of one job
//
// The agent must show the quoted price to the user and get a yes before passing --yes.

import { writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';

const BASE = (process.env.MINIAPI_BASE_URL || 'https://api.minicut.ai').replace(/\/$/, '');
const KEY = process.env.MINIAPI_KEY || '';
const UA = 'miniapi-skill/1.0';
const SIGNUP = 'https://api.minicut.ai/console/keys?utm_source=skills-sh&utm_medium=skill&utm_campaign=miniapi-video';

function die(msg, code = 1) { console.error(msg); process.exit(code); }

function headers(withKey) {
  const h = { 'User-Agent': UA, 'Content-Type': 'application/json' };
  if (withKey) {
    if (!KEY) die(`MINIAPI_KEY is not set. Create a key at ${SIGNUP}, add funds ($10 minimum), then: export MINIAPI_KEY=mapi_live_...`, 3);
    h.Authorization = `Key ${KEY}`;
  }
  return h;
}

async function call(method, path, { body, key = true, text = false } = {}) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  const res = await fetch(url, { method, headers: headers(key), body: body ? JSON.stringify(body) : undefined });
  const raw = await res.text();
  if (!res.ok) {
    let code = '', message = raw.slice(0, 300);
    try { const j = JSON.parse(raw); code = j?.error?.code || ''; message = j?.error?.message || message; } catch {}
    if (res.status === 402) die(`Not enough balance for this job (${code}). Add funds: ${BASE}/console/billing/add?amount=10`, 4);
    die(`MiniAPI ${res.status} ${code}: ${message}`, 5);
  }
  return text ? raw : JSON.parse(raw);
}

function parseBody(s) {
  if (!s) die('Missing the JSON body, for example: \'{"prompt":"a red fox runs through snow","duration":5}\'');
  try { return JSON.parse(s); } catch { die('The body is not valid JSON.'); }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function download(result, outDir) {
  const files = [result.video, result.audio, ...(result.images || []), result.model_mesh].filter(Boolean);
  if (!files.length) { console.log(JSON.stringify(result, null, 2)); return []; }
  await mkdir(outDir, { recursive: true });
  const saved = [];
  for (const f of files) {
    const res = await fetch(f.url);
    if (!res.ok) die(`Could not download ${f.url}: ${res.status}`);
    const p = join(outDir, f.file_name || `miniapi-${Date.now()}`);
    await writeFile(p, Buffer.from(await res.arrayBuffer()));
    saved.push(p);
  }
  return saved;
}

const [cmd, ...args] = process.argv.slice(2);
const flag = (name) => args.includes(name);
const flagValue = (name) => { const i = args.indexOf(name); return i >= 0 ? args[i + 1] : undefined; };

switch (cmd) {
  case 'models': {
    const txt = await call('GET', '/llms.txt', { key: false, text: true });
    const lines = txt.split('\n').filter((l) => /\/models\/[^)]+\.md\)/.test(l));
    for (const l of lines) {
      const m = l.match(/\[([^\]]+)\]\([^)]*\/models\/([^)]+)\.md\):\s*(.*)$/);
      if (m) console.log(`${m[2]}\t${m[1]}\t${m[3]}`);
    }
    break;
  }
  case 'model': {
    const id = args[0] || die('Usage: model <id>');
    const res = await fetch(`${BASE}/models/${encodeURIComponent(id)}.md`, { headers: { 'User-Agent': UA } });
    if (res.ok) { console.log(await res.text()); break; }
    // The model page did not load: fall back to the list line and the reference, so the agent can still build a body.
    const txt = await call('GET', '/llms.txt', { key: false, text: true });
    const line = txt.split('\n').find((l) => l.includes(`/models/${id}.md`));
    console.log(`Model page did not load (${res.status}). ${line ? line.trim() : `No model with id ${id}.`}`);
    console.log(`Parameters for every model: ${BASE}/docs/api . Prices: ${BASE}/pricing`);
    break;
  }
  case 'balance': {
    console.log(JSON.stringify(await call('GET', '/v1/balance'), null, 2));
    break;
  }
  case 'quote': {
    const id = args[0] || die('Usage: quote <id> <json>');
    const q = await call('POST', `/v1/quote/${encodeURIComponent(id)}`, { body: parseBody(args[1]) });
    console.log(`PRICE ${q.price} ${q.currency} for ${q.quantity} ${q.unit} on ${q.model_id} (${q.tier}). Quote is free. Nothing ran.`);
    break;
  }
  case 'status': {
    const [id, rid] = args;
    if (!id || !rid) die('Usage: status <id> <request_id>');
    console.log(JSON.stringify(await call('GET', `/v1/queue/${encodeURIComponent(id)}/requests/${rid}/status`), null, 2));
    break;
  }
  case 'run': {
    const id = args[0] || die('Usage: run <id> <json> --yes');
    const body = parseBody(args[1]);
    const q = await call('POST', `/v1/quote/${encodeURIComponent(id)}`, { body });
    console.log(`PRICE ${q.price} ${q.currency} for ${q.quantity} ${q.unit} on ${q.model_id} (${q.tier}).`);
    if (!flag('--yes')) {
      console.log('Not submitted. Show this price to the user. Run again with --yes only after they say yes.');
      process.exit(2);
    }
    const job = await call('POST', `/v1/queue/${encodeURIComponent(id)}`, { body });
    console.log(`SUBMITTED ${job.request_id}, held ${job.price} ${job.currency}. Failed jobs are not charged.`);
    let s;
    const started = Date.now();
    do {
      await sleep(4000);
      s = await call('GET', job.status_url);
      process.stdout.write(`\r${s.status} ${Math.round((Date.now() - started) / 1000)}s   `);
    } while (s.status !== 'COMPLETED' && Date.now() - started < 30 * 60 * 1000);
    process.stdout.write('\n');
    if (s.status !== 'COMPLETED') die(`Still ${s.status} after 30 minutes. Check later: status ${id} ${job.request_id}`, 6);
    if (s.state !== 'completed') die(`Job ended ${s.state}${s.error ? `: ${s.error.code} ${s.error.message || ''}` : ''}. You were not charged.`, 7);
    const result = await call('GET', job.response_url);
    const saved = await download(result, flagValue('--out') || 'miniapi-output');
    for (const p of saved) console.log(`SAVED ${p}`);
    if (result.billing) console.log(`CHARGED ${result.billing.price} ${result.billing.currency}`);
    break;
  }
  default:
    console.log('Commands: models | model <id> | balance | quote <id> <json> | run <id> <json> [--yes] [--out dir] | status <id> <request_id>');
}
