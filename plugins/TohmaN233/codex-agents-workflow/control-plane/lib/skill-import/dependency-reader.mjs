import { informationalImportObservation } from '../workflow-import-observations.mjs';
import { posix } from 'node:path';
import { normalizeImportedExecutableRequirements, readDependencyMetadata } from './metadata-reader.mjs';
import { digest } from '../workflow-revisions.mjs';

function syntheticPathAssertions(path,text,files,matches){
  if(!/(?:^|\/)tests?\/.*\.(?:test|spec)\.[cm]?js$/i.test(path)||!matches.length)return null;
  const dependencies=[];
  for(const match of matches){
    const line=text.slice(text.lastIndexOf('\n',match.index)+1,text.indexOf('\n',match.index)<0?undefined:text.indexOf('\n',match.index));
    const assertion=/^\s*assert\.match\(([A-Za-z_$][\w$]*)\((['"])(?:\\.|(?!\2)[^\\\r\n])*\2\),\s*\/[^\r\n]+\/\w*\);\s*$/.exec(line);
    if(!assertion)return null;
    const name=assertion[1];
    const imports=[...text.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]/g)].filter(item=>item[1].split(',').map(v=>v.trim()).includes(name));
    if(imports.length!==1||!imports[0][2].startsWith('.'))return null;
    const module=posix.normalize(posix.join(posix.dirname(path),imports[0][2]));
    if(!files[module])return null;
    const code=files[module].toString('utf8');
    const fn=new RegExp('export function '+name+'\\(([A-Za-z_$][\\w$]*)(?:\\s*=\\s*[\'\"][\'\"])?\\)\\s*\\{([\\s\\S]*?)^\\}','m').exec(code);
    if(!fn)return null;
    // Finite pure-function grammar: regex tests of the sole parameter and
    // literal returns. No filesystem reads, process calls or dynamic calls.
    const body=fn[2].replace(/'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"/g,'LITERAL')
      .replace(/\/(?:\\.|\[(?:\\.|[^\]\\])*\]|[^/\\\r\n])+\/[gimsuy]*/g,'REGEX');
    const condition='if\\s*\\(REGEX\\.test\\('+fn[1]+'\\)\\)\\s*\\{\\s*return LITERAL;\\s*\\}\\s*';
    if(!new RegExp('^\\s*(?:'+condition+')*return LITERAL;\\s*$').test(body))return null;
    dependencies.push(digest(files[module]));
  }
  return {version:1,kind:'pure_path_classifier_assertion',resource_sha256:digest(files[path]),dependency_sha256:[...new Set(dependencies)].sort()};
}

// Fenced Markdown is output/template syntax. Its links are artifact observations,
// not instructions to load resources from the Skill bundle. Ordinary prose links
// and explicit dependency declarations retain their original checks.
function markdownTemplateLines(text){
  const lines=new Set();let fence=null;
  for(const [index,line] of text.split('\n').entries()){
    const marker=/^ {0,3}(`{3,}|~{3,})([^\r\n]*)\r?$/.exec(line);
    if(fence){
      if(marker&&marker[1][0]===fence.character&&marker[1].length>=fence.length&&!marker[2].trim())fence=null;
      else if(fence.markdown)lines.add(index+1);
    }else if(marker)fence={character:marker[1][0],length:marker[1].length,markdown:/^(?:md|markdown)(?:\s|$)/i.test(marker[2].trim())};
  }
  return lines;
}

// Deliberately finite static observations. This never runs a script or claims
// to infer its behavior. Unresolved observations remain visible Draft blockers.
export function analyzeSkillDependencies(snapshot) {
  const unresolved = snapshot.problems.map(item => ({ ...item, origin: 'observed' }));
  const references = []; const requirements = { providers: [], tools: ['read_workflow_resource'], mcp_servers: [], executables: [], environment: [] };
  const observed_dependencies = [];
  const declared = readDependencyMetadata(snapshot); unresolved.push(...declared.unresolved);
  for (const [kind, names] of Object.entries(declared.requirements)) requirements[kind].push(...names);
  const observe = (kind, name, path, evidence) => {
    if (name) observed_dependencies.push({ kind, name, path, evidence });
  };
  const executableForPath = path => /\.py$/i.test(path) ? 'python' : /\.[mc]?js$/i.test(path) ? 'node' : /\.ps1$/i.test(path) ? 'powershell' : /\.sh$/i.test(path) ? 'sh' : /\.(?:cmd|bat)$/i.test(path) ? 'cmd' : null;
  for (const [path, bytes] of Object.entries(snapshot.files)) {
    if (/\/scripts\/|\.(?:py|mjs|cjs|js|sh|ps1|cmd|bat)$/i.test(path)) {
      unresolved.push({ code: 'SCRIPT_REQUIRES_REVIEW', path, origin: 'observed' });
      observe('executable', executableForPath(path), path, 'script_resource_present');
    }
    if (snapshot.inventory.some(item => 'source/' + item.path === path && item.binary)) {
      unresolved.push({ code: 'BINARY_RESOURCE_REQUIRES_CAPABILITY', path, origin: 'observed' }); continue;
    }
    const text = bytes.toString('utf8');
    // Shell substitutions can be local variables (for example ANSI colors), and
    // JavaScript template interpolation is not an environment read at all.
    for (const match of text.matchAll(/\b(?:process\.env\.([A-Z_][A-Z0-9_]*)|os\.environ\[["']([A-Z_][A-Z0-9_]*)["']\])/g)) observe('environment', match[1] ?? match[2], path, 'static_reference');
    if (/\.sh$/i.test(path)) {
      const locals = new Set([...text.matchAll(/(?:^|[;\n])\s*(?:export\s+|local\s+)?([A-Z_][A-Z0-9_]*)\s*=(["'])([^$`\n]*?)\2(?=\s|;|$)/g)].map(m => m[1]));
      for (const match of text.matchAll(/\$\{([A-Z_][A-Z0-9_]*)\}/g)) if (!locals.has(match[1])) observe('environment', match[1], path, 'static_reference');
    }
    const normalizedText=text.replaceAll('\\\\','/').replaceAll('\\','/').toLowerCase();
    const privateRoots=[snapshot.root,snapshot.source_path].filter(Boolean).map(value=>String(value).replaceAll('\\','/').toLowerCase());
    const privateRoot=privateRoots.some(root=>normalizedText.includes(root));
    const browserDefaults=/\b[a-z]:\/program files(?: \(x86\))?\/(?:google\/chrome\/application\/chrome|microsoft\/edge\/application\/msedge)\.exe\b/g;
    const browserDiscovery=[...normalizedText.matchAll(browserDefaults)].length>0;
    const unknownDrive=/\b[a-z]:\//.test(normalizedText.replace(browserDefaults,''));
    const homePaths=[...text.matchAll(/(?:^|[\s"'(])(?:[A-Za-z]:[\\/])?(?:[\\/]Users[\\/]|[\\/]home[\\/])/gm)];
    if (privateRoot||unknownDrive||homePaths.length) {
      const proof=privateRoot||unknownDrive?null:syntheticPathAssertions(path,text,snapshot.files,homePaths);
      unresolved.push({ code: 'SOURCE_LINKED_PATH', path, origin: 'observed',...(proof?{synthetic_evidence:proof}:{}) });
    }
    // OS executable discovery defaults are runtime observations, not links back
    // to the private authoring bundle. Actual private roots still block above.
    if (browserDiscovery||/(?:^|[\s"'(])\/(?:usr|opt|etc|Applications)\//m.test(text)) unresolved.push({code:'RUNTIME_PATH_REFERENCE',path,origin:'observed'});
    // Markdown syntax is only syntax in Markdown. Regexes, JSDoc and package
    // bin metadata in programs/data are not authoring instructions.
    const markdown=/\.(?:md|markdown)$/i.test(path);
    const templateLines=markdown?markdownTemplateLines(text):new Set();
    for (const match of markdown?text.matchAll(/\[[^\]\n]*\]\(([^)\n]+)\)/g):[]) {
      const target = match[1].replace(/^<|>$/g, '').split(/\s+["']/)[0];
      const line = text.slice(0, match.index).split('\n').length;
      if(templateLines.has(line)){references.push({path,target,line,kind:'artifact_template'});continue;}
      if (target.startsWith('#')) continue;
      if (/^[a-z][a-z0-9+.-]*:/i.test(target)) {
        references.push({ path, target, line, kind: 'external' });
        unresolved.push({ code: 'EXTERNAL_REFERENCE_REQUIRES_REVIEW', path, line, target, origin: 'observed' }); continue;
      }
      let local;
      try { local = decodeURIComponent(target.split('#')[0]); } catch { unresolved.push({ code: 'INVALID_REFERENCE', path, line, origin: 'observed' }); continue; }
      if (local.startsWith('/') || local.includes('\\')) { unresolved.push({ code: 'SOURCE_LINKED_PATH', path, line, target: local, origin: 'observed' }); continue; }
      const resolved = posix.normalize(posix.join(posix.dirname(path), local));
      const contained = resolved.startsWith('source/') && Object.hasOwn(snapshot.files, resolved);
      references.push({ path, target: local, resolved, line, kind: 'local', present: contained });
      if (!contained) unresolved.push({ code: 'UNRESOLVED_LOCAL_REFERENCE', path, line, target: local, origin: 'observed' });
    }
    // Recognize common inline command/code references without pretending to
    // parse an entire shell language. A missed dynamic path remains a review
    // concern; an explicit missing path must never look self-contained.
    let commands=markdown?text:'';
    if(/\.[cm]?js$/i.test(path)&&/['"](?:node:)?child_process['"]/.test(text)){
      // Finite literal process-call contexts. A banner, regex or ordinary
      // string naming a script is not a command; a literal spawn/exec is.
      const calls=new Set(['execFile','execFileSync','spawn','spawnSync','exec','execSync']);
      for(const entry of text.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"](?:node:)?child_process['"]/g))
        for(const binding of entry[1].split(',')){const alias=/^\s*(execFile(?:Sync)?|spawn(?:Sync)?|exec(?:Sync)?)\s+as\s+([A-Za-z_$][\w$]*)\s*$/.exec(binding);if(alias)calls.add(alias[2]);}
      const spans=[...text.matchAll(new RegExp('\\b(?:'+[...calls].map(name=>name.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')\\s*\\([^)]*\\)','g'))];
      let end=0;commands='';
      for(const match of spans){if(match.index<end)continue;commands+=text.slice(end,match.index).replace(/[^\n]/g,' ')+match[0];end=match.index+match[0].length;}
    }
    if(/(?:^|\/)package\.json$/i.test(path)){
      try{
        const metadata=JSON.parse(text);
        commands=Object.values(metadata.scripts??{}).filter(value=>typeof value==='string').join('\n');
      }catch{unresolved.push({code:'INVALID_PACKAGE_METADATA',path,origin:'observed'});}
    }
    for (const match of commands.matchAll(/(?:^|[\s`"'(])((?:\.\/)?(?:scripts|tools|bin)\/[A-Za-z0-9._/-]+\.(?:py|mjs|cjs|js|sh|ps1|cmd|bat))(?=$|[\s`"',);])/gmi)) {
      const target = match[1].replace(/^\.\//, '');
      const line = commands.slice(0, match.index).split('\n').length;
      let packageRoot=posix.dirname(path);
      while(packageRoot!=='source'&&!Object.hasOwn(snapshot.files,packageRoot+'/package.json'))packageRoot=posix.dirname(packageRoot);
      const packageResolved=posix.normalize(packageRoot+'/'+target);
      const rootResolved = posix.normalize('source/' + target);
      const relativeResolved = posix.normalize(posix.join(posix.dirname(path), target));
      const resolved = Object.hasOwn(snapshot.files, relativeResolved) ? relativeResolved
        : Object.hasOwn(snapshot.files,packageResolved) ? packageResolved
          : Object.hasOwn(snapshot.files, rootResolved) ? rootResolved : relativeResolved;
      const present = resolved.startsWith('source/') && Object.hasOwn(snapshot.files, resolved);
      if (!references.some(item => item.path === path && item.line === line && item.target === target)) references.push({ path, target, resolved, line, kind: 'command', present });
      observe('executable', executableForPath(target), path, 'inline_command_reference');
      if (!present) unresolved.push({ code: 'UNRESOLVED_COMMAND_REFERENCE', path, line, target, origin: 'observed' });
    }
  }
  for (const kind of Object.keys(requirements)) requirements[kind] = kind === 'executables'
    ? normalizeImportedExecutableRequirements(requirements[kind])
    : [...new Set(requirements[kind])].sort();
  const observations = observed_dependencies.filter((item, index, all) => all.findIndex(other => other.kind === item.kind && other.name === item.name && other.path === item.path && other.evidence === item.evidence) === index)
    .sort((a, b) => `${a.kind}\0${a.name}\0${a.path}\0${a.evidence}`.localeCompare(`${b.kind}\0${b.name}\0${b.path}\0${b.evidence}`));
  const hasRequiredExternal = requirements.executables.length || requirements.environment.length || requirements.mcp_servers.length || requirements.tools.some(tool => tool !== 'read_workflow_resource');
  const classification = unresolved.some(item => item.code === 'SOURCE_LINKED_PATH') ? 'source_linked'
    : (unresolved.length || hasRequiredExternal) ? 'external_requirements'
      : observations.length ? 'dependency_observations' : 'self_contained_candidate';
  return { requirements, observed_dependencies: observations, tool_policy: declared.tool_policy, references, declarations: declared.declarations, observations:unresolved.filter(informationalImportObservation), unresolved:unresolved.filter(i=>!informationalImportObservation(i)), classification };
}
