import { readFileSync } from 'node:fs';
import { lstat, readFile, readdir, unlink } from 'node:fs/promises';
import { extname, isAbsolute, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createCodexToolBroker } from './codex-tool-broker.mjs';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

const name='workflow-resource-program';
const version='1';
const implementation=digest(readFileSync(fileURLToPath(import.meta.url),'utf8').replace(/\r\n/g,'\n'));
const emptyEffects=()=>({observed:true,changed_paths:[],outside_paths:[],artifacts:[]});
const within=(path,root)=>root==='.'||path===root||path.startsWith(root+'/');

export function workflowResourceProgramIdentity(){
  return {name,version,sha256:digest(canonicalJSON({name,version,implementation}))};
}

async function snapshot(workspace){
  const files=new Map();
  async function visit(directory){
    for(const item of await readdir(directory,{withFileTypes:true})){
      if(item.name==='.git')continue;
      const absolute=join(directory,item.name),path=relative(workspace,absolute).replaceAll('\\','/');
      const stat=await lstat(absolute);
      requireValue(!stat.isSymbolicLink(),'WORKFLOW_RESOURCE_SCOPE','Workflow resource execution encountered a workspace link');
      if(stat.isDirectory()){await visit(absolute);continue;}
      if(stat.isFile())files.set(path,digest(await readFile(absolute)));
    }
  }
  await visit(workspace);return files;
}
function effects(before,after,writePaths){
  const changed=[...new Set([...before.keys(),...after.keys()])].filter(path=>before.get(path)!==after.get(path)).sort();
  return {observed:true,changed_paths:changed.filter(path=>writePaths.some(root=>within(path,root))),
    outside_paths:changed.filter(path=>!writePaths.some(root=>within(path,root))),artifacts:[]};
}
function toolValue(result){
  requireValue(result?.success===true&&result.contentItems?.[0]?.type==='inputText','WORKFLOW_RESOURCE_TOOL','The scoped program broker returned no structured result');
  return JSON.parse(result.contentItems[0].text);
}

export function workflowResourceProgramRegistry(){
  const active=new Map();
  const identity=workflowResourceProgramIdentity(),broker_id='workflow-resource-program-broker';
  const evidence_sha256=digest(canonicalJSON({broker_id,identity,scope:'run-pinned-workflow-resource'}));
  const key=context=>`${context.run_id}/${context.node_id}/${context.attempt_id}`;
  return {[name]:{
    identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:identity,broker_id,evidence_sha256},
    async execute({input,argv,permissions,context,signal}){
      requireValue(argv.length>=3&&typeof context.workspace==='string'&&isAbsolute(context.workspace),'WORKFLOW_RESOURCE_CONTRACT','Resource program needs a workspace, program, resource and scratch directory');
      const [program,resourcePath,scratch,...args]=argv;
      const resource=context.resources?.find(item=>item.path===resourcePath);
      requireValue(resource&&digest(resource.bytes)===resource.sha256,'WORKFLOW_RESOURCE_PIN','Executable resource is absent or differs from its Run pin');
      requireValue(permissions.write_paths.some(root=>within(scratch,root)),'WORKFLOW_RESOURCE_SCOPE','Scratch directory is outside the Host write scope');
      const before=await snapshot(context.workspace);
      const entry={before,workspace:context.workspace,writePaths:permissions.write_paths,broker:null};
      active.set(key(context),entry);
      const authorize=async()=>{requireValue(!signal?.aborted,'WORKFLOW_RESOURCE_CANCELLED','Resource execution authority was revoked');};
      const materialized=(context.resources??[]).map(item=>({path:item.path,sha256:item.sha256,
        destination:`${scratch}/${item.sha256}${extname(item.path)}`}));
      const inputBytes=Buffer.from(canonicalJSON(input));
      const inputFile=args.includes('@INPUT@')?{destination:`${scratch}/${digest(inputBytes)}.json`,sha256:digest(inputBytes)}:null;
      const temporary=[...materialized,...(inputFile?[inputFile]:[])];
      const script=materialized.find(item=>item.path===resourcePath).destination;
      let run=null,error=null;
      try{
        await authorize();
        const broker=await createCodexToolBroker({workspace:context.workspace,access:'bounded_write',allowedPaths:permissions.write_paths,
          resources:context.resources,executionBinding:context.execution_binding,runtimeEnvironment:context.runtime_environment,prepareRuntimeEnvironment:context.prepareRuntimeEnvironment,
          inputRoots:typeof context.task_root==='string'&&isAbsolute(context.task_root)?[{name:'task_root',path:context.task_root}]:[],
          authorize,onOperation:async()=>{}});
        entry.broker=broker;
        toolValue(await broker.call('mkdir_workspace',{path:scratch},'scratch'));
        for(const item of materialized){
          let current=null;
          try{current=digest(await readFile(join(context.workspace,...item.destination.split('/'))));}
          catch(error){if(error.code!=='ENOENT')throw error;}
          if(current!==item.sha256)toolValue(await broker.call('materialize_workflow_resource',
            {path:item.path,destination:item.destination,expected_sha256:current},`materialize-${item.sha256}`));
        }
        if(inputFile){let current=null;
          try{current=digest(await readFile(join(context.workspace,...inputFile.destination.split('/'))));}
          catch(error){if(error.code!=='ENOENT')throw error;}
          if(current!==inputFile.sha256)toolValue(await broker.call('write_workspace',
            {path:inputFile.destination,text:inputBytes.toString('utf8'),expected_sha256:current},'materialize-input'));
        }
        const argumentsForRun=args.map(value=>{
          if(value==='@INPUT@')return `@WORKSPACE@/${inputFile.destination}`;
          if(value.startsWith('@RESOURCE:')&&value.endsWith('@')){
            const named=materialized.find(item=>item.path===value.slice(10,-1));
            requireValue(named,'WORKFLOW_RESOURCE_PIN',`Argument refers to a resource absent from this node: ${value}`);
            return `@WORKSPACE@/${named.destination}`;
          }
          return value;
        });
        run=toolValue(await broker.call('run_task_program',{program,args:[`@WORKSPACE@/${script}`,...argumentsForRun],cwd:'workspace'},'run'));
        for(const item of temporary){const absolute=join(context.workspace,...item.destination.split('/'));
          const stat=await lstat(absolute);
          requireValue(stat.isFile()&&!stat.isSymbolicLink()&&digest(await readFile(absolute))===item.sha256,
            'WORKFLOW_RESOURCE_PIN','Materialized resource or input changed during execution');}
      }catch(caught){error=caught;}
      finally{
        try{
          if(entry.broker){const stopped=await entry.broker.quiesce();
            requireValue(stopped.quiescent&&!stopped.error,'WORKFLOW_RESOURCE_STOP','Program did not settle cleanly');}
          for(const item of temporary){const absolute=join(context.workspace,...item.destination.split('/'));
            try{if(digest(await readFile(absolute))===item.sha256)await unlink(absolute);}
            catch(cleanupError){if(cleanupError.code!=='ENOENT')throw cleanupError;}}
        }finally{active.delete(key(context));}
      }
      const observed=effects(before,await snapshot(context.workspace),permissions.write_paths);
      const outside=observed.outside_paths.length>0;
      let output=null;
      if(!error&&run?.exit_code===0&&!outside){try{output=JSON.parse(run.stdout);}
        catch(caught){error=caught;}}
      return {exit_code:error||outside?1:run?.exit_code??1,output,
        diagnostic:error?`${error.code??'WORKFLOW_RESOURCE_ERROR'}: ${error.message}`
          :outside?`Program wrote outside declared scope: ${observed.outside_paths.join(', ')}`:run?.stderr??'',effects:observed};
    },
    async cancel({context}){
      const entry=active.get(key(context));
      if(entry?.broker){const result=await entry.broker.quiesce();requireValue(result.quiescent&&!result.error,'WORKFLOW_RESOURCE_STOP','Program cancellation did not confirm termination');}
      const observed=entry?effects(entry.before,await snapshot(entry.workspace),entry.writePaths):emptyEffects();
      return {termination_confirmed:true,evidence:[{kind:'workflow-resource-program-quiescent',sha256:digest(canonicalJSON({context,broker_id}))}],effects:observed};
    },
  }};
}
