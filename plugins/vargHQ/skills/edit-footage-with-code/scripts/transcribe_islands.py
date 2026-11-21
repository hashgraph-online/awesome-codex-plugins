#!/usr/bin/env python3
"""Transcribe each stretch of speech on its own, so ASR cannot hide a retake.

  python3 transcribe_islands.py take.mp4 --take-json edit/take.json --out edit/islands

Whisper-family models tidy repeats into one clean sentence and stretch words across pauses.
Given one island at a time they cannot. Writes edit/islands/words.json on the take's clock:
feed it back into analyze_take.py --words. Slower than one pass: a few seconds per island.
"""
import argparse, json, os, shlex, subprocess, sys


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("take"); p.add_argument("--take-json", required=True); p.add_argument("--out", default="edit/islands")
    p.add_argument("--gap", type=float, default=0.35, help="a pause this long starts a new island")
    p.add_argument("--model", default="small.en"); p.add_argument("--language")
    p.add_argument("--cmd", default="npx hyperframes transcribe {wav} -d {dir} --model {model} --json",
                   help="any command that writes {dir}/transcript.json as [{text,start,end}]")
    a = p.parse_args()
    speech = json.load(open(a.take_json))["speech"]
    islands = []
    for s, e in speech:
        if islands and s - islands[-1][1] < a.gap:
            islands[-1][1] = e
        else:
            islands.append([s, e])
    os.makedirs(a.out, exist_ok=True)
    words = []
    for i, (s, e) in enumerate(islands):
        d = os.path.join(a.out, "i%03d" % i); os.makedirs(d, exist_ok=True)
        wav = os.path.join(d, "island.wav")
        # a little room either side so the first and last consonants survive
        s0, e0 = max(0, s - 0.08), e + 0.12
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % s0, "-to", "%.3f" % e0, "-i", a.take, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)
        cmd = a.cmd.format(wav=shlex.quote(wav), dir=shlex.quote(d), model=a.model)
        if a.language:
            cmd += " --language " + shlex.quote(a.language)
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        path = os.path.join(d, "transcript.json")
        if r.returncode or not os.path.exists(path):
            print("island %d (%.2f-%.2f s) failed: %s" % (i, s, e, r.stderr.strip()[-200:]), file=sys.stderr)
            continue
        for w in json.load(open(path)):
            words.append({"text": w["text"], "start": round(min(e0, s0 + float(w["start"])), 3), "end": round(min(e0, s0 + float(w["end"])), 3), "island": i})
    json.dump(words, open(os.path.join(a.out, "words.json"), "w"), indent=0)
    print(json.dumps({"islands": len(islands), "words": len(words), "file": os.path.join(a.out, "words.json")}))


if __name__ == "__main__":
    main()
