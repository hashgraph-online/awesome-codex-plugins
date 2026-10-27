import ipaddress
import os
import sys
from urllib.parse import urlparse

def _is_loopback(host):
    if host in ("localhost", ""):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def check_remote_endpoint(endpoint, label):
    """Reject cleartext transport to a remote host, and name the destination.

    Endpoints are read from config.yaml. Requests can carry screen-derived data
    or an API key, so remote endpoints must use HTTPS.
    """
    parsed = urlparse(endpoint)
    host = parsed.hostname or ""

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"{label} endpoint must be an http:// or https:// URL, got {endpoint!r}"
        )

    if parsed.scheme == "http" and not _is_loopback(host):
        raise ValueError(
            f"{label} endpoint {endpoint!r} uses plaintext HTTP to a remote host. "
            "Screen-derived content and your API key would cross the network "
            "unencrypted. Use https://, or point the endpoint at localhost."
        )

    if not _is_loopback(host):
        print(
            f"[autoskill] connecting to {parsed.scheme}://{host} for {label}",
            file=sys.stderr,
        )

    return endpoint


class ClaudeBackend:
    def __init__(self, api_key, model, client=None):
        if client is None:
            import httpx
            client = httpx.Client(base_url="https://api.anthropic.com", timeout=60.0)
        self.api_key = api_key
        self.model = model
        self.client = client

    def __call__(self, prompt):
        response = self.client.post(
            "/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["content"][0]["text"]


class LocalBackend:
    def __init__(self, endpoint, model, client=None):
        if client is None:
            import httpx
            client = httpx.Client(base_url=endpoint, timeout=120.0)
        self.endpoint = endpoint
        self.model = model
        self.client = client

    def __call__(self, prompt):
        response = self.client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]


def make_backend(config):
    kind = config.get("backend")
    if kind == "claude":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        model = config.get("claude", {}).get("model", "claude-opus-4-7")
        return ClaudeBackend(api_key=api_key, model=model)

    if kind == "foundry":
        import httpx
        api_key = os.environ.get("FOUNDRY_API_KEY")
        if not api_key:
            raise RuntimeError("FOUNDRY_API_KEY environment variable not set")
        f = config.get("foundry", {})
        endpoint = check_remote_endpoint(f["endpoint"], "foundry")
        client = httpx.Client(base_url=endpoint, timeout=60.0)
        return ClaudeBackend(api_key=api_key, model=f.get("model", "claude-opus-4-7"), client=client)

    if kind == "local":
        l = config.get("local", {})
        return LocalBackend(endpoint=check_remote_endpoint(l["endpoint"], "local"), model=l["model"])

    raise ValueError(f"unknown backend: {kind!r}")
