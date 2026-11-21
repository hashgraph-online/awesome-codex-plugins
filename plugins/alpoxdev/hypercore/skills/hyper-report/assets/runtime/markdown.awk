# hyper-report markdown dialect -> static HTML fragment.
#
# Reads the report body on stdin (frontmatter already stripped by the caller) and
# writes one HTML element per top-level block on stdout. The element stream is
# what the paginator in report.js distributes across fixed pages.
#
# Supported: ATX headings, paragraphs, bullet and ordered lists (nested by
# indentation), blockquotes, fenced code, GFM tables with column alignment,
# thematic breaks, standalone images as figures, inline bold/italic/code/links,
# the [TOC] marker, raw HTML blocks, and the :::kpi, :::callout, :::pagebreak
# directives. Underscore emphasis is deliberately unsupported so identifiers
# such as snake_case_sql survive intact.

function esc(s) {
  gsub(/&/, "\\&amp;", s)
  gsub(/</, "\\&lt;", s)
  gsub(/>/, "\\&gt;", s)
  return s
}

function trim(s) {
  sub(/^[ \t]+/, "", s)
  sub(/[ \t]+$/, "", s)
  return s
}

function protect_code(s,   out, a, b, seg) {
  out = ""
  split("", _code)
  _code_n = 0
  while ((a = index(s, "`")) > 0) {
    b = index(substr(s, a + 1), "`")
    if (b == 0) break
    seg = substr(s, a + 1, b - 1)
    _code[++_code_n] = seg
    out = out substr(s, 1, a - 1) "\001" _code_n "\001"
    s = substr(s, a + b + 1)
  }
  return out s
}

function restore_code(s,   out, a, b, idx) {
  out = ""
  while ((a = index(s, "\001")) > 0) {
    b = index(substr(s, a + 1), "\001")
    if (b == 0) break
    idx = substr(s, a + 1, b - 1) + 0
    out = out substr(s, 1, a - 1) "<code>" _code[idx] "</code>"
    s = substr(s, a + b + 1)
  }
  return out s
}

function bold(s,   out) {
  out = ""
  while (match(s, /\*\*[^* ][^*]*\*\*/)) {
    out = out substr(s, 1, RSTART - 1) "<strong>" substr(s, RSTART + 2, RLENGTH - 4) "</strong>"
    s = substr(s, RSTART + RLENGTH)
  }
  return out s
}

function italic(s,   out) {
  out = ""
  while (match(s, /\*[^* ][^*]*\*/)) {
    out = out substr(s, 1, RSTART - 1) "<em>" substr(s, RSTART + 1, RLENGTH - 2) "</em>"
    s = substr(s, RSTART + RLENGTH)
  }
  return out s
}

function images(s,   out, whole, cut, alt, url) {
  out = ""
  while (match(s, /!\[[^]]*\]\([^)]*\)/)) {
    whole = substr(s, RSTART, RLENGTH)
    cut = index(whole, "](")
    alt = substr(whole, 3, cut - 3)
    url = substr(whole, cut + 2, length(whole) - cut - 2)
    out = out substr(s, 1, RSTART - 1) "<img src=\"" url "\" alt=\"" alt "\">"
    s = substr(s, RSTART + RLENGTH)
  }
  return out s
}

function links(s,   out, whole, cut, text, url) {
  out = ""
  while (match(s, /\[[^]]*\]\([^)]*\)/)) {
    whole = substr(s, RSTART, RLENGTH)
    cut = index(whole, "](")
    text = substr(whole, 2, cut - 2)
    url = substr(whole, cut + 2, length(whole) - cut - 2)
    out = out substr(s, 1, RSTART - 1) "<a href=\"" url "\">" text "</a>"
    s = substr(s, RSTART + RLENGTH)
  }
  return out s
}

function citations(s,   out) {
  out = ""
  while (match(s, /\[S[0-9][0-9]*\]/)) {
    out = out substr(s, 1, RSTART - 1) "<span class=\"cite\">" substr(s, RSTART + 1, RLENGTH - 2) "</span>"
    s = substr(s, RSTART + RLENGTH)
  }
  return out s
}

function inline(s) {
  s = esc(s)
  s = protect_code(s)
  s = bold(s)
  s = italic(s)
  s = images(s)
  s = links(s)
  s = citations(s)
  s = restore_code(s)
  return s
}

# --- block emitters --------------------------------------------------------

function emit_fence(i,   lang, body, cls, j) {
  lang = trim(substr(lines[i], 4))
  body = ""
  j = i + 1
  while (j <= n && lines[j] !~ /^```/) {
    body = body esc(lines[j]) "\n"
    j++
  }
  cls = (lang == "") ? "" : " class=\"language-" lang "\""
  printf "<pre><code%s>%s</code></pre>\n", cls, body
  return j + 1
}

function emit_heading(i,   level, text, tag) {
  level = 0
  while (substr(lines[i], level + 1, 1) == "#" && level < 6) level++
  text = substr(lines[i], level + 1)
  sub(/^[ \t]+/, "", text)
  sub(/[ \t]+#+[ \t]*$/, "", text)
  tag = "h" level
  printf "<%s>%s</%s>\n", tag, inline(text), tag
  return i + 1
}

function split_row(row, cells,   buf) {
  buf = row
  sub(/^[ \t]*\|/, "", buf)
  sub(/\|[ \t]*$/, "", buf)
  return split(buf, cells, "|")
}

function emit_table(i,   j, rows, cols, r, c, out, cells, sep, cls) {
  j = i
  rows = 0
  while (j <= n && lines[j] ~ /^[ \t]*\|/) {
    raw_row[++rows] = lines[j]
    j++
  }
  if (rows < 2) return -1
  sep = trim(raw_row[2])
  if (sep !~ /^\|[ :|-]+\|$/) return -1
  cols = split_row(sep, cells)
  for (c = 1; c <= cols; c++) {
    cls = trim(cells[c])
    if (cls ~ /^:-+:$/) align[c] = " class=\"center\""
    else if (cls ~ /-:$/) align[c] = " class=\"num\""
    else align[c] = ""
  }
  out = "<table>"
  for (r = 1; r <= rows; r++) {
    if (r == 2) continue
    split_row(raw_row[r], cells)
    if (r == 1) {
      out = out "<thead><tr>"
      for (c = 1; c <= cols; c++) out = out "<th" align[c] ">" inline(trim(cells[c])) "</th>"
      out = out "</tr></thead><tbody>"
    } else {
      out = out "<tr>"
      for (c = 1; c <= cols; c++) out = out "<td" align[c] ">" inline(trim(cells[c])) "</td>"
      out = out "</tr>"
    }
  }
  out = out "</tbody></table>"
  print out
  return j
}

function emit_quote(i,   body, j, line) {
  body = ""
  j = i
  while (j <= n && lines[j] ~ /^[ \t]*>/) {
    line = lines[j]
    sub(/^[ \t]*>[ \t]?/, "", line)
    body = (body == "") ? line : body " " line
    j++
  }
  printf "<blockquote><p>%s</p></blockquote>\n", inline(body)
  return j
}

function indent_of(s) {
  match(s, /^[ \t]*/)
  return RLENGTH
}

# Lists keep a stack of open list tags. A deeper item opens a nested list inside
# the still-open <li>; a shallower one closes every list above its own level.
function emit_list(i,   j, out, line, kind, level, open, txt, depth) {
  j = i
  out = ""
  depth = 0
  while (j <= n) {
    line = lines[j]
    if (line !~ /^[ \t]*([-*+]|[0-9]+[.)])[ \t]+/) break
    kind = (line ~ /^[ \t]*[0-9]+[.)][ \t]+/) ? "ol" : "ul"
    level = int(indent_of(line) / 2)
    txt = line
    sub(/^[ \t]*([-*+]|[0-9]+[.)])[ \t]+/, "", txt)
    while (depth > level + 1) {
      out = out "</li></" open[depth] ">"
      depth--
    }
    if (depth == level + 1) {
      if (open[depth] != kind) {
        out = out "</li></" open[depth] ">"
        depth--
      } else {
        out = out "</li>"
      }
    }
    while (depth < level + 1) {
      depth++
      open[depth] = kind
      out = out "<" kind ">"
    }
    out = out "<li>" inline(txt)
    j++
  }
  while (depth > 0) {
    out = out "</li></" open[depth] ">"
    depth--
  }
  print out
  return j
}

function emit_raw(i,   j, out) {
  j = i
  out = ""
  while (j <= n && lines[j] !~ /^[ \t]*$/) {
    out = out lines[j] "\n"
    j++
  }
  printf "%s", out
  return j
}

function emit_para(i,   j, text, line, alt, url) {
  j = i
  text = ""
  while (j <= n) {
    line = lines[j]
    if (line ~ /^[ \t]*$/) break
    if (text != "" && (line ~ /^```/ || line ~ /^:::/ || line ~ /^[ \t]*\|/ || line ~ /^#{1,6}[ \t]/ || line ~ /^[ \t]*>/ || line ~ /^[ \t]*([-*+]|[0-9]+[.)])[ \t]+/ || line ~ /^(-{3,}|\*{3,}|_{3,})[ \t]*$/ || line ~ /^\[TOC\][ \t]*$/ || line ~ /^[ \t]*</)) break
    text = (text == "") ? line : text " " line
    j++
  }
  if (text ~ /^!\[[^]]*\]\([^)]*\)$/) {
    alt = text
    sub(/^!\[/, "", alt)
    sub(/\]\(.*$/, "", alt)
    url = text
    sub(/^.*\]\(/, "", url)
    sub(/\)$/, "", url)
    printf "<figure><img src=\"%s\" alt=\"%s\"><figcaption>%s</figcaption></figure>\n", url, alt, inline(alt)
    return j
  }
  printf "<p>%s</p>\n", inline(text)
  return j
}

function emit_kpi(i,   j, out, line, label, value, sep) {
  j = i + 1
  out = "<div class=\"kpis\">"
  while (j <= n && lines[j] !~ /^:::/) {
    line = trim(lines[j])
    if (line != "" && index(line, "|") > 0) {
      sep = index(line, "|")
      label = trim(substr(line, 1, sep - 1))
      value = trim(substr(line, sep + 1))
      sub(/^[-*+][ \t]+/, "", label)
      out = out "<div class=\"kpi\"><div class=\"kpi-value\">" inline(value) "</div><div class=\"kpi-label\">" inline(label) "</div></div>"
    }
    j++
  }
  print out "</div>"
  return j + 1
}

function emit_callout(i,   label, j, body, line) {
  label = trim(substr(lines[i], 11))
  j = i + 1
  body = ""
  while (j <= n && lines[j] !~ /^:::/) {
    line = trim(lines[j])
    if (line != "") body = (body == "") ? line : body " " line
    j++
  }
  printf "<div class=\"callout\"><div class=\"callout-label\">%s</div><p>%s</p></div>\n", inline(label), inline(body)
  return j + 1
}

# --- main ------------------------------------------------------------------

{ lines[++n] = $0 }

END {
  i = 1
  while (i <= n) {
    line = lines[i]
    if (line ~ /^[ \t]*$/) {
      i++
      continue
    }
    if (line ~ /^```/) {
      i = emit_fence(i)
      continue
    }
    if (line ~ /^:::[ \t]*pagebreak[ \t]*$/) {
      print "<div data-break=\"1\"></div>"
      i++
      continue
    }
    if (line ~ /^:::[ \t]*kpi[ \t]*$/) {
      i = emit_kpi(i)
      continue
    }
    if (line ~ /^:::[ \t]*callout/) {
      i = emit_callout(i)
      continue
    }
    if (line ~ /^[ \t]*\|/) {
      ni = emit_table(i)
      if (ni > 0) {
        i = ni
        continue
      }
    }
    if (line ~ /^#{1,6}[ \t]/) {
      i = emit_heading(i)
      continue
    }
    if (line ~ /^[ \t]*>/) {
      i = emit_quote(i)
      continue
    }
    if (line ~ /^[ \t]*([-*+]|[0-9]+[.)])[ \t]+/) {
      i = emit_list(i)
      continue
    }
    if (line ~ /^(-{3,}|\*{3,}|_{3,})[ \t]*$/) {
      print "<hr>"
      i++
      continue
    }
    if (line ~ /^\[TOC\][ \t]*$/) {
      print "<nav class=\"toc\" data-toc aria-label=\"Contents\"></nav>"
      i++
      continue
    }
    if (line ~ /^[ \t]*</) {
      i = emit_raw(i)
      continue
    }
    i = emit_para(i)
  }
}
