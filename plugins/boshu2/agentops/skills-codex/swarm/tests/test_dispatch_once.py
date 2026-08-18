from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "dispatch_once.py"
SPEC = importlib.util.spec_from_file_location("dispatch_once", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def packet(identity: str, *paths: str) -> dict:
    return {"packet_id": identity, "write_scope": {"include": list(paths), "exclude": []}}


class DispatchOnceTests(unittest.TestCase):
    def test_each_packet_is_dispatched_once_in_input_order(self) -> None:
        calls: list[str] = []

        def executor(value: dict) -> str:
            calls.append(value["packet_id"])
            return "candidate:" + value["packet_id"]

        result = MODULE.dispatch_once(
            [packet("a", "src/a"), packet("b", "src/b")], executor
        )

        self.assertEqual(calls, ["a", "b"])
        self.assertEqual([row["packet_id"] for row in result], ["a", "b"])

    def test_executor_failure_is_reported_without_retry(self) -> None:
        calls = 0

        def executor(_value: dict) -> None:
            nonlocal calls
            calls += 1
            raise RuntimeError("boom")

        result = MODULE.dispatch_once([packet("a", "src/a")], executor)

        self.assertEqual(calls, 1)
        self.assertEqual(result[0]["error"]["type"], "RuntimeError")

    def test_overlapping_scopes_fail_before_dispatch(self) -> None:
        calls = 0

        def executor(_value: dict) -> None:
            nonlocal calls
            calls += 1

        with self.assertRaisesRegex(ValueError, "write scopes overlap"):
            MODULE.dispatch_once(
                [packet("a", "src"), packet("b", "src/b/file.go")], executor
            )
        self.assertEqual(calls, 0)

    def test_overlapping_glob_scopes_fail_before_dispatch(self) -> None:
        calls = 0

        def executor(_value: dict) -> None:
            nonlocal calls
            calls += 1

        with self.assertRaisesRegex(ValueError, "write scopes overlap"):
            MODULE.dispatch_once(
                [packet("a", "src/**"), packet("b", "src/lib/**")], executor
            )
        self.assertEqual(calls, 0)

    def test_disjoint_glob_prefixes_dispatch(self) -> None:
        calls: list[str] = []

        MODULE.dispatch_once(
            [packet("a", "src/a/**"), packet("b", "src/b/**")],
            lambda value: calls.append(value["packet_id"]),
        )

        self.assertEqual(calls, ["a", "b"])

    def test_uncertain_glob_overlap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "write scopes overlap"):
            MODULE.dispatch_once(
                [packet("a", "src/*/generated"), packet("b", "src/*/manual")],
                lambda _value: None,
            )

    def test_case_only_scope_difference_is_rejected(self) -> None:
        calls = 0

        def executor(_value: dict) -> None:
            nonlocal calls
            calls += 1

        with self.assertRaisesRegex(ValueError, "write scopes overlap"):
            MODULE.dispatch_once(
                [packet("a", "src/Auth"), packet("b", "src/auth")], executor
            )
        self.assertEqual(calls, 0)

    def test_nonempty_exclude_is_rejected_not_ignored(self) -> None:
        with self.assertRaisesRegex(ValueError, "exclude is not honored"):
            MODULE.dispatch_once(
                [
                    {
                        "packet_id": "a",
                        "write_scope": {
                            "include": ["src/a"],
                            "exclude": ["src/a/skip"],
                        },
                    }
                ],
                lambda _value: None,
            )


if __name__ == "__main__":
    unittest.main()
