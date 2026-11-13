# Splice the report body and theme into the page template.
#
#   awk -v tpl=report.html -v body=body.html -v css=report.css \
#       -v theme=civic.css -v js=report.js \
#       -v title="..." -v footerLeft="..." -v footerRight="..." \
#       -f assemble.awk > out.html
#
# One left-to-right pass over the template replaces each placeholder with its
# file content. Substituted text is never rescanned, so a body that happens to
# contain "__TITLE__" is left alone, and no value can corrupt another the way a
# chained sed substitution would.

function slurp(path,   line, buf) {
  buf = ""
  while ((getline line < path) > 0) buf = buf line "\n"
  close(path)
  return buf
}

function esc(s) {
  gsub(/&/, "\\&amp;", s)
  gsub(/</, "\\&lt;", s)
  gsub(/>/, "\\&gt;", s)
  return s
}

BEGIN {
  value["__BASE_CSS__"] = slurp(css)
  value["__THEME_CSS__"] = (theme == "") ? "" : slurp(theme)
  value["__RUNTIME_JS__"] = slurp(js)
  value["__BODY_HTML__"] = slurp(body)
  value["__TITLE__"] = esc(title)
  value["__FOOTER_LEFT__"] = esc(footerLeft)
  value["__FOOTER_RIGHT__"] = esc(footerRight)

  pattern = "__BASE_CSS__|__THEME_CSS__|__RUNTIME_JS__|__BODY_HTML__|__TITLE__|__FOOTER_LEFT__|__FOOTER_RIGHT__"

  text = slurp(tpl)
  out = ""
  while (match(text, pattern)) {
    out = out substr(text, 1, RSTART - 1) value[substr(text, RSTART, RLENGTH)]
    text = substr(text, RSTART + RLENGTH)
  }
  printf "%s%s", out, text
}
