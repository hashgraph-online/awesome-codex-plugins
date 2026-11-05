#!/usr/bin/env python3
"""Check a video script written in the video-script format. Measures, does not judge taste.

Usage: python3 check_script.py script.md [--json]
Exit code 1 when any check FAILs.

The script file: `key: value` header lines, then one Markdown table with the columns
| # | time | spoken | on screen | visual | sound |   (column names are matched loosely)
Header keys read here: format, length, wpm, hook_max, max_shot, facts, cta. Everything else is ignored.
With `facts: <file>` every number in the spoken and on-screen columns must also appear in that file.
"""
import json
import re
import sys

DEFAULTS = {
    "wpm": 150,        # comfortable narration pace; 2.5 words a second
    "hook_max": {"social": 3, "ad": 3, "drama": 3, "demo": 5, "review": 5, "explainer": 5},
    "max_shot": 11,    # 4-11 s runs obey the prompt better and retake cheaper; set per model
    "caption_s_per_word": 0.33,  # BBC subtitle guidelines: 160-180 wpm, about 0.33 s a word
}

# Phrases that mark machine-written copy. Each one is a reason to rewrite the line, not a ban on the idea.
AI_TELLS = [
    "delve", "tapestry", "testament to", "in today's fast-paced", "in today's world", "ever-evolving",
    "game-changer", "game changer", "revolutionize", "unlock the power", "unleash", "elevate your",
    "seamless", "seamlessly", "cutting-edge", "next level", "take it to the next level", "look no further",
    "whether you're", "imagine a world", "buckle up", "let's dive in", "dive into", "without further ado",
    "it's not just", "isn't just", "more than just", "the best part?", "here's the thing", "picture this",
    "say goodbye to", "say hello to", "transform the way", "embark", "journey", "realm", "landscape",
    # chatbot flattery: the sycophancy family
    "great question", "excellent question", "you're absolutely right",
]
# Patterns that a phrase list can't catch. (regex, label)
AI_TELL_PATTERNS = [
    # "It's not a glow. It's a vibe." / "This isn't a tool, it's a revolution."
    (r"\b(it's|it is|this is|that's|it was|this was|this isn't|it isn't|that isn't)\s+(not\s+)?(just\s+|only\s+)?"
     r"(a |an |the )?[\w' -]{1,30}[.,;:\u2014\u2013-]+\s*(it's|it is|this is|that's|it was|this was)\b",
     "it's not X. it's Y"),
]
WEAK_OPENERS = [
    "hey guys", "hi guys", "welcome back", "in this video", "today we're going to", "today i'm going to",
    "have you ever wondered", "did you know", "hello everyone", "what's up",
]
CTA_WORDS = ["try", "get", "download", "sign up", "link", "shop", "order", "start", "join", "follow",
             "comment", "save", "visit", "book", "grab", "tap", "watch", "subscribe", "install", "claim"]


def parse_time(s):
    s = s.strip().lower().replace("s", "")
    if ":" in s:
        m, sec = s.split(":", 1)
        return int(m) * 60 + float(sec)
    return float(s)


def parse(path):
    text = open(path, encoding="utf-8").read()
    header, rows, cols = {}, [], None
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cols is None:
                cols = [c.lower() for c in cells]
                continue
            if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                continue
            rows.append(dict(zip(cols, cells)))
        elif cols is None:
            m = re.match(r"^\s*([a-z_ ]+):\s*(.+)$", line, re.I)
            if m:
                header[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
    return header, rows, text


def col(row, *names):
    for k, v in row.items():
        if any(n in k for n in names):
            return v
    return ""


def spoken_words(s):
    s = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", s)          # stage directions, [src: ...]
    s = re.sub(r"\b[A-Z][A-Z0-9 ]{1,20}:\s*", " ", s)     # SPEAKER: labels
    s = s.replace("<br>", " ")
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'’%$.,-]*", s)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    header, rows, text = parse(sys.argv[1])
    fmt = header.get("format", "social").split()[0].lower()

    def num(key, default):
        m = re.match(r"\s*([\d.]+)", header.get(key, ""))
        return float(m.group(1)) if m else float(default)

    wpm = num("wpm", DEFAULTS["wpm"])
    wps = wpm / 60
    hook_max = num("hook_max", DEFAULTS["hook_max"].get(fmt, 3))
    max_shot = num("max_shot", DEFAULTS["max_shot"])
    header["facts"] = header.get("facts", "").split("  ")[0].strip()
    res = []

    def add(level, check, msg):
        res.append({"level": level, "check": check, "msg": msg})

    if not rows:
        add("FAIL", "table", "no beat table found (| # | time | spoken | on screen | visual | sound |)")
        return finish(res)

    beats = []
    for i, r in enumerate(rows, 1):
        t = col(r, "time")
        m = re.match(r"\s*([\d:.]+)\s*s?\s*[-–—]+\s*([\d:.]+)\s*s?", t)
        if not m:
            add("FAIL", "timing", f"beat {i}: time '{t}' is not start-end (0:00-0:03)")
            continue
        a, b = parse_time(m.group(1)), parse_time(m.group(2))
        beats.append({"n": i, "a": a, "b": b, "spoken": col(r, "spoken", "vo", "dialog", "voice"),
                      "screen": col(r, "screen", "text", "super"), "visual": col(r, "visual", "shot", "image"),
                      "sound": col(r, "sound", "audio", "sfx", "music")})

    # timing
    for x, y in zip(beats, beats[1:]):
        if abs(x["b"] - y["a"]) > 0.25:
            add("FAIL", "timing", f"gap or overlap between beat {x['n']} ({x['b']}s) and beat {y['n']} ({y['a']}s)")
    total = beats[-1]["b"] if beats else 0
    if "length" in header:
        want = parse_time(re.sub(r"[^\d:.]", "", header["length"]) or "0")
        if want and abs(total - want) > max(1.0, 0.1 * want):
            add("FAIL", "length", f"beats run {total:.1f}s, header says {want:.0f}s")

    # pace
    all_words = 0
    for x in beats:
        d = max(0.1, x["b"] - x["a"])
        w = len(spoken_words(x["spoken"]))
        all_words += w
        if w > d * wps * 1.15:
            add("FAIL", "pace", f"beat {x['n']}: {w} words in {d:.1f}s (max ~{d * wps:.0f} at {wpm:.0f} wpm); cut words or add time")
        elif w > d * wps:
            add("WARN", "pace", f"beat {x['n']}: {w} words in {d:.1f}s is tight at {wpm:.0f} wpm")
        sw = len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’%$.,-]*", re.sub(r"\[[^\]]*\]", " ", x["screen"])))
        if sw and sw * DEFAULTS["caption_s_per_word"] > d:
            add("WARN", "caption", f"beat {x['n']}: {sw} on-screen words need {sw * DEFAULTS['caption_s_per_word']:.1f}s to read, beat is {d:.1f}s")
        if d > max_shot:
            add("WARN", "shot", f"beat {x['n']} is {d:.1f}s, longer than one generated clip ({max_shot:.0f}s); split it into shots")
        if not x["visual"].strip() or x["visual"].strip() in ("-", "—"):
            add("FAIL", "visual", f"beat {x['n']} has no visual; every beat must say what we see")
    if total:
        add("INFO", "pace", f"{all_words} spoken words in {total:.0f}s = {all_words / total * 60:.0f} wpm (budget {wpm:.0f})")

    # hook
    h = beats[0]
    if h["a"] > 0.01:
        add("FAIL", "hook", "first beat does not start at 0")
    if h["b"] > hook_max:
        add("WARN", "hook", f"first beat ends at {h['b']:.1f}s; the hook should land by {hook_max:.0f}s for {fmt}")
    if not (h["spoken"].strip() or h["screen"].strip()):
        add("WARN", "hook", "first beat has no words on screen or spoken; say what the video is about at once")
    first = (h["spoken"] or h["screen"]).lower().strip(' "“')
    for p in WEAK_OPENERS:
        if first.startswith(p):
            add("WARN", "hook", f"opens with '{p}': start on the subject, the conflict or the result instead")

    # words
    spoken_all = " ".join(x["spoken"] for x in beats)
    words_all = (spoken_all + " " + " ".join(x["screen"] for x in beats)).lower()
    # each tell is reported with its beat and speaker, so a script can show who says it
    def segments(x):
        spoken = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", x["spoken"]).replace("’", "'").replace("‘", "'")
        parts = re.split(r"\b([A-Z][A-Z0-9 ]{1,20}):\s*", spoken)
        if len(parts) == 1:
            yield "", parts[0]
        else:
            if parts[0].strip():
                yield "", parts[0]
            for i in range(1, len(parts) - 1, 2):
                yield parts[i].strip(), parts[i + 1]
        yield "on screen", x["screen"]
    for x in beats:
        for who, seg in segments(x):
            low = seg.lower()
            where = f"beat {x['n']}" + (f" {who}" if who else "")
            hits = [p for p in AI_TELLS if re.search(r"\b" + re.escape(p) + r"\b", low)]
            hits += [label for rx, label in AI_TELL_PATTERNS if re.search(rx, low)]
            for p in hits:
                add("WARN", "ai-tell", f"{where}: '{p}' reads as machine copy; say the concrete thing instead")
    sentences = [s for s in re.split(r"[.!?]+", re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", spoken_all)) if s.strip()]
    long = [s.strip() for s in sentences if len(s.split()) > 20]
    for s in long[:3]:
        add("WARN", "ear", f"spoken sentence of {len(s.split())} words; split it for the ear: '{s.strip(' \"“”')[:60]}...'")
    n_and_then = len(re.findall(r"\band then\b", spoken_all, re.I))
    if n_and_then >= 2:
        add("WARN", "causality", f"'and then' x{n_and_then}: link beats with 'but' or 'so' (cause), not 'and then'")

    # claims
    import os
    has_sources = bool(re.search(r"^#+\s*sources", text, re.I | re.M))
    facts = header.get("facts", "")
    facts_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), facts) if facts else ""
    facts_text = open(facts_path, encoding="utf-8").read() if facts and os.path.isfile(facts_path) else None
    num_rx = r"\$?\d[\d,.]*\s?(%|x\b|×|percent|million|billion|k\b|°)?"
    for x in beats:
        for field in ("spoken", "screen"):
            s_ = x[field]
            if facts_text is not None:
                for m in re.finditer(r"\d[\d,.]*", s_):
                    n = m.group(0).rstrip(".,")
                    if n not in facts_text and n.replace(",", "") not in facts_text:
                        add("WARN", "claim", f"beat {x['n']}: '{n}' is not in {facts}; every number must come from the facts")
            elif re.search(r"\d+(\.\d+)?\s?(%|x\b|×|percent|million|billion|k\b)|\$\d", s_, re.I) and "[src" not in s_ and not has_sources and not facts:
                add("WARN", "claim", f"beat {x['n']} states a number ('{s_[:50]}') with no facts: file, [src: ...] or Sources section")
    if facts and facts_text is None:
        add("INFO", "claim", f"facts '{facts}' is not a file here; check every number against it by hand")

    # ending
    cta = header.get("cta", "").lower()
    if (fmt in ("ad", "demo", "review") or (fmt == "social" and cta)) and cta.split()[:1] != ["none"]:
        tail = " ".join((x["spoken"] + " " + x["screen"]).lower() for x in beats[-2:])
        if not ((cta and any(w in tail for w in cta.split()[:3])) or any(re.search(r"\b" + w + r"\b", tail) for w in CTA_WORDS)):
            add("WARN", "ending", "no clear next step in the last two beats (one action: what to do, where)")
    return finish(res)


def finish(res):
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1))
    else:
        for r in res:
            print(f"{r['level']:5} {r['check']:9} {r['msg']}")
        n = {lvl: sum(r["level"] == lvl for r in res) for lvl in ("FAIL", "WARN")}
        print(f"\n{n['FAIL']} fail, {n['WARN']} warn")
    sys.exit(1 if any(r["level"] == "FAIL" for r in res) else 0)


if __name__ == "__main__":
    main()
