import { lstat, readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';
import { digest, LIMITS } from '../workflow-revisions.mjs';

// Read only the explicitly saved source paths. This is a change observation,
// never a new execution pin, a complete inventory or an automatic import.
export async function skillSourceStatus(pack) {
  const references = [];
  if (pack.provenance?.source_path && pack.provenance?.source_hash) {
    references.push({ kind: 'import_origin', resource: 'source/SKILL.md', path: pack.provenance.source_path, source_hash: pack.provenance.source_hash });
    const root = dirname(pack.provenance.source_path);
    for (const item of pack.import_report?.resource_inventory ?? []) if (typeof item.path === 'string' && typeof item.source_sha256 === 'string') references.push({ kind: 'import_resource', resource: 'source/' + item.path, path: join(root, ...item.path.split('/')), source_hash: item.source_sha256 });
  }
  for (const node of pack.workflow.nodes) if (node?.type === 'skill_ref' && node.skill_ref) {
    references.push({ kind: 'skill_ref', node_id: node.id, path: node.skill_ref.path, source_hash: node.skill_ref.source_hash });
    for (const nested of node.skill_ref.allowed_nested_skills ?? []) references.push({ kind: 'nested_skill', node_id: node.id, path: nested.path, source_hash: nested.source_hash });
  }
  requireValue(references.length <= 4096, 'SKILL_STATUS_LIMIT', 'Too many source references to inspect');
  const entries = [];
  for (const reference of references) {
    try {
      await noSymlinks(reference.path); const info = await lstat(reference.path);
      const limit = reference.kind === 'import_resource' ? LIMITS.resource : LIMITS.definition;
      requireValue(info.isFile() && info.nlink === 1 && info.size <= limit, 'SKILL_SOURCE', 'Source must be a bounded regular file without links');
      const bytes = await readFile(reference.path); requireValue(bytes.length <= limit, 'SKILL_SIZE', 'Source grew during inspection');
      const current_source_hash = digest(bytes);
      entries.push({ ...reference, current_source_hash, status: current_source_hash === reference.source_hash ? 'unchanged' : 'update_available' });
    } catch (error) {
      entries.push({ ...reference, status: 'unavailable', error: { code: error.code ?? 'SKILL_SOURCE_READ_FAILED', message: error.message } });
    }
  }
  return { revision_hash: pack.revision_hash, checked_at: new Date().toISOString(), scope: pack.import_report?.resource_inventory ? 'complete imported Skill source inventory bytes' : 'explicit Skill source bytes', workflow_changed: false, entries };
}
