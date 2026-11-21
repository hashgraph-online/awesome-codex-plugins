/* hyper-diagram viewer: kept in the delivered HTML. Adds a small toolbar
   (theme, zoom, SVG download) once the page is baked. It does nothing while
   the runtime bakes the page or while an export captures it (?capture=1). */
(function () {
  'use strict';
  function start() {
    const html = document.documentElement;
    if (html.dataset.hdState !== 'baked' || /[?&]capture=1/.test(location.search)) return;
    const svg = document.getElementById('hd-svg');
    if (!svg || document.querySelector('.hd-toolbar')) return;
    const baseW = parseFloat(svg.getAttribute('width')), baseH = parseFloat(svg.getAttribute('height'));
    let zoom = 1;
    const setZoom = (z) => { zoom = Math.min(3, Math.max(0.4, z)); svg.setAttribute('width', baseW * zoom); svg.setAttribute('height', baseH * zoom); };
    const bar = document.createElement('div');
    bar.className = 'hd-toolbar';
    const add = (label, title, fn) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = label; b.title = title; b.addEventListener('click', fn); bar.appendChild(b); };
    add('◐', '밝게·어둡게', () => { html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark'; });
    add('−', '축소', () => setZoom(zoom / 1.2));
    add('100%', '원래 크기', () => setZoom(1));
    add('+', '확대', () => setZoom(zoom * 1.2));
    add('SVG', 'SVG로 내려받기', () => {
      const clone = svg.cloneNode(true);
      clone.setAttribute('data-theme', html.dataset.theme || 'light');
      clone.setAttribute('width', baseW); clone.setAttribute('height', baseH);
      const style = document.createElementNS('http://www.w3.org/2000/svg', 'style');
      style.textContent = (document.getElementById('hd-theme') || {}).textContent || '';
      clone.insertBefore(style, clone.firstChild);
      const blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = (document.title || 'diagram').replace(/[\\/:*?"<>|]+/g, '-') + '.svg';
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });
    document.body.appendChild(bar);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
