#!/usr/bin/env python3
"""Find what the user keeps correcting: the raw material for a new skill or a new rule.
usage: mine_corrections.py [--days N] [--project SUBSTR] [--top K] [--out FILE]
Reads Claude Code transcripts (~/.claude/projects/**/*.jsonl), keeps the user's own messages
that sound like a correction or rejection, groups them by theme and prints the themes that
recur across the most sessions, each with dated verbatim quotes. Nothing leaves the machine."""
import collections, glob, json, os, re, sys, time

THEMES = {  # theme → words that signal it (zh / en); extend freely
    "looks cheap / ugly": r"丑|难看|土|廉价|降了档次|像模板|像 ?PPT|ugly|cheap|generic|template",
    "didn't look at references": r"参考|没好好找|照着|reference",
    "asked instead of doing": r"别问|不要什么都问|自己做|自己定|直接做|stop asking|just do",
    "can't see the result": r"看不到|发我看|给我看|只看到选项|show me|can't see",
    "followed my example too literally": r"只是(启发|例子)|不是范围|不一定要听我|example",
    "too slow / too expensive": r"卡顿|卡死|好卡|很卡|太慢|好慢|额度|烧 ?token|slow|quota|expensive",
    "lost or overwrote work": r"丢|毁了|覆盖|找回|lost|overwrit|deleted",
    "sounds like AI": r"AI ?味|像 ?AI|说人话|sounds like AI|robotic",
    "wrong / not what I asked": r"不对|错了|不是这个|没听懂|我说的是|wrong|not what I",
}
NEG = r"不要|别|不对|错|丑|又|还是|怎么|为什么|没|不是|wrong|don't|stop|again|why|not"

def args():
    a = sys.argv[1:]
    get = lambda k, d: a[a.index(k) + 1] if k in a else d
    return int(get("--days", 30)), get("--project", ""), int(get("--top", 8)), get("--out", None)

def user_texts(path):
    for line in open(path, errors="ignore"):
        try:
            o = json.loads(line)
        except Exception:
            continue
        m = o.get("message")
        if o.get("type") != "user" or o.get("isMeta") or not isinstance(m, dict) or m.get("role") != "user":
            continue
        c = m.get("content")
        t = c if isinstance(c, str) else "\n".join(x.get("text", "") for x in c or [] if isinstance(x, dict) and x.get("type") == "text")
        t = re.sub(r"<([a-z-]+)[^>]*>.*?</\1>", "", t, flags=re.S).strip()  # system reminders, notices, other sessions
        if t and not t.startswith(("[Request interrupted", "Caveat:", "Base directory", "This session is being continued", "Task (from", "Background (from")) \
                and "from the session that started" not in t[:300]:
            yield (o.get("timestamp") or "")[:10], t

def main():
    days, proj, top, out = args()
    cutoff = time.time() - days * 86400
    hits = collections.defaultdict(list)
    for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        if proj not in f or os.path.getmtime(f) < cutoff:
            continue
        sid = os.path.basename(f)[:8]
        for day, t in user_texts(f):
            if len(t) > 1500 or not re.search(NEG, t, re.I):
                continue
            for theme, pat in THEMES.items():
                if re.search(pat, t, re.I):
                    hits[theme].append((day, sid, t))
    ranked = sorted(hits.items(), key=lambda kv: -len({s for _, s, _ in kv[1]}))[:top]
    lines = [f"# Repeated corrections, last {days} days", "",
             "A theme that recurs across many sessions and no skill covers yet is a skill candidate; one covered by a skill that still recurs means the skill isn't working (make it a gate or a script).", ""]
    for theme, xs in ranked:
        sessions = {s for _, s, _ in xs}
        lines += [f"## {theme} — {len(sessions)} sessions, {len(xs)} messages", ""]
        seen = set()
        for day, sid, t in sorted(xs, reverse=True):
            q = re.sub(r"\s+", " ", t)[:220]
            if q in seen:
                continue
            seen.add(q)
            lines.append(f"- {day} `{sid}`: {q}")
            if len(seen) == 6:
                break
        lines.append("")
    text = "\n".join(lines)
    if out:
        open(out, "w").write(text)
        print(f"wrote {out}: {len(ranked)} themes")
    else:
        print(text)

if __name__ == "__main__":
    main()
