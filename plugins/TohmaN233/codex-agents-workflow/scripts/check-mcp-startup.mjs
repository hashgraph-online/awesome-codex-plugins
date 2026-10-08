import {spawn} from 'node:child_process';
import {readFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
export async function probe(root, {cwd,timeoutMs=10000,env=process.env}={}) {
 const spec=JSON.parse(await readFile(resolve(root,'.mcp.json'),'utf8')).mcpServers['codex-agents-workflow'];
 cwd??=resolve(root,spec.cwd??'.');
 return new Promise((resolveResult,reject)=>{
  const child=spawn(spec.command,spec.args,{cwd,env,windowsHide:true,stdio:['pipe','pipe','pipe']});
  let buffer='',stderr='',initialized=false,listed=false,settled=false,failure;
  const timer=setTimeout(()=>finish(new Error('WORKFLOW_MCP_TIMEOUT: initialize/tools/list did not complete')),timeoutMs);
  function finish(error){if(settled)return;settled=true;failure=error;clearTimeout(timer);child.stdin.end();child.kill();}
  function send(value){child.stdin.write(JSON.stringify(value)+'\n');}
  child.on('error',finish);child.stdin.on('error',finish);
  child.stderr.on('data',x=>{stderr=(stderr+x).slice(-8000);});
  child.on('close',code=>{if(!settled)finish(new Error(`WORKFLOW_MCP_EXIT: process exited ${code} before readiness`));if(failure)reject(new Error(`${failure.message}\n${stderr}`));else resolveResult({status:'ready',initialized,tools_list_verified:listed,host_tool_exposure:'not_checked'});});
  child.stdout.on('data',x=>{buffer+=x;let index;while((index=buffer.indexOf('\n'))>=0){const line=buffer.slice(0,index);buffer=buffer.slice(index+1);if(!line.trim())continue;try{const msg=JSON.parse(line);if(msg.error)throw Error(JSON.stringify(msg.error));if(msg.id===1){if(!msg.result?.capabilities?.tools)throw Error('Missing tool capability');initialized=true;send({jsonrpc:'2.0',method:'notifications/initialized'});send({jsonrpc:'2.0',id:2,method:'tools/list',params:{}});}if(msg.id===2){const names=msg.result?.tools?.map(t=>t.name)??[];for(const name of ['workflow_list','workflow_capabilities','workflow_start'])if(!names.includes(name))throw Error(`Missing required tool ${name}`);listed=true;finish();}}catch(e){finish(e);}}});
  send({jsonrpc:'2.0',id:1,method:'initialize',params:{protocolVersion:'2025-11-25',capabilities:{},clientInfo:{name:'workflow-startup-check',version:'1'}}});
 });
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
 probe(resolve(dirname(fileURLToPath(import.meta.url)),'..')).then(value=>console.log(JSON.stringify(value))).catch(error=>{console.error(error.message);process.exitCode=1;});
}
