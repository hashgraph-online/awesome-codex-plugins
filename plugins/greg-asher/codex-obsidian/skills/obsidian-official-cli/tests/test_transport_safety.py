"""Malformed Unicode and inherited-output timeout regressions; no vault access."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import cli


class UnicodeSafetyTests(unittest.TestCase):
    def test_unpaired_surrogates_block_all_argument_positions_before_launch(self):
        for invalid in ['\ud800', '\udcff']:
            requests = [
                {'argv': ['vault=' + invalid, 'append', 'path=Note.md']},
                {'argv': ['append', 'path=' + invalid + '.md']},
                {'argv': ['property:set', 'path=Note.md', 'value=' + invalid]},
                {'argv': ['append', 'path=Note.md', 'content=' + invalid]},
                {'argv': ['append', 'path=Note.md'], 'content': invalid},
            ]
            for request in requests:
                with self.subTest(request=repr(request)):
                    output = io.StringIO()
                    with patch('cli.sys.stdin', io.StringIO(json.dumps(request))), \
                            patch('cli.subprocess.Popen') as launch, contextlib.redirect_stdout(output):
                        self.assertEqual(cli.main(), 1)
                    launch.assert_not_called()
                    report = json.loads(output.getvalue())
                    self.assertEqual(report['status'], 'launch-failed')
                    self.assertIn('unpaired Unicode surrogate', report['error'])

    def test_json_escaped_surrogate_blocks_in_real_helper_process(self):
        source = ('import sys; '
                  f'sys.path.insert(0, {str(SCRIPTS)!r}); import cli; '
                  'original=cli.command; '
                  'cli.command=lambda argv: [sys.executable,"-c","print(123)",'
                  '*original(argv, platform="linux")[1:]]; '
                  'sys.exit(cli.main())')
        # Even a broken validator can launch only a harmless recorder, never Obsidian.
        result = subprocess.run([sys.executable, '-B', '-c', source],
                                input=b'{"argv":["append","path=Note.md"],"content":"\\udcff"}',
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report['status'], 'launch-failed')
        self.assertIn('unpaired Unicode surrogate', report['error'])

    def test_emoji_and_non_bmp_arguments_reach_child_unchanged(self):
        request = {'argv': ['vault=verified-id', 'append', 'path=Notes/😀-𝄞.md'],
                   'content': 'Approved 😀 𝄞 東京'}
        child = 'import sys,json; print(json.dumps(sys.argv[1:]))'
        checked_command = cli.command
        def recorder(argv):
            validated = checked_command(argv, platform='linux')
            return [sys.executable, '-c', child, *validated[1:]]
        output = io.StringIO()
        # JSON serialization uses escaped surrogate pairs for valid non-BMP text.
        with patch('cli.command', side_effect=recorder), \
                patch('cli.sys.stdin', io.StringIO(json.dumps(request))), contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(), 0)
        report = json.loads(output.getvalue())
        self.assertEqual(json.loads(report['stdout']),
                         [*request['argv'], 'content=' + request['content']])


class CaptureSafetyTests(unittest.TestCase):
    def test_timeout_returns_while_descendant_still_holds_output_open(self):
        with tempfile.TemporaryDirectory() as directory:
            release = Path(directory) / 'release'
            ready = Path(directory) / 'ready'
            descendant = ('from pathlib import Path; import time; '
                          'print("descendant output", flush=True); '
                          f'Path({str(ready)!r}).write_text("ready"); '
                          f'release=Path({str(release)!r}); deadline=time.monotonic()+10; '
                          '\nwhile not release.exists() and time.monotonic()<deadline: time.sleep(0.02)')
            parent = ('import subprocess,sys,time; '
                      f'subprocess.Popen([sys.executable,"-c",{descendant!r}]); time.sleep(10)')
            source = '\n'.join([
                'import sys,time,threading,subprocess',
                f'sys.path.insert(0, {str(SCRIPTS)!r})',
                'import cli',
                'real_popen=subprocess.Popen',
                # Match the Windows blocking-reader behavior on POSIX too.
                # Native Windows uses its actual communicate implementation.
                'def launch(*args, **kwargs):',
                '    p=real_popen(*args, **kwargs)',
                '    deadline=time.monotonic()+5',
                f'    while not __import__("pathlib").Path({str(ready)!r}).exists():',
                '        if time.monotonic()>deadline: raise RuntimeError("descendant did not start")',
                '        time.sleep(0.01)',
                '    if sys.platform != "win32" and p.stdout is not None:',
                '        def communicate(timeout):',
                '            readers=[threading.Thread(target=s.read, daemon=True) for s in [p.stdout,p.stderr]]',
                '            for reader in readers: reader.start()',
                '            for reader in readers: reader.join(timeout)',
                '            if any(reader.is_alive() for reader in readers):',
                '                raise subprocess.TimeoutExpired(args[0],timeout)',
                '            return b"",b""',
                '        p.communicate=communicate',
                '    return p',
                'cli.subprocess.Popen=launch',
                'cli.COMMAND_TIMEOUT=0.1',
                f'cli.command=lambda argv: [sys.executable,"-c",{parent!r}]',
                'sys.exit(cli.main())',
            ])
            helper = subprocess.Popen([sys.executable, '-B', '-c', source],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                out, err = helper.communicate(b'{"argv":["version"]}', timeout=5)
                self.assertEqual(helper.returncode, 2, err)
                report = json.loads(out)
                self.assertEqual(report['status'], 'uncertain')
                self.assertIn('descendant output', report['stdout'])
                self.assertTrue(ready.exists())
                self.assertFalse(release.exists())  # no EOF from descendant was needed
            finally:
                release.touch()
                if helper.poll() is None:
                    try:
                        helper.communicate(timeout=3)
                    except subprocess.TimeoutExpired:
                        helper.kill()
                        helper.communicate(timeout=3)

    def test_capture_read_does_not_move_live_writer_offset(self):
        with tempfile.NamedTemporaryFile(buffering=0) as stream:
            stream.write(b'original')
            offset = stream.tell()
            self.assertEqual(cli.read_capture(stream, 32), ('original', False))
            self.assertEqual(stream.tell(), offset)
            stream.write(b' later')
            self.assertEqual(stream.tell(), len(b'original later'))

    def test_output_limit_is_explicit_and_not_success_evidence(self):
        output = io.StringIO()
        child = 'import sys; sys.stdout.buffer.write(b"x"*65)'
        with patch('cli.command', return_value=[sys.executable, '-c', child]), \
                patch('cli.MAX_CAPTURE_BYTES', 32), \
                patch('cli.sys.stdin', io.StringIO('{"argv":["read","path=Note.md"]}')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'process-completed')
        self.assertEqual(report['stdout'], 'x' * 32)
        self.assertTrue(report['stdout_truncated'])

    def test_request_limit_caps_both_streams_by_bytes(self):
        child = ('import sys; data = "ééé".encode("utf-8"); '
                 'sys.stdout.buffer.write(data); sys.stderr.buffer.write(data)')
        output = io.StringIO()
        request = json.dumps({'argv': ['read', 'path=Atlas.md'], 'capture_limit': 4})
        with patch('cli.command', return_value=[sys.executable, '-c', child]), \
                patch('cli.sys.stdin', io.StringIO(request)), contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(), 2)
        report = json.loads(output.getvalue())
        for stream in ('stdout', 'stderr'):
            self.assertEqual(report[stream], 'éé')
            self.assertTrue(report[stream + '_truncated'])

    def test_invalid_request_limits_fail_before_launch(self):
        for limit in (False, None, '4', 4.0, 0, -1, cli.MAX_CAPTURE_BYTES + 1):
            with self.subTest(limit=limit):
                output = io.StringIO()
                request = json.dumps({'argv': ['version'], 'capture_limit': limit})
                with patch('cli.sys.stdin', io.StringIO(request)), \
                        patch('cli.subprocess.Popen') as launch, contextlib.redirect_stdout(output):
                    self.assertEqual(cli.main(), 1)
                launch.assert_not_called()
                self.assertIn('capture_limit must be an integer', json.loads(output.getvalue())['error'])

    def test_cleanup_errors_cannot_replace_timeout_evidence(self):
        for failure in [PermissionError('kill blocked'), subprocess.TimeoutExpired('stub', 1)]:
            with self.subTest(failure=type(failure).__name__):
                process = Mock()
                process.communicate.side_effect = subprocess.TimeoutExpired('stub', 30)
                if isinstance(failure, PermissionError):
                    process.kill.side_effect = failure
                else:
                    process.wait.side_effect = failure
                output = io.StringIO()
                with patch('cli.command', return_value=['stub']), \
                        patch('cli.subprocess.Popen', return_value=process), \
                        patch('cli.sys.stdin', io.StringIO('{"argv":["append"]}')), \
                        contextlib.redirect_stdout(output):
                    self.assertEqual(cli.main(), 2)
                report = json.loads(output.getvalue())
                self.assertEqual(report['status'], 'uncertain')
                self.assertIn('cleanup_error', report)
                if not isinstance(failure, PermissionError):
                    process.wait.assert_called_once_with(timeout=cli.CLEANUP_TIMEOUT)

    def test_capture_failure_preserves_completed_process_evidence(self):
        output = io.StringIO()
        with patch('cli.command', return_value=[sys.executable, '-c', 'pass']), \
                patch('cli.read_capture', side_effect=OSError('capture unavailable')), \
                patch('cli.sys.stdin', io.StringIO('{"argv":["append"]}')), \
                contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'process-completed')
        self.assertEqual(report['returncode'], 0)
        self.assertEqual(report['capture_error'], 'capture unavailable')


if __name__ == '__main__':
    unittest.main()
