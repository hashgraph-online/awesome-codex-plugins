import test from 'node:test';
import assert from 'node:assert/strict';
import {cooperativeExecutionPolicy} from '../lib/execution/main-execution-policy.mjs';

test('writable Host worker context isolation does not initialize another OS sandbox',()=>{
 const parent={parent_thread_id:'authenticated-main',sandbox_type:'workspace-write'};
 const policy=cooperativeExecutionPolicy('bounded_write',parent,{hostWorker:true});
 assert.equal(policy.thread_sandbox,'danger-full-access');
 assert.equal(policy.command_type,'dangerFullAccess');
 assert.equal(policy.basis,'cooperative_host_worker');
 assert.equal(policy.parent_sandbox_type,'workspace-write');
 assert.equal(policy.command_boundary,'host_allowed_paths_and_workspace_audit');
 assert.equal(policy.os_read_isolation,'not_claimed');
 assert.equal(cooperativeExecutionPolicy('bounded_write',parent).command_type,'workspaceWrite','Ordinary caller policy remains intact');
});

test('worker flag does not convert a read-only grant into writable execution',()=>{
 const parent={parent_thread_id:'authenticated-main',sandbox_type:'read-only'};
 assert.throws(()=>cooperativeExecutionPolicy('bounded_write',parent,{hostWorker:true}),{code:'MAIN_EXECUTION_POLICY'});
 assert.equal(cooperativeExecutionPolicy('read_only',parent,{hostWorker:true}).thread_type,'readOnly');
});
