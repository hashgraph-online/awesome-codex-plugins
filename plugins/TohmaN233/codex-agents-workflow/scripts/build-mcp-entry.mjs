import {readFile,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {WORKFLOW_EXECUTION_MCP_SERVER,WORKFLOW_DIRECT_TOOLS,WORKFLOW_LONG_CALL_TOOLS,WORKFLOW_MCP_TRANSPORT_ENV} from '../control-plane/lib/workflow-call-policy.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');

// Git checkouts on Windows can present the source as CRLF. The generated
// argument is a canonical LF representation so the manifest compares by
// source semantics while still detecting meaningful code changes.
export const canonicalLf = source => source.replace(/\r\n?/g, '\n');
export const bootstrapSuffix = "\nboot().catch(error=>{console.error('WORKFLOW_MCP_BOOT_FAILED',error.stack||error);process.exitCode=1;});";
export const buildBootstrapSource = source => canonicalLf(source) + bootstrapSuffix;

export function buildMcpManifest(manifest,source) {
  const spec=manifest.mcpServers['codex-agents-workflow'];
  // The initial namespace identifies this marketplace. Bootstrap then moves
  // outside the whole replaceable cache entry before serving any requests.
  spec.cwd='..';
  spec.tool_timeout_sec=3660;
  spec.args=['-e',buildBootstrapSource(source)];
  spec.env_vars=[...new Set([...spec.env_vars,'CODEX_CLI_PATH'])];
  // Management retains its historical callable tools and code-mode contract.
  spec.disabled_tools=(spec.disabled_tools??[]).filter(name=>!WORKFLOW_LONG_CALL_TOOLS.includes(name));
  if(!spec.disabled_tools.length)delete spec.disabled_tools;
  spec.env={...spec.env,[WORKFLOW_MCP_TRANSPORT_ENV]:'code_mode'};
  const execution=structuredClone(spec);
  delete execution.disabled_tools;
  execution.env={...execution.env,[WORKFLOW_MCP_TRANSPORT_ENV]:'direct_mcp'};
  execution.enabled_tools=[...WORKFLOW_DIRECT_TOOLS];
  execution.omit_tools_from=['code_mode','deferred'];
  manifest.mcpServers[WORKFLOW_EXECUTION_MCP_SERVER]=execution;
  return manifest;
}

export async function buildMcpEntry() {
  const source=await readFile(resolve(root,'scripts/mcp-bootstrap.cjs'),'utf8');
  const manifestPath=resolve(root,'.mcp.json');
  const manifest=buildMcpManifest(JSON.parse(await readFile(manifestPath,'utf8')),source);
  await writeFile(manifestPath,JSON.stringify(manifest,null,2)+'\n');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await buildMcpEntry();
