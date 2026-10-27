// 内测名单面板：报名 → 拿到排位 → 叫朋友插队（每叫来 1 人往前 5 位）。
(() => {
  const T = k => I18N[k] ?? k;
  const sheet = document.getElementById('sheet'), form = document.getElementById('joinForm');
  const email = document.getElementById('email'), err = document.getElementById('joinErr');
  const done = document.getElementById('joined'), pos = document.getElementById('pos'), inv = document.getElementById('inv');
  const store = {
    get: k => { try { return localStorage.getItem(k); } catch { return null; } },
    set: (k, v) => { try { localStorage.setItem(k, v); } catch {} },
  };
  const by = new URLSearchParams(location.search).get('r');
  if (by && !store.get('tutti_by')) store.set('tutti_by', by.toUpperCase().slice(0, 6));

  const link = ref => `https://tutti.pics${I18N.path}?r=${ref}`;
  function show(r) {
    form.hidden = true; done.hidden = false;
    pos.textContent = r.position;
    inv.textContent = r.invites ? T('rank_invites').replace('{n}', r.invites) : T('rank_boost').replace('{n}', r.boost);
    store.set('tutti_ref', r.ref); sheet.dataset.ref = r.ref;
  }
  async function refresh() {
    const ref = store.get('tutti_ref');
    if (!ref) return;
    try { const r = await fetch(`/api/me?ref=${ref}`); if (r.ok) show(await r.json()); } catch {}
  }

  function open() { sheet.hidden = false; requestAnimationFrame(() => sheet.classList.add('on')); refresh(); if (!store.get('tutti_ref')) setTimeout(() => email.focus(), 350); }
  function close() { sheet.classList.remove('on'); setTimeout(() => (sheet.hidden = true), 300); if (location.hash === '#join') history.replaceState(null, '', location.pathname + location.search); }
  document.querySelectorAll('a[href="#join"]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); open(); }));
  document.getElementById('sheetClose').addEventListener('click', close);
  if (location.hash === '#join') open();

  form.addEventListener('submit', async e => {
    e.preventDefault(); err.hidden = true;
    const btn = form.querySelector('button'); btn.disabled = true; btn.textContent = T('joining');
    try {
      const r = await fetch('/api/join', { method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ email: email.value, ref: store.get('tutti_by'), lang: navigator.language }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || 'http');
      show(j);
    } catch (x) {
      err.hidden = false;
      err.textContent = x.message === 'bad_email' ? T('err_email') : T('err_busy');
    } finally { btn.disabled = false; btn.textContent = T('join_btn'); }
  });

  document.getElementById('invite').addEventListener('click', async () => {
    const ref = sheet.dataset.ref, url = link(ref), text = T('share_text').replace('{url}', url);
    try {
      const blob = window.TUTTI && await TUTTI.poster();
      const f = blob && new File([blob], 'tutti.jpg', { type: 'image/jpeg' });
      if (f && navigator.canShare?.({ files: [f] })) return await navigator.share({ files: [f], text });
      if (navigator.share) return await navigator.share({ text, url });
    } catch (e) { if (e.name === 'AbortError') return; }
    copy(url);
  });
  document.getElementById('copyLink').addEventListener('click', () => copy(link(sheet.dataset.ref)));
  async function copy(t) {
    const b = document.getElementById('copyLink');
    try { await navigator.clipboard.writeText(t); b.textContent = T('copied'); } catch { b.textContent = t; }
    setTimeout(() => (b.textContent = T('copy_link')), 2200);
  }
})();
