"""Redaction over rendered text: the one redactor, and the argv one beside it.

:func:`redact_text` replaces credential- and identity-shaped values in a
rendered line; :func:`redact_argv` renders a dispatch's argv for the audit
record, the prompt elided and every flag-hinted or secret-shaped value cut.
Every sink that writes provider output (logs, failure captures, batch reports,
the detached run log, jail evidence) goes through :func:`redact_text`, and
always before any cap.

A leaf on purpose: it imports nothing from the skill, so the provider layer,
the Landlock dispatch and the write path all redact through this one table
without reaching up into ``write_safety`` (docs/development/dispatcher.md#import-layers),
which re-exports both functions.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, List, Optional, Sequence, Tuple

#: argv elements whose *value* is redacted before logging, matched
#: case-insensitively on the flag that precedes them. Belt-and-braces: no
#: adapter puts a secret on argv, and if one ever does this catches it.
#: ``write_safety.AuditLog.SECRET_FLAG_HINTS`` is this tuple.
SECRET_FLAG_HINTS = ("key", "token", "secret", "password", "credential", "auth")


# ---------------------------------------------------------------------------
# Redaction over rendered text
# ---------------------------------------------------------------------------
#
# One boundary, four sinks: the success log (``llm_client._save_log``), the
# per-attempt failure captures (``failed/*.attemptN.json``), the batch report
# (``subagent_batch_report.json``) and the exit-3 stdout block that becomes
# ``orchestrator-run.log`` under ``--detach``. Provider stdout/stderr reached all
# four unfiltered; each growing its own filter is the shape this replaces.
#
# **This runs BEFORE any cap.** Both the 64 KiB/line rule and the last-20-lines
# rule cut by construction, and a cut applied first slices a secret into a
# remnant no pattern matches — a byte tail keeps a value whose key name is gone,
# and a line tail keeps a PEM body whose ``-----BEGIN`` header is gone. Nothing
# downstream can recover either.
#
# **Why not just reuse `.gitleaks.toml`.** gitleaks is a Go binary over a file
# tree at commit time; this runs in-process on every rendered line of every
# fan-out slot. The blast radii also run opposite ways — a commit-time false
# positive is a red PR, a runtime false negative is a live credential in
# ``log_*.txt`` — so this set is deliberately a strict *superset*, carrying PII
# and low-entropy delimiter shapes gitleaks must never flag. The one-way drift
# gate lives in ``tests/test_redaction.py``; this table is never transcribed into
# the TOML, which would make the scanner red against this repo's committed
# decoys on day one.

#: The word that makes a key name a *secret* key name.
#: ``auth``/``authorization`` are excluded **on purpose** — P2 covers the header
#: form, and a bare ``auth:`` key is far too common in this repo's auth-plan
#: fixtures. That is the one entry on which this and ``SECRET_FLAG_HINTS``
#: differ, because ``auth`` is a reliable signal in a *flag name*.
_SECRET_KEYWORD = r"(?:secret|passwd|password|token|api[_-]?key|apikey|credential)"

#: What a key name is spelled with. Note which two members are **not** word
#: characters: ``.`` and ``-``. Every ``\b`` inside a run of this class is
#: manufactured by one of those two, and that is the whole of the quadratic
#: story below.
_KEY_CHAR = r"[A-Za-z0-9_.\-]"

#: The key half of a delimited key/value secret: **one maximal run of key
#: characters that contains the keyword**, matched from the run's own start.
#:
#: Underscore/dot/dash-joined compounds around the keyword are the reason this
#: is a run at all — ``aws_secret_access_key`` is a real shape that a
#: word-anchored ``\bsecret\b`` never matches — and the run has to reach from
#: whatever precedes the keyword all the way to the delimiter.
#:
#: **The shape this replaces was quadratic, and it was quadratic at rest.**
#: It read ``\b [KEY_CHAR]* KEYWORD [KEY_CHAR]*``, two unbounded greedy runs
#: around the keyword, and nothing about the 2026-09-22 anchoring work touched
#: it — this row shipped that way for as long as the table has existed. Both
#: runs cost the same way. CPython's ``re`` retries the whole pattern at every
#: start position the left anchor admits; at each of them the leading ``*`` ran
#: to the end of the key-character run and then backtracked one character at a
#: time looking for the keyword, and every keyword it found on the way ran the
#: *trailing* ``*`` to the end of the run and backtracked that too, looking for
#: the delimiter. So the work is (start positions) x (run length), and ``\b``
#: does not bound the first factor the way it does for a prose pattern: ``.``
#: and ``-`` are in the character class **and** are non-word characters, so a
#: run densely punctuated with either manufactures a word boundary every few
#: characters while never breaking the run.
#:
#: MEASURED 2026-09-22 at HEAD, one ``pattern.sub`` pass, doubling the input:
#:
#: ===========================  =========  =========  =========
#: 1 line of...                      8 KB      16 KB      32 KB
#: ===========================  =========  =========  =========
#: prose with spaces             0.0003 s   0.0007 s   0.0014 s
#: JSON-ish                      0.0003 s   0.0005 s   0.0011 s
#: pure base64                   0.0003 s   0.0006 s   0.0012 s
#: base64url (``-``/``_``)       0.1224 s   0.4953 s   1.9670 s
#: hyphenated slugs              0.5020 s   1.9862 s   7.9555 s
#: dotted identifiers            1.0282 s   4.1735 s  16.5351 s
#: ``token.`` repeated           98.904 s          -          -
#: ===========================  =========  =========  =========
#:
#: Four-fold per doubling is n^2. Whitespace, quotes and braces break the run
#: and keep it linear, which is why prose and JSON were never slow and why
#: nobody noticed; a base64url blob, a dotted module-path list or a run of
#: hyphenated slugs on **one line** has none of them. 32 KB of dotted
#: identifiers already costs 15 s, and :func:`redact_text` runs on the FULL
#: provider stream **before** ``_bound_stream`` caps it, so a megabyte of it is hours
#: inside every log sink.
#:
#: **The rule now.** One run, walked once::
#:
#:     (?<!KEY_CHAR)  (?= KEY_CHAR*? KEYWORD )  KEY_CHAR*   …then _DELIM, _CAND
#:      run start          the run holds it      consume it
#:
#: Three things changed, and each needs its own argument, because only the
#: third one is about speed:
#:
#: 1. *Two runs became one.* The old shape cut the run in half at the keyword
#:    and made the engine find the cut by backtracking. The keyword is still
#:    required, but as a **lookahead over the whole run** rather than as a seam
#:    inside it. That costs nothing: "a run containing the keyword" and "a run
#:    that splits into prefix + keyword + suffix" are the same set of runs, and
#:    the group that gets replaced is the **value**, which is past the run
#:    either way — so where inside the run the old pattern chose to start never
#:    affected what came out.
#: 2. *``\b`` became ``(?<!KEY_CHAR)``, and it HAD to.* The old ``\b`` guarded
#:    the start of the *leading* run, not the keyword. Keep it once the two
#:    runs are one and it demands a word boundary immediately before the
#:    keyword — which ``aws_secret_access_key`` does not have. That is exactly
#:    the narrowing a bound-the-runs-and-keep-``\b`` fix would have shipped,
#:    and it is why this row could not be repaired the way P11 was. The
#:    lookbehind that replaces it says "this is the first character of the
#:    run", which is a property of the *run* rather than of English: it is true
#:    at exactly one position inside any run, and no key name can fail it,
#:    because every run has a start.
#: 3. *The run is still unbounded, deliberately.* Bounding it is the obvious
#:    fix and it is a real narrowing — a key name with more than the bound
#:    between its last secret word and its delimiter would silently stop being
#:    redacted — so it is not what shipped. The linearity comes from the
#:    lookahead instead: a lookahead in Python is **atomic**, never re-entered
#:    on backtracking, so "does this run hold a keyword?" is asked once per
#:    RUN rather than once per keyword occurrence, and the run is then consumed
#:    exactly once. Per run of length L that is O(L) for the lookahead, O(L) to
#:    consume it and O(L) lookbehinds that fail at the other positions; runs
#:    are disjoint, so the pass is O(n).
#:
#: One property of ``_DELIM`` is doing quiet work under (3): its first
#: character is always one of ``"``, ``'``, whitespace, ``:`` or ``=``, and
#: **none of those is a key character**. So the *maximal* run is the only place
#: the delimiter can possibly match, every shorter one is dead, and a run that
#: is walked once rather than re-cut loses nothing by construction.
#:
#: DIFFERENTIALLY VERIFIED 2026-09-22 over 975 200 generated strings (random
#: character soup, random fragment soup, and the full cross product of glue x
#: keyword x separator x delimiter x value, separators up to 1 000 characters):
#: **zero** characters that the old row redacted and this one does not, and on
#: every ASCII-only input the output is byte-identical. The 21 320 inputs where
#: it differs are all the same broadening and all non-ASCII: a keyword glued
#: directly behind a word character *outside* ``[A-Za-z0-9_]`` (``ötoken=…``)
#: has no ``\b`` anywhere in front of it and was therefore invisible to the old
#: row — the same glue gap section 1b closed for the vendor prefixes, closed
#: here for free.
#:
#: And it is linear: 0.04 s per megabyte on **every** shape in the table above,
#: the 98 s one included. ``tests/test_redaction.py``'s
#: ``TestRedactTextIsLinearOnAMegabyteStream`` now runs this row against the
#: dotted, hyphenated, base64url and keyword-dense payloads with no exception
#: list at all.
_SECRET_KEY = (
    r"(?<!" + _KEY_CHAR + r")"                                  # at a run start
    r"(?=" + _KEY_CHAR + r"*?" + _SECRET_KEYWORD + r")"         # the run holds it
    + _KEY_CHAR + r"*"                                          # consume the run
)

#: An explicit ``:`` or ``=`` is mandatory, and the optional quotes are what make
#: ``"api_key": "…"`` match. **Never relax this to whitespace**: the measured
#: 114 false positives — "token generation", "password hashing", "Token refresh"
#: — all came from a whitespace-separated branch, and no real secret is emitted
#: without a delimiter.
_DELIM = r"[\"']?\s*[:=]\s*[\"']?"

#: The candidate value, qualified further by :func:`_looks_like_credential`.
_CAND = r"[^\s\"',;]{8,}"

#: Punctuation that says "expression", not "credential". Model output routinely
#: contains code, and code contains ``JWT_SECRET = os.environ.get(…)``.
_CODEY = set("(){}[]<>$\\!`|&*")

#: Values that are the keyword itself (``password=password``) or a placeholder.
_PLACEHOLDER_VALUES = {
    "password", "secret", "token", "apikey", "api_key", "credential", "passwd",
    "changeme", "example", "redacted", "required", "optional",
    "true", "false", "none", "null",
}


def _looks_like_credential(value: str) -> bool:
    """Whether a delimited value is plausibly a credential rather than code.

    Delimiter-anchoring alone is not sufficient — it still fires on
    ``password=password``, ``JWT_SECRET = os.environ.get(…)`` and
    ``password_hash=bcrypt.hashpw(…)`` in the e2e response fixtures. This is the
    other half of the precision story, and it is not optional.
    """
    if len(value) < 8 or (_CODEY & set(value)):
        return False
    if value.strip("'\"").lower() in _PLACEHOLDER_VALUES:
        return False
    # A bare integer is a count, never a credential. Measured 2026-09-17 on a
    # real ``claude -p --output-format json`` failure: the envelope's
    # ``"cacheReadInputTokens":<eight digits>`` matched the key half on
    # ``token`` and this predicate on "has a digit", so the count came out as
    # ``<redacted:secret-kv>`` and the one JSON document in
    # ``log_claude-code_*.txt`` stopped parsing — the salvage gate then read
    # the mangled excerpt as a truncated structure. Every token counter claude
    # emits (``output_tokens``, ``inputTokens``, ``thinkingTokens``, …) carries
    # the keyword, and a review's counters routinely pass eight digits.
    if value.isdigit():
        return False
    return (
        any(c.isdigit() for c in value)
        or (any(c.isupper() for c in value) and any(c.islower() for c in value))
        or any(c in "-_./+=" for c in value)
    )


#: P12's two delimiters, and the block they bound.
_PEM_BEGIN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_PEM_END = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")
#: The P12 language itself: header, the shortest body, footer.
_PEM_BLOCK = re.compile(_PEM_BEGIN.pattern + r"[\s\S]*?" + _PEM_END.pattern)


class _PemPrivateKeyBlocks:
    """P12's row: exactly the matches of :data:`_PEM_BLOCK`, found in O(n).

    ``_PEM_BLOCK.finditer`` itself is quadratic in the number of headers that
    have no footer after them. CPython retries the pattern at every
    ``-----BEGIN`` and each retry's lazy body runs to the end of the text
    looking for a ``-----END`` that is not there: 0.1 s at 32 KB of repeated
    headers, 6.7 s at 256 KB (about 100 s at a megabyte), and
    :func:`redact_text` runs on the whole provider stream before any cap.

    The scan here asks the same question once. A header ends at the one place
    ``PRIVATE KEY-----`` closes its ``[A-Z ]`` run, so every later header ends
    later; when the first header has no footer after it, none does, and the
    scan stops. Otherwise it is the leftmost header, the first footer after its
    end, and the scan resumes past that footer, as ``finditer`` does. Each
    block is then matched with ``_PEM_BLOCK`` itself, bounded to that span, so
    the rows' callers (:func:`redact_text`, the executor's offset replay) get
    the same ``re.Match`` objects, and the redacted set is the regex's, byte for
    byte (``tests/test_redaction_pem_scanner.py``).
    """

    pattern = _PEM_BLOCK.pattern

    def finditer(self, string: str):
        pos = 0
        while True:
            begin = _PEM_BEGIN.search(string, pos)
            if begin is None:
                return
            end = _PEM_END.search(string, begin.end())
            if end is None:
                return
            yield _PEM_BLOCK.match(string, begin.start(), end.end())
            pos = end.end()

    def sub(self, repl: Any, string: str, count: int = 0) -> str:
        pieces: List[str] = []
        last = 0
        for index, match in enumerate(self.finditer(string)):
            if count and index >= count:
                break
            pieces.append(string[last:match.start()])
            pieces.append(repl(match) if callable(repl) else match.expand(repl))
            last = match.end()
        pieces.append(string[last:])
        return "".join(pieces)


#: ``(name, compiled pattern, group to replace, predicate)``. The *value* is
#: replaced, never the whole line, so surrounding text stays diffable and a
#: redacted log is still a usable failure artifact. A row's pattern is a
#: compiled regex, or an object with the same ``finditer``/``sub`` (P12).
#:
#: Order is load-bearing in one direction only: the multi-line and prefix shapes
#: run before the generic key/value branch, so a value they already replaced
#: reaches P1 as ``<redacted:…>`` — which ``_looks_like_credential`` rejects on
#: its angle brackets. That is also what makes :func:`redact_text` idempotent.
_REDACTIONS: List[Tuple[str, Any, int, Optional[Any]]] = [
    # P12 — multi-line, so it runs first: nothing else may chew its body.
    # `_PEM_BLOCK`'s matches, scanned linearly (see `_PemPrivateKeyBlocks`).
    ("pem-private-key", _PemPrivateKeyBlocks(), 0, None),
    # P13 — identity/PII, in the **two shapes the probe boundary really
    # emits**, both of them key-named. A bare unkeyed email pattern is still
    # deliberately not shipped: it would redact commit-message prose in
    # container_turns/.
    #
    # (a) The quoted-JSON key form — what `cursor-agent about|status --format
    # json` returns. The value bound is `+`, not `{3,}`: a two-character shell
    # (`sh`) is as much an identity field as a long one, and the old floor let
    # it through unredacted.
    (
        "identity-json",
        re.compile(
            r"[\"'](?:userEmail|email|terminalProgram|shell)[\"']\s*:\s*[\"']([^\"']+)[\"']"
        ),
        1,
        None,
    ),
    # (b) The `Key  Value` text table a build **without** `--format` prints, and
    # which `providers.cursor_agent._about_text_pairs` parses — reachable since
    # `about` was wired back in as `setup_probe`, so an unmatched line here is a
    # real identity value in a probe tail and in `CursorAbout.redacted`. Kept
    # tight so `shell = …` and `email = …` in prose and source stay untouched:
    # the label **starts the line**, the separator is that parser's own (`: `,
    # two spaces, or a tab) and the value runs to end of line. The label's
    # separator spellings are accepted because the same parser normalizes them
    # away before it looks the key up.
    (
        "identity-text",
        re.compile(
            r"(?im)^[ \t]*(?:user[ _\-]?email|email|terminal[ _\-]?program|shell)"
            r"(?:[ \t]*:[ \t]+|[ \t]{2,}|\t[ \t]*)(\S[^\n]*?)[ \t]*$"
        ),
        1,
        None,
    ),
    # P3–P10 — vendor prefixes, every one qualified by length and charset so a
    # short decoy is a non-match by construction rather than by exception.
    #
    # **The left anchor is per-prefix, and `\b` is not the default.** A leading
    # `\b` says "this shape may not begin inside a token", which is true of
    # prose and false of a credential: a key glued to a preceding word character
    # is still the key. MEASURED 2026-09-22 against a real claude-code
    # transcript, where a probe script printed the word `SET` with the value
    # glued straight onto it — `SETsk-proj-…`, `SETsk-or-v1-…` — after an
    # environment variable's name and a delimiter. `T` followed by `s` is not a
    # word boundary, so not one vendor pattern fired. The `OPENAI_API_KEY` line
    # survived anyway on P1's key half; the line whose key name was the bare
    # word `KEY` matched no key half either and reached disk intact. Agents
    # concatenate, and a rendered log is full of other programs' output, so
    # every row below was vulnerable in isolation.
    #
    # The anchor a row gets is decided by ONE question — *can this row's prefix
    # literal occur inside ordinary text whose tail its body charset accepts?*
    # — and the answer puts it in one of three tiers:
    #
    # * **No left anchor** for a prefix English cannot reach at all: `xox?-`,
    #   `AIza`, `glpat-`, `hf_`, `eyJ` + its two dots, `AKIA`/`ASIA`, and a URL
    #   scheme (which needs `://…:…@` besides). `AKIA`/`ASIA` earn it despite
    #   `ASIA` being an English word: the body is `[0-9A-Z]{16}`, so "inside a
    #   token" here means inside a 20-char uppercase blob, never prose —
    #   word-hood was not what that `\b` was protecting.
    # * **`(?<![a-z])`** for the two prefixes English *can* reach, and which it
    #   can only ever reach with a **lowercase letter** immediately before them.
    #   `sk-` ends `task`, `risk`, `disk`, `ask`, and the body accepts hyphens,
    #   so every vendor infix has a constructible compound behind it —
    #   `risk-ant-colony-optimization-solver`,
    #   `task-or-v1-branch-protection-rules`,
    #   `disk-live-migration-controller`. `gh[opusr]_` is reachable through the
    #   `-s` plural (`laughs_`, `weighs_`, `coughs_`) plus a 16-character run
    #   with no underscore in it. In every one of those the character before the
    #   prefix is lowercase, while the glue this fix exists for is uppercase, a
    #   digit, `_` or punctuation — `sk`/`gh` are lowercase, so a letter before
    #   them is a camelCase transition and never a word. The lookbehind
    #   therefore keeps the whole measured class and gives up exactly one glue:
    #   a lowercase letter. Stated rather than implied, because it is the one
    #   place this fix is narrower than an unanchored sweep would be.
    # * **`\b`, unchanged** for the two genuinely ambiguous ones: bare `sk-`
    #   plus 16 body characters is `task-oriented-development-workflow`,
    #   `risk-projection-model` and this repo's own `ask-suggestion-advisory`,
    #   none of which a lookbehind would save; and P2's `bearer`/`basic` end
    #   `forbearer` and `ultrabasic`, either of which would then eat the next
    #   eight-character word.
    #
    # Nothing below narrows: each row's old anchored language is a subset of
    # its new one, so this is broader redaction and never less.
    (
        "sk-family",
        re.compile(
            r"(?:(?<![a-z])sk-(?:ant-|proj-|or-v1-|live-)|\bsk-)[A-Za-z0-9_\-]{16,}\b"
        ),
        0,
        None,
    ),
    ("slack", re.compile(r"xox[baprse]-[A-Za-z0-9-]{8,}\b"), 0, None),
    ("github", re.compile(r"(?<![a-z])gh[opusr]_[A-Za-z0-9]{16,}\b"), 0, None),
    ("google-api-key", re.compile(r"AIza[0-9A-Za-z_\-]{35,}"), 0, None),
    ("aws-access-key-id", re.compile(r"(?:AKIA|ASIA)[0-9A-Z]{16}\b"), 0, None),
    ("gitlab-pat", re.compile(r"glpat-[A-Za-z0-9_\-]{20,}\b"), 0, None),
    ("huggingface", re.compile(r"hf_[A-Za-z0-9]{30,}\b"), 0, None),
    (
        "jwt",
        re.compile(r"eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"),
        0,
        None,
    ),
    # P11 — the password half only; the username survives so the URL stays
    # recognisable in a failure artifact. Unanchored: the scheme is lowercase,
    # so `\b` already let a lowercase glue through by matching the glue itself
    # as part of the scheme (`xhttps://…`) while refusing `SEThttps://…` — an
    # inconsistency, not a control, and the group replaced is the password
    # either way.
    #
    # **The scheme run is BOUNDED, and that bound is load-bearing**. This is the one row
    # whose pattern opens with a character
    # class rather than a literal, so CPython cannot skip start positions with
    # its literal-prefix scan — every other row here begins `sk-`, `xox`, `gh`,
    # `AIza`, `AKIA`, `glpat-`, `hf_` or `eyJ` and is scanned in C. Dropping
    # `\b` therefore took the start positions from "one per word" to "one per
    # character", and with `*` each of them greedily ran to the end of the
    # buffer and backtracked looking for `://`: **quadratic**. Measured on a
    # run of one character, 0.16 s at 20 KB, 2.5 s at 80 KB, 40 s at 320 KB,
    # which is ~1600 s on the 2 MB a provider really can emit — and `redact_text`
    # runs on the FULL stream **before** `_bound_stream` caps it, so an unbounded
    # quantifier here is a hang in
    # every log sink rather than a slow test. `{0,31}` makes the work per start
    # position constant, so the row is linear again: 0.038 s at 1.28 MB, the
    # same class as the rest of the table.
    #
    # It costs no coverage. The bound is on a *suffix* of the scheme and the
    # pattern is unanchored, so a scheme longer than 32 characters simply
    # matches starting later and replaces the same group — every string the
    # `\b`-anchored original redacted is still redacted, and so is every string
    # the unbounded version was redacting.
    (
        "url-basic-auth",
        re.compile(r"[a-z][a-z0-9+.\-]{0,31}://([^/\s:@]+):([^/\s@]+)@"),
        2,
        None,
    ),
    # P2 — the header form, and the one place `bearer`/`basic` are keywords.
    # `\b` stays: see the third tier above.
    (
        "auth-scheme",
        re.compile(r"(?i)\b(?:authorization\s*:\s*)?(?:bearer|basic)\s+([A-Za-z0-9._\-+/=]{8,})"),
        1,
        None,
    ),
    # P1 — the generic delimited key/value branch, last and predicate-gated.
    # No left anchor: ``_SECRET_KEY`` carries its own, and it is a run-start
    # lookbehind rather than ``\b`` — see the analysis over that constant for
    # why the two are not interchangeable here and why the old ``\b`` shape was
    # quadratic on one line of dotted or hyphenated provider output.
    (
        "secret-kv",
        re.compile(r"(?i)" + _SECRET_KEY + r"(?:" + _DELIM + r")(" + _CAND + r")"),
        1,
        _looks_like_credential,
    ),
]


def _replace_group(match: "re.Match", group: int, name: str) -> str:
    """The matched text with ``group`` swapped for ``<redacted:{name}>``."""
    start, end = match.span(group)
    if start < 0:  # an optional group that did not participate
        return match.group(0)
    base = match.start()
    return match.group(0)[: start - base] + f"<redacted:{name}>" + match.group(0)[end - base:]


def redact_text(text: str) -> str:
    """Credential- and identity-shaped values in ``text``, replaced in place.

    Applied to the **fully rendered** line — and always *before* any truncation
    cap, which is why L3 and L4 land together. The matched value is replaced with
    ``<redacted:{name}>``; the surrounding text is untouched.

    Out of scope, stated rather than implied: a high-entropy value with no
    keyword, no prefix and no delimiter (a bare 40-char blob in prose) cannot be
    caught by regex. That is accepted — keeping the credential out of the child's
    environment in the first place is the primary control, and this is the
    backstop.
    """
    if not text:
        return text or ""
    out = text
    for name, pattern, group, predicate in _REDACTIONS:
        def _sub(match, _name=name, _group=group, _predicate=predicate):
            if _predicate is not None and not _predicate(match.group(_group)):
                return match.group(0)
            return _replace_group(match, _group, _name)

        out = pattern.sub(_sub, out)
    return out


def redact_argv(argv: Sequence[str], prompt: str) -> List[str]:
    """The rendered argv with the prompt elided and any secret-shaped value cut.

    The prompt becomes ``<prompt sha256:… bytes:…>`` so the audit record proves
    *which* prompt ran without carrying its bytes.

    Two passes, and the flag-hint one is **kept, not replaced**: knowing
    a value's *position* from ``--api-key`` is strictly stronger than any pattern
    and catches the bare high-entropy blob no regex can. Every argument that
    survives that pass then goes through :func:`redact_text`, which closes the
    inverse hole — a secret in an argument that carries no hinted flag.
    """
    digest = _sha256_text(prompt)
    length = len((prompt or "").encode("utf-8"))
    out: List[str] = []
    redact_next = False
    for arg in argv:
        if prompt and arg == prompt:
            out.append(f"<prompt sha256:{digest} bytes:{length}>")
            redact_next = False
            continue
        if redact_next:
            out.append("<redacted>")
            redact_next = False
            continue
        lowered = arg.lower()
        if arg.startswith("-") and any(
            hint in lowered for hint in SECRET_FLAG_HINTS
        ):
            if "=" in arg:
                out.append(arg.split("=", 1)[0] + "=<redacted>")
                continue
            out.append(arg)
            redact_next = True
            continue
        out.append(redact_text(arg))
    return out


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
