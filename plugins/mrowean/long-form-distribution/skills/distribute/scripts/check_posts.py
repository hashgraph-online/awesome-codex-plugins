#!/usr/bin/env python3
"""Check that every post is built from the source piece's own sentences.

Usage:
  python3 check_posts.py --source piece.txt --posts issue.json
  python3 check_posts.py --source piece.txt --posts posts.txt

--source is the piece's full text. --posts is an issue file (the shape in
sample/issues/) or plain text with posts separated by lines of `---`.

Each line of each post is sorted into one of three kinds:

  quoted   every sentence is in the source, ignoring case, punctuation and
           spacing (trimmed sentences count; mark a cut in the middle with
           ... or …)
  adapted  reworded from a source sentence; the closest one is shown
  new      lead-in or framing written for the post

Adapted and new lines are expected: posts need lead-ins and wording that fits
the format. What they must not do is add facts. Any number, quoted phrase or
capitalised name in an adapted or new line that isn't in the source is
flagged NEW FACT. Lines with a URL or [link] are skipped.

It also catches the opposite: a caveat that made sense in the full piece and
disappears when a section becomes a standalone post. A line built from a
source sentence that carries a qualifier ("only", "about", "as of", "may", a
parenthetical...) is flagged CAVEAT? when the post drops it, and so is a
post that skips the source's very next sentence when that sentence is the
caveat ("But...", "Caveat:", "(...)"). These are warnings, not failures:
read the source line and decide whether the post still says what it said.

Also checks length limits: X 280 per post (and per thread post), Bluesky 300,
Threads 500, LinkedIn 1,300.

Exit code 1 on any NEW FACT or TOO LONG, otherwise 0. Standard library only.
"""
import argparse
import difflib
import json
import re
import sys

LIMITS = {"x": 280, "bluesky": 300, "threads": 500, "linkedin": 1300}
MIN_CHARS = 12  # shorter fragments ("So.", "1/") are too short to check

# Words that narrow a claim. Losing one turns "about 2% as of April" into "2%".
QUALIFIERS = [
    "only", "about", "around", "roughly", "approximately", "nearly", "almost",
    "up to", "at least", "at most", "most", "some", "may", "might", "could",
    "likely", "usually", "often", "sometimes", "as of", "until", "unless",
    "except", "though", "although", "however", "caveat", "estimate", "so far",
    "not yet", "early", "preliminary", "in theory", "per", "if",
]
# A sentence that opens like this is the source walking back the one before it.
CAVEAT_OPENERS = re.compile(
    r"^\s*(\(|but\b|however\b|though\b|that said\b|caveat\b|note\b|except\b|unless\b|"
    r"still\b|only\b|the catch\b|one caveat\b)", re.I)


def norm(s):
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"['“”\"]", "", s)
    return re.sub(r"[^a-z0-9%$]+", " ", s).strip()


def load_posts(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    if path.endswith(".json"):
        data = json.loads(raw)
        items = data["items"] if isinstance(data, dict) else data
        return [(i.get("id", str(n + 1)), i.get("platform", ""), i.get("format", ""), i["copy"])
                for n, i in enumerate(items)]
    parts = [p.strip() for p in re.split(r"^\s*---\s*$", raw, flags=re.M) if p.strip()]
    return [(str(n + 1), "", "", p) for n, p in enumerate(parts)]


def is_link_line(line):
    return bool(re.search(r"https?://|\[link\]", line, re.I))


def thread_parts(copy):
    """Split an X/Threads/Bluesky thread on its 1/ 2/ 3/ markers."""
    parts = re.split(r"(?m)^\s*(?=\d+/\s)", copy)
    return [p.strip() for p in parts if p.strip()]


def is_quoted(line, source):
    """True if every sentence in the line is in the source."""
    for sent in re.split(r"(?<=[.!?;:])\s+", line):
        for frag in re.split(r"\.\.\.|\u2026", sent):
            n = norm(frag)
            if len(n) >= MIN_CHARS and n not in source:
                return False
    return True


def closest(line, sentences):
    n = norm(line)
    best, score = "", 0.0
    for s in sentences:
        r = difflib.SequenceMatcher(None, n, norm(s), autojunk=False).ratio()
        if r > score:
            best, score = s, r
    return best, score


def new_facts(line, source):
    """Numbers, quoted phrases and capitalised names not in the source."""
    found = []
    # A number passes if it appears in the source next to the same word on
    # either side ("about 15", "15 reached"), so "12 hours" isn't cleared by
    # "September 12".
    for m in re.finditer(r"\$?\d[\d,.]*%?", line):
        num = m.group().rstrip(".,")
        before = re.findall(r"[\w'\u2019]+", line[:m.start()])[-1:]
        after = re.findall(r"[\w'\u2019%]+", line[m.end():])[:1]
        pairs = [norm(" ".join(before + [num])), norm(" ".join([num] + after))]
        if not any(re.search(r"(^| )" + re.escape(p) + r"( |$)", source) for p in pairs if p):
            found.append(" ".join(before + [num] + after))
    for q in re.findall(r"[\"\u201c]([^\"\u201d]{4,})[\"\u201d]", line):
        if norm(q) not in source:
            found.append(f'"{q}"')
    words = re.findall(r"(?<![.!?:]\s)(?<!^)\b([A-Z][\w'\u2019-]+)", line.strip())
    for w in words:
        if not re.search(r"(^| )" + re.escape(norm(w)) + r"( |$)", source):
            found.append(w)
    return found


def has_word(phrase, text_norm):
    return re.search(r"(^| )" + re.escape(phrase) + r"( |$)", text_norm) is not None


def origin(body, sentences):
    """The index of the source sentence a post line was built from, or None."""
    n = norm(body)
    for i, s in enumerate(sentences):  # quoted, or trimmed from one sentence
        if len(n) >= MIN_CHARS and n in norm(s):
            return i
    near, score = closest(body, sentences)
    return sentences.index(near) if score >= 0.6 else None


def dropped_caveats(copy, used, sentences):
    """Qualifiers and follow-on caveats the source had and the post lost."""
    post = norm(copy)
    out = []
    for i in sorted(used):
        src = sentences[i]
        bare = norm(re.sub(r"\([^)]*\)", " ", src))  # a parenthetical is reported whole, below
        lost = [q for q in QUALIFIERS if has_word(q, bare) and not has_word(q, post)]
        lost += [f"({p})" for p in re.findall(r"\(([^)]{4,})\)", src) if norm(p) not in post]
        if lost:
            out.append(f"source says {', '.join(lost)}, post doesn't\n              in: {src.strip()}")
        nxt = sentences[i + 1].strip() if i + 1 < len(sentences) else ""
        if (nxt and i + 1 not in used and CAVEAT_OPENERS.match(nxt)
                and closest(nxt, [l for l in copy.splitlines() if l.strip()] or [""])[1] < 0.6):
            out.append(f"the next sentence in the source is left out\n              after: {src.strip()}\n              next: {nxt}")
    return out


def check_post(copy, source, sentences):
    notes, failed, used = [], False, set()
    for line in (l.strip() for l in copy.splitlines()):
        body = re.sub(r"^\s*\d+/\s*", "", line)  # thread numbering
        if not body or is_link_line(body):
            continue
        for sent in re.split(r"(?<=[.!?])\s+", body):
            i = origin(sent, sentences)
            if i is not None:
                used.add(i)
        if is_quoted(body, source):
            continue
        near, score = closest(body, sentences)
        if score >= 0.6:
            notes.append(("adapted", f"{body}\n              from: {near}"))
        else:
            notes.append(("new", body))
        facts = new_facts(body, source)
        if facts:
            notes.append(("NEW FACT", ", ".join(facts)))
            failed = True
    notes += [("CAVEAT?", c) for c in dropped_caveats(copy, used, sentences)]
    return failed, notes, used


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", required=True, help="the piece's full text")
    ap.add_argument("--posts", required=True, help="issue .json, or text split by ---")
    a = ap.parse_args()

    with open(a.source, encoding="utf-8") as f:
        text = f.read()
    source = norm(text)
    sentences = [x for x in re.split(r"(?<=[.!?])\s+|\n+", text) if len(norm(x)) >= MIN_CHARS]
    posts = load_posts(a.posts)

    failures = 0
    for pid, platform, fmt, copy in posts:
        failed, notes, _ = check_post(copy, source, sentences)
        limit = LIMITS.get(platform)
        if limit:
            chunks = thread_parts(copy) if fmt == "thread" else [copy]
            for c in chunks:
                if len(c) > limit:
                    notes.append(("TOO LONG", f"{len(c)} > {limit}: {c[:60]}…"))
                    failed = True
        failures += failed
        status = "FAIL" if failed else "ok  "
        print(f"{status} {pid}")
        for kind, text in notes:
            print(f"     {kind}: {text}")

    print(f"\n{len(posts) - failures} of {len(posts)} posts pass.")
    print("Adapted and new lines are fine to keep. Read each one: it should frame or fit the")
    print("author's point, not make a new claim. Read each CAVEAT? against its source line:")
    print("if the post now claims more than the piece did, put the qualifier back.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
