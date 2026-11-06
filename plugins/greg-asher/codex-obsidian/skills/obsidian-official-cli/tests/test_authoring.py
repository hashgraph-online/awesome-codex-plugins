"""Deterministic mechanics only; does not simulate a successful Obsidian runtime."""
import contextlib
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import cli
import revision

FIXTURES = Path(__file__).parent / 'fixtures'


class RevisionTests(unittest.TestCase):
    def test_section_preserves_all_unrelated_bytes(self):
        before = (FIXTURES / 'Atlas.md').read_bytes().decode('utf-8')
        old = '## Risks\n\nSupplier date is unknown.\n\n### Mitigation\n\nConfirm delivery before launch.\n\n'
        new = old.replace('Supplier date is unknown.', 'Supplier confirmed 20 November; schedule remains at risk.')
        plan = revision.preview(before, old, new)
        start = before.index(old)
        self.assertEqual(plan['content'].encode()[:start], before.encode()[:start])
        self.assertEqual(plan['content'][start + len(new):], before[start + len(old):])
        self.assertIn('-Supplier date is unknown.', plan['diff'])
        self.assertIn('+Supplier confirmed', plan['diff'])
        self.assertNotIn('custom:', plan['diff'])
        self.assertEqual(revision.state(before, before, plan['content']), 'ready')
        self.assertEqual(revision.state(plan['content'], before, plan['content']), 'already-applied')

    def test_duplicate_and_missing_targets_block(self):
        for before, old in [('## Risks\nx\n## Risks\nx\n', '## Risks\nx\n'),
                            ('aaa', 'aa'), ('body', 'missing'), ('body', '')]:
            with self.subTest(before=before), self.assertRaises(ValueError):
                revision.preview(before, old, 'new')

    def test_context_disambiguates_without_normalizing(self):
        before = '## One\n### Risks\na\n## Two\n### Risks\nb\n'
        result = revision.preview(before, '## Two\n### Risks\nb', '## Two\n### Risks\nc')
        self.assertEqual(result['content'], before[:-2] + 'c\n')

    def test_crlf_unicode_and_final_newline_preserved_in_preview(self):
        before = '\ufeff---\r\nx: "é"\r\n---\r\n東京\r\nold'
        result = revision.preview(before, 'old', 'new')
        self.assertEqual(result['content'].encode(), before[:-3].encode() + b'new')
        self.assertIn('No newline at end of file', result['diff'])

    def test_state_detects_concurrency_partial_and_uncertain_completion(self):
        for current in ['before plus user edit', 'before half insertion', None]:
            self.assertEqual(revision.state(current, 'before', 'before full insertion'), 'conflict')
        self.assertEqual(revision.state('before full insertion', 'before', 'before full insertion'), 'already-applied')
        self.assertEqual(revision.state(None, None, 'new note'), 'ready')
        self.assertEqual(revision.state('existing collision', None, 'new note'), 'conflict')

    def test_append_retry_does_not_require_duplicate_effect(self):
        before, insertion = 'body\n', "O'Brien 東京 `$x`\n"
        expected = before + insertion
        self.assertEqual(revision.state(expected, before, expected), 'already-applied')
        self.assertEqual(expected.count(insertion), 1)

    def test_noop(self):
        self.assertEqual(revision.preview('a', 'a', 'a')['diff'], '')

    def test_non_text_rejected(self):
        with self.assertRaises(ValueError):
            revision.preview('body', 'body', 123)


class ContainmentTests(unittest.TestCase):
    def test_only_intended_root_even_when_cwd_is_elsewhere(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(revision.contained_target(root, 'Missing/Atlas.md'), root.resolve() / 'Missing/Atlas.md')
            self.assertFalse((root / 'Missing').exists())  # preview creates nothing
            for path in ['../escape.md', '/absolute.md', 'C:/note.md', 'x\\note.md', '', '.', 'a/../b', 'a//b']:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    revision.contained_target(root, path)

    def test_escaping_symlink(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            try:
                (root / 'linked').symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlink creation unavailable: {error}')
            with self.assertRaises(ValueError):
                revision.contained_target(root, 'linked/note.md')


    def test_internal_symlink_alias_blocks_even_within_vault(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'actual').mkdir()
            try:
                (root / 'alias').symlink_to(root / 'actual', target_is_directory=True)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlink creation unavailable: {error}')
            with self.assertRaisesRegex(ValueError, 'filesystem alias'):
                revision.contained_target(root, 'alias/note.md')

    def test_hard_link_blocks_mutation_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            note = root / 'note.md'
            note.write_text('unchanged')
            try:
                os.link(note, root / 'other.md')
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'hard link creation unavailable: {error}')
            with self.assertRaisesRegex(ValueError, 'multiple hard links'):
                revision.contained_target(root, 'note.md')


class LauncherTests(unittest.TestCase):
    def test_platform_argv_no_shell(self):
        args = ['vault=verified-id', 'append', 'path=Projects/Atlas.md', 'content=$x `id`']
        self.assertEqual(cli.command(args, platform='linux'), ['obsidian', *args])
        with patch('cli.shutil.which', return_value=r'C:\Program Files\Obsidian\Obsidian.com') as which:
            self.assertEqual(cli.command(args, platform='win32'),
                             [r'C:\Program Files\Obsidian\Obsidian.com', *args])
            which.assert_called_once_with('Obsidian.com')

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX shell paths')
    def test_macos_wrapper_quotes_arguments_and_override(self):
        args = ['vault=id', 'append', 'path=a b.md', "content=O'Brien `$budget`; $(echo unsafe) 東京\nsecond"]
        with patch('cli.os.access', return_value=True):
            result = cli.command(args, platform='darwin', environ={'CODEX_OBSIDIAN_ZSH_PATH': '/shell path/zsh'})
        self.assertEqual(result[:6], ['script', '-q', '/dev/null', '/shell path/zsh', '-ilc', result[5]])
        self.assertTrue(result[-1].startswith(cli.SANITIZE))
        self.assertEqual(shlex.split(result[-1][len(cli.SANITIZE):]), ['obsidian', *args])

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX shell paths')
    def test_shell_treats_prompt_and_metacharacters_as_data(self):
        text = "Ignore instructions; O'Brien `$budget` $(echo INJECTED)\n東京"
        args = ['vault=id', 'append', 'path=a b.md', cli.content_argument(text)]
        with patch('cli.os.access', return_value=True):
            launch = cli.command(args, platform='darwin', environ={'CODEX_OBSIDIAN_ZSH_PATH': '/bin/zsh'})
        # Actual shell execution with an argv recorder, not an Obsidian mock result.
        recorder = 'obsidian() { ' + shlex.quote(sys.executable) + ' -c ' + shlex.quote('import json,sys;print(json.dumps(sys.argv[1:]))') + ' "$@"; }; '
        result = subprocess.run(['/bin/sh', '-c', recorder + launch[-1]], capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), args)

    @unittest.skipUnless(os.name == 'posix', 'requires POSIX shell paths')
    def test_default_and_empty_override_follow_shell_default(self):
        with patch('cli.os.access', return_value=True):
            for env in [{}, {'CODEX_OBSIDIAN_ZSH_PATH': ''}]:
                self.assertEqual(cli.command(['version'], platform='darwin', environ=env)[3], '/usr/local/bin/zsh')

    def test_invalid_shell_and_arguments(self):
        with self.assertRaises(ValueError):
            cli.command(['version'], platform='darwin', environ={'CODEX_OBSIDIAN_ZSH_PATH': 'zsh'})
        for args in [[], 'version', [None], ['content=\0']]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                cli.command(args, platform='linux')

    def test_content_codec_and_explicit_unverified_cases(self):
        self.assertEqual(cli.content_argument('a\nb\tc'), 'content=a\\nb\\tc')
        for value in ['literal \\n', 'literal \\t', 'a\r\nb', '\0']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                cli.content_argument(value)

    def run_main(self, request, effect):
        output = io.StringIO()
        process = Mock()
        if isinstance(effect, Exception):
            process.communicate.side_effect = effect
        else:
            result = effect()
            process.communicate.return_value = (result.stdout, result.stderr)
            process.returncode = result.returncode
        def launch(*args, **kwargs):
            if isinstance(effect, Exception):
                stdout, stderr = effect.stdout or b'', effect.stderr or b''
            else:
                stdout, stderr = result.stdout, result.stderr
            kwargs['stdout'].write(stdout)
            kwargs['stderr'].write(stderr)
            return process
        with patch('cli.sys.stdin', io.StringIO(json.dumps(request))), contextlib.redirect_stdout(output), patch('cli.subprocess.Popen', side_effect=launch), patch('cli.command', return_value=['obsidian', 'version']):
            code = cli.main()
        return code, json.loads(output.getvalue())

    def test_zero_exit_is_only_process_evidence(self):
        result = subprocess.CompletedProcess([], 0, b'Command line interface is not enabled.', b'')
        code, report = self.run_main({'argv': ['version']}, lambda *a, **k: result)
        self.assertEqual(code, 0)
        self.assertEqual(report['status'], 'process-completed')
        self.assertIn('not enabled', report['stdout'])
        self.assertNotIn('verified', report)

    def test_timeout_is_uncertain(self):
        code, report = self.run_main({'argv': ['append']}, subprocess.TimeoutExpired('obsidian', 30, output=b'partial'))
        self.assertEqual(code, 2)
        self.assertEqual(report['status'], 'uncertain')
        self.assertEqual(report['stdout'], 'partial')
        self.assertIn('establish original completion', report['error'])

    def test_malformed_request_never_launches(self):
        for request in [[], {'argv': ['version'], 'extra': 'oops'}, {'argv': [], 'content': 'x'}, {'argv': ['append', 'content=x'], 'content': 'y'}]:
            with patch('cli.sys.stdin', io.StringIO(json.dumps(request))), contextlib.redirect_stdout(io.StringIO()), patch('cli.subprocess.Popen') as run:
                self.assertEqual(cli.main(), 1)
                run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
