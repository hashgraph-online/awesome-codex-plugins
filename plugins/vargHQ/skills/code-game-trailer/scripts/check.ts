// check.ts: measure a trailer before anyone sees it.
//
//   bun scripts/check.ts director.json                       capture/ + master.mp4 beside the director
//   bun scripts/check.ts director.json --video out.mp4 --every 15 --sheet sheet.jpg
//
// Reports (and writes <video>.check.json):
//   frames   per shot, from the captured frames: duplicate frames (identical to the previous one),
//            the longest frozen run, black frames outside fades
//   video    size, fps, duration, codec of the master
//   sheet    a contact sheet of every Nth frame (default every 15th = 2 per second at 30 fps), plus a
//            legend of tile -> time -> shot. Open it and LOOK: the numbers do not see a broken shot
//   sound    integrated loudness (LUFS) and true peak of the master (EBU R128)
//   text     every visible string (HUD, overlays, cards) with flags for debug text, third-party names
//            and claims that need proof ("one prompt", "real gameplay", ...)
import { readFile } from 'node:fs/promises';
import { existsSync, readdirSync } from 'node:fs';
import { dirname, resolve, join } from 'node:path';

const argv = process.argv.slice(2);
const opt = (n: string, d: string) => { const i = argv.indexOf(`--${n}`); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };
const directorPath = argv.find((a) => a.endsWith('.json'));
if (!directorPath) { console.error('usage: bun scripts/check.ts director.json [--video master.mp4] [--every 15]'); process.exit(1); }
const D = JSON.parse(await readFile(directorPath, 'utf8'));
const base = dirname(resolve(directorPath));
const capDir = resolve(opt('capture', D.out ? resolve(base, D.out) : join(base, 'capture')));
const video = resolve(opt('video', join(base, 'master.mp4')));
const M = JSON.parse(await readFile(join(capDir, 'manifest.json'), 'utf8'));
const fps = M.fps, every = Number(opt('every', '15'));
const sheet = resolve(opt('sheet', video.replace(/\.mp4$/, '') + '.sheet.jpg'));

async function ff(args: string[]) {
  const p = Bun.spawn(['ffmpeg', '-hide_banner', '-nostats', ...args], { stdout: 'pipe', stderr: 'pipe' });
  const [out, err] = await Promise.all([new Response(p.stdout).text(), new Response(p.stderr).text()]);
  await p.exited; return out + err;
}
const yavg = (txt: string) => [...txt.matchAll(/YAVG=([\d.]+)/g)].map((m) => Number(m[1]));
const report: any = { video, frames: [], warnings: [] as string[] };
const warn = (s: string) => { report.warnings.push(s); console.log(`  ! ${s}`); };

// ---------- frames, per shot ----------
console.log('frames (captured, before grading/grain):');
for (const s of D.shots) {
  const m = M.shots.find((x: any) => x.id === s.id);
  if (!m) { warn(`${s.id}: not captured`); continue; }
  const dir = join(capDir, m.dir), ext = readdirSync(dir).find((f) => /^\d{5}\./.test(f))?.split('.')[1] ?? 'jpg';
  const input = ['-framerate', String(fps), '-i', join(dir, `%05d.${ext}`)];
  const diff = yavg(await ff([...input, '-vf', 'tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-', '-f', 'null', '-']));
  const bright = yavg(await ff([...input, '-vf', 'signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-', '-f', 'null', '-']));
  let dup = 0, run = 0, longest = 0, at = -1;
  diff.forEach((d, i) => { if (d < 0.05) { dup++; run++; if (run > longest) { longest = run; at = i - run + 1; } } else run = 0; });
  const fadeIn = Math.round((s.fade_in ?? 0) * fps), fadeOut = Math.round((s.fade_out ?? 0) * fps);
  const black = bright.filter((b, i) => b < 3 && i >= fadeIn && i < bright.length - fadeOut).length;
  const motion = diff.length ? diff.reduce((a, b) => a + b, 0) / diff.length : 0;
  const hold = ['title', 'end'].includes(s.role);
  report.frames.push({ id: s.id, frames: m.frames, duplicates: dup, longest_frozen: longest + (longest ? 1 : 0), frozen_from_frame: at, black, mean_motion: +motion.toFixed(2), ms_per_frame: m.ms_per_frame });
  console.log(`  ${s.id.padEnd(16)} ${String(m.frames).padStart(4)} fr  dup ${String(dup).padStart(3)}  frozen ${String(longest ? longest + 1 : 0).padStart(3)} fr  black ${black}  motion ${motion.toFixed(2)}`);
  if (dup && !hold) warn(`${s.id}: ${dup} duplicate frames (longest run ${longest + 1} from frame ${at}): a clock the virtual clock does not cover, or the game paused`);
  if (hold && longest + 1 > fps * 1.2) warn(`${s.id}: holds still for ${((longest + 1) / fps).toFixed(1)} s: keep something moving on cards`);
  if (black) warn(`${s.id}: ${black} black frames outside fades (captured before the first render?)`);
  if (motion > 25 && !hold) warn(`${s.id}: very high frame-to-frame change (${motion.toFixed(1)}): strobing or a camera cut inside the shot?`);
}

// ---------- video ----------
if (!existsSync(video)) { warn(`no video at ${video}: run cut.ts first`); }
else {
  const pr = Bun.spawnSync(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,codec_name,width,height,r_frame_rate:format=duration', '-of', 'json', video]);
  const info = JSON.parse(pr.stdout.toString()), v = info.streams.find((x: any) => x.codec_type === 'video'), a = info.streams.find((x: any) => x.codec_type === 'audio');
  report.video_info = { width: v.width, height: v.height, fps: v.r_frame_rate, codec: v.codec_name, audio: a?.codec_name ?? null, duration: +Number(info.format.duration).toFixed(3) };
  console.log(`video: ${v.width}x${v.height} ${v.codec_name} ${v.r_frame_rate} fps, ${report.video_info.duration} s, audio ${a?.codec_name ?? 'none'}`);
  if (v.width !== (D.width ?? 1920) || v.height !== (D.height ?? 1080)) warn(`master is ${v.width}x${v.height}, director asks ${D.width ?? 1920}x${D.height ?? 1080}`);

  // contact sheet + legend
  const total = Math.round(report.video_info.duration * fps), tiles = Math.ceil(total / every), cols = 6, rows = Math.ceil(tiles / cols);
  await ff(['-y', '-i', video, '-vf', `select='not(mod(n\\,${every}))',scale=384:-2,tile=${cols}x${rows}:padding=4:color=0x202020`, '-frames:v', '1', '-q:v', '3', sheet]);
  const cutsPath = video.replace(/\.mp4$/, '') + '.cuts.json';
  const cuts = existsSync(cutsPath) ? JSON.parse(await readFile(cutsPath, 'utf8')).cuts : [];
  const legend: string[] = [];
  for (let k = 0; k < tiles; k++) { const t = (k * every) / fps, c = cuts.find((x: any) => t >= x.start && t < x.end); legend.push(`${k + 1}:${t.toFixed(1)}s${c ? ' ' + c.id : ''}`); }
  report.sheet = sheet; report.sheet_legend = legend;
  console.log(`sheet: ${sheet} (${cols}x${rows}, every ${every} frames, row by row)\n  ${legend.join('  ')}`);

  // loudness
  if (a) {
    const log = await ff(['-i', video, '-af', 'ebur128=peak=true', '-f', 'null', '-']);
    const sum = log.slice(log.lastIndexOf('Summary:'));
    const I = Number(sum.match(/I:\s+(-?[\d.]+) LUFS/)?.[1]), P = Number(sum.match(/Peak:\s+(-?[\d.]+) dBFS/)?.[1]);
    report.loudness = { integrated_lufs: I, true_peak_dbfs: P };
    console.log(`sound: ${I} LUFS integrated, true peak ${P} dBFS`);
    if (Math.abs(I + 14) > 1) warn(`loudness ${I} LUFS, target -14 (cut.ts --lufs)`);
    if (P > -0.9) warn(`true peak ${P} dBFS: above -1 dBTP`);
  } else console.log('sound: no audio track');
}

// ---------- text ----------
const strip = (h: string) => h.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
const texts: { where: string; text: string }[] = [];
for (const s of D.shots) {
  const m = M.shots.find((x: any) => x.id === s.id);
  if (m?.text) texts.push({ where: `${s.id} (on screen)`, text: m.text.replace(/\s+/g, ' ').trim() });
  if (s.overlay) texts.push({ where: `${s.id} (overlay)`, text: strip(typeof s.overlay === 'string' ? s.overlay : s.overlay.html || '') });
  if (s.card) { const q = new URLSearchParams(s.card.split('?')[1] || ''); texts.push({ where: `${s.id} (card)`, text: ['kicker', 'title', 'sub', 'foot'].map((k) => q.get(k)).filter(Boolean).join(' | ') }); }
}
const DEBUG = /\b(fps|ms\/frame|debug|todo|fixme|undefined|nan|null|lorem|console|error|stats|draw calls|triangles)\b/i;
const IP = /\b(gta|grand theft|minecraft|fortnite|zelda|mario|pok[eé]mon|halo|call of duty|gears of war|roblox|star wars|marvel|disney|pixar|nintendo|playstation|xbox|rockstar|valve|half-life|doom|tetris|pac-man|sonic|elden ring|cyberpunk 2077|the witcher|assassin'?s creed)\b/i;
const CLAIM = /\b(one prompt|single prompt|one[- ]shot|zero code|no code|real gameplay|actual gameplay|unedited|no edits|in real time|real-time|100%|made by ai|built by ai|ai[- ]generated|\d+ ?(hours?|minutes?|mins?)|\$\d+)/i;
console.log('text on screen:');
report.text = texts;
for (const { where, text } of texts) {
  console.log(`  ${where}: ${text || '(none)'}`);
  if (DEBUG.test(text)) warn(`${where}: looks like debug text: "${text.match(DEBUG)![0]}"`);
  if (IP.test(text)) warn(`${where}: third-party name "${text.match(IP)![0]}": rename it (and check the picture for their characters/logos)`);
  if (CLAIM.test(text)) warn(`${where}: claim "${text.match(CLAIM)![0]}": keep it only if NOTES.md proves it`);
}
await Bun.write(video.replace(/\.mp4$/, '') + '.check.json', JSON.stringify(report, null, 1));
console.log(report.warnings.length ? `${report.warnings.length} warning(s); now open the sheet and look at it` : 'no warnings; now open the sheet and look at it');
