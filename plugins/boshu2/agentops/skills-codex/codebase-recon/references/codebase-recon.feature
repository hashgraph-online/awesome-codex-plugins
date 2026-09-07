Feature: Evidence-bounded repository reconstruction

  @covered-by:tests/scripts/agentops-native-skills.bats::evidence-bounded
  Scenario: A baseline explains representative repository flows
    Given repository precedence and the current commit are known
    When entry, domain, integration, and test paths are traced
    Then material claims are typed and cited against that exact commit
    And inspected and uninspected scope are explicit

  @covered-by:tests/scripts/agentops-native-skills.bats::delta
  Scenario: A later run preserves a verified baseline
    Given an earlier recon pack exists
    When the repository is reconstructed again
    Then the cited prior manifest chain passes the recon validator
    And the earlier commit is an ancestor of the current repository HEAD
    And the new artifact's changed paths equal the Git diff between those commits
    And dirty source bytes outside the declared commits are rejected

  @covered-by:tests/scripts/agentops-native-skills.bats::prior-discovery
  Scenario: Current and earlier default packs are discoverable
    Given validated prior manifests under .agents/scratch/codebase-recon and .agents/recon
    When prior discovery runs
    Then both manifests are returned at their existing paths
    And an invalid manifest is never accepted as a delta's prior pack

  @covered-by:tests/scripts/agentops-native-skills.bats::companion
  Scenario: The manifest and human report are one stable evidence pack
    Given codebase-recon.json binds codebase-recon.md by SHA-256
    And the report binds the manifest commit, mode, flows, claims, and coverage
    When validation runs over immutable snapshots of both files
    Then a missing mismatched or symlinked companion is rejected
    And a manifest, report, HEAD, index, or worktree change before return is rejected
