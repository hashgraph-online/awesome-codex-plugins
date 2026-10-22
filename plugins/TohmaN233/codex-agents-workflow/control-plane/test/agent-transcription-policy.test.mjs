import test from 'node:test';
import assert from 'node:assert/strict';
import {agentTranscriptionClauses} from '../lib/agent-transcription-policy.mjs';

test('requested output is an artifact noun rather than a protocol copying command',()=>{
  for(const passive of ['requested','required','expected'])
    assert.deepEqual(agentTranscriptionClauses(`When no multilingual output is ${passive}, translation_languages is empty and the original single-language path applies.`),[]);
});

test('passive artifact wording never exempts a transport assignment or copying clause',()=>{
  for(const instruction of ['Output original paths unchanged.','Output is required to return input paths.','Output is requested from supplied records verbatim.','An output is expected, then return upstream fields.'])
    assert.equal(agentTranscriptionClauses(instruction).length,1,instruction);
});

test('declared enum assignments represent decisions rather than unchanged upstream transport',()=>{
  for(const assignment of ['mode_change=unchanged','mode_change = "unchanged"',"mode_change='unchanged'"]){
    const instruction=`Emit ${assignment} unless the user changes the requested mode; otherwise emit the newly requested mode.`;
    assert.deepEqual(agentTranscriptionClauses(instruction,{mode_change:['unchanged','create','update','audit']}),[]);
    assert.equal(agentTranscriptionClauses(instruction).length,1,'An undeclared assignment cannot bypass validation');
  }
});

test('literal decisions never exempt another copied value or a relay without a new decision',()=>{
  const literals={mode_change:['unchanged','create']};
  for(const instruction of ['Emit mode_change=unchanged and copy upstream records.','Emit mode_change=unchanged from the input.','Pass findings through unchanged.','Return the upstream findings unchanged.'])
    assert.equal(agentTranscriptionClauses(instruction,literals).length,1,instruction);
  assert.equal(agentTranscriptionClauses('Emit mode_change=unmodified.',literals).length,1);
});
