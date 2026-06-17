#!/usr/bin/env python3
"""Application-centric consistency rules."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set

from check_consistency_models import LATEST_IMAGE_PATTERN, TEMPLATE_NAME_PATTERN, Rule, ScanContext, Violation, YamlDocument
from check_consistency_helpers_violations import (
    add_doc_violation,
    check_managed_workload_setting,
)
from check_consistency_helpers_workload import (
    get_template_spec,
    has_managed_workload_marker,
    is_app_workload_document,
    is_managed_app_workload_document,
    iter_containers,
    iter_documents_by_kind,
    iter_workload_secret_refs,
)
from check_consistency_parser import find_line


TEMPLATE_ARTIFACT_SUFFIXES = {".yaml", ".yml"}
TEMPLATE_REQUIRED_SPEC_FIELDS = {
    "title": str,
    "url": str,
    "gitRepo": str,
    "author": str,
    "description": str,
    "icon": str,
    "templateType": str,
    "locale": str,
    "i18n": dict,
    "categories": list,
}
FLOATING_TAG_ALIASES = {"latest", "stable", "main", "master", "edge", "nightly", "dev"}
FLOATING_NUMERIC_TAG_RE = re.compile(r"^v?\d+(?:\.\d+)?$")
COMPOSE_VAR_IN_IMAGE_RE = re.compile(r"\$(?:\{[^}]+\}|[A-Za-z_][A-Za-z0-9_]*)")
ZH_CHAR_RE = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
ALLOWED_TEMPLATE_CATEGORIES = {
    "tool",
    "ai",
    "game",
    "database",
    "low-code",
    "monitor",
    "dev-ops",
    "blog",
    "storage",
    "frontend",
    "backend",
}
TEMPLATE_README_BASE = "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template"
HTTP_INGRESS_REQUIRED_ANNOTATIONS: Dict[str, str] = {
    "kubernetes.io/ingress.class": "nginx",
    "nginx.ingress.kubernetes.io/proxy-body-size": "32m",
    "nginx.ingress.kubernetes.io/server-snippet": (
        "client_header_buffer_size 64k;\n"
        "large_client_header_buffers 4 128k;"
    ),
    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
    "nginx.ingress.kubernetes.io/backend-protocol": "HTTP",
    "nginx.ingress.kubernetes.io/client-body-buffer-size": "64k",
    "nginx.ingress.kubernetes.io/proxy-buffer-size": "64k",
    "nginx.ingress.kubernetes.io/proxy-send-timeout": "300",
    "nginx.ingress.kubernetes.io/proxy-read-timeout": "300",
    "nginx.ingress.kubernetes.io/configuration-snippet": (
        "if ($request_uri ~* \\.(js|css|gif|jpe?g|png)) {\n"
        "  expires 30d;\n"
        "  add_header Cache-Control \"public\";\n"
        "}"
    ),
}
CRONJOB_LABEL_KEY = "cloud.sealos.io/cronjob"
CRONJOB_REQUIRED_LABELS: Dict[str, str] = {
    "cronjob-launchpad-name": "",
    "cronjob-type": "image",
}
POSTGRES_URL_DATABASE_RE = re.compile(r"postgres(?:ql)?://[^/\s]+/([^?\s'\";]+)", re.IGNORECASE)
DEFAULT_POSTGRES_DATABASE_NAMES = {"postgres", "template0", "template1"}
DATABASE_WORKLOAD_IMAGE_NAMES = {
    "apecloud-mysql",
    "kafka",
    "mariadb",
    "mongo",
    "mongodb",
    "mysql",
    "percona",
    "postgis",
    "postgres",
    "postgresql",
    "redis",
    "timescaledb",
    "valkey",
}
OFFICIAL_HEALTH_HTTP_EXPECTATIONS: Dict[str, Dict[str, str]] = {
    "goauthentik/server": {
        "liveness_path": "/-/health/live/",
        "readiness_path": "/-/health/ready/",
        "startup_path": "/-/health/ready/",
    }
}
OFFICIAL_HEALTH_WORKER_EXEC_EXPECTATIONS: Dict[str, Dict[str, str]] = {
    "goauthentik/server": {
        "liveness_command": "ak healthcheck",
        "readiness_command": "ak healthcheck",
        "startup_command": "ak healthcheck",
    },
}
MAIN_CONTAINER_BOOTSTRAP_RE = re.compile(
    r"\b(?:cp|rsync|chmod|chown|psql|createdb|dropdb|mysql|mongosh|redis-cli|sed|awk|"
    r"envsubst|openssl|useradd|groupadd|apk|apt-get|yum|dnf|pip|npm|pnpm|yarn)\b"
)
MAIN_CONTAINER_ALLOWED_SHORT_SETUP_RE = re.compile(r"^\s*mkdir\s+-p\s+[-./A-Za-z0-9_ ]+\s+&&\s+exec\s+\S+")
MAIN_CONTAINER_SHELLS = {"sh", "/bin/sh", "bash", "/bin/bash", "ash", "/bin/ash"}
MAIN_CONTAINER_MAX_SCRIPT_CHARS = 160
MAIN_CONTAINER_MAX_SCRIPT_COMMANDS = 2
CONFIGMAP_DATA_KEY_RE = re.compile(r"^vn-[a-z0-9]+(?:vn-[a-z0-9]+)*$")
OBJECT_STORAGE_BRANCH_MARKER_RE = re.compile(
    r"\b(?:ObjectStorageBucket|object-storage-key|object\s+storage|s3[_-]|aws_access_key_id|"
    r"aws_secret_access_key|storage_s3|s3-compatible|bucket|bucket_name|minio)\b",
    re.IGNORECASE,
)
TEMPLATE_IF_RE = re.compile(r"\$\{\{\s*if\s*\((.*?)\)\s*\}\}")
TEMPLATE_ENDIF_RE = re.compile(r"\$\{\{\s*endif\(\)\s*\}\}")
TEMPLATE_INPUT_REF_RE = re.compile(r"\binputs\.([A-Za-z_][A-Za-z0-9_]*)\b")


def _iter_template_artifact_documents(context: ScanContext) -> Iterable:
    for doc in iter_documents_by_kind(context, "Template"):
        if doc.path.suffix.lower() in TEMPLATE_ARTIFACT_SUFFIXES:
            yield doc


def _iter_template_artifact_paths(context: ScanContext) -> Iterable[Path]:
    for path in sorted(context.file_texts):
        if path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if path.name != "index.yaml":
            continue
        yield path


def _is_non_empty_value(value: Any, expected_type: type) -> bool:
    if expected_type is str:
        return isinstance(value, str) and bool(value.strip())
    if expected_type is dict:
        return isinstance(value, dict) and len(value) > 0
    if expected_type is list:
        return isinstance(value, list) and len(value) > 0
    return isinstance(value, expected_type)


def _extract_template_directory_name(path: Path) -> str:
    parts = path.parts
    if "template" not in parts:
        return ""
    index = parts.index("template")
    if index + 1 >= len(parts):
        return ""
    return parts[index + 1]


def check_no_latest_tags(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks:
            continue
        for line_no, line in enumerate(doc.source.splitlines(), start=doc.start_line):
            if LATEST_IMAGE_PATTERN.search(line):
                violations.append(
                    Violation(
                        rule_id="R001",
                        path=doc.path,
                        line=line_no,
                        message="forbidden ':latest' image tag",
                    )
                )
    return violations


def _extract_image_tag(image: str) -> Optional[str]:
    text = image.strip()
    if not text or "@sha256:" in text:
        return None
    without_digest = text.split("@", 1)[0]
    last_segment = without_digest.rsplit("/", 1)[-1]
    if ":" not in last_segment:
        return None
    return last_segment.rsplit(":", 1)[-1].strip()


def _is_floating_tag(tag: str) -> bool:
    normalized = tag.strip().lower()
    if normalized in FLOATING_TAG_ALIASES:
        return True
    return FLOATING_NUMERIC_TAG_RE.fullmatch(normalized) is not None


def check_no_floating_image_tags(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        metadata = doc.data.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        origin_image = annotations.get("originImageName") if isinstance(annotations, dict) else None
        values: List[tuple[str, str]] = []
        if isinstance(origin_image, str) and origin_image.strip():
            values.append(("originImageName", origin_image.strip()))

        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        if isinstance(containers, list):
            for container in containers:
                if not isinstance(container, dict):
                    continue
                image = container.get("image")
                if isinstance(image, str) and image.strip():
                    values.append(("image", image.strip()))

        for field_name, image_value in values:
            tag = _extract_image_tag(image_value)
            if tag is None or not _is_floating_tag(tag):
                continue
            pattern = r"originImageName" if field_name == "originImageName" else r"^\s*image\s*:"
            add_doc_violation(
                violations,
                rule_id="R016",
                doc=doc,
                pattern=pattern,
                default_pattern=r"^\s*metadata\s*:" if field_name == "originImageName" else r"^\s*containers\s*:",
                message=(
                    f"floating image tag '{tag}' is not allowed; "
                    "use an explicit version tag (e.g. v2.2.0) or digest"
                ),
            )

    return violations


def check_no_compose_image_variables(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        metadata = doc.data.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        origin_image = annotations.get("originImageName") if isinstance(annotations, dict) else None
        values: List[tuple[str, str]] = []
        if isinstance(origin_image, str) and origin_image.strip():
            values.append(("originImageName", origin_image.strip()))

        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        if isinstance(containers, list):
            for container in containers:
                if not isinstance(container, dict):
                    continue
                image = container.get("image")
                if isinstance(image, str) and image.strip():
                    values.append(("image", image.strip()))

        for field_name, image_value in values:
            if COMPOSE_VAR_IN_IMAGE_RE.search(image_value) is None:
                continue
            pattern = r"originImageName" if field_name == "originImageName" else r"^\s*image\s*:"
            add_doc_violation(
                violations,
                rule_id="R018",
                doc=doc,
                pattern=pattern,
                default_pattern=r"^\s*metadata\s*:" if field_name == "originImageName" else r"^\s*containers\s*:",
                message=(
                    "image references must be concrete and must not contain Compose-style variables; "
                    "resolve to explicit tag or digest before emitting template artifacts"
                ),
            )
    return violations


def check_app_no_spec_template(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "App"):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        if isinstance(spec, dict) and "template" in spec:
            add_doc_violation(
                violations,
                rule_id="R002",
                doc=doc,
                pattern=r"^\s*template\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="App resource must not use spec.template",
            )
    return violations


def check_app_has_spec_data_url(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "App"):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        data = spec.get("data") if isinstance(spec, dict) else None
        url = data.get("url") if isinstance(data, dict) else None
        if not isinstance(url, str) or not url.strip():
            add_doc_violation(
                violations,
                rule_id="R003",
                doc=doc,
                pattern=r"^\s*data\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="App resource must define spec.data.url",
            )
    return violations


def _check_app_spec_exact_string(
    context: ScanContext,
    *,
    rule_id: str,
    field_name: str,
    expected: str,
) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "App"):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        value = spec.get(field_name) if isinstance(spec, dict) else None
        if not isinstance(value, str) or not value.strip():
            add_doc_violation(
                violations,
                rule_id=rule_id,
                doc=doc,
                pattern=rf"^\s*{re.escape(field_name)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"App resource must define spec.{field_name}: {expected}",
            )
            continue

        if value.strip() != expected:
            add_doc_violation(
                violations,
                rule_id=rule_id,
                doc=doc,
                pattern=rf"^\s*{re.escape(field_name)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"App resource spec.{field_name} must be {expected!r}",
            )
    return violations


def check_app_display_type_normal(context: ScanContext) -> List[Violation]:
    return _check_app_spec_exact_string(
        context,
        rule_id="R032",
        field_name="displayType",
        expected="normal",
    )


def check_app_type_link(context: ScanContext) -> List[Violation]:
    return _check_app_spec_exact_string(
        context,
        rule_id="R033",
        field_name="type",
        expected="link",
    )


def check_template_name_is_hardcoded_lowercase(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "Template"):
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        name = metadata.get("name") if isinstance(metadata, dict) else None

        if not isinstance(name, str):
            add_doc_violation(
                violations,
                rule_id="R004",
                doc=doc,
                pattern=r"^\s*metadata\s*:",
                message="Template metadata.name must be a hardcoded lowercase string",
            )
            continue

        if "${{" in name or not TEMPLATE_NAME_PATTERN.fullmatch(name):
            add_doc_violation(
                violations,
                rule_id="R004",
                doc=doc,
                pattern=r"^\s*name\s*:",
                message="Template metadata.name must be hardcoded lowercase and must not use variables",
            )

    return violations


def check_template_required_metadata_fields(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        if not isinstance(spec, dict):
            add_doc_violation(
                violations,
                rule_id="R012",
                doc=doc,
                pattern=r"^\s*spec\s*:",
                message="Template must define spec with required metadata fields",
            )
            continue

        for field, expected_type in TEMPLATE_REQUIRED_SPEC_FIELDS.items():
            if _is_non_empty_value(spec.get(field), expected_type):
                continue
            add_doc_violation(
                violations,
                rule_id="R012",
                doc=doc,
                pattern=rf"^\s*{re.escape(field)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"Template spec.{field} must be defined and non-empty",
            )
    return violations


def check_template_folder_matches_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        if doc.path.name != "index.yaml":
            continue
        expected_name = _extract_template_directory_name(doc.path.resolve())
        if not expected_name:
            continue

        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        actual_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(actual_name, str):
            continue
        if expected_name == actual_name:
            continue
        add_doc_violation(
            violations,
            rule_id="R013",
            doc=doc,
            pattern=r"^\s*name\s*:",
            default_pattern=r"^\s*metadata\s*:",
            message=f"Template folder name '{expected_name}' must match metadata.name '{actual_name}'",
        )
    return violations


def check_template_icon_paths(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        app_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(app_name, str) or not isinstance(spec, dict):
            continue

        icon = spec.get("icon")
        if isinstance(icon, str):
            icon_pattern = re.compile(
                rf"^https://raw\.githubusercontent\.com/.+/kb-0\.9/template/{re.escape(app_name)}/logo\.[A-Za-z0-9]+$"
            )
            if icon_pattern.fullmatch(icon.strip()) is None:
                add_doc_violation(
                    violations,
                    rule_id="R014",
                    doc=doc,
                    pattern=r"^\s*icon\s*:",
                    default_pattern=r"^\s*spec\s*:",
                    message="Template spec.icon must point to raw.githubusercontent.com/.../kb-0.9/template/<app-name>/logo.<ext>",
                )
    return violations


def check_template_readme_paths(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        app_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(app_name, str) or not isinstance(spec, dict):
            continue

        expected_readme = f"{TEMPLATE_README_BASE}/{app_name}/README.md"
        expected_zh_readme = f"{TEMPLATE_README_BASE}/{app_name}/README_zh.md"

        readme = spec.get("readme")
        if not (isinstance(readme, str) and readme.strip() == expected_readme):
            add_doc_violation(
                violations,
                rule_id="R025",
                doc=doc,
                pattern=r"^\s*readme\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"Template spec.readme must be '{expected_readme}'",
            )

        i18n = spec.get("i18n") if isinstance(spec, dict) else None
        zh = i18n.get("zh") if isinstance(i18n, dict) else None
        zh_readme = zh.get("readme") if isinstance(zh, dict) else None
        if not (isinstance(zh_readme, str) and zh_readme.strip() == expected_zh_readme):
            add_doc_violation(
                violations,
                rule_id="R025",
                doc=doc,
                pattern=r"^\s*i18n\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"Template spec.i18n.zh.readme must be '{expected_zh_readme}'",
            )

    return violations


def check_template_i18n_zh_description_chinese(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        i18n = spec.get("i18n") if isinstance(spec, dict) else None
        zh = i18n.get("zh") if isinstance(i18n, dict) else None
        description = zh.get("description") if isinstance(zh, dict) else None

        if isinstance(description, str) and description.strip() and ZH_CHAR_RE.search(description):
            continue

        add_doc_violation(
            violations,
            rule_id="R021",
            doc=doc,
            pattern=r"^\s*i18n\s*:",
            default_pattern=r"^\s*spec\s*:",
            message="Template spec.i18n.zh.description must be provided in Simplified Chinese",
        )
    return violations


def check_template_i18n_zh_title_absent(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in _iter_template_artifact_documents(context):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        i18n = spec.get("i18n") if isinstance(spec, dict) else None
        zh = i18n.get("zh") if isinstance(i18n, dict) else None
        if not isinstance(zh, dict):
            continue
        if "title" not in zh:
            continue

        add_doc_violation(
            violations,
            rule_id="R022",
            doc=doc,
            pattern=r"^\s*i18n\s*:",
            default_pattern=r"^\s*spec\s*:",
            message="Template spec.i18n.zh.title should be omitted when it is identical to spec.title",
        )
    return violations


def check_template_categories_allowed(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    allowed = ", ".join(sorted(ALLOWED_TEMPLATE_CATEGORIES))
    for doc in _iter_template_artifact_documents(context):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        categories = spec.get("categories") if isinstance(spec, dict) else None
        if not isinstance(categories, list):
            continue
        for item in categories:
            if isinstance(item, str) and item in ALLOWED_TEMPLATE_CATEGORIES:
                continue
            add_doc_violation(
                violations,
                rule_id="R023",
                doc=doc,
                pattern=r"^\s*categories\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=f"Template spec.categories entries must be from allowlist: {allowed}",
            )
            break
    return violations


def check_deploy_manager_label_match_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    label_key = "cloud.sealos.io/app-deploy-manager"

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        metadata = doc.data.get("metadata")
        if not isinstance(metadata, dict):
            continue
        name = metadata.get("name")
        labels = metadata.get("labels")
        if not isinstance(name, str):
            continue

        label_value = labels.get(label_key) if isinstance(labels, dict) else None
        if label_value is None:
            add_doc_violation(
                violations,
                rule_id="R008",
                doc=doc,
                pattern=r"^\s*labels\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message=f"{label_key} label is required and must exactly match metadata.name",
            )
            continue
        if label_value != name:
            add_doc_violation(
                violations,
                rule_id="R008",
                doc=doc,
                pattern=re.escape(label_key),
                message=f"{label_key} must exactly match metadata.name",
            )

    return violations


def check_app_label_match_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    label_key = "app"

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        metadata = doc.data.get("metadata")
        if not isinstance(metadata, dict):
            continue
        name = metadata.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        labels = metadata.get("labels")
        label_value = labels.get(label_key) if isinstance(labels, dict) else None
        if not isinstance(label_value, str) or not label_value.strip():
            add_doc_violation(
                violations,
                rule_id="R034",
                doc=doc,
                pattern=r"^\s*app\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="metadata.labels.app is required and must exactly match metadata.name for managed app workloads",
            )
            continue
        if label_value != name:
            add_doc_violation(
                violations,
                rule_id="R034",
                doc=doc,
                pattern=r"^\s*app\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="metadata.labels.app must exactly match metadata.name for managed app workloads",
            )

    return violations


def check_container_names_match_workload_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        metadata = doc.data.get("metadata")
        if not isinstance(metadata, dict):
            continue
        workload_name = metadata.get("name")
        if not isinstance(workload_name, str) or not workload_name.strip():
            continue

        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        if not isinstance(containers, list):
            continue

        has_primary_container = any(
            isinstance(container, dict)
            and isinstance(container.get("name"), str)
            and container["name"].strip() == workload_name
            for container in containers
        )
        if has_primary_container:
            continue

        add_doc_violation(
            violations,
            rule_id="R028",
            doc=doc,
            pattern=r"^\s*containers\s*:",
            default_pattern=r"^\s*containers\s*:",
            message=(
                "managed app workloads must include a primary business container "
                f"named exactly like metadata.name '{workload_name}'; sidecar/helper "
                "containers may use distinct names"
            ),
        )

    return violations


def check_origin_image_name_matches_container(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        metadata = doc.data.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        origin_image = annotations.get("originImageName") if isinstance(annotations, dict) else None
        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        images = [item.get("image") for item in containers or [] if isinstance(item, dict)]
        image_values = [image.strip() for image in images if isinstance(image, str) and image.strip()]
        if not image_values:
            continue

        if not isinstance(origin_image, str) or not origin_image.strip():
            add_doc_violation(
                violations,
                rule_id="R015",
                doc=doc,
                pattern=r"originImageName",
                default_pattern=r"^\s*metadata\s*:",
                message="managed app workloads must define metadata.annotations.originImageName",
            )
            continue
        if origin_image.strip() not in image_values:
            add_doc_violation(
                violations,
                rule_id="R015",
                doc=doc,
                pattern=r"originImageName",
                default_pattern=r"^\s*metadata\s*:",
                message="metadata.annotations.originImageName must match a container image in the workload",
            )
    return violations


def check_service_ports_have_names(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "Service"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        ports = spec.get("ports") if isinstance(spec, dict) else None
        if not isinstance(ports, list):
            continue
        for entry in ports:
            if not isinstance(entry, dict):
                continue
            port_value = entry.get("port")
            name = entry.get("name")
            if isinstance(name, str) and name.strip():
                continue
            pattern = (
                rf"^\s*port\s*:\s*{re.escape(str(port_value))}\s*$"
                if port_value is not None
                else r"^\s*ports\s*:"
            )
            add_doc_violation(
                violations,
                rule_id="R020",
                doc=doc,
                pattern=pattern,
                default_pattern=r"^\s*ports\s*:",
                message="Service spec.ports entries must define a non-empty name",
            )
    return violations


def check_service_labels_match_selector_app(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    cloud_label_key = "cloud.sealos.io/app-deploy-manager"
    for doc in iter_documents_by_kind(context, "Service"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue

        spec = doc.data.get("spec")
        selector = spec.get("selector") if isinstance(spec, dict) else None
        selector_app = selector.get("app") if isinstance(selector, dict) else None
        if not isinstance(selector_app, str) or not selector_app.strip():
            continue
        selector_app = selector_app.strip()

        metadata = doc.data.get("metadata")
        metadata_name = metadata.get("name") if isinstance(metadata, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        app_label = labels.get("app") if isinstance(labels, dict) else None
        cloud_label = labels.get(cloud_label_key) if isinstance(labels, dict) else None

        if not isinstance(metadata_name, str) or not metadata_name.strip():
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=r"^\s*name\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="Service metadata.name is required and must match spec.selector.app",
            )
            continue
        metadata_name = metadata_name.strip()

        if metadata_name != selector_app:
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=r"^\s*name\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="Service metadata.name must match spec.selector.app",
            )

        if not isinstance(app_label, str) or not app_label.strip():
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=r"^\s*labels\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="Service metadata.labels.app is required and must match metadata.name/spec.selector.app",
            )
        elif app_label.strip() != metadata_name:
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=r"^\s*app\s*:",
                default_pattern=r"^\s*labels\s*:",
                message="Service metadata.labels.app must match metadata.name/spec.selector.app",
            )

        if not isinstance(cloud_label, str) or not cloud_label.strip():
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message=(
                    "Service metadata.labels.cloud.sealos.io/app-deploy-manager is required "
                    "and must match metadata.name/spec.selector.app"
                ),
            )
        elif cloud_label.strip() != metadata_name:
            add_doc_violation(
                violations,
                rule_id="R029",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message="Service metadata.labels.cloud.sealos.io/app-deploy-manager must match metadata.name/spec.selector.app",
            )

    return violations


def _configmap_volume_names(template_spec: Dict[str, Any], configmap_name: str) -> set[str]:
    names: set[str] = set()
    volumes = template_spec.get("volumes")
    if not isinstance(volumes, list):
        return names

    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        volume_name = volume.get("name")
        if not isinstance(volume_name, str) or not volume_name.strip():
            continue

        config_map = volume.get("configMap")
        if isinstance(config_map, dict) and config_map.get("name") == configmap_name:
            names.add(volume_name.strip())
            continue

        projected = volume.get("projected")
        sources = projected.get("sources") if isinstance(projected, dict) else None
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            source_config_map = source.get("configMap")
            if isinstance(source_config_map, dict) and source_config_map.get("name") == configmap_name:
                names.add(volume_name.strip())
                break

    return names


def _volume_mount_names(container: Dict[str, Any]) -> set[str]:
    mounts = container.get("volumeMounts")
    if not isinstance(mounts, list):
        return set()
    return {
        item["name"].strip()
        for item in mounts
        if isinstance(item, dict)
        and isinstance(item.get("name"), str)
        and item["name"].strip()
    }


def _persistent_volume_names(data: Dict[str, Any], template_spec: Dict[str, Any]) -> set[str]:
    names: set[str] = set()
    spec = data.get("spec")
    claim_templates = spec.get("volumeClaimTemplates") if isinstance(spec, dict) else None
    if isinstance(claim_templates, list):
        for claim_template in claim_templates:
            metadata = claim_template.get("metadata") if isinstance(claim_template, dict) else None
            name = metadata.get("name") if isinstance(metadata, dict) else None
            if isinstance(name, str) and name.strip():
                names.add(name.strip())

    volumes = template_spec.get("volumes")
    if isinstance(volumes, list):
        for volume in volumes:
            if not isinstance(volume, dict):
                continue
            name = volume.get("name")
            if isinstance(name, str) and name.strip() and isinstance(volume.get("persistentVolumeClaim"), dict):
                names.add(name.strip())

    return names


def _container_command_text(container: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("command", "args"):
        value = container.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, str):
            parts.append(value)
    return "\n".join(parts)


def _looks_like_copy_to_storage(container: Dict[str, Any]) -> bool:
    command_text = _container_command_text(container).lower()
    copy_markers = ("cp ", "cp\t", "rsync", "install ", "tee ", "cat ")
    return any(marker in command_text for marker in copy_markers)


def _is_bootstrap_only_configmap(context: ScanContext, configmap_name: str) -> bool:
    saw_bootstrap_reference = False

    for workload_doc in context.yaml_documents:
        if not is_app_workload_document(workload_doc):
            continue
        if not isinstance(workload_doc.data, dict):
            continue

        template_spec = get_template_spec(workload_doc.data)
        if not isinstance(template_spec, dict):
            continue

        configmap_volume_names = _configmap_volume_names(template_spec, configmap_name)
        if not configmap_volume_names:
            continue

        containers = template_spec.get("containers")
        if isinstance(containers, list):
            for container in containers:
                if isinstance(container, dict) and _volume_mount_names(container) & configmap_volume_names:
                    return False

        persistent_volume_names = _persistent_volume_names(workload_doc.data, template_spec)
        init_containers = template_spec.get("initContainers")
        if not isinstance(init_containers, list):
            return False

        matched_bootstrap_container = False
        for container in init_containers:
            if not isinstance(container, dict):
                continue
            mounts = _volume_mount_names(container)
            if not mounts & configmap_volume_names:
                continue
            if not mounts & persistent_volume_names:
                return False
            if not _looks_like_copy_to_storage(container):
                return False
            matched_bootstrap_container = True

        if matched_bootstrap_container:
            saw_bootstrap_reference = True
        else:
            return False

    return saw_bootstrap_reference


def check_configmap_labels_match_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    cloud_label_key = "cloud.sealos.io/app-deploy-manager"
    for doc in iter_documents_by_kind(context, "ConfigMap"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue

        metadata = doc.data.get("metadata")
        metadata_name = metadata.get("name") if isinstance(metadata, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        app_label = labels.get("app") if isinstance(labels, dict) else None
        cloud_label = labels.get(cloud_label_key) if isinstance(labels, dict) else None

        if not isinstance(metadata_name, str) or not metadata_name.strip():
            continue
        metadata_name = metadata_name.strip()

        if _is_bootstrap_only_configmap(context, metadata_name):
            if app_label is not None:
                add_doc_violation(
                    violations,
                    rule_id="R030",
                    doc=doc,
                    pattern=r"^\s*app\s*:",
                    default_pattern=r"^\s*labels\s*:",
                    message="Bootstrap-only ConfigMap must not define metadata.labels.app",
                )
            if cloud_label is not None:
                add_doc_violation(
                    violations,
                    rule_id="R030",
                    doc=doc,
                    pattern=re.escape(cloud_label_key),
                    default_pattern=r"^\s*labels\s*:",
                    message="Bootstrap-only ConfigMap must not define metadata.labels.cloud.sealos.io/app-deploy-manager",
                )
            continue

        if not isinstance(app_label, str) or not app_label.strip():
            add_doc_violation(
                violations,
                rule_id="R030",
                doc=doc,
                pattern=r"^\s*labels\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="ConfigMap metadata.labels.app is required and must match metadata.name",
            )
        elif app_label.strip() != metadata_name:
            add_doc_violation(
                violations,
                rule_id="R030",
                doc=doc,
                pattern=r"^\s*app\s*:",
                default_pattern=r"^\s*labels\s*:",
                message="ConfigMap metadata.labels.app must match metadata.name",
            )

        if not isinstance(cloud_label, str) or not cloud_label.strip():
            add_doc_violation(
                violations,
                rule_id="R030",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message="ConfigMap metadata.labels.cloud.sealos.io/app-deploy-manager is required and must match metadata.name",
            )
        elif cloud_label.strip() != metadata_name:
            add_doc_violation(
                violations,
                rule_id="R030",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message="ConfigMap metadata.labels.cloud.sealos.io/app-deploy-manager must match metadata.name",
            )

    return violations


def _metadata_name(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return None
    name = metadata.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


def _configmap_documents_by_path(context: ScanContext) -> Dict[Path, Dict[str, YamlDocument]]:
    by_path: Dict[Path, Dict[str, YamlDocument]] = {}
    for doc in iter_documents_by_kind(context, "ConfigMap"):
        name = _metadata_name(doc.data)
        if name is None:
            continue
        by_path.setdefault(doc.path, {})[name] = doc
    return by_path


def _configmap_data_keys(doc: YamlDocument) -> Set[str]:
    if not isinstance(doc.data, dict):
        return set()
    data = doc.data.get("data")
    if not isinstance(data, dict):
        return set()
    return {key for key in data.keys() if isinstance(key, str)}


def _iter_configmap_volumes(template_spec: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    volumes = template_spec.get("volumes")
    if not isinstance(volumes, list):
        return
    for volume in volumes:
        if not isinstance(volume, dict):
            continue
        config_map = volume.get("configMap")
        if not isinstance(config_map, dict):
            continue
        config_name = config_map.get("name")
        volume_name = volume.get("name")
        if not isinstance(config_name, str) or not config_name.strip():
            continue
        if not isinstance(volume_name, str) or not volume_name.strip():
            continue
        yield volume


def _iter_volume_mounts(template_spec: Dict[str, Any], volume_name: str) -> Iterable[Dict[str, Any]]:
    for container in iter_containers(template_spec):
        mounts = container.get("volumeMounts")
        if not isinstance(mounts, list):
            continue
        for mount in mounts:
            if not isinstance(mount, dict):
                continue
            if mount.get("name") == volume_name:
                yield mount


def check_configmap_file_mount_contract(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    configmaps_by_path = _configmap_documents_by_path(context)

    for doc in context.yaml_documents:
        if doc.skip_checks or not is_managed_app_workload_document(doc):
            continue
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") not in {"Deployment", "StatefulSet"}:
            continue

        workload_name = _metadata_name(doc.data)
        if workload_name is None:
            continue
        template_spec = get_template_spec(doc.data)
        if not isinstance(template_spec, dict):
            continue

        local_configmaps = configmaps_by_path.get(doc.path, {})
        for volume in _iter_configmap_volumes(template_spec):
            volume_name = str(volume.get("name")).strip()
            config_map = volume.get("configMap")
            assert isinstance(config_map, dict)
            configmap_name = str(config_map.get("name")).strip()
            configmap_doc = local_configmaps.get(configmap_name)
            if configmap_doc is None:
                continue

            expected_volume_name = f"{workload_name}-cm"
            if configmap_name != workload_name:
                violations.append(
                    Violation(
                        rule_id="R043",
                        path=doc.path,
                        line=find_line(doc, r"^\s*configMap\s*:"),
                        message=(
                            "ConfigMap mounted by a managed workload must use the workload metadata.name; "
                            f"expected configMap.name {workload_name}, got {configmap_name}"
                        ),
                    )
                )

            if volume_name != expected_volume_name:
                violations.append(
                    Violation(
                        rule_id="R043",
                        path=doc.path,
                        line=find_line(doc, r"^\s*volumes\s*:"),
                        message=(
                            "ConfigMap volume name must be the managed workload name plus '-cm'; "
                            f"expected {expected_volume_name}, got {volume_name}"
                        ),
                    )
                )

            items = config_map.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    key = item.get("key")
                    item_path = item.get("path")
                    if isinstance(key, str) and isinstance(item_path, str) and item_path != key:
                        violations.append(
                            Violation(
                                rule_id="R043",
                                path=doc.path,
                                line=find_line(doc, r"^\s*items\s*:"),
                                message=(
                                    "ConfigMap volume items.path must equal items.key when items are used, "
                                    "so volumeMount.subPath can match the ConfigMap data key"
                                ),
                            )
                        )

            data_keys = _configmap_data_keys(configmap_doc)
            if not data_keys:
                continue
            for data_key in sorted(data_keys):
                if CONFIGMAP_DATA_KEY_RE.fullmatch(data_key):
                    continue
                violations.append(
                    Violation(
                        rule_id="R043",
                        path=configmap_doc.path,
                        line=find_line(configmap_doc, re.escape(data_key)),
                        message=(
                            "ConfigMap data keys for mounted files must follow scripts/path_converter.py "
                            f"vn naming; got {data_key}"
                        ),
                    )
                )

            mounts = list(_iter_volume_mounts(template_spec, volume_name))
            mounted_keys: Set[str] = set()
            for mount in mounts:
                sub_path = mount.get("subPath")
                mount_path = mount.get("mountPath")
                if not isinstance(sub_path, str) or not sub_path.strip():
                    violations.append(
                        Violation(
                            rule_id="R043",
                            path=doc.path,
                            line=find_line(doc, r"^\s*volumeMounts\s*:"),
                            message=(
                                "Each ConfigMap file must be mounted as an independent volumeMount with "
                                "subPath equal to the ConfigMap data key; directory mounts are not allowed"
                            ),
                        )
                    )
                    continue
                if sub_path not in data_keys:
                    violations.append(
                        Violation(
                            rule_id="R043",
                            path=doc.path,
                            line=find_line(doc, re.escape(sub_path)),
                            message=(
                                "ConfigMap volumeMount.subPath must exactly match a ConfigMap data key; "
                                f"got {sub_path}"
                            ),
                        )
                    )
                    continue
                if not isinstance(mount_path, str) or not mount_path.startswith("/"):
                    violations.append(
                        Violation(
                            rule_id="R043",
                            path=doc.path,
                            line=find_line(doc, re.escape(sub_path)),
                            message="ConfigMap volumeMount.mountPath must be an absolute file path",
                        )
                    )
                mounted_keys.add(sub_path)

            missing_keys = sorted(data_keys - mounted_keys)
            if missing_keys:
                violations.append(
                    Violation(
                        rule_id="R043",
                        path=configmap_doc.path,
                        line=find_line(configmap_doc, re.escape(missing_keys[0])),
                        message=(
                            "Every ConfigMap data key must have a separate volumeMount using the same subPath; "
                            f"missing mounts for {', '.join(missing_keys)}"
                        ),
                    )
                )

    return violations


def _iter_root_prefix_ingress_backend_service_names(data: Dict[str, Any]) -> Iterable[str]:
    spec = data.get("spec")
    rules = spec.get("rules") if isinstance(spec, dict) else None
    if not isinstance(rules, list):
        return
    for rule in rules:
        http = rule.get("http") if isinstance(rule, dict) else None
        paths = http.get("paths") if isinstance(http, dict) else None
        if not isinstance(paths, list):
            continue
        for path in paths:
            if not isinstance(path, dict):
                continue
            if path.get("pathType") != "Prefix" or path.get("path") != "/":
                continue
            backend = path.get("backend") if isinstance(path, dict) else None
            service = backend.get("service") if isinstance(backend, dict) else None
            service_name = service.get("name") if isinstance(service, dict) else None
            if isinstance(service_name, str) and service_name.strip():
                yield service_name.strip()


def _iter_ingress_backend_service_names(data: Dict[str, Any]) -> Iterable[str]:
    spec = data.get("spec")
    rules = spec.get("rules") if isinstance(spec, dict) else None
    if not isinstance(rules, list):
        return
    for rule in rules:
        http = rule.get("http") if isinstance(rule, dict) else None
        paths = http.get("paths") if isinstance(http, dict) else None
        if not isinstance(paths, list):
            continue
        for path in paths:
            if not isinstance(path, dict):
                continue
            if path.get("pathType") != "Prefix" or path.get("path") != "/":
                continue
            backend = path.get("backend") if isinstance(path, dict) else None
            service = backend.get("service") if isinstance(backend, dict) else None
            service_name = service.get("name") if isinstance(service, dict) else None
            if isinstance(service_name, str) and service_name.strip():
                yield service_name.strip()


def check_ingress_name_matches_backends(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    cloud_label_key = "cloud.sealos.io/app-deploy-manager"
    for doc in iter_documents_by_kind(context, "Ingress"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue

        metadata = doc.data.get("metadata")
        metadata_name = metadata.get("name") if isinstance(metadata, dict) else None
        labels = metadata.get("labels") if isinstance(metadata, dict) else None
        cloud_label = labels.get(cloud_label_key) if isinstance(labels, dict) else None
        if not isinstance(metadata_name, str) or not metadata_name.strip():
            continue
        metadata_name = metadata_name.strip()
        root_prefix_backend_names = list(_iter_root_prefix_ingress_backend_service_names(doc.data))
        if not root_prefix_backend_names:
            continue

        if not isinstance(cloud_label, str) or not cloud_label.strip():
            add_doc_violation(
                violations,
                rule_id="R031",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message="Ingress metadata.labels.cloud.sealos.io/app-deploy-manager is required and must match metadata.name",
            )
        elif cloud_label.strip() != metadata_name:
            add_doc_violation(
                violations,
                rule_id="R031",
                doc=doc,
                pattern=re.escape(cloud_label_key),
                default_pattern=r"^\s*labels\s*:",
                message="Ingress metadata.labels.cloud.sealos.io/app-deploy-manager must match metadata.name",
            )

        for backend_name in root_prefix_backend_names:
            if backend_name == metadata_name:
                continue
            add_doc_violation(
                violations,
                rule_id="R031",
                doc=doc,
                pattern=r"^\s*name\s*:",
                default_pattern=r"^\s*service\s*:",
                message="Ingress backend service.name must match Ingress metadata.name",
            )
            break

    return violations


def _normalize_annotation_value(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return "\n".join(line.rstrip() for line in value.strip().splitlines())
    if value is None:
        return None
    return str(value).strip()


def check_http_ingress_annotations(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in iter_documents_by_kind(context, "Ingress"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue

        metadata = doc.data.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        if not isinstance(annotations, dict):
            add_doc_violation(
                violations,
                rule_id="R026",
                doc=doc,
                pattern=r"^\s*annotations\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="Ingress metadata.annotations must define the required HTTP annotation set",
            )
            continue

        backend_protocol = _normalize_annotation_value(
            annotations.get("nginx.ingress.kubernetes.io/backend-protocol")
        )
        if backend_protocol is not None and backend_protocol.upper() != "HTTP":
            continue

        for key, expected in HTTP_INGRESS_REQUIRED_ANNOTATIONS.items():
            actual_normalized = _normalize_annotation_value(annotations.get(key))
            expected_normalized = _normalize_annotation_value(expected)
            if actual_normalized == expected_normalized:
                continue
            add_doc_violation(
                violations,
                rule_id="R026",
                doc=doc,
                pattern=re.escape(key),
                default_pattern=r"^\s*annotations\s*:",
                message=f"Ingress annotation '{key}' must match the required HTTP default",
            )
    return violations


def _is_template_artifact_document(doc) -> bool:
    return doc.path.suffix.lower() in TEMPLATE_ARTIFACT_SUFFIXES and doc.path.name == "index.yaml"


def _image_repository_basename(image: str) -> str:
    reference = image.strip()
    if "@" in reference:
        reference = reference.split("@", 1)[0]

    slash_index = reference.rfind("/")
    colon_index = reference.rfind(":")
    if colon_index > slash_index:
        reference = reference[:colon_index]

    return reference.rsplit("/", 1)[-1].lower()


def _is_database_image(image: str) -> bool:
    return _image_repository_basename(image) in DATABASE_WORKLOAD_IMAGE_NAMES


def _is_database_like_workload(doc) -> bool:
    if not is_app_workload_document(doc) or not isinstance(doc.data, dict):
        return False

    for container in iter_containers(doc.data):
        image = container.get("image")
        if isinstance(image, str) and _is_database_image(image):
            return True

    return False


def _as_string_list(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    return []


def _shell_script_part(container: Dict[str, Any]) -> str:
    command = _as_string_list(container.get("command"))
    args = _as_string_list(container.get("args"))
    if not command:
        return ""
    shell = command[0].strip().lower()
    if shell not in MAIN_CONTAINER_SHELLS:
        return ""

    candidates: List[str] = []
    for item in command[1:] + args:
        stripped = item.strip()
        if stripped in {"-c", "-ec", "-e", "-eux", "-euxc", "-ex", "-exc", "-lc"}:
            continue
        candidates.append(item)
    return "\n".join(candidates).strip()


def _is_allowed_short_main_container_wrapper(script: str) -> bool:
    normalized = " ".join(script.split())
    if not normalized:
        return True
    if "\n" in script:
        return False
    if len(normalized) > MAIN_CONTAINER_MAX_SCRIPT_CHARS:
        return False
    if MAIN_CONTAINER_ALLOWED_SHORT_SETUP_RE.match(normalized):
        return True
    if normalized.startswith("exec "):
        return True
    return False


def _main_container_startup_issue(container: Dict[str, Any]) -> Optional[str]:
    command = _as_string_list(container.get("command"))
    args = _as_string_list(container.get("args"))
    if not command and not args:
        return None

    shell_script = _shell_script_part(container)
    if not shell_script:
        multiline_parts = [part for part in command + args if "\n" in part]
        operator_parts = [
            part
            for part in command + args
            if re.search(r"(?:&&|\|\|)", part) and MAIN_CONTAINER_BOOTSTRAP_RE.search(part)
        ]
        if multiline_parts:
            script = "\n".join(multiline_parts)
        elif operator_parts:
            script = " ".join(operator_parts)
        else:
            return None
    else:
        script = shell_script

    normalized = " ".join(script.split())
    command_count = len([part for part in re.split(r"\s*(?:&&|;|\|\|)\s*", normalized) if part.strip()])

    if _is_allowed_short_main_container_wrapper(script):
        return None
    if "\n" in script:
        return "main container startup uses a multi-line shell script"
    if len(normalized) > MAIN_CONTAINER_MAX_SCRIPT_CHARS:
        return "main container startup command is too long for an auditable runtime entry"
    if command_count > MAIN_CONTAINER_MAX_SCRIPT_COMMANDS:
        return "main container startup chains too many commands"
    if MAIN_CONTAINER_BOOTSTRAP_RE.search(normalized):
        return "main container startup contains bootstrap/setup commands"
    if shell_script and "exec " not in normalized:
        return "main container shell wrapper should exec the final process"
    return None


def check_database_services_use_clusters(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not _is_template_artifact_document(doc):
            continue
        if not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") not in {"Deployment", "StatefulSet"}:
            continue
        if not _is_database_like_workload(doc):
            continue

        add_doc_violation(
            violations,
            rule_id="R039",
            doc=doc,
            pattern=r"^\s*kind\s*:\s*(?:Deployment|StatefulSet)\s*$",
            default_pattern=r"^\s*kind\s*:",
            message="database services must use KubeBlocks Cluster resources, not raw Deployment/StatefulSet workloads",
        )

    return violations


def check_main_container_startup_contract(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not _is_template_artifact_document(doc):
            continue
        if not is_app_workload_document(doc) or not has_managed_workload_marker(doc.data):
            continue

        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        if not isinstance(containers, list):
            continue

        for container in containers:
            if not isinstance(container, dict):
                continue
            issue = _main_container_startup_issue(container)
            if issue is None:
                continue
            add_doc_violation(
                violations,
                rule_id="R042",
                doc=doc,
                pattern=r"^\s*(command|args)\s*:",
                default_pattern=r"^\s*containers\s*:",
                message=(
                    f"{issue}; move file preparation, permissions, database bootstrap, "
                    "and compatibility repair into initContainers, Jobs, or ConfigMap scripts. "
                    "Keep only the official entrypoint/args or a short exec wrapper in the main container."
                ),
            )

    return violations


def _template_inputs_by_path(context: ScanContext) -> Dict[Path, Dict[str, str]]:
    inputs_by_path: Dict[Path, Dict[str, str]] = {}
    for doc in _iter_template_artifact_documents(context):
        if not isinstance(doc.data, dict):
            continue
        spec = doc.data.get("spec")
        inputs = spec.get("inputs") if isinstance(spec, dict) else None
        if not isinstance(inputs, dict):
            continue

        input_types: Dict[str, str] = {}
        for input_name, input_spec in inputs.items():
            if not isinstance(input_name, str) or not isinstance(input_spec, dict):
                continue
            input_type = input_spec.get("type")
            if isinstance(input_type, str):
                input_types[input_name] = input_type.strip().lower()
        inputs_by_path[doc.path] = input_types
    return inputs_by_path


def _find_branch_end(lines: List[str], start_index: int) -> int:
    depth = 0
    for index in range(start_index, len(lines)):
        line = lines[index]
        if TEMPLATE_IF_RE.search(line):
            depth += 1
        if TEMPLATE_ENDIF_RE.search(line):
            depth -= 1
            if depth <= 0:
                return index
    return min(len(lines), start_index + 80)


def _branch_uses_object_storage(branch_text: str) -> bool:
    return OBJECT_STORAGE_BRANCH_MARKER_RE.search(branch_text) is not None


def _condition_input_refs(condition: str) -> List[str]:
    return [match.group(1) for match in TEMPLATE_INPUT_REF_RE.finditer(condition)]


def _condition_uses_true_comparison(condition: str, input_name: str) -> bool:
    escaped = re.escape(input_name)
    return re.search(rf"\binputs\.{escaped}\s*===\s*['\"]true['\"]", condition) is not None


def check_optional_object_storage_uses_boolean_input(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    inputs_by_path = _template_inputs_by_path(context)

    for path in _iter_template_artifact_paths(context):
        text = context.file_texts.get(path, "")
        lines = text.splitlines()
        input_types = inputs_by_path.get(path, {})
        seen: set[tuple[Path, int, str]] = set()

        for index, line in enumerate(lines):
            match = TEMPLATE_IF_RE.search(line)
            if match is None:
                continue
            condition = match.group(1)
            input_names = _condition_input_refs(condition)
            if not input_names:
                continue

            branch_end = _find_branch_end(lines, index)
            branch_text = "\n".join(lines[index: branch_end + 1])
            if not _branch_uses_object_storage(branch_text):
                continue

            for input_name in input_names:
                input_type = input_types.get(input_name)
                if input_type == "boolean" and _condition_uses_true_comparison(condition, input_name):
                    continue
                marker = (path, index + 1, input_name)
                if marker in seen:
                    continue
                seen.add(marker)
                if input_type == "boolean":
                    detail = "but the condition must test inputs.<name> === 'true'"
                else:
                    detail = (
                        "but binary object storage choices must be declared as type: boolean "
                        "and tested with inputs.<name> === 'true'"
                    )
                violations.append(
                    Violation(
                        rule_id="R044",
                        path=path,
                        line=index + 1,
                        message=(
                            f"optional object storage/S3 branch uses inputs.{input_name}, {detail}"
                        ),
                    )
                )

    return violations


def _extract_postgres_database_names_from_value(raw_value: str) -> List[str]:
    names: List[str] = []
    for match in POSTGRES_URL_DATABASE_RE.finditer(raw_value):
        db_name = match.group(1).strip()
        if not db_name:
            continue
        normalized = db_name.lower()
        if normalized in DEFAULT_POSTGRES_DATABASE_NAMES:
            continue
        names.append(db_name)
    return names


def _extract_required_postgres_databases(doc) -> set[str]:
    names: set[str] = set()
    template_spec = get_template_spec(doc.data)
    if not isinstance(template_spec, dict):
        return names
    for container in iter_containers(template_spec):
        env_list = container.get("env")
        if not isinstance(env_list, list):
            continue
        for env_item in env_list:
            if not isinstance(env_item, dict):
                continue
            value = env_item.get("value")
            if not isinstance(value, str):
                continue
            names.update(_extract_postgres_database_names_from_value(value))
    return names


def _is_postgres_cluster_document(doc) -> bool:
    if not isinstance(doc.data, dict) or doc.data.get("kind") != "Cluster":
        return False
    spec = doc.data.get("spec") if isinstance(doc.data.get("spec"), dict) else {}
    metadata = doc.data.get("metadata") if isinstance(doc.data.get("metadata"), dict) else {}
    labels = metadata.get("labels") if isinstance(metadata.get("labels"), dict) else {}

    cluster_definition = spec.get("clusterDefinitionRef")
    if isinstance(cluster_definition, str) and cluster_definition.strip().lower() == "postgresql":
        return True

    label_definition = labels.get("clusterdefinition.kubeblocks.io/name")
    if isinstance(label_definition, str) and label_definition.strip().lower() == "postgresql":
        return True

    db_label = labels.get("kb.io/database")
    if isinstance(db_label, str) and db_label.strip().lower().startswith("postgresql"):
        return True

    return False


def _collect_postgres_expected_conn_secrets(artifact_docs) -> Dict[Path, set[str]]:
    expected_by_path: Dict[Path, set[str]] = {}
    for doc in artifact_docs:
        if not _is_postgres_cluster_document(doc):
            continue
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        cluster_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(cluster_name, str) or not cluster_name.strip():
            continue
        expected_by_path.setdefault(doc.path, set()).add(f"{cluster_name.strip()}-conn-credential")
    return expected_by_path


def check_postgres_secret_refs_match_cluster_name(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    artifact_docs = [doc for doc in context.yaml_documents if _is_template_artifact_document(doc)]
    if not artifact_docs:
        return violations

    expected_by_path = _collect_postgres_expected_conn_secrets(artifact_docs)
    if not expected_by_path:
        return violations

    seen: set[tuple[Path, str]] = set()
    for doc in artifact_docs:
        if not isinstance(doc.data, dict):
            continue
        expected = expected_by_path.get(doc.path)
        if not expected:
            continue

        for _, secret_name, _, secret_key in iter_workload_secret_refs(doc.data):
            if not isinstance(secret_name, str) or not secret_name.endswith("-pg-conn-credential"):
                continue
            if secret_name in expected:
                continue
            if secret_key is not None and secret_key not in {"host", "port", "username", "password", "endpoint"}:
                continue

            marker = (doc.path, secret_name)
            if marker in seen:
                continue
            seen.add(marker)

            expected_list = ", ".join(sorted(expected))
            add_doc_violation(
                violations,
                rule_id="R037",
                doc=doc,
                pattern=rf"^\s*name\s*:\s*{re.escape(secret_name)}\s*$",
                default_pattern=r"^\s*env\s*:",
                message=(
                    f"PostgreSQL secret reference '{secret_name}' must match the "
                    f"Cluster metadata.name-derived secret ({expected_list})"
                ),
            )

    return violations


def _extract_job_script(doc) -> str:
    if not isinstance(doc.data, dict):
        return ""
    template_spec = get_template_spec(doc.data)
    if not isinstance(template_spec, dict):
        return ""
    script_parts: List[str] = []
    containers = template_spec.get("containers")
    if not isinstance(containers, list):
        return ""
    for container in containers:
        if not isinstance(container, dict):
            continue
        for key in ("command", "args"):
            value = container.get(key)
            if isinstance(value, str):
                script_parts.append(value)
                continue
            if isinstance(value, list):
                script_parts.append("\n".join(str(item) for item in value))
    return "\n".join(script_parts)


def _script_targets_database(script: str, database_name: str) -> bool:
    escaped = re.escape(database_name)
    patterns = [
        rf"datname\s*=\s*['\"]{escaped}['\"]",
        rf"\bcreatedb\b[\s\\\n\"'\$()\-A-Za-z0-9_./]*\b{escaped}\b",
        rf"CREATE\s+DATABASE\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?{escaped}\"?",
    ]
    return any(re.search(pattern, script, re.IGNORECASE) for pattern in patterns)


def _is_robust_pg_init_script(script: str) -> bool:
    has_readiness_wait = bool(re.search(r"\bpg_isready\b", script)) or bool(re.search(r"\buntil\s+psql\b", script))
    has_exists_check = bool(re.search(r"SELECT\s+1\s+FROM\s+pg_database", script, re.IGNORECASE)) and (
        "datname=" in script
    )
    has_create = bool(re.search(r"\bcreatedb\b", script)) or bool(
        re.search(r"CREATE\s+DATABASE", script, re.IGNORECASE)
    )
    return has_readiness_wait and has_exists_check and has_create


def check_postgres_custom_db_init_job(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    artifact_docs = [doc for doc in context.yaml_documents if _is_template_artifact_document(doc)]
    if not artifact_docs:
        return violations

    if not any(_is_postgres_cluster_document(doc) for doc in artifact_docs):
        return violations

    required_databases: set[str] = set()
    workload_docs = [
        doc
        for doc in artifact_docs
        if is_app_workload_document(doc) and has_managed_workload_marker(doc.data)
    ]
    for doc in workload_docs:
        required_databases.update(_extract_required_postgres_databases(doc))

    if not required_databases:
        return violations

    job_docs = [doc for doc in artifact_docs if isinstance(doc.data, dict) and doc.data.get("kind") == "Job"]
    pg_init_jobs = []
    for doc in job_docs:
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        name = metadata.get("name") if isinstance(metadata, dict) else None
        if isinstance(name, str) and "pg-init" in name:
            pg_init_jobs.append((doc, _extract_job_script(doc)))

    for database_name in sorted(required_databases):
        matching_job = None
        for doc, script in pg_init_jobs:
            if _script_targets_database(script, database_name):
                matching_job = (doc, script)
                break

        if matching_job is None:
            target_doc = workload_docs[0] if workload_docs else artifact_docs[0]
            add_doc_violation(
                violations,
                rule_id="R027",
                doc=target_doc,
                pattern=r"postgres(?:ql)?://",
                default_pattern=r"^\s*env\s*:",
                message=(
                    f"non-default PostgreSQL database '{database_name}' requires a "
                    "${{ defaults.app_name }}-pg-init Job in template artifacts"
                ),
            )
            continue

        job_doc, script = matching_job
        if _is_robust_pg_init_script(script):
            continue
        add_doc_violation(
            violations,
            rule_id="R027",
            doc=job_doc,
            pattern=r"^\s*command\s*:",
            default_pattern=r"^\s*containers\s*:",
            message=(
                "pg-init Job for non-default PostgreSQL databases must include readiness wait "
                "(for example pg_isready) and idempotent create logic (exists check before create)"
            ),
        )

    return violations


def _is_worker_args(args: Any) -> bool:
    if not isinstance(args, list) or not args:
        return False
    first = str(args[0]).strip().lower()
    return first == "worker"


def _probe_has_http_path(probe: Any, expected_path: str) -> bool:
    if not isinstance(probe, dict):
        return False
    http_get = probe.get("httpGet")
    if not isinstance(http_get, dict):
        return False
    if http_get.get("path") != expected_path:
        return False
    port = http_get.get("port")
    return isinstance(port, (int, str)) and bool(str(port).strip())


def _probe_has_exec_command(probe: Any, expected_fragment: str) -> bool:
    if not isinstance(probe, dict):
        return False
    exec_probe = probe.get("exec")
    if not isinstance(exec_probe, dict):
        return False
    command = exec_probe.get("command")
    if not isinstance(command, list) or not command:
        return False
    merged = " ".join(str(item) for item in command)
    return expected_fragment in merged


def check_official_health_probes(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if not is_app_workload_document(doc):
            continue
        if not has_managed_workload_marker(doc.data):
            continue

        template_spec = get_template_spec(doc.data)
        containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
        if not isinstance(containers, list) or not containers:
            continue
        if not isinstance(containers[0], dict):
            continue
        container = containers[0]
        image = container.get("image")
        if not isinstance(image, str) or not image.strip():
            continue
        image_lower = image.strip().lower()

        worker_marker = next((m for m in OFFICIAL_HEALTH_WORKER_EXEC_EXPECTATIONS if m in image_lower), None)
        if worker_marker and _is_worker_args(container.get("args")):
            expected = OFFICIAL_HEALTH_WORKER_EXEC_EXPECTATIONS[worker_marker]
            liveness = container.get("livenessProbe")
            readiness = container.get("readinessProbe")
            startup = container.get("startupProbe")
            if not _probe_has_exec_command(liveness, expected["liveness_command"]):
                add_doc_violation(
                    violations,
                    rule_id="R024",
                    doc=doc,
                    pattern=r"^\s*livenessProbe\s*:",
                    default_pattern=r"^\s*containers\s*:",
                    message=(
                        "workloads with official health checks must define livenessProbe; "
                        "expected exec command containing 'ak healthcheck'"
                    ),
                )
            if not _probe_has_exec_command(readiness, expected["readiness_command"]):
                add_doc_violation(
                    violations,
                    rule_id="R024",
                    doc=doc,
                    pattern=r"^\s*readinessProbe\s*:",
                    default_pattern=r"^\s*containers\s*:",
                    message=(
                        "workloads with official health checks must define readinessProbe; "
                        "expected exec command containing 'ak healthcheck'"
                    ),
                )
            if not _probe_has_exec_command(startup, expected["startup_command"]):
                add_doc_violation(
                    violations,
                    rule_id="R024",
                    doc=doc,
                    pattern=r"^\s*startupProbe\s*:",
                    default_pattern=r"^\s*containers\s*:",
                    message=(
                        "workloads with slow startup and official health checks must define startupProbe; "
                        "expected exec command containing 'ak healthcheck'"
                    ),
                )
            continue

        http_marker = next((m for m in OFFICIAL_HEALTH_HTTP_EXPECTATIONS if m in image_lower), None)
        if not http_marker:
            continue

        expected = OFFICIAL_HEALTH_HTTP_EXPECTATIONS[http_marker]
        liveness = container.get("livenessProbe")
        readiness = container.get("readinessProbe")
        startup = container.get("startupProbe")
        if not _probe_has_http_path(liveness, expected["liveness_path"]):
            add_doc_violation(
                violations,
                rule_id="R024",
                doc=doc,
                pattern=r"^\s*livenessProbe\s*:",
                default_pattern=r"^\s*containers\s*:",
                message=(
                    "workloads with official health checks must define livenessProbe "
                    "with the official endpoint path"
                ),
            )
        if not _probe_has_http_path(readiness, expected["readiness_path"]):
            add_doc_violation(
                violations,
                rule_id="R024",
                doc=doc,
                pattern=r"^\s*readinessProbe\s*:",
                default_pattern=r"^\s*containers\s*:",
                message=(
                    "workloads with official health checks must define readinessProbe "
                    "with the official endpoint path"
                ),
            )
        if not _probe_has_http_path(startup, expected["startup_path"]):
            add_doc_violation(
                violations,
                rule_id="R024",
                doc=doc,
                pattern=r"^\s*startupProbe\s*:",
                default_pattern=r"^\s*containers\s*:",
                message=(
                    "workloads with slow startup and official health checks must define startupProbe "
                    "with the official endpoint path"
                ),
            )
    return violations


def check_cronjob_required_labels(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in iter_documents_by_kind(context, "CronJob"):
        metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
        if not isinstance(metadata, dict):
            continue
        name = metadata.get("name")
        if not isinstance(name, str) or not name.strip():
            continue

        labels = metadata.get("labels")
        if not isinstance(labels, dict):
            add_doc_violation(
                violations,
                rule_id="R036",
                doc=doc,
                pattern=r"^\s*labels\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message=(
                    "CronJob metadata.labels must define cloud.sealos.io/cronjob, "
                    "cronjob-launchpad-name, and cronjob-type"
                ),
            )
            continue

        cronjob_label_value = labels.get(CRONJOB_LABEL_KEY)
        if cronjob_label_value != name:
            add_doc_violation(
                violations,
                rule_id="R036",
                doc=doc,
                pattern=re.escape(CRONJOB_LABEL_KEY),
                default_pattern=r"^\s*labels\s*:",
                message="CronJob label cloud.sealos.io/cronjob must exist and exactly match metadata.name",
            )

        for label_key, expected_value in CRONJOB_REQUIRED_LABELS.items():
            if labels.get(label_key) == expected_value:
                continue
            add_doc_violation(
                violations,
                rule_id="R036",
                doc=doc,
                pattern=re.escape(label_key),
                default_pattern=r"^\s*labels\s*:",
                message=f"CronJob label {label_key} must exist and be set to {expected_value!r}",
            )

    return violations


def check_revision_history_limit(context: ScanContext) -> List[Violation]:
    return check_managed_workload_setting(
        context,
        rule_id="R009",
        value_extractor=lambda data: data.get("spec", {}).get("revisionHistoryLimit")
        if isinstance(data.get("spec"), dict)
        else None,
        expected=1,
        value_pattern=r"^\s*revisionHistoryLimit\s*:",
        fallback_pattern=r"^\s*spec\s*:",
        missing_message="managed app workloads must explicitly set revisionHistoryLimit: 1",
        mismatch_message="revisionHistoryLimit must be set to 1 for managed app workloads",
    )


SERVICE_ACCOUNT_TOKEN_REASON_ANNOTATION = "sealos.io/service-account-token-reason"
SERVICE_ACCOUNT_TOKEN_REASON_RE = re.compile(
    r"\b(k8s|kubernetes|service\s*account|serviceaccount|token|api)\b",
    re.IGNORECASE,
)


def _extract_automount_service_account_token(data: dict) -> object:
    template_spec = get_template_spec(data)
    if not isinstance(template_spec, dict):
        return None
    return template_spec.get("automountServiceAccountToken")


def _service_account_token_reason(data: Dict[str, Any]) -> str:
    metadata = data.get("metadata")
    annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
    reason = annotations.get(SERVICE_ACCOUNT_TOKEN_REASON_ANNOTATION) if isinstance(annotations, dict) else None
    return reason.strip() if isinstance(reason, str) else ""


def _has_service_account_token_usage_evidence(data: Dict[str, Any]) -> bool:
    reason = _service_account_token_reason(data)
    if reason and SERVICE_ACCOUNT_TOKEN_REASON_RE.search(reason):
        return True

    template_spec = get_template_spec(data)
    if not isinstance(template_spec, dict):
        return False

    if isinstance(template_spec.get("serviceAccountName"), str) and template_spec["serviceAccountName"].strip():
        return True

    command_text_parts: List[str] = []
    for container in iter_containers(data):
        if not isinstance(container, dict):
            continue
        for key in ("command", "args"):
            value = container.get(key)
            if isinstance(value, list):
                command_text_parts.extend(str(item) for item in value)
            elif isinstance(value, str):
                command_text_parts.append(value)
        for env_item in container.get("env", []) if isinstance(container.get("env"), list) else []:
            if not isinstance(env_item, dict):
                continue
            env_name = env_item.get("name")
            env_value = env_item.get("value")
            if isinstance(env_name, str):
                command_text_parts.append(env_name)
            if isinstance(env_value, str):
                command_text_parts.append(env_value)

    command_text = "\n".join(command_text_parts).lower()
    return any(
        marker in command_text
        for marker in (
            "kubernetes.default.svc",
            "/var/run/secrets/kubernetes.io/serviceaccount",
            "serviceaccount",
            "service_account",
            "kubeconfig",
        )
    )


def check_automount_service_account_token(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not is_app_workload_document(doc) or not has_managed_workload_marker(doc.data):
            continue
        if not isinstance(doc.data, dict):
            continue

        value = _extract_automount_service_account_token(doc.data)
        if value is False:
            continue
        if value is True and _has_service_account_token_usage_evidence(doc.data):
            continue

        if value is True:
            message = (
                "automountServiceAccountToken may be true only when Kubernetes API/service account "
                "token usage is evidenced by integration settings, serviceAccountName, or "
                f"{SERVICE_ACCOUNT_TOKEN_REASON_ANNOTATION}"
            )
        else:
            message = "managed app workloads must explicitly set automountServiceAccountToken: false"

        add_doc_violation(
            violations,
            rule_id="R010",
            doc=doc,
            pattern=r"^\s*automountServiceAccountToken\s*:",
            default_pattern=r"^\s*template\s*:",
            message=message,
        )

    return violations


def check_image_pull_secret_refs(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in context.yaml_documents:
        if doc.skip_checks or not is_app_workload_document(doc) or not has_managed_workload_marker(doc.data):
            continue
        if not isinstance(doc.data, dict):
            continue

        template_spec = get_template_spec(doc.data)
        image_pull_secrets = template_spec.get("imagePullSecrets") if isinstance(template_spec, dict) else None

        # Public images should omit imagePullSecrets entirely. When a private-registry
        # workload does declare pull secrets, only the app-scoped runtime-managed
        # secret is allowed so templates do not depend on undeclared custom secrets.
        if image_pull_secrets is None:
            continue

        referenced_names: List[str] = []
        if isinstance(image_pull_secrets, list):
            for item in image_pull_secrets:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    referenced_names.append(name.strip())

        if referenced_names == ["${{ defaults.app_name }}"]:
            continue

        add_doc_violation(
            violations,
            rule_id="R035",
            doc=doc,
            pattern=r"^\s*imagePullSecrets\s*:",
            default_pattern=r"^\s*template\s*:",
            message=(
                "imagePullSecrets may be omitted for public images; if declared for "
                "private-registry workloads, it must reference only the app-scoped "
                "secret `${{ defaults.app_name }}`"
            ),
        )

    return violations


APP_RULES: Dict[str, Rule] = {
    "R001": Rule("R001", check_no_latest_tags),
    "R016": Rule("R016", check_no_floating_image_tags),
    "R018": Rule("R018", check_no_compose_image_variables),
    "R002": Rule("R002", check_app_no_spec_template),
    "R003": Rule("R003", check_app_has_spec_data_url),
    "R032": Rule("R032", check_app_display_type_normal),
    "R033": Rule("R033", check_app_type_link),
    "R004": Rule("R004", check_template_name_is_hardcoded_lowercase),
    "R012": Rule("R012", check_template_required_metadata_fields),
    "R013": Rule("R013", check_template_folder_matches_name),
    "R014": Rule("R014", check_template_icon_paths),
    "R025": Rule("R025", check_template_readme_paths),
    "R021": Rule("R021", check_template_i18n_zh_description_chinese),
    "R022": Rule("R022", check_template_i18n_zh_title_absent),
    "R023": Rule("R023", check_template_categories_allowed),
    "R024": Rule("R024", check_official_health_probes),
    "R036": Rule("R036", check_cronjob_required_labels),
    "R015": Rule("R015", check_origin_image_name_matches_container),
    "R020": Rule("R020", check_service_ports_have_names),
    "R029": Rule("R029", check_service_labels_match_selector_app),
    "R030": Rule("R030", check_configmap_labels_match_name),
    "R043": Rule("R043", check_configmap_file_mount_contract),
    "R044": Rule("R044", check_optional_object_storage_uses_boolean_input),
    "R031": Rule("R031", check_ingress_name_matches_backends),
    "R026": Rule("R026", check_http_ingress_annotations),
    "R027": Rule("R027", check_postgres_custom_db_init_job),
    "R037": Rule("R037", check_postgres_secret_refs_match_cluster_name),
    "R039": Rule("R039", check_database_services_use_clusters),
    "R042": Rule("R042", check_main_container_startup_contract),
    "R008": Rule("R008", check_deploy_manager_label_match_name),
    "R034": Rule("R034", check_app_label_match_name),
    "R028": Rule("R028", check_container_names_match_workload_name),
    "R009": Rule("R009", check_revision_history_limit),
    "R010": Rule("R010", check_automount_service_account_token),
    "R035": Rule("R035", check_image_pull_secret_refs),
}
