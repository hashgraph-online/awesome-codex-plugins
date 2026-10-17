import assert from 'node:assert/strict';
import test from 'node:test';
import { createLocaleStore, LOCALE_STORAGE_KEY, getLocale, setLocale } from '../web/i18n.js';
import { toCanvas } from '../web-src/graph-adapter.mjs';

function browser(language, saved) {
  const values = new Map(saved === undefined ? [] : [[LOCALE_STORAGE_KEY, saved]]);
  const events = new Map();
  return {
    navigator: { language }, document: { documentElement: {} },
    localStorage: { getItem: key => values.get(key) ?? null, setItem: (key, value) => values.set(key, value) },
    addEventListener: (name, listener) => events.set(name, listener),
    emit: (name, event) => events.get(name)(event),
  };
}

test('locale initializes from preference then browser, and remains shared after navigation', () => {
  const host = browser('zh-TW');
  const settings = createLocaleStore(host);
  assert.equal(settings.getLocale(), 'zh-CN');
  assert.equal(host.document.documentElement.lang, 'zh-CN');
  settings.setLocale('en');
  assert.equal(settings.t('模型', 'Model'), 'Model');
  const workflowPage = createLocaleStore(host);
  assert.equal(workflowPage.getLocale(), 'en');
  assert.equal(host.document.documentElement.lang, 'en');
  assert.equal(createLocaleStore(browser('en-CA')).getLocale(), 'en');
  assert.equal(createLocaleStore(browser('zh-CN', 'invalid')).getLocale(), 'zh-CN');
});

test('locale publishes changes without reloading and synchronizes only its own localStorage key', () => {
  const host = browser('en'); const store = createLocaleStore(host); let calls = 0;
  const unsubscribe = store.subscribeLocale(() => { calls++; });
  store.setLocale('zh-CN'); store.setLocale('zh-CN');
  assert.equal(calls, 1);
  host.emit('storage', { storageArea: host.localStorage, key: 'unrelated', newValue: 'en' });
  assert.equal(store.getLocale(), 'zh-CN');
  host.emit('storage', { storageArea: {}, key: LOCALE_STORAGE_KEY, newValue: 'en' });
  assert.equal(store.getLocale(), 'zh-CN');
  host.emit('storage', { storageArea: host.localStorage, key: LOCALE_STORAGE_KEY, newValue: 'en' });
  assert.equal(store.getLocale(), 'en'); assert.equal(calls, 2);
  unsubscribe(); store.setLocale('zh-CN'); assert.equal(calls, 2);
  host.emit('storage', { storageArea: host.localStorage, key: null, newValue: null });
  assert.equal(store.getLocale(), 'en');
});

test('invalid locale and failed persistence never publish a false success', () => {
  const host = browser('en'); const store = createLocaleStore(host);
  assert.throws(() => store.setLocale('fr'), /Unsupported workbench locale/);
  host.localStorage.setItem = () => { throw new Error('Storage blocked'); };
  assert.throws(() => store.setLocale('zh-CN'), /Storage blocked/);
  assert.equal(store.getLocale(), 'en');
});

test('localized canvas labels preserve saved workflow names and edge enum values', () => {
  const originalLocale = getLocale();
  const workflow = { nodes: [{id:'start',type:'start',name:'用户 Start'}, {id:'end',type:'end'}], edges:[{id:'edge',source:'start',target:'end',on:'failure',label:'保留 User label'}] };
  const before = structuredClone(workflow);
  try {
    setLocale('en'); const english = toCanvas(workflow);
    assert.equal(english.edges[0].label, '保留 User label · Failure');
    assert.equal(english.nodes[0].data.definition.name, '用户 Start');
    setLocale('zh-CN'); const chinese = toCanvas(workflow);
    assert.equal(chinese.edges[0].label, '保留 User label · 失败');
    assert.equal(chinese.edges[0].data.definition.on, 'failure');
    assert.deepEqual(workflow, before);
  } finally { setLocale(originalLocale); }
});
