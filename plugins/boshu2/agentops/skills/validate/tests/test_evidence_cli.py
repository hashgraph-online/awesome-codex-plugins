"""Developer-only installed-binary evidence test; AO_BIN selects the candidate.

The driver uses Python, but every candidate process runs with an empty PATH.
No reference helper or Python executable is available on that runtime path.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


class EvidenceCLI(unittest.TestCase):
    def test_git_storage_boundaries_before_writes(self):
        candidate = Path(os.environ["AO_BIN"]).resolve(strict=True)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            subject = base / "subject"
            inputs = base / "inputs"
            empty_path = base / "empty-path"
            for directory in (subject, inputs, empty_path):
                directory.mkdir()
            (subject / "value").write_text("candidate\n")
            (inputs / "intent").write_text("independent acceptance\n")
            draft = {"verdict": "PASS", "criteria": [{"id": "c", "result": "PASS", "evidence_refs": ["receipt"]}],
                     "findings": [], "evidence_refs": ["receipt"], "checked": ["value"], "not_checked": [], "validated_at": "2026-07-14T00:00:00Z"}
            (inputs / "draft.json").write_text(json.dumps(draft))
            env = dict(os.environ, PATH=str(empty_path))
            for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
                env.pop(key, None)

            def invoke(args, active_env):
                return subprocess.run([str(candidate), "provenance", *map(str, args)], cwd=subject, env=active_env, text=True, capture_output=True, timeout=30)

            manifest = invoke(["manifest", "--root", subject, "--include", "value"], env)
            self.assertEqual(manifest.returncode, 0, manifest.stderr)
            (inputs / "manifest.json").write_text(manifest.stdout)

            def fingerprint(root):
                result = {}
                for p in [root, *root.rglob("*")]:
                    mode = p.lstat().st_mode
                    content = os.readlink(p) if p.is_symlink() else p.read_bytes() if p.is_file() else None
                    result[str(p.relative_to(root))] = (mode, content)
                return result

            checked = 0
            for kind in ("objects-env", "split-common-env", "commondir-pointer", "common-markers", "declared", "missing-binding", "missing-exclusion"):
                area = base / kind
                area.mkdir()
                pool = area / "pool"
                pool.mkdir()
                active = dict(env)
                flags = []
                if kind == "objects-env":
                    active["GIT_OBJECT_DIRECTORY"] = str(pool)
                elif kind in ("split-common-env", "commondir-pointer", "common-markers"):
                    (pool / "objects").mkdir()
                    (pool / "refs").mkdir()
                    (pool / "config").write_text("[core]\nrepositoryformatversion = 0\n")
                    if kind != "common-markers":
                        admin = area / "admin"
                        admin.mkdir()
                        (admin / "HEAD").write_text("ref: refs/heads/main\n")
                        active["GIT_DIR"] = str(admin)
                        if kind == "split-common-env":
                            active["GIT_COMMON_DIR"] = str(pool)
                        else:
                            (admin / "commondir").write_text("../pool\n")
                elif kind == "declared":
                    flags = ["--exclude-git-root", pool]
                elif kind == "missing-binding":
                    active["GIT_OBJECT_DIRECTORY"] = str(area / "missing")
                else:
                    flags = ["--exclude-git-root", area / "missing"]
                (pool / "child").mkdir()
                alias = area / "alias"
                alias.symlink_to(pool, target_is_directory=True)
                for destination in (pool, pool / "child", alias, alias / "child"):
                    calls = [
                        ["snapshot-intent", "--source", inputs / "intent"],
                        ["manifest", "--root", subject, "--include", "value", "--out", "new/man.json"],
                        ["store-verdict", "--root", subject, "--subject-manifest", inputs / "manifest.json", "--draft", inputs / "draft.json",
                         "--intent-source", inputs / "intent", "--author-context-id", "author", "--validator-context-id", "judge",
                         "--freshness-source", "runtime", "--freshness-attester-id", "test", "--scope-result", "PASS"],
                    ]
                    for args in calls:
                        before = fingerprint(area)
                        completed = invoke([*args, "--evidence-root", destination, *flags], active)
                        self.assertNotEqual(completed.returncode, 0, (kind, args, completed.stdout))
                        expected_error = {"missing-binding": "resolve GIT_OBJECT_DIRECTORY", "missing-exclusion": "resolve --exclude-git-root"}.get(kind, "Git storage")
                        self.assertIn(expected_error, completed.stderr)
                        self.assertEqual(before, fingerprint(area), (kind, args, "mutated before rejection"))
                        checked += 1
            # A declared unrelated pool does not block a valid external root.
            external = base / "external"
            external.mkdir()
            completed = invoke(["snapshot-intent", "--source", inputs / "intent", "--evidence-root", external,
                                "--exclude-git-root", base / "declared" / "pool"], env)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            print(f"Git storage boundaries: {checked} installed no-write rejections; aliases/descendants; empty PATH; unrelated root admitted")

    def test_python_reference_identity_parity(self):
        candidate = Path(os.environ["AO_BIN"]).resolve(strict=True)
        spec = importlib.util.spec_from_file_location("evidence_reference", Path(__file__).with_name("validate.py"))
        reference = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reference)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "subject"
            root.mkdir()
            (root / "nested").mkdir()
            (root / "nested" / "value").write_text("canonical \u2028 separator\n")
            (root / "nested" / "value").chmod(0o700)
            (root / "nested" / "skip.log").write_text("excluded")
            (root / "link").symlink_to("nested/value")
            empty = base / "empty-path"
            empty.mkdir()
            env = dict(os.environ, PATH=str(empty))

            def run(*args):
                completed = subprocess.run([str(candidate), "provenance", *map(str, args), "--json"], cwd=root, env=env, text=True, capture_output=True, timeout=30)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                return json.loads(completed.stdout)

            expected = reference.build_manifest(root, ["."], ["**/*.log"], git_metadata={"commit": "descriptive"})
            actual = run("manifest", "--root", root, "--include", ".", "--exclude", "**/*.log", "--git-metadata-json", '{"commit":"descriptive"}')
            self.assertEqual(actual, expected)
            manifest_file = base / "base.json"
            manifest_file.write_text(json.dumps(actual))
            (root / "nested" / "value").unlink()
            expected_deletion = reference.build_manifest(root, ["."], ["**/*.log"], expected)
            actual_deletion = run("manifest", "--root", root, "--include", ".", "--exclude", "**/*.log", "--base-manifest", manifest_file)
            self.assertEqual(actual_deletion, expected_deletion)
            value_file = base / "value.json"
            # Preserve raw numeric spellings so both decoders canonicalize them.
            value_file.write_text('{"a":1e2,"b":1e-5,"c":1e16,"d":-0.0,"e":-0,"f":123456789012345678901234567890,"separator":"\u2028"}')
            actual_digest = run("digest", value_file)["digest"]
            self.assertEqual(actual_digest, reference.digest_value(json.loads(value_file.read_text())))
            print("Python/Go parity: manifest, symlink/executable bits, exclusions, deletions, metadata independence, numeric/Unicode canonical digest")

    def test_installed_evidence_without_python(self):
        candidate = Path(os.environ["AO_BIN"]).resolve(strict=True)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            consumer = base / "consumer"
            protected = base / "protected"
            empty_path = base / "empty-path"
            for directory in (consumer, protected, empty_path):
                directory.mkdir()
            # Synthetic Git fixture: the helper must leave files, index and
            # object bytes untouched. It never needs to invoke Git.
            (consumer / ".git" / "objects").mkdir(parents=True)
            (consumer / ".git" / "refs").mkdir()
            (consumer / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
            (consumer / ".git" / "index").write_bytes(b"synthetic index sentinel")
            (consumer / ".git" / "objects" / "sentinel").write_bytes(b"synthetic object sentinel")
            (consumer / "value").write_bytes(b"candidate\n")
            before = {str(p.relative_to(consumer)): p.read_bytes() for p in consumer.rglob("*") if p.is_file()}
            env = dict(os.environ, PATH=str(empty_path))
            commands = []

            def run(*args, ok=True):
                commands.append([str(candidate), "provenance", *map(str, args)])
                completed = subprocess.run(commands[-1], cwd=consumer, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(completed.returncode == 0, ok, completed.stderr)
                return json.loads(completed.stdout) if ok else completed.stderr

            manifest = run("manifest", "--root", consumer, "--include", "value", "--evidence-root", protected, "--out", "manifest.json", "--json")
            run("verify-manifest", "--root", consumer, "--manifest", protected / "manifest.json", "--json")
            draft = {
                "verdict": "PASS",
                "criteria": [{"id": "criterion", "result": "PASS", "evidence_refs": ["synthetic:receipt"]}],
                "findings": [], "evidence_refs": ["synthetic:receipt"],
                "checked": ["value"], "not_checked": [], "validated_at": "2026-07-14T00:00:00Z",
            }
            (protected / "draft.json").write_text(json.dumps(draft))
            verdicts = []
            for purpose in ("factual-support", "destination-disclosure"):
                intent = protected / (purpose + ".intent")
                payload = (purpose + ": independent immutable acceptance\n").encode()
                intent.write_bytes(payload)
                snap = run("snapshot-intent", "--source", intent, "--evidence-root", protected, "--json")
                self.assertEqual(snap["acceptance_digest"], hashlib.sha256(payload).hexdigest())
                self.assertEqual(Path(snap["intent_ref"]).read_bytes(), payload)
                args = ["store-verdict", "--root", consumer, "--evidence-root", protected,
                        "--draft", protected / "draft.json", "--subject-manifest", protected / "manifest.json",
                        "--intent-source", intent, "--author-context-id", "author", "--validator-context-id", "judge",
                        "--freshness-source", "runtime", "--freshness-attester-id", "test-runtime", "--scope-result", "PASS", "--json"]
                stored = run(*args)
                self.assertEqual(stored["verdict"], "PASS")
                self.assertTrue(run(*args)["idempotent"])
                run("verify-verdict", "--verdict", stored["path"], "--json")
                run("verify-subject", "--root", consumer, "--manifest", protected / "manifest.json", "--verdict", stored["path"], "--intent", intent, "--json")
                verdicts.append(stored)
            self.assertNotEqual(verdicts[0]["acceptance_digest"], verdicts[1]["acceptance_digest"])
            run("verify-subject", "--root", consumer, "--manifest", protected / "manifest.json", "--verdict", verdicts[0]["path"], "--intent", protected / "destination-disclosure.intent", ok=False)
            for destination in (consumer, consumer / "missing", base / "missing"):
                run("snapshot-intent", "--source", protected / "factual-support.intent", "--evidence-root", destination, ok=False)
            run("snapshot-intent", "--source", protected / "factual-support.intent", ok=False)
            run("snapshot-intent", "--source", protected / "factual-support.intent", "--evidence-root", protected, "--helper-version", "unsupported", ok=False)
            subject = consumer / "value"
            original_mode = subject.stat().st_mode & 0o777
            verify = ["verify-subject", "--root", consumer, "--manifest", protected / "manifest.json", "--verdict", verdicts[0]["path"], "--intent", protected / "factual-support.intent"]
            subject.chmod(original_mode ^ 0o100)
            run(*verify, ok=False)
            subject.chmod(original_mode)
            subject.write_bytes(b"changed bytes")
            run(*verify, ok=False)
            subject.unlink()
            subject.symlink_to(protected / "factual-support.intent")
            run(*verify, ok=False)
            subject.unlink()
            subject.write_bytes(before["value"])
            subject.chmod(original_mode)
            after = {str(p.relative_to(consumer)): p.read_bytes() for p in consumer.rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertFalse((consumer / ".agents").exists())
            self.assertFalse((base / "missing").exists())
            print(f"candidate evidence: {len(commands)} operations; empty PATH; external intent/manifest/verdict bytes; consumer/index/objects unchanged")


if __name__ == "__main__":
    unittest.main()
