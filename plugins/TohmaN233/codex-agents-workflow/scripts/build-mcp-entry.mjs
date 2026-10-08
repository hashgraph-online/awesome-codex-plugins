import {readFile,writeFile} from 'node:fs/promises';
import {dirname,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');

// Git checkouts on Windows can present the source as CRLF. The generated
// argument is a canonical LF representation so the manifest compares by
// source semantics while still detecting meaningful code changes.
export const canonicalLf = source => source.replace(/\r\n?/g, '\n');
export const bootstrapSuffix = "\nboot().catch(error=>{console.error('WORKFLOW_MCP_BOOT_FAILED',error.stack||error);process.exitCode=1;});";
export const buildBootstrapSource = source => canonicalLf(source) + bootstrapSuffix;

export async function buildMcpEntry() {
  const source=await readFile(resolve(root,'scripts/mcp-bootstrap.cjs'),'utf8');
  const manifestPath=resolve(root,'.mcp.json');
  const manifest=JSON.parse(await readFile(manifestPath,'utf8'));
  const spec=manifest.mcpServers['codex-agents-workflow'];
  // The version's stable parent identifies this installation's marketplace.
  // Do not hold the replaceable version directory as the process cwd.
  spec.cwd='..';
  spec.tool_timeout_sec=3660;
  spec.args=['-e',buildBootstrapSource(source)];
  spec.env_vars=[...new Set([...spec.env_vars,'CODEX_CLI_PATH'])];
  await writeFile(manifestPath,JSON.stringify(manifest,null,2)+'\n');
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await buildMcpEntry();
