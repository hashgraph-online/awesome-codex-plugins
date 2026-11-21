"""Version 1 Perform catalog parsing, layering, and materialization."""

import copy
import json
import pathlib
import re
import types

from . import _values as values_module
from . import diagnostics as diagnostics_module
from . import discovery as discovery_module
from . import launching as launching_module
from . import rendering, validation
from .diagnostics import Diagnostic, PerformRequestError

ACTION_NAME_REGEX = r"^[a-z0-9][a-z0-9._-]*$"
LANGUAGE_NAME_REGEX = r"^[a-z0-9][a-z0-9.+_-]*$"
PLACEHOLDER_REGEX = r"%[A-Za-z][A-Za-z0-9_]*%"
STRICT_SELECTOR_REGEX = r"^([a-z0-9][a-z0-9._-]*)\[([a-z0-9][a-z0-9.+_-]*)\]$"

ACTION_NAME_PATTERN = re.compile(ACTION_NAME_REGEX)
LANGUAGE_NAME_PATTERN = re.compile(LANGUAGE_NAME_REGEX)
PLACEHOLDER_PATTERN = re.compile(PLACEHOLDER_REGEX)
STRICT_SELECTOR_PATTERN = re.compile(STRICT_SELECTOR_REGEX)

ROOT_FIELDS = frozenset(("version", "ignore_actions", "actions"))
HELP_GLOSS = "Explain Perform action files and launch methods"
NO_EDITS_SENTENCE = "No edits."


class DuplicateKeyError(ValueError):
    """A JSON object repeated a key and is therefore ambiguous."""

    def __init__(self, key):
        """Store the repeated key."""
        super().__init__("Duplicate JSON key: {!r}".format(key))
        self.key = key


def is_action_name(value):
    """Return whether a value is a valid bare action name."""
    return isinstance(value, str) and validation.full_match(ACTION_NAME_PATTERN, value)


def is_language_name(value):
    """Return whether a value is a valid language component."""
    return isinstance(value, str) and validation.full_match(LANGUAGE_NAME_PATTERN, value)


def parse_selector(value):
    """Parse and canonicalize one strict ACTION[LANGUAGE] selector."""
    if not isinstance(value, str):
        raise PerformRequestError("invalid_selector", "The selector must be a string.")
    match = STRICT_SELECTOR_PATTERN.match(value)
    if match is None or match.end() != len(value):
        raise PerformRequestError("invalid_selector", "Expected a strict ACTION[LANGUAGE] selector using the documented ASCII grammar.")
    return match.group(1), match.group(2), "{}[{}]".format(match.group(1), match.group(2))


def parse_ignore_selector(value):
    """Return action and optional language for one ignore selector."""
    if is_action_name(value):
        return value, None
    action, language, _canonical = parse_selector(value)
    return action, language


def _unique_pairs(pairs):
    """Build one JSON object while rejecting duplicate keys."""
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(key)
        value[key] = item
    return value


def loads_unique_json(text):
    """Decode JSON with duplicate-key detection at every object depth."""
    return json.loads(text, object_pairs_hook=_unique_pairs)


def _has_manual_no_edits_prefix(prompt):
    """Return whether a prompt starts with the mechanically supplied sentence."""
    return prompt.startswith(NO_EDITS_SENTENCE) and (len(prompt) == len(NO_EDITS_SENTENCE) or prompt[len(NO_EDITS_SENTENCE)].isspace())


class _FieldOrigin:
    """Internal source location for one applied action field or definition."""

    __slots__ = ("filename", "filename_sort_key", "json_path", "source")

    def __init__(self, source, filename, json_path):
        """Store a coherent file and JSON location with precedence metadata."""
        self.source = source
        self.filename = filename
        self.json_path = json_path
        self.filename_sort_key = filename.encode("utf-8", errors="surrogateescape")

    def rank(self):
        """Return the deterministic application rank used for causal errors."""
        return self.source.source_order, self.filename_sort_key


class VariantPatch:
    """Accumulated fields and latest definition origin for one selector."""

    __slots__ = ("definition_origin", "field_origins", "fields")

    def __init__(self, fields=None, field_origins=None, definition_origin=None):
        """Store accumulated fields and the latest definition origin."""
        self.fields = copy.deepcopy(fields or {})
        self.field_origins = dict(field_origins or {})
        self.definition_origin = definition_origin

    def overlay(self, fields, field_origins, definition_origin):
        """Replace supplied fields wholesale while retaining lower unspecified fields."""
        for field, value in fields.items():
            self.fields[field] = copy.deepcopy(value)
            self.field_origins[field] = field_origins[field]
        self.definition_origin = definition_origin


class ActionSummary:
    """Selection metadata for one effective action variant."""

    __slots__ = ("gloss", "language", "name", "prompt_vars", "selector")

    def __init__(self, name, language, gloss, prompt_vars):
        """Store the fields needed for deterministic narrowing and semantic selection."""
        self.name = name
        self.language = language
        self.selector = "{}[{}]".format(name, language)
        self.gloss = gloss
        self.prompt_vars = copy.deepcopy(prompt_vars)

    def to_dict(self):
        """Return the structured metadata for this action variant."""
        result = {"selector": self.selector, "name": self.name, "language": self.language, "gloss": self.gloss}
        if self.prompt_vars:
            result["prompt_vars"] = copy.deepcopy(dict(self.prompt_vars))
        return result


class ActionDefinitionSource(values_module.FrozenValue):
    """Portable-catalogue metadata for one defining JSON file."""

    __slots__ = ("_is_frozen", "directory", "filename", "kind", "source_order")
    directory: str
    filename: str
    kind: str
    source_order: int

    def __init__(self, kind, directory, filename, source_order):
        """Store source semantics, displayed directory, filename, and precedence index."""
        self.kind = kind
        self.directory = directory
        self.filename = filename
        self.source_order = source_order
        self._freeze()


class ActionCatalogueEntry(ActionSummary, values_module.FrozenValue):
    """Read-only action fields and optional defining source for catalogue rendering."""

    __slots__ = ("_is_frozen", "definition_source")
    definition_source: object

    def __init__(self, name, language, gloss, prompt_vars, definition_source=None):
        """Snapshot catalogue fields and definition provenance."""
        if definition_source is not None and not isinstance(definition_source, ActionDefinitionSource):
            raise TypeError("definition_source must be an ActionDefinitionSource or None")
        ActionSummary.__init__(self, name, language, gloss, prompt_vars)
        self.prompt_vars = types.MappingProxyType(self.prompt_vars)
        self.definition_source = definition_source
        self._freeze()


class EffectiveAction:
    """Fully materialized and validated action variant."""

    __slots__ = ("fields", "language", "name", "selector")

    def __init__(self, name, language, fields):
        """Store immutable-by-convention effective action data."""
        self.name = name
        self.language = language
        self.selector = "{}[{}]".format(name, language)
        self.fields = copy.deepcopy(fields)

    def summary(self):
        """Return selection metadata for this effective action."""
        return ActionSummary(
            name=self.name,
            language=self.language,
            gloss=self.fields["gloss"],
            prompt_vars=self.fields["prompt_vars"],
        )


class _ActionEntry:
    """Effective action paired with its rendering and precedence policies."""

    __slots__ = ("action", "definition_source", "precedence_independent", "renderer")

    def __init__(self, action, renderer, precedence_independent, definition_source=None):
        """Store one action with its rendering, precedence, and catalogue policies."""
        self.action = action
        self.renderer = renderer
        self.precedence_independent = precedence_independent
        self.definition_source = definition_source


class ActionInspection:
    """Exact base prompt and metadata shown before semantic binding."""

    __slots__ = ("action", "base_prompt")

    def __init__(self, action, base_prompt):
        """Store an inspected action and its automatically prefixed base prompt."""
        self.action = action
        self.base_prompt = base_prompt

    def to_dict(self):
        """Return only the details consumed while preparing execution."""
        fields = self.action.fields
        if fields["plan_mode"]:
            mode = "plan"
        elif fields["goal_mode"]:
            mode = "goal"
        else:
            mode = "default"
        result = {"prompt": self.base_prompt, "mode": mode}
        if fields["prompt_vars"]:
            result["prompt_vars"] = copy.deepcopy(fields["prompt_vars"])
        if fields["notes"]:
            result["notes"] = fields["notes"]
        return result


class RenderedAction:
    """Final prompt plus user-facing metadata kept outside it."""

    __slots__ = ("action", "prompt", "qualification")

    def __init__(self, action, prompt, qualification):
        """Store final literal prompt and normalized optional qualification."""
        self.action = action
        self.prompt = prompt
        self.qualification = qualification

    def to_dict(self):
        """Return the authoritative rendered prompt."""
        return {"prompt": self.prompt}


def _file_diagnostic(source, filename, code, message, severity="error", json_path=None, selector=None, fatality="file_fatal"):
    """Create a diagnostic with file and deterministic precedence metadata."""
    return Diagnostic(
        severity=severity,
        code=code,
        message=message,
        source_file=str(pathlib.Path(source.display_path) / filename),
        json_path=json_path,
        selector=selector,
        fatality=fatality,
        source_order=source.source_order,
        filename_sort_key=filename.encode("utf-8", errors="surrogateescape"),
    )


def _origin_for_fields(field_origins, definition_origin, implicated_fields):
    """Choose the latest implicated origin, with later arguments breaking ties."""
    selected = None
    for field in implicated_fields:
        origin = field_origins.get(field)
        if origin is not None and (selected is None or origin.rank() >= selected.rank()):
            selected = origin
    return definition_origin if selected is None else selected


def _origin_diagnostic(field_origins, definition_origin, implicated_fields, action, language, code, message):
    """Create one variant-local diagnostic at a coherent causal location."""
    origin = _origin_for_fields(field_origins, definition_origin, implicated_fields)
    return _file_diagnostic(origin.source, origin.filename, code, message, json_path=origin.json_path, selector="{}[{}]".format(action, language), fatality="variant_fatal")


def _prompt_variable_issues(prompt_vars, prompt):
    """Return declaration/use agreement issues in one materialized prompt."""
    declared = set(prompt_vars)
    used = {placeholder[1:-1] for placeholder in PLACEHOLDER_PATTERN.findall(prompt)}
    missing_from_prompt = sorted(declared - used, key=diagnostics_module.unicode_sort_key)
    undeclared = sorted(used - declared, key=lambda value: value.encode("ascii"))
    issues = [
        (
            ("prompt", "prompt_vars"),
            "unused_prompt_variable",
            "Declared prompt variable {} does not occur as %{}% in the materialized prompt.".format(name, name),
        )
        for name in missing_from_prompt
    ]
    issues.extend(
        (
            (
                ("prompt_vars", "prompt"),
                "undeclared_prompt_variable",
                "Prompt placeholder %{}% has no prompt_vars declaration for variable {}.".format(name, name),
            )
            for name in undeclared
        )
    )
    return issues


def _validate_gloss_field(_field, value):
    """Return any local gloss validation issues."""
    if not isinstance(value, str) or not value.strip() or validation.contains_disallowed_single_line_character(value):
        return [("invalid_gloss", "gloss must be a nonempty single-line string without Unicode control or separator characters.")]
    return []


def _validate_model_field(_field, value):
    """Return any local model validation issues."""
    if not validation.valid_model(value):
        return [("invalid_model", "model must be exactly 'default' or match {} without trimming.".format(validation.MODEL_REGEX))]
    return []


def _validate_effort_field(field, value):
    """Return any local reasoning-effort validation issues."""
    if not validation.valid_effort(value):
        return [("invalid_effort", "{} must match {} without trimming.".format(field, validation.EFFORT_REGEX))]
    return []


def _validate_boolean_field(field, value):
    """Return any local Boolean validation issues."""
    if type(value) is not bool:
        return [("invalid_boolean", "{} must be a JSON Boolean.".format(field))]
    return []


def _validate_prompt_vars_field(_field, value):
    """Return any local prompt-variable validation issues."""
    if not isinstance(value, dict):
        return [("invalid_prompt_vars", "prompt_vars must be an object.")]
    issues = []
    for name, description in value.items():
        if not isinstance(name, str) or not validation.full_match(validation.VARIABLE_NAME_PATTERN, name):
            issues.append(("invalid_variable_name", "Prompt variable names must match {}.".format(validation.VARIABLE_NAME_REGEX)))
        if not isinstance(description, str) or not description.strip() or validation.contains_disallowed_single_line_character(description):
            issues.append(("invalid_variable_description", "Every prompt variable description must be a nonempty single-line string without Unicode control or separator characters."))
    return issues


def _validate_prompt_field(_field, value):
    """Return any local prompt validation issues."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value or validation.contains_surrogate(value):
        return [("invalid_prompt", "prompt must be a nonempty string without NUL or Unicode surrogate characters after trimming.")]
    return []


def _validate_custom_codex_args_field(_field, value):
    """Return any local custom Codex argument validation issues."""
    code, message = validation.validate_action_codex_args(value)
    return [] if code is None else [(code, message)]


def _validate_notes_field(_field, value):
    """Return any local notes validation issues."""
    if not isinstance(value, str) or validation.contains_surrogate(value):
        return [("invalid_notes", "notes must be a string without Unicode surrogate characters.")]
    return []


_FIELD_VALIDATORS = {
    "gloss": _validate_gloss_field,
    "model": _validate_model_field,
    "reasoning_effort": _validate_effort_field,
    "goal_mode": _validate_boolean_field,
    "plan_mode": _validate_boolean_field,
    "plan_reasoning_effort": _validate_effort_field,
    "no_edits": _validate_boolean_field,
    "prompt_vars": _validate_prompt_vars_field,
    "prompt": _validate_prompt_field,
    "requires_interactive": _validate_boolean_field,
    "custom_codex_args": _validate_custom_codex_args_field,
    "notes": _validate_notes_field,
}

if frozenset(_FIELD_VALIDATORS) != validation.ACTION_FIELD_SET:
    raise RuntimeError("Action field validators must exactly cover ACTION_FIELDS.")


def _conflicting_modes_issue(fields):
    """Return the goal/plan conflict issue when both modes are enabled."""
    if fields.get("goal_mode") is True and fields.get("plan_mode") is True:
        return ("goal_mode", "plan_mode"), "conflicting_modes", "goal_mode and plan_mode cannot both be true."
    return None


def _plan_interactivity_issue(fields):
    """Return the plan interactivity issue when required mode is absent."""
    if fields.get("plan_mode") is True and "requires_interactive" in fields and fields["requires_interactive"] is not True:
        return ("plan_mode", "requires_interactive"), "plan_requires_interactive", "Plan-mode actions require requires_interactive to be true."
    return None


def _plan_no_edits_issue(fields):
    """Return the plan edit-policy issue when no_edits is not true."""
    if fields.get("plan_mode") is True and "no_edits" in fields and fields["no_edits"] is not True:
        return ("plan_mode", "no_edits"), "plan_requires_no_edits", "Plan-mode actions require no_edits to be true."
    return None


def _non_plan_effort_issue(fields):
    """Return the effort mismatch issue for non-plan actions."""
    if fields.get("plan_mode") is False and "reasoning_effort" in fields and "plan_reasoning_effort" in fields and fields["reasoning_effort"] != fields["plan_reasoning_effort"]:
        return (
            ("plan_mode", "reasoning_effort", "plan_reasoning_effort"),
            "unequal_efforts_without_plan",
            "reasoning_effort and plan_reasoning_effort must be equal when plan_mode is false.",
        )
    return None


def _manual_no_edits_issue(fields):
    """Return the duplicate no-edits prefix issue when present."""
    if fields.get("no_edits") is True and isinstance(fields.get("prompt"), str) and _has_manual_no_edits_prefix(fields["prompt"]):
        return (
            ("no_edits", "prompt"),
            "manual_no_edits_prefix",
            "Remove the manual 'No edits.' prefix; rendering adds it automatically when no_edits is true.",
        )
    return None


_CROSS_FIELD_VALIDATORS = (
    _conflicting_modes_issue,
    _plan_interactivity_issue,
    _plan_no_edits_issue,
    _non_plan_effort_issue,
    _manual_no_edits_issue,
)


def _field_issues(fields, action, language, complete, validate_prompt_variables=True):
    """Return field and cross-field issues for one action definition."""
    issues = []
    selector = "{}[{}]".format(action, language)
    unknown = sorted(set(fields) - validation.ACTION_FIELD_SET, key=lambda value: diagnostics_module.unicode_sort_key(str(value)))
    issues.extend(((field,), "unknown_action_field", "Unknown version 1 action field {!r}.".format(field)) for field in unknown)
    if unknown:
        return issues

    if complete:
        missing = [field for field in validation.ACTION_FIELDS if field not in fields]
        if missing:
            issues.append(((), "incomplete_action", "Materialized {} is missing required fields: {}.".format(selector, ", ".join(missing))))
            return issues

    for field, value in fields.items():
        for code, message in _FIELD_VALIDATORS[field](field, value):
            issues.append(((field,), code, message))

    for validator in _CROSS_FIELD_VALIDATORS:
        issue = validator(fields)
        if issue is not None:
            issues.append(issue)
    if validate_prompt_variables and complete and isinstance(fields.get("prompt_vars"), dict) and isinstance(fields.get("prompt"), str):
        issues.extend(_prompt_variable_issues(fields["prompt_vars"], fields["prompt"]))
    return issues


def _validate_fields(fields, field_origins, definition_origin, action, language, complete):
    """Validate fields and attach each issue to its causal file origin."""
    return [
        _origin_diagnostic(field_origins, definition_origin, implicated_fields, action, language, code, message)
        for implicated_fields, code, message in _field_issues(fields, action, language, complete)
    ]


class _BuiltInActionSpec:
    """Code-defined immutable action and its catalog policies."""

    __slots__ = (
        "definition_code",
        "fields_factory",
        "ignore_code",
        "language",
        "name",
        "precedence_independent",
        "renderer",
        "selector",
        "validate_prompt_variables",
    )

    def __init__(self, name, language, fields_factory, renderer, ignore_code, definition_code, precedence_independent=True, validate_prompt_variables=True):
        """Store one built-in definition and its validation and runtime policies."""
        self.name = name
        self.language = language
        self.selector = "{}[{}]".format(name, language)
        self.fields_factory = fields_factory
        self.renderer = renderer
        self.ignore_code = ignore_code
        self.definition_code = definition_code
        self.precedence_independent = precedence_independent
        self.validate_prompt_variables = validate_prompt_variables

    def build_entry(self):
        """Materialize and validate one built-in action entry."""
        if not is_action_name(self.name) or not is_language_name(self.language):
            raise RuntimeError("Invalid built-in action identity {}.".format(self.selector))
        if not callable(self.renderer):
            raise RuntimeError("Built-in action {} renderer must be callable.".format(self.selector))
        if type(self.precedence_independent) is not bool or type(self.validate_prompt_variables) is not bool:
            raise RuntimeError("Built-in action {} policies must be Boolean.".format(self.selector))
        fields = self.fields_factory()
        if not isinstance(fields, dict):
            raise RuntimeError("Built-in action {} fields factory must return a dictionary.".format(self.selector))
        issues = _field_issues(fields, self.name, self.language, complete=True, validate_prompt_variables=self.validate_prompt_variables)
        if issues:
            details = "; ".join("{}: {}".format(code, message) for _implicated_fields, code, message in issues)
            raise RuntimeError("Invalid built-in action {}: {}".format(self.selector, details))
        return _ActionEntry(EffectiveAction(self.name, self.language, fields), self.renderer, self.precedence_independent)


def _built_in_help_fields():
    """Return immutable help fields with resolved literal guide paths."""
    references = pathlib.Path(__file__).resolve().parents[2] / "references"
    guide_paths = (
        references / "action_files.md",
        references / "codex_skill.md",
        references / "standalone_cli.md",
    )
    prompt_lines = [
        "Read the following installed Perform guides completely and use them as authoritative documentation:",
        *("- {}".format(json.dumps(str(path), ensure_ascii=False)) for path in guide_paths),
        "Answer questions about Perform action files, discovery, layering, catalogues, the in-chat skill, the standalone CLI, and its Python API. If no user question is supplied, give a concise practical overview of those topics, include the main commands and selection forms, and explain which guide contains further details.",
    ]
    return {
        "gloss": HELP_GLOSS,
        "model": "default",
        "reasoning_effort": "medium",
        "goal_mode": False,
        "plan_mode": False,
        "plan_reasoning_effort": "medium",
        "no_edits": True,
        "prompt_vars": {},
        "prompt": "\n".join(prompt_lines),
        "requires_interactive": False,
        "custom_codex_args": [],
        "notes": "",
    }


_HELP_SPEC = _BuiltInActionSpec(
    "help",
    "agnostic",
    _built_in_help_fields,
    rendering.render_help_prompt,
    "reserved_help_ignore",
    "reserved_help_definition",
    validate_prompt_variables=False,
)
_BUILT_IN_SPECS = (_HELP_SPEC,)
HELP_SELECTOR = _HELP_SPEC.selector


def _built_in_spec_for_name(name):
    """Return the built-in specification reserving one action name."""
    for spec in _BUILT_IN_SPECS:
        if spec.name == name:
            return spec
    return None


def _load_json_file(source, filename):
    """Decode and root-validate one action file, returning data and diagnostics."""
    path = pathlib.Path(source.normalized_path) / filename
    try:
        with path.open("rb") as stream:
            raw = stream.read()
    except OSError as exc:
        return None, [_file_diagnostic(source, filename, "action_file_unreadable", "Could not read action file: {}".format(exc), fatality="catalog_fatal")]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [_file_diagnostic(source, filename, "invalid_utf8", "Action file is not valid UTF-8: {}".format(exc))]
    try:
        data = loads_unique_json(text)
    except DuplicateKeyError as exc:
        return None, [_file_diagnostic(source, filename, "duplicate_key", "Action file contains duplicate key {!r}; the entire file was ignored.".format(exc.key))]
    except (TypeError, ValueError) as exc:
        return None, [_file_diagnostic(source, filename, "invalid_json", "Action file is not valid JSON: {}".format(exc))]
    if not isinstance(data, dict):
        return None, [_file_diagnostic(source, filename, "invalid_root", "The version 1 root must be a JSON object.", json_path="")]
    unknown_root = sorted(set(data) - ROOT_FIELDS, key=lambda value: diagnostics_module.unicode_sort_key(str(value)))
    if unknown_root:
        return None, [
            _file_diagnostic(source, filename, "unknown_root_field", "Unknown version 1 root fields make the file unusable: {}.".format(", ".join(repr(field) for field in unknown_root)), json_path="")
        ]
    if "version" not in data or type(data["version"]) is not int:
        return None, [_file_diagnostic(source, filename, "invalid_version", "version is required and must be the integer 1, not a Boolean.", json_path="/version")]
    if data["version"] != 1:
        return None, [_file_diagnostic(source, filename, "unsupported_version", "Unsupported action-file version {!r}; only version 1 is supported.".format(data["version"]), json_path="/version")]
    if "actions" not in data or not isinstance(data["actions"], dict):
        return None, [_file_diagnostic(source, filename, "invalid_actions_root", "actions is required and must be an object.", json_path="/actions")]
    if "ignore_actions" in data and not isinstance(data["ignore_actions"], list):
        return None, [_file_diagnostic(source, filename, "invalid_ignore_actions", "ignore_actions must be a list when present.", json_path="/ignore_actions")]
    if "ignore_actions" not in data:
        data["ignore_actions"] = []
    return data, []


def _apply_file(data, source, filename, patches, diagnostics):
    """Apply one root-trusted file's ignores then valid definitions."""
    for index, ignore_selector in enumerate(data["ignore_actions"]):
        path = "/ignore_actions/{}".format(index)
        if not isinstance(ignore_selector, str):
            diagnostics.append(_file_diagnostic(source, filename, "invalid_ignore_selector", "Ignore selectors must be strings using ACTION or ACTION[LANGUAGE].", json_path=path, fatality="nonfatal"))
            continue
        try:
            action, language = parse_ignore_selector(ignore_selector)
        except PerformRequestError:
            diagnostics.append(
                _file_diagnostic(
                    source, filename, "invalid_ignore_selector", "Invalid ignore selector {!r}; expected ACTION or ACTION[LANGUAGE].".format(ignore_selector), json_path=path, fatality="nonfatal"
                )
            )
            continue
        built_in_spec = _built_in_spec_for_name(action)
        if built_in_spec is not None:
            diagnostics.append(
                _file_diagnostic(
                    source,
                    filename,
                    built_in_spec.ignore_code,
                    "The immutable built-in {} action cannot be ignored.".format(action),
                    json_path=path,
                    selector=ignore_selector,
                    fatality="nonfatal",
                )
            )
            continue
        if language is None:
            for identity in [identity for identity in patches if identity[0] == action]:
                del patches[identity]
        else:
            patches.pop((action, language), None)

    for action, languages in data["actions"].items():
        action_path = "/actions/{}".format(diagnostics_module.json_pointer_component(str(action)))
        if not is_action_name(action):
            diagnostics.append(
                _file_diagnostic(
                    source, filename, "invalid_action_name", "Action names must match {}.".format(ACTION_NAME_REGEX), json_path=action_path, selector=str(action), fatality="variant_fatal"
                )
            )
            continue
        built_in_spec = _built_in_spec_for_name(action)
        if built_in_spec is not None:
            diagnostics.append(
                _file_diagnostic(
                    source,
                    filename,
                    built_in_spec.definition_code,
                    "The immutable built-in {} action cannot be defined or overridden.".format(action),
                    json_path=action_path,
                    selector=action,
                    fatality="nonfatal",
                )
            )
            continue
        if not isinstance(languages, dict) or not languages:
            diagnostics.append(
                _file_diagnostic(
                    source,
                    filename,
                    "invalid_action_languages",
                    "Each action must contain a nonempty object of language implementations.",
                    json_path=action_path,
                    selector=action,
                    fatality="variant_fatal",
                )
            )
            continue
        for language, fields in languages.items():
            language_path = "{}/{}".format(action_path, diagnostics_module.json_pointer_component(str(language)))
            selector = "{}[{}]".format(action, language)
            if not is_language_name(language):
                diagnostics.append(
                    _file_diagnostic(
                        source, filename, "invalid_language_name", "Language names must match {}.".format(LANGUAGE_NAME_REGEX), json_path=language_path, selector=selector, fatality="variant_fatal"
                    )
                )
                continue
            if not isinstance(fields, dict) or not fields:
                diagnostics.append(
                    _file_diagnostic(
                        source,
                        filename,
                        "invalid_language_fields",
                        "Each language implementation must contain a nonempty object of fields.",
                        json_path=language_path,
                        selector=selector,
                        fatality="variant_fatal",
                    )
                )
                continue
            definition_origin = _FieldOrigin(source, filename, language_path)
            field_origins = {field: _FieldOrigin(source, filename, "{}/{}".format(language_path, diagnostics_module.json_pointer_component(str(field)))) for field in fields}
            complete = language == "agnostic"
            field_diagnostics = _validate_fields(fields, field_origins, definition_origin, action, language, complete=complete)
            diagnostics.extend(field_diagnostics)
            if field_diagnostics:
                continue
            identity = (action, language)
            if language == "agnostic" or identity not in patches:
                patches[identity] = VariantPatch(fields=fields, field_origins=field_origins, definition_origin=definition_origin)
            else:
                patches[identity].overlay(fields, field_origins, definition_origin)


def _materialize(patches, diagnostics):
    """Apply agnostic inheritance and final validation to accumulated patches."""
    entries = {}
    patches_by_action = {}
    for (action, language), patch in patches.items():
        patches_by_action.setdefault(action, {})[language] = patch
    for action in sorted(patches_by_action, key=lambda value: value.encode("ascii")):
        action_patches = patches_by_action[action]
        languages = sorted(action_patches, key=lambda value: value.encode("ascii"))
        base = action_patches.get("agnostic")
        for language in languages:
            patch = action_patches[language]
            if language == "agnostic":
                fields = copy.deepcopy(patch.fields)
                field_origins = dict(patch.field_origins)
            else:
                fields = copy.deepcopy(base.fields) if base is not None else {}
                field_origins = dict(base.field_origins) if base is not None else {}
                for field, value in patch.fields.items():
                    fields[field] = copy.deepcopy(value)
                    field_origins[field] = patch.field_origins[field]
            final_diagnostics = _validate_fields(fields, field_origins, patch.definition_origin, action, language, complete=True)
            diagnostics.extend(final_diagnostics)
            if final_diagnostics:
                continue
            origin = patch.definition_origin
            definition_source = ActionDefinitionSource(origin.source.kind, origin.source.display_path, origin.filename, origin.source.source_order)
            entries[(action, language)] = _ActionEntry(EffectiveAction(action, language, fields), rendering.render_prompt, False, definition_source=definition_source)
    return entries


class ActionCatalog:
    """Effective Perform actions, diagnostics, discovery, and rendering API."""

    __slots__ = ("_entries", "diagnostics", "discovery", "precedence_incomplete")

    def __init__(self, entries, diagnostics, discovery, precedence_incomplete=False):
        """Store validated action entries and deterministic diagnostics."""
        built_in_names = {spec.name for spec in _BUILT_IN_SPECS}
        mutable_built_in_names = sorted({entry.action.name for entry in entries.values()} & built_in_names, key=lambda value: value.encode("ascii"))
        if mutable_built_in_names:
            raise RuntimeError("Mutable actions cannot use reserved built-in names: {}.".format(", ".join(mutable_built_in_names)))
        self._entries = dict(entries)
        for spec in _BUILT_IN_SPECS:
            entry = spec.build_entry()
            identity = (entry.action.name, entry.action.language)
            if identity in self._entries:
                raise RuntimeError("Built-in action {} conflicts with a mutable action.".format(entry.action.selector))
            self._entries[identity] = entry
        self.diagnostics = diagnostics_module.sorted_unique_diagnostics(list(discovery.diagnostics) + list(diagnostics))
        self.discovery = discovery
        self.precedence_incomplete = precedence_incomplete or discovery.precedence_incomplete or any(diagnostic.fatal for diagnostic in self.diagnostics)

    def list_actions(self, name=None):
        """Return all summaries or variants of one exact bare action name."""
        if name is not None and not is_action_name(name):
            raise PerformRequestError("invalid_name", "Action-name filters must match {}.".format(ACTION_NAME_REGEX))
        summaries = [entry.action.summary() for entry in self._entries.values() if name is None or entry.action.name == name]
        return sorted(summaries, key=lambda summary: (summary.name.encode("ascii"), summary.language.encode("ascii")))

    def catalogue_entries(self):
        """Return stable read-only action entries with catalogue-only provenance."""
        if self.precedence_incomplete:
            raise PerformRequestError("fatal_catalog", "Catalog precedence is incomplete; fix the fatal discovery or file diagnostic before generating an action catalogue.")
        entries = []
        for entry in self._entries.values():
            action = entry.action
            entries.append(ActionCatalogueEntry(action.name, action.language, action.fields["gloss"], action.fields["prompt_vars"], definition_source=entry.definition_source))
        return sorted(entries, key=lambda entry: (entry.name.encode("ascii"), entry.language.encode("ascii")))

    def _require_complete_precedence(self):
        """Reject prompt-sensitive operations when an override source is unknowable."""
        if self.precedence_incomplete:
            raise PerformRequestError("fatal_catalog", "Catalog precedence is incomplete; fix the fatal discovery or file diagnostic before selecting or using a mutable action.")

    def _select_entry(self, name, requested_selector=None):
        """Select one action entry after request syntax has been normalized."""
        available = sorted((entry for entry in self._entries.values() if entry.action.name == name), key=lambda entry: entry.action.language.encode("ascii"))
        independent = bool(available) and all(entry.precedence_independent for entry in available)
        alternatives = [entry.action.selector for entry in available]
        if requested_selector is not None:
            for entry in available:
                if entry.action.selector == requested_selector:
                    if not entry.precedence_independent:
                        self._require_complete_precedence()
                    return entry
            if not independent:
                self._require_complete_precedence()
            raise PerformRequestError("not_found", "No effective action matches strict selector {}.".format(requested_selector), alternatives=alternatives)
        if not independent:
            self._require_complete_precedence()
        if len(available) == 1:
            return available[0]
        agnostic = "{}[agnostic]".format(name)
        for entry in available:
            if entry.action.selector == agnostic:
                return entry
        if not available:
            raise PerformRequestError("not_found", "No effective action is named {!r}.".format(name))
        raise PerformRequestError("ambiguous_language", "Action {!r} has multiple language variants; use --language or a strict selector.".format(name), alternatives=alternatives)

    def _resolve_entry(self, selector):
        """Resolve one strict selector without constructing derived prompt data."""
        name, _language, canonical = parse_selector(selector)
        return self._select_entry(name, requested_selector=canonical)

    def inspect(self, selector):
        """Return the exact effective base prompt for one strict selector."""
        action = self._resolve_entry(selector).action
        return ActionInspection(action, rendering.build_base_prompt(action.fields["prompt"], action.fields["no_edits"]))

    def launch_config(self, selector):
        """Return every effective field needed by a standalone launcher."""
        return launching_module.ActionLaunchConfig(self._resolve_entry(selector).action)

    def render(self, selector, variables, qualification=None):
        """Render one exact action after binding and qualification validation."""
        entry = self._resolve_entry(selector)
        prompt, normalized_qualification = entry.renderer(entry.action.fields, variables, PLACEHOLDER_PATTERN, qualification)
        return RenderedAction(entry.action, prompt, normalized_qualification)

    def prepare_launch(self, selector, variables, qualification=None):
        """Render one action and retain its complete launcher configuration."""
        rendered = self.render(selector, variables, qualification=qualification)
        return launching_module.ActionLaunchSpec(launching_module.ActionLaunchConfig(rendered.action), rendered.prompt, rendered.qualification)


def _list_source_files(source, diagnostics):
    """Return direct JSON filenames in exact UTF-8 byte order."""
    try:
        entries = list(pathlib.Path(source.normalized_path).iterdir())
    except OSError as exc:
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="action_source_unreadable",
                message="Could not enumerate applicable {} action source {}: {}".format(source.kind, source.display_path, exc),
                source_file=source.display_path,
                fatality="catalog_fatal",
                source_order=source.source_order,
            )
        )
        return []
    filenames = []
    for entry in entries:
        name = entry.name
        try:
            encoded = name.encode("utf-8")
        except UnicodeEncodeError:
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="unencodable_action_filename",
                    message="An action filename cannot be sorted as UTF-8 bytes in {}.".format(source.display_path),
                    source_file=source.display_path,
                    fatality="catalog_fatal",
                    source_order=source.source_order,
                )
            )
            continue
        if name.endswith(".json") and entry.is_file():
            filenames.append((encoded, name))
    return [name for _encoded, name in sorted(filenames, key=lambda item: item[0])]


def load_action_catalog(bundled_dir=None, cwd=None, env=None, action_directories=None, filesystem=None, git_runner=None, system_actions_dir="/etc/codex/toolkit_perform_actions"):
    """Discover or explicitly load action directories into one effective catalog."""
    if action_directories is not None:
        discovery = discovery_module.explicit_discovery(action_directories)
    else:
        if bundled_dir is None:
            raise ValueError("bundled_dir is required when action_directories is not supplied")
        discovery = discovery_module.discover_action_directories(
            bundled_dir=bundled_dir,
            cwd=cwd,
            env=env,
            filesystem=filesystem,
            git_runner=git_runner,
            system_actions_dir=system_actions_dir,
        )
    patches = {}
    diagnostics = []
    for source in discovery.sources:
        for filename in _list_source_files(source, diagnostics):
            data, file_diagnostics = _load_json_file(source, filename)
            diagnostics.extend(file_diagnostics)
            if data is not None:
                _apply_file(data, source, filename, patches, diagnostics)
    entries = _materialize(patches, diagnostics)
    return ActionCatalog(entries, diagnostics, discovery)
