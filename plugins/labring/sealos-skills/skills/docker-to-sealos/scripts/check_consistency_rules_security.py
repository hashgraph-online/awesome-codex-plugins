#!/usr/bin/env python3
"""Security and secret-handling consistency rules."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

from check_consistency_models import DB_SECRET_SUFFIXES, Rule, ScanContext, Violation, WORKLOAD_KINDS
from check_consistency_helpers_workload import iter_containers, iter_workload_secret_refs
from check_consistency_parser import find_line


APP_NAME_PLACEHOLDER = r"\$\{\{\s*defaults\.app_name\s*\}\}"
SERVICE_ACCOUNT_PLACEHOLDER = r"\$\{\{\s*SEALOS_SERVICE_ACCOUNT\s*\}\}"
APPROVED_DB_SECRET_PATTERN = re.compile(
    rf"^{APP_NAME_PLACEHOLDER}(?:{'|'.join(re.escape(suffix) for suffix in DB_SECRET_SUFFIXES)})$"
)
OBJECT_STORAGE_BASE_SECRET_NAME = "object-storage-key"
OBJECT_STORAGE_BUCKET_SECRET_PATTERN = re.compile(
    rf"^object-storage-key-{SERVICE_ACCOUNT_PLACEHOLDER}-{APP_NAME_PLACEHOLDER}(?:-[a-z0-9](?:[-a-z0-9]*[a-z0-9])?)*$"
)
OBJECT_STORAGE_BASE_ENV_NAMES: Set[str] = {
    "S3_ACCESS_KEY_ID",
    "S3_SECRET_ACCESS_KEY",
    "BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT",
}
OBJECT_STORAGE_BUCKET_ENV_NAMES: Set[str] = {"S3_BUCKET"}
DB_CONNECTION_INDICATOR_HINTS: Set[str] = {
    "DB",
    "DATABASE",
    "POSTGRES",
    "POSTGRESQL",
    "PG",
    "MYSQL",
    "MARIADB",
    "MONGO",
    "MONGODB",
    "REDIS",
    "KAFKA",
}
# These envs contain DB-related tokens (PG/URL/PORT) in names but are not
# direct database connection fields and should not be forced to secretKeyRef.
NON_DB_CONNECTION_ENV_EXACT: Set[str] = {
    "STUDIO_PG_META_URL",
    "POSTGREST_URL",
    "POSTGREST_BASE_URL",
    "PGRST_OPENAPI_SERVER_PROXY_URI",
    "PG_META_PORT",
    "CODE_SANDBOX_URL",
    "SANDBOX_URL",
}
ENV_VALUE_REF_RE = re.compile(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)")
DB_COMPOSABLE_KEYS: Set[str] = {"endpoint", "host", "port", "username", "password"}
REDIS_SERVICE_HOST_TEMPLATE_PATTERN = re.compile(
    rf"^{APP_NAME_PLACEHOLDER}-redis-redis(?:-redis)?\.\$\{{\{{\s*SEALOS_NAMESPACE\s*\}}\}}\.svc(?:\.cluster\.local)?$"
)
REDIS_SERVICE_HOST_RUNTIME_PATTERN = re.compile(
    r"^[a-z0-9](?:[-a-z0-9]*redis[-a-z0-9]*)\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.svc(?:\.cluster\.local)?$"
)
MONGODB_SERVICE_HOST_TEMPLATE_PATTERN = re.compile(
    rf"^{APP_NAME_PLACEHOLDER}-(?:mongo|mongodb)-mongodb\.\$\{{\{{\s*SEALOS_NAMESPACE\s*\}}\}}\.svc(?:\.cluster\.local)?$"
)
MONGODB_SERVICE_HOST_RUNTIME_PATTERN = re.compile(
    r"^[a-z0-9](?:[-a-z0-9]*mongo(?:db)?[-a-z0-9]*)-mongodb\.[a-z0-9](?:[-a-z0-9]*[a-z0-9])?\.svc(?:\.cluster\.local)?$"
)


def is_approved_db_secret_name(secret_name: str) -> bool:
    return APPROVED_DB_SECRET_PATTERN.fullmatch(secret_name) is not None


def is_approved_object_storage_secret_ref(source: str, secret_name: str, env_name: Optional[str]) -> bool:
    if source != "env" or not isinstance(env_name, str):
        return False
    if secret_name == OBJECT_STORAGE_BASE_SECRET_NAME:
        return env_name in OBJECT_STORAGE_BASE_ENV_NAMES
    if OBJECT_STORAGE_BUCKET_SECRET_PATTERN.fullmatch(secret_name):
        normalized_env = normalize_env_name(env_name)
        return normalized_env in OBJECT_STORAGE_BUCKET_ENV_NAMES or normalized_env.endswith("_BUCKET")
    return False


def normalize_env_name(env_name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", env_name.upper())


def infer_db_connection_field(env_name: str) -> Optional[str]:
    upper = normalize_env_name(env_name)
    if upper in NON_DB_CONNECTION_ENV_EXACT:
        return None
    if not any(hint in upper for hint in DB_CONNECTION_INDICATOR_HINTS):
        return None

    if re.search(r"(?:^|_)(?:PASSWORD|PASS|PWD)(?:$|_)", upper):
        return "password"
    if re.search(r"(?:^|_)(?:USERNAME|USER)(?:$|_)", upper):
        return "username"
    if re.search(r"(?:^|_)(?:ENDPOINT|URI|URL|DSN)(?:$|_)", upper):
        return "endpoint"
    if re.search(r"(?:^|_)(?:HOST|SERVER)(?:$|_)", upper):
        return "host"
    if re.search(r"(?:^|_)(?:PORT)(?:$|_)", upper):
        return "port"

    return None


def extract_secret_ref(env_item: Dict[str, object]) -> Optional[Dict[str, str]]:
    value_from = env_item.get("valueFrom")
    secret_ref = value_from.get("secretKeyRef") if isinstance(value_from, dict) else None
    if not isinstance(secret_ref, dict):
        return None
    name = secret_ref.get("name")
    key = secret_ref.get("key")
    if not isinstance(name, str) or not isinstance(key, str):
        return None
    return {"name": name, "key": key}


def is_composed_db_endpoint_from_secret(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    value = env_item.get("value")
    if not isinstance(value, str):
        return False

    ref_names = ENV_VALUE_REF_RE.findall(value)
    if not ref_names:
        return False

    has_endpoint = False
    has_host = False
    has_port = False
    for ref_name in ref_names:
        ref_env = env_items_by_name.get(ref_name)
        if not isinstance(ref_env, dict):
            return False
        ref_secret = extract_secret_ref(ref_env)
        if ref_secret is None:
            return False
        if not is_approved_db_secret_name(ref_secret["name"]):
            return False
        ref_key = ref_secret["key"]
        if ref_key not in DB_COMPOSABLE_KEYS:
            return False
        if ref_key == "endpoint":
            has_endpoint = True
        if ref_key == "host":
            has_host = True
        if ref_key == "port":
            has_port = True

    return has_endpoint or (has_host and has_port)


def resolve_env_value(value: object, env_items_by_name: Dict[str, Dict[str, object]], depth: int = 0) -> Optional[str]:
    if not isinstance(value, str):
        return None
    if depth > 4:
        return None

    ref_match = re.fullmatch(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)", value.strip())
    if not ref_match:
        return value

    ref_env = env_items_by_name.get(ref_match.group(1))
    if not isinstance(ref_env, dict):
        return None
    return resolve_env_value(ref_env.get("value"), env_items_by_name, depth + 1)


def is_redis_service_host(value: str) -> bool:
    stripped = value.strip()
    return (
        REDIS_SERVICE_HOST_TEMPLATE_PATTERN.fullmatch(stripped) is not None
        or REDIS_SERVICE_HOST_RUNTIME_PATTERN.fullmatch(stripped) is not None
    )


def is_redis_service_port(value: str) -> bool:
    return value.strip() == "6379"


def is_mongodb_service_host(value: str) -> bool:
    stripped = value.strip()
    return (
        MONGODB_SERVICE_HOST_TEMPLATE_PATTERN.fullmatch(stripped) is not None
        or MONGODB_SERVICE_HOST_RUNTIME_PATTERN.fullmatch(stripped) is not None
    )


def is_mongodb_service_port(value: str) -> bool:
    return value.strip() == "27017"


def is_redis_host_from_env(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    resolved = resolve_env_value(env_item.get("value"), env_items_by_name)
    return isinstance(resolved, str) and is_redis_service_host(resolved)


def is_redis_port_from_env(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    resolved = resolve_env_value(env_item.get("value"), env_items_by_name)
    return isinstance(resolved, str) and is_redis_service_port(resolved)


def is_redis_password_from_secret(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    ref_match = re.fullmatch(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)", str(env_item.get("value", "")).strip())
    if ref_match is None:
        return False
    ref_env = env_items_by_name.get(ref_match.group(1))
    if not isinstance(ref_env, dict):
        return False
    ref_secret = extract_secret_ref(ref_env)
    if ref_secret is None:
        return False
    return is_approved_db_secret_name(ref_secret["name"]) and ref_secret["key"] == "password"


def is_composed_redis_endpoint_from_service(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    value = env_item.get("value")
    if not isinstance(value, str):
        return False
    if not value.startswith("redis://"):
        return False

    ref_names = ENV_VALUE_REF_RE.findall(value)
    has_host = False
    has_port = False

    for ref_name in ref_names:
        ref_env = env_items_by_name.get(ref_name)
        if not isinstance(ref_env, dict):
            return False

        ref_secret = extract_secret_ref(ref_env)
        if ref_secret is not None:
            if not is_approved_db_secret_name(ref_secret["name"]):
                return False
            ref_key = ref_secret["key"]
            if ref_key == "endpoint":
                has_host = True
                has_port = True
            elif ref_key == "host":
                has_host = True
            elif ref_key == "port":
                has_port = True
            elif ref_key in {"username", "password"}:
                pass
            else:
                return False
            continue

        resolved = resolve_env_value(ref_env.get("value"), env_items_by_name)
        if not isinstance(resolved, str):
            return False
        if is_redis_service_host(resolved):
            has_host = True
            continue
        if is_redis_service_port(resolved):
            has_port = True
            continue
        normalized_ref = normalize_env_name(ref_name)
        if normalized_ref.endswith("PASSWORD") or normalized_ref.endswith("USERNAME"):
            continue
        return False

    if not ref_names:
        match = re.search(r"redis://(?::[^@]+@)?([^/:]+):([0-9]+)", value)
        if match is None:
            return False
        return is_redis_service_host(match.group(1)) and is_redis_service_port(match.group(2))

    return has_host and has_port


def is_composed_mongodb_endpoint_from_service(
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    value = env_item.get("value")
    if not isinstance(value, str):
        return False
    if not value.startswith("mongodb://"):
        return False

    ref_names = ENV_VALUE_REF_RE.findall(value)
    has_host = False
    has_port = False

    match = re.search(r"mongodb://(?:[^:@]+(?::[^@]+)?@)?([^/:?]+):([0-9]+)", value)
    if match is not None:
        if is_mongodb_service_host(match.group(1)):
            has_host = True
        if is_mongodb_service_port(match.group(2)):
            has_port = True

    for ref_name in ref_names:
        ref_env = env_items_by_name.get(ref_name)
        if not isinstance(ref_env, dict):
            return False

        ref_secret = extract_secret_ref(ref_env)
        if ref_secret is not None:
            if not is_approved_db_secret_name(ref_secret["name"]):
                return False
            ref_key = ref_secret["key"]
            if ref_key == "endpoint":
                has_host = True
                has_port = True
            elif ref_key == "host":
                has_host = True
            elif ref_key == "port":
                has_port = True
            elif ref_key in {"username", "password"}:
                pass
            else:
                return False
            continue

        resolved = resolve_env_value(ref_env.get("value"), env_items_by_name)
        if not isinstance(resolved, str):
            return False
        if is_mongodb_service_host(resolved):
            has_host = True
            continue
        if is_mongodb_service_port(resolved):
            has_port = True
            continue
        normalized_ref = normalize_env_name(ref_name)
        if normalized_ref.endswith("PASSWORD") or normalized_ref.endswith("USERNAME"):
            continue
        return False

    return has_host and has_port


def is_allowed_redis_service_env(
    env_name: str,
    expected_key: str,
    env_item: Dict[str, object],
    env_items_by_name: Dict[str, Dict[str, object]],
) -> bool:
    normalized = normalize_env_name(env_name)
    if "REDIS" not in normalized:
        return False

    if expected_key == "host":
        return is_redis_host_from_env(env_item, env_items_by_name)
    if expected_key == "port":
        return is_redis_port_from_env(env_item, env_items_by_name)
    if expected_key == "password":
        return is_redis_password_from_secret(env_item, env_items_by_name)
    if expected_key == "endpoint":
        return is_composed_redis_endpoint_from_service(env_item, env_items_by_name)
    return False


def _find_secret_ref_line(doc, source: str, secret_name: str, env_name: Optional[str]) -> int:
    if source == "env" and isinstance(env_name, str):
        return find_line(doc, rf"^\s*-\s*name\s*:\s*{re.escape(env_name)}\s*$")
    if source == "volume":
        return find_line(doc, rf"^\s*secretName\s*:\s*{re.escape(secret_name)}\s*$")
    return find_line(doc, rf"^\s*name\s*:\s*{re.escape(secret_name)}\s*$")


def _collect_reserved_db_secret_overrides(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") != "Secret":
            continue

        metadata = doc.data.get("metadata")
        secret_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(secret_name, str) or not is_approved_db_secret_name(secret_name):
            continue

        line = find_line(
            doc,
            rf"^\s*name\s*:\s*{re.escape(secret_name)}\s*$",
            default=find_line(doc, r"^\s*metadata\s*:"),
        )
        violations.append(
            Violation(
                rule_id="R007",
                path=doc.path,
                line=line,
                message=(
                    "database secret names managed by Kubeblocks are reserved; "
                    "do not define custom Secret resources with those names"
                ),
            )
        )
    return violations


def check_business_env_secret_policy(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = _collect_reserved_db_secret_overrides(context)

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        kind = doc.data.get("kind")
        if kind not in WORKLOAD_KINDS:
            continue

        for source, secret_name, env_name, _ in iter_workload_secret_refs(doc.data):
            if is_approved_db_secret_name(secret_name) or is_approved_object_storage_secret_ref(
                source, secret_name, env_name
            ):
                continue

            line = _find_secret_ref_line(doc, source, secret_name, env_name)
            violations.append(
                Violation(
                    rule_id="R007",
                    path=doc.path,
                    line=line,
                    message=(
                        "business workload secret references must not use custom secrets unless they reference "
                        "an approved database or object storage secret"
                    ),
                )
            )

    return violations


def check_db_connection_env_secret_requirements(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") not in WORKLOAD_KINDS:
            continue

        for container in iter_containers(doc.data):
            env_list = container.get("env")
            if not isinstance(env_list, list):
                continue

            env_items_by_name: Dict[str, Dict[str, object]] = {}
            for env_item in env_list:
                if not isinstance(env_item, dict):
                    continue
                env_name = env_item.get("name")
                if isinstance(env_name, str) and env_name not in env_items_by_name:
                    env_items_by_name[env_name] = env_item

            for env_item in env_list:
                if not isinstance(env_item, dict):
                    continue
                env_name = env_item.get("name")
                if not isinstance(env_name, str):
                    continue

                expected_key = infer_db_connection_field(env_name)
                if expected_key is None:
                    continue

                secret_ref = extract_secret_ref(env_item)
                if secret_ref is None:
                    if is_allowed_redis_service_env(env_name, expected_key, env_item, env_items_by_name):
                        continue
                    if expected_key == "endpoint" and is_composed_mongodb_endpoint_from_service(
                        env_item, env_items_by_name
                    ):
                        continue
                    if expected_key == "endpoint" and is_composed_db_endpoint_from_secret(
                        env_item, env_items_by_name
                    ):
                        continue
                    line = find_line(doc, rf"^\s*-\s*name\s*:\s*{re.escape(env_name)}\s*$")
                    violations.append(
                        Violation(
                            rule_id="R017",
                            path=doc.path,
                            line=line,
                            message=(
                                "database connection env fields (endpoint/host/port/username/password) "
                                "must use valueFrom.secretKeyRef"
                            ),
                        )
                    )
                    continue

                secret_name = secret_ref["name"]
                if not is_approved_db_secret_name(secret_name):
                    # Let R007 report unapproved/invalid secret references.
                    continue

                secret_key = secret_ref["key"]
                if secret_key != expected_key:
                    line = find_line(doc, rf"^\s*-\s*name\s*:\s*{re.escape(env_name)}\s*$")
                    violations.append(
                        Violation(
                            rule_id="R017",
                            path=doc.path,
                            line=line,
                            message=(
                                f"database env '{env_name}' must use secret key '{expected_key}' "
                                "from an approved database secret"
                            ),
                        )
                    )

    return violations


SECURITY_RULES: Dict[str, Rule] = {
    "R007": Rule("R007", check_business_env_secret_policy),
    "R017": Rule("R017", check_db_connection_env_secret_requirements),
}
