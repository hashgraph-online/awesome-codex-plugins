import { posix } from 'node:path';
import { digest } from '../workflow-revisions.mjs';

const identifier='[A-Za-z_$][\\w$]*';
const escaped=value=>value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const functionBody=(code,name,parameters)=>new RegExp('(?:export )?(?:async )?function '+escaped(name)+'\\('+parameters+'\\)\\s*\\{([\\s\\S]*?)^\\}','m').exec(code)?.[1];
function imported(resources,path,name){
  const text=resources[path]?.toString('utf8')??'';
  const entries=[...text.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]/g)].filter(item=>item[1].split(',').map(value=>value.trim()).includes(name));
  if(entries.length!==1||!entries[0][2].startsWith('.'))return null;
  const resolved=posix.normalize(posix.join(posix.dirname(path),entries[0][2]));return resources[resolved]?resolved:null;
}

function selectedFactory(resources,path,callee,choice,key){
  const module=imported(resources,path,callee);if(!module)return null;
  const bytes=resources[module],code=bytes.toString('utf8');
  const parameters=new RegExp('(?:export )?function '+escaped(callee)+'\\(('+identifier+'),\\s*('+identifier+')(?:,\\s*\\{[^()\\n]*\\} = \\{\\})?\\)\\s*\\{').exec(code);
  if(!parameters)return null;
  const choiceName=parameters[1],envName=parameters[2];
  if(/[\[\]`]/.test(parameters[0]))return null;
  const defaults=/,\s*\{([^{}]*)\}\s*=\s*\{\}/.exec(parameters[0]);
  if(defaults&&defaults[1].split(',').some(item=>!new RegExp('^\\s*'+identifier+'\\s*=\\s*(?:'+identifier+'|process\\.platform)\\s*$').test(item)))return null;
  let body=functionBody(code,callee,escaped(parameters[0].slice(parameters[0].indexOf('(')+1,parameters[0].lastIndexOf(')'))));if(!body)return null;
  const aliases=new Map();
  body=body.replace(new RegExp('const ('+identifier+') = \\(\\) => ('+identifier+')\\(([^;\\n]*)\\);','g'),(_all,alias,factory,args)=>{if(args===envName)aliases.set(alias,factory);return '';});
  body=body.replace(new RegExp('if\\s*\\('+escaped(choiceName)+'\\s*===\\s*([\'\"])([^\'\"]+)\\1\\)\\s*(?:\\{[^{}]*\\}|return null;)','g'),(all,_quote,value)=>value!==choice?'':all);
  const explicit=new RegExp('^\\s*if \\('+escaped(choiceName)+' === [\'\"]'+escaped(choice)+'[\'\"]\\) \\{\\s*if \\(!'+escaped(envName)+'\\.'+escaped(key)+'\\) throw new ('+identifier+')\\([\'\"][^\'\"]*[\'\"]\\);\\s*return ('+identifier+')\\(\\);\\s*\\}').exec(body);
  const automatic=new RegExp('^\\s*if \\('+escaped(envName)+'\\.'+escaped(key)+'\\) return ('+identifier+')\\(\\);\\s*return '+identifier+'\\(\\);\\s*$').exec(body);
  const alias=explicit?.[2]??automatic?.[1],factoryName=aliases.get(alias);if(!factoryName)return null;
  if(explicit&&!new RegExp('^\\s*if \\('+escaped(envName)+'\\.'+escaped(key)+'\\) return '+identifier+'\\(\\);\\s*return '+identifier+'\\(\\);\\s*$').test(body.slice(explicit[0].length)))return null;
  const factory=functionBody(code,factoryName,escaped(envName));if(!factory)return null;
  if(new RegExp('\\b(?:'+escaped(callee)+'|'+escaped(factoryName)+')\\s*=').test(code))return null;
  return {bytes,code,factory,envName,ctor:explicit?.[1]};
}

function dataFactory(selected){
  let {factory,envName,code}=selected;
  const method=new RegExp('async ('+identifier+')\\(('+identifier+')\\)\\s*\\{([\\s\\S]*?)^    \\},?','m').exec(factory);if(!method)return null;
  factory=factory.replace(method[0],'DEFERRED,');
  const locals=new Set(),constants=new Set();
  factory=factory.replace(new RegExp('const ('+identifier+') = '+escaped(envName)+'\\.('+identifier+') \\|\\| ('+identifier+');','g'),(_all,local,_field,constant)=>{locals.add(local);constants.add(constant);return '';});
  factory=factory.replace(/`(?:[^`$]|\$\{[A-Za-z_$][\w$]*\})*`/g,value=>{for(const match of value.matchAll(/\$\{([A-Za-z_$][\w$]*)\}/g))if(!locals.has(match[1]))constants.add(match[1]);return 'LITERAL';});
  const values=[];
  factory=factory.replace(/'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"/g,value=>{values.push(value.slice(1,-1));return 'LITERAL';});
  if(!/^\s*return\s*\{\s*name:\s*LITERAL,\s*(?:id:\s*LITERAL,\s*)?(?:concurrency:\s*\d+,\s*)?DEFERRED,?\s*\};\s*$/.test(factory))return null;
  for(const constant of constants)if(!new RegExp('^const '+escaped(constant)+' = (?:\\d+|[\'\"][^\'\"\\n]*[\'\"]);$','m').test(code))return null;
  return {name:values[0],method:method[1],methodBody:method[3]};
}

// Finite imported data-construction grammar. Spelling a function name, or
// placing it in a test file, never proves purity. Unknown wrappers stay blocked.
export function proveSelectionFixture(resources,path,replacement){
  const text=resources[path]?.toString('utf8');if(!text)return null;
  const assertion=new RegExp('^\\s*assert\\.equal\\(('+identifier+')\\(([\'\"])([^\'\"]+)\\2,\\s*\\{\\s*('+identifier+'):\\s*([\'\"])\\['+escaped(replacement)+'\\]\\5\\s*\\}\\)\\.name,\\s*([\'\"])([\\w-]+)\\6\\);\\s*$','m').exec(text);if(!assertion)return null;
  const selected=selectedFactory(resources,path,assertion[1],assertion[3],assertion[4]);if(!selected)return null;
  const data=dataFactory(selected);if(!data||data.name!==assertion[7])return null;
  return {version:1,kind:'selection_assertion',literal_length:1,resource_sha256:digest(resources[path]),dependency_sha256:[digest(selected.bytes)]};
}

// Pin a direct literal consumer, its imported factory and the invoked deferred
// method. Its first transport must be the unshadowed global fetch, whose
// rejection flows through a data-only Error constructor. A surrounding mock
// cannot authorize another transport or a complex unproven wrapper.
export function proveRejectingFetchFixture(resources,path,replacement){
  const text=resources[path]?.toString('utf8')??'';
  const consumer=new RegExp('^\\s*const ('+identifier+') = ('+identifier+')\\([\'\"]([^\'\"]+)[\'\"],\\s*\\{\\s*('+identifier+'):\\s*[\'\"]\\['+escaped(replacement)+'\\][\'\"]\\s*\\}\\);\\s*$','m').exec(text);if(!consumer)return null;
  // Prove mock lifetime through argument evaluation and method invocation.
  // No statement (including calls through aliases) may occur between installing
  // the rejecting stub, constructing the object, and invoking its method.
  const before=text.slice(0,consumer.index);
  if(!new RegExp('const '+identifier+' = globalThis\\.fetch;\\s*globalThis\\.fetch = async \\(\\) => \\{\\s*throw new (?:TypeError|Error)\\([\'\"][^\'\"\\n]*[\'\"]\\);?\\s*\\};\\s*try \\{\\s*$').test(before))return null;
  const selected=selectedFactory(resources,path,consumer[2],consumer[3],consumer[4]);if(!selected?.ctor)return null;
  const data=dataFactory(selected);if(!data)return null;
  const after=text.slice(consumer.index+consumer[0].length);
  if(!new RegExp('^\\s*await assert\\.rejects\\('+escaped(consumer[1])+'\\.'+escaped(data.method)+'\\(([\'\"])(?:\\\\.|(?!\\1)[^\\\\\\r\\n])*\\1\\),').test(after))return null;
  const {code,envName,ctor}=selected,synth=data.methodBody;
  if(/(?:import[^;]*\bfetch\b|(?:const|let|var|function)\s+fetch\b)/.test(code))return null;
  const beforeFetch=synth.slice(0,synth.indexOf('res = await fetch(url, {'));
  if(!/^\s*const url = `(?:[^`$]|\$\{[A-Za-z_$][\w$]*\})*`;\s*let res;\s*try \{\s*$/.test(beforeFetch))return null;
  if(!new RegExp("headers: \\{ ['\"][^'\"]+['\"]: "+escaped(envName)+'\\.'+escaped(consumer[4])).test(synth))return null;
  const caught=/\} catch \(e\) \{([\s\S]*?)^      \}/m.exec(synth)?.[1];
  if(!caught||!new RegExp('^\\s*throw new '+escaped(ctor)+'\\(`(?:[^`]|`[^`]*`)*`\\);\\s*$').test(caught))return null;
  if(!new RegExp('export class '+escaped(ctor)+' extends Error \\{\\s*constructor\\(message\\) \\{\\s*super\\(message\\);\\s*this\\.name = [\'\"]'+escaped(ctor)+'[\'\"];\\s*\\}\\s*\\}').test(code))return null;
  return {version:1,kind:'rejecting_fetch_fixture',literal_length:1,resource_sha256:digest(resources[path]),dependency_sha256:[digest(selected.bytes)]};
}
