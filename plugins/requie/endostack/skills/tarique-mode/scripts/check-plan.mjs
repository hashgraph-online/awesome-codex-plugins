#!/usr/bin/env node
// check-plan: lints a endostack program plan against PLAN-FORMAT.md.
// Invoke as: node check-plan.mjs path/to/plan.md
// Exits 0 on a clean plan, 1 when it finds problems, 2 on bad arguments or an unreadable file.
// The format is defined only in PLAN-FORMAT.md; edit that file and this one in the same commit.

import { readFileSync, realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

export const RULE =
  'Green tests by themselves do not prove a PR. A PR counts as proven once every unit, live, and perf box under it is checked.';

export const HOW_TO_READ = 'Reading this plan';
export const CHECKLIST = 'Run checklist';
export const CLOSE = 'Finish the run';
export const APPENDIX = 'Appendix';
export const PROTOTYPE_APPENDIX = 'Experiment results';

export const READ_PHRASES = [
  'each box is a single task',
  'each box cites its proof',
  'tick a box only once its proof exists',
];
export const PLAYBOOK_POINTER = /`[^`]*playbooks\/[^`\s]+\.md`/;

export const CHECKLIST_H3 = ['Start the run', 'Assign owners', 'Branch and PR rules', 'Verification and landing', 'Lane setup'];
export const CHECKLIST_MARKERS = ['`git show origin/main:', 'hourly audit loop', 'status message'];

export const LEADS = [
  ['needs', 'Needs.'],
  ['touches', 'Touches.'],
  ['changes', 'Changes.'],
  ['result', 'Observable result.'],
  ['unit', 'Unit proof.'],
  ['live', 'Live proof.'],
  ['perf', 'Perf proof.'],
  ['review', 'Operator review.'],
  ['land', 'Landing.'],
];
const NEEDS_BOX = ['touches', 'changes', 'result', 'unit', 'land'];
const PROOF_BLOCKS = ['unit', 'live', 'perf'];
const PERF_WORDS = ['Metric.', 'Probe.', 'Baseline.', 'Budget.'];
const REVIEW_WORDS = ['screenshot', 'video', 'operator'];
const LANE_LINE = /Ten lanes run on `([^`]+)` against the PR head\./;
const BOX = /^\s*[-*] \[( |x|X)\] (.*)$/;

// ---------- line classification ----------

function openFence(line) {
  const m = /^ {0,3}(`{3,}|~{3,})(.*)$/.exec(line);
  if (!m) return null;
  const ch = m[1][0];
  if (ch === '`' && m[2].includes('`')) return null;
  return { ch, len: m[1].length };
}

function closesFence(line, fence) {
  const m = /^ {0,3}(`{3,}|~{3,})[ \t]*$/.exec(line);
  return !!m && m[1][0] === fence.ch && m[1].length >= fence.len;
}

// Returns [{ no, text, code }] for every line after front matter.
export function classify(lines) {
  const out = [];
  let start = 0;
  if (lines[0] === '---') {
    const end = lines.indexOf('---', 1);
    start = end === -1 ? lines.length : end + 1;
  }
  let fence = null;
  for (let i = start; i < lines.length; i++) {
    const text = lines[i];
    if (fence) {
      out.push({ no: i + 1, text, code: true });
      if (closesFence(text, fence)) fence = null;
      continue;
    }
    const f = openFence(text);
    if (f) {
      fence = f;
      out.push({ no: i + 1, text, code: true });
      continue;
    }
    out.push({ no: i + 1, text, code: false });
  }
  return out;
}

// ---------- prose rules ----------

// Remove inline code spans. A run of N backticks closes only on the next run of exactly N.
// An unmatched run stays as literal text and scanning continues after it.
export function stripCodeSpans(s) {
  let out = '';
  let i = 0;
  while (i < s.length) {
    if (s[i] !== '`') {
      out += s[i++];
      continue;
    }
    let j = i;
    while (s[j] === '`') j++;
    const n = j - i;
    let k = j;
    let close = -1;
    while (k < s.length) {
      if (s[k] !== '`') {
        k++;
        continue;
      }
      let e = k;
      while (s[e] === '`') e++;
      if (e - k === n) {
        close = k;
        break;
      }
      k = e;
    }
    if (close === -1) {
      out += s.slice(i, j);
      i = j;
    } else {
      out += ' ';
      i = close + n;
    }
  }
  return out;
}

export function proseText(line) {
  let s = stripCodeSpans(line);
  s = s.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ');
  s = s.replace(/\]\([^)]*\)/g, ']');
  s = s.replace(/<[a-z][a-z0-9+.-]*:[^>\s]*>/gi, ' ');
  return s;
}

const PROSE_RULES = [
  [/[\u2013\u2014]/, 'long dash'],
  [/[\u2018\u2019\u201C\u201D]/, 'curly quote'],
  [/: \S/, 'mid-sentence colon'],
];

// ---------- structure helpers ----------

function headingsOf(rows, level) {
  const prefix = '#'.repeat(level) + ' ';
  return rows
    .map((r, idx) => ({ ...r, idx }))
    .filter((r) => !r.code && r.text.startsWith(prefix))
    .map((r) => ({ no: r.no, idx: r.idx, title: r.text.slice(prefix.length).trim() }));
}

function flat(rows) {
  return rows
    .filter((r) => !r.code)
    .map((r) => r.text)
    .join(' ')
    .replace(/\s+/g, ' ');
}

function leadAt(text) {
  for (const [key, label] of LEADS) {
    const bold = `**${label}**`;
    if (text.startsWith(bold)) return { key, rest: text.slice(bold.length).trim() };
  }
  return null;
}

// Collect checkbox items. Indented non-box lines that follow a box continue it.
function boxesIn(rows) {
  const items = [];
  let cur = null;
  for (const r of rows) {
    if (r.code) continue;
    const m = BOX.exec(r.text);
    if (m) {
      cur = { no: r.no, text: m[2], indent: r.text.search(/\S/) };
      items.push(cur);
    } else if (cur && r.text.trim() && r.text.search(/\S/) > cur.indent) {
      cur.text += ' ' + r.text.trim();
    } else {
      cur = null;
    }
  }
  return items;
}

// ---------- PR section ----------

function checkPr(sec, rows, report) {
  const body = rows.slice(sec.idx + 1, sec.end);
  const found = [];
  body.forEach((r, i) => {
    if (r.code) return;
    const l = leadAt(r.text);
    if (l) found.push({ ...l, no: r.no, i });
  });
  const counts = Object.fromEntries(LEADS.map(([k]) => [k, 0]));
  let total = boxesIn(body).length;

  const firstLead = found.length ? found[0].i : body.length;
  for (const b of boxesIn(body.slice(0, firstLead))) report(b.no, 'checkbox before the first sub-block');

  const order = found.map((f) => f.key).join(',');
  const want = LEADS.map(([k]) => k).join(',');
  if (order !== want) {
    const names = found.map((f) => LEADS.find(([k]) => k === f.key)[1]).join(' ');
    report(sec.no, `PR section must hold the nine bold labels in order (${LEADS.map((l) => l[1]).join(' ')}); found ${names || 'none'}`);
    return { counts, total };
  }

  found.forEach((f, n) => {
    const end = n + 1 < found.length ? found[n + 1].i : body.length;
    const block = body.slice(f.i + 1, end);
    const boxes = boxesIn(block);
    counts[f.key] = boxes.length;
    const label = LEADS.find(([k]) => k === f.key)[1];

    if (f.key === 'needs' && !f.rest) report(f.no, 'Needs. requires a PR id or "none" after the label');
    if (NEEDS_BOX.includes(f.key) && boxes.length === 0) report(f.no, `${label} needs at least one checkbox`);
    if (PROOF_BLOCKS.includes(f.key) && !f.rest.startsWith(RULE)) {
      report(f.no, `${label} must open with the proof rule sentence`);
    }

    if (f.key === 'live') {
      const lanes = LANE_LINE.exec(f.rest);
      if (!lanes) report(f.no, 'Live proof must say "Ten lanes run on `<model>` against the PR head." on its label line');
      else if (/[<>]|^(model|tbd|todo|\?)$/i.test(lanes[1].trim())) {
        report(f.no, `Live proof names a placeholder model \`${lanes[1]}\``);
      }
      let next = 1;
      for (const b of boxes) {
        const m = /^Lane (\d+)\.\s/.exec(b.text);
        if (!m) {
          report(b.no, 'Live proof accepts lane boxes only ("Lane N. ...")');
          continue;
        }
        if (Number(m[1]) !== next) report(b.no, `expected Lane ${next}, found Lane ${m[1]}`);
        next = Number(m[1]) + 1;
        if (!/Save `[^`]+`/.test(b.text)) report(b.no, `Lane ${m[1]} must name a screenshot to save (Save \`file.png\`)`);
        if (!/Pass when\b/.test(b.text)) report(b.no, `Lane ${m[1]} must state a pass predicate ("Pass when ...")`);
      }
      const laneCount = boxes.filter((b) => /^Lane \d+\.\s/.test(b.text)).length;
      if (laneCount !== 10) report(f.no, `Live proof needs exactly 10 lanes, found ${laneCount}`);
    }

    if (f.key === 'perf') {
      if (boxes.length !== 4) report(f.no, `Perf proof needs exactly 4 boxes, found ${boxes.length}`);
      boxes.slice(0, 4).forEach((b, k) => {
        if (!b.text.startsWith(PERF_WORDS[k] + ' ') && b.text !== PERF_WORDS[k]) {
          report(b.no, `Perf proof box ${k + 1} must start with "${PERF_WORDS[k]}"`);
        }
      });
    }

    if (f.key === 'review') {
      if (f.rest.startsWith('None.')) {
        if (boxes.length) report(f.no, 'Operator review says "None." but has checkboxes');
      } else {
        if (!boxes.length) report(f.no, 'Operator review needs checkboxes, or "None." after the label');
        const blockText = `${f.rest} ${flat(block)}`.toLowerCase();
        const absent = REVIEW_WORDS.filter((w) => !blockText.includes(w));
        absent.forEach((w) => report(f.no, `Operator review must mention ${w}`));
      }
    }
  });
  return { counts, total };
}

// ---------- whole plan ----------

export function checkPlan(source) {
  const lines = source.split(/\r?\n/);
  const rows = classify(lines);
  const problems = [];
  const report = (line, message) => problems.push({ line, message });

  for (const r of rows) {
    if (r.code) continue;
    const prose = proseText(r.text);
    for (const [re, msg] of PROSE_RULES) if (re.test(prose)) report(r.no, msg);
  }

  const h1 = headingsOf(rows, 1);
  const h2 = headingsOf(rows, 2);
  h2.forEach((h, n) => (h.end = n + 1 < h2.length ? h2[n + 1].idx : rows.length));
  const prs = [];

  if (!h1.length) report(1, 'missing H1 title');

  const readIdx = h2.findIndex((h) => h.title.startsWith(HOW_TO_READ));
  const listIdx = h2.findIndex((h) => h.title.startsWith(CHECKLIST));
  const closeIdx = h2.findIndex((h) => h.title.startsWith(CLOSE));

  if (readIdx === -1) report(1, `missing "## ${HOW_TO_READ} ..." section`);
  else {
    const read = h2[readIdx];
    if (h1.length) {
      const intro = rows.slice(h1[0].idx + 1, read.idx).filter((r) => r.text.trim()).length;
      if (h1[0].idx > read.idx) report(read.no, 'H1 must come before the reading section');
      else if (intro >= 10) report(read.no, `intro has ${intro} non-blank lines; keep it under 10`);
    }
    const text = flat(rows.slice(read.idx + 1, read.end));
    const lower = text.toLowerCase();
    for (const p of READ_PHRASES) if (!lower.includes(p)) report(read.no, `reading section must say "${p}"`);
    if (!PLAYBOOK_POINTER.test(text)) report(read.no, 'reading section must point to a playbook (`playbooks/<name>.md`)');
    if (!text.includes(RULE)) report(read.no, 'reading section must contain the proof rule sentence');
  }

  if (listIdx === -1) report(1, `missing "## ${CHECKLIST}" section`);
  else {
    const list = h2[listIdx];
    if (readIdx !== -1 && listIdx !== readIdx + 1) report(list.no, `"${CHECKLIST}" must directly follow the reading section`);
    const body = rows.slice(list.idx + 1, list.end);
    const h3 = headingsOf(body, 3);
    const titles = h3.map((h) => h.title);
    const ok = titles.length === CHECKLIST_H3.length && CHECKLIST_H3.every((p, k) => titles[k].startsWith(p));
    if (!ok) report(list.no, `"${CHECKLIST}" needs exactly these H3s in order (${CHECKLIST_H3.join(', ')})`);
    const text = flat(body);
    for (const m of CHECKLIST_MARKERS) if (!text.includes(m)) report(list.no, `"${CHECKLIST}" must mention ${m}`);
  }

  if (closeIdx === -1) report(1, `missing "## ${CLOSE}" section`);

  if (listIdx !== -1 && closeIdx !== -1) {
    if (closeIdx < listIdx) report(h2[closeIdx].no, `"${CLOSE}" must come after "${CHECKLIST}"`);
    for (let k = listIdx + 1; k < closeIdx; k++) prs.push(h2[k]);
    if (!prs.length) report(h2[closeIdx].no, `no PR sections between "${CHECKLIST}" and "${CLOSE}"`);
  }

  const first = Math.min(...[readIdx, listIdx, closeIdx].filter((n) => n !== -1), h2.length);
  for (let k = 0; k < first; k++) report(h2[k].no, `unexpected section "${h2[k].title}" before "${HOW_TO_READ}"`);
  if (readIdx !== -1 && listIdx > readIdx + 1) {
    for (let k = readIdx + 1; k < listIdx; k++) report(h2[k].no, `unexpected section "${h2[k].title}"`);
  }

  if (closeIdx !== -1) {
    const after = h2.slice(closeIdx + 1);
    for (const h of after) if (!h.title.startsWith(APPENDIX)) report(h.no, `section after "${CLOSE}" is not an appendix`);
    if (!after.some((h) => h.title.startsWith(APPENDIX) && h.title.includes(PROTOTYPE_APPENDIX))) {
      report(h2[closeIdx].no, `missing "## ${APPENDIX} ... ${PROTOTYPE_APPENDIX}" section`);
    }
  }

  const summaries = prs.map((sec) => ({ title: sec.title, no: sec.no, ...checkPr(sec, rows, report) }));
  problems.sort((a, b) => a.line - b.line);
  return { summaries, problems };
}

export function main(argv, io = { out: console.log, err: console.error }) {
  if (argv.length !== 1) {
    io.err('check-plan expects exactly one argument, the plan file (node check-plan.mjs path/to/plan.md)');
    return 2;
  }
  const file = argv[0];
  let source;
  try {
    source = readFileSync(file, 'utf8');
  } catch (e) {
    io.err(`${file}: cannot read (${e.code || e.message})`);
    return 2;
  }
  const { summaries, problems } = checkPlan(source);
  for (const s of summaries) {
    const parts = LEADS.map(([k]) => `${k}=${s.counts[k]}`).join(' ');
    io.out(`${s.title}\tboxes=${s.total} ${parts}`);
  }
  io.out(`checked ${summaries.length} PR sections; found ${problems.length} problems`);
  problems.forEach(({ line, message }) => io.err(`${file}:${line}: ${message}`));
  return problems.length > 0 ? 1 : 0;
}

function isEntry() {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isEntry()) process.exitCode = main(process.argv.slice(2));
