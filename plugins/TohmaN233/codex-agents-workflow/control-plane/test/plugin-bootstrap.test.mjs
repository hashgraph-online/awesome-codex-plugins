import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {mkdtemp,mkdir,readdir,readFile,writeFile,rm,symlink,unlink,rename} from 'node:fs/promises';
import {spawn} from 'node:child_process';
import {once} from 'node:events';
import {fileURLToPath} from 'node:url';
import {join,resolve} from 'node:path';
import {tmpdir} from './physical-tempdir.mjs';
import {installLocal,selectObsoleteMcpEvents} from '../../scripts/install-local.mjs';
import {uninstallLocal} from '../../scripts/uninstall-local.mjs';
import {NATIVE_BUILTINS_PROFILE_NAME,readNativeContextProfileTemplate,nativeContextProfilePaths,
 preflightNativeContextProfileRegistration,verifyInstalledNativeContextProfile,installNativeContextProfile,cleanupNativeContextProfile} from '../../scripts/native-context-profile.mjs';
const {installationNamespace,registeredRoot}=createRequire(import.meta.url)('../../scripts/mcp-bootstrap.cjs');

test('Windows bootstrap releases the replaceable cache namespace without terminating its client',{skip:process.platform!=='win32',timeout:10000},async()=>{
 const home=await mkdtemp(join(tmpdir(),'bootstrap-cache-cwd-'));
 const namespace=join(home,'cache','marketplace','codex-agents-workflow'),runtime=join(home,'user-data');
 await mkdir(join(namespace,'1.2'),{recursive:true});await mkdir(runtime);
 const bootstrap=fileURLToPath(new URL('../../scripts/mcp-bootstrap.cjs',import.meta.url));
 const clients=[];
 async function client(release){
  const program=`if(process.argv[1]==='release')require(process.argv[2]).releaseCacheWorkingDirectory(process.cwd(),process.argv[3]);process.stdout.write(JSON.stringify({cwd:process.cwd()})+'\\n');process.stdin.resume();`;
  const child=spawn(process.execPath,['-e',program,release?'release':'retain',bootstrap,runtime],{cwd:namespace,windowsHide:true,stdio:['pipe','pipe','pipe']});
  const closed=once(child,'close');clients.push({child,closed});
  let stderr='';child.stderr.on('data',data=>{stderr+=data;});
  const ready=once(child.stdout,'data').then(([data])=>JSON.parse(data));
  const early=closed.then(([code])=>{throw new Error(`Bootstrap client exited ${code}: ${stderr}`);});
  return {child,closed,cwd:(await Promise.race([ready,early])).cwd};
 }
 try{
  const old=await client(false);
  await assert.rejects(rename(namespace,namespace+'-backup'),error=>['EBUSY','EPERM','EACCES'].includes(error.code),'A cache cwd must reproduce the original Windows directory lock');
  old.child.stdin.end();assert.equal((await old.closed)[0],0);
  const current=await client(true);
  assert.equal(current.cwd,runtime);
  await rename(namespace,namespace+'-backup');
  assert.equal(current.child.exitCode,null,'Cache publication must preserve the running client');
  assert.doesNotThrow(()=>process.kill(current.child.pid,0));
  current.child.stdin.end();assert.equal((await current.closed)[0],0);
 }finally{
  for(const {child,closed} of clients){if(child.exitCode===null)child.stdin.end();await closed;}
  await rm(home,{recursive:true});
 }
});

test('bootstrap selects only the registry version, rejects disabled or ambiguous installation',()=>{
 const entry={pluginId:'codex-agents-workflow@codex-agents-workflow',installed:true,enabled:true,version:'0.8.0+current'};
 const namespace=resolve(tmpdir(),'codex-agents-workflow','codex-agents-workflow');
 assert.equal(registeredRoot({installed:[entry]},namespace).version,entry.version);
 assert.throws(()=>registeredRoot({installed:[entry,entry]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[{...entry,enabled:false}]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[{...entry,version:'../elsewhere'}]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({},namespace),/REGISTRY/);
 assert.throws(()=>installationNamespace(resolve(tmpdir(),'unrelated')),/NAMESPACE/);
});

test('bootstrap selects the launching namespace even when another source has a newer version',()=>{
 const namespace=resolve(tmpdir(),'awesome-codex-plugins','codex-agents-workflow');
 const entries=[
  {pluginId:'codex-agents-workflow@codex-agents-workflow',installed:true,enabled:true,version:'99.0.0'},
  {pluginId:'codex-agents-workflow@awesome-codex-plugins',installed:true,enabled:true,version:'1.1.0'},
 ];
 const selected=registeredRoot({installed:entries},namespace);
 assert.equal(selected.marketplace,'awesome-codex-plugins');
 assert.equal(selected.pluginId,entries[1].pluginId);
 assert.equal(selected.root,join(namespace,'1.1.0'));
 assert.throws(()=>registeredRoot({installed:[entries[0]]},namespace),/REGISTRY/);
 assert.throws(()=>registeredRoot({installed:[entries[0],{...entries[1],enabled:false}]},namespace),/REGISTRY/);
});

test('obsolete MCP cleanup selects only the exact marketplace namespace and version',()=>{
 const root=resolve(tmpdir(),'cache','marketplace-one','codex-agents-workflow');
 const other=resolve(tmpdir(),'cache','marketplace-two','codex-agents-workflow');
 const version='1.1',at='2026-10-12T00:00:00.000Z';
 const owned={phase:'resolved',version,pid:101,at,namespace:root,marketplace:'marketplace-one',
  pluginId:'codex-agents-workflow@marketplace-one',entry:join(root,version,'control-plane/server.mjs')};
 const foreign={...owned,pid:102,namespace:other,marketplace:'marketplace-two',
  pluginId:'codex-agents-workflow@marketplace-two',entry:join(other,version,'control-plane/server.mjs')};
 const lines=[owned,foreign,{...owned,pid:103,version:'1.2'},{...owned,pid:104,pluginId:foreign.pluginId},
  {...owned,pid:105,entry:foreign.entry},{...owned,pid:106,namespace:undefined},
  {...owned,pid:107,at:'invalid'}].map(JSON.stringify);
 assert.deepEqual(selectObsoleteMcpEvents(lines,version,root),[{pid:101,at}]);
 assert.deepEqual(selectObsoleteMcpEvents(lines,version,other),[{pid:102,at}]);
});

test('upgrade deletes obsolete plugin cache versions and creates no rollback store',async()=>{
 const home=await mkdtemp(join(tmpdir(),'direct-plugin-'));
 try{
  const cacheRoot=join(home,'cache'),codexHome=join(home,'codex-home');
  const old=join(cacheRoot,'1.0.0-old'),current=join(cacheRoot,'1.0.0-current');
  await mkdir(join(old,'.codex-plugin'),{recursive:true});await mkdir(join(current,'.codex-plugin'),{recursive:true});
  await mkdir(join(current,'agent-profiles'));await writeFile(join(current,'agent-profiles','caw-native-builtins.toml'),readNativeContextProfileTemplate());
  await writeFile(join(old,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version:'1.0.0-old'}));
  await writeFile(join(current,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version:'1.0.0-current'}));
  let calls=0;const released=[];
  const result=await installLocal({install:async()=>{calls++;},cacheRoot,codexHome,currentVersion:'1.0.0-current',release:async (version,namespace)=>{
   assert.equal(namespace,resolve(cacheRoot));
   released.push(version);return version==='1.0.0-current'?[201,202]:[101,102];
  }});
  const {native_context_profile,...installation}=result;
  assert.equal(calls,1);assert.deepEqual(installation,{installed:true,retained_versions:[],removed_versions:['1.0.0-old'],mcp_connection_refresh_required:true,released_processes:[{version:'1.0.0-old',count:2}]});
  assert.deepEqual(native_context_profile,{...verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,{codexHome}),changed:true});
  assert.deepEqual(released,['1.0.0-old']);
  assert.deepEqual(await readdir(cacheRoot),['1.0.0-current']);
  const repeated=await installLocal({install:async()=>{calls++;},cacheRoot,codexHome,currentVersion:'1.0.0-current',release:async()=>{throw new Error('Same-version update must preserve current MCP sessions');}});
  assert.equal(calls,2);assert.equal(repeated.native_context_profile.changed,false);assert.deepEqual(repeated.removed_versions,[]);
  assert.deepEqual(repeated.released_processes,[]);assert.equal(repeated.mcp_connection_refresh_required,false);
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
});

test('installation failure is exposed without automatic restore or retry',async()=>{
 const home=await mkdtemp(join(tmpdir(),'failed-plugin-'));
 try{
  const error=Object.assign(new Error('CLI failed: Windows sharing violation'),{code:'EBUSY'});let calls=0,released=0;
  await assert.rejects(installLocal({codexHome:home,install:async()=>{calls++;throw error;},release:async()=>{released++;return [201,202];}}),e=>e===error);
  assert.equal(calls,1);assert.equal(released,0);assert.deepEqual(await readdir(home),[]);
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
});

test('successful CLI replacement releases logged obsolete MCP owners after their cache directory disappears',async()=>{
 const home=await mkdtemp(join(tmpdir(),'replaced-plugin-'));
 try{
  const cacheRoot=join(home,'cache','marketplace','codex-agents-workflow'),codexHome=join(home,'codex-home');
  const old=join(cacheRoot,'1.0.0-old'),current=join(cacheRoot,'1.0.0-current');
  await mkdir(join(old,'.codex-plugin'),{recursive:true});await mkdir(join(current,'agent-profiles'),{recursive:true});
  await writeFile(join(old,'.codex-plugin','plugin.json'),JSON.stringify({name:'codex-agents-workflow',version:'1.0.0-old'}));
  await writeFile(join(current,'agent-profiles','caw-native-builtins.toml'),readNativeContextProfileTemplate());
  await mkdir(join(codexHome,'codex-agents-workflow'),{recursive:true});
  const event={phase:'resolved',version:'1.0.0-old',pid:101,at:'2026-10-12T00:00:00.000Z',namespace:cacheRoot,marketplace:'marketplace',
   pluginId:'codex-agents-workflow@marketplace',entry:join(old,'control-plane','server.mjs')};
  await writeFile(join(codexHome,'codex-agents-workflow','mcp-startup.jsonl'),JSON.stringify(event)+'\n');
  let installed=false;const released=[];
  const result=await installLocal({cacheRoot,codexHome,currentVersion:'1.0.0-current',install:async()=>{
   await rm(old,{recursive:true});installed=true;
  },release:async(version,namespace)=>{
   assert.equal(installed,true,'Never stop old owners before successful replacement');assert.equal(namespace,resolve(cacheRoot));
   released.push(version);return [101];
  }});
  assert.deepEqual(released,['1.0.0-old']);
  assert.deepEqual(result.removed_versions,[]);
  assert.deepEqual(result.released_processes,[{version:'1.0.0-old',count:1}]);
  assert.equal(result.mcp_connection_refresh_required,true);
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
});

async function profileFixture(run){
 const home=await mkdtemp(join(tmpdir(),'native-profile-'));
 try{
  const codexHome=join(home,'codex-home'),deployedPluginRoot=join(home,'cache','1.2');
  await mkdir(join(deployedPluginRoot,'agent-profiles'),{recursive:true});
  await writeFile(join(deployedPluginRoot,'agent-profiles','caw-native-builtins.toml'),readNativeContextProfileTemplate());
  await run({home,codexHome,deployedPluginRoot,...nativeContextProfilePaths({codexHome})});
 }finally{assert(home.startsWith(resolve(tmpdir())));await rm(home,{recursive:true});}
}
const code=expected=>error=>error.code===`NATIVE_CONTEXT_PROFILE_${expected}`;

test('native profile install is exact and idempotent, with inherited model and effort',async()=>profileFixture(async options=>{
 const template=readNativeContextProfileTemplate().toString('utf8');
 assert.match(template,/apps = false/);assert.match(template,/plugins = false/);assert.match(template,/include_instructions = false/);
 assert.doesNotMatch(template,/model|reasoning|sandbox|safety/i);
 const first=installNativeContextProfile(options),second=installNativeContextProfile(options);
 assert.equal(first.changed,true);assert.equal(second.changed,false);
 assert.deepEqual(await readFile(options.profile_path),readNativeContextProfileTemplate());
 assert.equal(verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options).sha256,first.sha256);
 assert.throws(()=>verifyInstalledNativeContextProfile('foreign',options),code('NAME'));
}));

for(const same of [true,false])test(`unowned ${same?'same':'different'} profile bytes fail before normal plugin install`,async()=>profileFixture(async options=>{
 await mkdir(join(options.codexHome,'agents'),{recursive:true});
 const bytes=same?readNativeContextProfileTemplate():Buffer.from('user agent file\n');await writeFile(options.profile_path,bytes);
 let installed=0,released=0;
 await assert.rejects(installLocal({codexHome:options.codexHome,install:async()=>installed++,release:async()=>{released++;return [];}}),code('COLLISION'));
 assert.equal(installed,0);assert.equal(released,0);assert.deepEqual(await readFile(options.profile_path),bytes);
 assert.throws(()=>cleanupNativeContextProfile(options),code('COLLISION'));
}));

test('user edits remain untouched by install, verify and supported uninstall',async()=>profileFixture(async options=>{
 installNativeContextProfile(options);await writeFile(options.profile_path,'user changed the profile\n');
 const receipt=await readFile(options.ownership_receipt_path);let uninstalled=0;
 assert.throws(()=>installNativeContextProfile(options),code('EDITED'));
 assert.throws(()=>verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options),code('EDITED'));
 await assert.rejects(uninstallLocal({codexHome:options.codexHome,uninstall:async()=>uninstalled++}),code('EDITED'));
 assert.equal(uninstalled,0);assert.equal(await readFile(options.profile_path,'utf8'),'user changed the profile\n');
 assert.deepEqual(await readFile(options.ownership_receipt_path),receipt);
}));

test('supported uninstall removes only exact owned files and exposes CLI failure',async()=>profileFixture(async options=>{
 installNativeContextProfile(options);await writeFile(join(options.codexHome,'agents','unrelated.toml'),'leave this file');
 const error=new Error('uninstall failed');await assert.rejects(uninstallLocal({codexHome:options.codexHome,uninstall:async()=>{throw error;}}),value=>value===error);
 verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options);
 let calls=0;const result=await uninstallLocal({codexHome:options.codexHome,uninstall:async()=>calls++});
 assert.equal(calls,1);assert.deepEqual(result,{uninstalled:true,native_context_profile:{name:NATIVE_BUILTINS_PROFILE_NAME,removed:true,ownership_receipt_removed:true}});
 assert.deepEqual(await readdir(join(options.codexHome,'agents')),['unrelated.toml']);
 assert.deepEqual(cleanupNativeContextProfile(options),{name:NATIVE_BUILTINS_PROFILE_NAME,removed:false,ownership_receipt_removed:false});
 assert.throws(()=>verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options),code('UNREGISTERED'));
}));

test('unfinished owned registration can finish or clean up without adopting foreign bytes',async()=>profileFixture(async options=>{
 const installed=installNativeContextProfile(options),receipt=JSON.parse(await readFile(options.ownership_receipt_path,'utf8'));
 await writeFile(options.ownership_receipt_path,JSON.stringify({...receipt,pending_sha256:installed.sha256}));
 assert.throws(()=>verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options),code('UNREGISTERED'));
 assert.equal(installNativeContextProfile(options).changed,false);
 await unlink(options.profile_path);assert.equal(cleanupNativeContextProfile(options).ownership_receipt_removed,true);
}));

test('a recorded prior template updates to the exact normally deployed profile',async()=>profileFixture(async options=>{
 installNativeContextProfile(options);
 const previous=Buffer.concat([readNativeContextProfileTemplate(),Buffer.from('\n# previous installed revision\n')]);
 const receipt=JSON.parse(await readFile(options.ownership_receipt_path,'utf8'));
 await writeFile(options.profile_path,previous);await writeFile(options.ownership_receipt_path,JSON.stringify({...receipt,sha256:createHash('sha256').update(previous).digest('hex')}));
 assert.throws(()=>verifyInstalledNativeContextProfile(NATIVE_BUILTINS_PROFILE_NAME,options),code('TEMPLATE_MISMATCH'));
 assert.equal(installNativeContextProfile(options).changed,true);
 assert.deepEqual(await readFile(options.profile_path),readNativeContextProfileTemplate());
}));

test('source/deployed mismatch leaves personal registration absent',async()=>profileFixture(async options=>{
 await writeFile(join(options.deployedPluginRoot,'agent-profiles','caw-native-builtins.toml'),'different deployment');
 assert.throws(()=>installNativeContextProfile(options),code('DEPLOYED_MISMATCH'));
 assert.equal(preflightNativeContextProfileRegistration(options).registered,false);
}));

test('native profile rejects relative homes and linked normal registration paths',async()=>profileFixture(async options=>{
 assert.throws(()=>nativeContextProfilePaths({codexHome:'relative-home'}),code('PATH'));
 const target=join(options.home,'linked-agents');await mkdir(target);await mkdir(options.codexHome);
 await symlink(target,join(options.codexHome,'agents'),'junction');
 assert.throws(()=>preflightNativeContextProfileRegistration(options),code('LINK'));
 assert.throws(()=>installNativeContextProfile(options),code('LINK'));
 assert.deepEqual(await readdir(target),[]);
}));
