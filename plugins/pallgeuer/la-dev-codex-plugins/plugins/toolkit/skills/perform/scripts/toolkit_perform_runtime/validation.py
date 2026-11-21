"""Shared validation rules for Perform catalog and launcher data."""

import re
import unicodedata

from .diagnostics import PerformRequestError

MODEL_REGEX = r"^[A-Za-z0-9][A-Za-z0-9._:+/-]*$"
EFFORT_REGEX = r"^[a-z][a-z0-9_-]*$"
VARIABLE_NAME_REGEX = r"^[A-Za-z][A-Za-z0-9_]*$"
ACTION_CODEX_OPTION_NAME_REGEX = r"^[A-Za-z0-9][A-Za-z0-9-]*$"

MODEL_PATTERN = re.compile(MODEL_REGEX)
EFFORT_PATTERN = re.compile(EFFORT_REGEX)
VARIABLE_NAME_PATTERN = re.compile(VARIABLE_NAME_REGEX)
ACTION_CODEX_OPTION_NAME_PATTERN = re.compile(ACTION_CODEX_OPTION_NAME_REGEX)
ACTION_FIELDS = (
    "gloss",
    "model",
    "reasoning_effort",
    "goal_mode",
    "plan_mode",
    "plan_reasoning_effort",
    "no_edits",
    "prompt_vars",
    "prompt",
    "requires_interactive",
    "custom_codex_args",
    "notes",
)
ACTION_FIELD_SET = frozenset(ACTION_FIELDS)

RESERVED_CODEX_CONFIG_KEYS = frozenset(("model", "model_reasoning_effort", "plan_mode_reasoning_effort"))
ALLOWED_ACTION_CODEX_OPTIONS = frozenset(("no-alt-screen", "search", "strict-config"))
ACTION_PREVENTING_CODEX_OPTIONS = frozenset(("help", "version"))
DISALLOWED_SINGLE_LINE_CATEGORIES = frozenset(("Cc", "Cf", "Cs", "Zl", "Zp"))


def full_match(pattern, value):
    """Match one anchored pattern without dollar-before-newline behavior."""
    match = pattern.match(value)
    return match is not None and match.end() == len(value)


def valid_model(value):
    """Return whether one value is a valid structured model setting."""
    return isinstance(value, str) and (value == "default" or full_match(MODEL_PATTERN, value))


def valid_effort(value):
    """Return whether one value is a valid structured effort setting."""
    return isinstance(value, str) and full_match(EFFORT_PATTERN, value)


def contains_surrogate(value):
    """Return whether text contains a Unicode surrogate code point."""
    return any(0xD800 <= ord(character) <= 0xDFFF for character in value)


def contains_unsupported_surrogate(value):
    """Return whether text contains a surrogate outside the POSIX surrogateescape range."""
    return any(0xD800 <= ord(character) <= 0xDFFF and not 0xDC80 <= ord(character) <= 0xDCFF for character in value)


def contains_disallowed_single_line_character(value):
    """Return whether text contains a control, format, surrogate, or line separator."""
    return any(unicodedata.category(character) in DISALLOWED_SINGLE_LINE_CATEGORIES for character in value)


def parse_variable_bindings(bindings):
    """Parse repeated variable-name=value strings without evaluating values."""
    if not isinstance(bindings, (list, tuple)) or any(not isinstance(binding, str) for binding in bindings):
        raise PerformRequestError("invalid_variable_argument", "Prompt-variable bindings must be a list or tuple of strings.")
    variables = {}
    for binding in bindings:
        name, separator, value = binding.partition("=")
        if not separator or not full_match(VARIABLE_NAME_PATTERN, name):
            raise PerformRequestError("invalid_variable_argument", "Every --var argument must use Name=VALUE syntax with a variable name matching {}.".format(VARIABLE_NAME_REGEX))
        if name in variables:
            raise PerformRequestError("duplicate_variable_argument", "Prompt variable {!r} was supplied more than once.".format(name))
        variables[name] = value
    return variables


def _split_long_option(argument):
    """Return a long option name, separator, and configured value."""
    if not argument.startswith("--") or argument == "--":
        return None
    option, separator, configured_value = argument[2:].partition("=")
    if not full_match(ACTION_CODEX_OPTION_NAME_PATTERN, option):
        return None
    return option, separator, configured_value


def validate_action_codex_args(value):
    """Return an optional diagnostic for action-defined global Codex options."""
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        return "invalid_custom_codex_args", "custom_codex_args must be a list containing only strings."
    if any(not item or "\x00" in item or contains_surrogate(item) for item in value):
        return "invalid_custom_codex_args", "custom_codex_args entries must be nonempty strings without NUL or Unicode surrogate characters."
    parsed_arguments = [_split_long_option(argument) for argument in value]
    if any(parsed is None for parsed in parsed_arguments):
        return "invalid_custom_codex_args", "custom_codex_args entries must use self-contained --option or --option=value syntax."
    for parsed in parsed_arguments:
        option, separator, _configured_value = parsed
        if option not in ALLOWED_ACTION_CODEX_OPTIONS:
            return "conflicting_custom_codex_args", "custom_codex_args option '--{}' is not in the supported action-option allowlist.".format(option)
        if separator:
            return "invalid_custom_codex_args", "Allowed custom_codex_args options are flags and must not use '=VALUE' syntax."
    return None, None


def _reserved_config_key(key):
    """Return whether one Codex config key belongs to structured action policy."""
    return any(key == reserved or key.startswith(reserved + ".") for reserved in RESERVED_CODEX_CONFIG_KEYS)


def validate_extra_codex_args(value):
    """Return an optional diagnostic for explicit caller Codex arguments."""
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        return "invalid_extra_codex_args", "extra_codex_args must be a list or tuple containing only strings."
    if any(not item or "\x00" in item or contains_unsupported_surrogate(item) for item in value):
        return "invalid_extra_codex_args", "extra_codex_args entries must be nonempty strings without NUL or unsupported Unicode surrogate characters."
    for argument in value:
        parsed = _split_long_option(argument)
        if parsed is None:
            return "invalid_extra_codex_args", "extra_codex_args entries must use self-contained --option or --option=value syntax."
        option, separator, configured_value = parsed
        if option in ACTION_PREVENTING_CODEX_OPTIONS:
            return "invalid_extra_codex_args", "extra_codex_args must not contain help or version options."
        if option == "model":
            return "conflicting_extra_codex_args", "extra_codex_args must not override model; use the structured model field."
        if option == "cd":
            return "conflicting_extra_codex_args", "extra_codex_args must not override the working directory; use the structured launcher cwd."
        if option == "json":
            return "conflicting_extra_codex_args", "extra_codex_args must not override JSON output; use the structured json_output field."
        if option == "verbose":
            return "conflicting_extra_codex_args", "extra_codex_args must not override launcher verbosity; use the codex-perform --verbose flag."
        if option == "config":
            if not separator:
                return "invalid_extra_codex_args", "--config in extra_codex_args must use self-contained --config=key=value syntax."
            key, assignment_separator, _configured_value = configured_value.partition("=")
            key = key.strip()
            if not assignment_separator or not key:
                return "invalid_extra_codex_args", "Codex config overrides in extra_codex_args must use key=value syntax."
            if _reserved_config_key(key):
                return "conflicting_extra_codex_args", "extra_codex_args must not override reserved config key {!r}; use its structured launcher field.".format(key)
    return None, None


def validate_goal_codex_args(value, argument_name):
    """Return an optional conflict for arguments that can prevent goal creation."""
    conflict_code = "conflicting_custom_codex_args" if argument_name == "custom_codex_args" else "conflicting_extra_codex_args"
    for argument in value:
        parsed = _split_long_option(argument)
        if parsed is None:
            continue
        option, separator, configured_value = parsed
        if option == "ephemeral":
            return conflict_code, "{} must not enable ephemeral mode for Goal actions because ephemeral threads do not support goals.".format(argument_name)
        if option == "disable" and separator and configured_value.strip() == "goals":
            return conflict_code, "{} must not disable the goals feature for Goal actions.".format(argument_name)
        if option == "config" and separator:
            key, assignment_separator, _configured_value = configured_value.partition("=")
            if assignment_separator and key.strip() in ("features", "features.goals"):
                return conflict_code, "{} must not override the goals feature configuration for Goal actions.".format(argument_name)
    return None, None


def validate_interactive_codex_args(value):
    """Return an optional conflict for arguments unavailable interactively."""
    for argument in value:
        parsed = _split_long_option(argument)
        if parsed is not None and parsed[0] == "ephemeral":
            return "invalid_extra_codex_args", "extra_codex_args may enable ephemeral mode only for noninteractive launches."
    return None, None
