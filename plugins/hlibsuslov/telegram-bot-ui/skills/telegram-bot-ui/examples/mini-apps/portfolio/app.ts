// Points portfolio (fictional), dark-fintech style: recipe 95. Hero figure with privacy toggle, quick actions,
// one remembered promo, asset rows, bonus tab with a live countdown that pauses in the background, asset detail
// with a one-line chart and period control, MainButton + SecondaryButton, a one-time onboarding sheet.
import { createTma, parseStartParam } from '../_kit/tma.ts';

type Asset = { id: string; name: string; unit: string; amount: number; rate: number; change: number; about: string; points: number[] };

const tma = createTma();
const $ = (id: string) => document.getElementById(id) as HTMLElement;
const lang = (tma.tg as unknown as { initDataUnsafe?: { user?: { language_code?: string; first_name?: string } } } | null)?.initDataUnsafe?.user;
const num = new Intl.NumberFormat(lang?.language_code || 'en', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const pct = new Intl.NumberFormat(lang?.language_code || 'en', { maximumFractionDigits: 1, signDisplay: 'always' });
const store = tma.store();

const ASSETS: Asset[] = [
  { id: 'points', name: 'Coffee points', unit: 'pts', amount: 1240.5, rate: 1, change: 10.7, about: 'Earned on orders. 100 points pay for a filter coffee at any store.', points: [1120, 1132, 1128, 1160, 1190, 1205, 1240] },
  { id: 'beans', name: 'Bean credits', unit: 'cr', amount: 36, rate: 4, change: -2.5, about: 'Credits for bags of beans. They follow the roastery price list, so their value moves weekly.', points: [152, 150, 149, 151, 147, 146, 144] },
  { id: 'cups', name: 'Free cups', unit: 'cups', amount: 2, rate: 120, change: 0, about: 'One free cup for every ten orders. They never expire.', points: [240, 240, 240, 240, 240, 240, 240] },
];
const PERIODS = ['1D', '1W', '1M', '1Y', 'All'];
let hidden = false;
let current: Asset | null = null;
let period = '1W';

/* ---------------------------------------------------------------- home */
function figure(el: HTMLElement, value: number, unit: string): void {
  const [int, frac] = num.format(value).split(/(?=[.,]\d{2}$)/);
  el.classList.remove('is-loading');
  if (hidden) { el.textContent = '••••'; return; }
  el.textContent = int;
  const minor = document.createElement('span');
  minor.className = 'tma-figure__minor';
  minor.textContent = `${frac ?? ''} ${unit}`;
  el.append(minor);
}
function delta(el: HTMLElement, change: number, label: string): void {
  el.className = `tma-delta ${change > 0 ? 'is-up' : change < 0 ? 'is-down' : ''}`;
  el.textContent = `${change > 0 ? '↑' : change < 0 ? '↓' : '→'} ${pct.format(change)} % ${label}`;
}
function renderHome(): void {
  const total = ASSETS.reduce((s, a) => s + a.amount * a.rate, 0);
  figure($('balance'), total, 'pts');
  delta($('balance-delta'), 4.2, 'this week');
  $('assets-total').textContent = hidden ? '' : `${num.format(total)} pts in total`;
  $('assets').removeAttribute('aria-busy');
  $('assets').replaceChildren(...ASSETS.map((a) => {
    const li = document.createElement('li');
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'tma-cell is-2';
    b.innerHTML = `<span class="tma-avatar"></span><span class="tma-cell__body"><span class="tma-cell__title"></span><span class="tma-cell__subtitle"></span></span><span class="tma-cell__after"><strong></strong><span></span></span>`;
    (b.querySelector('.tma-avatar') as HTMLElement).textContent = a.name[0];
    (b.querySelector('.tma-cell__title') as HTMLElement).textContent = a.name;
    (b.querySelector('.tma-cell__subtitle') as HTMLElement).textContent = a.rate === 1 ? 'Base unit' : `${a.rate} pts each`;
    (b.querySelector('.tma-cell__after strong') as HTMLElement).textContent = hidden ? '••••' : `${num.format(a.amount)} ${a.unit}`;
    const ch = b.querySelector('.tma-cell__after span') as HTMLElement;
    ch.textContent = a.change ? `${pct.format(a.change)} %` : 'no change';
    if (a.change) ch.style.color = a.change > 0 ? 'var(--tma-success)' : 'var(--tma-danger)';
    b.onclick = () => openAsset(a);
    li.append(b);
    return li;
  }));
}
function setHidden(v: boolean): void {
  hidden = v;
  $('hide').setAttribute('aria-pressed', String(v));
  ($('hide').querySelector('span') as HTMLElement).textContent = v ? 'Show balance' : 'Hide balance';
  ($('hide').querySelector('use') as SVGUseElement).setAttribute('href', `../_kit/icons.svg#i-${v ? 'eye-off' : 'eye'}`);
  renderHome();
}
$('hide').onclick = () => {
  setHidden(!hidden);
  tma.haptic.select();
  void store.set('hide-balance', hidden ? '1' : '0');
};
for (const b of document.querySelectorAll<HTMLButtonElement>('[data-act]')) {
  b.onclick = () => { tma.haptic.tap(); toast(`${b.textContent?.trim()}: not part of this demo`); };
}

/* ---------------------------------------------------------------- promo moment, remembered */
void store.get('promo-closed').then((v) => { $('promo').hidden = v === '1'; });
$('promo').querySelector('button')!.addEventListener('click', () => { $('promo').hidden = true; void store.set('promo-closed', '1'); });

/* ---------------------------------------------------------------- bonus tab: live countdown, paused when inactive */
const eventAt = Date.now() + (8 * 24 * 3600 + 21 * 3600 + 6) * 1000;
let timer = 0;
function tick(): void {
  const s = Math.max(0, Math.floor((eventAt - Date.now()) / 1000));
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  $('countdown').textContent = `${d} days ${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}
function startTimer(): void { if (!timer && !$('bonus').hidden) { tick(); timer = window.setInterval(tick, 1000); } }
function stopTimer(): void { clearInterval(timer); timer = 0; }
tma.on('deactivated', stopTimer);
tma.on('activated', startTimer);
$('remind').onclick = () => { tma.haptic.success(); toast('We will remind you the day before'); };

/* ---------------------------------------------------------------- asset detail */
function chart(a: Asset): void {
  const pts = a.points.map((p) => p * a.rate / (a.id === 'points' ? 1 : a.rate));
  const min = Math.min(...pts), max = Math.max(...pts), span = max - min || 1;
  const xy = pts.map((p, i) => `${(i / (pts.length - 1)) * 270},${150 - ((p - min) / span) * 110}`).join(' ');
  const svg = $('chart');
  svg.classList.toggle('is-down', a.change < 0);
  svg.setAttribute('aria-label', `${a.name}, ${period}: from ${num.format(pts[0])} to ${num.format(pts[pts.length - 1])}`);
  svg.innerHTML = `<line class="tma-chart__grid" x1="0" y1="40" x2="270" y2="40"/><line class="tma-chart__grid" x1="0" y1="95" x2="270" y2="95"/><line class="tma-chart__grid" x1="0" y1="150" x2="270" y2="150"/><polyline class="tma-chart__line" points="${xy}"/><text class="tma-chart__label" x="278" y="44"></text><text class="tma-chart__label" x="278" y="154"></text>`;
  const labels = svg.querySelectorAll('text');
  labels[0].textContent = num.format(max).replace(/[.,]00$/, '');
  labels[1].textContent = num.format(min).replace(/[.,]00$/, '');
}
function renderPeriods(): void {
  $('period').replaceChildren(...PERIODS.map((p) => {
    const b = document.createElement('button');
    b.type = 'button'; b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(p === period)); b.textContent = p;
    b.onclick = () => { if (p !== period && current) { period = p; tma.haptic.select(); renderPeriods(); chart(current); } };
    return b;
  }));
}
function openAsset(a: Asset): void {
  current = a;
  ($('a-icon')).textContent = a.name[0];
  $('a-name').textContent = a.name;
  $('a-sub').textContent = a.rate === 1 ? 'Base unit' : `${a.rate} pts each`;
  figure($('a-value'), a.amount, a.unit);
  delta($('a-delta'), a.change, 'this week');
  $('a-about').textContent = a.about;
  renderPeriods(); chart(a);
  void store.get(`watch-${a.id}`).then((v) => $('watch').setAttribute('aria-pressed', String(v === '1')));
  show('asset');
  tma.nav.push({ id: 'asset', kind: 'screen', onBack: closeAsset });
  if ($('onboarding').hidden) assetButtons(a); // the onboarding sheet owns the bottom bar while it is open
}
function assetButtons(a: Asset): void {
  tma.mainButton({ text: `Redeem ${a.name.toLowerCase()}`, onClick: () => { tma.haptic.success(); toast('Show the pay code at the counter'); } });
  tma.secondaryButton({ text: 'Send', position: 'left', onClick: () => toast('Sending is not part of this demo') });
}
function closeAsset(): void {
  tma.nav.pop('asset'); current = null;
  tma.mainButton(null); tma.secondaryButton(null);
  show('home', true);
}
$('watch').onclick = () => {
  if (!current) return;
  const on = $('watch').getAttribute('aria-pressed') !== 'true';
  $('watch').setAttribute('aria-pressed', String(on));
  tma.haptic.select();
  void store.set(`watch-${current.id}`, on ? '1' : '0');
};

/* ---------------------------------------------------------------- navigation */
let shown: 'home' | 'bonus' | 'asset' = 'home';
const tabScroll = tma.scrollMemory(); // Points and Bonus come back where the user left them
function show(id: 'home' | 'bonus' | 'asset', back = false): void {
  const prev = shown;
  if (id !== prev && prev !== 'asset' && id !== 'asset') tabScroll.leave(prev);
  shown = id;
  for (const s of ['home', 'bonus', 'asset']) $(s).hidden = s !== id;
  $(id).classList.toggle('is-back', back);
  $('tabbar').hidden = id === 'asset';
  for (const b of document.querySelectorAll<HTMLButtonElement>('[data-go]')) if (b.getAttribute('role') === 'tab') b.setAttribute('aria-selected', String(b.dataset.go === id));
  // header follows the top of the screen: the brand hero on Bonus, the page elsewhere
  tma.chrome({ header: id === 'bonus' ? (getComputedStyle(document.documentElement).getPropertyValue('--tma-brand').trim() as `#${string}`) || 'secondary_bg_color' : 'secondary_bg_color' });
  if (id === 'bonus') startTimer(); else stopTimer();
  if (id === 'asset') window.scrollTo(0, 0); // a new screen starts at the top; nav.pop restores the one under it
  else if (prev !== 'asset') tabScroll.enter(id);
}
for (const b of document.querySelectorAll<HTMLElement>('[data-go]')) {
  b.addEventListener('click', (e) => {
    e.preventDefault();
    if (b.getAttribute('role') === 'tab' && b.dataset.go === shown) { tabScroll.top(); return; }
    tma.haptic.select(); show(b.dataset.go as 'home' | 'bonus');
  });
}

/* ---------------------------------------------------------------- one-time onboarding sheet */
function closeOnboarding(): void {
  tma.nav.pop('onboarding');
  $('onboarding').hidden = true; $('scrim').hidden = true;
  if (current) assetButtons(current); else tma.mainButton(null); // give the layer below its buttons back
  tma.chrome({ bottomBar: 'secondary_bg_color' });
  void store.set('onboarded', '1');
}
void store.get('onboarded').then((v) => {
  if (v === '1') return;
  $('scrim').hidden = false; $('onboarding').hidden = false;
  tma.nav.push({ id: 'onboarding', kind: 'sheet', onBack: closeOnboarding });
  tma.chrome({ bottomBar: 'bg_color' });            // the bar matches the sheet surface
  tma.mainButton({ text: 'Continue', onClick: closeOnboarding });
});
$('ob-close').onclick = closeOnboarding;
$('ob-terms').addEventListener('click', (e) => {
  if (!tma.inTelegram || !tma.has('6.1')) return; // plain link outside Telegram or on very old clients
  e.preventDefault();
  (tma.tg as unknown as { openLink(u: string): void }).openLink((e.currentTarget as HTMLAnchorElement).href);
});

let toastTimer = 0;
function toast(text: string): void {
  const s = $('snackbar'); s.textContent = text; s.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { s.hidden = true; }, 2200);
}

/* ---------------------------------------------------------------- start */
tma.start(); // fullscreen on iOS / Android (8.0+), the expanded sheet elsewhere
tma.chrome({ header: 'secondary_bg_color', background: 'secondary_bg_color', bottomBar: 'secondary_bg_color' });
$('me').textContent = (lang?.first_name || 'You')[0];
void store.get('hide-balance').then((v) => { if (v === '1') setHidden(true); });
window.setTimeout(renderHome, 350); // skeleton first, as with a real request
const start = parseStartParam(tma.launch.tgWebAppStartParam, { asset: /^asset-([a-z]{2,12})$/, tab: /^tab-(home|bonus)$/ });
if (start?.route === 'tab' && start.match[1] === 'bonus') show('bonus');
if (start?.route === 'asset') { const a = ASSETS.find((x) => x.id === start.match[1]); if (a) window.setTimeout(() => openAsset(a), 360); }
tma.ready();
