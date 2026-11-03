// The seek-safe core, shared by the review app (index.html), the frame capture (?export=1 + tools/capture.ts)
// and the HyperFrames render (hf/). What is on screen is a pure function of time:
//   film.pose(t)  -> resets the set, runs BLOCKING(world time), applies the shot camera.
// No clocks, no Math.random, no state carried from the previous frame, nothing loaded at seek time.
// Seek to any t, in any order, any number of times: the same picture.
import * as THREE from 'three';
import { buildCafe } from './sets.js';
import { FILM, BEAT, SHOTS, BLOCKING } from './shots.js';
import { camFromJSON, evalCam, applyPose } from './camera.js';

export function createFilm(edits = {}) {
  const set = buildCafe();
  const shots = SHOTS.map((s, i) => {
    const ed = edits.shots?.[s.id] || {};
    return { ...s, i, dur: s.end - s.start, defCam: s.cam, cam: camFromJSON(ed.cam || s.cam), status: ed.status || '', note: ed.note || '' };
  });
  const camera = new THREE.PerspectiveCamera(40, FILM.aspect, 0.03, 200);
  const labels = [];
  set.scene.traverse(o => o.userData.label && labels.push(o));

  // Cut times live in one place (shot.start/end); everything that depends on a cut reads them.
  const shotAt = t => shots.find(s => t >= s.start && t < s.end) || shots[shots.length - 1];

  // shot + lt let an export render a shot past its end (tail handle): the camera holds END,
  // the blocking keeps running in world time.
  function pose(t, { shot, lt } = {}) {
    const sh = shot || shotAt(t);
    const local = lt ?? t - sh.start;
    const T = sh.start + local;
    set.reset();
    BLOCKING(set, T);
    sh.cheat?.(set, { lt: local, k: Math.min(1, local / sh.dur), T });
    const p = evalCam(sh, local);
    applyPose(camera, p);
    set.scene.updateMatrixWorld();
    return { shot: sh, pose: p, T, lt: local };
  }
  const setLabels = v => labels.forEach(l => (l.visible = v));
  return { FILM, BEAT, set, shots, camera, shotAt, pose, setLabels };
}

// One fixed-size renderer for video: pixel ratio 1, no DPR dependence, readable drawing buffer.
export function createVideoRenderer(canvas, width, height) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  r.setPixelRatio(1);
  r.setSize(width, height, false);
  r.outputColorSpace = THREE.SRGBColorSpace;
  return r;
}

// Clean export hooks for frame-by-frame capture (tools/capture.ts drives them over CDP).
//   __seek(t[, shotId, localTime])  render that moment, return true
//   __frame(...same, type)          render it and return the canvas as a data URL
//   __film                          title, fps, duration, size, shots (for the capture tool)
export function installExportHooks(film, renderer) {
  const { width, height } = renderer.getSize(new THREE.Vector2());
  film.setLabels(false); // no text in references: models redraw it as garbage
  film.camera.aspect = width / height;
  film.camera.updateProjectionMatrix();
  const render = (t, id, lt) => {
    const shot = id ? film.shots.find(s => s.id === id) : undefined;
    if (id && !shot) throw new Error(`unknown shot ${id}`);
    film.pose(t ?? 0, { shot, lt });
    renderer.render(film.set.scene, film.camera);
  };
  window.__seek = (t, id, lt) => (render(t, id, lt), true);
  window.__frame = (t, id, lt, type = 'image/png') => (render(t, id, lt), renderer.domElement.toDataURL(type));
  window.__film = {
    title: film.FILM.title, fps: film.FILM.fps, duration: film.FILM.duration, width, height,
    shots: film.shots.map(s => ({ id: s.id, start: s.start, end: s.end })),
  };
  render(0);
  window.__ready = true;
  return render;
}
