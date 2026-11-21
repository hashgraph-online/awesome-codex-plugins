"""Command-line transport for the Perform entry scripts."""

import argparse
import io
import sys

from . import api
from . import catalog as catalog_module
from . import paths as paths_module
from .diagnostics import PerformRequestError

_SEEN_ARGUMENTS_ATTRIBUTE = "_json_argument_parser_seen"


class _StoreOnceAction(argparse.Action):
    """Store one option value while rejecting repeated occurrences."""

    def __call__(self, parser, namespace, values, option_string=None):
        """Record one supplied destination and reject later occurrences."""
        seen = getattr(namespace, _SEEN_ARGUMENTS_ATTRIBUTE, None)
        if seen is None:
            seen = set()
            setattr(namespace, _SEEN_ARGUMENTS_ATTRIBUTE, seen)
        if self.dest in seen:
            parser.error("argument {}: may not be repeated".format(option_string))
        seen.add(self.dest)
        setattr(namespace, self.dest, self.const if self.nargs == 0 else values)


class JsonArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports invalid invocations as compact JSON."""

    def __init__(self, *args, **kwargs):
        """Disable abbreviations and register the store-once option action."""
        kwargs["allow_abbrev"] = False
        super().__init__(*args, **kwargs)
        self.register("action", "store_once", _StoreOnceAction)

    def parse_args(self, args=None, namespace=None):
        """Return JSON help immediately when an exact help flag is present."""
        arguments = list(sys.argv[1:] if args is None else args)
        if any(argument in ("-h", "--help") for argument in arguments):
            self.print_help()
            raise SystemExit(0)
        return super().parse_args(arguments, namespace)

    def parse_known_args(self, args=None, namespace=None):
        """Parse arguments and discard private duplicate-tracking state."""
        if namespace is None:
            namespace = argparse.Namespace()
        try:
            return super().parse_known_args(args, namespace)
        finally:
            if hasattr(namespace, _SEEN_ARGUMENTS_ATTRIBUTE):
                delattr(namespace, _SEEN_ARGUMENTS_ATTRIBUTE)

    def print_help(self, file=None):
        """Emit argparse-formatted help inside one compact JSON value."""
        emit_json({"help": self.format_help()}, stream=file)

    def error(self, message):
        """Emit one machine-readable argument error and stop."""
        emit_json(api.error_payload("invalid_arguments", message))
        raise SystemExit(2)


class CliOutcome:
    """Normal result and optional request error returned by one CLI command."""

    __slots__ = ("error", "result")

    def __init__(self, result=None, error=None):
        """Store an optional result and Perform request error."""
        if result is not None and not isinstance(result, dict):
            raise TypeError("result must be a dictionary or None")
        if error is not None and not isinstance(error, PerformRequestError):
            raise TypeError("error must be a PerformRequestError or None")
        self.result = result
        self.error = error


class CliContext:
    """Catalog state accumulated while running one CLI command."""

    __slots__ = ("catalog",)

    def __init__(self):
        """Start without a loaded catalog."""
        self.catalog = None

    def load_catalog(self, cwd):
        """Load and retain the conventional Perform catalog."""
        self.catalog = catalog_module.load_action_catalog(bundled_dir=paths_module.bundled_actions_dir(), cwd=cwd)
        return self.catalog


def encode_json(value):
    """Encode one compact JSON value and trailing newline as valid UTF-8."""
    return (api.compact_json(value) + "\n").encode("utf-8", errors="backslashreplace")


def _write_encoded_json(encoded, stream=None):
    """Write pre-encoded JSON once to a standard text or binary stream."""
    if stream is None:
        sys.stdout.buffer.write(encoded)
    elif hasattr(stream, "buffer"):
        stream.buffer.write(encoded)
    elif isinstance(stream, io.TextIOBase):
        stream.write(encoded.decode("utf-8"))
    else:
        stream.write(encoded)


def emit_json(value, stream=None):
    """Write one compact JSON value to a standard text or binary stream."""
    _write_encoded_json(encode_json(value), stream=stream)


def _exception_message(exc):
    """Render an exception without risking another response failure."""
    try:
        return str(exc)
    except Exception:
        return "The runtime failure could not be rendered."


def run_cli(command):
    """Run one command callback and emit its sole machine response."""
    context = CliContext()
    try:
        outcome = command(context)
        if not isinstance(outcome, CliOutcome):
            raise TypeError("command must return a CliOutcome")
    except PerformRequestError as exc:
        outcome = CliOutcome(error=exc)
    except Exception as exc:
        outcome = CliOutcome(error=PerformRequestError("runtime_error", _exception_message(exc)))
    exit_code = 0 if outcome.error is None else api.error_exit_code(outcome.error.status)
    try:
        if context.catalog is None:
            payload = api.merge_response_payload(result=outcome.result, error=outcome.error)
        else:
            payload = api.response_payload(context.catalog, result=outcome.result, error=outcome.error)
        encoded = encode_json(payload)
    except Exception as exc:
        encoded = encode_json(api.error_payload("runtime_error", _exception_message(exc)))
        exit_code = 4
    _write_encoded_json(encoded)
    return exit_code


__all__ = (
    "CliContext",
    "CliOutcome",
    "JsonArgumentParser",
    "emit_json",
    "encode_json",
    "run_cli",
)
