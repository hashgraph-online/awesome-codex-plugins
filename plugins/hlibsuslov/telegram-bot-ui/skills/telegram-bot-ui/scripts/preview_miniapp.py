#!/usr/bin/env python3
"""Local preview stand for a Telegram Mini App inside a MOCK of the Telegram client.

  py -3 scripts/preview_miniapp.py examples/mini-apps/vanilla --serve 8790
      open http://127.0.0.1:8790/                 one device with Telegram chrome, controls, call log
      open http://127.0.0.1:8790/?view=matrix     iOS/Android x light/dark x 320/390/430 + fullscreen
      open http://127.0.0.1:8790/?platform=android&scheme=dark&width=390&mode=fullscreen&version=8.0
      add &height=1600 for a taller device (long screens in one screenshot)
      add &audit=1 to measure the layout after ready(): gaps between surfaces, text inset, radii
      (examples/mini-apps/_kit/tma-audit.mjs, rules LA01-LA05); findings go to the call log, the surfaces get
      a dashed outline, window.__tmaAudit holds the result and window.tmaAudit() re-runs it on the current screen
  py -3 scripts/preview_miniapp.py examples/mini-apps/vanilla --check   # static checks, no server

The stand serves the app's folder (by default its parent, so `../_kit/tma.css` resolves) on
127.0.0.1 only, replaces the `telegram-web-app.js` script tag with a local mock of
`window.Telegram.WebApp`, and draws what Telegram draws around a Mini App: the status bar, the
header (Close or Back, title, menu), the bottom bar with MainButton / SecondaryButton, native
popups, the fullscreen controls and safe areas. Controls: platform, colour scheme, width, mode
(compact, full, fullscreen), client version, Android performance class, motion sensors and location
(synthetic readings and demo coordinates), the user's language_code (en, ru, uk, de, ar, he, fa),
the network for the app's own requests (slow 3 s, flaky, offline, 500, 401: `?network=offline`), style preset (to see any
app in native / fintech / soft / dense), the invoice outcome (paid, cancelled, failed, pending:
`?invoice=paid`), start_param. Every call
(haptics, popups, chrome colours, storage, links, unsupported members) is logged.

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
import html
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
  var store = {};
  function storage(name, since, limits) {
    var mem = store[name] = {};
    function cb(f, a, b) { setTimeout(function () { f && f(a, b); }, 0); }
    function guard(key) {
      if (!ok('WebApp.' + name, name)) return false;
      if (limits && !/^[A-Za-z0-9_-]{1,128}$/.test(key)) throw Error('WebAppStorageKeyInvalid');
      return true;
    }
    var api = {
      setItem: function (k, v, f) {
        if (!guard(k)) return api;
        if (limits && String(v).length > 4096) { cb(f, 'VALUE_TOO_LONG'); return api; }
        mem[k] = String(v); log('storage', name + '.setItem', k); cb(f, null, true); return api;
      },
      getItem: function (k, f) { if (guard(k)) cb(f, null, k in mem ? mem[k] : (limits ? '' : null)); return api; },
      getItems: function (ks, f) { var o = {}; ks.forEach(function (k) { o[k] = mem[k] || ''; }); cb(f, null, o); return api; },
      removeItem: function (k, f) { if (guard(k)) { delete mem[k]; cb(f, null, true); } return api; },
      removeItems: function (ks, f) { ks.forEach(function (k) { delete mem[k]; }); cb(f, null, true); return api; },
      getKeys: function (f) { cb(f, null, Object.keys(mem)); return api; },
      clear: function (f) { Object.keys(mem).forEach(function (k) { delete mem[k]; }); cb(f, null, true); return api; },
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
      log('call', 'ready', Math.round(performance.now()) + ' ms after navigation start'); post('ready');
      if (cfg.audit) setTimeout(function () { window.tmaAudit(); }, 800);
    },
    expand: function () { log('call', 'expand'); post('expand'); },
    close: function () { log('call', 'close'); post('close'); },
    sendData: function (d) { if (String(d).length > 4096) throw Error('WebAppDataInvalid'); log('call', 'sendData', d); post('close'); },
    setHeaderColor: function (c) { if (ok('WebApp.setHeaderColor', 'setHeaderColor')) { headerColor = keyword(c); post('chrome', { header: headerColor, headerKey: c }); log('chrome', 'setHeaderColor', c); } },
    setBackgroundColor: function (c) { if (ok('WebApp.setBackgroundColor', 'Background color')) { bgColor = keyword(c); post('chrome', { background: bgColor, backgroundKey: c }); log('chrome', 'setBackgroundColor', c); } },
    setBottomBarColor: function (c) { if (ok('WebApp.setBottomBarColor', 'Bottom bar color')) { barColor = keyword(c); post('chrome', { bottomBar: barColor, bottomBarKey: c }); log('chrome', 'setBottomBarColor', c); } },
    enableClosingConfirmation: function () { if (ok('WebApp.enableClosingConfirmation', 'Closing confirmation')) { closingConfirm = true; log('call', 'enableClosingConfirmation'); } },
    disableClosingConfirmation: function () { if (ok('WebApp.disableClosingConfirmation', 'Closing confirmation')) { closingConfirm = false; log('call', 'disableClosingConfirmation'); } },
    enableVerticalSwipes: function () { if (ok('WebApp.enableVerticalSwipes', 'Changing swipes behavior')) { swipes = true; log('call', 'enableVerticalSwipes'); } },
    disableVerticalSwipes: function () { if (ok('WebApp.disableVerticalSwipes', 'Changing swipes behavior')) { swipes = false; log('call', 'disableVerticalSwipes'); } },
    requestFullscreen: function () { ok('WebApp.requestFullscreen', 'requestFullscreen'); post('fullscreen', true); },
    exitFullscreen: function () { ok('WebApp.exitFullscreen', 'exitFullscreen'); post('fullscreen', false); },
    lockOrientation: function () { if (ok('WebApp.lockOrientation', 'lockOrientation')) log('call', 'lockOrientation'); },
    unlockOrientation: function () { if (ok('WebApp.unlockOrientation', 'unlockOrientation')) log('call', 'unlockOrientation'); },
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
    }
  });
  window.Telegram = { WebApp: WebApp, WebView: { isIframe: inStand, initParams: {} }, Utils: {} };
  // the stand's --api mock answers order status from the selected invoice outcome
  if (window.fetch) {
    var realFetch = window.fetch, netCount = 0;
    window.fetch = function (input, init) {
      init = init || {};
      var headers = new Headers(init.headers || (input && input.headers) || {});
      headers.set('X-TMA-Mock-Invoice', cfg.invoice || 'cancelled');
      init.headers = headers;
      var raw = typeof input === 'string' ? input : input.url;
      log('network', (init.method || 'GET') + ' ' + raw);
      // the stand's Network control breaks the app's own requests (not its files under /app/)
      var url = new URL(raw, location.href);
      var own = url.origin === location.origin && url.pathname.indexOf('/app/') !== 0 && url.pathname.indexOf('/__tma__') !== 0;
      var net = cfg.network || 'normal';
      if (own && net !== 'normal') {
        netCount++;
        var json = function (code, body) { return new Response(JSON.stringify(body), { status: code, headers: { 'Content-Type': 'application/json' } }); };
        if (net === 'offline' || (net === 'flaky' && netCount % 2 === 1)) {
          log('network', 'mock ' + net + ': the request fails like a lost connection');
          return Promise.reject(new TypeError('Failed to fetch'));
        }
        if (net === 'error') { log('network', 'mock 500'); return Promise.resolve(json(500, { reason: 'Mock server error' })); }
        if (net === 'session') { log('network', 'mock 401: initData too old'); return Promise.resolve(json(401, { reason: 'session-expired' })); }
        if (net === 'slow') { var self = this; return new Promise(function (r) { setTimeout(r, 3000); }).then(function () { return realFetch.call(self, input, init); }); }
      }
      return realFetch.call(this, input, init);
    };
  }
  // Layout audit (?audit=1 on the stand): geometry of the screen as drawn, see tma-audit.mjs
  window.tmaAudit = function () {
    return import('/__tma__/audit.mjs?v=' + Date.now()).then(function (m) {  // fresh after an edit to the rules
      var r = m.audit(document, { outline: true });
      window.__tmaAudit = r;
      r.findings.forEach(function (f) { log('layout', f.rule + ' ' + f.level, f.msg); });
      log('layout', 'audit', r.errors + ' error(s), ' + r.warnings + ' warning(s) on ' + r.surfaces + ' surfaces');
      return r;
    });
  };
  post('loaded', { version: version, platform: platform });
})();
"""

# --------------------------------------------------------------------------- stand (the "client" page)

STAND_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mini App preview (mock)</title>
<style>
  :root { color-scheme: light; --ink: #1d1d1f; --muted: #6e6e73; --line: #d2d2d7; --panel: #ffffff; --page: #e9e9ee; }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--page); color: var(--ink); font: 13px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .bar { position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; gap: 10px 14px; align-items: center; padding: 10px 16px; background: var(--panel); border-bottom: 1px solid var(--line); }
  .bar label { display: flex; gap: 6px; align-items: center; color: var(--muted); }
  .bar select, .bar input, .bar button { font: inherit; padding: 4px 8px; border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--ink); }
  .bar .mock { margin-left: auto; color: #b25000; font-weight: 600; }
  .stage { display: flex; gap: 24px; align-items: flex-start; padding: 24px; flex-wrap: wrap; }
  .matrix { display: grid; gap: 28px 24px; padding: 24px; grid-template-columns: repeat(3, max-content); align-items: start; }
  .cap { margin: 0 0 6px; color: var(--muted); font-weight: 600; }
  .device { position: relative; overflow: hidden; border-radius: 44px; box-shadow: 0 0 0 10px #111, 0 18px 40px rgb(0 0 0 / .25); background: #000; }
  .device.android { border-radius: 28px; }
  .device.tdesktop { border-radius: 10px; box-shadow: 0 0 0 1px #999, 0 10px 30px rgb(0 0 0 / .2); }
  .status { position: absolute; inset: 0 0 auto 0; display: flex; justify-content: space-between; align-items: center; padding: 0 26px; font: 600 15px system-ui; z-index: 3; pointer-events: none; }
  .island { position: absolute; top: 11px; left: 50%; width: 120px; height: 34px; margin-left: -60px; border-radius: 20px; background: #000; z-index: 4; }
  .tgh { position: absolute; left: 0; right: 0; display: flex; align-items: center; gap: 8px; padding: 0 10px; z-index: 2; }
  .pill { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border-radius: 18px; font: 500 15px system-ui; border: 0; cursor: pointer; }
  .tgh .title { flex: 1; text-align: center; line-height: 1.1; }
  .tgh .title b { display: block; font: 600 15px system-ui; } .tgh .title i { font: 12px system-ui; font-style: normal; opacity: .6; }
  .android .tgh .title { text-align: left; }
  iframe { position: absolute; left: 0; width: 100%; border: 0; background: transparent; }
  .bb { position: absolute; left: 0; right: 0; display: flex; gap: 8px; padding: 8px 12px; z-index: 2; }
  .bb.stack { flex-direction: column; }
  .bb button { flex: 1; height: 48px; border: 0; border-radius: 14px; font: 600 16px system-ui; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; position: relative; overflow: hidden; }
  .ios .bb button { border-radius: 24px; }
  .bb button[disabled] { opacity: .5; cursor: default; }
  .spin { width: 18px; height: 18px; border-radius: 50%; border: 2px solid currentColor; border-top-color: transparent; animation: s .8s linear infinite; }
  @keyframes s { to { transform: rotate(1turn); } }
  .home { position: absolute; bottom: 8px; left: 50%; width: 134px; height: 5px; margin-left: -67px; border-radius: 3px; z-index: 4; pointer-events: none; }
  .scrim { position: absolute; inset: 0; z-index: 6; display: grid; place-items: center; background: rgb(0 0 0 / .35); }
  .dlg { width: min(280px, 80%); border-radius: 16px; overflow: hidden; text-align: center; font: 15px system-ui; }
  .dlg h4 { margin: 18px 16px 4px; font: 600 16px system-ui; } .dlg p { margin: 4px 16px 18px; }
  .dlg button { display: block; width: 100%; padding: 11px; border: 0; border-top: 1px solid rgb(128 128 128 / .3); background: none; font: inherit; cursor: pointer; }
  .log { width: 380px; max-height: 80vh; overflow: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; font: 12px ui-monospace, Menlo, Consolas, monospace; }
  .log div { padding: 3px 0; border-bottom: 1px solid #f0f0f2; } .log .unsupported { color: #c62828; } .log .haptic { color: #6a1b9a; } .log .chrome { color: #1565c0; }
  .note { max-width: 380px; color: var(--muted); }
</style></head>
<body>
<div class="bar" id="bar">
  <label>Platform <select id="c-platform"><option>ios</option><option>android</option><option>tdesktop</option></select></label>
  <label>Scheme <select id="c-scheme"><option>light</option><option>dark</option></select></label>
  <label>Width <select id="c-width"><option>320</option><option>375</option><option selected>390</option><option>430</option><option>384</option><option>669</option></select></label>
  <label>Mode <select id="c-mode"><option>full</option><option>compact</option><option>fullscreen</option></select></label>
  <label>Version <select id="c-version"></select></label>
  <label>Style <select id="c-style"><option value="">app's own</option><option>native</option><option>fintech</option><option>soft</option><option>dense</option></select></label>
  <label>Invoice <select id="c-invoice"><option>cancelled</option><option>paid</option><option>failed</option><option>pending</option></select></label>
  <label>Network <select id="c-network"><option>normal</option><option>slow</option><option>flaky</option><option>offline</option><option value="error">500</option><option value="session">401</option></select></label>
  <label>Language <select id="c-lang"><option>en</option><option>ru</option><option>uk</option><option>de</option><option>ar</option><option>he</option><option>fa</option></select></label>
  <label>Android class <select id="c-perf"><option>HIGH</option><option>AVERAGE</option><option>LOW</option></select></label>
  <label>start_param <input id="c-start" size="14" placeholder="none"></label>
  <button id="c-reload" type="button">Reload</button>
  <a id="c-matrix" href="?view=matrix">Matrix</a>
  <span class="mock">MOCK: not a Telegram client</span>
</div>
<div id="root"></div>
<script>
const CONFIG = __CONFIG__;
const qs = new URLSearchParams(location.search);
const $ = (id) => document.getElementById(id);
const verSel = $('c-version');
CONFIG.versions.forEach(v => { const o = document.createElement('option'); o.textContent = v; verSel.append(o); });
verSel.value = CONFIG.versions[CONFIG.versions.length - 1];
for (const k of ['platform', 'scheme', 'width', 'mode', 'version', 'perf', 'start', 'style', 'invoice', 'lang', 'network']) if (qs.get(k)) $('c-' + k).value = qs.get(k);

function themeFor(platform, scheme) { return CONFIG.themes[(platform === 'android' ? 'android' : 'ios') + '-' + scheme]; }
function demoInitData(start, lang) {
  const user = JSON.stringify({ id: 100000001, first_name: 'Demo', language_code: lang || 'en', allows_write_to_pm: true });
  const p = new URLSearchParams({ query_id: 'MOCK-QUERY', user, auth_date: String(Math.floor(Date.now() / 1000)), hash: 'mock-unsigned' });
  if (start) { p.set('start_param', start); p.set('chat_type', 'sender'); }
  return p.toString();
}

class Device {
  constructor(host, o) {
    this.o = o; this.dev = CONFIG.devices[o.platform];
    this.height = o.height || CONFIG.heights[o.width] || 800;
    this.fullscreen = o.mode === 'fullscreen';
    this.theme = themeFor(o.platform, o.scheme);
    this.chrome = { header: this.theme.header_bg_color, background: this.theme.secondary_bg_color, bottomBar: this.theme.bottom_bar_bg_color };
    this.buttons = { main: null, secondary: null }; this.back = false; this.settings = false;
    this.el = document.createElement('div');
    this.el.className = 'device ' + o.platform;
    this.el.style.width = o.width + 'px'; this.el.style.height = this.height + 'px';
    host.append(this.el);
    this.frame = document.createElement('iframe');
    this.frame.title = 'Mini App (' + o.platform + ', ' + o.scheme + ', ' + o.width + ' px)';
    this.el.append(this.frame);
    this.layout();
    this.frame.src = this.src();
    Device.all.push(this);
  }
  insets() {
    const d = this.dev;
    if (this.fullscreen) return { safe: { top: d.safe_fs.top, bottom: this.barVisible() ? 0 : d.safe_fs.bottom, left: 0, right: 0 }, content: { top: d.content_fs.top, bottom: 0, left: 0, right: 0 } };
    return { safe: { top: 0, bottom: this.barVisible() ? 0 : d.home, left: 0, right: 0 }, content: { top: 0, bottom: 0, left: 0, right: 0 } };
  }
  src() {
    const ins = this.insets();
    const p = new URLSearchParams({
      tgWebAppData: demoInitData(this.o.start, this.o.lang), tgWebAppVersion: this.o.version, tgWebAppPlatform: this.o.platform,
      tgWebAppThemeParams: JSON.stringify(this.theme),
      tgWebAppMock: JSON.stringify({ scheme: this.o.scheme, mode: this.o.mode, fullscreen: this.fullscreen, safe: ins.safe, content: ins.content, perf: this.o.perf, style: this.o.style === 'native' ? '' : this.o.style, invoice: this.o.invoice, network: this.o.network, audit: qs.get('audit') === '1' }),
    });
    if (this.fullscreen) p.set('tgWebAppFullscreen', '1');
    let url = CONFIG.app;
    if (this.o.start) url += (url.includes('?') ? '&' : '?') + 'tgWebAppStartParam=' + encodeURIComponent(this.o.start);
    return url + '#' + p.toString();
  }
  barVisible() { return !!((this.buttons.main && this.buttons.main.isVisible) || (this.buttons.secondary && this.buttons.secondary.isVisible)); }
  barHeight() {
    if (!this.barVisible()) return 0;
    const both = this.buttons.main?.isVisible && this.buttons.secondary?.isVisible;
    const stacked = both && ['top', 'bottom'].includes(this.buttons.secondary.position);
    return (stacked ? 120 : this.dev.bar) + this.dev.home;
  }
  layout() {
    const d = this.dev, H = this.height, light = this.o.scheme === 'light';
    this.el.querySelectorAll('.status,.island,.tgh,.bb,.home').forEach(n => n.remove());
    const fg = light ? '#000' : '#fff';
    let top = 0;
    if (d.status) {
      const st = document.createElement('div'); st.className = 'status'; st.style.height = d.status + 'px';
      st.style.color = this.fullscreen ? fg : this.textOn(this.chrome.header);
      st.innerHTML = '<span>9:41</span><span>' + (this.o.platform === 'ios' ? '5G ▮' : '▾ ▮') + '</span>';
      this.el.append(st);
      if (this.o.platform === 'ios') { const isl = document.createElement('div'); isl.className = 'island'; this.el.append(isl); }
    }
    const compact = this.o.mode === 'compact';
    const sheetTop = compact ? Math.round(H * 0.45) : 0;
    if (!this.fullscreen) {
      const h = document.createElement('div'); h.className = 'tgh';
      const headerTop = compact ? sheetTop : d.status;
      h.style.top = headerTop + 'px'; h.style.height = d.header + 'px'; h.style.background = this.chrome.header;
      if (!compact) this.el.style.background = this.chrome.header; else this.el.style.background = '#555';
      const c = this.textOn(this.chrome.header), pill = 'background:rgb(127 127 127 / .16);color:' + c;
      h.innerHTML = '<button class="pill" style="' + pill + '" data-act="back">' + (this.back ? '‹ Back' : 'Close') + '</button>' +
        '<div class="title" style="color:' + c + '"><b>' + CONFIG.title + '</b><i>mini app</i></div>' +
        '<button class="pill" style="' + pill + '" data-act="menu" title="' + (this.settings ? 'Settings is in this menu' : 'Menu') + '">⋯</button>';
      this.el.append(h);
      top = headerTop + d.header;
    } else {
      this.el.style.background = this.chrome.background;
      const h = document.createElement('div'); h.className = 'tgh';
      h.style.top = (d.safe_fs.top + 4) + 'px'; h.style.height = '38px';
      const glass = 'background:rgb(127 127 127 / .28);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);color:' + fg;
      h.innerHTML = '<button class="pill" style="' + glass + '" data-act="back">' + (this.back ? '‹ Back' : 'Close') + '</button><div class="title"></div><button class="pill" style="' + glass + '" data-act="menu">⋯</button>';
      this.el.append(h);
      top = 0;
    }
    const bar = this.barHeight();
    this.frame.style.top = top + 'px';
    this.frame.style.height = (H - top - bar) + 'px';
    this.frame.style.background = this.chrome.background;
    if (bar) this.renderBar(H - bar, bar);
    if (this.dev.home && !this.o.platform.startsWith('t')) {
      const hm = document.createElement('div'); hm.className = 'home'; hm.style.background = fg; this.el.append(hm);
    }
    this.el.querySelectorAll('[data-act]').forEach(b => b.onclick = () => {
      if (b.dataset.act === 'back' && this.back) this.send('event', 'backButtonClicked');
      else if (b.dataset.act === 'back') Stand.log(this, 'call', 'Close tapped', this.closing ? 'closing confirmation would ask first' : 'app would close');
      else if (b.dataset.act === 'menu' && this.settings) this.send('event', 'settingsButtonClicked');
    });
  }
  textOn(hex) {
    const m = /^#?([0-9a-f]{6})$/i.exec(hex || ''); if (!m) return '#000';
    const n = parseInt(m[1], 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
    return (0.299 * r + 0.587 * g + 0.114 * b) > 150 ? '#000' : '#fff';
  }
  renderBar(y, h) {
    const bb = document.createElement('div'); bb.className = 'bb';
    const sec = this.buttons.secondary, main = this.buttons.main;
    if (sec && sec.isVisible && ['top', 'bottom'].includes(sec.position)) bb.classList.add('stack');
    bb.style.top = y + 'px'; bb.style.height = h + 'px'; bb.style.paddingBottom = (8 + this.dev.home) + 'px';
    bb.style.background = this.chrome.bottomBar;
    const mk = (s, primary) => {
      const b = document.createElement('button');
      b.style.background = s.color || (primary ? this.theme.button_color : this.chrome.bottomBar);
      b.style.color = s.textColor || (primary ? this.theme.button_text_color : this.theme.button_color);
      if (!primary && !s.color) b.style.boxShadow = 'inset 0 0 0 1.5px ' + this.theme.button_color;
      b.disabled = !s.isActive;
      if (s.isProgressVisible) b.innerHTML = '<span class="spin"></span>';
      else b.textContent = (s.iconCustomEmojiId ? '◆ ' : '') + s.text;
      if (s.hasShineEffect) b.title = 'has_shine_effect';
      b.onclick = () => this.send('event', primary ? 'mainButtonClicked' : 'secondaryButtonClicked');
      return b;
    };
    const order = [];
    if (sec && sec.isVisible) order.push(mk(sec, false));
    if (main && main.isVisible) order.push(mk(main, true));
    if (sec && sec.isVisible && main && main.isVisible && ['right', 'bottom'].includes(sec.position)) order.reverse();
    bb.append(...order);
    this.el.append(bb);
  }
  send(type, name, data) {
    if (type === 'event') this.frame.contentWindow.postMessage({ __tma: 1, type: 'event', name, data }, location.origin);
    else this.frame.contentWindow.postMessage({ __tma: 1, type: 'state', data: name }, location.origin);
  }
  pushInsets() { const ins = this.insets(); this.send('state', ins); }
  onMessage(m) {
    const d = m.data;
    if (m.type === 'button') {
      const before = this.barHeight();
      this.buttons[d.type] = d;
      this.layout();
      if (before !== this.barHeight()) this.pushInsets();
    } else if (m.type === 'header') {
      if (d.kind === 'BackButton') this.back = d.visible; else this.settings = d.visible;
      Stand.log(this, 'call', d.kind + (d.visible ? '.show' : '.hide')); this.layout();
    } else if (m.type === 'chrome') {
      if (d.header) this.chrome.header = d.header;
      if (d.background) this.chrome.background = d.background;
      if (d.bottomBar) this.chrome.bottomBar = d.bottomBar;
      this.layout();
    } else if (m.type === 'fullscreen') {
      if (this.fullscreen !== d) { this.fullscreen = d; this.layout(); this.pushInsets(); this.send('state', { fullscreen: d }); }
    } else if (m.type === 'popup') {
      this.popup(d);
    } else if (m.type === 'log') {
      Stand.log(this, d.kind, d.name, d.detail);
    } else if (m.type === 'ready') {
      this.readyAt = performance.now();
    } else if (m.type === 'close') {
      Stand.log(this, 'call', 'app closed');
    }
  }
  popup(d) {
    const dark = this.o.scheme === 'dark';
    const s = document.createElement('div'); s.className = 'scrim';
    const box = document.createElement('div'); box.className = 'dlg';
    box.style.background = dark ? '#2c2c2e' : '#f2f2f2'; box.style.color = dark ? '#fff' : '#000';
    if (d.title) { const t = document.createElement('h4'); t.textContent = d.title; box.append(t); }
    const p = document.createElement('p'); p.textContent = d.message; box.append(p);
    const label = { ok: 'OK', close: 'Close', cancel: 'Cancel' };
    d.buttons.forEach(b => {
      const btn = document.createElement('button');
      btn.textContent = b.text || label[b.type] || 'OK';
      btn.style.color = b.type === 'destructive' ? this.theme.destructive_text_color : this.theme.link_color;
      btn.onclick = () => { s.remove(); this.send('event', 'popupClosed', { button_id: b.id || '' }); };
      box.append(btn);
    });
    s.append(box); this.el.append(s);
    Stand.log(this, 'call', 'popup', d.message);
  }
}
Device.all = [];

const Stand = {
  logEl: null,
  log(dev, kind, name, detail) {
    if (!this.logEl) return;
    const row = document.createElement('div'); row.className = kind;
    row.textContent = kind + '  ' + name + (detail !== undefined && detail !== '' ? '  ' + JSON.stringify(detail) : '');
    this.logEl.prepend(row);
  },
};
window.addEventListener('message', (ev) => {
  const m = ev.data; if (!m || m.__tma !== 1) return;
  const dev = Device.all.find(d => d.frame.contentWindow === ev.source);
  if (dev) dev.onMessage(m);
});

function opts(over) {
  return Object.assign({ platform: $('c-platform').value, scheme: $('c-scheme').value, width: +$('c-width').value,
    mode: $('c-mode').value, version: verSel.value, start: $('c-start').value.trim(), perf: $('c-perf').value, style: $('c-style').value, invoice: $('c-invoice').value, lang: $('c-lang').value, network: $('c-network').value, height: +qs.get('height') || undefined }, over);
}
function render() {
  const root = $('root'); root.replaceChildren(); Device.all = [];
  if (qs.get('view') === 'matrix') {
    const grid = document.createElement('div'); grid.className = 'matrix'; root.append(grid);
    const cell = (cap, o) => { const w = document.createElement('div'); const c = document.createElement('p'); c.className = 'cap'; c.textContent = cap; w.append(c); grid.append(w); new Device(w, opts(o)); };
    for (const platform of ['ios', 'android']) for (const scheme of ['light', 'dark']) for (const width of [320, 390, 430])
      cell(platform + ' · ' + scheme + ' · ' + width, { platform, scheme, width, mode: 'full', height: 700 });
    cell('ios · dark · 390 · fullscreen', { platform: 'ios', scheme: 'dark', width: 390, mode: 'fullscreen', height: 760 });
    cell('android · light · 390 · fullscreen', { platform: 'android', scheme: 'light', width: 390, mode: 'fullscreen', height: 760 });
    cell('ios · light · 390 · compact', { platform: 'ios', scheme: 'light', width: 390, mode: 'compact', height: 760 });
    return;
  }
  const stage = document.createElement('div'); stage.className = 'stage'; root.append(stage);
  const devHost = document.createElement('div'); stage.append(devHost);
  const side = document.createElement('div');
  side.innerHTML = '<p class="note">Mock client. Palettes approximate Telegram defaults; initData is unsigned demo data; ' +
    'payments never happen. Verify on real iOS, Android and Desktop clients.</p><div class="log" id="log"></div>';
  stage.append(side);
  Stand.logEl = side.querySelector('#log');
  new Device(devHost, opts());
}
for (const id of ['c-platform', 'c-scheme', 'c-width', 'c-mode', 'c-version', 'c-perf', 'c-style', 'c-invoice', 'c-lang', 'c-network']) $(id).onchange = render;
$('c-reload').onclick = render;
render();
</script>
</body></html>
"""


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
    config = {"app": app_url, "title": html.escape(title), "themes": THEMES, "devices": DEVICES,
              "heights": {str(k): v for k, v in HEIGHTS.items()}, "versions": versions,
              "catalog": {"fetched_at": meta["fetched_at"], "newest": meta["newest_member_version"]}}
    return STAND_HTML.replace("__CONFIG__", json.dumps(config).replace("<", "\\u003c"))


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
            if not path.startswith("/app/") and path not in ("/", "/index.html", "/__tma__/mock.js", "/__tma__/audit.mjs") \
                    and self._api("GET", path):
                return None
            if path in ("/", "/index.html"):
                return self._send(200, stand_html(app_url, title).encode(), "text/html; charset=utf-8")
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
