import { createDraft } from '../../lib/workflow-schema.mjs';

const text = { type: 'string', minLength: 1 };
const output = { type: 'object', properties: { status: text, evidence: text }, required: ['status', 'evidence'], additionalProperties: false };

export function createThreadStartupSmokeWorkflow(provider) {
  const smoke = {
    id: 'thread_smoke', type: 'agent', role: provider.config.role,
    executor: { kind: 'thread', provider_id: provider.id, lifecycle: 'start' }, access: 'read_only',
    prompt_template: 'This is a harmless English smoke test for a Workflow thread handoff. Confirm that you received this task. Do not write files or create another task. Return status and evidence showing that this exact Codex task was started.',
    outputs_schema: output, input_bindings: { task: '/inputs/task' }, approval: { required: false }, retry: { max_attempts: 2 },
  };
  const final = {
    id: 'final', type: 'agent', role: 'finalizer', executor: { kind: 'main' }, access: 'read_only',
    prompt_template: 'Verify that the collected result belongs to the exact Codex task started by this smoke test. Output status and evidence. Do not claim success without the exact task identity and observed completion evidence.',
    outputs_schema: output, input_bindings: { task: '/inputs/task', thread_result: '/nodes/thread_smoke/output' }, approval: { required: false }, retry: { max_attempts: 2 },
  };
  return {
    ...createDraft('thread-startup-smoke-test-fixture', 'Thread startup smoke test'), status: 'ready',
    description: 'Test-only fixture for the exact Codex task identity handoff.', tags: ['test', 'thread', 'smoke-test'],
    skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] },
    requirements: { providers: [provider.id], tools: [], mcp_servers: [], executables: [] },
    inputs_schema: { type: 'object', properties: { task: text }, required: ['task'], additionalProperties: true }, outputs_schema: output,
    output_bindings: { status: '/nodes/final/output/status', evidence: '/nodes/final/output/evidence' }, finalization: { required: true, node_id: 'final' },
    nodes: [{ id: 'start', type: 'start' }, smoke, final, { id: 'end', type: 'end' }],
    edges: [{ id: 'start-thread_smoke', source: 'start', target: 'thread_smoke' }, { id: 'thread_smoke-final', source: 'thread_smoke', target: 'final' }, { id: 'final-end', source: 'final', target: 'end' }],
  };
}
