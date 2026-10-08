import { readFile, lstat, open, rename } from 'node:fs/promises';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';
import { defaultRoutingRules, validateRoutingRules } from './routing-rules.mjs';
import { noSymlinks, requireValue } from '../workflow-paths.mjs';
import { canonicalJSON } from '../workflow-revisions.mjs';
import { syncDirectory } from '../workflow-store.mjs';
import { canonicalizeRoutingProviderIds } from '../native-provider-identity.mjs';

export async function loadRoutingSettings(directory, providers) {
  const path = join(directory,'skill2workflow-rules.json');
  try {
    await noSymlinks(path); const info = await lstat(path);
    requireValue(info.isFile() && info.nlink === 1 && info.size <= 128000,'ROUTING_SETTINGS_FILE','Routing settings must be a bounded regular file');
    const bytes = await readFile(path);
    requireValue(bytes.length <= 128000,'ROUTING_SETTINGS_FILE','Routing settings grew beyond limit');
    return validateRoutingRules(canonicalizeRoutingProviderIds(JSON.parse(bytes.toString('utf8'))));
  } catch (error) { if (error.code === 'ENOENT') return defaultRoutingRules(providers); throw error; }
}
export async function saveRoutingSettings(directory, providers, store, rules, expected) {
  const validated = validateRoutingRules(canonicalizeRoutingProviderIds(rules));
  return store.withWriter(async()=>{
    const current = await loadRoutingSettings(directory,providers);
    requireValue(canonicalJSON(current) === canonicalJSON(expected),'ROUTING_SETTINGS_CONFLICT','Routing rules changed; reload before saving');
    await noSymlinks(directory);
    const temporary = join(directory,`.skill2workflow-${randomUUID()}.tmp`);
    const handle = await open(temporary,'wx',0o600);
    try { await handle.writeFile(canonicalJSON(validated)); await handle.sync(); } finally { await handle.close(); }
    await rename(temporary,join(directory,'skill2workflow-rules.json')); await syncDirectory(directory);
    return validated;
  });
}
