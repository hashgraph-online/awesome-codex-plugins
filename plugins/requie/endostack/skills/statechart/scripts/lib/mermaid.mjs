// Writes a chart model as a Mermaid stateDiagram-v2, encoding every label so
// that any text round-trips through Mermaid's parser as plain text.

const SAFE = /[A-Za-z0-9 .,'()!?+*=\-\/@$&^~|_]/;
const WORD_JOINER = '⁠';

function ref(cp) {
  return `#${cp};`;
}

// Encode text for a Mermaid label. `quoted` is set for composite names in "".
export function encodeLabel(input, { quoted = false } = {}) {
  // Normalise characters first.
  let s = '';
  for (let i = 0; i < input.length; i++) {
    const code = input.charCodeAt(i);
    if (code >= 0xd800 && code <= 0xdbff) {
      const next = input.charCodeAt(i + 1);
      if (next >= 0xdc00 && next <= 0xdfff) { s += input[i] + input[i + 1]; i++; continue; }
      s += '�';
      continue;
    }
    if (code >= 0xdc00 && code <= 0xdfff) { s += '�'; continue; }
    if (code === 0 || (code >= 0x80 && code <= 0x9f)) continue;
    if (/\s/u.test(input[i]) || code === 0x85 || code === 0x2028 || code === 0x2029) { s += ' '; continue; }
    s += input[i];
  }
  // Guard the sequences Mermaid decodes twice into entity syntax.
  s = s.replace(/#(?=[0-9A-Za-z])/g, `#${WORD_JOINER}`).replace(/&(?=[#A-Za-z])/g, `&${WORD_JOINER}`);
  s = s.replace(/marker-end="/g, `marker-end${WORD_JOINER}="`);
  const chars = Array.from(s);
  let out = '';
  for (let i = 0; i < chars.length; i++) {
    const c = chars[i];
    const next = chars[i + 1] ?? '';
    const prev = chars[i - 1] ?? '';
    const cp = c.codePointAt(0);
    const rest = chars.slice(i).join('');
    let code = false;
    if (c === ':' ) code = true;
    else if (c === '\\') code = true;
    else if (c === '%' && next === '%') code = true;
    else if (c === '%') code = true;
    else if (c === '<') code = true;
    else if (c === '>') code = true;
    else if (c === '_' && (!/[A-Za-z0-9]/.test(prev) || !/[A-Za-z0-9]/.test(next))) code = true;
    else if (c === '[' || c === ']' || c === '{' || c === '}' || c === ';' || c === '#' || c === '"' || c === '`') code = true;
    else if (c === ' ' && /^ (LR|RL|TB|BT)\b/.test(rest) && /direction$/i.test(chars.slice(Math.max(0, i - 9), i).join(''))) code = true;
    else if (c === 'C' && next === '4' && /^C4(Context|Container|Component|Dynamic|Deployment)/.test(rest)) code = true;
    else if (c === '-' && next === '-' && chars[i + 2] === '>') code = true;
    else if (cp === 0x2060) code = false;
    else if (!SAFE.test(c)) code = true;
    if (quoted && c === '"') code = true;
    out += code ? ref(cp) : c;
  }
  if (out.trim() === '') out = ref(32);
  return out;
}

// Title escape for YAML front matter (double-quoted scalar).
export function encodeTitle(t) {
  let s = '';
  for (const ch of t) {
    const cp = ch.codePointAt(0);
    if (ch === '"') s += '\\"';
    else if (ch === '\\') s += '\\\\';
    else if (ch === '<') s += '&lt;';
    else if (ch === '&') s += '&amp;';
    else if (cp < 0x20 || (cp >= 0x7f && cp <= 0x9f) || /\s/u.test(ch)) s += cp === 0 || (cp >= 0x80 && cp <= 0x9f) ? '' : ' ';
    else if (cp >= 0xd800 && cp <= 0xdfff) s += '�';
    else s += ch;
  }
  return s;
}

const CLASSDEFS = [
  'classDef breaks fill:#fde2e1,stroke:#c0392b,color:#7b1d14',
  'classDef mayBreak fill:#fdebd3,stroke:#d4740b,color:#6e3b04',
];

export function renderMermaid(model, { title, colors, ruleName }) {
  const lines = [];
  if (title) lines.push('---', `title: "${encodeTitle(title)}"`, '---');
  lines.push('stateDiagram-v2');
  const regions = model.mode === 'regions';
  if (regions) lines.push('  direction LR');
  const classOf = new Map(); // node id -> [classes]
  const legend = new Map(); // class -> text

  // Legend entries collected from marks.
  const ruleNames = (ids) => [...ids].map(ruleName).sort().join(' or ');
  const breakRules = new Set();
  const mayRules = new Set();
  const pathRules = new Set();
  const repeatRules = new Set();
  const groupsUsed = new Set();
  for (const tree of model.trees.values()) {
    for (const n of tree.nodes.values()) {
      if (!n.leaf) continue;
      const cls = [];
      if (n.group) { cls.push(colors.get(n.group)); groupsUsed.add(n.group); }
      if (n.mark === 'breaks') { cls.push('breaks'); for (const r of n.marks.always) breakRules.add(r); }
      else if (n.mark === 'mayBreak') { cls.push('mayBreak'); for (const r of [...n.marks.always, ...n.marks.some]) mayRules.add(r); }
      if (n.marks.bugPath.size) { cls.push('bugPath'); for (const r of n.marks.bugPath) pathRules.add(r); }
      if (n.marks.repeats.size) { cls.push('repeats'); for (const r of n.marks.repeats) repeatRules.add(r); }
      classOf.set(n.id, cls);
    }
  }
  const legendItems = [];
  for (const g of [...groupsUsed].sort()) legendItems.push({ cls: colors.get(g), text: g });
  if (breakRules.size) legendItems.push({ cls: 'breaks', text: `breaks ${ruleNames(breakRules)}` });
  if (mayRules.size) legendItems.push({ cls: 'mayBreak', text: `breaks ${ruleNames(mayRules)} in some cases` });
  if (pathRules.size) legendItems.push({ cls: 'bugPath', text: `path to the ${ruleNames(pathRules)} bug` });
  if (repeatRules.size) legendItems.push({ cls: 'repeats', text: `repeats forever so ${ruleNames(repeatRules)} breaks` });
  void legend;

  const body = [];
  const emitTree = (tree, indent) => {
    const emitNode = (key) => {
      const n = tree.nodes.get(key);
      if (n.leaf) { body.push(`${indent.repeat(n.depth + 1)}${n.id}: ${encodeLabel(n.name)}`); return; }
      const pad = indent.repeat(n.depth + 1);
      body.push(`${pad}state "${encodeLabel(n.name, { quoted: true })}" as ${n.id} {`);
      for (const c of [...n.children].sort((a, b) => sortKey(tree, a, b))) emitNode(c);
      body.push(`${pad}}`);
    };
    for (const k of [...tree.roots].sort((a, b) => sortKey(tree, a, b))) emitNode(k);
  };
  const emitArrows = (tree, arrows, initial, pad) => {
    for (const k of initial.slice().sort((a, b) => sortKey(tree, a, b))) body.push(`${pad}[*] --> ${tree.nodes.get(k).id}`);
    const num = (k) => Number(tree.nodes.get(k).id.slice(1));
    const sorted = arrows.slice().sort((a, b) => num(a.from) - num(b.from) || num(a.to) - num(b.to) || (a.text < b.text ? -1 : a.text > b.text ? 1 : 0));
    for (const a of sorted) body.push(`${pad}${tree.nodes.get(a.from).id} --> ${tree.nodes.get(a.to).id}: ${encodeLabel(a.text)}`);
  };
  if (legendItems.length) {
    body.push('  state Legend {');
    legendItems.forEach((it, i) => body.push(`    legend${i}: ${encodeLabel(it.text)}`));
    body.push('  }');
  }
  if (regions) {
    body.push('  state "all at once" as regions {');
    model.regionNames.forEach((r, k) => {
      if (k > 0) body.push('    --');
      const tree = model.trees.get(r);
      body.push(`    state "${encodeLabel(r, { quoted: true })}" as region${k} {`);
      const start = body.length;
      emitTree(tree, '  ');
      for (let i = start; i < body.length; i++) body[i] = `    ${body[i]}`;
      emitArrows(tree, model.arrows.get(r), model.initial.get(r), '      ');
      body.push('    }');
    });
    body.push('  }');
  } else {
    const tree = model.trees.get('');
    emitTree(tree, '  ');
    emitArrows(tree, model.arrows.get(''), model.initial.get(''), '  ');
  }
  lines.push(...body);
  const used = new Set([...classOf.values()].flat());
  for (const def of CLASSDEFS) if (used.has(def.split(' ')[1])) lines.push(`  ${def}`);
  legendItems.forEach((it, i) => lines.push(`  class legend${i} ${it.cls}`));
  const byClass = new Map();
  for (const [id, cls] of classOf) for (const c of cls) { if (!byClass.has(c)) byClass.set(c, []); byClass.get(c).push(id); }
  const order = [...new Set([...colors.values()]), 'breaks', 'mayBreak', 'bugPath', 'repeats'];
  for (const c of order) if (byClass.has(c)) lines.push(`  class ${byClass.get(c).join(',')} ${c}`);
  return `${lines.join('\n')}\n`;
}

function sortKey(tree, a, b) {
  const na = tree.nodes.get(a);
  const nb = tree.nodes.get(b);
  return Number(na.id.slice(1)) - Number(nb.id.slice(1));
}
