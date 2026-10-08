import {requireValue} from '../workflow-paths.mjs';
import {WORKFLOW_WAIT_MS} from '../workflow-wait.mjs';

function abortReason(signal) {
  if (signal.reason !== undefined) return signal.reason;
  const error = new Error('The originating Workflow start was aborted');
  error.name = 'AbortError';
  return error;
}

async function cancelAndPropagate(service, started, originalCancellation) {
  try {
    requireValue(typeof started.control_token === 'string' && started.control_token.length > 0,
      'RUN_AUTHORITY', 'Host launch returned no cancellation authority');
    await service.call('cancel', { run_id: started.run_id, control_token: started.control_token });
  } catch (cancelError) {
    throw Object.assign(new AggregateError([originalCancellation, cancelError],
      'Owned Workflow cancellation failed after the originating operation was aborted', { cause: cancelError }),
    { code: 'OWNED_WORKFLOW_CANCEL_FAILED' });
  }
  throw originalCancellation;
}

// Continue ordinary event waits in code. If the Host stops for a native handoff,
// return the exact controller continuation that the caller must execute.
export async function waitForOwnedWorkflow(service,started,{signal}={}) {
  if (started?.status === 'environment_attention') return started;
  const runId=started.run_id;
  requireValue(typeof runId==='string'&&runId.length>0,'RUN_IDENTITY','Host launch returned no Run identity');
  requireValue(typeof started.control_token === 'string' && started.control_token.length > 0,
    'RUN_AUTHORITY', 'Host launch returned no continuation authority');
  let args={run_id:runId,control_token:started.control_token,timeout_ms:WORKFLOW_WAIT_MS};
  for(;;){
    if(signal?.aborted) return cancelAndPropagate(service,started,abortReason(signal));
    let result;
    try { result=await service.call('wait',args,{signal}); }
    catch(error) {
      if(signal?.aborted) return cancelAndPropagate(service,started,error);
      throw error;
    }
    if(signal?.aborted) return cancelAndPropagate(service,started,abortReason(signal));
    requireValue(result.run_id===runId,'RUN_IDENTITY','Host wait returned another Run');
    if(!['timeout','subagent_event'].includes(result.wake_reason))return {...result,
      ...(result.next_action_args?.control_token?{control_token:result.next_action_args.control_token}:{}),
      execution_owner:started.execution_owner??'host_main_worker'};
    requireValue(result.next_action==='workflow_wait'&&result.next_action_args?.run_id===runId,
      'WORKFLOW_WAIT_CONTINUATION','Host wait omitted its exact continuation');
    args=result.next_action_args;
  }
}
