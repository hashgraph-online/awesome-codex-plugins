"""Locale-independent JSON streams shared by the command-line helpers."""
import json
import sys


def read_request():
    # Binary input avoids decoding a UTF-8 file using the system ANSI codepage.
    # StringIO support is useful for callers that already supplied decoded text.
    data = getattr(sys.stdin, 'buffer', sys.stdin).read()
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def emit_report(report, exit_code):
    # ASCII JSON escapes preserve Unicode on every supported text stream codec.
    payload = json.dumps(report, ensure_ascii=True)
    try:
        print(payload, flush=True)
    except (OSError, UnicodeError) as error:
        # Reporting is separate from execution: never relabel a completed or
        # possibly dispatched command as a launch failure because stdout broke.
        fallback = dict(report, report_error=str(error))
        try:
            print(json.dumps(fallback, ensure_ascii=True), file=sys.stderr, flush=True)
        except (OSError, UnicodeError):
            pass  # No report channel remains; a nonzero exit must not invite retry.
        return 2
    return exit_code
