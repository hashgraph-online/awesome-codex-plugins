"""Structured errors and diagnostics for Perform."""


def unicode_sort_key(value):
    """Encode one string into a deterministic surrogate-safe sort key."""
    return value.encode("utf-8", errors="surrogatepass")


class PerformRequestError(ValueError):
    """A Perform operation cannot safely fulfill the caller's request."""

    def __init__(self, status, message, alternatives=None, diagnostics=None):
        """Store stable request status, explanation, alternatives, and catalog diagnostics."""
        super().__init__(message)
        self.status = status
        self.message = message
        self.alternatives = list(alternatives or [])
        self.diagnostics = list(diagnostics or [])


class Diagnostic:
    """One deterministic catalog or discovery issue."""

    __slots__ = (
        "code",
        "fatality",
        "filename_sort_key",
        "json_path",
        "message",
        "selector",
        "severity",
        "source_file",
        "source_order",
    )

    def __init__(
        self,
        severity,
        code,
        message,
        source_file=None,
        json_path=None,
        selector=None,
        fatality="nonfatal",
        source_order=-1,
        filename_sort_key=b"",
    ):
        """Store diagnostic content and its deterministic ordering metadata."""
        self.severity = severity
        self.code = code
        self.message = message
        self.source_file = source_file
        self.json_path = json_path
        self.selector = selector
        self.fatality = fatality
        self.source_order = source_order
        self.filename_sort_key = filename_sort_key

    @property
    def fatal(self):
        """Return whether this issue makes catalog precedence incomplete."""
        return self.fatality == "catalog_fatal"

    def sort_key(self):
        """Return the stable diagnostic ordering key."""
        return (
            self.source_order,
            self.filename_sort_key,
            unicode_sort_key(self.json_path or ""),
            self.code.encode("ascii"),
            unicode_sort_key(self.message),
        )

    def identity(self):
        """Return content used to deduplicate repeated dependent errors."""
        return (
            self.severity,
            self.code,
            self.message,
            self.source_file,
            self.json_path,
            self.selector,
            self.fatality,
        )


def json_pointer_component(value):
    """Escape one value for a JSON pointer component."""
    return value.replace("~", "~0").replace("/", "~1")


def sorted_unique_diagnostics(diagnostics):
    """Deduplicate diagnostics and return them in deterministic order."""
    unique = {}
    for diagnostic in diagnostics:
        key = diagnostic.identity()
        previous = unique.get(key)
        if previous is None or diagnostic.sort_key() < previous.sort_key():
            unique[key] = diagnostic
    return sorted(unique.values(), key=lambda diagnostic: diagnostic.sort_key())
