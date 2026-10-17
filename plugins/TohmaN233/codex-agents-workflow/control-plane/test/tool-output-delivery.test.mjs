import test from 'node:test';
import assert from 'node:assert/strict';
import {inheritedToolOutputBudget} from '../lib/execution/tool-output-delivery.mjs';

test('user limit overrides model metadata without changing units or inflating limits',()=>{
  assert.deepEqual(inheritedToolOutputBudget({truncation_policy:{mode:'tokens',limit:10000}},{tool_output_token_limit:2000}),
    {source:'user_config',mode:'tokens',limit:2000,max_result_bytes:2000});
});
for(const mode of ['tokens','bytes'])test('preserves exact inherited '+mode+' ceiling',()=>{
  assert.deepEqual(inheritedToolOutputBudget({truncation_policy:{mode,limit:8192}}),
    {source:'model_metadata',mode,limit:8192,max_result_bytes:8192});
});
test('unknown or unusable effective budget fails qualification without invented defaults',()=>{
  for(const policy of [undefined,{mode:'unknown',limit:10000},{mode:'tokens',limit:0},{mode:'tokens',limit:511}])
    assert.throws(()=>inheritedToolOutputBudget({truncation_policy:policy}),{code:'CODEX_TOOL_OUTPUT_BUDGET'});
  assert.equal(inheritedToolOutputBudget({}, {tool_output_token_limit:2048}).source,'user_config');
});
