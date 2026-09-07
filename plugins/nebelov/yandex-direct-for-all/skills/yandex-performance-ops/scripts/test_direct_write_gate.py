from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import direct_write_gate as gate


class GateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)

    def operation(self, identifier: str = "first", depends_on=None) -> dict:
        return {
            "id": identifier,
            "service": "campaigns",
            "method": "update",
            "version": "v501",
            "params": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]},
            "depends_on": list(depends_on or []),
            "readback": {
                "service": "campaigns",
                "version": "v501",
                "params": {"SelectionCriteria": {"Ids": [1]}, "FieldNames": ["Id", "Name"]},
                "result_key": "Campaigns",
            },
            "expected_after": {"result": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]}},
            "reversible": True,
            "reversal_fields": ["Name"],
            "estimated_api_units": 1,
            "max_api_units": 1,
        }

    def irreversible_operation(self) -> dict:
        return {
            "id": "archive-one",
            "service": "ads",
            "method": "archive",
            "version": "v5",
            "params": {"SelectionCriteria": {"Ids": [1]}},
            "depends_on": [],
            "readback": {
                "service": "ads",
                "version": "v5",
                "params": {"SelectionCriteria": {"Ids": [1]}, "FieldNames": ["Id", "State"]},
                "result_key": "Ads",
            },
            "expected_after": {"result": {"Ads": [{"Id": 1, "State": "ARCHIVED"}]}},
            "reversible": False,
            "irreversible_reason": "Архивирование не возвращается автоматическим обратным пакетом",
            "estimated_api_units": 1,
            "max_api_units": 1,
        }

    def pack(self, approval_path: Path) -> dict:
        return {
            "schema_version": "1.0",
            "run_id": "test-run-001",
            "client_login": "example-client",
            "environment": "production",
            "operation_type": "campaigns.update",
            "created_at": (self.now - timedelta(minutes=1)).isoformat(),
            "expires_at": (self.now + timedelta(hours=1)).isoformat(),
            "source_snapshot_sha256": "0" * 64,
            "owner_approval_ref": str(approval_path),
            "max_api_units": 5,
            "operations": [self.operation()],
        }

    def materialize(self, root: Path, pack: dict) -> tuple[Path, Path]:
        pack_path = root / "pack.json"
        raw = json.dumps(pack, ensure_ascii=False, indent=2).encode("utf-8")
        pack_path.write_bytes(raw)
        digest = hashlib.sha256(raw).hexdigest()
        sha_path = root / "pack.sha256"
        sha_path.write_text(digest + "\n", encoding="utf-8")
        approval = {
            "approved": True,
            "pack_sha256": digest,
            "client_login": pack.get("client_login", "example-client"),
            "approved_at": (self.now - timedelta(seconds=30)).isoformat(),
            "expires_at": min(
                self.now + timedelta(minutes=30),
                gate._time(pack.get("expires_at", (self.now + timedelta(hours=1)).isoformat())),
            ).isoformat(),
        }
        approval_path = Path(pack.get("owner_approval_ref") or root / "approval.json")
        approval_path.write_text(json.dumps(approval), encoding="utf-8")
        os.chmod(approval_path, 0o600)
        return pack_path, sha_path

    def environment(self, root: Path) -> dict[str, str]:
        return {
            "YANDEX_DIRECT_ENVIRONMENT": "production",
            "YANDEX_DIRECT_CLIENT_LOGIN": "example-client",
            "YANDEX_DIRECT_PRODUCTION_WRITE_TOKEN": "synthetic-write-token",
            "YD_WRITE_ARMED": "1",
            "YDFALL_STATE_ROOT": str(root / "state"),
        }

    def prepare(self, root: Path, pack: dict, *, apply=True) -> gate.Prepared:
        pack_path, sha_path = self.materialize(root, pack)
        with mock.patch.dict(os.environ, self.environment(root), clear=True):
            return gate.prepare(pack_path, sha_path, apply=apply, now=self.now)

    def test_each_required_pack_and_operation_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.pack(root / "approval.json")
            for field in sorted(gate.REQUIRED_PACK_FIELDS):
                candidate = copy.deepcopy(base)
                del candidate[field]
                with self.subTest(pack_field=field), self.assertRaises(gate.GateError):
                    self.prepare(root, candidate)
            for field in sorted(gate.REQUIRED_OPERATION_FIELDS):
                candidate = copy.deepcopy(base)
                del candidate["operations"][0][field]
                with self.subTest(operation_field=field), self.assertRaises(gate.GateError):
                    self.prepare(root, candidate)

    def test_expiry_checksum_scope_budget_and_lock_fail_before_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = self.pack(root / "approval.json")

            expired = copy.deepcopy(base)
            expired["created_at"] = (self.now - timedelta(hours=2)).isoformat()
            expired["expires_at"] = (self.now - timedelta(hours=1)).isoformat()
            with self.assertRaises(gate.GateError):
                self.prepare(root, expired)

            budget = copy.deepcopy(base)
            budget["max_api_units"] = 1
            budget["operations"] = [self.operation("first"), self.operation("second")]
            with self.assertRaisesRegex(gate.GateError, "бюджет"):
                self.prepare(root, budget)

            pack_path, sha_path = self.materialize(root, base)
            sha_path.write_text("f" * 64 + "\n", encoding="utf-8")
            with mock.patch.dict(os.environ, self.environment(root), clear=True), self.assertRaisesRegex(gate.GateError, "сумма"):
                gate.prepare(pack_path, sha_path, apply=True, now=self.now)

            wrong_scope = self.environment(root)
            wrong_scope["YANDEX_DIRECT_CLIENT_LOGIN"] = "another-client"
            pack_path, sha_path = self.materialize(root, base)
            with mock.patch.dict(os.environ, wrong_scope, clear=True), self.assertRaisesRegex(gate.GateError, "область"):
                gate.prepare(pack_path, sha_path, apply=True, now=self.now)

            prepared = self.prepare(root, base)
            prepared.lock_path.parent.mkdir(parents=True, exist_ok=True)
            prepared.lock_path.write_text("other-run", encoding="utf-8")
            writer = mock.Mock()
            reader = mock.Mock()
            with self.assertRaisesRegex(gate.GateError, "уже выполняется"):
                gate.execute(prepared, writer=writer, reader=reader)
            writer.assert_not_called()
            reader.assert_not_called()

    def test_arming_and_environment_specific_write_token_are_mandatory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = self.pack(root / "approval.json")
            pack_path, sha_path = self.materialize(root, pack)
            values = self.environment(root)
            del values["YD_WRITE_ARMED"]
            with mock.patch.dict(os.environ, values, clear=True), self.assertRaisesRegex(gate.GateError, "вооружена"):
                gate.prepare(pack_path, sha_path, apply=True, now=self.now)
            values = self.environment(root)
            del values["YANDEX_DIRECT_PRODUCTION_WRITE_TOKEN"]
            with mock.patch.dict(os.environ, values, clear=True), self.assertRaisesRegex(gate.GateError, "отсутствует"):
                gate.prepare(pack_path, sha_path, apply=True, now=self.now)

    def test_irreversible_operation_requires_explicit_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = self.pack(root / "approval.json")
            pack["operation_type"] = "ads.archive"
            pack["operations"] = [self.irreversible_operation()]
            self.prepare(root, pack)
            del pack["operations"][0]["irreversible_reason"]
            with self.assertRaisesRegex(gate.GateError, "Необратимая"):
                self.prepare(root, pack)

    def test_partial_response_blocks_dependent_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = self.pack(root / "approval.json")
            pack["operations"] = [self.operation("first"), self.operation("second", ["first"])]
            prepared = self.prepare(root, pack)
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Errors": [{"Code": 1}]}]}}, 1))
            result = gate.execute(prepared, writer=writer, reader=mock.Mock(return_value=before))
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["operations"][0]["status"], "partial")
            self.assertEqual(writer.call_count, 1)

    def test_readback_mismatch_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = self.prepare(root, self.pack(root / "approval.json"))
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            after = {"result": {"Campaigns": [{"Id": 1, "Name": "Другое название"}]}}
            reader = mock.Mock(side_effect=[before, after])
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Id": 1}]}}, 1))
            result = gate.execute(prepared, writer=writer, reader=reader)
            self.assertEqual(result["status"], "incomplete")
            self.assertEqual(result["operations"][0]["status"], "readback_mismatch")
            diff = json.loads((root / "state" / "direct-writes" / "test-run-001" / "diff-001.json").read_text(encoding="utf-8"))
            self.assertEqual(diff["status"], "mismatch")

    def test_complete_write_builds_reversal_from_before_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = self.prepare(root, self.pack(root / "approval.json"))
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            after = {"result": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]}}
            reader = mock.Mock(side_effect=[before, after])
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Id": 1}]}}, 1))
            result = gate.execute(prepared, writer=writer, reader=reader)
            self.assertEqual(result["status"], "complete")
            evidence = root / "state" / "direct-writes" / "test-run-001"
            reversal = json.loads((evidence / "reversal-candidate.json").read_text(encoding="utf-8"))
            self.assertTrue(reversal["requires_new_owner_approval"])
            self.assertEqual(reversal["operations"][0]["params"], {"Campaigns": [{"Id": 1, "Name": "Старое название"}]})
            self.assertFalse(prepared.lock_path.exists())

    def test_completed_run_id_cannot_execute_or_overwrite_evidence_twice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepared = self.prepare(root, self.pack(root / "approval.json"))
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            after = {"result": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]}}
            reader = mock.Mock(side_effect=[before, after])
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Id": 1}]}}, 1))

            first = gate.execute(prepared, writer=writer, reader=reader)
            evidence = root / "state" / "direct-writes" / "test-run-001" / "result.json"
            first_evidence = evidence.read_bytes()

            self.assertEqual(first["status"], "complete")
            with self.assertRaisesRegex(gate.GateError, "run_id уже использован"):
                gate.execute(prepared, writer=writer, reader=reader)
            self.assertEqual(writer.call_count, 1)
            self.assertEqual(reader.call_count, 2)
            self.assertEqual(evidence.read_bytes(), first_evidence)
            self.assertFalse(prepared.lock_path.exists())

    def test_actual_unit_exhaustion_stops_before_next_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = self.pack(root / "approval.json")
            pack["max_api_units"] = 5
            pack["operations"] = [self.operation("first"), self.operation("second")]
            prepared = self.prepare(root, pack)
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            after = {"result": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]}}
            reader = mock.Mock(side_effect=[before, before, after])
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Id": 1}]}}, 4))
            result = gate.execute(prepared, writer=writer, reader=reader)
            self.assertEqual(writer.call_count, 1)
            self.assertEqual(result["operations"][0]["status"], "api_units_bound_exceeded")
            self.assertEqual(result["api_units"], 4)

    def test_reserved_operation_limit_blocks_next_call_before_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pack = self.pack(root / "approval.json")
            first = self.operation("first")
            first["max_api_units"] = 4
            second = self.operation("second")
            second["max_api_units"] = 2
            pack["max_api_units"] = 6
            pack["operations"] = [first, second]
            prepared = self.prepare(root, pack)
            before = {"result": {"Campaigns": [{"Id": 1, "Name": "Старое название"}]}}
            after = {"result": {"Campaigns": [{"Id": 1, "Name": "Новое название"}]}}
            reader = mock.Mock(side_effect=[before, before, after])
            writer = mock.Mock(return_value=({"result": {"UpdateResults": [{"Id": 1}]}}, 5))
            result = gate.execute(prepared, writer=writer, reader=reader)
            self.assertEqual(writer.call_count, 1)
            self.assertEqual(result["operations"][0]["status"], "api_units_bound_exceeded")


if __name__ == "__main__":
    unittest.main()
