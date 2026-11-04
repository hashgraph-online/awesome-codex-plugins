// gates.md and standing-orders.md: small Markdown formats a human can read and
// edit, parsed strictly so a hand edit that breaks the shape is caught.

import { UserError } from './errors.mjs';

const FIELDS = ['Status', 'Question', 'Options', 'Default', 'Answer'];

export function parseGates(text, name = 'gates.md') {
  const lines = text.split('\n').map((l) => l.replace(/\r$/, ''));
  const body = lines.filter((l) => l.trim() !== '');
  if (body.length === 0) return [];
  if (body[0] !== '# Gates') throw new UserError(`${name} must start with '# Gates'`);
  const gates = [];
  let cur = null;
  for (const line of body.slice(1)) {
    const h = /^## (.+)$/.exec(line);
    if (h) {
      cur = { id: h[1].trim(), fields: {} };
      if (cur.id === '') throw new UserError(`${name} has a gate with an empty id`);
      if (gates.some((g) => g.id === cur.id)) throw new UserError(`${name} has duplicate gate id '${cur.id}'`);
      gates.push(cur);
      continue;
    }
    const f = /^- (Status|Question|Options|Default|Answer): (.*)$/.exec(line);
    if (!f || !cur) throw new UserError(`${name} has a malformed line: ${line.slice(0, 80)}`);
    if (f[1] in cur.fields) throw new UserError(`${name}: gate '${cur.id}' repeats ${f[1]}`);
    cur.fields[f[1]] = f[2].trim();
  }
  return gates.map(({ id, fields }) => {
    for (const k of ['Status', 'Question', 'Options', 'Default']) {
      if (!(k in fields)) throw new UserError(`${name}: gate '${id}' is missing ${k}`);
    }
    if (fields.Status !== 'open' && fields.Status !== 'resolved') throw new UserError(`${name}: gate '${id}' has bad status '${fields.Status}'`);
    if (fields.Status === 'resolved' && !fields.Answer) throw new UserError(`${name}: gate '${id}' is resolved without an answer`);
    if (fields.Status === 'open' && 'Answer' in fields) throw new UserError(`${name}: open gate '${id}' has an answer`);
    return {
      id,
      status: fields.Status,
      question: fields.Question,
      options: fields.Options,
      default: fields.Default,
      ...(fields.Status === 'resolved' ? { answer: fields.Answer } : {}),
    };
  });
}

export function formatGates(gates) {
  if (gates.length === 0) return '';
  const out = ['# Gates'];
  for (const g of gates) {
    out.push('', `## ${g.id}`, `- Status: ${g.status}`, `- Question: ${g.question}`, `- Options: ${g.options}`, `- Default: ${g.default}`);
    if (g.status === 'resolved') out.push(`- Answer: ${g.answer}`);
  }
  return out.join('\n') + '\n';
}

export function parseStanding(text, name = 'standing-orders.md') {
  const lines = text.split('\n').map((l) => l.replace(/\r$/, '')).filter((l) => l.trim() !== '');
  return lines.map((line, i) => {
    const m = /^([0-9]+)\. (.+)$/.exec(line);
    if (!m || Number(m[1]) !== i + 1) throw new UserError(`${name} line ${i + 1} must read '${i + 1}. <order>'`);
    return m[2];
  });
}

export function formatStanding(lines) {
  return lines.map((l, i) => `${i + 1}. ${l}`).join('\n') + (lines.length ? '\n' : '');
}

export { FIELDS };
