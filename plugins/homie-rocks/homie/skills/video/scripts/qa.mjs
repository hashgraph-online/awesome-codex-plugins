#!/usr/bin/env node
/**
 * qa.mjs: check a finished video file before anyone sees it, from the decoded file itself (an
 * encoder that exits 0 has not proved the picture is there).
 *
 *   node qa.mjs <video.mp4> [--kind trailer|clip|music-video] [--max-mb 25] [--json]
 *
 * It decodes every frame (errors are counted), reads the streams (codec, size, frame rate, pixel
 * format, BT.709 colour tags), checks the file starts playing before it has downloaded (faststart:
 * the moov atom before the media data), finds black stretches and frozen stretches, measures the
 * loudness and true peak, finds silent stretches, and checks the size against the studio site's
 * 25 MiB file limit. PASS, WARN or FAIL, each with the fix.
 */
import { spawnSync } from 'node:child_process';
import { closeSync, existsSync, openSync, readSync, statSync } from 'node:fs';
import { resolve } from 'node:path';

const argv = process.argv.slice(2);
const flags = new Map(); const pos = [];
for (let i = 0; i < argv.length; i++) { const a = argv[i]; if (a.startsWith('--')) { const v = argv[i + 1]; if (v === undefined || v.startsWith('--')) flags.set(a.slice(2), true); else { flags.set(a.slice(2), v); i++; } } else pos.push(a); }

const run = (cmd, args) => spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });

/** Top-level MP4 atoms in order (enough to see whether moov comes before mdat). */
function atoms(file) {
  const fd = openSync(file, 'r');
  const size = statSync(file).size;
  const out = [];
  try {
    let at = 0;
    const head = Buffer.alloc(16);
    while (at + 8 <= size && out.length < 64) {
      readSync(fd, head, 0, 16, at);
      let len = head.readUInt32BE(0);
      const type = head.toString('latin1', 4, 8);
      if (len === 1) len = Number(head.readBigUInt64BE(8));
      else if (len === 0) len = size - at;
      if (len < 8) break;
      out.push(type);
      at += len;
    }
  } finally { closeSync(fd); }
  return out;
}

export function qa(file, { kind = 'trailer', maxMb = 25 } = {}) {
  if (!existsSync(file)) throw new Error(`no such file: ${file}`);
  const fails = []; const warns = [];
  const pr = run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration,size,format_name:stream=codec_type,codec_name,width,height,r_frame_rate,avg_frame_rate,pix_fmt,color_primaries,color_transfer,color_space,sample_rate,channels', '-of', 'json', file]);
  if (pr.status !== 0) throw new Error(`ffprobe could not read it: ${pr.stderr.trim().split('\n').pop()}`);
  const j = JSON.parse(pr.stdout);
  const v = (j.streams ?? []).find((s) => s.codec_type === 'video');
  const a = (j.streams ?? []).find((s) => s.codec_type === 'audio');
  const duration = Number(j.format?.duration ?? 0);
  const mb = +(Number(j.format?.size ?? statSync(file).size) / 1024 / 1024).toFixed(2);
  if (!v) fails.push('no video stream');
  const [fn, fd] = String(v?.avg_frame_rate ?? v?.r_frame_rate ?? '0/1').split('/').map(Number);
  const fps = fd ? +(fn / fd).toFixed(3) : null;
  if (v && v.codec_name !== 'h264') warns.push(`video codec ${v.codec_name}: H.264 plays on every phone and in every browser`);
  if (v && v.pix_fmt !== 'yuv420p') fails.push(`pixel format ${v.pix_fmt}: Safari and many phones need yuv420p${/^yuvj/.test(String(v.pix_fmt)) ? ' in limited range; this file is FULL range, which -pix_fmt alone does not change: convert it (scale=out_range=tv:out_color_matrix=bt709,format=yuv420p, with -color_range tv), as `cut` does' : ' (-pix_fmt yuv420p)'}`);
  if (v && (v.width % 2 || v.height % 2)) fails.push(`odd frame size ${v.width}x${v.height}: H.264 needs even sizes`);
  if (v && (v.color_primaries !== 'bt709' || v.color_transfer !== 'bt709' || v.color_space !== 'bt709')) warns.push(`colour tags ${v.color_primaries ?? 'unset'}/${v.color_transfer ?? 'unset'}/${v.color_space ?? 'unset'}: tag BT.709 (-colorspace bt709 -color_primaries bt709 -color_trc bt709) or players guess and the colours shift`);
  const ratio = v ? v.width / v.height : null;
  const shape = ratio === null ? null : Math.abs(ratio - 16 / 9) < 0.02 ? '16:9' : Math.abs(ratio - 9 / 16) < 0.02 ? '9:16' : Math.abs(ratio - 1) < 0.02 ? '1:1' : `${v.width}x${v.height}`;
  if (shape && !['16:9', '9:16', '1:1'].includes(shape)) warns.push(`frame ${shape}: deliver 16:9 (1920x1080) and, for vertical feeds, 9:16 (1080x1920)`);
  if (fps !== null && (fps < 23.9 || fps > 60.1)) warns.push(`${fps} fps: deliver 24, 25, 30 or 60`);
  const at = atoms(file);
  const moov = at.indexOf('moov'); const mdat = at.indexOf('mdat');
  const faststart = moov >= 0 && (mdat < 0 || moov < mdat);
  if (!faststart) fails.push('not faststart (the index is at the end): a phone downloads the whole file before playing; re-mux with -movflags +faststart');
  if (mb > maxMb) fails.push(`${mb} MB is over the ${maxMb} MB a studio site serves itself: a lower bitrate, or the studio's storage`);
  // A full decode: every frame, every error counted.
  const dec = run('ffmpeg', ['-hide_banner', '-v', 'error', '-i', file, '-f', 'null', '-']);
  const decodeErrors = String(dec.stderr).split('\n').filter(Boolean);
  if (decodeErrors.length) fails.push(`${decodeErrors.length} decode error(s), first: ${decodeErrors[0].slice(0, 160)}`);
  // Black and frozen stretches, silence, loudness: one pass.
  const filters = ['-vf', 'blackdetect=d=0.4:pix_th=0.08,freezedetect=n=0.002:d=1.5'];
  const af = a ? ['-af', 'ebur128=peak=true,silencedetect=n=-50dB:d=1.0'] : [];
  const det = run('ffmpeg', ['-hide_banner', '-nostats', '-i', file, ...filters, ...af, '-f', 'null', '-']);
  const text = String(det.stderr);
  const blacks = [...text.matchAll(/black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)/g)].map((m) => ({ from: +m[1], to: +m[2], seconds: +m[3] }));
  const freezes = []; let fStart = null;
  for (const line of text.split('\n')) {
    const s = /freeze_start: ([\d.]+)/.exec(line); if (s) fStart = +s[1];
    const e = /freeze_end: ([\d.]+)/.exec(line); if (e && fStart !== null) { freezes.push({ from: fStart, to: +e[1], seconds: +(+e[1] - fStart).toFixed(2) }); fStart = null; }
  }
  if (fStart !== null) freezes.push({ from: fStart, to: duration, seconds: +(duration - fStart).toFixed(2) });
  const silences = [...text.matchAll(/silence_start: ([\d.]+)[\s\S]*?silence_end: ([\d.]+) \| silence_duration: ([\d.]+)/g)].map((m) => ({ from: +m[1], to: +m[2], seconds: +m[3] }));
  const sum = text.slice(text.lastIndexOf('Summary:'));
  const lufs = /I:\s+(-?[\d.]+) LUFS/.exec(sum); const tp = /Peak:\s+(-?[\d.]+) dBFS/.exec(sum);
  const loud = { lufs: lufs ? Number(lufs[1]) : null, truePeakDb: tp ? Number(tp[1]) : null };
  // A fade from or to black at the very ends is a choice; black in the middle is a hole.
  const midBlack = blacks.filter((b) => b.from > 0.3 && b.to < duration - 0.3);
  if (midBlack.length) warns.push(`${midBlack.length} black stretch(es) inside it, first at ${midBlack[0].from}s for ${midBlack[0].seconds}s: a capture that lost the picture, or a cut to nothing`);
  if (blacks.some((b) => b.seconds > duration * 0.5)) fails.push('more than half of it is black');
  const longFreeze = freezes.filter((f) => f.seconds >= (kind === 'music-video' ? 3 : 1.5));
  if (longFreeze.length) warns.push(`${longFreeze.length} frozen stretch(es), first at ${longFreeze[0].from}s for ${longFreeze[0].seconds}s: held frames from a capture that could not keep up, or a still left too long (a card is fine: check it is one)`);
  if (!a) warns.push('no sound: a trailer without sound loses most of its effect; a muted social clip needs captions instead');
  else {
    if (loud.lufs !== null && (loud.lufs < -18 || loud.lufs > -10)) warns.push(`loudness ${loud.lufs} LUFS: deliver about -14 LUFS for the web and social`);
    if (loud.truePeakDb !== null && loud.truePeakDb > -1) warns.push(`true peak ${loud.truePeakDb} dBTP: keep it under -1 dBTP or it clips after the platform re-encodes it`);
    const midSilence = silences.filter((s) => s.from > 0.5 && s.to < duration - 0.5);
    if (midSilence.length) warns.push(`${midSilence.length} silent stretch(es), first at ${midSilence[0].from}s for ${midSilence[0].seconds}s`);
  }
  const verdict = fails.length ? 'FAIL' : warns.length ? 'WARN' : 'PASS';
  return {
    ok: !fails.length, command: 'qa', verdict, file, seconds: +duration.toFixed(3), mb, shape, fps,
    video: v ? { codec: v.codec_name, size: `${v.width}x${v.height}`, pixFmt: v.pix_fmt, colour: `${v.color_primaries ?? '-'}/${v.color_transfer ?? '-'}/${v.color_space ?? '-'}` } : null,
    audio: a ? { codec: a.codec_name, rate: Number(a.sample_rate), channels: a.channels, ...loud } : null,
    faststart, decodeErrors: decodeErrors.length, blacks, freezes, silences: silences.slice(0, 10),
    fails, warnings: warns,
    look: 'QA is not a review: open the contact sheet (video.mjs sheet) and watch it once, start to end, before anyone else does',
  };
}

if (process.argv[1]?.endsWith('qa.mjs')) {
  try {
    const file = resolve(String(pos[0] ?? ''));
    const r = qa(file, { kind: String(flags.get('kind') ?? 'trailer'), maxMb: Number(flags.get('max-mb') ?? 25) });
    if (flags.has('json')) process.stdout.write(`${JSON.stringify(r, null, 2)}\n`);
    else process.stdout.write(`${r.verdict}: ${r.file} (${r.seconds}s, ${r.shape}, ${r.fps} fps, ${r.mb} MB${r.audio ? `, ${r.audio.lufs} LUFS, ${r.audio.truePeakDb} dBTP` : ''})\n${[...r.fails.map((f) => `  FAIL  ${f}`), ...r.warnings.map((w) => `  WARN  ${w}`)].join('\n')}\n`);
    if (!r.ok) process.exitCode = 1;
  } catch (error) {
    process.stdout.write(`qa: ${error instanceof Error ? error.message : String(error)}\n`);
    process.exitCode = 1;
  }
}
