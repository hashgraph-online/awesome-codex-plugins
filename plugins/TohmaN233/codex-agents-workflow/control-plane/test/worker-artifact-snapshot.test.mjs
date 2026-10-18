import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {saveMainHostCheckSnapshot} from '../lib/execution/main-host-check-snapshot.mjs';
import {requireWorkerArtifactFreshness} from '../lib/execution/worker-artifact-snapshot.mjs';

test('legacy worker receipt checks declared product bytes without freezing bookkeeping',async t=>{
  const workspace=await mkdtemp(join(tmpdir(),'worker-product-legacy-'));t.after(()=>rm(workspace,{recursive:true,force:true}));
  const product=join(workspace,'page.html');await writeFile(product,'original page');
  let stored;
  const runtime={runs:{saveArtifact:async(_run,_name,bytes)=>{stored=bytes;return {artifact:'legacy-snapshot'};},readArtifact:async()=>Buffer.from(stored)}};
  const ref=await saveMainHostCheckSnapshot(runtime,'run','attempt',workspace);
  await writeFile(join(workspace,'state.json'),'updated runtime metadata');
  await requireWorkerArtifactFreshness(runtime,'run',workspace,['page.html'],ref);
  await assert.rejects(requireWorkerArtifactFreshness(runtime,'run',workspace,['missing.html'],ref),{code:'MAIN_ORCHESTRATION_HOST_CHECK_SNAPSHOT_REQUIRED'});
  await writeFile(product,'altered page');
  await assert.rejects(requireWorkerArtifactFreshness(runtime,'run',workspace,['page.html'],ref),{code:'MAIN_ORCHESTRATION_HOST_CHECK_STALE'});
  assert.equal(JSON.parse(stored).coverage,'whole_workspace','Legacy receipt bytes must stay unchanged');
});
