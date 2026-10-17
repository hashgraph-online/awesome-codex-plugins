import test from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {mkdtemp,readFile,realpath,rm,writeFile,mkdir} from 'node:fs/promises';
import {delimiter,dirname,join} from 'node:path';
import {tmpdir} from 'node:os';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {decideWebResponseDefault,prepareCodexWebResponseDefault,webResponseHookCommand} from '../lib/execution/codex-web-response-default.mjs';

const modulePath=fileURLToPath(new URL('../lib/execution/codex-web-response-default.mjs',import.meta.url));
const request=input=>({hook_event_name:'PreToolUse',session_id:'fixture',turn_id:'fixture',tool_use_id:'fixture',tool_name:'webrun',tool_input:input});

test('web defaults preserve full operations and all explicit values, mixed operations and other tools',()=>{
  assert.deepEqual(decideWebResponseDefault(request({search_query:Array.from({length:4},()=>({q:'neutral'}))})).output,{});
  for(const [key,value] of Object.entries({search_query:[{q:'neutral',domains:['example.com'],recency:7}],open:[{ref_id:'https://example.com',lineno:0}],find:[{ref_id:'https://example.com',pattern:'Example'}]})){
    const input={[key]:value};
    assert.deepEqual(decideWebResponseDefault(request(input)).output,{hookSpecificOutput:{hookEventName:'PreToolUse',permissionDecision:'allow',updatedInput:{...input,response_length:'short'}}});
    assert.equal(Object.hasOwn(input,'response_length'),false);
    for(const response_length of ['short','medium','long',null,false,0,'other',{},[]])assert.deepEqual(decideWebResponseDefault(request({...input,response_length})).output,{});
    for(const operation of ['image_query','click','screenshot','finance','weather','sports','time'])assert.deepEqual(decideWebResponseDefault(request({...input,[operation]:[]})).output,{});
    assert.deepEqual(decideWebResponseDefault(request({...input,future_field:[]})).output,{});
    for(const name of ['web.run','web__run','exec_command'])assert.deepEqual(decideWebResponseDefault({...request(input),tool_name:name}).output,{});
  }
});

test('web audit omits content, authentication, transcript and unrelated input fields',()=>{
  const input={open:[{ref_id:'https://user:password@example.com/?token=private&x=1',lineno:42,content:'PRIVATE_CONTENT'}],response_length:'medium',authorization:'AUTH',transcript:'TRANSCRIPT'};
  const {audit,output}=decideWebResponseDefault({...request(input),transcript_path:'SECRET_TRANSCRIPT',model:'PRIVATE_MODEL'});
  assert.deepEqual(output,{});
  assert.equal(audit.response_length,'medium');
  assert.equal(audit.response_length_present,true);
  assert.equal(audit.open[0].ref_id.includes('user:'),false);
  for(const secret of ['password','private','PRIVATE_CONTENT','AUTH','TRANSCRIPT','PRIVATE_MODEL'])assert.equal(JSON.stringify(audit).includes(secret),false);
});

test('metadata preparation uses two clients, exact trust key, closed ownership and full normal-hook preservation',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'web-default-metadata-'));
  try{
    const original={key:'user:pre_tool_use:0:0',source:'user',eventName:'preToolUse',matcher:'^webrun$',currentHash:'sha256:'+ 'a'.repeat(64),trustStatus:'trusted',enabled:true,command:'original',handlerType:'command'};
    const opened=[],calls=[];
    const clientFactory=(_binary,options)=>{
      const index=opened.length;opened.push({options,closed:false});
      return {initialized(){},async call(method){calls.push(method);if(method==='initialize')return {};
        const commandOverride=options.overrides.find(value=>value.startsWith('hooks.PreToolUse='));
        const command=commandOverride?JSON.parse(commandOverride.match(/command=("(?:\\.|[^"])*")/)[1]):null;
        const hooks=[original,...(index? [{key:'C:\\<session-flags>\\config.toml:pre_tool_use:0:0',source:'sessionFlags',eventName:'preToolUse',handlerType:'command',command,matcher:'^webrun$',enabled:true,currentHash:'sha256:'+'b'.repeat(64),trustStatus:'untrusted'}]:[])];
        return {data:[{cwd:dir,hooks,errors:[],warnings:[]}]};},async close(){opened[index].closed=true;}};
    };
    const prepared=await prepareCodexWebResponseDefault({binary:process.execPath,home:dir,cwd:dir,auditPath:join(dir,'audit.jsonl'),clientFactory,overrides:['features.standalone_web_search=true']});
    assert.deepEqual(calls,['initialize','hooks/list','initialize','hooks/list']);
    assert.ok(opened.every(value=>value.closed));
    assert.equal(prepared.normal_hooks_preserved.length,1);
    assert.equal(prepared.own_hook.matcher,'^webrun$');
    assert.match(prepared.overrides.at(-1),/^hooks\.state=\{/);
    assert.ok(prepared.overrides.at(-1).includes(JSON.stringify(prepared.own_hook.key)));
    assert.ok(prepared.overrides.includes('features.standalone_web_search=true'));
    assert.ok(prepared.overrides.every(value=>!value.includes('tool_output_token_limit')));
    assert.match(prepared.script_sha256,/^[a-f0-9]{64}$/);
    assert.match(prepared.node_sha256,/^[a-f0-9]{64}$/);
    assert.equal((await readFile(prepared.audit_path)).length,0);
    assert.equal(Object.values(prepared.environment_overlay)[0].split(delimiter)[0],dirname(await realpath(process.execPath)));
    await assert.rejects(prepareCodexWebResponseDefault({binary:process.execPath,home:dir,cwd:dir,auditPath:join(dir,'conflict'),clientFactory,overrides:['hooks.PreToolUse=[]']}),{code:'CODEX_WEB_RESPONSE_DEFAULT'});
  }finally{await rm(dir,{recursive:true,force:true});}
});

test('metadata preservation rejects changed original hooks and retains both operation and close failures',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'web-default-error-'));
  try{
    let index=0;
    const factory=()=>{const own=index++;return {initialized(){},async call(method){if(method==='initialize')return {};if(!own)throw new Error('metadata failed');},async close(){throw new Error('close failed');}};};
    await assert.rejects(prepareCodexWebResponseDefault({binary:process.execPath,home:dir,cwd:dir,auditPath:join(dir,'audit'),clientFactory:factory}),error=>error instanceof AggregateError&&error.errors.map(e=>e.message).join(',')==='metadata failed,close failed');
    index=0;
    const changing=(_binary,options)=>{const own=index++;return {initialized(){},async call(method){if(method==='initialize')return {};
      const hook={key:'user',source:'user',command:own?'changed':'original'};
      const commandOverride=options.overrides.find(value=>value.startsWith('hooks.PreToolUse='));
      const command=commandOverride?JSON.parse(commandOverride.match(/command=("(?:\\.|[^"])*")/)[1]):null;
      return {data:[{cwd:dir,errors:[],warnings:[],hooks:[hook,...(own?[{key:'own',source:'sessionFlags',eventName:'preToolUse',handlerType:'command',command,matcher:'^webrun$',enabled:true,currentHash:'sha256:'+'b'.repeat(64)}]:[])]}]};},async close(){}};};
    await assert.rejects(prepareCodexWebResponseDefault({binary:process.execPath,home:dir,cwd:dir,auditPath:join(dir,'audit'),clientFactory:changing}),/altered an existing hook/);
  }finally{await rm(dir,{recursive:true,force:true});}
});

test('neutral bootstrap executes through native shells without interpolating receipt paths and reports malformed input',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'web-default-shell-'));
  try{
    const nodePath=await realpath(process.execPath),auditPath=join(dir,"audit $ ` ' ;.jsonl");await writeFile(auditPath,'');
    const command=webResponseHookCommand({nodePath,scriptPath:modulePath,auditPath});
    assert.equal(/[\$`]/.test(command),false);assert.equal(command.includes(auditPath),false);
    const env={...process.env};const key=Object.keys(env).find(k=>k.toLowerCase()==='path')??'PATH';env[key]=dirname(nodePath)+delimiter+(env[key]??'');
    const shells=process.platform==='win32'?[
      ['powershell.exe',['-NoProfile','-NonInteractive','-Command',command],false],
      [process.env.COMSPEC??'cmd.exe',['/d','/s','/c',command],true]
    ]:[['/bin/sh',['-c',command],false]];
    for(const [shell,args,verbatim] of shells){
      const result=spawnSync(shell,args,{input:JSON.stringify(request({open:[{ref_id:'https://example.com',lineno:0}]})),encoding:'utf8',env,windowsHide:true,windowsVerbatimArguments:verbatim});
      assert.equal(result.status,0,result.stderr);assert.equal(JSON.parse(result.stdout).hookSpecificOutput.updatedInput.response_length,'short');
      const invalid=spawnSync(shell,args,{input:'{',encoding:'utf8',env,windowsHide:true,windowsVerbatimArguments:verbatim});
      assert.equal(invalid.status,0,invalid.stderr);
      const failure=JSON.parse(invalid.stdout).hookSpecificOutput;
      assert.equal(failure.permissionDecision,'deny');assert.match(failure.permissionDecisionReason,/invalid JSON/);assert.match(invalid.stderr,/invalid JSON/);
    }
    assert.equal((await readFile(auditPath,'utf8')).trim().split('\n').length,shells.length);
  }finally{await rm(dir,{recursive:true,force:true});}
});

test('actual metadata RPCs preserve same-event user hooks and admit SessionFlags trust in a temporary home',
  {skip:!process.env.CODEX_WEB_DEFAULT_TEST_BINARY},async()=>{
    const clientModule=process.env.CODEX_WEB_DEFAULT_TEST_CLIENT?pathToFileURL(process.env.CODEX_WEB_DEFAULT_TEST_CLIENT):new URL('../lib/execution/codex-app-server-client.mjs',import.meta.url);
    const {createCodexClient}=await import(clientModule);
    const dir=await mkdtemp(join(tmpdir(),'web-default-native-'));let client;
    try{
      const home=join(dir,'home');await mkdir(home);
      const config='[features]\nhooks=true\n[[hooks.PreToolUse]]\nmatcher="^webrun$"\n[[hooks.PreToolUse.hooks]]\ntype="command"\ncommand="echo preserved-user-hook"\n';
      await writeFile(join(home,'config.toml'),config);
      const prepared=await prepareCodexWebResponseDefault({binary:process.env.CODEX_WEB_DEFAULT_TEST_BINARY,home,cwd:dir,auditPath:join(dir,'audit.jsonl'),clientFactory:createCodexClient});
      assert.equal(prepared.normal_hooks_preserved.length,1);
      client=createCodexClient(process.env.CODEX_WEB_DEFAULT_TEST_BINARY,{home,cwd:dir,overrides:prepared.overrides,env:{...process.env,...prepared.environment_overlay}});
      await client.call('initialize',{clientInfo:{name:'web_default_test',version:'1.0.0'},capabilities:{experimentalApi:true}});client.initialized();
      const inventory=await client.call('hooks/list',{cwds:[dir]});
      assert.equal(inventory.data[0].hooks.length,2);
      const own=inventory.data[0].hooks.find(h=>h.key===prepared.own_hook.key);
      assert.equal(own.trustStatus,'trusted');assert.equal(own.enabled,true);assert.equal(own.currentHash,prepared.own_hook.current_hash);
      const original=inventory.data[0].hooks.find(h=>h.source==='user');assert.equal(original.command,'echo preserved-user-hook');assert.equal(original.matcher,'^webrun$');
      assert.equal(await readFile(join(home,'config.toml'),'utf8'),config);
      await client.close();client=null;
    }finally{if(client)await client.close();await rm(dir,{recursive:true,force:true});}
  });
