// Build word-timed caption groups from a word transcript and write them into index.html.
// usage (from the project folder): bun captions.mjs [transcript.json] [voOffsetSeconds] [skipWords] [lastEnd]
//   transcript: [{ text, start, end }] (hyperframes transcribe output)
//   voOffset:   the voice <audio> data-start (words are shifted by it)
//   skipWords:  leading words already shown as a title (e.g. "Day one." = 2)
//   lastEnd:    hard end for the last group (e.g. when the choice card takes over)
import { readFileSync, writeFileSync } from "node:fs";

const [src = "assets/audio/transcript.json", off = "0.2", skip = "2", lastEndArg = "20.2"] = process.argv.slice(2);
const OFF = +off, SKIP = +skip, LAST_END = +lastEndArg;
const MAX_WORDS = 3, MAX_CHARS = 18, PAUSE = 0.15; // one line at 74 px on a 1080-wide frame
const raw = JSON.parse(readFileSync(src, "utf8"));
const words = (Array.isArray(raw) ? raw : raw.words)
  .map((w) => ({ text: String(w.text).trim(), start: +w.start + OFF, end: +w.end + OFF }))
  .filter((w) => w.text && !/^[♪�]+$/.test(w.text))
  .slice(SKIP)
  .filter((w) => w.start < LAST_END - 0.05); // the ending card says the rest

// display fixes: numbers the ASR wrote as digits, then uppercase
const show = (s) => s.replace(/^1201(\W*)$/, "12:01$1").toUpperCase();

const groups = [];
let cur = [];
words.forEach((w, i) => {
  cur.push(w);
  const next = words[i + 1];
  const punct = /[.,?!:;]$/.test(w.text);
  const gap = next ? next.start - w.end : 1;
  const tooLong = next && [...cur, next].map((x) => x.text).join(" ").length > MAX_CHARS;
  if (!next || punct || gap >= PAUSE || cur.length >= MAX_WORDS || tooLong) { groups.push(cur); cur = []; }
});

const data = groups.map((g, gi) => {
  const start = Math.max(g[0].start - 0.04, gi ? groups[gi - 1].at(-1).end : 0);
  return { id: `cap${gi}`, start: +start.toFixed(3), words: g.map((w, wi) => ({ id: `cap${gi}w${wi}`, text: show(w.text), start: +w.start.toFixed(3), end: +w.end.toFixed(3) })) };
});
data.forEach((g, gi) => {
  const lastWord = g.words.at(-1).end;
  const next = data[gi + 1];
  g.end = +(next ? Math.min(next.start, lastWord + 0.35) : Math.min(LAST_END, lastWord + 0.3)).toFixed(3);
});

// one line, never wrapped: shrink long groups (Archivo Black caps average ~0.8 em per character)
const LINE_W = 920, BASE = 74, MIN = 54;
const sizeFor = (g) => Math.max(MIN, Math.min(BASE, Math.floor(LINE_W / (g.words.map((w) => w.text).join(" ").length * 0.8))));
const html = data.map((g) => `        <div id="${g.id}" class="cap" style="font-size:${sizeFor(g)}px">${g.words.map((w) => `<span id="${w.id}" class="w">${w.text}</span>`).join(" ")}</div>`).join("\n");
let page = readFileSync("index.html", "utf8");
page = page.replace(/<!--CAPTIONS:START-->[\s\S]*?<!--CAPTIONS:END-->/, `<!--CAPTIONS:START-->\n${html}\n<!--CAPTIONS:END-->`);
page = page.replace(/\/\*CAPTION_DATA:START\*\/[\s\S]*?\/\*CAPTION_DATA:END\*\//, `/*CAPTION_DATA:START*/\n        const CAPS = ${JSON.stringify(data.map((g) => ({ id: g.id, start: g.start, end: g.end, words: g.words.map(({ id, start, end }) => ({ id, start, end })) })))};\n        /*CAPTION_DATA:END*/`);
writeFileSync("index.html", page);
console.log(data.map((g) => `${g.start.toFixed(2)}-${g.end.toFixed(2)}  ${g.words.map((w) => w.text).join(" ")}`).join("\n"));
