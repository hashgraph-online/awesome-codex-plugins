import assert from 'node:assert/strict';
import { mkdtemp, readFile } from 'node:fs/promises';
import { tmpdir } from './physical-tempdir.mjs';
import { join } from 'node:path';
import test from 'node:test';

import { DEFAULT_CONFIG_PATH, SERVER_VERSION, startConsole, stopConsole } from '../server.mjs';

test('loopback console requires token and revision-checks saves', async (t) => {
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-console-'));
  const configPath = join(dir, 'control-plane.json');
  const state = await startConsole({ configPath, defaultConfigPath: DEFAULT_CONFIG_PATH, open: false });
  t.after(stopConsole);
  const base = `http://127.0.0.1:${state.port}`;
  const release=JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8'));
  assert.equal(SERVER_VERSION, release.version);
  assert.deepEqual(await (await fetch(`${base}/health`)).json(), {
    status: 'ok', version: SERVER_VERSION,
  });

  const unauthorized = await fetch(`${base}/api/config`);
  assert.equal(unauthorized.status, 401);

  const appSource = await (await fetch(`${base}/app.js`)).text();
  for (const moduleName of ['app-client.js', 'settings-view-state.js']) {
    assert.ok(appSource.includes(`'./${moduleName}'`), `${moduleName} is imported by settings`);
    const moduleResponse = await fetch(`${base}/${moduleName}`);
    assert.equal(moduleResponse.status, 200, moduleName);
    assert.match(moduleResponse.headers.get('content-type'), /javascript/);
    assert.equal(await moduleResponse.text(), await readFile(new URL(`../web/${moduleName}`, import.meta.url), 'utf8'));
  }
  const localeModule = await fetch(`${base}/i18n.js`);
  assert.equal(localeModule.status, 200);
  assert.match(localeModule.headers.get('content-type'), /javascript/);
  assert.match(await localeModule.text(), /subscribeLocale/);
  const indexSource = await (await fetch(`${base}/index.html`)).text();
  const stylesSource = await (await fetch(`${base}/styles.css`)).text();
  assert.match(appSource, /provider-reasoning-effort/);
  assert.match(appSource, /nativeModelSelect/);
  assert.match(appSource, /provider-api-key/);
  assert.match(appSource, /\/api\/models/);
  assert.doesNotMatch(appSource, /textInput\(provider\.config\?\.model \|\| '', 'provider-model'\)/);
  assert.match(appSource, /reasoning_effort \|\| ''/);
  assert.match(appSource, /task-type-card/);
  assert.match(appSource, /add-task-type-from-preset/);
  assert.match(appSource, /duplicate-task-type/);
  assert.match(appSource, /workflow-review/);
  assert.match(appSource, /Independent review stage/);
  assert.match(appSource, /defaultProviderIdForRole\(shape\.role, access\)/);
  assert.match(appSource, /Ask before every Provider use/);
  assert.match(appSource, /Ask before this Stage/);
  assert.match(appSource, /Leave both off for no additional model-call prompt/);
  assert.doesNotMatch(appSource, /task-type-route/);
  assert.doesNotMatch(appSource, /selectInput\(\['solo', 'delegate', 'audit', 'full'\]/);
  assert.doesNotMatch(appSource, /scenario-card/);
  assert.match(indexSource, /config-storage/);
  assert.match(indexSource, /add-api-provider/);
  assert.match(stylesSource, /\.provider-native-options\[hidden\], \.provider-api-options\[hidden\]/);

  const headers = { authorization: `Bearer ${state.token}` };
  const loadedResponse = await fetch(`${base}/api/config`, { headers });
  assert.equal(loadedResponse.status, 200);
  const loaded = await loadedResponse.json();
  assert.ok(loaded.config.task_types[0].stages[0].template.includes('{{task}}'));
  assert.equal(loaded.config.providers.some((provider) => provider.requires_user_approval), false);
  assert.equal(loaded.config.task_types.some((taskType) =>
    taskType.stages.some((stage) => stage.requires_user_approval)), false);
  assert.deepEqual(loaded.storage, {
    scope: 'override',
    config_path: configPath,
  });

  loaded.config.global.enabled = false;
  const savedResponse = await fetch(`${base}/api/config`, {
    method: 'PUT',
    headers: { ...headers, 'content-type': 'application/json' },
    body: JSON.stringify({ config: loaded.config, expected_revision: loaded.revision }),
  });
  assert.equal(savedResponse.status, 200);
  const saved = await savedResponse.json();
  assert.equal(saved.config.global.enabled, false);

  const staleResponse = await fetch(`${base}/api/config`, {
    method: 'PUT',
    headers: { ...headers, 'content-type': 'application/json' },
    body: JSON.stringify({ config: loaded.config, expected_revision: loaded.revision }),
  });
  assert.equal(staleResponse.status, 409);

  const secretStatus = await (await fetch(`${base}/api/provider-secrets`, { headers })).json();
  const custom = secretStatus.providers.find(provider => provider.provider_id === 'custom-openai-compatible');
  assert.equal(custom.ready, false);
  const key = 'session-only-console-test-key';
  const secretResponse = await fetch(`${base}/api/provider-secret`, {
    method: 'PUT', headers: { ...headers, 'content-type': 'application/json' },
    body: JSON.stringify({ provider_id: custom.provider_id, api_key: key }),
  });
  assert.equal(secretResponse.status, 200);
  assert.equal((await secretResponse.json()).ready, true);
  const afterSecret = await (await fetch(`${base}/api/config`, { headers })).text();
  assert.equal(afterSecret.includes(key), false);
  const cleared = await fetch(`${base}/api/provider-secret`, {
    method: 'PUT', headers: { ...headers, 'content-type': 'application/json' },
    body: JSON.stringify({ provider_id: custom.provider_id, clear: true }),
  });
  assert.equal(cleared.status, 200);
  assert.equal((await cleared.json()).ready, false);
});

test('ordinary console reports global storage under CODEX_HOME', async (t) => {
  const codexHome = await mkdtemp(join(tmpdir(), 'sol-control-global-'));
  const state = await startConsole({
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    open: false,
    env: { ...process.env, CODEX_HOME: codexHome, SOL_CONTROL_CONFIG: '' },
  });
  t.after(stopConsole);
  const payload = await (await fetch(`http://127.0.0.1:${state.port}/api/config`, {
    headers: { authorization: `Bearer ${state.token}` },
  })).json();
  assert.deepEqual(payload.storage, {
    scope: 'global',
    config_path: join(codexHome, 'codex-agents-workflow', 'control-plane.json'),
  });
});

test('an explicitly passed resolved global path is still reported as global', async (t) => {
  const codexHome = await mkdtemp(join(tmpdir(), 'sol-control-explicit-global-'));
  const configPath = join(codexHome, 'codex-agents-workflow', 'control-plane.json');
  const state = await startConsole({
    configPath,
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    open: false,
    env: { ...process.env, CODEX_HOME: codexHome, SOL_CONTROL_CONFIG: '' },
  });
  t.after(stopConsole);
  const payload = await (await fetch(`http://127.0.0.1:${state.port}/api/config`, {
    headers: { authorization: `Bearer ${state.token}` },
  })).json();
  assert.deepEqual(payload.storage, {
    scope: 'global',
    config_path: configPath,
  });
});

test('SOL_CONTROL_CONFIG is visibly reported as an override', async (t) => {
  const dir = await mkdtemp(join(tmpdir(), 'sol-control-env-override-'));
  const configPath = join(dir, 'control-plane.json');
  const state = await startConsole({
    defaultConfigPath: DEFAULT_CONFIG_PATH,
    open: false,
    env: { ...process.env, SOL_CONTROL_CONFIG: configPath },
  });
  t.after(stopConsole);
  const payload = await (await fetch(`http://127.0.0.1:${state.port}/api/config`, {
    headers: { authorization: `Bearer ${state.token}` },
  })).json();
  assert.deepEqual(payload.storage, {
    scope: 'override',
    config_path: configPath,
  });
});
