# Selenium Functional Test Patterns

## Explicit Wait Helper

Prefer a small helper that waits until a predicate succeeds and rethrows useful failure context.

```python
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

def wait_for(fn, timeout=5):
    return WebDriverWait(browser, timeout).until(lambda _driver: fn())
```

Keep helper call sites behavior-oriented:

```python
wait_for(lambda: "Project renamed" in browser.page_source)
```

## Interaction-Wait Pattern

After each browser action that triggers asynchronous work, wait for the next observable state:

- Page navigates: wait for URL or title.
- Form submits: wait for redirect, error text, or created row.
- JavaScript mutates DOM: wait for the element state or text.
- Server-side side effect: prefer a UI observation; if necessary, check the database in a focused helper.

## Page Pattern

Use the page pattern when repeated selectors make tests hard to read.

Good page methods:

- `login_as(email)`
- `add_item(text)`
- `assert_item_visible(text)`
- `go_to_my_lists()`

Weak page methods:

- `click_button_css_selector()`
- `find_input_by_id()`
- `sleep_then_reload()`

Keep page objects thin. They should express browser interactions, not recreate application business logic.

## Isolation Options

| Need | Pattern |
| --- | --- |
| Normal local tests | Database setup in `LiveServerTestCase` or fixtures |
| Authenticated journey without repeating login | Pre-create a session when the login flow is not under test |
| Staging data | Management command or API endpoint designed for test setup |
| Parallel safety | Unique users, URLs, list names, and generated identifiers |

Do not run test-only setup against production.

## CI Failure Artifacts

When functional tests fail in CI, collect:

- Screenshot.
- HTML source.
- Browser console logs where available.
- Server logs.
- Current URL and test name.

Artifacts should help diagnose the first failure without rerunning the pipeline.

## Common Flake Causes

- Implicit waits mixed with explicit waits.
- Sleep-based timing.
- Shared state across tests.
- Headless browser differences.
- Static files missing in test server or container.
- Selector coupled to layout instead of semantic structure.
