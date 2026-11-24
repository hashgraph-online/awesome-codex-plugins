// Kit behaviour against a fake Telegram.WebApp. node --test (Node >= 22.18 strips the types).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ApiError, createTma, idempotencyKey, parseStartParam, perfClass, pickLanguage, platformClass, readLaunchParams, textDirection, versionAtLeast,
  type WebAppLike, type RootLike, type FallbackButtonLike,
} from './tma.ts';

type Call = [string, ...unknown[]];

function fakeButton(name: string, calls: Call[]) {
  const handlers = new Set<() => void>();
  return {
    handlers,
    setParams(p: Record<string, unknown>) { calls.push([`${name}.setParams`, p]); },
    onClick(cb: () => void) { handlers.add(cb); },
    offClick(cb: () => void) { handlers.delete(cb); },
    showProgress() { calls.push([`${name}.showProgress`]); },
    hideProgress() { calls.push([`${name}.hideProgress`]); this.setParams({ is_active: true }); }, // like the real script
    show() { calls.push([`${name}.show`]); },
    hide() { calls.push([`${name}.hide`]); },
    click() { for (const h of [...handlers]) h(); },
  };
}

function fakeWebApp(version: string, extra: Partial<WebAppLike> = {}) {
  const calls: Call[] = [];
  const events = new Map<string, Set<(...a: unknown[]) => void>>();
  const mem = new Map<string, string>();
  const storage = {
    setItem(k: string, v: string, cb?: (e: unknown) => void) { mem.set(k, v); cb?.(null); },
    getItem(k: string, cb: (e: unknown, v?: string | null) => void) { cb(null, mem.get(k) ?? ''); },
    removeItem(k: string, cb?: (e: unknown) => void) { mem.delete(k); cb?.(null); },
  };
  const tg = {
    initData: 'query_id=q&auth_date=1&hash=x',
    version,
    platform: 'ios',
    colorScheme: 'dark' as const,
    isVersionAtLeast: (v: string) => versionAtLeast(version, v),
    ready: () => calls.push(['ready']),
    onEvent: (n: string, cb: (...a: unknown[]) => void) => { if (!events.has(n)) events.set(n, new Set()); events.get(n)!.add(cb); },
    offEvent: (n: string, cb: (...a: unknown[]) => void) => { events.get(n)?.delete(cb); },
    setHeaderColor: (c: string) => calls.push(['setHeaderColor', c]),
    setBackgroundColor: (c: string) => calls.push(['setBackgroundColor', c]),
    setBottomBarColor: (c: string) => calls.push(['setBottomBarColor', c]),
    enableClosingConfirmation: () => calls.push(['enableClosingConfirmation']),
    disableClosingConfirmation: () => calls.push(['disableClosingConfirmation']),
    showConfirm: (m: string, cb: (ok: boolean) => void) => { calls.push(['showConfirm', m]); cb(true); },
    MainButton: fakeButton('MainButton', calls),
    SecondaryButton: fakeButton('SecondaryButton', calls),
    BackButton: fakeButton('BackButton', calls),
    SettingsButton: fakeButton('SettingsButton', calls),
    HapticFeedback: {
      impactOccurred: (s: string) => calls.push(['impact', s]),
      notificationOccurred: (t: string) => calls.push(['notification', t]),
      selectionChanged: () => calls.push(['selection']),
    },
    CloudStorage: storage,
    DeviceStorage: storage,
    SecureStorage: storage,
    ...extra,
  };
  const emit = (n: string) => { for (const cb of events.get(n) ?? []) cb(); };
  return { tg, calls, events, emit };
}

function fakeRoot(): RootLike {
  return { dataset: {}, style: { setProperty() {}, colorScheme: '' } };
}

const env = (tg: unknown, extra = {}) => ({
  webApp: tg as WebAppLike, root: fakeRoot(), location: { hash: '', search: '' }, userAgent: '', fallbackButton: null, ...extra,
});

test('versionAtLeast compares numerically per part', () => {
  assert.equal(versionAtLeast('7.10', '7.2'), true);
  assert.equal(versionAtLeast('7.2', '7.10'), false);
  assert.equal(versionAtLeast('8.0', '8.0'), true);
  assert.equal(versionAtLeast('10.1', '9.6'), true);
});

test('perfClass reads the Android class and treats a missing one as unknown', () => {
  const ua = 'Mozilla/5.0 (Linux; Android 14) Telegram-Android/11.2.0 (Google Pixel 6; Android 14; SDK 34; LOW)';
  assert.equal(perfClass(ua), 'low');
  assert.equal(perfClass('Mozilla/5.0 (iPhone)'), 'unknown');
});

test('platformClass groups clients', () => {
  assert.equal(platformClass('ios'), 'ios');
  assert.equal(platformClass('android'), 'android');
  assert.equal(platformClass('tdesktop'), 'desktop');
  assert.equal(platformClass('weba'), 'web');
  assert.equal(platformClass(undefined), 'unknown');
});

test('launch params are read from the hash and the start param from the query', () => {
  const p = readLaunchParams({ hash: '#tgWebAppVersion=8.0&tgWebAppPlatform=ios&route=/x', search: '?tgWebAppStartParam=order-12' });
  assert.deepEqual(p, { tgWebAppVersion: '8.0', tgWebAppPlatform: 'ios', tgWebAppStartParam: 'order-12' });
});

test('start_param is allowlist-parsed', () => {
  const routes = { order: /^order-(\d{1,12})$/, tab: /^tab-(menu|order)$/ };
  assert.equal(parseStartParam('order-8812', routes)?.match[1], '8812');
  assert.equal(parseStartParam('tab-order', routes)?.route, 'tab');
  assert.equal(parseStartParam('order-1;drop', routes), null);
  assert.equal(parseStartParam('../../etc', routes), null);
  assert.equal(parseStartParam('x'.repeat(513), routes), null);
  assert.equal(parseStartParam(undefined, routes), null);
});

test('root mirrors scheme, platform and performance class', () => {
  const { tg } = fakeWebApp('8.0');
  const root = fakeRoot();
  createTma(env(tg, { root, userAgent: 'Telegram-Android/11 (X Y; Android 14; SDK 34; HIGH)' }));
  assert.equal(root.dataset.tmaScheme, 'dark');
  assert.equal(root.dataset.tmaPlatform, 'ios');
  assert.equal(root.dataset.tmaPerf, 'high');
  assert.equal(root.style.colorScheme, 'dark');
});

test('chrome colours are gated and re-applied on themeChanged', () => {
  const { tg, calls, emit } = fakeWebApp('7.0');
  const tma = createTma(env(tg));
  tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'bottom_bar_bg_color' });
  assert.deepEqual(calls.map((c) => c[0]), ['setHeaderColor', 'setBackgroundColor']); // bottom bar is 7.10
  emit('themeChanged');
  assert.equal(calls.filter((c) => c[0] === 'setHeaderColor').length, 2);
});

test('MainButton shows progress while the handler runs and replaces the old handler', async () => {
  const { tg, calls } = fakeWebApp('9.6');
  const root = fakeRoot();
  const tma = createTma(env(tg, { root }));
  let first = 0;
  let second = 0;
  tma.mainButton({ text: 'Add · 4.50', onClick: () => { first++; } });
  tma.mainButton({ text: 'Place order', onClick: async () => { second++; }, iconCustomEmojiId: '5368324170671202286' });
  assert.equal(tg.MainButton.handlers.size, 1);
  tg.MainButton.click();
  await new Promise((r) => setTimeout(r, 0));
  assert.deepEqual([first, second], [0, 1]);
  const last = calls.filter((c) => c[0] === 'MainButton.setParams' && 'text' in (c[1] as object)).at(-1)![1] as Record<string, unknown>;
  assert.equal(last.icon_custom_emoji_id, '5368324170671202286');
  assert.ok(calls.some((c) => c[0] === 'MainButton.showProgress'));
  assert.ok(calls.some((c) => c[0] === 'MainButton.hideProgress'));
  assert.ok(calls.some((c) => c[0] === 'impact' && c[1] === 'light'));
  assert.equal(root.dataset.tmaMainButton, 'visible');
  tma.mainButton(null);
  assert.equal(root.dataset.tmaMainButton, 'hidden');
  assert.equal(tg.MainButton.handlers.size, 0);
});

test('icon emoji is dropped below 9.5 and SecondaryButton refuses below 7.10', () => {
  const { tg, calls } = fakeWebApp('7.2');
  const tma = createTma(env(tg));
  tma.mainButton({ text: 'Pay', onClick: () => {}, iconCustomEmojiId: '1' });
  const p = calls.find((c) => c[0] === 'MainButton.setParams')![1] as Record<string, unknown>;
  assert.equal('icon_custom_emoji_id' in p, false);
  assert.equal(tma.secondaryButton({ text: 'Details', onClick: () => {} }), false);
});

test('BackButton follows the stack and calls the top layer only', () => {
  const { tg, calls } = fakeWebApp('8.0');
  const tma = createTma(env(tg));
  const seen: string[] = [];
  tma.nav.push({ id: 'detail', kind: 'screen', onBack: () => { seen.push('detail'); tma.nav.pop('detail'); } });
  tma.nav.push({ id: 'sheet', kind: 'sheet', onBack: () => { seen.push('sheet'); tma.nav.pop('sheet'); } });
  tg.BackButton.click();
  assert.deepEqual(seen, ['sheet']);
  assert.equal(tma.nav.depth, 1);
  tg.BackButton.click();
  assert.equal(tma.nav.depth, 0);
  assert.equal(calls.filter((c) => c[0] === 'BackButton.hide').length, 1);
});

test('haptics are silent below 6.1 and mapped by meaning above', () => {
  const old = fakeWebApp('6.0');
  createTma(env(old.tg)).haptic.select();
  assert.equal(old.calls.length, 0);
  const cur = fakeWebApp('8.0');
  const t = createTma(env(cur.tg));
  t.haptic.select(); t.haptic.success();
  assert.deepEqual(cur.calls, [['selection'], ['notification', 'success']]);
});

test('confirm uses showConfirm from 6.2 and the caller fallback below', async () => {
  const { tg } = fakeWebApp('6.2');
  assert.equal(await createTma(env(tg)).confirm('Discard the draft?', async () => false), true);
  const old = fakeWebApp('6.1', { showConfirm: undefined });
  assert.equal(await createTma(env(old.tg)).confirm('Discard?', async () => false), false);
});

test('storage: CloudStorage from 6.9, in memory outside Telegram, Device/Secure from 9.0', async () => {
  const { tg } = fakeWebApp('8.0');
  const tma = createTma(env(tg));
  await tma.store().set('draft', '{"n":1}');
  assert.equal(await tma.store().get('draft'), '{"n":1}');
  assert.equal(await tma.store().get('missing'), null); // '' from CloudStorage is null
  assert.equal(tma.deviceStore(), null);
  assert.equal(tma.secureStore(), null);
  const outside = createTma(env(null));
  assert.equal(outside.inTelegram, false);
  await outside.store().set('k', 'v');
  assert.equal(await outside.store().get('k'), 'v'); // one in-memory store per kit instance, gone on reload
});

test('outside Telegram the MainButton spec drives the fallback button', () => {
  const btn: FallbackButtonLike = { hidden: true, textContent: '', disabled: true, onclick: null };
  const tma = createTma(env(null, { fallbackButton: btn }));
  let clicked = 0;
  tma.mainButton({ text: 'Place order', onClick: () => { clicked++; } });
  assert.equal(btn.hidden, false);
  assert.equal(btn.textContent, 'Place order');
  btn.onclick?.();
  assert.equal(clicked, 1);
  tma.mainButton(null);
  assert.equal(btn.hidden, true);
});

test('dispose removes every subscription', () => {
  const { tg, events } = fakeWebApp('8.0');
  const tma = createTma(env(tg));
  tma.on('activated', () => {});
  tma.dispose();
  for (const set of events.values()) assert.equal(set.size, 0);
});

test('hex header colour waits for 6.9; one failing setter does not stop the others', () => {
  const old = fakeWebApp('6.2', { setBackgroundColor: () => { throw new Error('boom'); } });
  const tma = createTma(env(old.tg));
  tma.chrome({ header: '#123456', background: 'bg_color' });
  assert.equal(old.calls.filter((c) => c[0] === 'setHeaderColor').length, 0);
  const cur = fakeWebApp('6.9');
  createTma(env(cur.tg)).chrome({ header: '#123456' });
  assert.deepEqual(cur.calls.find((c) => c[0] === 'setHeaderColor'), ['setHeaderColor', '#123456']);
});

test('a second tap while the handler runs is ignored and the current spec wins after progress', async () => {
  const { tg, calls } = fakeWebApp('8.0');
  const tma = createTma(env(tg));
  let runs = 0;
  let release: () => void = () => {};
  tma.mainButton({ text: 'Book', onClick: () => new Promise<void>((r) => { runs++; release = r; }) });
  tg.MainButton.click();
  tg.MainButton.click();
  tma.mainButton({ text: 'Choose a time', active: false, onClick: () => {} }); // the screen changed meanwhile
  release();
  await new Promise((r) => setTimeout(r, 0));
  assert.equal(runs, 1);
  const last = calls.filter((c) => c[0] === 'MainButton.setParams').at(-1)![1] as Record<string, unknown>;
  assert.equal(last.is_active, false);
});

test('settings keeps one handler', () => {
  const { tg } = fakeWebApp('7.0');
  const tma = createTma(env(tg));
  tma.settings(() => {});
  tma.settings(() => {});
  assert.equal(tg.SettingsButton.handlers.size, 1);
  tma.settings(null);
  assert.equal(tg.SettingsButton.handlers.size, 0);
});

test('pay() gates on 6.1, passes the status through and maps unknown values to failed', async () => {
  const old = fakeWebApp('6.0', { openInvoice: () => { throw new Error('unsupported'); } });
  assert.equal(await createTma(env(old.tg)).pay('https://t.me/$x'), 'unsupported');
  for (const status of ['paid', 'cancelled', 'failed', 'pending', 'weird']) {
    const { tg } = fakeWebApp('8.0', { openInvoice: (_u: string, cb: (s: string) => void) => cb(status) });
    assert.equal(await createTma(env(tg)).pay('https://t.me/$x'), status === 'weird' ? 'failed' : status);
  }
  const throwing = fakeWebApp('8.0', { openInvoice: () => { throw new Error('bad link'); } });
  assert.equal(await createTma(env(throwing.tg)).pay('nope'), 'failed');
});

test('watchOrder polls with back-off until the server says final, or times out', async () => {
  const { tg } = fakeWebApp('8.0');
  const tma = createTma(env(tg));
  const naps: number[] = [];
  const states = ['awaiting_payment', 'paid', 'delivered'];
  const res = await tma.watchOrder(async () => states.shift()!, (s) => s === 'delivered',
    { sleep: async (ms) => { naps.push(ms); } });
  assert.deepEqual(res, { state: 'delivered', timedOut: false });
  assert.deepEqual(naps, [1000, 2000]);
  const slow = await tma.watchOrder(async () => 'pending', (s) => s === 'delivered',
    { timeoutMs: 5000, sleep: async () => {} });
  assert.equal(slow.timedOut, true);
});

test('writeAccess() trusts allows_write_to_pm, asks from 6.9, and is false on older clients', async () => {
  const allowed = fakeWebApp('6.0', { initDataUnsafe: { user: { allows_write_to_pm: true } } });
  assert.equal(await createTma(env(allowed.tg)).writeAccess(), true);
  const asks = fakeWebApp('7.0', { requestWriteAccess: (cb: (ok: boolean) => void) => { asks.calls.push(['requestWriteAccess']); cb(true); } });
  assert.equal(await createTma(env(asks.tg)).writeAccess(), true);
  assert.deepEqual(asks.calls.filter((c) => c[0] === 'requestWriteAccess'), [['requestWriteAccess']]);
  const old = fakeWebApp('6.2', { requestWriteAccess: () => { throw new Error('must not be called'); } });
  assert.equal(await createTma(env(old.tg)).writeAccess(), false);
});

test('haptics: every style and type, one play per burst, an in-app switch, silent below 6.1', () => {
  let t = 0;
  const f = fakeWebApp('8.0');
  const tma = createTma(env(f.tg, { now: () => t }));
  for (const s of ['light', 'medium', 'heavy', 'rigid', 'soft'] as const) assert.equal(tma.haptic.impact(s), true);
  assert.equal(tma.haptic.notify('warning'), true);
  assert.equal(tma.haptic.select(), true);
  assert.equal(tma.haptic.select(), false);           // same pattern again within the gap
  t += 100;
  assert.equal(tma.haptic.select(), true);            // after the gap it plays
  tma.haptic.setEnabled(false);
  t += 100;
  assert.equal(tma.haptic.success(), false);
  assert.equal(tma.haptic.enabled, false);
  const kinds = f.calls.filter((c) => c[0] === 'impact' || c[0] === 'notification' || c[0] === 'selection');
  assert.deepEqual(kinds.map((c) => c.slice(0, 2).join(':')), [
    'impact:light', 'impact:medium', 'impact:heavy', 'impact:rigid', 'impact:soft', 'notification:warning', 'selection', 'selection']);
  const old = fakeWebApp('6.0');
  assert.equal(createTma(env(old.tg)).haptic.tap(), false);
});

function fakeSensor(log: string[]) {
  return {
    isStarted: false, x: 0.1, y: 9.8, z: 0.2, alpha: 1, beta: 0.5, gamma: -0.25, absolute: false,
    start(p: Record<string, unknown>) { this.isStarted = true; log.push(`start ${JSON.stringify(p)}`); },
    stop() { this.isStarted = false; log.push('stop'); },
  };
}

test('motion(): clamps the rate, reads values on each event, pauses while hidden, stops once', () => {
  const log: string[] = [];
  const acc = fakeSensor(log);
  const f = fakeWebApp('8.0', { Accelerometer: acc } as Partial<WebAppLike>);
  const tma = createTma(env(f.tg));
  const seen: Array<Record<string, unknown>> = [];
  const stop = tma.motion('accelerometer', (r) => seen.push(r), { refreshMs: 5 });
  assert.ok(stop);
  assert.deepEqual(log, ['start {"refresh_rate":20}']);
  f.emit('accelerometerChanged');
  assert.deepEqual(seen, [{ x: 0.1, y: 9.8, z: 0.2 }]);
  f.emit('deactivated');
  f.emit('activated');
  assert.deepEqual(log.slice(1), ['stop', 'start {"refresh_rate":20}']);
  stop!(); stop!();
  assert.equal(log.filter((l) => l === 'stop').length, 2);
  f.emit('accelerometerChanged');
  assert.equal(seen.length, 1);
  assert.equal(createTma(env(fakeWebApp('7.10', { Accelerometer: fakeSensor([]) } as Partial<WebAppLike>).tg)).motion('accelerometer', () => {}), null);
});

test('location(): initialises once, resolves the data, or null when unavailable', async () => {
  const data = { latitude: 52.37, longitude: 4.9, altitude: null, course: null, speed: null, horizontal_accuracy: 15, vertical_accuracy: null };
  let inits = 0;
  const lm = {
    isInited: false, isLocationAvailable: true, isAccessGranted: true,
    init(cb?: () => void) { inits++; this.isInited = true; cb?.(); },
    getLocation(cb: (d: typeof data | null) => void) { cb(data); },
    openSettings() {},
  };
  const tma = createTma(env(fakeWebApp('8.0', { LocationManager: lm } as Partial<WebAppLike>).tg));
  assert.deepEqual(await tma.location(), data);
  assert.deepEqual(await tma.location(), data);
  assert.equal(inits, 1);
  lm.isLocationAvailable = false;
  assert.equal(await tma.location(), null);
  assert.equal(await createTma(env(fakeWebApp('7.0').tg)).location(), null);
});

test('textDirection knows RTL scripts by base language', () => {
  for (const t of ['ar', 'fa-IR', 'he_IL', 'iw', 'ur', 'ckb']) assert.equal(textDirection(t), 'rtl', t);
  for (const t of ['en', 'ru', 'pt-BR', 'zh-Hant', 'ja']) assert.equal(textDirection(t), 'ltr', t);
});

test('pickLanguage: exact tag, then base language, in candidate order, then the fallback', () => {
  const sup = ['en', 'ru', 'pt-BR', 'ar'];
  assert.equal(pickLanguage(['pt_br'], sup, 'en'), 'pt-BR');
  assert.equal(pickLanguage(['pt-PT'], sup, 'en'), 'pt-BR');
  assert.equal(pickLanguage(['ru-UA'], sup, 'en'), 'ru');
  assert.equal(pickLanguage([null, 'de', 'ar-EG'], sup, 'en'), 'ar');
  assert.equal(pickLanguage(['de', undefined], sup, 'en'), 'en');
});

test('locale: the app override, then language_code, then the browser; sets lang and dir on <html>', () => {
  const tg = fakeWebApp('8.0', { initDataUnsafe: { user: { language_code: 'ar' } } }).tg;
  const root = fakeRoot();
  const tma = createTma(env(tg, { root, languages: ['ru-RU'] }));
  assert.deepEqual(tma.locale(['en', 'ru', 'ar']), { lang: 'ar', dir: 'rtl' });
  assert.equal(root.lang, 'ar'); assert.equal(root.dir, 'rtl');
  assert.deepEqual(tma.locale(['en', 'ru', 'ar'], { override: 'ru' }), { lang: 'ru', dir: 'ltr' });
  assert.equal(root.dir, 'ltr');
  const outside = createTma(env(null, { root: fakeRoot(), languages: ['de-DE', 'ru'] }));
  assert.equal(outside.locale(['en', 'ru']).lang, 'ru');
  assert.equal(outside.locale(['en', 'fr'], { fallback: 'en' }).lang, 'en');
});

function fakeServer(answers: Array<number | 'offline' | 'hang'>) {
  const seen: Array<{ url: string; init: Record<string, unknown> }> = [];
  let i = 0;
  const fetch = (url: string, init: Record<string, unknown>) => {
    seen.push({ url, init });
    const a = answers[Math.min(i++, answers.length - 1)];
    if (a === 'offline') return Promise.reject(new TypeError('Failed to fetch'));
    if (a === 'hang') return new Promise<never>((_, rej) => (init.signal as AbortSignal).addEventListener('abort', () => rej(new Error('aborted'))));
    return Promise.resolve({ ok: a < 400, status: a, text: async () => (a < 400 ? '{"ok":true}' : '{"reason":"Sold out"}') });
  };
  return { fetch, seen };
}
const noSleep = async () => {};

test('api: sends the raw initData, JSON body and parses the answer', async () => {
  const { tg } = fakeWebApp('8.0');
  const srv = fakeServer([200]);
  const tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  assert.deepEqual(await tma.api('/api/cart', { body: { id: 1 } }), { ok: true });
  const h = srv.seen[0].init.headers as Record<string, string>;
  assert.equal(h.Authorization, `tma ${tg.initData}`);
  assert.equal(srv.seen[0].init.method, 'POST');
  assert.equal(srv.seen[0].init.body, '{"id":1}');
});

test('api: GET retries offline and 5xx, a write without a key does not', async () => {
  const { tg } = fakeWebApp('8.0');
  let srv = fakeServer(['offline', 503, 200]);
  let tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  assert.deepEqual(await tma.api('/api/list'), { ok: true });
  assert.equal(srv.seen.length, 3);
  srv = fakeServer(['offline', 200]);
  tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  await assert.rejects(tma.api('/api/book', { body: {} }), (e: ApiError) => e.kind === 'offline');
  assert.equal(srv.seen.length, 1);
  srv = fakeServer([502, 200]);
  tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  const key = idempotencyKey();
  await tma.api('/api/book', { body: {}, idempotencyKey: key });
  assert.equal(srv.seen.length, 2);
  assert.equal((srv.seen[1].init.headers as Record<string, string>)['Idempotency-Key'], key);
});

test('api: 401 is a session error, 4xx a rejection with the reason, both without retries', async () => {
  const { tg } = fakeWebApp('8.0');
  let srv = fakeServer([401]);
  let tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  await assert.rejects(tma.api('/api/me'), (e: ApiError) => e.kind === 'session' && e.status === 401);
  assert.equal(srv.seen.length, 1);
  srv = fakeServer([409]);
  tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  await assert.rejects(tma.api('/api/me'), (e: ApiError) => e.kind === 'rejected' && e.reason === 'Sold out');
  assert.equal(srv.seen.length, 1);
});

test('api: a hanging request times out', async () => {
  const { tg } = fakeWebApp('8.0');
  const srv = fakeServer(['hang']);
  const tma = createTma(env(tg, { fetch: srv.fetch, sleep: noSleep }));
  await assert.rejects(tma.api('/api/slow', { timeoutMs: 20, retries: 0 }), (e: ApiError) => e.kind === 'timeout');
});

test('hideKeyboard uses the client from 9.1', () => {
  const a = fakeWebApp('9.1', { hideKeyboard() { a.calls.push(['hideKeyboard']); } } as Partial<WebAppLike>);
  createTma(env(a.tg)).hideKeyboard();
  assert.deepEqual(a.calls.filter((c) => c[0] === 'hideKeyboard').length, 1);
});
