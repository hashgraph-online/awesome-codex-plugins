from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).with_name("check-alphabetical.py")
SPEC = importlib.util.spec_from_file_location("check_alphabetical", MODULE_PATH)
assert SPEC and SPEC.loader
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


def sections(*items: str) -> list[tuple[str, list[str]]]:
    return [("Community Plugins", list(items))]


class BaselineAwareAlphabeticalTests(unittest.TestCase):
    def test_strict_mode_reports_every_inversion(self) -> None:
        new, all_inversions = CHECKER.new_inversion_counts(sections("beta", "alpha"))

        self.assertEqual(new, all_inversions)
        self.assertEqual(new[("Community Plugins", "beta", "alpha")], 1)

    def test_unchanged_baseline_inversion_is_allowed(self) -> None:
        baseline = sections("beta", "alpha")

        new, all_inversions = CHECKER.new_inversion_counts(baseline, baseline)

        self.assertFalse(new)
        self.assertEqual(all_inversions[("Community Plugins", "beta", "alpha")], 1)

    def test_new_inversion_still_fails_with_a_dirty_baseline(self) -> None:
        baseline = sections("beta", "alpha")
        head = sections("beta", "charlie", "alpha")

        new, _all_inversions = CHECKER.new_inversion_counts(head, baseline)

        self.assertEqual(new, Counter({("Community Plugins", "charlie", "alpha"): 1}))


if __name__ == "__main__":
    unittest.main()
