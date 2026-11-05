#!/usr/bin/env python3
"""Launch official Obsidian argv supplied as JSON on stdin. No workflow decisions."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

from json_protocol import emit_report, read_request

COMMAND_TIMEOUT = 30
CLEANUP_TIMEOUT = 1
MAX_CAPTURE_BYTES = 1024 * 1024

SANITIZE = ('unset __CFBundleIdentifier LaunchInstanceID XPC_SERVICE_NAME '
            'CODEX_CI CODEX_SANDBOX CODEX_SHELL; export TERM=xterm-256color; ')


def command(argv, platform=sys.platform, environ=None):
    if not isinstance(argv, list) or not argv or any(
        not isinstance(arg, str) or '\0' in arg for arg in argv
    ):
        raise ValueError('argv must be a nonempty JSON array of NUL-free strings')
    for arg in argv:
        try:
            arg.encode('utf-8')
        except UnicodeEncodeError as error:
            raise ValueError('argv contains an unpaired Unicode surrogate; use valid Unicode text') from error
    if platform == 'win32':
        redirector = shutil.which('Obsidian.com')
        if not redirector:
            raise ValueError('Obsidian.com terminal redirector not found on PATH; '
                             'install Obsidian 1.12.7+, enable/register its CLI, '
                             'and restart the terminal')
        return [redirector, *argv]
    if platform != 'darwin':
        return ['obsidian', *argv]
    env = os.environ if environ is None else environ
    shell = env.get('CODEX_OBSIDIAN_ZSH_PATH') or '/usr/local/bin/zsh'
    if not Path(shell).is_absolute() or not os.access(shell, os.X_OK):
        raise ValueError('Set CODEX_OBSIDIAN_ZSH_PATH to an absolute executable Zsh path '
                         '(for example /bin/zsh), then retry the read-only probe')
    # shlex.join quotes every untrusted argument, including embedded apostrophes.
    return ['script', '-q', '/dev/null', shell, '-ilc',
            SANITIZE + shlex.join(['obsidian', *argv])]


def content_argument(text):
    """Encode only the documented CLI newline/tab sequences; reject ambiguity."""
    if not isinstance(text, str) or '\0' in text or '\r' in text:
        raise ValueError('content must be NUL-free LF text; CR/CRLF transport is unverified')
    if '\\n' in text or '\\t' in text:
        raise ValueError('literal backslash-n/backslash-t transport is unverified; do not write')
    return 'content=' + text.replace('\n', '\\n').replace('\t', '\\t')


def stop_launcher(process, report):
    # Descendants/app-side work may still complete; this never proves quiescence.
    try:
        process.kill()
        process.wait(timeout=CLEANUP_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        report['cleanup_error'] = str(error)


def read_capture(stream):
    # A separate open preserves the writer's offset if a descendant is alive.
    # Windows temporary files require delete-sharing on this additional handle.
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_TEMPORARY', 0)
    with os.fdopen(os.open(stream.name, flags), 'rb') as reader:
        data = reader.read(MAX_CAPTURE_BYTES + 1)
    return data[:MAX_CAPTURE_BYTES].decode('utf-8', errors='replace'), len(data) > MAX_CAPTURE_BYTES


def execute(launch):
    report = None
    exit_code = 1
    try:
        # File capture needs neither pipe EOF nor Windows reader-thread cleanup.
        # Private delete-on-close files stay outside the installed plugin cache.
        with tempfile.NamedTemporaryFile(buffering=0) as stdout, tempfile.NamedTemporaryFile(buffering=0) as stderr:
            try:
                process = subprocess.Popen(launch, stdout=stdout, stderr=stderr)
            except (OSError, ValueError, TypeError) as error:
                report = {'status': 'launch-failed', 'error': str(error)}
            else:
                try:
                    process.communicate(timeout=COMMAND_TIMEOUT)
                    report = {'status': 'process-completed', 'returncode': process.returncode}
                    exit_code = 0 if process.returncode == 0 else 1
                except subprocess.TimeoutExpired:
                    report = {'status': 'uncertain',
                              'error': f'{COMMAND_TIMEOUT}-second timeout; inspect state and establish original completion before retry'}
                    exit_code = 2
                    stop_launcher(process, report)
                except OSError as error:
                    report = {'status': 'uncertain',
                              'error': 'Error after process creation; inspect state before retry: ' + str(error)}
                    exit_code = 2
                    stop_launcher(process, report)
                for name, stream in [('stdout', stdout), ('stderr', stderr)]:
                    report[name], truncated = read_capture(stream)
                    if truncated:
                        report[name + '_truncated'] = True
                        exit_code = 2
    except OSError as error:
        if report is None:
            report = {'status': 'launch-failed', 'error': str(error)}
        else:
            # Never lose dispatch/completion evidence to capture/cleanup errors.
            report['capture_error'] = str(error)
            exit_code = 2
    return report, exit_code


def main():
    try:
        request = read_request()
        if not isinstance(request, dict) or set(request) - {'argv', 'content'}:
            raise ValueError('expected {"argv": [...], "content": optional literal text}')
        argv = request.get('argv')
        if not isinstance(argv, list) or not argv:
            raise ValueError('argv must include the requested CLI command')
        if 'content' in request:
            if not isinstance(argv, list) or any(
                isinstance(a, str) and a.startswith('content=') for a in argv
            ):
                raise ValueError('provide content once, separately from argv')
            argv = [*argv, content_argument(request['content'])]
        launch = command(argv)
    except (OSError, ValueError, TypeError) as error:
        return emit_report({'status': 'launch-failed', 'error': str(error)}, 1)
    report, exit_code = execute(launch)
    # A zero exit from Obsidian or its launcher never proves a completed write.
    return emit_report(report, exit_code)


if __name__ == '__main__':
    sys.exit(main())
