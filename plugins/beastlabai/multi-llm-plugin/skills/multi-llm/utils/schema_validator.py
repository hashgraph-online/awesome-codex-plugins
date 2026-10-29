"""Schema validation utilities for LLM outputs."""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"


class ValidationError(Exception):
    """Raised when schema validation fails."""
    pass


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the schemas directory.

    Args:
        schema_name: Name of schema file (e.g., "task_decomposition.schema.json")

    Returns:
        Schema as dictionary
    """
    schema_path = SCHEMA_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_type(value: Any, expected_type: Union[str, List[str]]) -> bool:
    """Validate a value against a JSON schema type, or a list of them (any matches)."""
    if isinstance(expected_type, list):
        return any(validate_type(value, name) for name in expected_type)
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    if expected_type not in type_map:
        return True  # Unknown type, assume valid

    expected = type_map[expected_type]
    return isinstance(value, expected)


def _has_type(schema: Dict[str, Any], name: str) -> bool:
    declared = schema.get("type")
    return declared == name or (isinstance(declared, list) and name in declared)


def validate_against_schema(
    data: Any,
    schema: Dict[str, Any],
    path: str = ""
) -> List[str]:
    """
    Validate data against a JSON schema (simplified validation).

    Args:
        data: Data to validate
        schema: JSON schema
        path: Current path for error messages

    Returns:
        List of validation error messages
    """
    errors = []

    # Type validation
    if "type" in schema:
        expected_type = schema["type"]
        if not validate_type(data, expected_type):
            errors.append(f"{path}: expected {expected_type}, got {type(data).__name__}")
            return errors  # Can't continue if type mismatch

    # Required fields for objects
    if _has_type(schema, "object") and isinstance(data, dict):
        for required_field in schema.get("required", []):
            if required_field not in data:
                errors.append(f"{path}: missing required field '{required_field}'")

        # Validate properties
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                prop_path = f"{path}.{prop_name}" if path else prop_name
                errors.extend(validate_against_schema(data[prop_name], prop_schema, prop_path))

    # Array items validation
    if _has_type(schema, "array") and isinstance(data, list):
        items_schema = schema.get("items", {})
        for i, item in enumerate(data):
            item_path = f"{path}[{i}]"
            errors.extend(validate_against_schema(item, items_schema, item_path))

    # Enum validation
    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{path}: value '{data}' not in enum {schema['enum']}")

    return errors


# ---------------------------------------------------------------------------
# Fuller JSON Schema subset (draft-07 keywords the task/verdict schemas need)
# ---------------------------------------------------------------------------
#
# ``validate_against_schema`` above is a deliberately loose validator whose
# behavior several older call sites depend on (it ignores
# ``additionalProperties``, ``allOf``, ``if``/``then`` and ``$ref`` entirely).
# The D2 task-JSON, verdict and generated-task schemas need those keywords to
# express per-``kind`` required sets, the ``additionalProperties: false`` rule
# that makes a typo'd field fail at materialization, and the
# ``subagent_type``/``executor_role`` agreement rule. Rather than tighten the
# loose validator under existing consumers, ``validate_document`` implements the
# larger subset and is used by the new validators only.
#
# Supported: type (incl. type arrays), enum, const, required, properties,
# additionalProperties (bool), items, minItems, uniqueItems, minLength,
# minimum, maximum, pattern, allOf, anyOf, oneOf, not, if/then/else and local
# ``$ref`` (``#/$defs/...`` / ``#/definitions/...``).

_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def _matches_type(value: Any, expected: Union[str, List[str]]) -> bool:
    names = [expected] if isinstance(expected, str) else list(expected)
    for name in names:
        py_type = _TYPE_MAP.get(name)
        if py_type is None:
            return True  # unknown type name: do not fail the document on it
        if name == "integer":
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                return True
            continue
        if name == "number":
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                return True
            continue
        if name in ("string", "array", "object", "null"):
            if isinstance(value, py_type):
                return True
            continue
        if isinstance(value, py_type):
            return True
    return False


def _resolve_ref(ref: str, root: Dict[str, Any]) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValidationError(f"Unsupported $ref (only local refs): {ref}")
    node: Any = root
    for part in ref[2:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            raise ValidationError(f"Unresolvable $ref: {ref}")
        node = node[part]
    if not isinstance(node, dict):
        raise ValidationError(f"$ref does not point at a schema: {ref}")
    return node


def validate_document(
    data: Any,
    schema: Dict[str, Any],
    path: str = "",
    root: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Validate ``data`` against ``schema``, returning a list of error strings.

    Implements the draft-07 subset documented above. ``path`` is the dotted
    location used in messages; ``root`` is the document the ``$ref`` pointers
    resolve against (defaults to ``schema`` itself).
    """
    if root is None:
        root = schema
    errors: List[str] = []
    where = path or "<root>"

    if "$ref" in schema:
        return validate_document(data, _resolve_ref(schema["$ref"], root), path, root)

    if "const" in schema and data != schema["const"]:
        errors.append(f"{where}: expected {schema['const']!r}, got {data!r}")

    if "enum" in schema and data not in schema["enum"]:
        errors.append(f"{where}: value {data!r} not in enum {schema['enum']}")

    if "type" in schema and not _matches_type(data, schema["type"]):
        errors.append(
            f"{where}: expected type {schema['type']}, got {type(data).__name__}"
        )
        return errors  # further keyword checks would be noise

    if isinstance(data, str):
        min_length = schema.get("minLength")
        if isinstance(min_length, int) and len(data) < min_length:
            errors.append(
                f"{where}: string shorter than minLength {min_length}"
            )
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and not re.search(pattern, data):
            errors.append(f"{where}: {data!r} does not match pattern {pattern}")

    if isinstance(data, (int, float)) and not isinstance(data, bool):
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{where}: {data} < minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{where}: {data} > maximum {schema['maximum']}")

    if isinstance(data, dict):
        for field in schema.get("required", []):
            if field not in data:
                errors.append(f"{where}: missing required field '{field}'")
        properties = schema.get("properties", {})
        for name, sub_schema in properties.items():
            if name in data:
                sub_path = f"{path}.{name}" if path else name
                errors.extend(
                    validate_document(data[name], sub_schema, sub_path, root)
                )
        extra_schema = schema.get("additionalProperties")
        if extra_schema is False:
            unknown = sorted(set(data) - set(properties))
            for name in unknown:
                errors.append(f"{where}: unexpected field '{name}'")
        elif isinstance(extra_schema, dict):
            for name in sorted(set(data) - set(properties)):
                sub_path = f"{path}.{name}" if path else name
                errors.extend(
                    validate_document(data[name], extra_schema, sub_path, root)
                )

    if isinstance(data, list):
        items_schema = schema.get("items")
        if isinstance(items_schema, dict):
            for index, item in enumerate(data):
                errors.extend(
                    validate_document(item, items_schema, f"{path}[{index}]", root)
                )
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(data) < min_items:
            errors.append(f"{where}: fewer than minItems {min_items} entries")
        if schema.get("uniqueItems"):
            seen: List[Any] = []
            for item in data:
                if item in seen:
                    errors.append(f"{where}: duplicate entry {item!r}")
                    break
                seen.append(item)

    for sub_schema in schema.get("allOf", []):
        errors.extend(validate_document(data, sub_schema, path, root))

    if "anyOf" in schema:
        if not any(
            not validate_document(data, sub, path, root)
            for sub in schema["anyOf"]
        ):
            errors.append(f"{where}: matched none of the anyOf alternatives")

    if "oneOf" in schema:
        matches = sum(
            1
            for sub in schema["oneOf"]
            if not validate_document(data, sub, path, root)
        )
        if matches != 1:
            errors.append(
                f"{where}: matched {matches} oneOf alternatives (exactly 1 required)"
            )

    if "not" in schema and not validate_document(data, schema["not"], path, root):
        errors.append(f"{where}: value {data!r} is explicitly disallowed")

    if "if" in schema:
        condition_holds = not validate_document(data, schema["if"], path, root)
        branch = "then" if condition_holds else "else"
        if branch in schema:
            errors.extend(validate_document(data, schema[branch], path, root))

    return errors


def validate_with_schema_file(data: Any, schema_name: str) -> List[str]:
    """Validate already-parsed ``data`` against a schema file by name."""
    return validate_document(data, load_schema(schema_name))


def validate_json_output(
    output: str,
    schema_name: str
) -> Tuple[bool, Union[Dict[str, Any], List[Any]], List[str]]:
    """
    Validate LLM JSON output against a schema.

    Args:
        output: Raw string output from LLM
        schema_name: Name of schema file to validate against

    Returns:
        Tuple of (is_valid, parsed_data, error_messages)
    """
    # Try to extract JSON from the output
    parsed = None
    errors = []

    # Try direct parsing
    try:
        parsed = json.loads(output.strip())
    except json.JSONDecodeError:
        pass

    # Try extracting from code blocks
    if parsed is None:
        code_block_match = re.search(
            r'```(?:json)?\s*([\[\{][\s\S]*?[\]\}])\s*```',
            output
        )
        if code_block_match:
            try:
                parsed = json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass

    # Try finding JSON structure
    if parsed is None:
        for pattern in [r'\[[\s\S]*\]', r'\{[\s\S]*\}']:
            match = re.search(pattern, output)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                    break
                except json.JSONDecodeError:
                    continue

    if parsed is None:
        return False, {}, ["Could not extract valid JSON from output"]

    # Load and validate against schema
    try:
        schema = load_schema(schema_name)
    except FileNotFoundError as e:
        return False, parsed, [str(e)]

    errors = validate_against_schema(parsed, schema)

    return len(errors) == 0, parsed, errors


def validate_task_dependencies(tasks: List[Dict[str, Any]]) -> List[str]:
    """
    Validate task dependencies form a valid DAG.

    Args:
        tasks: List of task dictionaries with 'id' and 'depends_on' fields

    Returns:
        List of validation errors
    """
    errors = []
    task_ids = {task.get("id") for task in tasks if "id" in task}

    for task in tasks:
        task_id = task.get("id")
        depends_on = task.get("depends_on", [])

        if not task_id:
            errors.append("Task missing 'id' field")
            continue

        for dep_id in depends_on:
            if dep_id not in task_ids:
                errors.append(f"Task {task_id}: dependency '{dep_id}' not found")
            if dep_id == task_id:
                errors.append(f"Task {task_id}: self-dependency")

    # Check for cycles using DFS
    visited = set()
    rec_stack = set()

    def has_cycle(task_id: Any) -> bool:
        visited.add(task_id)
        rec_stack.add(task_id)

        task = next((t for t in tasks if t.get("id") == task_id), None)
        if task:
            for dep_id in task.get("depends_on", []):
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

        rec_stack.remove(task_id)
        return False

    for task in tasks:
        task_id = task.get("id")
        if task_id and task_id not in visited:
            if has_cycle(task_id):
                errors.append(f"Circular dependency detected involving task {task_id}")

    return errors


def validate_code_review_issues(issues: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate code review issues format.

    Args:
        issues: List of issue dictionaries

    Returns:
        Tuple of (is_valid, error_messages)
    """
    is_valid, _, errors = validate_json_output(
        json.dumps(issues),
        "code_review_issues.schema.json"
    )
    return is_valid, errors


def drop_non_record_entries(
    payload: Any,
    model: str,
    *,
    noun: str = "issues",
) -> List[Dict[str, Any]]:
    """Return the record objects in one model's result, dropping everything else.

    **Every aggregation site stamps the producing model onto each element it
    reads** — ``issue["model"] = model``, ``s["source_model"] = model`` — and an
    item assignment against an ``int`` raises ``TypeError``. So a single
    malformed element does not degrade the model that produced it: it takes down
    the phase, and with it every other model's work.

    Measured 2026-09-20 on a ``--review-code --quick`` fan-out of five.
    ``cursor-agent:kimi-k3-high`` reviewed cleanly and ended its final message on
    ``[]``; the stdout fallback scraped the ``[0]`` out of its prose sentence
    "``unattended.ROWS[0].site`` correctly left as-is" instead (clause 5 of
    :func:`utils.json_extractor.extract_json_from_text` is the root-cause fix),
    so its result file held one bare integer. :func:`validate_code_review_issues`
    saw it exactly right — ``Warning: Validation errors: ['[0]: expected object,
    got int']`` — and only *warned*; the run then counted "Found 1 issues" and
    died on ``issue["model"] = model_spec``, stranding the eleven findings the
    other four models had already produced. ``--reaggregate``, the documented
    recovery, died at the same statement one function over.

    This is the validator's verdict being **acted on** rather than only printed,
    which is why it lives beside it. The trade is deliberate and matches the rest
    of the aggregate path (``build_unsanitize_map``'s stem collisions,
    ``resolve_result_files_by_model``'s divergent duplicates): degrade loudly and
    keep going, because fail-closed at the far end of a run throws away a
    completed fan-out to protect one element of it. A payload that is not a list
    at all yields no records for the same reason — iterating a dict there hands
    the caller its *keys*, which fail on the same assignment.

    Args:
        payload: Whatever that model's result was parsed to — a list of records
            in the ordinary case, but any JSON value can reach here from a
            result file on disk.
        model: The model spec the records will be stamped with; named in the
            warning, because "which model do I go and look at" is the first
            question this raises.
        noun: What the records are called in the warning ("issues",
            "suggestions"), matching ``resolve_result_files_by_model``'s.

    Returns:
        The elements of *payload* that are dicts, in order. Empty for ``None``,
        for an empty list, and for any payload that is not a list.
    """
    if payload is None:
        return []

    if not isinstance(payload, list):
        print(
            f"WARNING: {model} produced {type(payload).__name__} where a JSON "
            f"array of {noun} was expected; no {noun} from this model reach the "
            f"report. Every other model's results are aggregated as usual.",
            file=sys.stderr,
        )
        return []

    records = [entry for entry in payload if isinstance(entry, dict)]
    dropped = [entry for entry in payload if not isinstance(entry, dict)]
    if dropped:
        listed = ", ".join(
            f"{entry!r} ({type(entry).__name__})" for entry in dropped[:3]
        )
        if len(dropped) > 3:
            listed += ", …"
        print(
            f"WARNING: {len(dropped)} of {model}'s {len(payload)} {noun} are not "
            f"JSON objects and cannot be attributed to a model: {listed}.\n"
            f"  Dropped. This model's remaining {len(records)} {noun}, and every "
            f"other model's, are aggregated as usual.\n"
            f"  A bare scalar where a record belongs is what the schema "
            f"validator reports as \"expected object, got int\" — most often a "
            f"bracketed index scraped out of the model's prose (`ROWS[0]`) "
            f"rather than anything the model meant to report.",
            file=sys.stderr,
        )
    return records


SUBAGENT_TASKS_SCHEMA = "subagent_tasks.schema.json"
HUMAN_DECISION_VERDICTS_SCHEMA = "human_decision_verdicts.schema.json"
GENERATED_TASKS_SCHEMA = "generated_tasks.schema.json"

#: The one task-file format version this release writes and reads.
TASKS_SCHEMA_VERSION = 2


def validate_subagent_task(task: Dict[str, Any], where: str = "task") -> List[str]:
    """Validate one materialized task object against the D2g schema.

    Args:
        task: A single task dict (an entry of a task file's ``tasks`` array).
        where: Label used as the error path prefix (e.g. ``"tasks[0]"``).

    Returns:
        A list of error strings; empty when the task validates.
    """
    schema = load_schema(SUBAGENT_TASKS_SCHEMA)
    return validate_document(task, schema["$defs"]["task"], where, schema)


def validate_subagent_task_file(data: Any) -> List[str]:
    """Validate a whole materialized task file against the D2g schema.

    Checks the file-level wrapper (``tasks_schema_version``, ``kind``,
    ``inputs``, ``tasks``) and every task in it. Task files also carry
    producer-specific bookkeeping keys (``total_batches``, ``batching_stats``,
    ``reaggregate_command``, …), so the *file* object permits extra properties;
    ``additionalProperties: false`` is enforced on the task objects, which is
    where a typo'd or dropped field would otherwise dispatch a task that is
    merely shaped right.
    """
    return validate_with_schema_file(data, SUBAGENT_TASKS_SCHEMA)


def validate_human_decision_verdicts(data: Any) -> List[str]:
    """Validate a ``human_decision_batch_<n>.json`` document."""
    return validate_with_schema_file(data, HUMAN_DECISION_VERDICTS_SCHEMA)


def validate_generated_tasks_document(data: Any) -> List[str]:
    """Validate a ``task_generation_result.json`` document."""
    return validate_with_schema_file(data, GENERATED_TASKS_SCHEMA)


def supply_schema_version(data: Any, schema_name: str) -> Optional[str]:
    """Read a document that left out its ``schema_version`` as the one
    version its schema allows, and return that version; ``None`` when
    nothing was supplied.

    Fix round 28 (live run 12, Claude Code racing 03): the host copied the
    task-generation subagent's JSON into ``task_generation_result.json``
    without its ``"schema_version": "1.0"``, and the first ``--reaggregate``
    failed schema validation over a key that has one value. A schema that
    requires the key and pins it with ``const`` has one reading of an absent
    key, so the key is supplied (first, in place) before the document is
    validated, when it is all the document lacks: one that the schema still
    refuses with the key is left as it is, so its errors (and no line about a
    version) are what its reader reports, as for a fragment the extractor cut
    out of a broken reply. Only an absent key: a present one, whatever its
    value, is the schema's to judge, and a document that is not an object, or
    a schema with no such ``const``, is left alone.
    """
    if not isinstance(data, dict) or "schema_version" in data:
        return None
    schema = load_schema(schema_name)
    if "schema_version" not in (schema.get("required") or []):
        return None
    version = ((schema.get("properties") or {}).get("schema_version") or {}).get("const")
    if not isinstance(version, str):
        return None
    candidate = {"schema_version": version, **data}
    if validate_document(candidate, schema, "<root>", schema):
        return None
    data.clear()
    data.update(candidate)
    return version


def schema_version_supplied(subject: str, version: str) -> str:
    """The plain words that say *subject* (a file, or "the reply") had no
    ``schema_version`` and was read as *version*; each caller adds what it
    then did."""
    return (
        f'{subject} has no "schema_version"; it was read as version '
        f'"{version}", the only version of this document'
    )


def validate_state_file(state: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate state file format.

    Args:
        state: State dictionary

    Returns:
        Tuple of (is_valid, error_messages)
    """
    is_valid, _, errors = validate_json_output(
        json.dumps(state),
        "state_file.schema.json"
    )
    return is_valid, errors