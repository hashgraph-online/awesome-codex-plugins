# Typography: legibility and resilient content

Keep the existing font family, hierarchy and density unless a concrete failure
or an authorized redesign justifies changing them. One font family, serif body
text, compact UI and fixed type steps can be deliberate. A mandatory font
pairing or scale ratio is not an accessibility standard.

## Trace what is actually rendered

Inspect font-face declarations, loaded files, available weights, fallback
stacks and computed font values. Do not identify a font from a screenshot as
fact without evidence. A requested weight absent from the loaded font can
produce synthesis; establish the actual result before proposing a new asset.

Map heading, body, label, help text and numeric roles to project tokens. Find
where the changed role is used. If one shared caption token makes multiple
forms unreadable, report that cause once and list confirmed consumers.

Check wrapping with real approved content and representative long strings.
Inspect line-height, measure, tracking, zoom and user text-size adaptation;
readability depends on the font and task, not one universal pixel floor. Rem
units and unitless line-height are useful tools, not proof of accessible reflow.

## Match the text to its job

- Hierarchy should make the primary task and supporting facts distinguishable.
  Do not enlarge every heading in a dense professional tool to marketing scale.
- Numeric tables, timers and prices may benefit from tabular numerals when
  alignment changes cause real scanning difficulty. Use supported font features
  in the existing stack rather than loading a new font for one effect.
- Long labels and translated strings need room. Preserve approved words;
  correct container sizing or wrapping within scope before trimming meaning.
- Truncation must not conceal a value needed to decide or act. Verify the route
  to its full value with keyboard and touch, not only a desktop hover tooltip.
- Confirm language and direction metadata where relevant. Test mixed-direction
  values with supported locale behavior instead of manually reordering digits.
- Keep useful content selectable. Any selection suppression needs a concrete
  gesture interaction reason, not a site-wide stylistic preference.

For supported mobile browsers, inspect focus/zoom behavior on inputs. If small
text causes unwanted zoom or unreadability, test the smallest change in the
current component. Do not disable user zoom or transform text just to preserve
a small appearance.

## Verify and report

Render at matching desktop/mobile states, plus relevant text resize/reflow
checks. Record the loaded font and measured/computed values only when obtained.
A source `font-family` declaration does not prove that asset loaded, and a
screenshot alone does not prove locale or text-spacing behavior.

Separate standards (see the accessibility reference), project conventions and
optional optical tuning. No automatic punctuation substitution, letter-spacing
reset or font swap belongs in a scoped audit. For an authorized fix, recheck
line breaks, clipping, hierarchy and affected shared consumers after rendering.
