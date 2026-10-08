const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const {pathToFileURL} = require('node:url');
const {execFile} = require('node:child_process');
const {promisify} = require('node:util');

function installationNamespace(directory) {
  const root=path.resolve(directory);
  if(path.basename(root)!=='codex-agents-workflow')throw Error('WORKFLOW_PLUGIN_NAMESPACE: cwd must be the launching plugin cache namespace');
  const marketplace=path.basename(path.dirname(root));
  if(!marketplace || marketplace.includes('@'))throw Error('WORKFLOW_PLUGIN_NAMESPACE: invalid marketplace namespace');
  return {root,marketplace,pluginId:'codex-agents-workflow@'+marketplace};
}

function registeredRoot(registry, namespace) {
  const identity=installationNamespace(namespace);
  if(!Array.isArray(registry?.installed))throw Error('WORKFLOW_PLUGIN_REGISTRY: missing installed-plugin inventory');
  const entries = registry.installed.filter(p => p.pluginId === identity.pluginId && p.installed);
  if(entries.length !== 1 || !entries[0].enabled || !/^[0-9][A-Za-z0-9.+_-]*$/.test(entries[0].version)) throw Error('WORKFLOW_PLUGIN_REGISTRY: expected one enabled installed version');
  return {...identity,version:entries[0].version,root:path.join(identity.root,entries[0].version)};
}

async function boot() {
  const home = process.env.CODEX_HOME || path.join(os.homedir(),'.codex');
  const auditRoot=path.join(home,'codex-agents-workflow');
  await fs.mkdir(auditRoot,{recursive:true});
  const audit=event=>fs.appendFile(path.join(auditRoot,'mcp-startup.jsonl'),JSON.stringify({at:new Date().toISOString(),pid:process.pid,...event})+'\n');
  const context={};
  try {
    const namespace=await fs.realpath(process.cwd());
    const identity=installationNamespace(namespace);
    Object.assign(context,{namespace,marketplace:identity.marketplace,pluginId:identity.pluginId});
    // Ask the installation registry on EVERY handshake. Never choose max(cache dirs)
    // or use the revision captured by a long-running host's plugin catalog.
    // The host resolves cwd=".." relative to this installed package. That
    // stable namespace identifies the source even when another marketplace
    // installs the same plugin, or a warm host remembers an obsolete version.
    const {stdout}=await promisify(execFile)(process.env.CODEX_CLI_PATH || 'codex',['plugin','list','--marketplace',identity.marketplace,'--json'],{windowsHide:true,timeout:10000,maxBuffer:1024*1024});
    const selected=registeredRoot(JSON.parse(stdout),namespace);
    const manifest=JSON.parse(await fs.readFile(path.join(selected.root,'.codex-plugin/plugin.json'),'utf8'));
    if(manifest.name!=='codex-agents-workflow'||manifest.version!==selected.version)throw Error('WORKFLOW_PLUGIN_IDENTITY: registered version does not match installed files');
    // Node resolves imported modules through filesystem aliases. Use that same
    // physical entry for argv so server.mjs recognizes itself as the main module.
    const entry=await fs.realpath(path.join(selected.root,'control-plane/server.mjs'));
    await audit({phase:'resolved',...context,version:selected.version,entry});
    // Keep the configured stable cwd. Holding a disposable plugin version as
    // cwd prevents the installer from replacing that directory on Windows.
    process.argv[1]=entry;
    await import(pathToFileURL(entry).href);
  } catch(error) {
    await audit({phase:'failed',...context,code:error.code??'WORKFLOW_MCP_BOOT_FAILED',message:error.message});
    throw error;
  }
}
module.exports={installationNamespace,registeredRoot,boot};
