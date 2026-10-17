import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {createDraft} from '../lib/workflow-schema.mjs';
import {WorkflowStore} from '../lib/workflow-store.mjs';
import {rebindBuiltinHostToolIdentities,migrateStoredWorkflowHostToolIdentities} from '../lib/workflow-host-tool-identity.mjs';
import {workflowResourceProgramIdentity} from '../lib/execution/workflow-resource-program.mjs';

// Registered 1.2 implementation before scoped child-environment forwarding.
const predecessor={name:'workflow-resource-program',version:'1',sha256:'1387f321c01e9438426f81adda1cd77f6c7ba820f7d8ea68183bfb8a4f68934f'};
function fixture(id){return {...createDraft(id,'Environment upgrade'),host_tools:[{
  id:'resource-alias',identity:structuredClone(predecessor),argv:['node','scripts/check.mjs','work'],
  input_schema:{type:'object'},output_schema:{type:'object'},env_allow:[],
  permissions:{network:false,read_paths:[],write_paths:['work']},
  output_cap_bytes:4096,deadline_ms:10000,idempotency:{mode:'safe'},
}]};}

test('scoped environment upgrade rebinds only its known shipped predecessor',()=>{
  const original=fixture('scoped-env-known'),before=structuredClone(original);
  const rebound=rebindBuiltinHostToolIdentities(original);
  assert.deepEqual(original,before);
  assert.deepEqual(rebound.workflow,{...before,host_tools:[{...before.host_tools[0],identity:workflowResourceProgramIdentity()}]});
  assert.equal(rebound.changes.length,1);
  assert.deepEqual(rebindBuiltinHostToolIdentities(rebound.workflow).changes,[]);
  for(const identity of [{...predecessor,sha256:'e'.repeat(64)},{...predecessor,version:'2'}]){
    const unknown=fixture('scoped-env-unknown');unknown.host_tools[0].identity=identity;
    assert.throws(()=>rebindBuiltinHostToolIdentities(unknown),{code:'HOST_TOOL_IDENTITY_MIGRATION_UNSUPPORTED'});
  }
});

test('saved upgrade preserves prior revision, resources and graph with audited identity change',async t=>{
  const root=await mkdtemp(join(tmpdir(),'scoped-env-upgrade-'));
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const store=await new WorkflowStore(root).initialize();
  const original=await store.create(fixture('scoped-env-store'),{resources:{'scripts/check.mjs':'original bytes'}});
  const migrations=await migrateStoredWorkflowHostToolIdentities(store),after=await store.snapshot(original.workflow.id);
  assert.equal(migrations.length,1);assert.equal(after.workflow.revision,original.workflow.revision+1);
  assert.deepEqual(await store.snapshot(original.workflow.id,original.revision_hash),original);
  assert.deepEqual(await store.resources(original.workflow.id),await store.resources(original.workflow.id,original.revision_hash));
  assert.deepEqual(after.workflow.nodes,original.workflow.nodes);assert.deepEqual(after.workflow.edges,original.workflow.edges);
  assert.deepEqual(after.provenance.host_tool_identity_migration.changes,migrations[0].changes);
  assert.deepEqual(await migrateStoredWorkflowHostToolIdentities(store),[]);
});
