import { posix } from 'node:path';
import { builtinModules } from 'node:module';
import { canonicalJSON, digest } from '../workflow-revisions.mjs';
import { authoringSourcePath } from './authoring-source.mjs';
import { sourceContractIndex } from './source-contracts.mjs';
import { sourceSectionInventory } from './source-dispositions.mjs';

const program = /\.(?:py|[cm]?js|sh|ps1|cmd|bat)$/i;
const interpreters = /^(?:python(?:3(?:\.\d+)?)?|node|bash|sh|pwsh|powershell|cmd|Rscript)(?:\.exe)?$/i;
const processNames = new Set(['exec', 'execSync', 'execFile', 'execFileSync', 'spawn', 'spawnSync']);
const jsBuiltins = new Set(builtinModules.flatMap(name => [name, name.replace(/^node:/, '')]));
const pythonStdlib = new Set(('abc argparse array ast asyncio base64 bisect builtins calendar collections concurrent contextlib copy csv ctypes dataclasses datetime decimal difflib email enum errno faulthandler fnmatch fractions functools gc getpass glob gzip hashlib heapq hmac html http importlib inspect io itertools json logging math mimetypes multiprocessing numbers operator os pathlib pickle platform pprint queue random re resource sched secrets selectors shlex shutil signal socket sqlite3 ssl stat statistics string struct subprocess sys tempfile textwrap threading time timeit tkinter tomllib traceback types typing unittest urllib uuid warnings weakref xml zipfile zoneinfo').split(' '));
const sorted = values => [...new Set(values)].sort();
const normalize = value => posix.normalize(value.replaceAll('\\', '/'));
const executableName = value => posix.basename(value.replaceAll('\\', '/')).replace(/\.exe$/i, '');

function evidence(resource, bytes, start, end) {
  const text = bytes.toString('utf8'), before = text.slice(0, start), until = text.slice(0, end);
  return {
    resource, resource_sha256: digest(bytes), source_quote: text.slice(start, end),
    source_span: { resource, start_line: before.split('\n').length, end_line: until.split('\n').length },
    source_location: { start_byte: Buffer.byteLength(before), end_byte: Buffer.byteLength(until), start_column: start - before.lastIndexOf('\n'), end_column: end - until.lastIndexOf('\n') },
  };
}

// Preserve offsets while removing comments and string bodies from the recognizer.
// Templates are opaque: evaluating interpolation is deliberately out of scope.
function codeMask(text, python = false) {
  const out = text.split('');
  const blank = (start, end) => { for (let i = start; i < end; i++) if (out[i] !== '\n') out[i] = ' '; };
  for (let i = 0; i < text.length;) {
    if ((!python && text.startsWith('//', i)) || (python && text[i] === '#')) {
      const end = text.indexOf('\n', i); blank(i, end < 0 ? text.length : end); i = end < 0 ? text.length : end; continue;
    }
    if (!python && text.startsWith('/*', i)) { const end = text.indexOf('*/', i + 2); const stop = end < 0 ? text.length : end + 2; blank(i, stop); i = stop; continue; }
    if (!python && text[i] === '/' && /(?:[=(:,;\[!&|?]|\breturn)\s*$/.test(text.slice(0, i))) {
      const start = i++; let bracket = false;
      for (; i < text.length && text[i] !== '\n'; i++) { if (text[i] === '\\') { i++; continue; } if (text[i] === '[') bracket = true; else if (text[i] === ']') bracket = false; else if (text[i] === '/' && !bracket) { i++; break; } }
      blank(start, i); continue;
    }
    if (['"', "'", '`'].includes(text[i])) {
      const start = i, quote = python && text.slice(i, i + 3) === text[i].repeat(3) ? text[i].repeat(3) : text[i]; i += quote.length;
      for (; i < text.length; i++) { if (text[i] === '\\') { i++; continue; } if (text.startsWith(quote, i)) { i += quote.length; break; } }
      blank(start, i); continue;
    }
    i++;
  }
  return out.join('');
}

function callEnd(mask, open) {
  let depth = 0;
  for (let index = open; index < mask.length; index++) { if (mask[index] === '(') depth++; if (mask[index] === ')' && --depth === 0) return index + 1; }
  return null;
}

function splitArguments(text) {
  const mask = codeMask(text), result = []; let depth = 0, start = 0;
  for (let i = 0; i < mask.length; i++) {
    if ('([{'.includes(mask[i])) depth++;
    else if (')]}'.includes(mask[i])) depth--;
    else if (mask[i] === ',' && depth === 0) { result.push(text.slice(start, i).trim()); start = i + 1; }
  }
  result.push(text.slice(start).trim()); return result;
}

function literalString(value) {
  if (!/^(["'])(?:\\.|(?!\1)[^\\])*\1$/s.test(value.trim())) return null;
  const text = value.trim();
  // Only ordinary escapes; unknown escapes retain their spelling as evidence.
  return text.slice(1, -1).replace(/\\([\\'"nrt])/g, (_, char) => ({ n: '\n', r: '\r', t: '\t' }[char] ?? char));
}
function processInterface(executableExpression, argvExpression, resource, resources, python) {
  const executable = literalString(executableExpression) ?? (!python && executableExpression === 'process.execPath' ? 'node' : python && executableExpression === 'sys.executable' ? 'python' : null);
  if (executable === null) return null;
  if (!/^\[[\s\S]*\]$/.test(argvExpression ?? '')) return {executable,entrypoint:null,argv:null,argv_expression:argvExpression ?? null,status:'unresolved',files:[]};
  const expressions = splitArguments(argvExpression.slice(1, -1)).filter(Boolean), argv = expressions.map(literalString);
  const fixed = argv.filter(value => value !== null), iface = commandInterface([executable,...fixed].map(value => `"${value.replaceAll('"', '\\"')}"`).join(' '), resource, resources, true) ?? {executable,entrypoint:null,files:[],status:'literal'};
  iface.argv = argv;
  if (literalString(executableExpression) === null) iface.executable_expression = executableExpression;
  if (argv.some(value => value === null)) { iface.status = 'unresolved'; iface.argv_expressions = expressions; }
  return iface;
}

// A finite shell token grammar preserves transport spelling, without expansion.
function shellTokens(text) {
  const result = []; let value = '', quote = '', start = 0, depth=0;
  const push = end => { if (value) result.push({ value, start, end, operator:false }); value = ''; };
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quote) { if (char === quote) quote = ''; else if (char === '\\' && quote === '"' && ['"', '\\'].includes(text[i + 1])) value += text[++i]; else value += char; continue; }
    if (char === '"' || char === "'") { if (!value) start = i; quote = char; continue; }
    if (/\s/.test(char)) { push(i); continue; }
    const placeholder = char === '<' && /^<[^<>\s]+>/.exec(text.slice(i));
    if (placeholder) { if (!value) start = i; value += placeholder[0]; i += placeholder[0].length - 1; continue; }
    if(char==='(')depth++;else if(char===')')depth=Math.max(0,depth-1);
    if (depth===0&&('<>|;'.includes(char) || text.startsWith('&&', i) || text.startsWith('||', i))) {
      push(i); const operator = text.startsWith('<<-', i) ? '<<-' : text.startsWith('&&', i) || text.startsWith('||', i) || text.startsWith('>>', i) || text.startsWith('<<', i) ? text.slice(i, i + 2) : char;
      result.push({ value: operator, start: i, end: i + operator.length, operator:true }); i += operator.length - 1; continue;
    }
    if (!value) start = i; value += char;
  }
  push(text.length); return { tokens: result, balanced: !quote };
}

function localTarget(resource, target, resources) {
  const clean = normalize(target);
  const skillRoot = /^\$\{CLAUDE_SKILL_DIR\}\/(.+)$/.exec(clean);
  if (skillRoot) return normalize(posix.join(posix.dirname(authoringSourcePath(resources)),skillRoot[1]));
  if (/^(?:[a-z]+:|\/)|(?:\$|<|>|\{|\})/i.test(clean)) return null;
  const candidates = [clean, normalize(posix.join(posix.dirname(resource), clean)), normalize(`source/${clean}`)];
  let root = posix.dirname(resource);
  while (root !== '.' && root !== '/') { if (resources[`${root}/package.json`]) candidates.push(normalize(`${root}/${clean}`)); root = posix.dirname(root); }
  return candidates.find(item => Object.hasOwn(resources, item)) ?? candidates.find(item => item.startsWith('source/')) ?? clean;
}

function commandInterface(text, resource, resources, explicitExecutable = false) {
  const parsed = shellTokens(text); const tokens = parsed.tokens;
  while (['$', '>', '&', 'sudo', 'command', 'call'].includes(tokens[0]?.value)) tokens.shift();
  if (!tokens.length) return null;
  const executable = tokens[0].value;
  const direct = program.test(executable), interpreter = interpreters.test(executableName(executable));
  // Command-position parsing requires a recognizable executable or local script.
  if (!direct && !interpreter && !/^(?:ffmpeg|ffprobe|git|java|codegraph|npm|npx|uv|pip|pip3)$/i.test(executableName(executable)) && !(explicitExecutable && tokens.length > 1 && /^[\w./\\:-]+$/.test(executable))) return null;
  const argv = [], files = []; let stdin, shell_tail;
  for (let i = 1; i < tokens.length; i++) {
    const token = tokens[i].value;
    if (tokens[i].operator&&['<', '>', '>>', '<<', '<<-'].includes(token)) {
      const path = tokens[++i]?.value;
      if (token === '<') stdin = { kind: 'file', path: path ?? null }; else if (token.startsWith('<<')) stdin = {kind:'heredoc',delimiter:path ?? null,...(token==='<<-' ? {strip_tabs:true} : {})}; else files.push({ direction: token === '>>' ? 'append' : 'write', path: path ?? null });
      continue;
    }
    if (tokens[i].operator&&['|', ';', '&&', '||'].includes(token)) { shell_tail = text.slice(tokens[i].start); break; }
    argv.push(token);
  }
  const entrypoint = direct ? executable : interpreter ? argv.find(value => program.test(value)) ?? null : null;
  const dynamic = !parsed.balanced || !!shell_tail || /\$\(|`/.test(text) || tokens.at(-1)?.operator&&['<','>','>>','<<','<<-'].includes(tokens.at(-1)?.value) || (interpreter && !entrypoint && !argv.includes('-m') && !argv.includes('-c') && !argv.includes('-e'));
  return { executable, entrypoint, argv, ...(stdin ? { stdin } : {}), ...(shell_tail ? {shell_tail} : {}), files, status: dynamic ? 'unresolved' : 'literal', ...(entrypoint ? { target_resource: localTarget(resource, entrypoint, resources) } : {}) };
}

function declaredCommandAliases(resource,bytes,resources) {
  const text=bytes.toString('utf8'), aliases=new Map();
  const pattern=/(?:下文的\s*|(?:below|following)\s+[`]?)(?:`([^`\s]+)`)(?:\s*都指\s*|\s+(?:means|refers to|stands for)\s*)[：:]\s*\r?\n\s*(`{3,}|~{3,})(?:bash|sh|shell|console)?\s*\r?\n([^\r\n]+)/gi;
  for(const match of text.matchAll(pattern)) {
    const iface=commandInterface(match[3].trim(),resource,resources);
    if(!iface?.target_resource)continue;
    const start=match.index+match[0].lastIndexOf(match[3]);
    aliases.set(match[1],{interface:iface,declaration:evidence(resource,bytes,start,start+match[3].length)});
  }
  return aliases;
}

function toolInterface(tool,command,resource,bytes,begin){
  const result={tool,...(tool.startsWith('mcp__')?{mcp_server:tool.split('__')[1]}:{})};
  const open=command.indexOf('(',tool.length);
  if(open<0)return result;
  const end=callEnd(codeMask(command),open), expression=command.slice(open+1,end?end-1:command.length);
  const argumentEvidence=evidence(resource,bytes,begin+open+1,begin+(end?end-1:command.length));
  result.arguments_expression=expression;
  result.arguments_source_span=argumentEvidence.source_span;
  result.arguments_source_location=argumentEvidence.source_location;
  if(!end||command.slice(end).trim()){result.arguments_transport='opaque_expression';result.status='unresolved';return result;}
  if(!expression.trim()){result.arguments_transport='empty';return result;}
  try{result.arguments=JSON.parse(expression);result.arguments_transport='literal_json';}
  catch{result.arguments_transport='opaque_expression';result.status='unresolved';}
  return result;
}

function markdownCalls(resource, bytes, resources, primary, sections) {
  const text = bytes.toString('utf8'), calls = [], aliases=declaredCommandAliases(resource,bytes,resources);
  const frontmatter=text.startsWith('---\n')||text.startsWith('---\r\n') ? /^---\r?\n[\s\S]*?\r?\n---(?:\r?\n|$)/.exec(text)?.[0].length ?? 0 : 0;
  let cursor = 0, title = '', fence = null, fenceContext = '', previous = '', conditionalScope = '', sectionTrigger='', heredocUntil=0;
  for (const line of text.split('\n')) {
    if(cursor<frontmatter||cursor<heredocUntil){cursor+=line.length+1;continue;}
    const heading = !fence && /^#{1,6}\s+(.+)/.exec(line); if (heading) { title = heading[1]; conditionalScope = ''; sectionTrigger=''; }
    const fenceMark = /^\s*(```+|~~~+)(.*)/.exec(line);
    if (fenceMark && (!fence || fenceMark[1][0]===fence.char && fenceMark[1].length>=fence.length && !fenceMark[2].trim())) { if (fence) fence = null; else { fence = { char: fenceMark[1][0], length:fenceMark[1].length, lang: fenceMark[2].trim() }; fenceContext = previous; } cursor += line.length + 1; continue; }
    if (!line.trim()) conditionalScope = '';
    if (/\b(?:if|when|unless|optional|only\s+if)\b.*:\s*$/i.test(line)) conditionalScope = line.trim();
    if(!fence&&/^\s*(?:only\b.{0,120}\b(?:when|if)\b|use\b[^`]{0,100}\bonly\b.{0,100}\b(?:when|if)\b|只在.{0,100}时(?:使用|运行|执行))/i.test(line))sectionTrigger=line.trim();
    const context = [title, sectionTrigger, fence ? fenceContext : '', conditionalScope, line].join(' ');
    const example = /\b(?:examples?|sample|illustration|demo)\b|示例/i.test(title) || /\bfor example\b|\be\.g\.|\bexample\s*:/i.test(context);
    const conditional = /\b(?:if|when|unless|optional(?:ly)?|only\s+(?:if|when))\b|如果|仅当|用户.{0,20}时|只在.{0,60}时/i.test(context);
    const prohibited = /\b(?:never|do\s+not|don't|must\s+not)\b|禁止|不得/i.test([fence ? fenceContext : '',line].join(' '));
    const section = sections.find(item => item.source_span.start_line <= text.slice(0, cursor).split('\n').length && item.source_span.end_line >= text.slice(0, cursor).split('\n').length);
    const directive = /\b(?:run|execute|invoke|call|use|must|shall)\b|运行|执行|调用|必须/i.test(context);
    let authority = example ? 'example' : !primary || prohibited ? 'source_observation' : conditional ? 'conditional' : directive || section?.authority === 'required' ? 'required' : 'source_observation';
    const ranges = fence ? [{ start: line.search(/\S/), text: line.trim() }] : [...line.matchAll(/`([^`]+)`/g)].map(match => ({ start: match.index + 1, text: match[1] }));
    if (!fence && !ranges.length && /^\s*(?:python\d*|node|bash|sh|pwsh)\s+/.test(line)) ranges.push({ start: line.search(/\S/), text: line.trim() });
    for (const range of ranges) {
      if (range.start < 0) continue;
      const tokens = shellTokens(range.text).tokens;
      let segments = [], start = 0, before=null;
      for (const token of tokens) if (token.operator&&[';', '&&', '||', '|'].includes(token.value)) { segments.push({start, end:token.start,connector_before:before,connector_after:token.value}); start = token.end; before=token.value; }
      segments.push({start, end:range.text.length,connector_before:before,connector_after:null});
      const compositeEvidence=segments.length>1?evidence(resource,bytes,cursor+range.start,cursor+range.start+range.text.length):null;
      const compositeId=compositeEvidence?`composite_${digest(canonicalJSON({resource,sha256:compositeEvidence.resource_sha256,location:compositeEvidence.source_location})).slice(0,24)}`:null;
      const rangeCalls=[];let guards=[];
      for (const [segmentIndex,segment] of segments.entries()) {
        if(segment.connector_before===';')guards=[];
        if(['&&','||'].includes(segment.connector_before))guards.push({segment_index:segmentIndex,connector:segment.connector_before});
        const raw = range.text.slice(segment.start, segment.end), left = raw.length - raw.trimStart().length, command = raw.trim();
        const prefix=line.slice(0,range.start-1), suffix=line.slice(range.start+range.text.length+1);
        const adjacentDirective=/\b(?:run|execute|invoke|call|use)\s*$|(?:运行|执行|调用|换算成)\s*$/i.test(prefix);
        const alias=aliases.get(tokens.find(token=>token.start>=segment.start)?.value);
        let iface = commandInterface(command, resource, resources, adjacentDirective||!!alias);
        if(alias&&iface){iface={...structuredClone(alias.interface),argv:[...alias.interface.argv,...iface.argv],files:iface.files,...(iface.stdin?{stdin:iface.stdin}:{}),original_executable:iface.executable,alias_declaration:alias.declaration};}
        const tool = /^(mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_-]+|(?:tools|functions|web|image_gen)\.[A-Za-z_][\w.]*)(?:\s*\(|$)/.exec(command)?.[1]
          ?? (/\b(?:call|invoke)\s*$|调用\s*$/i.test(prefix) && !iface && /^[A-Za-z_]\w*$/.test(command) ? command : null);
        if (!iface && !tool) continue;
        const begin = cursor + range.start + segment.start + left;
        const shellFence = fence && /^(?:sh|shell|bash|powershell|pwsh|cmd|bat|console|terminal)?$/i.test(fence.lang);
        const declaration=[...aliases.values()].some(item=>item.declaration.source_location.start_byte===Buffer.byteLength(text.slice(0,begin)));
        const usage=/完整(?:用法|语法|说明)|组件(?:语法|列表)|\b(?:usage|syntax)\b/i.test(prefix);
        const descriptive=/^\s*(?:安装的|会|用于|means\b|refers\b|is\b)/i.test(suffix);
        const invocation = !declaration&&!descriptive&&(adjacentDirective || shellFence || usage || iface?.argv.length > 0&&!alias&&!program.test(iface.executable) || tool && command.slice(tool.length).trimStart().startsWith('('));
        if(invocation&&primary&&!example&&!prohibited&&!conditional)authority='required';
        if(iface?.stdin?.kind==='heredoc'){
          const bodyStart=cursor+line.length+1, rest=text.slice(bodyStart), escaped=(iface.stdin.delimiter??'').replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
          const delimiter=iface.stdin.delimiter&&new RegExp(`^(?:${iface.stdin.strip_tabs?'\\t*':''})${escaped}\\r?$`,'m').exec(rest);
          if(delimiter){const end=bodyStart+delimiter.index;iface.stdin.body=text.slice(bodyStart,end);const bodyEvidence=evidence(resource,bytes,bodyStart,end);iface.stdin.source_span=bodyEvidence.source_span;iface.stdin.source_location=bodyEvidence.source_location;heredocUntil=end+delimiter[0].length+1;}
          else iface.status='unresolved';
        }
        const originalInterface=tool?toolInterface(tool,command,resource,bytes,begin):iface;
        if(compositeId)originalInterface.composite_transport={...compositeEvidence,composite_id:compositeId,segment_index:segmentIndex,segment_count:segments.length,connector_before:segment.connector_before,connector_after:segment.connector_after,guards:structuredClone(guards),transport_status:'authoring_only',address_binding:'host_required'};
        const guarded=guards.length>0;
        const call={ ...evidence(resource, bytes, begin, begin + command.length), kind: tool ? 'tool' : iface.entrypoint ? 'local_script' : 'cli', origin: 'markdown', classification: example || prohibited || !invocation ? 'candidate' : 'exact_call', authority:guarded&&['required','conditional'].includes(authority)?'conditional':authority, trigger: guarded?`shell guard ${guards.map(item=>item.connector).join(' ')} in ${range.text}`:conditional ? context.trim().slice(0, 500) : 'source_call', interface: originalInterface, ...(iface?.target_resource ? { target_resource: iface.target_resource } : {}) };
        calls.push(call);rangeCalls.push(call);
      }
      if(compositeId){
        const observed=new Set(rangeCalls.map(call=>call.interface.composite_transport.segment_index));
        const unrecognized=segments.flatMap((segment,index)=>observed.has(index)?[]:[{segment_index:index,...evidence(resource,bytes,cursor+range.start+segment.start,cursor+range.start+segment.end)}]);
        for(const call of rangeCalls)call.interface.composite_transport.unrecognized_segments=unrecognized;
      }
    }
    if (line.trim()) previous = line; cursor += line.length + 1;
  }
  return calls;
}

function processCalls(resource, bytes, resources) {
  const text = bytes.toString('utf8'), python = /\.py$/i.test(resource), mask = codeMask(text, python), calls = [];
  const bindings = new Map(); const namespaces = new Set();
  if (python) {
    for (const match of text.matchAll(/\bimport\s+subprocess(?:\s+as\s+(\w+))?/g)) if (mask.slice(match.index, match.index + 6).trim()) namespaces.add(match[1] ?? 'subprocess');
    for (const match of text.matchAll(/\bfrom\s+subprocess\s+import\s+([^\n]+)/g)) if (mask.slice(match.index, match.index + 4).trim()) for (const binding of match[1].split(',')) { const parts = binding.trim().split(/\s+as\s+/); if (/^(run|call|Popen|check_call|check_output)$/.test(parts[0])) bindings.set(parts[1] ?? parts[0],parts[0]); }
  } else {
    for (const match of text.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"](?:node:)?child_process['"]/g)) if (mask.slice(match.index, match.index + 6).trim()) for (const binding of match[1].split(',')) { const parts = binding.trim().split(/\s+as\s+/); if (processNames.has(parts[0])) bindings.set(parts[1] ?? parts[0],parts[0]); }
    for (const match of text.matchAll(/(?:import\s+(?:\*\s+as\s+)?([\w$]+)\s+from\s*|(?:const|let|var)\s+([\w$]+)\s*=\s*require\(\s*)['"](?:node:)?child_process['"]/g)) if (mask.slice(match.index, match.index + 3).trim()) namespaces.add(match[1] ?? match[2]);
    for (const match of text.matchAll(/(?:const|let|var)\s*\{([^}]+)\}\s*=\s*require\(\s*['"](?:node:)?child_process['"]\s*\)/g)) if (mask.slice(match.index, match.index + 3).trim()) for (const binding of match[1].split(',')) { const parts = binding.trim().split(/\s*:\s*/); if (processNames.has(parts[0])) bindings.set(parts[1] ?? parts[0],parts[0]); }
  }
  for (const match of mask.matchAll(/\b([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)?)\s*\(/g)) {
    const name = match[1], [namespace, member] = name.split('.');
    if (!bindings.has(name) && !(namespaces.has(namespace) && (python ? /^(run|call|Popen|check_call|check_output)$/.test(member) : processNames.has(member)))) continue;
    const open = match.index + match[0].lastIndexOf('('), end = callEnd(mask, open); if (!end) continue;
    const args = splitArguments(text.slice(open + 1, end - 1)); let iface = null;
    if (python) {
      if (/^\[[\s\S]*\]$/.test(args[0] ?? '')) { const parts = splitArguments(args[0].slice(1,-1)); iface = processInterface(parts[0],`[${parts.slice(1).join(', ')}]`,resource,resources,true); }
      else { const command = literalString(args[0]); if (command !== null) iface = commandInterface(command, resource, resources, true); }
    } else {
      const executable = literalString(args[0]);
      if (executable !== null && (/^exec(?:Sync)?$/.test(bindings.get(name) ?? member ?? name))) iface = commandInterface(executable, resource, resources, true);
      else iface = processInterface(args[0], args[1], resource, resources, false);
    }
    if (iface) {
      const options = python ? args.slice(1).join(', ') : args.slice(2).join(', ');
      const input = new RegExp(`\\binput\\s*${python ? '=' : ':'}\\s*((?:"(?:\\\\.|[^"\\\\])*"|'(?:\\\\.|[^'\\\\])*')|[^,}]+)`).exec(options)?.[1]?.trim();
      if (input) { const value = literalString(input); iface.stdin = value === null ? {kind:'expression',expression:input} : {kind:'literal',value}; if (value === null) iface.status = 'unresolved'; }
      const stdin = python && /\bstdin\s*=\s*open\(\s*(["'])([^"']+)\1/.exec(options);
      if (stdin) iface.stdin = {kind:'file',path:stdin[2]};
    }
    calls.push({ ...evidence(resource, bytes, match.index, end), kind: iface?.entrypoint ? 'local_script' : 'process', origin: 'process_call', classification: 'exact_call', authority: 'source_observation', trigger: 'local_program_execution', interface: iface ?? { status: 'unresolved', expression: args.join(', ') }, ...(iface?.target_resource ? { target_resource: iface.target_resource } : {}) });
  }
  return calls;
}

function importObservations(resource, bytes, resources) {
  const text = bytes.toString('utf8'), python = /\.py$/i.test(resource), mask = codeMask(text, python), result = [];
  const add = (match, specifier, target, kind = 'import') => result.push({ ...evidence(resource, bytes, match.index, match.index + match[0].length), kind, specifier, ...(target ? { target_resource: target, present: Object.hasOwn(resources, target) } : {}) });
  if (!python) {
    const seen = new Set();
    for (const match of text.matchAll(/\b(?:import\s+(?:[^;\n]*?\s+from\s*)?|export\s+[^;\n]*?\s+from\s*|require\(\s*|import\(\s*)['"]([^'"]+)['"]/g)) {
      if (!mask.slice(match.index, match.index + 6).trim()) continue;
      seen.add(match.index); const name = match[1];
      const base = name.startsWith('.') ? normalize(posix.join(posix.dirname(resource), name)) : null;
      const target = base ? [base, `${base}.mjs`, `${base}.js`, `${base}.cjs`, `${base}/index.mjs`, `${base}/index.js`].find(path => resources[path]) ?? base : null;
      add(match, name, target, name.startsWith('node:') || jsBuiltins.has(name) ? 'builtin' : target ? 'local_import' : 'package_import');
    }
    for (const match of mask.matchAll(/\b(?:import|require)\s*\(/g)) if (!seen.has(match.index)) { const end = callEnd(mask, match.index + match[0].lastIndexOf('(')); if (end) add({index:match.index,0:text.slice(match.index,end)}, null, null, 'dynamic_import'); }
  } else {
    for (const match of mask.matchAll(/^\s*(?:from\s+([.\w]+)\s+import\s+([\w*, ]+)|import\s+([\w., ]+))/gm)) {
      const from = match[1], names = from ? [from] : match[3].split(',').map(value => value.trim().split(/\s+as\s+/)[0]);
      for (const name of names) {
        if (!name) continue;
        let bases = [];
        if (name.startsWith('.')) {
          const dots = /^\.+/.exec(name)[0].length; let base = posix.dirname(resource); for (let i = 1; i < dots; i++) base = posix.dirname(base);
          const tail = name.slice(dots).replaceAll('.', '/');
          if (tail) bases.push(normalize(`${base}/${tail}`));
          else for (const binding of match[2].split(',')) bases.push(normalize(`${base}/${binding.trim().split(/\s+as\s+/)[0]}`));
        } else bases = [normalize(`source/${name.replaceAll('.', '/')}`), normalize(`${posix.dirname(resource)}/${name.replaceAll('.', '/')}`)];
        const target = bases.flatMap(base => [`${base}.py`, `${base}/__init__.py`]).find(path => resources[path]) ?? (name.startsWith('.') ? `${bases[0]}.py` : null);
        // Masked matches retain exact original source rather than blank aliases.
        add({ index:match.index, 0:text.slice(match.index, match.index + match[0].length) }, name, target, target ? 'local_import' : pythonStdlib.has(name.split('.')[0]) ? 'builtin' : 'package_import');
      }
    }
  }
  return result;
}

function packageFor(observation, resources) {
  const python = /\.py$/i.test(observation.resource), name = python ? observation.specifier.split('.')[0] : observation.specifier.startsWith('@') ? observation.specifier.split('/').slice(0, 2).join('/') : observation.specifier.split('/')[0];
  if (!python) {
    let root = posix.dirname(observation.resource);
    while (root !== '.' && root !== '/') {
      const resource = `${root}/package.json`;
      if (resources[resource]) {
        let metadata; try { metadata = JSON.parse(resources[resource].toString('utf8')); } catch { return { kind: 'npm', name, status: 'invalid_metadata', resource, resource_sha256: digest(resources[resource]) }; }
        const version = metadata.dependencies?.[name] ?? metadata.optionalDependencies?.[name] ?? metadata.peerDependencies?.[name] ?? metadata.devDependencies?.[name];
        return { kind: 'npm', name, status: version ? 'declared' : 'observed', ...(version ? { version } : {}), resource, resource_sha256: digest(resources[resource]) };
      }
      root = posix.dirname(root);
    }
  } else {
    for (const resource of Object.keys(resources).sort().filter(path => /(?:^|\/)(?:requirements[^/]*\.txt|pyproject\.toml)$/i.test(path))) {
      const text = resources[resource].toString('utf8');
      const pattern = new RegExp(`(?:^|[\\s"'])(${name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})([\\[\\]A-Za-z0-9_.<>=!~,*+-]*)`, 'im'), match = pattern.exec(text);
      if (match) return { kind: 'python', name, status: 'declared', version: match[2], ...evidence(resource, resources[resource], match.index, match.index + match[0].length) };
    }
  }
  return { kind: python ? 'python' : 'npm', name, status: 'observed' };
}

/** Finite, deterministic observations over pinned bytes; no filesystem, network or source execution. */
export function callableInventory(resources) {
  const primary = authoringSourcePath(resources), sections = sourceSectionInventory(resources), contracts = sourceContractIndex(resources).contracts;
  const callsites = [], imports = [], packages = [], unresolved = [];
  for (const resource of Object.keys(resources).sort()) {
    const bytes = Buffer.from(resources[resource]);
    if (/\.(?:md|markdown)$/i.test(resource)) callsites.push(...markdownCalls(resource, bytes, resources, resource === primary, resource === primary ? sections : []));
    if (/\.(?:py|[cm]?js)$/i.test(resource)) { callsites.push(...processCalls(resource, bytes, resources)); imports.push(...importObservations(resource, bytes, resources)); }
    if (/(?:^|\/)package\.json$/i.test(resource)) {
      let metadata; try { metadata = JSON.parse(bytes.toString('utf8')); } catch { continue; }
      for (const [name, command] of Object.entries(metadata.scripts ?? {})) if (typeof command === 'string') {
        const iface = commandInterface(command, resource, resources); if (!iface) continue;
        const quoted = JSON.stringify(command), start = bytes.toString('utf8').indexOf(quoted);
        callsites.push({ ...evidence(resource, bytes, start, start + quoted.length), kind: 'package_script', origin: 'package_script', classification: 'candidate', authority: 'source_observation', trigger: `package_script:${name}`, interface: iface, ...(iface.target_resource ? {target_resource:iface.target_resource} : {}) });
      }
    }
  }
  for (const call of callsites) {
    call.callsite_id = `callable_${digest(canonicalJSON({resource:call.resource,sha256:call.resource_sha256,location:call.source_location,kind:call.kind})).slice(0, 24)}`;
    call.source_contract_ids = contracts.filter(item => item.resource === call.target_resource && item.authority === 'interface').map(item => item.contract_id);
    call.resolved_resource_refs = []; call.runtime_dependencies = []; call.reached_by_callsite_ids = [];
  }
  const composites=new Map();
  for(const call of callsites){
    const transport=call.interface.composite_transport;if(!transport)continue;
    const members=composites.get(transport.composite_id)??new Map();members.set(transport.segment_index,call);composites.set(transport.composite_id,members);
  }
  for(const call of callsites){
    const transport=call.interface.composite_transport;if(!transport)continue;
    const members=composites.get(transport.composite_id),previous=members.get(transport.segment_index-1),next=members.get(transport.segment_index+1);
    transport.previous_callsite_id=previous?.callsite_id??null;
    transport.next_callsite_id=next?.callsite_id??null;
    transport.member_callsite_ids=Array.from({length:transport.segment_count},(_,index)=>members.get(index)?.callsite_id??null);
    transport.binding_status=transport.unrecognized_segments.length?'unresolved_segments':'recognized_segments';
    for(const guard of transport.guards)guard.preceding_callsite_id=members.get(guard.segment_index-1)?.callsite_id??null;
    if(transport.connector_before==='|'){
      const pipe={kind:'pipeline',source_callsite_id:previous?.callsite_id??null,composite_id:transport.composite_id};
      if(call.interface.stdin){transport.pipe_input=pipe;transport.binding_status='stdin_conflict';}
      else call.interface.stdin=pipe;
    }
  }
  for (const item of imports) { item.import_id = `import_${digest(canonicalJSON({resource:item.resource,sha256:item.resource_sha256,location:item.source_location,specifier:item.specifier})).slice(0,24)}`; item.reached_by_callsite_ids = []; }
  const roots = callsites.filter(call => call.resource === primary && call.classification === 'exact_call' && ['required', 'conditional'].includes(call.authority));
  for (const root of roots) {
    const queue = root.target_resource ? [root.target_resource] : [], visited = new Set();
    root.actionable = true;
    const runtime = [], problem = (code, item, extra = {}) => unresolved.push({ code, callsite_id:root.callsite_id, resource:item.resource, resource_sha256:item.resource_sha256, source_quote:item.source_quote, source_span:item.source_span, source_location:item.source_location, ...(item.target_resource ? {target_resource:item.target_resource} : {}), ...extra });
    if (root.interface.executable) runtime.push({kind:'executable',name:root.interface.executable});
    if (root.interface.tool) runtime.push({kind:'tool',name:root.interface.tool});
    if (root.interface.mcp_server) runtime.push({kind:'mcp_server',name:root.interface.mcp_server});
    if (root.interface.status === 'unresolved') problem(root.interface.tool?'UNRESOLVED_TOOL_ARGUMENTS':root.interface.shell_tail ? 'COMPOSITE_SHELL_COMMAND' : 'DYNAMIC_COMMAND', root);
    const composite=root.interface.composite_transport;
    if(composite?.unrecognized_segments.length)problem('UNRESOLVED_COMPOSITE_SEGMENT',root,{composite_id:composite.composite_id,segments:composite.unrecognized_segments});
    if(composite?.binding_status==='stdin_conflict')problem('UNRESOLVED_PIPELINE_STDIN',root,{composite_id:composite.composite_id});
    if (/^npm$/i.test(executableName(root.interface.executable ?? '')) && root.interface.argv[0] === 'run') {
      const selected = callsites.find(call => call.origin === 'package_script' && call.resource === 'source/package.json' && call.trigger === `package_script:${root.interface.argv[1]}`);
      if (!selected) problem('UNRESOLVED_PACKAGE_SCRIPT',root);
      else {
        selected.reached_by_callsite_ids.push(root.callsite_id); root.resolved_resource_refs.push(selected.resource);
        if (selected.target_resource) queue.push(selected.target_resource);
        if (selected.interface.executable) runtime.push({kind:'executable',name:selected.interface.executable});
        if (selected.interface.status === 'unresolved') problem(selected.interface.shell_tail ? 'COMPOSITE_SHELL_COMMAND' : 'DYNAMIC_COMMAND', selected);
      }
    }
    while (queue.length) {
      const resource = queue.shift(); if (visited.has(resource)) continue; visited.add(resource);
      if (!resources[resource]) { problem('MISSING_LOCAL_CALLABLE', root, { target_resource:resource }); runtime.push({kind:'local_callable',resource,status:'missing'}); continue; }
      root.resolved_resource_refs.push(resource);
      if (program.test(resource) && !/\.(?:py|[cm]?js)$/i.test(resource)) { problem('PROGRAM_BODY_NOT_INDEXED',root,{target_resource:resource}); runtime.push({kind:'local_dependencies',resource,status:'unindexed'}); }
      for (const call of callsites.filter(item => item.resource === resource && item.origin === 'process_call')) {
        call.reached_by_callsite_ids.push(root.callsite_id);
        if (call.interface.status === 'unresolved') problem(call.interface.shell_tail ? 'COMPOSITE_SHELL_COMMAND' : 'DYNAMIC_PROCESS_CALL', call);
        if (call.interface.executable) runtime.push({kind:'executable',name:call.interface.executable});
        if (call.target_resource) queue.push(call.target_resource);
      }
      for (const item of imports.filter(item => item.resource === resource)) {
        item.reached_by_callsite_ids.push(root.callsite_id);
        if (item.kind === 'dynamic_import') problem('DYNAMIC_IMPORT', item);
        else if (item.target_resource) {
          if (item.present) queue.push(item.target_resource); else { problem('MISSING_LOCAL_IMPORT', item); runtime.push({kind:'local_import',resource:item.target_resource,status:'missing'}); }
        } else if (item.kind === 'package_import') {
          const dependency = packageFor(item, resources); const key = `${dependency.kind}:${dependency.name}:${dependency.resource ?? ''}`;
          let record = packages.find(candidate => candidate.package_id === key);
          if (!record) { record = { ...dependency, package_id:key, source_spans:[], reached_by_callsite_ids:[] }; packages.push(record); }
          record.source_spans.push(item.source_span); record.reached_by_callsite_ids.push(root.callsite_id);
          runtime.push({kind:dependency.kind === 'python' ? 'python_package' : 'npm_package',name:dependency.name,...(dependency.version ? {version:dependency.version} : {}),status:dependency.status});
          if (dependency.resource) root.resolved_resource_refs.push(dependency.resource);
          if (dependency.status === 'invalid_metadata') problem('INVALID_PACKAGE_METADATA', item, { target_resource:dependency.resource });
        }
      }
    }
    root.resolved_resource_refs = sorted(root.resolved_resource_refs);
    root.runtime_dependencies = [...new Map(runtime.map(item => [canonicalJSON(item),item])).values()];
  }
  for (const call of callsites.filter(item => item.reached_by_callsite_ids.length)) {
    call.reached_by_callsite_ids = sorted(call.reached_by_callsite_ids);
    // A child retains its own callable root while the originating entrypoint owns the complete closure.
    call.resolved_resource_refs = call.target_resource && resources[call.target_resource] ? [call.target_resource] : [];
  }
  for (const item of imports) item.reached_by_callsite_ids = sorted(item.reached_by_callsite_ids);
  for (const call of callsites) call.actionable ??= false;
  for (const item of packages) { item.reached_by_callsite_ids = sorted(item.reached_by_callsite_ids); item.source_spans = [...new Map(item.source_spans.map(span => [canonicalJSON(span),span])).values()]; }
  return { contract:'workflow-callable-inventory/v1', primary_resource:primary, callsites:callsites.sort((a,b) => a.resource.localeCompare(b.resource) || a.source_location.start_byte-b.source_location.start_byte), imports, packages, unresolved, limitations:['Finite shell literals and recognized JS child_process/Python subprocess bindings only; aliases assigned later, reflection, templates, shell expansion and arbitrary language grammars are not resolved.', 'Import observations are lexical; reachability follows local imports and recognized process calls, not runtime branches. External package internals and Python distribution/module name equivalence are not inferred.', 'Tool argument expressions are parsed only as literal JSON. Composite shell evidence is authoring-only: runtime addresses, pipeline/guard topology and unsupported segments must be bound or explicitly rejected by the Host, never executed from the source-relative original string.'] };
}

/** Optional deterministic helper; exact original callsite IDs cannot borrow section coverage. */
export function callableCoverageIssues(inventory, proposal) {
  const issues = [], expected = inventory.callsites.filter(item => item.actionable);
  const nodes = new Map((proposal?.nodes ?? []).map(item => [item.id,item]));
  for (const call of expected) {
    const entries = (proposal?.requirement_mappings ?? []).filter(item => item.requirement_id === call.callsite_id);
    if (!entries.length) { issues.push({code:'CALLABLE_COVERAGE_MISSING',callsite_id:call.callsite_id,source_span:call.source_span}); continue; }
    const responsible = entries.flatMap(item => item.node_ids ?? []).map(id => nodes.get(id)).filter(Boolean);
    if (!responsible.length) issues.push({code:'CALLABLE_COVERAGE_NODE',callsite_id:call.callsite_id});
    for (const resource of call.resolved_resource_refs) if (!entries.some(item => item.resource_refs?.includes(resource)) || !responsible.some(node => node.resource_refs?.includes(resource))) issues.push({code:'CALLABLE_COVERAGE_TARGET',callsite_id:call.callsite_id,resource});
    if (call.interface.tool && !entries.some(mapping => mapping.status === 'agent_assisted' && responsible.some(node => node.type === 'agent' && node.requirement_ids?.includes(call.callsite_id))) && !responsible.some(node => [node.tool, node.tool?.name, node.tool_name].includes(call.interface.tool))) issues.push({code:'CALLABLE_COVERAGE_TARGET',callsite_id:call.callsite_id});
  }
  return issues;
}
