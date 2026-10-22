const namePattern = /^[A-Za-z][A-Za-z0-9_-]{0,127}$/;

export const SHARED_PREFIX_SCHEMA = Object.freeze({
  type: 'object', required: ['common_inputs'], additionalProperties: false,
  properties: { common_inputs: { type: 'array', maxItems: 32, uniqueItems: true,
    items: { type: 'string', minLength: 1, maxLength: 128, pattern: '^[A-Za-z][A-Za-z0-9_-]*$' } } },
});

export function sharedPrefixDeclarationIssue(node, workflowMode) {
  const declaration = node.fanout?.shared_prefix;
  if (declaration === undefined) return null;
  if (node.type !== 'agent' || node.executor?.kind !== 'main'
    || node.executor.mode !== 'worker' || (node.skill_policy?.mode ?? workflowMode) !== 'cooperative'
    || node.fanout.result_mode !== 'per_item')
    return 'Shared prefix requires a Cooperative Main worker with per-item fan-out results';
  if (!declaration || typeof declaration !== 'object' || Array.isArray(declaration)
    || Object.keys(declaration).length !== 1 || !Object.hasOwn(declaration, 'common_inputs')
    || !Array.isArray(declaration.common_inputs) || declaration.common_inputs.length > 32
    || new Set(declaration.common_inputs).size !== declaration.common_inputs.length
    || declaration.common_inputs.some(name => typeof name !== 'string' || !namePattern.test(name)
      || name === node.fanout.input || name === node.fanout.item_name
      || !Object.hasOwn(node.input_bindings ?? {}, name)))
    return 'Shared prefix common_inputs must be up to 32 unique declared bindings, excluding the item list and assigned item';
  return null;
}
