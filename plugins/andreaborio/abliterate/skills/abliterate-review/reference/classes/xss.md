# Cross-site scripting (CWE-79)

## Sources
- Reflected: query/path/form values, `Referer`, error messages that echo input.
- Stored: profile fields, comments, filenames, titles, SVG/HTML uploads, markdown content, imported data, user-agent strings shown in admin pages.
- DOM: `location.hash/search`, `document.referrer`, `postMessage` data, `window.name`, `localStorage` values written from URL, API JSON rendered client-side.
- Email and PDF/HTML export templates fed by stored data.

## Sinks
| Stack | Sink / escape hatch | Safe alternative |
| --- | --- | --- |
| React | `dangerouslySetInnerHTML`, `href={userUrl}` / `src` with `javascript:`, `ref.current.innerHTML` | default `{text}`; sanitize with DOMPurify before the hatch; validate URL scheme |
| Vue | `v-html`, `:href="userUrl"`, `compile(userTemplate)` | `{{ text }}`, sanitize, scheme allowlist |
| Angular | `bypassSecurityTrustHtml/Url/Script/ResourceUrl`, `[innerHTML]` (sanitized by default) | default binding; avoid `bypassSecurityTrust*` on input |
| Plain DOM | `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `$(...).html()`, `jQuery(userString)`, `eval`, `setAttribute('on*')` | `textContent`, `createElement`+`setAttribute` for safe attrs |
| Jinja2 / Flask | `\|safe`, `Markup(x)`, `{% autoescape false %}`, `render_template_string(user)` | default autoescape (enabled for `.html` templates; check config for others) |
| Django | `\|safe`, `mark_safe`, `format_html` misuse (`format_html(userstr)` with no args), `{% autoescape off %}` | `format_html("<b>{}</b>", x)`, `escape` |
| Rails ERB | `raw`, `.html_safe`, `<%== %>`, `content_tag` with unescaped `:html_safe` strings, `link_to` with user URL | default `<%= %>`, `sanitize`, `safe_join` |
| Laravel Blade | `{!! $x !!}` | `{{ $x }}` |
| Thymeleaf | `th:utext`, `[(...)]` inline | `th:text`, `[[...]]` |
| Go | `template.HTML(x)`, `template.JS`, `template.URL`, `text/template` for HTML | `html/template` with plain strings |
| Express/PHP raw | `res.send(`<p>${x}</p>`)`, `echo $_GET['x']` | template engine with autoescape; `htmlspecialchars($x, ENT_QUOTES)` |
| Markdown | `marked`, `markdown-it({html:true})`, `showdown`, python-markdown, `commonmark` with `unsafe`/raw HTML on | disable raw HTML, then sanitize output (DOMPurify / bleach / `sanitize-html`) |

## Guards that work / Look-alike guards
Work:
- Context-correct output encoding by the templating layer (autoescape) with no hatch on the path.
- Sanitizer on the HTML immediately before the sink, with config reviewed (no `ALLOW_UNKNOWN_PROTOCOLS`, no `style`/`svg` surprises).
- URL scheme allowlist (`http:`, `https:`, `mailto:`) parsed with `new URL()`, applied to `href`/`src`/`action`/`formaction`.
- `Content-Type: text/plain` or `Content-Disposition: attachment` plus `X-Content-Type-Options: nosniff` for user uploads served from the app origin (or a separate sandbox origin).
- A strict CSP without `unsafe-inline` as defense in depth only.

Look-alike:
- HTML escaping in an attribute value without quoting; escaping for HTML placed inside `<script>` or inline `onclick`, a CSS context, or a URL.
- Stripping `<script>` or blocklisting `onerror`.
- `encodeURIComponent` before `href` (does not stop `javascript:` at the start).
- Sanitizing on write but rendering a different field/version; sanitizer applied, then string is transformed again (unescape, markdown render, template concat).
- Client-side-only sanitization when the API output is also rendered elsewhere.
- JSON embedded in `<script>` via `JSON.stringify` without escaping `</script>` or `<!--`.
- `Content-Type: application/json` on a response that a browser could sniff or that is later injected via `innerHTML`.

## Falsify before reporting
1. Does the value reach an escape hatch, or does the framework escape it by default? Find the exact template line/component and the hatch.
2. Context: HTML text, attribute, URL, JS, CSS? Which encoder is needed and is that the one applied?
3. Is a sanitizer on the path, and what is its config? Read it; a call to `DOMPurify.sanitize` with default config is fine for HTML text.
4. Does the response render as HTML (content type, `nosniff`), or is it JSON/plain text only?
5. Can the attacker's value reach a victim's browser (stored and shown to another user, or reflected via a link), or only their own session (self-XSS)?
6. Confirm: a test renders the component/template with a benign marker like `<b>x</b>` or `"onmouseover=` and the output contains escaped entities (`&lt;b&gt;`), or, for a URL, `javascript:void(0)` is rejected.

## Severity cues
- Raises: stored and shown to other/privileged users, no CSP, session cookie not `HttpOnly`, same origin as the app's API, admin panel render.
- Lowers: self-only, requires attacker already logged in as the same user, strong CSP that blocks inline script, content served from a sandboxed origin, reflected only via POST.
- A sanitizer bypass without a demonstrated unsafe config is `needs-evidence`.

## Regression test
- Fails before: render the view/component with name `<img src=x>` (benign marker) and assert the HTML output has `&lt;img` and no `<img` element from the value.
- URL contexts: a profile website of `javascript:void(0)` is rejected or rendered inert; `https://example.com/a?b=1` still renders as a link.
- Markdown: `<b>x</b>` in a comment is escaped or sanitized to the intended allowlist; `**bold**` and links still render.
- Allowed case: names with `&`, `<` in text, apostrophes and non-Latin characters display correctly (escaped once, not twice).
