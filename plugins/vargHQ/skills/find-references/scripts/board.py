#!/usr/bin/env python3
"""Build the board a person picks references from: one page, grouped by job, shuffled, then numbered, with no scores.

  board.py board.json board.html [--seed N]

Input JSON:
  {"title": "...", "jobs": [{"job": "light", "want": "the want card in words",
    "candidates": [{"file": "refs/01.jpg" or "url": "https://...", "title": "...", "link": "https://...",
                    "lends": "...", "must_not_copy": "...", "rights": "feed | words | look", "provenance": "..."}]}]}

A `look` reference has `link` and no `file` or `url`: nobody keeps its image and the page does not hotlink it. Its card
says "No image. Open the link."

Three candidates per job. `file` is relative to board.json, and the page keeps relative paths, so keep the images beside
it. Audio and video files get a player. Each candidate has keep and reject buttons and a note, saved in this browser.
"Copy my picks" gives JSON to paste back to the agent. Text is escaped, and only http and https links are used.
"""
import argparse
import hashlib
import html
import json
import os
import random
import sys
import urllib.parse

AUDIO = (".mp3", ".ogg", ".oga", ".wav", ".m4a", ".flac")
VIDEO = (".mp4", ".webm", ".mov")

STYLE = """
:root{color-scheme:light dark;--bg:#fafaf8;--card:#fff;--ink:#1c1c1a;--muted:#62625c;--line:#d9d9d2;--keep:#17693b;
--reject:#a32a22;--media:#ecece7}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1e1e1c;--ink:#eeeee8;--muted:#a5a59c;--line:#3a3a36;
--keep:#6fcf97;--reject:#f28b82;--media:#0d0d0c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1180px;margin:0 auto;padding:24px 16px 96px}
h1{font-size:1.6rem;line-height:1.2;margin:0 0 8px}
h2{font-size:1.2rem;margin:40px 0 4px;text-transform:capitalize}
.lede,.want{color:var(--muted);margin:0 0 16px;max-width:70ch}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fill,minmax(min(100%,320px),1fr))}
article{background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;display:flex;
flex-direction:column}
article[data-verdict=keep]{border-color:var(--keep);box-shadow:inset 0 0 0 1px var(--keep)}
article[data-verdict=reject]{opacity:.62}
.media{background:var(--media);display:flex;align-items:center;justify-content:center;min-height:120px}
.media img,.media video{display:block;max-width:100%;max-height:520px;height:auto}
.media audio{width:100%;margin:16px}
.none{color:var(--muted);padding:32px 16px}
.body{padding:12px;display:flex;flex-direction:column;gap:8px;flex:1}
.num{font-weight:700;margin-right:6px}
h3{font-size:1rem;line-height:1.35;margin:0;overflow-wrap:anywhere}
dl{margin:0;font-size:.9rem;display:grid;gap:2px}
dt{color:var(--muted);font-size:.78rem;margin-top:6px}
dd{margin:0;overflow-wrap:anywhere}
a{color:inherit}
.actions{display:flex;gap:8px;margin-top:auto;padding-top:8px}
button{font:inherit;min-height:44px;padding:0 14px;border:1px solid var(--line);border-radius:6px;
background:transparent;color:var(--ink);cursor:pointer}
button[aria-pressed=true][data-set=keep]{background:var(--keep);border-color:var(--keep);color:var(--card)}
button[aria-pressed=true][data-set=reject]{background:var(--reject);border-color:var(--reject);color:var(--card)}
textarea{font:inherit;width:100%;min-height:64px;padding:8px;border:1px solid var(--line);border-radius:6px;
background:transparent;color:var(--ink);resize:vertical}
footer{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:8px 16px;
display:flex;gap:12px;align-items:center;justify-content:space-between}
#count{color:var(--muted);font-size:.9rem}
#out{display:none;position:fixed;left:16px;right:16px;bottom:72px;height:40vh;background:var(--card)}
"""

SCRIPT = """
(function () {
  var KEY = "find-references-board:" + document.body.dataset.board;
  var state = {};
  try { state = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { state = {}; }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* the page still works */ } }
  var cards = Array.prototype.slice.call(document.querySelectorAll("article"));
  function paint(card) {
    var s = state[card.dataset.id] || {};
    if (s.verdict) { card.dataset.verdict = s.verdict; } else { delete card.dataset.verdict; }
    card.querySelectorAll("button[data-set]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.set === s.verdict));
    });
    card.querySelector("textarea").value = s.note || "";
  }
  function count() {
    var kept = cards.filter(function (c) { return (state[c.dataset.id] || {}).verdict === "keep"; }).length;
    document.getElementById("count").textContent = kept + " kept of " + cards.length;
  }
  cards.forEach(function (card) {
    var id = card.dataset.id;
    card.querySelectorAll("button[data-set]").forEach(function (b) {
      b.addEventListener("click", function () {
        state[id] = state[id] || {};
        state[id].verdict = state[id].verdict === b.dataset.set ? null : b.dataset.set;
        save(); paint(card); count();
      });
    });
    card.querySelector("textarea").addEventListener("input", function (e) {
      state[id] = state[id] || {};
      state[id].note = e.target.value;
      save();
    });
    paint(card);
  });
  count();
  document.getElementById("copy").addEventListener("click", function () {
    var picks = cards.map(function (c) {
      var s = state[c.dataset.id] || {};
      return { number: Number(c.dataset.number), job: c.dataset.job, title: c.dataset.title, ref: c.dataset.ref,
               verdict: s.verdict || null, note: s.note || "" };
    }).filter(function (p) { return p.verdict || p.note; });
    var text = JSON.stringify({ board: document.title, picks: picks }, null, 1);
    var out = document.getElementById("out");
    var button = this;
    function shown() {
      out.style.display = "block"; out.value = text; out.select(); button.textContent = "Select and copy";
    }
    function done() { out.style.display = "none"; button.textContent = "Copied"; }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, shown);
    } else { shown(); }
  });
})();
"""


def safe_link(url):
    """Only http and https. Anything else in a downloaded record becomes no link."""
    return url if urllib.parse.urlsplit(url or "").scheme in ("http", "https") else ""


def media(candidate, board_dir, out_dir):
    """The candidate's picture or player, with a path relative to the page."""
    source = safe_link(candidate.get("url"))
    if candidate.get("file"):
        path = os.path.relpath(os.path.join(board_dir, candidate["file"]), out_dir)
        source = "/".join(urllib.parse.quote(part) for part in path.split(os.sep))
    if not source:
        return '<div class="media"><p class="none">No image. Open the link.</p></div>'
    src = html.escape(source, quote=True)
    extension = os.path.splitext(urllib.parse.urlsplit(source).path)[1].lower()
    if extension in AUDIO:
        return f'<div class="media"><audio controls preload="none" src="{src}"></audio></div>'
    if extension in VIDEO:
        return f'<div class="media"><video controls preload="metadata" src="{src}"></video></div>'
    alt = html.escape(candidate.get("title") or "Candidate", quote=True)
    return f'<div class="media"><img src="{src}" alt="{alt}"></div>'


def card(candidate, job, number, board_dir, out_dir):
    title = candidate.get("title") or "Untitled"
    link = safe_link(candidate.get("link"))
    ref = link or candidate.get("file") or candidate.get("url") or title
    stable = hashlib.sha256(f"{job}|{ref}".encode()).hexdigest()[:12]
    heading = html.escape(title)
    if link:
        heading = f'<a href="{html.escape(link, quote=True)}" target="_blank" rel="noopener">{heading}</a>'
    rows = "".join(f"<dt>{label}</dt><dd>{html.escape(str(candidate[key]))}</dd>"
                   for label, key in (("Lends", "lends"), ("Must not copy", "must_not_copy"), ("Rights", "rights"),
                                      ("Provenance", "provenance")) if candidate.get(key))
    attributes = " ".join(f'data-{k}="{html.escape(str(v), quote=True)}"' for k, v in (
        ("id", stable), ("number", number), ("job", job), ("title", title), ("ref", ref)))
    return f"""<article {attributes}>
{media(candidate, board_dir, out_dir)}
<div class="body">
<h3><span class="num">{number}</span>{heading}</h3>
<dl>{rows}</dl>
<div class="actions"><button type="button" data-set="keep" aria-pressed="false">Keep</button>
<button type="button" data-set="reject" aria-pressed="false">Reject</button></div>
<textarea aria-label="Note on candidate {number}" placeholder="Why this one, or what is wrong with it?"></textarea>
</div>
</article>"""


def build(board, board_dir, out_dir, seed):
    """The page as a string. Shuffle first, then number, so that a number says nothing about rank."""
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    title = board.get("title") or "References"
    number, sections = 0, []
    for job in board.get("jobs", []):
        name = str(job.get("job") or "job")
        candidates = list(job.get("candidates") or [])
        rng.shuffle(candidates)
        cards = []
        for candidate in candidates:
            number += 1
            cards.append(card(candidate, name, number, board_dir, out_dir))
        want = f'<p class="want">Want: {html.escape(str(job["want"]))}</p>' if job.get("want") else ""
        body = f'<div class="grid">{"".join(cards)}</div>' if cards else '<p class="want">Nothing for this job.</p>'
        sections.append(f"<section><h2>{html.escape(name)}</h2>{want}{body}</section>")
    board_key = hashlib.sha256(title.encode()).hexdigest()[:12]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title><style>{STYLE}</style></head>
<body data-board="{board_key}"><main>
<h1>{html.escape(title)}</h1>
<p class="lede">Random order, no scores. Numbers come from the shuffle and mean nothing. Keep what you would use, reject
the rest, and say why in a note. Then copy your picks and paste them back to the agent.</p>
{"".join(sections)}
</main>
<textarea id="out" aria-label="Your picks as JSON" readonly></textarea>
<footer><span id="count"></span><button type="button" id="copy">Copy my picks</button></footer>
<script>{SCRIPT}</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("board_json")
    ap.add_argument("board_html")
    ap.add_argument("--seed", type=int, help="repeat a shuffle; by default each build is new")
    a = ap.parse_args()
    try:
        with open(a.board_json, encoding="utf-8") as f:
            board = json.load(f)
        board_dir = os.path.dirname(os.path.abspath(a.board_json))
        out_dir = os.path.dirname(os.path.abspath(a.board_html))
        page = build(board, board_dir, out_dir, a.seed)
        with open(a.board_html, "w", encoding="utf-8") as f:
            f.write(page)
    except (OSError, ValueError, AttributeError, TypeError) as error:
        sys.exit(f"board.py: {error}")
    jobs = board.get("jobs", [])
    candidates = sum(len(j.get("candidates") or []) for j in jobs)
    print(json.dumps({"out": a.board_html, "jobs": len(jobs), "candidates": candidates}))


if __name__ == "__main__":
    main()
