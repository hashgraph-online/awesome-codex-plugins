import { resourcePath, requireValue } from '../workflow-paths.mjs';

// A registered resource-program check declares its own mechanical inputs.
// Model references remain independent and may contain semantic documentation.
export function hostCompletionResourcePaths(contract, nodeResources = []) {
  if (contract.identity.name !== 'workflow-resource-program') return [...nodeResources];
  requireValue(contract.argv.length >= 3, 'WORKFLOW_RESOURCE_CONTRACT', 'Host completion resource program needs an entry and scratch directory');
  const paths = [resourcePath(contract.argv[1])];
  for (const argument of contract.argv.slice(3)) {
    if (argument.startsWith('@RESOURCE:') && argument.endsWith('@'))
      paths.push(resourcePath(argument.slice(10, -1)));
  }
  return [...new Set(paths)];
}
