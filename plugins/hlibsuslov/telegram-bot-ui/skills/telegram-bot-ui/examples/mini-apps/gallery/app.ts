// Kit gallery: renders every kit component and wires the native controls so each can be checked in the
// preview stand (platforms, schemes, widths, fullscreen, versions, styles) and on a real device.
import { createTma } from '../_kit/tma.ts';
import { formatGrams, formatStars, giftVars, limitedLeft, rarityPercent, rarityTier, starsText } from '../_kit/tg-values.ts';

const tma = createTma();
// English strings only; RTL languages are accepted so the stand's Language select shows the mirrored layout.
tma.locale(['en', 'ar', 'he', 'fa']);
const $ = (id: string) => document.getElementById(id) as HTMLElement;
const ICONS = '../_kit/icons.svg';
const GROUPS = ['text', 'structure', 'navigation', 'actions', 'settings', 'input', 'display', 'media', 'tables', 'overlays', 'telegram', 'device', 'icons'];
const icon = (id: string) => `<svg class="tma-icon" aria-hidden="true"><use href="${ICONS}#i-${id}"/></svg>`;

/* type scale: every role, regular and emphasized */
const ROLES: Array<[string, string]> = [['large-title', '34/41'], ['title1', '28/34'], ['title2', '22/28'], ['title3', '20/25'],
  ['headline', '17/22'], ['body', '17/22'], ['callout', '16/21'], ['subhead', '15/20'], ['footnote', '13/18'],
  ['caption1', '12/16'], ['caption2', '11/13']];
$('type-scale').replaceChildren(...ROLES.map(([role, size]) => {
  const row = document.createElement('p');
  row.style.margin = '0 0 var(--tma-s2)';
  row.innerHTML = `<span class="tma-text-${role}">${role}</span> <span class="tma-text-${role} is-em">emphasized</span> <span class="tma-caption">${size}</span>`;
  return row;
}));

/* colour roles: swatch + the resolved value, live */
const ROLE_VARS = ['--tma-page', '--tma-surface', '--tma-text', '--tma-hint', '--tma-subtitle', '--tma-accent', '--tma-accent-text',
  '--tma-link', '--tma-danger', '--tma-success', '--tma-separator', '--tma-fill', '--tma-tonal', '--tma-brand'];
function renderRoles(): void {
  $('roles').replaceChildren(...ROLE_VARS.map((v) => {
    const li = document.createElement('li');
    li.innerHTML = `<div class="tma-cell"><span class="tma-avatar" style="background:var(${v});box-shadow:inset 0 0 0 1px var(--tma-separator)"></span>
      <span class="tma-cell__body"><span class="tma-cell__title tma-code" style="background:none;padding:0">${v}</span></span>
      <span class="tma-cell__after tma-caption"></span></div>`;
    // the resolved value comes from the client's theme: set it as text, never as markup
    li.querySelector('.tma-cell__after')!.textContent = getComputedStyle(document.documentElement).getPropertyValue(v).trim().slice(0, 22);
    return li;
  }));
}
renderRoles();
tma.on('themeChanged', renderRoles);

/* group filter chips */
let group = 'all';
function renderGroups(): void {
  $('groups').replaceChildren(...['all', ...GROUPS].map((g) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'tma-chip'; b.setAttribute('role', 'tab');
    b.setAttribute('aria-pressed', String(g === group));
    b.textContent = g === 'all' ? 'All' : g[0].toUpperCase() + g.slice(1);
    b.onclick = () => { if (g !== group) { group = g; tma.haptic.select(); renderGroups(); filter(); } };
    return b;
  }));
}
function filter(): void {
  for (const s of document.querySelectorAll<HTMLElement>('[data-group]')) s.hidden = group !== 'all' && s.dataset.group !== group;
}
renderGroups();

/* icons grid from the sprite */
fetch(ICONS).then((r) => r.text()).then((svg) => {
  const ids = [...svg.matchAll(/<symbol id="i-([a-z-]+)"/g)].map((m) => m[1]);
  $('icon-count').textContent = `${ids.length} icons`;
  $('icons').replaceChildren(...ids.map((id) => {
    const d = document.createElement('div');
    d.style.cssText = 'display:grid;justify-items:center;gap:4px;text-align:center';
    d.innerHTML = `${icon(id)}<span class="tma-caption" style="overflow-wrap:anywhere">${id}</span>`;
    return d;
  }));
}).catch(() => { $('icon-count').textContent = 'icons.svg did not load'; });

/* Telegram's own values (telegram-elements.md): sample API data, formatted by the kit */
$('stars-balance').textContent = formatStars(1250);
for (const el of document.querySelectorAll<HTMLElement>('[data-nano]')) el.textContent = formatGrams(el.dataset.nano ?? '0', { signed: 'signed' in el.dataset });
// Regular gifts sit on plain surface tiles, as in Telegram's gift catalogue; Gift.background (9.3), when a
// gift has one, colours the tile through giftVars(). The unique gift below shows the backdrop colours.
type RegularGift = { background?: { center_color: number; edge_color: number; text_color: number }; remaining?: number; total?: number };
const GIFTS: Record<string, RegularGift> = { cake: { remaining: 142, total: 5000 }, plant: {} };
for (const b of document.querySelectorAll<HTMLElement>('[data-gift]')) {
  const g = GIFTS[b.dataset.gift ?? ''];
  if (!g) continue;
  if (g.background) for (const [k, v] of Object.entries(giftVars(g.background))) b.style.setProperty(k, v);
  const counter = b.querySelector<HTMLElement>('.tma-limited');
  if (counter && g.remaining !== undefined && g.total !== undefined) {
    const left = limitedLeft(g.remaining, g.total);
    (counter.querySelector('i') as HTMLElement).style.width = `${Math.max(2, left.ratio * 100)}%`;
    (counter.lastElementChild as HTMLElement).textContent = left.text;
  }
}
const UNIQUE = {
  model: { name: 'Fern', rarity_per_mille: 12 }, symbol: { name: 'Leaf', rarity_per_mille: 25 },
  backdrop: { name: 'Moss', rarity_per_mille: 15, colors: { center_color: 0x5b8a72, edge_color: 0x2f4f3f, symbol_color: 0x1e3329, text_color: 0xffffff } },
  crafted: 'rare',
};
for (const [k, v] of Object.entries(giftVars(UNIQUE.backdrop.colors))) $('unique').style.setProperty(k, v);
$('unique').style.setProperty('--gift-symbol-image', `url("${new URL('media/gift-symbol.svg', location.href).href}")`);
$('unique-attrs').replaceChildren(...([['Model', UNIQUE.model], ['Backdrop', UNIQUE.backdrop], ['Symbol', UNIQUE.symbol]] as const).map(([label, a]) => {
  const row = document.createElement('div');
  const dt = document.createElement('dt'); dt.textContent = label;
  const dd = document.createElement('dd');
  dd.append(`${a.name} `);
  const chip = document.createElement('span'); chip.className = 'tma-rarity'; chip.textContent = rarityPercent(a.rarity_per_mille) ?? '';
  dd.append(chip);
  row.append(dt, dd);
  return row;
}), (() => {
  const row = document.createElement('div');
  row.innerHTML = '<dt>Crafted rarity</dt><dd><span class="tma-rarity"></span></dd>';
  row.querySelector('.tma-rarity')!.textContent = rarityTier(UNIQUE.crafted); // the markup above always has the chip
  return row;
})());
const user = (tma.tg as unknown as { initDataUnsafe?: { user?: { is_premium?: boolean } } } | null)?.initDataUnsafe?.user;
$('premium-perk').textContent = user?.is_premium ? 'You have it: two extra saved recipes are on' : 'Subscribers get two extra saved recipes';
$('demo-stars').onclick = () => {
  tma.mainButton({ text: `Pay ${starsText(120)}`, onClick: () => { toast('This demo opens no invoice'); tma.mainButton(null); } });
};
$('demo-boost').onclick = () => {
  const url = 'https://t.me/boost/example_club';
  if (tma.inTelegram && tma.has('6.1')) (tma.tg as unknown as { openTelegramLink(u: string): void }).openTelegramLink(url);
  else toast('Boosts open in Telegram');
};

/* device: haptics playground, tilt, location (haptics-and-device.md) */
const chip = (label: string, run: () => boolean) => {
  const b = document.createElement('button');
  b.type = 'button'; b.className = 'tma-chip'; b.textContent = label;
  b.onclick = () => { if (!run()) toast(tma.haptic.enabled ? 'No haptics here (needs Telegram 6.1+)' : 'Vibration is off in this app'); };
  return b;
};
$('impacts').replaceChildren(...(['light', 'medium', 'heavy', 'rigid', 'soft'] as const).map((s) => chip(s[0].toUpperCase() + s.slice(1), () => tma.haptic.impact(s))));
$('notifies').replaceChildren(chip('Success', tma.haptic.success), chip('Warning', tma.haptic.warning), chip('Error', tma.haptic.error), chip('Selection', tma.haptic.select));
($('haptic-on') as HTMLInputElement).onchange = (e) => { tma.haptic.setEnabled((e.target as HTMLInputElement).checked); tma.haptic.select(); };
let stopTilt: (() => void) | null = null;
$('demo-tilt').onclick = () => {
  if (stopTilt) { stopTilt(); stopTilt = null; $('tilt').style.transform = ''; $('tilt-v').textContent = 'Stopped'; return; }
  stopTilt = tma.motion('orientation', (r) => {
    const rx = Math.max(-12, Math.min(12, (r.beta ?? 0) * 30)), ry = Math.max(-12, Math.min(12, (r.gamma ?? 0) * 30));
    $('tilt').style.transform = `perspective(600px) rotateX(${rx.toFixed(1)}deg) rotateY(${ry.toFixed(1)}deg)`;
    $('tilt-v').textContent = `beta ${(r.beta ?? 0).toFixed(2)} · gamma ${(r.gamma ?? 0).toFixed(2)} rad`;
  }, { refreshMs: 50 });
  if (!stopTilt) $('tilt-v').textContent = 'Motion sensors need Telegram 8.0 on a phone';
  else tma.haptic.tap();
};
$('demo-location').onclick = async () => {
  $('loc-v').textContent = 'Locating…';
  const d = await tma.location();
  $('loc-v').textContent = d ? `Central, 400 m away (±${d.horizontal_accuracy ?? '?'} m)` : 'Location is off: choose a pickup point from the list';
  if (d) tma.haptic.success();
};

/* selection controls */
for (const seg of document.querySelectorAll<HTMLElement>('.tma-segmented')) {
  seg.addEventListener('click', (e) => {
    const b = (e.target as HTMLElement).closest('button');
    if (!b || b.getAttribute('aria-selected') === 'true') return;
    for (const x of seg.querySelectorAll('button')) x.setAttribute('aria-selected', String(x === b));
    tma.haptic.select();
  });
}
$('milk').addEventListener('click', (e) => {
  const b = (e.target as HTMLElement).closest('[role="option"]');
  if (!b) return;
  for (const x of $('milk').querySelectorAll('[role="option"]')) x.setAttribute('aria-selected', String(x === b));
  tma.haptic.select();
});
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-step]')) {
  b.onclick = () => { const o = $('shots'); o.textContent = String(Math.min(4, Math.max(0, Number(o.textContent) + Number(b.dataset.step)))); tma.haptic.select(); };
}
const fmt = (id: string, out: string, f: (v: string) => string) => {
  const input = $(id) as HTMLInputElement;
  input.onchange = () => { if (input.value) $(out).textContent = f(input.value); tma.haptic.select(); };
};
fmt('date-in', 'date-v', (v) => new Date(v).toLocaleDateString(undefined, { day: 'numeric', month: 'short' }));
fmt('time-in', 'time-v', (v) => v);
const slider = $('f5') as HTMLInputElement;
slider.oninput = () => { $('f5o').textContent = slider.value; };
/* rating: a radio group of five stars; the chosen value is also said in words */
const RATE_WORDS = ['Poor', 'Fair', 'Good', 'Very good', 'Excellent'];
function setRating(value: number): void {
  for (const [i, x] of [...$('rating').children].entries()) {
    x.classList.toggle('is-on', i < value);
    x.setAttribute('aria-checked', String(i + 1 === value));
    x.setAttribute('tabindex', i + 1 === (value || 1) ? '0' : '-1');
  }
  $('rate-v').textContent = value ? `${RATE_WORDS[value - 1]} · ${value} of 5` : 'Tap a star to rate';
}
$('rating').replaceChildren(...[1, 2, 3, 4, 5].map((n) => {
  const b = document.createElement('button');
  b.type = 'button'; b.setAttribute('role', 'radio'); b.setAttribute('aria-label', `${n} of 5`);
  b.innerHTML = icon('star');
  b.onclick = () => { setRating(n); tma.haptic.select(); };
  b.onkeydown = (e) => {
    const step = e.key === 'ArrowRight' || e.key === 'ArrowUp' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowDown' ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const next = Math.min(5, Math.max(1, n + step));
    setRating(next); ($('rating').children[next - 1] as HTMLElement).focus(); tma.haptic.select();
  };
  return b;
}));
setRating(0);
for (const pin of document.querySelectorAll<HTMLInputElement>('.tma-pin input')) {
  pin.addEventListener('input', () => { (pin.nextElementSibling as HTMLInputElement | null)?.focus(); });
}

/* pop-up menu */
const trigger = $('size-trigger');
const menu = $('size-menu');
trigger.onclick = () => { menu.hidden = !menu.hidden; trigger.setAttribute('aria-expanded', String(!menu.hidden)); };
menu.addEventListener('click', (e) => {
  const b = (e.target as HTMLElement).closest('button');
  if (!b) return;
  trigger.firstChild!.textContent = b.textContent;
  menu.hidden = true; trigger.setAttribute('aria-expanded', 'false'); tma.haptic.select();
});

/* banner dismissal is remembered */
const store = tma.store();
void store.get('promo-hidden').then((v) => { if (v === '1') $('promo').hidden = true; });
$('promo').querySelector('button')!.addEventListener('click', () => { $('promo').hidden = true; void store.set('promo-hidden', '1'); });

/* level-2 screen with BackButton */
function closeDetail(): void { tma.nav.pop('detail'); $('detail').hidden = true; $('home').hidden = false; $('tabbar').hidden = false; }
$('open-screen').onclick = () => {
  $('home').hidden = true; $('detail').hidden = false; $('tabbar').hidden = true;
  tma.nav.push({ id: 'detail', kind: 'screen', onBack: closeDetail });
};

/* native buttons and haptics */
$('demo-main').onclick = () => {
  tma.mainButton({ text: 'Pay 120 points', onClick: async () => { await new Promise((r) => setTimeout(r, 600)); tma.haptic.success(); toast('Paid with points'); tma.mainButton(null); tma.secondaryButton(null); } });
  if (!tma.secondaryButton({ text: 'Later', position: 'left', onClick: () => { tma.mainButton(null); tma.secondaryButton(null); } })) toast('SecondaryButton needs Bot API 7.10');
};
$('demo-haptics').onclick = () => { tma.haptic.select(); setTimeout(() => tma.haptic.tap(), 250); setTimeout(() => tma.haptic.success(), 500); };
$('demo-delete').onclick = async () => {
  const ok = await tma.confirm('Delete your order history? Points stay.', async () => true);
  if (ok) { tma.haptic.warning(); toast('Order history deleted'); }
};
$('demo-file').onclick = () => {
  if (tma.has('8.0')) (tma.tg as unknown as { downloadFile(p: { url: string; file_name: string }): void }).downloadFile({ url: `${location.origin}/receipt-1042.pdf`, file_name: 'Receipt 1042.pdf' });
  else toast('Downloads need Bot API 8.0');
};
$('ext-link').addEventListener('click', (e) => {
  if (!tma.inTelegram || !tma.has('6.1')) return;
  e.preventDefault();
  (tma.tg as unknown as { openLink(u: string): void }).openLink((e.currentTarget as HTMLAnchorElement).href);
});

/* overlays */
function openLayer(id: string): void {
  $('scrim').hidden = false; $(id).hidden = false;
  ($(id).querySelector('button') as HTMLButtonElement | null)?.focus();
  tma.nav.push({ id, kind: 'sheet', onBack: () => closeLayer(id) });
}
function closeLayer(id: string): void { tma.nav.pop(id); $(id).hidden = true; $('scrim').hidden = true; }
$('demo-sheet').onclick = () => openLayer('sheet');
$('demo-actions').onclick = () => openLayer('actions');
for (const id of ['sheet', 'actions']) $(id).addEventListener('click', (e) => { if ((e.target as HTMLElement).closest('[data-close]')) closeLayer(id); });
$('scrim').onclick = () => { for (const id of ['sheet', 'actions']) if (!$(id).hidden) closeLayer(id); };
$('demo-popup').onclick = () => {
  if (!tma.has('6.2')) { toast('Popups need Bot API 6.2'); return; }
  (tma.tg as unknown as { showPopup(p: unknown, cb: (id: string) => void): void }).showPopup({
    title: 'Cancel order 1042?', message: 'The barista has not started it yet. Your points come back.',
    buttons: [{ id: 'keep', type: 'default', text: 'Keep order' }, { id: 'cancel', type: 'destructive', text: 'Cancel order' }],
  }, (id) => { if (id === 'cancel') toast('Order cancelled'); });
};
$('demo-snack').onclick = () => toast('Saved to favourites');
let toastTimer = 0;
function toast(text: string): void {
  const s = $('snackbar');
  s.textContent = text; s.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { s.hidden = true; }, 2200);
}

/* QR slot: a decorative sample pattern (clearly labelled in the markup) */
const cells: string[] = [];
for (let y = 0; y < 21; y++) for (let x = 0; x < 21; x++) {
  const finder = (x < 8 && y < 8) || (x > 12 && y < 8) || (x < 8 && y > 12);
  if (!finder && ((x * 7 + y * 13 + x * y) % 5 < 2)) cells.push(`M${x} ${y}h1v1h-1z`);
}
$('qr-path').setAttribute('d', 'M0 0h7v7H0zM1 1v5h5V1zM2 2h3v3H2zM14 0h7v7h-7zM15 1v5h5V1zM16 2h3v3h-3zM0 14h7v7H0zM1 15v5h5v-5zM2 16h3v3H2z' + cells.join(''));
($('qr-path') as unknown as SVGPathElement).setAttribute('fill-rule', 'evenodd');

tma.start(); // fullscreen on iOS / Android (8.0+), the expanded sheet elsewhere
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
tma.ready();
