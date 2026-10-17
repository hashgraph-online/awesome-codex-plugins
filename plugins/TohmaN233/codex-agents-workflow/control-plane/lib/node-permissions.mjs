// Host-owned execution defaults. Semantic read/review profiles describe work
// and routing; they never reduce the generated node's filesystem authority.
// Runtime still intersects this scope with the Run's authorized paths/access.
export function generatedNodePermissions(access = 'bounded_write') {
  return { access, ...(access === 'bounded_write' ? { path_scope: { binding: 'run.allowed_paths' } } : {}) };
}
