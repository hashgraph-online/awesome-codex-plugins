#!/usr/bin/env python3
"""Unit tests for search_lcsc.py.

Tests parsing, normalization, table/detail formatting, CLI filtering,
sorting, and the wmsc enrichment/fallback logic. All tests use mocked
responses for fast, deterministic, offline execution. The mock payloads
mirror the live API shapes observed 2026-09-12: jlcsearch search hits
carry no ``extra`` block, category endpoints key their rows by category
name, and the wmsc detail comes back in ``search_lcsc_direct``'s
normalized form.

Run with:
    python3 skills/lcsc/scripts/test_search_lcsc.py
    python3 -m unittest skills/lcsc/scripts/test_search_lcsc.py
"""

import io
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add script directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import search_lcsc


# Live jlcsearch /api/search hit (full=true no longer adds an 'extra' block)
SEARCH_HIT = {
    "lcsc": 318884,
    "mfr": "TS-1187A-B-A-B",
    "package": "SMD-4P,5.1x5.1mm",
    "is_basic": True,
    "is_preferred": False,
    "description": "-30℃~+85℃ 1.5mm 1.6N 100,000 cycles 12V 50mA SMD-4P,5.1x5.1mm Tactile Switches ROHS",
    "stock": 1683297,
    "price": 0.0197,
}

# Live /resistors/list.json row: 'price1', 'in_stock', parametric columns,
# empty description, 'attributes' as a JSON string
CATEGORY_ROW = {
    "lcsc": 25804,
    "mfr": "0603WAF1002T5E",
    "description": "",
    "stock": 37165617,
    "price1": 0.000842857,
    "in_stock": True,
    "resistance": 10000,
    "tolerance_fraction": 0.01,
    "power_watts": 100,
    "package": "0603",
    "is_basic": True,
    "is_preferred": False,
    "attributes": json.dumps({"Resistance": "10kΩ", "Power(Watts)": "100mW", "Tolerance": "±1%"}),
}

# What fetch_datasheet_lcsc.search_lcsc_direct returns for C318884 (wmsc
# product/detail, normalized to the jlcsearch-compatible dict)
WMSC_DIRECT = {
    "mfr": "TS-1187A-B-A-B",
    "description": "Tactile Switch SPST 160gf 1.5mm 5.1mm x 5.1mm Surface Mount",
    "datasheet": "https://datasheet.lcsc.com/datasheet/pdf/56c8.pdf?productCode=C318884",
    "stock": 597040,
    "price": [
        {"ladder": 20, "productPrice": "0.0207", "usdPrice": 0.0207, "currencySymbol": "$"},
        {"ladder": 200, "productPrice": "0.0160", "usdPrice": 0.016, "currencySymbol": "$"},
    ],
    "lcsc": "318884",
    "extra": {
        "number": "C318884",
        "mpn": "TS-1187A-B-A-B",
        "description": "Tactile Switch SPST 160gf 1.5mm 5.1mm x 5.1mm Surface Mount",
        "manufacturer": {"name": "XKB Connection"},
        "datasheet": {"pdf": "https://datasheet.lcsc.com/datasheet/pdf/56c8.pdf?productCode=C318884"},
    },
}


def _mock_urlopen(payload: dict):
    """Build a urlopen replacement returning ``payload`` as JSON."""
    resp = MagicMock()
    resp.read.return_value = json.dumps(payload).encode("utf-8")
    resp.__enter__.return_value = resp
    return MagicMock(return_value=resp)


class TestSearchJlcsearch(unittest.TestCase):
    """Test response parsing for the general and category endpoints."""

    def test_general_search_reads_components(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"components": [SEARCH_HIT]})) as mock_open:
            comps = search_lcsc.search_jlcsearch("C318884")
        self.assertEqual(comps, [SEARCH_HIT])
        url = mock_open.call_args[0][0].full_url
        self.assertIn("/api/search?q=C318884", url)
        self.assertIn("full=true", url)

    def test_category_search_reads_category_key(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"resistors": [CATEGORY_ROW]})) as mock_open:
            comps = search_lcsc.search_jlcsearch("10k 0402", category="resistors")
        self.assertEqual(len(comps), 1)
        self.assertEqual(comps[0]["lcsc"], 25804)
        url = mock_open.call_args[0][0].full_url
        self.assertIn("/resistors/list.json?search=10k%200402", url)

    def test_category_search_no_list_value(self):
        with patch("urllib.request.urlopen", _mock_urlopen({"error": "not found"})):
            self.assertEqual(search_lcsc.search_jlcsearch("x", category="bogus"), [])


class TestNormalizeComponent(unittest.TestCase):
    """Test normalization of component dictionaries across API shapes."""

    def test_normalize_search_hit(self):
        item = search_lcsc.normalize_component(dict(SEARCH_HIT))
        self.assertEqual(item["lcsc_code"], "C318884")
        self.assertEqual(item["lcsc_id"], 318884)
        self.assertEqual(item["mpn"], "TS-1187A-B-A-B")
        self.assertEqual(item["manufacturer"], "")
        self.assertEqual(item["package"], "SMD-4P,5.1x5.1mm")
        self.assertTrue(item["is_basic"])
        self.assertEqual(item["stock"], 1683297)
        self.assertAlmostEqual(item["price_usd"], 0.0197, places=4)
        self.assertEqual(item["datasheet_url"], "")
        self.assertEqual(item["prices"], [])
        self.assertEqual(item["attributes"], {})

    def test_normalize_category_row(self):
        item = search_lcsc.normalize_component(dict(CATEGORY_ROW))
        self.assertEqual(item["lcsc_code"], "C25804")
        self.assertEqual(item["mpn"], "0603WAF1002T5E")
        self.assertEqual(item["package"], "0603")
        self.assertTrue(item["is_basic"])
        self.assertEqual(item["stock"], 37165617)
        self.assertAlmostEqual(item["price_usd"], 0.000842857, places=6)
        self.assertEqual(item["attributes"]["Resistance"], "10kΩ")
        # Empty description falls back to the parametric values
        self.assertEqual(item["description"], "10kΩ 100mW ±1%")

    def test_normalize_wmsc_direct(self):
        item = search_lcsc.normalize_component(json.loads(json.dumps(WMSC_DIRECT)))
        self.assertEqual(item["lcsc_code"], "C318884")
        self.assertEqual(item["lcsc_id"], 318884)
        self.assertEqual(item["manufacturer"], "XKB Connection")
        self.assertEqual(item["datasheet_url"], WMSC_DIRECT["datasheet"])
        self.assertEqual(item["stock"], 597040)
        self.assertEqual(item["prices"], [{"min_qty": 20, "price": 0.0207}, {"min_qty": 200, "price": 0.016}])
        self.assertAlmostEqual(item["price_usd"], 0.0207, places=4)
        self.assertFalse(item["is_basic"])
        self.assertEqual(item["package"], "-")


class TestEnrichFromWmsc(unittest.TestCase):
    """Test that the wmsc detail fills only the blanks in a jlcsearch hit."""

    @patch("search_lcsc.search_lcsc_direct")
    def test_enrich_fills_blanks_keeps_jlcsearch_figures(self, mock_direct):
        mock_direct.return_value = json.loads(json.dumps(WMSC_DIRECT))
        item = search_lcsc.normalize_component(dict(SEARCH_HIT))
        search_lcsc.enrich_from_wmsc(item)
        mock_direct.assert_called_once_with("C318884")
        self.assertEqual(item["manufacturer"], "XKB Connection")
        self.assertEqual(item["datasheet_url"], WMSC_DIRECT["datasheet"])
        self.assertEqual(len(item["prices"]), 2)
        # jlcsearch's (JLCPCB) stock, price, package and description win
        self.assertEqual(item["stock"], 1683297)
        self.assertAlmostEqual(item["price_usd"], 0.0197, places=4)
        self.assertEqual(item["package"], "SMD-4P,5.1x5.1mm")
        self.assertTrue(item["description"].startswith("-30℃"))

    @patch("search_lcsc.search_lcsc_direct")
    def test_enrich_skips_non_lcsc_code(self, mock_direct):
        item = search_lcsc.normalize_component({"lcsc": None, "mfr": "X"})
        search_lcsc.enrich_from_wmsc(item)
        mock_direct.assert_not_called()

    @patch("search_lcsc.search_lcsc_direct", return_value=None)
    def test_enrich_direct_failure_leaves_item(self, mock_direct):
        item = search_lcsc.normalize_component(dict(SEARCH_HIT))
        before = dict(item)
        search_lcsc.enrich_from_wmsc(item)
        self.assertEqual(item, before)


class TestFormatting(unittest.TestCase):
    """Test table and detailed card view formatting."""

    def setUp(self):
        self.sample_item = {
            "lcsc_code": "C17408",
            "lcsc_id": 17408,
            "mpn": "0805W8F1000T5E",
            "manufacturer": "UNI-ROYAL",
            "package": "0805",
            "description": "100 Ohm 1% 1/8W 0805 SMD Resistor",
            "is_basic": True,
            "stock": 2500000,
            "price_usd": 0.0034,
            "datasheet_url": "https://example.com/resistor.pdf",
            "attributes": {"Resistance": "100Ω", "Power": "125mW"},
            "prices": [{"min_qty": 100, "price": 0.0034}],
        }

    def test_format_table_empty(self):
        output = search_lcsc.format_table([])
        self.assertEqual(output, "No components found.")

    def test_format_table_populated(self):
        output = search_lcsc.format_table([self.sample_item])
        self.assertIn("LCSC #", output)
        self.assertIn("C17408", output)
        self.assertIn("0805W8F1000T5E", output)
        self.assertIn("Basic", output)
        self.assertIn("2,500,000", output)
        self.assertIn("$0.0034", output)

    def test_format_details(self):
        output = search_lcsc.format_details(self.sample_item)
        self.assertIn("LCSC Code:      C17408", output)
        self.assertIn("MPN:            0805W8F1000T5E", output)
        self.assertIn("Manufacturer:   UNI-ROYAL", output)
        self.assertIn("JLCPCB Type:    Basic", output)
        self.assertIn("Resistance: 100Ω", output)
        self.assertIn("https://example.com/resistor.pdf", output)
        self.assertIn("100+: $0.0034 USD", output)


class TestMainCli(unittest.TestCase):
    """Test command-line argument parsing and filtering."""

    def setUp(self):
        self.mock_raw_results = [
            {
                "lcsc": 17408,
                "mfr": "0805W8F1000T5E",
                "package": "0805",
                "is_basic": True,
                "is_preferred": False,
                "description": "100R 0805 Resistor",
                "stock": 2500000,
                "price": 0.0034
            },
            {
                "lcsc": 99999,
                "mfr": "EXT-RES-100R",
                "package": "1206",
                "is_basic": False,
                "is_preferred": False,
                "description": "100R 1206 Resistor Extended",
                "stock": 0,
                "price": 0.0500
            }
        ]

    def _run(self, argv):
        stdout = io.StringIO()
        with patch.object(sys, "argv", ["search_lcsc.py"] + argv), \
             patch("sys.stdout", stdout):
            with self.assertRaises(SystemExit) as cm:
                search_lcsc.main()
        return cm.exception.code, stdout.getvalue()

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_basic_filter(self, mock_search):
        mock_search.return_value = list(self.mock_raw_results)
        code, output = self._run(["100R", "--basic"])
        self.assertEqual(code, 0)
        self.assertIn("C17408", output)
        self.assertNotIn("C99999", output)

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_instock_filter(self, mock_search):
        mock_search.return_value = list(self.mock_raw_results)
        code, output = self._run(["100R", "--in-stock"])
        self.assertEqual(code, 0)
        self.assertIn("C17408", output)
        self.assertNotIn("C99999", output)

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_json_output(self, mock_search):
        mock_search.return_value = list(self.mock_raw_results)
        code, output = self._run(["100R", "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(output)
        self.assertEqual(parsed["query"], "100R")
        self.assertEqual(parsed["count"], 2)
        self.assertEqual(len(parsed["components"]), 2)
        self.assertEqual(parsed["components"][0]["lcsc_code"], "C17408")

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_sort_price(self, mock_search):
        mock_search.return_value = list(self.mock_raw_results)
        code, output = self._run(["100R", "--sort", "price", "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(output)
        prices = [c["price_usd"] for c in parsed["components"]]
        self.assertEqual(prices, sorted(prices))

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_no_results_exit_code(self, mock_search):
        mock_search.return_value = []
        code, _ = self._run(["nonexistent_part"])
        self.assertEqual(code, 1)

    @patch("search_lcsc.search_lcsc_direct")
    @patch("search_lcsc.search_jlcsearch")
    def test_cli_keyword_search_does_not_hit_wmsc(self, mock_search, mock_direct):
        mock_search.return_value = list(self.mock_raw_results)
        code, _ = self._run(["100R"])
        self.assertEqual(code, 0)
        mock_direct.assert_not_called()

    @patch("search_lcsc.search_lcsc_direct")
    @patch("search_lcsc.search_jlcsearch")
    def test_cli_lcsc_code_details_enriched(self, mock_search, mock_direct):
        mock_search.return_value = [dict(SEARCH_HIT)]
        mock_direct.return_value = json.loads(json.dumps(WMSC_DIRECT))
        code, output = self._run(["C318884", "--details"])
        self.assertEqual(code, 0)
        mock_direct.assert_called_once_with("C318884")
        self.assertIn("Manufacturer:   XKB Connection", output)
        self.assertIn("productCode=C318884", output)
        self.assertIn("20+: $0.0207 USD", output)
        self.assertIn("JLCPCB Type:    Basic", output)

    @patch("search_lcsc.search_lcsc_direct")
    @patch("search_lcsc.search_jlcsearch")
    def test_cli_lcsc_code_falls_back_to_wmsc(self, mock_search, mock_direct):
        mock_search.return_value = []
        mock_direct.return_value = json.loads(json.dumps(WMSC_DIRECT))
        code, output = self._run(["C318884", "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(output)
        self.assertEqual(parsed["count"], 1)
        self.assertEqual(parsed["components"][0]["lcsc_code"], "C318884")
        self.assertEqual(parsed["components"][0]["manufacturer"], "XKB Connection")
        self.assertEqual(parsed["components"][0]["stock"], 597040)

    @patch("search_lcsc.search_jlcsearch")
    def test_cli_category_search(self, mock_search):
        mock_search.return_value = [dict(CATEGORY_ROW)]
        code, output = self._run(["10k 0402", "--category", "resistors"])
        self.assertEqual(code, 0)
        mock_search.assert_called_once_with(query="10k 0402", limit=10, package="", category="resistors")
        self.assertIn("C25804", output)
        self.assertIn("0603WAF1002T5E", output)
        self.assertIn("37,165,617", output)
        self.assertIn("$0.0008", output)
        self.assertIn("10kΩ 100mW", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
