#!/usr/bin/env python3
"""Local preview stand for a Telegram Mini App inside a MOCK of the Telegram client.

  py -3 scripts/preview_miniapp.py examples/mini-apps/vanilla --serve 8790
      open http://127.0.0.1:8790/                 one device with Telegram chrome, panels around it
      open http://127.0.0.1:8790/?view=matrix     iOS/Android x light/dark x 320/390/430 + fullscreen
      open http://127.0.0.1:8790/?platform=android&scheme=dark&width=390&mode=fullscreen&version=8.0
      add &height=1600 for a taller device (long screens in one screenshot)
      add &zoom=100 (fit, 50, 75, 100) and &panels=0 (no side or bottom panels) for screenshots at 1:1
      add &audit=1 to measure the layout after ready(): gaps between surfaces, text inset, radii
      (examples/mini-apps/_kit/tma-audit.mjs, rules LA01-LA05); findings go to the Layout tab, the surfaces get
      a dashed outline, window.__tmaAudit holds the result and window.tmaAudit() re-runs it on the current screen
  py -3 scripts/preview_miniapp.py examples/mini-apps/vanilla --check   # static checks, no server

The stand serves the app's folder (by default its parent, so `../_kit/tma.css` resolves) on
127.0.0.1 only, replaces the `telegram-web-app.js` script tag with a local mock of
`window.Telegram.WebApp`, and draws what Telegram draws around a Mini App: the status bar, the
header (Close or Back, title, menu), the bottom bar with MainButton / SecondaryButton, native
popups, the closing confirmation, the loading placeholder until ready(), the fullscreen controls and
safe areas. The page (preview_stand/: HTML, CSS, JS, no build, no network) has:

  toolbar     relaunch, the app's address and its ready() status, platform, width, day/night theme, zoom
  left        launch parameters that relaunch the app: client version, the user's language_code
              (en, ru, uk, de, ar, he, fa), start_param, Android performance class; live settings the running
              app sees at once: viewport (compact, full, fullscreen), the network for its own requests
              (slow 3 s, flaky, offline, 500, 401: `?network=offline`), the invoice outcome (paid, cancelled,
              failed, pending: `?invoice=paid`), style preset (native / fintech / soft / dense); the user's
              moves: system back, minimize (deactivated / activated), close, relaunch
  bottom      Events (every call: haptics, popups, chrome colours, buttons, storage, links, payments,
              unsupported members, the app's errors), Network (each request, its status and time), Layout
  right       Inspector: lifecycle, viewport and safe areas, chrome colours, MainButton and SecondaryButton,
              closing confirmation and swipes, theme parameters, initData, CloudStorage / DeviceStorage /
              SecureStorage (kept across relaunches in the tab, Clear for a first launch)

The URL holds every setting (Copy link reproduces the view); the day/night switch sends themeChanged
to the running app instead of reloading it. Motion sensors and location give synthetic readings and
demo coordinates.

Versions come from data/mini-apps/webapp-catalog.json: a member newer than the selected client
version behaves like the real script (methods throw `WebAppMethodUnsupported`, objects and setters
warn and do nothing).

THIS IS A MOCK. Theme palettes are approximations of Telegram's defaults, chrome sizes are
typical values, initData is unsigned demo data, payments never happen. A screen that looks right
here proves nothing about real clients: test on iOS, Android and Desktop
(references/mini-apps/performance-and-testing.md).

If the served folder has a build.mjs (the skill's examples), it runs `node build.mjs` first.
The app itself is served at /app/<path of the entry under the root>, e.g. /app/rework/index.html.

  --api mock.json   answers the app's own requests, so a server flow (checkout, order status) runs in the
                    stand: {"POST /api/checkout": {"body": {...}}, "GET /api/orders/*": {"body": {...}}}.
                    Keys are "METHOD /path" with * for one path segment; values take "status" (200),
                    "body" (JSON) and "delay_ms". The string "$order_status" in a body becomes the order state
                    for the stand's Invoice control: paid -> "paid", failed -> "failed", else "open".
                    Without --api every request outside /app/ answers 501.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_JS = os.path.join(SKILL, "examples", "mini-apps", "_kit", "tma-audit.mjs")
CATALOG = os.path.join(SKILL, "data", "mini-apps", "webapp-catalog.json")
SCRIPT_TAG = re.compile(r"<script\b[^>]*\bsrc=[\"']https://telegram\.org/js/telegram-web-app\.js[^\"']*[\"'][^>]*>\s*</script>", re.I)
MOCK_TAG = '<script src="/__tma__/mock.js"></script>'

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# Approximate Telegram default palettes (mock only; real ones come from the user's theme).
THEMES = {
    "ios-light": {"bg_color": "#ffffff", "text_color": "#000000", "hint_color": "#8e8e93", "link_color": "#007aff",
                  "button_color": "#007aff", "button_text_color": "#ffffff", "secondary_bg_color": "#f2f2f7",
                  "header_bg_color": "#f8f8f8", "accent_text_color": "#007aff", "section_bg_color": "#ffffff",
                  "section_header_text_color": "#6d6d72", "subtitle_text_color": "#8e8e93",
                  "destructive_text_color": "#ff3b30", "section_separator_color": "#c8c7cc",
                  "bottom_bar_bg_color": "#f2f2f7"},
    "ios-dark": {"bg_color": "#000000", "text_color": "#ffffff", "hint_color": "#98989e", "link_color": "#3e88f7",
                 "button_color": "#3e88f7", "button_text_color": "#ffffff", "secondary_bg_color": "#000000",
                 "header_bg_color": "#1a1a1a", "accent_text_color": "#3e88f7", "section_bg_color": "#1c1c1e",
                 "section_header_text_color": "#8d8e93", "subtitle_text_color": "#98989e",
                 "destructive_text_color": "#eb5545", "section_separator_color": "#38383a",
                 "bottom_bar_bg_color": "#1d1d1d"},
    "android-light": {"bg_color": "#ffffff", "text_color": "#222222", "hint_color": "#a8a8a8", "link_color": "#2678b6",
                      "button_color": "#50a8eb", "button_text_color": "#ffffff", "secondary_bg_color": "#f0f0f0",
                      "header_bg_color": "#527da3", "accent_text_color": "#1c93e3", "section_bg_color": "#ffffff",
                      "section_header_text_color": "#3a95d5", "subtitle_text_color": "#82868a",
                      "destructive_text_color": "#cc2929", "section_separator_color": "#d9d9d9",
                      "bottom_bar_bg_color": "#ffffff"},
    "android-dark": {"bg_color": "#212d3b", "text_color": "#ffffff", "hint_color": "#8d9ba8", "link_color": "#62bcf9",
                     "button_color": "#50a8eb", "button_text_color": "#ffffff", "secondary_bg_color": "#151e27",
                     "header_bg_color": "#242d39", "accent_text_color": "#64b5ef", "section_bg_color": "#1d2733",
                     "section_header_text_color": "#64b5ef", "subtitle_text_color": "#7d8b99",
                     "destructive_text_color": "#ee686f", "section_separator_color": "#0f161e",
                     "bottom_bar_bg_color": "#1d2733"},
}
# Typical chrome geometry (px). Safe areas follow Telegram's split: device insets vs Telegram's own controls.
DEVICES = {
    "ios": {"status": 54, "header": 52, "bar": 64, "home": 34, "safe_fs": {"top": 54, "bottom": 34},
            "content_fs": {"top": 46}},
    "android": {"status": 28, "header": 56, "bar": 64, "home": 0, "safe_fs": {"top": 28, "bottom": 24},
                "content_fs": {"top": 48}},
    "tdesktop": {"status": 0, "header": 40, "bar": 60, "home": 0, "safe_fs": {"top": 0, "bottom": 0},
                 "content_fs": {"top": 0}},
}
HEIGHTS = {320: 600, 375: 740, 390: 800, 430: 860, 384: 640, 669: 860}  # 669: iPhone Duo inner display (iOS 27 kit)
# Methods that throw WebAppMethodUnsupported in telegram-web-app.js when the client is too old (read 2026-11-23).
THROWING = ["addToHomeScreen", "checkHomeScreenStatus", "closeScanQrPopup", "downloadFile", "exitFullscreen",
            "openInvoice", "readTextFromClipboard", "requestChat", "requestContact", "requestEmojiStatusAccess",
            "requestFullscreen", "requestWriteAccess", "setEmojiStatus", "shareMessage", "shareToStory", "showPopup",
            "showScanQrPopup", "switchInlineQuery", "showAlert", "showConfirm"]


def gates() -> dict[str, str]:
    with open(CATALOG, encoding="utf-8") as fh:
        members = json.load(fh)["members"]
    return {k: m["version"] for k, m in members.items()
            if m["owner"] in ("WebApp", "BottomButton") and m["version"] and m["version"] != "6.0"}


# --------------------------------------------------------------------------- mock (runs in the app frame)

MOCK_JS = r"""/* MOCK of window.Telegram.WebApp for the local preview stand. Not Telegram's script. */
(function () {
  'use strict';
  var GATES = __GATES__;
  var THROWING = __THROWING__;
  var hp = new URLSearchParams(location.hash.slice(1));
  var cfg = {};
  try { cfg = JSON.parse(hp.get('tgWebAppMock') || '{}'); } catch (e) {}
  var version = hp.get('tgWebAppVersion') || '6.0';
  var platform = hp.get('tgWebAppPlatform') || 'unknown';
  var themeParams = {};
  try { themeParams = JSON.parse(hp.get('tgWebAppThemeParams') || '{}'); } catch (e) {}
  var colorScheme = cfg.scheme || 'light';
  var initData = hp.get('tgWebAppData') || '';
  var root = document.documentElement;
  var handlers = {};
  if (cfg.style) root.setAttribute('data-tma-style', cfg.style);  // stand's Style control: preview any app in a preset
  if (platform === 'android' && cfg.perf) {  // Telegram Android reports its performance class in the User-Agent
    var ua = navigator.userAgent + ' Telegram-Android/11.0.0 (Mock Device; Android 14; SDK 34; ' + cfg.perf + ')';
    try { Object.defineProperty(navigator, 'userAgent', { get: function () { return ua; } }); } catch (e) {}
  }
  var inStand = window.parent && window.parent !== window;

  // the stand and the app share one origin (both served here): never post to '*'
  function post(type, data) { if (inStand) window.parent.postMessage({ __tma: 1, type: type, data: data }, location.origin); }
  function log(kind, name, detail) { post('log', { kind: kind, name: name, detail: detail === undefined ? '' : detail }); }
  function cmp(a, b) {
    var x = String(a).split('.'), y = String(b).split('.');
    for (var i = 0; i < Math.max(x.length, y.length); i++) {
      var p = +x[i] || 0, q = +y[i] || 0;
      if (p !== q) return p > q;
    }
    return true;
  }
  function ok(key, name) {
    var need = GATES[key];
    if (!need || cmp(version, need)) return true;
    var msg = '[Telegram.WebApp] ' + name + ' is not supported in version ' + version + ' (needs ' + need + ')';
    log('unsupported', key, 'client ' + version + ', needs ' + need);
    if (THROWING.indexOf(name) >= 0) { console.error(msg); throw Error('WebAppMethodUnsupported'); }
    console.warn(msg);
    return false;
  }
  function css(name, value) { root.style.setProperty('--tg-' + name, value); }
  function applyTheme() {
    Object.keys(themeParams).forEach(function (k) { css('theme-' + k.replace(/_/g, '-'), themeParams[k]); });
    css('color-scheme', colorScheme);
  }
  var safe = cfg.safe || { top: 0, bottom: 0, left: 0, right: 0 };
  var content = cfg.content || { top: 0, bottom: 0, left: 0, right: 0 };
  function applyInsets() {
    ['top', 'bottom', 'left', 'right'].forEach(function (s) {
      css('safe-area-inset-' + s, (safe[s] || 0) + 'px');
      css('content-safe-area-inset-' + s, (content[s] || 0) + 'px');
    });
  }
  function applyViewport() {
    css('viewport-height', window.innerHeight + 'px');
    css('viewport-stable-height', window.innerHeight + 'px');
  }
  applyTheme(); applyViewport();
  if (cmp(version, '8.0')) applyInsets();
  window.addEventListener('resize', function () { applyViewport(); emit('viewportChanged', { isStateStable: true }); });

  function emit(name, data) {
    (handlers[name] || []).slice().forEach(function (cb) { try { cb.call(WebApp, data); } catch (e) { console.error(e); } });
  }
  function keyword(c) {
    if (c === 'bg_color' || c === 'secondary_bg_color' || c === 'bottom_bar_bg_color') return themeParams[c] || null;
    return c;
  }
  // Errors the app throws or prints reach the stand's Events panel (the mock's own warnings are logged as unsupported)
  window.addEventListener('error', function (e) {
    if (e.message) log('error', e.message, e.filename ? e.filename.replace(location.origin, '') + ':' + e.lineno : '');
  });
  window.addEventListener('unhandledrejection', function (e) {
    var r = e.reason; log('error', 'unhandled rejection', r && r.message ? r.message : String(r));
  });
  var consoleError = console.error;
  console.error = function () {
    var a = Array.prototype.slice.call(arguments);
    if (String(a[0]).indexOf('[Telegram.WebApp]') !== 0) {
      log('error', 'console.error', a.map(function (x) {
        if (x && x.message) return x.message;
        try { return typeof x === 'object' ? JSON.stringify(x) : String(x); } catch (err) { return String(x); }
      }).join(' ').slice(0, 500));
    }
    return consoleError.apply(console, arguments);
  };

  var store = {};
  function storage(name, since, limits) {
    var mem = store[name] = {};
    var kept = cfg.storage && cfg.storage[name];  // the stand keeps storage across relaunches, like Telegram
    if (kept && typeof kept === 'object') Object.keys(kept).forEach(function (k) { mem[k] = String(kept[k]); });
    function cb(f, a, b) { setTimeout(function () { f && f(a, b); }, 0); }
    function changed() { post('storage', { name: name, items: Object.assign({}, mem) }); }
    function guard(key) {
      if (!ok('WebApp.' + name, name)) return false;
      if (limits && !/^[A-Za-z0-9_-]{1,128}$/.test(key)) throw Error('WebAppStorageKeyInvalid');
      return true;
    }
    var api = {
      setItem: function (k, v, f) {
        if (!guard(k)) return api;
        if (limits && String(v).length > 4096) { cb(f, 'VALUE_TOO_LONG'); return api; }
        mem[k] = String(v); log('storage', name + '.setItem', k); changed(); cb(f, null, true); return api;
      },
      getItem: function (k, f) { if (guard(k)) cb(f, null, k in mem ? mem[k] : (limits ? '' : null)); return api; },
      getItems: function (ks, f) { var o = {}; ks.forEach(function (k) { o[k] = mem[k] || ''; }); cb(f, null, o); return api; },
      removeItem: function (k, f) { if (guard(k)) { delete mem[k]; log('storage', name + '.removeItem', k); changed(); cb(f, null, true); } return api; },
      removeItems: function (ks, f) { ks.forEach(function (k) { delete mem[k]; }); log('storage', name + '.removeItems', ks); changed(); cb(f, null, true); return api; },
      getKeys: function (f) { cb(f, null, Object.keys(mem)); return api; },
      clear: function (f) { Object.keys(mem).forEach(function (k) { delete mem[k]; }); log('storage', name + '.clear'); changed(); cb(f, null, true); return api; },
      restoreItem: function (k, f) { cb(f, 'RESTORE_DECLINED'); return api; }
    };
    return api;
  }

  function bottomButton(type) {
    var main = type === 'main';
    var s = { type: type, text: main ? 'Continue' : 'Cancel', color: null, textColor: null, isVisible: false,
              isActive: true, isProgressVisible: false, hasShineEffect: false, position: 'left', iconCustomEmojiId: '' };
    var evt = main ? 'mainButtonClicked' : 'secondaryButtonClicked';
    var b = {
      setParams: function (p) {
        if (!main && !ok('WebApp.SecondaryButton', 'SecondaryButton')) return b;
        if ('text' in p) s.text = String(p.text).trim();
        if ('color' in p) s.color = p.color;
        if ('text_color' in p) s.textColor = p.text_color;
        if ('is_visible' in p) s.isVisible = !!p.is_visible;
        if ('is_active' in p) s.isActive = !!p.is_active;
        if ('has_shine_effect' in p && cmp(version, '7.10')) s.hasShineEffect = !!p.has_shine_effect;
        if ('position' in p && cmp(version, '7.10')) s.position = p.position;
        if ('icon_custom_emoji_id' in p && cmp(version, '9.5')) s.iconCustomEmojiId = p.icon_custom_emoji_id;
        if (s.isVisible && !s.text) { console.error('[Telegram.WebApp] Bottom button text is required'); throw Error('WebAppBottomButtonParamInvalid'); }
        post('button', s); return b;
      },
      setText: function (t) { return b.setParams({ text: t }); },
      show: function () { return b.setParams({ is_visible: true }); },
      hide: function () { return b.setParams({ is_visible: false }); },
      enable: function () { return b.setParams({ is_active: true }); },
      disable: function () { return b.setParams({ is_active: false }); },
      showProgress: function () { s.isProgressVisible = true; post('button', s); return b; },
      hideProgress: function () { s.isProgressVisible = false; post('button', s); return b; },
      onClick: function (cb) { WebApp.onEvent(evt, cb); return b; },
      offClick: function (cb) { WebApp.offEvent(evt, cb); return b; }
    };
    Object.keys(s).forEach(function (k) { Object.defineProperty(b, k, { get: function () { return s[k]; }, enumerable: true }); });
    return b;
  }
  function headerButton(kind, since, evt) {
    var visible = false;
    var b = {
      show: function () { if (ok('WebApp.' + kind, kind)) { visible = true; post('header', { kind: kind, visible: true }); } return b; },
      hide: function () { if (ok('WebApp.' + kind, kind)) { visible = false; post('header', { kind: kind, visible: false }); } return b; },
      onClick: function (cb) { WebApp.onEvent(evt, cb); return b; },
      offClick: function (cb) { WebApp.offEvent(evt, cb); return b; }
    };
    Object.defineProperty(b, 'isVisible', { get: function () { return visible; } });
    return b;
  }

  var popupCb = null;
  function popup(params, cb) {
    if (!params || typeof params.message !== 'string' || !params.message.length || params.message.length > 256)
      throw Error('WebAppPopupParamInvalid');
    if (params.title && params.title.length > 64) throw Error('WebAppPopupParamInvalid');
    var buttons = params.buttons && params.buttons.length ? params.buttons : [{ type: 'close' }];
    if (buttons.length > 3) throw Error('WebAppPopupParamInvalid');
    if (popupCb) throw Error('WebAppPopupOpened');
    popupCb = cb || function () {};
    post('popup', { title: params.title || '', message: params.message, buttons: buttons });
  }

  var unsafe = {};
  new URLSearchParams(initData).forEach(function (v, k) { try { unsafe[k] = /^[\[{]/.test(v) ? JSON.parse(v) : v; } catch (e) { unsafe[k] = v; } });
  var fullscreen = !!cfg.fullscreen, closingConfirm = false, swipes = true, headerColor = null, bgColor = null, barColor = null;
  var callLog = function (name) { return function () { log('call', name, Array.prototype.slice.call(arguments).filter(function (a) { return typeof a !== 'function'; })); }; };

  var WebApp = {
    initData: initData, initDataUnsafe: unsafe, version: version, platform: platform,
    get colorScheme() { return colorScheme; }, get themeParams() { return themeParams; },
    get isExpanded() { return cfg.mode !== 'compact'; },
    get viewportHeight() { return window.innerHeight; }, get viewportStableHeight() { return window.innerHeight; },
    get isFullscreen() { return fullscreen; }, isActive: true, isOrientationLocked: false,
    get safeAreaInset() { return safe; }, get contentSafeAreaInset() { return content; },
    get isClosingConfirmationEnabled() { return closingConfirm; }, get isVerticalSwipesEnabled() { return swipes; },
    get headerColor() { return headerColor; }, get backgroundColor() { return bgColor; }, get bottomBarColor() { return barColor; },
    isVersionAtLeast: function (v) { return cmp(version, v); },
    onEvent: function (n, cb) { (handlers[n] = handlers[n] || []).push(cb); },
    offEvent: function (n, cb) { handlers[n] = (handlers[n] || []).filter(function (f) { return f !== cb; }); },
    ready: function () {
      var ms = Math.round(performance.now());
      log('call', 'ready', ms + ' ms after navigation start'); post('ready', { ms: ms });
      if (cfg.audit) setTimeout(function () { window.tmaAudit(); }, 800);
    },
    expand: function () { log('call', 'expand'); post('expand'); },
    close: function () { log('call', 'close'); post('close'); },
    sendData: function (d) { if (String(d).length > 4096) throw Error('WebAppDataInvalid'); log('call', 'sendData', d); post('close'); },
    setHeaderColor: function (c) { if (ok('WebApp.setHeaderColor', 'setHeaderColor')) { headerColor = keyword(c); post('chrome', { header: headerColor, headerKey: c }); log('chrome', 'setHeaderColor', c); } },
    setBackgroundColor: function (c) { if (ok('WebApp.setBackgroundColor', 'Background color')) { bgColor = keyword(c); post('chrome', { background: bgColor, backgroundKey: c }); log('chrome', 'setBackgroundColor', c); } },
    setBottomBarColor: function (c) { if (ok('WebApp.setBottomBarColor', 'Bottom bar color')) { barColor = keyword(c); post('chrome', { bottomBar: barColor, bottomBarKey: c }); log('chrome', 'setBottomBarColor', c); } },
    enableClosingConfirmation: function () { if (ok('WebApp.enableClosingConfirmation', 'Closing confirmation')) { closingConfirm = true; log('call', 'enableClosingConfirmation'); post('flags', { closingConfirmation: true }); } },
    disableClosingConfirmation: function () { if (ok('WebApp.disableClosingConfirmation', 'Closing confirmation')) { closingConfirm = false; log('call', 'disableClosingConfirmation'); post('flags', { closingConfirmation: false }); } },
    enableVerticalSwipes: function () { if (ok('WebApp.enableVerticalSwipes', 'Changing swipes behavior')) { swipes = true; log('call', 'enableVerticalSwipes'); post('flags', { verticalSwipes: true }); } },
    disableVerticalSwipes: function () { if (ok('WebApp.disableVerticalSwipes', 'Changing swipes behavior')) { swipes = false; log('call', 'disableVerticalSwipes'); post('flags', { verticalSwipes: false }); } },
    requestFullscreen: function () { ok('WebApp.requestFullscreen', 'requestFullscreen'); log('call', 'requestFullscreen'); post('fullscreen', true); },
    exitFullscreen: function () { ok('WebApp.exitFullscreen', 'exitFullscreen'); log('call', 'exitFullscreen'); post('fullscreen', false); },
    lockOrientation: function () { if (ok('WebApp.lockOrientation', 'lockOrientation')) { log('call', 'lockOrientation'); post('flags', { orientationLocked: true }); } },
    unlockOrientation: function () { if (ok('WebApp.unlockOrientation', 'unlockOrientation')) { log('call', 'unlockOrientation'); post('flags', { orientationLocked: false }); } },
    hideKeyboard: function () { if (ok('WebApp.hideKeyboard', 'hideKeyboard')) { log('call', 'hideKeyboard'); if (document.activeElement) document.activeElement.blur(); } },
    showPopup: function (p, cb) { ok('WebApp.showPopup', 'showPopup'); popup(p, cb); },
    showAlert: function (m, cb) { ok('WebApp.showAlert', 'showAlert'); popup({ message: m, buttons: [{ type: 'close' }] }, function () { cb && cb(); }); },
    showConfirm: function (m, cb) { ok('WebApp.showConfirm', 'showConfirm'); popup({ message: m, buttons: [{ type: 'ok', id: 'ok' }, { type: 'cancel' }] }, function (id) { cb && cb(id === 'ok'); }); },
    showScanQrPopup: function (p) { ok('WebApp.showScanQrPopup', 'showScanQrPopup'); log('call', 'showScanQrPopup', p && p.text); },
    closeScanQrPopup: function () { ok('WebApp.closeScanQrPopup', 'closeScanQrPopup'); },
    openLink: function (u, o) { ok('WebApp.openLink', 'openLink'); log('link', 'openLink', u); },
    openTelegramLink: function (u) { ok('WebApp.openTelegramLink', 'openTelegramLink'); log('link', 'openTelegramLink', u); },
    openInvoice: function (u, cb) {
      ok('WebApp.openInvoice', 'openInvoice');
      var status = ['paid', 'cancelled', 'failed', 'pending'].indexOf(cfg.invoice) >= 0 ? cfg.invoice : 'cancelled';
      log('payment', 'openInvoice (mock: no money moves; status ' + status + ')', u);
      setTimeout(function () { emit('invoiceClosed', { url: u, status: status }); cb && cb(status); }, 300);
    },
    shareMessage: function (id, cb) { ok('WebApp.shareMessage', 'shareMessage'); log('call', 'shareMessage', id); setTimeout(function () { emit('shareMessageSent'); cb && cb(true); }, 200); },
    shareToStory: function (u, p) { ok('WebApp.shareToStory', 'shareToStory'); log('call', 'shareToStory', u); },
    switchInlineQuery: function (q, t) { ok('WebApp.switchInlineQuery', 'switchInlineQuery'); log('call', 'switchInlineQuery', [q, t]); },
    requestWriteAccess: function (cb) { ok('WebApp.requestWriteAccess', 'requestWriteAccess'); log('call', 'requestWriteAccess', 'mock: allowed'); setTimeout(function () { emit('writeAccessRequested', { status: 'allowed' }); cb && cb(true); }, 200); },
    requestContact: function (cb) { ok('WebApp.requestContact', 'requestContact'); log('call', 'requestContact', 'mock: cancelled'); setTimeout(function () { emit('contactRequested', { status: 'cancelled' }); cb && cb(false); }, 200); },
    requestChat: function (id, cb) { ok('WebApp.requestChat', 'requestChat'); log('call', 'requestChat', id); setTimeout(function () { cb && cb(false); }, 200); },
    setEmojiStatus: function (id, p, cb) { ok('WebApp.setEmojiStatus', 'setEmojiStatus'); log('call', 'setEmojiStatus', id); },
    requestEmojiStatusAccess: function (cb) { ok('WebApp.requestEmojiStatusAccess', 'requestEmojiStatusAccess'); log('call', 'requestEmojiStatusAccess'); },
    downloadFile: function (p, cb) { ok('WebApp.downloadFile', 'downloadFile'); log('call', 'downloadFile', p && p.file_name); },
    addToHomeScreen: function () { ok('WebApp.addToHomeScreen', 'addToHomeScreen'); log('call', 'addToHomeScreen'); },
    checkHomeScreenStatus: function (cb) { ok('WebApp.checkHomeScreenStatus', 'checkHomeScreenStatus'); setTimeout(function () { cb && cb('unknown'); }, 0); },
    readTextFromClipboard: function (cb) { ok('WebApp.readTextFromClipboard', 'readTextFromClipboard'); log('call', 'readTextFromClipboard', 'attachment-menu apps only'); },
    MainButton: bottomButton('main'),
    SecondaryButton: bottomButton('secondary'),
    BackButton: headerButton('BackButton', '6.1', 'backButtonClicked'),
    SettingsButton: headerButton('SettingsButton', '7.0', 'settingsButtonClicked'),
    HapticFeedback: {
      impactOccurred: function (s) { if (ok('WebApp.HapticFeedback', 'HapticFeedback')) log('haptic', 'impactOccurred', s); return this; },
      notificationOccurred: function (t) { if (ok('WebApp.HapticFeedback', 'HapticFeedback')) log('haptic', 'notificationOccurred', t); return this; },
      selectionChanged: function () { if (ok('WebApp.HapticFeedback', 'HapticFeedback')) log('haptic', 'selectionChanged'); return this; }
    },
    CloudStorage: storage('CloudStorage', '6.9', true),
    DeviceStorage: storage('DeviceStorage', '9.0', false),
    SecureStorage: storage('SecureStorage', '9.0', false),
    Accelerometer: sensor('Accelerometer', 'accelerometer', function (t) { return { x: 0.6 * Math.sin(t), y: 9.6 + 0.2 * Math.cos(t), z: 0.8 * Math.cos(t * 0.7) }; }),
    Gyroscope: sensor('Gyroscope', 'gyroscope', function (t) { return { x: 0.3 * Math.cos(t), y: 0.2 * Math.sin(t * 1.3), z: 0.05 * Math.sin(t) }; }),
    DeviceOrientation: sensor('DeviceOrientation', 'deviceOrientation', function (t) { return { alpha: (t * 0.2) % (2 * Math.PI), beta: 0.35 * Math.sin(t), gamma: 0.3 * Math.cos(t * 0.8), absolute: false }; }),
    LocationManager: {
      isInited: false, isLocationAvailable: true, isAccessRequested: false, isAccessGranted: false,
      init: function (cb) { if (!ok('WebApp.LocationManager', 'LocationManager')) return this; var m = this; setTimeout(function () { m.isInited = true; emit('locationManagerUpdated'); cb && cb(); }, 0); log('call', 'LocationManager.init'); return this; },
      getLocation: function (cb) {
        if (!ok('WebApp.LocationManager', 'LocationManager')) return this;
        var m = this; m.isAccessRequested = true; m.isAccessGranted = true;
        log('call', 'LocationManager.getLocation', 'mock grants access; demo coordinates');
        setTimeout(function () { var d = { latitude: 52.3702, longitude: 4.8952, altitude: null, course: null, speed: null, horizontal_accuracy: 25, vertical_accuracy: null, course_accuracy: null, speed_accuracy: null }; emit('locationRequested', { locationData: d }); cb && cb(d); }, 400);
        return this;
      },
      openSettings: function () { log('call', 'LocationManager.openSettings', 'needs a user gesture on real clients'); }
    }
  };
  // motion sensors (8.0): smooth synthetic readings at the requested refresh rate; stopped while the app is hidden
  function sensor(name, ev, reading) {
    var timer = null;
    var o = {
      isStarted: false,
      start: function (p, cb) {
        if (!ok('WebApp.' + name, name)) { cb && cb(false); return o; }
        var rate = Math.min(1000, Math.max(20, (p && p.refresh_rate) || 1000));
        if (timer) clearInterval(timer);
        var t0 = Date.now();
        o.isStarted = true; emit(ev + 'Started'); log('call', name + '.start', 'refresh_rate ' + rate);
        timer = setInterval(function () { var r = reading((Date.now() - t0) / 1000); for (var k in r) o[k] = r[k]; emit(ev + 'Changed'); }, rate);
        cb && cb(true); return o;
      },
      stop: function (cb) { if (timer) clearInterval(timer); timer = null; o.isStarted = false; emit(ev + 'Stopped'); log('call', name + '.stop'); cb && cb(true); return o; }
    };
    return o;
  }
  if (cfg.serverless) {
    WebApp.Serverless = { call: function (name, input, cb) { log('call', 'Serverless.call', name); setTimeout(function () { var e = Error('mock: no endpoint'); e.type = 'ENDPOINT_ERROR'; e.status = 0; cb && cb(e); }, 100); } };
  }

  window.addEventListener('message', function (ev) {
    var m = ev.data;
    if (!m || m.__tma !== 1 || ev.source !== window.parent) return;
    if (m.type === 'event') {
      if (m.name === 'popupClosed' && popupCb) { var f = popupCb; popupCb = null; f(m.data && m.data.button_id); }
      emit(m.name, m.data);
    } else if (m.type === 'state') {
      if (m.data.themeParams) { themeParams = m.data.themeParams; colorScheme = m.data.colorScheme; applyTheme(); emit('themeChanged'); }
      if (m.data.safe) { safe = m.data.safe; content = m.data.content; if (cmp(version, '8.0')) { applyInsets(); emit('safeAreaChanged'); emit('contentSafeAreaChanged'); } }
      if ('fullscreen' in m.data) { fullscreen = m.data.fullscreen; emit('fullscreenChanged'); }
      if ('active' in m.data) { WebApp.isActive = m.data.active; emit(m.data.active ? 'activated' : 'deactivated'); }
      // settings the stand changes while the app runs: the next request, invoice or read sees them
      if ('mode' in m.data) cfg.mode = m.data.mode;
      if ('network' in m.data) cfg.network = m.data.network;
      if ('invoice' in m.data) cfg.invoice = m.data.invoice;
      if ('style' in m.data) { cfg.style = m.data.style; if (cfg.style) root.setAttribute('data-tma-style', cfg.style); else root.removeAttribute('data-tma-style'); }
      if (m.data.storage) Object.keys(m.data.storage).forEach(function (n) {
        var mem = store[n]; if (!mem) return;
        Object.keys(mem).forEach(function (k) { delete mem[k]; });
        Object.assign(mem, m.data.storage[n]);
      });
    }
  });
  window.Telegram = { WebApp: WebApp, WebView: { isIframe: inStand, initParams: {} }, Utils: {} };
  // the stand's --api mock answers order status from the selected invoice outcome
  if (window.fetch) {
    var realFetch = window.fetch, netCount = 0, netId = 0;
    window.fetch = function (input, init) {
      init = init || {};
      var headers = new Headers(init.headers || (input && input.headers) || {});
      headers.set('X-TMA-Mock-Invoice', cfg.invoice || 'cancelled');
      init.headers = headers;
      var raw = typeof input === 'string' ? input : (input && input.url) || String(input);
      var url = new URL(raw, location.href);
      var method = String(init.method || (input && input.method) || 'GET').toUpperCase();
      var shown = url.origin === location.origin ? url.pathname + url.search : url.href;
      var id = ++netId, t0 = performance.now(), self = this;
      // the stand's Network panel shows each request while it runs and how it ended
      function done(status, note) { post('net', { id: id, phase: 'end', method: method, url: shown, status: status, ms: Math.round(performance.now() - t0), note: note || '' }); }
      post('net', { id: id, phase: 'start', method: method, url: shown });
      // the stand's Network control breaks the app's own requests (not its files under /app/)
      var own = url.origin === location.origin && url.pathname.indexOf('/app/') !== 0 && url.pathname.indexOf('/__tma__') !== 0;
      var net = cfg.network || 'normal';
      function real(note) {
        return realFetch.call(self, input, init).then(function (r) { done(r.status, note); return r; },
          function (e) { done('failed', e && e.message); throw e; });
      }
      if (own && net !== 'normal') {
        netCount++;
        var json = function (code, body) { return new Response(JSON.stringify(body), { status: code, headers: { 'Content-Type': 'application/json' } }); };
        if (net === 'offline' || (net === 'flaky' && netCount % 2 === 1)) {
          done('failed', 'mock ' + net + ': the request fails like a lost connection');
          return Promise.reject(new TypeError('Failed to fetch'));
        }
        if (net === 'error') { done(500, 'mock server error'); return Promise.resolve(json(500, { reason: 'Mock server error' })); }
        if (net === 'session') { done(401, 'mock: initData too old'); return Promise.resolve(json(401, { reason: 'session-expired' })); }
        if (net === 'slow') return new Promise(function (r) { setTimeout(r, 3000); }).then(function () { return real('mock slow: held 3 s'); });
      }
      return real('');
    };
  }
  // Layout audit (?audit=1 on the stand): geometry of the screen as drawn, see tma-audit.mjs
  window.tmaAudit = function (opts) {
    var outline = !opts || opts.outline !== false;
    // a second run starts clean: drop the outlines of the first
    Array.prototype.forEach.call(document.querySelectorAll('[style*="dashed"]'), function (el) {
      if (/dashed/.test(el.style.outline)) el.style.outline = '';
    });
    return import('/__tma__/audit.mjs?v=' + Date.now()).then(function (m) {  // fresh after an edit to the rules
      var r = m.audit(document, { outline: outline });
      window.__tmaAudit = r;
      r.findings.forEach(function (f) { log('layout', f.rule + ' ' + f.level, f.msg); });
      log('layout', 'audit', r.errors + ' error(s), ' + r.warnings + ' warning(s) on ' + r.surfaces + ' surfaces');
      post('audit', { surfaces: r.surfaces, errors: r.errors, warnings: r.warnings,
        findings: r.findings.map(function (f) { return { rule: f.rule, level: f.level, msg: f.msg }; }) });
      return r;
    }, function (e) { log('error', 'layout audit', e && e.message); throw e; });
  };
  post('loaded', { version: version, platform: platform });
})();
"""

# --------------------------------------------------------------------------- stand (the "client" page)

# The stand page lives in preview_stand/ (HTML, CSS, JS, no build step, no network); stand_html() fills its config.
STAND_DIR = os.path.join(SKILL, "scripts", "preview_stand")
STAND_ASSETS = {"/__tma__/stand.css": ("stand.css", "text/css; charset=utf-8"),
                "/__tma__/stand.js": ("stand.js", "text/javascript; charset=utf-8")}


# --------------------------------------------------------------------------- server

def find_entry(app: str) -> str:
    path = os.path.abspath(app)
    if os.path.isdir(path):
        path = os.path.join(path, "index.html")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no Mini App entry at {path}")
    return path


def rewrite_html(html: str) -> str:
    """Swap Telegram's script for the local mock; leave everything else untouched."""
    return SCRIPT_TAG.sub(MOCK_TAG, html, count=1)


def check_entry(html: str) -> list[str]:
    """Static checks the stand can make without a browser."""
    problems = []
    head = html.split("</head>", 1)[0]
    m = SCRIPT_TAG.search(head)
    if not m:
        problems.append("telegram-web-app.js is not loaded in <head>")
    else:
        before = head[:m.start()]
        if re.search(r"<script\b", before, re.I):
            problems.append("another <script> runs before telegram-web-app.js (load Telegram's script first)")
    if not re.search(r'name=["\']viewport["\']', head):
        problems.append("no <meta name=\"viewport\">")
    return problems


def safe_path(root: str, rel: str) -> str | None:
    """Resolve a URL path inside root; None for anything that escapes it."""
    rel = urllib.parse.unquote(rel)
    # No backslashes, NULs, drive letters or UNC forms: on Windows os.path.join would replace the root, and
    # realpath would touch the outside path before the containment check.
    if any(c in rel for c in ("\\", "\x00", ":")) or rel.startswith("//"):
        return None
    rel = rel.lstrip("/")
    if any(part.startswith(".") for part in rel.split("/") if part):
        return None  # dotfiles and dot-folders (.env, .git) are never served
    full = os.path.realpath(os.path.join(root, *[p for p in rel.split("/") if p not in ("", ".")]))
    root_real = os.path.realpath(root)
    if full != root_real and not full.startswith(root_real + os.sep):
        return None
    return full


def stand_html(app_url: str, title: str) -> str:
    with open(CATALOG, encoding="utf-8") as fh:
        meta = json.load(fh)["meta"]
    versions = ["6.0", "6.1", "6.2", "6.9", "7.0", "7.2", "7.10", "8.0", "9.0", "9.5", "9.6", "10.1"]
    # The title stays raw text: the page only ever sets it as text. Escaping "<" keeps the JSON inside its
    # <script type="application/json"> block whatever the app's <title> holds.
    config = {"app": app_url, "title": title, "themes": THEMES, "devices": DEVICES,
              "heights": {str(k): v for k, v in HEIGHTS.items()}, "versions": versions,
              "catalog": {"fetched_at": meta["fetched_at"], "newest": meta["newest_member_version"]}}
    with open(os.path.join(STAND_DIR, "stand.html"), encoding="utf-8") as fh:
        page = fh.read()
    return page.replace("__CONFIG__", json.dumps(config).replace("<", "\\u003c"), 1)


def mock_js() -> str:
    return MOCK_JS.replace("__GATES__", json.dumps(gates(), sort_keys=True)).replace("__THROWING__", json.dumps(THROWING))


class StandServer(ThreadingHTTPServer):
    # On Windows SO_REUSEADDR lets a second server bind a busy port silently; fail loudly instead.
    allow_reuse_address = os.name != "nt"


def load_api(path: str | None) -> list[tuple[str, re.Pattern, dict]]:
    """--api file: [(method, path regex, response)]. `*` matches one path segment."""
    if not path:
        return []
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    routes = []
    for key, resp in data.items():
        if key.startswith("$"):
            continue
        method, _, pattern = key.partition(" ")
        if not pattern.startswith("/") or not isinstance(resp, dict):
            raise ValueError(f"--api: bad route {key!r} (expected \"METHOD /path\": {{...}})")
        rx = re.compile("^" + "/".join("[^/]+" if part == "*" else re.escape(part) for part in pattern.split("/")) + "$")
        routes.append((method.upper(), rx, resp))
    return routes


ORDER_STATUS = {"paid": "paid", "failed": "failed"}


def mock_response(resp: dict, invoice: str) -> tuple[int, bytes]:
    body = json.dumps(resp.get("body", {})).replace('"$order_status"', json.dumps(ORDER_STATUS.get(invoice, "open")))
    return int(resp.get("status", 200)), body.encode()


def make_handler(root: str, app_rel: str, title: str, api: list | None = None):
    app_url = "/app/" + app_rel.replace(os.sep, "/")
    api = api or []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _host_ok(self) -> bool:
            # DNS rebinding guard: only answer requests addressed to the loopback name we serve on.
            port = self.server.server_address[1]
            return (self.headers.get("Host") or "") in (f"127.0.0.1:{port}", f"localhost:{port}")

        def _api(self, method: str, path: str) -> bool:
            for m, rx, resp in api:
                if m == method and rx.match(path):
                    length = int(self.headers.get("Content-Length") or 0)
                    if length:
                        self.rfile.read(min(length, 1 << 20))
                    if resp.get("delay_ms"):
                        time.sleep(min(int(resp["delay_ms"]), 5000) / 1000)
                    code, body = mock_response(resp, self.headers.get("X-TMA-Mock-Invoice") or "")
                    self._send(code, body, "application/json")
                    return True
            return False

        def _other(self, method: str) -> None:
            if not self._host_ok():
                return self._send(403, b"forbidden host", "text/plain")
            path = urllib.parse.urlsplit(self.path).path
            if not self._api(method, path):
                self._send(501, f"no mock for {method} {path}: pass --api mock.json".encode(), "text/plain")

        def do_POST(self):  # noqa: N802
            self._other("POST")

        def do_PUT(self):  # noqa: N802
            self._other("PUT")

        def do_PATCH(self):  # noqa: N802
            self._other("PATCH")

        def do_DELETE(self):  # noqa: N802
            self._other("DELETE")

        def do_GET(self):  # noqa: N802
            if not self._host_ok():
                return self._send(403, b"forbidden host", "text/plain")
            path = urllib.parse.urlsplit(self.path).path
            if not path.startswith(("/app/", "/__tma__/")) and path not in ("/", "/index.html") \
                    and self._api("GET", path):
                return None
            if path in ("/", "/index.html"):
                return self._send(200, stand_html(app_url, title).encode(), "text/html; charset=utf-8")
            if path in STAND_ASSETS:
                name, ctype = STAND_ASSETS[path]
                with open(os.path.join(STAND_DIR, name), "rb") as fh:
                    return self._send(200, fh.read(), ctype)
            if path == "/__tma__/mock.js":
                return self._send(200, mock_js().encode(), "text/javascript; charset=utf-8")
            if path == "/__tma__/audit.mjs":
                with open(AUDIT_JS, "rb") as fh:
                    return self._send(200, fh.read(), "text/javascript; charset=utf-8")
            if path.startswith("/app/"):
                full = safe_path(root, path[len("/app/"):])
                if not full or not os.path.isfile(full):
                    return self._send(404, b"not found", "text/plain")
                with open(full, "rb") as fh:
                    body = fh.read()
                ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
                if full.endswith((".js", ".mjs")):
                    ctype = "text/javascript"
                if full.endswith(".html"):
                    body = rewrite_html(body.decode("utf-8")).encode("utf-8")
                    ctype = "text/html"
                if ctype.startswith("text/") and "charset" not in ctype:
                    ctype += "; charset=utf-8"
                return self._send(200, body, ctype)
            return self._send(404, b"not found", "text/plain")

    return Handler


def build_if_needed(root: str) -> str | None:
    """Run `node build.mjs` in the served folder when it has one. Returns a warning or None."""
    if not os.path.isfile(os.path.join(root, "build.mjs")):
        return None
    node = shutil.which("node")
    if not node:
        return "node not found: dist/ files may be missing or stale (install Node >= 22.18 and run node build.mjs)"
    res = subprocess.run([node, "build.mjs"], cwd=root, capture_output=True, text=True)
    if res.returncode:
        return f"node build.mjs failed: {res.stderr.strip()[:300]}"
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mini App preview stand (mock Telegram client)")
    ap.add_argument("app", help="the Mini App folder (with index.html) or its HTML entry")
    ap.add_argument("--root", help="folder to serve (default: the app folder, or its parent in a kit project "
                                   "with ../_kit or build.mjs); dotfiles are never served")
    ap.add_argument("--serve", type=int, metavar="PORT", help="serve on 127.0.0.1:PORT")
    ap.add_argument("--title", default=None, help="bot name in the mock header")
    ap.add_argument("--build", action="store_true",
                    help="run the folder's node build.mjs first (it is the project's own code: only for a project you trust)")
    ap.add_argument("--no-build", action="store_true", help=argparse.SUPPRESS)  # the old default; kept so old commands still parse
    ap.add_argument("--check", action="store_true", help="static checks of the entry, no server")
    ap.add_argument("--api", metavar="FILE", help="JSON mock of the app's own API (see the module docstring)")
    args = ap.parse_args(argv)

    entry = find_entry(args.app)
    app_dir = os.path.dirname(entry)
    parent = os.path.dirname(app_dir)
    # Serve the parent only for a kit project (shared ../_kit or a build.mjs); otherwise just the app's folder.
    kit_project = os.path.isdir(os.path.join(parent, "_kit")) or os.path.isfile(os.path.join(parent, "build.mjs"))
    root = os.path.abspath(args.root) if args.root else (parent if kit_project else app_dir)
    if safe_path(root, os.path.relpath(entry, root).replace(os.sep, "/")) is None:
        print(f"the entry {entry} is outside --root {root}")
        return 2
    with open(entry, encoding="utf-8") as fh:
        html = fh.read()
    problems = check_entry(html)
    title = args.title or (re.search(r"<title>(.*?)</title>", html, re.S | re.I) or [None, "Mini App"])[1].strip()

    if args.check or not args.serve:
        for p in problems:
            print(f"WARN: {p}")
        print(f"entry {os.path.relpath(entry, root)} under {root}; {len(problems)} warning(s); "
              f"mock covers {len(gates())} version-gated members")
        if not args.serve:
            print("add --serve PORT to open the stand")
        return 1 if problems else 0

    warn = build_if_needed(root) if args.build and not args.no_build else (
        "build.mjs not run (pass --build for a project you trust): dist/ may be stale"
        if os.path.isfile(os.path.join(root, "build.mjs")) else None)
    if warn:
        print(f"WARN: {warn}")
    try:
        server = StandServer(("127.0.0.1", args.serve), make_handler(root, os.path.relpath(entry, root), title, load_api(args.api)))
    except OSError as exc:
        print(f"port {args.serve} is busy ({exc.strerror}); stop the other stand or pick another port")
        return 2
    print(f"Mini App preview (MOCK) on http://127.0.0.1:{server.server_address[1]}/  "
          f"(matrix: /?view=matrix). Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
