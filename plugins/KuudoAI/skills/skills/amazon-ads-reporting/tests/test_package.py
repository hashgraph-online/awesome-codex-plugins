import json
import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_ROOT.parents[1]
TEMPLATES = SKILL_ROOT / "assets" / "templates"
ACCOUNT_PLACEHOLDER = "amzn1.ads-account.g.REPLACE_ME"
PRODUCT_FILTERS = {
    "sp": "SPONSORED_PRODUCTS",
    "sb": "SPONSORED_BRANDS",
    "sd": "SPONSORED_DISPLAY",
}


def request_bodies(node):
    if isinstance(node, dict):
        if "accessRequestedAccounts" in node and "reports" in node:
            yield node
        else:
            for value in node.values():
                yield from request_bodies(value)


class TemplateContractTests(unittest.TestCase):
    def test_every_template_is_canonical_and_unfilled(self):
        files = sorted(TEMPLATES.rglob("*.json"))
        self.assertEqual(23, len(files))

        for path in files:
            document = json.loads(path.read_text())
            bodies = list(request_bodies(document))
            self.assertTrue(bodies, f"{path} has no CreateReport request")

            expected_product = PRODUCT_FILTERS[path.parent.name]
            for body in bodies:
                self.assertEqual(
                    {"accessRequestedAccounts", "reports"}, set(body), path
                )
                self.assertEqual(
                    ACCOUNT_PLACEHOLDER,
                    body["accessRequestedAccounts"][0]["advertiserAccountId"],
                    path,
                )
                self.assertEqual(1, len(body["reports"]), path)

                report = body["reports"][0]
                self.assertEqual({"format", "periods", "query"}, set(report), path)
                self.assertEqual("GZIP_JSON", report["format"], path)
                self.assertNotIn("timeRange", report["query"], path)
                self.assertNotIn("filters", report["query"], path)
                self.assertIn("date.value", report["query"]["fields"], path)

                period = report["periods"][0]["datePeriod"]
                self.assertRegex(period["startDate"], r"^(PRIOR_YEAR_)?START_DATE$")
                self.assertRegex(period["endDate"], r"^(PRIOR_YEAR_)?END_DATE$")

                predicate = report["query"]["filter"]["on"]
                self.assertEqual("adProduct.value", predicate["field"], path)
                self.assertEqual("EQUALS", predicate["comparisonOperator"], path)
                self.assertIs(False, predicate["not"], path)
                self.assertEqual([expected_product], predicate["values"], path)

    def test_catalog_resolves_every_template_and_reference(self):
        catalog = (SKILL_ROOT / "references" / "report-catalog.md").read_text()
        catalog_templates = set(
            re.findall(r"assets/templates/[a-z0-9_./-]+\.json", catalog)
        )
        disk_templates = {
            path.relative_to(SKILL_ROOT).as_posix()
            for path in TEMPLATES.rglob("*.json")
        }
        self.assertEqual(disk_templates, catalog_templates)

        catalog_references = set(
            re.findall(r"references/reports/[a-z0-9_./-]+\.md", catalog)
        )
        for reference in catalog_references:
            self.assertTrue((SKILL_ROOT / reference).is_file(), reference)
        self.assertEqual(18, len(catalog_references))
        self.assertEqual(1, catalog.count("**NOT REPRODUCIBLE**"))

        for reference in catalog_references:
            self.assertTrue((SKILL_ROOT / reference).read_text().startswith("# "), reference)

    def test_wrapper_bodies_match_the_pre_split_templates(self):
        pairs = [
            ("sp/campaign.json", "report_main_campaign", "sp/campaign__main.json"),
            (
                "sp/campaign.json",
                "report_prior_year_for_yoy",
                "sp/campaign__prior_year.json",
            ),
            (
                "sp/targeting.json",
                "report_1_main_targeting",
                "sp/targeting__main.json",
            ),
            (
                "sp/targeting.json",
                "report_2_top_of_search_impression_share",
                "sp/targeting__top_of_search.json",
            ),
            ("sb/keyword.json", "report_1_main_keyword", "sb/keyword__main.json"),
            (
                "sb/keyword.json",
                "report_2_top_of_search_impression_share",
                "sb/keyword__top_of_search.json",
            ),
        ]
        for wrapper_path, key, split_path in pairs:
            wrapper = json.loads((TEMPLATES / wrapper_path).read_text())
            split = json.loads((TEMPLATES / split_path).read_text())
            self.assertEqual(wrapper[key], split, split_path)


class PackagePolicyTests(unittest.TestCase):
    def test_portable_package_has_no_host_or_vendor_artifacts(self):
        self.assertFalse((SKILL_ROOT / ".claude-plugin").exists())
        self.assertFalse((SKILL_ROOT / "CHANGELOG.md").exists())
        self.assertFalse(list(SKILL_ROOT.rglob(".DS_Store")))

        package_text = "\n".join(
            path.read_text(errors="ignore")
            for path in SKILL_ROOT.rglob("*")
            if path.is_file() and path.suffix in {".md", ".json"}
        )
        for forbidden in (
            "Blackwood for Men",
            "OPENBRIDGE_REFRESH_TOKEN",
            "http://localhost:9080",
        ):
            self.assertNotIn(forbidden, package_text)

    def test_repository_governance_records_exist(self):
        entry_path = REPO_ROOT / "catalog" / "entries" / "amazon-ads-reporting.json"
        triggers_path = (
            REPO_ROOT / "evals" / "amazon-ads-reporting" / "trigger-cases.json"
        )
        self.assertTrue(entry_path.is_file())
        self.assertTrue(triggers_path.is_file())

        entry = json.loads(entry_path.read_text())
        self.assertEqual("amazon-ads-reporting", entry["name"])
        self.assertEqual("certified", entry["classification"])
        self.assertEqual("first-party", entry["origin"])

        triggers = json.loads(triggers_path.read_text())
        positives = [case for case in triggers if case["should_trigger"]]
        negatives = [case for case in triggers if not case["should_trigger"]]
        self.assertGreaterEqual(len(positives), 5)
        self.assertGreaterEqual(len(negatives), 5)


if __name__ == "__main__":
    unittest.main()
