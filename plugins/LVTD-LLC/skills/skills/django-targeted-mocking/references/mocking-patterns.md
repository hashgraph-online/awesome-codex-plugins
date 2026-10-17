# Mocking Patterns

## Settings

Use Django helpers so `setting_changed` fires and state is restored.

```python
from django.test import override_settings

@override_settings(PAGE_SIZE=10)
def test_page_size(client):
    ...
```

With pytest-django:

```python
def test_page_size(settings):
    settings.PAGE_SIZE = 10
    ...
```

## Output and Input

For management command output, pass file-like objects when the API supports it.

```python
out = io.StringIO()
call_command("my_command", stdout=out)
assert "done" in out.getvalue()
```

In pytest, use `capsys` for stdout/stderr capture.

## HTTP

Use `requests-mock` for direct, explicit response setup.

```python
def test_api_client(requests_mock):
    requests_mock.get("https://api.example.test/books", json={"items": []})
    assert fetch_books() == []
```

Block real outbound requests by default with a session-scoped fixture when the project uses `requests`.

```python
@pytest.fixture(autouse=True, scope="session")
def block_http():
    with requests_mock.Mocker() as mocker:
        mocker.real_http = False
        yield mocker
```

Use VCR.py when real responses are useful. Scrub secrets from cassettes and set CI to non-recording mode.

## Time

Prefer explicit time parameters in application code:

```python
def is_expired(record, now):
    return record.expires_at <= now
```

When that is not practical, use a time-specific package so all relevant time calls agree.

```python
import time_machine

@time_machine.travel("2026-06-14 12:00:00Z")
def test_deadline():
    ...
```

## Interface-Checked Mocks

Use specs when replacing an object with an expected API.

```python
with mock.patch("app.emailing.EmailClient", autospec=True) as client_cls:
    ...
```

For small interfaces, a fake object can be clearer than a mock.

```python
class FakeEmailClient:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)
```
