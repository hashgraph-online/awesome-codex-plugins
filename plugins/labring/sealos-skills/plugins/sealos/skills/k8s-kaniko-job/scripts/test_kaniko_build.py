"""Security regression tests for the Kaniko executor's output boundaries."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).with_name("kaniko-build.py")
SPEC = importlib.util.spec_from_file_location("kaniko_build", SCRIPT)
KANIKO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(KANIKO)


class KanikoBuildTests(unittest.TestCase):
    def test_registry_secret_uses_kubectl_stdin(self):
        with mock.patch.object(KANIKO, "kubectl", return_value=(0, "", "")) as kubectl:
            KANIKO.create_registry_secret("ns-test", "user", "token-value", "registry-test")
        args, kwargs = kubectl.call_args
        self.assertEqual(args[0], ["create", "-f", "-"])
        payload = json.loads(kwargs["input_text"])
        self.assertEqual(payload["metadata"]["name"], "registry-test")
        self.assertIn("config.json", payload["stringData"])

    def test_s3_secret_uses_kubectl_stdin(self):
        with (
            mock.patch.dict(os.environ, {"AWS_SECRET_ACCESS_KEY": "secret-value"}),
            mock.patch.object(KANIKO, "kubectl", return_value=(0, "", "")) as kubectl,
        ):
            _, secret_name = KANIKO.s3_credential_env({}, "ns-test")
        args, kwargs = kubectl.call_args
        self.assertEqual(args[0], ["create", "-f", "-"])
        payload = json.loads(kwargs["input_text"])
        self.assertEqual(payload["metadata"]["name"], secret_name)
        self.assertEqual(payload["stringData"]["AWS_SECRET_ACCESS_KEY"], "secret-value")

    def test_render_only_redacts_runtime_and_build_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory) / "runtime.json"
            runtime.write_text(json.dumps({
                "accessKeyId": "private-access-id",
                "secretKeyRef": {"name": "private-secret-name", "key": "private-key"},
                "s3Endpoint": "http://private-endpoint:1319",
            }))
            result = subprocess.run(
                [
                    sys.executable, str(SCRIPT), "--image", "ghcr.io/demo/app:tag",
                    "--runtime-file", str(runtime), "--render-only",
                    "--build-arg", "EXAMPLE=private-build-value",
                ],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("kind: Job", result.stdout)
        self.assertIn("--digest-file=/dev/termination-log", result.stdout)
        for secret in (
            "private-access-id", "private-secret-name", "private-key",
            "private-endpoint", "private-build-value",
        ):
            self.assertNotIn(secret, result.stdout + result.stderr)

    def test_invalid_image_is_rejected_without_echoing_it(self):
        image = "https://evil.example/ghcr.io/demo/app:tag"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--image", image, "--render-only"],
            capture_output=True, text=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(image, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
