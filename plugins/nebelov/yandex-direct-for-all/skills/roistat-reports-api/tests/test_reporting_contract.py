#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reporting = load("roistat_reporting", "build_roistat_report_pack.py")
writing = load("roistat_writing", "save_roistat_report.py")


class PaginationTests(unittest.TestCase):
    def test_multiple_pages_and_complete_state(self):
        pages = [
            {"data": [{"id": "a"}, {"id": "b"}], "total": 3},
            {"data": [{"id": "c"}], "total": 3},
        ]
        calls = []

        def fetch(endpoint, request):
            calls.append((endpoint, request.copy()))
            return pages.pop(0)

        rows, state = reporting.paginate(fetch, "orders", {}, 2, 5)
        self.assertEqual([row["id"] for row in rows], ["a", "b", "c"])
        self.assertEqual([call[1]["offset"] for call in calls], [0, 2])
        self.assertEqual(state, {"status": "complete", "pages": 2, "objects": 3, "complete": True})

    def test_empty_response_is_complete(self):
        rows, state = reporting.paginate(lambda *_: {"data": [], "total": 0}, "orders", {}, 50, 5)
        self.assertEqual(rows, [])
        self.assertTrue(state["complete"])

    def test_invalid_schema_is_rejected(self):
        with self.assertRaises(ValueError):
            reporting.paginate(lambda *_: {"data": "not-a-list"}, "orders", {}, 50, 5)

    def test_network_error_is_not_hidden(self):
        def fail(*_):
            raise OSError("synthetic network error")

        with self.assertRaisesRegex(OSError, "synthetic network error"):
            reporting.paginate(fail, "orders", {}, 50, 5)

    def test_page_limit_produces_partial_state(self):
        rows, state = reporting.paginate(lambda *_: {"data": [{"id": "a"}, {"id": "b"}], "total": 99}, "orders", {}, 2, 1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(state["status"], "partial")
        self.assertFalse(state["complete"])


class ReproducibilityTests(unittest.TestCase):
    def test_totals_are_reproducible_from_saved_rows(self):
        analytics = [
            {"sales__last": 2, "revenue__last": "120.50"},
            {"sales__last": 1, "revenue__last": 40},
        ]
        orders = [{"revenue": 100}, {"revenue": "70.50"}]
        expected = {
            "analytics_sales": 3.0,
            "raw_sales": 2.0,
            "sales_difference": -1.0,
            "analytics_revenue": 160.5,
            "raw_revenue": 170.5,
            "revenue_difference": 10.0,
        }
        self.assertEqual(reporting.reconciliation(analytics, orders), expected)
        self.assertEqual(reporting.reconciliation(json.loads(json.dumps(analytics)), json.loads(json.dumps(orders))), expected)

    def test_artifacts_are_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private" / "result.json"
            reporting.atomic_json(path, {"status": "complete"})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)


class WriteGateTests(unittest.TestCase):
    def make_package(self, root: Path):
        spec = root / "report.json"
        spec.write_text(json.dumps({"title": "SYNTHETIC_REPORT", "settings": {"metric": "visits"}}), encoding="utf-8")
        digest = hashlib.sha256(spec.read_bytes()).hexdigest()
        checksum = root / "report.sha256"
        checksum.write_text(digest + "\n", encoding="utf-8")
        now = datetime.now(timezone.utc)
        approval = root / "approval.json"
        approval.write_text(json.dumps({
            "approved": True,
            "spec_sha256": digest,
            "project": "SYNTHETIC_PROJECT",
            "action": "create",
            "target_ref": "SYNTHETIC_REPORT",
            "approved_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
        }), encoding="utf-8")
        os.chmod(approval, 0o600)
        return spec, checksum, approval

    def test_missing_armed_flag_is_rejected_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            spec, checksum, approval = self.make_package(Path(directory))
            environment = {"ROISTAT_PROJECT": "SYNTHETIC_PROJECT", "ROISTAT_WRITE_API_KEY": "synthetic-secret"}
            with mock.patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(writing.GateError, "не вооружена"):
                    writing.prepare("SYNTHETIC_PROJECT", "create", "SYNTHETIC_REPORT", spec, checksum, approval, apply=True)

    def test_check_only_requires_no_write_key_and_calls_no_api(self):
        with tempfile.TemporaryDirectory() as directory:
            spec, checksum, approval = self.make_package(Path(directory))
            with mock.patch.dict(os.environ, {"ROISTAT_PROJECT": "SYNTHETIC_PROJECT"}, clear=True):
                prepared = writing.prepare("SYNTHETIC_PROJECT", "create", "SYNTHETIC_REPORT", spec, checksum, approval, apply=False)
            self.assertEqual(prepared.api_key, "")

    def test_complete_write_reads_back_and_preserves_other_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec, checksum, approval = self.make_package(root)
            environment = {
                "ROISTAT_PROJECT": "SYNTHETIC_PROJECT",
                "ROISTAT_WRITE_API_KEY": "synthetic-secret",
                "ROISTAT_WRITE_ARMED": "1",
                "YDFALL_STATE_ROOT": str(root / "state"),
            }
            with mock.patch.dict(os.environ, environment, clear=True):
                prepared = writing.prepare("SYNTHETIC_PROJECT", "create", "SYNTHETIC_REPORT", spec, checksum, approval, apply=True)
            stored = [{"id": "existing", "title": "EXISTING", "settings": {"metric": "cost"}}]

            def api(_prepared, endpoint, body):
                if endpoint.endswith("reports"):
                    return {"reports": list(stored)}
                stored.append({"id": "new", **body["report"]})
                return {"status": "success"}

            result = writing.execute(prepared, api)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(stored[0]["title"], "EXISTING")
            evidence = next((root / "state" / "roistat-writes").iterdir())
            self.assertTrue((evidence / "before.json").is_file())
            self.assertTrue((evidence / "after.json").is_file())
            self.assertEqual(stat.S_IMODE((evidence / "result.json").stat().st_mode), 0o600)

    def test_create_rejects_mutation_of_existing_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec, checksum, approval = self.make_package(root)
            environment = {
                "ROISTAT_PROJECT": "SYNTHETIC_PROJECT",
                "ROISTAT_WRITE_API_KEY": "synthetic-secret",
                "ROISTAT_WRITE_ARMED": "1",
                "YDFALL_STATE_ROOT": str(root / "state"),
            }
            with mock.patch.dict(os.environ, environment, clear=True):
                prepared = writing.prepare("SYNTHETIC_PROJECT", "create", "SYNTHETIC_REPORT", spec, checksum, approval, apply=True)
            calls = 0

            def api(_prepared, endpoint, body):
                nonlocal calls
                if endpoint.endswith("reports"):
                    calls += 1
                    if calls == 1:
                        return {"reports": [{"id": "existing", "title": "EXISTING", "settings": {"metric": "cost"}}]}
                    return {"reports": [
                        {"id": "existing", "title": "EXISTING_CHANGED", "settings": {"metric": "cost"}},
                        {"id": "new", **prepared.spec},
                    ]}
                return {"status": "success"}

            with self.assertRaisesRegex(writing.GateError, "существующие"):
                writing.execute(prepared, api)


if __name__ == "__main__":
    unittest.main()
