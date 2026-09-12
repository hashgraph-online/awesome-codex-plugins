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

# The unchanged Validate reference oracle, not a stand-in. The composed-contract test
# below drives RPI against this module's actual identity functions; that is the
# only shape that can catch a disagreement between the two skills, which is
# exactly the defect that hid here (both suites green over a broken contract
# because the fake Validate borrowed RPI's own digest function).
VALIDATE_PATH = Path(__file__).parents[2] / "validate" / "tests" / "validate.py"
VALIDATE_SPEC = importlib.util.spec_from_file_location("ao_validate", VALIDATE_PATH)
assert VALIDATE_SPEC and VALIDATE_SPEC.loader
VALIDATE = importlib.util.module_from_spec(VALIDATE_SPEC)
VALIDATE_SPEC.loader.exec_module(VALIDATE)

# A literal, independently written digest. Fakes must never derive an expected
# identity by calling the code under test — that is how the original defect
# stayed invisible.
INTENT_DIGEST = "c" * 64


def validation_round(
    status,
    finding_ids,
    *,
    digest="a" * 64,
    evidence=("acceptance-receipt",),
    family="fresh",
    summaries=None,
    checked=("acceptance",),
    not_checked=(),
):
    """One validate leg's result, as the repair phase consumes it (pure data)."""
    summaries = summaries or {}
    return {
        "status": status,
        "findings": [
            {"id": fid, "summary": summaries.get(fid, f"finding {fid}")}
            for fid in finding_ids
        ],
        "subject_digest": digest,
        "evidence_refs": list(evidence),
        "validator_family": family,
        "checked": list(checked),
        "not_checked": list(not_checked),
    }


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

    def test_fail_from_one_experiment_feeds_the_repair_phase(self):
        """Replaces the old stop-on-FAIL test (ADR-0017).

        One experiment still dispatches Plan and Implement exactly once, and the
        FAIL it produces is no longer terminal by itself: it is the first round
        handed to the bounded repair phase, which owns the stop decision.
        """
        calls, plan, implement, validate = self.phases("FAIL")
        result = MODULE.invoke_once("intent", continue_guard, plan, implement, validate)
        self.assertEqual(calls, ["plan", "implement", "validate"])
        self.assertEqual(result["status"], "FAIL")

        outcome = MODULE.run_repair_phase(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64),
                validation_round("PASS", [], digest="d" * 64, evidence=(
                    {"ref": "fixed-f1", "subject_digest": "d" * 64, "resolves": ["f1"]},
                )),
            ],
            repair_rounds=2,
            intent_ref=result["intent_ref"],
            acceptance_digest=result["acceptance_digest"],
        )
        self.assertEqual(outcome["stop_reason"], "converged")
        self.assertEqual(outcome["report"]["status"], "PASS")
        self.assertEqual(outcome["rounds_used"], 1)

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


class RepairPhaseTests(unittest.TestCase):
    """The bounded repair phase and its convergence law (ADR-0017).

    RPI is no longer single-pass: a `FAIL` or `NOT_PROVEN` with findings may be
    repaired and re-validated while acceptance progress and the bound hold. The loop is
    modelled here as pure data — a sequence of already-produced validate rounds
    — so the stop semantics are executable without Git, `ao`, or a tracker.
    """

    def repair(self, rounds, **kwargs):
        kwargs.setdefault("intent_ref", "bead:agentops-test")
        kwargs.setdefault("acceptance_digest", INTENT_DIGEST)
        return MODULE.run_repair_phase(rounds, **kwargs)

    def test_repair_rounds_zero_with_findings_is_budget_exhausted(self):
        outcome = self.repair([validation_round("FAIL", ["f1"])], repair_rounds=0)
        self.assertEqual(outcome["stop_reason"], "repair_budget_exhausted")
        self.assertEqual(outcome["rounds_used"], 0)
        self.assertEqual(outcome["report"]["status"], "FAIL")

    def test_a_pass_over_unchanged_bytes_after_a_fail_is_a_flip_not_a_proof(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64),
                validation_round("PASS", [], digest="a" * 64),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")
        self.assertEqual(outcome["report"]["status"], "NOT_PROVEN")

    def test_new_evidence_must_resolve_a_prior_finding_to_admit_an_unchanged_digest(self):
        outcome = self.repair(
            [
                validation_round("NOT_PROVEN", ["gap"], digest="a" * 64),
                validation_round(
                    "NOT_PROVEN", ["gap"], digest="a" * 64,
                    evidence=({"ref": "receipt-2", "subject_digest": "a" * 64, "resolves": ["gap"]},),
                ),
            ]
        )
        # "resolves" claims gap, but gap is still open: nothing was resolved.
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")

    def test_a_bare_new_evidence_label_does_not_admit_an_unchanged_digest(self):
        outcome = self.repair(
            [
                validation_round("NOT_PROVEN", ["gap", "other"], digest="a" * 64),
                validation_round("NOT_PROVEN", ["other"], digest="a" * 64, evidence=("receipt-2",)),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")

    def test_evidence_bound_to_another_digest_does_not_admit(self):
        outcome = self.repair(
            [
                validation_round("NOT_PROVEN", ["gap", "other"], digest="a" * 64),
                validation_round(
                    "NOT_PROVEN", ["other"], digest="a" * 64,
                    evidence=({"ref": "receipt-2", "subject_digest": "b" * 64, "resolves": ["gap"]},),
                ),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")

    def test_missing_findings_or_evidence_keys_are_rejected(self):
        for key in ("findings", "evidence_refs"):
            with self.subTest(missing=key):
                bad = validation_round("PASS", [])
                del bad[key]
                with self.assertRaisesRegex(ValueError, key):
                    self.repair([bad])
        bad = validation_round("PASS", [])
        bad["checked"] = "acceptance"
        with self.assertRaisesRegex(ValueError, "checked must be a list"):
            self.repair([bad])

    def test_scalar_evidence_refs_are_rejected(self):
        bad = validation_round("FAIL", ["f1"])
        bad["evidence_refs"] = "receipt-1"
        with self.assertRaisesRegex(ValueError, "evidence_refs must be a list"):
            self.repair([bad])

    def test_new_evidence_does_not_admit_a_current_fail_over_unchanged_bytes(self):
        outcome = self.repair(
            [
                validation_round("NOT_PROVEN", ["gap", "bug"], digest="a" * 64),
                validation_round("FAIL", ["bug"], digest="a" * 64, evidence=("receipt-2",)),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")
        self.assertEqual(outcome["report"]["status"], "FAIL")

    def test_malformed_rounds_are_rejected_not_swallowed(self):
        cases = {
            "pass with findings": validation_round("PASS", ["f1"]),
            "fail without findings": validation_round("FAIL", []),
            "missing digest": validation_round("FAIL", ["f1"], digest=None),
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                with self.assertRaises(ValueError):
                    self.repair([bad])
        duplicate = validation_round("FAIL", ["f1"])
        duplicate["findings"].append({"id": "f1", "summary": "again"})
        with self.assertRaisesRegex(ValueError, "twice"):
            self.repair([duplicate])

    def test_rounds_past_the_bound_are_never_normalized(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1", "f2"], digest="a" * 64),
                validation_round("FAIL", ["f1"], digest="b" * 64, evidence=(
                    {"ref": "fixed-f2", "subject_digest": "b" * 64, "resolves": ["f2"]},
                )),
                {"status": "garbage-that-would-raise"},
            ],
            repair_rounds=1,
        )
        self.assertEqual(outcome["stop_reason"], "repair_budget_exhausted")

    def test_a_first_round_pass_converges_without_spending_a_repair_round(self):
        outcome = self.repair([validation_round("PASS", [])])
        self.assertEqual(outcome["stop_reason"], "converged")
        self.assertEqual(outcome["report"]["status"], "PASS")
        self.assertEqual(outcome["rounds_used"], 0)
        self.assertEqual(outcome["open_findings"], [])
        self.assertEqual(
            outcome["report"]["checked"][0], "repair round 0: 0 open findings"
        )

    def test_repair_stops_at_the_declared_repair_rounds_budget(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1", "f2"], digest="a" * 64),
                validation_round("FAIL", ["f1"], digest="b" * 64, evidence=(
                    {"ref": "fixed-f2", "subject_digest": "b" * 64, "resolves": ["f2"]},
                )),
                validation_round("FAIL", ["f1"], digest="c" * 64),
            ],
            repair_rounds=1,
        )
        self.assertEqual(outcome["stop_reason"], "repair_budget_exhausted")
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(outcome["report"]["status"], "FAIL")
        self.assertEqual(
            outcome["report"]["checked"][:2],
            ["repair round 0: 2 open findings", "repair round 1: 1 open findings"],
        )

    def test_new_finding_with_unknown_cause_requires_causal_review(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64),
                validation_round("FAIL", ["f1", "f2"], digest="b" * 64),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "new_finding_requires_causal_review")
        self.assertEqual(outcome["report"]["status"], "FAIL")
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(
            sorted(f["id"] for f in outcome["open_findings"]), ["f1", "f2"]
        )

    def test_repair_stops_when_a_closed_finding_reopens(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1", "f2"], digest="a" * 64),
                validation_round("FAIL", ["f1"], digest="b" * 64, evidence=(
                    {"ref": "fixed-f2", "subject_digest": "b" * 64, "resolves": ["f2"]},
                )),
                validation_round("FAIL", ["f2"], digest="c" * 64),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "reopened_finding")
        self.assertEqual(outcome["rounds_used"], 2)
        self.assertEqual(outcome["report"]["status"], "FAIL")

    def test_digest_and_count_movement_without_bound_proof_are_not_progress(self):
        for remaining in (["f1", "f2"], ["f1"], []):
            with self.subTest(remaining=remaining):
                outcome = self.repair([
                    validation_round("FAIL", ["f1", "f2"], digest="a" * 64),
                    validation_round("FAIL" if remaining else "PASS", remaining,
                                     digest="b" * 64, evidence=("another-check-label",)),
                ])
                self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")
                self.assertNotEqual(outcome["report"]["status"], "PASS")

    def test_discovered_preexisting_defects_may_grow_count_with_real_progress(self):
        outcome = self.repair([
            validation_round("FAIL", ["fixed"], digest="a" * 64),
            validation_round("FAIL", ["discovered-1", "discovered-2"], digest="b" * 64,
                             evidence=(
                {"ref": "fixed-check", "subject_digest": "b" * 64, "resolves": ["fixed"]},
                {"ref": "reproduced-on-prior", "subject_digest": "a" * 64,
                 "preexisting": ["discovered-1", "discovered-2"]},
            )),
        ])
        self.assertEqual(outcome["stop_reason"], "not_converged")
        self.assertEqual(outcome["report"]["status"], "FAIL")
        self.assertEqual(len(outcome["open_findings"]), 2)
        self.assertEqual(outcome["rounds_used"], 1)

    def test_new_finding_cannot_hide_behind_another_resolved_gap(self):
        for proof in ((), ({"ref": "wrong-baseline", "subject_digest": "c" * 64,
                           "preexisting": ["new"]},)):
            with self.subTest(proof=proof):
                outcome = self.repair([
                    validation_round("FAIL", ["fixed"], digest="a" * 64),
                    validation_round("FAIL", ["new"], digest="b" * 64, evidence=(
                        {"ref": "fixed-check", "subject_digest": "b" * 64, "resolves": ["fixed"]},
                    ) + proof),
                ])
                self.assertEqual(outcome["stop_reason"], "new_finding_requires_causal_review")

    def test_introduced_regression_stops_even_if_another_gap_closed(self):
        outcome = self.repair([
            validation_round("FAIL", ["fixed"], digest="a" * 64),
            validation_round("FAIL", ["regression"], digest="b" * 64, evidence=(
                {"ref": "fixed-check", "subject_digest": "b" * 64, "resolves": ["fixed"]},
                {"ref": "before-after-check", "subject_digest": "b" * 64,
                 "introduced": ["regression"]},
            )),
        ])
        self.assertEqual(outcome["stop_reason"], "introduced_regression")
        self.assertEqual(outcome["report"]["status"], "FAIL")

    def test_recurring_class_requires_causal_review_without_design_diagnosis(self):
        first = validation_round("FAIL", ["f1", "f2"], digest="a" * 64)
        first["findings"][0]["class"] = "deadline-bypass"
        recurrence = validation_round("FAIL", ["new-id"], digest="c" * 64)
        recurrence["findings"][0]["class"] = "deadline-bypass"
        outcome = self.repair([
            first,
            validation_round("FAIL", ["f2"], digest="b" * 64, evidence=(
                {"ref": "fixed-f1", "subject_digest": "b" * 64, "resolves": ["f1"]},
            )),
            recurrence,
        ])
        self.assertEqual(outcome["stop_reason"], "recurring_finding_class")
        self.assertEqual(outcome["rounds_used"], 2)
        self.assertNotIn("design", str(outcome))

    def test_old_receipt_does_not_prove_new_acceptance_progress(self):
        receipt = {"ref": "old-check", "subject_digest": "b" * 64, "resolves": ["f2"]}
        outcome = self.repair([
            validation_round("FAIL", ["f1", "f2"], digest="a" * 64, evidence=(receipt,)),
            validation_round("FAIL", ["f1"], digest="b" * 64, evidence=(receipt,)),
        ])
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")

    def test_peer_leg_cannot_silently_override_a_receipts_causal_binding(self):
        with self.assertRaisesRegex(ValueError, "conflicting bindings"):
            self.repair([[
                validation_round("FAIL", ["f1"], evidence=(
                    {"ref": "comparison", "subject_digest": "a" * 64, "preexisting": ["f1"]},
                )),
                validation_round("FAIL", ["f1"], family="other", evidence=(
                    {"ref": "comparison", "subject_digest": "a" * 64, "introduced": ["f1"]},
                )),
            ]])

    def test_peer_leg_cannot_silently_replace_a_recurrence_class(self):
        first = validation_round("FAIL", ["f1"])
        first["findings"][0]["class"] = "deadline-bypass"
        peer = validation_round("FAIL", ["f1"], family="other")
        self.assertEqual(MODULE.normalize_round([first, peer])["open_findings"][0]["class"],
                         "deadline-bypass")
        peer["findings"][0]["class"] = "cosmetic"
        with self.assertRaisesRegex(ValueError, "conflicting classes"):
            self.repair([[first, peer]])

    def test_pass_cannot_converge_with_unverified_acceptance_or_missing_proof(self):
        cases = (
            validation_round("PASS", [], not_checked=("required-cancellation-case",)),
            validation_round("PASS", [], checked=()),
            validation_round("PASS", [], evidence=()),
        )
        for raw in cases:
            with self.subTest(raw=raw):
                for round_value in (raw, [raw, validation_round("PASS", [], family="other")]):
                    outcome = self.repair([round_value])
                    self.assertEqual(outcome["report"]["status"], "NOT_PROVEN")
                    self.assertNotEqual(outcome["stop_reason"], "converged")
                    self.assertEqual(outcome["report"]["not_checked"], raw["not_checked"])

    def test_repair_stops_when_the_digest_is_unchanged_and_no_new_evidence(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64, evidence=["r1"]),
                validation_round("FAIL", ["f1"], digest="a" * 64, evidence=["r1"]),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")
        self.assertEqual(outcome["rounds_used"], 1)

    def test_not_proven_is_resolved_by_new_evidence_with_an_unchanged_digest(self):
        outcome = self.repair(
            [
                validation_round(
                    "NOT_PROVEN", ["gap1"], digest="a" * 64, evidence=["r1"]
                ),
                validation_round(
                    "PASS", [], digest="a" * 64,
                    evidence=["r1", {"ref": "r2", "subject_digest": "a" * 64, "resolves": ["gap1"]}],
                ),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "converged")
        self.assertEqual(outcome["report"]["status"], "PASS")
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(outcome["report"]["subject_manifest_digest"], "a" * 64)

    def test_new_evidence_does_not_rescue_a_fail_round(self):
        """Evidence alone cannot repair an unchanged subject already judged FAIL.

        A FAIL means the subject is wrong; both a changed subject and proven
        acceptance progress are needed, not an extra unbound evidence label.
        """
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64, evidence=["r1"]),
                validation_round("FAIL", ["f1"], digest="a" * 64, evidence=["r1", "r2"]),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")

    def test_a_reworded_summary_with_the_same_id_is_the_same_finding(self):
        outcome = self.repair(
            [
                validation_round(
                    "FAIL", ["f1"], digest="a" * 64, summaries={"f1": "gate fails"}
                ),
                validation_round(
                    "FAIL",
                    ["f1"],
                    digest="b" * 64,
                    summaries={"f1": "the deterministic gate still rejects the tree"},
                ),
            ]
        )
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(outcome["stop_reason"], "no_acceptance_progress")
        self.assertEqual([f["id"] for f in outcome["open_findings"]], ["f1"])
        self.assertEqual(
            outcome["open_findings"][0]["summary"],
            "the deterministic gate still rejects the tree",
        )

    def test_open_findings_are_the_union_of_fresh_and_cross_family_ids(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1", "f2", "f3"], digest="a" * 64),
                [
                    validation_round("FAIL", ["f1"], digest="b" * 64, family="fresh", evidence=(
                        {"ref": "fixed-f3", "subject_digest": "b" * 64, "resolves": ["f3"]},
                    )),
                    validation_round("FAIL", ["f2"], digest="b" * 64, family="codex"),
                ],
            ]
        )
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(sorted(f["id"] for f in outcome["open_findings"]), ["f1", "f2"])
        self.assertEqual(
            outcome["report"]["checked"][1], "repair round 1: 2 open findings"
        )

    def test_a_generated_only_change_needs_proven_acceptance_progress(self):
        outcome = self.repair(
            [
                validation_round("FAIL", ["f1"], digest="a" * 64),
                validation_round("PASS", [], digest="b" * 64, evidence=(
                    {"ref": "projection-parity", "subject_digest": "b" * 64, "resolves": ["f1"]},
                )),
            ]
        )
        self.assertEqual(outcome["stop_reason"], "converged")
        self.assertEqual(outcome["rounds_used"], 1)
        self.assertEqual(
            outcome["report"]["checked"][:2],
            ["repair round 0: 1 open findings", "repair round 1: 0 open findings"],
        )

    def test_open_findings_never_land_in_not_checked(self):
        outcome = self.repair(
            [
                validation_round(
                    "FAIL",
                    ["f1"],
                    digest="a" * 64,
                    not_checked=["edge case acceptance"],
                )
            ],
            repair_rounds=0,
        )
        self.assertEqual(outcome["report"]["not_checked"], ["edge case acceptance"])
        self.assertEqual([f["id"] for f in outcome["open_findings"]], ["f1"])
        self.assertNotIn("finding f1", outcome["report"]["not_checked"])

    def test_a_risky_surface_uses_one_fresh_family_by_default(self):
        for family in ("codex", "claude"):
            with self.subTest(family=family):
                single = self.repair(
                    [validation_round("PASS", [], family=family)], risky_surface=True
                )
                self.assertEqual(single["stop_reason"], "converged")
                self.assertEqual(single["report"]["status"], "PASS")

    def test_selected_cross_model_review_needs_a_second_family(self):
        single = self.repair(
            [validation_round("PASS", [], family="claude")], cross_model=True
        )
        self.assertEqual(single["stop_reason"], "diversity_unsatisfied")
        self.assertEqual(single["report"]["status"], "NOT_PROVEN")

        same_family = self.repair(
            [[validation_round("PASS", [], family="claude"),
              validation_round("PASS", [], family="claude")]],
            cross_model=True,
        )
        self.assertEqual(same_family["stop_reason"], "diversity_unsatisfied")
        self.assertEqual(same_family["report"]["status"], "NOT_PROVEN")

        crossed = self.repair(
            [
                [
                    validation_round("PASS", [], family="fresh"),
                    validation_round("PASS", [], family="codex"),
                ]
            ],
            cross_model=True,
        )
        self.assertEqual(crossed["stop_reason"], "converged")
        self.assertEqual(crossed["report"]["status"], "PASS")

    def test_selected_cross_model_disagreement_keeps_the_failure(self):
        split = self.repair(
            [[validation_round("PASS", [], family="claude"),
              validation_round("FAIL", ["f1"], family="codex")]],
            cross_model=True,
        )
        self.assertEqual(split["report"]["status"], "FAIL")
        self.assertEqual([f["id"] for f in split["open_findings"]], ["f1"])

    def test_the_report_keeps_the_nine_key_rpi_report_shape(self):
        outcome = self.repair([validation_round("PASS", [])])
        self.assertEqual(
            sorted(outcome["report"]),
            sorted(
                [
                    "schema_version",
                    "status",
                    "intent_ref",
                    "acceptance_digest",
                    "subject_manifest_digest",
                    "verdict_ref",
                    "verdict_digest",
                    "checked",
                    "not_checked",
                ]
            ),
        )
        self.assertEqual(outcome["report"]["schema_version"], "rpi-report.v1")

    def test_the_repair_phase_needs_at_least_one_validation_round(self):
        with self.assertRaisesRegex(ValueError, "at least one validation round"):
            self.repair([])


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
