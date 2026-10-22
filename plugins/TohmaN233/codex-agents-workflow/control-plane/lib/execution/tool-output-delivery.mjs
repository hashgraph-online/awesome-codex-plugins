import {requireValue} from '../workflow-paths.mjs';

// A serialized UTF-8 byte ceiling is conservative for byte-based tokenization:
// one token cannot encode less than one byte. This is not a chars/token estimate.
// Include the whole content envelope and JSON escaping, not only its output text.
export const serializedToolResultBytes=result=>Buffer.byteLength(JSON.stringify(result),'utf8');

export function inheritedToolOutputBudget(metadata,config={}) {
  const explicit=config.tool_output_token_limit;
  const source=explicit!==undefined&&explicit!==null?'user_config':'model_metadata';
  const policy=source==='user_config'?{mode:'tokens',limit:explicit}:metadata?.truncation_policy;
  requireValue(policy&&['tokens','bytes'].includes(policy.mode)&&Number.isSafeInteger(policy.limit)
    &&policy.limit>=512,'CODEX_TOOL_OUTPUT_BUDGET',
    'An effective inherited tool-output budget of at least 512 tokens/bytes is required for lossless command delivery');
  return Object.freeze({source,mode:policy.mode,limit:policy.limit,max_result_bytes:policy.limit});
}
