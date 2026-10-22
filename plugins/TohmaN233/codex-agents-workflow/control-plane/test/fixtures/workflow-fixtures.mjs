import { createDraft } from '../../lib/workflow-schema.mjs';

export const agent = id => ({
  id,
  type: 'agent',
  executor: { kind: 'main' },
  role: 'implementer',
  access: 'read_only',
  prompt_template: '{{task}}',
  approval: { required: false },
  retry: { max_attempts: 1 },
  input_bindings: {},
});

export const edge = (source, target, label) => ({
  id: `${source}-${target}`,
  source,
  target,
  ...(label ? { label } : {}),
});

export function readyWorkflow(id = 'example') {
  return {
    ...createDraft(id, 'Example'),
    status: 'ready',
    finalization: { required: true, node_id: 'final' },
    nodes: [
      { id: 'start', type: 'start' },
      { ...agent('final'), role: 'finalizer' },
      { id: 'end', type: 'end' },
    ],
    edges: [edge('start', 'final'), edge('final', 'end')],
  };
}
