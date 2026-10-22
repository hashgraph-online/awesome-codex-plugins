import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm,lstat} from 'node:fs/promises';
import {join,dirname} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {digest,canonicalJSON} from '../lib/workflow-revisions.mjs';
import {createCodexSession,prepareCodexNormalPrefix,prepareCodexLiveCommonSource,CODEX_NORMAL_PREFIX_USAGE_CAPABILITY,CODEX_NORMAL_PREFIX_SETUP_SCHEMA} from '../lib/execution/codex-session.mjs';
import {OWNED_MCP_NAMESPACE} from '../lib/execution/owned-tool-mcp.mjs';
import {SHARED_PREFIX_OUTPUT_SCHEMA,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256} from '../lib/execution/shared-prefix-output-transport.mjs';
import {createTypedBatchOutputTransport} from '../lib/execution/typed-batch-output-transport.mjs';
import {createRunOwnedNormalHome,normalPrefixHome,qualifyNormalPrefixHome,sealNormalPrefix,closeNormalPrefixHome} from '../lib/execution/run-owned-normal-prefix.mjs';

const total=n=>({inputTokens:n,cachedInputTokens:Math.floor(n/2),outputTokens:2,reasoningOutputTokens:0});
// The fixture accepts the emitted CLI/config subset: JSON literals plus TOML
// inline tables. Keep quoted command text intact while translating table keys.
const fixtureToml=raw=>JSON.parse(raw.replace(/"(?:\\.|[^"\\])*"|[A-Za-z_][\w-]*\s*(?==)|=/g,token=>
  token.startsWith('"')?token:token==='='?':':JSON.stringify(token.trim())));
test('normal Host admission can reject unsupported accounting before invoking setup',async()=>{
  assert.equal(prepareCodexNormalPrefix.usageCapability,CODEX_NORMAL_PREFIX_USAGE_CAPABILITY);
  assert.equal(prepareCodexNormalPrefix.usageCapability.complete_usage,false);
  assert.match(prepareCodexNormalPrefix.usageCapability.reason,/no_qualified_independent/);
  assert.equal(prepareCodexNormalPrefix.usageCapability.responseTransport.api_schema_sha256,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256);
  assert.equal(prepareCodexNormalPrefix.usageCapability.responseTransport.setup_schema,CODEX_NORMAL_PREFIX_SETUP_SCHEMA);
  assert.throws(()=>{CODEX_NORMAL_PREFIX_SETUP_SCHEMA.properties.ready.const=false;},TypeError);
  assert.throws(()=>{prepareCodexNormalPrefix.usageCapability={complete_usage:true};},TypeError);
  assert.throws(()=>{CODEX_NORMAL_PREFIX_USAGE_CAPABILITY.complete_usage=true;},TypeError);
});
async function fixture(t,{baseline=100,toolMode='code_mode_only',shellType,ordinary=false,nativeCommands=false,failedTurn=false,useResponsesLite=false,sharedResponseTransport,baseConfig={},ignoreStandaloneOverride=false,configurationChange=()=>{},accountChange=value=>value,inventoryChange=value=>value,forkChange=()=>{},usageChange=updates=>updates,stallSetup=false,failSourceClose=false}={}){
  const root=await mkdtemp(join(tmpdir(),'normal-prefix-')),normalHome=join(root,'normal'),parent=join(root,'owned'),cwd=join(root,'shared'),binary=join(root,'binary');
  await mkdir(normalHome);await mkdir(cwd);await writeFile(binary,'fixture');let sourcePath,owner,cohort,child,turns=0,starts=0,ready,sourceCloseCalls=0,turnStarted;
  const setupStarted=new Promise(resolve=>turnStarted=resolve);
  const launches=[],forks=[],logins=[],rpcCalls=[],startArguments=[],turnArguments=[],parentReads=[],metadata={slug:'prefix-model',tool_mode:toolMode,...(shellType?{shell_type:shellType}:{}),use_responses_lite:useResponsesLite,base_instructions:'ordinary',truncation_policy:{mode:'tokens',limit:10000}};
  const base={model:'prefix-model',...baseConfig},clientFactory=(_binary,launch)=>{
    launches.push(launch);const events=[];const client={events,initialized(){},async close(){ready?.();if(turns>0&&launch.home!==normalHome){sourceCloseCalls++;if(failSourceClose)throw Object.assign(Error('fixture source shutdown failure'),{code:'FIXTURE_SOURCE_STOP'});}},async flushEvents(){},async call(method,args){
      rpcCalls.push({client_index:launches.indexOf(launch),method});
      if(method==='initialize')return {};
      if(method==='account/read')return accountChange({account:{type:'chatgpt'},requiresOpenaiAuth:true},launch);
      if(method==='account/login/start'){logins.push(args);return {};}
      if(method==='model/list')return inventoryChange({data:[{model:metadata.slug,supportedReasoningEfforts:[{reasoningEffort:'high'}]}]},launch);
      if(method==='hooks/list'){
        const declaration=launch.overrides?.find(value=>value.startsWith('hooks.PreToolUse='));
        const hook=declaration?fixtureToml(declaration.slice(declaration.indexOf('=')+1))[0]:null;
        const key='sessionFlags:pre_tool_use:0:0',currentHash='sha256:'+digest(canonicalJSON(hook));
        const stateOverride=launch.overrides?.find(value=>value.startsWith('hooks.state='));
        const state=stateOverride?fixtureToml(stateOverride.slice(stateOverride.indexOf('=')+1))[key]:null;
        return {data:[{cwd:launch.cwd,errors:[],warnings:[],hooks:hook?[{key,currentHash,source:'sessionFlags',eventName:'preToolUse',handlerType:'command',
          matcher:hook.matcher,command:hook.hooks[0].command,enabled:state?.enabled??true,trustStatus:state?.trusted_hash===currentHash?'trusted':'untrusted'}]:[]}]};
      }
      if(method==='thread/read'){assert.equal(launch.home,normalHome,'The initiating thread is readable only in the original normal library');parentReads.push(args);return {thread:{id:args.threadId}};}
      if(method==='config/read'){
        let config=structuredClone(base);if(launch.home!==normalHome){
          for(const line of (await readFile(join(launch.home,'config.toml'),'utf8')).trim().split('\n')){
            const at=line.indexOf(' = '),key=JSON.parse(line.slice(0,at)),raw=line.slice(at+3);
            config[key]=fixtureToml(raw);
          }
        }
        for(const override of launch.overrides??[]){if(ignoreStandaloneOverride&&override==='features.standalone_web_search=true')continue;const at=override.indexOf('='),keys=override.slice(0,at).split('.');let target=config;for(const k of keys.slice(0,-1))target=target[k]??={};target[keys.at(-1)]=fixtureToml(override.slice(at+1));}
        if(config.mcp_servers?.[OWNED_MCP_NAMESPACE]){config.mcp_servers[OWNED_MCP_NAMESPACE].enabled=true;config.mcp_servers[OWNED_MCP_NAMESPACE].environment_id='local';config.mcp_servers[OWNED_MCP_NAMESPACE].tool_timeout_sec=null;config.features.network_proxy??=null;}
        if(launch.overrides?.some(value=>value.startsWith('model_catalog_json=')))configurationChange(config);
        return {config};
      }
      if(method==='skills/list')return {data:[{cwd:launch.cwd,skills:[],errors:[]}]};
      if(method==='thread/start'){
        starts++;startArguments.push(args);assert.equal(args.ephemeral,ordinary);sourcePath=join(launch.home,'source.jsonl');await writeFile(sourcePath,'neutral completed stored history');
        return {model:metadata.slug,modelProvider:'openai',sandbox:{type:{'read-only':'readOnly','workspace-write':'workspaceWrite','danger-full-access':'dangerFullAccess'}[args.sandbox]},thread:{id:'source',path:sourcePath,ephemeral:false},instructionSources:[]};
      }
      if(method==='thread/fork'){
        forks.push(args);assert.equal(args.excludeTurns,true);
        assert.equal(Object.hasOwn(args.config.mcp_servers[OWNED_MCP_NAMESPACE],'tool_timeout_sec'),false,'Nullable effective defaults cannot be passed as TOML overrides');
        const result={cwd:launch.cwd,runtimeWorkspaceRoots:[launch.cwd],model:metadata.slug,modelProvider:'openai',sandbox:{type:'readOnly'},thread:{id:'child',ephemeral:true,forkedFromId:'source',turns:[]},instructionSources:[]};forkChange(result);return result;
      }
      if(method==='turn/start'){
        assert.deepEqual(args.outputSchema,sharedResponseTransport?.api_schema??(ordinary?{type:'string'}:SHARED_PREFIX_OUTPUT_SCHEMA));
        turnArguments.push(args);
        turns++;const source=args.threadId==='source',id=ordinary?'ordinary-turn-'+turns:source?'source-turn':'child-turn';
        if(source&&stallSetup)await new Promise(resolve=>{ready=resolve;turnStarted();});
        const update=(value,last)=>({method:'thread/tokenUsage/updated',params:{threadId:args.threadId,turnId:id,tokenUsage:{total:value,last}}});
        const childTotal={...total(baseline+30),outputTokens:4};
        events.push(...(source?[update(total(100),total(100))]:usageChange([update(childTotal,total(30))])),
          {method:'item/completed',params:{threadId:args.threadId,turnId:id,item:{type:'agentMessage',phase:'final_answer',text:sharedResponseTransport?JSON.stringify({results:[]}):JSON.stringify({json_result:source?'{"ready":true}':'"neutral child"'})}}});
        if(nativeCommands){
          const item={type:'commandExecution',id:'reused-native-id',command:'original help',exitCode:0,aggregatedOutput:'x'.repeat(5000)};
          events.push({method:'item/completed',params:{threadId:'foreign',turnId:id,item}},
            {method:'item/completed',params:{threadId:args.threadId,turnId:'foreign-turn',item}},
            ...[1,2].map(()=>({method:'item/completed',params:{threadId:args.threadId,turnId:id,item}})));
        }
        events.push({method:'turn/completed',params:{threadId:args.threadId,turn:{id,status:failedTurn?'failed':'completed'}}});
        return {turn:{id}};
      }
      assert.fail('Unexpected fixture RPC '+method);
    },async waitFor(match){const found=events.find(match);if(found)return found;return {method:'turn/completed',params:{threadId:turns===1?'source':'child',turn:{id:turns===1?'source-turn':'child-turn',status:'completed'}}};}};return client;
  };
  const options={parent,owner:{run_id:'neutral-run',attempt_id:'neutral-attempt'},cwd,binary,expectedBinaryHash:digest('fixture'),model:metadata.slug,effort:'high',access:'read_only',dynamicToolFormat:'untagged_function',
    env:{CODEX_HOME:normalHome},sharedResponseTransport,skillPolicy:{mode:'cooperative',implicit:'deny',ambient_allow:[],shadowed_skill_paths:[]},modelMetadataReader:async()=>metadata,clientFactory,
    hostAuth:{async credentials(){return {accessToken:'private-fixture-token',chatgptAccountId:'fixture-account',chatgptPlanType:'fixture'};}},onPrefixOwned:value=>owner=value};
  t.after(async()=>{failSourceClose=false;ready?.();await child?.close();await cohort?.close();await owner?.close();await rm(root,{recursive:true,maxRetries:3,retryDelay:100});});
  return {root,normalHome,options,launches,forks,logins,rpcCalls,startArguments,turnArguments,parentReads,get starts(){return starts;},get turns(){return turns;},get owner(){return owner;},get sourcePath(){return sourcePath;},
    get sourceCloseCalls(){return sourceCloseCalls;},setupStarted,
    async prepare(){return cohort=await prepareCodexNormalPrefix(options,'Only neutral shared setup');},
    async prepareLive(){return cohort=await prepareCodexLiveCommonSource(options,'Only neutral shared setup');},
    async worker(prefix){const item=join(root,'item');await mkdir(item,{recursive:true});child=await createCodexSession({...options,cwd:item,prefix,onPrefixOwned:undefined});const turn=child.turn;child.turn=(text,args={})=>turn(text,{output_schema:{type:'string'},...args});return child;}};
}

test('writable Host common source selects ordinary execution without changing its initiating Main policy',async t=>{
  const f=await fixture(t);f.options.hostWorker=true;f.options.sourceExecutionAccess='bounded_write';
  f.options.resolveModelSelection=async()=>({model:'prefix-model',effort:'high',main_execution_context:{parent_thread_id:'main',sandbox_type:'workspace-write'}});
  await f.prepare();
  assert.equal(f.startArguments[0].sandbox,'danger-full-access');
  const source=f.launches.find(item=>item.home!==f.normalHome&&item.onToolCall);
  assert(source,'Owned model still uses its private common context library');
});

test('live common preparation retains two ordinary clients plus two metadata clients with exact execution qualification',async t=>{
  const f=await fixture(t,{shellType:'unified_exec',useResponsesLite:true}),cohort=await f.prepareLive();
  assert.equal(f.launches.length,4,'One discovery, two model-free hook inventories and one private execution client');
  const count=method=>f.rpcCalls.filter(call=>call.method===method).length;
  assert.equal(count('initialize'),4);assert.equal(count('hooks/list'),3);assert.equal(count('config/read'),2);
  assert.equal(count('account/login/start'),2);assert.equal(count('account/read'),5);assert.equal(count('model/list'),2);
  for(const index of [1,2])assert.deepEqual(f.rpcCalls.filter(call=>call.client_index===index).map(call=>call.method),['initialize','hooks/list']);
  assert.equal(f.launches[0].home,f.normalHome);assert.notEqual(f.launches.at(-1).home,f.normalHome);
  assert(f.launches.at(-1).overrides.some(value=>value.startsWith('model_catalog_json=')));
  assert(f.launches.at(-1).overrides.some(value=>value.startsWith('hooks.state=')));
  assert.equal(cohort.source.tool_interface.standalone_web_search.effective_enabled,true);
  assert.equal(cohort.setup.audit.native_shell_execution,'unified_exec');
  assert.equal(cohort.setup.audit.command_declaration_basis,'inherited_native_shell');
});

test('live common source uses its trusted typed setup transport and retains semantic readiness',async t=>{
  const itemSchema={type:'object',properties:{markdown:{type:'string'}},required:['markdown'],additionalProperties:false};
  const sharedResponseTransport=createTypedBatchOutputTransport(itemSchema),f=await fixture(t,{shellType:'unified_exec',sharedResponseTransport}),cohort=await f.prepareLive();
  assert.deepEqual(f.turnArguments[0].outputSchema,sharedResponseTransport.api_schema);
  assert.match(f.turnArguments[0].input[0].text,/return results=\[\]/);
  assert.equal(cohort.setup.output,'{"ready":true}');
  assert.equal(cohort.setup.audit.response_transport.api_schema_sha256,sharedResponseTransport.api_schema_sha256);
  assert.equal(f.launches.length,2);
});

for(const [name,configurationChange]of Object.entries({unknown_feature:value=>value.features.unexpected=true,changed_storage:value=>value.sqlite_home='foreign',changed_catalog:value=>value.model_catalog_json='foreign',unknown_binding:value=>value.mcp_servers[OWNED_MCP_NAMESPACE].unexpected=true,unknown_nullable_binding:value=>value.mcp_servers[OWNED_MCP_NAMESPACE].unexpected=null,unknown_nullable_feature:value=>value.features.unexpected=null,changed_environment:value=>value.mcp_servers[OWNED_MCP_NAMESPACE].environment_id='remote'}))test(`merged live source rejects actual execution configuration ${name} before paid turn`,async t=>{
  const f=await fixture(t,{shellType:'unified_exec',configurationChange});
  await assert.rejects(f.prepareLive(),{code:'CODEX_PREFIX_CONFIG_UNCONTROLLED'});assert.equal(f.starts,0);assert.equal(f.turns,0);
});

for(const [name,configurationChange]of Object.entries({unknown_hook:value=>value.hooks.unexpected=true,
  unknown_nullable_hook:value=>value.hooks.PreToolUse[0].hooks[0].unexpected=null,
  changed_hook_command:value=>value.hooks.PreToolUse[0].hooks[0].command='foreign',
  changed_hook_matcher:value=>value.hooks.PreToolUse[0].matcher='.*',
  changed_hook_trust:value=>Object.values(value.hooks.state)[0].trusted_hash='sha256:'+'0'.repeat(64)}))test(`merged live source rejects scoped web ${name} before paid turn`,async t=>{
  const f=await fixture(t,{shellType:'unified_exec',useResponsesLite:true,configurationChange});
  await assert.rejects(f.prepareLive(),{code:'CODEX_PREFIX_CONFIG_UNCONTROLLED'});assert.equal(f.starts,0);assert.equal(f.turns,0);
});

test('merged live source checks exact account model and metadata on the retained clients',async t=>{
  for(const boundary of ['account','model','metadata','account_id']){
    const f=await fixture(t,{shellType:'unified_exec',accountChange:(value,launch)=>boundary==='account'&&launch.overrides?.length?{account:{type:'apiKey'},requiresOpenaiAuth:true}:value,
      inventoryChange:(value,launch)=>boundary==='model'&&launch.overrides?.length?{data:[]}:value});
    if(boundary==='metadata')f.options.modelMetadataReader=async()=>({slug:'foreign'});
    if(boundary==='account_id'){let calls=0;f.options.hostAuth.credentials=async()=>({accessToken:'private-fixture-token',chatgptAccountId:++calls===1?'first':'changed'});}
    const expected={account:'CODEX_AUTH_MODE',model:'CODEX_MODEL_UNAVAILABLE',metadata:'DIRECT_TOOL_CATALOG_MODEL',account_id:'HOST_AUTH_ACCOUNT_CHANGED'}[boundary];
    await assert.rejects(f.prepareLive(),{code:expected});assert.equal(f.starts,0);assert.equal(f.turns,0);
  }
});

test('private execution configuration qualifies only its exact declared overlay',async t=>{
  const f=await fixture(t),home=await createRunOwnedNormalHome({parent:f.options.parent,owner:f.options.owner,cwd:f.options.cwd,normalHome:f.normalHome,configuration:{config:{model:'prefix-model',features:{standalone_web_search:false}}}});
  const privateHome=normalPrefixHome(home),base={model:'prefix-model',features:{standalone_web_search:false},sqlite_home:privateHome.sqlite_home,log_dir:join(privateHome.home,'logs'),model_catalog_json:join(f.normalHome,'models_cache.json')};
  const overlay={model_catalog_json:join(f.options.parent,'models-direct.json'),features:{standalone_web_search:true,code_mode_host:true,code_mode:{direct_only_tool_namespaces:['codex_agents_workflow_owned']}},mcp_servers:{codex_agents_workflow_owned:{command:process.execPath,args:['known-owned-stdio'],env:{CODEX_WORKFLOW_TOOL_ENDPOINT:'http://127.0.0.1:1/private'},environment_id:'local',enabled:true,supports_parallel_tool_calls:true,default_tools_approval_mode:'approve'}}};
  const actual={...base,...overlay,features:{...base.features,...overlay.features}};
  await qualifyNormalPrefixHome(home,{config:actual},{overlay});
  for(const mutate of [value=>value.features.unexpected=true,value=>value.sqlite_home='foreign',value=>value.model_catalog_json='foreign',value=>value.mcp_servers.codex_agents_workflow_owned.env.CODEX_WORKFLOW_TOOL_ENDPOINT='foreign',value=>value.mcp_servers.codex_agents_workflow_owned.unexpected=true]){
    const changed=structuredClone(actual);mutate(changed);await assert.rejects(qualifyNormalPrefixHome(home,{config:changed},{overlay}),{code:'CODEX_PREFIX_CONFIG_UNCONTROLLED'});
  }
  await assert.rejects(qualifyNormalPrefixHome(home,{config:actual},{overlay:{...overlay,features:{...overlay.features,unexpected:true}}}),{code:'CODEX_PREFIX_CONFIG_OVERLAY'});
  const scoped={...overlay,features:{...overlay.features,hooks:true},hooks:{PreToolUse:[{matcher:'^webrun$',hooks:[{type:'command',command:'node -e "known bootstrap"',timeout:10,async:false}]}],
    state:{'sessionFlags:pre_tool_use:0:0':{enabled:true,trusted_hash:'sha256:'+'a'.repeat(64)}}}};
  const scopedActual={...actual,features:{...actual.features,hooks:true},hooks:structuredClone(scoped.hooks)};
  scopedActual.hooks.PreToolUse[0].hooks[0].commandWindows=null;scopedActual.hooks.PreToolUse[0].hooks[0].statusMessage=null;
  await qualifyNormalPrefixHome(home,{config:scopedActual},{overlay:scoped});
  for(const mutate of [value=>value.hooks.unknown=true,value=>value.hooks.PreToolUse[0].hooks[0].command='changed',
    value=>value.hooks.PreToolUse[0].hooks[0].unknown=null,value=>value.hooks.PreToolUse[0].matcher='.*',
    value=>value.hooks.state['sessionFlags:pre_tool_use:0:0'].enabled=false]){
    const changed=structuredClone(scopedActual);mutate(changed);
    await assert.rejects(qualifyNormalPrefixHome(home,{config:changed},{overlay:scoped}),{code:'CODEX_PREFIX_CONFIG_UNCONTROLLED'});
  }
  for(const mutate of [value=>value.hooks.PreToolUse[0].matcher='.*',value=>value.hooks.PreToolUse[0].hooks[0].unknown=true,
    value=>value.hooks.state.extra={enabled:true,trusted_hash:'sha256:'+'b'.repeat(64)}]){
    const changed=structuredClone(scoped);mutate(changed);
    await assert.rejects(qualifyNormalPrefixHome(home,{config:scopedActual},{overlay:changed}),{code:'CODEX_PREFIX_CONFIG_OVERLAY'});
  }
  await closeNormalPrefixHome(home);
});

test('ordinary native shell survives actual session preparation without broker declarations in shared input',async t=>{
  const f=await fixture(t,{shellType:'unified_exec'}),cohort=await f.prepareLive();
  assert.deepEqual(cohort.source.tool_interface.native_shell,{source:'unified_exec',execution:'unified_exec'});
  const catalog=JSON.parse(await readFile(join(cohort.session.profile.receipt_home,'models-direct.json'),'utf8'));
  assert.equal(catalog.models[0].shell_type,'unified_exec');
  assert.equal(f.turnArguments[0].input.length,1);
  assert.equal(cohort.setup.audit.owned_command_declarations,undefined);
  assert.equal(cohort.source.command_declarations_sha256,undefined);
});

test('ordinary native command audit retains bounded evidence across correction and failed terminal turns',async t=>{
  for(const failedTurn of [false,true]){
    const f=await fixture(t,{ordinary:true,nativeCommands:true,failedTurn,shellType:'unified_exec'});
    const session=await createCodexSession({...f.options,maxTurns:2});
    try{
      if(failedTurn)await assert.rejects(session.turn('neutral',{output_schema:{type:'string'}}),{code:'CODEX_TURN_FAILED'});
      else{
        await session.turn('neutral',{output_schema:{type:'string'}});
        await session.prepareHostCompletion();
        await session.continueTurn('exact correction',{output_schema:{type:'string'}});
      }
      const commands=session.commandAudit();assert.equal(commands.length,failedTurn?1:2);
      assert(commands.every(item=>item.item_id==='reused-native-id'&&item.output.length<=2000));
    }finally{await session.close();}
  }
});

test('standalone web search adapter qualifies live source after original private-home checks without enabling disabled search',async t=>{
  const f=await fixture(t,{useResponsesLite:true,baseConfig:{web_search:'disabled',features:{standalone_web_search:false}}}),cohort=await f.prepareLive();
  const execution=f.launches.at(-1);
  assert(execution);
  assert.equal(f.launches.filter(launch=>launch.overrides?.includes('features.standalone_web_search=true')).length,3);
  assert(execution.overrides.some(value=>value.startsWith('hooks.state=')));
  assert(f.launches.filter(launch=>!launch.overrides?.some(value=>value.startsWith('model_catalog_json='))).every(launch=>!launch.overrides?.includes('features.standalone_web_search=true')));
  const config=await cohort.session.client.call('config/read',{});
  assert.equal(config.config.web_search,'disabled');assert.equal(config.config.features.standalone_web_search,true);
  const privateConfig=await readFile(join(execution.home,'config.toml'),'utf8');
  assert.match(privateConfig,/"standalone_web_search" = false/);
  assert.equal(cohort.source.tool_interface.standalone_web_search.effective_enabled,true);
  assert.equal(cohort.source.model,'prefix-model');assert.equal(cohort.source.effort,'high');
  assert.equal(f.turnArguments[0].effort,'high');assert.equal(f.sourceCloseCalls,0);
});

test('standalone web search adapter preserves qualified feature in detached fork configuration and receipts',async t=>{
  const f=await fixture(t,{useResponsesLite:true,baseConfig:{web_search:'cached',features:{standalone_web_search:false}}}),cohort=await f.prepare();
  const worker=await f.worker(cohort.prefix);await assert.rejects(worker.turn('Only this neutral item'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  assert.equal(f.forks[0].config.features.standalone_web_search,true);
  const config=await worker.client.call('config/read',{});assert.equal(config.config.web_search,'cached');
  const receipt=JSON.parse(await readFile(join(worker.profile.receipt_home,'attempt.json'),'utf8'));
  const {response_default,...standalone}=receipt.tool_interface.standalone_web_search;
  assert.deepEqual(standalone,{source:'authenticated_model_metadata',
    basis:'use_responses_lite_and_javascript_aggregation',source_use_responses_lite:true,execution_override:true,effective_enabled:true});
  assert.deepEqual(response_default,{response_length:'short',scope:['search_query','open','find'],explicit_values:'preserved',mixed_operations:'preserved',
    audit_path:join(worker.profile.receipt_home,'web-queries.jsonl'),normal_hook_count:0});
});

test('standalone web search adapter rejects ineffective execution override before a source thread or paid turn',async t=>{
  const f=await fixture(t,{useResponsesLite:true,ignoreStandaloneOverride:true,baseConfig:{features:{standalone_web_search:false}}});
  await assert.rejects(f.prepareLive(),{code:'CODEX_STANDALONE_WEB_SEARCH_CONFIG'});
  assert.equal(f.starts,0);assert.equal(f.turns,0);
});

for(const baseline of [0,100])test(`prefix uses one private library and independent ephemeral child; actual inferred baseline ${baseline}`,async t=>{
  const f=await fixture(t,{baseline}),cohort=await f.prepare();assert.equal(f.turns,1);assert.equal(cohort.setup.usage.input_tokens,100);
  const worker=await f.worker(cohort.prefix);await assert.rejects(worker.turn('Only this neutral item'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  assert.equal(f.starts,1);assert.equal(f.forks.length,1);
  assert.equal(worker.profile.home,dirname(f.sourcePath));assert.equal(worker.profile.user_owned_home,false);assert.equal(f.forks[0].path,f.sourcePath);assert.equal(f.forks[0].lastTurnId,'source-turn');assert.equal(f.forks[0].ephemeral,true);
  assert.equal(f.forks[0].dynamicTools,undefined);assert.equal(f.forks[0].experimentalRawEvents,undefined);assert(f.forks[0].config.mcp_servers[OWNED_MCP_NAMESPACE]);
  const receipt=JSON.parse(await readFile(join(worker.profile.receipt_home,'attempt.json')));assert.equal(receipt.raw_observation.supported,false);assert.equal(receipt.prefix_fork.inherited_counter_baseline.inputTokens,baseline);
  assert.equal(receipt.usage.available,false);assert.equal(receipt.prefix_fork.usage_evidence.observed_usage.input_tokens,30);
  assert.equal(receipt.prefix_fork.usage_evidence.observed_usage.cached_input_tokens,15);
  assert.equal(f.turnArguments[0].input.length,2);assert.equal(f.turnArguments[1].input.length,1);assert.equal(receipt.prefix_fork.command_declarations_inherited,true);
  assert.equal(receipt.prefix_fork.command_declarations_sha256,cohort.setup.prefix_source.command_declarations_sha256);
  assert.equal(receipt.turn_input_receipts[0].response_transport.api_schema_sha256,SHARED_PREFIX_OUTPUT_SCHEMA_SHA256);
  assert.equal(f.turnArguments[0].outputSchema.required[0],'json_result');assert.deepEqual(f.turnArguments[0].outputSchema,f.turnArguments[1].outputSchema);
  const sourceAudit=cohort.setup.audit,childAudit=receipt.turn_input_receipts[0];
  assert.equal(sourceAudit.response_transport.semantic_schema_sha256,digest(canonicalJSON(CODEX_NORMAL_PREFIX_SETUP_SCHEMA)));
  assert.equal(childAudit.response_transport.semantic_schema_sha256,digest(canonicalJSON({type:'string'})));
  const transport=prepareCodexNormalPrefix.usageCapability.responseTransport;
  assert.equal(sourceAudit.transported_semantic_input_sha256,digest(canonicalJSON([{type:'text',text:transport.prepare('Only neutral shared setup',transport.setup_schema).text}])));
  assert.equal(childAudit.transported_semantic_input_sha256,digest(canonicalJSON([{type:'text',text:transport.prepare('Only this neutral item',{type:'string'}).text}])));
  assert.equal(sourceAudit.semantic_input_sha256,digest(canonicalJSON([{type:'text',text:'Only neutral shared setup'}])));
  assert.equal(sourceAudit.input_sha256,digest(canonicalJSON(f.turnArguments[0].input)));
  assert.equal(childAudit.semantic_input_sha256,digest(canonicalJSON([{type:'text',text:'Only this neutral item'}])));
  assert.equal(childAudit.input_sha256,digest(canonicalJSON(f.turnArguments[1].input)));
  assert.equal(childAudit.transported_semantic_input_sha256,childAudit.input_sha256);
  assert.notEqual(sourceAudit.input_sha256,sourceAudit.semantic_input_sha256);
  assert.notEqual(childAudit.input_sha256,childAudit.semantic_input_sha256);
  assert.equal(worker.shutdownState().close_confirmed,true);await worker.close();await cohort.close();await cohort.close();await assert.rejects(lstat(f.sourcePath),{code:'ENOENT'});
  assert(f.logins.length>=2);assert(f.launches.filter(v=>v.home!==f.normalHome).every(v=>typeof v.onAuthRefresh==='function'));
});
test('forged or changed prefix is rejected before a worker model turn',async t=>{
  const f=await fixture(t),cohort=await f.prepare();await assert.rejects(f.worker({}),{code:'CODEX_PREFIX_HANDLE'});assert.equal(f.turns,1);
  const owned=await createCodexSession({...f.options,prefix:cohort.prefix});await writeFile(f.sourcePath,'changed');
  try{await assert.rejects(owned.turn('neutral'),{code:'CODEX_PREFIX_CHANGED'});assert.equal(f.turns,1);}finally{await owned.close();}
});
test('private source rejects direct dynamic tools before a model turn and exposes failed setup accounting',async t=>{
  const f=await fixture(t,{toolMode:'direct'});await assert.rejects(f.prepare(),error=>{assert.equal(error.code,'CODEX_PREFIX_TOOL_MODE');assert.equal(error.setup.usage.available,false);return true;});assert.equal(f.turns,0);assert.equal(f.starts,0);
});
test('foreign fork identity fails before child model submission',async t=>{
  const f=await fixture(t,{forkChange:r=>r.thread.forkedFromId='foreign'}),cohort=await f.prepare(),worker=await f.worker(cohort.prefix);
  await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_FORK_UNCONTROLLED'});assert.equal(f.turns,1);
});

test('fork reconciles multiple responses, exact duplicates and initial/terminal zero estimates',async t=>{
  const zero={inputTokens:0,cachedInputTokens:0,cacheWriteInputTokens:0,outputTokens:0,reasoningOutputTokens:0};
  const initial={inputTokens:100,cachedInputTokens:50,cacheWriteInputTokens:7,outputTokens:2,reasoningOutputTokens:0};
  const one={inputTokens:30,cachedInputTokens:15,cacheWriteInputTokens:3,outputTokens:2,reasoningOutputTokens:1};
  const two={inputTokens:20,cachedInputTokens:8,cacheWriteInputTokens:2,outputTokens:4,reasoningOutputTokens:2};
  const add=(a,b)=>Object.fromEntries(Object.keys(a).map(k=>[k,a[k]+b[k]]));
  const f=await fixture(t,{usageChange:updates=>{
    const event=(total,last)=>({...updates[0],params:{...updates[0].params,tokenUsage:{total,last}}});
    const first=event(add(initial,one),one),final=add(add(initial,one),two);
    return [event(initial,zero),first,structuredClone(first),event(final,two),event(final,zero)];
  }}),cohort=await f.prepare(),worker=await f.worker(cohort.prefix);
  await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  const receipt=JSON.parse(await readFile(join(worker.profile.receipt_home,'attempt.json')));
  assert.deepEqual(receipt.prefix_fork.usage_evidence.observed_usage,{input_tokens:50,cached_input_tokens:23,cache_write_input_tokens:5,output_tokens:6,reasoning_output_tokens:3});
  assert.equal(receipt.prefix_fork.usage_evidence.response_update_count,2);assert.equal(receipt.prefix_fork.usage_evidence.zero_update_count,2);
  assert.equal(receipt.prefix_fork.usage_evidence.duplicate_update_count,1);assert.deepEqual(receipt.prefix_fork.usage_evidence.baseline,initial);
});

const invalidUsage={
  missing:()=>[],missing_last:u=>{delete u[0].params.tokenUsage.last;return u;},
  missing_turn:u=>{delete u[0].params.turnId;return u;},foreign_turn:u=>{u[0].params.turnId='foreign';return u;},
  last_exceeds_total:u=>{u[0].params.tokenUsage.last.inputTokens=1000;return u;},
  zero_only:u=>{for(const k of Object.keys(u[0].params.tokenUsage.last))u[0].params.tokenUsage.last[k]=0;return u;},
  dropped_update:u=>{const next=structuredClone(u[0]);next.params.tokenUsage.total.inputTokens+=60;u.push(next);return u;},
  decreasing:u=>{const next=structuredClone(u[0]);next.params.tokenUsage.total.inputTokens--;u.push(next);return u;},
  conflicting_duplicate:u=>{const next=structuredClone(u[0]);next.params.tokenUsage.last.outputTokens++;u.push(next);return u;},
  optional_field_change:u=>{const next=structuredClone(u[0]);next.params.tokenUsage.total.cacheWriteInputTokens=0;u.push(next);return u;},
};
for(const [name,usageChange] of Object.entries(invalidUsage))test(`fork fails visibly with unavailable usage: ${name}`,async t=>{
  const f=await fixture(t,{usageChange}),cohort=await f.prepare(),worker=await f.worker(cohort.prefix);
  await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  const receipt=JSON.parse(await readFile(join(worker.profile.receipt_home,'attempt.json')));
  assert.equal(receipt.status,'failed');assert.equal(receipt.usage.available,false);assert(receipt.usage_unavailable_reason);assert.equal(f.turns,2);
});

for(const field of ['cachedInputTokens','outputTokens','reasoningOutputTokens'])test(`fork checks response delta for ${field}`,async t=>{
  const f=await fixture(t,{usageChange:u=>{const next=structuredClone(u[0]);for(const k of Object.keys(next.params.tokenUsage.total))next.params.tokenUsage.total[k]+=next.params.tokenUsage.last[k];next.params.tokenUsage.total[field]++;u.push(next);return u;}});
  const cohort=await f.prepare(),worker=await f.worker(cohort.prefix);await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
});

for(const retained of ['both','leading_lost','trailing_lost'])test(`two-response fork never certifies an unfenced boundary: ${retained}`,async t=>{
  const f=await fixture(t,{usageChange:updates=>{
    const first=structuredClone(updates[0]);first.params.tokenUsage={total:{inputTokens:110,cachedInputTokens:55,outputTokens:3,reasoningOutputTokens:0},last:{inputTokens:10,cachedInputTokens:5,outputTokens:1,reasoningOutputTokens:0}};
    const second=structuredClone(first);second.params.tokenUsage={total:{inputTokens:130,cachedInputTokens:65,outputTokens:5,reasoningOutputTokens:1},last:{inputTokens:20,cachedInputTokens:10,outputTokens:2,reasoningOutputTokens:1}};
    return retained==='both'?[first,second]:retained==='leading_lost'?[second]:[first];
  }}),cohort=await f.prepare(),worker=await f.worker(cohort.prefix);
  await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  const receipt=JSON.parse(await readFile(join(worker.profile.receipt_home,'attempt.json')));
  assert.equal(receipt.usage.available,false);assert.equal(receipt.usage_unavailable_reason,'fork_response_completeness_unavailable');
  assert.equal(receipt.prefix_fork.usage_evidence.completeness.available,false);
  assert.equal(receipt.prefix_fork.usage_evidence.observed_usage.input_tokens,retained==='both'?30:retained==='leading_lost'?20:10);
});

test('backing library remains leased before a child turn and close revokes future acquisitions',async t=>{
  const f=await fixture(t),cohort=await f.prepare(),worker=await f.worker(cohort.prefix);
  await assert.rejects(cohort.close(),{code:'CODEX_PREFIX_CHILD_ACTIVE'});await assert.rejects(f.worker(cohort.prefix),{code:'CODEX_PREFIX_HANDLE'});
  await worker.close();await cohort.close();await assert.rejects(lstat(f.sourcePath),{code:'ENOENT'});
});
test('private configuration preserves nonsecret settings and rejects secret-bearing configuration',async t=>{
  const root=await mkdtemp(join(tmpdir(),'prefix-config-')),cwd=join(root,'cwd'),normalHome=join(root,'normal');await mkdir(cwd);await mkdir(normalHome);
  t.after(()=>rm(root,{recursive:true,maxRetries:3,retryDelay:100}));
  const args={parent:join(root,'owned'),owner:{run_id:'run',attempt_id:'attempt'},cwd,normalHome};
  await assert.rejects(createRunOwnedNormalHome({...args,configuration:{config:{mcp_servers:{test:{env:{API_KEY:'never persist'}}}}}}),{code:'CODEX_PREFIX_CONFIG_SECRET'});
  const handle=await createRunOwnedNormalHome({...args,configuration:{config:{features:{web_search:true},history:{persistence:'save-all'},sqlite_home:'old',log_dir:'old'}}});
  const privateHome=normalPrefixHome(handle),config=await readFile(join(privateHome.home,'config.toml'),'utf8');assert.match(config,/"web_search" = true/);assert.match(config,/"persistence" = "save-all"/);assert(!config.includes('"old"'));await closeNormalPrefixHome(handle);
});
test('prefix owner exists before allocation and early cancellation launches no client',async t=>{
  const f=await fixture(t);f.options.onPrefixOwned=async owner=>{await owner.interrupt();};
  await assert.rejects(f.prepare(),{code:'CODEX_PREFIX_CANCELLED'});assert.equal(f.launches.length,0);
  await assert.rejects(lstat(f.options.parent),{code:'ENOENT'});
});
test('owned close drains pending setup and cleans its private store',async t=>{
  const f=await fixture(t,{stallSetup:true}),preparing=f.prepare();await f.setupStarted;
  const rejected=assert.rejects(preparing,error=>{assert(error.prefix_owner);return true;});
  await f.owner.close();await rejected;assert.equal(f.forks.length,0);await assert.rejects(lstat(f.sourcePath),{code:'ENOENT'});
});
test('failed source close retains exact billed setup and does not silently retry',async t=>{
  const f=await fixture(t,{failSourceClose:true});await assert.rejects(f.prepare(),error=>{
    assert.equal(error.setup.usage.input_tokens,100);assert(error.prefix_owner);return true;
  });assert.equal(f.sourceCloseCalls,1);assert.equal(f.forks.length,0);assert.equal((await lstat(f.sourcePath)).isFile(),true);
});
for(const caller of ['workspace-write','danger-full-access'])test(`shared setup inherits ordinary parent execution policy ${caller} while its logical access remains read-only`,async t=>{
  const f=await fixture(t);delete f.options.model;delete f.options.effort;f.options.sourceExecutionAccess='bounded_write';
  f.options.resolveModelSelection=async()=>({model:'prefix-model',effort:'high',main_execution_context:{parent_thread_id:'authenticated-parent',sandbox_type:caller}});
  let profile;f.options.onProfilePrepared=value=>profile=value;await f.prepare();assert.equal(f.startArguments[0].sandbox,caller);
  const receipt=JSON.parse(await readFile(join(profile.receipt_home,'attempt.json')));assert.equal(receipt.access,'read_only');assert.equal(receipt.execution_policy.parent_thread_id,'authenticated-parent');
  assert.equal(receipt.execution_policy.thread_sandbox,caller);assert.equal(receipt.prefix_source,true);
});
test('parent selection is resolved once on the original discovery client before any private client and inherited by its child',async t=>{
  const f=await fixture(t);delete f.options.model;delete f.options.effort;f.options.authentication={mode:'managed_chatgpt'};
  f.options.resolveModelSelection=async client=>{await client.call('thread/read',{threadId:'initiating-parent',includeTurns:false});return {model:'prefix-model',effort:'high'};};
  const cohort=await f.prepare(),worker=await f.worker(cohort.prefix);await assert.rejects(worker.turn('Only this neutral item'),{code:'CODEX_PREFIX_USAGE_UNAVAILABLE'});
  assert.equal(f.parentReads.length,1);assert.equal(f.parentReads[0].threadId,'initiating-parent');assert.equal(f.launches[0].home,f.normalHome);
  assert.equal(f.forks.length,1);assert.equal(f.startArguments.length,1);
  assert(f.logins.length>=4,'Both private source and private child discovery/execution clients use short-lived Host authentication');
});
test('a failed child allocation releases its early library lease before any child process exists',async t=>{
  const f=await fixture(t),cohort=await f.prepare(),before=f.launches.length;
  await assert.rejects(createCodexSession({...f.options,prefix:cohort.prefix,binary:join(f.root,'missing')}),{code:'ENOENT'});
  assert.equal(f.launches.length,before);await cohort.close();await assert.rejects(lstat(f.sourcePath),{code:'ENOENT'});
});
test('changed command declarations reject a trusted prefix before fork or child model submission',async t=>{
  const f=await fixture(t),home=await createRunOwnedNormalHome({parent:f.options.parent,owner:f.options.owner,cwd:f.options.cwd,normalHome:f.normalHome,configuration:{config:{model:'prefix-model'}}});
  const path=join(normalPrefixHome(home).home,'source.jsonl');await writeFile(path,'neutral completed source');
  const prefix=await sealNormalPrefix(home,{path,thread_id:'source',turn_id:'source-turn',model:'prefix-model',effort:'high',usage:{available:true},
    selection:{model:'prefix-model',effort:'high'},command_declarations_sha256:digest('different declarations')});
  const worker=await f.worker(prefix);try{await assert.rejects(worker.turn('neutral'),{code:'CODEX_PREFIX_DECLARATIONS_CHANGED'});assert.equal(f.forks.length,0);assert.equal(f.turns,0);}
  finally{await worker.close();await closeNormalPrefixHome(home);}
});
