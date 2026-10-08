import { readFile, realpath } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { configRevision, loadConfig, saveConfig } from '../config.mjs';
import { digest } from '../workflow-revisions.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';
import { requireValue } from '../workflow-paths.mjs';
import { qualifiedStrictSettings, codexQualification } from './strict-config.mjs';
import { discoverLocalCodex } from './local-codex-catalog.mjs';

// Registration belongs to pre-Run preparation. An ordinary in-place update at
// the selected address, or rediscovery after its removal, is proved before
// replacing its local identity; running
// attempts keep their original identity and reject executable drift.
export async function refreshCodexRegistration({ configPath, defaultConfigPath, config, env = process.env,
  qualify = qualifiedStrictSettings, persist = saveConfig, discover = discoverLocalCodex } = {}) {
  config ??= await loadConfig({ configPath, defaultConfigPath });
  const settings = config.strict_executor;
  if (!settings?.enabled) return config;
  let registeredPath = settings.codex_binary, selected, reason = 'executable_updated';
  try { selected = await realpath(registeredPath); }
  catch (error) {
    if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
    const source = await discover({ env });
    registeredPath = source.binary; selected = await realpath(registeredPath); reason = 'stale_installation_rediscovered';
  }
  const observed = digest(await readFile(selected));
  if (observed === settings.binary_sha256 && registeredPath === settings.codex_binary) return config;
  const candidate = structuredClone(config);
  candidate.strict_executor.binary_sha256 = observed;
  candidate.strict_executor.codex_binary = registeredPath;
  const qualified = await qualify(candidate, env);
  requireValue(await realpath(registeredPath) === selected && digest(await readFile(selected)) === observed,
    'CODEX_BINARY_CHANGED', 'Selected Codex executable changed during registration');
  const path = join(dirname(configPath), 'codex-runtime-registration.json');
  const audit = { status: 'prepared', reason, previous_selected_path: settings.codex_binary, selected_path: registeredPath, resolved_path: selected,
    previous_sha256: settings.binary_sha256, executable_sha256: observed, qualification: codexQualification(qualified), at: new Date().toISOString() };
  await writeDurableJSON(path, audit);
  try {
    const saved = await persist(candidate, { configPath, expectedRevision: configRevision(config) });
    await writeDurableJSON(path, { ...audit, status: 'registered', config_revision: saved.revision });
    return saved.config;
  } catch (error) {
    try { await writeDurableJSON(path, { ...audit, status: 'failed', error: { code: error.code ?? 'CODEX_REGISTRATION_FAILED', message: error.message } }); }
    catch (auditError) { throw new AggregateError([error, auditError], 'Codex registration and diagnostic persistence failed'); }
    throw error;
  }
}
