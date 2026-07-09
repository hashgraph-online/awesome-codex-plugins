# Django HTMX Template And Interaction Patterns

## Valid Forms First

Keep forms valid without JavaScript, then add HTMX attributes:

```django
<form
  method="post"
  action="{% url 'profile_panel' %}"
  hx-post="{% url 'profile_panel' %}"
  hx-target="#profile-panel"
  hx-swap="outerHTML"
>
  {% csrf_token %}
  {% include "core/partials/profile_fields.html" with form=form %}
  <button type="submit">Save</button>
</form>
```

## Stable Targets

- Use `hx-target="#component-id"` with IDs that appear exactly once.
- Use `hx-swap="outerHTML"` when replacing the target element itself.
- Ensure partials returned to an `outerHTML` swap include the target root element
  with the same ID.
- Use `hx-swap="innerHTML"` when replacing only the target contents.
- Use `hx-select` or `reselect()` when the server returns a larger HTML response
  but only one fragment should be swapped.
- Use `hx-indicator` for visible pending states and `hx-disabled-elt` for
  controls that must not be clicked twice.
- Use `hx-confirm` for simple confirmation. Use an Alpine-controlled modal only
  when the confirmation has real UI complexity.

## Out-Of-Band Updates

Use out-of-band swaps for shared chrome, messages, counters, and badges that are
outside the main target:

```django
<div id="messages" hx-swap-oob="true">
  {% include "components/messages.html" with messages=messages %}
</div>
```

For lists, return the row or item fragment after create/update/delete instead of
rebuilding a full page unless the queryset ordering, filters, totals, or
pagination also change.

## Events And Alpine Coordination

Use HTMX events to connect server results to local browser state:

```python
response = render(request, "core/partials/dialog_body.html", context)
return trigger_client_event(response, "dialog:saved", after="swap")
```

```html
<div
  x-data="{ open: true }"
  @dialog:saved.window="open = false"
>
  <div x-show="open" id="dialog-body">
    ...
  </div>
</div>
```

Keep the ownership line clear:

- HTMX owns server trips, fresh HTML, history updates, and cross-component server
  facts.
- Alpine owns local-only state, keyboard/menu behavior, temporary UI state, and
  transitions.
- Do not mirror server truth into Alpine stores unless there is a clear reason
  and synchronization plan.
- After swapping content that contains Alpine components, rely on the loaded
  Alpine build to initialize new markup. Avoid manually calling Alpine lifecycle
  APIs unless a bug proves it is necessary.

## History, Navigation, And Boosting

- Use `hx-push-url="true"` only when the new state deserves a real browser URL.
- Ensure every pushed URL can render a full page on direct load and refresh.
- Use `push_url()` or `replace_url()` when the server decides which URL should
  appear after a swap.
- Keep `historyRestoreAsHxRequest = false` so htmx history-cache misses are sent
  as normal full-page requests rather than HX requests.
- Use `hx-boost` sparingly. Confirm forms still send CSRF tokens and links still
  render useful full pages.

## Django Recipe Notes

- For active search, prefer a GET form or input that targets a result-list
  partial. Preserve query params when the search should be refreshable or
  shareable.
- For pagination, return the list plus pagination controls from the same partial
  so page links keep targeting the right container.
- For infinite scroll, append item fragments only when ordering is stable, and
  include or remove the next-page sentinel deliberately.
- For polling, keep the polled partial small and use `HttpResponseStopPolling` or
  status `286` when work is complete.
- For custom dialogs, let Django render the dialog body and use
  `trigger_client_event()` to close the local dialog shell after successful
  saves.
- For click-to-edit, pair a display partial and a bound-form partial for the same
  object. Test display, edit, save, cancel, and invalid form paths.
- For global request headers, keep cross-cutting setup in the base template or
  bundled JS, not individual feature templates.
