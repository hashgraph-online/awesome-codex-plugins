"""Plan and run bounded development-skills checks with Pydantic Evals."""

from __future__ import annotations

import argparse
import asyncio
import fnmatch
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

try:
    import logfire
except ImportError:  # logfire extra absent: tracing becomes a no-op
    import logfire_api as logfire
from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext
from pydantic_evals.lifecycle import CaseLifecycle
from pydantic_evals.reporting import ReportCase, ReportCaseFailure


@dataclass(frozen=True)
class FileContains:
    path: str
    text: str


@dataclass(frozen=True)
class ToolInputMatch:
    tool: str
    field: str
    contains: str


@dataclass(frozen=True)
class ToolCall:
    name: str
    input: Any
    group: int


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass(frozen=True)
class Scenario:
    identifier: str
    prompt: str
    files: dict[str, str] = field(default_factory=dict)
    required_tools: tuple[str, ...] = ()
    clean_worktree: bool | None = None
    file_contains: tuple[FileContains, ...] = ()
    transcript_contains: tuple[str, ...] = ()
    tags: tuple[str, ...] = ("workflow",)
    covers: tuple[str, ...] = ()
    agents: tuple[str, ...] = ("claude", "codex")
    mode: str = "workflow"
    exact_changed_files: tuple[str, ...] | None = None
    forbidden_tools: tuple[str, ...] = ()
    file_not_contains: tuple[FileContains, ...] = ()
    tool_sequence: tuple[ToolInputMatch, ...] = ()


@dataclass(frozen=True)
class TrialResult:
    returncode: int
    transcript: str
    stderr: str = ""
    changed_files: tuple[str, ...] = ()
    file_contents: tuple[tuple[str, str | None], ...] = ()
    duration_seconds: float = 0.0
    token_usage: TokenUsage = field(default_factory=TokenUsage)


def _string_list(item: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = item.get(key, list(default))
    if not isinstance(value, list) or not all(
        isinstance(element, str) and element for element in value
    ):
        raise ValueError(f"{item.get('id', 'case')}: {key} must be non-empty strings")
    if key != "covers" and not value:
        raise ValueError(f"{item.get('id', 'case')}: {key} must not be empty")
    return tuple(value)


def load_scenarios(path: Path) -> list[Scenario]:
    data = json.loads(path.read_text())
    if not isinstance(data.get("cases"), list):
        raise ValueError("cases must be a list")
    scenarios: list[Scenario] = []
    identifiers: set[str] = set()
    for item in data["cases"]:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"]:
            raise ValueError("every case needs a non-empty string id")
        if item["id"] in identifiers:
            raise ValueError(f"duplicate case id: {item['id']}")
        identifiers.add(item["id"])
        if not isinstance(item.get("prompt"), str) or not item["prompt"]:
            raise ValueError(f"{item['id']}: prompt must be a non-empty string")
        files = item.get("files", {})
        if not isinstance(files, dict) or not all(
            isinstance(relative, str) and isinstance(content, str)
            for relative, content in files.items()
        ):
            raise ValueError(f"{item['id']}: files must map string paths to string content")
        assertions = item.get("assertions", [])
        allowed = {
            "tool",
            "tool_not",
            "clean_worktree",
            "changed_files_exact",
            "file_contains",
            "file_not_contains",
            "transcript_contains",
            "tool_sequence",
        }
        if not isinstance(assertions, list) or not all(
            isinstance(assertion, dict) and set(assertion) <= allowed and len(assertion) == 1
            for assertion in assertions
        ):
            raise ValueError(f"{item['id']}: each assertion must be one executable check")
        for assertion in assertions:
            if "clean_worktree" in assertion and not isinstance(assertion["clean_worktree"], bool):
                raise ValueError(f"{item['id']}: clean_worktree must be a boolean")
            if "tool" in assertion and not isinstance(assertion["tool"], str):
                raise ValueError(f"{item['id']}: tool must be a string")
            if "tool_not" in assertion and not isinstance(assertion["tool_not"], str):
                raise ValueError(f"{item['id']}: tool_not must be a string")
            if "changed_files_exact" in assertion and (
                not isinstance(assertion["changed_files_exact"], list)
                or not all(isinstance(value, str) for value in assertion["changed_files_exact"])
            ):
                raise ValueError(f"{item['id']}: changed_files_exact must be a string list")
            if "transcript_contains" in assertion and not isinstance(
                assertion["transcript_contains"], str
            ):
                raise ValueError(f"{item['id']}: transcript_contains must be a string")
            for key in ("file_contains", "file_not_contains"):
                if key not in assertion:
                    continue
                check = assertion[key]
                if (
                    not isinstance(check, dict)
                    or set(check) != {"path", "text"}
                    or not all(isinstance(value, str) for value in check.values())
                ):
                    raise ValueError(f"{item['id']}: {key} needs string path and text")
            if "tool_sequence" in assertion:
                sequence = assertion["tool_sequence"]
                if (
                    not isinstance(sequence, list)
                    or len(sequence) < 2
                    or not all(
                        isinstance(match, dict)
                        and set(match) == {"tool", "field", "contains"}
                        and all(isinstance(value, str) and value for value in match.values())
                        for match in sequence
                    )
                ):
                    raise ValueError(
                        f"{item['id']}: tool_sequence needs at least two tool/field/contains matches"
                    )
        tags = _string_list(item, "tags", ("workflow",))
        covers = _string_list(item, "covers", ())
        agents = _string_list(item, "agents", ("claude", "codex"))
        if not set(agents) <= {"claude", "codex"}:
            raise ValueError(f"{item['id']}: agents must contain claude or codex")
        mode = item.get("mode", "workflow")
        if mode not in {"workflow", "routing"}:
            raise ValueError(f"{item['id']}: mode must be workflow or routing")
        if mode == "routing" and agents != ("claude",):
            raise ValueError(f"{item['id']}: routing cases currently support claude only")
        if mode == "routing" and (
            not any("tool" in assertion for assertion in assertions)
            or any(set(assertion) - {"tool", "tool_not"} for assertion in assertions)
        ):
            raise ValueError(f"{item['id']}: routing cases may assert only tool and tool_not")
        scenarios.append(
            Scenario(
                identifier=item["id"],
                prompt=item["prompt"],
                files=files,
                required_tools=tuple(
                    assertion["tool"] for assertion in assertions if "tool" in assertion
                ),
                clean_worktree=next(
                    (
                        assertion["clean_worktree"]
                        for assertion in assertions
                        if "clean_worktree" in assertion
                    ),
                    None,
                ),
                file_contains=tuple(
                    FileContains(**assertion["file_contains"])
                    for assertion in assertions
                    if "file_contains" in assertion
                ),
                transcript_contains=tuple(
                    assertion["transcript_contains"]
                    for assertion in assertions
                    if "transcript_contains" in assertion
                ),
                tags=tags,
                covers=covers,
                agents=agents,
                mode=mode,
                exact_changed_files=next(
                    (
                        tuple(assertion["changed_files_exact"])
                        for assertion in assertions
                        if "changed_files_exact" in assertion
                    ),
                    None,
                ),
                forbidden_tools=tuple(
                    assertion["tool_not"] for assertion in assertions if "tool_not" in assertion
                ),
                file_not_contains=tuple(
                    FileContains(**assertion["file_not_contains"])
                    for assertion in assertions
                    if "file_not_contains" in assertion
                ),
                tool_sequence=next(
                    (
                        tuple(ToolInputMatch(**match) for match in assertion["tool_sequence"])
                        for assertion in assertions
                        if "tool_sequence" in assertion
                    ),
                    (),
                ),
            )
        )
    return scenarios


def _plugin_relative(path: str) -> str:
    marker = "plugins/development-skills/"
    return path.split(marker, 1)[1] if marker in path else path


def _covers_change(pattern: str, changed: str) -> bool:
    if fnmatch.fnmatchcase(changed, pattern):
        return True
    if pattern.endswith("/SKILL.md"):
        return changed.startswith(pattern.removesuffix("SKILL.md"))
    return False


def select_scenarios(
    scenarios: list[Scenario],
    *,
    agent: str,
    identifiers: tuple[str, ...] = (),
    tags: tuple[str, ...] = (),
    changed_files: tuple[str, ...] = (),
    all_cases: bool = False,
) -> list[Scenario]:
    """Return only explicitly selected cases supported by the requested agent."""
    if not (identifiers or tags or changed_files or all_cases):
        return []
    normalized_changes = tuple(_plugin_relative(path) for path in changed_files)
    selected = []
    for scenario in scenarios:
        if agent not in scenario.agents:
            continue
        if identifiers and scenario.identifier not in identifiers:
            continue
        if tags and not set(tags).intersection(scenario.tags):
            continue
        if normalized_changes and not any(
            _covers_change(pattern, changed)
            for changed in normalized_changes
            for pattern in scenario.covers
        ):
            continue
        selected.append(scenario)
    return selected


def build_run_plan(
    scenarios: list[Scenario],
    *,
    agent: str,
    model: str,
    effort: str,
    repeat: int,
    timeout_seconds: int,
) -> dict[str, Any]:
    sessions = len(scenarios) * repeat
    return {
        "action": "plan",
        "agent": agent,
        "model": model,
        "effort": effort,
        "repeat": repeat,
        "timeout_seconds": timeout_seconds,
        "sessions": sessions,
        "maximum_duration_seconds": sessions * timeout_seconds,
        "cases": [scenario.identifier for scenario in scenarios],
        "modes": sorted({scenario.mode for scenario in scenarios}),
        "run_requires": "--run",
    }


def ensure_session_budget(plan: dict[str, Any], *, max_sessions: int) -> None:
    sessions = plan["sessions"]
    if sessions > max_sessions:
        raise ValueError(f"{sessions} sessions exceeds the limit of {max_sessions}")


def _git_changed_files(repository_root: Path, base: str) -> tuple[str, ...]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", base],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repository_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return tuple(sorted({*tracked.stdout.splitlines(), *untracked.stdout.splitlines()}))


def _plugin_dir(repository_root: Path) -> Path:
    candidate = repository_root / "plugins/development-skills"
    return candidate if candidate.is_dir() else repository_root


def build_command(
    agent: str,
    prompt: str,
    workdir: Path,
    transcript: Path,
    repository_root: Path,
    *,
    model: str,
    effort: str,
    mode: str = "workflow",
) -> list[str]:
    plugin_dir = _plugin_dir(repository_root)
    if agent == "claude":
        command = [
            "claude",
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            model,
            "--effort",
            effort,
            "--plugin-dir",
            str(plugin_dir),
        ]
        if mode == "routing":
            command.extend(
                [
                    "--include-partial-messages",
                    "--no-session-persistence",
                    "--permission-mode",
                    "dontAsk",
                    "--tools",
                    "Skill",
                ]
            )
        else:
            command.append("--dangerously-skip-permissions")
        return command
    if agent == "codex":
        if mode == "routing":
            raise ValueError("routing cases currently support claude only")
        instructions = plugin_dir / "skills/using-development-skills/SKILL.md"
        if instructions.is_file():
            preload = f"Read {instructions} before your first decision."
        else:
            preload = (
                f"Inspect {plugin_dir / 'skills'} and read the relevant SKILL.md before your "
                "first decision."
            )
        prompt = f"{preload}\n\n{prompt}"
        return [
            "codex",
            "exec",
            "--json",
            "--model",
            model,
            "--config",
            f'model_reasoning_effort="{effort}"',
            "--sandbox",
            "workspace-write",
            "--add-dir",
            str(plugin_dir),
            "--output-last-message",
            str(transcript.with_name("last_message.txt")),
            "--cd",
            str(workdir),
            prompt,
        ]
    raise ValueError(f"unsupported agent: {agent}")


def run_agent(
    agent: str,
    prompt: str,
    workdir: Path,
    transcript: Path,
    repository_root: Path,
    *,
    model: str,
    effort: str,
    timeout_seconds: int = 600,
    mode: str = "workflow",
) -> TrialResult:
    command = build_command(
        agent,
        prompt,
        workdir,
        transcript,
        repository_root,
        model=model,
        effort=effort,
        mode=mode,
    )
    if mode == "routing":
        return _run_routing_agent(command, workdir, transcript, timeout_seconds)
    started = time.monotonic()
    try:
        with logfire.span(
            "development_skills_eval.agent",
            agent=agent,
            model=model,
            effort=effort,
            workdir=str(workdir),
        ):
            process = subprocess.run(
                command,
                cwd=workdir,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_seconds,
            )
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else error.stdout
        )
        stderr = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else error.stderr
        )
        transcript.write_text(stdout or "")
        return TrialResult(
            124,
            stdout or "",
            stderr or "timeout",
            duration_seconds=time.monotonic() - started,
            token_usage=_token_usage(stdout or "", agent),
        )
    transcript.write_text(process.stdout)
    return TrialResult(
        process.returncode,
        process.stdout,
        process.stderr,
        _changed_files(workdir),
        duration_seconds=time.monotonic() - started,
        token_usage=_token_usage(process.stdout, agent),
    )


def _run_routing_agent(
    command: list[str], workdir: Path, transcript: Path, timeout_seconds: int
) -> TrialResult:
    """Stop Claude as soon as its first Skill selection is observable."""
    started = time.monotonic()
    environment = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
    process = subprocess.Popen(
        command,
        cwd=workdir,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    lines: list[str] = []
    selected: dict[str, Any] | None = None
    timed_out = False
    try:
        assert process.stdout is not None
        while process.poll() is None:
            if time.monotonic() - started >= timeout_seconds:
                timed_out = True
                break
            ready, _, _ = select.select([process.stdout], [], [], 0.2)
            if not ready:
                continue
            line = process.stdout.readline()
            if not line:
                continue
            lines.append(line.rstrip("\n"))
            selected = _routing_selection("\n".join(lines))
            if selected:
                break
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if process.stdout:
            lines.extend(line.rstrip("\n") for line in process.stdout.readlines())
        stderr = process.stderr.read() if process.stderr else ""
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    rendered = "\n".join(lines)
    selected = selected or _routing_selection(rendered)
    if selected:
        rendered += "\n" + json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "tool_use", "name": "Skill", "input": selected}]},
            }
        )
    transcript.write_text(rendered)
    return TrialResult(
        124 if timed_out else (0 if selected else process.returncode),
        rendered,
        "timeout" if timed_out else stderr,
        _changed_files(workdir),
        duration_seconds=time.monotonic() - started,
        token_usage=_token_usage(rendered, "claude"),
    )


def _routing_selection(transcript: str) -> dict[str, Any] | None:
    selected = sorted(
        name for name in _tool_names(transcript) if name.startswith("development-skills:")
    )
    if selected:
        return {"skill": selected[0]}
    pending_skill = False
    partial_input = ""
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "stream_event":
            continue
        stream = event.get("event", {})
        if stream.get("type") == "content_block_start":
            block = stream.get("content_block", {})
            pending_skill = block.get("type") == "tool_use" and block.get("name") == "Skill"
            partial_input = ""
        elif pending_skill and stream.get("type") == "content_block_delta":
            delta = stream.get("delta", {})
            if delta.get("type") != "input_json_delta":
                continue
            partial_input += delta.get("partial_json", "")
            try:
                candidate = json.loads(partial_input)
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and isinstance(candidate.get("skill"), str):
                return candidate
    return None


def _token_usage(transcript: str, agent: str) -> TokenUsage:
    if agent == "claude":
        messages: dict[str, dict[str, Any]] = {}
        streamed = TokenUsage()
        for index, line in enumerate(transcript.splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = event.get("message", {}) if isinstance(event, dict) else {}
            usage = message.get("usage") if isinstance(message, dict) else None
            if event.get("type") == "assistant" and isinstance(usage, dict):
                messages[str(message.get("id", index))] = usage
            stream = event.get("event", {}) if event.get("type") == "stream_event" else {}
            stream_usage = stream.get("usage") if isinstance(stream, dict) else None
            if isinstance(stream, dict) and stream.get("type") == "message_start":
                stream_usage = stream.get("message", {}).get("usage")
            if isinstance(stream_usage, dict):
                streamed = TokenUsage(
                    streamed.input_tokens + int(stream_usage.get("input_tokens", 0) or 0),
                    streamed.output_tokens + int(stream_usage.get("output_tokens", 0) or 0),
                    streamed.cache_creation_input_tokens
                    + int(stream_usage.get("cache_creation_input_tokens", 0) or 0),
                    streamed.cache_read_input_tokens
                    + int(stream_usage.get("cache_read_input_tokens", 0) or 0),
                )
        if messages:
            return TokenUsage(
                sum(int(usage.get("input_tokens", 0) or 0) for usage in messages.values()),
                sum(int(usage.get("output_tokens", 0) or 0) for usage in messages.values()),
                sum(
                    int(usage.get("cache_creation_input_tokens", 0) or 0)
                    for usage in messages.values()
                ),
                sum(
                    int(usage.get("cache_read_input_tokens", 0) or 0) for usage in messages.values()
                ),
            )
        return streamed

    total = TokenUsage()
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed" or not isinstance(event.get("usage"), dict):
            continue
        usage = event["usage"]
        total = TokenUsage(
            total.input_tokens + int(usage.get("input_tokens", 0) or 0),
            total.output_tokens + int(usage.get("output_tokens", 0) or 0),
            total.cache_creation_input_tokens,
            total.cache_read_input_tokens + int(usage.get("cached_input_tokens", 0) or 0),
        )
    return total


def _changed_files(workdir: Path) -> tuple[str, ...]:
    tracked = subprocess.run(
        ["git", "diff", "HEAD", "--name-only"],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=workdir,
        capture_output=True,
        text=True,
        check=True,
    )
    return tuple(sorted({*tracked.stdout.splitlines(), *untracked.stdout.splitlines()}))


def _tool_names(transcript: str) -> set[str]:
    names: set[str] = set()
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                for key in ("tool_name", "name"):
                    if isinstance(value.get(key), str):
                        names.add(value[key])
                # A Skill invocation is a tool_use whose input names the target skill. Capture it ONLY from a
                # real tool_use block (not from any dict carrying a "skill" key) so routing evals assert which
                # skill actually fired — a skill-catalog/init event can't satisfy them vacuously.
                if value.get("type") == "tool_use" and isinstance(value.get("input"), dict):
                    target = value["input"].get("skill")
                    if isinstance(target, str):
                        names.add(target)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(event)
    return names


def _tool_inputs(transcript: str) -> list[ToolCall]:
    inputs: list[ToolCall] = []
    group = 0

    def add(tool_name: str, tool_input: Any) -> None:
        nonlocal group
        group += 1
        inputs.append(ToolCall(tool_name, tool_input, group))
        inputs.extend(
            ToolCall("file_change", {"path": path}, group)
            for path in _changed_paths(tool_name, tool_input)
        )
        if tool_name != "command_execution" and isinstance(tool_input, dict):
            command = tool_input.get("command", tool_input.get("cmd"))
            if isinstance(command, str):
                inputs.append(ToolCall("command_execution", {"command": command}, group))

    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        def walk(value: Any) -> None:
            if isinstance(value, dict):
                tool_input = value.get("tool_input", value.get("input"))
                tool_name = value.get("tool_name", value.get("name"))
                if isinstance(tool_name, str) and tool_input is not None:
                    add(tool_name, tool_input)
                elif value.get("type") == "file_change" and "changes" in value:
                    add("file_change", {"changes": value["changes"]})
                elif value.get("type") == "command_execution" and "command" in value:
                    add("command_execution", {"command": value["command"]})
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(event)
    return inputs


def _changed_paths(tool_name: str, tool_input: Any) -> tuple[str, ...]:
    if isinstance(tool_input, dict):
        if tool_name in {"Write", "Edit", "MultiEdit", "NotebookEdit"}:
            path = next(
                (
                    tool_input[field]
                    for field in ("file_path", "path", "notebook_path")
                    if isinstance(tool_input.get(field), str)
                ),
                None,
            )
            return (path,) if path else ()
        if tool_name == "file_change":
            changes = tool_input.get("changes", ())
            if isinstance(changes, list):
                return tuple(
                    change["path"]
                    for change in changes
                    if isinstance(change, dict) and isinstance(change.get("path"), str)
                )
            path = tool_input.get("path")
            return (path,) if isinstance(path, str) else ()
        patch = tool_input.get("patch") if tool_name == "apply_patch" else None
    else:
        patch = tool_input if tool_name == "apply_patch" else None
    if not isinstance(patch, str):
        return ()
    return tuple(
        match.group(1)
        for match in re.finditer(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch, re.MULTILINE)
    )


def _assistant_text(transcript: str) -> str:
    texts: list[str] = []
    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            if isinstance(content, list):
                texts.extend(
                    block["text"]
                    for block in content
                    if isinstance(block, dict)
                    and block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                )
        elif event.get("type") == "result" and isinstance(event.get("result"), str):
            texts.append(event["result"])
        elif event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                texts.append(item["text"])
    return "\n".join(texts)


def _matches_tool_input(call: ToolCall, match: ToolInputMatch) -> bool:
    if call.name != match.tool or not isinstance(call.input, dict):
        return False
    value = call.input.get(match.field)
    serialized = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    return match.contains in serialized


@dataclass
class ObservableChecks(Evaluator[Scenario, TrialResult, None]):
    def evaluate(self, ctx: EvaluatorContext[Scenario, TrialResult, None]) -> dict[str, bool]:
        observed = _tool_names(ctx.output.transcript)
        results = {"agent_exit_zero": ctx.output.returncode == 0}
        if ctx.inputs.required_tools:
            results["required_tools"] = set(ctx.inputs.required_tools).issubset(observed)
        if ctx.inputs.forbidden_tools:
            results["forbidden_tools"] = set(ctx.inputs.forbidden_tools).isdisjoint(observed)
        if ctx.inputs.clean_worktree is not None:
            results["clean_worktree"] = (not ctx.output.changed_files) == ctx.inputs.clean_worktree
        if ctx.inputs.exact_changed_files is not None:
            results["changed_files_exact"] = set(ctx.inputs.exact_changed_files) == set(
                ctx.output.changed_files
            )
        contents = dict(ctx.output.file_contents)
        for index, check in enumerate(ctx.inputs.file_contains):
            name = (
                "file_contains" if len(ctx.inputs.file_contains) == 1 else f"file_contains_{index}"
            )
            results[name] = check.text in (contents.get(check.path) or "")
        for index, check in enumerate(ctx.inputs.file_not_contains):
            name = (
                "file_not_contains"
                if len(ctx.inputs.file_not_contains) == 1
                else f"file_not_contains_{index}"
            )
            content = contents.get(check.path)
            results[name] = content is not None and check.text not in content
        assistant_text = _assistant_text(ctx.output.transcript)
        for index, text in enumerate(ctx.inputs.transcript_contains):
            name = (
                "transcript_contains"
                if len(ctx.inputs.transcript_contains) == 1
                else f"transcript_contains_{index}"
            )
            results[name] = text in assistant_text
        tool_inputs = _tool_inputs(ctx.output.transcript)
        if ctx.inputs.tool_sequence:
            previous_group = -1
            sequence_passed = True
            for match in ctx.inputs.tool_sequence:
                matched = next(
                    (
                        tool_input
                        for tool_input in tool_inputs
                        if tool_input.group > previous_group
                        and _matches_tool_input(tool_input, match)
                    ),
                    None,
                )
                if matched is None:
                    sequence_passed = False
                    break
                previous_group = matched.group
            results["tool_sequence"] = sequence_passed
        return results


class FixtureManager:
    def __init__(self, workspace: Path, keep: bool):
        self.workspace = workspace
        self.keep = keep
        self.paths: dict[str, Path] = {}

    def create(self, scenario: Scenario) -> Path:
        path = Path(
            tempfile.mkdtemp(
                prefix=f"development-skills-eval-{scenario.identifier}-", dir=self.workspace
            )
        )
        root = path.resolve()
        try:
            for relative, content in scenario.files.items():
                target = (path / relative).resolve()
                if not target.is_relative_to(root):
                    raise ValueError(f"fixture file {relative!r} escapes outside the fixture")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            if not scenario.files:
                (path / ".gitkeep").touch()
            subprocess.run(["git", "init", "-q"], cwd=path, check=True)
            exclude = path / ".git/info/exclude"
            exclude.write_text(
                exclude.read_text() + "\nsession.jsonl\nlast_message.txt\n.eval-plugin/\n"
            )
            subprocess.run(["git", "add", "."], cwd=path, check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.email=eval@example.local",
                    "-c",
                    "user.name=Eval",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                cwd=path,
                check=True,
            )
        except Exception:
            shutil.rmtree(path, ignore_errors=True)
            raise
        self.paths[scenario.identifier] = path
        return path

    def discard(self, scenario: Scenario) -> None:
        path = self.paths.pop(scenario.identifier, None)
        if path and not self.keep:
            shutil.rmtree(path)


class FixtureLifecycle(CaseLifecycle[Scenario, TrialResult, None]):
    def __init__(self, case: Case[Scenario, TrialResult, None], manager: FixtureManager):
        super().__init__(case)
        self.manager = manager

    async def setup(self) -> None:
        self.manager.create(self.case.inputs)

    async def teardown(
        self,
        _result: ReportCase[Scenario, TrialResult, None]
        | ReportCaseFailure[Scenario, TrialResult, None]
        | None,
    ) -> None:
        self.manager.discard(self.case.inputs)


def evaluate(
    scenarios: list[Scenario],
    *,
    agent: str,
    plugin_root: Path,
    repeat: int,
    workspace: Path,
    model: str,
    effort: str,
    keep: bool = False,
    timeout_seconds: int = 180,
):
    manager = FixtureManager(workspace, keep)

    def task(scenario: Scenario) -> TrialResult:
        path = manager.paths[scenario.identifier]
        isolated_plugin = path / ".eval-plugin"
        shutil.copytree(_plugin_dir(plugin_root), isolated_plugin, symlinks=True)
        result = run_agent(
            agent,
            scenario.prompt,
            path,
            path / "session.jsonl",
            isolated_plugin,
            model=model,
            effort=effort,
            timeout_seconds=timeout_seconds,
            mode=scenario.mode,
        )
        contents: list[tuple[str, str | None]] = []
        root = path.resolve()
        content_checks = {check.path for check in scenario.file_contains}
        content_checks.update(check.path for check in scenario.file_not_contains)
        for relative in sorted(content_checks):
            target = (path / relative).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"asserted file {relative!r} escapes outside the fixture")
            contents.append((relative, target.read_text() if target.is_file() else None))
        return replace(result, file_contents=tuple(contents))

    dataset = Dataset(
        name="development-skills",
        cases=[Case(name=scenario.identifier, inputs=scenario) for scenario in scenarios],
        evaluators=[ObservableChecks()],
    )
    return asyncio.run(
        dataset.evaluate(
            task,
            repeat=repeat,
            max_concurrency=1,
            progress=False,
            lifecycle=lambda case: FixtureLifecycle(case, manager),
        )
    )


def _report_json(report: Any, *, agent: str, model: str, effort: str) -> str:
    cases = []
    totals: dict[str, list[int]] = {}
    usage = {
        "sessions": 0,
        "duration_seconds": 0.0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    for case in report.cases:
        assertions = {name: result.value for name, result in case.assertions.items()}
        for name, value in assertions.items():
            passed, total = totals.setdefault(name, [0, 0])
            totals[name] = [passed + int(value is True), total + 1]
        output = case.output
        tokens = output.token_usage
        usage["sessions"] += 1
        usage["duration_seconds"] += output.duration_seconds
        usage["input_tokens"] += tokens.input_tokens
        usage["output_tokens"] += tokens.output_tokens
        usage["cache_creation_input_tokens"] += tokens.cache_creation_input_tokens
        usage["cache_read_input_tokens"] += tokens.cache_read_input_tokens
        cases.append(
            {
                "case": case.source_case_name or case.name,
                "run": case.name,
                "assertions": assertions,
                "usage": {
                    "duration_seconds": output.duration_seconds,
                    "input_tokens": tokens.input_tokens,
                    "output_tokens": tokens.output_tokens,
                    "cache_creation_input_tokens": tokens.cache_creation_input_tokens,
                    "cache_read_input_tokens": tokens.cache_read_input_tokens,
                },
            }
        )
    usage["duration_seconds"] = round(usage["duration_seconds"], 3)
    rates = {
        name: {"passed": passed, "total": total, "rate": passed / total}
        for name, (passed, total) in totals.items()
    }
    failures = [
        {
            "case": failure.source_case_name or failure.name,
            "run": failure.name,
            "error": failure.error_message,
        }
        for failure in report.failures
    ]
    return (
        json.dumps(
            {
                "metadata": {"agent": agent, "model": model, "effort": effort},
                "cases": cases,
                "failures": failures,
                "rates": rates,
                "usage": usage,
            },
            indent=2,
        )
        + "\n"
    )


def report_failed(report: Any) -> bool:
    return bool(report.failures) or any(
        result.value is not True for case in report.cases for result in case.assertions.values()
    )


def _report_results(report: dict[str, Any]) -> dict[tuple[str, str], list[bool]]:
    results: dict[tuple[str, str], list[bool]] = {}
    for case in report.get("cases", []):
        name = case["case"]
        results.setdefault((name, "task_succeeded"), []).append(True)
        for assertion, passed in case["assertions"].items():
            results.setdefault((name, assertion), []).append(passed is True)
    for failure in report.get("failures", []):
        results.setdefault((failure["case"], "task_succeeded"), []).append(False)
    return results


def _rate(values: list[bool]) -> dict[str, int | float]:
    passed = sum(values)
    return {"passed": passed, "total": len(values), "rate": passed / len(values)}


def compare_reports(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare identical Pydantic eval runs without hiding missing evidence."""
    old = _report_results(baseline)
    new = _report_results(candidate)
    comparisons: list[dict[str, Any]] = []
    counts = {"regressions": 0, "improvements": 0, "stable": 0, "inconclusive": 0}

    for case, assertion in sorted(old.keys() | new.keys()):
        old_values = old.get((case, assertion))
        new_values = new.get((case, assertion))
        old_rate = _rate(old_values) if old_values else None
        new_rate = _rate(new_values) if new_values else None
        if (
            not old_rate
            or not new_rate
            or old_rate["total"] != new_rate["total"]
            or (assertion == "task_succeeded" and old_rate["rate"] == new_rate["rate"] < 1)
        ):
            status = "INCONCLUSIVE"
            counts["inconclusive"] += 1
        elif new_rate["rate"] < old_rate["rate"]:
            status = "REGRESSION"
            counts["regressions"] += 1
        elif new_rate["rate"] > old_rate["rate"]:
            status = "IMPROVEMENT"
            counts["improvements"] += 1
        else:
            status = "STABLE"
            counts["stable"] += 1
        comparisons.append(
            {
                "case": case,
                "assertion": assertion,
                "baseline": old_rate,
                "candidate": new_rate,
                "status": status,
            }
        )

    inconclusive_reasons: list[str] = []
    metadata_keys = {"agent", "model", "effort"}
    baseline_metadata = baseline.get("metadata")
    candidate_metadata = candidate.get("metadata")
    if not isinstance(baseline_metadata, dict) or not isinstance(candidate_metadata, dict):
        inconclusive_reasons.append("agent, model, and effort metadata are required")
    elif (
        not metadata_keys <= baseline_metadata.keys()
        or not metadata_keys <= candidate_metadata.keys()
    ):
        inconclusive_reasons.append("agent, model, and effort metadata are required")
    elif baseline_metadata != candidate_metadata:
        inconclusive_reasons.append("baseline and candidate metadata differ")
    if baseline.get("failures") or candidate.get("failures"):
        inconclusive_reasons.append("one or more runs are missing")
    if any(
        case.get("assertions", {}).get("agent_exit_zero") is False
        for report in (baseline, candidate)
        for case in report.get("cases", [])
    ):
        inconclusive_reasons.append("one or more agent runs exited non-zero")

    if inconclusive_reasons:
        for comparison in comparisons:
            comparison["status"] = "INCONCLUSIVE"
        counts = {
            "regressions": 0,
            "improvements": 0,
            "stable": 0,
            "inconclusive": len(comparisons) or 1,
        }
        verdict = "INCONCLUSIVE"
    elif not comparisons:
        verdict = "INCONCLUSIVE"
    elif counts["regressions"]:
        verdict = "REGRESSION"
    elif counts["inconclusive"]:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "NO_REGRESSION"
    return {
        "verdict": verdict,
        "summary": counts,
        "comparisons": comparisons,
        "inconclusive_reasons": inconclusive_reasons,
    }


def _write_output(rendered: str, output: Path | None) -> None:
    if output:
        output.write_text(rendered)
    else:
        print(rendered, end="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--cases", type=Path)
    parser.add_argument("--case", dest="case_ids", action="append", default=[])
    parser.add_argument("--tag", dest="tags", action="append", default=[])
    parser.add_argument("--changed-from")
    parser.add_argument("--all", dest="all_cases", action="store_true")
    parser.add_argument("--agent", choices=["claude", "codex"])
    parser.add_argument("--model")
    parser.add_argument("--effort")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--plugin-dir", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--max-sessions", type=int, default=4)
    parser.add_argument(
        "--compare",
        nargs=2,
        type=Path,
        metavar=("BASELINE_REPORT", "CANDIDATE_REPORT"),
    )
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    if args.compare:
        if any(
            (
                args.cases,
                args.agent,
                args.model,
                args.effort,
                args.case_ids,
                args.tags,
                args.changed_from,
                args.all_cases,
                args.run,
            )
        ):
            parser.error("--compare cannot be combined with eval options")
        baseline, candidate = (json.loads(path.read_text()) for path in args.compare)
        comparison = compare_reports(baseline, candidate)
        _write_output(json.dumps(comparison, indent=2) + "\n", args.output)
        if comparison["verdict"] != "NO_REGRESSION":
            sys.exit(1)
        return
    if not args.cases or not args.agent or not args.model or not args.effort:
        parser.error(
            "--cases, --agent, --model, and --effort are required unless --compare is used"
        )
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")
    if args.max_sessions < 1:
        parser.error("--max-sessions must be positive")
    if not (args.case_ids or args.tags or args.changed_from or args.all_cases):
        parser.error("select cases with --case, --tag, --changed-from, or --all")

    scenarios = load_scenarios(args.cases)
    unknown = sorted(set(args.case_ids) - {scenario.identifier for scenario in scenarios})
    if unknown:
        parser.error(f"unknown case: {', '.join(unknown)}")
    changed_files = (
        _git_changed_files(args.repository_root, args.changed_from) if args.changed_from else ()
    )
    selected = select_scenarios(
        scenarios,
        agent=args.agent,
        identifiers=tuple(args.case_ids),
        tags=tuple(args.tags),
        changed_files=changed_files,
        all_cases=args.all_cases,
    )
    plan = build_run_plan(
        selected,
        agent=args.agent,
        model=args.model,
        effort=args.effort,
        repeat=args.repeat,
        timeout_seconds=args.timeout_seconds,
    )
    if not args.run:
        _write_output(json.dumps(plan, indent=2) + "\n", args.output)
        return
    try:
        ensure_session_budget(plan, max_sessions=args.max_sessions)
    except ValueError as error:
        parser.error(str(error))
    if not selected:
        parser.error("no supported cases matched the selection")

    logfire.configure(send_to_logfire="if-token-present", service_name="development-skills-evals")
    report = evaluate(
        selected,
        agent=args.agent,
        plugin_root=args.plugin_dir or args.repository_root,
        repeat=args.repeat,
        workspace=args.workspace,
        model=args.model,
        effort=args.effort,
        keep=args.keep,
        timeout_seconds=args.timeout_seconds,
    )
    rendered = _report_json(report, agent=args.agent, model=args.model, effort=args.effort)
    _write_output(rendered, args.output)
    if report_failed(report):
        sys.exit(1)


if __name__ == "__main__":
    main()
