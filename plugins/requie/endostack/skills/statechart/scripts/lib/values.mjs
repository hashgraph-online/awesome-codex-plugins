// TLC value grammar: parse, print back as TLC prints, compute equality keys,
// and convert to the plain JavaScript data a view module receives.
//
// Value shapes:
//   {t:'bool', v}  {t:'int', v}  {t:'str', v}  {t:'mv', v}
//   {t:'set', items}  {t:'tup', items}  {t:'rec', fields:[[name, value]]}
//   {t:'fn', pairs:[[key, value]]}  {t:'iv', lo, hi}

const INT_MAX = 2147483647;
const INT_MIN = -2147483648;

// Copy a string into a fresh allocation so parsed data never keeps the large
// source text alive through a V8 sliced string.
export function detach(s) {
  return s.length === 0 ? '' : Buffer.from(s, 'utf8').toString('utf8');
}

export class ValueError extends Error {}

const STRING_ESCAPES = { '"': '"', '\\': '\\', n: '\n', t: '\t', r: '\r', f: '\f' };

// Tokenizer shared by the value parser and the mark scanner.
export function* valueTokens(text, start = 0) {
  let i = start;
  const n = text.length;
  while (i < n) {
    const c = text[i];
    if (c === ' ' || c === '\t' || c === '\n' || c === '\r') { i++; continue; }
    const at = i;
    if (c === '"') {
      let out = '';
      i++;
      for (;;) {
        if (i >= n) throw new ValueError('unterminated string');
        const d = text[i];
        if (d === '"') { i++; break; }
        if (d === '\n' || d === '\r') throw new ValueError('string spans a line');
        if (d === '\\') {
          const e = STRING_ESCAPES[text[i + 1]];
          if (e === undefined) throw new ValueError(`unknown string escape \\${text[i + 1] ?? ''}`);
          out += e;
          i += 2;
          continue;
        }
        out += d;
        i++;
      }
      yield { k: 'str', v: detach(out), at, end: i };
      continue;
    }
    const two = text.slice(i, i + 2);
    if (two === '<<' || two === '>>' || two === ':>' || two === '@@' || two === '..') {
      yield { k: two, at, end: i + 2 };
      i += 2;
      continue;
    }
    if (text.startsWith('|->', i)) { yield { k: '|->', at, end: i + 3 }; i += 3; continue; }
    if ('{}[](),'.includes(c)) { yield { k: c, at, end: i + 1 }; i++; continue; }
    if (c === '-' && /[0-9]/.test(text[i + 1] ?? '')) {
      let j = i + 1;
      while (j < n && /[0-9]/.test(text[j])) j++;
      yield { k: 'num', v: text.slice(i, j), at, end: j };
      i = j;
      continue;
    }
    if (/[A-Za-z0-9_]/.test(c)) {
      let j = i;
      while (j < n && /[A-Za-z0-9_]/.test(text[j])) j++;
      const w = text.slice(i, j);
      yield { k: /^[0-9]+$/.test(w) ? 'num' : 'word', v: w, at, end: j };
      i = j;
      continue;
    }
    throw new ValueError(`unexpected character ${JSON.stringify(c)}`);
  }
}

class Parser {
  constructor(text) {
    this.toks = [...valueTokens(text)];
    this.i = 0;
  }
  peek() { return this.toks[this.i]; }
  next() {
    const t = this.toks[this.i++];
    if (!t) throw new ValueError('unexpected end of value');
    return t;
  }
  expect(k) {
    const t = this.next();
    if (t.k !== k) throw new ValueError(`expected ${k} but found ${t.v ?? t.k}`);
    return t;
  }
  list(close, item) {
    const out = [];
    if (this.peek()?.k === close) { this.i++; return out; }
    for (;;) {
      out.push(item());
      const t = this.next();
      if (t.k === close) return out;
      if (t.k !== ',') throw new ValueError(`expected , or ${close} but found ${t.v ?? t.k}`);
      if (this.peek()?.k === close) throw new ValueError('trailing comma');
    }
  }
  int(t) {
    const v = Number(t.v);
    if (!Number.isSafeInteger(v) || v > INT_MAX || v < INT_MIN) throw new ValueError(`integer out of range: ${t.v}`);
    return v;
  }
  value() {
    const t = this.next();
    switch (t.k) {
      case 'str': return { t: 'str', v: t.v };
      case 'num': {
        const lo = this.int(t);
        if (this.peek()?.k === '..') {
          this.i++;
          const h = this.next();
          if (h.k !== 'num') throw new ValueError('interval needs an integer upper bound');
          return { t: 'iv', lo, hi: this.int(h) };
        }
        return { t: 'int', v: lo };
      }
      case 'word': {
        if (t.v === 'TRUE') return { t: 'bool', v: true };
        if (t.v === 'FALSE') return { t: 'bool', v: false };
        if (t.v === 'SUBSET' || t.v === 'UNION' || t.v === 'DOMAIN') throw new ValueError(`unsupported operator ${t.v}`);
        return { t: 'mv', v: detach(t.v) };
      }
      case '{': return { t: 'set', items: this.list('}', () => this.value()) };
      case '<<': return { t: 'tup', items: this.list('>>', () => this.value()) };
      case '[': {
        const fields = this.list(']', () => {
          const name = this.next();
          if (name.k !== 'word' && name.k !== 'num') throw new ValueError('record field name expected');
          this.expect('|->');
          return [detach(name.v), this.value()];
        });
        if (fields.length === 0) throw new ValueError('empty record');
        return { t: 'rec', fields };
      }
      case '(': {
        const pairs = [];
        for (;;) {
          const k = this.value();
          this.expect(':>');
          const v = this.value();
          pairs.push([k, v]);
          const s = this.next();
          if (s.k === ')') break;
          if (s.k !== '@@') throw new ValueError(`expected @@ or ) but found ${s.v ?? s.k}`);
        }
        return { t: 'fn', pairs };
      }
      default:
        throw new ValueError(`unexpected ${t.v ?? t.k}`);
    }
  }
}

export function parseValue(text) {
  const p = new Parser(text);
  if (p.toks.length === 0) throw new ValueError('empty value');
  const v = p.value();
  if (p.i !== p.toks.length) throw new ValueError(`unexpected ${p.toks[p.i].v ?? p.toks[p.i].k} after value`);
  return v;
}

export function quoteString(s) {
  let out = '"';
  for (const ch of s) {
    if (ch === '"') out += '\\"';
    else if (ch === '\\') out += '\\\\';
    else if (ch === '\n') out += '\\n';
    else if (ch === '\t') out += '\\t';
    else if (ch === '\r') out += '\\r';
    else if (ch === '\f') out += '\\f';
    else out += ch;
  }
  return out + '"';
}

export function show(v) {
  switch (v.t) {
    case 'bool': return v.v ? 'TRUE' : 'FALSE';
    case 'int': return String(v.v);
    case 'str': return quoteString(v.v);
    case 'mv': return v.v;
    case 'set': return `{${v.items.map(show).join(', ')}}`;
    case 'tup': return `<<${v.items.map(show).join(', ')}>>`;
    case 'rec': return `[${v.fields.map(([f, x]) => `${f} |-> ${show(x)}`).join(', ')}]`;
    case 'fn': return `(${v.pairs.map(([k, x]) => `${show(k)} :> ${show(x)}`).join(' @@ ')})`;
    case 'iv': return `${v.lo}..${v.hi}`;
    default: throw new Error(`unknown value ${v.t}`);
  }
}

const keyCache = new WeakMap();

function setKey(elements) {
  const ints = new Set();
  const others = new Set();
  for (const e of elements) {
    if (e.t === 'int') ints.add(e.v);
    else others.add(key(e));
  }
  const nums = [...ints].sort((a, b) => a - b);
  const runs = [];
  for (let i = 0; i < nums.length;) {
    let j = i;
    while (j + 1 < nums.length && nums[j + 1] === nums[j] + 1) j++;
    runs.push(i === j ? `i${nums[i]}` : `i${nums[i]}~${nums[j]}`);
    i = j + 1;
  }
  return `S{${[...runs, ...[...others].sort()].join(',')}}`;
}

function fnKey(entries) {
  const m = new Map();
  for (const [k, v] of entries) m.set(key(k), key(v));
  return `F{${[...m.keys()].sort().map((k) => `${k}=${m.get(k)}`).join(',')}}`;
}

// Canonical text: two values get the same key exactly when TLC treats them as equal.
export function key(v) {
  let k = keyCache.get(v);
  if (k !== undefined) return k;
  switch (v.t) {
    case 'bool': k = v.v ? 'T' : 'F'; break;
    case 'int': k = `i${v.v}`; break;
    case 'str': k = `s${JSON.stringify(v.v)}`; break;
    case 'mv': k = `m${v.v}`; break;
    case 'set': k = setKey(v.items); break;
    case 'iv': { const xs = []; for (let i = v.lo; i <= v.hi; i++) xs.push({ t: 'int', v: i }); k = setKey(xs); break; }
    case 'tup': k = fnKey(v.items.map((x, i) => [{ t: 'int', v: i + 1 }, x])); break;
    case 'rec': k = fnKey(v.fields.map(([f, x]) => [{ t: 'str', v: f }, x])); break;
    case 'fn': k = fnKey(v.pairs); break;
    default: throw new Error(`unknown value ${v.t}`);
  }
  keyCache.set(v, k);
  return k;
}

function own(obj, k, v) {
  Object.defineProperty(obj, k, { value: v, enumerable: true, writable: true, configurable: true });
}

// The JSON-like form a view module receives.
export function toView(v) {
  switch (v.t) {
    case 'bool': case 'int': case 'str': case 'mv': return v.v;
    case 'set': return v.items.map(toView);
    case 'iv': { const a = []; for (let i = v.lo; i <= v.hi; i++) a.push(i); return a; }
    case 'tup': { const o = {}; v.items.forEach((x, i) => own(o, String(i + 1), toView(x))); return o; }
    case 'rec': { const o = {}; for (const [f, x] of v.fields) own(o, f, toView(x)); return o; }
    case 'fn': {
      const o = {};
      for (const [k, x] of v.pairs) own(o, k.t === 'str' || k.t === 'mv' ? k.v : show(k), toView(x));
      return o;
    }
    default: throw new Error(`unknown value ${v.t}`);
  }
}

// Parse a TLC state printout: "/\ a = 1\n/\ b = 2" or "a = 1" for one variable.
export function parseState(text, variables) {
  const body = text.replace(/\s+$/, '');
  const parts = [];
  if (body.startsWith('/\\ ')) {
    for (const chunk of body.split(/\n(?=\/\\ )/)) parts.push(chunk.slice(3));
  } else if (body !== '') {
    parts.push(body);
  }
  const byName = new Map();
  for (const p of parts) {
    const m = /^([A-Za-z0-9_]+) = /.exec(p);
    if (!m) throw new ValueError(`cannot read state line ${JSON.stringify(p.split('\n')[0])}`);
    byName.set(m[1], parseValue(p.slice(m[0].length)));
  }
  if (!variables) return byName;
  return variables.map((name) => {
    const v = byName.get(name);
    if (v === undefined) throw new ValueError(`state has no value for variable ${name}`);
    return v;
  });
}

export function stateKey(vals) {
  return vals.map(key).join('\u0001');
}
