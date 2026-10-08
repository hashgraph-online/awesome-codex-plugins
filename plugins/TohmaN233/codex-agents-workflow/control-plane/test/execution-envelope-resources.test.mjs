import test from 'node:test';
import assert from 'node:assert/strict';
import { executionEnvelope } from '../lib/workflow-execution-envelope.mjs';
import { compilePrompt } from '../lib/workflow-executor.mjs';

test('worker constraint projection excludes the native parent identity while the Run keeps it pinned',()=>{
  const parent='01a0db81-70bf-7233-9021-4b4e3849bec7';
  const node={id:'work',type:'agent',executor:{kind:'main'},access:'read_only',prompt_template:'Respect {{constraints}}.'};
  const state={run_id:'fixture-run',workflow_id:'fixture',workflow_revision:1,inputs:{task:'Fixture'},
    constraints:{native_parent_thread_id:parent,network:false},permissions:{workspace:'C:/fixture',access:'read_only',allowed_paths:[]},
    nodes:{work:{status:'claimed',output:null}}};
  const pins={root:{workflow:{skill_policy:{mode:'cooperative',implicit:'allow',ambient_allow:[],shadowed_skill_paths:[]},edges:[],requirements:{}},
    resources:[]},providers:[],skills:[]};
  const envelope=executionEnvelope(node,state,pins,{id:'attempt-1'},'lease');
  assert.deepEqual(envelope.constraints,{network:false});
  assert.equal(state.constraints.native_parent_thread_id,parent);
  const prompt=compilePrompt(envelope,64000);assert.doesNotMatch(prompt,new RegExp(parent));
  assert.match(prompt,/network/);assert.doesNotMatch(prompt,/native_parent_thread_id/);
});

test('handoff exposes pinned resource IDs, never the content-addressed object directory', () => {
  const node = { id: 'work', type: 'agent', executor: { kind: 'main' }, access: 'read_only', prompt_template: 'Inspect the source.', resources: ['source/SKILL.md'] };
  const state = { run_id: 'fixture-run', workflow_id: 'fixture', workflow_revision: 1, inputs: { task: 'Fixture' }, constraints: {}, permissions: { workspace: 'C:/fixture', access: 'read_only', allowed_paths: [] }, nodes: { work: { status: 'claimed', output: null } } };
  const pins = { root: { workflow: { skill_policy: { mode: 'cooperative', implicit: 'allow', ambient_allow: [], shadowed_skill_paths: [] }, edges: [], requirements: {} }, resources: [{ path: 'source/SKILL.md', sha256: 'a'.repeat(64), bytes: 12 }] }, providers: [], skills: [] };
  const envelope = executionEnvelope(node, state, pins, { id: 'attempt-1' }, 'lease');

  assert.equal('resources_root' in envelope, false);
  assert.deepEqual(envelope.resources, ['source/SKILL.md']);
  assert.deepEqual(envelope.resource_access, { reader: 'read_workflow_resource', paths: ['source/SKILL.md'] });
  assert.match(envelope.prompt_template, /logical identifiers, not filesystem paths/);
  assert.match(envelope.prompt_template, /read_workflow_resource/);
  assert.doesNotMatch(envelope.prompt_template, /agent_packet\.resources/);
});
