from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import jsonschema


SPEC = importlib.util.spec_from_file_location("validate_tool", Path(__file__).with_name("validate.py"))
tool = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(tool)


class ValidateV2Tests(unittest.TestCase):
    def draft(self):
        return {
            "acceptance_digest": "a" * 64,
            "subject_manifest_digest": "b" * 64,
            "author_context_id": "author",
            "validator_context_id": "validator",
            "freshness_attestation": {"source": "runtime", "attester_identity": "runtime-1"},
            "verdict": "PASS",
            "criteria": [{"id": "c1", "result": "PASS", "evidence_refs": ["e1"]}],
            "findings": [],
            "evidence_refs": ["e1"],
            "checked": ["c1"],
            "not_checked": [],
            "validated_at": "2026-07-14T00:00:00Z",
        }

    def assert_schema_valid(self, artifact):
        schema = json.loads((Path(__file__).parents[3] / "schemas" / "verdict.v2.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(artifact)

    def runtime_facts(self):
        manifest = {
            "schema_version": "subject-manifest.v1",
            "declared_roots": ["src"],
            "exclusions": [],
            "entries": [],
        }
        manifest["canonical_manifest_digest"] = tool.digest_value(tool.manifest_identity(manifest))
        return b"bead:agentops-test\nacceptance: works\n", manifest

    def store_bound(
        self,
        draft,
        destination,
        *,
        scope="PASS",
        author="author",
        validator="validator",
        freshness_source="runtime",
        freshness_attester="validator",
    ):
        intent, manifest = self.runtime_facts()
        return tool.store_verdict(
            draft,
            destination,
            intent,
            manifest,
            author,
            scope,
            validator,
            freshness_source,
            freshness_attester,
        )

    def test_manifest_is_content_addressed_and_detects_mutation(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "bin").mkdir()
            subject = root / "bin" / "tool"
            subject.write_text("one", encoding="utf-8")
            subject.chmod(0o755)
            manifest = tool.build_manifest(root, ["bin"], [])
            self.assertTrue(tool.verify_manifest(manifest, root, None)[0])
            subject.write_text("two", encoding="utf-8")
            self.assertFalse(tool.verify_manifest(manifest, root, None)[0])

    def test_git_metadata_is_not_identity_bearing(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "value").write_text("same", encoding="utf-8")
            first = tool.build_manifest(root, ["."], [], git_metadata={"commit": "one"})
            second = tool.build_manifest(root, ["."], [], git_metadata={"commit": "two"})
            self.assertEqual(first["canonical_manifest_digest"], second["canonical_manifest_digest"])
            self.assertNotEqual(first["git_metadata"], second["git_metadata"])
            self.assertTrue(tool.verify_manifest(first, root, None)[0])
            self.assertTrue(tool.verify_manifest(second, root, None)[0])

    def test_symlink_and_deletion_identity(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "target").write_text("x", encoding="utf-8")
            (root / "link").symlink_to("target")
            base = tool.build_manifest(root, ["."], [])
            (root / "target").unlink()
            current = tool.build_manifest(root, ["."], [], base)
            kinds = {entry["path"]: entry["kind"] for entry in current["entries"]}
            self.assertEqual(kinds["link"], "symlink")
            self.assertEqual(kinds["target"], "deletion")

    def test_verdict_identity_floor_and_idempotence(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = self.draft()
            draft["author_context_id"] = "same"
            draft["validator_context_id"] = "same"
            first, path, existed = self.store_bound(draft, Path(raw), author="same", validator="same")
            self.assertEqual(first["verdict"], "NOT_PROVEN")
            self.assert_schema_valid(first)
            self.assertFalse(existed)
            second, second_path, existed = self.store_bound(draft, Path(raw), author="same", validator="same")
            self.assertTrue(existed)
            self.assertEqual(path, second_path)
            self.assertEqual(json.loads(path.read_text())["artifact_digest"], first["artifact_digest"])

    def test_runtime_identity_and_attestation_replace_missing_model_fields(self):
        for missing in ("author_context_id", "validator_context_id", "freshness_attestation"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as raw:
                draft = self.draft()
                draft.pop(missing)
                artifact, _path, _existed = self.store_bound(draft, Path(raw))
                self.assertEqual(artifact["verdict"], "PASS")
                self.assert_schema_valid(artifact)

    def test_runtime_validator_and_freshness_override_model_claims(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = self.draft()
            draft["validator_context_id"] = "model-claimed-validator"
            draft["freshness_attestation"] = {"source": "caller", "attester_identity": "model-claimed-attester"}
            artifact, _path, _existed = self.store_bound(draft, Path(raw))
            self.assertEqual(artifact["validator_context_id"], "validator")
            self.assertEqual(
                artifact["freshness_attestation"],
                {"source": "runtime", "attester_identity": "validator"},
            )
            self.assertEqual(artifact["verdict"], "PASS")

    def test_pass_with_failed_criterion_is_downgraded(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = self.draft()
            draft["criteria"][0]["result"] = "FAIL"
            artifact, _path, _existed = self.store_bound(draft, Path(raw))
            self.assertEqual(artifact["verdict"], "NOT_PROVEN")
            self.assert_schema_valid(artifact)

    def test_pass_without_evidence_is_downgraded(self):
        mutations = (
            lambda draft: draft.__setitem__("evidence_refs", []),
            lambda draft: draft.__setitem__("checked", []),
            lambda draft: draft["criteria"][0].__setitem__("evidence_refs", []),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as raw:
                draft = self.draft()
                mutate(draft)
                artifact, _path, _existed = self.store_bound(draft, Path(raw))
                self.assertEqual(artifact["verdict"], "NOT_PROVEN")
                self.assertIn("PASS requires evidence", artifact["findings"][-1]["summary"])
                self.assert_schema_valid(artifact)

    def test_intent_snapshot_is_content_addressed_and_idempotent(self):
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw)
            payload = b"caller intent\nacceptance: works\n"
            first, existed = tool.snapshot_intent(payload, destination)
            self.assertFalse(existed)
            self.assertEqual(first.name, f"{tool.hashlib.sha256(payload).hexdigest()}.intent")
            self.assertEqual(first.read_bytes(), payload)
            second, existed = tool.snapshot_intent(payload, destination)
            self.assertTrue(existed)
            self.assertEqual(first, second)

    def test_store_verdict_cli_snapshots_intent_before_persistence(self):
        with tempfile.TemporaryDirectory() as raw:
            workspace = Path(raw)
            intent, manifest = self.runtime_facts()
            intent_path = workspace / "intent.txt"
            manifest_path = workspace / "manifest.json"
            draft_path = workspace / "draft.json"
            intent_path.write_bytes(intent)
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            draft_path.write_text(json.dumps(self.draft()), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).with_name("validate.py")),
                    "store-verdict",
                    "--draft",
                    str(draft_path),
                    "--intent-source",
                    str(intent_path),
                    "--subject-manifest",
                    str(manifest_path),
                    "--author-context-id",
                    "author",
                    "--validator-context-id",
                    "validator",
                    "--freshness-source",
                    "runtime",
                    "--freshness-attester-id",
                    "validator",
                    "--scope-result",
                    "PASS",
                    "--workspace",
                    str(workspace),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            snapshot = Path(response["intent_ref"])
            self.assertEqual(snapshot.read_bytes(), intent)
            self.assertEqual(response["acceptance_digest"], tool.hashlib.sha256(intent).hexdigest())

    def test_corrupt_existing_digest_yields_new_not_proven_artifact(self):
        with tempfile.TemporaryDirectory() as raw:
            destination = Path(raw)
            draft = self.draft()
            artifact, path, _ = self.store_bound(draft, destination)
            path.write_text("corrupt\n", encoding="utf-8")
            replacement, replacement_path, existed = self.store_bound(draft, destination)
            self.assertEqual(replacement["verdict"], "NOT_PROVEN")
            self.assertNotEqual(replacement["artifact_digest"], artifact["artifact_digest"])
            self.assertNotEqual(replacement_path, path)
            self.assertFalse(existed)
            self.assert_schema_valid(replacement)

    def test_incomplete_draft_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaisesRegex(tool.ContractError, "missing required fields"):
                tool.store_verdict({"verdict": "FAIL"}, Path(raw))
            self.assertEqual(list(Path(raw).iterdir()), [])

    def test_unknown_field_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = self.draft()
            draft["next_action"] = "repair"
            with self.assertRaisesRegex(tool.ContractError, "unknown fields"):
                self.store_bound(draft, Path(raw))
            self.assertEqual(list(Path(raw).iterdir()), [])

    def test_pass_without_runtime_facts_is_not_proven(self):
        with tempfile.TemporaryDirectory() as raw:
            artifact, _path, _existed = tool.store_verdict(self.draft(), Path(raw))
            self.assertEqual(artifact["verdict"], "NOT_PROVEN")
            self.assertIn("runtime intent source is missing", artifact["findings"][-1]["summary"])
            self.assert_schema_valid(artifact)

    def test_runtime_facts_override_model_authored_digests(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = self.draft()
            draft["acceptance_digest"] = "c" * 64
            draft["subject_manifest_digest"] = "d" * 64
            artifact, _path, _existed = self.store_bound(draft, Path(raw))
            intent, manifest = self.runtime_facts()
            self.assertEqual(artifact["acceptance_digest"], tool.hashlib.sha256(intent).hexdigest())
            self.assertEqual(artifact["subject_manifest_digest"], manifest["canonical_manifest_digest"])
            self.assertEqual(artifact["verdict"], "PASS")

    def test_runtime_scope_failure_forces_fail(self):
        with tempfile.TemporaryDirectory() as raw:
            artifact, _path, _existed = self.store_bound(self.draft(), Path(raw), scope="FAIL")
            self.assertEqual(artifact["verdict"], "FAIL")
            self.assertEqual(artifact["findings"][-1]["id"], "validate.scope")
            self.assert_schema_valid(artifact)


if __name__ == "__main__":
    unittest.main()
