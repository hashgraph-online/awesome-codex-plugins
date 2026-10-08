import {watch} from 'node:fs';
import {requireValue} from './workflow-paths.mjs';

export const WORKFLOW_WAIT_MS=3_600_000;
const terminal=new Set(['succeeded','failed','cancelled']);
const attention=new Set(['failed','interrupted','blocked','awaiting_approval','awaiting_human_acceptance','needs_attention']);
const childEvents=new Set(['native_agent_rejection','native_serial_result','native_parallel_result','managed_native_results']);
function wakeReason(record,worker,afterSequence){
  if(terminal.has(record.state.status))return record.state.status;
  if(worker&&['failed','stale','audit_or_cleanup_failed'].includes(worker.phase))return 'host_failed';
  if(record.state.status==='paused'||worker?.phase==='awaiting_human_acceptance'||Object.values(record.state.approvals??{}).some(a=>a.status==='pending')||Object.values(record.state.nodes??{}).some(n=>attention.has(n.status)))return 'needs_attention';
  if((record.events??[]).some(e=>e.sequence>afterSequence&&childEvents.has(e.kind)))return 'subagent_event';
  if(worker&&!['running','starting'].includes(worker.phase))return 'host_stopped';
}

// This is a Host-side event wait, not a model polling loop. Heartbeat checks only
// read the small worker record; ordinary progress does not release the model.
export function waitForWorkflow({runId,controlToken,directory,readState,readWorker,afterSequence=0,timeoutMs=WORKFLOW_WAIT_MS,signal,healthMs=1000}) {
  requireValue(Number.isInteger(timeoutMs)&&timeoutMs>=1&&timeoutMs<=WORKFLOW_WAIT_MS,'WORKFLOW_WAIT_TIMEOUT','Wait timeout must be 1–3600000 ms');
  requireValue(Number.isInteger(afterSequence)&&afterSequence>=0,'WORKFLOW_WAIT_CURSOR','Wait cursor must be a nonnegative sequence');
  return new Promise((resolve,reject)=>{
    let watcher,timer,health,retry,record,tornSince=null,expired=false,checking=false,dirty=true,pending=false,settled=false;
    const cleanup=()=>{watcher?.close();clearTimeout(timer);clearTimeout(retry);clearInterval(health);signal?.removeEventListener('abort',abort);};
    const finish=(value,error)=>{if(settled)return;settled=true;cleanup();error?reject(error):resolve(value);};
    const abort=()=>finish(null,Object.assign(new Error('Workflow wait cancelled; the Run was not cancelled'),{code:'WORKFLOW_WAIT_CANCELLED'}));
    const view=(reason,worker)=>{const nativeHandoff=['non_main_semantic','main_orchestration'].includes(worker?.outcome?.stop_reason);return {run_id:runId,status:record.state.status,
      completion_satisfied:record.state.status==='succeeded',recovery_required:record.state.status==='failed',sequence:record.sequence,wake_reason:nativeHandoff?'native_handoff_required':reason,
      ...(record.state.error?{error:record.state.error}:{}),
      ...(worker?{host_worker:{phase:worker.phase,...(worker.outcome?{outcome:structuredClone(worker.outcome)}:{}),...(worker.termination?{termination:structuredClone(worker.termination)}:{}),...(worker.error?{error:worker.error}:{})}}:{}),
      attention:Object.entries(record.state.nodes??{}).filter(([,n])=>attention.has(n.status)).map(([node_id,n])=>({node_id,status:n.status,...(n.error?{error:n.error}:{})})),
      pending_approvals:Object.entries(record.state.approvals??{}).filter(([,a])=>a.status==='pending').map(([approval_id])=>approval_id),
      ...(nativeHandoff?{next_action:'workflow_native_next',next_action_args:{run_id:runId,...(controlToken?{control_token:controlToken}:{})}}
        :['timeout','subagent_event'].includes(reason)?{next_action:'workflow_wait',next_action_args:{run_id:runId,...(controlToken?{control_token:controlToken}:{}),after_sequence:record.sequence,timeout_ms:timeoutMs}}:{})};};
    const check=async(stateChanged=false)=>{
      dirty ||= stateChanged;pending=true;if(checking||settled)return;checking=true;
      try{
        while(pending&&!settled){
          pending=false;
          if(dirty||!record){dirty=false;record=await readState();tornSince=null;requireValue(record.state.run_id===runId,'RUN_IDENTITY','Wait observed a different Run');requireValue(afterSequence<=record.sequence,'WORKFLOW_WAIT_CURSOR','Wait cursor is ahead of this Run');}
          const worker=await readWorker();
          if(settled)return;
          const reason=wakeReason(record,worker,afterSequence);
          if(reason){finish(view(reason,worker));return;}
          if(expired){finish(view('timeout',worker));return;}
        }
      }catch(error){
        // A watcher can fire while appendEvent is still writing. Only this
        // incomplete-tail condition receives a bounded commit grace period;
        // persistent tails and every other integrity failure remain errors.
        if(error.code==='RUN_JOURNAL_TORN'&&!settled){
          tornSince??=Date.now();
          if(Date.now()-tornSince<1000){dirty=true;clearTimeout(retry);retry=setTimeout(()=>void check(true),25);}
          else finish(null,error);
        }else finish(null,error);
      }finally{checking=false;}
    };
    try{
      watcher=watch(directory,(_event,name)=>{if(!name||['events.jsonl','host-main-worker.json'].includes(String(name)))void check(String(name)!=='host-main-worker.json');});
      watcher.on('error',error=>finish(null,error));
      signal?.addEventListener('abort',abort,{once:true});
      if(signal?.aborted){abort();return;}
      health=setInterval(()=>void check(false),healthMs);
      timer=setTimeout(()=>{expired=true;void check(true);},timeoutMs);
      void check(true);
    }catch(error){finish(null,error);}
  });
}
