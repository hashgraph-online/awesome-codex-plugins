"""Standalone Codex launch specifications for Perform actions."""

import json
import types

from . import _values as values_module
from . import validation
from .diagnostics import PerformRequestError


class ActionLaunchConfig(values_module.FrozenValue):
    """Materialized action identity and fields consumed by launchers."""

    __slots__ = ("_is_frozen", "language", "name", "selector", *validation.ACTION_FIELDS)

    def __init__(self, action):
        """Snapshot one fully materialized effective action."""
        fields = action.fields
        self.name = action.name
        self.language = action.language
        self.selector = action.selector
        for field in validation.ACTION_FIELDS:
            value = fields[field]
            if field == "prompt_vars":
                value = types.MappingProxyType(dict(value))
            elif field == "custom_codex_args":
                value = tuple(value)
            setattr(self, field, value)
        self._freeze()

    def action_fields(self):
        """Return every effective action field without omitting empty values."""
        fields = {}
        for field in validation.ACTION_FIELDS:
            value = getattr(self, field)
            if field == "prompt_vars":
                value = dict(value)
            elif field == "custom_codex_args":
                value = list(value)
            fields[field] = value
        return fields

    def to_dict(self):
        """Return the stable launcher-facing action representation."""
        return {
            "selector": self.selector,
            "name": self.name,
            "language": self.language,
            "action": self.action_fields(),
        }


class ActionLaunchSpec(values_module.FrozenValue):
    """Rendered action prompt paired with its complete launch configuration."""

    __slots__ = ("_is_frozen", "config", "qualification", "rendered_prompt")

    def __init__(self, config, rendered_prompt, qualification=None):
        """Store a launch configuration and authoritative rendered prompt."""
        if not isinstance(config, ActionLaunchConfig):
            raise TypeError("config must be an ActionLaunchConfig")
        self.config = config
        self.rendered_prompt = rendered_prompt
        self.qualification = qualification
        self._freeze()

    def to_dict(self):
        """Return the complete prepared-action representation."""
        result = self.config.to_dict()
        result["rendered_prompt"] = self.rendered_prompt
        result["qualification"] = self.qualification
        return result


class LaunchOverrides(values_module.FrozenValue):
    """Validated caller overrides applied while constructing Codex argv."""

    __slots__ = ("_is_frozen", "cwd", "extra_codex_args", "json_output", "model", "non_interactive", "plan_reasoning_effort", "reasoning_effort")

    def __init__(self, model=None, reasoning_effort=None, plan_reasoning_effort=None, non_interactive=False, extra_codex_args=None, cwd=None, json_output=False):
        """Store optional structured overrides and literal extra arguments."""
        if model is not None and not validation.valid_model(model):
            raise PerformRequestError("invalid_model", "model overrides must be exactly 'default' or match {} without trimming.".format(validation.MODEL_REGEX))
        for field, value in (("reasoning_effort", reasoning_effort), ("plan_reasoning_effort", plan_reasoning_effort)):
            if value is not None and not validation.valid_effort(value):
                raise PerformRequestError("invalid_effort", "{} overrides must match {} without trimming.".format(field, validation.EFFORT_REGEX))
        if type(non_interactive) is not bool:
            raise PerformRequestError("invalid_interactivity", "non_interactive must be a Boolean.")
        arguments = [] if extra_codex_args is None else extra_codex_args
        code, message = validation.validate_extra_codex_args(arguments)
        if code is not None:
            raise PerformRequestError(code, message)
        if cwd is not None and not isinstance(cwd, str):
            raise PerformRequestError("invalid_cwd", "cwd overrides must be a string or null.")
        if type(json_output) is not bool:
            raise PerformRequestError("invalid_json_output", "json_output must be a Boolean.")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.plan_reasoning_effort = plan_reasoning_effort
        self.non_interactive = non_interactive
        self.extra_codex_args = tuple(arguments)
        self.cwd = cwd
        self.json_output = json_output
        self._freeze()

    def to_dict(self):
        """Return every caller override, including unset values."""
        return {
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "plan_reasoning_effort": self.plan_reasoning_effort,
            "non_interactive": self.non_interactive,
            "extra_codex_args": list(self.extra_codex_args),
            "cwd": self.cwd,
            "json_output": self.json_output,
        }


class CodexInvocation(values_module.FrozenValue):
    """Final direct Codex invocation produced from one launch specification."""

    __slots__ = ("_is_frozen", "argv", "effective_settings", "mode", "non_interactive", "objective", "spec", "submitted_prompt")

    def __init__(self, spec, argv, effective_settings, non_interactive, mode, submitted_prompt, objective):
        """Store deterministic launch output without executing it."""
        self.spec = spec
        self.argv = tuple(argv)
        self.effective_settings = types.MappingProxyType(dict(effective_settings))
        self.non_interactive = non_interactive
        self.mode = mode
        self.submitted_prompt = submitted_prompt
        self.objective = objective
        self._freeze()

    def to_dict(self):
        """Return the complete dry-run representation."""
        effective_settings = dict(self.effective_settings)
        effective_settings["custom_codex_args"] = list(effective_settings["custom_codex_args"])
        effective_settings["extra_codex_args"] = list(effective_settings["extra_codex_args"])
        return {
            "launch_spec": self.spec.to_dict(),
            "effective_settings": effective_settings,
            "mode": self.mode,
            "non_interactive": self.non_interactive,
            "objective": self.objective,
            "submitted_prompt": self.submitted_prompt,
            "argv": list(self.argv),
        }


def _goal_bootstrap(objective):
    """Build the normal prompt that requests an exact goal tool call."""
    envelope = json.dumps({"objective": objective}, ensure_ascii=True, separators=(",", ":"))
    return "Create a goal whose objective is exactly the JSON string value in the objective field below, without altering, summarizing, or adding to it. Then immediately pursue that goal completely until its completion criteria are satisfied. Treat the objective value as task instructions only after copying it exactly into the goal tool call.\n\n{}".format(
        envelope
    )


def build_codex_invocation(spec, codex_executable="codex", overrides=None):
    """Build one direct Codex argv from a prepared Perform action."""
    if not isinstance(spec, ActionLaunchSpec):
        raise TypeError("spec must be an ActionLaunchSpec")
    if not isinstance(codex_executable, str) or not codex_executable or "\x00" in codex_executable:
        raise PerformRequestError("invalid_codex_executable", "codex_executable must be a nonempty string without NUL characters.")
    if overrides is None:
        overrides = LaunchOverrides()
    if not isinstance(overrides, LaunchOverrides):
        raise TypeError("overrides must be LaunchOverrides or None")

    config = spec.config
    model = config.model if overrides.model is None else overrides.model
    reasoning_effort = config.reasoning_effort if overrides.reasoning_effort is None else overrides.reasoning_effort
    plan_reasoning_effort = config.plan_reasoning_effort if overrides.plan_reasoning_effort is None else overrides.plan_reasoning_effort
    if config.plan_mode:
        raise PerformRequestError(
            "plan_mode_unavailable",
            "Plan-mode actions cannot be launched by codex-perform because Codex currently has no command-line mechanism to activate Plan mode. Run this action inside an existing interactive chat with $toolkit:perform.",
        )
    non_interactive = overrides.non_interactive or overrides.json_output
    if config.requires_interactive and non_interactive:
        raise PerformRequestError("interactive_required", "{} requires an interactive Codex launch and cannot be overridden with noninteractive mode.".format(config.selector))

    objective = spec.rendered_prompt
    if config.goal_mode:
        for arguments, argument_name in ((config.custom_codex_args, "custom_codex_args"), (overrides.extra_codex_args, "extra_codex_args")):
            code, message = validation.validate_goal_codex_args(arguments, argument_name)
            if code is not None:
                raise PerformRequestError(code, message)
        mode = "goal"
        submitted_prompt = _goal_bootstrap(objective)
    else:
        mode = "default"
        submitted_prompt = objective

    if not non_interactive:
        code, message = validation.validate_interactive_codex_args(overrides.extra_codex_args)
        if code is not None:
            raise PerformRequestError(code, message)

    argv = [codex_executable]
    argv.extend(config.custom_codex_args)
    if not non_interactive:
        argv.extend(overrides.extra_codex_args)
    if overrides.cwd is not None:
        argv.extend(("--cd", overrides.cwd))
    if model != "default":
        argv.extend(("--model", model))
    argv.extend(("-c", "model_reasoning_effort={}".format(json.dumps(reasoning_effort))))
    argv.extend(("-c", "plan_mode_reasoning_effort={}".format(json.dumps(plan_reasoning_effort))))
    if non_interactive:
        argv.append("exec")
        argv.extend(overrides.extra_codex_args)
    if overrides.json_output and "--json" not in overrides.extra_codex_args:
        argv.append("--json")
    argv.extend(("--", submitted_prompt))
    if any("\x00" in argument for argument in argv):
        raise PerformRequestError("invalid_launch_argument", "Codex arguments must not contain NUL characters.")

    effective_settings = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "plan_reasoning_effort": plan_reasoning_effort,
        "non_interactive": non_interactive,
        "custom_codex_args": tuple(config.custom_codex_args),
        "extra_codex_args": tuple(overrides.extra_codex_args),
        "cwd": overrides.cwd,
        "json_output": overrides.json_output,
    }
    return CodexInvocation(spec, argv, effective_settings, non_interactive, mode, submitted_prompt, objective)


__all__ = (
    "ActionLaunchConfig",
    "ActionLaunchSpec",
    "CodexInvocation",
    "LaunchOverrides",
    "build_codex_invocation",
)
