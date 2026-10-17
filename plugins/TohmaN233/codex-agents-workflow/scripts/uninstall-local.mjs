import {execFileSync} from 'node:child_process';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {preflightNativeContextProfileRegistration,cleanupNativeContextProfile} from './native-context-profile.mjs';

// Codex's stock external plugin removal does not remove personal agent files.
// Use this explicit wrapper to remove the plugin and its exact owned profile.
export async function uninstallLocal({codexHome,uninstall=()=>execFileSync('codex',['plugin','remove','codex-agents-workflow@codex-agents-workflow'],{stdio:'inherit',windowsHide:true})}={}){
 preflightNativeContextProfileRegistration({codexHome});
 await uninstall();
 return {uninstalled:true,native_context_profile:cleanupNativeContextProfile({codexHome})};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)console.log(JSON.stringify(await uninstallLocal()));
