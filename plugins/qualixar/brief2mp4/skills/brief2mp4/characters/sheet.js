/*
 * sheet.js: draws a character sheet on a 1920 x 1080 canvas: the standing view, six poses and the nine mouth
 * shapes, in one skin. Used by scripts/character_sheet.py for consistency checks and thumbnails.
 */
(function (g) {
  'use strict';
  if (typeof require === 'function' && !(g.B2M && g.B2M.SKINS)) require('./index.js');
  const B = (g.B2M = g.B2M || {});
  const POSES = ['wave', 'point', 'sit', 'jump', 'surprised', 'think'];
  const FONT = '600 24px "Helvetica Neue", Arial, sans-serif';

  function cell(g2, x, y, w, h, fill, label) {
    g2.save();
    g2.fillStyle = fill; g2.fillRect(x, y, w, h);
    g2.strokeStyle = 'rgba(0,0,0,0.25)'; g2.lineWidth = 2; g2.strokeRect(x, y, w, h);
    g2.fillStyle = 'rgba(0,0,0,0.7)'; g2.font = FONT; g2.textAlign = 'center';
    g2.fillText(label, x + w / 2, y + h + 30);
    g2.restore();
    g2.save(); g2.beginPath(); g2.rect(x, y, w, h); g2.clip();
  }

  const quiet = (name, view) => ({ keys: [{ t: 0, pose: name }], blink: false, breath: false, view });

  const faceWidth = (c) => c.proportions.face || c.proportions.height * 0.3;
  const bodyWidth = (c) => c.proportions.width || c.proportions.height * 0.6;

  function drawBody(g2, character, skin, name, box, scale) {
    const posed = B.pose(character, quiet(name), 0, { steps: skin.steps, smooth: !skin.steps });
    B.drawCanvas(g2, B.layout(character, skin, posed, { x: box.x + box.w / 2, y: box.y + box.h - 18, scale }));
    g2.restore();
  }

  function drawMouth(g2, character, skin, viseme, box) {
    const track = { keys: [{ t: 0, pose: 'idle' }], blink: false, breath: false, visemes: [{ t: 0, v: viseme }, { t: 9, v: 'rest' }] };
    const posed = B.pose(character, track, 0.5, { steps: skin.steps, smooth: !skin.steps });
    const zoom = 150 / (faceWidth(character) * 1.2);
    const at = B.partPoint(character, posed, { x: 0, y: 0, scale: zoom }, 'mouth', skin);
    B.drawCanvas(g2, B.layout(character, skin, posed, { x: box.x + box.w / 2 - at[0], y: box.y + box.h / 2 - at[1], scale: zoom }));
    g2.restore();
  }

  // The close-up head that faces the camera, for shots where a character talks to the viewer.
  function drawFront(g2, character, skin, box) {
    const posed = B.pose(character, quiet('idle', 'front'), 0, { steps: skin.steps, smooth: !skin.steps });
    const zoom = (0.74 * box.w) / faceWidth(character);
    const at = B.partPoint(character, posed, { x: 0, y: 0, scale: zoom }, 'mouth', skin);
    B.drawCanvas(g2, B.layout(character, skin, posed, { x: box.x + box.w / 2 - at[0], y: box.y + box.h * 0.6 - at[1], scale: zoom }));
    g2.restore();
  }

  function hasFront(character) { return character.parts.some((p) => p.variants && p.variants.front); }

  function drawSheet(g2, character, skin) {
    const W = 1920, H = 1080;
    g2.setTransform(1, 0, 0, 1, 0, 0); g2.fillStyle = skin.bg; g2.fillRect(0, 0, W, H);
    g2.fillStyle = 'rgba(0,0,0,0.75)'; g2.font = '700 38px "Helvetica Neue", Arial, sans-serif'; g2.textAlign = 'left';
    g2.fillText(character.name + '  /  ' + skin.name, 40, 58);
    const tint = 'rgba(255,255,255,0.28)', front = hasFront(character) && !skin.profileOnly, left = front ? 780 : 600, colW = (1880 - left) / 3;
    cell(g2, 40, 90, 400, 560, tint, 'standing view'); drawBody(g2, character, skin, 'idle', { x: 40, y: 90, w: 400, h: 560 }, Math.min(2.1, (0.88 * 560) / character.proportions.height, (0.9 * 400) / bodyWidth(character)));
    if (front) { cell(g2, 460, 90, 300, 560, tint, 'front view (close-up)'); drawFront(g2, character, skin, { x: 460, y: 90, w: 300, h: 560 }); }
    POSES.forEach((name, i) => {
      const box = { x: left + (i % 3) * colW, y: 90 + Math.floor(i / 3) * 300, w: colW - 20, h: 250 };
      cell(g2, box.x, box.y, box.w, box.h, tint, name); drawBody(g2, character, skin, name, box, Math.min(1.6, (0.74 * box.h) / character.proportions.height, (0.9 * box.w) / bodyWidth(character)));
    });
    B.VISEMES.forEach((v, i) => {
      const box = { x: 40 + i * 204, y: 720, w: 190, h: 260 };
      cell(g2, box.x, box.y, box.w, box.h, tint, v); drawMouth(g2, character, skin, v, box);
    });
  }

  Object.assign(B, { drawSheet, SHEET_POSES: POSES });
  if (typeof module !== 'undefined' && module.exports) module.exports = B;
})(globalThis);
