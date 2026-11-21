#!/usr/bin/env bash
# Markup-family scan: reuse the text scanner with the markup engine label, and expose the
# source-local exemption map.
set -euo pipefail

RS_ENGINE_DIR=$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$RS_ENGINE_DIR/engine-text.sh"

# scan_markup <file> <textfile> <root> <rule-ids> prints matching markup-engine rules.
scan_markup() {
  scan_text "$1" "$2" "$3" "${4:-}" markup
}

# markup_ignore_regions <file> prints start<TAB>end<TAB>ids for every element that carries a
# data-detect-ignore attribute. A region spans the element's opening tag through its matching
# closing tag, or only the tag line when the tag self-closes. The ids column keeps the attribute
# value verbatim; the detector decides which rule ids it covers.
markup_ignore_regions() {
  LC_ALL=C awk '
    BEGIN { SQ = sprintf("%c", 39) }
    function newlines(s,   n, t) {
      n = 0
      while ((t = index(s, "\n")) > 0) { n++; s = substr(s, t + 1) }
      return n
    }
    function tag_at(s,   m) {
      if (match(s, /^<\/?[A-Za-z][A-Za-z0-9-]*/)) {
        m = substr(s, 1, RLENGTH)
        sub(/^<\/?/, "", m)
        return tolower(m)
      }
      return ""
    }
    function attr_ids(s,   i, p, q, quote, val) {
      i = index(s, "data-detect-ignore")
      if (i == 0) return ""
      p = i + length("data-detect-ignore")
      while (p <= length(s) && (substr(s, p, 1) == " " || substr(s, p, 1) == "\t")) p++
      if (substr(s, p, 1) != "=") return ""
      p++
      while (p <= length(s) && (substr(s, p, 1) == " " || substr(s, p, 1) == "\t")) p++
      quote = substr(s, p, 1)
      if (quote != "\"" && quote != SQ) return ""
      p++
      q = index(substr(s, p), quote)
      if (q == 0) return ""
      val = substr(s, p, q - 1)
      gsub(/[ \t]+/, "", val)
      return val
    }
    { text = text $0 "\n" }
    END {
      pos = 1
      len = length(text)
      while (pos <= len) {
        i = index(substr(text, pos), "data-detect-ignore")
        if (i == 0) break
        at = pos + i - 1
        lt = at
        while (lt > 1 && substr(text, lt, 1) != "<") lt--
        if (index(substr(text, lt, at - lt), ">") != 0) {
          pos = at + length("data-detect-ignore")
          continue
        }
        tag = tag_at(substr(text, lt))
        if (tag == "") {
          pos = at + length("data-detect-ignore")
          continue
        }
        gt = at
        while (gt <= len && substr(text, gt, 1) != ">") gt++
        if (gt > len) break
        ids = attr_ids(substr(text, lt, gt - lt + 1))
        sline = newlines(substr(text, 1, lt)) + 1
        if (substr(text, gt - 1, 1) == "/") {
          eline = sline
        } else {
          depth = 1
          j = gt + 1
          eline = 0
          while (j <= len) {
            k = index(substr(text, j), "<")
            if (k == 0) break
            k = j + k - 1
            nm = tag_at(substr(text, k))
            if (substr(text, k, 2) == "</") {
              if (nm == tag) {
                depth--
                if (depth == 0) { eline = newlines(substr(text, 1, k)) + 1; break }
              }
              j = k + 2
            } else if (nm == "") {
              j = k + 1
            } else {
              q = k
              while (q <= len && substr(text, q, 1) != ">") q++
              if (!(q > k && substr(text, q - 1, 1) == "/") && nm == tag) depth++
              j = q + 1
            }
          }
          if (eline == 0) eline = newlines(text) + 1
        }
        if (ids != "") printf "%d\t%d\t%s\n", sline, eline, ids
        pos = gt + 1
      }
    }
  ' "$1"
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi
