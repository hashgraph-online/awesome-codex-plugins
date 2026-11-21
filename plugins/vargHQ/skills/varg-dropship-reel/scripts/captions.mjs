#!/usr/bin/env node
// Word-by-word "money reel" captions: 1-2 words at a time, bold uppercase, white with a
// black outline, numbers/prices and chosen keywords in lime. Input is a varg transcription
// result with word timestamps (groq_whisper_large_v3_turbo returns `data.words`).
//
//   node captions.mjs words.json captions.ass [--keywords "shopify,profit,guide"] [--width 1080 --height 1920]
//   ffmpeg -i reel.mp4 -vf "subtitles=captions.ass:fontsdir=fonts" -c:a copy reel_captioned.mp4
//
// Runs with node 18+ or bun, no dependencies.
import { readFileSync, writeFileSync } from "node:fs";

const [input, output = "captions.ass", ...rest] = process.argv.slice(2);
if (!input) {
  console.error("usage: node captions.mjs words.json captions.ass [--keywords a,b] [--width 1080] [--height 1920] [--font Bangers]");
  process.exit(1);
}
const opt = (name, fallback) => {
  const i = rest.indexOf(`--${name}`);
  return i >= 0 ? rest[i + 1] : fallback;
};
const W = Number(opt("width", 1080));
const H = Number(opt("height", 1920));
const font = opt("font", "Bangers");
const keywords = new Set(
  opt("keywords", "shopify,profit,demand,free,guide,china,ai,instagram,tiktok")
    .split(",").map((k) => k.trim().toLowerCase()).filter(Boolean),
);

const raw = JSON.parse(readFileSync(input, "utf8"));
const words = raw.words ?? raw.data?.words ?? raw.output?.data?.words;
if (!Array.isArray(words)) {
  console.error("No `words` array found. Transcribe with groq_whisper_large_v3_turbo, which returns word timestamps.");
  process.exit(1);
}

// Whisper sometimes glues "for $4.47" into one token (Groq) and sometimes splits "$4" ".47" or "varg"
// ".ai" (local whisper): split on spaces, then glue ".47" / ".ai" back on, so a price or a domain is one beat.
const tokens = [];
for (const w of words) {
  const parts = String(w.word).trim().split(/\s+/).filter(Boolean);
  const span = (w.end - w.start) / parts.length;
  parts.forEach((p, i) => {
    const prev = tokens[tokens.length - 1];
    const gluePrice = /^[.,]\d/.test(p) && /\d$/.test(prev?.text ?? "");
    const glueDomain = /^\.[a-z]{2,6}\b/i.test(p) && /[a-z0-9]$/i.test(prev?.text ?? ""); // "varg" ".ai"
    const glueHyphen = /^-[a-z]/i.test(p) && /[a-z]$/i.test(prev?.text ?? ""); // "step" "-by" "-step"
    if (i === 0 && prev && (gluePrice || glueDomain || glueHyphen)) {
      prev.text += p;
      prev.end = w.end;
      return;
    }
    tokens.push({ text: p, start: w.start + i * span, end: w.start + (i + 1) * span });
  });
}

const isHot = (t) => /[$€£\d]/.test(t) || keywords.has(t.toLowerCase().replace(/[^a-z0-9]/g, ""));
const clean = (t) => t.replace(/^[,"]+|[,"]+$/g, "").toUpperCase();

// Group into chunks of up to 2 words / 14 characters; a price or keyword always starts its own chunk
// unless it is the second word of a short pair ("FOR $4.47" reads well as one beat).
const chunks = [];
for (const t of tokens) {
  const last = chunks[chunks.length - 1];
  const text = clean(t.text);
  if (!text) continue;
  const fits = last && last.words.length < 2 && (last.chars + text.length + 1) <= 14 && !/[.!?]$/.test(last.words.at(-1).raw);
  if (fits) {
    last.words.push({ text, raw: t.text, hot: isHot(t.text) });
    last.chars += text.length + 1;
    last.end = t.end;
  } else {
    chunks.push({ words: [{ text, raw: t.text, hot: isHot(t.text) }], chars: text.length, start: t.start, end: t.end });
  }
}
// Hold each chunk until the next one starts (no flicker between words).
chunks.forEach((c, i) => { if (chunks[i + 1]) c.end = Math.max(c.end, chunks[i + 1].start); });

const ts = (s) => {
  const cs = Math.max(0, Math.round(s * 100));
  const h = Math.floor(cs / 360000), m = Math.floor(cs / 6000) % 60, sec = Math.floor(cs / 100) % 60, c = cs % 100;
  return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}.${String(c).padStart(2, "0")}`;
};
const LIME = "&H003BFF9B&"; // #9BFF3B in ASS BGR order
const size = Math.round(W * 0.14); // the originals run 1-2 words across about half the frame width
const y = Math.round(H * 0.6);

const header = `[Script Info]
ScriptType: v4.00+
PlayResX: ${W}
PlayResY: ${H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Money,${font},${size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,${Math.round(size * 0.09)},${Math.round(size * 0.06)},5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;
const lines = chunks.map((c) => {
  const text = c.words.map((w) => (w.hot ? `{\\c${LIME}}${w.text}{\\c&H00FFFFFF&}` : w.text)).join(" ");
  // Small pop-in: 85% -> 100% over 80 ms.
  return `Dialogue: 0,${ts(c.start)},${ts(c.end)},Money,,0,0,0,,{\\pos(${W / 2},${y})\\fscx85\\fscy85\\t(0,80,\\fscx100\\fscy100)}${text}`;
});
writeFileSync(output, header + lines.join("\n") + "\n");
console.error(`${chunks.length} caption beats -> ${output}`);
