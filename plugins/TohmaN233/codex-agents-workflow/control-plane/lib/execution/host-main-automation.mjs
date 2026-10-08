import { validateData, validateDataSchema } from '../workflow-data-schema.mjs';
import { requireValue } from '../workflow-paths.mjs';

export const HOST_AUTOMATION_CONTRACT = Object.freeze({
  version: 1,
  lifecycle: 'host_managed',
  agent_submission: 'semantic_values_only',
  finite_choices: 'host_form',
});

export function validateHostAutomationContract(contract) {
  requireValue(contract && typeof contract === 'object' && !Array.isArray(contract), 'HOST_AUTOMATION_CONTRACT', 'Workflow requires a host automation contract');
  requireValue(contract.version === HOST_AUTOMATION_CONTRACT.version, 'HOST_AUTOMATION_CONTRACT', 'Unsupported host automation contract version');
  for (const key of ['lifecycle', 'agent_submission', 'finite_choices']) {
    requireValue(contract[key] === HOST_AUTOMATION_CONTRACT[key], 'HOST_AUTOMATION_CONTRACT', `Invalid host automation setting: ${key}`);
  }
  return contract;
}

const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);

/**
 * App Server structured output accepts only closed object schemas and requires
 * every declared property. Keep this check separate from the broader Workflow
 * data-schema validator: tool and input schemas may legitimately use dynamic
 * maps, but model-authored output may not be silently narrowed or discarded.
 */
export function strictAgentOutputSchema(schema, path = '$') {
  validateDataSchema(schema);
  if (path === '$' && Object.keys(schema).length === 0) {
    return { type: 'object', properties: {}, required: [], additionalProperties: false };
  }
  const strict = structuredClone(schema);
  const objectSchema = strict.type === 'object' || object(strict.properties) || Object.hasOwn(strict, 'additionalProperties');
  if (objectSchema) {
    requireValue(strict.type === 'object', 'AGENT_OUTPUT_SCHEMA', `${path}: model output objects require type=object`);
    requireValue(strict.additionalProperties === false, 'AGENT_OUTPUT_SCHEMA', `${path}: model output objects require additionalProperties=false; use declared fields or host-owned evidence instead of an open map`);
    strict.properties ??= {};
    strict.required ??= [];
    requireValue(Array.isArray(strict.required), 'AGENT_OUTPUT_SCHEMA', `${path}: required must be an array`);
    const propertyNames = Object.keys(strict.properties);
    requireValue(propertyNames.every(key => strict.required.includes(key)) && strict.required.every(key => Object.hasOwn(strict.properties, key)), 'AGENT_OUTPUT_SCHEMA', `${path}: strict model output requires every declared property, and only declared properties, in required`);
    for (const [key, child] of Object.entries(strict.properties)) strict.properties[key] = strictAgentOutputSchema(child, `${path}/properties/${key}`);
  }
  if (strict.type === 'array' && strict.items) strict.items = strictAgentOutputSchema(strict.items, `${path}/items`);
  return strict;
}

export function semanticResultSchema(definition, { finalAcceptance = false } = {}) {
  const schema = structuredClone(definition.outputs_schema ?? {});
  const hostManaged = [];
  if (definition.decision) {
    schema.properties ??= {};
    delete schema.properties.decision_id;
    delete schema.properties.references;
    schema.properties.decision = { ...(schema.properties.decision ?? {}), enum: [...definition.decision.options] };
    hostManaged.push('decision_id', 'references');
  }
  if (finalAcceptance) {
    schema.properties ??= {};
    delete schema.properties.accepted;
    hostManaged.push('accepted');
  }
  if (Array.isArray(schema.required)) schema.required = schema.required.filter(key => !hostManaged.includes(key));
  return schema;
}

export function managedNativeResultSchema(definition) {
  return strictAgentOutputSchema(semanticResultSchema(definition));
}

export function hostNodeTurnSchema(semanticSchema) {
  const result = strictAgentOutputSchema(semanticSchema);
  return { type: 'object', additionalProperties: false,
    properties: { outcome: { type: 'string', enum: ['completed', 'blocked'] },
      result: { anyOf: [result, { type: 'null' }] }, block_reason: { type: 'string' } },
    required: ['outcome', 'result', 'block_reason'] };
}

export function hostNodeTurnResult(value, semanticSchema) {
  requireValue(value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).sort().join(',') === 'block_reason,outcome,result',
  'HOST_NODE_TURN_SCHEMA', 'Managed node must return the exact Host outcome envelope');
  if (value.outcome === 'blocked') {
    requireValue(value.result === null && typeof value.block_reason === 'string'
      && value.block_reason.trim().length > 0 && value.block_reason.length <= 2000,
    'HOST_NODE_TURN_SCHEMA', 'Blocked node needs a concrete reason and no success result');
    throw Object.assign(new Error(value.block_reason), { code: 'WORKFLOW_NODE_BLOCKED' });
  }
  requireValue(value.outcome === 'completed' && value.block_reason === '', 'HOST_NODE_TURN_SCHEMA', 'Completed node cannot carry a blocker');
  validateData(value.result, semanticSchema);
  return value.result;
}

export function createMainHostBinding({ runId, controlToken, owner, definition, lease, finalAcceptance }) {
  return {
    protocol: 'host-main-v1',
    run_id: runId,
    control_token: controlToken,
    node_id: definition.id,
    attempt_id: lease.attempt_id,
    lease_token: lease.lease_token,
    owner,
    decision: definition.decision ? {
      id: definition.decision.id,
      required_references: [...(definition.decision.required_references ?? [])],
      blocked_option: definition.decision.options.includes('blocked') ? 'blocked' : null,
    } : null,
    final_acceptance: finalAcceptance === true,
  };
}

export function createMainAgentPacket({ definition, dispatched, resources, finalAcceptance }) {
  const schema = semanticResultSchema(definition, { finalAcceptance });
  return {
    role: definition.role ?? null,
    access: dispatched.envelope.access,
    workspace: dispatched.envelope.workspace,
    allowed_paths: dispatched.envelope.effective_allowed_paths,
    prompt: dispatched.compiled_prompt,
    resources: structuredClone(resources),
    response_form: {
      mode: 'semantic_values_only',
      schema,
      decision: definition.decision ? { kind: 'choice', options: [...definition.decision.options] } : null,
      acceptance: finalAcceptance ? { kind: 'boolean_choice', options: [true, false] } : null,
    },
  };
}

export function hostCompletionEnvelope(definition, args, finalAcceptance) {
  const completion = hostResultProposalEnvelope(definition, args, { finalAcceptance });
  if (finalAcceptance) {
    requireValue(typeof args.accepted === 'boolean', 'FINAL_ACCEPTANCE_REQUIRED', 'The host acceptance form requires a boolean choice');
    if (definition.outputs_schema?.properties?.accepted) completion.structured_output.accepted = args.accepted;
    completion.acceptance = { accepted: args.accepted };
  }
  return completion;
}

/**
 * Build the durable semantic proposal produced by an isolated Main execution.
 * Authoring's human acceptance is deliberately absent. Ordinary finalizers
 * retain their semantic accepted field and complete without a human gate.
 */
export function hostResultProposalEnvelope(definition, args, { finalAcceptance = false } = {}) {
  const schema = semanticResultSchema(definition, { finalAcceptance });
  validateData(args.output, schema);
  const structured_output = structuredClone(args.output);
  if (definition.decision) {
    structured_output.decision_id = definition.decision.id;
    structured_output.references = [...(definition.decision.required_references ?? [])];
  }
  return {
    status: 'succeeded',
    summary: typeof args.summary === 'string' && args.summary.length ? args.summary : `Main node ${definition.id} completed`,
    structured_output,
    artifacts: structuredClone(args.artifacts ?? args.changed_paths ?? []),
    evidence: structuredClone(args.evidence ?? [{ kind: 'host_semantic_submission', node_id: definition.id }]),
    changed_paths: structuredClone(args.changed_paths ?? []),
    outside_paths: structuredClone(args.outside_paths ?? []),
  };
}
