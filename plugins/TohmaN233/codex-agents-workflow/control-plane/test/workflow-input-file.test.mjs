import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from './physical-tempdir.mjs';
import { loadWorkflowInputsFile } from '../lib/workflow-service.mjs';
import { digest } from '../lib/workflow-revisions.mjs';
import { workflowToolDefinitions } from '../lib/workflow-tools.mjs';

test('Workflow start loads one exact in-workspace JSON input packet by relative or absolute path',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'workflow-input-file-'));
  t.after(()=>rm(workspace,{recursive:true,force:true}));
  const bytes=Buffer.from(JSON.stringify({implementation_plan:'checked',source_manifest:{table_path:'data/cards.tsv'}}));
  const path=join(workspace,'launch-inputs.json');
  await writeFile(path,bytes);
  for(const inputs_path of ['launch-inputs.json',path]){
    const request=await loadWorkflowInputsFile({workflow_id:'example',workspace,access:'bounded_write',inputs_path,constraints:{purpose:'test'}});
    assert.deepEqual(request.inputs,{implementation_plan:'checked',source_manifest:{table_path:'data/cards.tsv'}});
    assert.equal(request.inputs_path,undefined);
    assert.deepEqual(request.constraints.workflow_input_file,{path:'launch-inputs.json',sha256:digest(bytes),bytes:bytes.length});
    assert.equal(request.constraints.purpose,'test');
  }
  const start=workflowToolDefinitions().find(item=>item.name==='workflow_start');
  assert(start.inputSchema.properties.inputs_path);
});

test('Workflow input packets reject ambiguous, escaping and malformed sources',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'workflow-input-file-'));
  const outside=await mkdtemp(join(tmpdir(),'workflow-input-outside-'));
  t.after(()=>Promise.all([rm(workspace,{recursive:true,force:true}),rm(outside,{recursive:true,force:true})]));
  await writeFile(join(workspace,'valid.json'),'{}');
  await writeFile(join(workspace,'invalid.json'),'{');
  await writeFile(join(outside,'outside.json'),'{}');
  await assert.rejects(loadWorkflowInputsFile({workspace,inputs_path:'valid.json',inputs:{}}),{code:'RUN_INPUT_SOURCE'});
  await assert.rejects(loadWorkflowInputsFile({workspace,inputs_path:join(outside,'outside.json')}),{code:'PATH_ESCAPE'});
  await assert.rejects(loadWorkflowInputsFile({workspace,inputs_path:'invalid.json'}),{code:'RUN_INPUT_JSON'});
});

test('model starts cannot transcribe nested local material into inline inputs',async()=>{
  const scalar={task:'implement the selected cards',source_manifest_path:'work/reference/source.json',tags:['pilot','ten']};
  assert.deepEqual(await loadWorkflowInputsFile({inputs:scalar},{model:true}),{inputs:scalar});
  await assert.rejects(loadWorkflowInputsFile({inputs:{task:'implement',source_manifest:{table_path:'data/cards.tsv'}}},{model:true}),{
    code:'RUN_STRUCTURED_INPUT_SOURCE',
    message:/inputs_path|scalar local path/,
  });
  await assert.rejects(loadWorkflowInputsFile({inputs:{task:'implement',items:[{id:'copied'}]}},{model:true}),{code:'RUN_STRUCTURED_INPUT_SOURCE'});
  assert.deepEqual(await loadWorkflowInputsFile({inputs:{source_manifest:{table_path:'data/cards.tsv'}}}),{inputs:{source_manifest:{table_path:'data/cards.tsv'}}});
});
