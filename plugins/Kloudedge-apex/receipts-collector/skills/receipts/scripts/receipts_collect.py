#!/usr/bin/env python3
"""Collect local receipts. Python 3.9+, standard library only."""
import argparse
import bisect
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile

VERSION = "0.1.0"
UTC = dt.timezone.utc
COUNTERS = ("tool_calls", "edits", "checks", "tool_errors", "compactions")
USAGE = ("input", "cache_read", "cache_write", "output")
KINDS = (
    ("tests_pass", r"\b(?:(?:all )?tests? (?:now )?pass(?:ing|es)?|\d+/\d+ pass)\b"),
    ("pushed", r"\bpushed\b"), ("committed", r"\bcommitted\b"),
    ("deployed", r"\bdeployed\b"), ("fixed", r"\bfixed\b"),
    ("verified", r"\bverified\b"),
    ("done", r"\b(?:done|complete(?:d)?|finished|implemented)\b"),
    ("other", r"\b(?:merged|working|ready)\b"),
)
FILTER_KINDS = (
    ("tests_pass", r"\b(?:(?:all )?tests? (?:now )?pass(?:ing|es)?|\d+/\d+ pass)\b"),
    ("pushed", r"\b(?:un)?push(?:ed)?\b"),
    ("committed", r"\b(?:uncommitted|committed|commit)\b"),
    ("deployed", r"\b(?:un)?deploy(?:ed)?\b"),
)
SECRET = re.compile(r"sk-[A-Za-z0-9_-]{16,}|A(?:KIA|SIA)[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|"
                    r"xox[a-z]-[A-Za-z0-9-]{10,}|-----BEGIN|eyJ[A-Za-z0-9_-]{20,}|[rsp]k_(?:live|test)_[A-Za-z0-9]{16,}|"
                    r"AIza[0-9A-Za-z_-]{35}|[A-Za-z0-9_~.-]{3}\dQ~[A-Za-z0-9_~.-]{31,34}|"
                    r"(?i:\b(?:password|passwd|pwd|secret|token|api[_-]?key|accountkey)\s*[=:]\s*['\"]?[^\s;,'\"]+)|"
                    r"(?i:\b\w+_(?:password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*['\"]?[^\s;,'\"]+)|"
                    r"[A-Za-z0-9+/]{32,}={0,2}")
SECRET_TOKEN = re.compile(r"[^\s<>\"'`]*<secret>[^\s<>\"'`]*")
SECRET_FRAGMENT = re.compile(r"[A-Za-z0-9]<secret>|<secret>[-_.~]?[A-Za-z0-9]")
TOOL_NAME = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_.:-]{0,127})?")
# Shared with the verifier; the collector remains a standalone downloadable file.
TLDS = frozenset((
    "com net org io ai dev app co xyz cloud internal local lan corp home arpa "
    "ac ad ae af ag al am ao aq ar as at au aw ax az ba bb bd be bf bg bh bi bj bl bm bn bo bq br bs bt bv bw by bz "
    "ca cc cd cf cg ch ci ck cl cm cn cr cu cv cw cx cy cz de dj dk dm do dz ec ee eg eh er es et eu fi fj fk fm fo fr "
    "ga gb gd ge gf gg gh gi gl gm gn gp gq gr gs gt gu gw gy hk hm hn hr ht hu id ie il im in iq ir is it je jm jo jp "
    "ke kg kh ki km kn kp kr kw ky kz la lb lc li lk lr ls lt lu lv ly ma mc md me mf mg mh mk ml mm mn mo mp mq mr ms "
    "mt mu mv mw mx my mz na nc ne nf ng ni nl no np nr nu nz om pa pe pf pg ph pk pl pm pn pr ps pt pw py qa re ro rs "
    "ru rw sa sb sc sd se sg sh si sj sk sl sm sn so sr ss st su sv sx sy sz tc td tf tg th tj tk tl tm tn to tr tt tv "
    "tw tz ua ug uk us uy uz va vc ve vg vi vn vu wf ws ye yt za zm zw"
).split())
IPV4 = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}"
LEAKS = (
    ("url", re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s<>\"'`]*")),
    ("email", re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]*@[\w.-]+\.[A-Za-z]{2,}")),
    ("email", re.compile(r"\S*@\S+\.\S+")),
    ("email", re.compile(r"[\w.+-]+@[A-Za-z][\w-]*(?![\w.-])")),
    ("path", re.compile(r"\S*[A-Za-z]:\\\S*")),
    ("path", re.compile(r"(?<![\w])(?:[A-Za-z]:[\\/]|\\\\|~/|\.\.?/|/)[^\s<>\"'`]*")),
    ("relative_path", re.compile(r"\b[\w.-]+(?:[/\\][\w.-]+)+\b")),
    ("path", re.compile(r"\b[\w-]+\.(?:py|js|ts|tsx|jsx|jsonl?|md|txt|toml|yaml|yml|sh|rs|go|java|c|h|cpp|swift|html|css|csv|log|"
                        r"pdf|doc|docx|xls|xlsx|ppt|pptx|key|pem|p12|pfx|crt|cer|sql|db|sqlite|env|tf|tfvars|rb|php|kt|kts|scala|cs|"
                        r"vue|svelte|dart|proto|ipynb|lock|ini|cfg|conf|xml|zip|tar|gz|parquet)\b", re.I)),
    ("path", re.compile(r"(?<![\w/<.])\.[A-Za-z][\w.-]*/?")),
    ("path", re.compile(r"(?<![\w<])[\w.-]+/(?=[\s,.;:)]|$)")),
    ("path", re.compile(r"\b[\w.-]*id_(?:rsa|ed25519)\b")),
    ("path", re.compile(r"\b(?:feature|feat|fix|hotfix|bugfix|release|chore)-[\w.-]+\b", re.I)),
    ("host", re.compile(r"(?<![\w@<./-])(?:[A-Za-z0-9-]+\.)+([A-Za-z]{2,63})(?::(\d{1,5}))?(?![\w/-])")),
    ("ipv4", re.compile(r"(?<![\w.])" + IPV4 + r"(?::\d{1,5})?(?![\w.])")),
    ("ipv6", re.compile(r"(?<![\w:])(?:[0-9a-fA-F]*:){2,}[0-9a-fA-F:.]*(?:%[\w.-]+)?(?![\w:])")),
    ("phone", re.compile(r"(?<!\w)\+\d{1,3}[ .-]*\(?\d{2,4}\)?(?:[ .-]+\d{2,4}){2,3}(?!\w)")),
    ("hash", re.compile(r"[0-9a-fA-F]{20,}")),
    ("number", re.compile(r"\d{7,}")),
)
CODE_LANGUAGES = frozenset((
    "bash sh zsh shell shellscript console terminal powershell ps1 cmd bat python py python3 javascript js typescript ts tsx jsx "
    "css scss sass less html xml svg json jsonc jsonl yaml yml toml ini conf config sql diff patch env dotenv go golang rust rs "
    "ruby rb php java kotlin kt scala c h cpp c++ csharp cs swift objective-c objc dart lua perl r julia elixir erlang haskell "
    "dockerfile docker make makefile cmake terraform tf hcl nginx graphql vue svelte asm assembly text/x-python application/json"
).split())
CODE_LINE = re.compile(r"^\s*\d+\t|^\s*(?:export\s+)?[A-Za-z_][\w.]*\s*=\s*\S|[;{}]\s*$|=>|^\s*[\w.]+\(\s*['\"]")


class CollectionError(Exception):
    """Diagnostics contain fixed structure descriptions, never log values."""


def hashed(salt, value, length=16):
    return hashlib.sha256((salt + "\n" + value).encode("utf-8")).hexdigest()[:length]


def public_tool_name(salt, name):
    """MCP tool names carry a user-chosen server label (often a customer or system name); hash that segment."""
    if isinstance(name, str) and name.startswith("mcp__"):
        parts = name.split("__")
        if len(parts) >= 3 and parts[1]:
            return "mcp__h" + hashed(salt, parts[1], 12) + "__" + "__".join(parts[2:])
    return name


def timestamp(value):
    if not isinstance(value, str):
        raise CollectionError("shape: timestamp must be an ISO string")
    try:
        match = re.fullmatch(r"(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2}:\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})", value)
        if match is None:
            raise ValueError
        date, time, fraction, zone = match.groups()
        fraction = "." + (fraction + "000000")[:6] if fraction else ""
        parsed = dt.datetime.fromisoformat(date + "T" + time + fraction + ("+00:00" if zone == "Z" else zone))
        if parsed.tzinfo is None:
            raise ValueError
        return parsed.astimezone(UTC)
    except ValueError:
        raise CollectionError("shape: timestamp must include a valid timezone") from None


def iso(value):
    return value.isoformat().replace("+00:00", "Z")


def sensitive_match(label, match):
    if label == "relative_path":
        return not all(p.isdigit() for p in match[0].split('/'))
    if label == "host":
        return match[1].lower() in TLDS or match[2] is not None
    if label == "ipv6":
        address = match[0].rstrip('.')
        if '::' not in address and len(address.split(':')) < 4:
            return False
        try:
            ipaddress.IPv6Address(address.split('%', 1)[0])
        except ValueError:
            return False
    return True


# Check unbounded prefixes once per maximal run, not again at every word boundary.
MASK_RUNS = {
    0: (re.compile(r"[a-z0-9+.-]+", re.I), re.compile(r"\b[a-z]", re.I)),
    1: (re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+|@"), None),
    3: (re.compile(r"[\w.+-]+"), None),
    6: (re.compile(r"[\w.-]+(?:[/\\][\w.-]+)*"), re.compile(r"\b(?=[\w.-])")),
    7: (re.compile(r"[\w-]+"), re.compile(r"\b(?=[\w-])")),
    9: (re.compile(r"[\w.-]+"), re.compile(r"(?<![\w<])(?=[\w.-])")),
    10: (re.compile(r"[\w.-]+"), re.compile(r"\b(?=[\w.-])")),
}


def mask_runs(text, pattern, runs, boundary, replace):
    pieces, consumed = [], 0
    for run in runs.finditer(text):
        if run.end() <= consumed:
            continue
        start = max(run.start(), consumed)
        if boundary:
            boundary_match = boundary.search(text, start, run.end())
            if boundary_match is None:
                continue
            start = boundary_match.start()
        match = pattern.match(text, start)
        if match:
            pieces.extend((text[consumed:match.start()], replace(match)))
            consumed = match.end()
    pieces.append(text[consumed:])
    return "".join(pieces)


def expand_secret_tokens(text):
    pieces, consumed = [], 0
    for match in re.finditer(r"<secret>[^\s<>\"'`]*", text):
        start = match.start()
        while start > consumed and not text[start - 1].isspace() and text[start - 1] not in "<>\"'`":
            start -= 1
        pieces.extend((text[consumed:start], "<secret>"))
        consumed = match.end()
    pieces.append(text[consumed:])
    return "".join(pieces)


def mask_rules(text):
    for index, (label, pattern) in enumerate(LEAKS):
        marker = {"relative_path": "path", "host": "url", "ipv4": "url", "ipv6": "url",
                  "number": "num", "phone": "num"}.get(label, label)
        def replace(match):
            return "<" + marker + ">" if sensitive_match(label, match) else match[0]
        if index == 2:
            def dotted_email(match):
                token = match[0]
                at, dot = token.find("@"), token.rfind(".", 0, len(token) - 1)
                return "<email>" if at >= 0 and dot > at + 1 else token
            text = re.sub(r"\S+", dotted_email, text)
        elif index == 4:
            text = re.sub(r"\S+", lambda m: "<path>" if re.search(r"[A-Za-z]:\\", m[0]) else m[0], text)
        elif index in MASK_RUNS:
            text = mask_runs(text, pattern, *MASK_RUNS[index], replace)
        else:
            text = pattern.sub(replace, text)
    return expand_secret_tokens(text)


def mask(text):
    text = expand_secret_tokens(text)
    while True:
        # Replacements and clipping can expose earlier rules (foo.hx -> foo.h).
        cleaned = mask_rules(text)[:240]
        if cleaned == text:
            return cleaned
        text = cleaned


def mask_secrets(value, diagnostics):
    if isinstance(value, str):
        cleaned, hits = SECRET.subn("<secret>", value)
        diagnostics["masked_secrets"] += hits
        return cleaned
    if isinstance(value, list):
        return [mask_secrets(item, diagnostics) for item in value]
    if isinstance(value, dict):
        cleaned = {mask_secrets(key, diagnostics): mask_secrets(item, diagnostics) for key, item in value.items()}
        if "last_tool" in cleaned and isinstance(cleaned["last_tool"], str) and not TOOL_NAME.fullmatch(cleaned["last_tool"]):
            cleaned["last_tool"] = ""
        return cleaned
    return value


def negated_candidate(sentence):
    for _, pattern in FILTER_KINDS:
        for match in re.finditer(pattern, sentence, re.I):
            if match[0].lower().startswith("un"):
                return True
            tokens = re.findall(r"[\w]+(?:['’][\w]+)?", sentence[:match.start()].lower())[-6:]
            prefix = " ".join(tokens).replace("’", "'")
            if re.search(r"\b(?:not|never|before|pending|will|would)\b|n't\b|"
                         r"\b(?:still untracked|if you want|tell me if|should i|once you)\b", prefix):
                return True
    return False


def candidates(text, salt, session, message, no_sentences, diagnostics=None):
    found = []
    dropped = 0
    offsets, code_lines = [], []
    offset, fence, language = 0, "", ""
    for line in text.splitlines(keepends=True):
        offsets.append(offset)
        offset += len(line)
        marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        code_lines.append(bool(marker or language in CODE_LANGUAGES or CODE_LINE.search(line)))
        if marker:
            if not fence:
                fence = marker[1]
                language = marker[2].strip().lower().split(maxsplit=1)[0] if marker[2].strip() else ""
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence, language = "", ""
    offset = 0
    for index, boundary in enumerate(list(re.finditer(r"(?<=[.!?])\s+|[\r\n]+", text)) + [None]):
        sentence = text[offset:boundary.start() if boundary else len(text)]
        line_index = bisect.bisect_right(offsets, offset + len(sentence) - len(sentence.lstrip())) - 1
        offset = boundary.end() if boundary else len(text)
        # Keep original segment indices so removing code does not renumber claim ids.
        if sentence.strip() and (code_lines[line_index] or CODE_LINE.search(sentence)):
            if diagnostics is not None:
                diagnostics["dropped_code_segments"] += 1
            continue
        sentence = sentence.strip()
        if negated_candidate(sentence):
            dropped += 1
            continue
        kinds = [kind for kind, pattern in KINDS if re.search(pattern, sentence, re.I)]
        if kinds:
            found.append({"claim_id": hashed(salt, session + message + str(index)),
                          "kind": kinds[0], "sentence": kinds[0] if no_sentences else sentence,
                          "_targeted": [kind for kind in kinds if kind in ("pushed", "committed", "tests_pass")],
                          "_no_sentence": no_sentences})
    return found, dropped


def text_content(content):
    # Read only text parts; never traverse images, thinking, or embedded files.
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p["text"] for p in content if isinstance(p, dict)
                         and p.get("type") in ("text", "input_text", "output_text")
                         and isinstance(p.get("text"), str))
    if content is None:
        return ""
    raise CollectionError("shape: text content must be a string or list")


def output_prefix(content, limit=300):
    if isinstance(content, str):
        return content[:limit]
    if isinstance(content, list):
        parts = []
        remaining = limit
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"][:remaining])
                if remaining is not None:
                    remaining -= len(parts[-1]) + 1
                    if remaining <= 0:
                        break
        return "\n".join(parts)[:limit]
    if isinstance(content, dict):
        # Structured shell results also occur in synthetic/integrator logs.
        return json.dumps(content, separators=(",", ":"))[:limit]
    if content is None:
        return ""
    raise CollectionError("shape: tool output must be text, list, or object")


def check_ok(content, agent, is_error=False, code_mode=False):
    if code_mode:
        text = output_prefix(content, None)
        if text.startswith("Script failed"):
            return False
        markers = r'(?:exit_code"\s*:|(?i:exit code):?|exitCode"?\s*:|Process exited with code)\s*(-?[0-9]+)'
        if any(m[1].lstrip("-0") for m in re.finditer(markers, text)):
            return False
        return None if text.startswith("Script running") else True
    prefix = output_prefix(content).lower()
    if re.search(r"exit code:\s*[1-9]", prefix):
        return False
    if agent == "claude-code":
        return not is_error
    return not (re.search(r'exit_code"\s*:\s*[1-9]', prefix) or prefix.lstrip().startswith("error"))


DYNAMIC = "__DYN__"
JS_WORD = re.compile(r"[A-Za-z_$][\w$]*")
JS_REGEX = re.compile(r"/(?:\\[^\r\n]|\[(?:\\[^\r\n]|[^\]\\\r\n])*\]|[^/\\[\r\n])*/[a-z]*")


def js_token(source, index, depth=0, regex_allowed=True):
    """Read static JS tokens only; expressions are never evaluated."""
    if depth > 32:
        return "unknown", "", len(source)
    while index < len(source):
        if source[index].isspace():
            index += 1
        elif source.startswith("//", index):
            end = source.find("\n", index + 2)
            index = len(source) if end < 0 else end + 1
        elif source.startswith("/*", index):
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
        else:
            break
    if index == len(source):
        return "end", "", index
    char = source[index]
    if char == "/" and regex_allowed:
        regex = JS_REGEX.match(source, index)
        if regex:
            return "regex", "", regex.end()
    if char not in "\"'`":
        word = JS_WORD.match(source, index)
        return ("word", word[0], index + len(word[0])) if word else ("punct", char, index + 1)
    quote, index, value = char, index + 1, []
    while index < len(source):
        char = source[index]
        index += 1
        if char == quote:
            return "string", "".join(value), index
        if char == "\\":
            if index == len(source):
                break
            escaped = source[index]
            index += 1
            if escaped in "xu":
                digits = 2 if escaped == "x" else 4
                end = index + digits
                if escaped == "u" and source[index:index + 1] == "{":
                    index += 1
                    end = source.find("}", index)
                code = source[index:end]
                if not code or not re.fullmatch(r"[0-9a-fA-F]+", code):
                    break
                try:
                    value.append(chr(int(code, 16)))
                except ValueError:
                    break
                index = end + (1 if source[end:end + 1] == "}" else 0)
            elif escaped in "\r\n":
                if escaped == "\r" and source[index:index + 1] == "\n":
                    index += 1
            else:
                value.append({"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f", "v": "\v", "0": "\0"}.get(escaped, escaped))
        elif quote == "`" and char == "$" and source[index:index + 1] == "{":
            index += 1
            braces = 1
            previous = ("punct", "{")
            while index < len(source) and braces:
                kind, token, index = js_token(source, index, depth + 1, js_regex_allowed(previous))
                previous = (kind, token)
                if kind == "punct":
                    braces += (token == "{") - (token == "}")
                if kind in ("unknown", "end"):
                    break
            if braces:
                break
            value.append(DYNAMIC)
        else:
            value.append(char)
    return "unknown", "", len(source)


def js_regex_allowed(previous):
    return (previous[0] == "punct" and previous[1] in "=([{,:;!&|?" or
            previous in (("word", "return"), ("word", "throw"), ("word", "case")))


def code_commands(source):
    tokens, index = [], 0
    while index < len(source):
        kind, value, index = js_token(source, index, regex_allowed=not tokens or js_regex_allowed(tokens[-1]))
        tokens.append((kind, value))
    commands, edit = [], False
    for index in range(len(tokens) - 4):
        if tokens[index:index + 2] != [("word", "tools"), ("punct", ".")] or tokens[index + 3] != ("punct", "("):
            continue
        tool = tokens[index + 2]
        if tool == ("word", "apply_patch"):
            edit = True
        if tool not in (("word", "exec_command"), ("word", "shell")) or tokens[index + 4] != ("punct", "{"):
            continue
        # Split only the outer object's properties; nested options are not commands.
        properties, current, stack = [], [], []
        for token in tokens[index + 5:]:
            if not stack and token in (("punct", ","), ("punct", "}")):
                properties.append(current)
                current = []
                if token[1] == "}":
                    break
                continue
            current.append(token)
            if token[0] == "punct":
                if token[1] in "{([":
                    stack.append(token[1])
                elif token[1] in "})]":
                    if not stack or stack.pop() != {"}": "{", ")": "(", "]": "["}[token[1]]:
                        break
        else:
            continue
        command = None
        for prop in properties:
            if prop[:1] == [("punct", ".")] or prop[:1] == [("punct", "[")]:
                command = None  # A spread/computed key may override the command.
                break
            if not prop or prop[0] not in (("word", "cmd"), ("string", "cmd"), ("word", "command"), ("string", "command")):
                continue
            command = None
            if prop[1:2] != [("punct", ":")]:
                continue
            value = prop[2:]
            if len(value) == 1 and value[0][0] == "string":
                command = value[0][1]
            elif value[:1] == [("punct", "[")] and value[-1:] == [("punct", "]")]:
                items = value[1:-1]
                if items and all(t[0] == "string" if i % 2 == 0 else t == ("punct", ",") for i, t in enumerate(items)):
                    command = shlex.join(t[1] for t in items[::2])
        if command is not None:
            commands.append(command)
    return commands, edit


def command_families(command, depth=0):
    """Recognize shell command segments without executing or retaining them."""
    if depth > 3:
        return []
    try:
        lex = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
        lex.whitespace = " \t\r"
        lex.whitespace_split = True
        lex.commenters = "#"
        segments = [[]]
        for token in lex:
            if token and all(c in ";&|()\n" for c in token):
                segments.append([])
            else:
                segments[-1].append(token)
    except ValueError:
        return []
    families = []
    for words in segments:
        if words and DYNAMIC in words[0]:
            continue
        while words and (re.match(r"^[A-Za-z_]\w*=", words[0]) or words[0] in ("env", "command", "sudo")):
            words.pop(0)
        if not words or DYNAMIC in words[0]:
            continue
        words[0] = words[0].rsplit("/", 1)[-1]
        head = words[0]
        if head in ("bash", "sh", "zsh") and len(words) >= 3 and "c" in words[1]:
            families.extend(command_families(words[2], depth + 1))
            continue
        rest = words[1:]
        if head == "git":
            while rest and rest[0].startswith("-"):
                rest = rest[2:] if rest[0] in ("-C", "-c", "--git-dir", "--work-tree") else rest[1:]
            if rest and rest[0] in ("push", "commit"):
                families.append(("git", rest[0]))
            continue
        joined = " ".join(words)
        if (head in ("pytest", "jest", "vitest", "rspec", "phpunit")
            or re.match(r"^python(?:\d+(?:\.\d+)*)? -m (?:pytest|unittest)\b", joined)
            or (head in ("npm", "pnpm", "yarn", "go", "cargo", "make", "mvn", "gradle", "dotnet") and rest[:1] == ["test"])
            or (head in ("npm", "pnpm", "yarn") and rest[:2] == ["run", "test"])):
            families.append(("test", None))
        elif (head == "make" or (head in ("pnpm", "cargo", "go", "docker", "vite", "next") and rest[:1] == ["build"])
              or head == "npm" and rest[:2] == ["run", "build"]):
            families.append(("build", None))
        elif head in ("eslint", "ruff", "flake8", "golangci-lint", "clippy") or head == "cargo" and rest[:1] == ["clippy"]:
            families.append(("lint", None))
        elif head in ("tsc", "mypy", "pyright"):
            families.append(("typecheck", None))
    return families


def tool_projection(name, arguments, agent):
    if not isinstance(name, str):
        raise CollectionError("shape: tool name must be a string")
    if agent == "codex" and name == "exec":
        commands, edit = code_commands(arguments) if isinstance(arguments, str) else ([], False)
        return {"name": name, "edit": edit or any(re.search(r"\bapply_patch\b", cmd) for cmd in commands),
                "families": [family for cmd in commands for family in command_families(cmd)]}
    base = name.rsplit(".", 1)[-1]
    shell = base in ("Bash", "shell", "exec_command", "local_shell", "local_shell_call") or name == "container.exec"
    command = ""
    if shell:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                # A direct shell input is a supported custom-tool form.
                command = arguments
        if isinstance(arguments, dict):
            command = arguments.get("command", arguments.get("cmd", ""))
        if isinstance(command, list) and all(isinstance(w, str) for w in command):
            command = shlex.join(command)
        if not isinstance(command, str):
            raise CollectionError("shape: shell command must be text or an argv list")
    edit = (name in ("Edit", "Write", "MultiEdit", "NotebookEdit") if agent == "claude-code"
            else base == "apply_patch" or bool(shell and re.search(r"\bapply_patch\b", command)))
    return {"name": name, "edit": edit, "families": command_families(command) if shell else []}


def usage_projection(raw, codex=False):
    if not isinstance(raw, dict):
        raise CollectionError("shape: usage must be an object")
    def count(key):
        value = raw.get(key, 0)
        if type(value) is not int or value < 0:
            raise CollectionError("shape: usage counter must be a nonnegative integer")
        return value
    cached = count("cached_input_tokens" if codex else "cache_read_input_tokens")
    written = count("cache_write_input_tokens" if codex else "cache_creation_input_tokens")
    incoming = count("input_tokens")
    # Codex's input counter includes cached tokens; keep the buckets disjoint.
    return dict(zip(USAGE, (max(0, incoming - cached - written) if codex else incoming,
                            cached, written, count("output_tokens"))))


def log_files(root, diagnostics):
    root = Path(root).expanduser().resolve()
    if not root.exists():
        diagnostics["missing_directories"] += 1
        return []
    def walk_error(_):
        raise CollectionError("read: cannot enumerate log directory")
    result = []
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        kept = []
        for name in sorted(dirs):
            if (Path(parent) / name).is_symlink():
                diagnostics["skipped_symlinks"] += 1
            else:
                kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            path = Path(parent) / name
            if not name.endswith(".jsonl"):
                continue
            if path.is_symlink():
                diagnostics["skipped_symlinks"] += 1
                continue
            if path.is_file():
                result.append((root, path))
    return result


def is_codex_context(text):
    text = text.lstrip()
    return text.startswith("# AGENTS.md instructions") or re.match(
        r"<(?:environment_context|user_instructions|permissions|permissions_instructions|recommended_plugins|"
        r"skills_instructions|developer_instructions|system_instructions|collaboration_mode|multi_agent_role|"
        r"multi_agent_mode|app_context|environment_details)(?:\s|>)", text) is not None


def read_events(root, path, agent, salt, no_sentences, diagnostics, repo_cwds=None):
    events = []
    relative = path.relative_to(root)
    session_raw = path.stem
    parent_session = None
    # A Claude sidechain directory is rooted under its parent session id.
    if agent == "claude-code" and "subagents" in relative.parts:
        position = relative.parts.index("subagents")
        if position:
            parent_session = session_raw = relative.parts[position - 1]
    clock = None
    project = None
    empty_project = hashed(salt, "")
    branch = None
    file_id = hashed(salt, str(relative))
    codex_meta_seen = False
    exec_calls = set()
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            for number, line in enumerate(stream, 1):
                try:
                    record = json.loads(line)
                except (ValueError, UnicodeError, RecursionError):
                    diagnostics["skipped_unparseable_lines"] += 1
                    continue
                if not isinstance(record, dict):
                    raise CollectionError("shape: log record must be an object")
                kind = record.get("type")
                if agent == "claude-code":
                    if kind not in ("user", "assistant", "system", "summary", "attachment"):
                        continue
                    if record.get("sessionId") is not None:
                        if not isinstance(record["sessionId"], str):
                            raise CollectionError("shape: sessionId must be a string")
                        session_raw = record["sessionId"]
                    if parent_session and record.get("isSidechain") is True:
                        session_raw = parent_session
                    pl = record.get("message", {})
                else:
                    if kind not in ("session_meta", "turn_context", "compacted", "event_msg", "response_item"):
                        continue
                    pl = record.get("payload")
                    if not isinstance(pl, dict):
                        raise CollectionError("shape: Codex payload must be an object")
                    if kind == "session_meta":
                        if codex_meta_seen:
                            continue
                        codex_meta_seen = True
                        session_raw = pl.get("id", pl.get("session_id", session_raw))
                        if not isinstance(session_raw, str):
                            raise CollectionError("shape: session id must be a string")
                time_value = record.get("timestamp")
                if not time_value and kind == "session_meta":
                    time_value = pl.get("timestamp")
                if time_value:
                    clock = timestamp(time_value)
                elif clock is None:
                    # Summary records may have only a leaf uuid; anchor after parsing.
                    if kind != "summary":
                        raise CollectionError("shape: first relevant record has no timestamp")
                meta = record if agent == "claude-code" else pl if kind == "session_meta" else {}
                if "cwd" in meta:
                    if not isinstance(meta["cwd"], str):
                        raise CollectionError("shape: cwd must be a string")
                    project = hashed(salt, meta["cwd"])
                    if repo_cwds is not None and not record.get("isSidechain"):
                        repo_cwds.setdefault((agent, hashed(salt, session_raw)), set()).add(meta["cwd"])
                raw_branch = meta.get("gitBranch") if agent == "claude-code" else (meta.get("git") or {}).get("branch")
                if raw_branch is not None:
                    if not isinstance(raw_branch, str):
                        raise CollectionError("shape: branch must be a string")
                    branch = hashed(salt, raw_branch)
                if pl is None and kind not in ("user", "assistant"):
                    pl = {}
                if not isinstance(pl, dict):
                    raise CollectionError("shape: message or payload must be an object")
                explicit_id = record.get("uuid") or pl.get("id")
                message_id = explicit_id or file_id + ":" + str(number)
                if not isinstance(message_id, str):
                    raise CollectionError("shape: message id must be a string")
                common = {"session_id": hashed(salt, session_raw), "agent": agent, "project": project,
                          "empty_project": empty_project,
                          "branch": branch, "ts": clock, "order": (file_id, number), "type": "meta",
                          "record_id": hashed(salt, kind + ":" + explicit_id) if explicit_id else None}
                def emit(event_type, **values):
                    if event_type == "assistant":
                        values["claims"], values["dropped"] = values["claims"]
                        for claim in values["claims"]:
                            claim["sentence"] = mask(mask_secrets(claim["sentence"], diagnostics))
                    events.append(dict(common, type=event_type, **values))
                emit("meta")
                sidechain = record.get("isSidechain") is True
                if kind in ("summary", "compacted") or kind == "system" and record.get("subtype") == "compact_boundary":
                    emit("compaction")
                if agent == "claude-code" and kind in ("user", "assistant"):
                    if not isinstance(pl, dict):
                        raise CollectionError("shape: Claude message must be an object")
                    content = pl.get("content")
                    parts = content if isinstance(content, list) else []
                    if kind == "user" and not sidechain and not any(isinstance(p, dict) and p.get("type") == "tool_result" for p in parts):
                        text = text_content(content).lstrip()
                        pseudo = any(record.get(flag) is True for flag in ("isMeta", "isCompactSummary", "isVisibleInTranscriptOnly"))
                        pseudo |= text.startswith(("<local-command-stdout>", "<local-command-stderr>", "<local-command-caveat>",
                                                   "<bash-input>", "<bash-stdout>", "<bash-stderr>", "[Request interrupted by user"))
                        if not pseudo:
                            emit("user", source="native", command=text.startswith(("<command-name>", "<command-message>")))
                    if kind == "assistant":
                        text = "" if sidechain else text_content(content)
                        if text.strip():
                            emit("assistant", source="native", claims=candidates(text, salt, session_raw, message_id, no_sentences, diagnostics))
                        if pl.get("usage") is not None:
                            emit("usage", usage=usage_projection(pl["usage"]), cumulative=False,
                                 usage_id=hashed(salt, str(pl.get("id") or message_id)))
                    for part in parts:
                        if not isinstance(part, dict):
                            raise CollectionError("shape: content part must be an object")
                        if part.get("type") == "tool_use":
                            emit("call", call_id=hashed(salt, str(part.get("id") or message_id)),
                                 **tool_projection(public_tool_name(salt, part.get("name")), part.get("input"), agent))
                        elif part.get("type") == "tool_result":
                            emit("result", call_id=hashed(salt, str(part.get("tool_use_id", ""))),
                                 ok=check_ok(part.get("content"), agent, part.get("is_error", False)))
                elif agent == "codex":
                    pk = pl.get("type")
                    if kind == "event_msg" and pk in ("user_message", "agent_message"):
                        if pk == "user_message":
                            emit("user", source="event")
                        else:
                            text = text_content(pl.get("message"))
                            if text.strip():
                                emit("assistant", source="event", claims=candidates(text, salt, session_raw, message_id, no_sentences, diagnostics))
                    elif kind == "event_msg" and pk == "token_count" and pl.get("info") is not None:
                        info = pl["info"]
                        if not isinstance(info, dict):
                            raise CollectionError("shape: token_count info must be an object or null")
                        raw = info.get("total_token_usage", info.get("last_token_usage"))
                        if raw is not None:
                            emit("usage", usage=usage_projection(raw, True), cumulative="total_token_usage" in info,
                                 usage_id=hashed(salt, session_raw + "\n" + file_id))
                    elif kind == "response_item":
                        if pk == "message" and pl.get("role") in ("user", "assistant"):
                            if pl["role"] == "user":
                                content = pl.get("content")
                                parts = [content] if isinstance(content, str) else [
                                    p["text"] for p in content or [] if isinstance(p, dict)
                                    and p.get("type") == "input_text" and isinstance(p.get("text"), str)]
                                if any(text.strip() and not is_codex_context(text) for text in parts):
                                    emit("user", source="response")
                            else:
                                text = text_content(pl.get("content"))
                                if text.strip():
                                    emit("assistant", source="response", claims=candidates(text, salt, session_raw, message_id, no_sentences, diagnostics))
                        elif pk in ("function_call", "custom_tool_call", "local_shell_call"):
                            arguments = pl.get("arguments", pl.get("input", pl.get("action", {})))
                            call_id = hashed(salt, str(pl.get("call_id") or pl.get("id") or message_id))
                            if pl.get("name") == "exec":
                                exec_calls.add(call_id)
                            emit("call", call_id=call_id,
                                 **tool_projection(public_tool_name(salt, pl.get("name", "local_shell_call" if pk == "local_shell_call" else "")), arguments, agent))
                        elif pk in ("function_call_output", "custom_tool_call_output"):
                            call_id = hashed(salt, str(pl.get("call_id") or pl.get("id") or ""))
                            emit("result", call_id=call_id,
                                 ok=check_ok(pl.get("output"), agent, code_mode=call_id in exec_calls))
    except OSError:
        raise CollectionError("read: cannot open or read a log file") from None
    times = [e["ts"] for e in events if e["ts"] is not None]
    for event in events:
        if event["ts"] is None:
            if not times:
                raise CollectionError("shape: summary has no timestamp context")
            event["ts"] = min(times)
    return events


def claim_status(kind, seen_push, seen_commit, seen_test, check, last_edit, edits_after, turn_edits, turn_checks):
    if kind == "pushed" and not seen_push:
        return "contradicted", "claimed_push_no_push_cmd"
    if kind == "committed" and not seen_commit:
        return "contradicted", "claimed_commit_no_commit_cmd"
    if kind == "tests_pass" and not seen_test:
        return "contradicted", "no_check_in_session"
    if check is not None and edits_after == 0:
        return ("confirmed", "check_ok_after_edit") if check["ok"] is True else ("contradicted", "check_failed_after_edit")
    if check is not None and edits_after:
        return "contradicted", "edits_after_last_check"
    if not turn_edits and not turn_checks:
        return "unverified", "no_edit_no_check"
    return "unverified", "other"


def summarize_session(events, start, end):
    events.sort(key=lambda e: (e["ts"], e["order"]))
    first_copy = {}
    unique = []
    for event in events:
        identity = event["record_id"]
        if identity is not None:
            first_copy.setdefault(identity, event["order"])
            if first_copy[identity] != event["order"]:
                continue
        unique.append(event)
    events = unique
    selected = [e for e in events if start <= e["ts"] <= end]
    if not selected:
        return None
    first = selected[0]
    session = {k: first[k] for k in ("session_id", "agent", "project", "branch")}
    for key in ("project", "branch"):
        session[key] = next((e[key] for e in selected if e[key] is not None),
                            next((e[key] for e in events if e["ts"] < start and e[key] is not None),
                                 None))
    if session["project"] is None:
        session["project"] = first["empty_project"]
    session.update(started=iso(first["ts"]), ended=iso(selected[-1]["ts"]), turns=0,
                   claims=[], stalls=[], usage=dict.fromkeys(USAGE, 0), ended_how="no_final_message",
                   empty_turns=0, candidates_dropped_negated=0)
    session.update(dict.fromkeys(COUNTERS, 0))
    preferred_user = "event" if any(e["type"] == "user" and e.get("source") == "event" for e in events) else "response"
    preferred_assistant = "response" if any(e["type"] == "assistant" and e.get("source") == "response" for e in events) else "event"
    calls = {}
    last_edit = None
    last_check = None
    edits_after = 0
    seen_push = seen_commit = seen_test = False
    turn = None
    snapshots = {}
    usage_seen = False
    seen_events = set()

    def usage_delta(event):
        raw = event["usage"]
        key = event["usage_id"]
        previous = snapshots.get(key, dict.fromkeys(USAGE, 0))
        if event["cumulative"]:
            # Small corrections keep the high-water marks; only a large drop resets.
            reset = 2 * sum(raw.values()) < sum(previous.values())
            delta = {k: raw[k] if reset else max(0, raw[k] - previous[k]) for k in USAGE}
            snapshots[key] = dict(raw) if reset else {k: max(raw[k], previous[k]) for k in USAGE}
        elif event["agent"] == "claude-code":
            delta = {k: max(0, raw[k] - previous[k]) for k in USAGE}
            snapshots[key] = {k: max(raw[k], previous[k]) for k in USAGE}
        else:
            delta = raw
        return delta

    def evidence(event):
        nonlocal last_edit, last_check, edits_after, seen_push, seen_commit, seen_test
        if event["type"] == "call":
            if event["edit"]:
                last_edit = event["ts"]
                if last_check is not None:
                    edits_after += 1
            checks = event["families"]
            if checks:
                seen_push |= any(action == "push" for _, action in checks)
                seen_commit |= any(action == "commit" for _, action in checks)
                seen_test |= any(family == "test" for family, _ in checks)
                last_check = {"ts": event["ts"], "family": checks[-1][0], "ok": None}
                calls[event["call_id"]] = last_check
                edits_after = 0
        elif event["type"] == "result" and event["call_id"] in calls:
            calls[event["call_id"]]["ok"] = event["ok"]

    # Seed evidence and usage without changing selected counts, turns or dedup ids.
    pre_seen = set()
    for event in events:
        if event["ts"] < start:
            if event["type"] == "usage":
                usage_delta(event)
            elif event["type"] in ("call", "result"):
                key = (event["type"], event["call_id"])
                if key not in pre_seen:
                    pre_seen.add(key)
                    evidence(event)

    def finish():
        if turn is None:
            return
        if turn["command"] and not turn["calls"] and not turn["text"]:
            session["turns"] -= 1
            return
        if turn["text"]:
            session["claims"].extend(turn["claims"])
            session["candidates_dropped_negated"] += turn["dropped"]
            session["ended_how"] = "final_message"
        if turn["directive"] and (not turn["text"] or turn["terminal_error"]):
            reason = "error_then_silence" if turn["terminal_error"] else "no_final_message"
            if turn["calls"]:
                session["stalls"].append({"ts": iso(turn["ts"]), "reason": reason,
                                          "last_tool": turn["last_tool"], "tool_errors_in_last_turn": turn["errors"]})
            else:
                session["empty_turns"] += 1
            session["ended_how"] = reason if turn["calls"] else "no_final_message"

    for event in selected:
        typ = event["type"]
        if typ in ("user", "assistant") and event["source"] != "native":
            if event["source"] != (preferred_user if typ == "user" else preferred_assistant):
                continue
        # Duplicate tool ids are replayed on resume; count their activity once.
        if typ in ("call", "result"):
            key = (typ, event["call_id"])
            if key in seen_events:
                continue
            seen_events.add(key)
            evidence(event)
        if typ == "user":
            finish()
            session["turns"] += 1
            turn = None
        if turn is None:
            turn = {"directive": typ == "user", "text": False, "claims": [], "last_tool": "",
                    "errors": 0, "terminal_error": False, "edits": 0, "checks": 0, "ts": event["ts"],
                    "calls": 0, "dropped": 0, "command": typ == "user" and event.get("command", False)}
        turn["ts"] = event["ts"]
        if typ == "call":
            session["tool_calls"] += 1
            turn["calls"] += 1
            turn["last_tool"] = event["name"]
            turn["terminal_error"] = False
            if event["edit"]:
                session["edits"] += 1
                turn["edits"] += 1
            checks = event["families"]
            if checks:
                session["checks"] += 1
                turn["checks"] += 1
        elif typ == "result":
            if event["ok"] is False:
                session["tool_errors"] += 1
                turn["errors"] += 1
                turn["terminal_error"] = True
        elif typ == "compaction":
            session["compactions"] += 1
        elif typ == "usage":
            usage_seen = True
            delta = usage_delta(event)
            for key in USAGE:
                session["usage"][key] += delta[key]
        elif typ == "assistant":
            turn["text"] = True
            turn["terminal_error"] = False
            turn["claims"] = []
            turn["dropped"] = event["dropped"]
            for candidate in event["claims"]:
                claim = dict(candidate, ts=iso(event["ts"]), last_edit_ts=iso(last_edit) if last_edit else None,
                             last_check_ts=iso(last_check["ts"]) if last_check else None,
                             last_check_family=last_check["family"] if last_check else "none",
                             last_check_ok=last_check["ok"] if last_check else None, edits_after_last_check=edits_after,
                             repo_check="not_checked")
                targeted = claim.pop("_targeted", [])
                for kind, seen in (("pushed", seen_push), ("committed", seen_commit), ("tests_pass", seen_test)):
                    if kind in targeted and not seen:
                        claim["kind"] = kind
                        break
                if claim.pop("_no_sentence", False):
                    claim["sentence"] = claim["kind"]
                claim["status"], claim["status_reason"] = claim_status(claim["kind"], seen_push, seen_commit, seen_test,
                    last_check, last_edit, edits_after, turn["edits"], turn["checks"])
                turn["claims"].append(claim)
    finish()
    session["claims"].sort(key=lambda c: (c["ts"], c["claim_id"]))
    return session, usage_seen


def git_read(cwd, *args):
    # Disable locks, inherited repository overrides and partial-clone fetching.
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    try:
        process = subprocess.run(["git", "--no-pager", "-c", "core.fsmonitor=false", "-C", cwd] + list(args),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                 timeout=10, env=environment)
    except (OSError, UnicodeError, subprocess.TimeoutExpired):
        return None
    return process.stdout if process.returncode == 0 else None


def historical_ref(cwd, ref, ended):
    history = git_read(cwd, "reflog", "show", "--date=iso-strict", "--format=%H%x09%gD", ref, "--")
    if history is None:
        return None
    for line in history.splitlines():
        match = re.fullmatch(r"([0-9a-f]{40}|[0-9a-f]{64})\t.+@\{([^}]+)\}", line)
        if match:
            try:
                if timestamp(match[2]) <= ended:
                    return match[1]
            except CollectionError:
                return None
    return None


def check_repository(session, cwds, salt):
    # A session that changed repositories has no single attributable cwd.
    if len(cwds) != 1:
        return
    cwd = next(iter(cwds))
    if not Path(cwd).is_absolute() or not Path(cwd).is_dir():
        return
    ended = timestamp(session["ended"])
    push_result = None
    commit_windows = {}
    for claim in session["claims"]:
        if claim["kind"] not in ("committed", "pushed"):
            continue
        since = iso(timestamp(claim["ts"]) - dt.timedelta(hours=1))
        if since not in commit_windows:
            commit_windows[since] = git_read(cwd, "log", "--since=" + since,
                "--until=" + iso(ended + dt.timedelta(hours=1)), "--format=%H", "--")
        commits = commit_windows[since]
        if commits is None:
            continue
        if claim["kind"] == "committed":
            claim["repo_check"] = "commit_found" if commits.strip() else "commit_absent"
        else:
            if push_result is None:
                push_result = "not_checked"
                branch = git_read(cwd, "symbolic-ref", "--quiet", "--short", "HEAD")
                if branch and hashed(salt, branch.strip()) == session["branch"]:
                    head = historical_ref(cwd, "HEAD", ended)
                    upstream = git_read(cwd, "rev-parse", "--symbolic-full-name", "@{u}")
                    if head and upstream and upstream.strip().startswith("refs/"):
                        upstream_head = historical_ref(cwd, upstream.strip(), ended)
                        if upstream_head:
                            ahead = git_read(cwd, "log", upstream_head + ".." + head, "--format=%H", "--")
                            if ahead is not None:
                                push_result = "push_absent" if ahead.strip() else "push_found"
            claim["repo_check"] = push_result
        if claim["repo_check"] != "not_checked" and claim["status"] == "contradicted":
            claim["status"] = "confirmed" if claim["repo_check"].endswith("_found") else "contradicted"
            claim["status_reason"] = "repo_" + claim["repo_check"]


def collect(claude_dir, codex_dir, salt, since=None, until=None, no_sentences=False, stamp=False, repo_check=False):
    diagnostics = dict.fromkeys(("skipped_unparseable_lines", "skipped_symlinks", "missing_directories", "sessions_without_usage", "masked_secrets", "dropped_code_segments"), 0)
    repo_cwds = {} if repo_check else None
    grouped = {}
    newest = None
    for agent, root in (("claude-code", claude_dir), ("codex", codex_dir)):
        for resolved, path in log_files(root, diagnostics):
            for event in read_events(resolved, path, agent, salt, no_sentences, diagnostics, repo_cwds):
                key = (agent, event["session_id"])
                grouped.setdefault(key, []).append(event)
                newest = max(newest, event["ts"]) if newest else event["ts"]
    newest = newest or dt.datetime(1970, 1, 1, tzinfo=UTC)
    start = dt.datetime.combine(since or (newest - dt.timedelta(days=30)).date(), dt.time(), UTC)
    end = dt.datetime.combine(until, dt.time.max, UTC) if until else newest
    if start > end:
        raise CollectionError("period: start is after end")
    sessions = []
    for events in grouped.values():
        result = summarize_session(events, start, end)
        if result is not None:
            session, usage_seen = result
            if repo_check:
                check_repository(session, repo_cwds.get((session["agent"], session["session_id"]), set()), salt)
            sessions.append(session)
            diagnostics["sessions_without_usage"] += not usage_seen
    sessions.sort(key=lambda s: (s["started"], s["session_id"]))
    totals = dict.fromkeys(("sessions", "claims", "stalls") + COUNTERS, 0)
    totals.update(by_status=dict.fromkeys(("confirmed", "contradicted", "unverified"), 0), usage=dict.fromkeys(USAGE, 0))
    by_month = {}
    for session in sessions:
        totals["sessions"] += 1
        totals["claims"] += len(session["claims"])
        totals["stalls"] += len(session["stalls"])
        for key in COUNTERS:
            totals[key] += session[key]
        for key in USAGE:
            totals["usage"][key] += session["usage"][key]
        for claim in session["claims"]:
            totals["by_status"][claim["status"]] += 1
        month = session["started"][:7]
        bucket = by_month.setdefault(month, dict(month=month, **dict.fromkeys(USAGE + ("sessions", "compactions"), 0)))
        bucket["sessions"] += 1
        bucket["compactions"] += session["compactions"]
        for key in USAGE:
            bucket[key] += session["usage"][key]
    totals["by_month"] = [by_month[month] for month in sorted(by_month)]
    export = {"schema": "nueton-receipts/export@1", "collector_version": VERSION,
              "salt_fingerprint": hashlib.sha256(salt.encode("utf-8")).hexdigest()[:8],
              "period": {"start": iso(start), "end": iso(end)}, "agents": sorted({s["agent"] for s in sessions}),
              "sessions": sessions, "totals": totals}
    if stamp:
        export["generated_at"] = iso(dt.datetime.now(UTC))
    return mask_secrets(export, diagnostics), diagnostics


def load_salt(path):
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except FileExistsError:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise CollectionError("salt: expected a regular file")
            if stat.S_IMODE(os.fstat(stream.fileno()).st_mode) != 0o600:
                raise CollectionError("salt: existing file must have mode 0600")
            salt = stream.read().strip()
            if not salt:
                raise CollectionError("salt: existing file is empty")
            return salt
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        salt = os.urandom(32).hex()
        stream.write(salt + "\n")
    return salt


def write_export(export, destination, diagnostics=None):
    export = mask_secrets(export, diagnostics if diagnostics is not None else {"masked_secrets": 0})
    path = Path(destination).expanduser()
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".receipts-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(export, stream, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def render_card(export):
    def row(label, value):
        if len(label) + len(value) >= 40:
            raise CollectionError("card: value does not fit 40 columns")
        return label + value.rjust(40 - len(label))

    totals = export["totals"]
    period = export["period"]
    agents = ", ".join(label for agent, label in (("claude-code", "claude code"), ("codex", "codex"))
                       if agent in export["agents"])
    lines = [row("RECEIPT", "receipts.nueton.ai"),
             row("period", period["start"][:10] + " .. " + period["end"][:10]),
             row("agents", agents), row("sessions", format(totals["sessions"], ",")),
             row('"done" candidates', format(totals["claims"], ",")), "-" * 40]
    lines.extend(row(status, format(totals["by_status"][status], ","))
                 for status in ("confirmed", "contradicted", "unverified"))
    lines.extend((row("silent stalls", format(totals["stalls"], ",")), "-" * 40))
    if totals["claims"]:
        lines.extend(("Counts are keyword matches. Read them", "before you quote them."))
    else:
        lines.extend(("No completion claims found in this", "window."))
    lines.append("Check yours, free: receipts.nueton.ai")
    return "".join(line.ljust(40) + "\n" for line in lines)


def write_card(card, destination, force=False):
    path = Path(destination).expanduser()
    temporary = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".receipts-card-", dir=str(path.parent))
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(card)
            os.fchmod(stream.fileno(), 0o644)
        if force:
            os.replace(temporary, path)
        else:
            # Linking the complete file refuses existing paths without a check/write race.
            os.link(temporary, path)
    except FileExistsError:
        raise CollectionError("card: output already exists; use --force-card to overwrite") from None
    except (OSError, UnicodeError):
        raise CollectionError("card: cannot write card output") from None
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def date_argument(value):
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return dt.date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude-dir", default="~/.claude/projects")
    parser.add_argument("--codex-dir", default="~/.codex/sessions")
    parser.add_argument("--since", type=date_argument, help="first UTC date; default newest record minus 30 days")
    parser.add_argument("--until", type=date_argument, help="last UTC date, inclusive; default newest record")
    parser.add_argument("--salt", help="hashing salt; otherwise read/create ~/.nueton-receipts/salt (0600)")
    parser.add_argument("--out", default="~/.nueton-receipts/export.json")
    parser.add_argument("--no-sentences", action="store_true", help="replace masked sentences with claim kinds")
    parser.add_argument("--stamp", action="store_true", help="include generated_at (disables byte determinism)")
    parser.add_argument("--summary", action="store_true", help="print counts only; never print sentences")
    parser.add_argument("--card", action="store_true", help="print a shareable 40-column counts-only card")
    parser.add_argument("--card-out", metavar="PATH", help="also save the card as UTF-8 text (0644); implies --card")
    parser.add_argument("--force-card", action="store_true", help="allow overwriting --card-out")
    parser.add_argument("--repo-check", action="store_true", help="inspect local Git history for commit/push claims (read-only)")
    args = parser.parse_args(argv)
    if args.force_card and not args.card_out:
        parser.error("--force-card requires --card-out")
    if args.salt is not None and not args.salt.strip():
        print("ERROR salt: --salt must not be empty", file=sys.stderr)
        return 1
    try:
        salt = args.salt if args.salt is not None else load_salt(Path.home() / ".nueton-receipts/salt")
    except (OSError, UnicodeError):
        print("ERROR salt: cannot read/create ~/.nueton-receipts/salt with mode 0600", file=sys.stderr)
        return 1
    except CollectionError as error:
        print("ERROR " + str(error), file=sys.stderr)
        return 1
    try:
        if args.card_out:
            card_path = Path(args.card_out).expanduser().resolve()
            export_path = Path(args.out).expanduser().resolve()
            if card_path == export_path or (card_path.exists() and export_path.exists() and card_path.samefile(export_path)):
                raise CollectionError("card: --card-out must differ from --out")
        export, diagnostics = collect(args.claude_dir, args.codex_dir, salt, args.since, args.until, args.no_sentences, args.stamp, args.repo_check)
        write_export(export, args.out, diagnostics)
        card = render_card(export) if args.card or args.card_out else None
        if args.card_out:
            write_card(card, args.card_out, args.force_card)
    except CollectionError as error:
        print("ERROR " + str(error), file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print("ERROR io: cannot read inputs, access salt, or write export", file=sys.stderr)
        return 1
    if args.summary:
        totals = export["totals"]
        print("sessions={sessions} claims={claims} confirmed={confirmed} contradicted={contradicted} unverified={unverified} stalls={stalls}".format(**totals, **totals["by_status"]),
              file=sys.stderr if card is not None else sys.stdout)
    if card is not None:
        print(card, end="")
    print(" ".join("{}={}".format(k, v) for k, v in sorted(diagnostics.items())), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
