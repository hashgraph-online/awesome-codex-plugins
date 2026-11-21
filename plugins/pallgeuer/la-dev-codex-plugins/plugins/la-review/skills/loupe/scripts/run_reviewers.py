#!/usr/bin/env python3
"""Run configured Loupe reviewer commands and emit structured JSON.

This Python script must support Python 3.6+.
"""

import argparse
import json
import math
import os
import pathlib
import re
import shlex
import signal
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from typing import Any, BinaryIO, Dict, List, Mapping, Optional, Sequence

DEFAULT_TIMEOUT_SECONDS = 30 * 60
PROCESS_TERMINATION_SECONDS = 5
NO_LAUNCHABLE_REVIEWERS_MESSAGE = "No launchable reviewers are available."
MISSING_ADDITIONAL_EXECUTABLE_MESSAGE_TEMPLATE = "Missing additional executable '{}' for {}. Please install {} and rerun Loupe."

CODEX_COMMAND_TEMPLATE = """( set -o pipefail; codex exec --cd "$(git rev-parse --show-toplevel)" --ephemeral --sandbox workspace-write -c model_reasoning_effort='"{reasoning_effort}"' --json {prompt} | jq -ser 'map(select(.type == "item.completed" and .item.type == "agent_message") | .item.text) | last // empty' )"""
CLAUDE_COMMAND_TEMPLATE = """( set -o pipefail; cd "$(git rev-parse --show-toplevel)" && claude -p --session-id {session_id} --permission-mode auto --effort {reasoning_effort} --output-format json {prompt} | jq -er ".result" )"""  # fmt: skip

REVIEW_SKILL_PROHIBITION = "Do not launch any kind of review skill."
REVIEW_POLICY = "Review only. Do not modify repository files, stage changes, commit, install dependencies, or use external network access except normal web search. You may inspect files and run local validation, including manual tests; incidental temp/cache artifacts are okay."
REVIEW_NOTE = "{} {}".format(REVIEW_SKILL_PROHIBITION, REVIEW_POLICY)

CODE_REVIEW_COMMAND_PROMPT_TEMPLATE = "{review_policy} /code-review {review_scope}"
REVIEW_COMMAND_PROMPT_TEMPLATE = "{review_policy} /review {review_scope}"
CORRECTNESS_REVIEW_PROMPT_TEMPLATE = """Review scope: {review_scope}
Task: It is very important to me that the code now works completely correctly and as intended, and robustly performs the exact required actions in all cases without the risk of unintended side-effects. Carefully analyze the code in detail to ensure this. Construct and run a large number of manual tests to test all conceivable unusual/complex/mixed situations, as well as special/edge cases, and on purposely try to find (in an adversarial manner) manual tests that make the current implementation fail or do the wrong thing. Explicitly consider measured test code coverage, if possible. If a manual test fails, then think critically whether the expectation of the test is truly correct or the current implementation behavior is actually truly correct.
Note: {review_note}"""
DESIGN_REVIEW_PROMPT_TEMPLATE = """Review scope: {review_scope}
Task: It is very important to me that the code is well-structured, well-organized, maintainable long-term, has clean/meaningful interfaces/contracts/abstraction boundaries throughout, and exhibits good design patterns/architectural choices. Carefully analyze the code in detail to ensure this, and identify any code smells/recommended refactoring opportunities. Search also explicitly for any duplicated logic, unnecessary thin wrappers, dead code, old compatibility code that is no longer needed, and unnecessarily inefficient code.
Note: {review_note}"""


class ReasoningEffortProvider:
    """Validated reasoning-effort policy shared by one reviewer provider."""

    __slots__ = ("allowed_reasoning_efforts", "default_reasoning_effort", "provider_key")

    def __init__(self, provider_key: str, default_reasoning_effort: str, allowed_reasoning_efforts: Sequence[str]) -> None:
        """Store provider identity, default effort, and supported efforts."""
        self.provider_key = provider_key
        self.default_reasoning_effort = default_reasoning_effort
        self.allowed_reasoning_efforts = tuple(allowed_reasoning_efforts)


CLAUDE_PROVIDER = ReasoningEffortProvider("claude", "medium", ("low", "medium", "high", "xhigh", "max"))
CODEX_PROVIDER = ReasoningEffortProvider("codex", "high", ("minimal", "low", "medium", "high", "xhigh", "max", "ultra"))
PROVIDERS = (CLAUDE_PROVIDER, CODEX_PROVIDER)


class Reviewer:
    """Command and prompt template for one external reviewer."""

    def __init__(
        self,
        reviewer_name: str,
        command_template: str,
        prompt_template: str,
        required_executable: Optional[str] = None,
        additional_required_executables: Sequence[str] = (),
        reviewer_key: Optional[str] = None,
        provider: Optional[ReasoningEffortProvider] = None,
        persistent_session: bool = False,
    ) -> None:
        """Store reviewer identity, templates, configuration keys, executables, and session policy."""
        self.reviewer_name = reviewer_name
        self.command_template = command_template
        self.prompt_template = prompt_template
        self.required_executable = required_executable
        self.additional_required_executables = tuple(additional_required_executables)
        self.reviewer_key = reviewer_key
        self.provider = provider
        self.persistent_session = persistent_session

    def build_prompt(self, review_scope: str) -> str:
        """Return the complete prompt passed to this reviewer for a scope."""
        return self.prompt_template.format(review_scope=review_scope, review_policy=REVIEW_POLICY, review_skill_prohibition=REVIEW_SKILL_PROHIBITION, review_note=REVIEW_NOTE)

    def build_command(self, review_scope: str, reasoning_effort: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Return the launched shell command for this reviewer, scope, effort, and assigned session."""
        if self.persistent_session and session_id is None:
            raise ValueError("persistent reviewer '{}' requires a session ID".format(self.reviewer_name))
        resolved_reasoning_effort = reasoning_effort
        if resolved_reasoning_effort is None and self.provider is not None:
            resolved_reasoning_effort = self.provider.default_reasoning_effort
        return self.command_template.format(
            prompt=shlex.quote(self.build_prompt(review_scope)),
            reasoning_effort=resolved_reasoning_effort or "",
            session_id=shlex.quote(session_id or ""),
        )


class ReviewerRun:
    """Mutable execution state for one launched reviewer process."""

    def __init__(
        self,
        reviewer: Reviewer,
        launched_command: str,
        launch_error: Optional[str] = None,
        session_id: Optional[str] = None,
        session_log_path: Optional[str] = None,
    ) -> None:
        """Initialize process, timing, output, and persistent-session fields."""
        self.reviewer = reviewer
        self.launched_command = launched_command
        self.session_id = session_id
        self.session_log_path = session_log_path
        self.process = None  # type: Optional[subprocess.Popen[Any]]
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.stdout = ""
        self.stderr = ""
        self.launch_error = launch_error
        self.collection_error: Optional[str] = None
        self.thread: Optional[threading.Thread] = None
        self.stdout_file: Optional[BinaryIO] = None
        self.stderr_file: Optional[BinaryIO] = None
        self.timed_out = False

    def launch(self) -> None:
        """Start the reviewer process and begin collecting its output."""
        try:
            self.stdout_file = tempfile.TemporaryFile(mode="w+b")  # noqa: SIM115
            self.stderr_file = tempfile.TemporaryFile(mode="w+b")  # noqa: SIM115
            self.started_at = time.monotonic()
            self.process = subprocess.Popen(
                ["bash", "-lc", self.launched_command],
                stdout=self.stdout_file,
                stderr=self.stderr_file,
                universal_newlines=True,
                start_new_session=True,
            )
        except OSError as exc:
            self.launch_error = str(exc)
            self.finished_at = time.monotonic()
            self.close()
            return

        self.thread = threading.Thread(target=self._collect_output)
        self.thread.daemon = True
        self.thread.start()

    def _collect_output(self) -> None:
        """Wait for the process to finish and capture stdout and stderr."""
        if self.process is None:
            self.finished_at = time.monotonic()
            return
        try:
            self.process.wait()
            self._refresh_output()
        except OSError as exc:
            self.collection_error = str(exc)
        self.finished_at = time.monotonic()

    def _read_output_file(self, output_file: BinaryIO) -> str:
        """Return current text from a temporary output file."""
        output_file.flush()
        output_file.seek(0)
        return output_file.read().decode("utf-8", errors="replace")

    def _refresh_output(self) -> None:
        """Read any output captured so far from temporary files."""
        if self.stdout_file is not None:
            self.stdout = self._read_output_file(self.stdout_file)
        if self.stderr_file is not None:
            self.stderr = self._read_output_file(self.stderr_file)

    def close(self) -> None:
        """Close temporary output files."""
        for output_file in (self.stdout_file, self.stderr_file):
            if output_file is not None:
                output_file.close()
        self.stdout_file = None
        self.stderr_file = None

    def is_running(self) -> bool:
        """Return whether the reviewer process is still being collected."""
        return self.thread is not None and self.thread.is_alive()

    def elapsed_seconds(self) -> float:
        """Return elapsed reviewer runtime in seconds."""
        if self.started_at is None:
            return 0.0
        finished_at = self.finished_at
        if finished_at is None:
            finished_at = time.monotonic()
        return round(finished_at - self.started_at, 3)

    def return_code(self) -> Optional[int]:
        """Return the subprocess return code when a process was launched."""
        if self.process is None:
            return None
        return self.process.returncode

    def status(self) -> str:
        """Return the normalized status string for this reviewer run."""
        if self.launch_error is not None:
            return "launch_failed"
        if self.timed_out:
            return "timed_out"
        if self.collection_error is not None:
            return "failed"
        if self.return_code() == 0:
            return "succeeded"
        return "failed"

    def result(self) -> Dict[str, Any]:
        """Return the JSON-serializable reviewer result."""
        stderr_parts: List[str] = []
        try:
            self._refresh_output()
        except OSError as exc:
            self.collection_error = str(exc)
        if self.stderr:
            stderr_parts.append(self.stderr)
        if self.launch_error is not None:
            stderr_parts.append(self.launch_error)
        if self.collection_error is not None:
            stderr_parts.append(self.collection_error)
        return {
            "reviewer_name": self.reviewer.reviewer_name,
            "launched_command": self.launched_command,
            "session_id": self.session_id,
            "session_log_path": self.session_log_path,
            "status": self.status(),
            "timed_out": self.timed_out,
            "return_code": self.return_code(),
            "elapsed_seconds": self.elapsed_seconds(),
            "stdout": self.stdout,
            "stderr": "\n".join(stderr_parts),
        }


REVIEWERS = (
    Reviewer(
        reviewer_name="Claude Code Review",
        command_template=CLAUDE_COMMAND_TEMPLATE,
        prompt_template=CODE_REVIEW_COMMAND_PROMPT_TEMPLATE,
        required_executable="claude",
        additional_required_executables=("jq",),
        reviewer_key="claude-code-review",
        provider=CLAUDE_PROVIDER,
        persistent_session=True,
    ),
    Reviewer(
        reviewer_name="Codex Review",
        command_template=CODEX_COMMAND_TEMPLATE,
        prompt_template=REVIEW_COMMAND_PROMPT_TEMPLATE,
        required_executable="codex",
        additional_required_executables=("jq",),
        reviewer_key="codex-review",
        provider=CODEX_PROVIDER,
    ),
    Reviewer(
        reviewer_name="Codex Correctness",
        command_template=CODEX_COMMAND_TEMPLATE,
        prompt_template=CORRECTNESS_REVIEW_PROMPT_TEMPLATE,
        required_executable="codex",
        additional_required_executables=("jq",),
        reviewer_key="codex-correctness",
        provider=CODEX_PROVIDER,
    ),
    Reviewer(
        reviewer_name="Codex Design",
        command_template=CODEX_COMMAND_TEMPLATE,
        prompt_template=DESIGN_REVIEW_PROMPT_TEMPLATE,
        required_executable="codex",
        additional_required_executables=("jq",),
        reviewer_key="codex-design",
        provider=CODEX_PROVIDER,
    ),
)


def executable_is_available(executable: str) -> bool:
    """Return whether the reviewer launch shell can resolve an executable."""
    try:
        completed = subprocess.run(
            ["bash", "-lc", "command -v {}".format(shlex.quote(executable))],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0


def claude_config_root(environment: Mapping[str, str], git_root: Optional[str]) -> str:
    """Return Claude's absolute configuration root for the reviewer launch environment."""
    configured_root = environment.get("CLAUDE_CONFIG_DIR")
    expanded_root = pathlib.Path(configured_root or "~/.claude").expanduser()
    if not expanded_root.is_absolute():
        expanded_root = pathlib.Path(git_root) / expanded_root if git_root is not None else pathlib.Path.cwd() / expanded_root
    return str(expanded_root.absolute())


def claude_session_log_path(environment: Mapping[str, str], git_root: Optional[str], session_id: str) -> Optional[str]:
    """Return the expected absolute Claude transcript path for one assigned session."""
    if git_root is None:
        return None
    project_storage_name = re.sub(r"[^A-Za-z0-9]", "-", git_root)
    return str(pathlib.Path(claude_config_root(environment, git_root)) / "projects" / project_storage_name / "{}.jsonl".format(session_id))


def reviewer_launch_plan(
    reviewers: Sequence[Reviewer],
    review_scope: str,
    reasoning_efforts: Optional[Mapping[str, str]] = None,
    git_root: Optional[str] = None,
    environment: Optional[Mapping[str, str]] = None,
) -> List[ReviewerRun]:
    """Return reviewer runs that can launch or fail with planned session metadata and errors."""
    availability_cache: Dict[str, bool] = {}
    resolved_reasoning_efforts = reasoning_efforts or {}
    active_environment = os.environ if environment is None else environment
    runs: List[ReviewerRun] = []
    for reviewer in reviewers:
        required_executable = reviewer.required_executable
        if required_executable is not None and required_executable not in availability_cache:
            availability_cache[required_executable] = executable_is_available(required_executable)
        if required_executable is not None and not availability_cache[required_executable]:
            continue
        launch_errors = []
        for executable in reviewer.additional_required_executables:
            if executable not in availability_cache:
                availability_cache[executable] = executable_is_available(executable)
            if not availability_cache[executable]:
                launch_errors.append(MISSING_ADDITIONAL_EXECUTABLE_MESSAGE_TEMPLATE.format(executable, reviewer.reviewer_name, executable))
        launch_error = "\n".join(launch_errors) if launch_errors else None
        reasoning_effort = resolved_reasoning_efforts.get(reviewer.reviewer_key) if reviewer.reviewer_key is not None else None
        session_id = str(uuid.uuid4()) if reviewer.persistent_session else None
        session_log_path = claude_session_log_path(active_environment, git_root, session_id) if session_id is not None else None
        runs.append(
            ReviewerRun(
                reviewer=reviewer,
                launched_command=reviewer.build_command(review_scope, reasoning_effort, session_id),
                launch_error=launch_error,
                session_id=session_id,
                session_log_path=session_log_path,
            )
        )
    return runs


def provider_registry(providers: Sequence[ReasoningEffortProvider]) -> Dict[str, ReasoningEffortProvider]:
    """Return validated providers keyed by their stable configuration key."""
    registry: Dict[str, ReasoningEffortProvider] = {}
    for provider in providers:
        if not isinstance(provider, ReasoningEffortProvider):
            raise ValueError("reasoning-effort providers must be ReasoningEffortProvider instances")
        if not isinstance(provider.provider_key, str) or not provider.provider_key:
            raise ValueError("reasoning-effort provider keys must be nonempty strings")
        if provider.provider_key in registry:
            raise ValueError("duplicate reasoning-effort provider key '{}'".format(provider.provider_key))
        if not provider.allowed_reasoning_efforts or len(set(provider.allowed_reasoning_efforts)) != len(provider.allowed_reasoning_efforts):
            raise ValueError("reasoning-effort provider '{}' must define unique allowed efforts".format(provider.provider_key))
        if any(not isinstance(effort, str) or not effort for effort in provider.allowed_reasoning_efforts):
            raise ValueError("reasoning-effort provider '{}' has an invalid allowed effort".format(provider.provider_key))
        if provider.default_reasoning_effort not in provider.allowed_reasoning_efforts:
            raise ValueError("reasoning-effort provider '{}' default '{}' is not allowed".format(provider.provider_key, provider.default_reasoning_effort))
        registry[provider.provider_key] = provider
    return registry


def effort_key_providers(reviewers: Sequence[Reviewer], providers: Sequence[ReasoningEffortProvider] = PROVIDERS) -> Dict[str, ReasoningEffortProvider]:
    """Return validated provider and reviewer effort keys mapped to providers."""
    registry = provider_registry(providers)
    key_providers = dict(registry)
    for reviewer in reviewers:
        if not isinstance(reviewer, Reviewer):
            raise ValueError("reviewers must be Reviewer instances")
        if (reviewer.reviewer_key is None) != (reviewer.provider is None):
            raise ValueError("reviewer '{}' must configure both reviewer_key and provider or neither".format(reviewer.reviewer_name))
        if reviewer.reviewer_key is None:
            continue
        if not isinstance(reviewer.reviewer_key, str) or not reviewer.reviewer_key:
            raise ValueError("reviewer '{}' has an invalid reviewer key".format(reviewer.reviewer_name))
        if reviewer.reviewer_key in key_providers:
            raise ValueError("duplicate or colliding reasoning-effort key '{}'".format(reviewer.reviewer_key))
        provider = reviewer.provider
        if provider is None:
            raise AssertionError("validated reviewer provider is unexpectedly absent")
        registered_provider = registry.get(provider.provider_key)
        if registered_provider is not provider:
            raise ValueError("reviewer '{}' references unregistered provider '{}'".format(reviewer.reviewer_name, provider.provider_key))
        key_providers[reviewer.reviewer_key] = provider
    return key_providers


def effort_environment_variable(effort_key: str) -> str:
    """Return the environment variable corresponding to an effort key."""
    return "LOUPE_EFFORT_{}".format(effort_key.upper().replace("-", "_"))


def validate_reasoning_effort(effort_key: str, reasoning_effort: str, source: str, key_providers: Mapping[str, ReasoningEffortProvider]) -> str:
    """Return a valid provider-specific reasoning effort or raise a configuration error."""
    provider = key_providers.get(effort_key)
    if provider is None:
        raise ValueError("{} uses unknown reasoning-effort key '{}' (choose from: {})".format(source, effort_key, ", ".join(sorted(key_providers))))
    allowed_reasoning_efforts = provider.allowed_reasoning_efforts
    if reasoning_effort not in allowed_reasoning_efforts:
        raise ValueError("{} sets invalid {} reasoning effort '{}' (choose from: {})".format(source, provider.provider_key, reasoning_effort, ", ".join(allowed_reasoning_efforts)))
    return reasoning_effort


def parse_cli_effort_overrides(assignments: Sequence[str], key_providers: Mapping[str, ReasoningEffortProvider]) -> Dict[str, str]:
    """Parse repeatable KEY=VALUE effort assignments, with later values taking precedence."""
    overrides: Dict[str, str] = {}
    for assignment in assignments:
        effort_key, separator, reasoning_effort = assignment.partition("=")
        effort_key = effort_key.strip()
        reasoning_effort = reasoning_effort.strip()
        if not separator or not effort_key or not reasoning_effort:
            raise ValueError("--effort value '{}' must use KEY=VALUE with nonblank fields".format(assignment))
        overrides[effort_key] = validate_reasoning_effort(effort_key, reasoning_effort, "--effort", key_providers)
    return overrides


def environment_effort_overrides(environment: Mapping[str, str], key_providers: Mapping[str, ReasoningEffortProvider]) -> Dict[str, str]:
    """Return validated effort overrides from recognized Loupe environment variables."""
    overrides: Dict[str, str] = {}
    for effort_key in key_providers:
        variable = effort_environment_variable(effort_key)
        if variable in environment:
            reasoning_effort = environment[variable].strip()
            overrides[effort_key] = validate_reasoning_effort(effort_key, reasoning_effort, variable, key_providers)
    return overrides


def resolve_reasoning_efforts(reviewers: Sequence[Reviewer], cli_overrides: Mapping[str, str], environment_overrides: Mapping[str, str]) -> Dict[str, str]:
    """Resolve each configurable reviewer effort using CLI, environment, and built-in precedence."""
    reasoning_efforts: Dict[str, str] = {}
    for reviewer in reviewers:
        if reviewer.reviewer_key is None or reviewer.provider is None:
            continue
        provider_key = reviewer.provider.provider_key
        if reviewer.reviewer_key in cli_overrides:
            reasoning_effort = cli_overrides[reviewer.reviewer_key]
        elif provider_key in cli_overrides:
            reasoning_effort = cli_overrides[provider_key]
        elif reviewer.reviewer_key in environment_overrides:
            reasoning_effort = environment_overrides[reviewer.reviewer_key]
        elif provider_key in environment_overrides:
            reasoning_effort = environment_overrides[provider_key]
        else:
            reasoning_effort = reviewer.provider.default_reasoning_effort
        reasoning_efforts[reviewer.reviewer_key] = reasoning_effort
    return reasoning_efforts


def timeout_seconds(value: str) -> float:
    """Parse one finite nonnegative reviewer timeout."""
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a finite nonnegative number") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise argparse.ArgumentTypeError("timeout must be a finite nonnegative number")
    return parsed


def parse_args(argv: Optional[Sequence[str]], reviewers: Sequence[Reviewer] = REVIEWERS, environment: Optional[Mapping[str, str]] = None) -> argparse.Namespace:
    """Parse runner arguments and resolve validated reviewer reasoning efforts."""
    parser = argparse.ArgumentParser(description="Run external Loupe reviewers and emit structured JSON.")
    parser.add_argument("scope", help="Review scope text.")
    parser.add_argument("--timeout-seconds", type=timeout_seconds, default=DEFAULT_TIMEOUT_SECONDS, help="Global reviewer timeout in seconds.")
    parser.add_argument("--output", help="Path where the exact emitted JSON should also be written.")
    parser.add_argument("--dry-run", action="store_true", help="Print the commands that would run without launching reviewers.")
    parser.add_argument("--effort", action="append", default=[], metavar="KEY=VALUE", help="Override a provider or reviewer reasoning effort; may be repeated.")
    args = parser.parse_args(argv)
    args.review_scope = args.scope.strip()
    if not args.review_scope:
        parser.error("review scope must not be empty")
    active_environment = os.environ if environment is None else environment
    try:
        key_providers = effort_key_providers(reviewers)
        cli_overrides = parse_cli_effort_overrides(args.effort, key_providers)
        environment_overrides = environment_effort_overrides(active_environment, key_providers)
    except ValueError as exc:
        parser.error(str(exc))
    args.reasoning_efforts = resolve_reasoning_efforts(reviewers, cli_overrides, environment_overrides)
    return args


def get_repo_root() -> Optional[str]:
    """Return the current Git repository root, if available."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def send_process_group_signal(process, signal_number):  # type: (subprocess.Popen[Any], signal.Signals) -> None
    """Send a signal to a launched reviewer process group."""
    try:
        os.killpg(process.pid, signal_number)
    except ProcessLookupError:
        return


def launch_reviewer_runs(runs: Sequence[ReviewerRun]) -> None:
    """Launch every reviewer run."""
    for run in runs:
        if run.launch_error is not None:
            continue
        run.launch()


def wait_for_reviewer_runs(runs: Sequence[ReviewerRun], timeout_seconds: float) -> None:
    """Wait for reviewer runs until completion or the global timeout."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        running = [run for run in runs if run.is_running()]
        if not running:
            return
        if time.monotonic() >= deadline:
            for run in running:
                run.timed_out = True
                if run.process is not None:
                    send_process_group_signal(run.process, signal.SIGTERM)
            break
        time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))

    termination_deadline = time.monotonic() + PROCESS_TERMINATION_SECONDS
    for run in running:
        if run.thread is not None:
            run.thread.join(max(0.0, termination_deadline - time.monotonic()))
    for run in running:
        if run.is_running() and run.process is not None:
            send_process_group_signal(run.process, signal.SIGKILL)
    kill_deadline = time.monotonic() + PROCESS_TERMINATION_SECONDS
    for run in runs:
        if run.thread is not None:
            run.thread.join(max(0.0, kill_deadline - time.monotonic()))


def result_exit_code(results: Sequence[Dict[str, Any]]) -> int:
    """Return zero only when every reviewer succeeded."""
    if results and all(result["status"] == "succeeded" for result in results):
        return 0
    return 1


def dry_run_output(review_scope: str, git_root: Optional[str], timeout_seconds: float, runs: Sequence[ReviewerRun]) -> Dict[str, Any]:
    """Return the dry-run JSON payload without reviewer result fields."""
    return {
        "review_scope": review_scope,
        "git_root": git_root,
        "timeout_seconds": timeout_seconds,
        "reviewers": [
            {
                "reviewer_name": run.reviewer.reviewer_name,
                "launched_command": run.launched_command,
                "session_id": run.session_id,
                "session_log_path": run.session_log_path,
            }
            for run in runs
        ],
    }


def review_output(review_scope: str, git_root: Optional[str], timeout_seconds: float, elapsed_seconds: float, results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the completed review JSON payload."""
    return {
        "review_scope": review_scope,
        "git_root": git_root,
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": elapsed_seconds,
        "reviewers": list(results),
    }


def emit_json_output(payload: Dict[str, Any], output_path: Optional[str]) -> None:
    """Write identical JSON text to stdout and an optional artifact path."""
    output = json.dumps(payload, indent=2, allow_nan=False) + "\n"
    sys.stdout.write(output)
    if output_path is not None:
        with pathlib.Path(output_path).open("w", encoding="utf-8") as output_file:
            output_file.write(output)


def emit_no_launchable_reviewers_message() -> None:
    """Report that every configured reviewer was filtered out."""
    sys.stderr.write("{}\n".format(NO_LAUNCHABLE_REVIEWERS_MESSAGE))


def emit_launch_error_messages(runs: Sequence[ReviewerRun]) -> None:
    """Report missing helper executables for launchable reviewers."""
    for run in runs:
        if run.launch_error is not None:
            sys.stderr.write("{}\n".format(run.launch_error))


def main(argv: Optional[Sequence[str]] = None, reviewers: Sequence[Reviewer] = REVIEWERS, environment: Optional[Mapping[str, str]] = None) -> int:
    """Run configured external reviewers with environment and CLI effort overrides."""
    active_environment = os.environ if environment is None else environment
    args = parse_args(argv, reviewers=reviewers, environment=active_environment)
    git_root = get_repo_root()
    runs = reviewer_launch_plan(reviewers, args.review_scope, args.reasoning_efforts, git_root=git_root, environment=active_environment)
    if args.dry_run:
        emit_json_output(dry_run_output(args.review_scope, git_root, args.timeout_seconds, runs), args.output)
        if not runs:
            emit_no_launchable_reviewers_message()
            return 1
        if any(run.launch_error is not None for run in runs):
            emit_launch_error_messages(runs)
            return 1
        return 0
    if not runs:
        emit_json_output(review_output(args.review_scope, git_root, args.timeout_seconds, 0.0, []), args.output)
        emit_no_launchable_reviewers_message()
        return 1

    try:
        started_at = time.monotonic()
        launch_reviewer_runs(runs)
        wait_for_reviewer_runs(runs, args.timeout_seconds)
        elapsed_seconds = round(time.monotonic() - started_at, 3)
        results = [run.result() for run in runs]
        emit_json_output(review_output(args.review_scope, git_root, args.timeout_seconds, elapsed_seconds, results), args.output)
        return result_exit_code(results)
    finally:
        for run in runs:
            run.close()


if __name__ == "__main__":
    sys.exit(main())
