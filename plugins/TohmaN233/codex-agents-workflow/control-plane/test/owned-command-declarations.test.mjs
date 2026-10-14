import test from 'node:test';
import fsPromises from 'node:fs/promises';
import {syncBuiltinESMExports} from 'node:module';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {createCodexSession} from '../lib/execution/codex-session.mjs';
import {createCodexCommandBroker} from '../lib/execution/codex-command-broker.mjs';
import {OWNED_MCP_NAMESPACE} from '../lib/execution/owned-tool-mcp.mjs';
import {ownedCommandDeclarations} from '../lib/execution/owned-command-declarations.mjs';
import {HostMainManager} from '../lib/execution/host-main-manager.mjs';
import {canonicalJSON,digest} from '../lib/workflow-revisions.mjs';

async function fixture(t,{toolMode='code_mode_only',submissionError,bindingMutation,beforeSubmit,resourceTools=[],
  sessionOptions={},resultText='neutral result',submissionMutation,runCommand=false,nativeCommand=false,returnedSandbox}={}) {
  const root=await mkdtemp(join(tmpdir(),'owned-command-declarations-'));
  const binary=join(root,'binary'),home=join(root,'home');
  await writeFile(binary,'fixture');await mkdir(home);
  const submissions=[],threads=[],launches=[],submissionReceipts=[],commands=[],policyEvents=[];
  let authorizations=0;
  const cwd=sessionOptions.cwd??root;
  const metadata={slug:'declarations-model',tool_mode:toolMode,base_instructions:'Unchanged ordinary instructions',
    supports_search_tool:true,supports_parallel_tool_calls:true,input_modalities:['text','image'],truncation_policy:{mode:'tokens',limit:10000}};
  const session=await createCodexSession({...sessionOptions,parent:root,binary,expectedBinaryHash:digest('fixture'),cwd,
    model:sessionOptions.resolveModelSelection?undefined:metadata.slug,effort:sessionOptions.resolveModelSelection?undefined:'high',
    access:sessionOptions.access??'read_only',env:{CODEX_HOME:home},maxTurns:3,dynamicToolFormat:'untagged_function',
    skillPolicy:sessionOptions.skillPolicy??{implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},modelMetadataReader:async()=>metadata,
    onEvent:async event=>{policyEvents.push(event);await sessionOptions.onEvent?.(event);},
    ...(resourceTools.length?{toolBroker:{tools:()=>structuredClone(resourceTools),revoke(){},async quiesce(){return {quiescent:true};}}}:{}),
    authorize:async()=>{await sessionOptions.authorize?.();if(++authorizations===3)await beforeSubmit?.(session);},
    clientFactory:(_binary,launch)=>{
      launches.push(launch);
      const client={pid:100,events:[],initialized(){},async close(){},async call(method,args={}){
        if(method==='initialize')return {};
        if(method==='account/read')return {account:{type:'chatgpt'},requiresOpenaiAuth:true};
        if(method==='model/list')return {data:[{model:metadata.slug,displayName:'fixture',description:'fixture',
          defaultReasoningEffort:'high',supportedReasoningEfforts:[{reasoningEffort:'high',description:'fixture'}]}]};
        if(method==='config/read'){
          const config={mcp_servers:{ordinary:{command:'ordinary',enabled:false}}};
          for(const override of launch.overrides){
            const assignment=override.indexOf('='),keys=override.slice(0,assignment).split('.');
            if(!['mcp_servers','features'].includes(keys[0]))continue;
            let target=config;for(const key of keys.slice(0,-1))target=target[key]??={};
            const raw=override.slice(assignment+1);target[keys.at(-1)]=JSON.parse(raw.startsWith('{')?raw.replace(/(\w+)=/g,'"$1":'):raw);
          }
          if(config.mcp_servers[OWNED_MCP_NAMESPACE]){
            config.mcp_servers[OWNED_MCP_NAMESPACE].enabled=true;bindingMutation?.(config);
          }
          return {config};
        }
        if(method==='skills/list')return {data:[{cwd,errors:[],skills:[]}]};
        if(method==='thread/start'){
          threads.push(structuredClone(args));return {model:metadata.slug,modelProvider:'openai',sandbox:{type:returnedSandbox??({'danger-full-access':'dangerFullAccess','workspace-write':'workspaceWrite','read-only':'readOnly'}[args.sandbox])},
            thread:{id:'declarations-thread-'+threads.length},instructionSources:[]};
        }
        if(method==='turn/start'){
          submissionReceipts.push(JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json'),'utf8')));
          submissionMutation?.(args);
          submissions.push(structuredClone(args));if(submissionError)throw submissionError;
          const id='declarations-turn-'+submissions.length;
          if(runCommand)await launch.onToolCall({threadId:args.threadId,turnId:id,callId:'neutral-command',
            tool:'run_workspace_command',arguments:{cmd:'neutral fixture'}});
          if(nativeCommand)client.events.push({method:'item/completed',params:{threadId:args.threadId,turnId:id,
            item:{type:'commandExecution',id:'native-command-'+submissions.length,processId:'native-process-'+submissions.length,
              cwd,command:'neutral native command',aggregatedOutput:'native capture',status:'completed',exitCode:0}}});
          client.events.push({method:'item/completed',params:{threadId:args.threadId,turnId:id,
            item:{type:'agentMessage',phase:'final_answer',text:typeof resultText==='function'?resultText(submissions.length):resultText}}});
          return {turn:{id}};
        }
        if(method==='command/exec'){
          if(args.command[1]==='-e'){const result=await promisify(execFile)(args.command[0],args.command.slice(1),{cwd:args.cwd,env:{...process.env,...args.env},windowsHide:true});return {...result,exitCode:0};}
          commands.push(structuredClone(args));
          const spec=JSON.parse(await readFile(args.command.at(-1),'utf8'));
          await writeFile(spec.output_path,'neutral capture');
          return {exitCode:0,stdout:JSON.stringify({schema_version:1,exit_code:0,output_bytes:15}),stderr:''};
        }
        assert.fail('Unexpected fixture method: '+method);
      },async waitFor(){return {method:'turn/completed',params:{turn:{id:'declarations-turn-'+submissions.length,status:'completed'}}};}};
      return client;
    }});
  t.after(async()=>{await session.close();await rm(root,{recursive:true,force:true});});
  const tools=createCodexCommandBroker({binary,home,cwd:root,access:'read_only',spoolRoot:join(root,'unused-spool'),getOutputBudget:()=>({max_result_bytes:10000})}).tools();
  return {session,submissions,threads,launches,metadata,tools,submissionReceipts,root,commands,policyEvents,
    receipt:async()=>JSON.parse(await readFile(join(session.profile.receipt_home,'attempt.json'),'utf8'))};
}

for(const access of ['bounded_write','read_only'])test('authenticated Main execution policy reaches actual thread and owned command RPC '+access,async t=>{
  const context={parent_thread_id:'authenticated-parent',sandbox_type:'danger-full-access'};
  const f=await fixture(t,{toolMode:'direct',runCommand:true,sessionOptions:{access,allowedPaths:access==='bounded_write'?['.']:[],
    ...(access==='bounded_write'?{ownedCommandTemp:true}:{}),
    resolveModelSelection:async()=>({model:'declarations-model',effort:'high',main_execution_context:context})}});
  const result=await f.session.turn('Neutral task');
  assert.equal(f.threads[0].sandbox,access==='bounded_write'?'danger-full-access':'read-only');
  assert.equal(f.commands.length,1,'inherited full access skips OS deny qualification, not a hidden probe');
  const requested=f.commands[0].sandboxPolicy;
  if(access==='bounded_write'){
    assert.deepEqual(requested,{type:'dangerFullAccess'});
    await writeFile(join(f.commands[0].env.TEMP,'neutral-temp-marker'),'neutral');
  }
  else {assert.equal(requested.type,'workspaceWrite');assert.equal(requested.writableRoots.length,1);
    assert(requested.writableRoots[0].startsWith(f.session.profile.receipt_home));}
  const receipt=await f.receipt();
  assert.equal(receipt.execution_policy.actual_thread_type,access==='bounded_write'?'dangerFullAccess':'readOnly');
  assert.equal(receipt.execution_policy.os_read_isolation,'not_claimed');
  assert.equal(receipt.execution_policy.command_boundary,access==='bounded_write'?'host_allowed_paths_and_workspace_audit':'capture_spool_only');
  assert.equal(result.command_audit[0].diagnostics.execution_policy.requested_command_policy.type,requested.type);
  assert.equal(result.command_audit[0].diagnostics.execution_policy.command_policy_observation,'request_only');
  assert(f.policyEvents.some(event=>event.method==='workflow/toolInterface'&&JSON.parse(event.diagnostic).execution_policy?.parent_thread_id===context.parent_thread_id));
});

test('native thread substituting inherited caller permissions fails before model turn',async t=>{
  const f=await fixture(t,{returnedSandbox:'workspaceWrite',sessionOptions:{access:'bounded_write',allowedPaths:['.'],
    resolveModelSelection:async()=>({model:'declarations-model',effort:'high',main_execution_context:{parent_thread_id:'actual-parent',sandbox_type:'danger-full-access'}})}});
  await assert.rejects(f.session.turn('Neutral task'),{code:'CODEX_SANDBOX_UNCONTROLLED'});
  const actual=(await f.receipt()).execution_policy;
  assert.equal(actual.thread_policy_verified,false);assert.equal(actual.actual_thread_type,'workspaceWrite');
  assert.equal(f.submissions.length,0);assert.equal(f.commands.length,0);
});

async function hostFixture(t,{toolMode='code_mode_only',tamperSemantic=false,resultText='{"value":"done"}'}={}){
  const root=await mkdtemp(join(tmpdir(),'owned-command-host-identity-')),workspace=join(root,'workspace');
  await mkdir(workspace);
  t.after(()=>rm(root,{recursive:true,force:true,maxRetries:3,retryDelay:100}));
  const schema={type:'object',properties:{value:{type:'string'}},required:['value'],additionalProperties:false};
  const definition={id:'work',type:'agent',executor:{kind:'main'},resources:[],outputs_schema:schema};
  const record={pins:{root:{workflow:{nodes:[definition]},resources:[],provenance:{kind:'fixture'}}},
    state:{main_actor:'logical-main',nodes:{work:{attempts:[]}}}};
  const envelope={node_id:'work',executor:definition.executor,allowed_skills:[],resources:[],
    skill_policy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},
    inputs:{task:'Exact Host semantic task'},access:'read_only',workspace,effective_allowed_paths:[],constraints:{},
    prompt_template:'{{task}}',outputs_schema:schema};
  const events=[],results=[],prompts=[],proposals=[];let commits=0,sessionFixture;
  const runtime={runs:{directory:()=>join(root,'runs'),read:async()=>record,
    saveExecutorResult:async(_id,_attempt,proposal)=>{proposals.push(proposal);return {artifact:'result.json',sha256:'a'.repeat(64)};}},
    authorizedExecution:async(_run,auth,select)=>({record,binding:{...select(record),...auth},envelope}),
    execution:async()=>envelope,reserveHostMainTurn:async()=>{},recordHostMainDispatchReceipt:async()=>{},
    recordExecutorEvent:async(_id,args)=>events.push(args.event),recordHostMainUsage:async()=>{},
    completeHostMainResult:async()=>{commits++;}};
  const strict={enabled:true,codex_binary:process.execPath,binary_sha256:'b'.repeat(64),
    authentication:{mode:'managed_chatgpt',api_key_env:''},main_model:'declarations-model',main_reasoning_effort:'high',inactivity_timeout_ms:0};
  const manager=new HostMainManager({register:async({config})=>config,configPath:join(root,'control-plane.json'),env:{},qualify:async()=>strict,
    getConfig:async()=>({global:{enabled:true},strict_executor:strict,providers:[]}),
    mainModelSelection:async()=>({model:'declarations-model',effort:'high'}),sessionFactory:async options=>{
      sessionFixture=await fixture(t,{toolMode,sessionOptions:options,resultText});
      for(const method of ['turn','continueTurn']){
        const original=sessionFixture.session[method];
        sessionFixture.session[method]=async(text,turnOptions)=>{
          prompts.push(text);
          const result=await original(tamperSemantic?text+' altered outside Host task':text,turnOptions);
          results.push(result);return result;
        };
      }
      return sessionFixture.session;
    }});
  t.after(()=>manager.close());
  const binding={run_id:'run',node_id:'work',attempt_id:'attempt'};
  const entry={runtime,runId:'run',stopping:false,status:'running'};
  t.after(()=>entry.session?.close());
  return {execute:()=>manager.executeNode(entry,{host_binding:binding,agent_packet:{prompt:envelope.prompt_template}}),
    results,prompts,proposals,events,commits:()=>commits,sessionFixture:()=>sessionFixture};
}

test('Host Main accepts direct owned catalog session with unchanged semantic task identity',async t=>{
  const f=await hostFixture(t);
  await f.execute();
  assert.equal(f.commits(),1);assert.equal(f.proposals.length,1);
  const result=f.results[0],submission=f.sessionFixture().submissions[0];
  assert.equal(submission.input.length,1);
  assert.equal(result.audit.input_sha256,digest(canonicalJSON([{type:'text',text:f.prompts[0]}])));
  assert.equal(result.audit.submitted_input_sha256,digest(canonicalJSON(submission.input)));
  assert.equal(result.audit.submitted_input_sha256,result.audit.input_sha256);
});

test('Host Main rejects altered semantic input from actual session despite valid declaration audit',async t=>{
  const f=await hostFixture(t,{tamperSemantic:true});
  await assert.rejects(f.execute(),{code:'HOST_MAIN_INPUT_MISMATCH'});
  assert.equal(f.commits(),0);assert.equal(f.proposals.length,0);
  const result=f.results[0],submission=f.sessionFixture().submissions[0];
  assert.equal(result.audit.input_sha256,digest(canonicalJSON([submission.input[0]])));
  assert.notEqual(result.audit.input_sha256,digest(canonicalJSON([{type:'text',text:f.prompts[0]}])));
  assert.equal(result.audit.submitted_input_sha256,digest(canonicalJSON(submission.input)));
});

test('Host Main correction accepts actual same-thread continuation without declaration replay',async t=>{
  const f=await hostFixture(t,{resultText:index=>index===1?'invalid JSON':'{"value":"done"}'});
  await f.execute();
  assert.equal(f.commits(),1);assert.equal(f.proposals.length,1);assert.equal(f.results.length,2);
  const {submissions,submissionReceipts}=f.sessionFixture();
  assert.equal(submissions[0].input.length,1);assert.equal(submissions[1].input.length,1);
  assert.equal(submissions[0].threadId,submissions[1].threadId);
  assert(f.events.some(event=>event.kind==='completion_invalid'));
  for(const [index,result] of f.results.entries()){
    const semantic=digest(canonicalJSON([{type:'text',text:f.prompts[index]}]));
    assert.equal(result.audit.input_sha256,semantic);
    assert.equal(result.audit.submitted_input_sha256,digest(canonicalJSON(submissions[index].input)));
    const planned=submissionReceipts[index].turn_input_receipts.at(-1);
    assert.equal(planned.input_sha256,semantic);assert.equal(planned.submitted_input_sha256,result.audit.submitted_input_sha256);
  }
});

test('Host Main direct session retains the unchanged semantic and submitted identity',async t=>{
  const f=await hostFixture(t,{toolMode:'direct'});
  await f.execute();
  assert.equal(f.commits(),1);
  const result=f.results[0],submission=f.sessionFixture().submissions[0];
  assert.deepEqual(submission.input,[{type:'text',text:f.prompts[0]}]);
  assert.equal(result.audit.input_sha256,digest(canonicalJSON(submission.input)));
  assert.equal(result.audit.submitted_input_sha256,result.audit.input_sha256);
  assert.equal(result.audit.owned_command_declarations,undefined);
});

test('first owned code-mode submission uses qualified direct catalog without duplicate command prose',async t=>{
  const resourceTools=[{name:'read_workflow_resource',description:'Existing resource tool',inputSchema:{type:'object',properties:{path:{type:'string'}}}}];
  const f=await fixture(t,{resourceTools}),text='Neutral semantic task';
  await f.session.turn(text);
  const input=f.submissions[0].input;
  assert.deepEqual(input[0],{type:'text',text});
  assert.equal(input.length,1,'The native direct catalog delivers tool definitions outside semantic task prose');
  assert.deepEqual(f.threads[0].dynamicTools,[]);
  const receipt=await f.receipt();assert.equal(receipt.tool_interface.owned_mcp_direct_tools,true);
  assert.deepEqual(receipt.tool_interface.owned_mcp_direct_namespaces,[`mcp__${OWNED_MCP_NAMESPACE}`,OWNED_MCP_NAMESPACE]);
  const endpointBinding=f.launches.at(-1).overrides.find(value=>value.includes('.env.CODEX_WORKFLOW_TOOL_ENDPOINT='));
  const response=await fetch(JSON.parse(endpointBinding.slice(endpointBinding.indexOf('=')+1)),{
    method:'POST',body:JSON.stringify({method:'tools/list'})});
  assert.equal(response.status,200);
  assert.deepEqual((await response.json()).tools,[...resourceTools,...f.tools]);
});

test('owned direct catalog input hashes are durable before submission across continuation and fresh threads',async t=>{
  const f=await fixture(t);
  const first=await f.session.turn('first'),continued=await f.session.continueTurn('correction'),fresh=await f.session.turn('fresh');
  assert.deepEqual(f.submissions[1].input,[{type:'text',text:'correction'}]);
  assert.equal(f.submissions[1].threadId,f.submissions[0].threadId);
  assert.notEqual(f.submissions[2].threadId,f.submissions[0].threadId);
  assert(f.submissions.every(submission=>submission.input.length===1));
  const receipt=await f.receipt();
  assert.equal(receipt.turn_input_receipts.length,3);
  for(const [index,result] of [first,continued,fresh].entries()){
    const submitted=f.submissions[index].input,entry=receipt.turn_input_receipts[index];
    assert.equal(result.audit.semantic_input_sha256,digest(canonicalJSON([submitted[0]])));
    assert.equal(result.audit.input_sha256,digest(canonicalJSON([submitted[0]])));
    assert.equal(result.audit.submitted_input_sha256,digest(canonicalJSON(submitted)));
    assert.equal(entry.semantic_input_sha256,result.audit.semantic_input_sha256);
    assert.equal(entry.input_sha256,result.audit.input_sha256);
    assert.equal(entry.submitted_input_sha256,result.audit.submitted_input_sha256);
    assert.equal(entry.turn_id,result.turn_id);
    const {turn_id,...planned}=entry;
    assert.deepEqual(f.submissionReceipts[index].turn_input_receipts.at(-1),planned);
    assert.equal(entry.owned_command_declarations,undefined);assert.equal(result.audit.owned_command_declarations,undefined);
  }
  const catalog=JSON.parse(await readFile(f.threads[0].config.model_catalog_json,'utf8'));
  assert.deepEqual(catalog.models[0],{...f.metadata,shell_type:'disabled'});
});

for(const toolMode of ['direct','function','unknown'])test(`${toolMode} dynamic tool path keeps submitted input and exact broker schemas`,async t=>{
  const f=await fixture(t,{toolMode}),result=await f.session.turn('direct task');
  assert.deepEqual(f.submissions[0].input,[{type:'text',text:'direct task'}]);
  assert.deepEqual(f.threads[0].dynamicTools,f.tools);
  assert.equal(result.audit.owned_command_declarations,undefined);
  assert.equal(result.audit.semantic_input_sha256,result.audit.input_sha256);
  assert.equal(result.audit.submitted_input_sha256,result.audit.input_sha256);
  assert(!f.launches.at(-1).overrides.some(value=>value.startsWith('mcp_servers.')));
});

for(const toolMode of ['code_mode_only','direct'])test(`${toolMode} semantic identity includes exact pinned Skill input without Host declarations`,async t=>{
  const skillRoot=await mkdtemp(join(tmpdir(),'owned-command-skill-identity-'));
  t.after(()=>rm(skillRoot,{recursive:true,force:true}));
  const source=join(skillRoot,'SKILL.md'),body='Exact pinned Skill instructions';await writeFile(source,body);
  const f=await fixture(t,{toolMode,sessionOptions:{allowedSkills:[{source_path:source,source_hash:digest(body),name:'identity-skill',files:{'SKILL.md':body}}]}});
  const result=await f.session.turn('Skill semantic task',{explicit_sources:[source]});
  const submitted=f.submissions[0].input,semantic=submitted.filter(item=>item.type==='skill'||item.type==='text'&&item.text==='Skill semantic task');
  assert.equal(semantic.length,2);assert.equal(semantic[1].type,'skill');assert.equal(semantic[1].name,'identity-skill');
  assert.equal(await readFile(semantic[1].path,'utf8'),body);
  assert.notEqual(semantic[1].path,source,'The original contract hashes the exact submitted pinned Skill path');
  const expected=digest(canonicalJSON(semantic));
  assert.equal(result.audit.input_sha256,expected);assert.equal(result.audit.semantic_input_sha256,expected);
  assert.notEqual(expected,digest(canonicalJSON([submitted[0]])),'Skill input must remain part of semantic identity');
  assert.equal(result.audit.submitted_input_sha256,digest(canonicalJSON(submitted)));
  const planned=f.submissionReceipts[0].turn_input_receipts[0];
  assert.equal(planned.input_sha256,expected);assert.equal(planned.submitted_input_sha256,result.audit.submitted_input_sha256);
  assert.equal(submitted.length,2);
  const continued=await f.session.continueTurn('Skill correction');
  assert.deepEqual(f.submissions[1].input,[{type:'text',text:'Skill correction'}]);
  assert.equal(continued.audit.input_sha256,digest(canonicalJSON(f.submissions[1].input)));
  assert.equal(continued.audit.submitted_input_sha256,continued.audit.input_sha256);
});

test('submitted input mutation is distinguishable from semantic identity and durable planned receipt',async t=>{
  const f=await fixture(t,{submissionMutation:args=>{
    args.input[0].text+=' altered in fixture transport';
  }});
  const result=await f.session.turn('Exact semantic input'),submitted=f.submissions[0].input;
  const planned=f.submissionReceipts[0].turn_input_receipts[0];
  assert.equal(result.audit.input_sha256,digest(canonicalJSON([{type:'text',text:'Exact semantic input'}])));
  assert.equal(planned.input_sha256,result.audit.input_sha256);
  assert.equal(planned.submitted_input_sha256,result.audit.submitted_input_sha256);
  assert.notEqual(digest(canonicalJSON(submitted)),planned.submitted_input_sha256);
  assert.equal(planned.owned_command_declarations,undefined);
  assert.equal(planned.turn_id,undefined);
  // This is a fixture transport fault, not a new runtime receipt validator.
  // The independently captured actual args expose its disagreement with the
  // already committed planned hashes; semantic input still has its own identity.
});

test('failed submission preserves planned declaration hashes without acknowledged turn and fences retries',async t=>{
  const original=Object.assign(new Error('fixture submission failed'),{code:'FIXTURE_SUBMISSION_FAILED'});
  const f=await fixture(t,{submissionError:original});
  await assert.rejects(f.session.turn('first'),error=>error===original);
  const receipt=await f.receipt(),entry=receipt.turn_input_receipts[0];
  assert.equal(receipt.status,'failed');assert.equal(receipt.error_code,original.code);
  assert.equal(entry.input_sha256,digest(canonicalJSON([f.submissions[0].input[0]])));
  assert.equal(entry.submitted_input_sha256,digest(canonicalJSON(f.submissions[0].input)));
  assert.equal(entry.turn_id,undefined);assert.deepEqual(receipt.turn_ids,[]);
  await assert.rejects(f.session.turn('retry'),{code:'CODEX_SESSION_CLOSED'});
  await assert.rejects(f.session.continueTurn('retry'),{code:'CODEX_SESSION_CLOSED'});
  assert.equal(f.submissions.length,1);
});

test('missing qualified execution namespace prevents declaration submission',async t=>{
  const f=await fixture(t,{bindingMutation:config=>delete config.mcp_servers[OWNED_MCP_NAMESPACE]});
  await assert.rejects(f.session.turn('first'),{code:'CODEX_MCP_BINDING'});
  assert.equal(f.threads.length,0);assert.equal(f.submissions.length,0);
});

test('changed direct owned catalog policy rejects before any thread or model submission',async t=>{
  for(const mutate of [config=>delete config.features.code_mode,config=>config.features.code_mode.direct_only_tool_namespaces.pop(),
    config=>{config.features.code_mode_only_strict_3p_tools=true;}]){
    const f=await fixture(t,{bindingMutation:mutate});
    await assert.rejects(f.session.turn('first'),error=>['CODEX_MCP_DIRECT_BINDING','CODEX_MCP_DIRECT_UNSUPPORTED'].includes(error.code));
    assert.equal(f.threads.length,0);assert.equal(f.submissions.length,0);
  }
});

test('input audit write failure prevents submission and preserves original filesystem errors',async t=>{
  let path;
  const f=await fixture(t,{beforeSubmit:async session=>{
    path=join(session.profile.receipt_home,'attempt.json');
    await rm(path);await mkdir(path);
  }});
  let failure;
  try{await f.session.turn('first');assert.fail('Audit failure must reject');}catch(error){failure=error;}
  assert(failure instanceof AggregateError);
  const causes=error=>error instanceof AggregateError?error.errors.flatMap(causes):[error];
  assert(causes(failure).some(error=>['EISDIR','EPERM','EACCES','ENOTEMPTY'].includes(error.code)));
  assert.equal(f.submissions.length,0);
  await assert.rejects(f.session.turn('retry'),{code:'CODEX_SESSION_CLOSED'});
  await assert.rejects(f.session.continueTurn('retry'),{code:'CODEX_SESSION_CLOSED'});
  await rm(path,{recursive:true});await f.session.close();
  assert.equal((await f.receipt()).status,'failed');
});

test('continuation receipt failure preserves original errors and fences the already owned thread before submission',async t=>{
  const f=await fixture(t);await f.session.turn('first');
  const path=join(f.session.profile.receipt_home,'attempt.json');await rm(path);await mkdir(path);
  let failure;
  try{await f.session.continueTurn('correction');assert.fail('Receipt failure must reject');}catch(error){failure=error;}
  assert(failure instanceof AggregateError);
  const causes=error=>error instanceof AggregateError?error.errors.flatMap(causes):[error];
  assert(causes(failure).some(error=>['EISDIR','EPERM','EACCES','ENOTEMPTY'].includes(error.code)));
  assert.equal(f.submissions.length,1);assert.equal(f.threads.length,1);
  await assert.rejects(f.session.turn('retry'),{code:'CODEX_SESSION_CLOSED'});
  await assert.rejects(f.session.continueTurn('retry'),{code:'CODEX_SESSION_CLOSED'});
  await rm(path,{recursive:true});await f.session.close();
  assert.equal((await f.receipt()).status,'failed');
});

test('declaration serialization derives callable names and preserves all supplied schema data without clipping',async t=>{
  const f=await fixture(t),tools=structuredClone(f.tools);
  tools[0].inputSchema.properties.program.description='Exact schema annotation 中文';
  const declarations=ownedCommandDeclarations('qualified_owned_namespace',tools),data=JSON.parse(declarations.input.text);
  assert.deepEqual(data.owned_command_declarations.tools,tools.map(tool=>({
    callable:'tools.mcp__qualified_owned_namespace__'+tool.name,...tool})));
  assert.equal(declarations.audit.bytes,Buffer.byteLength(declarations.input.text));
  assert.equal(declarations.audit.sha256,digest(declarations.input.text));
  assert.deepEqual(tools[0].inputSchema,data.owned_command_declarations.tools[0].inputSchema);
  tools[0].description='x'.repeat(32768);
  assert.throws(()=>ownedCommandDeclarations(OWNED_MCP_NAMESPACE,tools),{code:'CODEX_COMMAND_DECLARATIONS_LIMIT'});
  assert.throws(()=>ownedCommandDeclarations(OWNED_MCP_NAMESPACE,f.tools.slice(0,1)),{code:'CODEX_COMMAND_DECLARATIONS'});
  assert.throws(()=>ownedCommandDeclarations(OWNED_MCP_NAMESPACE,[...f.tools,...f.tools]),{code:'CODEX_COMMAND_DECLARATIONS'});
  assert.throws(()=>ownedCommandDeclarations('invalid-namespace',f.tools),{code:'CODEX_COMMAND_DECLARATIONS'});
  const invalid=structuredClone(f.tools);invalid[0].inputSchema.unsupported=undefined;
  assert.throws(()=>ownedCommandDeclarations(OWNED_MCP_NAMESPACE,invalid),{code:'INVALID_JSON'});
});

const completionOptions={access:'bounded_write',allowedPaths:['.'],ownedCommandTemp:true,resolveModelSelection:async()=>({model:'declarations-model',effort:'high',main_execution_context:{parent_thread_id:'authenticated-parent',sandbox_type:'danger-full-access'}})};

test('command completion boundary settles transport and renews only for same-thread correction',async t=>{
 const f=await fixture(t,{toolMode:'direct',runCommand:true,sessionOptions:completionOptions});
 await assert.rejects(f.session.prepareHostCompletion(),{code:'CODEX_HOST_COMPLETION_BOUNDARY'});
 const first=await f.session.turn('First neutral proposal');const launchCount=f.launches.length;
 await writeFile(join(f.commands[0].env.TEMP,'neutral-marker'),'neutral');
 await f.session.prepareHostCompletion();
 await assert.rejects(readFile(join(f.commands[0].env.TEMP,'neutral-marker')),{code:'ENOENT'});
 assert.equal(f.session.commandAudit().length,1);
 assert.equal((await f.receipt()).command_completion_boundary.turn_id,first.turn_id);
 await f.session.prepareHostCompletion();
 const second=await f.session.continueTurn('Exact same-session correction');
 assert.equal(second.thread_id,first.thread_id);assert.equal(f.threads.length,1);assert.equal(f.launches.length,launchCount);
 assert.equal(f.commands.length,2);assert.equal(f.session.commandAudit().length,2);
 assert.notEqual(f.session.commandAudit()[0].process_id,f.session.commandAudit()[1].process_id);
 assert.equal(second.command_audit.length,1);
 assert.deepEqual(second.command_audit.map(item=>[item.thread_id,item.turn_id]),[[second.thread_id,second.turn_id]]);
 assert.equal(first.command_audit.length,1);
 assert.equal(first.command_audit[0].turn_id,first.turn_id);
 const firstAudit=JSON.parse(await readFile(join(f.session.profile.receipt_home,`command-audit-${digest(first.turn_id)}.json`),'utf8'));
 const secondAudit=JSON.parse(await readFile(join(f.session.profile.receipt_home,`command-audit-${digest(second.turn_id)}.json`),'utf8'));
 assert.deepEqual(firstAudit.command_audit,first.command_audit);
 assert.deepEqual(secondAudit.command_audit,second.command_audit);
 await f.session.prepareHostCompletion();
 assert.equal((await f.receipt()).command_completion_boundary.generation,2);
 await f.session.close();assert.equal(f.session.commandAudit().length,2);
});

test('command completion boundary exposes failed command settlement without corrective renewal',async t=>{
 let fail=true;
 const f=await fixture(t,{toolMode:'direct',runCommand:true,sessionOptions:{...completionOptions,onEvent:async event=>{
   if(fail&&event.method==='workflow/command'&&event.phase==='close_settled')throw Object.assign(new Error('settlement receipt failed'),{code:'FIXTURE_SETTLEMENT_RECEIPT'});
 }}});
 await f.session.turn('Neutral first proposal');
 await assert.rejects(f.session.prepareHostCompletion(),{code:'CODEX_COMMAND_OBSERVATION_FAILED'});
 fail=false;
 await assert.rejects(f.session.prepareHostCompletion(),{code:'CODEX_COMMAND_OBSERVATION_FAILED'});
 await assert.rejects(f.session.continueTurn('Must not renew after failed settlement'),{code:'CODEX_HOST_COMPLETION_BOUNDARY'});
 assert.equal(f.submissions.length,1);assert.equal(f.commands.length,1);
 await f.session.close();
});

test('mixed native and broker commands retain exact per-turn ownership across corrections',async t=>{
 const f=await fixture(t,{toolMode:'direct',runCommand:true,nativeCommand:true,sessionOptions:completionOptions});
 const first=await f.session.turn('Neutral mixed first turn');await f.session.prepareHostCompletion();
 const second=await f.session.continueTurn('Neutral same-thread mixed correction');
 for(const result of [first,second]){
  assert.equal(result.command_audit.length,2);
  assert(result.command_audit.some(item=>item.item_id?.startsWith('native-command-')));
  assert(result.command_audit.some(item=>item.call_id==='neutral-command'));
  assert(result.command_audit.every(item=>item.thread_id===result.thread_id&&item.turn_id===result.turn_id));
 }
 assert.equal(f.session.commandAudit().length,4);
 assert.equal(f.session.commandAuditForTurn(first.thread_id,first.turn_id).length,2);
 assert.equal(f.session.commandAuditForTurn(second.thread_id,second.turn_id).length,2);
 await f.session.prepareHostCompletion();await f.session.close();
 assert.equal(f.session.commandAudit().length,4);
});

test('command completion boundary fences concurrent session cancellation before checker readiness',async t=>{
 let entered,release;const started=new Promise(resolve=>{entered=resolve;}),gate=new Promise(resolve=>{release=resolve;});
 const f=await fixture(t,{toolMode:'direct',runCommand:true,sessionOptions:{...completionOptions,onEvent:async event=>{
   if(event.method==='workflow/command'&&event.phase==='close_begin'){entered();await gate;}
 }}});
 await f.session.turn('Neutral first proposal');
 const settling=f.session.prepareHostCompletion();const rejected=assert.rejects(settling,{code:'CODEX_SESSION_CLOSED'});
 await started;const stopped=f.session.close();release();await rejected;await stopped;
 await assert.rejects(f.session.continueTurn('Cancelled correction'),{code:'CODEX_SESSION_CLOSED'});
 assert.equal(f.submissions.length,1);assert.equal(f.commands.length,1);assert.equal((await f.receipt()).close_phase,'closed');
});

test('command completion boundary propagates real broker spool removal failure',async t=>{
 const f=await fixture(t,{toolMode:'direct',runCommand:true,sessionOptions:completionOptions});
 await f.session.turn('Neutral proposal');
 const spool=join(f.session.profile.cwd??f.root,'.workflow-command-output',digest(f.session.profile.receipt_home));
 const original=fsPromises.rm;let failed=false;
 fsPromises.rm=async(path,...args)=>{if(String(path)===spool){failed=true;throw Object.assign(new Error('denied exact owned spool removal'),{code:'EACCES'});}return original(path,...args);};
 syncBuiltinESMExports();
 try{await assert.rejects(f.session.prepareHostCompletion(),{code:'EACCES'});}
 finally{fsPromises.rm=original;syncBuiltinESMExports();}
 assert.equal(failed,true);await assert.rejects(f.session.continueTurn('No hidden cleanup retry'),{code:'CODEX_HOST_COMPLETION_BOUNDARY'});
 assert.equal(f.submissions.length,1);await f.session.close();
});
