// Reads the XML that SANY's exporter prints: the root module name, its state
// variables in declaration order, and each definition's level
// (0 constant, 1 state, 2 action, 3 temporal).

const NAMED_ENTITIES = { lt: '<', gt: '>', amp: '&', quot: '"', apos: "'" };

export function decodeXml(s) {
  return s.replace(/&(#x[0-9a-fA-F]+|#[0-9]+|lt|gt|amp|quot|apos);/g, (_, e) => {
    if (e[0] === '#') {
      const cp = e[1] === 'x' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10);
      return String.fromCodePoint(cp);
    }
    return NAMED_ENTITIES[e];
  });
}

function first(chunk, tag) {
  const open = `<${tag}>`;
  const i = chunk.indexOf(open);
  if (i < 0) return null;
  const j = chunk.indexOf(`</${tag}>`, i);
  return decodeXml(chunk.slice(i + open.length, j));
}

export function parseSanyXml(xml) {
  const root = first(xml, 'RootModule');
  if (!root) throw new Error('SANY printed no root module.');
  const entries = new Map();
  const chunks = xml.split('<entry>');
  for (let c = 1; c < chunks.length; c++) {
    const chunk = chunks[c];
    const uid = first(chunk, 'UID');
    const m = /^<UID>\d+<\/UID><([A-Za-z]+)>/.exec(chunk);
    if (!uid || !m) continue;
    const kind = m[1];
    if (kind !== 'OpDeclNode' && kind !== 'UserDefinedOpKind' && kind !== 'ModuleNode') continue;
    const loc = {
      file: first(chunk, 'filename'),
      line: Number(/<line><begin>(\d+)<\/begin>/.exec(chunk)?.[1] ?? 0),
      col: Number(/<column><begin>(\d+)<\/begin>/.exec(chunk)?.[1] ?? 0),
    };
    const entry = { uid, kind, name: first(chunk, 'uniquename'), level: Number(first(chunk, 'level') ?? 0), loc };
    if (kind === 'OpDeclNode') entry.declKind = Number(first(chunk, 'kind'));
    if (kind === 'ModuleNode') entry.refs = [...chunk.matchAll(/<OpDeclNodeRef><UID>(\d+)<\/UID><\/OpDeclNodeRef>/g)].map((r) => r[1]);
    entries.set(uid, entry);
  }
  const rootNode = [...entries.values()].find((e) => e.kind === 'ModuleNode' && e.name === root);
  if (!rootNode) throw new Error(`SANY printed no module node for ${root}.`);
  const vars = rootNode.refs.map((u) => entries.get(u)).filter((e) => e && e.declKind === 3);
  const inherited = vars.filter((v) => v.loc.file !== root);
  const own = vars.filter((v) => v.loc.file === root).sort((a, b) => a.loc.line - b.loc.line || a.loc.col - b.loc.col);
  const definitions = new Map();
  for (const e of entries.values()) {
    if (e.kind !== 'UserDefinedOpKind') continue;
    const list = definitions.get(e.name) ?? [];
    list.push({ level: e.level, file: e.loc.file });
    definitions.set(e.name, list);
  }
  // INSTANCE brings in the instantiated module's declarations too; TLC prints
  // each variable once by name, so keep the first occurrence of each name.
  const names = [...new Set([...inherited, ...own].map((v) => v.name))];
  return { module: root, variables: names, definitions };
}

// Level of a definition as the root module sees it: the root's own definition
// wins over a LOCAL one in an extended module.
export function definitionLevel(sany, name) {
  const list = sany.definitions.get(name);
  if (!list || list.length === 0) return null;
  const rootDef = list.find((d) => d.file === sany.module);
  return (rootDef ?? list[0]).level;
}
