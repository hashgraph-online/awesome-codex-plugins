import test from 'node:test';
import assert from 'node:assert/strict';
import { generationProgress } from '../lib/skill-import/generation-progress.mjs';

test('review progress distinguishes the bounded second attempt, actual model, reads and compaction', () => {
  const record={pins:{generation:{settings:{max_rounds:2},reviewer:{id:'review',config:{model:'any-model',reasoning_effort:'high'}}}},state:{started_at:'2026-09-08T22:05:00Z',nodes:{expand:{attempts:[{},{}]},final:{active_attempt_id:'second',attempts:[{},{id:'second',started_at:'2026-09-08T22:21:08Z',executor_events:[{kind:'tool_operation',metadata:{path:'source/helper.py',phase:'read'}},{kind:'codex_event',metadata:{item_type:'contextCompaction',method:'item/started'}}]}]}}}};
  const value=generationProgress(record,'final',Date.parse('2026-09-08T22:22:08Z'));
  assert.equal(value.round,2);assert.equal(value.max_rounds,2);assert.equal(value.model,'any-model');assert.equal(value.stage_elapsed_ms,60000);
  assert.equal(value.resource_reads,1);assert.equal(value.last_resource,'source/helper.py');assert.equal(value.activity,'compacting');
  record.state.nodes.final.attempts[1].executor_events=Array.from({length:64},()=>({kind:'codex_event',metadata:{method:'item/completed'}}));
  const later=generationProgress(record,'final');assert.equal(later.resource_reads,0);assert.equal(later.read_count_scope,'recent_64_events');assert.equal(later.last_resource,undefined);
});
