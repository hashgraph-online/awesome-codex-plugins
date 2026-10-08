import assert from 'node:assert/strict';
import test from 'node:test';
import { createBootstrapInbox } from '../web-src/mcp-app-bootstrap.js';
import { createSettingsViewState } from '../web/settings-view-state.js';

test('holds the exact initial API read until opener bootstrap arrives and consumes it once', async () => {
  const inbox = createBootstrapInbox();
  let fallbackCalls = 0;
  const fallback = async () => {
    fallbackCalls += 1;
    return { body: { source: 'app-request' }, status: 200 };
  };

  let settled = false;
  const initialRead = inbox.request('/api/workflow/list', 'POST', { include_legacy: true }, fallback).then(value => {
    settled = true;
    return value;
  });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(settled, false, 'the first read must remain pending before the opener result');
  assert.equal(fallbackCalls, 0, 'the app-request tool must not duplicate the opener read');

  inbox.receive({
    _meta: {
      bootstrap: { '/api/workflow/list': [{ id: 'from-opener' }] },
      bootstrapStatus: { '/api/workflow/list': 200 },
      bootstrapRequests: { '/api/workflow/list': { method: 'POST', body: { include_legacy: true } } },
    },
  });
  assert.deepEqual(await initialRead, [{ id: 'from-opener' }]);
  assert.equal(fallbackCalls, 0);

  assert.deepEqual(await inbox.request('/api/workflow/list', 'POST', { include_legacy: true }, fallback), { source: 'app-request' });
  assert.equal(fallbackCalls, 1, 'a cached bootstrap response is consumed only once');
});

test('uses opener data only for an exact method and body match', async () => {
  const inbox = createBootstrapInbox();
  inbox.receive({
    _meta: {
      bootstrap: { '/api/workflow/list': [{ id: 'includes-legacy' }] },
      bootstrapStatus: { '/api/workflow/list': 200 },
      bootstrapRequests: { '/api/workflow/list': { method: 'POST', body: { include_legacy: true } } },
    },
  });

  assert.deepEqual(
    await inbox.request('/api/workflow/list', 'POST', {}, async () => ({ body: [{ id: 'ordinary-list' }], status: 200 })),
    [{ id: 'ordinary-list' }],
  );
  assert.deepEqual(
    await inbox.request('/api/workflow/list', 'POST', { include_legacy: true }, async () => {
      throw new Error('exact bootstrap request should not call the API tool');
    }),
    [{ id: 'includes-legacy' }],
  );
});

test('invalidates unconsumed opener failures after a successful configuration mutation', async () => {
  const inbox = createBootstrapInbox();
  inbox.receive({
    _meta: {
      bootstrap: {
        '/api/config': { config: { version: 6 } },
        '/api/workflow/role_templates': { error: 'Migrate configuration first', code: 'WORKFLOW_MIGRATION_REQUIRED' },
      },
      bootstrapStatus: { '/api/config': 200, '/api/workflow/role_templates': 400 },
      bootstrapRequests: {
        '/api/config': { method: 'GET', body: {} },
        '/api/workflow/role_templates': { method: 'POST', body: {} },
      },
    },
  });

  assert.deepEqual(await inbox.request('/api/config', 'GET', undefined, async () => {
    throw new Error('cached config must not call the API tool');
  }), { config: { version: 6 } });
  assert.deepEqual(await inbox.request('/api/workflow/migrate_v6', 'POST', {}, async () => ({
    body: { migrated: true }, status: 200,
  })), { migrated: true });
  assert.deepEqual(await inbox.request('/api/workflow/role_templates', 'POST', {}, async () => ({
    body: [{ id: 'fresh-role' }], status: 200,
  })), [{ id: 'fresh-role' }]);
});

test('preserves opener error status and body for migration diagnostics', async () => {
  const inbox = createBootstrapInbox();
  inbox.receive({
    _meta: {
      bootstrap: { '/api/workflow/list': { error: 'Migrate configuration first', code: 'WORKFLOW_MIGRATION_REQUIRED' } },
      bootstrapStatus: { '/api/workflow/list': 400 },
      bootstrapRequests: { '/api/workflow/list': { method: 'POST', body: { include_legacy: true } } },
    },
  });

  await assert.rejects(
    inbox.request('/api/workflow/list', 'POST', { include_legacy: true }, async () => {
      throw new Error('must not call the API tool for a cached opener response');
    }),
    error => error.message === 'Migrate configuration first'
      && error.status === 400
      && error.detail.code === 'WORKFLOW_MIGRATION_REQUIRED',
  );
});

test('rejects bootstrap data when its real HTTP status is missing', async () => {
  const inbox = createBootstrapInbox();
  inbox.receive({
    _meta: {
      bootstrap: { '/api/config': { config: { version: 7 } } },
      bootstrapStatus: {},
      bootstrapRequests: { '/api/config': { method: 'GET', body: {} } },
    },
  });
  await assert.rejects(
    inbox.request('/api/config', 'GET', undefined, async () => ({ body: {}, status: 200 })),
    /missing or invalid bootstrap status/,
  );
});

test('confirmed settings discard clears pending secrets and reloads the mounted view on return', async () => {
  const settingsView = createSettingsViewState();
  const root = {
    password: { value: 'unsaved-api-key' },
    configTitle: 'unsaved title',
    querySelectorAll(selector) {
      assert.equal(selector, 'input[type="password"]');
      return [this.password];
    },
  };
  let dirty = true;
  let view = 'settings';
  let mountCount = 0;
  let reloadCount = 0;
  const mountSettings = () => {
    mountCount += 1;
    if (mountCount > 1) settingsView.reloadOnReturn(root, target => {
      reloadCount += 1;
      target.configTitle = 'saved title';
    });
  };

  mountSettings();
  assert.equal(await settingsView.canLeave(root, dirty, async () => false), false, 'cancel keeps the current edit active');
  assert.equal(view, 'settings');
  assert.equal(root.password.value, 'unsaved-api-key');

  assert.equal(await settingsView.canLeave(root, dirty, async () => true, () => {
    root.configTitle = 'saved title';
    dirty = false;
  }), true, 'confirmed discard resets and allows navigation');
  view = 'workflows';
  assert.equal(root.password.value, '', 'confirmed discard clears unsaved credentials immediately');
  assert.equal(root.configTitle, 'saved title', 'confirmed discard resets every unsaved form field synchronously');

  view = 'settings';
  mountSettings();
  assert.equal(reloadCount, 1, 'returning to the existing mount reloads saved settings');
  assert.equal(root.configTitle, 'saved title');
  assert.equal(dirty, false);
});
