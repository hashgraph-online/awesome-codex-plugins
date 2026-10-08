import test from 'node:test';
import assert from 'node:assert/strict';
import { compilePrompt } from '../lib/workflow-executor.mjs';

const envelope = inputs => ({ node_id: 'write', workflow_id: 'fixture', inputs, constraints: {}, context_projection: { references: [] } });

test('template-bound task context and verification cross the model boundary once', () => {
  const inputs = { task: 'EXACT_TASK_PAYLOAD', context: { marker: 'EXACT_CONTEXT_PAYLOAD' }, verification: 'EXACT_VERIFICATION_PAYLOAD', card_jobs: [{ id: 'card-1' }] };
  const prompt = compilePrompt({ ...envelope(inputs), prompt_template: 'Task: {{ task }}\nBackground: {{context}}\nCheck: {{verification}}' }, 64000);
  for (const marker of ['EXACT_TASK_PAYLOAD', 'EXACT_CONTEXT_PAYLOAD', 'EXACT_VERIFICATION_PAYLOAD']) assert.equal(prompt.split(marker).length - 1, 1, marker);
  assert.match(prompt, /"card_jobs":\[\{"id":"card-1"\}\]/);
  assert.deepEqual(inputs.context, { marker: 'EXACT_CONTEXT_PAYLOAD' });
});

test('deduplicated template data preserves code indentation and surrounding whitespace', () => {
  const inputs={task:'    return amount\n',context:'\t\n',verification:' keep trailing space '};
  const prompt=compilePrompt({...envelope(inputs),prompt_template:'Task:\n{{task}}END\nContext:{{context}}END\nCheck:{{verification}}END'},64000);
  assert.ok(prompt.startsWith('Task:\n    return amount\nEND\nContext:\t\nEND\nCheck: keep trailing space END'));
  assert.equal(prompt.includes('"task":'),false);
});

test('bindings not used by a template remain visible without unused template-field limits', () => {
  const task = 'SOURCE_TEXT_'.repeat(3000);
  const prompt = compilePrompt({ ...envelope({ task }), prompt_template: 'Read the declared task.' }, 64000);
  assert.ok(prompt.includes(task));
  assert.equal(prompt.split(task).length - 1, 1);
  assert.throws(() => compilePrompt({ ...envelope({ task }), prompt_template: '{{task}}' }, 64000), /template field task exceeds/);
});

test('one large rendered input fits the final limit instead of being echoed as JSON', () => {
  const task = 'x'.repeat(22000);
  const prompt = compilePrompt({ ...envelope({ task }), prompt_template: 'Handle {{task}}.' }, 24000);
  assert.ok(prompt.length < 24000);
  assert.equal(prompt.split(task).length - 1, 1);
});

test('empty optional template values remain declared', () => {
  const prompt = compilePrompt({ ...envelope({ task: 'bounded', context: '' }), prompt_template: '{{task}} {{context}}' }, 64000);
  assert.match(prompt, /\(not provided\)/);
  assert.match(prompt, /"context":""/);
  assert.doesNotMatch(prompt, /legacy|upstream_results|workflow_inputs/i);
});

test('Workflow prompt ignores legacy Role metadata and keeps only the node task',()=>{
  const roleMarker='ROLE_BEHAVIOR_EXACT',taskMarker='NODE_TASK_EXACT';
  const prompt=compilePrompt({...envelope({task:taskMarker}),prompt_template:'Do {{task}}.',role_profile:{id:'role-test',revision_hash:'a'.repeat(64),instructions:roleMarker}},64000);
  assert.equal(prompt.includes(roleMarker),false);
  assert.equal(prompt.split(taskMarker).length-1,1);
  assert.match(prompt,/^Do NODE_TASK_EXACT\./);
});
