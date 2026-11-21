"""Process/locale and diff regression checks. Children never access a vault."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import cli
import revision


class ProtocolRegressionTests(unittest.TestCase):
    def child(self, module, request, codec, source=None):
        env = {**os.environ, 'PYTHONIOENCODING': codec, 'PYTHONDONTWRITEBYTECODE': '1'}
        args = [sys.executable, '-B', str(SCRIPTS / (module + '.py'))]
        if source is not None:
            args = [sys.executable, '-B', '-c', source]
        return subprocess.run(args, input=json.dumps(request, ensure_ascii=False).encode('utf-8'),
                              capture_output=True, env=env, timeout=10)

    def cli_child(self, request, codec, marker, stdout='東京', stderr='échec'):
        # Patch only executable selection; run an actual argv-recording child.
        # Use ASCII Python source so it cannot depend on the test locale either.
        child = ('from pathlib import Path; import json,sys; '
                 f'Path({str(marker)!r}).write_text(json.dumps(sys.argv[1:]), encoding="utf-8"); '
                 f'sys.stdout.buffer.write({stdout.encode("utf-8")!r}); '
                 f'sys.stderr.buffer.write({stderr.encode("utf-8")!r})')
        source = ('import sys; '
                  f'sys.path.insert(0, {str(SCRIPTS)!r}); import cli; '
                  f'cli.command = lambda argv: [sys.executable, "-c", {child!r}, *argv]; '
                  'sys.exit(cli.main())')
        return self.child('cli', request, codec, source)

    def test_utf8_cli_request_survives_cp1252_and_ascii_streams(self):
        request = {'argv': ['vault=id', 'append', 'path=Projects/Café.md'],
                   'content': "Café 東京 O'Brien `$budget`\nnext"}
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'received.json'
            for codec in ['cp1252', 'ascii']:
                with self.subTest(codec=codec):
                    result = self.cli_child(request, codec, marker)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(marker.read_text(encoding='utf-8')),
                                     [*request['argv'], cli.content_argument(request['content'])])
                    report = json.loads(result.stdout)
                    self.assertEqual(report['status'], 'process-completed')
                    self.assertEqual(report['stdout'], '東京')
                    self.assertEqual(report['stderr'], 'échec')
                    result.stdout.decode('ascii')  # report transports Unicode via JSON escapes

    def test_utf8_revision_request_and_fingerprints_are_locale_independent(self):
        request = {'before': '# Café\n東京 old\n', 'old': 'old', 'new': 'révisé'}
        expected = revision.preview(**request)
        for codec in ['cp1252', 'ascii']:
            with self.subTest(codec=codec):
                result = self.child('revision', request, codec)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected)
                result.stdout.decode('ascii')

    def test_invalid_utf8_blocks_before_launch(self):
        source = ('import sys; '
                  f'sys.path.insert(0, {str(SCRIPTS)!r}); import cli; '
                  'cli.command = lambda argv: (_ for _ in ()).throw(AssertionError("must not launch")); '
                  'sys.exit(cli.main())')
        result = subprocess.run([sys.executable, '-B', '-c', source],
                                input=b'{"argv":["append"],"content":"\xff"}',
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'launch-failed')

    def test_completed_effect_is_not_relabelled_when_report_stdout_breaks(self):
        class BrokenStdout(io.StringIO):
            def write(self, text):
                raise BrokenPipeError('report channel closed')

        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'effect.txt'
            child = ('from pathlib import Path; import sys; '
                     f'Path({str(marker)!r}).write_text("applied", encoding="utf-8"); '
                     'sys.stdout.buffer.write("東京".encode("utf-8"))')
            errors = io.StringIO()
            with patch('cli.sys.stdin', io.StringIO('{"argv":["append"]}')), \
                    patch('cli.command', return_value=[sys.executable, '-c', child]), \
                    contextlib.redirect_stdout(BrokenStdout()), contextlib.redirect_stderr(errors):
                code = cli.main()
            report = json.loads(errors.getvalue())
            self.assertEqual(marker.read_text(encoding='utf-8'), 'applied')
            self.assertEqual(code, 2)
            self.assertEqual(report['status'], 'process-completed')
            self.assertEqual(report['returncode'], 0)
            self.assertEqual(report['stdout'], '東京')
            self.assertIn('report channel closed', report['report_error'])

    def test_process_launch_failure_is_distinct_from_post_dispatch_io_error(self):
        for failure, status, code in [(True, 'launch-failed', 1), (False, 'uncertain', 2)]:
            with self.subTest(launch_failure=failure):
                output = io.StringIO()
                process = Mock()
                process.communicate.side_effect = OSError('pipe read failed')
                with patch('cli.sys.stdin', io.StringIO('{"argv":["append"]}')), \
                        patch('cli.command', return_value=['stub']), \
                        patch('cli.subprocess.Popen', side_effect=FileNotFoundError('not installed') if failure else None,
                              return_value=process), contextlib.redirect_stdout(output):
                    self.assertEqual(cli.main(), code)
                self.assertEqual(json.loads(output.getvalue())['status'], status)

    def test_timeout_cleans_up_launcher_but_retains_uncertainty(self):
        output = io.StringIO()
        process = Mock()
        process.communicate.side_effect = subprocess.TimeoutExpired('stub', 30, output=b'partial')
        def launch(*args, **kwargs):
            kwargs['stdout'].write(b'partial')
            return process
        with patch('cli.sys.stdin', io.StringIO('{"argv":["append"]}')), \
                patch('cli.command', return_value=['stub']), \
                patch('cli.subprocess.Popen', side_effect=launch), contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(), 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report['status'], 'uncertain')
        self.assertEqual(report['stdout'], 'partial')
        process.communicate.assert_called_once_with(timeout=30)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=cli.CLEANUP_TIMEOUT)
        # No pipe streams/readers are created or synchronously closed.
        process.stdout.close.assert_not_called()
        process.stderr.close.assert_not_called()


class WindowsRegressionTests(unittest.TestCase):
    def test_redirector_resolves_explicitly_and_preserves_argv(self):
        args = ['vault=id', 'append', 'path=Projects/Café.md', 'content=$x `id`']
        redirector = r'C:\Program Files\Obsidian\Obsidian.com'
        with patch('cli.shutil.which', return_value=redirector) as which:
            self.assertEqual(cli.command(args, platform='win32'), [redirector, *args])
        which.assert_called_once_with('Obsidian.com')

    def test_missing_redirector_blocks_without_gui_fallback(self):
        with patch('cli.shutil.which', return_value=None) as which:
            with self.assertRaisesRegex(ValueError, 'Obsidian.com terminal redirector not found'):
                cli.command(['version'], platform='win32')
        which.assert_called_once_with('Obsidian.com')


class DiffRegressionTests(unittest.TestCase):
    CASES = ['\u0085', '\u2028', '\u2029', '\v', '\f', '\x1c', '\x1d', '\x1e', '\r']

    def test_unicode_and_control_separators_remain_line_content(self):
        for separator in self.CASES:
            with self.subTest(separator=repr(separator)):
                before = 'first' + separator + 'old\nnext\n'
                plan = revision.preview(before, 'old', 'new')
                self.assertEqual(plan['content'], before.replace('old', 'new'))
                self.assertIn('@@ -1,2 +1,2 @@\n', plan['diff'])
                self.assertIn('-first' + separator + 'old\n', plan['diff'])
                self.assertIn('+first' + separator + 'new\n', plan['diff'])
                self.assertNotIn('No newline at end of file', plan['diff'])

    @unittest.skipUnless(shutil.which('patch'), 'optional patch utility unavailable')
    def test_diff_applies_to_exact_candidate_with_unicode_and_eof_variants(self):
        cases = ['first' + separator + 'old\nnext' + ending
                 for separator in self.CASES for ending in ['', '\n']]
        cases += ['first\r\nold\r\nnext\r\n', 'old', 'old\n']
        with tempfile.TemporaryDirectory() as directory:
            note, change = Path(directory) / 'note.md', Path(directory) / 'change.diff'
            for before in cases:
                with self.subTest(before=repr(before)):
                    plan = revision.preview(before, 'old', 'new')
                    note.write_bytes(before.encode('utf-8'))
                    change.write_bytes(plan['diff'].encode('utf-8'))
                    result = subprocess.run([shutil.which('patch'), str(note), str(change)],
                                            capture_output=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(note.read_bytes(), plan['content'].encode('utf-8'))


if __name__ == '__main__':
    unittest.main()
