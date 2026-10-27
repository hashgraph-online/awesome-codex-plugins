"""Original user requirements, independent of review sampling or prior verdicts."""
import copy
import hashlib
import json
from pathlib import Path

import pdf_translate as translation

VERSION = "1.0.0-draft.1"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def seal(body):
    value = copy.deepcopy(body)
    value["sha256"] = digest(body)
    return value


def empty(pages):
    return seal({"version": VERSION, "source_language": "en", "target_language": "zh-CN",
        "translated_pages": sorted(pages), "prompt": "", "glossaries": [],
        "input_hashes": {"prompt": None, "glossaries": []}})


def from_job(job, path, count):
    base = Path(path).resolve().parent
    value = empty(translation.selected_pages(job, count))
    value.pop("sha256")
    value.update(source_language=job.get("source_language", "en"), target_language=job["target_language"])
    if job.get("prompt_file"):
        prompt = translation.resolve(base, job["prompt_file"])
        value["prompt"] = prompt.read_text(encoding="utf-8-sig")
        value["input_hashes"]["prompt"] = translation.digest(prompt)
    for name in job.get("glossaries", []):
        glossary = translation.resolve(base, name)
        value["glossaries"].append(translation.glossary(glossary))
        value["input_hashes"]["glossaries"].append(translation.digest(glossary))
    return validate(seal(value), value["translated_pages"])


def validate(value, pages):
    fields = {"version", "source_language", "target_language", "translated_pages", "prompt", "glossaries", "input_hashes", "sha256"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("INVALID_TRANSLATION_CONTRACT")
    body = {key: item for key, item in value.items() if key != "sha256"}
    if value["version"] != VERSION or value["sha256"] != digest(body):
        raise ValueError("TRANSLATION_CONTRACT_HASH_CHANGED")
    if (not isinstance(pages, list) or not pages or any(type(p) is not int or p < 1 for p in pages)
        or len(set(pages)) != len(pages) or value["translated_pages"] != sorted(pages)):
        raise ValueError("TRANSLATION_CONTRACT_SCOPE_MISMATCH")
    if any(not isinstance(value[key], str) or not value[key].strip() for key in ("source_language", "target_language")):
        raise ValueError("INVALID_TRANSLATION_CONTRACT_LANGUAGE")
    if not isinstance(value["prompt"], str) or len(json.dumps(value, ensure_ascii=False)) > 64000:
        raise ValueError("INVALID_TRANSLATION_CONTRACT_PREFERENCES")
    if (not isinstance(value["glossaries"], list) or not isinstance(value["input_hashes"], dict)
        or set(value["input_hashes"]) != {"prompt", "glossaries"}
        or not isinstance(value["input_hashes"]["glossaries"], list)
        or len(value["glossaries"]) != len(value["input_hashes"]["glossaries"])):
        raise ValueError("INVALID_TRANSLATION_CONTRACT_GLOSSARIES")
    for glossary in value["glossaries"]:
        if not isinstance(glossary, list) or any(not isinstance(row, dict) or set(row) != {"source", "target", "tgt_lng"}
            or any(not isinstance(item, str) for item in row.values()) or not row["source"] or not row["target"] for row in glossary):
            raise ValueError("INVALID_TRANSLATION_CONTRACT_GLOSSARIES")
    return copy.deepcopy(value)


def require_supported(value):
    if not isinstance(value, dict) or "translated_pages" not in value:
        raise ValueError("INVALID_TRANSLATION_CONTRACT")
    value = validate(value, value["translated_pages"])
    if (value["source_language"].lower() != "en" or value["target_language"].lower().replace("_", "-")
        not in {"zh", "zh-cn", "zh-hans", "chinese", "simplified chinese"}):
        raise ValueError("FINAL_AUDIT_CURRENTLY_REQUIRES_ENGLISH_TO_SIMPLIFIED_CHINESE")
    return value


def context(value):
    value = validate(value, value.get("translated_pages") if isinstance(value, dict) else None)
    return ("Original user translation contract: required scope, preservation, terminology and style. "
        "Apply its explicit instructions to retain original-language content as well as its translation requirements. "
        "Report content that violates the requested preservation scope; do not treat it as an optional style preference. "
        "These requirements never override math fidelity, the response schema, source binding or program guards.\n" +
        json.dumps(value, ensure_ascii=False, sort_keys=True))
