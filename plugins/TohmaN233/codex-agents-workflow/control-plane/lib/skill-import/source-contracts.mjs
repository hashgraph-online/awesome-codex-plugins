import { posix } from 'node:path';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';

const executableNames = new Set(['python','python3','node','ffmpeg','ffprobe','git','java','rscript','codegraph']);
const safe = value => value.replace(/[^A-Za-z0-9]+/g,'_').replace(/^_+|_+$/g,'').slice(0,64).toLowerCase() || 'resource';
const lineNumber = (text,index) => text.slice(0,index).split('\n').length;
const sourceSpan = (resource,text,start,end) => ({resource,start_line:lineNumber(text,start),end_line:lineNumber(text,end)});

function balancedCalls(text,name){
  const calls=[];let cursor=0;
  while(cursor<text.length){
    const found=text.indexOf(name,cursor);if(found<0)break;
    let open=found+name.length;while(/\s/.test(text[open] ?? ''))open++;
    if(text[open]!=='('){cursor=open+1;continue;}
    let depth=0,quote='',escaped=false,index=open;
    for(;index<text.length;index++){
      const char=text[index];
      if(quote){if(escaped)escaped=false;else if(char==='\\')escaped=true;else if(char===quote)quote='';continue;}
      if(char==='"'||char==="'"){quote=char;continue;}
      if(char==='(')depth++;else if(char===')'&&--depth===0){calls.push({start:found,end:index+1,body:text.slice(open+1,index)});index++;break;}
    }
    cursor=Math.max(index,open+1);
  }
  return calls;
}

const pythonStrings = value => [...value.matchAll(/(?:^|[,{[(\s])(?:[rubf]{0,2})?(["'])(.*?)\1/gis)].map(match=>match[2]);
const literal = value => {
  const trimmed=value.trim();
  if(/^[-+]?\d+(?:\.\d+)?$/.test(trimmed))return Number(trimmed);
  if(trimmed==='True')return true;if(trimmed==='False')return false;if(trimmed==='None')return null;
  const string=trimmed.match(/^(?:[rubf]{0,2})?(["'])(.*?)\1$/is);return string?string[2]:undefined;
};
const keyword = (body,name) => body.match(new RegExp(`\\b${name}\\s*=\\s*([^,\\n)]+)`,'i'))?.[1];

function argparseContract(resource,bytes){
  const text=bytes.toString('utf8'),calls=balancedCalls(text,'add_argument');
  if(!calls.length)return null;
  const positionals=[],options=[],spans=[];
  for(const call of calls){
    const names=pythonStrings(call.body).filter(item=>item.length>0);if(!names.length)continue;
    const flags=names.filter(item=>item.startsWith('-')),required=/\brequired\s*=\s*True\b/.test(call.body),nargs=literal(keyword(call.body,'nargs') ?? ''),action=literal(keyword(call.body,'action') ?? ''),type=keyword(call.body,'type')?.trim() ?? '';
    const choicesText=call.body.match(/\bchoices\s*=\s*[\[{(]([^\]})]*)[\]})]/s)?.[1] ?? '';
    const choices=pythonStrings(choicesText);
    const entry={name:flags.length?(flags.find(item=>item.startsWith('--')) ?? flags[0]).replace(/^-+/, '').replaceAll('-','_'):names[0],...(required?{required:true}:{}),...(nargs!==undefined?{nargs}:{}),...(action?{action}:{}),...(type?{value_type:type}:{}),...(choices.length?{choices}:{}),source_span:sourceSpan(resource,text,call.start,call.end)};
    if(flags.length)options.push({...entry,flags});else positionals.push({...entry,required:true});
    spans.push(entry.source_span);
  }
  if(!positionals.length&&!options.length)return null;
  const hash=digest(bytes),contract_id=`interface_${safe(resource)}_${hash.slice(0,12)}`;
  return {contract_id,kind:'python_cli',authority:'interface',status:'resolved',resource,resource_sha256:hash,source_spans:spans,interface:{interpreter:'python',entrypoint:resource,positionals,options}};
}

function pythonArtifactContract(resource,bytes){
  const text=bytes.toString('utf8'),properties={},required=new Set(),spans=[];
  for(const match of text.matchAll(/\brequired\s*=\s*[\[(]([^\])]+)[\])]/gs)){
    for(const key of pythonStrings(match[1]))required.add(key);
    spans.push(sourceSpan(resource,text,match.index,match.index+match[0].length));
  }
  for(const match of text.matchAll(/(?:\b(?:self\.)?(?:spec|data|payload|scenario)\s*\[\s*["']([^"']+)["']\s*\]|\b(?:self\.)?(?:spec|data|payload|scenario)\.get\(\s*["']([^"']+)["']\s*\))\s*!=\s*([^:\n]+)/g)){
    const key=match[1]??match[2],value=literal(match[3]);if(value===undefined)continue;
    properties[key]={const:value};spans.push(sourceSpan(resource,text,match.index,match.index+match[0].length));
  }
  for(const match of text.matchAll(/(?:\b(?:self\.)?(?:spec|data|payload|scenario)\s*\[\s*["']([^"']+)["']\s*\]|\b(?:self\.)?(?:spec|data|payload|scenario)\.get\(\s*["']([^"']+)["']\s*\))\s+not\s+in\s+([\[{(][^\]})]+[\]})])/g)){
    const key=match[1]??match[2],values=pythonStrings(match[3]);if(!values.length)continue;
    properties[key]={type:'string',enum:values};spans.push(sourceSpan(resource,text,match.index,match.index+match[0].length));
  }
  const variables=new Map();
  for(const match of text.matchAll(/\b([A-Za-z_]\w*)\s*=\s*(?:_require_list\(\s*)?(?:self\.)?(?:spec|data|payload|scenario)\.get\(\s*["']([^"']+)["']/g))variables.set(match[1],match[2]);
  for(const match of text.matchAll(/not\s+isinstance\(\s*([A-Za-z_]\w*)\s*,\s*(list|dict|str|int|float|bool)\s*\)([^\n]*)/g)){
    const key=variables.get(match[1]);if(!key)continue;
    const map={list:'array',dict:'object',str:'string',int:'integer',float:'number',bool:'boolean'},schema={type:map[match[2]]};
    if(match[2]==='list'&&new RegExp(`\\bor\\s+not\\s+${match[1]}\\b`).test(match[3]))schema.minItems=1;
    properties[key]={...(properties[key]??{}),...schema};spans.push(sourceSpan(resource,text,match.index,match.index+match[0].length));
  }
  for(const [variable,key] of variables){
    const direct=new RegExp(`for\\s+([A-Za-z_]\\w*)\\s+in\\s+${variable}\\s*:[\\s\\S]{0,500}?_require_mapping\\(\\s*\\1\\b`,'m').exec(text);
    const enumerated=new RegExp(`for\\s+[A-Za-z_]\\w*\\s*,\\s*([A-Za-z_]\\w*)\\s+in\\s+enumerate\\(\\s*${variable}\\s*\\)\\s*:[\\s\\S]{0,500}?_require_mapping\\(\\s*\\1\\b`,'m').exec(text);
    const loop=direct??enumerated;
    if(loop){properties[key]={...(properties[key]??{}),type:'array',items:{type:'object',additionalProperties:true}};spans.push(sourceSpan(resource,text,loop.index,loop.index+loop[0].length));}
  }
  for(const match of text.matchAll(/not\s+str\(\s*(?:self\.)?(?:spec|data|payload|scenario)\.get\(\s*["']([^"']+)["'][^)]*\)[^\n]*\.strip\(\)/g)){properties[match[1]]={type:'string',minLength:1};spans.push(sourceSpan(resource,text,match.index,match.index+match[0].length));}
  for(const [variable,key] of variables)if(new RegExp(`\\bif\\s+not\\s+${variable}\\s*:`).test(text)){properties[key]={...(properties[key]??{}),type:'array',minItems:1};}
  for(const key of required)properties[key]??={};
  for(const key of Object.keys(properties))if(!required.has(key)&&!Object.hasOwn(properties[key],'const')&&!Object.hasOwn(properties[key],'enum'))delete properties[key];
  if(!Object.keys(properties).length)return null;
  const hash=digest(bytes),contract_id=`artifact_${safe(resource)}_${hash.slice(0,12)}`;
  // A file-wide lexical scan cannot prove which function consumes the object,
  // or that it describes a producer's output. Keep the constraints as review
  // evidence, never as an exact Host-enforced artifact schema.
  return {contract_id,kind:'json_artifact',authority:'source_observation',status:'candidate',observed_direction:'read',resource,resource_sha256:hash,source_spans:dedupeSpans(spans),artifact_schema:{type:'object',properties,required:[...required],additionalProperties:true}};
}

function dedupeSpans(spans){return [...new Map(spans.map(item=>[canonicalJSON(item),item])).values()].sort((a,b)=>a.resource.localeCompare(b.resource)||a.start_line-b.start_line||a.end_line-b.end_line);}

/** Statically indexes exact source interfaces. It never imports or executes source code. */
export function sourceContractIndex(resources){
  const contracts=[];
  for(const resource of Object.keys(resources).sort()){
    if(!/\.py$/i.test(resource))continue;
    const bytes=Buffer.from(resources[resource]);
    for(const contract of [argparseContract(resource,bytes),pythonArtifactContract(resource,bytes)])if(contract)contracts.push(contract);
  }
  return {contract:'workflow-source-contract-index/v1',contracts:contracts.sort((a,b)=>a.contract_id.localeCompare(b.contract_id))};
}

export function sourceContractMap(resources){return new Map(sourceContractIndex(resources).contracts.map(item=>[item.contract_id,item]));}

function shellTokens(line){
  const tokens=[];let value='',quote='',quoted=false,escaped=false;
  const push=()=>{if(value){tokens.push({value,quoted});value='';quoted=false;}};
  for(const char of line){
    if(quote){if(escaped){value+=char;escaped=false;}else if(char==='\\'&&quote==='"')escaped=true;else if(char===quote){quote='';quoted=true;}else value+=char;continue;}
    if(char==='"'||char==="'"){quote=char;quoted=true;continue;}
    if(/\s/.test(char)){push();continue;}
    if(['|',';'].includes(char)){push();tokens.push({value:char,quoted:false});continue;}
    value+=char;
  }
  push();return tokens;
}

const normalizedExecutable = value => /^rscript$/i.test(value)?'Rscript':value.toLowerCase();

/** Returns actual command-position dependencies and explicit dependency prose; quoted arguments never create dependencies. */
export function dependencyExecutables(line){
  const inline=[...line.matchAll(/`([^`]+)`/g)].map(match=>match[1]);
  if(inline.length){const outer=line.replace(/`[^`]+`/g,' ');return [...new Set([...inline.flatMap(dependencyExecutables),...dependencyExecutables(outer)])];}
  const cleaned=line.replace(/^\s*(?:(?:\d+[.)]|[-*+])\s*)?`?\s*/,'').replace(/`\s*$/,'');
  const tokens=shellTokens(cleaned),found=new Set(),first=tokens.find(item=>!item.quoted)?.value?.replace(/^&$/,'');
  const basename=value=>posix.basename(String(value).replaceAll('\\','/')).replace(/\.(?:exe|cmd|bat)$/i,'').toLowerCase();
  let commandStart=true;
  for(let index=0;index<tokens.length;index++){
    const token=tokens[index];
    if(['|',';','&&','||'].includes(token.value)){commandStart=true;continue;}
    if(!commandStart||token.quoted)continue;
    let name=basename(token.value);if(['sudo','env','command','call','&'].includes(name)){commandStart=true;continue;}
    if(executableNames.has(name))found.add(normalizedExecutable(name));
    commandStart=false;
  }
  if(!found.size || !executableNames.has(basename(first))){
    const unquoted=cleaned.replace(/(["']).*?\1/g,' ');
    if(/\b(?:require(?:s|d)?|dependency|install|need(?:s)?|use|with|run|available)\b|\bon\s+(?:the\s+)?PATH\b/i.test(unquoted))for(const match of unquoted.matchAll(/\b(?:python3?|node|ffmpeg|ffprobe|git|java|Rscript|codegraph)\b/gi))found.add(normalizedExecutable(match[0]));
  }
  return [...found];
}
