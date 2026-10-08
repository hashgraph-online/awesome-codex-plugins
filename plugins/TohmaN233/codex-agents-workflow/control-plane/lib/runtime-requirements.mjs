import {createHash} from 'node:crypto';
import {requireValue} from './workflow-paths.mjs';

const namePattern=/^[a-zA-Z0-9][a-zA-Z0-9_.+-]{0,99}$/;
const modulePattern=/^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*$/;
export const isPythonRequirement=name=>/^(?:python(?:[23](?:\.\d+)?)?|pypy[23]?)(?:\.exe)?$/i.test(name);

function versionParts(value,name){
  requireValue(typeof value==='string'&&/^\d+(?:\.\d+){0,2}$/.test(value),'ENVIRONMENT_VERSION_UNSUPPORTED',`Unsupported version for ${name}: ${value}`,{dependency:name,reason:'Use one to three numeric version components.'});
  const parts=value.split('.').map(Number);
  requireValue(parts.every(Number.isSafeInteger),'ENVIRONMENT_VERSION_UNSUPPORTED',`Version components for ${name} must be safe integers`,{dependency:name});
  return [...parts,...Array(3-parts.length).fill(0)];
}
const compare=(a,b)=>{for(let i=0;i<3;i++)if(a[i]!==b[i])return a[i]<b[i]?-1:1;return 0;};

// Constraints are a conjunction of ==, >=, >, <= or < followed by numeric
// versions. Missing components are zero; ranges, OR, prereleases and ~= are not
// guessed. Normalization reduces intersections to one exact value or two bounds.
function normalizeVersion(value,name){
  if(value===undefined)return undefined;
  requireValue(typeof value==='string'&&value.length>0&&value.length<=256,'ENVIRONMENT_VERSION_UNSUPPORTED',`Unsupported version constraint for ${name}`,{dependency:name});
  let lower=null,upper=null,exact=null;
  for(const raw of value.split(',')){
    const match=raw.trim().match(/^(==|>=|>|<=|<)\s*(\d+(?:\.\d+){0,2})$/);
    requireValue(match,'ENVIRONMENT_VERSION_UNSUPPORTED',`Unsupported version constraint for ${name}: ${raw}`,{dependency:name,reason:'Use comma-separated comparisons, for example >=3.11,<4.'});
    const op=match[1],version=versionParts(match[2],name),bound={version,inclusive:op.endsWith('=')};
    if(op==='=='){
      requireValue(!exact||compare(exact,version)===0,'ENVIRONMENT_REQUIREMENT_CONFLICT',`Conflicting exact versions for ${name}`,{dependency:name});
      exact=version;
    }else if(op.startsWith('>')){
      if(!lower||compare(version,lower.version)>0||(compare(version,lower.version)===0&&!bound.inclusive))lower=bound;
    }else if(!upper||compare(version,upper.version)<0||(compare(version,upper.version)===0&&!bound.inclusive))upper=bound;
  }
  const accepts=version=>(!lower||compare(version,lower.version)>0||(lower.inclusive&&compare(version,lower.version)===0))&&(!upper||compare(version,upper.version)<0||(upper.inclusive&&compare(version,upper.version)===0));
  requireValue((!exact||accepts(exact))&&(!lower||!upper||compare(lower.version,upper.version)<0||(compare(lower.version,upper.version)===0&&lower.inclusive&&upper.inclusive)),'ENVIRONMENT_REQUIREMENT_CONFLICT',`Version constraints for ${name} have no intersection`,{dependency:name});
  if(exact)return '=='+exact.join('.');
  if(lower&&upper&&compare(lower.version,upper.version)===0)return '=='+lower.version.join('.');
  return [lower&&`${lower.inclusive?'>=':'>'}${lower.version.join('.')}`,upper&&`${upper.inclusive?'<=':'<'}${upper.version.join('.')}`].filter(Boolean).join(',');
}

export function normalizeExecutableRequirements(executables=[]){
  requireValue(Array.isArray(executables)&&executables.length<=256,'ENVIRONMENT_REQUIREMENTS','Executable requirements must be an array of at most 256 entries');
  const merged=new Map();
  for(const value of executables){
    const item=typeof value==='string'?{name:value}:value;
    requireValue(item&&typeof item==='object'&&!Array.isArray(item)&&typeof item.name==='string'&&namePattern.test(item.name),'ENVIRONMENT_DEPENDENCY_NAME','Executable dependencies must be logical program names, not commands or paths',{dependency:item?.name??value});
    const name=item.name;
    requireValue(Object.keys(item).every(key=>['name','version','python_modules'].includes(key)),'ENVIRONMENT_REQUIREMENTS',`Unsupported requirement fields for ${name}`,{dependency:name});
    const version=normalizeVersion(item.version,name);
    const modules=item.python_modules??[];
    requireValue(Array.isArray(modules)&&modules.length<=128&&modules.every(value=>typeof value==='string'&&value.length<=128&&modulePattern.test(value)),'ENVIRONMENT_PYTHON_MODULES',`Python modules for ${name} must be import names`,{dependency:name});
    requireValue(item.python_modules===undefined||isPythonRequirement(name),'ENVIRONMENT_PYTHON_MODULES',`python_modules is only supported for Python interpreters: ${name}`,{dependency:name});
    const previous=merged.get(name);
    const combined=previous?.version&&version?normalizeVersion(`${previous.version},${version}`,name):previous?.version??version;
    const allModules=[...new Set([...(previous?.python_modules??[]),...modules])].sort();
    merged.set(name,{name,...(combined?{version:combined}:{}),...(allModules.length?{python_modules:allModules}:{})});
  }
  return [...merged.values()].sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0);
}

export function normalizeRuntimeRequirements(requirements={}){
  requireValue(requirements&&typeof requirements==='object'&&!Array.isArray(requirements),'ENVIRONMENT_REQUIREMENTS','Runtime requirements must be an object');
  return {...requirements,executables:normalizeExecutableRequirements(requirements.executables??[])};
}

export function runtimeRequirementKey(requirement){
  const [normalized]=normalizeExecutableRequirements([requirement]);
  return `${normalized.name}:${createHash('sha256').update(JSON.stringify(normalized)).digest('hex')}`;
}

export function versionSatisfies(actual,constraint,name='executable'){
  const parts=versionParts(actual,name),normalized=normalizeVersion(constraint,name);
  if(!normalized)return true;
  return normalized.split(',').every(value=>{
    const [,op,target]=value.match(/^(==|>=|>|<=|<)(.+)$/),order=compare(parts,versionParts(target,name));
    return op==='=='?order===0:op==='>='?order>=0:op==='>'?order>0:op==='<='?order<=0:order<0;
  });
}
