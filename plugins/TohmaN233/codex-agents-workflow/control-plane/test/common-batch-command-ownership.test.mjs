import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,readFile,writeFile,rm} from 'node:fs/promises';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {tmpdir} from './physical-tempdir.mjs';
import {prepareCodexCommonBatch} from '../lib/execution/codex-common-batch-session.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';
import {ownedMcpContext} from '../lib/execution/owned-tool-mcp.mjs';
const exec=promisify(execFile),schema={type:'object',properties:{conclusion:{type:'string'}},required:['conclusion'],additionalProperties:false};
const initial={inputTokens:100,cachedInputTokens:80,outputTokens:2,reasoningOutputTokens:0,totalTokens:102};
async function exercise(t,prepare){
 const root=await mkdtemp(join(tmpdir(),'batch-command-ownership-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
 const parent=join(root,'owned');await mkdir(parent);const events=[],commandCalls=[],branches=[];let observe,router,forks=0,closes=0,owner;
 const emit=async event=>{events.push(event);await observe?.(event);};
 const selection={model:'fixture-model',effort:'high',main_execution_context:{parent_thread_id:'fixture-parent',sandbox_type:'workspace-write'}};
 const client={events,async call(method,args){
  if(method==='thread/fork'){
   const id='branch-'+forks++;await emit({method:'thread/tokenUsage/updated',params:{threadId:id,turnId:'source-turn',tokenUsage:{total:initial}}});
   return {model:selection.model,thread:{id,ephemeral:true,forkedFromId:'source'}};
  }
  if(method==='command/exec'){
   commandCalls.push(args);const result=await exec(args.command[0],args.command.slice(1),{cwd:args.cwd,windowsHide:true});
   return {stdout:result.stdout,stderr:result.stderr,exitCode:0};
  }
  if(method==='turn/start'){
   const id=args.threadId,turn='turn-'+id;await emit({method:'turn/started',params:{threadId:id,turn:{id:turn}}});
   const callId='call-'+id,context=ownedMcpContext({threadId:id,sessionId:id,callId,'x-codex-turn-metadata':{turn_id:turn}});
   await router({context,callId,tool:'run_workspace_program',arguments:{program:process.execPath,args:['-e',"require('fs').writeFileSync('proof.txt',process.cwd())"],yield_time_ms:30000}});
   await emit({method:'thread/tokenUsage/updated',params:{threadId:id,turnId:turn,tokenUsage:{total:{...initial,inputTokens:110,outputTokens:4,totalTokens:114}}}});
   await emit({method:'item/completed',params:{threadId:id,turnId:turn,item:{type:'agentMessage',text:JSON.stringify({results:[{conclusion:'Completed the assigned fixture.'}]})}}});
   await emit({method:'turn/completed',params:{threadId:id,turn:{id:turn,status:'completed'}}});return {turn:{id:turn}};
  }
  if(method==='turn/interrupt'){await emit({method:'turn/completed',params:{threadId:args.threadId,turn:{id:args.turnId,status:'interrupted'}}});return {};}
  assert.fail('Unexpected shared RPC: '+method);
 },async waitFor(predicate,{after=0}={}){const event=events.slice(after).find(predicate);assert(event,'Missing exact fixture event');return event;},async close(){closes++;}};
 const options={parent,binary:join(root,'MUST_NOT_SPAWN_ANOTHER_APP_SERVER'),expectedBinaryHash:'a'.repeat(64),home:root,cwd:root,env:process.env,access:'bounded_write',allowedPaths:['.'],shared_output_schema:schema,hostWorker:true,onPrefixOwned:value=>{owner=value;},
  resolveModelSelection:async()=>selection,toolBroker:{tools:()=>[]}};
 const reference=createCodexCommandBroker({...options,getClient:()=>client,spoolRoot:join(root,'reference'),getOutputBudget:()=>({max_result_bytes:20000})});
 let batch,causal;
 try{
  batch=await prepare(options,'Neutral common information.',{}, {prepareSource:async configured=>{
   observe=configured.sharedEventObserver;router=configured.sharedToolRouter;
   await configured.onPrefixOwned({interrupt:async()=>{},close:()=>client.close()});
   events.push({method:'thread/tokenUsage/updated',params:{threadId:'source',turnId:'source-turn',tokenUsage:{total:initial}}});
   return {source:{...selection,selection,tools:reference.tools(),tool_output_budget:{max_result_bytes:20000},command_audit_metadata:value=>value,tool_transport:{assertHealthy(){},failed:new Promise(()=>{})}},session:{client,profile:{home:root}},setup:{thread_id:'source',turn_id:'source-turn',output:'{"ready":true}',item_types:['userMessage','agentMessage']}};
  }});
  for(let index=0;index<3;index++){
   const cwd=join(root,'item-'+index);await mkdir(cwd);const toolBroker={tools:()=>[],revoke(){},async quiesce(){return {quiescent:true};},isQuiescent:()=>true};
   branches.push(await batch.openSession({...options,cwd,owner:{index},toolBroker}));
  }
  await Promise.all(branches.map(async(branch,index)=>{
   const result=await branch.turn('Write only the assigned item.',{output_schema:schema});assert.equal(JSON.parse(result.output).conclusion,'Completed the assigned fixture.');
   await branch.prepareHostCompletion();assert.equal(closes,0,'A settled item must not close the shared App Server');
   assert.equal(await readFile(join(root,'item-'+index,'proof.txt'),'utf8'),join(root,'item-'+index));
  }));
  assert.equal(commandCalls.length,3);assert.equal(new Set(commandCalls.map(call=>call.processId)).size,3);assert.equal(new Set(commandCalls.map(call=>call.cwd)).size,3);
 }catch(error){causal=error;}finally{
  const cleanup=await Promise.allSettled(branches.map(branch=>branch.close()));
  for(const action of [()=>owner?.close(),()=>reference.close()])try{await action();}catch(error){cleanup.push({status:'rejected',reason:error});}
  const failures=cleanup.filter(result=>result.status==='rejected').map(result=>result.reason);
  if(causal||failures.length)throw new AggregateError([...(causal?[causal]:[]),...failures],'Fixture execution or cleanup failed');
 }
 assert.equal(closes,1,'Only the common owner closes the shared App Server');
}
test('real common-batch factory runs three isolated program brokers on the existing client without another App Server',async t=>{await exercise(t,prepareCodexCommonBatch);});
test('the regression test rejects a common-batch factory that omits existing-client wiring',async t=>{
 const url=new URL('../lib/execution/codex-common-batch-session.mjs',import.meta.url),original=await readFile(url,'utf8');
 assert(original.includes('          getClient:()=>session.client,'));
 const mutant=original.replace('          getClient:()=>session.client,','').replace(/from '(\.\.?\/[^']+)'/g,(_match,path)=>'from '+JSON.stringify(new URL(path,url).href));
 const root=await mkdtemp(join(tmpdir(),'batch-command-mutant-'));t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));const path=join(root,'mutant.mjs');await writeFile(path,mutant);
 const changed=await import(pathToFileURL(path));await assert.rejects(exercise(t,changed.prepareCodexCommonBatch),error=>{
  const causes=[];const visit=value=>{if(!value||causes.includes(value))return;causes.push(value);for(const child of value.errors??[])visit(child);visit(value.cause);};visit(error);
  assert(causes.some(value=>value.code==='ENOENT'&&value.message.includes('MUST_NOT_SPAWN_ANOTHER_APP_SERVER')),'Mutant must fail by trying to launch the redundant server');return true;
 });
});
