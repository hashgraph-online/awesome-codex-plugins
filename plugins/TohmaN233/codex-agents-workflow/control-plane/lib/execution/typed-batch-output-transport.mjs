import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {validateData,validateDataSchema} from '../workflow-data-schema.mjs';
import {strictAgentOutputSchema} from './host-main-automation.mjs';
import {CODEX_NORMAL_PREFIX_SETUP_SCHEMA} from './codex-session.mjs';

/** One typed API contract for the common-only source and every batch child. */
export function createTypedBatchOutputTransport(itemSchema,{repair_schema}={}){
  validateDataSchema(itemSchema);
  const item=structuredClone(itemSchema),strict=strictAgentOutputSchema(item);
  requireValue(canonicalJSON(item)===canonicalJSON(strict),'TYPED_BATCH_OUTPUT_SCHEMA','Batch item schema must already be the exact strict output schema');
  const repair=repair_schema===undefined?undefined:structuredClone(repair_schema);
  if(repair){validateDataSchema(repair);requireValue(canonicalJSON(repair)===canonicalJSON(strictAgentOutputSchema(repair)),
    'TYPED_BATCH_OUTPUT_SCHEMA','Repair schema must already be the exact strict output schema');}
  const itemHash=digest(canonicalJSON(item)),repairHash=repair?digest(canonicalJSON(repair)):null,setupHash=digest(canonicalJSON(CODEX_NORMAL_PREFIX_SETUP_SCHEMA));
  const api={type:'object',properties:{results:{type:'array',minItems:0,maxItems:1,items:item},
    ...(repair?{repairs:{type:'array',minItems:0,maxItems:1,items:repair}}:{})},required:['results',...(repair?['repairs']:[])],additionalProperties:false};
  validateDataSchema(api);
  const apiHash=digest(canonicalJSON(api));
  // Validate framing here; Host retains original semantic validation and its
  // same-child correction loop. Object fields are not narrowed or discarded.
  const framing={...api,properties:{results:{...api.properties.results,items:item.type?{type:item.type}:{}},
    ...(repair?{repairs:{...api.properties.repairs,items:repair.type?{type:repair.type}:{}}}:{})}};
  const checkSchema=(schema,expected)=>{
    validateDataSchema(schema);
    requireValue(digest(canonicalJSON(schema))===expected,'TYPED_BATCH_OUTPUT_SCHEMA','Current output schema differs from the pinned batch phase contract');
  };
  const prepare=(text,schema,setup)=>{
    requireValue(typeof text==='string'&&text.length>0,'TYPED_BATCH_OUTPUT_TEXT','Typed batch input must be nonempty text');
    const amendment=!setup&&repairHash!==null&&digest(canonicalJSON(schema))===repairHash;
    checkSchema(schema,setup?setupHash:amendment?repairHash:itemHash);
    return {text:text+'\n\n'+(setup
      ?'Common-only preparation: return results=[]'+(repair?' and repairs=[]':'')+' in the API output object. Do not produce an item result.'
      :amendment?'Return results=[] and exactly one typed amendment object in repairs. Do not return a full item result.'
      :'Return exactly one typed semantic item in results'+(repair?' and repairs=[]':'')+'. Do not serialize the item as a JSON string.'),
    output_schema:structuredClone(api),schema_sha256:apiHash};
  };
  const decode=(raw,schema,setup)=>{
    requireValue(typeof raw==='string','TYPED_BATCH_OUTPUT_TEXT','Typed batch API output must be JSON text');
    const amendment=!setup&&repairHash!==null&&digest(canonicalJSON(schema))===repairHash;
    checkSchema(schema,setup?setupHash:amendment?repairHash:itemHash);
    let envelope;
    try{envelope=JSON.parse(raw);}
    catch(cause){requireValue(false,'TYPED_BATCH_OUTPUT_JSON','Typed batch API output must be valid JSON',{cause});}
    canonicalJSON(envelope);
    validateData(envelope,framing);
    requireValue(envelope.results.length===(setup||amendment?0:1)&&(!repair||envelope.repairs.length===(amendment?1:0)),'TYPED_BATCH_OUTPUT_PHASE',setup
      ?'Common-only preparation cannot produce an item result':'A child must produce exactly one item result');
    return JSON.stringify(setup?{ready:true}:amendment?envelope.repairs[0]:envelope.results[0]);
  };
  return Object.freeze({prepare:(text,schema)=>prepare(text,schema,false),decode:(raw,schema)=>decode(raw,schema,false),
    prepare_setup:(text,schema)=>prepare(text,schema,true),decode_setup:(raw,schema)=>decode(raw,schema,true),
    get api_schema(){return structuredClone(api);},api_schema_sha256:apiHash,setup_schema:CODEX_NORMAL_PREFIX_SETUP_SCHEMA});
}
