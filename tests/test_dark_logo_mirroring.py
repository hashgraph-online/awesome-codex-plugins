"""Dark-logo asset selection and bundle isolation regressions."""

import importlib.util
import io
import json
import tempfile
import unittest
import unittest.mock
import zipfile
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "generate_plugins_json", Path(__file__).resolve().parents[1] / "scripts/generate_plugins_json.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DarkLogoMirroringTests(unittest.TestCase):
    def test_normal_and_metadata_only_mirrors_preserve_dark_logo_bytes(self):
        for metadata_only in (False, True):
            with self.subTest(metadata_only=metadata_only), tempfile.TemporaryDirectory() as scratch:
                manifest = {"name": "sample", "interface": {"logoDark": "./assets/dark.svg"}}
                content = b'<svg xmlns="http://www.w3.org/2000/svg"><path fill="#fff"/></svg>\n'
                archive_data = io.BytesIO()
                with zipfile.ZipFile(archive_data, "w") as archive:
                    archive.writestr("archive/.codex-plugin/plugin.json", json.dumps(manifest))
                    archive.writestr("archive/assets/dark.svg", content)
                archive_data.seek(0)
                with (
                    zipfile.ZipFile(archive_data) as archive,
                    unittest.mock.patch.object(MODULE, "fetch_repo_archive", return_value=archive),
                    unittest.mock.patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)),
                    unittest.mock.patch.object(MODULE, "is_metadata_only_mirror", return_value=metadata_only),
                ):
                    mirrored, _path, _relative = MODULE.mirror_plugin_bundle(
                        {"name": "sample", "owner": "example", "repo": "sample"}
                    )
                destination = Path(scratch) / "example/sample"
                self.assertEqual((destination / "assets/dark.svg").read_bytes(), content)
                self.assertEqual(json.loads((destination / ".codex-plugin/plugin.json").read_text()), mirrored)
                self.assertEqual(mirrored["interface"]["logoDark"], manifest["interface"]["logoDark"])

    def test_absent_optional_dark_logo_does_not_add_an_asset(self):
        root = MODULE.PurePosixPath("archive")
        names = {"archive/.codex-plugin/plugin.json", "archive/assets/dark.svg"}
        for interface in ({}, {"logoDark": None}, {"logoDark": "./assets/missing.svg"}):
            with self.subTest(interface=interface):
                manifest = {"interface": interface}
                self.assertEqual(
                    MODULE.collect_selected_paths(manifest, names, root, {"owner": "example", "repo": "sample"}),
                    {".codex-plugin/plugin.json"},
                )
                self.assertEqual(
                    MODULE.collect_metadata_only_paths(manifest, names, root), {".codex-plugin/plugin.json"}
                )

    def test_unsafe_dark_logo_paths_do_not_select_outside_assets(self):
        root = MODULE.PurePosixPath("archive/plugins/sample")
        names = {"archive/outside.svg", "archive/plugins/sample/assets/../../../outside.svg"}
        for path in ("../../outside.svg", "/archive/outside.svg", "assets/../../../outside.svg", "C:/outside.svg"):
            with self.subTest(path=path):
                manifest = {"interface": {"logoDark": path}}
                self.assertEqual(
                    MODULE.collect_selected_paths(manifest, names, root, {"owner": "example", "repo": "sample"}),
                    {".codex-plugin/plugin.json"},
                )
                self.assertEqual(
                    MODULE.collect_metadata_only_paths(manifest, names, root), {".codex-plugin/plugin.json"}
                )

    def test_shared_repository_entries_keep_distinct_dark_logo_assets(self):
        archive_data = io.BytesIO()
        with zipfile.ZipFile(archive_data, "w") as archive:
            for name in ("alpha", "beta"):
                manifest = {"name": name, "interface": {"displayName": name, "logoDark": "./assets/dark.svg"}}
                archive.writestr("archive/plugins/{}/.codex-plugin/plugin.json".format(name), json.dumps(manifest))
                archive.writestr("archive/plugins/{}/assets/dark.svg".format(name), name.encode("ascii"))
        archive_data.seek(0)
        with (
            tempfile.TemporaryDirectory() as scratch,
            zipfile.ZipFile(archive_data) as archive,
            unittest.mock.patch.object(MODULE, "fetch_repo_archive", return_value=archive),
            unittest.mock.patch.object(MODULE, "PLUGINS_ROOT", Path(scratch)),
        ):
            paths = []
            for name in ("alpha", "beta"):
                _manifest, marketplace_path, _relative = MODULE.mirror_plugin_bundle(
                    {"name": name, "owner": "example", "repo": "shared", "_mirror_subpath": "true"}
                )
                paths.append(marketplace_path)
            self.assertEqual(len(set(paths)), 2)
            for name in ("alpha", "beta"):
                destination = Path(scratch) / "example/shared/plugins" / name
                self.assertEqual((destination / "assets/dark.svg").read_bytes(), name.encode("ascii"))


if __name__ == "__main__":
    unittest.main()
