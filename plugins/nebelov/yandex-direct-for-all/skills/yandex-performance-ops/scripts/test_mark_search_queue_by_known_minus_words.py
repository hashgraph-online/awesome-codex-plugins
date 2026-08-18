from __future__ import annotations

import csv
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import mark_search_queue_by_known_minus_words as marker
import build_local_search_negatives_pack as candidates
import validate_direct_build_dossier as dossier
import validate_direct_copy_pack as copy_pack


class MarkerTests(unittest.TestCase):
    def test_candidate_contract_preserves_every_source_row(self) -> None:
        source = [{"query": "первый", "clicks": "1"}, {"query": "второй", "clicks": "0"}]
        output = candidates.candidate_rows(source, "search-query-report", "поисковые запросы")
        self.assertEqual(len(output), len(source))
        self.assertEqual([row["query"] for row in output], ["первый", "второй"])
        self.assertTrue(all(row["decision"] == "" for row in output))
        self.assertTrue(all(row["reviewer"] == "" for row in output))
        self.assertTrue(all(row["candidate_status"] == "pending_review" for row in output))
        self.assertEqual(json.loads(output[0]["evidence"]), source[0])

    def test_preserves_count_order_source_and_empty_manual_decision(self) -> None:
        rows = [
            {"row_id": "first", "query": "купить товар бесплатно", "campaign": "Поиск"},
            {"row_id": "second", "query": "бесплатная доставка товара", "campaign": "Поиск"},
            {"row_id": "third", "query": "скачать каталог", "campaign": "Поиск"},
        ]
        decisions = [
            {"minus_word": "бесплатно", "normalized": "бесплатно", "decision_sha256": "a" * 64},
            {"minus_word": "скачать", "normalized": "скачать", "decision_sha256": "b" * 64},
        ]
        marked = marker.mark_rows(rows, "query", decisions)
        self.assertEqual([row["row_id"] for row in marked], ["first", "second", "third"])
        self.assertEqual([row["query"] for row in marked], [row["query"] for row in rows])
        self.assertEqual(len(marked), len(rows))
        self.assertEqual(json.loads(marked[0]["matched_minus_words"]), ["бесплатно"])
        self.assertEqual(json.loads(marked[1]["matched_minus_words"]), [])
        self.assertEqual(json.loads(marked[2]["matched_decision_sha256"]), ["b" * 64])
        self.assertTrue(all(row["candidate_status"] == "pending_review" for row in marked))
        self.assertTrue(all(row["manual_decision"] == "" for row in marked))
        self.assertTrue(all(len(row["source_row_sha256"]) == 64 for row in marked))

    def test_cli_output_is_private_and_keeps_every_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "queue.tsv"
            source.write_text("row_id\tquery\n1\tпример запроса\n2\tещё запрос\n", encoding="utf-8")
            decisions = root / "decisions.json"
            decisions.write_text(json.dumps([{"minus_word": "пример", "decision_sha256": "c" * 64}]), encoding="utf-8")
            target = root / "private" / "marked.tsv"
            with mock.patch.object(os.sys, "argv", ["marker", "--input", str(source), "--known-decisions", str(decisions), "--output", str(target)]):
                self.assertEqual(marker.main(), 0)
            with target.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual([row["row_id"] for row in rows], ["1", "2"])
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(target.parent.stat().st_mode & 0o777, 0o700)

    def test_dossier_rejects_missing_sections_and_unstable_group_uid(self) -> None:
        errors: list[str] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing = root / "missing.json"
            dossier.require_nonempty(missing, "карта продукта", errors)
            architecture = root / "architecture.json"
            architecture.write_text(
                json.dumps({"campaigns": [{"groups": [{"group_uid": "short", "ads": [{}]}]}]}),
                encoding="utf-8",
            )
            counts = dossier.validate_architecture(architecture, errors)
        self.assertEqual(counts, {"campaigns": 1, "groups": 1, "ads": 1})
        self.assertTrue(any("карта продукта" in error for error in errors))
        self.assertTrue(any("group_uid" in error for error in errors))

    def test_copy_validation_rejects_latin_and_truncated_display_link(self) -> None:
        self.assertIn("display_link: must be Russian, not Latin", copy_pack.validate_display_link("service"))
        self.assertIn("display_link: looks truncated", copy_pack.validate_display_link("услуга-"))
        self.assertEqual(copy_pack.validate_display_link("основная-услуга"), [])


if __name__ == "__main__":
    unittest.main()
