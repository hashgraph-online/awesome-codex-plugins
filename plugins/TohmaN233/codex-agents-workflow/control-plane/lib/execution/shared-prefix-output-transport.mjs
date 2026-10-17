import {requireValue} from '../workflow-paths.mjs';
import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {validateData,validateDataSchema} from '../workflow-data-schema.mjs';

// The API format is independent of this turn's semantic contract. The Host
// still validates source readiness and each item's original result separately.
export const SHARED_PREFIX_OUTPUT_SCHEMA=Object.freeze({
  type:'object',
  properties:Object.freeze({json_result:Object.freeze({type:'string',
    description:'The current task result serialized as JSON text.'})}),
  required:Object.freeze(['json_result']),additionalProperties:false
});
export const SHARED_PREFIX_OUTPUT_SCHEMA_SHA256=digest(canonicalJSON(SHARED_PREFIX_OUTPUT_SCHEMA));

export function prepareSharedPrefixOutputTransport(text,semanticSchema){
  requireValue(typeof text==='string'&&text.length>0,'SHARED_PREFIX_OUTPUT_TEXT','Shared-prefix input must be nonempty text');
  validateDataSchema(semanticSchema);
  const contract=canonicalJSON(semanticSchema);
  return {text:text+'\n\nCurrent result contract (JSON Schema):\n'+contract
    +'\nReturn the current task result conforming to this contract. Serialize that result as JSON text in the string field json_result of the API output object. The inner result may be an object, array or scalar as specified by the current contract.',
    output_schema:structuredClone(SHARED_PREFIX_OUTPUT_SCHEMA),schema_sha256:SHARED_PREFIX_OUTPUT_SCHEMA_SHA256};
}

function parse(text,code,label){
  try{return JSON.parse(text);}
  catch(cause){requireValue(false,code,`${label} must be valid JSON`,{cause});}
}

export function decodeSharedPrefixOutputTransport(raw,semanticSchema){
  requireValue(typeof raw==='string','SHARED_PREFIX_OUTPUT_TEXT','Shared-prefix API output must be JSON text');
  validateDataSchema(semanticSchema);
  const envelope=parse(raw,'SHARED_PREFIX_OUTPUT_OUTER_JSON','Shared-prefix API output');
  validateData(envelope,SHARED_PREFIX_OUTPUT_SCHEMA);
  const value=parse(envelope.json_result,'SHARED_PREFIX_OUTPUT_INNER_JSON','Current task result');
  canonicalJSON(value); // Reject non-finite numbers and unsupported JSON depth.
  validateData(value,semanticSchema);
  return envelope.json_result; // Preserve the original inner JSON bytes/text.
}
