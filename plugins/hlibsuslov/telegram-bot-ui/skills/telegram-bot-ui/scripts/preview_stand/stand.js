/* Mini App preview stand: a MOCK Telegram client around the app (served by scripts/preview_miniapp.py).
   The URL holds every launch setting, so a copied link reproduces the view; panel sizes stay in localStorage.
   Launch parameters relaunch the app; theme, viewport, network, invoice outcome and style reach the running app
   the way Telegram would tell it (themeChanged, viewportChanged, fullscreenChanged, activated / deactivated). */
(function () {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const CONFIG = JSON.parse($('stand-config').textContent);
  const qs = new URLSearchParams(location.search);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const icon = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  const hex = (c) => (/^#[0-9a-f]{3,8}$/i.test(String(c || '')) ? c : 'transparent');
  const atLeast = (v, need) => {
    const x = String(v).split('.'), y = String(need).split('.');
    for (let i = 0; i < Math.max(x.length, y.length); i++) {
      const p = +x[i] || 0, q = +y[i] || 0;
      if (p !== q) return p > q;
    }
    return true;
  };
  const textOn = (c) => {
    const m = /^#?([0-9a-f]{6})$/i.exec(c || '');
    if (!m) return '#000';
    const n = parseInt(m[1], 16);
    return 0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255) > 150 ? '#000' : '#fff';
  };

  const PLATFORM = { ios: 'iOS', android: 'Android', tdesktop: 'Desktop' };
  const MODE = { compact: 'Compact', full: 'Full', fullscreen: 'Fullscreen' };
  const WIDTHS = [[320, 'small phone'], [375, 'compact phone'], [384, 'desktop window'], [390, 'phone'], [430, 'large phone'], [669, 'foldable, inner']];
  const NEWEST = CONFIG.versions[CONFIG.versions.length - 1];

  // ------------------------------------------------------------------ settings: the URL is the source of truth

  const DEFAULTS = { platform: 'ios', scheme: 'light', width: '390', mode: 'full', version: NEWEST, lang: 'en', start: '',
    perf: 'HIGH', style: '', invoice: 'cancelled', network: 'normal', view: 'device', zoom: 'fit' };
  const CHOICES = { platform: Object.keys(PLATFORM), scheme: ['light', 'dark'], mode: Object.keys(MODE), version: CONFIG.versions,
    lang: ['en', 'ru', 'uk', 'de', 'ar', 'he', 'fa'], perf: ['HIGH', 'AVERAGE', 'LOW'], style: ['', 'native', 'fintech', 'soft', 'dense'],
    invoice: ['cancelled', 'paid', 'failed', 'pending'], network: ['normal', 'slow', 'flaky', 'offline', 'error', 'session'],
    view: ['device', 'matrix'], zoom: ['fit', '50', '75', '100'] };
  const S = {};
  for (const k of Object.keys(DEFAULTS)) {
    const v = qs.get(k);
    S[k] = v === null || (CHOICES[k] && !CHOICES[k].includes(v)) ? DEFAULTS[k] : v;
  }
  if (!(+S.width >= 240 && +S.width <= 1400)) S.width = DEFAULTS.width;
  S.start = S.start.slice(0, 512);
  const HEIGHT = Math.min(3000, Math.max(0, +qs.get('height') || 0));
  const AUDIT = qs.get('audit') === '1';
  const PANELS_OFF = qs.get('panels') === '0';

  function writeUrl() {
    const p = new URLSearchParams();
    for (const k of Object.keys(DEFAULTS)) if (S[k] !== DEFAULTS[k]) p.set(k, S[k]);
    if (HEIGHT) p.set('height', HEIGHT);
    if (AUDIT) p.set('audit', '1');
    if (PANELS_OFF) p.set('panels', '0');
    const q = p.toString();
    history.replaceState(null, '', location.pathname + (q ? '?' + q : ''));
  }

  // ------------------------------------------------------------------ stand preferences (not part of a link)

  const UI_KEY = 'tma-stand-ui';
  const saved = (() => { try { return JSON.parse(localStorage.getItem(UI_KEY) || '{}'); } catch (e) { return {}; } })();
  const ui = Object.assign({ left: true, right: true, bottom: true, leftW: 288, rightW: 320, bottomH: 236, theme: null,
    itab: 'state', btab: 'events' }, saved);
  const saveUi = () => { try { localStorage.setItem(UI_KEY, JSON.stringify(ui)); } catch (e) { /* private mode */ } };
  const narrow = matchMedia('(max-width: 900px)');

  // CloudStorage, DeviceStorage and SecureStorage survive a relaunch, like in Telegram; Clear starts a first launch.
  const STORE_KEY = 'tma-stand-storage';
  const storage = (() => { try { return JSON.parse(sessionStorage.getItem(STORE_KEY) || '{}'); } catch (e) { return {}; } })();
  const saveStorage = () => { try { sessionStorage.setItem(STORE_KEY, JSON.stringify(storage)); } catch (e) { /* quota */ } };

  // ------------------------------------------------------------------ small pieces of UI

  let toastTimer = 0;
  function toast(text) {
    const t = $('toast');
    t.textContent = text; t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 1800);
  }
  function copy(text, done) {
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject(new Error('no clipboard')))
      .then(() => toast(done), () => toast('Copy failed: the browser blocked the clipboard'));
  }
  function setRadio(group, value) {
    group.querySelectorAll('[role="radio"]').forEach((b) => {
      const on = b.dataset.value === value;
      b.setAttribute('aria-checked', on ? 'true' : 'false');
      b.tabIndex = on ? 0 : -1;
    });
  }
  function onRadio(group, cb) {
    group.addEventListener('click', (e) => {
      const b = e.target.closest('[role="radio"]');
      if (b && group.getAttribute('aria-disabled') !== 'true') cb(b.dataset.value);
    });
  }
  // Arrow keys move between tabs and between the options of a segmented control.
  document.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    const item = e.target.closest('[role="tab"], [role="radio"]');
    const group = item && item.parentElement;
    if (!group || !/tablist|radiogroup/.test(group.getAttribute('role') || '')) return;
    const items = [...group.querySelectorAll(':scope > [role="tab"], :scope > [role="radio"]')];
    const next = items[(items.indexOf(item) + (e.key === 'ArrowRight' ? 1 : items.length - 1)) % items.length];
    e.preventDefault(); next.focus(); next.click();
  });

  // ------------------------------------------------------------------ dropdowns (shadcn Select look)
  // The native <select> stays the source of truth (value, change events, the URL); a trigger and a listbox draw it.
  // "main · description" options show the description muted.
  const selects = [];
  let openMenu = null;
  const parts = (text) => {
    const i = text.indexOf(' · ');
    return i < 0 ? [text, ''] : [text.slice(0, i), text.slice(i + 3)];
  };
  function closeMenu(focusTrigger) {
    if (!openMenu) return;
    const { menu, trigger } = openMenu;
    menu.remove(); trigger.setAttribute('aria-expanded', 'false');
    openMenu = null;
    if (focusTrigger) trigger.focus();
  }
  function enhanceSelect(sel) {
    const box = sel.parentElement;
    box.classList.add('is-enhanced');
    sel.tabIndex = -1; sel.setAttribute('aria-hidden', 'true');
    const trigger = document.createElement('button');
    trigger.type = 'button'; trigger.className = 'select-trigger';
    trigger.setAttribute('role', 'combobox');
    trigger.setAttribute('aria-haspopup', 'listbox'); trigger.setAttribute('aria-expanded', 'false');
    const label = document.querySelector(`label[for="${sel.id}"]`);
    if (label) { label.htmlFor = ''; label.id = label.id || sel.id + '-label'; trigger.setAttribute('aria-labelledby', label.id); label.onclick = () => trigger.focus(); }
    else trigger.setAttribute('aria-label', sel.getAttribute('aria-label') || '');
    box.append(trigger);
    const refresh = () => {
      const o = sel.selectedOptions[0];
      const [main, desc] = parts(o ? o.textContent : '');
      trigger.innerHTML = `<span class="select-value">${esc(main)}${desc ? `<span class="select-desc"> · ${esc(desc)}</span>` : ''}</span>`;
      trigger.disabled = sel.disabled;
    };
    function open() {
      if (sel.disabled) return;
      closeMenu();
      const menu = document.createElement('div');
      menu.className = 'select-menu'; menu.setAttribute('role', 'listbox'); menu.tabIndex = -1;
      menu.setAttribute('aria-labelledby', trigger.getAttribute('aria-labelledby') || '');
      const opts = [...sel.options];
      let active = Math.max(0, sel.selectedIndex);
      menu.innerHTML = opts.map((o, i) => {
        const [main, desc] = parts(o.textContent);
        return `<div class="select-item" role="option" id="${sel.id}-opt-${i}" data-i="${i}" aria-selected="${i === sel.selectedIndex}">` +
          `<svg class="icon select-check" aria-hidden="true"><use href="#i-check"/></svg><span class="select-main">${esc(main)}</span>` +
          (desc ? `<span class="select-sub">${esc(desc)}</span>` : '') + '</div>';
      }).join('');
      document.body.append(menu);
      const r = trigger.getBoundingClientRect();
      menu.style.minWidth = r.width + 'px';
      const h = Math.min(menu.scrollHeight, 320), below = innerHeight - r.bottom - 8;
      menu.style.left = Math.min(r.left, innerWidth - menu.offsetWidth - 8) + 'px';
      menu.style.top = (below >= h || below >= r.top ? r.bottom + 4 : r.top - h - 4) + 'px';
      const items = [...menu.children];
      const highlight = (i) => {
        active = (i + items.length) % items.length;
        items.forEach((it, j) => it.classList.toggle('is-active', j === active));
        menu.setAttribute('aria-activedescendant', items[active].id);
        const it = items[active];  // scroll the menu only, never the page under it
        if (it.offsetTop < menu.scrollTop) menu.scrollTop = it.offsetTop - 4;
        else if (it.offsetTop + it.offsetHeight > menu.scrollTop + menu.clientHeight) menu.scrollTop = it.offsetTop + it.offsetHeight - menu.clientHeight + 4;
      };
      const choose = (i) => {
        closeMenu(true);
        if (i !== sel.selectedIndex) { sel.selectedIndex = i; refresh(); sel.dispatchEvent(new Event('change')); }
      };
      menu.addEventListener('pointermove', (e) => { const it = e.target.closest('.select-item'); if (it && +it.dataset.i !== active) highlight(+it.dataset.i); });
      menu.addEventListener('click', (e) => { const it = e.target.closest('.select-item'); if (it) choose(+it.dataset.i); });
      menu.addEventListener('keydown', (e) => {
        const k = e.key;
        if (k === 'ArrowDown' || k === 'ArrowUp') highlight(active + (k === 'ArrowDown' ? 1 : -1));
        else if (k === 'Home' || k === 'End') highlight(k === 'Home' ? 0 : items.length - 1);
        else if (k === 'Enter' || k === ' ') choose(active);
        else if (k === 'Escape' || k === 'Tab') closeMenu(k === 'Escape');
        else if (k.length === 1) {
          const n = items.findIndex((it, j) => j > active && it.textContent.toLowerCase().startsWith(k.toLowerCase()));
          const m = n >= 0 ? n : items.findIndex((it) => it.textContent.toLowerCase().startsWith(k.toLowerCase()));
          if (m >= 0) highlight(m);
        } else return;
        e.preventDefault();
      });
      trigger.setAttribute('aria-expanded', 'true');
      openMenu = { menu, trigger };
      highlight(active);
      menu.focus({ preventScroll: true });
    }
    trigger.addEventListener('click', () => (openMenu && openMenu.trigger === trigger ? closeMenu(true) : open()));
    trigger.addEventListener('keydown', (e) => {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); open(); }
    });
    sel.addEventListener('change', refresh);
    selects.push(refresh);
    refresh();
  }
  const refreshSelects = () => selects.forEach((f) => f());
  document.addEventListener('pointerdown', (e) => {
    if (openMenu && !openMenu.menu.contains(e.target) && !openMenu.trigger.contains(e.target)) closeMenu();
  });
  window.addEventListener('resize', () => closeMenu());
  // only a scroll that moves the trigger closes the menu (the event log scrolls on its own as calls arrive)
  document.addEventListener('scroll', (e) => {
    if (openMenu && (e.target === document || (e.target.contains && e.target.contains(openMenu.trigger)))) closeMenu();
  }, true);

  // ------------------------------------------------------------------ glyphs the mock draws (not Telegram's artwork)

  const G = {
    close: '<svg viewBox="0 0 24 24"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    chevron: '<svg viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"/></svg>',
    arrow: '<svg viewBox="0 0 24 24"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>',
    dots: '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg>',
    dotsV: '<svg viewBox="0 0 24 24"><circle cx="12" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="12" cy="19" r="1"/></svg>',
    down: '<svg viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></svg>',
    status: '<svg width="18" height="12" viewBox="0 0 18 12"><rect y="8" width="3" height="4" rx="1"/><rect x="5" y="5.5" width="3" height="6.5" rx="1"/>' +
      '<rect x="10" y="3" width="3" height="9" rx="1"/><rect x="15" width="3" height="12" rx="1"/></svg>' +
      '<svg width="16" height="12" viewBox="0 0 16 12"><path d="M8 2.3c2.3 0 4.4.9 6 2.4l1.3-1.3A10.6 10.6 0 0 0 8 .4C5.2.4 2.6 1.5.7 3.4L2 4.7a8.7 8.7 0 0 1 6-2.4Zm0 3.7c1.3 0 2.5.5 3.4 1.3l1.3-1.3A6.6 6.6 0 0 0 8 4.1a6.6 6.6 0 0 0-4.7 1.9l1.3 1.3C5.5 6.5 6.7 6 8 6Zm0 3.6c.5 0 .9.2 1.2.5L8 11.6l-1.2-1.5c.3-.3.7-.5 1.2-.5Z"/></svg>' +
      '<svg width="27" height="13" viewBox="0 0 27 13"><rect x=".5" y=".5" width="23" height="12" rx="3.5" fill="none" stroke="currentColor" opacity=".4"/>' +
      '<rect x="2" y="2" width="20" height="9" rx="2"/><path d="M25 4.5v4a2 2 0 0 0 0-4Z" opacity=".4"/></svg>',
  };

  function themeFor(platform, scheme) { return CONFIG.themes[(platform === 'android' ? 'android' : 'ios') + '-' + scheme]; }
  function demoInitData(start, lang) {
    const user = JSON.stringify({ id: 100000001, first_name: 'Demo', language_code: lang || 'en', allows_write_to_pm: true });
    const p = new URLSearchParams({ query_id: 'MOCK-QUERY', user, auth_date: String(Math.floor(Date.now() / 1000)), hash: 'mock-unsigned' });
    if (start) { p.set('start_param', start); p.set('chat_type', 'sender'); }
    return p.toString();
  }

  // ------------------------------------------------------------------ one device: the mock client and its state

  let uid = 0;
  class Device {
    constructor(host, o, label) {
      this.uid = ++uid;
      this.o = o; this.label = label;
      this.dev = CONFIG.devices[o.platform];
      this.W = +o.width; this.H = o.height || CONFIG.heights[String(o.width)] || 800;
      this.s = 1;
      this.wrap = document.createElement('div'); this.wrap.className = 'device-wrap';
      this.cap = document.createElement('div'); this.cap.className = 'device-cap';
      this.capText = document.createElement('span');
      this.chip = document.createElement('span'); this.chip.className = 'haptic-chip';
      this.cap.append(this.capText, this.chip);
      this.slot = document.createElement('div'); this.slot.className = 'device-slot';
      this.el = document.createElement('div'); this.el.className = 'device ' + o.platform;
      this.el.style.width = this.W + 'px'; this.el.style.height = this.H + 'px';
      this.slot.append(this.el); this.wrap.append(this.cap, this.slot); host.append(this.wrap);
      this.wrap.addEventListener('pointerdown', () => Stand.select(this));
      this.launch();
    }

    // -- lifecycle
    launch() {
      // o.mode and o.scheme follow the controls, so a relaunch opens the app the way the user last set it
      this.mode = this.o.mode; this.prevMode = this.o.mode === 'fullscreen' ? 'full' : this.o.mode;
      this.scheme = this.o.scheme; this.theme = themeFor(this.o.platform, this.o.scheme);
      this.keys = { header: null, background: null, bottomBar: null };
      this.buttons = { main: null, secondary: null };
      this.back = false; this.settings = false;
      this.flags = { closingConfirmation: false, verticalSwipes: true, orientationLocked: false };
      this.phase = 'loading'; this.active = true; this.late = false; this.readyMs = null; this.loadMs = null;
      this.t0 = performance.now();
      this.el.querySelectorAll('.scrim, .state-cover').forEach((n) => n.remove());
      if (this.frame) this.frame.remove();
      this.frame = document.createElement('iframe');
      this.frame.title = 'Mini App, ' + this.label;
      this.el.prepend(this.frame);
      if (!this.ph) {
        this.ph = document.createElement('div'); this.ph.className = 'placeholder'; this.ph.innerHTML = '<span class="spin"></span>';
        this.el.append(this.ph);
      }
      this.ph.hidden = false;
      this.layout(); this.renderCap();
      this.frame.addEventListener('load', () => this.onLoad());
      this.frame.src = this.src();
      clearTimeout(this.waitTimer);
      this.waitTimer = setTimeout(() => this.checkReady(), 3000);
    }
    elapsed() { return (performance.now() - this.t0) / 1000; }
    onLoad() {
      let blank = false;
      try { blank = this.frame.contentWindow.location.href === 'about:blank'; } catch (e) { /* cross-origin: not ours */ }
      if (blank || this.phase === 'closed') return;
      this.loadMs = Math.round(performance.now() - this.t0);
      if (this.phase === 'loading') this.phase = 'loaded';
      this.ph.hidden = true;  // Telegram hides its placeholder on ready() or, failing that, when the page has loaded
      changed();
    }
    checkReady() {
      if (this.phase === 'ready' || this.phase === 'closed') return;
      this.late = true;
      Log.add(this, 'stand', 'ready() not called after 3 s',
        'Telegram keeps its loading placeholder until ready() or the page load: call ready() once the first screen is drawn');
      changed();
    }
    relaunch() { this.launch(); Log.mark(this, 'relaunched'); changed(); }

    // -- geometry
    get fullscreen() { return this.mode === 'fullscreen'; }
    bezel() { return this.o.platform === 'tdesktop' ? 4 : this.o.platform === 'ios' ? 13 : 11; }
    outerW() { return this.W + 2 * this.bezel(); }
    outerH() { return this.H + 2 * this.bezel(); }
    setScale(s) {
      this.s = s;
      const b = this.bezel() * s;
      this.slot.style.width = this.outerW() * s + 'px'; this.slot.style.height = this.outerH() * s + 'px';
      this.el.style.left = b + 'px'; this.el.style.top = b + 'px';
      this.el.style.transform = s === 1 ? '' : `scale(${s})`;
    }
    insets() {
      const d = this.dev;
      if (this.fullscreen) return { safe: { top: d.safe_fs.top, bottom: this.barVisible() ? 0 : d.safe_fs.bottom, left: 0, right: 0 },
        content: { top: d.content_fs.top, bottom: 0, left: 0, right: 0 } };
      return { safe: { top: 0, bottom: this.barVisible() ? 0 : d.home, left: 0, right: 0 }, content: { top: 0, bottom: 0, left: 0, right: 0 } };
    }
    viewport() { return { w: this.W, h: Math.round(parseFloat(this.frame.style.height) || 0) }; }
    color(which) {
      const key = this.keys[which];
      if (key) return key in this.theme ? this.theme[key] : key;
      return which === 'header' ? this.theme.header_bg_color : which === 'background' ? this.theme.secondary_bg_color : this.theme.bottom_bar_bg_color;
    }
    src() {
      const ins = this.insets(), o = this.o;
      this.initData = demoInitData(o.start, o.lang);
      const mock = { scheme: this.scheme, mode: this.mode, fullscreen: this.fullscreen, safe: ins.safe, content: ins.content, perf: o.perf,
        style: S.style === 'native' ? '' : S.style, invoice: S.invoice, network: S.network, audit: AUDIT, storage };
      const p = new URLSearchParams({ tgWebAppData: this.initData, tgWebAppVersion: o.version, tgWebAppPlatform: o.platform,
        tgWebAppThemeParams: JSON.stringify(this.theme), tgWebAppMock: JSON.stringify(mock) });
      if (this.fullscreen) p.set('tgWebAppFullscreen', '1');
      let url = CONFIG.app;
      if (o.start) url += (url.includes('?') ? '&' : '?') + 'tgWebAppStartParam=' + encodeURIComponent(o.start);
      return url + '#' + p.toString();
    }
    barVisible() { return !!((this.buttons.main && this.buttons.main.isVisible) || (this.buttons.secondary && this.buttons.secondary.isVisible)); }
    barHeight() {
      if (!this.barVisible()) return 0;
      const both = this.buttons.main?.isVisible && this.buttons.secondary?.isVisible;
      const stacked = both && ['top', 'bottom'].includes(this.buttons.secondary.position);
      return (stacked ? 120 : this.dev.bar) + this.dev.home;
    }

    // -- drawing the client around the frame
    renderCap() {
      this.capText.innerHTML = `<b>${PLATFORM[this.o.platform]}</b> ${this.W} × ${this.H} · ${this.scheme === 'dark' ? 'Night' : 'Day'} · ${MODE[this.mode]}`;
    }
    layout() {
      const d = this.dev, H = this.H, fs = this.fullscreen, compact = this.mode === 'compact';
      const fg = this.scheme === 'light' ? '#000' : '#fff';
      this.el.querySelectorAll('.cn').forEach((n) => n.remove());
      const add = (cls, html, style) => {
        const n = document.createElement('div');
        n.className = 'cn ' + cls;
        if (html) n.innerHTML = html;
        if (style) Object.assign(n.style, style);
        this.el.append(n);
        return n;
      };
      const header = this.color('header'), bg = this.color('background');
      const sheetTop = compact ? Math.round(H * 0.42) : 0;
      this.el.style.background = fs ? bg : compact ? this.theme.secondary_bg_color : header;
      if (compact) add('behind', '', { background: this.theme.secondary_bg_color, bottom: 'auto', height: sheetTop + 'px' });
      if (d.status) {
        add('sb', `<span>9:41</span><span class="sb-icons">${G.status}</span>`,
          { height: d.status + 'px', color: fs || compact ? fg : textOn(header) });
        add(this.o.platform === 'ios' ? 'island' : 'camera');
      }
      let top = 0;
      if (!fs) {
        const hTop = compact ? sheetTop : d.status, c = textOn(header);
        const h = add('tgh', this.headerHtml(c), { top: hTop + 'px', height: d.header + 'px', background: header, color: c });
        if (compact) {
          h.style.borderRadius = '12px 12px 0 0';
          add('grabber', '', { top: hTop + 5 + 'px', background: c });
        }
        top = hTop + d.header;
      } else {
        const glass = `background:rgb(127 127 127 / .28);color:${fg}`;
        add('fsbar', `<button class="pill" style="${glass}" data-act="close">${this.back ? G.chevron + 'Back' : 'Close'}</button>` +
          `<button class="pill" style="${glass}" data-act="menu" aria-label="Menu">${G.down}${G.dots}</button>`,
          { top: d.safe_fs.top + 4 + 'px', height: '36px' });
      }
      const bar = this.barHeight();
      const frameH = H - top - bar;
      this.frame.style.top = top + 'px'; this.frame.style.height = frameH + 'px'; this.frame.style.background = bg;
      Object.assign(this.ph.style, { top: top + 'px', height: frameH + 'px', background: this.theme.bg_color, color: this.theme.hint_color });
      if (bar) this.renderBar(H - bar, bar, add);
      if (d.home) add('home', '', { background: fg });
      this.el.querySelectorAll('.cn [data-act]').forEach((b) => {
        b.onclick = () => (b.dataset.act === 'close' ? this.headerClose() : this.menu());
      });
    }
    headerHtml(c) {
      const title = `<div class="title"><b>${esc(CONFIG.title)}</b><i>mini app</i></div>`;
      if (this.o.platform === 'ios') {
        const pill = `background:rgb(127 127 127 / .16);color:${c}`;
        return `<button class="pill" style="${pill}" data-act="close">${this.back ? G.chevron + 'Back' : 'Close'}</button>${title}` +
          `<button class="pill round" style="${pill}" data-act="menu" aria-label="Menu">${G.dots}</button>`;
      }
      return `<button class="ib" style="color:${c}" data-act="close" aria-label="${this.back ? 'Back' : 'Close'}">${this.back ? G.arrow : G.close}</button>` +
        `${title}<button class="ib" style="color:${c}" data-act="menu" aria-label="Menu">${G.dotsV}</button>`;
    }
    renderBar(y, h, add) {
      const bb = add('bb', '', { top: y + 'px', height: h + 'px', paddingBottom: 8 + this.dev.home + 'px', background: this.color('bottomBar') });
      const sec = this.buttons.secondary, main = this.buttons.main;
      if (sec && sec.isVisible && ['top', 'bottom'].includes(sec.position)) bb.classList.add('stack');
      const mk = (s, primary) => {
        const b = document.createElement('button');
        b.style.background = hex(s.color || (primary ? this.theme.button_color : this.color('bottomBar')));
        b.style.color = hex(s.textColor || (primary ? this.theme.button_text_color : this.theme.button_color));
        if (!primary && !s.color) b.style.boxShadow = 'inset 0 0 0 1.5px ' + hex(this.theme.button_color);
        b.disabled = !s.isActive;
        if (s.isProgressVisible) b.innerHTML = '<span class="spin"></span>';
        else b.textContent = (s.iconCustomEmojiId ? '◆ ' : '') + s.text;
        if (s.hasShineEffect && !s.isProgressVisible) b.classList.add('shine');
        b.onclick = () => this.send('event', primary ? 'mainButtonClicked' : 'secondaryButtonClicked');
        return b;
      };
      const order = [];
      if (sec && sec.isVisible) order.push(mk(sec, false));
      if (main && main.isVisible) order.push(mk(main, true));
      if (sec && sec.isVisible && main && main.isVisible && ['right', 'bottom'].includes(sec.position)) order.reverse();
      bb.append(...order);
    }

    // -- talking to the app
    send(type, name, data) {
      const w = this.frame.contentWindow;
      if (!w || this.phase === 'closed') return;
      if (type === 'event') w.postMessage({ __tma: 1, type: 'event', name, data }, location.origin);
      else w.postMessage({ __tma: 1, type: 'state', data: name }, location.origin);
    }
    pushInsets() { this.send('state', this.insets()); }
    onMessage(m) {
      const d = m.data;
      switch (m.type) {
        case 'button': {
          const before = this.barHeight();
          this.buttons[d.type] = d;
          this.layout();
          if (before !== this.barHeight()) this.pushInsets();
          break;
        }
        case 'header':
          if (d.kind === 'BackButton') this.back = d.visible; else this.settings = d.visible;
          Log.add(this, 'call', d.kind + (d.visible ? '.show' : '.hide'));
          this.layout();
          break;
        case 'chrome':
          if ('headerKey' in d) this.keys.header = d.headerKey;
          if ('backgroundKey' in d) this.keys.background = d.backgroundKey;
          if ('bottomBarKey' in d) this.keys.bottomBar = d.bottomBarKey;
          this.layout();
          break;
        case 'fullscreen':
          if (d) this.setMode('fullscreen', 'requestFullscreen()');
          else this.setMode(this.prevMode, 'exitFullscreen()');
          break;
        case 'expand':
          if (this.mode === 'compact') this.setMode('full', 'expand()');
          break;
        case 'popup': this.popup(d); break;
        case 'log':
          Log.add(this, d.kind, d.name, d.detail);
          if (d.kind === 'haptic') this.buzz(d.name, d.detail);
          break;
        case 'ready':
          if (this.phase !== 'ready') { this.readyMs = d && d.ms; this.phase = 'ready'; this.ph.hidden = true; }
          break;
        case 'close': this.closeApp('the app closed itself'); break;
        case 'flags': Object.assign(this.flags, d); break;
        case 'storage':
          storage[d.name] = d.items; saveStorage();
          break;
        case 'net': Net.update(this, d); break;
        case 'audit': Audit.show(this, d); break;
        default: break;
      }
      changed();
    }

    // -- what Telegram or the user does to a running app
    setScheme(scheme) {
      if (scheme === this.scheme || this.phase === 'closed') return;
      this.scheme = scheme; this.theme = themeFor(this.o.platform, scheme);
      this.layout(); this.renderCap();
      this.send('state', { themeParams: this.theme, colorScheme: scheme });
      Log.add(this, 'stand', (scheme === 'dark' ? 'night' : 'day') + ' theme', 'themeChanged sent; the chrome colours follow');
      changed();
    }
    setMode(mode, by) {
      if (mode === this.mode || this.phase === 'closed') return;
      if (mode === 'fullscreen' && !atLeast(this.o.version, '8.0')) {
        Log.add(this, 'stand', 'fullscreen needs client 8.0', 'this client is ' + this.o.version);
        return;
      }
      const wasFs = this.fullscreen;
      if (mode !== 'fullscreen') this.prevMode = mode;
      this.mode = mode;
      this.send('state', { mode });
      this.layout(); this.renderCap(); this.pushInsets();
      if (wasFs !== this.fullscreen) this.send('state', { fullscreen: this.fullscreen });
      Log.add(this, 'stand', MODE[mode].toLowerCase() + ' viewport', (by ? by + '; ' : '') +
        (wasFs !== this.fullscreen ? 'fullscreenChanged and viewportChanged sent' : 'viewportChanged sent'));
      changed();
    }
    setLive(key, value) {
      this.send('state', { [key]: key === 'style' && value === 'native' ? '' : value });
    }
    setActive(on) {
      if (this.phase === 'closed' || on === this.active) return;
      this.active = on;
      const v8 = atLeast(this.o.version, '8.0');
      if (v8) this.send('state', { active: on });
      if (on) this.el.querySelectorAll('.state-cover').forEach((n) => n.remove());
      else this.cover('Minimized', 'Telegram tells the app it is in the background: pause timers, sensors and media.', 'Restore', () => this.setActive(true));
      Log.add(this, 'stand', on ? 'restored' : 'minimized', v8 ? (on ? 'activated sent' : 'deactivated sent') : 'no event below client 8.0');
      changed();
    }
    headerClose() {
      if (this.back) {
        this.send('event', 'backButtonClicked');
        Log.add(this, 'stand', 'header Back tapped', 'backButtonClicked sent');
      } else this.requestClose('Close tapped');
    }
    systemBack() {
      if (this.phase === 'closed') return;
      if (this.back) {
        this.send('event', 'backButtonClicked');
        Log.add(this, 'stand', 'system back', 'backButtonClicked sent');
      } else this.requestClose('system back');
    }
    menu() {
      if (this.settings) {
        this.send('event', 'settingsButtonClicked');
        Log.add(this, 'stand', 'menu → Settings', 'settingsButtonClicked sent');
      } else Log.add(this, 'stand', 'menu opened', 'no Settings item: the app has not shown SettingsButton');
    }
    requestClose(source) {
      if (this.phase === 'closed') return;
      if (!this.flags.closingConfirmation) return this.closeApp(source);
      Log.add(this, 'stand', source, 'closing confirmation asks first');
      this.dialog({ message: 'Changes that you made may not be saved.', buttons: [{ id: 'close', type: 'destructive', text: 'Close anyway' }, { id: '', type: 'cancel' }] },
        (id) => (id === 'close' ? this.closeApp(source + ', confirmed') : Log.add(this, 'stand', 'closing cancelled', 'the app stays open')));
    }
    closeApp(why) {
      if (this.phase === 'closed') return;
      this.phase = 'closed';
      clearTimeout(this.waitTimer);
      this.frame.src = 'about:blank';
      this.el.querySelectorAll('.scrim, .state-cover').forEach((n) => n.remove());
      this.cover('Closed', why.charAt(0).toUpperCase() + why.slice(1) + '. Telegram drops the page with its state.', 'Relaunch', () => this.relaunch());
      Log.add(this, 'stand', 'app closed', why);
      changed();
    }
    cover(title, text, action, onAction) {
      const c = document.createElement('div');
      c.className = 'state-cover';
      c.innerHTML = `<b>${esc(title)}</b><p>${esc(text)}</p><button type="button">${esc(action)}</button>`;
      c.querySelector('button').onclick = onAction;
      this.el.append(c);
    }
    buzz(name, detail) {
      this.el.classList.remove('is-buzzing');
      void this.el.offsetWidth;
      this.el.classList.add('is-buzzing');
      this.chip.innerHTML = icon('vibrate') + esc(name.replace('Occurred', '').replace('selectionChanged', 'selection') + (detail ? ' ' + detail : ''));
      this.chip.classList.add('is-on');
      clearTimeout(this.chipTimer);
      this.chipTimer = setTimeout(() => this.chip.classList.remove('is-on'), 1300);
    }
    popup(d) {
      Log.add(this, 'popup', d.title ? d.title : 'popup', d.message);
      this.dialog(d, (id) => this.send('event', 'popupClosed', { button_id: id }));
    }
    // A native-looking dialog of the mock client (popups, closing confirmation).
    dialog(d, done) {
      const plat = this.o.platform, dark = this.scheme === 'dark', t = this.theme;
      const s = document.createElement('div'); s.className = 'scrim';
      const box = document.createElement('div'); box.className = 'dlg ' + plat;
      box.setAttribute('role', 'alertdialog');
      if (plat === 'ios') { box.style.background = dark ? 'rgb(37 37 37 / .94)' : 'rgb(242 242 242 / .94)'; box.style.color = dark ? '#fff' : '#000'; }
      else { box.style.background = hex(t.bg_color); box.style.color = hex(t.text_color); }
      if (d.title) { const h = document.createElement('h4'); h.textContent = d.title; box.append(h); }
      const p = document.createElement('p'); p.textContent = d.message; box.append(p);
      const acts = document.createElement('div'); acts.className = 'acts';
      const label = { ok: 'OK', close: 'Close', cancel: 'Cancel' };
      const buttons = d.buttons && d.buttons.length ? d.buttons : [{ type: 'close' }];
      if (plat === 'ios' && buttons.length === 2) acts.classList.add('two');
      buttons.forEach((b) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = b.text || label[b.type] || 'OK';
        if (b.type === 'cancel') btn.classList.add('cancel');
        btn.style.color = hex(b.type === 'destructive' ? t.destructive_text_color : t.link_color);
        btn.onclick = () => { s.remove(); done(b.id || ''); };
        acts.append(btn);
      });
      box.append(acts); s.append(box); this.el.append(s);
      acts.querySelector('button').focus({ preventScroll: true });
    }
  }

  // ------------------------------------------------------------------ the event log

  const KINDS = { call: 'Calls', haptic: 'Haptics', chrome: 'Chrome', popup: 'Popups', storage: 'Storage', link: 'Links',
    payment: 'Payments', network: 'Network', unsupported: 'Unsupported', error: 'Errors', layout: 'Layout', stand: 'Stand' };
  const BAD = new Set(['unsupported', 'error']);
  const LIMIT = 3000;
  const Log = {
    rows: [], counts: {}, filter: 'all', query: '',
    detail(v) {
      if (v === undefined || v === null || v === '') return '';
      if (typeof v === 'string') return v;
      try { return JSON.stringify(v); } catch (e) { return String(v); }
    },
    add(dev, kind, name, detail) {
      if (!KINDS[kind]) kind = 'call';
      const r = { kind, name: String(name), detail: this.detail(detail), dev: dev ? dev.label : '', t: dev ? dev.elapsed() : 0 };
      this.rows.push(r);
      this.counts[kind] = (this.counts[kind] || 0) + 1;
      if (this.rows.length > LIMIT) {
        const old = this.rows.shift();
        this.counts[old.kind]--;
        if (old.el && old.el.parentNode) old.el.remove();
      }
      if (this.match(r)) this.append(r);
      this.renderCounts();
    },
    mark(dev, what) {
      this.add(dev, 'stand', what, `${PLATFORM[dev.o.platform]} · ${dev.W} × ${dev.H} · ${dev.scheme} · ${dev.mode} · client ${dev.o.version} · ${dev.o.lang}` +
        (dev.o.start ? ' · start_param ' + dev.o.start : ''));
    },
    match(r) {
      if (this.filter !== 'all' && r.kind !== this.filter) return false;
      if (!this.query) return true;
      return (r.kind + ' ' + r.name + ' ' + r.detail + ' ' + r.dev).toLowerCase().includes(this.query);
    },
    row(r) {
      const d = document.createElement('div');
      d.className = 'log-row' + (BAD.has(r.kind) ? ' is-bad' : '') + (r.kind === 'stand' ? ' is-stand' : '');
      d.dataset.k = r.kind;
      const t = r.t < 100 ? r.t.toFixed(2) : r.t.toFixed(0);
      d.innerHTML = `<span class="log-t">${t}s</span><span class="kind">${r.kind}</span>` +
        `<span class="log-main">${Stand.matrix && r.dev ? `<span class="dev-tag">${esc(r.dev)}</span>` : ''}<span class="log-name">${esc(r.name)}</span>` +
        `${r.detail ? `<span class="log-detail">${esc(r.detail)}</span>` : ''}</span>`;
      if (r.detail.length + r.name.length > 70) {
        d.classList.add('has-more');
        d.title = 'Click to show all of it';
        d.onclick = () => { if (!getSelection().toString()) d.classList.toggle('is-open'); };
      }
      r.el = d;
      return d;
    },
    append(r) {
      const box = $('log');
      const stick = box.scrollTop + box.clientHeight >= box.scrollHeight - 24;
      box.append(this.row(r));
      if (stick) box.scrollTop = box.scrollHeight;
      $('log-empty').hidden = true;
    },
    render() {
      const box = $('log'), frag = document.createDocumentFragment();
      let n = 0;
      for (const r of this.rows) if (this.match(r)) { frag.append(this.row(r)); n++; }
      box.replaceChildren(frag);
      box.scrollTop = box.scrollHeight;
      $('log-empty').hidden = n > 0;
      if (!n && this.rows.length) $('log-empty').textContent = 'Nothing matches this filter.';
      else $('log-empty').textContent = 'The app\'s calls show here: haptics, popups, chrome colours, buttons, storage, links, payments, and every member this client version does not support.';
      this.renderChips();
    },
    renderCounts() {
      $('n-events').textContent = this.rows.length;
      const bad = (this.counts.unsupported || 0) + (this.counts.error || 0);
      $('n-bad').hidden = !bad; $('n-bad').textContent = bad;
      $('n-bad').title = bad + ' unsupported call(s) or error(s)';
      this.renderChips();
    },
    renderChips() {
      const box = $('log-chips');
      const kinds = Object.keys(KINDS).filter((k) => this.counts[k] > 0 || this.filter === k);
      const sig = kinds.join(',');
      if (box.dataset.sig !== sig) {
        box.dataset.sig = sig;
        box.innerHTML = `<button type="button" role="radio" data-value="all">All <span class="n"></span></button>` +
          kinds.map((k) => `<button type="button" role="radio" data-value="${k}" data-kind data-k="${k}">${KINDS[k]} <span class="n"></span></button>`).join('');
      }
      box.querySelectorAll('button').forEach((b) => {
        const k = b.dataset.value;
        b.querySelector('.n').textContent = k === 'all' ? this.rows.length : this.counts[k] || 0;
        b.setAttribute('aria-checked', k === this.filter ? 'true' : 'false');
      });
    },
    clear() {
      this.rows = []; this.counts = {};
      this.render(); this.renderCounts();
    },
  };

  // ------------------------------------------------------------------ the app's own requests

  const Net = {
    map: new Map(),
    update(dev, d) {
      const key = dev.uid + ':' + d.id;
      let e = this.map.get(key);
      if (!e) {
        e = { dev: dev.label, method: d.method, url: d.url, status: null, ms: null, note: '' };
        this.map.set(key, e);
      }
      if (d.phase === 'end') {
        Object.assign(e, { status: d.status, ms: d.ms, note: d.note || '' });
        Log.add(dev, 'network', e.method + ' ' + e.url, `${e.status} · ${e.ms} ms${e.note ? ' · ' + e.note : ''}`);
      }
      this.renderRow(e);
      $('n-network').textContent = this.map.size;
    },
    match(e) { return !Log.query || (e.method + ' ' + e.url + ' ' + e.status + ' ' + e.note + ' ' + e.dev).toLowerCase().includes(Log.query); },
    renderRow(e) {
      const tr = e.tr || (e.tr = document.createElement('tr'));
      const st = e.status === null ? '<span class="st-wait">pending</span>'
        : `<span class="${typeof e.status === 'number' && e.status < 400 ? 'st-ok' : 'st-bad'}">${esc(e.status)}</span>`;
      tr.innerHTML = `<td>${esc(e.method)}</td><td class="path" title="${esc(e.url)}">${Stand.matrix ? `<span class="dev-tag">${esc(e.dev)}</span>` : ''}${esc(e.url)}</td>` +
        `<td>${st}</td><td class="ms">${e.ms === null ? '' : e.ms + ' ms'}</td><td class="note">${esc(e.note)}</td>`;
      tr.hidden = !this.match(e);
      if (!tr.parentNode) $('net-rows').append(tr);
      $('net-empty').hidden = this.map.size > 0;
    },
    render() { this.map.forEach((e) => this.renderRow(e)); $('net-empty').hidden = this.map.size > 0; },
    clear() { this.map.clear(); $('net-rows').replaceChildren(); $('n-network').textContent = 0; $('net-empty').hidden = false; },
  };

  // ------------------------------------------------------------------ layout audit (_kit/tma-audit.mjs)

  const Audit = {
    run() {
      const d = Stand.selected;
      const w = d && d.phase !== 'closed' && d.frame.contentWindow;
      if (!w || typeof w.tmaAudit !== 'function') return toast('Launch the app first: the audit measures the screen inside it');
      $('audit-run').disabled = true;
      Promise.resolve(w.tmaAudit({ outline: $('audit-outline').checked }))
        .catch(() => toast('The audit failed: see Errors in Events'))
        .finally(() => { $('audit-run').disabled = false; });
    },
    show(dev, r) {
      const list = $('audit-findings');
      $('audit-empty').hidden = true;
      $('audit-summary').textContent = `${r.errors} error(s), ${r.warnings} warning(s) on ${r.surfaces} surfaces` +
        (Stand.matrix ? ' · ' + dev.label : '') + ' · ' + new Date().toLocaleTimeString();
      list.innerHTML = r.findings.length ? r.findings.map((f) => `<li><span class="lvl lvl-${f.level === 'error' ? 'error' : 'warn'}">${f.level === 'error' ? 'error' : 'warning'}</span>` +
        `<span class="rule">${esc(f.rule)}</span><span>${esc(f.msg)}</span></li>`).join('')
        : `<li class="ok">${icon('check')}No findings: gaps, insets and radii follow the rules on this screen.</li>`;
      const n = $('n-layout'), bad = r.errors + r.warnings;
      n.hidden = false; n.textContent = bad;
      n.className = 'count' + (r.errors ? ' count-bad' : r.warnings ? ' count-warn' : '');
      if (AUDIT && !this.shown) { this.shown = true; Tabs.bottom('layout'); }
    },
  };

  // ------------------------------------------------------------------ inspector

  const kv = (rows) => `<dl class="kv">${rows.filter(Boolean).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join('')}</dl>`;
  const sw = (c) => `<span class="sw" style="background:${hex(c)}"></span>`;
  const onOff = (v, on, off) => `<span class="${v ? 'on' : 'off'}">${v ? on : off}</span>`;
  const insetText = (i) => {
    const sides = ['top', 'bottom', 'left', 'right'].filter((s) => i[s]);
    return sides.length ? sides.map((s) => `${s} ${i[s]}`).join(' · ') : '<span class="off">0 on every side</span>';
  };
  let themeOpen = false;

  const Inspector = {
    tab: ['state', 'launch', 'storage'].includes(ui.itab) ? ui.itab : 'state',
    render() {
      const d = Stand.selected, box = $('inspector');
      if (!d) { box.innerHTML = ''; return; }
      const top = box.scrollTop;
      box.innerHTML = this[this.tab](d);
      box.scrollTop = top;
    },
    state(d) {
      const v8 = atLeast(d.o.version, '8.0'), ins = d.insets(), vp = d.viewport();
      const ready = d.readyMs != null ? `<span class="on">called at ${d.readyMs} ms</span>`
        : d.phase === 'closed' ? '<span class="off">—</span>'
        : d.late ? '<span class="warn">not called</span>' : '<span class="off">waiting…</span>';
      const life = d.phase === 'closed' ? '<span class="off">closed</span>' : d.active ? '<span class="on">active</span>' : '<span class="warn">minimized</span>';
      const head = (title) => `<h3>${title}${Stand.matrix ? `<span class="muted">${esc(d.label)}</span>` : ''}</h3>`;
      const btn = (name, b, primary) => {
        if (!b) return `<div class="btn-card"><div class="btn-card-head">${name}<span class="tag">not used</span></div></div>`;
        const bg = b.color || (primary ? d.theme.button_color : d.color('bottomBar'));
        const fg = b.textColor || (primary ? d.theme.button_text_color : d.theme.button_color);
        const ring = !primary && !b.color ? `;box-shadow:inset 0 0 0 1.5px ${hex(d.theme.button_color)}` : '';
        const tags = [b.isActive ? 'active' : 'disabled', b.isProgressVisible && 'progress', b.hasShineEffect && 'shine',
          !primary && 'position ' + b.position, b.iconCustomEmojiId && 'emoji icon'].filter(Boolean);
        return `<div class="btn-card"><div class="btn-card-head">${name}${onOff(b.isVisible, 'shown', 'hidden')}</div>` +
          `<div class="btn-mini" style="background:${hex(bg)};color:${hex(fg)}${ring}">${esc(b.text || ' ')}</div>` +
          `<div class="btn-tags">${tags.map((t) => `<span class="tag">${esc(t)}</span>`).join('')}</div></div>`;
      };
      const colour = (which) => `${sw(d.color(which))}${esc(d.color(which))}<span class="sub">${d.keys[which]
        ? esc(d.keys[which]) : 'Telegram default'}</span>`;
      return `<section class="insp">${head('Lifecycle')}${kv([
        ['ready()', ready],
        ['Page load', d.loadMs != null ? d.loadMs + ' ms' : '<span class="off">…</span>'],
        ['State', life],
      ])}</section>` +
      `<section class="insp"><h3>Viewport</h3>${kv([
        ['Mode', esc(MODE[d.mode]) + (d.mode === 'compact' ? ' <span class="tag">isExpanded false</span>' : '')],
        ['Size', `${vp.w} × ${vp.h}`],
        ['Safe area', v8 ? insetText(ins.safe) : '<span class="off">needs 8.0</span>'],
        ['Content safe area', v8 ? insetText(ins.content) : '<span class="off">needs 8.0</span>'],
      ])}</section>` +
      `<section class="insp"><h3>Header</h3>${kv([
        ['Colour', colour('header')],
        ['Background', colour('background')],
        ['BackButton', onOff(d.back, 'shown', 'hidden')],
        ['SettingsButton', onOff(d.settings, 'in the menu', 'hidden')],
      ])}</section>` +
      `<section class="insp"><h3>Bottom bar</h3>${kv([['Colour', colour('bottomBar')]])}` +
        `${btn('MainButton', d.buttons.main, true)}${btn('SecondaryButton', d.buttons.secondary, false)}</section>` +
      `<section class="insp"><h3>Behaviour</h3>${kv([
        ['Closing confirmation', onOff(d.flags.closingConfirmation, 'on', 'off')],
        ['Vertical swipes', onOff(d.flags.verticalSwipes, 'on', 'off')],
        ['Orientation', d.flags.orientationLocked ? '<span class="on">locked</span>' : '<span class="off">free</span>'],
      ])}</section>` +
      `<section class="insp"><h3>Theme <span class="muted">${d.scheme === 'dark' ? 'night' : 'day'}, ${d.o.platform === 'android' ? 'Android' : 'iOS'} palette</span></h3>` +
        `<details class="more" id="theme-details"${themeOpen ? ' open' : ''}><summary>${Object.keys(d.theme).length} theme parameters</summary><ul class="theme-grid">` +
        Object.entries(d.theme).map(([k, v]) => `<li>${sw(v)}<span>${esc(k)}</span><span>${esc(v)}</span></li>`).join('') +
        `</ul></details><p class="note">Approximations of Telegram's defaults; real users bring their own themes.</p></section>`;
    },
    launch(d) {
      const unsafe = {};
      new URLSearchParams(d.initData).forEach((v, k) => { try { unsafe[k] = /^[[{]/.test(v) ? JSON.parse(v) : v; } catch (e) { unsafe[k] = v; } });
      return `<section class="insp"><h3>Launch</h3>${kv([
        ['Platform', esc(d.o.platform)],
        ['Version', esc(d.o.version)],
        ['Language', esc(d.o.lang)],
        ['start_param', d.o.start ? esc(d.o.start) : '<span class="off">none</span>'],
        ['Mode at launch', esc(MODE[d.o.mode])],
        d.o.platform === 'android' && ['Performance class', esc(d.o.perf)],
      ])}</section>` +
      `<section class="insp"><h3>initDataUnsafe</h3><pre class="json">${esc(JSON.stringify(unsafe, null, 2))}</pre></section>` +
      `<section class="insp"><div class="copy-row"><h3 style="margin:0">initData</h3><button type="button" class="btn btn-ghost btn-sm" data-copy="initData">${icon('copy')}Copy</button></div>` +
        `<pre class="json">${esc(d.initData)}</pre><p class="note">The hash is <code>mock-unsigned</code>: a server that checks the signature must refuse it.` +
        ' Test signatures with the server examples, not here.</p></section>';
    },
    storage() {
      const names = ['CloudStorage', 'DeviceStorage', 'SecureStorage'];
      return names.map((n) => {
        const items = storage[n] || {}, keys = Object.keys(items);
        return `<section class="insp"><div class="copy-row"><h3 style="margin:0">${n} <span class="muted">${keys.length} key(s)</span></h3>` +
          (keys.length ? `<button type="button" class="btn btn-ghost btn-sm" data-clear="${n}">${icon('ban')}Clear</button>` : '') + '</div>' +
          (keys.length ? `<table class="store">${keys.map((k) => `<tr><td>${esc(k)}</td><td>${esc(items[k])}</td></tr>`).join('')}</table>`
            : '<p class="note">Nothing stored yet.</p>') + '</section>';
      }).join('') + '<section class="insp"><p class="note" style="margin:0">Kept across relaunches in this tab, as Telegram keeps them ' +
        'between launches. Clear one to test a first launch.</p></section>';
    },
  };
  $('inspector').addEventListener('toggle', (e) => { if (e.target.id === 'theme-details') themeOpen = e.target.open; }, true);
  $('inspector').addEventListener('click', (e) => {
    const c = e.target.closest('[data-copy]'), clr = e.target.closest('[data-clear]');
    if (c && Stand.selected) copy(Stand.selected.initData, 'initData copied');
    if (clr) {
      const name = clr.dataset.clear;
      storage[name] = {}; saveStorage();
      Stand.devices.forEach((d) => d.send('state', { storage: { [name]: {} } }));
      Log.add(Stand.selected, 'stand', name + ' cleared', 'the next read finds nothing, like a first launch');
      changed();
    }
  });

  // ------------------------------------------------------------------ status in the address bar

  function renderStatus() {
    const d = Stand.selected;
    $('address-text').innerHTML = `${esc(location.host)}<b>${esc(CONFIG.app)}</b>${S.start ? esc('?tgWebAppStartParam=' + S.start) : ''}`;
    $('address').title = location.origin + CONFIG.app;
    let tone = 'busy', text = 'loading';
    if (d) {
      if (d.phase === 'closed') { tone = 'off'; text = 'closed'; }
      else if (!d.active) { tone = 'warn'; text = 'minimized'; }
      else if (d.phase === 'ready') { tone = 'ok'; text = 'ready · ' + d.readyMs + ' ms'; }
      else if (d.late) { tone = 'warn'; text = 'ready() not called'; }
      else if (d.phase === 'loaded') { text = 'waiting for ready()'; }
    }
    $('status').dataset.tone = tone; $('status-text').textContent = text;
    const min = $('act-minimize');
    min.querySelector('span').textContent = d && !d.active ? 'Restore' : 'Minimize';
    min.querySelector('use').setAttribute('href', d && !d.active ? '#i-maximize-2' : '#i-minimize-2');
  }

  // A timer, not requestAnimationFrame: the panels stay current in a background tab and for scripts reading them.
  let pending = false;
  function changed() {
    if (pending) return;
    pending = true;
    setTimeout(() => {
      pending = false;
      Inspector.render(); renderStatus();
      if (!Stand.matrix && Stand.selected) setRadio($('c-mode'), Stand.selected.mode);
    }, 0);
  }

  // ------------------------------------------------------------------ the stage: one device or the matrix

  const MATRIX = [];
  for (const platform of ['ios', 'android']) for (const scheme of ['light', 'dark']) for (const width of [320, 390, 430]) {
    MATRIX.push({ platform, scheme, width, mode: 'full', height: 700 });
  }
  MATRIX.push({ platform: 'ios', scheme: 'dark', width: 390, mode: 'fullscreen', height: 760 },
    { platform: 'android', scheme: 'light', width: 390, mode: 'fullscreen', height: 760 },
    { platform: 'ios', scheme: 'light', width: 390, mode: 'compact', height: 760 });

  const Stand = {
    devices: [], selected: null, matrix: false,
    opts(over) {
      return Object.assign({ platform: S.platform, scheme: S.scheme, width: +S.width, mode: S.mode, version: S.version, start: S.start,
        perf: S.perf, lang: S.lang, height: HEIGHT || undefined }, over);
    },
    render() {
      const stage = $('stage');
      stage.replaceChildren(); this.devices = [];
      this.matrix = S.view === 'matrix';
      stage.className = 'stage' + (this.matrix ? ' matrix' : '');
      const cells = this.matrix ? MATRIX : [{}];
      for (const c of cells) {
        const o = this.opts(c);
        const label = `${PLATFORM[o.platform]} · ${o.scheme} · ${o.width}` + (o.mode !== 'full' ? ' · ' + o.mode : '');
        const d = new Device(stage, o, label);
        this.devices.push(d);
        Log.mark(d, 'launched');
      }
      this.select(this.devices[0]);
      this.fit(); syncControls(); Log.render(); Net.render();
    },
    select(d) {
      if (!d || d === this.selected) return;
      this.selected = d;
      this.devices.forEach((x) => x.wrap.classList.toggle('is-selected', x === d && this.matrix));
      changed();
    },
    fit() {
      const c = $('canvas'), w = c.clientWidth, h = c.clientHeight;
      if (!this.devices.length || !w) return;
      const z = S.zoom === 'fit' ? 0 : +S.zoom / 100;
      if (this.matrix) {
        const cols = w < 700 ? 2 : 3, maxW = Math.max(...this.devices.map((d) => d.outerW()));
        const s = z || Math.min(1, Math.max(0.25, (w - 80 - 36 * (cols - 1)) / (cols * maxW)));
        $('stage').style.setProperty('--cols', cols);
        this.devices.forEach((d) => d.setScale(s));
      } else {
        const d = this.devices[0];
        d.setScale(z || Math.max(0.2, Math.min(1, (w - 80) / d.outerW(), (h - 56 - 34) / d.outerH())));
      }
    },
    relaunchAll() { this.devices.forEach((d) => d.relaunch()); },
  };

  // Clicking into an app frame selects its device (the click itself never reaches this page).
  window.addEventListener('blur', () => setTimeout(() => {
    const f = document.activeElement;
    if (f && f.tagName === 'IFRAME') Stand.select(Stand.devices.find((d) => d.frame === f));
  }, 0));
  window.addEventListener('message', (ev) => {
    const m = ev.data;
    if (ev.origin !== location.origin || !m || m.__tma !== 1) return;
    const dev = Stand.devices.find((d) => d.frame.contentWindow === ev.source);
    if (dev) dev.onMessage(m);
  });

  // ------------------------------------------------------------------ controls

  function fillSelects() {
    const ver = $('c-version');
    CONFIG.versions.slice().reverse().forEach((v) => {
      const o = document.createElement('option');
      o.value = v; o.textContent = v === NEWEST ? v + ' · newest' : v;
      ver.append(o);
    });
    const wid = $('c-width');
    const widths = WIDTHS.slice();
    if (!widths.some(([w]) => String(w) === S.width)) widths.push([+S.width, 'custom']);
    widths.forEach(([w, name]) => {
      const o = document.createElement('option');
      o.value = String(w); o.textContent = `${w} × ${HEIGHT || CONFIG.heights[String(w)] || 800} · ${name}`;
      wid.append(o);
    });
  }
  function syncControls() {
    for (const k of ['version', 'lang', 'perf', 'style', 'invoice', 'network', 'width', 'zoom']) $('c-' + k).value = S[k];
    $('c-start').value = S.start;
    setRadio($('c-platform'), S.platform);
    setRadio($('c-scheme'), Stand.matrix ? '' : (Stand.selected ? Stand.selected.scheme : S.scheme));
    setRadio($('c-mode'), Stand.matrix ? '' : (Stand.selected ? Stand.selected.mode : S.mode));
    const m = Stand.matrix;
    for (const id of ['c-platform', 'c-scheme', 'c-mode']) {
      $(id).setAttribute('aria-disabled', m ? 'true' : 'false');
      $(id).title = m ? 'The matrix shows every platform, theme and width at once' : '';
    }
    $('c-width').disabled = m;
    $('f-perf').hidden = !m && S.platform !== 'android';
    $('view-device').setAttribute('aria-selected', m ? 'false' : 'true');
    $('view-matrix').setAttribute('aria-selected', m ? 'true' : 'false');
    $('c-start-apply').disabled = true;
    refreshSelects();
    renderStatus();
  }
  function relaunchWith(key, value) {
    S[key] = value; writeUrl(); Stand.render();
  }

  onRadio($('c-platform'), (v) => relaunchWith('platform', v));
  onRadio($('c-scheme'), (v) => {
    S.scheme = v; writeUrl(); setRadio($('c-scheme'), v);
    Stand.devices.forEach((d) => { d.o.scheme = v; d.setScheme(v); });
  });
  onRadio($('c-mode'), (v) => {
    S.mode = v; writeUrl();
    Stand.devices.forEach((d) => { d.o.mode = v; d.setMode(v, 'the user'); });
    changed();
  });
  $('c-width').onchange = (e) => relaunchWith('width', e.target.value);
  $('c-zoom').onchange = (e) => { S.zoom = e.target.value; writeUrl(); Stand.fit(); };
  for (const k of ['version', 'lang', 'perf']) $('c-' + k).onchange = (e) => relaunchWith(k, e.target.value);
  for (const k of ['network', 'invoice', 'style']) {
    $('c-' + k).onchange = (e) => {
      S[k] = e.target.value; writeUrl();
      Stand.devices.forEach((d) => d.setLive(k, S[k]));
      const shown = e.target.selectedOptions[0].textContent;
      Log.add(Stand.selected, 'stand', { network: 'network', invoice: 'invoice outcome', style: 'style preset' }[k] + ' → ' + shown,
        k === 'style' ? 'data-tma-style on <html>' : 'applies to the next request');
    };
  }
  const startOk = (v) => /^[A-Za-z0-9_-]*$/.test(v);
  $('c-start').addEventListener('input', (e) => {
    const v = e.target.value.trim();
    $('c-start-apply').disabled = v === S.start || !startOk(v);
    e.target.setAttribute('aria-invalid', startOk(v) ? 'false' : 'true');
    e.target.title = startOk(v) ? '' : 'Telegram allows only A-Z, a-z, 0-9, _ and - (up to 512)';
  });
  const applyStart = () => {
    const v = $('c-start').value.trim();
    if (!startOk(v)) return toast('start_param: only A-Z, a-z, 0-9, _ and -');
    if (v !== S.start) relaunchWith('start', v);
  };
  $('c-start-apply').onclick = applyStart;
  $('c-start').addEventListener('keydown', (e) => { if (e.key === 'Enter') applyStart(); });

  $('view-device').onclick = () => { if (S.view !== 'device') relaunchWith('view', 'device'); };
  $('view-matrix').onclick = () => { if (S.view !== 'matrix') relaunchWith('view', 'matrix'); };
  $('relaunch').onclick = () => Stand.relaunchAll();
  $('act-relaunch').onclick = () => Stand.selected && Stand.selected.relaunch();
  $('act-back').onclick = () => Stand.selected && Stand.selected.systemBack();
  $('act-close').onclick = () => Stand.selected && Stand.selected.requestClose('Close tapped');
  $('act-minimize').onclick = () => Stand.selected && Stand.selected.setActive(!Stand.selected.active);
  $('copy-link').onclick = () => copy(location.href, 'Link copied: it opens this exact view');
  $('stand-theme').onclick = () => {
    const t = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = t; ui.theme = t; saveUi();
  };

  // ------------------------------------------------------------------ bottom panel and inspector tabs

  const Tabs = {
    bottom(name) {
      ui.btab = name; saveUi();
      for (const t of ['events', 'network', 'layout']) {
        $('tab-' + t).setAttribute('aria-selected', t === name ? 'true' : 'false');
        $('tab-' + t).tabIndex = t === name ? 0 : -1;
        $('pane-' + t).hidden = t !== name;
      }
      $('log-search').closest('.search').hidden = name === 'layout';
      $('log-clear').hidden = name === 'layout';
    },
    inspector(name) {
      Inspector.tab = name; ui.itab = name; saveUi();
      document.querySelectorAll('[data-itab]').forEach((b) => {
        b.setAttribute('aria-selected', b.dataset.itab === name ? 'true' : 'false');
        b.tabIndex = b.dataset.itab === name ? 0 : -1;
      });
      Inspector.render();
    },
  };
  for (const t of ['events', 'network', 'layout']) $('tab-' + t).onclick = () => Tabs.bottom(t);
  document.querySelectorAll('[data-itab]').forEach((b) => { b.onclick = () => Tabs.inspector(b.dataset.itab); });
  $('log-chips').addEventListener('click', (e) => {
    const b = e.target.closest('[role="radio"]');
    if (b) { Log.filter = b.dataset.value; Log.render(); }
  });
  $('log-search').addEventListener('input', (e) => { Log.query = e.target.value.trim().toLowerCase(); Log.render(); Net.render(); });
  $('log-clear').onclick = () => { Log.clear(); Net.clear(); };
  $('audit-run').onclick = () => Audit.run();

  // ------------------------------------------------------------------ panels: toggles and resizing

  const ws = $('workspace');
  const panels = {
    left: !PANELS_OFF && !narrow.matches && ui.left,
    right: !PANELS_OFF && !narrow.matches && ui.right && ('right' in saved || innerWidth >= 1200),
    bottom: !PANELS_OFF && ui.bottom,
  };
  function applyPanels() {
    for (const p of ['left', 'right', 'bottom']) {
      ws.dataset[p] = panels[p] ? '1' : '0';
      document.querySelector(`.toggle[data-panel="${p}"]`).setAttribute('aria-pressed', panels[p] ? 'true' : 'false');
    }
    ws.style.setProperty('--left-w', ui.leftW + 'px');
    ws.style.setProperty('--right-w', ui.rightW + 'px');
    $('panel-bottom').style.setProperty('--bottom-h', ui.bottomH + 'px');
    Stand.fit();
  }
  function togglePanel(p, on) {
    panels[p] = on === undefined ? !panels[p] : on;
    if (!PANELS_OFF && !(narrow.matches && p !== 'bottom')) { ui[p] = panels[p]; saveUi(); }
    if (narrow.matches && panels[p] && p !== 'bottom') panels[p === 'left' ? 'right' : 'left'] = false;  // one overlay at a time
    applyPanels();
  }
  document.querySelectorAll('.toggle[data-panel]').forEach((b) => { b.onclick = () => togglePanel(b.dataset.panel); });
  $('bottom-close').onclick = () => togglePanel('bottom', false);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && narrow.matches && (panels.left || panels.right)) { panels.left = panels.right = false; applyPanels(); }
  });
  $('canvas').addEventListener('pointerdown', () => {
    if (narrow.matches && (panels.left || panels.right)) { panels.left = panels.right = false; applyPanels(); }
  });
  narrow.addEventListener('change', () => {
    if (narrow.matches) { panels.left = panels.right = false; } else { panels.left = ui.left; panels.right = ui.right; }
    applyPanels();
  });

  const LIMITS = { left: [220, 440], right: [260, 520], bottom: [120, 0] };
  function resize(which, px) {
    const [lo, hiFixed] = LIMITS[which];
    const hi = which === 'bottom' ? Math.max(lo, $('panel-bottom').parentElement.clientHeight - 200) : hiFixed;
    const v = Math.round(Math.min(hi, Math.max(lo, px)));
    ui[which === 'left' ? 'leftW' : which === 'right' ? 'rightW' : 'bottomH'] = v;
    applyPanels();
  }
  document.querySelectorAll('[data-resize]').forEach((r) => {
    const which = r.dataset.resize;
    r.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      r.setPointerCapture(e.pointerId);
      r.classList.add('is-dragging'); document.body.classList.add('is-resizing');
      const box = ws.getBoundingClientRect(), center = $('panel-bottom').parentElement.getBoundingClientRect();
      const move = (ev) => resize(which, which === 'left' ? ev.clientX - box.left : which === 'right' ? box.right - ev.clientX : center.bottom - ev.clientY);
      const up = () => {
        r.removeEventListener('pointermove', move); r.removeEventListener('pointerup', up);
        r.classList.remove('is-dragging'); document.body.classList.remove('is-resizing'); saveUi();
      };
      r.addEventListener('pointermove', move); r.addEventListener('pointerup', up);
    });
    r.addEventListener('keydown', (e) => {
      const grow = { left: 'ArrowRight', right: 'ArrowLeft', bottom: 'ArrowUp' }[which];
      const shrink = { left: 'ArrowLeft', right: 'ArrowRight', bottom: 'ArrowDown' }[which];
      if (e.key !== grow && e.key !== shrink) return;
      e.preventDefault();
      const cur = ui[which === 'left' ? 'leftW' : which === 'right' ? 'rightW' : 'bottomH'];
      resize(which, cur + (e.key === grow ? 16 : -16)); saveUi();
    });
  });

  let fitFrame = 0;
  new ResizeObserver(() => { cancelAnimationFrame(fitFrame); fitFrame = requestAnimationFrame(() => Stand.fit()); }).observe($('canvas'));

  // ------------------------------------------------------------------ start

  $('app-title').textContent = CONFIG.title;
  document.title = CONFIG.title + ' · Mini App stand (mock)';
  fillSelects();
  document.querySelectorAll('.select > select').forEach(enhanceSelect);
  Tabs.bottom(['events', 'network', 'layout'].includes(ui.btab) ? ui.btab : 'events');
  Tabs.inspector(Inspector.tab);
  applyPanels();
  Stand.render();
}());
