const operationalMemoryNames = new Set([
  'progress.md',
  'decision_log.md',
  'open_questions.md',
]);

const normalized = value => String(value ?? '').trim().replaceAll('\\', '/').replace(/^\.\//, '').toLowerCase();

// Project-memory and checkpoint documents are executor bookkeeping. They may
// be read as context, but they are never product artifacts or completion gates.
// A bare companion filename is classified as memory only when the same source
// clause explicitly places the document alongside project_memory content.
export function isOperationalMemoryArtifactPath(path, { sourceText = '' } = {}) {
  const value = normalized(path);
  if (!value) return false;
  const parts = value.split('/').filter(Boolean);
  if (parts.includes('project_memory')) return true;
  const basename = parts.at(-1);
  if (basename === 'project.md' && parts.length === 1) return true;
  const projectMemoryContext=/(?:^|[^A-Za-z0-9_])project_memory(?:[\\/]|\b)/i.test(sourceText);
  return parts.length === 1 && projectMemoryContext && (operationalMemoryNames.has(basename) || basename === 'changelog.md');
}
