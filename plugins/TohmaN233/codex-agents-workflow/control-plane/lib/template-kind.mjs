import { requireValue } from './workflow-paths.mjs';

export function templateKind(pack) {
  const declared=pack.workflow.template_kind;
  if(declared!==undefined) {
    requireValue(['role','workflow'].includes(declared),'TEMPLATE_KIND','Template kind must be role or workflow');
    return declared;
  }
  // Existing definitions predate this feature. Never reinterpret their launch
  // semantics from graph shape or a stage count.
  return 'workflow';
}

export function roleNode(pack) {
  requireValue(templateKind(pack)==='role','ROLE_TEMPLATE_KIND','Selected template is a Workflow, not a role');
  const stages=pack.workflow.nodes.filter(node=>node.type==='agent'&&node.role!=='finalizer');
  requireValue(stages.length===1,'ROLE_TEMPLATE_SHAPE','A role needs exactly one agent instruction stage');
  return stages[0];
}
