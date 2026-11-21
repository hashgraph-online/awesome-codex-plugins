import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';
import {requireWorkerArtifactFreshness} from '../lib/execution/worker-artifact-snapshot.mjs';

test('legacy worker receipt checks declared product bytes without freezing bookkeeping',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'worker-product-legacy-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const product=join(workspace,'page.html');
  const originalPage=Buffer.from('original page');
  const originalState=Buffer.from('original runtime metadata');
  await writeFile(product,originalPage);
  await writeFile(join(workspace,'state.json'),originalState);
  // Persisted v1 receipts predate the current Main snapshot writer.
  const stored=canonicalJSON({schema_version:1,coverage:'whole_workspace',workspace:resolve(workspace),entries:[
    {path:'',kind:'directory'},
    {path:'page.html',kind:'file',bytes:originalPage.length,sha256:digest(originalPage)},
    {path:'state.json',kind:'file',bytes:originalState.length,sha256:digest(originalState)},
  ]});
  const runtime={runs:{readArtifact:async()=>Buffer.from(stored)}};
  const ref={artifact:'legacy-snapshot'};
  await writeFile(join(workspace,'state.json'),'updated runtime metadata');
  await requireWorkerArtifactFreshness(runtime,'run',workspace,['page.html'],ref);
  await assert.rejects(requireWorkerArtifactFreshness(runtime,'run',workspace,['missing.html'],ref),{code:'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED'});
  await writeFile(product,'altered page');
  await assert.rejects(requireWorkerArtifactFreshness(runtime,'run',workspace,['page.html'],ref),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
});
