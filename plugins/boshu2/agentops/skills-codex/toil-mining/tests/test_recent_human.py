#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "recent_human.py"


def record(
    timestamp: str,
    message: str,
    client_id: str | None,
    *,
    outer_type: str = "event_msg",
    payload_type: str = "user_message",
) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "type": outer_type,
        "payload": {
            "type": payload_type,
            "client_id": client_id,
            "message": message,
        },
    }


class RecentHumanCliTest(unittest.TestCase):
    def run_cli(
        self, *paths: Path, since: str, until: str
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--since",
                since,
                "--until",
                until,
                *(str(path) for path in paths),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def write_jsonl(self, path: Path, values: list[object | str]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for value in values:
                if isinstance(value, str):
                    handle.write(value)
                else:
                    handle.write(json.dumps(value))
                handle.write("\n")

    def test_extracts_normalizes_excludes_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.jsonl"
            second = root / "b.jsonl"
            self.write_jsonl(
                first,
                [
                    {"timestamp": "2026-07-14T09:59:00Z", "type": "session_meta"},
                    record(
                        "2026-07-14T10:05:00Z",
                        "\n# Files mentioned by the user:\n\n## notes: /tmp/pasted.txt\n\n"
                        "# My request for Codex:\n  Mine these sessions.  \n",
                        "client-attachment",
                    ),
                    record(
                        "2026-07-14T10:06:00Z", "Keep this twice", "client-duplicate"
                    ),
                    record(
                        "2026-07-14T10:07:00Z",
                        "You are a fresh-context, cross-family reviewer — review this.",
                        "client-generated-envelope",
                    ),
                    record("2026-07-14T10:08:00Z", "Injected worker prompt", None),
                    record("2026-07-14T09:59:59Z", "Before window", "client-before"),
                    record(
                        "2026-07-14T10:09:00Z",
                        "assistant event",
                        "client-assistant",
                        payload_type="assistant_message",
                    ),
                    "{not valid json",
                    record(
                        "2026-07-14T10:10:00Z",
                        "# Files mentioned by the user:\n# My request for Codex:\n",
                        "client-empty",
                    ),
                ],
            )
            self.write_jsonl(
                second,
                [
                    record(
                        "2026-07-14T10:06:30Z", "Keep this twice", "client-duplicate"
                    ),
                    record("2026-07-14T11:00:00Z", "At until", "client-until"),
                    record("2026-07-14T10:00:00Z", "At since", "client-since"),
                    record("not-a-time", "Bad time", "client-bad-time"),
                ],
            )

            completed = self.run_cli(
                second,
                first,
                since="2026-07-14T10:00:00Z",
                until="2026-07-14T11:00:00+00:00",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)
            first = first.resolve()
            second = second.resolve()

            self.assertEqual(result["inputs"], sorted([str(first), str(second)]))
            self.assertEqual(
                result["window"],
                {
                    "since_inclusive": "2026-07-14T10:00:00.000Z",
                    "until_exclusive": "2026-07-14T11:00:00.000Z",
                },
            )
            self.assertEqual(
                result["messages"],
                [
                    {
                        "source_path": str(second),
                        "line": 3,
                        "timestamp": "2026-07-14T10:00:00.000Z",
                        "text": "At since",
                    },
                    {
                        "source_path": str(first),
                        "line": 2,
                        "timestamp": "2026-07-14T10:05:00.000Z",
                        "text": "Mine these sessions.",
                    },
                    {
                        "source_path": str(first),
                        "line": 3,
                        "timestamp": "2026-07-14T10:06:00.000Z",
                        "text": "Keep this twice",
                    },
                ],
            )
            counts = result["counts"]
            self.assertEqual(counts["input_files"], 2)
            self.assertEqual(counts["input_lines"], 13)
            self.assertEqual(counts["parsed_records"], 12)
            self.assertEqual(counts["candidate_user_messages"], 10)
            self.assertEqual(counts["emitted_messages"], 3)
            self.assertEqual(
                counts["excluded"],
                {
                    "invalid_json": 1,
                    "non_user_message": 2,
                    "invalid_timestamp": 1,
                    "outside_window": 2,
                    "missing_client_id": 1,
                    "machine_echo": 1,
                    "machine_echo_by_pattern": {
                        "internal_context": 0,
                        "fresh_context_refuter": 1,
                        "agent_message_envelope": 0,
                    },
                    "empty_after_normalization": 1,
                    "duplicate_client_id": 1,
                    "duplicate_client_id_text_conflict": 0,
                },
            )
            self.assertTrue(result["checked"])
            self.assertTrue(result["not_checked"])

    def test_output_is_independent_of_input_path_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "a.jsonl"
            second = root / "b.jsonl"
            self.write_jsonl(
                first,
                [record("2026-07-14T10:00:00-04:00", "First", "client-first")],
            )
            self.write_jsonl(
                second,
                [record("2026-07-14T14:01:00Z", "Second", "client-second")],
            )
            kwargs = {
                "since": "2026-07-14T13:59:00Z",
                "until": "2026-07-14T14:02:00Z",
            }
            left = self.run_cli(first, second, **kwargs)
            right = self.run_cli(second, first, **kwargs)
            self.assertEqual(left.returncode, 0, left.stderr)
            self.assertEqual(right.returncode, 0, right.stderr)
            self.assertEqual(left.stdout, right.stdout)

    def test_requires_timezone_and_ordered_explicit_window(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory) / "session.jsonl"
            self.write_jsonl(session, [])
            no_timezone = self.run_cli(
                session,
                since="2026-07-14T10:00:00",
                until="2026-07-14T11:00:00Z",
            )
            self.assertEqual(no_timezone.returncode, 2)
            self.assertIn("must include a timezone", no_timezone.stderr)

            reversed_window = self.run_cli(
                session,
                since="2026-07-14T11:00:00Z",
                until="2026-07-14T10:00:00Z",
            )
            self.assertEqual(reversed_window.returncode, 2)
            self.assertIn("--since must be earlier", reversed_window.stderr)


if __name__ == "__main__":
    unittest.main()
