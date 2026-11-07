"""
SPICE simulator backend abstraction.

Supports ngspice, LTspice, and Xyce with a unified interface for finding
the binary, running simulations, formatting measurement commands, and
parsing results. The circuit netlist is portable — only the measurement
layer and output parsing differ between simulators.

Auto-detection tries ngspice → LTspice → Xyce. Override with --simulator
flag or SPICE_SIMULATOR environment variable.

PspiceBackend is not part of BACKENDS or auto-detection: it only runs
complete user-supplied decks and is reachable solely through
run_external_deck.py --simulator pspice.
"""

import codecs
import os
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

import _core_path  # noqa: F401
from kicad_core.executables import find_executable
from spice_models import spice_echo


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class SimulatorBackend:
    """Abstract base for SPICE simulator backends."""
    name = "base"

    def find(self):
        """Locate the simulator binary. Returns path string or None."""
        raise NotImplementedError

    def run(self, cir_file, timeout=5, cwd=None):
        """Run simulation in batch mode.

        Args:
            cir_file: Path to the .cir netlist file
            timeout: Maximum seconds to wait

        Returns:
            (success: bool, stdout: str, stderr: str)
        """
        raise NotImplementedError

    def format_measurement_block(self, analyses, measurements, output_file,
                                  extra_vars=None):
        """Generate simulator-specific measurement + output commands.

        Args:
            analyses: List of (type, spec) tuples.
                      e.g., [("ac", "dec 100 1 100Meg"), ("dc", "Vgate 0 5 0.05")]
            measurements: List of measurement tuples. Each is one of:
                - ("name", "when", "expr", "value")     → find where expr = value
                - ("name", "find", "expr", "at=freq")    → find expr value at a point
                - ("name", "max", "expr")                → find maximum of expr
                - ("name", "min", "expr")                → find minimum of expr
                - ("name", "let", "expression")          → computed variable
            output_file: Path where results should be written (for ngspice echo)
            extra_vars: Dict of extra key=value pairs to include in output

        Returns:
            String block to append after the circuit netlist (before .end)
        """
        raise NotImplementedError

    def parse_results(self, output_file, stdout, stderr):
        """Parse simulation results into a flat {key: float_or_None} dict.

        Args:
            output_file: Path to the output file (for ngspice echo-based output)
            stdout: Captured stdout from simulator process
            stderr: Captured stderr from simulator process

        Returns:
            Dict mapping measurement names to values
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# ngspice backend
# ---------------------------------------------------------------------------

class NgspiceBackend(SimulatorBackend):
    """ngspice — the default backend. Uses .control blocks for measurement."""
    name = "ngspice"

    def find(self):
        # Explicit override
        env_path = os.environ.get("NGSPICE_PATH")
        if env_path and os.path.isfile(env_path):
            return os.path.abspath(env_path)
        # Standard PATH lookup
        found = find_executable("ngspice")
        if found:
            return found
        # Windows default
        for candidate in [
            os.path.join(os.environ.get("PROGRAMFILES", ""), "Spice64", "bin", "ngspice.exe"),
            r"C:\Spice64\bin\ngspice.exe",
        ]:
            if os.path.isfile(candidate):
                return candidate
        return None

    def run(self, cir_file, timeout=5, cwd=None):
        binary = self.find()
        if not binary:
            return False, "", "ngspice not found"
        try:
            result = subprocess.run(
                [binary, "-n", "-b", cir_file],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=cwd,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Simulation timed out after {timeout}s"
        except OSError as e:
            return False, "", str(e)

    def format_measurement_block(self, analyses, measurements, output_file,
                                  extra_vars=None):
        lines = [".control"]

        # Analysis commands
        for analysis_type, spec in analyses:
            lines.append(f"{analysis_type} {spec}")

        # Measurements and let assignments
        echo_vars = []
        for meas in measurements:
            name = meas[0]
            func = meas[1]

            if func == "when":
                expr, value = meas[2], meas[3]
                rise_fall = ""
                if len(meas) > 4:
                    rise_fall = f" {meas[4]}"
                lines.append(f"meas {analyses[0][0]} {name} when {expr}={value}{rise_fall}")
                echo_vars.append(f"{name}=$&{name}")

            elif func == "find":
                expr, at_spec = meas[2], meas[3]
                lines.append(f"meas {analyses[0][0]} {name} find {expr} {at_spec}")
                echo_vars.append(f"{name}=$&{name}")

            elif func == "max":
                expr = meas[2]
                from_to = ""
                if len(meas) > 3:
                    from_to = f" {meas[3]}"
                lines.append(f"meas {analyses[0][0]} {name} max {expr}{from_to}")
                echo_vars.append(f"{name}=$&{name}")

            elif func == "min":
                expr = meas[2]
                lines.append(f"meas {analyses[0][0]} {name} min {expr}")
                echo_vars.append(f"{name}=$&{name}")

            elif func == "let":
                expression = meas[2]
                lines.append(f"let {name} = {expression}")
                # Only echo let variables that are explicitly marked as output
                # (4th element = True). Unmarked lets may be vectors from sweeps
                # or intermediates for other measurements.
                if len(meas) > 3 and meas[3]:
                    echo_vars.append(f"{name}=$&{name}")

        # Each value is one word: the parser splits on whitespace, so a later word with
        # "=" would read as a measurement
        if extra_vars:
            for key, val in extra_vars.items():
                words = spice_echo(val).split()
                echo_vars.append(f"{spice_echo(key)}={words[0] if words else ''}")

        # Echo all results to output file
        echo_str = " ".join(echo_vars)
        # Normalize path separators for ngspice (needs forward slashes)
        output_path = output_file.replace("\\", "/")
        lines.append(f'echo "{echo_str}" > {output_path}')
        lines.append("quit")
        lines.append(".endc")

        return "\n".join(lines)

    def parse_results(self, output_file, stdout, stderr):
        """Parse ngspice echo output file — delegates to shared parser."""
        from spice_results import parse_output_file
        return parse_output_file(output_file)


# ---------------------------------------------------------------------------
# LTspice backend
# ---------------------------------------------------------------------------

class LtspiceBackend(SimulatorBackend):
    """LTspice — uses .meas in netlist body, parses .log file."""
    name = "ltspice"

    def find(self):
        env_path = os.environ.get("LTSPICE_PATH")
        if env_path and os.path.isfile(env_path):
            return os.path.abspath(env_path)

        # Standard PATH
        for name in ("ltspice", "LTspice", "XVIIx64"):
            found = find_executable(name)
            if found:
                return found

        # Platform-specific defaults
        if sys.platform == "win32":
            for candidate in [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "LTC", "LTspiceXVII", "XVIIx64.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "LTC", "LTspiceXVII", "XVIIx64.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "ADI", "LTspice", "LTspice.exe"),
            ]:
                if os.path.isfile(candidate):
                    return candidate
        elif sys.platform == "darwin":
            candidate = "/Applications/LTspice.app/Contents/MacOS/LTspice"
            if os.path.isfile(candidate):
                return candidate

        # Linux: check for wine + LTspice
        wine = find_executable("wine")
        if wine:
            home = os.path.expanduser("~")
            for candidate in [
                os.path.join(home, ".wine", "drive_c", "Program Files", "LTC", "LTspiceXVII", "XVIIx64.exe"),
                os.path.join(home, ".wine", "drive_c", "Program Files", "ADI", "LTspice", "LTspice.exe"),
            ]:
                if os.path.isfile(candidate):
                    return f"wine:{candidate}"

        return None

    def run(self, cir_file, timeout=5, cwd=None):
        binary = self.find()
        if not binary:
            return False, "", "LTspice not found"

        try:
            if binary.startswith("wine:"):
                # Linux via wine
                exe = binary[5:]
                cmd = ["wine", exe, "-b", cir_file]
            else:
                cmd = [binary, "-b", cir_file]

            result = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=cwd,
            )
            # LTspice returns 0 on success
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Simulation timed out after {timeout}s"
        except OSError as e:
            return False, "", str(e)

    def format_measurement_block(self, analyses, measurements, output_file,
                                  extra_vars=None):
        """LTspice: .meas statements in the netlist body (no .control)."""
        lines = []

        # Analysis commands (as dot commands)
        for analysis_type, spec in analyses:
            lines.append(f".{analysis_type} {spec}")

        # Measurement commands
        for meas in measurements:
            name = meas[0]
            func = meas[1]
            atype = analyses[0][0] if analyses else "ac"

            if func == "when":
                expr, value = meas[2], meas[3]
                lines.append(f".meas {atype} {name} when {expr}={value}")
            elif func == "find":
                expr, at_spec = meas[2], meas[3]
                lines.append(f".meas {atype} {name} find {expr} {at_spec}")
            elif func == "max":
                expr = meas[2]
                lines.append(f".meas {atype} {name} max {expr}")
            elif func == "min":
                expr = meas[2]
                lines.append(f".meas {atype} {name} min {expr}")
            elif func == "let":
                # LTspice doesn't support let — use .param or skip
                pass

        return "\n".join(lines)

    def parse_results(self, output_file, stdout, stderr):
        """Parse LTspice .log file for .meas results.

        LTspice writes measurement results to a .log file alongside the .raw:
            fc_sim: vdb(out)=-3 FROM 1 TO 1e+08
              AT=15917.3
        """
        results = {}

        # The log file has the same base name as the .cir but with .log
        cir_base = output_file.rsplit(".", 1)[0] if "." in output_file else output_file
        log_candidates = [cir_base + ".log", cir_base + ".LOG"]
        log_path = None
        for lp in log_candidates:
            if os.path.isfile(lp):
                log_path = lp
                break

        if not log_path:
            # Try parsing stdout instead
            text = stdout
        else:
            try:
                with open(log_path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                text = stdout

        # Parse LTspice .meas output format:
        # "meas_name: ... AT=value" or "meas_name: ... = value"
        for line in text.splitlines():
            line = line.strip()
            # Pattern: "name: ... = value" (end of line)
            m = re.match(r'^(\w+):\s+.*?=\s*([-+]?[\d.eE]+)', line)
            if m:
                results[m.group(1)] = float(m.group(2))
                continue
            # Pattern: "  AT=value" (continuation line)
            m = re.match(r'^\s+AT=([-+]?[\d.eE]+)', line)
            if m:
                # Associate with the previous measurement
                pass  # Handled by the main pattern above

        return results


# ---------------------------------------------------------------------------
# Xyce backend
# ---------------------------------------------------------------------------

class XyceBackend(SimulatorBackend):
    """Xyce — Sandia's parallel SPICE. Uses .measure, parses stdout."""
    name = "xyce"

    def find(self):
        env_path = os.environ.get("XYCE_PATH")
        if env_path and os.path.isfile(env_path):
            return os.path.abspath(env_path)
        for name in ("Xyce", "xyce"):
            found = find_executable(name)
            if found:
                return found
        return None

    def run(self, cir_file, timeout=5, cwd=None):
        binary = self.find()
        if not binary:
            return False, "", "Xyce not found"
        try:
            # Xyce doesn't use -b; just pass the netlist file
            result = subprocess.run(
                [binary, cir_file],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=timeout, cwd=cwd,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Simulation timed out after {timeout}s"
        except OSError as e:
            return False, "", str(e)

    def format_measurement_block(self, analyses, measurements, output_file,
                                  extra_vars=None):
        """Xyce: .measure statements (note: .measure not .meas)."""
        lines = []

        for analysis_type, spec in analyses:
            lines.append(f".{analysis_type} {spec}")

        for meas in measurements:
            name = meas[0]
            func = meas[1]
            atype = analyses[0][0] if analyses else "ac"

            if func == "when":
                expr, value = meas[2], meas[3]
                lines.append(f".measure {atype} {name} when {expr}={value}")
            elif func == "find":
                expr, at_spec = meas[2], meas[3]
                lines.append(f".measure {atype} {name} find {expr} {at_spec}")
            elif func == "max":
                expr = meas[2]
                lines.append(f".measure {atype} {name} max {expr}")
            elif func == "min":
                expr = meas[2]
                lines.append(f".measure {atype} {name} min {expr}")
            elif func == "let":
                # Xyce doesn't support let — skip
                pass

        return "\n".join(lines)

    def parse_results(self, output_file, stdout, stderr):
        """Parse Xyce .measure results from stdout or .mt0 file.

        Xyce prints: "fc_sim = 1.5917e+04"
        """
        results = {}

        # Try .mt0 file first (Xyce measure output file)
        cir_base = output_file.rsplit(".", 1)[0] if "." in output_file else output_file
        mt0_path = cir_base + ".mt0"
        text = ""
        if os.path.isfile(mt0_path):
            try:
                with open(mt0_path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                text = stdout
        else:
            text = stdout

        for line in text.splitlines():
            line = line.strip()
            m = re.match(r'^(\w+)\s*=\s*([-+]?[\d.eE]+)', line)
            if m:
                results[m.group(1)] = float(m.group(2))

        return results


# ---------------------------------------------------------------------------
# PSpice external-deck backend
# ---------------------------------------------------------------------------

def _on_windows():
    return os.name == "nt"


def _is_native_windows_exe(path):
    return os.path.isabs(path) and path.lower().endswith(".exe")


def _file_signature(path):
    """Return (mtime_ns, size) for a file, or None when it does not exist."""
    try:
        info = path.stat()
    except FileNotFoundError:
        return None
    return info.st_mtime_ns, info.st_size


_NATIVE_LINE_LIMIT = 1_000_000


class _NativeLineTooLong(Exception):
    """A native log line exceeds _NATIVE_LINE_LIMIT characters."""


def _open_native_output(path):
    """Open a native log as text, honoring a UTF-16 or UTF-8 byte-order mark."""
    with path.open("rb") as raw:
        head = raw.read(3)
    if head.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return path.open(encoding="utf-16")
    if head.startswith(codecs.BOM_UTF8):
        return path.open(encoding="utf-8-sig")
    return path.open(encoding="utf-8", errors="replace")


def _bounded_lines(text):
    """Yield stripped lines, as str.splitlines would split them, reading the
    stream in bounded chunks.

    Raises _NativeLineTooLong rather than classify part of an oversized line.
    """
    limit = _NATIVE_LINE_LIMIT
    pending = ""
    while chunk := text.read(limit):
        lines = (pending + chunk).splitlines(keepends=True)
        last = lines[-1]
        pending = lines.pop() if last.splitlines()[0] == last else ""
        if len(pending) > limit or any(
            len(line.splitlines()[0]) > limit for line in lines
        ):
            raise _NativeLineTooLong(
                f"line longer than {limit} characters"
            )
        for line in lines:
            yield line.strip()
    if pending:
        yield pending.strip()


def _kill_process_tree(pid):
    if _on_windows():
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        subprocess.run(
            [
                os.path.join(system_root, "System32", "taskkill.exe"),
                "/F", "/T", "/PID", str(pid),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _run_process_tree(command, cwd, timeout):
    """Run a command and return its exit code, killing its tree on any error.

    Output goes to the null device rather than pipes, so a child process
    that inherits the handles cannot keep the call blocked past the timeout.
    """
    if _on_windows():
        isolation = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    else:
        isolation = {"start_new_session": True}
    with subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **isolation,
    ) as process:
        try:
            return process.wait(timeout=timeout)
        except BaseException:
            # Covers Ctrl-C too: the child is in its own session/group and
            # would otherwise outlive the runner.
            _kill_process_tree(process.pid)
            process.kill()
            process.wait()
            raise

class PspiceBackend(SimulatorBackend):
    """PSpice backend reserved for complete, user-supplied decks."""
    name = "pspice"

    _FATAL_RE = re.compile(r"ERROR\s+--|ERROR\(ORPSIM-", re.IGNORECASE)
    _NOTE_LINE_LIMIT = 200

    @staticmethod
    def native_output_path(deck):
        """Return the .out file PSpice writes next to the deck."""
        return Path(deck).resolve().with_suffix(".out")

    def find(self):
        env_path = os.environ.get("PSPICE_PATH")
        if env_path and os.path.isfile(env_path):
            return os.path.abspath(env_path)
        if _on_windows():
            return self._find_windows_exe()
        for name in ("pspice", "pspice.exe"):
            found = shutil.which(name)
            if found:
                return os.path.abspath(found)
        return None

    @staticmethod
    def _find_windows_exe():
        return find_executable("pspice")

    def _command(self, binary, deck_name, output_name):
        return [binary, "-r", "-e", deck_name, "-o", output_name]

    def run(self, cir_file, timeout=5):
        """Run PSpice on the deck and classify its native output.

        Returns (success, stdout, stderr). The simulator's own stdout and
        stderr are discarded; the native .out file is the record.
        """
        binary = self.find()
        if not binary:
            return (
                False,
                "",
                "PSpice executable not found; set PSPICE_PATH or add "
                "pspice to PATH",
            )
        if _on_windows() and not _is_native_windows_exe(binary):
            return (
                False,
                "",
                "PSpice executable must be an absolute path to a native "
                f".exe program: {binary}",
            )

        deck = Path(cir_file).resolve()
        native_output = self.native_output_path(deck)
        try:
            before = _file_signature(native_output)
        except OSError as exc:
            return (
                False,
                "",
                f"Could not inspect PSpice native output {native_output}: {exc}",
            )
        # "./name" keeps a deck named "-x.cir" from being read as an option.
        command = self._command(
            binary,
            os.path.join(os.curdir, deck.name),
            os.path.join(os.curdir, native_output.name),
        )

        try:
            returncode = _run_process_tree(command, str(deck.parent), timeout)
        except subprocess.TimeoutExpired:
            return False, "", f"Simulation timed out after {timeout}s"
        except OSError as exc:
            return False, "", f"Could not launch PSpice: {exc}"

        if returncode != 0:
            return (
                False,
                "",
                f"PSpice exited with exit code {returncode}",
            )

        try:
            after = _file_signature(native_output)
        except OSError as exc:
            return (
                False,
                "",
                f"Could not inspect PSpice native output {native_output}: {exc}",
            )
        if after is None:
            return (
                False,
                "",
                f"PSpice did not write native output {native_output}",
            )
        if after == before:
            return (
                False,
                "",
                f"PSpice did not update native output {native_output}",
            )
        if after[1] == 0:
            return (
                False,
                "",
                f"PSpice native output is empty: {native_output}",
            )

        try:
            with _open_native_output(native_output) as text:
                note = self._failure_note(_bounded_lines(text))
        except OSError as exc:
            return (
                False,
                "",
                f"Could not read PSpice native output {native_output}: {exc}",
            )
        except UnicodeDecodeError as exc:
            return (
                False,
                "",
                f"Could not decode PSpice native output {native_output}: {exc}",
            )
        except _NativeLineTooLong as exc:
            return (
                False,
                "",
                f"Could not classify PSpice native output {native_output}: "
                f"{exc}",
            )

        if note:
            return False, "", note
        return True, "", ""

    def _failure_note(self, lines):
        # Consume every line, even after a fatal one, so a decode error
        # anywhere in the log is still reported.
        fatal = None
        aborted = concluded = False
        for line in lines:
            if fatal is None and self._FATAL_RE.match(line):
                fatal = line
            aborted = aborted or line == "JOB ABORTED"
            concluded = concluded or line == "JOB CONCLUDED"
        if fatal is not None:
            return (
                "PSpice native fatal error line found: "
                f"{fatal[:self._NOTE_LINE_LIMIT]}"
            )
        if aborted:
            return "PSpice native abort marker found: JOB ABORTED"
        if not concluded:
            return "PSpice completion marker missing: JOB CONCLUDED"
        return None

    def format_measurement_block(self, analyses, measurements, output_file,
                                 extra_vars=None):
        raise NotImplementedError(
            "PSpice generated-testbench measurements are not supported; "
            "use run_external_deck.py with a complete external deck"
        )

    def parse_results(self, output_file, stdout, stderr):
        raise NotImplementedError(
            "PSpice generated-testbench result parsing is not supported; "
            "use run_external_deck.py with a complete external deck"
        )


# ---------------------------------------------------------------------------
# Backend registry and auto-detection
# ---------------------------------------------------------------------------

BACKENDS = {
    "ngspice": NgspiceBackend,
    "ltspice": LtspiceBackend,
    "xyce": XyceBackend,
}


def detect_simulator(preference="auto"):
    """Find an available simulator.

    Args:
        preference: "auto" to try all in order, or a specific name

    Returns:
        SimulatorBackend instance, or None if nothing found
    """
    # Check env var override
    if preference == "auto":
        env_pref = os.environ.get("SPICE_SIMULATOR", "").lower()
        if env_pref in BACKENDS:
            preference = env_pref

    if preference != "auto":
        backend_cls = BACKENDS.get(preference)
        if backend_cls:
            backend = backend_cls()
            if backend.find():
                return backend
        return None

    # Auto-detect: try ngspice first (most common), then LTspice, then Xyce
    for backend_cls in [NgspiceBackend, LtspiceBackend, XyceBackend]:
        backend = backend_cls()
        if backend.find():
            return backend

    return None
