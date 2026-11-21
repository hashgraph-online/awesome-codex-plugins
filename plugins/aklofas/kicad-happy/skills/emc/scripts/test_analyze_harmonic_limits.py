#!/usr/bin/env python3
"""Unit tests for the standalone harmonic-limit screening CLI."""

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import analyze_harmonic_limits as harmonic  # noqa: E402


VALID_SPECTRUM = {
    "schema_version": "harmonic-lines/1",
    "level_unit": "dbuv",
    "source": {
        "kind": "simulation",
        "description": "synthetic spectral lines",
    },
    "points": [
        {"frequency_hz": 2_000_000, "level": 31.5},
        {"frequency_hz": 1_000_000, "level": 42.0},
    ],
}

VALID_PROFILE = {
    "schema_version": "emc-limit-profile/1",
    "profile_id": "synthetic-user-profile",
    "limit_unit": "dbuv",
    "source": {
        "kind": "user_supplied",
        "citation": "Synthetic example — not a regulatory source",
    },
    "bands": [
        {
            "name": "synthetic-band",
            "start_hz": 500_000,
            "stop_hz": 1_800_000,
            "limits": {
                "peak": 50.0,
                "quasi_peak": 40.0,
                "average": 30.0,
            },
        }
    ],
}


class TestHarmonicLimitCliSurface(unittest.TestCase):
    """Exercise the standalone tool through its user-facing entry point."""

    def test_help_identifies_both_input_schemas_and_limit_columns(self):
        script = SCRIPT_DIR / "analyze_harmonic_limits.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("harmonic-lines/1", result.stdout)
        self.assertIn("emc-limit-profile/1", result.stdout)
        self.assertIn("--limit-column {peak,quasi_peak,average}", result.stdout)
        self.assertIn("--design-margin-db", result.stdout)
        self.assertIn("--output", result.stdout)


class TestSpectrumValidation(unittest.TestCase):
    """Reject ambiguous spectrum data and normalize point order."""

    def _validate(self, data):
        return harmonic.validate_spectrum(data)

    def test_points_are_sorted_by_frequency(self):
        normalized = self._validate(copy.deepcopy(VALID_SPECTRUM))
        self.assertEqual(
            [point["frequency_hz"] for point in normalized["points"]],
            [1_000_000.0, 2_000_000.0],
        )

    def test_empty_point_list_is_valid(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["points"] = []
        self.assertEqual(self._validate(data)["points"], [])

    def test_duplicate_numeric_frequencies_are_rejected(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["points"] = [
            {"frequency_hz": 1, "level": 2},
            {"frequency_hz": 1.0, "level": 3},
        ]
        with self.assertRaisesRegex(
            harmonic.ValidationError,
            "duplicate frequency_hz 1.0",
        ):
            self._validate(data)

    def test_invalid_spectrum_metadata_is_rejected(self):
        cases = (
            ("schema_version", "harmonic-lines/2", "schema_version"),
            ("level_unit", "dbuv_peak", "level_unit"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field):
                data = copy.deepcopy(VALID_SPECTRUM)
                data[field] = value
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    expected,
                ):
                    self._validate(data)

    def test_nonpositive_and_nonfinite_frequencies_are_rejected(self):
        for value in (0, -1, math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                data = copy.deepcopy(VALID_SPECTRUM)
                data["points"][0]["frequency_hz"] = value
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    "frequency_hz",
                ):
                    self._validate(data)

    def test_nonfinite_levels_and_boolean_numbers_are_rejected(self):
        for value in (math.nan, math.inf, -math.inf, True):
            with self.subTest(value=value):
                data = copy.deepcopy(VALID_SPECTRUM)
                data["points"][0]["level"] = value
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    "level",
                ):
                    self._validate(data)

    def test_integer_too_large_for_float_is_a_validation_error(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["points"][0]["frequency_hz"] = 10**400
        with self.assertRaisesRegex(
            harmonic.ValidationError, "frequency_hz"
        ):
            self._validate(data)

    def test_source_must_be_an_object_when_present(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["source"] = "simulation"
        with self.assertRaisesRegex(
            harmonic.ValidationError, "spectrum.source"
        ):
            self._validate(data)


class TestLimitProfileValidation(unittest.TestCase):
    """Require provenance and unambiguous detector bands."""

    def _validate(self, data):
        return harmonic.validate_limit_profile(data)

    def test_valid_profile_preserves_required_provenance(self):
        normalized = self._validate(copy.deepcopy(VALID_PROFILE))
        self.assertEqual(normalized["profile_id"], "synthetic-user-profile")
        self.assertEqual(normalized["source"], VALID_PROFILE["source"])

    def test_extra_source_fields_are_preserved(self):
        data = copy.deepcopy(VALID_PROFILE)
        data["source"]["url"] = "https://example.invalid/profile"
        data["source"]["edition"] = "synthetic-1"
        normalized = self._validate(data)
        self.assertEqual(normalized["source"], data["source"])

    def test_profile_requires_at_least_one_band(self):
        data = copy.deepcopy(VALID_PROFILE)
        data["bands"] = []
        with self.assertRaisesRegex(
            harmonic.ValidationError, "profile.bands must contain"
        ):
            self._validate(data)

    def test_required_profile_strings_are_enforced(self):
        mutations = (
            (("schema_version",), "emc-limit-profile/2", "schema_version"),
            (("profile_id",), "", "profile_id"),
            (("limit_unit",), "dbuv_rms", "limit_unit"),
            (("source", "kind"), "", "source.kind"),
            (("source", "citation"), "", "source.citation"),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path):
                data = copy.deepcopy(VALID_PROFILE)
                target = data
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    expected,
                ):
                    self._validate(data)

    def test_duplicate_band_names_are_rejected(self):
        data = copy.deepcopy(VALID_PROFILE)
        data["bands"].append(copy.deepcopy(data["bands"][0]))
        with self.assertRaisesRegex(
            harmonic.ValidationError,
            "duplicate band name",
        ):
            self._validate(data)

    def test_invalid_ranges_are_rejected(self):
        for start, stop in ((0, 1), (-1, 1), (2, 1)):
            with self.subTest(start=start, stop=stop):
                data = copy.deepcopy(VALID_PROFILE)
                data["bands"][0]["start_hz"] = start
                data["bands"][0]["stop_hz"] = stop
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    "start_hz",
                ):
                    self._validate(data)

    def test_detector_names_are_closed_and_one_is_required(self):
        cases = (
            ({}, "at least one"),
            ({"rms": 10}, "unsupported detector"),
        )
        for limits, expected in cases:
            with self.subTest(limits=limits):
                data = copy.deepcopy(VALID_PROFILE)
                data["bands"][0]["limits"] = limits
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    expected,
                ):
                    self._validate(data)

    def test_sloped_limit_shape_is_validated(self):
        cases = (
            ({"start": 70}, "exactly 'start' and 'stop'"),
            ({"start": 70, "stop": 60, "mid": 60}, "exactly"),
            ({"start": math.nan, "stop": 60}, r"limits\.peak\.start"),
            ({"start": 70, "stop": True}, r"limits\.peak\.stop"),
        )
        for limit, expected in cases:
            with self.subTest(limit=limit):
                data = copy.deepcopy(VALID_PROFILE)
                data["bands"][0]["limits"]["peak"] = limit
                with self.assertRaisesRegex(
                    harmonic.ValidationError, expected
                ):
                    self._validate(data)

    def test_sloped_limit_on_single_frequency_band_must_be_flat(self):
        data = copy.deepcopy(VALID_PROFILE)
        data["bands"][0].update(start_hz=100, stop_hz=100)
        data["bands"][0]["limits"]["peak"] = {"start": 50, "stop": 40}
        with self.assertRaisesRegex(
            harmonic.ValidationError, "must equal"
        ):
            self._validate(data)
        data["bands"][0]["limits"]["peak"] = {"start": 50, "stop": 50}
        self.assertEqual(
            self._validate(data)["bands"][0]["limits"]["peak"],
            {"start": 50.0, "stop": 50.0},
        )

    def test_nonfinite_limit_is_rejected(self):
        for value in (math.nan, math.inf, -math.inf, False):
            with self.subTest(value=value):
                data = copy.deepcopy(VALID_PROFILE)
                data["bands"][0]["limits"]["peak"] = value
                with self.assertRaisesRegex(
                    harmonic.ValidationError,
                    "limits.peak",
                ):
                    self._validate(data)


class TestScreenHarmonics(unittest.TestCase):
    """Check deterministic per-band comparison and screening semantics."""

    def _screen(
        self,
        spectrum=VALID_SPECTRUM,
        profile=VALID_PROFILE,
        limit_column="peak",
        margin=0.0,
    ):
        return harmonic.screen_harmonics(
            harmonic.validate_spectrum(copy.deepcopy(spectrum)),
            harmonic.validate_limit_profile(copy.deepcopy(profile)),
            limit_column,
            margin,
        )

    def test_boundaries_are_inclusive_and_highest_level_wins(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 100, "level": 20},
            {"frequency_hz": 150, "level": 35},
            {"frequency_hz": 200, "level": 30},
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "inclusive",
                "start_hz": 100,
                "stop_hz": 200,
                "limits": {"peak": 40},
            }
        ]

        band = self._screen(spectrum, profile)["bands"][0]
        self.assertEqual(band["worst_frequency_hz"], 150.0)
        self.assertEqual(band["level"], 35.0)
        self.assertEqual(band["margin_db"], 5.0)

    def test_equal_levels_choose_lowest_frequency_deterministically(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 200, "level": 35},
            {"frequency_hz": 100, "level": 35},
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"][0].update(start_hz=100, stop_hz=200)

        band = self._screen(spectrum, profile)["bands"][0]
        self.assertEqual(band["worst_frequency_hz"], 100.0)

    def test_overlapping_bands_evaluate_same_point_independently(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 150, "level": 35}
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "first",
                "start_hz": 100,
                "stop_hz": 200,
                "limits": {"peak": 40},
            },
            {
                "name": "second",
                "start_hz": 150,
                "stop_hz": 250,
                "limits": {"peak": 30},
            },
        ]

        bands = self._screen(spectrum, profile)["bands"]
        self.assertEqual(
            [band["worst_frequency_hz"] for band in bands],
            [150.0, 150.0],
        )
        self.assertEqual(
            [band["status"] for band in bands],
            ["at_or_below_limit_screen", "above_limit_screen"],
        )

    def test_positive_zero_and_negative_margins_are_classified(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 100, "level": 40}
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "positive",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": 41},
            },
            {
                "name": "zero",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": 40},
            },
            {
                "name": "negative",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": 39},
            },
        ]

        bands = self._screen(spectrum, profile)["bands"]
        self.assertEqual(
            [band["margin_db"] for band in bands], [1.0, 0.0, -1.0]
        )
        self.assertEqual(
            [band["status"] for band in bands],
            [
                "at_or_below_limit_screen",
                "at_or_below_limit_screen",
                "above_limit_screen",
            ],
        )

    def test_design_margin_creates_near_limit_only_for_nonnegative_margin(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 100, "level": 40}
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "near",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": 42},
            },
            {
                "name": "above",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": 39},
            },
        ]

        bands = self._screen(spectrum, profile, margin=3.0)["bands"]
        self.assertEqual(
            [band["status"] for band in bands],
            ["near_limit", "above_limit_screen"],
        )

    def _one_band(self, level, limit, margin=0.0):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [{"frequency_hz": 100, "level": level}]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "single",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"peak": limit},
            }
        ]
        return self._screen(spectrum, profile, margin=margin)["bands"][0]

    def test_decimal_design_margin_threshold_is_not_float_noise(self):
        cases = (
            (30.3, 33.3, 3.0, 3.0, "at_or_below_limit_screen"),
            (30.4, 33.3, 3.0, 2.9, "near_limit"),
            (40.1, 40.3, 0.2, 0.2, "at_or_below_limit_screen"),
            (40.2, 40.3, 0.2, 0.1, "near_limit"),
        )
        for level, limit, design, expected, status in cases:
            with self.subTest(level=level, limit=limit):
                band = self._one_band(level, limit, design)
                self.assertEqual(band["margin_db"], expected)
                self.assertEqual(band["status"], status)

    def test_margin_that_rounds_to_zero_is_not_negative_zero(self):
        margin = self._one_band(5e-324, 0.0)["margin_db"]
        self.assertEqual(math.copysign(1.0, margin), 1.0)

    def test_margin_that_overflows_to_infinity_is_rejected(self):
        with self.assertRaisesRegex(
            harmonic.ValidationError, r"bands\[0\]\.margin_db"
        ):
            self._one_band(-1e308, 1e308)

    def _sloped(self, points):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = points
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "sloped",
                "start_hz": 150_000,
                "stop_hz": 500_000,
                "limits": {"peak": {"start": 70, "stop": 60}},
            }
        ]
        return self._screen(spectrum, profile)["bands"][0]

    def test_sloped_limit_interpolates_linearly_in_log_frequency(self):
        geometric_mean = math.sqrt(150_000 * 500_000)
        cases = ((150_000, 70.0), (geometric_mean, 65.0), (500_000, 60.0))
        for frequency, limit in cases:
            with self.subTest(frequency=frequency):
                band = self._sloped(
                    [{"frequency_hz": frequency, "level": 60}]
                )
                self.assertEqual(band["limit"], limit)
                self.assertEqual(band["margin_db"], round(limit - 60, 6))

    def test_sloped_limit_selects_smallest_margin_not_highest_level(self):
        band = self._sloped(
            [
                {"frequency_hz": 150_000, "level": 60},
                {"frequency_hz": 500_000, "level": 52},
            ]
        )
        self.assertEqual(band["worst_frequency_hz"], 500_000.0)
        self.assertEqual(band["level"], 52.0)
        self.assertEqual(band["limit"], 60.0)
        self.assertEqual(band["margin_db"], 8.0)

    def test_sloped_limit_tie_break_uses_the_rounded_margin(self):
        band = self._sloped(
            [
                {"frequency_hz": 150_000, "level": 70},
                {"frequency_hz": 500_000, "level": 60.0000001},
            ]
        )
        self.assertEqual(band["margin_db"], 0.0)
        self.assertEqual(band["worst_frequency_hz"], 150_000.0)

    def test_sloped_limit_keeps_exact_endpoints_on_a_narrow_band(self):
        stop_hz = 150_000.00000000003
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [{"frequency_hz": stop_hz, "level": 64}]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "narrow",
                "start_hz": 150_000,
                "stop_hz": stop_hz,
                "limits": {"peak": {"start": 70, "stop": 60}},
            }
        ]
        band = self._screen(spectrum, profile)["bands"][0]
        self.assertEqual(band["limit"], 60.0)
        self.assertEqual(band["status"], "above_limit_screen")

    def test_flat_limit_still_selects_highest_level(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 150_000, "level": 1e-15},
            {"frequency_hz": 500_000, "level": 2e-15},
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "flat",
                "start_hz": 150_000,
                "stop_hz": 500_000,
                "limits": {"peak": 60},
            }
        ]
        band = self._screen(spectrum, profile)["bands"][0]
        self.assertEqual(band["worst_frequency_hz"], 500_000.0)

    def test_sloped_limit_in_empty_band_reports_null_limit(self):
        band = self._sloped([{"frequency_hz": 1_000_000, "level": 60}])
        self.assertIsNone(band["limit"])
        self.assertEqual(band["status"], "not_assessed")

    def test_each_supported_detector_uses_its_own_limit(self):
        results = {
            detector: self._screen(limit_column=detector)["bands"][0][
                "limit"
            ]
            for detector in ("peak", "quasi_peak", "average")
        }
        self.assertEqual(
            results,
            {"peak": 50.0, "quasi_peak": 40.0, "average": 30.0},
        )

    def test_empty_spectrum_marks_every_band_not_assessed(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = []
        result = self._screen(spectrum=spectrum)
        self.assertTrue(result["bands"])
        self.assertTrue(
            all(
                band["status"] == "not_assessed"
                for band in result["bands"]
            )
        )

    def test_missing_detector_and_empty_band_are_not_assessed(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 100, "level": 40}
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "missing-detector",
                "start_hz": 100,
                "stop_hz": 100,
                "limits": {"average": 30},
            },
            {
                "name": "empty",
                "start_hz": 200,
                "stop_hz": 300,
                "limits": {"peak": 50},
            },
        ]

        missing, empty = self._screen(spectrum, profile)["bands"]
        self.assertEqual(
            missing,
            {
                "name": "missing-detector",
                "worst_frequency_hz": 100.0,
                "level": 40.0,
                "limit": None,
                "margin_db": None,
                "status": "not_assessed",
                "lines_above_limit": None,
                "lines_near_limit": None,
            },
        )
        self.assertEqual(
            empty,
            {
                "name": "empty",
                "worst_frequency_hz": None,
                "level": None,
                "limit": 50.0,
                "margin_db": None,
                "status": "not_assessed",
                "lines_above_limit": 0,
                "lines_near_limit": 0,
            },
        )

    def test_lines_above_and_near_limit_are_counted_per_band(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"] = [
            {"frequency_hz": 150_000, "level": 71},
            {"frequency_hz": 200_000, "level": 50},
            {"frequency_hz": 300_000, "level": 62},
            {"frequency_hz": 500_000, "level": 60},
        ]
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"] = [
            {
                "name": "sloped",
                "start_hz": 150_000,
                "stop_hz": 500_000,
                "limits": {"peak": {"start": 70, "stop": 60}},
            }
        ]
        band = self._screen(spectrum, profile, margin=3.0)["bands"][0]
        # Margins: -1 (above), ~17.6, ~2.2 (near), 0 (near).
        self.assertEqual(band["lines_above_limit"], 1)
        self.assertEqual(band["lines_near_limit"], 2)

    def test_matching_units_are_screened_and_echoed(self):
        for unit in ("dbuv", "dbuv_per_m", "dbua"):
            with self.subTest(unit=unit):
                spectrum = copy.deepcopy(VALID_SPECTRUM)
                spectrum["level_unit"] = unit
                profile = copy.deepcopy(VALID_PROFILE)
                profile["limit_unit"] = unit
                result = self._screen(spectrum, profile)
                self.assertEqual(result["level_unit"], unit)
                self.assertEqual(result["bands"][0]["margin_db"], 8.0)

    def test_mismatched_units_are_rejected(self):
        profile = copy.deepcopy(VALID_PROFILE)
        profile["limit_unit"] = "dbuv_per_m"
        with self.assertRaisesRegex(
            harmonic.ValidationError,
            "profile.limit_unit 'dbuv_per_m' does not match "
            "spectrum.level_unit 'dbuv'",
        ):
            self._screen(profile=profile)

    def test_provenance_of_both_inputs_is_echoed(self):
        result = self._screen()
        self.assertEqual(result["spectrum_source"], VALID_SPECTRUM["source"])
        self.assertEqual(
            result["profile"]["source"], VALID_PROFILE["source"]
        )

    def test_missing_spectrum_source_is_reported_as_null(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        del spectrum["source"]
        self.assertIsNone(self._screen(spectrum)["spectrum_source"])

    def test_output_carries_screening_boundary_and_never_uses_pass_fail(self):
        result = self._screen()
        self.assertEqual(
            result["schema_version"], "harmonic-limit-screen/1"
        )
        self.assertEqual(result["result_class"], "screening_only")
        self.assertEqual(result["limit_column"], "peak")
        self.assertNotIn("detector", result)
        self.assertEqual(
            result["claim_boundary"],
            "This comparison is not a compliance determination.",
        )
        statuses = {band["status"] for band in result["bands"]}
        self.assertFalse(statuses & {"pass", "fail"})

    def test_invalid_limit_column_and_design_margin_are_rejected(self):
        spectrum = harmonic.validate_spectrum(
            copy.deepcopy(VALID_SPECTRUM)
        )
        profile = harmonic.validate_limit_profile(
            copy.deepcopy(VALID_PROFILE)
        )
        with self.assertRaisesRegex(harmonic.ValidationError, "limit_column"):
            harmonic.screen_harmonics(spectrum, profile, "rms")
        for value in (-1, math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    harmonic.ValidationError, "design_margin_db"
                ):
                    harmonic.screen_harmonics(
                        spectrum, profile, "peak", value
                    )


class TestHarmonicLimitCli(unittest.TestCase):
    """Exercise deterministic JSON I/O and actionable CLI failures."""

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.root = Path(self.tempdir.name)
        self.spectrum_path = self.root / "spectrum.json"
        self.profile_path = self.root / "limits.json"
        self.spectrum_path.write_text(
            json.dumps(VALID_SPECTRUM), encoding="utf-8"
        )
        self.profile_path.write_text(
            json.dumps(VALID_PROFILE), encoding="utf-8"
        )

    def _run(self, extra=()):
        stdout = io.StringIO()
        stderr = io.StringIO()
        arguments = [
            "--spectrum",
            str(self.spectrum_path),
            "--limits",
            str(self.profile_path),
            "--limit-column",
            "peak",
            *extra,
        ]
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = harmonic.main(arguments)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_valid_input_produces_deterministic_stdout_json(self):
        first = self._run()
        second = self._run()

        self.assertEqual(first, second)
        self.assertEqual(first[0], 0)
        self.assertEqual(first[2], "")
        self.assertTrue(first[1], "successful CLI must emit JSON")
        self.assertEqual(
            json.loads(first[1])["result_class"], "screening_only"
        )

    def test_output_file_receives_json_and_stdout_stays_empty(self):
        output = self.root / "screen.json"
        code, stdout, stderr = self._run(
            (
                "--design-margin-db",
                "3",
                "--output",
                str(output),
            )
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")
        self.assertTrue(output.exists(), "successful CLI must write output")
        output_text = output.read_text(encoding="utf-8")
        parsed = json.loads(output_text)
        self.assertEqual(parsed["design_margin_db"], 3.0)
        self.assertTrue(output_text.endswith("\n"))

    def test_output_cannot_overwrite_either_input(self):
        for source in (self.spectrum_path, self.profile_path):
            with self.subTest(source=source.name):
                original = source.read_bytes()
                code, stdout, stderr = self._run(("--output", str(source)))
                after = source.read_bytes()
                source.write_bytes(original)
                self.assertEqual(code, 2)
                self.assertEqual(stdout, "")
                self.assertIn("would overwrite input", stderr)
                self.assertIn(str(source), stderr)
                self.assertEqual(after, original)

    def test_output_cannot_overwrite_input_through_a_hard_link(self):
        alias = self.root / "alias.json"
        alias.hardlink_to(self.spectrum_path)
        original = self.spectrum_path.read_bytes()
        code, stdout, stderr = self._run(("--output", str(alias)))
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("would overwrite input", stderr)
        self.assertEqual(self.spectrum_path.read_bytes(), original)

    def test_invalid_json_returns_actionable_error(self):
        self.spectrum_path.write_text("{invalid", encoding="utf-8")
        code, stdout, stderr = self._run()

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn(str(self.spectrum_path), stderr)
        self.assertIn("valid JSON", stderr)

    def test_validation_error_returns_nonzero_without_output(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["level_unit"] = "dbuv_peak"
        self.spectrum_path.write_text(json.dumps(data), encoding="utf-8")
        code, stdout, stderr = self._run()

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("level_unit", stderr)

    def test_missing_input_returns_actionable_error(self):
        self.spectrum_path.unlink()
        code, stdout, stderr = self._run()

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn(str(self.spectrum_path), stderr)

    def _assert_clean_failure(self, expected, *paths):
        code, stdout, stderr = self._run()
        self.assertEqual(code, 2, stderr)
        self.assertEqual(stdout, "")
        self.assertTrue(stderr.startswith("Error: "), stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertIn(expected, stderr)
        for path in paths:
            self.assertIn(str(path), stderr)

    def test_duplicate_json_keys_are_rejected_in_both_inputs(self):
        self.spectrum_path.write_text(
            '{"schema_version": "harmonic-lines/1",'
            ' "level_unit": "dbuv_peak", "level_unit": "dbuv",'
            ' "points": []}',
            encoding="utf-8",
        )
        self._assert_clean_failure(
            "duplicate key 'level_unit'", self.spectrum_path
        )

        self.spectrum_path.write_text(
            json.dumps(VALID_SPECTRUM), encoding="utf-8"
        )
        self.profile_path.write_text(
            '{"schema_version": "emc-limit-profile/1",'
            ' "profile_id": "a", "profile_id": "b"}',
            encoding="utf-8",
        )
        self._assert_clean_failure(
            "duplicate key 'profile_id'", self.profile_path
        )

    def test_nested_duplicate_json_keys_are_rejected(self):
        self.profile_path.write_text(
            '{"source": {"kind": "a", "kind": "b"}}', encoding="utf-8"
        )
        self._assert_clean_failure("duplicate key 'kind'")

    def test_undecodable_input_is_a_clean_error(self):
        payloads = {
            "invalid utf-8": b"\xff",
            "utf-16": json.dumps(VALID_SPECTRUM).encode("utf-16"),
        }
        for name, payload in payloads.items():
            with self.subTest(name=name):
                self.spectrum_path.write_bytes(payload)
                self._assert_clean_failure("UTF-8", self.spectrum_path)

    def test_input_larger_than_size_limit_is_rejected(self):
        size = max(
            self.spectrum_path.stat().st_size,
            self.profile_path.stat().st_size,
        )
        with mock.patch.object(harmonic, "MAX_INPUT_BYTES", size):
            code, _, stderr = self._run()
        self.assertEqual((code, stderr), (0, ""))

        self.spectrum_path.write_bytes(
            self.spectrum_path.read_bytes() + b" " * (size + 1)
        )
        with mock.patch.object(harmonic, "MAX_INPUT_BYTES", size):
            self._assert_clean_failure(
                f"exceeds the {size} byte size limit", self.spectrum_path
            )

    def test_json_error_positions_use_normalized_newlines(self):
        for newline in (b"\r\n", b"\r"):
            with self.subTest(newline=newline):
                self.spectrum_path.write_bytes(
                    b"{" + newline + b" invalid" + newline + b"}"
                )
                self._assert_clean_failure(
                    "line 2 column 2 (char 3)", self.spectrum_path
                )

    def test_utf8_byte_order_mark_is_accepted(self):
        self.spectrum_path.write_bytes(
            b"\xef\xbb\xbf" + json.dumps(VALID_SPECTRUM).encode("utf-8")
        )
        code, stdout, stderr = self._run()
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(
            json.loads(stdout)["schema_version"], "harmonic-limit-screen/1"
        )

    def test_deeply_nested_json_is_a_clean_error(self):
        self.spectrum_path.write_bytes(
            b'{"extra":' + b"[" * 20000 + b"0" + b"]" * 20000 + b"}"
        )
        self._assert_clean_failure("nested", self.spectrum_path)

    def test_integer_too_large_for_float_is_a_clean_error(self):
        data = copy.deepcopy(VALID_SPECTRUM)
        data["points"][0]["frequency_hz"] = 10**400
        self.spectrum_path.write_text(json.dumps(data), encoding="utf-8")
        self._assert_clean_failure("frequency_hz")

    def test_nonfinite_json_numbers_are_rejected_at_load(self):
        cases = (
            ("NaN", "non-finite number NaN"),
            ("Infinity", "non-finite number Infinity"),
            ("-Infinity", "non-finite number -Infinity"),
            ("1e400", "number 1e400 is not finite"),
        )
        for literal, expected in cases:
            with self.subTest(literal=literal):
                self.profile_path.write_text(
                    '{"source": {"extra": ' + literal + "}}",
                    encoding="utf-8",
                )
                self._assert_clean_failure(expected, self.profile_path)

    def test_nonfinite_values_never_reach_the_output(self):
        spectrum = copy.deepcopy(VALID_SPECTRUM)
        spectrum["points"][1]["level"] = -1e308
        profile = copy.deepcopy(VALID_PROFILE)
        profile["bands"][0]["limits"]["peak"] = 1e308
        self.spectrum_path.write_text(json.dumps(spectrum), encoding="utf-8")
        self.profile_path.write_text(json.dumps(profile), encoding="utf-8")
        self._assert_clean_failure("margin_db")

    def test_unwritable_output_names_the_path(self):
        output = self.root / "missing-directory" / "screen.json"
        code, stdout, stderr = self._run(("--output", str(output)))

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn(f"could not write {output}:", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_output_without_a_file_name_is_a_clean_error(self):
        code, stdout, stderr = self._run(("--output", "."))

        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("could not write .: not a file path", stderr)

    def test_output_is_replaced_atomically(self):
        output = self.root / "screen.json"
        output.write_text("previous result\n", encoding="utf-8")
        before = sorted(path.name for path in self.root.iterdir())

        with mock.patch.object(
            harmonic.os, "replace", side_effect=OSError("simulated")
        ):
            code, stdout, stderr = self._run(("--output", str(output)))

        self.assertEqual(code, 2)
        self.assertIn(f"could not write {output}: simulated", stderr)
        self.assertEqual(
            output.read_text(encoding="utf-8"), "previous result\n"
        )
        self.assertEqual(
            sorted(path.name for path in self.root.iterdir()), before
        )

        code, _, stderr = self._run(("--output", str(output)))
        self.assertEqual((code, stderr), (0, ""))
        self.assertEqual(
            json.loads(output.read_text(encoding="utf-8"))["result_class"],
            "screening_only",
        )
        self.assertEqual(
            sorted(path.name for path in self.root.iterdir()), before
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
