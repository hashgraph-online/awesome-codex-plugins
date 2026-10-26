# Suite Audit

Use this reference for an authorized decision to maintain or retire named tests.
It supplements [Test](../SKILL.md) when protection or redundancy is uncertain;
it creates no deletion target, new mode or mandatory audit artifact.

## Identify the protection before changing the test

Read each candidate test in full and name the exact accepted behavior it guards:
inputs, public result or error, important boundaries and the plausible regression
its assertions would detect. Use its file and test name so the decision has an
exact subject. A test's size, age or implementation detail alone says nothing
about whether its protection can be removed.

Trace that behavior to its production owner and reachable public interface.
Inspect current callers, including relevant command dispatch, scripts, adapters,
registries or generated wiring, and the overlapping tests. Record what was
actually traced and where caller or reachability knowledge ends. Consult history
when the reason for an assertion would otherwise be lost.

A missing substring or search hit is a lead, not proof that behavior is unused.
Dynamic or external callers may escape the search. If production reachability,
current callers or the protected contract remain unknown, retain the test and
report the maintenance decision as unresolved.

## Compare the meaningful surviving proof

Name the tests that would survive the proposed change and the behavior each one
actually observes. Compare them against the candidate's protection, not against
its line count. A new interface test that runs successfully, parses a response or
checks only an exit code may still miss a compatibility promise.

Before removing real protection, establish stronger surviving coverage at the
public contract: it must exercise the relevant production route, assert the
promised values or errors and distinguish the regression being guarded. Preserve
unique error, boundary and compatibility cases when consolidating. Use Test's
proof and runner rules for new or changed checks; overlapping green tests alone
do not establish equivalence.

## Choose the smallest authorized outcome

| Outcome | Condition |
|---|---|
| Retain | The test provides meaningful protection, or its protection is still unknown. |
| Rewrite | The behavior matters, but the test observes the wrong boundary or has a weak or brittle oracle; preserve its accepted protection. |
| Consolidate | Named overlap can be expressed more clearly while stronger surviving public-contract proof preserves every real protection. |
| Retire | The behavior was removed by an authorized contract change, stronger surviving public-contract proof covers its real protection, or the passing test protects nothing (below). |

A passing test protects nothing when no observable behavior change could make
it fail: it restates source text, an export list or a copied fixture, or it
asserts nothing a broken implementation would violate. That shown fact is its
retirement evidence in place of surviving proof. Keep a source-inspection check
that pins a key, byte sequence or path users see and survives an
identifier-only rename, and keep the only check guarding a public API, schema,
storage format or security behavior. A failing or unrunnable test is a
possible defect, never a protects-nothing candidate; retire it only under an
authorized contract change.

A retirement decision names the exact protected behavior, production owner and
reachability, current callers, and meaningful surviving proof, or, for a test
that protects nothing, the shown fact that no behavior change could make it
fail. Missing evidence
means retain/unresolved. Do not redefine acceptance to make a failing test
obsolete, remove a whole suite on a search result, or delete tests to meet a quota.
Apply only the authorized named changes and run the owning suite and repository
check recipe on the resulting candidate. A removed protection may require the
fresh read required by repository policy; this reference does not grant approval.

## CLI compatibility example

Suppose `tasks list --json` has a public contract with a top-level `tasks` array,
stable record `id` values and an empty result of `{"tasks":[]}`. A serializer
refactor makes a helper-level output test look redundant. A new process test that
only checks exit 0 and parseable JSON would allow `{"entries":[]}` to pass and
break a legitimate script reading `tasks`.

Trace the command's live dispatch to its output owner and inspect known script
callers. Before removing the helper check, establish stronger process coverage
for the accepted empty and nonempty shapes and the stable IDs, with assertions
that reject the renamed field. Keep any unique errors or boundaries from the
old test. If surviving proof or consumer knowledge is insufficient, retain the
check; an absent repository caller cannot withdraw a public contract.

Return the named decisions and their supporting facts through the existing
handoff, including unresolved protection and checks actually run. Persist an
audit only for a requested or declared consumer at its selected destination.
No retirement cards, report directories, commits or delivery steps are implied.
