"""The telegram-bot-ui emoji library contract, skill side: the vendored schemas and a validator.

`data/emoji/library-contract.json` holds the component schemas of the library's OpenAPI 3.1
document (GET /api/emoji-openapi.json), the tag taxonomy this skill understands and the pack
threshold, with the source URL and the day they were copied. LibraryClient (emoji_packs.py)
checks every library answer and every line of the offline export with `check_answer`, so a
changed API fails with a message that names the field, not with a KeyError three calls later.

The validator covers the JSON Schema subset the contract uses: $ref (local), type (one or a
list), const, enum, pattern, minimum, maximum, format (date, uri), properties, required,
additionalProperties, propertyNames, items (a schema or false), prefixItems, minItems, oneOf.
A refreshed contract that uses any other keyword is refused when it loads, so no constraint is
silently skipped. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from bot_ui.emoji import EmojiError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRACT = os.path.join(ROOT, "data", "emoji", "library-contract.json")
ANNOTATIONS = {"description", "examples", "title", "default", "deprecated"}
KEYWORDS = {"$ref", "type", "const", "enum", "pattern", "minimum", "maximum", "format", "properties", "required",
            "additionalProperties", "propertyNames", "items", "prefixItems", "minItems", "oneOf"} | ANNOTATIONS
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_PROBLEMS = 5


class ContractError(EmojiError):
    """An answer outside the vendored contract (CONTRACT_MISMATCH) or a taxonomy this skill does not read
    (TAXONOMY_UNSUPPORTED)."""


_loaded: dict | None = None


def load_contract(path: str | None = None) -> dict:
    """The vendored contract (cached); refuses schemas that use keywords the validator does not check."""
    global _loaded
    if path is None and _loaded is not None:
        return _loaded
    with open(path or CONTRACT, encoding="utf-8") as fh:
        doc = json.load(fh)
    unknown = sorted({k for s in doc["schemas"].values() for k in _keywords(s)} - KEYWORDS)
    if unknown:
        raise ContractError("CONTRACT_UNSUPPORTED", f"the vendored contract uses schema keywords the validator does not "
                                                    f"check: {', '.join(unknown)}")
    if path is None:
        _loaded = doc
    return doc


def _keywords(schema: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(schema, list):
        for s in schema:
            out |= _keywords(s)
    elif isinstance(schema, dict):
        for key, sub in schema.items():
            out.add(key)
            if key == "properties":
                for s in sub.values():
                    out |= _keywords(s)
            elif key in ("additionalProperties", "propertyNames", "items", "prefixItems", "oneOf"):
                out |= _keywords(sub)
    return out


def _type_ok(value: Any, name: str) -> bool:
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, {"string": str, "object": dict, "array": list}[name])


def _short(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 40 else text[:37] + "..."


def problems(value: Any, schema: Any, schemas: dict, path: str = "$") -> list[str]:
    """Every way `value` breaks `schema`, as "<json path>: <what>" (empty: it conforms)."""
    if schema is True:
        return []
    if schema is False:
        return [f"{path}: no value is allowed here"]
    if "$ref" in schema:
        name = schema["$ref"].rsplit("/", 1)[-1]
        return problems(value, schemas[name], schemas, path)
    if "oneOf" in schema:
        branches = [problems(value, s, schemas, path) for s in schema["oneOf"]]
        passing = sum(not b for b in branches)
        if passing == 0:
            return min(branches, key=len)      # the closest shape says best what is wrong
        if passing > 1:
            return [f"{path}: {_short(value)} matches {passing} of the allowed shapes, not one"]
    types = schema.get("type")
    if types is not None:
        types = [types] if isinstance(types, str) else types
        if not any(_type_ok(value, t) for t in types):
            return [f"{path}: expected {' or '.join(types)}, got {_short(value)}"]
    out: list[str] = []
    if "const" in schema and value != schema["const"]:
        out.append(f"{path}: expected {_short(schema['const'])}, got {_short(value)}")
    if "enum" in schema and value not in schema["enum"]:
        out.append(f"{path}: {_short(value)} is not one of {', '.join(map(str, schema['enum']))}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            out.append(f"{path}: {_short(value)} does not match {schema['pattern']}")
        fmt = schema.get("format")
        if (fmt == "date" and not DATE.match(value)) or (fmt == "uri" and not re.match(r"^[a-z][a-z0-9+.-]*:", value)):
            out.append(f"{path}: {_short(value)} is not a {fmt}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            out.append(f"{path}: {value} is below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            out.append(f"{path}: {value} is above {schema['maximum']}")
    if isinstance(value, dict):
        props = schema.get("properties") or {}
        out += [f"{path}: missing {k}" for k in schema.get("required") or [] if k not in value]
        for key, item in value.items():
            if "propertyNames" in schema:
                out += problems(key, schema["propertyNames"], schemas, f"{path} key {key!r}")
            if key in props:
                out += problems(item, props[key], schemas, f"{path}.{key}")
            elif "additionalProperties" in schema:
                out += problems(item, schema["additionalProperties"], schemas, f"{path}.{key}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            out.append(f"{path}: {len(value)} items, at least {schema['minItems']} expected")
        head = schema.get("prefixItems") or []
        for i, item in enumerate(value):
            sub = head[i] if i < len(head) else schema.get("items", True)
            out += problems(item, sub, schemas, f"{path}[{i}]")
            if len(out) > MAX_PROBLEMS * 4:
                break
    return out


def taxonomy_version(doc: Any) -> Any:
    """The taxonomy version an answer declares: `taxonomy` (an integer), or `taxonomy.version` (/api/emoji-facets)."""
    if not isinstance(doc, dict):
        return None
    tax = doc.get("taxonomy")
    return tax.get("version") if isinstance(tax, dict) else tax


def check_taxonomy(version: Any, what: str) -> None:
    understood = load_contract()["taxonomy"]["understood"]
    if isinstance(version, bool) or not isinstance(version, int) or version not in understood:
        raise ContractError("TAXONOMY_UNSUPPORTED",
                            f"{what} uses tag taxonomy {_short(version)}; this skill understands taxonomy "
                            f"{', '.join(map(str, understood))}. Facet values may be renamed in another version, so its tags "
                            "are not read: update the skill, or refresh data/emoji/library-contract.json "
                            "(scripts/emoji_packs.py library contract).")


def check_answer(doc: Any, schema_name: str, what: str) -> Any:
    """`doc` if it carries a taxonomy this skill understands and conforms to the contract's schema; else ContractError."""
    contract = load_contract()
    if taxonomy_version(doc) is not None:
        check_taxonomy(taxonomy_version(doc), what)
    found = problems(doc, contract["schemas"][schema_name], contract["schemas"])
    if found:
        more = f" (+{len(found) - MAX_PROBLEMS} more)" if len(found) > MAX_PROBLEMS else ""
        raise ContractError("CONTRACT_MISMATCH",
                            f"{what} does not match the emoji library contract ({schema_name}, vendored "
                            f"{contract['vendored']} from {contract['source']}): {'; '.join(found[:MAX_PROBLEMS])}{more}")
    return doc


def vendor(openapi: dict, facets: dict, day: str) -> dict:
    """A fresh contract file from a saved OpenAPI document and a saved /api/emoji-facets answer."""
    schemas = dict(openapi["components"]["schemas"])
    if "CatalogLine" in schemas:
        schemas["CatalogLine"] = {k: v for k, v in schemas["CatalogLine"].items() if k != "examples"}
    tax = facets["taxonomy"]
    old = load_contract()
    return {
        "_about": old["_about"], "source": old["source"], "sourceCode": old["sourceCode"], "vendored": day,
        "openapi": openapi["openapi"], "apiVersion": openapi["info"]["version"],
        "catalog": openapi["info"].get("x-catalog-version"),
        "taxonomy": {"understood": [tax["version"]], "version": tax["version"], "generated": facets.get("generated"),
                     "facets": tax["facets"]},
        "thresholds": facets["thresholds"], "schemas": schemas,
    }
