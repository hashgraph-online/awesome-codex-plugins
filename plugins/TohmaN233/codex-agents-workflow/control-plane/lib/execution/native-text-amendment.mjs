import {requireValue} from '../workflow-paths.mjs';
import {validateData} from '../workflow-data-schema.mjs';
import {canonicalJSON} from '../workflow-revisions.mjs';

const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const fail=message=>requireValue(false,'NATIVE_TEXT_AMENDMENT',message);
const exact=(value,keys)=>object(value)&&Object.keys(value).every(key=>keys.includes(key))&&keys.every(key=>Object.hasOwn(value,key));

// Physical lines include their CRLF, LF or CR separator. A trailing separator
// ends its line; it does not manufacture an additional empty physical line.
export function textLineBoundaries(text){
  requireValue(typeof text==='string'&&Buffer.from(text,'utf8').toString('utf8')===text,'NATIVE_TEXT_AMENDMENT','The sealed text field must be exact well-formed UTF8 text');
  const ends=[];const separators=/\r\n|\r|\n/g;let match;
  while((match=separators.exec(text)))ends.push(match.index+match[0].length);
  if(!ends.length||ends.at(-1)<text.length)ends.push(text.length);
  return [0,...ends];
}
export const textLineCount=text=>textLineBoundaries(text).length-1;

export function validateTextAmendmentDeclaration(node,tool,nativeWorker){
  const config=node.completion_contract?.host_check?.text_amendment;if(config===undefined)return;
  const mainItemWorker=node.executor?.kind==='main'&&node.executor.mode==='worker'&&node.fanout?.result_mode==='per_item'&&node.fanout.distribution==='one_per_item';
  requireValue((nativeWorker||mainItemWorker)&&(!node.fanout||!node.fanout.shared_change_field&&(node.fanout.distribution==='one_per_item'||node.fanout.item_delivery==='incremental')),
    'NATIVE_TEXT_AMENDMENT_MODE','Text amendments require a Cooperative native worker with one current completed-result item per child turn; delegated shared-change results are unsupported');
  const schema=node.fanout?node.outputs_schema?.properties?.[node.fanout.result_output]?.items:node.outputs_schema;
  requireValue(exact(config,['fields','repair_scope_field','max_edits','max_replacement_bytes',...(Object.hasOwn(config,'addressing')?['addressing']:[])])
    &&(config.addressing===undefined||config.addressing==='host_ranges')&&Array.isArray(config.fields)&&config.fields.length>0&&config.fields.length<=64
    &&new Set(config.fields).size===config.fields.length&&config.fields.every(field=>typeof field==='string'&&schema?.properties?.[field]?.type==='string'&&schema.required?.includes(field))
    &&typeof config.repair_scope_field==='string'&&Number.isSafeInteger(config.max_edits)&&config.max_edits>=1&&config.max_edits<=64
    &&Number.isSafeInteger(config.max_replacement_bytes)&&config.max_replacement_bytes>=1&&config.max_replacement_bytes<=2*1024*1024,
  'NATIVE_TEXT_AMENDMENT_CONTRACT','Text amendment fields must be required top-level strings with bounded edit and byte limits');
  const scope=tool.output_schema?.properties?.[config.repair_scope_field];
  requireValue(tool.output_schema.required?.includes(config.repair_scope_field)&&scope?.type==='object'&&scope.additionalProperties===false
    &&!(scope.required?.length)&&object(scope.properties)&&Object.keys(scope.properties).length===config.fields.length&&config.fields.every(field=>{
      const ranges=scope.properties[field],item=ranges?.items;
      return ranges?.type==='array'&&item?.type==='object'&&item.additionalProperties===false&&object(item.properties)
        &&Object.keys(item.properties).sort().join(',')==='end_line,start_line'&&item.required?.length===2&&['start_line','end_line'].every(key=>item.required.includes(key)&&item.properties[key].type==='integer'&&item.properties[key].minimum>=1);
    }), 'NATIVE_TEXT_AMENDMENT_SCOPE_SCHEMA','The checker must return a required typed scope object with only declared fields and exact positive line ranges');
}

export function validateTextRepairScope(baseline,scope,config){
  if(!object(scope)||!Object.keys(scope).length)fail('Rejected text needs a nonempty typed repair scope');
  let count=0;
  for(const [field,ranges]of Object.entries(scope)){
    if(!config.fields.includes(field)||!Array.isArray(ranges)||!ranges.length)fail('Repair scope contains an undeclared field or empty ranges');
    const lines=textLineCount(baseline[field]);let last=0;
    for(const range of ranges){
      if(!exact(range,['start_line','end_line'])||!Number.isSafeInteger(range.start_line)||!Number.isSafeInteger(range.end_line)
        ||range.start_line<=last||range.end_line<range.start_line||range.end_line>lines)fail('Repair scope has overlapping, unordered or out-of-bounds physical lines');
      last=range.end_line;count++;
    }
  }
  if(count>64)fail('Repair scope exceeds 64 disjoint ranges');
  return scope;
}

export function textAmendmentSchema(config){
  if(config.addressing==='host_ranges')return {type:'object',properties:{replacements:{type:'array',minItems:1,maxItems:config.max_edits,
    items:{type:'array',items:{type:'string',description:'One content line without a CR or LF separator. Host restores separators and line addresses.'}}}},required:['replacements'],additionalProperties:false};
  return {type:'object',properties:{amendments:{type:'array',minItems:1,maxItems:config.max_edits,items:{type:'object',additionalProperties:false,
    properties:{field:{type:'string',enum:config.fields},start_line:{type:'integer',minimum:1},end_line:{type:'integer',minimum:1},replacement:{type:'string',description:'Exact replacement text for complete physical lines, including explicit separators. Nonempty non-EOF replacement must end with CRLF, LF or CR.'}},
    required:['field','start_line','end_line','replacement']}}},required:['amendments'],additionalProperties:false};
}

function hostRangeTargets(baseline,scope,config){
  validateTextRepairScope(baseline,scope,config);
  const targets=[];
  for(const field of config.fields)for(const range of scope[field]??[]){
    const bounds=textLineBoundaries(baseline[field]),text=baseline[field].slice(bounds[range.start_line-1],bounds[range.end_line]);
    const ending=/(\r\n|\r|\n)$/.exec(text)?.[0]??'',content=ending?text.slice(0,-ending.length):text;
    targets.push({field,...range,lines:content.split(/\r\n|\r|\n/),separators:text.match(/\r\n|\r|\n/g)??[],ending,
      defaultSeparator:/\r\n|\r|\n/.exec(text)?.[0]??/\r\n|\r|\n/.exec(baseline[field])?.[0]??'\n'});
  }
  if(targets.length>config.max_edits)fail('Host repair blocks exceed the pinned edit limit');
  return targets;
}

export function textAmendmentInstruction(baseline,scope,config){
  if(config.addressing!=='host_ranges')return `Return only physical-line amendments for the prior manuscript. Use 1-based inclusive lines; each line includes its separator. Nonempty non-EOF replacement must end with CRLF, LF or CR. Preserve unrelated content. Allowed scope: ${canonicalJSON(scope)}.`;
  const targets=hostRangeTargets(baseline,scope,config);
  return `Host owns field selection, line addresses and separators. The following ${targets.length} affected blocks are already fixed in order. Return replacements with exactly ${targets.length} entries in this order, each an array of content lines without CR or LF characters. Return [] for a deleted block. Return only revised text, without fields, line numbers, hashes or a full manuscript. Preserve meaning and unrelated content. Blocks: ${canonicalJSON(targets.map(({field,lines})=>({field,lines})))}`;
}

export function applyTextAmendment(baseline,scope,config,payload){
  validateTextRepairScope(baseline,scope,config);
  try{validateData(payload,textAmendmentSchema(config));}catch(error){if(error.code!=='DATA_INVALID')throw error;fail(error.message);}
  if(config.addressing==='host_ranges'){
    const targets=hostRangeTargets(baseline,scope,config);
    if(payload.replacements.length!==targets.length)fail('Every Host repair block needs exactly one ordered replacement');
    const amendments=targets.map((target,index)=>{
      const lines=payload.replacements[index];
      if(lines.some(line=>/[\r\n]/.test(line)))fail('Host repair content lines cannot contain line separators');
      const replacement=lines.map((line,n)=>line+(n===lines.length-1?target.ending:target.separators[n]??target.defaultSeparator)).join('');
      return {field:target.field,start_line:target.start_line,end_line:target.end_line,replacement};
    });
    const {addressing,...legacy}=config;
    return applyTextAmendment(baseline,scope,legacy,{amendments});
  }
  const byField=new Map();let bytes=0;
  for(const edit of payload.amendments){
    if(Buffer.from(edit.replacement,'utf8').toString('utf8')!==edit.replacement)fail('Replacement must be exact well-formed UTF8 text');
    bytes+=Buffer.byteLength(edit.replacement,'utf8');
    if(bytes>config.max_replacement_bytes)fail('Replacement UTF8 bytes exceed the pinned limit');
    if(edit.end_line<edit.start_line||!Object.hasOwn(scope,edit.field)||!scope[edit.field].some(range=>edit.start_line>=range.start_line&&edit.end_line<=range.end_line))fail('Edit leaves the sealed rejected field or line scope');
    const boundaries=textLineBoundaries(baseline[edit.field]);
    if(edit.end_line<boundaries.length-1&&edit.replacement&&!/[\r\n]$/.test(edit.replacement))fail('Non-EOF replacement must end with an explicit physical line separator');
    const edits=byField.get(edit.field)??[];
    if(edits.length&&edit.start_line<=edits.at(-1).end_line)fail('Edits must be ordered and nonoverlapping within each field');
    edits.push(edit);byField.set(edit.field,edits);
  }
  const merged=structuredClone(baseline);
  for(const [field,edits]of byField){
    const text=baseline[field],boundaries=textLineBoundaries(text);let cursor=0,parts=[];
    for(const edit of edits){const start=boundaries[edit.start_line-1],end=boundaries[edit.end_line];parts.push(text.slice(cursor,start),edit.replacement);cursor=end;}
    merged[field]=parts.join('')+text.slice(cursor);
  }
  return merged;
}
