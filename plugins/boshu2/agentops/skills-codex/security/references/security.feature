# Executable spec for the /security skill — repository security scans (driven-adapter).
# /security runs the available scanners over the repo, fails its own scan on high/critical
# findings, and retains artifacts for audit. Its report feeds validate's verdict. Hexagon:
# driven-adapter; consumes repo-context; produces security-gate-summary.json; supplier-to
# validate. (soc-qk4b)

Feature: Security scans the repository and reports on severity
  As the repository security scanner
  I want the available scanners run and high/critical findings to fail the scan
  So that severe vulnerabilities surface as findings rather than passing silently

  Scenario: scanners run over the repository
    When /security runs
    Then it runs the available scanners over the repo and writes security-gate-summary.json

  Scenario: high or critical findings fail the scan
    When a scanner reports a high or critical finding
    Then /security fails (it does not pass with severe findings outstanding)

  Scenario: a clean full pass is reported without a release decision
    When the full scanner pass reports no high/critical findings
    Then /security reports the clean result and stops, leaving any promote or release
      decision to the caller

  Scenario: artifacts are retained for audit
    When a scan completes
    Then its artifacts are retained for audit and incident response
