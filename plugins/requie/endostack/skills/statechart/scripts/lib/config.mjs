// Reads a TLC model config the way TLC does, refusing anything TLC would
// reject or might read differently from how it looks.

export class ConfigError extends Error {}

const LIST_KEYWORDS = new Map([
  ['INVARIANT', 'INVARIANT'], ['INVARIANTS', 'INVARIANT'],
  ['PROPERTY', 'PROPERTY'], ['PROPERTIES', 'PROPERTY'],
  ['CONSTRAINT', 'CONSTRAINT'], ['CONSTRAINTS', 'CONSTRAINT'],
  ['ACTION_CONSTRAINT', 'ACTION_CONSTRAINT'], ['ACTION_CONSTRAINTS', 'ACTION_CONSTRAINT'],
]);
const SINGLE_KEYWORDS = new Set(['INIT', 'NEXT', 'SPECIFICATION', 'VIEW', 'SYMMETRY', 'TYPE', 'TYPE_CONSTRAINT']);
const CONSTANT_KEYWORDS = new Set(['CONSTANT', 'CONSTANTS']);
const UNSUPPORTED_KEYWORDS = new Set(['ALIAS', 'POSTCONDITION']);
export const KEYWORDS = new Set([...LIST_KEYWORDS.keys(), ...SINGLE_KEYWORDS, ...CONSTANT_KEYWORDS, 'CHECK_DEADLOCK']);

const INT_MAX = 2147483647;
const STRING_ESCAPES = new Set(['"', '\\', 'n', 't', 'r', 'f']);

function codePoint(ch) {
  return `U+${ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`;
}

function describeChar(ch) {
  const cp = ch.codePointAt(0);
  if (cp < 0x20 || (cp >= 0x7f && cp < 0xa0)) return codePoint(ch);
  return `"${ch}" (${codePoint(ch)})`;
}

function tokenize(text, file) {
  const refuse = (line, msg) => new ConfigError(`The command cannot read the config ${file} at line ${line}: ${msg}`);
  const tlcRefuses = (line, msg) => new ConfigError(`TLC refuses the config ${file} at line ${line}: ${msg}`);
  if (text.charCodeAt(0) === 0xfeff) {
    throw refuse(1, 'it starts with a byte order mark. Save it as UTF-8 without a BOM.');
  }
  const toks = [];
  let i = 0;
  let line = 1;
  const n = text.length;
  const newline = () => {
    if (text[i] === '\r' && text[i + 1] === '\n') i += 2; else i += 1;
    line++;
  };
  while (i < n) {
    const c = text[i];
    if (c === '\n' || c === '\r') { newline(); continue; }
    if (c === ' ' || c === '\t') { i++; continue; }
    if (c === '\\' && text[i + 1] === '*') {
      while (i < n && text[i] !== '\n' && text[i] !== '\r') i++;
      continue;
    }
    if (c === '(' && text[i + 1] === '*') {
      const startLine = line;
      let depth = 0;
      for (;;) {
        if (i >= n) throw refuse(startLine, 'a comment that starts here with (* is never closed with *).');
        if (text[i] === '(' && text[i + 1] === '*') { depth++; i += 2; continue; }
        if (text[i] === '*' && text[i + 1] === ')') { depth--; i += 2; if (depth === 0) break; continue; }
        if (text[i] === '\n' || text[i] === '\r') { newline(); continue; }
        i++;
      }
      continue;
    }
    const at = line;
    if (c === '"') {
      let j = i + 1;
      for (;;) {
        if (j >= n || text[j] === '\n' || text[j] === '\r') throw refuse(at, 'a string is not closed on the line where it starts.');
        if (text[j] === '\0') throw refuse(at, 'a string contains a NUL character.');
        if (text[j] === '\\') {
          if (!STRING_ESCAPES.has(text[j + 1])) {
            throw refuse(at, `a string uses the escape \\${text[j + 1] ?? ''}; only \\" \\\\ \\n \\t \\r \\f are allowed.`);
          }
          j += 2;
          continue;
        }
        if (text[j] === '"') break;
        j++;
      }
      toks.push({ k: 'str', raw: text.slice(i, j + 1), line: at });
      i = j + 1;
      continue;
    }
    if (/[A-Za-z0-9_]/.test(c)) {
      let j = i;
      while (j < n && /[A-Za-z0-9_]/.test(text[j])) j++;
      const w = text.slice(i, j);
      i = j;
      if (/^(WF|SF)_/.test(w)) throw tlcRefuses(at, `the word ${w} starts with ${w.slice(0, 3)}, which TLC reads as a fairness keyword.`);
      if (/[A-Za-z]/.test(w)) { toks.push({ k: KEYWORDS.has(w) || UNSUPPORTED_KEYWORDS.has(w) ? 'kw' : 'name', raw: w, line: at }); continue; }
      if (w === '_') { toks.push({ k: 'name', raw: w, line: at }); continue; }
      if (/^[0-9]+$/.test(w)) {
        if (Number(w) > INT_MAX) throw tlcRefuses(at, `the number ${w} is larger than 2147483647, the largest integer TLC reads.`);
        toks.push({ k: 'num', raw: w, line: at });
        continue;
      }
      throw refuse(at, `the word ${w} mixes digits and underscores with no letter; TLC would split it into a number and a name.`);
    }
    const two = text.slice(i, i + 2);
    if (two === '<-') { toks.push({ k: '<-', raw: two, line: at }); i += 2; continue; }
    if (['[]', ']_', '==', '=<', '!!'].includes(two)) throw refuse(at, `the TLA+ symbol ${two} does not belong in a config.`);
    if ('{}()[],=!'.includes(c)) { toks.push({ k: c, raw: c, line: at }); i++; continue; }
    const ch = String.fromCodePoint(text.codePointAt(i));
    throw refuse(at, `the character ${describeChar(ch)} is not allowed in a config.`);
  }
  return toks;
}

// Parse config text. Returns
//   { invariants, properties, checkDeadlock, sections:[{keyword, tokens}], constraints,
//     actionConstraints, hasView, hasSymmetry, substitutions: Map, written: string }
export function parseConfig(text, file = 'config') {
  const toks = tokenize(text, file);
  const cannot = (line, msg) => new ConfigError(`The command cannot read the config ${file} at line ${line}: ${msg}`);
  const tlcRefuses = (line, msg) => new ConfigError(`TLC refuses the config ${file}${line ? ` at line ${line}` : ''}: ${msg}`);
  let deferred = null;
  const defer = (err) => { if (!deferred) deferred = err; };

  const out = {
    invariants: [], properties: [], checkDeadlock: true, sections: [],
    constraints: [], actionConstraints: [], substitutions: new Map(),
    init: null, next: null, specification: null, hasView: false, hasSymmetry: false,
  };
  const seenSingle = new Set();
  let seenDeadlock = false;
  let i = 0;
  const peek = () => toks[i];
  const isName = (t) => t && t.k === 'name';

  if (toks.length === 0) throw tlcRefuses(null, 'it is empty; TLC needs INIT and NEXT or SPECIFICATION.');
  if (toks[0].k !== 'kw') throw tlcRefuses(toks[0].line, `expecting a keyword such as INIT, NEXT, SPECIFICATION, CONSTANTS, INVARIANT or PROPERTY, but found ${toks[0].raw}.`);

  const readValue = (kwLine) => {
    const t = toks[i];
    if (!t) throw cannot(kwLine, 'the config ends where a value belongs.');
    if (t.k === 'name' || t.k === 'num' || t.k === 'str') { i++; return [t.raw]; }
    if (t.k === 'kw') throw cannot(t.line, `the keyword ${t.raw} stands where a value belongs.`);
    if (t.k === '{') {
      const parts = ['{'];
      i++;
      if (toks[i]?.k === '}') { i++; parts.push('}'); return parts; }
      for (;;) {
        parts.push(...readValue(t.line));
        const s = toks[i];
        if (!s) throw cannot(t.line, 'a set value opened with { is never closed.');
        i++;
        if (s.k === '}') { parts.push('}'); return parts; }
        if (s.k !== ',') throw cannot(s.line, `expected , or } in a set value but found ${s.raw}.`);
        parts.push(',');
      }
    }
    throw cannot(t.line, `${t.raw} cannot start a constant value. Values are names, non-negative numbers, strings, or {sets} of those.`);
  };

  while (i < toks.length) {
    const kw = toks[i];
    if (kw.k !== 'kw') throw tlcRefuses(kw.line, `expecting a keyword but found ${kw.raw}.`);
    i++;
    const word = kw.raw;
    if (UNSUPPORTED_KEYWORDS.has(word)) throw cannot(kw.line, `the ${word} section is not supported by this command. Remove it.`);
    if (word === 'CHECK_DEADLOCK') {
      if (seenDeadlock) throw tlcRefuses(kw.line, 'CHECK_DEADLOCK appears twice.');
      seenDeadlock = true;
      const v = toks[i];
      if (!v || v.k === 'kw') throw tlcRefuses(kw.line, 'CHECK_DEADLOCK needs TRUE or FALSE after it.');
      if (v.raw !== 'TRUE' && v.raw !== 'FALSE') throw tlcRefuses(v.line, `CHECK_DEADLOCK takes TRUE or FALSE (in capitals), not ${v.raw}.`);
      i++;
      out.checkDeadlock = v.raw === 'TRUE';
      continue;
    }
    if (SINGLE_KEYWORDS.has(word)) {
      if (seenSingle.has(word)) throw tlcRefuses(kw.line, `${word} appears twice.`);
      seenSingle.add(word);
      const v = toks[i];
      if (!v) throw tlcRefuses(kw.line, `the config ends where the name after ${word} belongs.`);
      if (v.k === 'kw') throw cannot(v.line, `the keyword ${v.raw} stands where the name after ${word} belongs.`);
      if (!isName(v)) defer(tlcRefuses(v.line, `${v.raw} is not defined in the specification.`));
      i++;
      const follow = toks[i];
      if (follow && follow.k !== 'kw') throw tlcRefuses(follow.line, `${word} takes one name, then a keyword must follow, but found ${follow.raw}.`);
      out.sections.push({ keyword: word, tokens: [v.raw] });
      if (word === 'INIT') out.init = v.raw;
      if (word === 'NEXT') out.next = v.raw;
      if (word === 'SPECIFICATION') out.specification = v.raw;
      if (word === 'VIEW') out.hasView = true;
      if (word === 'SYMMETRY') out.hasSymmetry = true;
      continue;
    }
    if (LIST_KEYWORDS.has(word)) {
      const kind = LIST_KEYWORDS.get(word);
      const names = [];
      while (i < toks.length && toks[i].k !== 'kw') {
        const t = toks[i++];
        if (!isName(t)) defer(tlcRefuses(t.line, `${t.raw} is not defined in the specification.`));
        names.push(t.raw);
      }
      if (kind === 'INVARIANT') out.invariants.push(...names);
      else if (kind === 'PROPERTY') out.properties.push(...names);
      else {
        if (kind === 'CONSTRAINT') out.constraints.push(...names);
        else out.actionConstraints.push(...names);
        if (names.length) out.sections.push({ keyword: word, tokens: names });
      }
      continue;
    }
    // CONSTANT(S)
    const tokens = [];
    const emptyArgs = () => tlcRefuses(kw.line, 'TLC stops here without giving a reason: an operator constant needs one or more values in parentheses, as in Op(a, b) = c.');
    while (i < toks.length && toks[i].k !== 'kw') {
      const nameTok = toks[i];
      if (!isName(nameTok)) {
        if (nameTok.k === 'num' || nameTok.k === 'str') throw cannot(nameTok.line, `${nameTok.raw} cannot be the name of a constant.`);
        throw cannot(nameTok.line, `expected a constant name but found ${nameTok.raw}.`);
      }
      i++;
      const entry = [nameTok.raw];
      while (toks[i]?.k === '!') {
        const seg = toks[i + 1];
        if (!isName(seg)) throw cannot(toks[i].line, 'a ! in a constant name must be followed by a name.');
        entry.push('!', seg.raw);
        i += 2;
      }
      const op = toks[i];
      if (!op) throw cannot(nameTok.line, `the config ends after the constant ${nameTok.raw}; give it = value or <- name.`);
      if (op.k === 'kw') throw cannot(op.line, `the keyword ${op.raw} stands where = or <- belongs after the constant ${nameTok.raw}.`);
      if (op.k === '<-') {
        i++;
        entry.push('<-');
        if (toks[i]?.k === '[') {
          const mod = toks[i + 1];
          if (!isName(mod) || toks[i + 2]?.k !== ']') throw cannot(toks[i].line, 'expected [Module] after <-.');
          entry.push('[', mod.raw, ']');
          i += 3;
        }
        const target = toks[i];
        if (!target) throw cannot(op.line, 'the config ends where the name after <- belongs.');
        if (target.k === 'kw') throw cannot(target.line, `the keyword ${target.raw} stands where the name after <- belongs.`);
        if (!isName(target)) throw cannot(target.line, `${target.raw} cannot follow <-; give a definition name.`);
        i++;
        entry.push(target.raw);
        if (entry.length === 3) out.substitutions.set(nameTok.raw, target.raw);
        else if (entry[1] === '<-') out.substitutions.set(nameTok.raw, target.raw);
        tokens.push(...entry);
        continue;
      }
      if (op.k === '(') {
        i++;
        entry.push('(');
        if (toks[i]?.k === ')') throw emptyArgs();
        for (;;) {
          if (!toks[i] || toks[i].k === 'kw') throw emptyArgs();
          entry.push(...readValue(kw.line));
          const s = toks[i];
          if (!s || s.k === 'kw') throw emptyArgs();
          i++;
          if (s.k === ')') { entry.push(')'); break; }
          if (s.k !== ',') throw emptyArgs();
          entry.push(',');
        }
      }
      const eq = toks[i];
      if (!eq) throw cannot(nameTok.line, `the config ends after the constant ${nameTok.raw}; give it = value.`);
      if (eq.k === 'kw') throw cannot(eq.line, `the keyword ${eq.raw} stands where = belongs after the constant ${nameTok.raw}.`);
      if (eq.k !== '=') throw cannot(eq.line, `expected = or <- after the constant ${nameTok.raw} but found ${eq.raw}.`);
      i++;
      entry.push('=');
      if (toks[i]?.k === '[') {
        const mod = toks[i + 1];
        if (!isName(mod) || toks[i + 2]?.k !== ']') throw cannot(toks[i].line, 'expected [Module] after =.');
        entry.push('[', mod.raw, ']');
        i += 3;
      }
      entry.push(...readValue(eq.line));
      tokens.push(...entry);
    }
    out.sections.push({ keyword: word, tokens });
  }

  if (deferred) throw deferred;
  if (out.specification && (out.init || out.next)) {
    throw tlcRefuses(null, 'it names both SPECIFICATION and INIT/NEXT; keep one form.');
  }
  if (!out.specification && !out.init) {
    throw tlcRefuses(null, 'it names neither SPECIFICATION nor INIT, so TLC has no initial predicate.');
  }
  out.written = out.sections.map((s) => [s.keyword, ...s.tokens].join(' ')).join('\n');
  return out;
}
