"""
SPICE simulator backend abstraction.

Supports ngspice, LTspice, and Xyce with a unified interface for finding
the binary, running simulations, formatting measurement commands, and
parsing results. The circuit netlist is portable — only the measurement
layer and output parsing differ between simulators.

Auto-detection tries ngspice → LTspice → Xyce. Override with --simulator
flag or SPICE_SIMULATOR environment variable.
"""

import os
import re
import shutil
import subprocess
import sys


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
        found = shutil.which("ngspice")
        if found:
            return os.path.abspath(found)
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
                [binary, "-b", cir_file],
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

        # Add extra variables
        if extra_vars:
            for key, val in extra_vars.items():
                echo_vars.append(f"{key}={val}")

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
            found = shutil.which(name)
            if found:
                return os.path.abspath(found)

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
        wine = shutil.which("wine")
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
            found = shutil.which(name)
            if found:
                return os.path.abspath(found)
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
