import { requireValue } from '../workflow-paths.mjs';

const object=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const portableKeywords=new Set(['type','properties','required','additionalProperties','items','enum','const','description','anyOf','minLength','maxLength','pattern','minItems','maxItems','minimum','maximum','exclusiveMinimum','exclusiveMaximum']);

// Codex App Server uses strict structured output: every object is closed and
// every declared property is required. Optional Workflow fields are nullable
// only at the model boundary; the Host restores omission before validation.
export function codexStructuredSchema(source){
  const visit=(schema,depth=0)=>{
    requireValue(object(schema)&&depth<=10,'CODEX_OUTPUT_SCHEMA','Authoring output schema exceeds the structured-output nesting contract');
    if(!schema.type){
      requireValue(Object.keys(schema).every(key=>key==='description'),'CODEX_OUTPUT_SCHEMA','An untyped authoring slot must be a bounded semantic scalar');
      return {anyOf:[{type:'string'},{type:'number'},{type:'boolean'}],...(schema.description?{description:schema.description}:{})};
    }
    const result=Object.fromEntries(Object.entries(schema).filter(([key])=>portableKeywords.has(key)&&!['properties','required','additionalProperties','items'].includes(key)));
    if(schema.type==='object'){
      requireValue(schema.additionalProperties===false&&object(schema.properties),'CODEX_OUTPUT_SCHEMA','Structured authoring objects must declare closed properties');
      const required=new Set(schema.required??[]),properties={};
      for(const [key,child] of Object.entries(schema.properties)){
        const converted=visit(child,depth+1);
        properties[key]=required.has(key)?converted:{anyOf:[converted,{type:'null'}]};
      }
      return {...result,properties,required:Object.keys(properties),additionalProperties:false};
    }
    if(schema.type==='array'){
      requireValue(object(schema.items),'CODEX_OUTPUT_SCHEMA','Structured authoring arrays need an item schema');
      result.items=visit(schema.items,depth+1);
    }
    return result;
  };
  const schema=visit(source);
  requireValue(schema.type==='object','CODEX_OUTPUT_SCHEMA','Structured output root must be an object');
  let properties=0,enums=0;
  const audit=(node,root=false)=>{
    requireValue(object(node)&&!Object.keys(node).some(key=>!portableKeywords.has(key)),'CODEX_OUTPUT_SCHEMA','Structured output contains an unsupported keyword');
    if(node.anyOf){requireValue(!root&&Array.isArray(node.anyOf)&&node.anyOf.length>0,'CODEX_OUTPUT_SCHEMA','Structured output union must be a non-root anyOf');node.anyOf.forEach(item=>audit(item));return;}
    if(node.type==='object'){
      const names=Object.keys(node.properties??{});
      requireValue(node.additionalProperties===false&&Array.isArray(node.required)&&node.required.length===names.length&&names.every(name=>node.required.includes(name)),'CODEX_OUTPUT_SCHEMA','Every structured object must be closed with all fields required');
      properties+=names.length;Object.values(node.properties).forEach(item=>audit(item));
    }
    if(node.type==='array')audit(node.items);
    enums+=(node.enum??[]).length;
  };
  audit(schema,true);
  requireValue(properties<=5000&&enums<=1000,'CODEX_OUTPUT_SCHEMA','Structured output exceeds the documented property or enum limit');
  return schema;
}

export function restoreOptionalOmissions(value,schema){
  if(Array.isArray(value)&&schema?.type==='array')return value.map(item=>restoreOptionalOmissions(item,schema.items));
  if(!object(value)||schema?.type!=='object')return value;
  const required=new Set(schema.required??[]),restored={...value};
  for(const [key,child] of Object.entries(schema.properties??{})){
    if(!Object.hasOwn(restored,key))continue;
    if(restored[key]===null&&!required.has(key))delete restored[key];
    else restored[key]=restoreOptionalOmissions(restored[key],child);
  }
  return restored;
}
