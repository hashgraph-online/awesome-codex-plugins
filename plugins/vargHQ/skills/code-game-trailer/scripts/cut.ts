// cut.ts: captured frames + the director's shot list -> one trailer MP4 (H.264 + AAC, -14 LUFS).
//
//   bun scripts/cut.ts director.json                                  capture/ -> master.mp4 (picture only)
//   bun scripts/cut.ts director.json --music bed.wav --sfx sfx.wav    + music bed and game sounds, loudness-normalised
//   bun scripts/cut.ts director.json --grade [--grain 2]              + gentle contrast and vignette (+ light film grain)
//
// Options: --capture <dir> (default capture/ beside the director), --out master.mp4, --crf 18,
//          --lufs -14, --tp -1.5, --music-offset <s> (skip into the track; or director.music.offset)
// Shot order is the director's order. Per shot: "fade_in" / "fade_out" (seconds, from/to black) and
// "flash_in" (seconds, from white). Cuts land on frames: shot k starts at the sum of the earlier shots'
// frame counts / fps. Writes <out>.cuts.json (shot id, start, end in the master) for check.ts and score.ts.
// Needs ffmpeg with libx264, loudnorm and the aac encoder (no drawtext needed: text is HTML in the capture).
import { readFile, mkdtemp, rm } from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';
import { tmpdir } from 'node:os';

const argv = process.argv.slice(2);
const flag = (n: string) => argv.includes(`--${n}`);
const opt = (n: string, d: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const directorPath = argv.find((a) => a.endsWith('.json'));
if (!directorPath) { console.error('usage: bun scripts/cut.ts director.json [--music bed.wav] [--sfx sfx.wav] [--grade] [--out master.mp4]'); process.exit(1); }
const D = JSON.parse(await readFile(directorPath, 'utf8'));
const base = dirname(resolve(directorPath));
const capDir = resolve(opt('capture', D.out ? resolve(base, D.out) : join(base, 'capture')));
const M = JSON.parse(await readFile(join(capDir, 'manifest.json'), 'utf8'));
const out = resolve(opt('out', join(base, 'master.mp4')));
const fps = M.fps, crf = opt('crf', '18');
const music = opt('music', D.music?.file ? resolve(base, D.music.file) : '');
const sfx = opt('sfx', '');
const musicOffset = Number(opt('music-offset', String(D.music?.offset ?? 0)));
// -1.5 dBTP on the WAV keeps the AAC under -1 dBTP (measured: -1 on the WAV came out at -0.7 after AAC)
const lufs = Number(opt('lufs', '-14')), tp = Number(opt('tp', '-1.5'));

async function run(args: string[], quiet = true) {
  const p = Bun.spawn(['ffmpeg', '-hide_banner', '-y', ...(quiet ? ['-loglevel', 'error'] : []), ...args], { stdout: 'pipe', stderr: 'pipe' });
  const [code, err] = await Promise.all([p.exited, new Response(p.stderr).text()]);
  if (code) throw new Error(`ffmpeg failed (${code}):\n${err.slice(-3000)}`);
  return err;
}

// ---------- picture ----------
const shots = D.shots.map((s: any) => {
  const m = M.shots.find((x: any) => x.id === s.id);
  if (!m) throw new Error(`shot ${s.id} is not in ${capDir}/manifest.json: run capture.ts first`);
  const dir = join(capDir, m.dir), files = readdirSync(dir).filter((f) => /^\d{5}\.(jpg|png)$/.test(f)).sort();
  if (files.length !== m.frames) throw new Error(`shot ${s.id}: ${files.length} frame files, manifest says ${m.frames}`);
  return { ...s, frames: m.frames, ext: files[0].split('.')[1], dir };
});
const inputs: string[] = [], chains: string[] = [], cuts: any[] = [];
let t = 0;
shots.forEach((s: any, i: number) => {
  inputs.push('-framerate', String(fps), '-i', join(s.dir, `%05d.${s.ext}`));
  const dur = s.frames / fps, f: string[] = [`[${i}:v]setsar=1`];
  if (s.flash_in) f.push(`fade=t=in:st=0:d=${s.flash_in}:color=white`);
  if (s.fade_in) f.push(`fade=t=in:st=0:d=${s.fade_in}`);
  if (s.fade_out) f.push(`fade=t=out:st=${(dur - s.fade_out).toFixed(4)}:d=${s.fade_out}`);
  chains.push(`${f.join(',')}[v${i}]`);
  cuts.push({ id: s.id, role: s.role ?? null, start: +t.toFixed(4), end: +(t + dur).toFixed(4), frames: s.frames, first_frame: Math.round(t * fps) });
  t += dur;
});
// --grade: gentle contrast + vignette. --grain N adds film grain (2-3 hides banding in dark skies) but costs
// bitrate: temporal grain at crf 16 made an 18.6 s master 209 MB (measured), so keep it light or leave it off.
const grain = Number(opt('grain', '0'));
const grade = (flag('grade') ? ',eq=contrast=1.04:saturation=1.06,vignette=angle=PI/5' : '') + (grain ? `,noise=alls=${grain}:allf=t` : '');
const filter = `${chains.join(';')};${shots.map((_: any, i: number) => `[v${i}]`).join('')}concat=n=${shots.length}:v=1:a=0${grade},format=yuv420p[v]`;
const total = t;

const tmp = await mkdtemp(join(tmpdir(), 'game-trailer-cut-'));
try {
  const t0 = performance.now();
  // ---------- sound: mix, trim to the picture, fade the tail, two-pass loudnorm ----------
  let audio = '';
  if (music || sfx) {
    const ins: string[] = [], labels: string[] = [];
    if (music) { ins.push('-ss', String(musicOffset), '-i', music); labels.push(`[${labels.length}:a]`); }
    if (sfx) { ins.push('-i', sfx); labels.push(`[${labels.length}:a]`); }
    const mix = labels.length > 1 ? `${labels.join('')}amix=inputs=${labels.length}:normalize=0:duration=longest` : `${labels[0]}anull`;
    const pre = `${mix},aformat=sample_rates=48000:channel_layouts=stereo,atrim=0:${total.toFixed(3)},apad=whole_dur=${total.toFixed(3)},afade=t=out:st=${Math.max(0, total - 0.8).toFixed(3)}:d=0.8`;
    const raw = join(tmp, 'mix.wav');
    await run([...ins, '-filter_complex', `${pre}[a]`, '-map', '[a]', '-c:a', 'pcm_s24le', raw]);
    const log = await run(['-i', raw, '-af', `loudnorm=I=${lufs}:TP=${tp}:LRA=11:print_format=json`, '-f', 'null', '-'], false);
    const m = JSON.parse(log.slice(log.lastIndexOf('{'), log.lastIndexOf('}') + 1));
    audio = join(tmp, 'norm.wav');
    await run(['-i', raw, '-af', `loudnorm=I=${lufs}:TP=${tp}:LRA=11:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true,aresample=48000`, '-c:a', 'pcm_s24le', audio]);
    console.log(`audio: measured ${m.input_i} LUFS / ${m.input_tp} dBTP -> target ${lufs} LUFS, ${tp} dBTP`);
  }
  // ---------- encode ----------
  await run([...inputs, ...(audio ? ['-i', audio] : []), '-filter_complex', filter, '-map', '[v]', ...(audio ? ['-map', `${shots.length}:a`, '-c:a', 'aac', '-b:a', '192k', '-shortest'] : []),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-profile:v', 'high', '-r', String(fps), '-movflags', '+faststart', out]);
  await Bun.write(out.replace(/\.mp4$/, '') + '.cuts.json', JSON.stringify({ video: out, fps, duration: +total.toFixed(4), cuts }, null, 1));
  console.log(`${out}  ${total.toFixed(2)} s, ${shots.length} shots, ${((performance.now() - t0) / 1000).toFixed(1)} s to cut`);
  for (const c of cuts) console.log(`  ${c.start.toFixed(2).padStart(6)} - ${c.end.toFixed(2).padStart(6)}  ${c.id}`);
} finally {
  await rm(tmp, { recursive: true, force: true });
}
