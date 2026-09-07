from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "run_once.py"
SPEC = importlib.util.spec_from_file_location("rpi_run_once", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

# The REAL Validate implementation, not a stand-in. The composed-contract test
# below drives RPI against this module's actual identity functions; that is the
# only shape that can catch a disagreement between the two skills, which is
# exactly the defect that hid here (both suites green over a broken contract
# because the fake Validate borrowed RPI's own digest function).
VALIDATE_PATH = Path(__file__).parents[2] / "validate" / "scripts" / "validate.py"
VALIDATE_SPEC = importlib.util.spec_from_file_location("ao_validate", VALIDATE_PATH)
assert VALIDATE_SPEC and VALIDATE_SPEC.loader
VALIDATE = importlib.util.module_from_spec(VALIDATE_SPEC)
VALIDATE_SPEC.loader.exec_module(VALIDATE)

# A literal, independently written digest. Fakes must never derive an expected
# identity by calling the code under test — that is how the original defect
# stayed invisible.
INTENT_DIGEST = "c" * 64


def continue_guard(intent):
    return {
        "decision": "CONTINUE",
        "reason": "The frozen outcome still requires implementation proof.",
        "frozen_outcome": str(intent),
        "parked_process_work": [],
        "remaining_proof": ["implementation", "fresh validation"],
        "stop_condition": "Stop after one fresh validation result.",
    }


class RunOnceTests(unittest.TestCase):
    def phases(self, verdict: str = "PASS"):
        calls: list[str] = []

        def plan(intent):
            calls.append("plan")
            return {
                "intent_ref": "bead:agentops-test",
                "intent": intent,
                "acceptance": ["works"],
                "acceptance_digest": INTENT_DIGEST,
            }

        def implement(_plan):
            calls.append("implement")
            return {"subject_manifest_digest": "a" * 64, "checks": ["focused"]}

        def validate(_plan, _candidate):
            calls.append("validate")
            return {
                "verdict": verdict,
                "acceptance_digest": INTENT_DIGEST,
                "subject_manifest_digest": "a" * 64,
                "author_context_id": "author-ctx",
                "validator_context_id": "validator-ctx",
                "freshness_attestation": {
                    "source": "runtime",
                    "attester_identity": "runtime:rpi-test",
                },
                "verdict_digest": "b" * 64,
                "verdict_ref": "/tmp/verdict.json",
                "checked": ["acceptance"],
                "not_checked": [],
            }

        return calls, plan, implement, validate

    def test_anti_ceremony_guard_runs_once_before_plan(self):
        calls, plan, implement, validate = self.phases()

        def anti_ceremony(intent):
            calls.append("anti-ceremony")
            return {
                "decision": "CONTINUE",
                "reason": "The frozen outcome still requires implementation proof.",
                "frozen_outcome": intent,
                "parked_process_work": [],
                "remaining_proof": ["implementation", "fresh validation"],
                "stop_condition": "Stop after one fresh validation result.",
            }

        result = MODULE.invoke_once(
            "intent",
            anti_ceremony,
            plan,
            implement,
            validate,
        )

        self.assertEqual(
            calls,
            ["anti-ceremony", "plan", "implement", "validate"],
        )
        self.assertEqual(result["status"], "PASS")

    def test_anti_ceremony_stop_dispatches_no_core_phase(self):
        calls: list[str] = []
        reason = "The proposed traversal would create only process artifacts."

        def anti_ceremony(_intent):
            calls.append("anti-ceremony")
            return {
                "decision": "STOP",
                "reason": reason,
                "frozen_outcome": "Ship the already-proved caller outcome",
                "parked_process_work": ["another plan", "another audit"],
                "remaining_proof": [],
                "stop_condition": "Stop before Plan.",
            }

        result = MODULE.invoke_once(
            "intent",
            anti_ceremony,
            lambda _intent: calls.append("plan"),
            lambda _plan: calls.append("implement"),
            lambda _plan, _candidate: calls.append("validate"),
        )

        self.assertEqual(calls, ["anti-ceremony"])
        self.assertEqual(result["status"], "NOT_PLANNED")
        self.assertEqual(
            result["checked"],
            [f"anti-ceremony guard: STOP — {reason}"],
        )
        self.assertEqual(result["not_checked"], ["plan", "implement", "validate"])

    def test_each_phase_runs_once_and_pass_reports(self):
        calls, plan, implement, validate = self.phases()
        result = MODULE.invoke_once("intent", continue_guard, plan, implement, validate)
        self.assertEqual(calls, ["plan", "implement", "validate"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["intent_ref"], "bead:agentops-test")
        self.assertEqual(result["acceptance_digest"], INTENT_DIGEST)
        self.assertNotIn("next_action", result)

    def test_fail_reports_and_stops_without_another_dispatch(self):
        calls, plan, implement, validate = self.phases("FAIL")
        result = MODULE.invoke_once("intent", continue_guard, plan, implement, validate)
        self.assertEqual(calls, ["plan", "implement", "validate"])
        self.assertEqual(result["status"], "FAIL")

    def test_fresh_validation_does_not_require_persisted_verdict(self):
        calls, plan, implement, validate = self.phases()

        def inline_result(resolved, subject):
            result = validate(resolved, subject)
            result.pop("verdict_digest")
            result.pop("verdict_ref")
            return result

        result = MODULE.invoke_once("intent", continue_guard, plan, implement, inline_result)

        self.assertEqual(calls, ["plan", "implement", "validate"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["subject_manifest_digest"], "a" * 64)
        self.assertIsNone(result["verdict_ref"])
        self.assertIsNone(result["verdict_digest"])

    def test_fresh_validation_requires_distinct_contexts_and_attestation(self):
        _calls, plan, implement, validate = self.phases()

        for field, value in (
            ("validator_context_id", "author-ctx"),
            ("freshness_attestation", None),
        ):
            with self.subTest(field=field):
                def invalid(resolved, subject, field=field, value=value):
                    result = validate(resolved, subject)
                    result[field] = value
                    return result

                with self.assertRaisesRegex(ValueError, "distinct context identities"):
                    MODULE.invoke_once("intent", continue_guard, plan, implement, invalid)

    def test_missing_plan_stops_before_implement(self):
        calls: list[str] = []
        result = MODULE.invoke_once(
            "intent",
            continue_guard,
            lambda _intent: None,
            lambda _plan: calls.append("implement"),
            lambda _plan, _candidate: calls.append("validate"),
        )
        self.assertEqual(calls, [])
        self.assertEqual(result["status"], "NOT_PLANNED")

    def test_missing_candidate_stops_before_validate(self):
        calls: list[str] = []
        result = MODULE.invoke_once(
            "intent",
            continue_guard,
            lambda _intent: {
                "intent_ref": "caller",
                "acceptance": ["works"],
                "acceptance_digest": INTENT_DIGEST,
            },
            lambda _plan: None,
            lambda _plan, _candidate: calls.append("validate"),
        )
        self.assertEqual(calls, [])
        self.assertEqual(result["status"], "NOT_BUILT")

    def test_validate_cannot_report_a_different_intent(self):
        calls, plan, implement, validate = self.phases()

        def mismatched(resolved, subject):
            result = validate(resolved, subject)
            result["acceptance_digest"] = "f" * 64
            return result

        with self.assertRaisesRegex(ValueError, "resolved intent digest"):
            MODULE.invoke_once("intent", continue_guard, plan, implement, mismatched)

    def test_plan_without_a_declared_digest_is_a_contract_error(self):
        _calls, _plan, implement, validate = self.phases()

        def undeclared(_intent):
            return {"intent_ref": "caller", "acceptance": ["works"]}

        with self.assertRaisesRegex(ValueError, "acceptance_digest"):
            MODULE.invoke_once("intent", continue_guard, undeclared, implement, validate)

    def test_plan_digest_must_be_a_sha256(self):
        _calls, _plan, implement, validate = self.phases()

        for bogus in ("", "not-a-digest", "C" * 64, "a" * 63, 12345):
            with self.subTest(digest=bogus):
                def undeclared(_intent, value=bogus):
                    return {
                        "intent_ref": "caller",
                        "acceptance": ["works"],
                        "acceptance_digest": value,
                    }

                with self.assertRaisesRegex(ValueError, "acceptance_digest"):
                    MODULE.invoke_once("intent", continue_guard, undeclared, implement, validate)


class ComposedIdentityContractTests(unittest.TestCase):
    """RPI against the REAL Validate identity functions.

    This is the test the defect needed. RPI used to digest a canonical-JSON
    re-serialization of the parsed intent mapping while Validate digested the raw
    intent bytes, and RPI hard-compared the two. Nothing caught it because RPI's
    own suite mocked Validate with RPI's digest function, so the mock agreed with
    the code under test by construction. Here the digest crosses the skill
    boundary in both directions with no shared helper.
    """

    # Deliberately NOT canonical JSON: real intent sources have indentation,
    # trailing newlines, and key order. A canonical-JSON digest of the parsed
    # mapping differs from sha256(these bytes), so this payload discriminates
    # between the two implementations instead of accidentally agreeing.
    INTENT_BYTES = b'{\n  "acceptance": ["works"],\n  "intent_ref": "bead:agentops-test"\n}\n'

    def test_rpi_carries_the_digest_validate_derives_from_the_snapshot_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            intent_dir = Path(tmp) / "intents"

            def plan(_intent):
                # Plan resolves the intent and snapshots the EXACT bytes through
                # Validate's own store, which is what defines the identity.
                path, _existed = VALIDATE.snapshot_intent(self.INTENT_BYTES, intent_dir)
                return {
                    "intent_ref": str(path),
                    "acceptance": ["works"],
                    "acceptance_digest": hashlib.sha256(self.INTENT_BYTES).hexdigest(),
                }

            def implement(_plan):
                return {"subject_manifest_digest": "a" * 64}

            def validate(resolved, _candidate):
                # Validate re-reads the snapshot from disk and re-derives the
                # digest through its own runtime-fact binder — no value is passed
                # through from Plan, so agreement is earned, not assumed.
                replayed = Path(resolved["intent_ref"]).read_bytes()
                bound = VALIDATE.bind_runtime_facts(
                    {"verdict": "PASS"},
                    replayed,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
                return {
                    "verdict": "PASS",
                    "acceptance_digest": bound["acceptance_digest"],
                    "subject_manifest_digest": "a" * 64,
                    "author_context_id": "author-ctx",
                    "validator_context_id": "validator-ctx",
                    "freshness_attestation": {
                        "source": "runtime",
                        "attester_identity": "runtime:composed-test",
                    },
                    "verdict_digest": "b" * 64,
                    "verdict_ref": str(Path(tmp) / "verdict.json"),
                    "checked": ["acceptance"],
                    "not_checked": [],
                }

            result = MODULE.invoke_once(
                self.INTENT_BYTES,
                continue_guard,
                plan,
                implement,
                validate,
            )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["acceptance_digest"],
            hashlib.sha256(self.INTENT_BYTES).hexdigest(),
        )

    def test_the_canonical_json_digest_is_not_the_intent_identity(self):
        """Pins the two digests apart so the defect cannot silently return.

        If someone reintroduces a canonical-JSON digest of the parsed mapping as
        the acceptance identity, this fails: the byte digest and the value digest
        are different numbers for the same intent.
        """
        import json

        byte_digest = hashlib.sha256(self.INTENT_BYTES).hexdigest()
        value_digest = VALIDATE.digest_value(json.loads(self.INTENT_BYTES))
        self.assertNotEqual(byte_digest, value_digest)

        # And the collision the byte digest forbids: two distinct sources that
        # parse to the same mapping must NOT share an acceptance identity.
        reordered = b'{"intent_ref": "bead:agentops-test", "acceptance": ["works"]}'
        self.assertEqual(json.loads(reordered), json.loads(self.INTENT_BYTES))
        self.assertNotEqual(byte_digest, hashlib.sha256(reordered).hexdigest())
        self.assertEqual(value_digest, VALIDATE.digest_value(json.loads(reordered)))


if __name__ == "__main__":
    unittest.main()
