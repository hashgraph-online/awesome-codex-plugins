#!/usr/bin/env bash
# Shared discovery sets, fingerprinting, ordering helpers, and the shared regex scanner.
#
# Every matcher in the registry is a JavaScript regular expression. The scanner below implements the
# subset those rules use (literals, classes, escapes, groups, alternation, greedy quantifiers,
# lookahead, anchors, and the i flag) as a backtracking VM in POSIX awk, so detection does not depend
# on a JavaScript runtime. Regexes are matched against the whole file, including newlines.
set -euo pipefail

RS_SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_SCRIPT_DIR/rule-registry.sh"

# rs_lower <value> lowercases ASCII.
rs_lower() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]'
}

# rs_is_supported_ext <.ext> succeeds for the detector's supported source extensions.
rs_is_supported_ext() {
  case "$(rs_lower "$1")" in
    .html|.jsx|.tsx|.vue|.svelte|.css|.scss|.less) return 0 ;;
  esac
  return 1
}

# rs_is_markup_ext <.ext> succeeds for markup extensions.
rs_is_markup_ext() {
  case "$(rs_lower "$1")" in
    .html|.jsx|.tsx|.vue|.svelte) return 0 ;;
  esac
  return 1
}

# rs_is_style_ext <.ext> succeeds for stylesheet extensions.
rs_is_style_ext() {
  case "$(rs_lower "$1")" in
    .css|.scss|.less) return 0 ;;
  esac
  return 1
}

# rs_is_ignored_dir <name> succeeds for directories the detector never descends into.
rs_is_ignored_dir() {
  case "$1" in
    .git|node_modules|dist|build|coverage|.next|.nuxt|.svelte-kit) return 0 ;;
  esac
  return 1
}

# rs_extname <path> prints the extension with its leading dot, or an empty string.
# Mirrors path.extname: a leading dot alone is not an extension.
rs_extname() {
  local base dot
  base=${1##*/}
  case "$base" in
    ''|.*) case "$base" in
        .?*) dot=${base#*.}; case "$base" in ..*) printf ''; return 0 ;; esac
             printf '.%s' "$dot" ;;
        *) printf '' ;;
      esac ;;
    *.*) printf '.%s' "${base##*.}" ;;
    *) printf '' ;;
  esac
}

# rs_resolve <path> prints a lexically normalized absolute path, like path.resolve.
rs_resolve() {
  case "$1" in
    /*) printf '%s' "$1" | LC_ALL=C awk -F/ '{ n = 0; for (i = 1; i <= NF; i++) {
          if ($i == "" || $i == ".") continue
          else if ($i == "..") { if (n > 0) n-- }
          else stack[++n] = $i }
        out = ""; for (i = 1; i <= n; i++) out = out "/" stack[i]
        if (out == "") out = "/"
        print out }' ;;
    *) printf '%s/%s' "$PWD" "$1" | LC_ALL=C awk -F/ '{ n = 0; for (i = 1; i <= NF; i++) {
          if ($i == "" || $i == ".") continue
          else if ($i == "..") { if (n > 0) n-- }
          else stack[++n] = $i }
        out = ""; for (i = 1; i <= n; i++) out = out "/" stack[i]
        if (out == "") out = "/"
        print out }' ;;
  esac
}

# rs_basename <path> / rs_dirname <path> mirror the Node path helpers for plain paths.
rs_basename() {
  local p=${1%/}
  printf '%s' "${p##*/}"
}
rs_dirname() {
  local p=${1%/} head
  case "$p" in
    */*) head=${p%/*}; printf '%s' "${head:-/}" ;;
    *) printf '.' ;;
  esac
}

# rs_excerpt <value> collapses whitespace, trims, and caps at 180 characters.
rs_excerpt() {
  printf '%s' "$1" | LC_ALL=C awk '{
    out = $0
    gsub(/[ \t\r\n\f\v]+/, " ", out)
    sub(/^ /, "", out); sub(/ $/, "", out)
    if (length(out) > 180) out = substr(out, 1, 180)
    printf "%s\n", out
  }'
}

# rs_fingerprint <rule-id> <file> <line> <evidence> prints the sha256 of the NUL-joined tuple.
rs_fingerprint() {
  if command -v shasum >/dev/null 2>&1; then
    printf '%s\0%s\0%s\0%s' "$1" "$2" "$3" "$4" | shasum -a 256 | LC_ALL=C awk '{ print $1 }'
  else
    printf '%s\0%s\0%s\0%s' "$1" "$2" "$3" "$4" | sha256sum | LC_ALL=C awk '{ print $1 }'
  fi
}

# rs_engine_prog prints the awk matcher program. It reads a three-column rule table
# (id, pattern, flags) on stdin and the scanned text through RX_TEXTFILE.
rs_engine_prog() {
  cat <<'RX_ENGINE'
# Backtracking regular-expression engine (JavaScript-compatible subset) in POSIX awk.
# Supports: literals, '.', character classes, escapes (\s \S \d \w \b \B \n \t \r \f \v),
# groups, alternation, greedy quantifiers (* + ? {n} {n,} {n,m}), lookahead (?=) (?!),
# anchors ^ $, and the i flag.
# Input: rule table on stdin: id <TAB> pattern <TAB> flags
# Environment: RX_TEXTFILE (file to scan), RX_MODE (match|count|bool), RX_ENGINE (label column),
#              RX_NOEOL=1 when the file has no trailing newline.
# Output: RX_MODE=match -> id <TAB> engine <TAB> line <TAB> excerpt
#         RX_MODE=count -> id <TAB> count
#         RX_MODE=bool  -> id <TAB> 0|1
# Escapes \d, \w and \s follow the ASCII JavaScript definitions; matching is byte oriented, which
# keeps offsets and line numbers exact for the ASCII signatures the registry targets.

function is_space(ch) {
  return index(" \t\n\r\f\v", ch) > 0
}
function is_word(ch) {
  if (ch == "") return 0
  if (ch >= "a" && ch <= "z") return 1
  if (ch >= "A" && ch <= "Z") return 1
  if (ch >= "0" && ch <= "9") return 1
  return ch == "_"
}
function fold(ch,   f) {
  if (!icase) return ch
  if (ch in foldcache) return foldcache[ch]
  f = (ch >= "A" && ch <= "Z") ? tolower(ch) : ch
  foldcache[ch] = f
  return f
}
function newnode(t,   n) { n = ++nn; nt[n] = t; kid[n] = 0; sib[n] = 0; return n }
function append(n, c,   p) {
  if (kid[n] == 0) { kid[n] = c; return }
  p = kid[n]
  while (sib[p] != 0) p = sib[p]
  sib[p] = c
}
function mkrep(child, mn, mx,   n) {
  n = newnode("rep"); rmin[n] = mn; rmax[n] = mx; kid[n] = child; return n
}
function mkclass(   n) { n = newnode("class"); cls[n] = cid; return n }
function finish_class(   n) {
  cn[cid] = ccount; csn[cid] = cscount
  cnegf[cid] = cneg; cspacef[cid] = cspace; cnonspacef[cid] = cnonspace
  clsall[cid] = (cneg == 0 && cspace == 1 && cnonspace == 1) ? 1 : 0
  return mkclass()
}

# ---------- parser ----------
function parse_alt(   left, right, n) {
  left = parse_seq()
  while (pi <= plen && substr(pat, pi, 1) == "|") {
    pi++
    right = parse_seq()
    n = newnode("alt")
    append(n, left); append(n, right)
    left = n
  }
  return left
}
function parse_seq(   n, piece) {
  n = newnode("seq")
  while (pi <= plen) {
    c = substr(pat, pi, 1)
    if (c == "|" || c == ")") break
    piece = parse_piece()
    append(n, piece)
  }
  return n
}
function parse_piece(   a, c, mn, mx) {
  a = parse_atom()
  while (pi <= plen) {
    c = substr(pat, pi, 1)
    if (c == "*") { pi++; a = mkrep(a, 0, -1) }
    else if (c == "+") { pi++; a = mkrep(a, 1, -1) }
    else if (c == "?") { pi++; a = mkrep(a, 0, 1) }
    else if (c == "{" && parse_brace()) { a = mkrep(a, bmn, bmx) }
    else break
  }
  return a
}
# Parses {n}, {n,}, {n,m} at pi. Returns 1 and advances when valid.
function parse_brace(   i, d, firstPart) {
  i = pi + 1; d = ""
  while (i <= plen && substr(pat, i, 1) >= "0" && substr(pat, i, 1) <= "9") { d = d substr(pat, i, 1); i++ }
  if (d == "") return 0
  firstPart = d
  if (substr(pat, i, 1) == "}") {
    bmn = firstPart + 0; bmx = firstPart + 0; pi = i + 1; return 1
  }
  if (substr(pat, i, 1) != ",") return 0
  i++; d = ""
  while (i <= plen && substr(pat, i, 1) >= "0" && substr(pat, i, 1) <= "9") { d = d substr(pat, i, 1); i++ }
  if (substr(pat, i, 1) != "}") return 0
  bmn = firstPart + 0
  if (d == "") bmx = -1; else bmx = d + 0
  pi = i + 1
  return 1
}
function parse_atom(   c, e, n, clsNode) {
  c = substr(pat, pi, 1)
  if (c == "(") {
    pi++
    if (substr(pat, pi, 1) == "?") {
      pi++
      c = substr(pat, pi, 1)
      if (c == ":") { pi++ }
      else if (c == "=" || c == "!") {
        pi++
        n = newnode("look"); lneg[n] = (c == "!"); kid[n] = parse_alt()
        if (substr(pat, pi, 1) == ")") pi++
        return n
      } else {
        # unsupported group modifier: treat remaining as group
      }
    }
    n = newnode("group"); kid[n] = parse_alt()
    if (substr(pat, pi, 1) == ")") pi++
    return n
  }
  if (c == "[") { pi++; return parse_class() }
  if (c == ".") { pi++; return newnode("any") }
  if (c == "^") { pi++; n = newnode("as"); akind[n] = 0; return n }
  if (c == "$") { pi++; n = newnode("as"); akind[n] = 1; return n }
  if (c == "\\") {
    pi++; e = substr(pat, pi, 1); pi++
    if (e == "d") { start_class(); addrange("0", "9"); return finish_class() }
    if (e == "w") { start_class(); addrange("0", "9"); addrange("A", "Z"); addrange("a", "z"); addsingle("_"); return finish_class() }
    if (e == "s") { start_class(); cspace = 1; return finish_class() }
    if (e == "S") { start_class(); cnonspace = 1; return finish_class() }
    if (e == "b") { n = newnode("as"); akind[n] = 2; return n }
    if (e == "B") { n = newnode("as"); akind[n] = 3; return n }
    if (e == "n") return mkchar("\n")
    if (e == "t") return mkchar("\t")
    if (e == "r") return mkchar("\r")
    if (e == "f") return mkchar("\f")
    if (e == "v") return mkchar("\v")
    if (e == "0") return mkchar("\0")
    return mkchar(e)
  }
  pi++
  return mkchar(c)
}
function mkchar(ch,   n) { n = newnode("lit"); lch[n] = fold(ch); return n }

# class table state during parse
function start_class(   c) {
  cid = ++nc
  cneg = 0; cspace = 0; cnonspace = 0; ccount = 0; cscount = 0
}
function addrange(lo, hi) {
  ccount++
  crlo[cid, ccount] = fold(lo)
  crhi[cid, ccount] = fold(hi)
}
function addsingle(ch) {
  cscount++
  csch[cid, cscount] = fold(ch)
}
function parse_class(   neg, ch, hi, first, done, i) {
  start_class()
  if (substr(pat, pi, 1) == "^") { cneg = 1; pi++ }
  first = 1
  while (pi <= plen) {
    ch = substr(pat, pi, 1)
    if (ch == "]" && !first) { pi++; done = 1; break }
    first = 0
    if (ch == "\\") {
      pi++; ch = substr(pat, pi, 1); pi++
      if (ch == "d") { addrange("0", "9"); continue }
      if (ch == "w") { addrange("0", "9"); addrange("A", "Z"); addrange("a", "z"); addsingle("_"); continue }
      if (ch == "s") { cspace = 1; continue }
      if (ch == "S") { cnonspace = 1; continue }
      if (ch == "n") { addsingle("\n"); continue }
      if (ch == "t") { addsingle("\t"); continue }
      if (ch == "r") { addsingle("\r"); continue }
      if (ch == "f") { addsingle("\f"); continue }
      if (ch == "v") { addsingle("\v"); continue }
      addsingle(ch)
      continue
    }
    if (ch == "-" && ccount + cscount == 0) { addsingle("-"); pi++; continue }
    if (substr(pat, pi + 1, 1) == "-" && pi + 2 <= plen && substr(pat, pi + 2, 1) != "]") {
      hi = substr(pat, pi + 2, 1)
      if (hi == "\\") { hi = substr(pat, pi + 3, 1); pi++ }
      addrange(ch, hi); pi += 3; continue
    }
    addsingle(ch); pi++
  }
  return finish_class()
}
function cls_match(c, ch,   k, x, m, key) {
  key = c SUBSEP ch
  if (key in clcache) return clcache[key]
  x = fold(ch); m = 0
  for (k = 1; k <= cn[c]; k++) if (x >= crlo[c, k] && x <= crhi[c, k]) { m = 1; break }
  if (!m) for (k = 1; k <= csn[c]; k++) if (x == csch[c, k]) { m = 1; break }
  if (!m && cspacef[c] && index(" \t\n\r\f\v", ch) > 0) m = 1
  if (!m && cnonspacef[c] && index(" \t\n\r\f\v", ch) == 0) m = 1
  if (cnegf[c]) m = !m
  clcache[key] = m
  return m
}

# ---------- code emitter ----------
function newpc(   p) { p = ++pc; return p }
# Recognizes (?=(?:[\s\S]*LITERAL){n}) and returns n with cpat_lit set.
function unwrap_single(n,   c) {
  while (1) {
    if (nt[n] == "group") { c = kid[n] }
    else if (nt[n] == "seq" && kid[n] != 0 && sib[kid[n]] == 0) { c = kid[n] }
    else return n
    if (c == n || c == 0) return n
    n = c
  }
}
function extract_count(n,   c, k, kids2, j, lit) {
  n = unwrap_single(n)
  if (nt[n] != "rep" || rmax[n] != rmin[n] || rmax[n] < 1) return 0
  c = unwrap_single(kid[n])
  if (nt[c] != "seq") return 0
  k = 0; j = kid[c]
  while (j != 0) { k++; kids2[k] = j; j = sib[j] }
  if (k < 2 || !is_all_star(kids2[1])) return 0
  lit = ""
  for (j = 2; j <= k; j++) {
    if (nt[kids2[j]] != "lit") return 0
    lit = lit lch[kids2[j]]
  }
  if (length(lit) < 1) return 0
  cpat_lit = lit
  return rmax[n]
}
function is_all_star(n) {
  return nt[n] == "rep" && rmin[n] == 0 && rmax[n] == -1 && nt[kid[n]] == "class" && clsall[cls[kid[n]]]
}
function emit(n,   c, k, kids, i, s, j, ends, subp, after, skip, e, lit) {
  k = 0
  if (nt[n] == "seq") {
    k = 0; c = kid[n]
    while (c != 0) { k++; kids[k] = c; c = sib[c] }
    i = 1
    while (i <= k) {
      if (is_all_star(kids[i])) {
        lit = ""; j = i + 1
        while (j <= k && nt[kids[j]] == "lit") { lit = lit lch[kids[j]]; j++ }
        if (length(lit) >= 2) {
          s = newpc(); op[s] = 15; sarg[s] = lit; a1[s] = pc + 1
          i = j
          continue
        }
      }
      emit(kids[i]); i++
    }
  } else if (nt[n] == "group") {
    emit(kid[n])
  } else if (nt[n] == "alt") {
    c = kid[n]
    while (c != 0) { k++; kids[k] = c; c = sib[c] }
    j = 0
    for (i = 1; i <= k; i++) {
      if (i < k) {
        s = newpc(); op[s] = 4; a1[s] = pc + 1
        emit(kids[i])
        j++; ends[j] = newpc(); op[ends[j]] = 5
        a2[s] = pc + 1
      } else {
        emit(kids[i])
      }
    }
    for (i = 1; i <= j; i++) a1[ends[i]] = pc + 1
  } else if (nt[n] == "lit") {
    s = newpc(); op[s] = 1; sarg[s] = lch[n]
  } else if (nt[n] == "any") {
    s = newpc(); op[s] = 2
  } else if (nt[n] == "class") {
    s = newpc(); op[s] = 3; a1[s] = cls[n]
  } else if (nt[n] == "as") {
    s = newpc()
    if (akind[n] == 0) op[s] = 7
    else if (akind[n] == 1) op[s] = 8
    else if (akind[n] == 2) op[s] = 9
    else op[s] = 10
  } else if (nt[n] == "look") {
    if (!lneg[n]) { cpat_count = extract_count(kid[n]) }
    else cpat_count = 0
    if (cpat_count > 0) {
      s = newpc(); op[s] = 16; sarg[s] = cpat_lit; a1[s] = cpat_count
      return
    }
    s = newpc(); op[s] = lneg[n] ? 12 : 11
    skip = newpc(); op[skip] = 5
    subp = pc + 1
    emit(kid[n])
    e = newpc(); op[e] = 13
    after = pc + 1
a1[s] = subp; a2[s] = after; a1[skip] = after
  } else if (nt[n] == "rep") {
    c = kid[n]
    simple = (nt[c] == "lit" || nt[c] == "any" || nt[c] == "class")
    for (i = 1; i <= rmin[n]; i++) emit(c)
    if (rmax[n] == -1) {
      s = newpc(); op[s] = 4; a1[s] = s + 1
      emit(c)
      j = newpc(); op[j] = 5; a1[j] = s
      a2[s] = pc + 1
    } else if (simple) {
      if (rmax[n] > rmin[n]) {
        s = newpc(); op[s] = 14
        if (nt[c] == "lit") { a1[s] = 1; sarg[s] = lch[c] }
        else if (nt[c] == "any") { a1[s] = 2 }
        else { a1[s] = 3; a2[s] = cls[c] }
        a3[s] = rmax[n] - rmin[n]
        a4[s] = pc + 1
        pc = a4[s] - 1
      }
    } else {
      for (i = rmin[n]; i < rmax[n]; i++) {
        s = newpc(); op[s] = 4; a1[s] = pc + 1
        emit(c)
        a2[s] = pc + 1
      }
    }
  }
}
function compile(   root) {
  nn = 0; pc = 0; nc = 0
  pi = 1; plen = length(pat)
  root = parse_alt()
  emit(root)
  pc++
  op[pc] = 6
  mstart = 1
}

# ---------- VM ----------
function is_wb(pos,   before, after) {
  before = (pos > 0) ? substr(text, pos, 1) : ""
  after = (pos < tlen) ? substr(text, pos + 1, 1) : ""
  return is_word(before) != is_word(after)
}
function vm(startpc, startpos, term,   sp, p, pos, o, ch, r, ok, cnt, matchone, stp, stx, lit, ll, i, k2, cn2, lo, hi, mid) {
  sp = 0; p = startpc; pos = startpos
  while (1) {
    o = op[p]
    if (o == term) return pos
    ok = 0
    if (o == 1) {
      if (pos < tlen) { ch = substr(text, pos + 1, 1); if (fold(ch) == sarg[p]) { pos++; p++; ok = 1 } }
    } else if (o == 2) {
      if (pos < tlen) { ch = substr(text, pos + 1, 1); if (ch != "\n") { pos++; p++; ok = 1 } }
    } else if (o == 3) {
      if (pos < tlen) { if (cls_match(a1[p], substr(text, pos + 1, 1))) { pos++; p++; ok = 1 } }
    } else if (o == 4) {
      sp++; stp[sp] = a2[p]; stx[sp] = pos; p = a1[p]; ok = 1
    } else if (o == 5) {
      p = a1[p]; ok = 1
    } else if (o == 7) {
      if (pos == 0) { p++; ok = 1 }
    } else if (o == 8) {
      if (pos == tlen) { p++; ok = 1 }
    } else if (o == 9) {
      if (is_wb(pos)) { p++; ok = 1 }
    } else if (o == 10) {
      if (!is_wb(pos)) { p++; ok = 1 }
    } else if (o == 11) {
      r = vm(a1[p], pos, 13); if (r != -1) { p++; ok = 1 }
    } else if (o == 12) {
      r = vm(a1[p], pos, 13); if (r == -1) { p++; ok = 1 }
    } else if (o == 16) {
      lit = sarg[p]
      cn2 = lcnt[lit]
      lo = 1; hi = cn2; i = cn2 + 1
      while (lo <= hi) {
        mid = int((lo + hi) / 2)
        if (locc[lit, mid] >= pos) { i = mid; hi = mid - 1 } else lo = mid + 1
      }
      if (i <= cn2 && lchain[lit, i] >= a1[p]) { p++; ok = 1 }
    } else if (o == 15) {
      lit = sarg[p]; ll = length(lit)
      cn2 = lcnt[lit]; i = 1
      while (i <= cn2 && locc[lit, i] < pos) i++
      if (i > cn2) { ok = 0 }
      else {
        for (k2 = cn2; k2 > i; k2--) { sp++; stp[sp] = a1[p]; stx[sp] = locc[lit, k2] + ll }
        pos = locc[lit, i] + ll; p = a1[p]; ok = 1
      }
    } else if (o == 14) {
      cnt = 0
      while (cnt < a3[p] && pos < tlen) {
        ch = substr(text, pos + 1, 1)
        if (a1[p] == 1) matchone = (fold(ch) == sarg[p])
        else if (a1[p] == 2) matchone = (ch != "\n")
        else matchone = cls_match(a2[p], ch)
        if (!matchone) break
        sp++; stp[sp] = a4[p]; stx[sp] = pos
        pos++; cnt++
      }
      p = a4[p]; ok = 1
    }
    if (!ok) {
      if (sp == 0) return -1
      p = stp[sp]; pos = stx[sp]; sp--
    }
  }
}
function excerpt(value,   out) {
  out = value
  gsub(/[ \t\r\n\f\v]+/, " ", out)
  sub(/^ /, "", out); sub(/ $/, "", out)
  if (length(out) > 180) out = substr(out, 1, 180)
  return out
}
function count_nl(s,   n, t, i) {
  n = 0
  t = s
  while ((i = index(t, "\n")) > 0) { n++; t = substr(t, i + 1) }
  return n
}
BEGIN {
  FS = "\t"
  textfile = ENVIRON["RX_TEXTFILE"]
  mode = ENVIRON["RX_MODE"]
  envgine = ENVIRON["RX_ENGINE"]
  text = ""
  while ((getline line < textfile) > 0) text = text line "\n"
  if (ENVIRON["RX_NOEOL"] == "1") sub(/\n$/, "", text)
  tlen = length(text)
  while ((getline rl) > 0) {
    if (rl == "") continue
    split(rl, f, "\t")
    rid = f[1]; pat = f[2]; flags = f[3]
    icase = (index(flags, "i") > 0)
    compile()
    split("", lcnt); split("", locc); split("", lchain)
    split("", clcache); split("", foldcache)
    for (q = 1; q <= pc; q++) if (op[q] == 15 || op[q] == 16) litw[sarg[q]] = 1
    for (wl in litw) {
      c2 = 0; q = 0
      while ((q2 = index(substr(text, q + 1), wl)) > 0) {
        q = q + q2 - 1
        c2++; locc[wl, c2] = q
        q = q + 1
      }
      lcnt[wl] = c2
      for (i = c2; i >= 1; i--) {
        j = i + 1
        while (j <= c2 && locc[wl, j] < locc[wl, i] + length(wl)) j++
        lchain[wl, i] = 1 + ((j <= c2) ? lchain[wl, j] : 0)
      }
    }
    split("", litw)
    if (mode == "bool") {
      found = 0
      s = 0
      while (s <= tlen) { r = vm(mstart, s, 6); if (r != -1) { found = 1; break } s++ }
      print rid "\t" found
    } else if (mode == "count") {
      n = 0; s = 0
      while (s <= tlen) {
        r = vm(mstart, s, 6)
        if (r == -1) { s++; continue }
        n++
        if (r == s) s = s + 1; else s = r
      }
      print rid "\t" n
    } else {
      s = 0
      while (s <= tlen) {
        r = vm(mstart, s, 6)
        if (r == -1) { s++; continue }
        m = substr(text, s + 1, r - s)
        print rid "\t" envgine "\t" (count_nl(substr(text, 1, s)) + 1) "\t" excerpt(m)
        if (r == s) s = s + 1; else s = r
      }
    }
  }
}
RX_ENGINE
}

# rs_scan_table <mode> <engine> <textfile> reads a three-column rule table on stdin
# (id, pattern, flags) and scans one file. mode=match prints id, engine, line, excerpt;
# mode=count prints id, count; mode=bool prints id, 0|1.
rs_scan_table() {
  local _rs_mode=$1
  local _rs_engine=$2
  local _rs_text=$3
  local _rs_noeol=0
  if [ -s "$_rs_text" ] && [ -n "$(tail -c 1 "$_rs_text" 2>/dev/null)" ]; then
    _rs_noeol=1
  fi
  RX_TEXTFILE="$_rs_text" RX_NOEOL="$_rs_noeol" RX_MODE="$_rs_mode" RX_ENGINE="$_rs_engine" \
    LC_ALL=C awk "$(rs_engine_prog)"
}

# rs_scan <mode> <engine> <textfile> [rule-ids] runs the selected registry rules over one file.
rs_scan() {
  local _rs_mode=$1
  local _rs_engine=$2
  local _rs_text=$3
  local _rs_ids=${4:-}
  if [ -n "$_rs_ids" ]; then _rs_ids=",$_rs_ids,"; fi
  rule_registry_rows | LC_ALL=C awk -F '\t' -v engine="$_rs_engine" -v ids="$_rs_ids" '
    {
      if (ids != "" && index(ids, "," $1 ",") == 0) next
      count = split($4, engines, ",")
      hit = 0
      for (i = 1; i <= count; i++) if (engines[i] == engine) { hit = 1; break }
      if (hit) print $1 "\t" $13 "\t" $14
    }' | rs_scan_table "$_rs_mode" "$_rs_engine" "$_rs_text"
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
