import { validateData } from './workflow-data-schema.mjs';

// Consume the exact workspace from runPermissions. Explicit roots retain their
// original schema behavior; only an absent declared string root is Host-owned.
// Raw caller inputs remain separate for source pins and fresh startup rereads.
export function effectiveRunInputs(inputs, schema, permissions) {
  if (!Object.hasOwn(inputs, 'project_root') && schema?.properties?.project_root?.type === 'string')
    inputs = { ...inputs, project_root: permissions.workspace };
  validateData(inputs, schema);
  return inputs;
}
