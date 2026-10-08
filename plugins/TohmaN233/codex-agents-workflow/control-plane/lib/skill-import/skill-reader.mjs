import { readFile, lstat, readdir } from 'node:fs/promises';
import { basename, dirname, join, resolve, isAbsolute } from 'node:path';
import { parseDocument } from '../vendor/yaml.mjs';
import { requireValue, noSymlinks, resourcePath } from '../workflow-paths.mjs';
import { digest, canonicalJSON, LIMITS, prepareResources } from '../workflow-revisions.mjs';

export function parseSkill(text) {
  requireValue(typeof text === 'string' && Buffer.byteLength(text) <= LIMITS.definition, 'SKILL_SIZE', 'Skill instructions exceed the bounded definition size');
  const match = /^\uFEFF?---\r?\n([\s\S]*?)\r?\n(?:---|\.\.\.)(?:\r?\n|$)/.exec(text);
  requireValue(match, 'SKILL_FRONTMATTER', 'SKILL.md requires YAML frontmatter');
  const document = parseDocument(match[1], { uniqueKeys: true, version: '1.2', prettyErrors: false, customTags: [] });
  requireValue(!document.errors.length && !document.warnings.length, 'SKILL_YAML', 'Skill YAML is invalid or uses unsupported tags', { diagnostics: [...document.errors, ...document.warnings].map(item => ({ code: item.code, pos: item.pos })) });
  let metadata;
  try { metadata = document.toJS({ maxAliasCount: 20 }); canonicalJSON(metadata); }
  catch { throw Object.assign(new Error('Skill YAML contains excessive aliases or non-JSON data'), { code: 'SKILL_YAML_DATA' }); }
  requireValue(metadata && !Array.isArray(metadata) && typeof metadata.name === 'string' && metadata.name.trim() && typeof metadata.description === 'string' && metadata.description.trim(), 'SKILL_METADATA', 'Skill needs a nonempty name and description');
  const instructions = text.slice(match[0].length);
  requireValue(instructions.trim(), 'SKILL_INSTRUCTIONS', 'Skill instructions are empty');
  return { metadata, instructions, instructions_start_line: match[0].split('\n').length, frontmatter: match[1] };
}

// Known credential forms are never copied into a Pack. Redaction is explicit and
// makes the Draft non-executable; it is not claimed to detect arbitrary secrets.
export function redactKnownCredentials(text, { sourcePath = '' } = {}) {
  const findings = [];
  const replace = (_match, prefix = '') => {
    findings.push({ code: 'CREDENTIAL_REDACTED', replacement: `REDACTED_REQUIREMENT_${findings.length + 1}` });
    return prefix + `[${findings.at(-1).replacement}]`;
  };
  let sanitized = text.replace(/\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16})\b/g, match => replace(match));
  const key = String.raw`(?:[A-Z_]*(?:API_KEY|ACCESS_TOKEN|AUTH_TOKEN|PASSWORD)|api[_-]?key|access[_-]?token|password|client[_-]?secret)`;
  const placeholder = value => /^(?:\$|<|%|process\.env\.|os\.environ|REDACTED_|\[REDACTED_|YOUR[-_ ]|EXAMPLE[-_ ]|CHANGEME)/i.test(value) || /^(?:\.{2,}|null|None|true|false)$/i.test(value);
  // A code reference or type annotation is not a stored credential. Inspect
  // quoted literal assignments (including typed Python assignments) everywhere;
  // inspect unquoted values only in data and shell assignment contexts.
  const quoted = new RegExp(String.raw`(\b${key}["']?[ \t]*(?::[ \t]*[A-Za-z_][A-Za-z0-9_.\[\] |,]*[ \t]*)?(?:=(?!=)|:)[ \t]*)(["'])((?:\\.|(?!\2)[^\\\r\n])*)\2`, 'g');
  sanitized = sanitized.replace(quoted, (match, prefix, quote, value) => value && !placeholder(value) ? replace(match, prefix + quote) + quote : match);
  const code = /\.(?:py|pyi|[cm]?js|jsx|tsx?|java|cs|go|rs|c|h|cpp|hpp|rb|swift|kt)$/i.test(sourcePath);
  const codeLanguage = /^(?:python|py|javascript|js|typescript|ts|tsx|jsx|java|csharp|cs|go|rust|rs|c|cpp|ruby|rb|swift|kotlin)$/i;
  const bare = new RegExp(String.raw`^([ \t]*(?:export[ \t]+)?["']?${key}["']?[ \t]*(?:=(?!=)|:)[ \t]*)([^\s"'\x60,;\]}]+)`, 'gm');
  let fence = null;
  sanitized = sanitized.split(/(?<=\n)/).map(line => {
    const boundary = /^[ \t]*(`{3,}|~{3,})[ \t]*([\w-]*)/.exec(line);
    if (boundary) { fence = fence ? null : { code: codeLanguage.test(boundary[2]) }; return line; }
    if (code || fence?.code) return line;
    return line.replace(bare, (match, prefix, value) => placeholder(value) ? match : replace(match, prefix));
  }).join('');
  return { text: sanitized, findings };
}
const credentialFile = path => !/(?:^|\/)\.env\.(?:example|template)$/i.test(path) && /(?:^|\/)(?:\.env(?:\..*)?|auth\.json|credentials(?:\.json)?|cookies?(?:\.json|\.txt)?|id_rsa|id_ed25519|[^/]+\.(?:key|p12|pfx|pem))$/i.test(path);
const binaryText = bytes => { try { const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes); return text.includes('\0') ? null : text; } catch { return null; } };

export async function readSkillSnapshot(sourcePath, { expectedSourceHash } = {}) {
  requireValue(typeof sourcePath === 'string' && isAbsolute(sourcePath), 'SKILL_SOURCE', 'Skill source path must be absolute');
  const path = resolve(sourcePath); requireValue(basename(path) === 'SKILL.md', 'SKILL_SOURCE', 'Select the exact SKILL.md source');
  await noSymlinks(path); const mainInfo = await lstat(path);
  requireValue(mainInfo.isFile() && mainInfo.nlink === 1 && mainInfo.size <= LIMITS.definition, 'SKILL_SOURCE', 'Skill source must be a bounded regular file without links');
  const original = await readFile(path); const sourceHash = digest(original);
  requireValue(!expectedSourceHash || sourceHash === expectedSourceHash, 'SKILL_SOURCE_CHANGED', 'Selected Skill changed since inventory');
  const rawText = binaryText(original); requireValue(rawText !== null, 'SKILL_ENCODING', 'Skill instructions must be valid UTF-8'); parseSkill(rawText);
  const mainRedaction = redactKnownCredentials(rawText); const parsed = parseSkill(mainRedaction.text);
  const problems = mainRedaction.findings.map(item => ({ ...item, path: 'SKILL.md' }));
  const root = dirname(path); const files = { 'source/SKILL.md': Buffer.from(mainRedaction.text) }; const inventory = [];
  const seen = new Set(['skill.md']); let count = 1; let total = original.length;
  async function visit(directory, prefix = '') {
    await noSymlinks(directory);
    const entries = (await readdir(directory, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name, 'en'));
    if (entries.length > LIMITS.files) { problems.push({ code: 'SKILL_DIRECTORY_LIMIT', path: prefix || '.' }); return; }
    for (const entry of entries) {
      const relative = prefix + entry.name; if (relative === 'SKILL.md' || ['.git', 'node_modules', '__pycache__'].includes(entry.name)) continue;
      try { resourcePath(relative); } catch { problems.push({ code: 'UNPORTABLE_RESOURCE_PATH', path: relative }); continue; }
      if (++count > LIMITS.files) { problems.push({ code: 'RESOURCE_COUNT_LIMIT', path: relative }); return; }
      const absolute = join(directory, entry.name); const info = await lstat(absolute);
      if (info.isSymbolicLink() || !info.isFile() && !info.isDirectory() || info.isFile() && info.nlink !== 1) { problems.push({ code: 'LINK_OR_SPECIAL_RESOURCE', path: relative }); continue; }
      if (info.isDirectory()) { await visit(absolute, relative + '/'); continue; }
      const collision = relative.normalize('NFC').toLowerCase();
      if (seen.has(collision)) { problems.push({ code: 'RESOURCE_CASE_COLLISION', path: relative }); continue; } seen.add(collision);
      if (credentialFile(relative)) { problems.push({ code: 'CREDENTIAL_FILE_EXCLUDED', path: relative }); continue; }
      if (info.size > LIMITS.resource || total + info.size > LIMITS.resources) { problems.push({ code: 'RESOURCE_SIZE_LIMIT', path: relative }); continue; }
      await noSymlinks(absolute); const bytes = await readFile(absolute);
      if (bytes.length > LIMITS.resource || total + bytes.length > LIMITS.resources) { problems.push({ code: 'RESOURCE_SIZE_LIMIT', path: relative }); continue; } total += bytes.length;
      const text = binaryText(bytes); const redaction = text === null ? null : redactKnownCredentials(text, { sourcePath: relative });
      if (redaction) problems.push(...redaction.findings.map(item => ({ ...item, path: relative })));
      const snapshot = redaction ? Buffer.from(redaction.text) : bytes; files['source/' + relative] = snapshot;
      inventory.push({ path: relative, source_sha256: digest(bytes), snapshot_sha256: digest(snapshot), bytes: snapshot.length, binary: text === null });
    }
    requireValue(canonicalJSON((await readdir(directory)).sort()) === canonicalJSON(entries.map(entry => entry.name).sort()), 'SKILL_DIRECTORY_CHANGED', 'Skill resource inventory changed while importing');
  }
  await visit(root); prepareResources(files);
  // Inventory and source hashes are rechecked before returning a coherent import.
  await noSymlinks(path); requireValue(digest(await readFile(path)) === sourceHash, 'SKILL_SOURCE_CHANGED', 'Skill instructions changed while importing');
  for (const item of inventory) { const file = join(root, ...item.path.split('/')); await noSymlinks(file); requireValue(digest(await readFile(file)) === item.source_sha256, 'SKILL_RESOURCE_CHANGED', 'Skill resource changed while importing', { path: item.path }); }
  const metadataFiles = {};
  for (const name of ['agents/openai.yaml', 'SKILL.json']) if (files['source/' + name]) metadataFiles[name] = { sha256: digest(files['source/' + name]), resource: 'source/' + name };
  return { source_path: path, source_hash: sourceHash, root, ...parsed, files, inventory, problems, metadata_files: metadataFiles };
}
