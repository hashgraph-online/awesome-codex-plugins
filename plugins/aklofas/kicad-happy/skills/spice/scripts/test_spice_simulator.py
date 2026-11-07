#!/usr/bin/env python3
"""Unit tests for SPICE simulator selection and external-deck execution."""

import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from types import SimpleNamespace
from unittest.mock import call, patch

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import spice_simulator  # noqa: E402
import run_external_deck  # noqa: E402


class TestExternalDeckCliSurface(unittest.TestCase):
    """Exercise the standalone script as a user invokes it."""

    def test_help_lists_only_explicit_external_deck_choices(self):
        script = SCRIPT_DIR / "run_external_deck.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("{pspice,ngspice,ltspice,xyce}", result.stdout)
        self.assertIn("--timeout", result.stdout)
        self.assertIn("--output", result.stdout)
        self.assertNotIn("{auto,", result.stdout)

    def test_missing_deck_is_rejected_before_simulator_discovery(self):
        script = SCRIPT_DIR / "run_external_deck.py"
        missing = SCRIPT_DIR / "missing-external-deck.cir"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                str(missing),
                "--simulator",
                "pspice",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("deck is not a file", result.stderr)

    def test_nonpositive_timeout_is_rejected(self):
        script = SCRIPT_DIR / "run_external_deck.py"
        with tempfile.TemporaryDirectory() as tmp:
            deck = Path(tmp) / "synthetic.cir"
            deck.write_text("* synthetic\n.end\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    str(deck),
                    "--simulator",
                    "pspice",
                    "--timeout",
                    "0",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("--timeout must be greater than zero", result.stderr)


class TestExternalDeckSelection(unittest.TestCase):
    """Keep PSpice selection outside the generated-backend registry."""

    def test_pspice_is_constructed_only_for_explicit_request(self):
        with (
            patch("run_external_deck.PspiceBackend") as pspice_class,
            patch("run_external_deck.detect_simulator") as detect,
        ):
            pspice_class.return_value.find.return_value = "pspice.exe"
            selected = run_external_deck.select_backend("pspice")

        self.assertIs(selected, pspice_class.return_value)
        detect.assert_not_called()

    def test_existing_backend_requests_use_existing_detector(self):
        expected = object()
        with (
            patch("run_external_deck.PspiceBackend") as pspice_class,
            patch(
                "run_external_deck.detect_simulator",
                return_value=expected,
            ) as detect,
        ):
            selected = run_external_deck.select_backend("ngspice")

        self.assertIs(selected, expected)
        detect.assert_called_once_with("ngspice")
        pspice_class.assert_not_called()


class TestExternalDeckCli(unittest.TestCase):
    """Verify the standalone JSON and process-exit contract."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.deck = Path(self.tempdir.name) / "example deck.cir"
        self.deck.write_text("* synthetic deck\n.end\n", encoding="utf-8")

    @staticmethod
    def _backend(name, result):
        calls = []

        def run(deck, timeout):
            calls.append((deck, timeout))
            return result

        return SimpleNamespace(name=name, run=run, calls=calls)

    def _run(self, arguments, backend):
        stdout = io.StringIO()
        stderr = io.StringIO()
        ticks = iter([10.0, 11.2344])
        fake_time = SimpleNamespace(perf_counter=lambda: next(ticks))
        with (
            patch(
                "run_external_deck.select_backend",
                return_value=backend,
            ),
            patch.object(
                run_external_deck,
                "time",
                fake_time,
                create=True,
            ),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = run_external_deck.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def _json_stdout(self, stdout):
        self.assertNotEqual(stdout, "", "CLI should emit result JSON")
        return json.loads(stdout)

    def test_success_emits_stable_json_and_zero_exit(self):
        backend = self._backend("pspice", (True, "", ""))
        code, stdout, stderr = self._run(
            [
                str(self.deck),
                "--simulator",
                "pspice",
                "--timeout",
                "120",
            ],
            backend,
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            self._json_stdout(stdout),
            {
                "simulator": "pspice",
                "success": True,
                "deck": str(self.deck.resolve()),
                "native_output": str(
                    self.deck.resolve().with_suffix(".out")
                ),
                "elapsed_s": 1.234,
                "note": "PSpice reported JOB CONCLUDED",
            },
        )
        self.assertEqual(
            backend.calls,
            [(str(self.deck.resolve()), 120)],
        )

    def test_existing_backend_reports_no_invented_native_output(self):
        backend = self._backend("ngspice", (True, "", ""))
        code, stdout, _ = self._run(
            [str(self.deck), "--simulator", "ngspice"],
            backend,
        )

        self.assertEqual(code, 0)
        self.assertIsNone(self._json_stdout(stdout)["native_output"])

    def test_backend_failure_emits_json_stderr_and_nonzero_exit(self):
        backend = self._backend(
            "pspice",
            (
                False,
                "",
                "PSpice completion marker missing: JOB CONCLUDED",
            ),
        )
        code, stdout, stderr = self._run(
            [str(self.deck), "--simulator", "pspice"],
            backend,
        )

        self.assertEqual(code, 1)
        self.assertFalse(self._json_stdout(stdout)["success"])
        self.assertIn("completion marker missing", stderr.lower())

    def test_missing_simulator_returns_actionable_failure(self):
        code, stdout, stderr = self._run(
            [str(self.deck), "--simulator", "pspice"],
            None,
        )

        self.assertEqual(code, 1)
        self.assertFalse(self._json_stdout(stdout)["success"])
        self.assertIn("set PSPICE_PATH", stderr)

    def test_output_option_writes_json_file_instead_of_stdout(self):
        result_path = Path(self.tempdir.name) / "result.json"
        backend = self._backend("pspice", (True, "", ""))
        code, stdout, stderr = self._run(
            [
                str(self.deck),
                "--simulator",
                "pspice",
                "--output",
                str(result_path),
            ],
            backend,
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        self.assertTrue(result_path.is_file())
        self.assertTrue(
            json.loads(result_path.read_text(encoding="utf-8"))["success"]
        )
        self.assertTrue(result_path.read_text(encoding="utf-8").endswith("\n"))

    def _usage_error(self, arguments):
        backend = self._backend("pspice", (True, "", ""))
        stderr = io.StringIO()
        with (
            patch("run_external_deck.select_backend", return_value=backend),
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as raised,
        ):
            run_external_deck.main(arguments)
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual(backend.calls, [], "simulator must not be launched")
        return stderr.getvalue()

    def test_output_may_not_overwrite_deck_native_output_or_sidecar(self):
        native = self.deck.with_suffix(".out")
        for victim in (
            self.deck,
            native,
            native.with_suffix(".json"),
            native.with_suffix(".dat"),
        ):
            with self.subTest(victim=victim.name):
                message = self._usage_error(
                    [
                        str(self.deck),
                        "--simulator",
                        "pspice",
                        "--output",
                        str(victim),
                    ]
                )
                self.assertIn("would overwrite", message)
        self.assertEqual(
            self.deck.read_text(encoding="utf-8"),
            "* synthetic deck\n.end\n",
        )

    @unittest.skipUnless(os.name == "nt", "case-insensitive file system")
    def test_output_collision_check_ignores_case_on_windows(self):
        message = self._usage_error(
            [
                str(self.deck),
                "--simulator",
                "pspice",
                "--output",
                str(self.deck).upper(),
            ]
        )
        self.assertIn("would overwrite", message)

    def test_sidecar_name_is_only_reserved_for_pspice(self):
        sidecar = self.deck.with_suffix(".json")
        backend = self._backend("ngspice", (True, "", ""))
        code, _, _ = self._run(
            [
                str(self.deck),
                "--simulator",
                "ngspice",
                "--output",
                str(sidecar),
            ],
            backend,
        )
        self.assertEqual(code, 0)
        self.assertTrue(sidecar.is_file())

    def test_output_directory_and_missing_directory_are_usage_errors(self):
        missing = Path(self.tempdir.name) / "missing" / "result.json"
        for destination, expected in (
            (Path(self.tempdir.name), "is a directory"),
            (missing, "directory does not exist"),
        ):
            with self.subTest(destination=destination.name):
                message = self._usage_error(
                    [
                        str(self.deck),
                        "--simulator",
                        "pspice",
                        "--output",
                        str(destination),
                    ]
                )
                self.assertIn(expected, message)
                self.assertNotIn("Traceback", message)

    def test_deck_with_a_simulator_output_suffix_is_rejected(self):
        cases = (
            ("pspice", (".out", ".OUT", ".json", ".dat")),
            ("ltspice", (".log", ".RAW", ".raw")),
            ("xyce", (".mt0", ".MT0")),
        )
        for simulator, suffixes in cases:
            for index, suffix in enumerate(suffixes):
                with self.subTest(simulator=simulator, suffix=suffix):
                    # A stem per case: on a case-insensitive filesystem
                    # clash.OUT would be the clash.out written before it.
                    clashing = Path(self.tempdir.name) / f"clash-{simulator}-{index}{suffix}"
                    clashing.write_text(
                        "* synthetic deck\n.end\n", encoding="utf-8"
                    )
                    message = self._usage_error(
                        [str(clashing), "--simulator", simulator]
                    )
                    self.assertIn(f"{suffix} suffix", message)
                    self.assertIn(simulator, message)
                    self.assertEqual(
                        clashing.read_text(encoding="utf-8"),
                        "* synthetic deck\n.end\n",
                    )

    def test_sidecar_suffix_deck_is_allowed_for_other_simulators(self):
        deck = Path(self.tempdir.name) / "plain.json"
        deck.write_text("* synthetic deck\n.end\n", encoding="utf-8")
        backend = self._backend("ngspice", (True, "", ""))
        code, _, _ = self._run(
            [str(deck), "--simulator", "ngspice"], backend
        )
        self.assertEqual(code, 0)

    def test_default_timeout_is_ten_minutes(self):
        backend = self._backend("pspice", (True, "", ""))
        self._run([str(self.deck), "--simulator", "pspice"], backend)
        self.assertEqual(backend.calls, [(str(self.deck.resolve()), 600)])

    def test_result_json_is_replaced_atomically(self):
        result_path = Path(self.tempdir.name) / "result.json"
        result_path.write_text("previous result\n", encoding="utf-8")
        backend = self._backend("pspice", (True, "", ""))
        with patch(
            "run_external_deck.os.replace",
            side_effect=OSError("replace blocked"),
        ):
            code, stdout, stderr = self._run(
                [
                    str(self.deck),
                    "--simulator",
                    "pspice",
                    "--output",
                    str(result_path),
                ],
                backend,
            )

        self.assertEqual(code, 1)
        self.assertEqual(stdout, "")
        self.assertIn(f"could not write {result_path}", stderr)
        self.assertIn("replace blocked", stderr)

        self.assertEqual(
            result_path.read_text(encoding="utf-8"),
            "previous result\n",
        )
        self.assertEqual(
            sorted(p.name for p in result_path.parent.iterdir()),
            ["example deck.cir", "result.json"],
        )

    def _write_result(self, result_path):
        backend = self._backend("pspice", (True, "", ""))
        code, _, stderr = self._run(
            [
                str(self.deck),
                "--simulator",
                "pspice",
                "--output",
                str(result_path),
            ],
            backend,
        )
        self.assertEqual(code, 0, stderr)

    def test_result_mode_honors_umask_or_keeps_existing_mode(self):
        result_path = Path(self.tempdir.name) / "result.json"
        real_chmod = os.chmod
        modes = []

        def record_chmod(path, mode):
            modes.append(mode)
            real_chmod(path, mode)

        with (
            patch("run_external_deck.os.umask", return_value=0o027),
            patch("run_external_deck.os.chmod", side_effect=record_chmod),
        ):
            self._write_result(result_path)
            existing_mode = stat.S_IMODE(result_path.stat().st_mode)
            self._write_result(result_path)

        self.assertEqual(modes, [0o640, existing_mode])

    @unittest.skipUnless(os.name == "posix", "POSIX file modes")
    def test_result_file_mode_on_posix(self):
        result_path = Path(self.tempdir.name) / "result.json"
        previous = os.umask(0o022)
        try:
            self._write_result(result_path)
            self.assertEqual(stat.S_IMODE(result_path.stat().st_mode), 0o644)
            result_path.chmod(0o604)
            self._write_result(result_path)
        finally:
            os.umask(previous)
        self.assertEqual(stat.S_IMODE(result_path.stat().st_mode), 0o604)

    @unittest.skipUnless(os.name == "nt", "Windows read-only replace")
    def test_failed_replace_of_read_only_result_leaves_no_temp_file(self):
        result_path = Path(self.tempdir.name) / "result.json"
        result_path.write_text("previous result\n", encoding="utf-8")
        result_path.chmod(stat.S_IREAD)
        self.addCleanup(result_path.chmod, stat.S_IREAD | stat.S_IWRITE)
        backend = self._backend("pspice", (True, "", ""))

        code, _, stderr = self._run(
            [
                str(self.deck),
                "--simulator",
                "pspice",
                "--output",
                str(result_path),
            ],
            backend,
        )

        self.assertEqual(code, 1)
        self.assertIn(f"could not write {result_path}", stderr)
        self.assertEqual(
            sorted(p.name for p in result_path.parent.iterdir()),
            ["example deck.cir", "result.json"],
        )

    def test_result_creation_failure_is_a_clean_error(self):
        result_path = Path(self.tempdir.name) / "result.json"
        for backend in (None, self._backend("pspice", (True, "", ""))):
            with self.subTest(simulator_available=backend is not None):
                with patch(
                    "run_external_deck.tempfile.mkstemp",
                    side_effect=PermissionError("access denied"),
                ):
                    code, stdout, stderr = self._run(
                        [
                            str(self.deck),
                            "--simulator",
                            "pspice",
                            "--output",
                            str(result_path),
                        ],
                        backend,
                    )
                self.assertEqual(code, 1)
                self.assertEqual(stdout, "")
                self.assertIn(f"could not write {result_path}", stderr)
                self.assertIn("access denied", stderr)
                self.assertFalse(result_path.exists())


class TestPspiceDiscovery(unittest.TestCase):
    """Exercise the documented PSPICE_PATH then PATH lookup order."""

    def test_pspice_path_existing_file_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / "PSpice executable.exe"
            executable.touch()
            with (
                patch.dict(
                    os.environ,
                    {"PSPICE_PATH": str(executable)},
                    clear=False,
                ),
                patch("spice_simulator.shutil.which") as which,
            ):
                found = spice_simulator.PspiceBackend().find()

        self.assertEqual(found, str(executable))
        which.assert_not_called()

    def test_invalid_pspice_path_falls_back_to_path_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.exe"
            with (
                patch.dict(
                    os.environ,
                    {"PSPICE_PATH": str(missing)},
                    clear=False,
                ),
                patch(
                    "spice_simulator.shutil.which",
                    side_effect=[None, "/tools/pspice.exe"],
                ) as which,
                patch("spice_simulator._on_windows", return_value=False),
            ):
                found = spice_simulator.PspiceBackend().find()

        self.assertEqual(found, os.path.abspath("/tools/pspice.exe"))
        self.assertEqual(
            which.call_args_list,
            [call("pspice"), call("pspice.exe")],
        )

    def test_relative_discoveries_are_made_absolute(self):
        # The simulator runs with cwd=deck.parent, so a relative path would
        # resolve next to the deck instead of where it was discovered.
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "pspice.exe").touch()
            previous = os.getcwd()
            os.chdir(tmp)
            try:
                with (
                    patch.dict(
                        os.environ, {"PSPICE_PATH": "pspice.exe"}, clear=False
                    ),
                    patch("spice_simulator.shutil.which") as which,
                ):
                    from_env = spice_simulator.PspiceBackend().find()
                with (
                    patch.dict(os.environ, {"PSPICE_PATH": ""}, clear=False),
                    patch(
                        "spice_simulator.shutil.which",
                        return_value=os.path.join(".", "pspice"),
                    ),
                    patch("spice_simulator._on_windows", return_value=False),
                ):
                    from_path = spice_simulator.PspiceBackend().find()
                expected_dir = os.getcwd()
            finally:
                os.chdir(previous)

        which.assert_not_called()
        self.assertEqual(from_env, os.path.join(expected_dir, "pspice.exe"))
        self.assertEqual(from_path, os.path.join(expected_dir, "pspice"))

    @unittest.skipUnless(os.name == "nt", "Windows path semantics")
    def test_windows_path_search_finds_only_absolute_pspice_exe(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd_dir = Path(tmp, "cwd")
            script_dir = Path(tmp, "scripts")
            exe_dir = Path(tmp, "bin")
            for folder in (cwd_dir, script_dir, exe_dir):
                folder.mkdir()
            (cwd_dir / "pspice.exe").touch()
            (script_dir / "pspice.bat").touch()
            (exe_dir / "pspice.exe").touch()
            search_path = os.pathsep.join(
                [".", "", str(script_dir), f'"{exe_dir}"']
            )
            previous = os.getcwd()
            os.chdir(cwd_dir)
            try:
                with (
                    patch.dict(
                        os.environ,
                        {"PSPICE_PATH": "", "PATH": search_path},
                        clear=False,
                    ),
                    patch("spice_simulator.shutil.which") as which,
                ):
                    found = spice_simulator.PspiceBackend().find()
                with patch.dict(
                    os.environ,
                    {"PSPICE_PATH": "", "PATH": f".{os.pathsep}{script_dir}"},
                    clear=False,
                ):
                    missing = spice_simulator.PspiceBackend().find()
            finally:
                os.chdir(previous)

        which.assert_not_called()
        self.assertEqual(found, str(exe_dir / "pspice.exe"))
        self.assertIsNone(missing)


STUB_SOURCE = '''\
import json
import os
import subprocess
import sys
import time
from pathlib import Path

here = Path(__file__).resolve().parent
config = json.loads((here / "stub.json").read_text(encoding="utf-8"))
args = sys.argv[1:]
(here / "record.json").write_text(
    json.dumps({"argv": args, "cwd": os.getcwd()}),
    encoding="utf-8",
)
if config.get("out_hex") is not None:
    Path(args[args.index("-o") + 1]).write_bytes(
        bytes.fromhex(config["out_hex"])
    )
if config.get("stdout_hex"):
    sys.stdout.buffer.write(bytes.fromhex(config["stdout_hex"]))
    sys.stdout.flush()
if config.get("heartbeat"):
    child = (
        "import time\\n"
        "from pathlib import Path\\n"
        "for _ in range(600):\\n"
        f"    Path({config['heartbeat']!r}).write_text('alive')\\n"
        "    time.sleep(0.05)\\n"
    )
    subprocess.Popen([sys.executable, "-c", child])
time.sleep(config.get("sleep", 0))
sys.exit(config.get("exit_code", 0))
'''


class StubPspice(spice_simulator.PspiceBackend):
    """Real PspiceBackend launch path with a Python script as the program."""

    def __init__(self, stub):
        self.stub = stub

    def find(self):
        return sys.executable

    def _command(self, binary, deck_name, output_name):
        command = super()._command(binary, deck_name, output_name)
        return [command[0], str(self.stub), *command[1:]]


class TestPspiceRun(unittest.TestCase):
    """Classify native PSpice batch outcomes of a real child process."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        root = Path(self.tempdir.name)
        self.stub_dir = root / "stub"
        self.stub_dir.mkdir()
        self.stub = self.stub_dir / "stub_pspice.py"
        self.stub.write_text(STUB_SOURCE, encoding="utf-8")
        self.deck_dir = root / "deck dir"
        self.deck_dir.mkdir()
        self.deck = self.deck_dir / "deck with spaces.cir"
        self.deck.write_text(
            "* synthetic passive deck\n.end\n",
            encoding="utf-8",
        )
        self.output = self.deck.with_suffix(".out")
        self.backend = StubPspice(self.stub)

    def _run(self, native=None, timeout=60, **config):
        if isinstance(native, str):
            native = native.encode("utf-8")
        if native is not None:
            config["out_hex"] = native.hex()
        (self.stub_dir / "stub.json").write_text(
            json.dumps(config),
            encoding="utf-8",
        )
        return self.backend.run(self.deck, timeout=timeout)

    def _record(self):
        return json.loads(
            (self.stub_dir / "record.json").read_text(encoding="utf-8")
        )

    def test_process_runs_in_deck_directory_with_expected_arguments(self):
        success, _, _ = self._run("JOB CONCLUDED\n")

        self.assertTrue(success)
        record = self._record()
        self.assertEqual(
            record["argv"],
            [
                "-r", "-e", os.path.join(os.curdir, self.deck.name),
                "-o", os.path.join(os.curdir, self.output.name),
            ],
        )
        self.assertTrue(os.path.samefile(record["cwd"], self.deck_dir))

    def test_deck_name_with_leading_dash_is_not_passed_as_an_option(self):
        self.deck = self.deck_dir / "-r.cir"
        self.deck.write_text("* dash deck\n.end\n", encoding="utf-8")

        success, _, diagnostic = self._run("JOB CONCLUDED\n")

        self.assertTrue(success, diagnostic)
        argv = self._record()["argv"]
        self.assertEqual(argv[2], os.path.join(os.curdir, "-r.cir"))
        self.assertEqual(argv[4], os.path.join(os.curdir, "-r.out"))
        self.assertTrue((self.deck_dir / "-r.out").is_file())

    def test_exit_zero_with_completion_marker_succeeds(self):
        result = self._run("PSpice batch output\n   JOB CONCLUDED  \r\n")
        self.assertEqual(result, (True, "", ""))

    def test_marker_must_be_a_whole_line(self):
        for text in (
            "JOB CONCLUDED early\n",
            "* JOB CONCLUDED\n",
            "echo JOB CONCLUDEDX\n",
        ):
            with self.subTest(text=text):
                (success, _, diagnostic) = self._run(text)
                self.assertFalse(success)
                self.assertIn("completion marker missing", diagnostic)

    def test_abort_marker_must_be_a_whole_line(self):
        (success, _, diagnostic) = self._run(
            "JOB ABORTED later\nJOB CONCLUDED\n"
        )
        self.assertTrue(success, diagnostic)

    def test_stale_native_output_is_not_success(self):
        self.output.write_text("JOB CONCLUDED\n", encoding="utf-8")

        success, _, diagnostic = self._run(None)

        self.assertFalse(success)
        self.assertIn("did not update native output", diagnostic)
        self.assertEqual(
            self.output.read_text(encoding="utf-8"),
            "JOB CONCLUDED\n",
        )

    def test_rewritten_native_output_replaces_stale_content(self):
        self.output.write_text("stale\n", encoding="utf-8")

        success, _, diagnostic = self._run("fresh\n JOB CONCLUDED\n")

        self.assertTrue(success, diagnostic)

    def test_missing_native_output_fails(self):
        success, _, diagnostic = self._run(None)
        self.assertFalse(success)
        self.assertIn("did not write native output", diagnostic)
        self.assertIn(str(self.output.resolve()), diagnostic)

    def test_empty_native_output_fails(self):
        success, _, diagnostic = self._run("")
        self.assertFalse(success)
        self.assertIn("empty", diagnostic.lower())

    def test_exit_zero_without_completion_marker_fails(self):
        (success, _, diagnostic) = self._run("analysis stopped\n")
        self.assertFalse(success)
        self.assertIn("completion marker missing", diagnostic.lower())

    def test_abort_marker_fails_even_with_zero_exit(self):
        (success, _, diagnostic) = self._run(
            "JOB ABORTED\nJOB CONCLUDED\n"
        )
        self.assertFalse(success)
        self.assertIn("abort marker", diagnostic.lower())

    def test_fatal_error_line_fails(self):
        (success, _, diagnostic) = self._run(
            "ERROR -- invalid model\nJOB CONCLUDED\n"
        )
        self.assertFalse(success)
        self.assertIn("fatal error", diagnostic.lower())

    def test_orpsim_error_is_fatal_and_reported_without_completion(self):
        (success, _, diagnostic) = self._run(
            "WARNING(ORPSIM-0001): harmless\n"
            "ERROR(ORPSIM-9999): Synthetic library not found\n"
            "ERROR(ORPSIM-9998): second problem\n"
        )
        self.assertFalse(success)
        self.assertIn("fatal error", diagnostic.lower())
        self.assertIn("Synthetic library not found", diagnostic)
        self.assertNotIn("second problem", diagnostic)
        self.assertNotIn("completion marker missing", diagnostic)

    def test_long_fatal_error_line_is_truncated(self):
        (success, _, diagnostic) = self._run(
            "ERROR(ORPSIM-9999): " + "x" * 1000 + "\n"
        )
        self.assertFalse(success)
        self.assertLess(len(diagnostic), 300)

    def test_warning_and_zero_error_summary_are_not_fatal(self):
        (success, _, diagnostic) = self._run(
            "WARNING(ORPSIM-0001): synthetic warning\n"
            "ERROR COUNT = 0\nJOB CONCLUDED\n"
        )
        self.assertTrue(success, diagnostic)

    def test_nonzero_process_exit_fails(self):
        (success, _, diagnostic) = self._run(
            "JOB CONCLUDED\n",
            exit_code=7,
        )
        self.assertFalse(success)
        self.assertIn("exit code 7", diagnostic.lower())

    def test_utf16_native_output_is_decoded_by_byte_order_mark(self):
        for encoding in ("utf-16", "utf-16-be", "utf-8-sig"):
            with self.subTest(encoding=encoding):
                raw = "synthetic\nJOB CONCLUDED\n".encode(encoding)
                if encoding == "utf-16-be":
                    raw = b"\xfe\xff" + raw
                (success, _, diagnostic) = self._run(raw)
                self.assertTrue(success, diagnostic)

    def test_undecodable_native_output_is_reported_distinctly(self):
        (success, _, diagnostic) = self._run(b"\xff\xfe\x41")
        self.assertFalse(success)
        self.assertIn("Could not decode", diagnostic)
        self.assertNotIn("marker missing", diagnostic)

    def test_native_output_is_read_in_bounded_chunks(self):
        limit = 16
        sizes = []

        class GuardedStream(io.StringIO):
            def read(self, size=-1):
                sizes.append(size)
                if size is None or size < 0:
                    raise AssertionError("unbounded read of native output")
                return super().read(size)

            def readline(self, size=-1):
                raise AssertionError("unexpected readline")

        def guarded_open(path):
            return GuardedStream(path.read_text(encoding="utf-8"))

        native = (
            "header line one\n"
            "*" * limit + "\n"
            "split at chunk\n"
            "JOB CONCLUDED"
        )
        with (
            patch.object(spice_simulator, "_NATIVE_LINE_LIMIT", limit),
            patch.object(
                spice_simulator, "_open_native_output", guarded_open
            ),
        ):
            self.assertEqual(self._run(native), (True, "", ""))

        self.assertGreater(len(sizes), 2)
        self.assertTrue(all(0 < size <= limit for size in sizes), sizes)

    def test_lines_split_like_str_splitlines(self):
        # PSpice listings separate pages with form feeds.
        success, _, diagnostic = self._run(
            "page footer\f  ERROR -- after form feed\r\nJOB CONCLUDED\n"
        )
        self.assertFalse(success)
        self.assertIn("ERROR -- after form feed", diagnostic)

    def test_over_limit_line_fails_instead_of_partial_classification(self):
        limit = 16
        with patch.object(spice_simulator, "_NATIVE_LINE_LIMIT", limit):
            at_limit = self._run("x" * limit + "\nJOB CONCLUDED\n")
            over_limit = self._run(
                "ERROR" + " " * (limit * 3) + "-- hidden\nJOB CONCLUDED\n"
            )
            plus_one_terminated = self._run(
                "x" * (limit + 1) + "\nJOB CONCLUDED\n"
            )
            plus_one_at_eof = self._run(
                "JOB CONCLUDED\n" + "x" * (limit + 1)
            )

        self.assertEqual(at_limit, (True, "", ""))
        for result in (over_limit, plus_one_terminated, plus_one_at_eof):
            self.assertFalse(result[0])
            self.assertIn("Could not classify", result[2])
            self.assertIn(f"longer than {limit} characters", result[2])

    def test_decode_error_after_fatal_line_is_still_reported(self):
        raw = (
            "ERROR -- first\n" + "z" * 20000 + "\nJOB CONCLUDED\n"
        ).encode("utf-16") + b"\x41"
        success, _, diagnostic = self._run(raw)
        self.assertFalse(success)
        self.assertIn("Could not decode", diagnostic)

    def test_invalid_utf8_stdout_does_not_break_a_successful_run(self):
        result = self._run("JOB CONCLUDED\n", stdout_hex="ff")
        self.assertEqual(result, (True, "", ""))

    def test_timeout_returns_failure_without_deleting_native_output(self):
        self.output.write_text(
            "partial native output\n",
            encoding="utf-8",
        )

        success, _, diagnostic = self._run(timeout=1, sleep=60)

        self.assertFalse(success)
        self.assertEqual(diagnostic, "Simulation timed out after 1s")
        self.assertEqual(
            self.output.read_text(encoding="utf-8"),
            "partial native output\n",
        )

    def test_timeout_kills_the_whole_process_tree_promptly(self):
        heartbeat = self.stub_dir / "heartbeat.txt"
        timeout = 3

        started = time.perf_counter()
        success, _, diagnostic = self._run(
            timeout=timeout,
            sleep=60,
            heartbeat=str(heartbeat),
        )
        elapsed = time.perf_counter() - started

        self.assertFalse(success)
        self.assertIn("timed out", diagnostic)
        self.assertLess(elapsed, timeout + 5)
        self.assertTrue(heartbeat.exists(), "grandchild never started")
        time.sleep(0.3)
        last_beat = heartbeat.stat().st_mtime_ns
        time.sleep(0.5)
        self.assertEqual(
            heartbeat.stat().st_mtime_ns,
            last_beat,
            "grandchild survived the timeout",
        )

    def test_interrupt_kills_the_whole_process_tree(self):
        heartbeat = self.stub_dir / "heartbeat.txt"
        original_wait = subprocess.Popen.wait

        def interrupted_wait(process, timeout=None):
            if timeout is None:
                return original_wait(process)
            deadline = time.perf_counter() + 30
            while not heartbeat.exists() and time.perf_counter() < deadline:
                time.sleep(0.05)
            raise KeyboardInterrupt

        with patch.object(subprocess.Popen, "wait", interrupted_wait):
            with self.assertRaises(KeyboardInterrupt):
                self._run(sleep=60, heartbeat=str(heartbeat))

        self.assertTrue(heartbeat.exists(), "grandchild never started")
        time.sleep(0.3)
        last_beat = heartbeat.stat().st_mtime_ns
        time.sleep(0.5)
        self.assertEqual(
            heartbeat.stat().st_mtime_ns,
            last_beat,
            "grandchild survived the interrupt",
        )

    def test_windows_tree_kill_uses_system_taskkill_path(self):
        with (
            patch("spice_simulator._on_windows", return_value=True),
            patch.dict(os.environ, {"SystemRoot": r"D:\Win"}, clear=False),
            patch("spice_simulator.subprocess.run") as run,
        ):
            spice_simulator._kill_process_tree(1234)

        self.assertEqual(
            run.call_args.args[0],
            [
                os.path.join(r"D:\Win", "System32", "taskkill.exe"),
                "/F", "/T", "/PID", "1234",
            ],
        )

    def test_missing_executable_returns_actionable_failure(self):
        with patch.object(self.backend, "find", return_value=None):
            success, stdout, diagnostic = self.backend.run(
                self.deck,
                timeout=120,
            )

        self.assertFalse(success)
        self.assertEqual(stdout, "")
        self.assertIn("set PSPICE_PATH", diagnostic)

    def test_launch_error_returns_actionable_failure(self):
        with patch(
            "spice_simulator.subprocess.Popen",
            side_effect=OSError("launch blocked"),
        ):
            success, _, diagnostic = self.backend.run(
                self.deck,
                timeout=120,
            )

        self.assertFalse(success)
        self.assertIn("Could not launch PSpice", diagnostic)
        self.assertIn("launch blocked", diagnostic)

    def test_native_output_stat_errors_produce_cli_failure_json(self):
        (self.stub_dir / "stub.json").write_text(
            json.dumps({"out_hex": b"JOB CONCLUDED\n".hex()}),
            encoding="utf-8",
        )
        for stage in ("before", "after"):
            with self.subTest(stage=stage):
                error = PermissionError(13, "Access denied", str(self.output))
                signatures = [error] if stage == "before" else [None, error]
                stdout = io.StringIO()
                stderr = io.StringIO()
                with (
                    patch(
                        "spice_simulator._file_signature",
                        side_effect=signatures,
                    ),
                    patch(
                        "run_external_deck.select_backend",
                        return_value=self.backend,
                    ),
                    redirect_stdout(stdout),
                    redirect_stderr(stderr),
                ):
                    code = run_external_deck.main([
                        str(self.deck), "--simulator", "pspice",
                    ])

                self.assertEqual(code, 1)
                result = json.loads(stdout.getvalue())
                self.assertFalse(result["success"])
                self.assertIn(str(self.output.resolve()), result["note"])
                self.assertIn("Access denied", result["note"])
                self.assertIn(result["note"], stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())

    def test_unreadable_native_output_returns_actionable_failure(self):
        with patch.object(
            spice_simulator,
            "_open_native_output",
            side_effect=OSError("read blocked"),
        ):
            success, _, diagnostic = self._run("JOB CONCLUDED\n")

        self.assertFalse(success)
        self.assertIn("Could not read PSpice native output", diagnostic)
        self.assertIn("read blocked", diagnostic)

    def test_windows_non_exe_or_relative_executable_is_rejected(self):
        candidates = (
            "C:/tools/pspice.bat",
            "C:/tools/PSPICE.CMD",
            "C:/tools/pspice.bat.",
            "C:/tools/pspice.com",
            "pspice.exe",
        )
        for binary in candidates:
            with self.subTest(binary=binary):
                with (
                    patch.object(
                        self.backend,
                        "find",
                        return_value=binary,
                    ),
                    patch("spice_simulator._on_windows", return_value=True),
                    patch("spice_simulator.subprocess.Popen") as popen,
                ):
                    success, _, diagnostic = self.backend.run(
                        self.deck,
                        timeout=120,
                    )

                self.assertFalse(success)
                self.assertIn("absolute path to a native .exe", diagnostic)
                popen.assert_not_called()

    def test_unsupported_generated_measurement_methods_are_actionable(self):
        message = "use run_external_deck.py"
        with self.assertRaisesRegex(NotImplementedError, message):
            self.backend.format_measurement_block(
                [],
                [],
                "measurements.out",
            )
        with self.assertRaisesRegex(NotImplementedError, message):
            self.backend.parse_results("measurements.out", "", "")


class TestExistingBackendSelection(unittest.TestCase):
    """Guard the generated-testbench simulator selection contract."""

    def test_registry_excludes_pspice(self):
        self.assertEqual(
            list(spice_simulator.BACKENDS),
            ["ngspice", "ltspice", "xyce"],
        )
        self.assertNotIn("pspice", spice_simulator.BACKENDS)

    def test_explicit_pspice_is_not_available_through_existing_detector(self):
        with patch.dict(os.environ, {"PSPICE_PATH": __file__}, clear=False):
            self.assertIsNone(spice_simulator.detect_simulator("pspice"))

    def test_auto_detection_order_is_unchanged(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch.object(
                spice_simulator.NgspiceBackend,
                "find",
                return_value=None,
            ) as ng_find,
            patch.object(
                spice_simulator.LtspiceBackend,
                "find",
                return_value=None,
            ) as lt_find,
            patch.object(
                spice_simulator.XyceBackend,
                "find",
                return_value="/bin/Xyce",
            ) as xyce_find,
        ):
            backend = spice_simulator.detect_simulator("auto")

        self.assertIsInstance(backend, spice_simulator.XyceBackend)
        ng_find.assert_called_once_with()
        lt_find.assert_called_once_with()
        xyce_find.assert_called_once_with()


class TestSimulatorDiscoveryWindows(unittest.TestCase):
    """On Windows a simulator in the current directory is never picked."""

    CASES = (
        (spice_simulator.NgspiceBackend, "NGSPICE_PATH", "ngspice.exe"),
        (spice_simulator.LtspiceBackend, "LTSPICE_PATH", "XVIIx64.exe"),
        (spice_simulator.XyceBackend, "XYCE_PATH", "Xyce.exe"),
    )

    def test_cwd_tool_not_found_absolute_path_found(self):
        from kicad_core import executables
        for backend, var, exe in self.CASES:
            with self.subTest(backend=backend.__name__):
                with tempfile.TemporaryDirectory() as tmp:
                    tmp = Path(tmp)
                    cwd, bin_, empty = tmp / "cwd", tmp / "bin", tmp / "empty"
                    for d in (cwd, bin_, empty):
                        d.mkdir()
                    for name in (exe, exe[:-4]):
                        (cwd / name).write_bytes(b"")
                        (cwd / name).chmod(0o755)
                    (bin_ / exe).write_bytes(b"")
                    env = {var: "", "PROGRAMFILES": str(empty), "PROGRAMFILES(X86)": str(empty),
                           "LOCALAPPDATA": str(empty), "PATH": "."}
                    old = os.getcwd()
                    os.chdir(cwd)
                    try:
                        with patch.dict(os.environ, env), \
                                patch.object(executables, "_on_windows", return_value=True):
                            self.assertIsNone(backend().find())
                            os.environ["PATH"] = os.pathsep.join([".", str(bin_)])
                            self.assertEqual(backend().find(), str(bin_ / exe))
                    finally:
                        os.chdir(old)


if __name__ == "__main__":
    unittest.main(verbosity=2)
