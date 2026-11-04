"""Remote source icons must enforce the same constraints as local plugin bundles."""

import base64
import importlib.util
import io
import json
import unittest
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-plugin-pr.py"
SPEC = importlib.util.spec_from_file_location("validate_plugin_pr", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class RemoteIconValidationTests(unittest.TestCase):
    @staticmethod
    def source_archive(icon_path: str, icon_bytes: bytes) -> zipfile.ZipFile:
        manifest = {
            "name": "example",
            "version": "1.0.0",
            "description": "Example plugin",
            "repository": "https://github.com/maker/example",
            "license": "MIT",
            "interface": {
                "displayName": "Example",
                "shortDescription": "Example plugin",
                "composerIcon": "./" + icon_path,
            },
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(
                "example-main/.codex-plugin/plugin.json", json.dumps(manifest)
            )
            archive.writestr("example-main/" + icon_path, icon_bytes)
        return zipfile.ZipFile(io.BytesIO(buffer.getvalue()))

    def validate(self, path: str, content: bytes) -> list[str]:
        archive = self.source_archive(path, content)
        with archive, patch.object(
            validator, "fetch_repo_archive", return_value=archive
        ):
            errors, warnings = validator.validate_remote_repo("maker", "example")
        self.assertEqual(warnings, [])
        return errors

    def test_rejects_unsupported_extension(self):
        errors = self.validate("assets/icon.txt", b"not an image")
        self.assertTrue(any("unsupported format" in error for error in errors), errors)

    def test_rejects_embedded_base64_svg(self):
        errors = self.validate(
            "assets/icon.svg",
            b'<svg><image href="data:image/png;base64,AAA="/></svg>',
        )
        self.assertIn("SVG icon contains embedded base64 raster data.", errors)

    def test_rejects_case_variant_embedded_image_uri(self):
        errors = self.validate(
            "assets/icon.svg",
            b'<svg><image HREF="DATA:IMAGE/PNG;BASE64,AAA="/></svg>',
        )
        self.assertIn("SVG icon contains embedded base64 raster data.", errors)

    def test_allows_harmless_base64_word_in_title(self):
        errors = self.validate(
            "assets/icon.svg",
            b"<svg><title>Base64 encoding explained</title></svg>",
        )
        self.assertEqual(errors, [])

    def test_rejects_entity_encoded_embedded_image_uri(self):
        errors = self.validate(
            "assets/icon.svg",
            b'<svg><image href="data&#58;image/png;base64,AAA="/></svg>',
        )
        self.assertIn("SVG icon contains embedded base64 raster data.", errors)

    def test_rejects_placeholder_svg(self):
        errors = self.validate("assets/icon.svg", b"<svg><!-- TODO --></svg>")
        self.assertIn("SVG icon contains TODO/PLACEHOLDER text.", errors)

    def test_rejects_icon_exceeding_50_kib(self):
        oversized_png = b"\x89PNG\r\n\x1a\n" + b"x" * (validator.MAX_ICON_SIZE_BYTES + 1)
        errors = self.validate("assets/icon.png", oversized_png)
        self.assertTrue(any("exceeds 50KB" in error for error in errors), errors)

    def test_oversized_zip_icon_is_rejected_before_expansion(self):
        archive = self.source_archive(
            "assets/icon.png", b"X" * (validator.MAX_ICON_SIZE_BYTES + 1)
        )
        original_read = archive.read

        def reject_icon_expansion(name, *args, **kwargs):
            if str(name).endswith("/assets/icon.png"):
                raise AssertionError("Oversized ZIP member must not be expanded")
            return original_read(name, *args, **kwargs)

        with archive, patch.object(
            validator, "fetch_repo_archive", return_value=archive
        ), patch.object(archive, "read", side_effect=reject_icon_expansion):
            errors, warnings = validator.validate_remote_repo("maker", "example")

        self.assertEqual(warnings, [])
        self.assertTrue(any("exceeds 50KB" in error for error in errors), errors)

    def test_corrupt_remote_icon_reports_clean_error(self):
        archive = self.source_archive("assets/icon.png", b"PNG")
        original_read = archive.read

        def corrupt_icon(name, *args, **kwargs):
            if str(name).endswith("/assets/icon.png"):
                raise zipfile.BadZipFile("invalid icon payload CRC")
            return original_read(name, *args, **kwargs)

        with archive, patch.object(
            validator, "fetch_repo_archive", return_value=archive
        ), patch.object(archive, "read", side_effect=corrupt_icon):
            errors, warnings = validator.validate_remote_repo("maker", "example")

        self.assertEqual(warnings, [])
        self.assertTrue(
            any("corrupt archive member" in error for error in errors), errors
        )

    def test_rejects_parent_path_in_remote_icon(self):
        errors = self.validate("../private/icon.png", b"not an icon")
        self.assertIn("composerIcon must be a safe plugin-relative path", errors)

    def test_rejects_windows_style_escape_in_remote_icon(self):
        errors = self.validate("..\\\\private\\\\icon.png", b"not an icon")
        self.assertIn("composerIcon must be a safe plugin-relative path", errors)

    def test_rejects_local_symlink_icon_escape(self):
        manifest = {
            "name": "example",
            "version": "1.0.0",
            "description": "Example plugin",
            "repository": "https://github.com/maker/example",
            "license": "MIT",
            "interface": {
                "displayName": "Example",
                "shortDescription": "Example plugin",
                "composerIcon": "./assets/icon.png",
            },
        }
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "example"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / "assets").mkdir()
            outside = root / "outside.png"
            outside.write_bytes(b"private")
            (bundle / "assets" / "icon.png").symlink_to(outside)
            (bundle / ".codex-plugin" / "plugin.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with patch.object(validator, "REPO_ROOT", root):
                errors, _warnings = validator.validate_local_bundle(bundle)
        self.assertIn("composerIcon must stay within its plugin bundle", errors)

    def test_local_icon_directory_reports_validation_error(self):
        # A manifest may point to an existing directory named like an icon.
        # It must not abort the validator with IsADirectoryError.
        manifest = {
            "name": "example",
            "version": "1.0.0",
            "description": "Example plugin",
            "repository": "https://github.com/maker/example",
            "license": "MIT",
            "interface": {
                "displayName": "Example",
                "shortDescription": "Example plugin",
                "composerIcon": "./assets/icon.png",
            },
        }
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            bundle = root / "plugins" / "maker" / "example"
            (bundle / ".codex-plugin").mkdir(parents=True)
            (bundle / "assets" / "icon.png").mkdir(parents=True)
            (bundle / ".codex-plugin" / "plugin.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            with patch.object(validator, "REPO_ROOT", root):
                errors, _warnings = validator.validate_local_bundle(bundle)
        self.assertTrue(
            any("not a regular file" in error for error in errors), errors
        )

    def test_accepts_valid_small_png(self):
        # A real one-pixel PNG, not the literal ASCII sequence "\\x89PNG".
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
            "AAAAC0lEQVR42mP8/x8AAwMCAO+/6vcAAAAASUVORK5CYII="
        )
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        errors = self.validate("assets/icon.png", png)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
