import {resolve,isAbsolute,join} from 'node:path';
import {WorkflowRunStore} from './workflow-run-store.mjs';
import {diagnostic,requireHistoryAdmissionDiagnostic} from './run-history-maintenance.mjs';
import {requireValue} from './workflow-paths.mjs';
import {withRunAdmissionObserver} from './workflow-store.mjs';

const controller=new AbortController();
let identity=null,started=false,finished=false,protocolFailure=null,sequence=0;
const pendingDiagnostics=new Map();
const fail=(code,message)=>Object.assign(new Error(message),{code});
function failureDiagnostic(error){
 try{return diagnostic(error,0,identity.run_root);}
 catch(validation){
  // Rejected provenance is a visible failed terminal, never a successful audit
  // or a stalled IPC audit. Preserve both faults as hashes without unsafe paths.
  return diagnostic(Object.assign(new AggregateError([error,validation],'Worker retirement provenance requires attention'),{code:validation.code}));
 }
}
function exact(message){
 requireValue(message&&Buffer.byteLength(JSON.stringify(message))<=16_384
  &&Object.keys(message).every(key=>['schema_version','run_root','job_id','owner_token','owner_pid','created_at','worker_pid','type','sequence','error'].includes(key))
  &&Object.keys(identity).every(key=>message[key]===identity[key]),'RUN_HISTORY_WORKER_IDENTITY','Worker request differs from its exact launch');
}
function send(message){return new Promise((resolveSend,reject)=>{
 if(!process.connected){reject(fail('RUN_HISTORY_WORKER_IPC','Worker IPC closed before delivery'));return;}
 const sent=error=>error?reject(Object.assign(fail('RUN_HISTORY_WORKER_IPC','Worker IPC did not confirm delivery'),{cause:error})):resolveSend();
 try{process.send({...identity,...message},sent);}catch(error){sent(error);}
});}
function rejectDiagnostics(error){for(const pending of pendingDiagnostics.values())pending.reject(error);}
async function observeAdmission(detail){
 requireHistoryAdmissionDiagnostic(detail,identity.run_root);
 requireValue(started&&!finished&&sequence<Number.MAX_SAFE_INTEGER,'RUN_HISTORY_WORKER_PROTOCOL','Worker diagnostic is outside its audit');
 const current=++sequence;let pending;
 const acknowledged=new Promise((resolveACK,reject)=>{pending={resolve:resolveACK,reject};});
 // Disconnect can reject the ACK while send is still pending. Own that early
 // rejection immediately; the awaited ACK below still throws the same fault.
 void acknowledged.catch(()=>{});
 pendingDiagnostics.set(current,pending);
 try{await send({type:'admission',sequence:current,detail});await acknowledged;}finally{pendingDiagnostics.delete(current);}
}
async function finish(type,value){
 if(finished||pendingDiagnostics.size)throw fail('RUN_HISTORY_WORKER_PROTOCOL','Worker terminal requires one result and settled diagnostics');finished=true;
 await send({type,...value});process.disconnect();
}
process.on('disconnect',()=>{controller.abort();rejectDiagnostics(fail('RUN_HISTORY_WORKER_IPC','Worker diagnostic ACK channel closed'));});
process.on('message',message=>{
 Promise.resolve().then(async()=>{
  if(!identity){
   requireValue(message?.type==='initialize'&&message.schema_version===1&&isAbsolute(message.run_root)&&resolve(message.run_root)===message.run_root
    &&message.worker_pid===process.pid&&message.owner_pid===process.ppid&&Number.isSafeInteger(message.created_at)
    &&/^[a-f0-9-]{36}$/.test(message.job_id)&&/^[a-f0-9-]{36}$/.test(message.owner_token),
    'RUN_HISTORY_WORKER_IDENTITY','Worker initialization requires its genuine parent and exact job');
   const {type,...bound}=message;identity=bound;exact(message);await send({type:'ready'});return;
  }
  exact(message);
  if(message.type==='admission_ack'){
   const pending=pendingDiagnostics.get(message.sequence);
   requireValue(pending&&Number.isSafeInteger(message.sequence)&&!pending.acknowledged,'RUN_HISTORY_WORKER_PROTOCOL','Worker received an unexpected diagnostic ACK');
   pending.acknowledged=true;
   if(message.error){requireValue(typeof message.error.code==='string'&&typeof message.error.message==='string','RUN_HISTORY_WORKER_PROTOCOL','Worker diagnostic ACK error is invalid');pending.reject(Object.assign(fail(message.error.code,message.error.message),{cause:message.error}));}
   else pending.resolve();return;
  }
  if(message.type==='cancel'){controller.abort();return;}
  requireValue(message.type==='audit'&&!started&&!finished,'RUN_HISTORY_WORKER_PROTOCOL','Worker audit may start only once');started=true;
  try{
   const result=await withRunAdmissionObserver({admissionRoot:join(identity.run_root,'.run-locks','.store-operation'),onWait:observeAdmission},async()=>{
    const store=await new WorkflowRunStore(identity.run_root).initialize();return store.cleanupHistory({signal:controller.signal});
   });
   if(protocolFailure)throw protocolFailure;
   // cleanupHistory owns admission checkpoints and the atomic deletion commit.
   // Once it returns successfully, a later abort cannot undo that commit; keep
   // its real census and successful terminal. Partial/unknown failures throw.
   await finish('succeeded',{audit:{examined:result.examined,deleted_count:result.deleted_count,preserved_count:result.preserved_count}});
  }catch(error){
   if(!process.connected)throw error;
   error=protocolFailure??error;
   await finish(error.code==='RUN_HISTORY_CANCELLED'&&controller.signal.aborted?'cancelled':'failed',{error:failureDiagnostic(error)});
  }
 }).catch(error=>{
  protocolFailure??=error;controller.abort();rejectDiagnostics(error);
  // A protocol error is never a successful audit or an expected cancellation.
  if(identity&&!started&&!finished&&process.connected)finish('failed',{error:failureDiagnostic(error)}).catch(()=>{process.exitCode=1;process.disconnect();});
  else if(finished||!process.connected){process.exitCode=1;if(!started&&process.connected)process.disconnect();}
 });
});
