import { requireValue, workflowId } from './workflow-paths.mjs';
import { canonicalJSON, LIMITS } from './workflow-revisions.mjs';
import { HOST_AUTOMATION_CONTRACT, validateHostAutomationContract } from './execution/host-main-automation.mjs';
import { WORKSPACE_SOURCE_LOCATIONS, WORKSPACE_SOURCE_LOCATIONS_SCHEMA } from './workspace-source-locations.mjs';

export const NODE_TYPES = new Set(['start', 'end', 'agent', 'condition', 'parallel', 'join', 'skill_ref', 'subworkflow', 'tool', 'human_gate']);
export const HUMAN_GATE_OUTPUT = Object.freeze({ approved: true });
export const LOOP_REGION_SCHEMA = {
  type:'object',required:['id','entry_node','exit_node','node_ids','max_rounds','until'],additionalProperties:false,
  properties:{id:{type:'string'},entry_node:{type:'string'},exit_node:{type:'string'},node_ids:{type:'array',minItems:1,maxItems:512,items:{type:'string'}},max_rounds:{type:'integer',minimum:1,maximum:Number.MAX_SAFE_INTEGER},until:{type:'object'},feedback_bindings:{type:'object'},item_scope:{type:'object',required:['items','verdicts','paths_field'],additionalProperties:false,properties:{items:{},verdicts:{},paths_field:{type:'string'},dependencies_field:{type:'string'}}}}
};

export function validateWorkflowShape(workflow) {
  const encoded = canonicalJSON(workflow);
  requireValue(Buffer.byteLength(encoded) <= LIMITS.definition, 'WORKFLOW_SIZE', 'Workflow definition exceeds size limit');
  requireValue(workflow.schema_version === 1, 'WORKFLOW_SCHEMA', 'Unsupported Workflow schema version');
  workflowId(workflow.id);
  requireValue(typeof workflow.name === 'string' && workflow.name.trim().length > 0 && workflow.name.length <= 256, 'WORKFLOW_NAME', 'Workflow requires a name of at most 256 characters');
  requireValue(['draft', 'ready'].includes(workflow.status), 'WORKFLOW_STATUS', 'Workflow status must be draft or ready');
  requireValue(Array.isArray(workflow.nodes) && Array.isArray(workflow.edges) && workflow.nodes.length <= 512 && workflow.edges.length <= 2048, 'WORKFLOW_GRAPH', 'Workflow needs bounded node and edge arrays');
  requireValue(workflow.loops === undefined || Array.isArray(workflow.loops) && workflow.loops.length <= workflow.nodes.length,
    'LOOP_SCHEMA', 'Repair regions must be an array bounded by the graph node count');
  requireValue(typeof workflow.enabled === 'boolean', 'WORKFLOW_ENABLED', 'Workflow enabled flag is required');
  requireValue(workflow.template_kind===undefined || ['role','workflow'].includes(workflow.template_kind), 'TEMPLATE_KIND', 'Template kind must be role or workflow');
  requireValue(workflow.role_prompt_mode===undefined || workflow.template_kind==='role'&&workflow.role_prompt_mode==='append_context','ROLE_PROMPT_MODE','Role prompt mode must be append_context on a Role template');
  if (workflow.host_automation !== undefined) validateHostAutomationContract(workflow.host_automation);
  for (const node of workflow.nodes) {
    if (node.output_validators === undefined) continue;
    requireValue(node.output_validators && typeof node.output_validators === 'object' && !Array.isArray(node.output_validators)
      && ['agent', 'tool'].includes(node.type) && Object.keys(node.output_validators).length > 0,
    'OUTPUT_VALIDATORS', 'Output validators need a producing Agent or Host tool node', { node_id: node.id });
    for (const [name, kind] of Object.entries(node.output_validators)) {
      requireValue(kind === WORKSPACE_SOURCE_LOCATIONS && node.outputs_schema?.properties?.[name]
        && (node.outputs_schema.required ?? []).includes(name)
        && canonicalJSON(node.outputs_schema.properties[name]) === canonicalJSON(WORKSPACE_SOURCE_LOCATIONS_SCHEMA),
      'OUTPUT_VALIDATORS', 'Marked output must use the exact workspace source locations schema',
      { node_id: node.id, output_name: name, validator: kind });
    }
  }
  return workflow;
}

export function createDraft(id, name) {
  return {
    schema_version: 1, context_projection_version: 2, id: workflowId(id), name, enabled: true, status: 'draft', revision: 1,
    description: '', tags: [], template_kind: 'workflow', inputs_schema: {}, outputs_schema: {},
    skill_policy: { mode: 'strict', implicit: 'deny', ambient_allow: [], shadowed_skill_paths: [] },
    host_automation: structuredClone(HOST_AUTOMATION_CONTRACT),
    requirements: { providers: [], tools: [], mcp_servers: [], executables: [] },
    finalization: { required: true, node_id: '' }, nodes: [], edges: [],
  };
}
