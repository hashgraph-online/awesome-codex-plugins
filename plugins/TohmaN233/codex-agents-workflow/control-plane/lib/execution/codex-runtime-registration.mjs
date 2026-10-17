import { lstat, readFile, realpath } from 'node:fs/promises';
import { dirname, isAbsolute, join } from 'node:path';
import { configRevision, loadConfig, saveConfig } from '../config.mjs';
import { digest } from '../workflow-revisions.mjs';
import { writeDurableJSON } from '../workflow-events.mjs';
import { canonicalNoLinks, ensureDirectory, noSymlinks, requireValue } from '../workflow-paths.mjs';
import { WorkflowStore } from '../workflow-store.mjs';
import { qualifiedStrictSettings, qualifiedCooperativeSettings, codexQualification } from './strict-config.mjs';
import { discoverLocalCodex } from './local-codex-catalog.mjs';

// Registration precedes SDK session ownership: Strict prepares before a Run,
// while cooperative managers prepare only their reached authorized worker.
// Updates and rediscovery are proved before replacing the local identity;
// already-owned attempts retain their original pins and reject executable drift.
export async function refreshCodexRegistration({ configPath, defaultConfigPath, config, env = process.env,
  strict = true, scope = 'main', qualify = strict ? qualifiedStrictSettings : qualifiedCooperativeSettings, persist = saveConfig, discover = discoverLocalCodex } = {}) {
  config ??= await loadConfig({ configPath, defaultConfigPath });
  const settings = config.strict_executor;
  if (strict && !settings?.enabled) return config;
  const discoverReceivingCodex = () => {
    const override = env.CODEX_CATALOG_BINARY;
    requireValue(!override || isAbsolute(override), 'CODEX_CATALOG_PATH', 'CODEX_CATALOG_BINARY must be absolute');
    return discover({env:override?{...env,PATH:'',Path:'',LOCALAPPDATA:''}:env,extra:override?[override]:[]});
  };
  let registeredPath = settings.codex_binary, selected, reason = 'executable_updated';
  try {
    if (!registeredPath) {
      const source = await discoverReceivingCodex();
      registeredPath = source.selected_path ?? source.binary; reason = 'initial_registration';
    }
    selected = await realpath(registeredPath);
  }
  catch (error) {
    if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
    const source = await discoverReceivingCodex();
    registeredPath = source.selected_path ?? source.binary; selected = await realpath(registeredPath); reason = 'stale_installation_rediscovered';
  }
  const observed = digest(await readFile(selected));
  if (observed === settings.binary_sha256 && registeredPath === settings.codex_binary) return config;
  const candidate = structuredClone(config);
  candidate.strict_executor.binary_sha256 = observed;
  candidate.strict_executor.codex_binary = registeredPath;
  const qualified = await qualify(candidate, env, { scope });
  const path = join(dirname(configPath), 'codex-runtime-registration.json');
  const canonicalPath = await canonicalNoLinks(configPath);
  const configKey = process.platform === 'win32' ? canonicalPath.toLowerCase() : canonicalPath;
  const guard = await ensureDirectory(join(dirname(canonicalPath), '.codex-registration-' + digest(configKey)));
  // Qualification has no model effects and happens before this short bounded
  // commit admission. Receiving clients share the same per-config filesystem
  // guard; ordinary user config writers retain their fail-fast CAS contract.
  return new WorkflowStore(guard).withConfigBootstrapWriter(async () => {
    const previousRevision = configRevision(config), current = await loadConfig({configPath,defaultConfigPath});
    const currentRevision = configRevision(current);
    requireValue(await realpath(registeredPath) === selected && digest(await readFile(selected)) === observed,
      'CODEX_BINARY_CHANGED', 'Selected Codex executable changed during registration');
    if (currentRevision !== previousRevision) {
      let peer;
      try {
        await noSymlinks(path);const info = await lstat(path);
        requireValue(info.isFile() && info.nlink === 1 && info.size <= 1024 * 1024,
          'CODEX_REGISTRATION_AUDIT', 'Codex registration receipt must be a bounded regular file');
        peer = JSON.parse(await readFile(path, 'utf8'));
      } catch (error) { if (error.code !== 'ENOENT' || error.path !== path) throw error; }
      requireValue(currentRevision === configRevision(candidate) && peer?.status === 'registered'
        && peer.config_path === configKey && peer.previous_config_revision === previousRevision && peer.config_revision === currentRevision
        && peer.previous_selected_path === settings.codex_binary && peer.previous_sha256 === settings.binary_sha256
        && peer.selected_path === registeredPath && peer.resolved_path === selected && peer.executable_sha256 === observed,
        'CODEX_REGISTRATION_CONFLICT', 'configuration changed since it was loaded; no exact compatible peer registration was proved');
      return current;
    }
    const audit = { status: 'prepared', reason, config_path: configKey, previous_config_revision: previousRevision,
      previous_selected_path: settings.codex_binary, selected_path: registeredPath, resolved_path: selected,
      previous_sha256: settings.binary_sha256, executable_sha256: observed, qualification: codexQualification(qualified), at: new Date().toISOString() };
    await writeDurableJSON(path, audit);
    try {
      const saved = await persist(candidate, { configPath, expectedRevision: previousRevision });
      await writeDurableJSON(path, { ...audit, status: 'registered', config_revision: saved.revision });
      return saved.config;
    } catch (error) {
      try { await writeDurableJSON(path, { ...audit, status: 'failed', error: { code: error.code ?? 'CODEX_REGISTRATION_FAILED', message: error.message } }); }
      catch (auditError) { throw new AggregateError([error, auditError], 'Codex registration and diagnostic persistence failed'); }
      throw error;
    }
  });
}
