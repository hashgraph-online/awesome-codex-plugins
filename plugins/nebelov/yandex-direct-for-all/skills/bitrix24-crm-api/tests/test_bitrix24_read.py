#!/usr/bin/env python3
"""Тесты чтения Битрикс24 без сети: подменённый портал с синтетическими данными."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import bitrix24_read as b24  # noqa: E402

HOOK = "https://example.bitrix24.ru/rest/1/synthetic-code/"
LEADS = [{"ID": str(i), "DATE_CREATE": "2026-10-01T10:00:00+03:00", "PHONE": [{"VALUE": "+70000000000"}],
          "UTM_SOURCE": "yandex"} for i in range(1, 121)]


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Portal:
    def __init__(self, fail_once_503: bool = False):
        self.calls: list[str] = []
        self.fail = fail_once_503

    def __call__(self, request, timeout=None):
        method = request.full_url.rsplit("/", 1)[1].removesuffix(".json")
        self.calls.append(method)
        params = json.loads(request.data or b"{}")
        if self.fail:
            self.fail = False
            raise urllib.error.HTTPError(request.full_url, 503, "busy", {}, io.BytesIO(b'{"error":"QUERY_LIMIT_EXCEEDED"}'))
        if method == "scope":
            return Response(json.dumps({"result": ["crm", "user"]}).encode())
        if method == "crm.status.entity.types":
            return Response(json.dumps({"result": [{"ID": "STATUS"}]}).encode())
        if method == "crm.category.list":
            return Response(json.dumps({"result": {"categories": [{"id": 0, "isDefault": "Y"}]}, "total": 1}).encode())
        if method in ("crm.status.list", "crm.lead.userfield.list", "crm.deal.userfield.list"):
            return Response(json.dumps({"result": []}).encode())
        if method in ("crm.lead.fields", "crm.deal.fields"):
            return Response(json.dumps({"result": {}}).encode())
        if method == "voximplant.statistic.get":
            return Response(json.dumps({"result": [{"ID": "1", "CALL_START_DATE": "x", "COMMENT": "Иван", "CALL_RECORD_URL":
                                                    "https://rec", "PHONE_NUMBER": "+7000"}]}).encode())
        if method == "crm.lead.list":
            after = int(params["filter"][">ID"])
            page = [dict(x) for x in LEADS if int(x["ID"]) > after][:50]
            return Response(json.dumps({"result": page}).encode())
        raise AssertionError(method)


class Bitrix24ReadTests(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"BITRIX24_WEBHOOK_URL": HOOK}, clear=False)
        self.env.start()
        self.sleep = mock.patch.object(b24.time, "sleep", lambda *_: None)
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()
        self.env.stop()

    def test_export_walks_all_pages_by_id_without_personal_data(self):
        portal = Portal()
        with tempfile.TemporaryDirectory() as root, mock.patch.object(b24.urllib.request, "urlopen", portal):
            b24.main(["export", "--entity", "lead", "--since", "2026-10-01", "--until", "2026-11-01", "--out", root])
            rows = json.loads(Path(root, "lead.json").read_text())
            manifest = json.loads(Path(root, "lead.manifest.json").read_text())
        self.assertEqual((len(rows), manifest["pages"], manifest["complete"]), (120, 3, True))
        self.assertNotIn("PHONE", rows[0])
        self.assertNotIn("PHONE", manifest["fields"])

    def test_write_methods_and_nested_batch_are_refused(self):
        with self.assertRaises(ValueError):
            b24.call(HOOK, "crm.lead.update", {})
        with self.assertRaises(ValueError):
            b24.call(HOOK, "batch", {"cmd": {"a": "crm.lead.delete?id=1"}})
        with self.assertRaises(ValueError):
            b24.call(HOOK, "batch", {"cmd": {"a": "batch?cmd=1"}})

    def test_probe_retries_limit_and_hides_webhook(self):
        portal = Portal(fail_once_503=True)
        out = io.StringIO()
        with mock.patch.object(b24.urllib.request, "urlopen", portal), mock.patch("sys.stdout", out):
            b24.main(["probe"])
        self.assertEqual(portal.calls[:2], ["scope", "scope"])
        self.assertNotIn("synthetic-code", out.getvalue())
        self.assertIn('"crm"', out.getvalue())

    def test_error_text_never_contains_webhook(self):
        def leak(request, timeout=None):
            raise urllib.error.HTTPError(request.full_url, 404, "nf", {}, io.BytesIO(
                json.dumps({"error": "NOT_FOUND", "error_description": "no " + HOOK + "scope.json"}).encode()))
        with mock.patch.object(b24.urllib.request, "urlopen", leak), self.assertRaises(RuntimeError) as caught:
            b24.call(HOOK, "scope")
        self.assertNotIn("synthetic-code", str(caught.exception))

    def test_masking_happens_before_truncation(self):
        def leak(request, timeout=None):
            body = ("x" * 190 + " " + HOOK).encode()  # граница обрезки внутри адреса
            raise urllib.error.HTTPError(request.full_url, 500, "err", {}, io.BytesIO(body))
        with mock.patch.object(b24.urllib.request, "urlopen", leak), self.assertRaises(RuntimeError) as caught:
            b24.call(HOOK, "scope")
        self.assertNotIn("synthetic", str(caught.exception))

    def test_personal_fields_need_flag_and_explicit_name(self):
        portal = Portal()
        with tempfile.TemporaryDirectory() as root, mock.patch.object(b24.urllib.request, "urlopen", portal):
            b24.main(["export", "--entity", "call", "--fields", "phone_number,CALL_START_DATE", "--since", "2026-10-01",
                      "--until", "2026-11-01", "--out", root])
            without_flag = json.loads(Path(root, "call.json").read_text())
            b24.main(["export", "--entity", "call", "--fields", "ID", "--include-personal-data", "--since",
                      "2026-10-01", "--until", "2026-11-01", "--out", root])
            flag_but_not_named = json.loads(Path(root, "call.json").read_text())
        self.assertNotIn("PHONE_NUMBER", without_flag[0])
        self.assertEqual(set(flag_but_not_named[0]), {"ID"})

    def test_row_without_id_on_full_page_fails_and_removes_old_export(self):
        broken = [dict(x) for x in LEADS[:50]]
        broken[-1].pop("ID")
        def portal(request, timeout=None):
            return Response(json.dumps({"result": broken}).encode())
        with tempfile.TemporaryDirectory() as root, mock.patch.object(b24.urllib.request, "urlopen", portal):
            Path(root, "lead.json").write_text("[]")
            with self.assertRaises(RuntimeError):
                b24.main(["export", "--entity", "lead", "--since", "2026-10-01", "--until", "2026-11-01", "--out", root])
            self.assertFalse(Path(root, "lead.json").exists())

    def test_missing_webhook_still_removes_old_export(self):
        with tempfile.TemporaryDirectory() as root, mock.patch.dict(os.environ, {"BITRIX24_WEBHOOK_URL": ""}):
            Path(root, "lead.manifest.json").write_text('{"complete": true}')
            with self.assertRaises(ValueError):
                b24.main(["export", "--entity", "lead", "--since", "2026-10-01", "--until", "2026-11-01", "--out", root])
            self.assertFalse(Path(root, "lead.manifest.json").exists())

    def test_telephony_webhook_must_be_https(self):
        with mock.patch.dict(os.environ, {"BITRIX24_TELEPHONY_WEBHOOK_URL": "http://example.bitrix24.ru/rest/1/x/"}):
            with self.assertRaises(ValueError):
                b24.webhook(b24.build_parser().parse_args(["probe"]), telephony=True)

    def test_calls_keep_only_declared_fields_and_id_is_forced(self):
        portal = Portal()
        with tempfile.TemporaryDirectory() as root, mock.patch.object(b24.urllib.request, "urlopen", portal):
            b24.main(["export", "--entity", "call", "--since", "2026-10-01", "--until", "2026-11-01", "--out", root])
            calls = json.loads(Path(root, "call.json").read_text())
            b24.main(["export", "--entity", "lead", "--fields", "UTM_SOURCE", "--since", "2026-10-01",
                      "--until", "2026-11-01", "--out", root])
            manifest = json.loads(Path(root, "lead.manifest.json").read_text())
        self.assertEqual(set(calls[0]), {"ID", "CALL_START_DATE"})
        self.assertEqual((manifest["fields"][0], manifest["rows"], manifest["complete"]), ("ID", 120, True))

    def test_schema_counts_default_category_once(self):
        portal = Portal()
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as root, mock.patch.object(b24.urllib.request, "urlopen", portal), \
                mock.patch("sys.stdout", out):
            b24.main(["schema", "--out", root])
        self.assertEqual(json.loads(out.getvalue())["deal_categories"], 1)

    def test_missing_webhook_is_clear_error(self):
        with mock.patch.dict(os.environ, {"BITRIX24_WEBHOOK_URL": ""}):
            with self.assertRaises(ValueError):
                b24.main(["probe"])


if __name__ == "__main__":
    unittest.main()
