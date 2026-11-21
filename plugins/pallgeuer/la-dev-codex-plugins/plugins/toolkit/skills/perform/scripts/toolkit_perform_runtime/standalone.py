"""High-level standalone launcher facade for Perform actions."""

import functools

from . import action_catalogue, api, validation
from . import catalog as catalog_module
from . import paths as paths_module
from .diagnostics import PerformRequestError


def _attach_catalog_diagnostics(method):
    """Attach the owning catalog's visible diagnostics to request failures."""

    @functools.wraps(method)
    def wrapped(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except PerformRequestError as error:
            for diagnostic in api.diagnostic_strings(self._catalog):
                if diagnostic not in error.diagnostics:
                    error.diagnostics.append(diagnostic)
            raise

    return wrapped


class StandaloneLauncher:
    """Versioned selection and preparation facade for standalone launchers."""

    __slots__ = ("_catalog",)

    def __init__(self, catalog):
        """Store one loaded action catalog."""
        if not isinstance(catalog, catalog_module.ActionCatalog):
            raise TypeError("catalog must be an ActionCatalog")
        self._catalog = catalog

    @property
    def precedence_incomplete(self):
        """Return whether mutable catalog precedence is unsafe for selection."""
        return self._catalog.precedence_incomplete

    def _parse_request(self, action, language=None):
        """Normalize one action and optional language without catalog lookup."""
        if language is not None and not catalog_module.is_language_name(language):
            raise PerformRequestError("invalid_language", "Language values must match {} without trimming.".format(catalog_module.LANGUAGE_NAME_REGEX))
        if isinstance(action, str) and validation.full_match(catalog_module.STRICT_SELECTOR_PATTERN, action):
            name, selector_language, selector = catalog_module.parse_selector(action)
            if language is not None and language != selector_language:
                raise PerformRequestError("conflicting_language", "Strict selector {} conflicts with --language {!r}.".format(selector, language))
            return name, selector_language, selector, True
        if not catalog_module.is_action_name(action):
            raise PerformRequestError("invalid_selector", "Expected a bare action name or strict ACTION[LANGUAGE] selector.")
        selector = None if language is None else "{}[{}]".format(action, language)
        return action, language, selector, False

    def _resolve_selector(self, action, language=None):
        """Resolve one deterministic action request to a canonical selector."""
        name, _requested_language, requested_selector, _strict = self._parse_request(action, language=language)
        return self._catalog._select_entry(name, requested_selector=requested_selector).action.selector

    @_attach_catalog_diagnostics
    def list_actions(self, action=None, language=None):
        """Return one filtered JSON-ready action-summary payload."""
        if action is not None:
            name, requested_language, requested_selector, _strict = self._parse_request(action, language=language)
            available = self._catalog.list_actions(name=name)
            if requested_selector is not None:
                variants = [summary for summary in available if summary.selector == requested_selector]
            elif requested_language is not None:
                variants = [summary for summary in available if summary.language == requested_language]
            else:
                variants = available
        else:
            if language is not None and not catalog_module.is_language_name(language):
                raise PerformRequestError("invalid_language", "Language values must match {} without trimming.".format(catalog_module.LANGUAGE_NAME_REGEX))
            variants = self._catalog.list_actions()
            if language is not None:
                variants = [summary for summary in variants if summary.language == language]
        payload = {"variants": [summary.to_dict() for summary in variants]}
        return api.response_payload(self._catalog, result=payload)

    @_attach_catalog_diagnostics
    def show_action(self, action, language=None):
        """Return one JSON-ready launch-configuration payload."""
        selector = self._resolve_selector(action, language=language)
        payload = self._catalog.launch_config(selector).to_dict()
        return api.response_payload(self._catalog, result=payload)

    @_attach_catalog_diagnostics
    def write_action_catalogue(self, output=None):
        """Safely update a stable Markdown catalogue of effective actions."""
        payload = action_catalogue.write_action_catalogue(self._catalog, output=output)
        return api.response_payload(self._catalog, result=payload)

    @_attach_catalog_diagnostics
    def prepare_launch(self, action, language=None, variable_bindings=None, qualification=None):
        """Select and render one action from raw launcher inputs."""
        selector = self._resolve_selector(action, language=language)
        variables = validation.parse_variable_bindings([] if variable_bindings is None else variable_bindings)
        return self._catalog.prepare_launch(selector, variables, qualification=qualification)


def load_standalone_launcher(cwd, env=None):
    """Load conventional action sources into the standalone facade."""
    catalog = catalog_module.load_action_catalog(bundled_dir=paths_module.bundled_actions_dir(), cwd=cwd, env=env)
    return StandaloneLauncher(catalog)


__all__ = ("StandaloneLauncher", "load_standalone_launcher")
