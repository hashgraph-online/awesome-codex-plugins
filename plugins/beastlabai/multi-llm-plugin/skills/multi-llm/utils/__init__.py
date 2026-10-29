"""Multi-LLM skill utilities package."""

from .git_utils import (
    GitError,
    baseline_covers,
    get_modified_files,
    get_staged_files,
    list_untracked_files,
    subtract_baseline,
    stage_files,
    unstage_files,
    intent_to_add_untracked,
    get_staged_diff,
    get_file_diff,
    get_current_head,
    head_or_empty_tree,
    get_branch_name,
    is_clean_working_tree,
    get_diff_since_ref,
    get_files_changed_since_ref,
)

from .llm_client import (
    LLMClientError,
    SubagentTimeoutError,
    invoke_subagent,
    parse_subagent_response,
    invoke_for_json,
    invoke_with_provider,
    invoke_with_file_output,
)

from .json_extractor import (
    extract_json_from_text,
    find_json_candidates,
    generate_output_path,
    is_answer_shaped,
    read_json_from_file,
    sanitize_model_name,
)

from .schema_validator import (
    ValidationError,
    drop_non_record_entries,
    load_schema,
    validate_against_schema,
    validate_json_output,
    validate_task_dependencies,
    validate_code_review_issues,
    validate_state_file,
)

from .suggestion_processor import (
    SuggestionGroup,
    extract_suggestions_from_review,
    compute_similarity,
    group_similar_suggestions,
    deduplicate_suggestions,
    merge_suggestions_by_model,
    filter_by_importance,
    export_groups_to_json,
    import_groups_from_json,
)

from .task_decomposer import (
    TaskStatus,
    Task,
    TaskDecomposer,
    decompose_plan_file,
)

from .file_discovery import (
    FileDiscovery,
    discover_implementation_context,
)

from .plan_updater import (
    PlanUpdater,
    update_plan_status,
    extract_task_list,
    insert_generated_tasks,
    insert_tasks_file_reference,
    get_tasks_file_path,
    insert_implementation_summary_reference,
    get_implementation_summary_path,
    GENERATED_TASKS_START,
    GENERATED_TASKS_END,
    TASKS_FILE_REFERENCE_PATTERN,
    TASKS_FILE_REFERENCE_TEMPLATE,
    IMPL_SUMMARY_REFERENCE_PATTERN,
    IMPL_SUMMARY_REFERENCE_TEMPLATE,
)

from .state_manager import (
    StateManager,
    get_or_create_state,
    list_active_sessions,
)

from .output_handler import (
    archive_file,
    prepare_output_file,
    append_to_changelog,
    get_output_paths,
    get_relative_output_path,
    get_output_dir,
    get_phase_dir,
    cleanup_old_archives,
    sanitize_prefix,
    PHASE_DIRECTORIES,
    OUTPUT_TYPE_TO_PHASE,
    OUTPUT_TYPE_TO_FILENAME,
)

from .prompt_loader import (
    load_prompt,
    clear_cache,
)

from .validation import (
    validate_groups,
    apply_validation_to_groups,
    save_validation_results,
)

from .consolidation import (
    generate_group_id as consolidation_generate_group_id,
    generate_consolidated_id,
    normalize_reference,
    pre_group_by_section,
    prepare_consolidation_tasks,
    merge_consolidation_results,
    generate_consolidated_json,
    generate_consolidated_report,
    generate_consolidated_html,
    load_merged_suggestions,
    CONSOLIDATION_SPLIT_THRESHOLD,
    MAX_GROUPS_PER_CONSOLIDATION_BATCH,
    CONSOLIDATION_SUBAGENT_TIMEOUT,
    CONSOLIDATION_RECOMMENDED_THRESHOLD,
    CONSOLIDATION_CHAR_BUDGET,
    TYPE_PRIORITY,
)

from .report_parser import (
    parse_consolidated_skipped_groups,
    parse_consolidated_validation_overrides,
    load_consolidated_html_selections,
    merge_consolidated_selections,
)

from .interactive import (
    NoDecisionChannel,
    select_models_interactive,
    select_models_two_step,
    resolve_models,
)

from .code_fix_batcher import (
    CodeFixBatch,
    batch_code_fixes,
    format_fix_batch_prompt,
    estimate_batch_processing_stats as estimate_code_fix_batch_stats,
    determine_executor_role,
    determine_subagent_type,
    is_high_risk_fix,
    get_line_start,
)

from .provider_registry import (
    load_config,
    get_provider,
    parse_model_spec,
    get_available_models,
    get_all_model_specs,
    get_provider_timeout,
    get_progress_interval,
    get_progress_poll,
    get_provider_max_concurrent,
    is_model_valid,
    get_default_models,
    has_default_models,
    get_quick_models,
    has_quick_models,
)

# providers — GENERATED from provider_registry._PROVIDERS (§9.1).
#
# The hand-written list this replaced omitted THREE adapters (ClaudeCode,
# KiloCode, Muse) and nothing noticed, because deleting an export left the suite
# green. `_PROVIDERS` is the one adapter table and it is already fully imported
# by the block above, so the roster is read off it rather than retyped: adding
# an adapter to the registry exports it here by construction.
from .providers import LLMProvider
from .provider_registry import _PROVIDERS as _REGISTERED_PROVIDERS

_PROVIDER_CLASSES = {
    type(provider).__name__: type(provider)
    for provider in _REGISTERED_PROVIDERS.values()
}
globals().update(_PROVIDER_CLASSES)
_PROVIDER_EXPORTS = tuple(sorted(_PROVIDER_CLASSES))

__all__ = [
    # git_utils
    "GitError",
    "baseline_covers",
    "get_modified_files",
    "get_staged_files",
    "list_untracked_files",
    "subtract_baseline",
    "stage_files",
    "unstage_files",
    "intent_to_add_untracked",
    "get_staged_diff",
    "get_file_diff",
    "get_current_head",
    "head_or_empty_tree",
    "get_branch_name",
    "is_clean_working_tree",
    "get_diff_since_ref",
    "get_files_changed_since_ref",
    # llm_client
    "LLMClientError",
    "SubagentTimeoutError",
    "invoke_subagent",
    "parse_subagent_response",
    "invoke_for_json",
    "invoke_with_provider",
    "invoke_with_file_output",
    # json_extractor
    "extract_json_from_text",
    "find_json_candidates",
    "generate_output_path",
    "is_answer_shaped",
    "read_json_from_file",
    "sanitize_model_name",
    # schema_validator
    "ValidationError",
    "drop_non_record_entries",
    "load_schema",
    "validate_against_schema",
    "validate_json_output",
    "validate_task_dependencies",
    "validate_code_review_issues",
    "validate_state_file",
    # suggestion_processor
    "SuggestionGroup",
    "extract_suggestions_from_review",
    "compute_similarity",
    "group_similar_suggestions",
    "deduplicate_suggestions",
    "merge_suggestions_by_model",
    "filter_by_importance",
    "export_groups_to_json",
    "import_groups_from_json",
    # task_decomposer
    "TaskStatus",
    "Task",
    "TaskDecomposer",
    "decompose_plan_file",
    # file_discovery
    "FileDiscovery",
    "discover_implementation_context",
    # plan_updater
    "PlanUpdater",
    "update_plan_status",
    "extract_task_list",
    "insert_generated_tasks",
    "insert_tasks_file_reference",
    "get_tasks_file_path",
    "insert_implementation_summary_reference",
    "get_implementation_summary_path",
    "GENERATED_TASKS_START",
    "GENERATED_TASKS_END",
    "TASKS_FILE_REFERENCE_PATTERN",
    "TASKS_FILE_REFERENCE_TEMPLATE",
    "IMPL_SUMMARY_REFERENCE_PATTERN",
    "IMPL_SUMMARY_REFERENCE_TEMPLATE",
    # state_manager
    "StateManager",
    "get_or_create_state",
    "list_active_sessions",
    # output_handler
    "archive_file",
    "prepare_output_file",
    "append_to_changelog",
    "get_output_paths",
    "get_relative_output_path",
    "get_output_dir",
    "get_phase_dir",
    "cleanup_old_archives",
    "sanitize_prefix",
    "PHASE_DIRECTORIES",
    "OUTPUT_TYPE_TO_PHASE",
    "OUTPUT_TYPE_TO_FILENAME",
    # prompt_loader
    "load_prompt",
    "clear_cache",
    # validation
    "validate_groups",
    "apply_validation_to_groups",
    "save_validation_results",
    # consolidation
    "consolidation_generate_group_id",
    "generate_consolidated_id",
    "normalize_reference",
    "pre_group_by_section",
    "prepare_consolidation_tasks",
    "merge_consolidation_results",
    "generate_consolidated_json",
    "generate_consolidated_report",
    "generate_consolidated_html",
    "load_merged_suggestions",
    "CONSOLIDATION_SPLIT_THRESHOLD",
    "MAX_GROUPS_PER_CONSOLIDATION_BATCH",
    "CONSOLIDATION_SUBAGENT_TIMEOUT",
    "CONSOLIDATION_RECOMMENDED_THRESHOLD",
    "CONSOLIDATION_CHAR_BUDGET",
    "TYPE_PRIORITY",
    # report_parser (consolidated)
    "parse_consolidated_skipped_groups",
    "parse_consolidated_validation_overrides",
    "load_consolidated_html_selections",
    "merge_consolidated_selections",
    # interactive
    "NoDecisionChannel",
    "select_models_interactive",
    "select_models_two_step",
    "resolve_models",
    # code_fix_batcher
    "CodeFixBatch",
    "batch_code_fixes",
    "format_fix_batch_prompt",
    "estimate_code_fix_batch_stats",
    "determine_executor_role",
    "determine_subagent_type",
    "is_high_risk_fix",
    "get_line_start",
    # provider_registry
    "load_config",
    "get_provider",
    "parse_model_spec",
    "get_available_models",
    "get_all_model_specs",
    "get_provider_timeout",
    "get_progress_interval",
    "get_progress_poll",
    "get_provider_max_concurrent",
    "is_model_valid",
    "get_default_models",
    "has_default_models",
    "get_quick_models",
    "has_quick_models",
    # providers — generated from provider_registry._PROVIDERS (see above)
    "LLMProvider",
    *_PROVIDER_EXPORTS,
]
