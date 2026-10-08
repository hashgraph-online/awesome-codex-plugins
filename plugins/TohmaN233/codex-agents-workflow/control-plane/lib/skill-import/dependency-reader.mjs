import { informationalImportObservation } from '../workflow-import-observations.mjs';
import { posix } from 'node:path';
import { normalizeImportedExecutableRequirements, readDependencyMetadata } from './metadata-reader.mjs';

// Deliberately finite static observations. This never runs a script or claims
// to infer its behavior. Unresolved observations remain visible Draft blockers.
export function analyzeSkillDependencies(snapshot) {
  const unresolved = snapshot.problems.map(item => ({ ...item, origin: 'observed' }));
  const references = []; const requirements = { providers: [], tools: ['read_workflow_resource'], mcp_servers: [], executables: [], environment: [] };
  const observed_dependencies = [];
  const declared = readDependencyMetadata(snapshot); unresolved.push(...declared.unresolved);
  for (const [kind, names] of Object.entries(declared.requirements)) requirements[kind].push(...names);
  const observe = (kind, name, path, evidence) => {
    if (name) observed_dependencies.push({ kind, name, path, evidence });
  };
  const executableForPath = path => /\.py$/i.test(path) ? 'python' : /\.[mc]?js$/i.test(path) ? 'node' : /\.ps1$/i.test(path) ? 'powershell' : /\.sh$/i.test(path) ? 'sh' : /\.(?:cmd|bat)$/i.test(path) ? 'cmd' : null;
  for (const [path, bytes] of Object.entries(snapshot.files)) {
    if (/\/scripts\/|\.(?:py|mjs|cjs|js|sh|ps1|cmd|bat)$/i.test(path)) {
      unresolved.push({ code: 'SCRIPT_REQUIRES_REVIEW', path, origin: 'observed' });
      observe('executable', executableForPath(path), path, 'script_resource_present');
    }
    if (snapshot.inventory.some(item => 'source/' + item.path === path && item.binary)) {
      unresolved.push({ code: 'BINARY_RESOURCE_REQUIRES_CAPABILITY', path, origin: 'observed' }); continue;
    }
    const text = bytes.toString('utf8');
    // Shell substitutions can be local variables (for example ANSI colors), and
    // JavaScript template interpolation is not an environment read at all.
    for (const match of text.matchAll(/\b(?:process\.env\.([A-Z_][A-Z0-9_]*)|os\.environ\[["']([A-Z_][A-Z0-9_]*)["']\])/g)) observe('environment', match[1] ?? match[2], path, 'static_reference');
    if (/\.sh$/i.test(path)) {
      const locals = new Set([...text.matchAll(/(?:^|[;\n])\s*(?:export\s+|local\s+)?([A-Z_][A-Z0-9_]*)\s*=(["'])([^$`\n]*?)\2(?=\s|;|$)/g)].map(m => m[1]));
      for (const match of text.matchAll(/\$\{([A-Z_][A-Z0-9_]*)\}/g)) if (!locals.has(match[1])) observe('environment', match[1], path, 'static_reference');
    }
    if (/\b[A-Za-z]:[\\/]|(?:^|[\s"'(])\/(?:Users|home)\//m.test(text) || text.includes(snapshot.root)) unresolved.push({ code: 'SOURCE_LINKED_PATH', path, origin: 'observed' });
    if (/(?:^|[\s"'(])\/(?:usr|opt|etc)\//m.test(text)) unresolved.push({code:'RUNTIME_PATH_REFERENCE',path,origin:'observed'});
    for (const match of text.matchAll(/\[[^\]\n]*\]\(([^)\n]+)\)/g)) {
      const target = match[1].replace(/^<|>$/g, '').split(/\s+["']/)[0];
      const line = text.slice(0, match.index).split('\n').length;
      if (target.startsWith('#')) continue;
      if (/^[a-z][a-z0-9+.-]*:/i.test(target)) {
        references.push({ path, target, line, kind: 'external' });
        unresolved.push({ code: 'EXTERNAL_REFERENCE_REQUIRES_REVIEW', path, line, target, origin: 'observed' }); continue;
      }
      let local;
      try { local = decodeURIComponent(target.split('#')[0]); } catch { unresolved.push({ code: 'INVALID_REFERENCE', path, line, origin: 'observed' }); continue; }
      if (local.startsWith('/') || local.includes('\\')) { unresolved.push({ code: 'SOURCE_LINKED_PATH', path, line, target: local, origin: 'observed' }); continue; }
      const resolved = posix.normalize(posix.join(posix.dirname(path), local));
      const contained = resolved.startsWith('source/') && Object.hasOwn(snapshot.files, resolved);
      references.push({ path, target: local, resolved, line, kind: 'local', present: contained });
      if (!contained) unresolved.push({ code: 'UNRESOLVED_LOCAL_REFERENCE', path, line, target: local, origin: 'observed' });
    }
    // Recognize common inline command/code references without pretending to
    // parse an entire shell language. A missed dynamic path remains a review
    // concern; an explicit missing path must never look self-contained.
    for (const match of text.matchAll(/(?:^|[\s`"'(])((?:\.\/)?(?:scripts|tools|bin)\/[A-Za-z0-9._/-]+\.(?:py|mjs|cjs|js|sh|ps1|cmd|bat))(?=$|[\s`"',);])/gmi)) {
      const target = match[1].replace(/^\.\//, '');
      const line = text.slice(0, match.index).split('\n').length;
      const rootResolved = posix.normalize('source/' + target);
      const relativeResolved = posix.normalize(posix.join(posix.dirname(path), target));
      const resolved = Object.hasOwn(snapshot.files, rootResolved) ? rootResolved : relativeResolved;
      const present = resolved.startsWith('source/') && Object.hasOwn(snapshot.files, resolved);
      if (!references.some(item => item.path === path && item.line === line && item.target === target)) references.push({ path, target, resolved, line, kind: 'command', present });
      observe('executable', executableForPath(target), path, 'inline_command_reference');
      if (!present) unresolved.push({ code: 'UNRESOLVED_COMMAND_REFERENCE', path, line, target, origin: 'observed' });
    }
  }
  for (const kind of Object.keys(requirements)) requirements[kind] = kind === 'executables'
    ? normalizeImportedExecutableRequirements(requirements[kind])
    : [...new Set(requirements[kind])].sort();
  const observations = observed_dependencies.filter((item, index, all) => all.findIndex(other => other.kind === item.kind && other.name === item.name && other.path === item.path && other.evidence === item.evidence) === index)
    .sort((a, b) => `${a.kind}\0${a.name}\0${a.path}\0${a.evidence}`.localeCompare(`${b.kind}\0${b.name}\0${b.path}\0${b.evidence}`));
  const hasRequiredExternal = requirements.executables.length || requirements.environment.length || requirements.mcp_servers.length || requirements.tools.some(tool => tool !== 'read_workflow_resource');
  const classification = unresolved.some(item => item.code === 'SOURCE_LINKED_PATH') ? 'source_linked'
    : (unresolved.length || hasRequiredExternal) ? 'external_requirements'
      : observations.length ? 'dependency_observations' : 'self_contained_candidate';
  return { requirements, observed_dependencies: observations, tool_policy: declared.tool_policy, references, declarations: declared.declarations, observations:unresolved.filter(informationalImportObservation), unresolved:unresolved.filter(i=>!informationalImportObservation(i)), classification };
}
