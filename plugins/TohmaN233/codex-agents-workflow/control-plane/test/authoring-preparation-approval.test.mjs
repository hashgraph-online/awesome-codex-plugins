import test from 'node:test';
import assert from 'node:assert/strict';
import {hostPreparationObservationEvidence} from '../lib/skill-import/source-requirements.mjs';

function absorbed(line,quote=line,{name='python',kind='approval'}={}){
  const span={resource:'source/SKILL.md',start_line:1,end_line:1};
  return hostPreparationObservationEvidence(
    {requirement_kind:kind,source_spans:[span]},
    {requirement_kind:'dependency',source_spans:[span],details:{phase:'unconditional',executable:name,source_quote:quote}},
    {'source/SKILL.md':Buffer.from(line)},
  );
}

test('Host preparation checks the whole observed approval clause even with a shortened quote',()=>{
  assert.equal(absorbed('If Python is missing, ask for approval to install Python.'),true);
  assert.equal(absorbed('Ask for approval to install Python >=3.11.'),true);
  assert.equal(absorbed('Ask for approval to install Python if missing.'),true);
  assert.equal(absorbed('Ask for input for the Python path.',undefined,{kind:'user_input'}),true);
  const prefix='Ask for approval to install Python';
  for(const suffix of [' and publish the result.',' as well as publish the result.',' plus publish the result.',' followed by publishing the result.']){
    assert.equal(absorbed(prefix+suffix),false,suffix);
    assert.equal(absorbed(prefix+suffix,prefix),false,`short quote hides ${suffix}`);
  }
  assert.equal(absorbed('Use Python to locate the release draft and obtain approval before publishing.'),false);
  assert.equal(absorbed('Ask for input for the Python path as well as the release destination.',undefined,{kind:'user_input'}),false);
  assert.equal(absorbed('Ask for approval to install render+publish.',undefined,{name:'render'}),false);
});
