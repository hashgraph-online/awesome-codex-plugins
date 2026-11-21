#!/usr/bin/env python3
"""Rank voice takes with an audio LLM judge without trusting its taste (references/judge.md).

  judge_takes.py prompt take --line "I didn't mean to break it."     the one-take check prompt, line filled in
  judge_takes.py prompt pair --question "Which take sounds more like someone apologising than reading?"
  judge_takes.py check reply.json --line "..." [--need-breath]        the judge's one-take JSON -> pass / fail / review
  judge_takes.py make t1.mp3 t2.mp3 t3.mp3 -o pairs/ [--video]        every pair in both orders, blind file names
  judge_takes.py tally pairs/pairs.json verdicts.json                 wins count only when both orders agree

`make` levels every take to the same loudness, joins A, a short tone and B into one file (one file per pair beats two
uploads, AudioJudge), and names files p01_ab, p01_ba so nothing says which take is which. --video makes MP4s with
CLIP A / CLIP B cards for video-only judges such as varg analyze_video (needs Pillow); prefer audio when the judge
takes audio: Gemini hears audio inside a video at 1 Kbps, an audio file at 16 Kbps.
`verdicts.json` maps each pair id to the judge's answer: "A", "B", "tie", or the reply object with an "answer" key.
"""
import argparse, itertools, json, os, re, subprocess, sys

TAKE_PROMPT = """You are checking ONE voice take. The script line is: "{line}"
Listen to the whole take. Do not compare it with anything and do not say whether it is good.
1. Write down exactly what you hear, word for word.
2. List every sound that is not a word (breath, sigh, sniff, laugh, click, noise) with its MM:SS time, or "none".
Then for each question write one short reason, then answer yes, no or unknown (unknown when the audio does not tell you):
Q1 Is any word missing, added or changed compared with the script line?
Q2 Is a stage direction spoken as a word (for example "sigh", "exhales", "quietly")?
Q3 Is any name or brand word said wrongly? Give its MM:SS.
Q4 Is the last syllable cut off?
Ignore the accent, the voice's gender and any music. Don't call the take good. Report what you hear.
Return JSON: {{"heard": "...", "sounds": [{{"t": "MM:SS", "what": "..."}}],
 "Q1": {{"reason": "...", "answer": "yes|no|unknown"}}, "Q2": {{...}}, "Q3": {{...}}, "Q4": {{...}}}}"""

PAIR_PROMPT = """This file holds two takes of the same line: "CLIP A", a short tone, then "CLIP B".
Question: {question}
First describe each take in one sentence about this question only. Then answer A, B or tie.
Answer tie if you are not sure. Return JSON: {{"A": "...", "B": "...", "answer": "A|B|tie"}}"""

BREATH = re.compile(r"breath|inhal|exhal|gasp|sigh|sniff", re.I)


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


def load_reply(path):
    raw = open(path).read()
    m = re.search(r"\{.*\}", raw, re.S)  # judges often wrap JSON in prose or a code fence
    if not m:
        die(f"{path}: no JSON object in the reply")
    return json.loads(m.group(0))


def cmd_prompt(a):
    if a.kind == "take":
        if not a.line:
            die("prompt take needs --line")
        print(TAKE_PROMPT.format(line=a.line))
    else:
        if not a.question:
            die("prompt pair needs --question (one narrow question, never 'which is better')")
        print(PAIR_PROMPT.format(question=a.question))


def cmd_check(a):
    r = load_reply(a.reply)
    fails, review = [], []
    for q, what in (("Q1", "words differ from the line"), ("Q2", "a stage direction is spoken"),
                    ("Q3", "a name is said wrongly"), ("Q4", "the last syllable is cut off")):
        ans = str((r.get(q) or {}).get("answer", "unknown")).strip().lower()
        if ans == "yes":
            fails.append(f"{q}: {what} ({(r.get(q) or {}).get('reason', '')})")
        elif ans != "no":
            review.append(f"{q}: {ans}")
    # the judge's own transcript, checked in code instead of trusting its Q1
    heard = re.sub(r"\[[^\]]*\]|\([^)]*\)|\*[^*]*\*", " ", str(r.get("heard", "")))  # [sigh], (pause) are not words
    heard, line = words(heard), words(a.line)
    if heard and heard != line:
        extra = [w for w in heard if w not in line]
        missing = [w for w in line if w not in heard]
        fails.append(f"transcript differs: missing {missing or '-'}, extra {extra or '-'}")
    elif not heard:
        review.append("no transcript in the reply")
    sounds = r.get("sounds") or []
    if isinstance(sounds, str):
        sounds = [] if sounds.strip().lower() == "none" else [{"what": sounds}]
    if a.need_breath and not any(BREATH.search(str(s.get("what", s))) for s in sounds):
        fails.append("no breath or sigh listed, and the cue asks for one")
    verdict = "fail" if fails else "review" if review else "pass"
    out = {"verdict": verdict, "fails": fails, "review": review,
           "sounds": [f"{s.get('t', '?')} {s.get('what', s)}" for s in sounds if isinstance(s, dict)]}
    print(json.dumps(out, indent=2))
    sys.exit(0 if verdict == "pass" else 1)


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         stdout=subprocess.PIPE, text=True, check=True).stdout
    return float(out)


def cmd_make(a):
    if len(a.takes) < 2:
        die("make needs at least two takes")
    for t in a.takes:
        if not os.path.exists(t):
            die(f"missing {t}")
    os.makedirs(a.out, exist_ok=True)
    tmp = os.path.join(a.out, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    # same loudness for every take: a louder take wins on loudness alone
    lev = []
    for i, t in enumerate(a.takes):
        p = os.path.join(tmp, f"t{i}.wav")
        ff("-i", t, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "1", p)
        lev.append(p)
    tone = os.path.join(tmp, "tone.wav")  # 0.5 s quiet, 0.3 s 1 kHz beep, 0.5 s quiet
    ff("-f", "lavfi", "-i", "sine=f=1000:d=0.3:sample_rate=48000", "-af",
       "volume=-20dB,adelay=500,apad=pad_dur=0.5", "-ac", "1", tone)
    cards = {}
    if a.video:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            die("--video needs Pillow (uv run --with pillow)")
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 150)
        except OSError:
            font = next((ImageFont.truetype(f, 150) for f in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                         "/Library/Fonts/Arial.ttf") if os.path.exists(f)), ImageFont.load_default())
        for lab in ("A", "B", ""):
            im = Image.new("RGB", (1280, 720))
            if lab:
                d = ImageDraw.Draw(im)
                txt = f"CLIP {lab}"
                d.text(((1280 - d.textlength(txt, font=font)) / 2, 280), txt, fill=(255, 255, 255), font=font)
            cards[lab] = os.path.join(tmp, f"card_{lab or 'gap'}.png")
            im.save(cards[lab])
    pairs = []
    for n, (i, j) in enumerate(itertools.combinations(range(len(a.takes)), 2), 1):
        for order, (x, y) in (("ab", (i, j)), ("ba", (j, i))):
            pid = f"p{n:02d}_{order}"
            ext = "mp4" if a.video else "wav"
            out = os.path.join(a.out, f"{pid}.{ext}")
            if a.video:
                segs = []
                for k, (img, aud) in enumerate(((cards["A"], lev[x]), (cards[""], tone), (cards["B"], lev[y]))):
                    s = os.path.join(tmp, f"s{k}.mp4")
                    # an explicit length: -shortest with a looped still overshoots by up to a second
                    ff("-loop", "1", "-framerate", "10", "-i", img, "-i", aud, "-t", f"{seconds(aud):.3f}", "-c:v", "libx264",
                       "-tune", "stillimage", "-pix_fmt", "yuv420p", "-r", "10", "-c:a", "aac", "-ar", "48000",
                       "-ac", "2", "-b:a", "160k", s)
                    segs.append(s)
                lst = os.path.join(tmp, "list.txt")
                open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
                ff("-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", out)
            else:
                ff("-i", lev[x], "-i", tone, "-i", lev[y], "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1",
                   "-ar", "48000", "-ac", "1", out)
            pairs.append({"id": pid, "file": out, "A": a.takes[x], "B": a.takes[y]})
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    manifest = os.path.join(a.out, "pairs.json")
    json.dump({"takes": a.takes, "pairs": pairs}, open(manifest, "w"), indent=2)
    print(f"{len(pairs)} files for {len(pairs) // 2} pairs -> {manifest}")
    print("Send each file to the judge with `prompt pair`, in a fresh call; never tell it which take is which.")


def answer_of(v):
    if isinstance(v, dict):
        v = v.get("answer")
    v = str(v or "").strip().upper()
    return v if v in ("A", "B") else "TIE"


def cmd_tally(a):
    man = json.load(open(a.pairs))
    verdicts = json.load(open(a.verdicts))
    wins = {t: 0 for t in man["takes"]}
    by_pair = {}
    for p in man["pairs"]:
        key = p["id"].rsplit("_", 1)[0]
        if p["id"] not in verdicts:
            die(f"no verdict for {p['id']}")
        ans = answer_of(verdicts[p["id"]])
        by_pair.setdefault(key, []).append(p["A"] if ans == "A" else p["B"] if ans == "B" else None)
    rows, split = [], []
    for key, picks in sorted(by_pair.items()):
        if len(picks) == 2 and picks[0] and picks[0] == picks[1]:
            wins[picks[0]] += 1
            rows.append((key, os.path.basename(picks[0])))
        else:
            rows.append((key, "tie" if picks[0] == picks[1] else "split"))
            if picks[0] != picks[1]:
                split.append(key)
    for key, res in rows:
        print(f"{key}: {res}")
    print("\nconsistent wins:")
    for t, w in sorted(wins.items(), key=lambda kv: -kv[1]):
        print(f"  {w}  {t}")
    if split:
        print(f"\nsplit across orders (send to a person): {', '.join(split)}")
    print("A person listens to the top 2-3 and picks; log the pick and the reason as a label.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt")
    p.add_argument("kind", choices=["take", "pair"])
    p.add_argument("--line")
    p.add_argument("--question")
    p.set_defaults(fn=cmd_prompt)
    p = sub.add_parser("check")
    p.add_argument("reply")
    p.add_argument("--line", required=True)
    p.add_argument("--need-breath", action="store_true")
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser("make")
    p.add_argument("takes", nargs="+")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--video", action="store_true")
    p.set_defaults(fn=cmd_make)
    p = sub.add_parser("tally")
    p.add_argument("pairs")
    p.add_argument("verdicts")
    p.set_defaults(fn=cmd_tally)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
