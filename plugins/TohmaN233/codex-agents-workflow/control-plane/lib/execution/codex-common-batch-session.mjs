import {join} from 'node:path';
import {mkdtemp} from 'node:fs/promises';
import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {writeDurableJSON} from '../workflow-events.mjs';
import {createCodexPrefixBatch} from './codex-prefix-batch.mjs';
import {prepareCodexLiveCommonSource,CODEX_NORMAL_PREFIX_USAGE_CAPABILITY,codexEventMetadata} from './codex-session.mjs';
import {createCodexCommandBroker} from './codex-command-broker.mjs';
import {cooperativeExecutionPolicy} from './main-execution-policy.mjs';
import {createTypedBatchOutputTransport} from './typed-batch-output-transport.mjs';

const usageFields={inputTokens:'input_tokens',cachedInputTokens:'cached_input_tokens',cacheWriteInputTokens:'cache_write_input_tokens',outputTokens:'output_tokens',reasoningOutputTokens:'reasoning_output_tokens'};
const usageFrom=(usage,reason)=>usage?({available:true,...Object.fromEntries(Object.entries(usageFields).filter(([key])=>usage[key]!==undefined).map(([key,name])=>[name,usage[key]]))}):{available:false,...(reason?{unavailable_reason:reason}:{})};
const failTogether=(errors,label)=>{if(errors.length===1)throw errors[0];if(errors.length)throw new AggregateError(errors,label);};

/** Ordinary native tools plus code-mode MCP, one private common-only source,
 * independently owned program/resource brokers, logical assignment scopes,
 * and real restored-before-submit usage baselines. */
export async function prepareCodexCommonBatch(options,text,turnOptions={}, {prepareSource=prepareCodexLiveCommonSource}={}){
  requireValue(options.shared_output_schema!==undefined,'CODEX_BATCH_OUTPUT_SCHEMA','Common batch requires its exact shared item output schema');
  const responseTransport=createTypedBatchOutputTransport(options.shared_output_schema,{repair_schema:options.shared_repair_schema});
  let sourceOwner,prepared,engine,revoked=false,closing,finish;
  const settled=new Promise(resolve=>finish=resolve),branches=new Map();
  const open=()=>{requireValue(!revoked,'CODEX_BATCH_CLOSED','Common batch ownership was revoked');options.assertActive?.();};
  const owner={
    async interrupt(){revoked=true;const errors=[];for(const action of [()=>engine?.interrupt(),()=>sourceOwner?.interrupt(),
      ...[...branches.values()].map(branch=>()=>branch.interrupt())])try{await action();}catch(error){errors.push(error);}failTogether(errors,'Common batch interruption failed');},
    async close(){
      if(closing)return closing;
      revoked=true;
      const operation=(async()=>{
        await settled;
        const results=await Promise.allSettled([...branches.values()].map(branch=>branch.close()));
        const errors=results.filter(item=>item.status==='rejected').map(item=>item.reason);
        // Retain the shared source while any child's command/resource effects
        // remain uncertain. A recovery close may retry the exact owners.
        failTogether(errors,'Common batch child cleanup failed; source retained');
        await sourceOwner?.close();
      })();closing=operation;
      try{return await operation;}finally{if(closing===operation)closing=null;}
    },
  };
  try{
    await options.onPrefixOwned?.(owner);open();
    prepared=await prepareSource({...options,sharedResponseTransport:responseTransport,
      onPrefixOwned:owned=>{sourceOwner=owned;open();},
      sharedEventObserver:async event=>{engine?.observe(event);},
      sharedToolRouter:params=>{
        requireValue(engine,'CODEX_BATCH_TOOL_CONTEXT','No shared child was admitted before common preparation completed');
        return engine.callTool(params,(index,call)=>{
          const branch=branches.get(index);
          requireValue(branch,'CODEX_BATCH_TOOL_CONTEXT','Shared callback has no admitted child broker');
          return branch.callTool(call);
        });
      }},text,turnOptions);open();
    const {source,session,setup}=prepared;
    const sourceUsage=session.client.events.filter(event=>event.method==='thread/tokenUsage/updated'&&event.params?.threadId===setup.thread_id&&event.params.turnId===setup.turn_id).at(-1);
    requireValue(sourceUsage?.params?.tokenUsage?.total,'CODEX_BATCH_USAGE','Common source has no exact actual cumulative usage');
    requireValue(setup.item_types.every(type=>['userMessage','agentMessage','reasoning'].includes(type)),
      'CODEX_BATCH_SOURCE_TOOLS','Common preparation must return ready once without tools or other execution');
    const fixedTurnOptions={effort:source.effort,outputSchema:responseTransport.prepare_setup(text,responseTransport.setup_schema).output_schema};
    engine=createCodexPrefixBatch({client:session.client,timeoutMs:turnOptions.timeout_ms||3600000,
      onTransition:metadata=>options.onEvent?.({method:'workflow/toolInterface',diagnostic:canonicalJSON({live_common_batch:metadata})})});
    engine.adoptSource({thread_id:setup.thread_id,turn_id:setup.turn_id,model:source.model,total:sourceUsage.params.tokenUsage.total,output:setup.output,turnOptions:fixedTurnOptions});
    let index=0;
    return {prefix:owner,setup,close:owner.close,interrupt:owner.interrupt,
      async openSession(childOptions){
        open();await childOptions.authorize?.();open();
        source.tool_transport.assertHealthy();
        requireValue(childOptions.access===options.sourceExecutionAccess||childOptions.access===options.access,
          'CODEX_BATCH_SCOPE','Child access differs from its authorized common source');
        const selection=await childOptions.resolveModelSelection(session.client);open();
        requireValue(selection.model===source.model&&selection.effort===source.effort,
          'CODEX_BATCH_MODEL','Shared child must preserve the initiating model and effort');
        requireValue(canonicalJSON(selection.main_execution_context??null)===canonicalJSON(source.selection.main_execution_context??null),
          'CODEX_BATCH_SCOPE','Shared child changed its initiating execution policy');
        const branchIndex=index++,receiptHome=await mkdtemp(join(childOptions.parent,'codex-batch-child-'));
        let thread,busy=false,closed=false,turns=0,lastTurn,turnPromise,modelTurnPromise,closePromise,commandSettled=false,commands;
        const audits=[],nativeCommandIds=new Set();
        const receipt={schema_version:1,owner:childOptions.owner,
          session_mode:'live_common_batch',source_thread_id:setup.thread_id,thread_id:thread?.thread_id??null,
          model:source.model,effort:source.effort,receipt_home:receiptHome,
          raw_observation:{supported:false,diagnostic:'thread/fork has no qualified raw-event opt-in; normalized notifications remain observable'}};
        let recordTail=Promise.resolve();
        const record=fields=>{
          const write=async()=>{Object.assign(receipt,{thread_id:thread?.thread_id??null},fields);await writeDurableJSON(join(receiptHome,'attempt.json'),receipt);};
          recordTail=recordTail.then(write,write);return recordTail;
        };
        const childOpen=()=>{open();requireValue(!closed,'CODEX_SESSION_CLOSED','Shared child ownership was revoked');childOptions.assertActive?.();};
        const makeCommands=()=>createCodexCommandBroker({binary:childOptions.binary,home:session.profile.home,cwd:childOptions.cwd,
          getClient:()=>session.client,
          access:childOptions.access,env:childOptions.env,allowedPaths:childOptions.allowedPaths,
          spoolRoot:childOptions.ownedCommandTemp?join(childOptions.cwd,'.workflow-command-output',digest(receiptHome)):join(receiptHome,'command-output'),
          ownedCommandTemp:childOptions.ownedCommandTemp,recoverToolErrors:true,
          getExecutionPolicy:()=>cooperativeExecutionPolicy(childOptions.access,selection.main_execution_context,{hostWorker:options.hostWorker===true}),
          getOutputBudget:()=>source.tool_output_budget,networkAccess:childOptions.commandNetworkAccess??false,
          shutdownGraceMs:childOptions.commandShutdownGraceMs,
          onOperation:operation=>childOptions.onEvent?.({method:'workflow/command',...Object.fromEntries(
            ['call_id','process_id','tool','args_sha256','phase','pending_process_ids','pending_preparations','forced','error_code','exit_code','output_bytes','duration_ms','runtime_temp']
              .filter(key=>Object.hasOwn(operation,key)).map(key=>[key,operation[key]]))})});
        commands=makeCommands();
        const commandAudit=()=>[...audits,...(commandSettled?[]:commands.audit())].map(source.command_audit_metadata);
        const retainNativeCommands=result=>{
          for(const item of result.command_items??[]){
            const key=typeof item.id==='string'?result.turn_id+'\0'+item.id:null;
            if(key&&nativeCommandIds.has(key))continue;
            if(key)nativeCommandIds.add(key);
            audits.push({
            ...(typeof item.id==='string'?{item_id:item.id}:{}),
            ...(typeof item.processId==='string'?{process_id:item.processId}:{}),
            ...(Number.isSafeInteger(item.durationMs)?{duration_ms:item.durationMs}:{}),
            status:item.status??null,exit_code:Number.isInteger(item.exitCode)?item.exitCode:null,
            cwd:item.cwd,command:item.command,output:item.aggregatedOutput,
            });
          }
        };
        const branch={
          profile:{...session.profile,receipt_home:receiptHome},commandAudit,
          get client(){return session.client;},
          async callTool(params){
            childOpen();await childOptions.authorize?.();childOpen();
            await childOptions.onEvent?.(codexEventMetadata({method:'item/tool/call',params:{...params,
              threadId:params.context.thread_id,turnId:params.context.turn_id}}));
            return commands.handles(params.tool)?commands.call(params.tool,params.arguments,params.callId):childOptions.toolBroker.call(params.tool,params.arguments,params.callId);
          },
          async interrupt(){await commands.interrupt();if(thread)await engine.interruptBranch(thread.thread_id);},
          async prepareHostCompletion(){
            childOpen();requireValue(!busy&&lastTurn,'CODEX_HOST_COMPLETION_BOUNDARY','Shared child needs its exact terminal turn');
            if(commandSettled)return;
            await commands.close();audits.push(...commands.audit());commandSettled=true;
            await record({status:'command_settled',turn_id:lastTurn});
          },
          async close(){
            if(closePromise)return closePromise;
            if(closed&&!branches.has(branchIndex))return;
            closed=true;
            const operation=(async()=>{
              const errors=[];
              const attempt=async action=>{try{await action();}catch(error){errors.push(error);}};
              await attempt(()=>childOptions.toolBroker?.revoke());
              if(thread)await attempt(()=>branch.interrupt());
              // An interrupted model turn must settle before its logical slot
              // is released. Its original turn failure is reported by turn().
              const pendingModel=modelTurnPromise??turnPromise;
              if(pendingModel)await attempt(async()=>{
                let timer;
                try{await Promise.race([pendingModel.then(()=>{},()=>{}),new Promise((_,reject)=>{
                  timer=setTimeout(()=>reject(Object.assign(new Error('Shared child turn did not settle after interruption; retain source'),{code:'CODEX_BATCH_STOP_UNCONFIRMED'})),8000);
                })]);}finally{clearTimeout(timer);}
              });
              await attempt(()=>commands.close());
              await attempt(async()=>{const result=await childOptions.toolBroker.quiesce();
                requireValue(result?.quiescent===true&&childOptions.toolBroker.isQuiescent()===true,'CODEX_BROKER_STOP_UNCONFIRMED','Shared child resource effects remain unsettled');if(result.error)throw result.error;});
              if(!errors.length&&thread)await attempt(()=>engine.closeBranch(thread.thread_id));
              await attempt(()=>record({status:errors.length?'cleanup_failed':'closed',turn_id:lastTurn??null}));
              failTogether(errors,'Shared child cleanup failed');branches.delete(branchIndex);
            })();closePromise=operation;
            try{return await operation;}finally{if(closePromise===operation)closePromise=null;}
          },
        };
        branches.set(branchIndex,branch);
        try{
          await childOptions.onSessionOwned?.(branch);childOpen();
          await childOptions.onProfilePrepared?.(branch.profile);childOpen();
          requireValue(canonicalJSON([...(childOptions.toolBroker?.tools()??[]),...commands.tools()])===canonicalJSON(source.tools),
            'CODEX_BATCH_TOOL_SURFACE','Shared child must preserve the exact ordinary MCP public schemas');
          childOpen();
          thread=await engine.fork(branchIndex);childOpen();
          await record({status:'fork_ready'});
          await childOptions.onEvent?.({method:'workflow/rawObservation',thread_id:thread.thread_id,status:'unsupported',diagnostic:receipt.raw_observation.diagnostic});
        }catch(error){try{await branch.close();}catch(cleanupError){throw new AggregateError([error,cleanupError],'Shared child setup and cleanup failed');}throw error;}
        const execute=async(text,{output_schema,explicit_sources=[]}={},continuation=false)=>{
          childOpen();requireValue(!busy&&turns<(childOptions.maxTurns??1)&&(continuation?turns>0:turns===0),
            'CODEX_SESSION_BUSY','Shared child requires its same-thread bounded continuation');
          requireValue(typeof text==='string'&&text.length>0&&text.length<=200000&&!explicit_sources.length,
            'CODEX_PROMPT_LIMIT','Shared child input must be bounded inline semantic text');
          busy=true;turns++;
          const operation=(async()=>{
            const transport=responseTransport.prepare(text,output_schema),input=[{type:'text',text:transport.text}],semantic=[{type:'text',text}];
            const audit={session_mode:'live_common_batch',executable_sha256:childOptions.expectedBinaryHash,thread_id:thread.thread_id,
              semantic_input_sha256:digest(canonicalJSON(semantic)),transported_semantic_input_sha256:digest(canonicalJSON(input)),
              input_sha256:digest(canonicalJSON(input)),submitted_input_sha256:digest(canonicalJSON(input)),
              response_transport:{api_schema_sha256:transport.schema_sha256,semantic_schema_sha256:digest(canonicalJSON(output_schema))}};
            await childOptions.authorize?.();childOpen();
            if(commandSettled){commands=makeCommands();commandSettled=false;}
            await record({status:'turn_submit',input_audit:audit,turn_input_receipts:[...(receipt.turn_input_receipts??[]),audit]});childOpen();
            source.tool_transport.assertHealthy();
            let result;
            try{
              // Keep the source SDK environment fixed: changing cwd triggers
              // Codex MCP replacement. Program/resource brokers enforce their
              // assigned cwd/scope. Ordinary native commands inherit source
              // cwd/roots and caller policy; their assignment is logical, not
              // a new OS isolation boundary, as with other native tools.
              const pending=engine.turnBranch(thread.thread_id,input,fixedTurnOptions);
              modelTurnPromise=pending;
              pending.then(()=>{if(modelTurnPromise===pending)modelTurnPromise=null;},()=>{if(modelTurnPromise===pending)modelTurnPromise=null;});
              result=await Promise.race([pending,source.tool_transport.failed]);
            }
            catch(error){if(error.branch_result){retainNativeCommands(error.branch_result);lastTurn=error.branch_result.turn_id;
              const {command_items:unusedCommands,...measuredResult}=error.branch_result;error.branch_result={...measuredResult,
              usage:usageFrom(error.branch_result.usage,error.branch_result.usage_unavailable_reason),audit,command_audit:commandAudit()};}throw error;}
            retainNativeCommands(result);lastTurn=result.turn_id;
            const {command_items:unusedCommands,...measuredResult}=result;
            const converted={...measuredResult,usage:usageFrom(result.usage),audit,command_audit:commandAudit()};
            try{
              await childOptions.onEvent?.({method:'workflow/turnUsage',thread_id:result.thread_id,turn_id:result.turn_id,
                usage_available:converted.usage.available,...Object.fromEntries(Object.values(usageFields).filter(key=>converted.usage[key]!==undefined).map(key=>[key,converted.usage[key]])),usage_basis:'restored_before_submit_total_delta'});
              await record({status:'completed',turn_id:lastTurn,usage:converted.usage,input_audit:audit,
                turn_input_receipts:[...receipt.turn_input_receipts.slice(0,-1),{...audit,turn_id:lastTurn}]});
              // Host owns semantic validation and its finite same-child repair.
              return {...converted,output:responseTransport.decode(result.output,output_schema)};
            }
            catch(error){error.branch_result=converted;throw error;}
          })();turnPromise=operation;
          try{return await operation;}finally{busy=false;turnPromise=null;}
        };
        branch.turn=(text,opts)=>execute(text,opts,false);branch.continueTurn=(text,opts)=>execute(text,opts,true);
        return branch;
      },
    };
  }catch(error){error.setup??=prepared?.setup??{usage:{available:false}};error.prefix_owner=owner;throw error;}
  finally{finish();}
}

Object.defineProperty(prepareCodexCommonBatch,'usageCapability',{value:Object.freeze({complete_usage:true,
  reason:'live_common_source_restored_counter_observed_before_branch_submit',responseTransport:Object.freeze({
    ...CODEX_NORMAL_PREFIX_USAGE_CAPABILITY.responseTransport,create_for_schema:createTypedBatchOutputTransport})})});
