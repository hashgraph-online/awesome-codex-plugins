import {canonicalJSON,digest} from '../workflow-revisions.mjs';
import {requireValue} from '../workflow-paths.mjs';

const commandNames=['run_workspace_program','run_workspace_command','continue_workspace_command'];
const MAX_DECLARATION_BYTES=32768;

// Declaration data for the Host-introduced process APIs. Transport and
// execution authority remain with the already qualified owned MCP broker.
export function ownedCommandDeclarations(namespace,tools) {
  requireValue(typeof namespace==='string'&&/^[A-Za-z_][A-Za-z0-9_]{0,63}$/.test(namespace),
    'CODEX_COMMAND_DECLARATIONS','Owned command namespace is invalid');
  requireValue(Array.isArray(tools)&&tools.length===commandNames.length&&tools.every((tool,index)=>
    tool?.name===commandNames[index]&&typeof tool.description==='string'&&tool.description.length>0
    &&tool.inputSchema?.type==='object'&&Object.keys(tool).length===3
    &&Object.keys(tool).every(key=>['name','description','inputSchema'].includes(key))),
    'CODEX_COMMAND_DECLARATIONS','Owned command declarations require the exact broker definitions');
  const text=canonicalJSON({owned_command_declarations:{namespace,
    tools:tools.map(tool=>({callable:`tools.mcp__${namespace}__${tool.name}`,...tool}))}});
  const bytes=Buffer.byteLength(text,'utf8');
  requireValue(bytes<=MAX_DECLARATION_BYTES,'CODEX_COMMAND_DECLARATIONS_LIMIT','Owned command declaration data exceeds its fixed byte bound');
  return {input:{type:'text',text},audit:{namespace,tool_count:commandNames.length,bytes,sha256:digest(text)}};
}
