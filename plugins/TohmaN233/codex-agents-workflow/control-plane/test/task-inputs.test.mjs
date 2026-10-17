import test from 'node:test';
import assert from 'node:assert/strict';
import {prepareTaskInputs,generateTaskBrief} from '../lib/task-inputs.mjs';
import {pathBoundaries,intersectBoundaries} from '../lib/workflow-bindings.mjs';
import {pathAllowed,runtimeWatchReasonIsViolation} from '../connectors/scope-guard.mjs';

test('task input preparation preserves schema and invokes main only when needed',async()=>{
  const base={inputs:{task:'Translate foo.txt into Chinese'},schema:{type:'object',additionalProperties:false,required:['file','language'],properties:{file:{type:'string'},language:{type:'string'}}}};
  const result=await prepareTaskInputs({...base,runModel:async request=>{assert.equal(request.inputs.task,base.inputs.task);return {ready:true,inputs_json:'{"file":"foo.txt","language":"Chinese"}',questions:[]};}});
  assert.deepEqual(result,{file:'foo.txt',language:'Chinese'});
  assert.deepEqual(await prepareTaskInputs({...base,inputs:result,runModel:async()=>assert.fail('No redundant model call')}),result);
  await assert.rejects(prepareTaskInputs({...base,runModel:async()=>({ready:false,questions:['Which source file?']})}),{code:'TASK_INFORMATION_REQUIRED'});
  await assert.rejects(prepareTaskInputs({...base,runModel:async()=>({ready:true,inputs_json:'{}'})}),{code:'DATA_INVALID'});
});
test('whole-project boundary intersects narrower scopes without allowing escapes',()=>{
  assert.deepEqual(pathBoundaries(['.']),['.']);
  assert.deepEqual(intersectBoundaries(['.'],['src']),['src']);
  assert.deepEqual(intersectBoundaries(['src'],['.']),['src']);
  assert(pathAllowed('new/result.txt',['.']));
  assert(!pathAllowed('../outside.txt',['.']));
  assert(!pathAllowed('C:/outside.txt',['.']));
  assert.throws(()=>pathBoundaries(['']),{code:'PATH_SCOPE'});
  assert.throws(()=>pathBoundaries(['../outside']),{code:'PATH_SCOPE'});
});

test('runtime scope watch defers filename-less events to the terminal snapshot',()=>{
  assert.equal(runtimeWatchReasonIsViolation('unknown_path'),false);
  assert.equal(runtimeWatchReasonIsViolation('allowed_path'),false);
  assert.equal(runtimeWatchReasonIsViolation('allowed_path_ancestor'),false);
  assert.equal(runtimeWatchReasonIsViolation('outside_allowed_paths'),true);
  assert.equal(runtimeWatchReasonIsViolation('read_only'),true);
  assert.equal(runtimeWatchReasonIsViolation('watch_error:boom'),true);
});

test('task brief generation uses registered Luna settings and returns an editable task',async()=>{
  const provider={id:'native-luna',enabled:true,kind:'native_agent',capabilities:{read:true},config:{model:'gpt-5.6-luna',reasoning_effort:'max'}};
  const config={providers:[provider],strict_executor:{main_model:'another-model',main_reasoning_effort:'medium'}};
  const result=await generateTaskBrief({workflow:{name:'video-use'},existing:'保留原声',config,runModel:async request=>{
    assert.equal(request.brief,true);assert.equal(request.inputs.existing_task,'保留原声');
    assert.equal(request.config.strict_executor.main_model,'gpt-5.6-luna');assert.equal(request.config.strict_executor.main_reasoning_effort,'max');
    return {ready:true,inputs_json:JSON.stringify({task:'按工作流处理【请填写：素材路径】，保留原声。'})};
  }});
  assert.match(result.task,/保留原声/);assert.equal(result.provider_id,'native-luna');
  assert.equal(config.strict_executor.main_model,'another-model');
  await assert.rejects(generateTaskBrief({workflow:{},config:{...config,providers:[{...provider,enabled:false}]}}),{code:'TASK_BRIEF_PROVIDER'});
});
