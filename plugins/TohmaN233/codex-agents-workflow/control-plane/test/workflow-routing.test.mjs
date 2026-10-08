import test from 'node:test';
import assert from 'node:assert/strict';
import { routeReadyWorkflows } from '../lib/workflow-routing.mjs';

const pack=(id,name,description,tags=[],extra={})=>({revision_hash:id.padEnd(64,'0').slice(0,64),provenance:extra.provenance ?? {},workflow:{id,name,description,tags,status:extra.status ?? 'ready',enabled:extra.enabled ?? true,inputs_schema:{required:['task']},nodes:extra.nodes ?? [],...extra.workflow}});

test('compact routing selects explicit or uniquely strong Ready matches and exposes material effects',()=>{
  const packs=[
    pack('video-use','Video production','Create and validate a final video artifact.',['video','media'],{nodes:[{type:'agent',access:'bounded_write',executor:{kind:'main'}}]}),
    pack('review-only','Repository review','Inspect a repository and report findings.',['review'],{nodes:[{type:'agent',access:'read_only',executor:{kind:'provider'}}]}),
    pack('draft','Draft flow','Create videos.',['video'],{status:'draft'}),
    pack('system-build','Build Workflow','Create Workflows.',['workflow'],{provenance:{kind:'bundled_authoring_workflow'}}),
    pack('retired-video','Retired video workflow','Create and validate video.',['video'],{provenance:{kind:'v6-migration'}}),
    pack('role-review','Review role','Review the repository.',['review'],{workflow:{template_kind:'role'}}),
  ];
  const explicit=routeReadyWorkflows(packs,'Run video-use for this clip.');
  assert.equal(explicit.decision,'selected');assert.equal(explicit.selected.id,'video-use');assert.equal(explicit.selected.effects.writes,true);
  assert.deepEqual(explicit.candidates,[],'a selected route must not expose unrelated Workflow summaries');
  const semantic=routeReadyWorkflows(packs,'Please produce a video media artifact.');
  assert.equal(semantic.selected.id,'video-use');assert.equal(semantic.available_ready,2);
  const none=routeReadyWorkflows(packs,'Translate a novel chapter.');assert.equal(none.decision,'none');
  assert.equal(routeReadyWorkflows(packs,'Run role-review to review the repository.').candidates.some(item=>item.id==='role-review'),false);
  const duplicate=routeReadyWorkflows([pack('video-a','Shared workflow','First.'),pack('video-b','Shared workflow','Second.')],'Run Shared workflow.');
  assert.equal(duplicate.decision,'candidates');assert.equal(duplicate.selected,null);assert.equal(duplicate.candidates.length,2);
});
