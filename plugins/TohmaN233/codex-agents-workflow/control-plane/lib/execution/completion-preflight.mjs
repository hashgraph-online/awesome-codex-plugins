import { validateData } from '../workflow-data-schema.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { resolveBindings, bindingPointers, pointerParts } from '../workflow-bindings.mjs';
import { bindingContext } from '../workflow-execution-envelope.mjs';
import { semanticResultSchema } from './host-main-automation.mjs';
import { validateLoopExitOutput, validateLoopItemSources } from '../workflow-loops.mjs';

export function validateFanoutProducerOutput(definition, output, state, pins) {
  for (const consumer of pins.root.workflow.nodes) {
    const binding = consumer.fanout && consumer.input_bindings?.[consumer.fanout.input];
    if (!binding || !pins.root.workflow.edges.some(edge => edge.source === definition.id && edge.target === consumer.id && !edge.label)
      || !bindingPointers(binding).some(pointer => {
        const parts = pointerParts(pointer);
        return parts[0] === 'nodes' && parts[1] === definition.id && parts[2] === 'output';
      })) continue;
    const context = bindingContext(state);
    context.nodes[definition.id] = { ...context.nodes[definition.id], output };
    const items = resolveBindings({ items: binding }, context).items;
    requireValue(Array.isArray(items) && items.length > 0, 'SUBAGENT_FANOUT_INPUT',
      `Node ${definition.id} must provide a nonempty ${consumer.fanout.input} list before ${consumer.id} can start`);
  }
}
import { WORKSPACE_SOURCE_LOCATIONS, validateWorkspaceSourceLocations } from '../workspace-source-locations.mjs';

// The completion transaction performs the same checks again against the then-current
// workspace. This early check only gives a live node a chance to correct its output.
export async function preflightSemanticOutput(definition, output, workspace, { state, pins, finalAcceptance = false } = {}) {
  validateData(output, semanticResultSchema(definition, { finalAcceptance }));
  for (const [output_name, kind] of Object.entries(definition.output_validators ?? {})) {
    if (kind === WORKSPACE_SOURCE_LOCATIONS) await validateWorkspaceSourceLocations(output[output_name], workspace,
      { producer_node_id: definition.id, output_name });
  }
  if (state && pins) {
    validateFanoutProducerOutput(definition, output, state, pins);
    validateLoopExitOutput(state, pins.root.workflow, definition.id, output);
    const proposed={...state,nodes:{...state.nodes,[definition.id]:{...state.nodes[definition.id],output,status:'succeeded'}}};
    validateLoopItemSources(proposed, pins.root.workflow, {allowUnavailable:true});
  }
}

export function correctableCompletionError(error) {
  return ['DATA_INVALID', 'SOURCE_LOCATION_INVALID', 'HOST_MAIN_OUTPUT_JSON', 'SUBAGENT_FANOUT_INPUT', 'LOOP_VERDICT_INVALID'].includes(error?.code);
}

export function boundedCompletionDiagnostic(error) {
  const code = String(error?.code ?? 'COMPLETION_INVALID').slice(0, 80);
  const reason = typeof error?.reason === 'string' ? error.reason.slice(0, 120) : '';
  const index = Number.isSafeInteger(error?.index) ? error.index : null;
  const path = typeof error?.path === 'string' ? error.path.slice(0, 512) : '';
  const message = String(error?.message ?? 'Invalid completion').slice(0, 900);
  const range = Object.fromEntries(['start_line', 'end_line', 'actual_line_count']
    .filter(key => Number.isSafeInteger(error?.[key])).map(key => [key, error[key]]));
  return { code, ...(reason ? { reason } : {}), ...(index !== null ? { index } : {}), ...(path ? { path } : {}), ...range, message };
}
