#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


callback = load("amocrm_callback", "amocrm_local_callback_server.py")
exchange = load("amocrm_exchange", "exchange_amocrm_token.py")
schema = load("amocrm_schema", "fetch_amocrm_schema.py")


class ReconciliationTests(unittest.TestCase):
    def row(self, **updates):
        value = {
            "source": "SYNTHETIC_SOURCE",
            "occurred_at": "2026-01-02T03:04:05+00:00",
            "status": "SYNTHETIC_STATUS",
            "responsible": "SYNTHETIC_OWNER",
            "external_link": "urn:synthetic:lead:one",
        }
        value.update(updates)
        return value

    def test_all_required_fields_are_compared(self):
        left = self.row()
        right = self.row(responsible="OTHER_SYNTHETIC_OWNER")
        result = schema.reconcile_leads([left], [right])
        self.assertEqual(result[0]["status"], "mismatch")
        self.assertTrue(result[0]["source_match"])
        self.assertTrue(result[0]["time_match"])
        self.assertTrue(result[0]["status_match"])
        self.assertFalse(result[0]["responsible_match"])

    def test_missing_required_field_is_rejected(self):
        row = self.row()
        row.pop("source")
        with self.assertRaises(ValueError):
            schema.reconcile_leads([row], [])

    def test_right_only_row_is_preserved(self):
        result = schema.reconcile_leads([], [self.row()])
        self.assertEqual(result[0]["status"], "right_only")
        self.assertIsNone(result[0]["left"])

    def test_duplicate_external_link_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "дубли"):
            schema.reconcile_leads([self.row(), self.row()], [])


class PaginationTests(unittest.TestCase):
    def test_next_links_are_followed(self):
        pages = {
            "https://synthetic.invalid/page/1": {"_embedded": {"leads": []}, "_links": {"next": {"href": "https://synthetic.invalid/page/2"}}},
            "https://synthetic.invalid/page/2": {"_embedded": {"leads": []}, "_links": {}},
        }
        result, state = schema.fetch_paginated(lambda url: pages[url], "https://synthetic.invalid/page/1")
        self.assertEqual(len(result), 2)
        self.assertEqual(state, {"pages": 2, "complete": True, "status": "complete"})

    def test_repeated_page_is_rejected(self):
        page = {"_links": {"next": {"href": "https://synthetic.invalid/page/1"}}}
        with self.assertRaisesRegex(RuntimeError, "повторную"):
            schema.fetch_paginated(lambda _url: page, "https://synthetic.invalid/page/1")


class SecretFileTests(unittest.TestCase):
    def private_json(self, root: Path, name: str, value):
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(path, 0o600)
        return path

    def test_callback_saves_only_code_with_private_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "code.json"
            callback.atomic_code(path, "SYNTHETIC_AUTHORIZATION_CODE")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"authorization_code": "SYNTHETIC_AUTHORIZATION_CODE"})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertNotIn("callback?", path.read_text(encoding="utf-8"))

    def test_token_payload_reads_secrets_only_from_private_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            integration = {
                "subdomain": "synthetic-account",
                "client_id": "SYNTHETIC_CLIENT",
                "client_secret": "SYNTHETIC_SECRET",
                "redirect_uri": "https://synthetic.invalid/callback",
            }
            code_file = self.private_json(root, "code.json", {"authorization_code": "SYNTHETIC_CODE"})
            token_file = root / "token.json"
            payload = exchange.build_payload(integration, code_file, token_file, False)
            self.assertEqual(payload["code"], "SYNTHETIC_CODE")
            self.assertEqual(payload["grant_type"], "authorization_code")

    def test_world_readable_secret_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials.json"
            path.write_text("{}", encoding="utf-8")
            os.chmod(path, 0o644)
            with self.assertRaisesRegex(RuntimeError, "0600"):
                exchange.private_json(path)

    def test_schema_output_is_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "schema" / "summary.json"
            schema.atomic_json(path, {"status": "complete"})
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)


if __name__ == "__main__":
    unittest.main()
