import test from 'node:test';
import assert from 'node:assert/strict';
import { authoringCompletionPolicy, automaticAuthoringCompletion } from '../lib/skill-import/completion-policy.mjs';

test('historical authoring recovery never adopts automatic completion from current defaults',()=>{
  assert.equal(automaticAuthoringCompletion({kind:'authoring_workflow_run',generation:{max_rounds:3}}),false);
  assert.equal(automaticAuthoringCompletion({completion_policy:authoringCompletionPolicy('manual')}),false);
  assert.equal(automaticAuthoringCompletion({completion_policy:authoringCompletionPolicy()}),true);
});

test('malformed or changed completion policy fails closed instead of acquiring Host authority',()=>{
  for(const policy of [null,{},'automatic',{mode:'automatic',target:'draft'},{mode:'manual',target:'launch_ready'},{mode:'automatic',target:'launch_ready',human:true}])
    assert.throws(()=>automaticAuthoringCompletion({completion_policy:policy}),{code:'AUTHORING_COMPLETION_POLICY'});
});
