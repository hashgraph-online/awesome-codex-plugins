import {open,lstat} from 'node:fs/promises';

// Read only the exact Host-created file, once after its command RPC terminates.
// Diagnostics describe evidence; they never authorize or change execution.
const MAX_BYTES=16384,MAX_EVENTS=32;
const phases=new Set(['started','stream_close','child_exit','child_close','stdio_drain_timeout','stop_control_consumed','stop_signal_sent','receipt']);
const safeCode=code=>typeof code==='string'&&/^[A-Z0-9_]{1,96}$/.test(code)?code:'CODEX_COMMAND_LIFECYCLE_READ_FAILED';
const pid=value=>Number.isSafeInteger(value)&&value>0;
const signal=value=>value===null||typeof value==='string'&&/^SIG[A-Z0-9]{1,16}$/.test(value);
const unknown=(error_code,filesystem_code)=>({status:'unknown',error_code,...(filesystem_code?{filesystem_code}:{}),boundaries:null,phase_counts:null});
const captures=new WeakMap();
const failure=code=>Object.assign(new Error('Exact lifecycle diagnostic evidence is unavailable'),{code});
const identity=(a,b)=>a.dev===b.dev&&a.ino===b.ino;
const usable=stat=>stat.isFile()&&stat.ino!==0n;

// Exclusive creation never opens a replacement FIFO, link or device. Keep this
// exact regular descriptor through execution; there is no terminal path open.
export async function prepareCommandLifecycleDiagnostics(path,processId){
  const ticket=Object.freeze({}),capture={path,processId,handle:null,identity:null,error:null};captures.set(ticket,capture);
  try{
    capture.handle=await open(path,'wx+');capture.identity=await capture.handle.stat({bigint:true});
    if(!usable(capture.identity))throw failure('CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE');
  }catch(error){
    capture.error=unknown(error.code==='CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE'?error.code:'CODEX_COMMAND_LIFECYCLE_CAPTURE_FAILED',safeCode(error.code));
    if(capture.handle){try{await capture.handle.close();}catch(closeError){capture.error.close_error_code=safeCode(closeError.code);}capture.handle=null;}
  }
  return ticket;
}

export async function releaseCommandLifecycleDiagnostics(ticket){
  const capture=captures.get(ticket);if(!capture)return null;captures.delete(ticket);
  if(capture.handle)try{await capture.handle.close();}catch(error){return unknown('CODEX_COMMAND_LIFECYCLE_CLOSE_FAILED',safeCode(error.code));}
  return capture.error;
}

async function boundedText(capture){
  const {handle,path}=capture;
  try{
    const before=await lstat(path,{bigint:true}),stat=await handle.stat({bigint:true});
    if(!usable(before)||!usable(stat)||!identity(before,capture.identity)||!identity(stat,capture.identity))throw failure('CODEX_COMMAND_LIFECYCLE_PATH_CHANGED');
    if(stat.size>BigInt(MAX_BYTES))throw failure('CODEX_COMMAND_LIFECYCLE_OVERSIZE');
    const buffer=Buffer.alloc(MAX_BYTES+1),{bytesRead}=await handle.read(buffer,0,buffer.length,0);
    if(bytesRead>MAX_BYTES)throw Object.assign(new Error('Lifecycle evidence exceeds its bound'),{code:'CODEX_COMMAND_LIFECYCLE_OVERSIZE'});
    if(BigInt(bytesRead)<stat.size)throw failure('CODEX_COMMAND_LIFECYCLE_INCOMPLETE');
    const after=await lstat(path,{bigint:true}),end=await handle.stat({bigint:true});
    if(!usable(after)||!usable(end)||!identity(after,capture.identity)||!identity(end,capture.identity))throw failure('CODEX_COMMAND_LIFECYCLE_PATH_CHANGED');
    if(end.size!==stat.size||end.mtimeNs!==stat.mtimeNs||end.ctimeNs!==stat.ctimeNs)throw failure('CODEX_COMMAND_LIFECYCLE_CHANGED_DURING_READ');
    return buffer.subarray(0,bytesRead).toString('utf8');
  }finally{if(handle)try{await handle.close();}catch(error){throw Object.assign(failure('CODEX_COMMAND_LIFECYCLE_CLOSE_FAILED'),{filesystem_code:safeCode(error.code)});}}
}

export async function readCommandLifecycleDiagnostics(ticket,processId,receipt){
  const capture=captures.get(ticket);
  if(!capture||capture.processId!==processId)return unknown('CODEX_COMMAND_LIFECYCLE_CAPABILITY_UNAVAILABLE');
  captures.delete(ticket);
  if(capture.error)return capture.error;
  try{
    const text=await boundedText(capture);
    if(!text.endsWith('\n'))return unknown('CODEX_COMMAND_LIFECYCLE_INCOMPLETE');
    const lines=text.trimEnd().split('\n');
    if(lines.length>MAX_EVENTS)return unknown('CODEX_COMMAND_LIFECYCLE_OVERSIZE');
    let events;try{events=lines.map(line=>JSON.parse(line));}catch{return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');}
    const counts={},streams=new Set(),boundaries={started:null,child_exit:null,child_close:null,receipt:null};let previous=-Infinity;
    for(const event of events){
      if(!event||typeof event!=='object'||Array.isArray(event)||event.process_id!==processId||!phases.has(event.phase)
        ||typeof event.at!=='string'||!Number.isFinite(Date.parse(event.at))||new Date(event.at).toISOString()!==event.at)
        return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
      const time=Date.parse(event.at);
      if(time<previous)return unknown('CODEX_COMMAND_LIFECYCLE_CLOCK_ANOMALY');
      previous=time;counts[event.phase]=(counts[event.phase]??0)+1;
      if(Object.hasOwn(boundaries,event.phase)){
        if(boundaries[event.phase])return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
        boundaries[event.phase]={at:event.at};
      }
      if(event.phase==='started'){
        if(event!==events[0])return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
        if(typeof event.platform!=='string'||!/^[a-z0-9]{1,16}$/.test(event.platform))return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
        for(const key of ['runner_pid','runner_parent_pid','child_pid']){
          if(!Number.isSafeInteger(event[key])||event[key]<=0)return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
          boundaries.started[key]=event[key];
        }
      }
      if(['child_exit','child_close'].includes(event.phase)&&(!(event.exit_code===null||Number.isSafeInteger(event.exit_code))||!signal(event.signal)))
        return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
      if(['stdio_drain_timeout','stop_control_consumed','stop_signal_sent'].includes(event.phase)&&(!pid(event.child_pid)
        ||boundaries.started&&event.child_pid!==boundaries.started.child_pid))return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
      if(event.phase==='stop_control_consumed'&&typeof event.child_exited!=='boolean')return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
      if(event.phase==='stop_signal_sent'&&(!['SIGINT','SIGTERM'].includes(event.signal)||typeof event.accepted!=='boolean'))return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
      if(event.phase==='stream_close'){
        if(!['stdout','stderr'].includes(event.stream)||streams.has(event.stream))return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
        streams.add(event.stream);
      }
      if(event.phase==='receipt'){
        if(event!==events.at(-1)||event.schema_version!==1||!Number.isSafeInteger(event.exit_code)
          ||!Number.isSafeInteger(event.output_bytes)||event.output_bytes<0
          ||!signal(event.signal)||event.error_code!==undefined&&!['CODEX_COMMAND_PIPE_HELD','CODEX_COMMAND_LIFECYCLE_FAILED'].includes(event.error_code))return unknown('CODEX_COMMAND_LIFECYCLE_INVALID');
        if(receipt&&(event.exit_code!==receipt.exit_code||event.output_bytes!==receipt.output_bytes||event.signal!==receipt.signal
          ||event.error_code!==receipt.error_code))return unknown('CODEX_COMMAND_LIFECYCLE_RECEIPT_MISMATCH');
        boundaries.receipt.exit_code=event.exit_code;boundaries.receipt.output_bytes=event.output_bytes;
        if(event.error_code)boundaries.receipt.error_code=safeCode(event.error_code);
      }
    }
    // Missing observations can be partial evidence. Observed contradictions
    // cannot: the original child close follows exit, and drain timeout can
    // only fire after exit and before any close that clears its timer.
    const index=phase=>events.findIndex(event=>event.phase===phase),exit=index('child_exit'),close=index('child_close'),drain=index('stdio_drain_timeout');
    if(exit>=0&&close>=0&&close<exit||exit>=0&&drain>=0&&drain<exit||close>=0&&drain>=0&&close<drain||counts.stdio_drain_timeout>1)
      return unknown('CODEX_COMMAND_LIFECYCLE_PHASE_ORDER');
    const missing=Object.keys(boundaries).filter(key=>!boundaries[key]&&!(key==='child_close'&&counts.stdio_drain_timeout));
    if(streams.size!==2)missing.push('stream_close');
    const lifecycleFailed=events.at(-1)?.error_code==='CODEX_COMMAND_LIFECYCLE_FAILED';
    return {status:missing.length||lifecycleFailed?'partial':'complete',
      ...(missing.length?{error_code:'CODEX_COMMAND_LIFECYCLE_PHASES_MISSING',missing_phases:missing}:{}),
      ...(lifecycleFailed?{error_code:'CODEX_COMMAND_LIFECYCLE_FAILED'}:{}),boundaries,phase_counts:counts};
  }catch(error){return unknown(error.code==='ENOENT'?'CODEX_COMMAND_LIFECYCLE_MISSING'
    :['CODEX_COMMAND_LIFECYCLE_INVALID','CODEX_COMMAND_LIFECYCLE_OVERSIZE','CODEX_COMMAND_LIFECYCLE_INCOMPLETE','CODEX_COMMAND_LIFECYCLE_PATH_CHANGED','CODEX_COMMAND_LIFECYCLE_CHANGED_DURING_READ','CODEX_COMMAND_LIFECYCLE_CLOSE_FAILED'].includes(error.code)?error.code:'CODEX_COMMAND_LIFECYCLE_READ_FAILED',safeCode(error.filesystem_code??error.code));}
}
