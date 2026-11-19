# Page data

Use this recipe when the user asks a page to save visitor input. An RSVP uses a private collection. A visitor can update their response from the same browser. The author reads all entries from the private management link's Data tab.

Put a new page title in HTML `<title>`, not `publish.title`. Bind submit/click handlers before asynchronous state or configuration reads; await readiness inside the handler so the first interaction is saved.

```html
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<title>RSVP</title>
<form>
  <label>Will you attend?
    <select name="reply"><option value="yes">Yes</option><option value="no">No</option></select>
  </label>
  <p>Your response is saved on BrewPage and can be read by the page’s author.</p>
  <button type="submit">Save response</button>
</form>
<p role="status"></p>
<script src="https://brewpage.app/js/state.js"></script>
<script>
  const status = document.querySelector('[role="status"]');
  document.querySelector('form').addEventListener('submit', async event => {
    event.preventDefault();
    const reply = new FormData(event.currentTarget).get('reply');
    try {
      const state = await globalThis.bp?.state();
      if (!state) {
        status.textContent = 'Saving is unavailable here.';
        return;
      }
      await state.col('rsvps').set('me', { reply });
      status.textContent = state.local ? 'Saved in this browser for preview.' : 'Response saved.';
    } catch (error) {
      status.textContent = error.message || 'Could not save your response.';
    }
  });
</script>
</html>
```

Pair the page with this publish declaration.

```json
{"collections":{"rsvps":{"mode":"private","maxDocsPerVisitor":1}}}
```

## Local preview and publish

- Keep the absolute `https://brewpage.app/js/state.js` classic script before dependent code. Avoid `async`, import and top-level await. Guard `bp.state()` and keep a visible failure message. Local browser preview can use browser-local storage on `localhost`. A draft returns the files and declaration without fetching templates, tools or hosted storage. Browser-local preview does not prove that entries persist on BrewPage.
- A requested publish includes the HTML and `state` together. Use the installed MCP tool's `state` object or REST runner `--state` with one JSON object. The public HTML REST API uses a JSON body with `content` and `state`. A site uses a multipart `state` field. Verify the returned address, applied state and notices. Page data works on a supported publication origin or a connected custom domain. Markdown cannot run the SDK.
- On an owned test fixture, submit a visitor reply, then reload and confirm it through the owner's Data tab or the authorized Page data read operation. Use the exact target. A later content-only update should preserve the declaration and entries. Omit `state` when changing content alone. Never widen an existing private collection, copy its entries to a new publication, or fabricate a saved answer.

For a public guestbook, use a separately named `shared` collection only if the user wants everyone to read its entries. Give visitors a public visibility notice and render stored values as text with `bp.text()` or `textContent`. For a poll, `set('me', ...)` retains one entry per browser and explicit `choices` supports aggregate counts. Never collect credentials in the page. Use the [BrewPage Page data reference](https://brewpage.app/llms-page-data.txt) and [working templates](https://brewpage.app/templates) for other authorized variations.
