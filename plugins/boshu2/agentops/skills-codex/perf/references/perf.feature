# Executable spec for the /perf skill — profiling + optimization (domain role).
# /perf profiles a target's execution to find hotspots, benchmarks it, detects regressions
# between a baseline and candidate, and recommends/applies optimizations — producing actionable
# metrics, not vague advice. Hexagon: domain; consumes repo-context (it profiles the repo's
# code/runtime); produces result.json; shared-kernel with standards. (soc-qk4b)

Feature: Perf profiles and optimizes hotspots with actionable metrics
  As the performance analyzer
  I want a target profiled for hotspots and optimizations grounded in measurements
  So that performance work targets real bottlenecks, not guesses

  Scenario: profile finds hotspots with metrics
    When /perf profile <target> runs
    Then it profiles the target's execution and reports the hotspots with measured metrics
    And the output is actionable metrics, not vague advice

  Scenario: compare detects a regression between baseline and candidate
    When /perf compare <baseline> <candidate> runs
    Then it reports the performance delta and flags a regression when the candidate is slower

  Scenario: optimize recommends or applies changes
    When /perf optimize <target> runs
    Then it analyzes the hotspots and recommends (or applies) optimizations grounded in the profile
