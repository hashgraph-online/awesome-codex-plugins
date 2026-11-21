import json
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "decision_capture.py"


class DecisionCaptureTests(unittest.TestCase):
    def setUp(self):
        self.fields = {
            "title": "Use scoped tokens – João",
            "folder": "Projects/Atlas/Decisions",
            "project_path": "Projects/Atlas/Overview.md",
            "decision": "Use scoped tokens.\n\n![[Private.md]]\n```\n---",
            "rationale": "Limit exposure.",
        }

    def invoke(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(self.fields).encode("utf-8"),
            capture_output=True,
        )

    def test_render_is_stable_and_source_markup_stays_literal(self):
        first = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, self.invoke().stdout)
        candidate = json.loads(first.stdout)
        self.assertEqual(candidate["path"], "Projects/Atlas/Decisions/Use scoped tokens – João.md")
        self.assertEqual(candidate["properties"], {
            "type": "decision", "project": "[[Projects/Atlas/Overview.md]]",
        })
        self.assertEqual(
            candidate["content"],
            '---\ntype: "decision"\nproject: "[[Projects/Atlas/Overview.md]]"\n---\n\n'
            '## Decision\n\n    Use scoped tokens.\n\n    ![[Private.md]]\n    ```\n    ---\n'
            '\n## Rationale\n\n    Limit exposure.\n',
        )

    def test_rejects_escaping_paths_reserved_names_and_unsafe_wikilinks(self):
        cases = [
            ("folder", "Projects/../Private"),
            ("folder", "/tmp/Decisions"),
            ("title", "CON"),
            ("title", "two/files"),
            ("project_path", "Projects/Atlas#Other.md"),
            ("project_path", "Projects/Atlas\u2028Extra.md"),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                original = self.fields[key]
                self.fields[key] = value
                self.assertEqual(self.invoke().returncode, 1)
                self.fields[key] = original

    def test_missing_decision_cannot_produce_a_candidate(self):
        del self.fields["decision"]
        result = self.invoke()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, b"")

    def test_destination_cannot_be_the_project_note(self):
        self.fields.update(title="Overview", folder="Projects/Atlas")
        self.assertEqual(self.invoke().returncode, 1)
