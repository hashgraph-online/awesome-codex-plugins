<!-- generated from skills/*/SKILL.md metadata -->

# Skill tiers

## cross-vendor

`agy-native`

## execution

`idea-genie`, `implement`, `interview`, `memory`, `navigate`, `orchestrate`, `plan`, `refactor`, `research`, `reverse-engineer`, `test`, `using-gc`

## judgment

`council`, `craft-goal`, `postmortem`, `premortem`, `reality-check`, `review`, `validate`

## knowledge

`domain`

## meta

`agent-native`, `rpi`, `skill-builder`, `skill-eval`

## orchestration

`claude-exec`, `codex-exec`

## product

`doc`, `security`

## Inventory

| Skill | Tier | Disposition | Hard dependencies | Capabilities | Effects |
|---|---|---|---|---|---|
| `agent-native` | meta | `keep_optional_adapter` | - | `role_dispatch`, `observe_workers`, `handoff`, `dispatch_once` | `manage_runtime_sessions`, `invoke_selected_executor` |
| `agy-native` | cross-vendor | `keep_optional_adapter` | - | `dispatch_explicit_packet`, `provide_fresh_context` | `start_agy_session` |
| `claude-exec` | orchestration | `keep_optional_adapter` | - | `claude_exec` | `run_claude_process`, `permission_tiered_workspace_effects` |
| `codex-exec` | orchestration | `keep_optional_adapter` | - | `codex_exec` | `run_codex_process`, `sandbox_tiered_workspace_and_network_effects` |
| `council` | judgment | `keep_strategy` | - | `collect_independent_judgments`, `synthesize_disagreement`, `bounded_deliberation`, `duel_scored_ideas`, `answer_interview_panel` | `write_advisory_council_report` |
| `craft-goal` | judgment | `keep_strategy` | - | `goal_prompt_design`, `goal_prompt_lint` | - |
| `doc` | product | `keep_specialist` | - | `doc`, `initialize_missing_docs`, `write_session_handoff` | `write_documentation`, `write_requested_handoff`, `create_requested_evidence_directory` |
| `domain` | knowledge | `keep_specialist` | - | `domain`, `clarify_domain_language`, `reconcile_domain_names` | `update_existing_domain_contracts` |
| `idea-genie` | execution | `keep_strategy` | - | `generate_evidenced_options`, `dueling_idea_genies` | `write_idea_portfolio` |
| `implement` | execution | `keep` | - | `execute_one_experiment`, `collect_factual_evidence` | `modify_declared_subject`, `derive_subject_manifest` |
| `interview` | execution | `keep_strategy` | - | `interview_caller`, `settle_caller_choices`, `write_acceptance_examples`, `settle_domain_terms` | `update_intent_source` |
| `memory` | execution | `keep_off_path` | - | `recall_applicable_context`, `mine_supported_observations`, `curate_topic_pages`, `toil_mining` | `write_protected_drafts`, `update_authorized_topic_pages`, `write_requested_toil_report` |
| `navigate` | execution | `keep_strategy` | - | `observe_work_graph`, `select_next_wave`, `ratchet_work_graph`, `report_graph_hygiene` | `update_native_graph` |
| `orchestrate` | execution | `keep` | - | `coordinate_native_work`, `recover_assignments`, `reconcile_feedback` | `dispatch_authorized_workers`, `update_native_handoffs` |
| `plan` | execution | `keep` | - | `shape_intent`, `define_acceptance`, `bound_write_scope`, `resume_discovery` | `update_intent_source` |
| `postmortem` | judgment | `keep_strategy` | - | `postmortem` | `write_postmortem_report` |
| `premortem` | judgment | `keep_strategy` | - | `challenge_plan` | `write_advisory_plan_review` |
| `reality-check` | judgment | `keep_strategy` | - | `compare_claim_to_evidence`, `measure_declared_goals`, `report_native_status` | `write_advisory_gap_report`, `write_goal_snapshot`, `write_requested_rendered_spec` |
| `refactor` | execution | `keep_specialist` | - | `refactor` | `modify_source_files` |
| `research` | execution | `keep_specialist` | - | `research`, `codebase_recon`, `pattern_mining` | `write_research_report`, `write_recon_pack`, `write_pattern_evidence` |
| `reverse-engineer` | execution | `keep_specialist` | - | `reverse_engineer` | `clone_upstream_repo`, `authorized_binary_execution`, `write_teardown_artifacts` |
| `review` | judgment | `keep` | - | `review_advisory`, `identify_supported_findings`, `report_review_gaps` | - |
| `rpi` | meta | `keep_strategy` | `plan`, `implement`, `validate` | `own_authorized_outcome`, `report` | `dispatch_core_phases` |
| `security` | product | `keep_specialist` | - | `security` | `write_scan_artifacts` |
| `skill-builder` | meta | `keep_specialist` | - | `skill_builder`, `heal_skill`, `export_skill`, `distill_expertise` | `write_skill_source`, `write_build_report`, `regenerate_skill_projections`, `repair_skill_projections`, `write_converted_skill_projection`, `write_advisory_proposal` |
| `skill-eval` | meta | `keep_specialist` | - | `author_seeded_probe`, `run_probe_tier`, `evaluate_skill_decision` | `write_probe_package`, `dispatch_probe_producer` |
| `test` | execution | `keep_specialist` | - | `test` | `write_test_files`, `write_test_evidence`, `modify_source_files` |
| `using-gc` | execution | `keep_optional_adapter` | - | `dispatch_explicit_packet`, `observe_gc_runtime`, `inspect_pack_registries`, `drive_mayor_door` | `operate_gas_city`, `configure_codex_trust` |
| `validate` | judgment | `keep` | - | `compute_subject_identity`, `judge_acceptance`, `return_validation_result`, `persist_verdict` | `write_verdict_artifact` |
