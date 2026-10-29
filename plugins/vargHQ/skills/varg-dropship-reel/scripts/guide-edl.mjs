#!/usr/bin/env node
// Write edit.json for the guide reel from the voiceover's word timings: every laptop screen is cut
// in on the word that names it, so the picture changes exactly when the voice moves on.
//
//   node guide-edl.mjs words.json clips/ > edit.json
//   node guide-edl.mjs words.json clips/ --lang es > edit.json          # a localized voiceover (en, es built in)
//   node guide-edl.mjs words.json clips/ --anchors anchors.json > edit.json   # any language: your own anchor phrases
//
// clips/ holds (5 s image-to-video clips unless noted):
//   hook1.mp4 hook2.mp4          the hook, two clips (any length)
//   productA.mp4                 research page, pen: photo → product cost → sell price
//   productB.mp4                 research page, pen: profit → demand chart → "Generate my store"
//   store.mp4                    store product page, pen: price → Add to cart
//   home.mp4                     research tool landing page
//   settings.mp4                 store settings: free shipping, payments, Launch
//   adpaste.mp4 ads.mp4          AI ad tool: paste link / the generated videos
//   flow.mp4                     TikTok · Reels · Shorts → your store
//   orders.mp4                   orders paid and shipped
//   skyline.mp4                  the ending
// The script must follow references/script.md (the anchors below are its words); words.json is a
// transcription with word timestamps ({ "words": [{ "word", "start", "end" }] }).
// Runs with node 18+ or bun; needs ffprobe.
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const argv = process.argv.slice(2);
const flag = (name) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? argv.splice(i, 2)[1] : undefined; };
const lang = flag("lang") ?? "en";
const anchorsFile = flag("anchors");
const [wordsPath, clipsDir = "clips"] = argv;
if (!wordsPath) {
  console.error("usage: node guide-edl.mjs words.json clips/ > edit.json");
  process.exit(1);
}
const raw = JSON.parse(readFileSync(wordsPath, "utf8"));
const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9$.]/g, "");
const W = (raw.words ?? raw.data?.words).map((w) => ({ t: norm(w.word), start: w.start, end: w.end }));

// The phrase that starts each beat of the script, per language (accents are ignored). "buy" starts one
// word earlier ("It/They/Se can be purchased"). Another language: pass --anchors with the same keys.
const ANCHORS = {
  en: { buy: "can be purchased", sold: "sold", even: "even after", here: "here is how", first: "first", offer: "offer", then: "then go", itWill: "it will", start: "start posting", when: "when a customer", comment: "comment" },
  es: { buy: "pueden comprar", sold: "vender", even: "incluso despues", here: "asi es como", first: "primero", offer: "ofrece", then: "luego entra", itWill: "generara", start: "empieza a publicar", when: "cuando un cliente", comment: "comenta" },
};
const A = anchorsFile ? JSON.parse(readFileSync(anchorsFile, "utf8")) : ANCHORS[lang];
if (!A) throw new Error(`no built-in anchors for "${lang}": pass --anchors anchors.json`);

const find = (phrase, after = 0) => {
  const seq = phrase.split(" ").map(norm);
  for (let i = 0; i + seq.length <= W.length; i++) {
    if (W[i].start >= after && seq.every((s, k) => W[i + k].t.startsWith(s))) return i;
  }
  throw new Error(`anchor "${phrase}" not found after ${after}s: does the script follow references/script.md?`);
};
const at = (phrase, after = 0, back = 0) => W[find(phrase, after) - back].start;
const len = (f) => Number(spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", join(clipsDir, f)]).stdout.toString());

const buy = at(A.buy, 0, 1); // starts one word earlier: "It"/"They"/"Se"
const sold = at(A.sold, buy);
const even = at(A.even, sold);
const here = at(A.here, even);
const first = at(A.first, here);
const offer = at(A.offer, first);
const then = at(A.then, offer);
const itWill = at(A.itWill, then);
const start = at(A.start, itWill);
const when = at(A.when, start);
const comment = at(A.comment, when);
const end = W[W.length - 1].end + 0.5;

const shots = [];
const add = (file, from, to, inPoint = 0, zoom = 1) => {
  const dur = +(to - from).toFixed(3);
  const avail = len(file) - inPoint - 0.05;
  const s = { file: join(clipsDir, file), in: inPoint, dur };
  if (zoom !== 1) s.zoom = zoom;
  if (dur > avail) s.speed = +Math.max(0.6, avail / dur).toFixed(3); // slow a short clip down a little
  shots.push(s);
};
const h1 = Math.min(len("hook1.mp4") - 0.3, buy / 2);
add("hook1.mp4", 0, h1, 0.2);
add("hook2.mp4", h1, buy, 0.3);
add("productA.mp4", buy, sold);
add("store.mp4", sold, even, 0.3);
add("productB.mp4", even, here);
add("productA.mp4", here, first, 0, 1.1); // "without even touching the product": back on the photo
const mid = first + (offer - first) * 0.45;
add("home.mp4", first, mid, 0.4);
add("productB.mp4", mid, offer, 2.6, 1.08); // "…and generate a free store": the button
add("settings.mp4", offer, then);
add("adpaste.mp4", then, itWill, 0.3);
add("ads.mp4", itWill, start);
add("flow.mp4", start, when, 0.2);
add("orders.mp4", when, comment);
add("skyline.mp4", comment, end, 0.3);

console.log(JSON.stringify({ out: "reel.mp4", voiceover: "vo.mp3", captions: "captions.ass", fontsdir: "fonts", hook: +buy.toFixed(2), shots }, null, 1));
console.error(`${shots.length} shots, ${shots.reduce((a, s) => a + s.dur, 0).toFixed(2)} s, hook ${buy.toFixed(2)} s`);
