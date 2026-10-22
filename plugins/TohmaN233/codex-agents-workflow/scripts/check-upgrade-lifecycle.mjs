import {spawn,execFileSync} from 'node:child_process';
import {createInterface} from 'node:readline';
import {mkdir,writeFile,readFile,access,mkdtemp} from 'node:fs/promises';
import {join,dirname,resolve} from 'node:path';
import {tmpdir} from 'node:os';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const base=await mkdtemp(join(tmpdir(),'workflow-host-upgrade-')),home=join(base,'home'),repo=join(base,'market'),plugin=join(repo,'plugins/codex-agents-workflow');
const binary=process.env.CODEX_CLI_PATH || 'codex';
const marketplace=process.argv[2] || 'codex-agents-workflow';
if(!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(marketplace))throw Error('Invalid test marketplace name');
const pluginId='codex-agents-workflow@'+marketplace;
const pluginRoot=resolve(dirname(fileURLToPath(import.meta.url)),'..');
await mkdir(home,{recursive:true});await mkdir(join(repo,'.agents/plugins'),{recursive:true});await mkdir(join(plugin,'.codex-plugin'),{recursive:true});
const manifest={name:'codex-agents-workflow',version:'1.0.0',description:'Isolated MCP lifecycle regression fixture',mcpServers:'./.mcp.json'};
await writeFile(join(plugin,'.codex-plugin/plugin.json'),JSON.stringify(manifest));
await writeFile(join(plugin,'.mcp.json'),await readFile(join(pluginRoot,'.mcp.json')));await mkdir(join(plugin,'control-plane'),{recursive:true});
await writeFile(join(plugin,'control-plane/server.mjs'),`import {createRequire} from 'node:module'; const require=createRequire(import.meta.url); require('node:readline').createInterface({input:process.stdin}).on('line',l=>{const m=JSON.parse(l);if(m.id!==undefined)console.log(JSON.stringify({jsonrpc:'2.0',id:m.id,result:m.method==='initialize'?{protocolVersion:'2025-11-25',capabilities:{tools:{}},serverInfo:{name:'codex-agents-workflow',version:'1'}}:m.method==='tools/list'?{tools:[{name:'ping',inputSchema:{type:'object'}}]}:{}}));});`);
await writeFile(join(repo,'.agents/plugins/marketplace.json'),JSON.stringify({name:marketplace,plugins:[{name:'codex-agents-workflow',source:{source:'local',path:'./plugins/codex-agents-workflow'},policy:{installation:'AVAILABLE',authentication:'ON_INSTALL'},category:'Productivity'}]}));
const env={...process.env,CODEX_HOME:home};
function cli(args){return execFileSync(binary,args,{env,encoding:'utf8',windowsHide:true});}
cli(['plugin','marketplace','add',repo]);cli(['plugin','add',pluginId]);
const child=spawn(binary,['app-server','--stdio'],{cwd:base,env,windowsHide:true,stdio:['pipe','pipe','pipe']});
let id=0,stderr='';const pending=new Map();child.stderr.on('data',d=>stderr+=d);child.on('exit',()=>{for(const p of pending.values())p.reject(Error('Host exited: '+stderr));});
createInterface({input:child.stdout}).on('line',l=>{const m=JSON.parse(l),p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}else if(m.method==='mcpServer/startupStatus/updated')console.log(JSON.stringify(m.params));});
function call(method,params){return new Promise((resolve,reject)=>{pending.set(++id,{resolve,reject});child.stdin.write(JSON.stringify({id,method,params})+'\n');});}
const timer=setTimeout(()=>child.kill(),30000);
try{await call('initialize',{clientInfo:{name:'warm_fixture',version:'1'},capabilities:{experimentalApi:true}});child.stdin.write('{"method":"initialized"}\n');
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function connectedStatus(threadId){
 const deadline=Date.now()+10000;let latest;
 while(Date.now()<=deadline){
  const status=await call('mcpServerStatus/list',{threadId});latest=status.data.find(item=>item.name==='codex-agents-workflow');
  // Verify actual tool exposure; some app-server versions omit runtimeStatus.
  if(latest?.tools?.ping)return latest;
  if(latest?.runtimeStatus==='failed')throw Error(`MCP startup failed: ${JSON.stringify(latest)}`);
  await pause(100);
 }
 throw Error(`MCP did not connect within 10 seconds: ${JSON.stringify(latest??null)}`);
}
async function check(label){const t=await call('thread/start',{cwd:base,ephemeral:true});await connectedStatus(t.thread.id);console.log(label,'connected');}
await check('BEFORE');
manifest.version='1.0.1';await writeFile(join(plugin,'.codex-plugin/plugin.json'),JSON.stringify(manifest));cli(['plugin','add',pluginId]);
console.log('OLD_EXISTS',await access(join(home,'plugins/cache',marketplace,'codex-agents-workflow/1.0.0')).then(()=>true,()=>false));
await check('AFTER');
const audit=(await readFile(join(home,'codex-agents-workflow/mcp-startup.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
assert.equal(audit.at(-1).version,'1.0.1');assert.equal(audit.at(-1).marketplace,marketplace);assert.equal(audit.at(-1).pluginId,pluginId);
console.log('PASS: existing host selected new installed version after upgrade from',marketplace,'; evidence:',base);
}finally{clearTimeout(timer);await writeFile(join(base,'stderr.log'),stderr);child.stdin.end();child.kill();}
