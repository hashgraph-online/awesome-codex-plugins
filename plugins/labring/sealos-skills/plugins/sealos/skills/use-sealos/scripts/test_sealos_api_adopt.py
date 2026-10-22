#!/usr/bin/env python3
"""Unit tests for Brain Template Instance adoption in sealos-api.py.

Mocks http_json; does not hit the network.
"""

import argparse
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sealos-api.py")
SPEC = importlib.util.spec_from_file_location("sealos_api", SCRIPT)
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)

ADOPT_OK = {
    "project": {"id": "proj-1"},
    "adoption": {"status": "adopted", "warnings": []},
}


class FakeHttp:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, url, method="GET", headers=None, data=None, **_kwargs):
        self.calls.append(
            {"url": url, "method": method, "headers": dict(headers or {}), "data": data}
        )
        if not self._responses:
            raise AssertionError(f"unexpected http_json call: {method} {url}")
        return self._responses.pop(0)

    def brain_calls(self):
        return [c for c in self.calls if "/adopt-template-instance" in c["url"]]

    def template_calls(self):
        return [c for c in self.calls if "template." in c["url"]]


class AdoptTests(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()
        os.environ.pop("SEALAI_DEPLOY_TASK_ID", None)
        os.environ.pop("SEALAI_PROJECT_ID", None)
        os.environ.pop("SEALAI_DEPLOY_LABELS_JSON", None)
        self.sleep_patch = patch.object(api.time, "sleep")
        self.sleep = self.sleep_patch.start()
        self.kc_patch = patch.object(api, "load_kubeconfig", return_value="apiVersion: v1")
        self.kc_patch.start()
        self.domain_patch = patch.object(api, "region_domain", return_value="usw-1.sealos.io")
        self.domain_patch.start()

    def tearDown(self):
        self.sleep_patch.stop()
        self.kc_patch.stop()
        self.domain_patch.stop()
        os.environ.clear()
        os.environ.update(self._env)

    def _adopt(self, instance="my-instance", template_name=None, dry_run=False, http=None):
        if http is not None:
            with patch.object(api, "http_json", http):
                return api.maybe_adopt_template_instance(
                    instance, template_name=template_name, dry_run=dry_run
                )
        return api.maybe_adopt_template_instance(
            instance, template_name=template_name, dry_run=dry_run
        )

    def test_skip_when_deploy_task_id_set(self):
        os.environ["SEALAI_DEPLOY_TASK_ID"] = "task-1"
        http = FakeHttp([])
        result = self._adopt(http=http)
        self.assertEqual(result["skipped"], True)
        self.assertEqual(result["reason"], "managed")
        self.assertIsNone(result["ok"])
        self.assertEqual(http.calls, [])

    def test_skip_when_project_id_set(self):
        os.environ["SEALAI_PROJECT_ID"] = "proj-1"
        http = FakeHttp([])
        result = self._adopt(http=http)
        self.assertEqual(result["reason"], "managed")
        self.assertEqual(http.calls, [])

    def test_skip_when_region_is_sealos_run(self):
        self.domain_patch.stop()
        self.domain_patch = patch.object(api, "region_domain", return_value="gzg.sealos.run")
        self.domain_patch.start()
        http = FakeHttp([])
        result = self._adopt(http=http)
        self.assertEqual(result["skipped"], True)
        self.assertEqual(result["reason"], "not-sealos-io")
        self.assertIsNone(result["ok"])
        self.assertEqual(http.calls, [])

    def test_skip_sealos_run_even_when_managed_env_set(self):
        os.environ["SEALAI_PROJECT_ID"] = "proj-1"
        self.domain_patch.stop()
        self.domain_patch = patch.object(api, "region_domain", return_value="bja.sealos.run")
        self.domain_patch.start()
        http = FakeHttp([])
        result = self._adopt(http=http)
        self.assertEqual(result["reason"], "not-sealos-io")
        self.assertEqual(http.calls, [])

    def test_skip_dry_run(self):
        http = FakeHttp([])
        result = self._adopt(dry_run=True, http=http)
        self.assertEqual(result["skipped"], True)
        self.assertEqual(result["reason"], "dry-run")
        self.assertIsNone(result["ok"])
        self.assertEqual(http.calls, [])

    def test_success_post_body_has_instance_name_no_namespace(self):
        http = FakeHttp([(200, ADOPT_OK)])
        result = self._adopt(instance="my-instance", template_name="memos", http=http)
        self.assertEqual(result["skipped"], False)
        self.assertTrue(result["ok"])
        self.assertEqual(result["projectId"], "proj-1")
        self.assertEqual(len(http.calls), 1)
        call = http.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"],
            "https://brain.usw-1.sealos.io/api/projects/adopt-template-instance",
        )
        self.assertEqual(
            call["data"],
            {"instanceName": "my-instance", "templateName": "memos"},
        )
        self.assertNotIn("namespace", call["data"])
        self.assertNotIn("displayName", call["data"])
        quoted = api.urllib.parse.quote("apiVersion: v1", safe="")
        self.assertEqual(call["headers"]["Authorization"], f"Bearer {quoted}")

    def test_success_omits_template_name_when_unknown(self):
        http = FakeHttp([(200, ADOPT_OK)])
        self._adopt(instance="my-instance", http=http)
        self.assertEqual(http.calls[0]["data"], {"instanceName": "my-instance"})

    def test_404_then_200_retries(self):
        http = FakeHttp(
            [
                (404, {"error": "Instance not found"}),
                (200, ADOPT_OK),
            ]
        )
        result = self._adopt(http=http)
        self.assertTrue(result["ok"])
        self.assertEqual(result["status"], 200)
        self.assertEqual(len(http.brain_calls()), 2)
        self.assertEqual(http.brain_calls()[0]["data"], http.brain_calls()[1]["data"])
        self.sleep.assert_called_once_with(api.ADOPT_RETRY_SLEEP_SECONDS)

    def test_incomplete_resource_set_then_retry(self):
        incomplete = {
            "project": {"id": "proj-1"},
            "adoption": {"warnings": ["incompleteResourceSet"]},
        }
        http = FakeHttp([(200, incomplete), (200, ADOPT_OK)])
        result = self._adopt(http=http)
        self.assertTrue(result["ok"])
        self.assertEqual(result["warnings"], [])
        self.assertEqual(len(http.calls), 2)
        self.sleep.assert_called_once()

    def test_transport_failure_then_200_retries(self):
        http = FakeHttp(
            [
                (0, {"error": "request to https://brain.usw-1.sealos.io failed"}),
                (200, ADOPT_OK),
            ]
        )
        result = self._adopt(http=http)
        self.assertTrue(result["ok"])
        self.assertEqual(len(http.calls), 2)
        self.sleep.assert_called_once_with(api.ADOPT_RETRY_SLEEP_SECONDS)

    def test_409_does_not_retry(self):
        http = FakeHttp([(409, {"error": "already labeled by another project"})])
        result = self._adopt(http=http)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], 409)
        self.assertEqual(len(http.calls), 1)
        self.sleep.assert_not_called()

    def test_managed_skip_does_not_call_brain_on_deploy(self):
        os.environ["SEALAI_DEPLOY_TASK_ID"] = "task-1"
        http = FakeHttp([(201, {"name": "demo-abc"})])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.yaml")
            with open(path, "w") as f:
                f.write("apiVersion: app.sealos.io/v1\nkind: Template\nmetadata:\n  name: demo\n")
            args = argparse.Namespace(
                template=path,
                args_json=None,
                args_file=None,
                labels_json=None,
                dry_run=False,
            )
            buf = io.StringIO()
            with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
                api.cmd_deploy(args)
        out = json.loads(buf.getvalue())
        self.assertTrue(out["success"])
        self.assertEqual(out["brain_adoption"]["reason"], "managed")
        self.assertEqual(len(http.template_calls()), 1)
        self.assertEqual(http.brain_calls(), [])

    def test_deploy_exit_zero_when_adopt_fails(self):
        http = FakeHttp(
            [(201, {"name": "demo-abc"})]
            + [(502, {"error": "label failed"})] * api.ADOPT_MAX_ATTEMPTS
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.yaml")
            with open(path, "w") as f:
                f.write("apiVersion: app.sealos.io/v1\nkind: Template\nmetadata:\n  name: demo\n")
            args = argparse.Namespace(
                template=path,
                args_json=None,
                args_file=None,
                labels_json=None,
                dry_run=False,
            )
            buf = io.StringIO()
            with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
                api.cmd_deploy(args)
        out = json.loads(buf.getvalue())
        self.assertTrue(out["success"])
        self.assertFalse(out["brain_adoption"]["ok"])
        self.assertEqual(out["brain_adoption"]["status"], 502)
        self.assertEqual(len(http.brain_calls()), api.ADOPT_MAX_ATTEMPTS)
        self.assertEqual(http.brain_calls()[0]["data"]["instanceName"], "demo-abc")
        self.assertEqual(http.brain_calls()[0]["data"]["templateName"], "demo")

    def test_deploy_skip_dry_run_does_not_call_brain(self):
        http = FakeHttp([(200, {"name": "demo-abc"})])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.yaml")
            with open(path, "w") as f:
                f.write("kind: Template\nmetadata:\n  name: demo\n")
            args = argparse.Namespace(
                template=path,
                args_json=None,
                args_file=None,
                labels_json=None,
                dry_run=True,
            )
            buf = io.StringIO()
            with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
                api.cmd_deploy(args)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["brain_adoption"]["reason"], "dry-run")
        self.assertEqual(http.brain_calls(), [])

    def test_deploy_skip_sealos_run_does_not_call_brain(self):
        self.domain_patch.stop()
        self.domain_patch = patch.object(api, "region_domain", return_value="hzh.sealos.run")
        self.domain_patch.start()
        http = FakeHttp([(201, {"name": "demo-abc"})])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.yaml")
            with open(path, "w") as f:
                f.write("apiVersion: app.sealos.io/v1\nkind: Template\nmetadata:\n  name: demo\n")
            args = argparse.Namespace(
                template=path,
                args_json=None,
                args_file=None,
                labels_json=None,
                dry_run=False,
            )
            buf = io.StringIO()
            with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
                api.cmd_deploy(args)
        out = json.loads(buf.getvalue())
        self.assertTrue(out["success"])
        self.assertEqual(out["brain_adoption"]["reason"], "not-sealos-io")
        self.assertEqual(len(http.template_calls()), 1)
        self.assertEqual(http.brain_calls(), [])

    def test_adopt_subcommand_zero_on_sealos_run(self):
        self.domain_patch.stop()
        self.domain_patch = patch.object(api, "region_domain", return_value="gzg.sealos.run")
        self.domain_patch.start()
        http = FakeHttp([])
        args = argparse.Namespace(instance="foo", template_name=None)
        buf = io.StringIO()
        with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
            api.cmd_adopt(args)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["brain_adoption"]["reason"], "not-sealos-io")
        self.assertEqual(http.calls, [])

    def test_adopt_subcommand_nonzero_on_502(self):
        http = FakeHttp([(502, {"error": "label failed"})] * api.ADOPT_MAX_ATTEMPTS)
        args = argparse.Namespace(instance="foo", template_name=None)
        buf = io.StringIO()
        with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
            with self.assertRaises(SystemExit) as caught:
                api.cmd_adopt(args)
        self.assertEqual(caught.exception.code, 1)
        out = json.loads(buf.getvalue())
        self.assertFalse(out["brain_adoption"]["ok"])
        self.assertEqual(out["brain_adoption"]["status"], 502)

    def test_extract_wrapped_response_shapes(self):
        self.assertEqual(api.extract_instance_name({"name": "a"}), "a")
        self.assertEqual(api.extract_instance_name({"data": {"name": "b"}}), "b")
        self.assertEqual(api.extract_instance_name({"data": {"instanceName": "c"}}), "c")
        self.assertEqual(api.extract_instance_name({}, fallback="store-name"), "store-name")
        self.assertIsNone(api.extract_instance_name({"message": "ok"}))

    def test_missing_instance_name_skips_and_deploy_stays_zero(self):
        http = FakeHttp([(201, {"message": "created"})])
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.yaml")
            with open(path, "w") as f:
                f.write("kind: Template\nmetadata:\n  name: demo\n")
            args = argparse.Namespace(
                template=path,
                args_json=None,
                args_file=None,
                labels_json=None,
                dry_run=False,
            )
            buf = io.StringIO()
            with patch.object(api, "http_json", http), contextlib.redirect_stdout(buf):
                api.cmd_deploy(args)
        out = json.loads(buf.getvalue())
        self.assertTrue(out["success"])
        self.assertEqual(out["brain_adoption"]["reason"], "missing-instance-name")
        self.assertTrue(out["brain_adoption"]["skipped"])
        self.assertEqual(http.brain_calls(), [])


class BrainRegionTests(unittest.TestCase):
    def test_io_regions_enabled(self):
        for domain in ("usw-1.sealos.io", "sealos.io", "USW-1.SEALOS.IO", "usw-1.sealos.io."):
            self.assertTrue(api.is_brain_adoption_region(domain), domain)

    def test_run_and_other_hosts_disabled(self):
        for domain in (
            "gzg.sealos.run",
            "bja.sealos.run",
            "hzh.sealos.run",
            "evil.sealos.io.example.com",
            "notsealos.io",
            "",
            None,
        ):
            self.assertFalse(api.is_brain_adoption_region(domain), domain)


if __name__ == "__main__":
    unittest.main()
