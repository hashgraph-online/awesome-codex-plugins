// Deterministic render: drives window.__frame(t) in headless Chrome and pipes PNG frames into ffmpeg.
// Frame i shows exactly t = i / fps (the same sampling HyperFrames uses), so cuts land on the frame.
//
//   bun tools/capture.ts                                  whole film -> renders/animatic.mp4
//   bun tools/capture.ts --shots s02,s03 --grey --out renders/run_A.mp4
//        one video-to-video run: those shots back to back, padded with a tail to whole seconds (min 4 s),
//        greyscale (so the model cannot hand the previz back as its output), plus run_A.json placement
//   bun tools/capture.ts --stills --size 1536x864         START / middle / END png per shot (for image edits)
// Options: --url (default http://localhost:8777/), --fps, --size WxH, --tail auto|<seconds>|0, --crf
import { mkdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { launch, args } from './cdp.ts';
import { FILM } from '../js/config.js';

const o = args({ url: 'http://localhost:8777/', out: '', shots: '', tail: 'auto', grey: false, stills: false, fps: String(FILM.fps), size: `${FILM.export.width}x${FILM.export.height}`, crf: '16' });
const fps = Number(o.fps);
const [w, h] = String(o.size).split('x').map(Number);
const c = await launch({ width: w, height: h });
try {
  await c.goto(`${o.url}?export=1&w=${w}&h=${h}`);
  const film = await c.evaluate('window.__film');
  const pick = o.shots ? String(o.shots).split(',').map(id => {
    const s = film.shots.find((x: any) => x.id === id);
    if (!s) throw new Error(`unknown shot ${id}; shots: ${film.shots.map((x: any) => x.id).join(' ')}`);
    return s;
  }) : null;

  if (o.stills) {
    const dir = o.out || 'renders/stills';
    await mkdir(dir, { recursive: true });
    for (const s of pick || film.shots) {
      const dur = s.end - s.start;
      for (const [tag, lt] of [['a', 0], ['m', dur / 2], ['b', dur - 1 / fps]] as const) {
        await Bun.write(join(dir, `${s.id}_${tag}.png`), await c.frame(`window.__frame(null, ${JSON.stringify(s.id)}, ${lt})`));
      }
      console.log(`${s.id}: ${dir}/${s.id}_{a,m,b}.png`);
    }
  } else {
    // frame list: whole film by global time, or chosen shots by local time (+ tail on the last one)
    const frames: string[] = [], place: any[] = [];
    if (!pick) for (let i = 0; i < Math.round(film.duration * fps); i++) frames.push(`window.__frame(${i / fps})`);
    else {
      for (const s of pick) {
        const n = Math.round((s.end - s.start) * fps), from = frames.length / fps;
        for (let i = 0; i < n; i++) frames.push(`window.__frame(null, ${JSON.stringify(s.id)}, ${i / fps})`);
        place.push({ id: s.id, in: +from.toFixed(4), out: +(frames.length / fps).toFixed(4), timeline: s.start });
      }
      const last = pick[pick.length - 1], dur = last.end - last.start;
      const target = o.tail === 'auto' ? Math.max(4, Math.ceil(frames.length / fps - 1e-6)) * fps : frames.length + Math.round(Number(o.tail) * fps);
      for (let j = 0; frames.length < target; j++) frames.push(`window.__frame(null, ${JSON.stringify(last.id)}, ${dur + j / fps})`);
    }
    const out = String(o.out || (pick ? `renders/run_${pick.map((s: any) => s.id).join('-')}.mp4` : 'renders/animatic.mp4'));
    await mkdir(dirname(out), { recursive: true });
    const vf = o.grey ? ['-vf', 'hue=s=0,eq=contrast=1.15'] : [];
    const ff = Bun.spawn(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
      ...vf, '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', String(o.crf), '-preset', 'medium', '-movflags', '+faststart', out], { stdin: 'pipe' });
    const t0 = Date.now();
    for (let i = 0; i < frames.length; i++) {
      ff.stdin.write(await c.frame(frames[i]));
      if (i % fps === 0) { await ff.stdin.flush(); process.stdout.write(`\r${i}/${frames.length} frames`); }
    }
    ff.stdin.end();
    if (await ff.exited) throw new Error('ffmpeg failed');
    const secs = frames.length / fps;
    console.log(`\r${frames.length} frames, ${secs.toFixed(2)} s -> ${out} (${((Date.now() - t0) / 1000).toFixed(1)} s to render)`);
    if (pick) {
      const side = out.replace(/\.mp4$/, '.json');
      await Bun.write(side, JSON.stringify({ video: out, fps, size: [w, h], duration: secs, grey: !!o.grey, shots: place,
        note: 'in/out = seconds inside this clip; timeline = where the shot starts in the film. Frames after the last out are the tail handle.' }, null, 1));
      console.log(`placement -> ${side}`);
    }
  }
  if (c.errors.length) console.warn(`page errors:\n${c.errors.join('\n')}`);
} finally {
  await c.close();
}
