import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve,join} from 'node:path';
import {runPermissions} from '../lib/workflow-execution-envelope.mjs';
test('run write scopes accept absolute descendants of the current workspace',()=>{
 const workspace=resolve('media-project');
 for(const target of [join(workspace,'edit'),join(workspace,'edit').replaceAll('\\','/'),'edit'])assert.deepEqual(runPermissions({workspace,access:'bounded_write',allowed_paths:[target]}).allowed_paths,['edit']);
 assert.deepEqual(runPermissions({workspace,access:'bounded_write',allowed_paths:[workspace]}).allowed_paths,['.']);
 for(const target of [resolve(workspace,'../outside'),workspace+'-other/edit','../outside'])assert.throws(()=>runPermissions({workspace,access:'bounded_write',allowed_paths:[target]}),{code:'PATH_SCOPE'});
});
