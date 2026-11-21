"""Literal prompt inspection and rendering for Perform."""

from . import validation
from .diagnostics import PerformRequestError

NO_EDITS_PREFIX = "No edits. "


def build_base_prompt(prompt, no_edits):
    """Return the stored prompt with the automatic no-edits prefix applied once."""
    if no_edits:
        return NO_EDITS_PREFIX + prompt
    return prompt


def validate_bindings(prompt_vars, variables):
    """Validate an exact variable-name-to-nonempty-string binding set."""
    if not isinstance(variables, dict):
        raise PerformRequestError("invalid_variables", "variables must be a JSON object.")
    for name, value in variables.items():
        if not isinstance(name, str) or not validation.full_match(validation.VARIABLE_NAME_PATTERN, name):
            raise PerformRequestError("invalid_variable_name", "Every prompt-variable binding key must match {}.".format(validation.VARIABLE_NAME_REGEX))
        if not isinstance(value, str) or value == "" or "\x00" in value or validation.contains_surrogate(value):
            raise PerformRequestError("invalid_variable_value", "Every prompt-variable binding must map a declared variable name to a nonempty string without NUL or Unicode surrogate characters.")
    expected = set(prompt_vars)
    supplied = set(variables)
    missing = sorted(expected - supplied, key=lambda value: value.encode("ascii"))
    extra = sorted(supplied - expected, key=lambda value: str(value).encode("utf-8"))
    if missing:
        raise PerformRequestError("missing_variables", "Missing prompt-variable bindings: {}.".format(", ".join(missing)))
    if extra:
        raise PerformRequestError("extra_variables", "Undeclared prompt-variable bindings: {}.".format(", ".join(str(value) for value in extra)))


def validate_qualification(qualification):
    """Normalize and structurally validate optional qualification text."""
    if qualification is None:
        return None
    if not isinstance(qualification, str):
        raise PerformRequestError("invalid_qualification", "qualification must be null or a string.")
    if validation.contains_disallowed_single_line_character(qualification):
        raise PerformRequestError("invalid_qualification", "qualification must not contain control, format, surrogate, or line-separator characters.")
    normalized = qualification.strip()
    if not normalized:
        raise PerformRequestError("invalid_qualification", "qualification must contain one nonempty line.")
    if "\r" in normalized or "\n" in normalized:
        raise PerformRequestError("invalid_qualification", "qualification must be one line without CR or LF characters.")
    if normalized.startswith("BUT:"):
        normalized = normalized[len("BUT:") :].lstrip()
        if not normalized:
            raise PerformRequestError("invalid_qualification", "qualification must contain text after the optional 'BUT:' prefix.")
    return normalized


def _render_main_prompt(fields, variables, placeholder_pattern=None):
    """Validate bindings and render the main prompt with optional substitution."""
    prompt_vars = fields["prompt_vars"]
    validate_bindings(prompt_vars, variables)

    if placeholder_pattern is None:
        substituted = fields["prompt"]
    else:

        def replace(match):
            return variables[match.group(0)[1:-1]]

        substituted = placeholder_pattern.sub(replace, fields["prompt"])
    rendered = build_base_prompt(substituted, fields["no_edits"])
    if not rendered.strip():
        raise PerformRequestError("empty_rendered_prompt", "Prompt-variable substitution produced an empty main prompt after trimming.")
    return rendered


def render_prompt(fields, variables, placeholder_pattern, qualification=None):
    """Substitute placeholders once, apply no-edits, and append an optional qualification."""
    rendered = _render_main_prompt(fields, variables, placeholder_pattern=placeholder_pattern)
    normalized_qualification = validate_qualification(qualification)
    if normalized_qualification is not None:
        rendered = rendered.rstrip()
        separator = "\n" if "\n" in rendered else " "
        rendered += separator + "BUT: " + normalized_qualification
    return rendered, normalized_qualification


def render_help_prompt(fields, variables, _placeholder_pattern, qualification=None):
    """Render literal immutable help and append an optional normalized question."""
    rendered = _render_main_prompt(fields, variables)
    normalized_question = validate_qualification(qualification)
    if normalized_question is not None:
        rendered = rendered.rstrip() + "\n\nUser question: " + normalized_question
    return rendered, normalized_question
