// Procedural sound for a stickman reel: an ambient bed and four effects, synthesized with ffmpeg only.
// No samples, so there is no licence to check. Runs with bun (or node).
// usage: bun sfx.mjs <out_dir> [bed_seconds]
//   ambient.wav  sea wash + wind + lamp-motor hum, loudness-normalised to -30 LUFS (a bed under a voice)
//   thud.wav, thud-b.wav      low pitch-drop hit (title stamp, choice card landing)
//   knock-182/171/196.wav     door knock, three takes at different pitch (never repeat one take)
//   buzz.wav                  electrical flicker, gated by the same on/off table the picture uses
//   whoosh.wav                noise swell peaking at 0.8 s (place it 0.8 s before the card lands)
import { execFileSync } from "node:child_process";
import { mkdirSync, renameSync } from "node:fs";
import { join } from "node:path";

const [OUT = "assets/audio", durArg = "25"] = process.argv.slice(2);
const DUR = +durArg, SR = 48000;
mkdirSync(OUT, { recursive: true });
const ff = (...args) => execFileSync("ffmpeg", ["-hide_banner", "-loglevel", "error", "-y", ...args], { stdio: "inherit" });
const out = (f) => join(OUT, f);

// 1) ambient bed
ff(
  "-f", "lavfi", "-i", `anoisesrc=d=${DUR}:c=pink:r=${SR}:a=0.5:s=7`,
  "-f", "lavfi", "-i", `anoisesrc=d=${DUR}:c=brown:r=${SR}:a=0.6:s=11`,
  "-f", "lavfi", "-i", `aevalsrc='0.05*sin(2*PI*116*t)+0.03*sin(2*PI*232*t)+0.02*sin(2*PI*348*t)+0.012*sin(2*PI*464*t)*(0.6+0.4*sin(2*PI*1.7*t))':d=${DUR}:s=${SR}`,
  "-filter_complex",
  `[0]highpass=f=150,lowpass=f=1400,volume='0.35+0.65*pow(sin(2*PI*t/6.4),2)':eval=frame[sea];` +
    `[1]bandpass=f=420:width_type=h:w=380,tremolo=f=0.23:d=0.5,volume=1.6[wind];[2]volume=0.9[hum];` +
    `[sea][wind][hum]amix=inputs=3:normalize=0,afade=t=in:d=0.4,afade=t=out:st=${DUR - 1.2}:d=1.2,loudnorm=I=-30:TP=-6:LRA=7[o]`,
  "-map", "[o]", "-ar", String(SR), "-ac", "2", out("ambient.wav"),
);
// 2) thuds
ff("-f", "lavfi", "-i", `aevalsrc='exp(-t*8)*sin(2*PI*(42+70*exp(-t*16))*t)*0.95+0.35*exp(-t*55)*(random(0)*2-1)':d=0.9:s=${SR}`,
  "-af", "lowpass=f=3500,aecho=0.7:0.3:60:0.2,alimiter=limit=0.85", "-ac", "2", out("thud.wav"));
ff("-f", "lavfi", "-i", `aevalsrc='exp(-t*9)*sin(2*PI*(36+55*exp(-t*14))*t)*0.95+0.3*exp(-t*60)*(random(0)*2-1)':d=0.9:s=${SR}`,
  "-af", "lowpass=f=3000,aecho=0.7:0.35:80:0.25,alimiter=limit=0.85", "-ac", "2", out("thud-b.wav"));
// 3) knocks: damped wood modes + a noise click + a small room
for (const p of [182, 171, 196]) {
  ff("-f", "lavfi", "-i", `aevalsrc='exp(-t*36)*(0.75*sin(2*PI*${p}*t)+0.38*sin(2*PI*(${p}*2.31)*t)+0.18*sin(2*PI*(${p}*5.2)*t))+0.45*exp(-t*140)*(random(0)*2-1)':d=0.35:s=${SR}`,
    "-af", "lowpass=f=2600,aecho=0.6:0.35:28|47:0.3|0.2,alimiter=limit=0.9", "-ac", "2", out(`knock-${p}.wav`));
}
// 4) buzz, gated: off 0-0.06, on 0.06-0.14, off 0.14-0.30, on 0.30-0.36, off 0.36-0.52, on 0.52+ (decays)
ff("-f", "lavfi", "-i", `aevalsrc='(between(t,0.06,0.14)+between(t,0.30,0.36)+between(t,0.52,0.9)*exp(-(t-0.52)*5))*(0.35*sin(2*PI*100*t)+0.25*sin(2*PI*200*t)+0.18*sin(2*PI*300*t)+0.12*sin(2*PI*500*t)+0.2*(random(0)*2-1))':d=0.9:s=${SR}`,
  "-af", "highpass=f=80,lowpass=f=5000,alimiter=limit=0.8", "-ac", "2", out("buzz.wav"));
// 5) whoosh
ff("-f", "lavfi", "-i", `anoisesrc=d=1.0:c=pink:r=${SR}:a=0.9:s=3`,
  "-af", "highpass=f=250,lowpass=f=4200,volume='if(lt(t,0.8),pow(t/0.8,2.4),max(0,1-(t-0.8)/0.18))':eval=frame,aphaser=in_gain=0.7:out_gain=0.9:delay=2.5:decay=0.5:speed=1.3,alimiter=limit=0.8",
  "-ac", "2", out("whoosh.wav"));

// peak-normalise each effect to -3 dBFS; the mix sets the final level with data-volume
for (const f of ["thud", "thud-b", "knock-182", "knock-171", "knock-196", "buzz", "whoosh"]) {
  const log = execFileSync("sh", ["-c", `ffmpeg -hide_banner -i "${out(`${f}.wav`)}" -af volumedetect -f null - 2>&1`]).toString();
  const m = /max_volume: (-?[\d.]+) dB/.exec(log);
  const gain = -3 - +m[1];
  ff("-i", out(`${f}.wav`), "-af", `volume=${gain.toFixed(2)}dB`, out(`${f}.n.wav`));
  renameSync(out(`${f}.n.wav`), out(`${f}.wav`));
}
console.log(`wrote ambient + 7 effects to ${OUT}`);
