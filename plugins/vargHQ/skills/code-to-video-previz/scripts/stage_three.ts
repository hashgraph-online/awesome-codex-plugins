// Render staging.json through three.js in headless Chrome, frame by frame. Needs Bun, Chrome and ffmpeg.
//
//   bun stage_three.ts staging.json still s01:0 out.png [WxH] [--flat]
//   bun stage_three.ts staging.json film all renders/previz.mp4 [WxH] [--flat] [--grey]
//   bun stage_three.ts staging.json live          serves the page and prints its URL; it plays the shots in a loop
//
// --flat: hemisphere light, no shadows (for a video-model guide clip). --grey: desaturate the MP4.
import { dirname, resolve, join } from 'node:path';
import { mkdir } from 'node:fs/promises';
import { launch } from './cdp.ts';

const flags = process.argv.filter(a => a.startsWith('--'));
const [sceneFile, mode, which, out, size] = process.argv.slice(2).filter(a => !a.startsWith('--'));
const S = await Bun.file(sceneFile).json();
const [w, h] = size ? size.split('x').map(Number) : [S.frame.w, S.frame.h];
const here = import.meta.dir, sceneDir = dirname(resolve(sceneFile));

const server = Bun.serve({ port: 0, async fetch(req) {
  const u = new URL(req.url);
  if (u.pathname === '/stage_three.html') return new Response(Bun.file(join(here, 'stage_three.html')));
  if (u.pathname === '/favicon.ico') return new Response(null, { status: 204 });
  return new Response(Bun.file(join(sceneDir, u.pathname)));
} });
const scene = sceneFile.split('/').pop();
if (mode === 'live') {
  console.log(`http://localhost:${server.port}/stage_three.html?scene=${scene}&w=${w}&h=${h}${flags.includes('--flat') ? '&flat=1' : ''}`);
  await new Promise(() => {});
}
const url = `http://localhost:${server.port}/stage_three.html?export=1&scene=${scene}&w=${w}&h=${h}${flags.includes('--flat') ? '&flat=1' : ''}`;
const c = await launch({ width: w, height: h });
await c.goto(url);
const t0 = Date.now();
if (mode === 'still') {
  const [id, lt] = (which || '').split(':');
  await mkdir(dirname(resolve(out)), { recursive: true });
  await Bun.write(out, await c.frame(`window.__frame(${JSON.stringify(id)}, ${Number(lt || 0)})`));
  console.log(`RENDER_S ${(Date.now() - t0) / 1000} three ${w}x${h} 1 frame ${out}`);
} else {
  const fps: number = S.frame.fps, ids = which === 'all' ? null : which.split(',');
  const shots = S.shots.filter((s: any) => !ids || ids.includes(s.id));
  await mkdir(dirname(resolve(out)), { recursive: true });
  const vf = ['-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2' + (flags.includes('--grey') ? ',hue=s=0' : '')];   // yuv420p needs even sizes
  const enc = Bun.spawn(['ffmpeg', '-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', ...vf, '-pix_fmt', 'yuv420p', '-crf', '18', out], { stdin: 'pipe' });
  let n = 0;
  for (const s of shots) {
    const frames = Math.round((s.end - s.start) * fps);
    for (let i = 0; i < frames; i++, n++) enc.stdin.write(await c.frame(`window.__frame(${JSON.stringify(s.id)}, ${i / fps})`));
  }
  enc.stdin.end();
  await enc.exited;
  console.log(`RENDER_S ${(Date.now() - t0) / 1000} three ${w}x${h} ${n} frames ${out}`);
}
if (c.errors?.length) console.log('PAGE ERRORS', c.errors.join('\n'));
await c.close();
server.stop(true);
process.exit(0);
