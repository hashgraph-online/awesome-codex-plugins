// Reads the state graph TLC dumps with `-dump dot,actionlabels`.
// Returns { states: Map<id, {id, text, initial}>, edges: [{from, to, action}] }.
// Strings are detached from the input so the parsed graph does not keep the
// (possibly very large) DOT text alive.

import { detach } from './values.mjs';

function unescapeDot(s) {
  let out = '';
  for (let i = 0; i < s.length; i++) {
    const c = s[i];
    if (c === '\\' && i + 1 < s.length) {
      const d = s[++i];
      if (d === 'n') out += '\n';
      else out += d;
    } else out += c;
  }
  return out;
}

function readQuoted(line, from) {
  let i = from;
  let raw = '';
  while (i < line.length) {
    const c = line[i];
    if (c === '\\') { raw += c + (line[i + 1] ?? ''); i += 2; continue; }
    if (c === '"') return { value: unescapeDot(raw), end: i + 1 };
    raw += c;
    i++;
  }
  throw new Error('The DOT dump has an unterminated label.');
}

function attrs(line, from) {
  const out = {};
  let i = line.indexOf('[', from);
  if (i < 0) return out;
  i++;
  while (i < line.length) {
    while (line[i] === ' ' || line[i] === ',') i++;
    if (line[i] === ']' || i >= line.length) break;
    const eq = line.indexOf('=', i);
    if (eq < 0) break;
    const name = line.slice(i, eq).trim();
    i = eq + 1;
    while (line[i] === ' ') i++;
    if (line[i] === '"') {
      const q = readQuoted(line, i + 1);
      out[name] = q.value;
      i = q.end;
    } else {
      let j = i;
      while (j < line.length && line[j] !== ',' && line[j] !== ']') j++;
      out[name] = line.slice(i, j).trim();
      i = j;
    }
  }
  return out;
}

const NODE_RE = /^(-?\d+) \[/;
const EDGE_RE = /^(-?\d+) -> (-?\d+)(?: \[|;|$)/;

export function parseDot(text) {
  const states = new Map();
  const edges = [];
  let inLegend = false;
  let pos = 0;
  while (pos < text.length) {
    let nl = text.indexOf('\n', pos);
    if (nl < 0) nl = text.length;
    const line = text.slice(pos, nl).trim();
    pos = nl + 1;
    if (line.startsWith('subgraph cluster_legend')) { inLegend = true; continue; }
    if (inLegend || line === '') continue;
    const e = EDGE_RE.exec(line);
    if (e) {
      const a = attrs(line, e[0].length - 1);
      if (a.style === 'dashed' && a.label === undefined) continue; // stuttering self-loop
      edges.push({ from: detach(e[1]), to: detach(e[2]), action: a.label === undefined ? null : detach(a.label) });
      continue;
    }
    const n = NODE_RE.exec(line);
    if (n) {
      const a = attrs(line, n[0].length - 1);
      states.set(detach(n[1]), { id: detach(n[1]), text: detach(a.label ?? ''), initial: (a.style ?? '').includes('filled') });
    }
  }
  for (const e of edges) {
    if (!states.has(e.from) || !states.has(e.to)) {
      throw new Error(`The DOT dump has a step ${e.from} -> ${e.to} to or from a state it never lists.`);
    }
  }
  return { states, edges };
}
