# When a screenshot looks wrong

Read this when a shot looks wrong or a fix seems not to have worked. A wrong-looking shot is either a capture problem
(the shot doesn't show what a person would see) or a real defect. Work out which before you reset anything, and keep
the shot and the step that produced it either way, so the problem can be reproduced.

## Check these first

1. **The build.** Read the dev server's or bundler's log for errors: a failed rebuild leaves the old code running. If
   the app serves development bundles without a content hash, clear the browser cache at the start of the step (the
   example runner does).
2. **The page.** A page with a public cache header can show the version from before your edit: load it with a new
   query string (`?qa=<timestamp>`).
3. **The state.** Is the page in the state the step meant to reach: the right user, the right record, the dialog
   open, the step of a multi-step form showing? Hover and focus styles from the last action leak into the next shot
   (`qa.clearHover()`).
4. **The viewport and theme.** Check the width, the device scale and the theme the shot was taken at. If the app
   stores its own theme choice as well as following the system setting, set both.
5. **Readiness.** Wait for the condition that matters (a selector, some text, a stable size) plus fonts and visible
   images (`qa.settle()`), not a fixed delay. Avoid waiting for network idle on pages that poll. Lazy images below
   the fold need a scroll before a full-page shot.

## Then decide

- If one of those explains it, fix the capture and shoot again with a new suffix (`QA_SUFFIX=R2`).
- If the shot still looks wrong with the build, state, viewport, theme and readiness confirmed, it's a defect: record
  it as a finding with the shot.
- If you can't tell, try to reproduce it the way a person would (a fresh tab, a normal reload, a real device width)
  and say in the finding what you ruled out.

## Proving a fix

- The "after" shot's file time is later than your edit (`stat -c %y` on Linux, `stat -f '%Sm' -t '%FT%T'` on macOS),
  and the zoomed crop contains the changed element.
- Look at every shot cropped and zoomed. A step that finished without errors only proves its selectors matched.

## Differences between machines

Scrollbars and fonts differ between operating systems: classic scrollbars narrow the page on Windows, most Linux
desktops and typical CI browser images, and a heading can wrap where a font isn't installed. When a layout depends on
the full window width or a particular font, check it in the browser your CI uses as well.
