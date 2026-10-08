import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { requireValue } from '../workflow-paths.mjs';

const VERSION='1.0.0';
const STAGES=Object.freeze({
  'authoring-graph-assembly':Object.freeze({stage:'graph_assembly',previous:null}),
  'authoring-execution-binding':Object.freeze({stage:'execution_binding',previous:'graph_assembly'}),
  'authoring-deterministic-validation':Object.freeze({stage:'deterministic_validation',previous:'execution_binding'}),
});
const stageEvidenceSchema=stage=>({
  type:'object',
  required:['stage','proposal_hash','result'],
  additionalProperties:false,
  properties:{
    stage:{type:'string',enum:[stage]},
    proposal_hash:{type:'string',minLength:64,maxLength:64,pattern:'^[a-f0-9]+$'},
    result:{type:'object'},
  },
});
const inputSchema=({stage,previous})=>({
  type:'object',
  required:previous?['evidence','previous']:['evidence'],
  additionalProperties:false,
  properties:{
    evidence:stageEvidenceSchema(stage),
    ...(previous?{previous:stageEvidenceSchema(previous)}:{}),
  },
});

const implementationBytes=readFileSync(fileURLToPath(import.meta.url),'utf8').replace(/\r\n/g,'\n');
export const AUTHORING_HOST_IMPLEMENTATION_SHA256=digest(implementationBytes);

export function authoringToolIdentity(name){
  const stage=STAGES[name];
  requireValue(stage,'AUTHORING_HOST_TOOL_UNKNOWN',`Unknown authoring Host tool ${name}`);
  return {name,version:VERSION,sha256:digest(canonicalJSON({name,version:VERSION,stage,implementation_sha256:AUTHORING_HOST_IMPLEMENTATION_SHA256}))};
}

export function authoringHostToolContracts(){
  return Object.entries(STAGES).map(([id,stage])=>({
    id,
    identity:authoringToolIdentity(id),
    argv:[id],
    input_schema:inputSchema(stage),
    output_schema:stageEvidenceSchema(stage.stage),
    env_allow:[],
    permissions:{network:false,read_paths:[],write_paths:[]},
    output_cap_bytes:32768,
    deadline_ms:10000,
    idempotency:{mode:'safe'},
  }));
}

function executeFor(tool){
  const expected=STAGES[tool];
  return async ({input})=>{
    const evidence=input.evidence;
    requireValue(evidence.stage===expected.stage,'AUTHORING_HOST_STAGE',`Expected ${expected.stage} evidence`);
    if(expected.previous){
      requireValue(input.previous?.stage===expected.previous,'AUTHORING_HOST_SEQUENCE',`Expected ${expected.previous} predecessor evidence`);
      requireValue(input.previous.proposal_hash===evidence.proposal_hash,'AUTHORING_HOST_SEQUENCE','Authoring Host stages disagree about the canonical proposal');
    }
    return {exit_code:0,output:structuredClone(evidence),diagnostic:`AUTHORING_HOST_STAGE: ${expected.stage}`,effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};
  };
}

async function cancel({context={}}={}){
  return {termination_confirmed:true,evidence:[{kind:'authoring-host-stage-settled',sha256:digest(canonicalJSON({broker:'authoring-compiler-stages',version:VERSION,run_id:context.run_id??null,node_id:context.node_id??null,attempt_id:context.attempt_id??null,settled:true}))}],effects:{observed:true,changed_paths:[],outside_paths:[],artifacts:[]}};
}

export function authoringHostToolRegistry(){
  const broker_id='authoring-compiler-stages';
  return Object.fromEntries(Object.keys(STAGES).map(id=>{
    const identity=authoringToolIdentity(id);
    const evidence_sha256=digest(canonicalJSON({broker_id,version:VERSION,tool:id,implementation_sha256:AUTHORING_HOST_IMPLEMENTATION_SHA256,network:false,writes:false}));
    return [id,{identity,attestation:{qualified:true,cancellable:true,effect_observation:true,tool_identity:identity,broker_id,evidence_sha256},execute:executeFor(id),cancel}];
  }));
}

export const AUTHORING_HOST_TOOL_IDS=Object.freeze(Object.keys(STAGES));
