#!/usr/bin/env python3
"""Application-centric consistency rules."""

from __future__ import annotations

from collections import Counter
import ipaddress
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple
from urllib.parse import unquote_plus, urlsplit

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
WEBSOCKET_INGRESS_REQUIRED_ANNOTATIONS: Dict[str, str] = {
    "kubernetes.io/ingress.class": "nginx",
    "nginx.ingress.kubernetes.io/proxy-body-size": "32m",
    "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
    "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600",
    "nginx.ingress.kubernetes.io/backend-protocol": "WS",
    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
}
WEBSOCKET_PORT_NAME_TOKENS = {"websocket", "ws", "wss"}
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
DATABASE_RAW_WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
DATABASE_RAW_RESOURCE_KINDS = DATABASE_RAW_WORKLOAD_KINDS | {"Service"}
DATABASE_CLIENT_JOB_TOKENS = {"init", "migrate", "migration", "bootstrap", "setup", "seed", "backup", "restore"}
DATABASE_RESOURCE_NAME_TOKENS = {"postgres", "postgresql", "mysql", "mariadb", "mongo", "mongodb", "redis", "kafka"}
PRIVATE_IMAGE_REGISTRY_PREFIXES = ("ghcr.io/",)
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
OBJECT_STORAGE_INPUT_TEXT_RE = re.compile(
    r"\b(?:object\s*storage|objectstorage|s3|s3-compatible|bucket|binary\s+data|external\s+storage)\b",
    re.IGNORECASE,
)
LICENSE_GATED_TEXT_RE = re.compile(
    r"\b(?:enterprise|paid|commercial|premium|subscription|license|licensed|licence|licenced)\b",
    re.IGNORECASE,
)
OBJECT_STORAGE_BRANCH_MARKER_RE = re.compile(
    r"\b(?:ObjectStorageBucket|object-storage-key|object\s+storage|s3[_-]|aws_access_key_id|"
    r"aws_secret_access_key|storage_s3|s3-compatible|bucket|bucket_name|minio)\b",
    re.IGNORECASE,
)
OBJECT_STORAGE_PROVIDER_VALUE_RE = re.compile(
    r"\b(?:s3|s3 compatible|object storage|minio|sealos objectstorage|sealos object storage|aws s3|external s3)\b",
    re.IGNORECASE,
)
OBJECT_STORAGE_PROVIDER_DECISION_VALUE_RE = re.compile(
    r"\b(?:aws\s+s3|sealos\s+object\s*storage|managed\s+(?:s3|object\s*storage)|bundled\s+minio)\b",
    re.IGNORECASE,
)
OBJECT_STORAGE_INPUT_TEXT_MAX_ITEMS = 32
OBJECT_STORAGE_INPUT_TEXT_MAX_VALUE_CHARS = 512
OBJECT_STORAGE_INPUT_TEXT_MAX_CHARS = 4096
OBJECT_STORAGE_UNSAFE_INPUT_MARKER = "object storage provider"
OBJECT_STORAGE_SELECTOR_TOKENS = {"PROVIDER", "BACKEND", "TYPE", "MODE", "DRIVER"}
OBJECT_STORAGE_PROVIDER_DECISION_TOKENS = {"USE", "ENABLE", "ENABLED", "DISABLE", "DISABLED"}
OBJECT_STORAGE_CONFIG_TOKENS = {
    "ACCESS",
    "BUCKET",
    "CAPACITY",
    "CLASS",
    "DOMAIN",
    "ENDPOINT",
    "KEY",
    "PASSWORD",
    "POLICY",
    "REGION",
    "SECURE",
    "SECRET",
    "SIZE",
    "SSL",
    "TLS",
    "URL",
    "USER",
    "USERNAME",
}
OBJECT_STORAGE_PROXY_ROLE_TOKENS = {"ADAPTER", "COMPAT", "COMPATIBILITY", "GATEWAY", "PROXY"}
OBJECT_STORAGE_PROXY_HELPER_TOKENS = {"CHECK", "INIT", "PROBE", "WAIT"}
PERSISTENT_VOLUME_SOURCE_KEYS = {
    "awsElasticBlockStore",
    "azureDisk",
    "azureFile",
    "cephfs",
    "cinder",
    "csi",
    "fc",
    "flexVolume",
    "flocker",
    "gcePersistentDisk",
    "glusterfs",
    "hostPath",
    "iscsi",
    "nfs",
    "persistentVolumeClaim",
    "photonPersistentDisk",
    "portworxVolume",
    "quobyte",
    "rbd",
    "scaleIO",
    "storageos",
    "vsphereVolume",
}
MINIO_SERVER_IMAGE_RE = re.compile(
    r"(?:^|/)(?:minio/minio|bitnami(?:legacy)?/minio)(?::|@|$)",
    re.IGNORECASE,
)
EXTERNAL_OBJECT_STORAGE_SOURCE_ANNOTATION = "docker-to-sealos.external-object-storage-source"
OBJECT_STORAGE_COMPATIBILITY_PROXY_SOURCE_ANNOTATION = (
    "docker-to-sealos.object-storage-compatibility-proxy-source"
)
OBJECT_STORAGE_USER_REQUEST_EVIDENCE_RE = re.compile(
    r"user-request:[A-Za-z0-9][A-Za-z0-9._/-]*"
)
OBJECT_STORAGE_SOURCE_EVIDENCE_MAX_CHARS = 2048
OBJECT_STORAGE_SOURCE_SENSITIVE_QUERY_TOKENS = {
    "access",
    "auth",
    "authorization",
    "apikey",
    "credential",
    "key",
    "password",
    "secret",
    "sig",
    "signature",
    "token",
}
AWS_OBJECT_STORAGE_INPUT_RE = re.compile(
    r"^AWS_(?:ACCESS_KEY(?:_ID)?|SECRET(?:_ACCESS)?_KEY|SESSION_TOKEN|"
    r"ENDPOINT(?:_URL)?(?:_S3)?|REGION|DEFAULT_REGION|S3_BUCKET(?:_NAME)?|BUCKET(?:_NAME)?)$",
    re.IGNORECASE,
)
AWS_OBJECT_STORAGE_CONTEXT_RE = re.compile(
    r"\b(?:s3|object\s*storage|minio|external\s*storage)\b",
    re.IGNORECASE,
)
EXTERNAL_OBJECT_STORAGE_DESCRIPTION_RE = re.compile(
    r"\b(?:s3|object\s*storage|minio)\b",
    re.IGNORECASE,
)
EXTERNAL_OBJECT_STORAGE_CONFIG_TOKENS = {
    "BUCKET",
    "CREDENTIAL",
    "CREDENTIALS",
    "ENDPOINT",
    "KEY",
    "PASSWORD",
    "REGION",
    "SECRET",
    "TOKEN",
    "URL",
    "USER",
    "USERNAME",
}
MANAGED_OBJECT_STORAGE_TOGGLE_NAMES = {
    "ENABLE_OBJECT_STORAGE",
    "ENABLE_S3_STORAGE",
    "ENABLE_SEALOS_OBJECT_STORAGE",
    "ENABLE_SEALOS_OBJECTSTORAGE",
    "ENABLE_S3",
    "USE_OBJECT_STORAGE",
    "USE_MANAGED_OBJECT_STORAGE",
    "USE_MANAGED_S3",
    "USE_SEALOS_OBJECT_STORAGE",
    "USE_SEALOS_OBJECTSTORAGE",
    "USE_SEALOS_S3",
}
TEMPLATE_IF_RE = re.compile(r"\$\{\{\s*if\s*\((.*?)\)\s*\}\}")
TEMPLATE_ENDIF_RE = re.compile(r"\$\{\{\s*endif\(\)\s*\}\}")
TEMPLATE_INPUT_REF_RE = re.compile(r"\binputs\.([A-Za-z_][A-Za-z0-9_]*)\b")
RUNTIME_BUNDLE_EVIDENCE_KIND = "RuntimeBundleEvidence"
RUNTIME_BUNDLE_SOURCE_FIELD = "source"
RUNTIME_BUNDLE_IMAGES_FIELD = "images"
RUNTIME_BUNDLE_COMPONENTS_FIELD = "components"
RUNTIME_BUNDLE_ROUTES_FIELD = "routes"
RUNTIME_BUNDLE_ENVS_FIELD = "env"
TOPOLOGY_EVIDENCE_KIND = "TopologyEvidence"
TOPOLOGY_EVIDENCE_DIR = "topology-evidence"
TOPOLOGY_RESOURCE_KINDS = {
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "CronJob",
    "Cluster",
    "ObjectStorageBucket",
}
TOPOLOGY_REPLICA_KINDS = {"Deployment", "StatefulSet"}


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


def _line_number_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _metadata_annotations(data: Dict[str, Any]) -> Dict[str, Any]:
    metadata = data.get("metadata")
    annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
    return annotations if isinstance(annotations, dict) else {}


def _split_runtime_bundle_values(value: Any) -> List[str]:
    if isinstance(value, list):
        raw = "\n".join(str(item) for item in value if item is not None)
    elif value is None:
        raw = ""
    else:
        raw = str(value)
    return [item.strip() for item in re.split(r"[\n,]+", raw) if item.strip()]


def _parse_runtime_bundle_route_string(value: str) -> Tuple[str, str]:
    if "->" in value:
        path, service = value.split("->", 1)
    elif "=" in value:
        path, service = value.split("=", 1)
    else:
        path, service = value, ""
    return path.strip(), service.strip()


def _parse_runtime_bundle_routes(value: Any) -> List[Tuple[str, str]]:
    routes: List[Tuple[str, str]] = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                path = item.get("path")
                service = item.get("service")
                routes.append(
                    (
                        path.strip() if isinstance(path, str) else "",
                        service.strip() if isinstance(service, str) else "",
                    )
                )
                continue
            routes.append(_parse_runtime_bundle_route_string(str(item)))
        return routes
    for item in _split_runtime_bundle_values(value):
        routes.append(_parse_runtime_bundle_route_string(item))
    return routes


def _iter_runtime_bundle_evidence_documents(context: ScanContext) -> Iterable[YamlDocument]:
    for doc in iter_documents_by_kind(context, RUNTIME_BUNDLE_EVIDENCE_KIND):
        if doc.path.suffix.lower() in TEMPLATE_ARTIFACT_SUFFIXES:
            yield doc


def _runtime_bundle_spec(doc: YamlDocument) -> Dict[str, Any]:
    data = doc.data
    spec = data.get("spec") if isinstance(data, dict) else None
    return spec if isinstance(spec, dict) else {}


def _template_artifacts_by_name(context: ScanContext) -> Dict[str, YamlDocument]:
    templates: Dict[str, YamlDocument] = {}
    for doc in _iter_template_artifact_documents(context):
        if not isinstance(doc.data, dict):
            continue
        name = _metadata_name(doc.data)
        if name:
            templates[name] = doc
    return templates


def _iter_ingress_routes(data: Dict[str, Any]) -> Iterable[Tuple[str, str]]:
    spec = data.get("spec")
    rules = spec.get("rules") if isinstance(spec, dict) else None
    if not isinstance(rules, list):
        return
    for rule in rules:
        http = rule.get("http") if isinstance(rule, dict) else None
        paths = http.get("paths") if isinstance(http, dict) else None
        if not isinstance(paths, list):
            continue
        for path_entry in paths:
            if not isinstance(path_entry, dict):
                continue
            path_value = path_entry.get("path")
            backend = path_entry.get("backend")
            service = backend.get("service") if isinstance(backend, dict) else None
            service_name = service.get("name") if isinstance(service, dict) else None
            if isinstance(path_value, str) and isinstance(service_name, str):
                routes_tuple = (path_value.strip(), service_name.strip())
                if routes_tuple[0] and routes_tuple[1]:
                    yield routes_tuple


def _collect_runtime_bundle_state(context: ScanContext, artifact_path: Path) -> Dict[str, set]:
    state = {
        "images": set(),
        "workloads": set(),
        "services": set(),
        "routes": set(),
        "envs": set(),
    }
    for doc in context.yaml_documents:
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.path != artifact_path:
            continue
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue

        kind = doc.data.get("kind")
        name = _metadata_name(doc.data)
        if kind == "Service" and name:
            state["services"].add(name)
        elif kind == "Ingress":
            state["routes"].update(_iter_ingress_routes(doc.data))

        if not is_app_workload_document(doc) or not has_managed_workload_marker(doc.data):
            continue
        if name:
            state["workloads"].add(name)

        annotations = _metadata_annotations(doc.data)
        origin_image = annotations.get("originImageName")
        if isinstance(origin_image, str) and origin_image.strip():
            state["images"].add(origin_image.strip())

        for container in iter_containers(doc.data):
            image = container.get("image")
            if isinstance(image, str) and image.strip():
                state["images"].add(image.strip())
            env_list = container.get("env")
            if not isinstance(env_list, list):
                continue
            for env_item in env_list:
                if not isinstance(env_item, dict):
                    continue
                env_name = env_item.get("name")
                if isinstance(env_name, str) and env_name.strip():
                    state["envs"].add(env_name.strip())
    return state


def _iter_topology_evidence_documents(context: ScanContext) -> Iterable[YamlDocument]:
    for doc in iter_documents_by_kind(context, TOPOLOGY_EVIDENCE_KIND):
        if doc.path.suffix.lower() in TEMPLATE_ARTIFACT_SUFFIXES:
            yield doc


def _normalize_topology_when(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _topology_conditions_by_line(text: str) -> Dict[int, Tuple[str, ...]]:
    active: List[str] = []
    conditions: Dict[int, Tuple[str, ...]] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = TEMPLATE_IF_RE.search(line)
        if match is not None:
            active.append(_normalize_topology_when(match.group(1)))
        conditions[line_number] = tuple(active)
        if TEMPLATE_ENDIF_RE.search(line) and active:
            active.pop()
    return conditions


def _topology_when_for_document(
    doc: YamlDocument,
    conditions_by_line: Dict[int, Tuple[str, ...]],
) -> str:
    api_line = doc.start_line
    for offset, line in enumerate(doc.source.splitlines()):
        if re.match(r"^\s*apiVersion\s*:", line):
            api_line = doc.start_line + offset
            break
    active = conditions_by_line.get(api_line, ())
    return " && ".join(active) if active else "always"


def _is_kubeblocks_cluster(data: Dict[str, Any]) -> bool:
    api_version = data.get("apiVersion")
    return (
        data.get("kind") == "Cluster"
        and isinstance(api_version, str)
        and api_version.startswith("apps.kubeblocks.io/")
    )


def _topology_cluster_components(data: Dict[str, Any]) -> Optional[Tuple[Tuple[str, int], ...]]:
    spec = data.get("spec")
    component_specs = spec.get("componentSpecs") if isinstance(spec, dict) else None
    if not isinstance(component_specs, list) or not component_specs:
        return None

    components: Dict[str, int] = {}
    for component in component_specs:
        if not isinstance(component, dict):
            return None
        name = component.get("name")
        replicas = component.get("replicas")
        if (
            not isinstance(name, str)
            or not name.strip()
            or isinstance(replicas, bool)
            or not isinstance(replicas, int)
            or replicas < 1
            or name.strip() in components
        ):
            return None
        components[name.strip()] = replicas
    return tuple(sorted(components.items()))


def _topology_record_label(record: Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]]) -> str:
    kind, name, when, replicas, components = record
    details = [f"{kind}/{name}", f"when={when}"]
    if replicas is not None:
        details.append(f"replicas={replicas}")
    if components:
        rendered = ",".join(f"{component}={count}" for component, count in components)
        details.append(f"components={rendered}")
    return " ".join(details)


def _collect_topology_records(
    context: ScanContext,
    artifact_path: Path,
    violations: List[Violation],
) -> Tuple[
    List[Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]]],
    Dict[Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]], YamlDocument],
]:
    text = context.file_texts.get(artifact_path, "")
    conditions_by_line = _topology_conditions_by_line(text)
    records: List[Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]]] = []
    docs_by_record: Dict[
        Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]],
        YamlDocument,
    ] = {}

    for doc in context.yaml_documents:
        if doc.skip_checks or doc.path != artifact_path or not isinstance(doc.data, dict):
            continue
        kind = doc.data.get("kind")
        if kind not in TOPOLOGY_RESOURCE_KINDS:
            continue
        if kind == "Cluster" and not _is_kubeblocks_cluster(doc.data):
            continue

        name = _metadata_name(doc.data)
        if not name:
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*metadata\s*:",
                default_pattern=r"^\s*kind\s*:",
                message="topology-bearing resources must define metadata.name",
            )
            continue

        replicas: Optional[int] = None
        if kind in TOPOLOGY_REPLICA_KINDS:
            spec = doc.data.get("spec")
            raw_replicas = spec.get("replicas", 1) if isinstance(spec, dict) else 1
            if isinstance(raw_replicas, bool) or not isinstance(raw_replicas, int) or raw_replicas < 1:
                add_doc_violation(
                    violations,
                    rule_id="R050",
                    doc=doc,
                    pattern=r"^\s*replicas\s*:",
                    default_pattern=r"^\s*spec\s*:",
                    message="Deployment and StatefulSet spec.replicas must be a positive integer",
                )
            else:
                replicas = raw_replicas

        components: Tuple[Tuple[str, int], ...] = ()
        if kind == "Cluster":
            parsed_components = _topology_cluster_components(doc.data)
            if parsed_components is None:
                add_doc_violation(
                    violations,
                    rule_id="R050",
                    doc=doc,
                    pattern=r"^\s*componentSpecs\s*:",
                    default_pattern=r"^\s*spec\s*:",
                    message=(
                        "KubeBlocks Cluster topology requires non-empty componentSpecs with unique names "
                        "and positive integer replicas"
                    ),
                )
            else:
                components = parsed_components

        record = (
            str(kind),
            name,
            _topology_when_for_document(doc, conditions_by_line),
            replicas,
            components,
        )
        records.append(record)
        docs_by_record.setdefault(record, doc)

    return records, docs_by_record


def _parse_topology_evidence_resources(
    doc: YamlDocument,
    resources: Any,
    violations: List[Violation],
) -> List[Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]]]:
    if not isinstance(resources, list) or not resources:
        add_doc_violation(
            violations,
            rule_id="R050",
            doc=doc,
            pattern=r"^\s*resources\s*:",
            default_pattern=r"^\s*spec\s*:",
            message="TopologyEvidence spec.resources must be a non-empty list",
        )
        return []

    records: List[Tuple[str, str, str, Optional[int], Tuple[Tuple[str, int], ...]]] = []
    for item in resources:
        if not isinstance(item, dict):
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*resources\s*:",
                message="TopologyEvidence resources entries must be objects",
            )
            continue

        kind = item.get("kind")
        name = item.get("name")
        when = item.get("when")
        if kind not in TOPOLOGY_RESOURCE_KINDS:
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*kind\s*:",
                default_pattern=r"^\s*resources\s*:",
                message=f"TopologyEvidence resource kind must be one of {sorted(TOPOLOGY_RESOURCE_KINDS)}",
            )
            continue
        if not isinstance(name, str) or not name.strip():
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*name\s*:",
                default_pattern=r"^\s*resources\s*:",
                message="TopologyEvidence resources entries must define a non-empty name",
            )
            continue
        if not isinstance(when, str) or not when.strip():
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*when\s*:",
                default_pattern=r"^\s*resources\s*:",
                message="TopologyEvidence resources entries must define when as always or a template condition",
            )
            continue

        replicas: Optional[int] = None
        raw_replicas = item.get("replicas")
        if kind in TOPOLOGY_REPLICA_KINDS:
            if isinstance(raw_replicas, bool) or not isinstance(raw_replicas, int) or raw_replicas < 1:
                add_doc_violation(
                    violations,
                    rule_id="R050",
                    doc=doc,
                    pattern=r"^\s*replicas\s*:",
                    default_pattern=r"^\s*resources\s*:",
                    message="TopologyEvidence Deployment and StatefulSet entries require positive integer replicas",
                )
                continue
            replicas = raw_replicas
        elif raw_replicas is not None:
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*replicas\s*:",
                default_pattern=r"^\s*resources\s*:",
                message=f"TopologyEvidence {kind} entries do not use replicas",
            )
            continue

        components: Tuple[Tuple[str, int], ...] = ()
        raw_components = item.get("components")
        if kind == "Cluster":
            if not isinstance(raw_components, list) or not raw_components:
                add_doc_violation(
                    violations,
                    rule_id="R050",
                    doc=doc,
                    pattern=r"^\s*components\s*:",
                    default_pattern=r"^\s*resources\s*:",
                    message="TopologyEvidence Cluster entries require a non-empty components list",
                )
                continue
            parsed_components: Dict[str, int] = {}
            invalid_component = False
            for component in raw_components:
                if not isinstance(component, dict):
                    invalid_component = True
                    break
                component_name = component.get("name")
                component_replicas = component.get("replicas")
                if (
                    not isinstance(component_name, str)
                    or not component_name.strip()
                    or isinstance(component_replicas, bool)
                    or not isinstance(component_replicas, int)
                    or component_replicas < 1
                    or component_name.strip() in parsed_components
                ):
                    invalid_component = True
                    break
                parsed_components[component_name.strip()] = component_replicas
            if invalid_component:
                add_doc_violation(
                    violations,
                    rule_id="R050",
                    doc=doc,
                    pattern=r"^\s*components\s*:",
                    default_pattern=r"^\s*resources\s*:",
                    message=(
                        "TopologyEvidence Cluster components require unique non-empty names and "
                        "positive integer replicas"
                    ),
                )
                continue
            components = tuple(sorted(parsed_components.items()))
        elif raw_components is not None:
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*components\s*:",
                default_pattern=r"^\s*resources\s*:",
                message=f"TopologyEvidence {kind} entries do not use components",
            )
            continue

        records.append(
            (
                str(kind),
                name.strip(),
                _normalize_topology_when(when),
                replicas,
                components,
            )
        )
    return records


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


def _iter_configmap_default_mode_lines(doc: YamlDocument) -> Iterable[Tuple[int, str]]:
    lines = doc.source.splitlines()
    in_config_map = False
    config_map_indent = -1

    for offset, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        if in_config_map and indent <= config_map_indent:
            in_config_map = False
            config_map_indent = -1

        if re.match(r"^\s*configMap\s*:\s*(?:#.*)?$", line):
            in_config_map = True
            config_map_indent = indent
            continue

        if in_config_map and re.match(r"^\s*defaultMode\s*:", line):
            yield doc.start_line + offset, stripped


def _configmap_default_mode_violation(line_text: str) -> Optional[str]:
    _, _, raw_value = line_text.partition(":")
    value = raw_value.split("#", 1)[0].strip().strip("'\"")
    if value.startswith("0") and value != "0":
        return (
            "ConfigMap volume defaultMode should be omitted; leading-zero modes can be rendered as "
            "invalid decimal values by the Sealos template path"
        )
    try:
        numeric_value = int(value, 10)
    except ValueError:
        return "ConfigMap volume defaultMode should be omitted unless explicitly required"
    if numeric_value > 0o777:
        return (
            "ConfigMap volume defaultMode must be omitted or use a Kubernetes-valid decimal file mode "
            "(0-511)"
        )
    return "ConfigMap volume defaultMode should be omitted unless explicitly required"


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
        for line_number, line_text in _iter_configmap_default_mode_lines(doc):
            message = _configmap_default_mode_violation(line_text)
            if message is None:
                continue
            violations.append(Violation(rule_id="R043", path=doc.path, line=line_number, message=message))

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


def _iter_root_prefix_ingress_backend_services(data: Dict[str, Any]) -> Iterable[Mapping[str, Any]]:
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
            backend = path.get("backend")
            service = backend.get("service") if isinstance(backend, dict) else None
            yield service if isinstance(service, dict) else {}


def _collect_declared_service_ports(context: ScanContext) -> Dict[Tuple[Path, str], Set[int]]:
    ports_by_service: Dict[Tuple[Path, str], Set[int]] = {}
    for doc in iter_documents_by_kind(context, "Service"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml" or not isinstance(doc.data, dict):
            continue
        metadata = doc.data.get("metadata")
        service_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(service_name, str) or not service_name.strip():
            continue
        spec = doc.data.get("spec")
        ports = spec.get("ports") if isinstance(spec, dict) else None
        service_key = (doc.path, service_name.strip())
        if not isinstance(ports, list):
            ports_by_service.setdefault(service_key, set())
            continue
        declared_ports = ports_by_service.setdefault(service_key, set())
        for port in ports:
            port_number = port.get("port") if isinstance(port, dict) else None
            if isinstance(port_number, int) and not isinstance(port_number, bool):
                declared_ports.add(port_number)
    return ports_by_service


def check_root_ingress_backend_port_numbers(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    ports_by_service = _collect_declared_service_ports(context)

    for doc in iter_documents_by_kind(context, "Ingress"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml" or not isinstance(doc.data, dict):
            continue

        for service in _iter_root_prefix_ingress_backend_services(doc.data):
            service_name = service.get("name")
            if not isinstance(service_name, str) or not service_name.strip():
                add_doc_violation(
                    violations,
                    rule_id="R051",
                    doc=doc,
                    pattern=r"^\s*service\s*:",
                    default_pattern=r"^\s*backend\s*:",
                    message="Root-path Prefix Ingress backend.service.name must reference a declared Service",
                )
                continue
            service_name = service_name.strip()

            port = service.get("port")
            port_number = port.get("number") if isinstance(port, dict) else None
            uses_named_port = isinstance(port, dict) and "name" in port
            if not isinstance(port_number, int) or isinstance(port_number, bool) or uses_named_port:
                add_doc_violation(
                    violations,
                    rule_id="R051",
                    doc=doc,
                    pattern=r"^\s*port\s*:",
                    default_pattern=r"^\s*service\s*:",
                    message=(
                        "Root-path Prefix Ingress backend.service.port must use an integer number "
                        "for Launchpad public-address discovery"
                    ),
                )
                continue

            service_key = (doc.path, service_name)
            if service_key not in ports_by_service:
                add_doc_violation(
                    violations,
                    rule_id="R051",
                    doc=doc,
                    pattern=re.escape(service_name),
                    default_pattern=r"^\s*service\s*:",
                    message=f"Ingress backend Service {service_name} is not declared in the template artifact",
                )
                continue

            declared_ports = ports_by_service[service_key]
            if port_number not in declared_ports:
                declared_text = ", ".join(str(value) for value in sorted(declared_ports)) or "none"
                add_doc_violation(
                    violations,
                    rule_id="R051",
                    doc=doc,
                    pattern=str(port_number),
                    default_pattern=r"^\s*port\s*:",
                    message=(
                        f"Ingress backend port {port_number} must match Service {service_name} "
                        f"spec.ports[*].port; declared ports: {declared_text}"
                    ),
                )

    return violations


def _normalize_annotation_value(value: Any) -> Optional[str]:
    if isinstance(value, str):
        return "\n".join(line.rstrip() for line in value.strip().splitlines())
    if value is None:
        return None
    return str(value).strip()


def _is_websocket_port_name(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized in WEBSOCKET_PORT_NAME_TOKENS or any(
        token in WEBSOCKET_PORT_NAME_TOKENS for token in normalized.split("-")
    )


def _service_port_key(value: Any) -> Optional[str]:
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _collect_service_websocket_ports(context: ScanContext) -> Dict[str, Set[str]]:
    ports_by_service: Dict[str, Set[str]] = {}
    for doc in iter_documents_by_kind(context, "Service"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue
        metadata = doc.data.get("metadata")
        service_name = metadata.get("name") if isinstance(metadata, dict) else None
        if not isinstance(service_name, str) or not service_name.strip():
            continue
        spec = doc.data.get("spec")
        ports = spec.get("ports") if isinstance(spec, dict) else None
        if not isinstance(ports, list):
            continue
        for port in ports:
            if not isinstance(port, dict):
                continue
            if not _is_websocket_port_name(port.get("name")):
                continue
            for key in ("name", "port", "targetPort"):
                port_key = _service_port_key(port.get(key))
                if port_key is None:
                    continue
                ports_by_service.setdefault(service_name.strip(), set()).add(port_key)
    return ports_by_service


def _iter_ingress_backend_service_ports(data: Mapping[str, Any]) -> Iterable[Tuple[str, str]]:
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
            backend = path.get("backend") if isinstance(path, dict) else None
            service = backend.get("service") if isinstance(backend, dict) else None
            if not isinstance(service, dict):
                continue
            name = service.get("name")
            port = service.get("port")
            if not isinstance(name, str) or not isinstance(port, dict):
                continue
            port_key = _service_port_key(port.get("name"))
            if port_key is None:
                port_key = _service_port_key(port.get("number"))
            if port_key is not None:
                yield name.strip(), port_key


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


def check_websocket_ingress_annotations(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    service_websocket_ports = _collect_service_websocket_ports(context)
    for doc in iter_documents_by_kind(context, "Ingress"):
        if doc.path.suffix.lower() not in TEMPLATE_ARTIFACT_SUFFIXES:
            continue
        if doc.path.name != "index.yaml":
            continue
        if not isinstance(doc.data, dict):
            continue

        metadata = doc.data.get("metadata")
        annotations = metadata.get("annotations") if isinstance(metadata, dict) else None
        backend_protocol = None
        if isinstance(annotations, dict):
            backend_protocol = _normalize_annotation_value(
                annotations.get("nginx.ingress.kubernetes.io/backend-protocol")
            )

        routes_websocket_port = any(
            port_key in service_websocket_ports.get(service_name, set())
            for service_name, port_key in _iter_ingress_backend_service_ports(doc.data)
        )
        declares_websocket = backend_protocol is not None and backend_protocol.upper() == "WS"

        if not declares_websocket and not routes_websocket_port:
            continue

        if not isinstance(annotations, dict):
            add_doc_violation(
                violations,
                rule_id="R048",
                doc=doc,
                pattern=r"^\s*annotations\s*:",
                default_pattern=r"^\s*metadata\s*:",
                message="WebSocket Ingress metadata.annotations must define the required WS annotation set",
            )
            continue

        for key, expected in WEBSOCKET_INGRESS_REQUIRED_ANNOTATIONS.items():
            actual_normalized = _normalize_annotation_value(annotations.get(key))
            expected_normalized = _normalize_annotation_value(expected)
            if actual_normalized == expected_normalized:
                continue
            add_doc_violation(
                violations,
                rule_id="R048",
                doc=doc,
                pattern=re.escape(key),
                default_pattern=r"^\s*annotations\s*:",
                message=f"Ingress annotation '{key}' must match the required WebSocket default",
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


def _normalize_database_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")


def _iter_mapping_values(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _iter_mapping_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_mapping_values(item)
    elif isinstance(value, str):
        yield value


def _matches_database_resource_name(value: Any) -> bool:
    return _normalize_database_token(value) in DATABASE_RESOURCE_NAME_TOKENS


def _contains_any_database_token(value: Any, tokens: Set[str]) -> bool:
    normalized = _normalize_database_token(value)
    if not normalized:
        return False
    return bool(set(normalized.split("-")) & tokens)


def _is_database_client_job(doc) -> bool:
    if not isinstance(doc.data, dict) or doc.data.get("kind") not in {"Job", "CronJob"}:
        return False

    metadata = doc.data.get("metadata")
    names: List[Any] = []
    if isinstance(metadata, dict):
        names.append(metadata.get("name"))
    for container in iter_containers(doc.data):
        names.append(container.get("name"))

    return any(_contains_any_database_token(name, DATABASE_CLIENT_JOB_TOKENS) for name in names)


def _workload_template_spec(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    kind = data.get("kind")
    spec = data.get("spec")
    if not isinstance(spec, dict):
        return None

    if kind in {"Deployment", "StatefulSet", "DaemonSet", "Job"}:
        template = spec.get("template")
        template_spec = template.get("spec") if isinstance(template, dict) else None
        return template_spec if isinstance(template_spec, dict) else None

    if kind == "CronJob":
        job_template = spec.get("jobTemplate")
        job_spec = job_template.get("spec") if isinstance(job_template, dict) else None
        template = job_spec.get("template") if isinstance(job_spec, dict) else None
        template_spec = template.get("spec") if isinstance(template, dict) else None
        return template_spec if isinstance(template_spec, dict) else None

    return None


def _iter_main_workload_containers(data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    template_spec = _workload_template_spec(data)
    containers = template_spec.get("containers") if isinstance(template_spec, dict) else None
    if not isinstance(containers, list):
        return
    for container in containers:
        if isinstance(container, dict):
            yield container


def _is_database_like_workload(doc) -> bool:
    if not isinstance(doc.data, dict):
        return False
    if doc.data.get("kind") not in DATABASE_RAW_WORKLOAD_KINDS:
        return False
    if _is_database_client_job(doc):
        return False

    for container in _iter_main_workload_containers(doc.data):
        image = container.get("image")
        if isinstance(image, str) and _is_database_image(image):
            return True
        if _matches_database_resource_name(container.get("name")):
            return True

    return False


def _is_database_like_service(doc) -> bool:
    if not isinstance(doc.data, dict) or doc.data.get("kind") != "Service":
        return False

    metadata = doc.data.get("metadata")
    if isinstance(metadata, dict):
        for value in _iter_mapping_values(
            {
                "name": metadata.get("name"),
                "labels": metadata.get("labels"),
            }
        ):
            if _matches_database_resource_name(value):
                return True

    spec = doc.data.get("spec")
    if isinstance(spec, dict):
        selector = spec.get("selector")
        if isinstance(selector, dict):
            for value in _iter_mapping_values(selector):
                if _matches_database_resource_name(value):
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
        kind = doc.data.get("kind")
        if kind not in DATABASE_RAW_RESOURCE_KINDS:
            continue

        is_database_resource = _is_database_like_service(doc) if kind == "Service" else _is_database_like_workload(doc)
        if not is_database_resource:
            continue

        add_doc_violation(
            violations,
            rule_id="R039",
            doc=doc,
            pattern=r"^\s*kind\s*:\s*(?:Deployment|StatefulSet|DaemonSet|Job|CronJob|Service)\s*$",
            default_pattern=r"^\s*kind\s*:",
            message="database services require KubeBlocks Cluster resources; raw Kubernetes resources are invalid",
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


def _template_input_specs_by_path(context: ScanContext) -> Dict[Path, Dict[str, Dict[str, Any]]]:
    inputs_by_path: Dict[Path, Dict[str, Dict[str, Any]]] = {}
    for doc in _iter_template_artifact_documents(context):
        if not isinstance(doc.data, dict):
            continue
        spec = doc.data.get("spec")
        inputs = spec.get("inputs") if isinstance(spec, dict) else None
        if not isinstance(inputs, dict):
            continue

        input_specs = inputs_by_path.setdefault(doc.path, {})
        for input_name, input_spec in inputs.items():
            if isinstance(input_name, str) and isinstance(input_spec, dict):
                input_specs[input_name] = input_spec
    return inputs_by_path


def check_template_input_references_declared(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    inputs_by_path = _template_inputs_by_path(context)

    for path in _iter_template_artifact_paths(context):
        text = context.file_texts.get(path, "")
        if not text:
            continue
        declared_inputs = inputs_by_path.get(path)
        if declared_inputs is None:
            has_template_doc = any(doc.path == path for doc in _iter_template_artifact_documents(context))
            if not has_template_doc:
                continue
            declared_inputs = {}

        seen: set[str] = set()
        for match in TEMPLATE_INPUT_REF_RE.finditer(text):
            input_name = match.group(1)
            if input_name in declared_inputs or input_name in seen:
                continue
            seen.add(input_name)
            violations.append(
                Violation(
                    rule_id="R045",
                    path=path,
                    line=_line_number_for_offset(text, match.start()),
                    message=(
                        f"inputs.{input_name} is referenced but missing from this Template CR spec.inputs"
                    ),
                )
            )

    return violations


def _yaml_mapping_key_match(line: str, key: str) -> Optional[re.Match[str]]:
    escaped = re.escape(key)
    return re.match(rf"^(?P<indent>\s*)(?:{escaped}|'{escaped}'|\"{escaped}\")\s*:", line)


def _template_mapping_field_line(
    doc: YamlDocument,
    collection_name: str,
    entry_name: str,
    field_name: str,
) -> int:
    lines = doc.source.splitlines()
    collection_index: Optional[int] = None
    collection_indent = -1

    for index, line in enumerate(lines):
        match = _yaml_mapping_key_match(line, collection_name)
        if match is None:
            continue
        collection_index = index
        collection_indent = len(match.group("indent"))
        break

    if collection_index is None:
        return doc.start_line

    entry_index: Optional[int] = None
    entry_indent = -1
    for index in range(collection_index + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= collection_indent:
            break
        match = _yaml_mapping_key_match(line, entry_name)
        if match is None or len(match.group("indent")) <= collection_indent:
            continue
        entry_index = index
        entry_indent = len(match.group("indent"))
        break

    if entry_index is None:
        return doc.start_line + collection_index

    for index in range(entry_index + 1, len(lines)):
        line = lines[index]
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= entry_indent:
            break
        match = _yaml_mapping_key_match(line, field_name)
        if match is not None and len(match.group("indent")) > entry_indent:
            return doc.start_line + index

    return doc.start_line + entry_index


def _yaml_value_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "sequence"
    if isinstance(value, dict):
        return "mapping"
    return type(value).__name__


def check_template_default_scalar_types(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []

    for doc in _iter_template_artifact_documents(context):
        if not isinstance(doc.data, dict):
            continue
        spec = doc.data.get("spec")
        if not isinstance(spec, dict):
            continue

        for collection_name, field_name in (("defaults", "value"), ("inputs", "default")):
            entries = spec.get(collection_name)
            if not isinstance(entries, dict):
                continue
            for entry_name, entry_spec in entries.items():
                if not isinstance(entry_name, str) or not isinstance(entry_spec, dict):
                    continue
                if field_name not in entry_spec or isinstance(entry_spec[field_name], str):
                    continue
                violations.append(
                    Violation(
                        rule_id="R052",
                        path=doc.path,
                        line=_template_mapping_field_line(
                            doc,
                            collection_name,
                            entry_name,
                            field_name,
                        ),
                        message=(
                            f"spec.{collection_name}.{entry_name}.{field_name} must be a YAML string, "
                            f"got {_yaml_value_type_name(entry_spec[field_name])}; encode this field as a "
                            "string and quote numeric-, boolean-, and null-like scalars"
                        ),
                    )
                )

    return violations


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
    return re.fullmatch(
        rf"\s*inputs\.{escaped}\s*===\s*['\"]true['\"]\s*",
        condition,
    ) is not None


def _bounded_object_storage_input_text(
    input_spec: Dict[str, Any],
    *,
    include_description: bool,
) -> str:
    values: List[str] = []
    unsafe_input = False
    total_chars = 0

    def append_scalar(value: Any) -> None:
        nonlocal total_chars, unsafe_input
        if not isinstance(value, (str, int, float, bool)):
            if value is not None:
                unsafe_input = True
            return
        remaining = OBJECT_STORAGE_INPUT_TEXT_MAX_CHARS - total_chars
        if remaining <= 0:
            unsafe_input = True
            return
        text = str(value)
        allowed = min(OBJECT_STORAGE_INPUT_TEXT_MAX_VALUE_CHARS, remaining)
        if len(text) > allowed:
            unsafe_input = True
        bounded_text = text[:allowed]
        values.append(bounded_text)
        total_chars += len(bounded_text)

    if include_description:
        append_scalar(input_spec.get("description"))
    append_scalar(input_spec.get("default"))
    options = input_spec.get("options")
    if isinstance(options, list):
        if len(options) > OBJECT_STORAGE_INPUT_TEXT_MAX_ITEMS:
            unsafe_input = True
        for item in options[:OBJECT_STORAGE_INPUT_TEXT_MAX_ITEMS]:
            append_scalar(item)
    else:
        append_scalar(options)

    if unsafe_input:
        values.insert(0, OBJECT_STORAGE_UNSAFE_INPUT_MARKER)
    return re.sub(r"[_-]+", " ", " ".join(values))[:OBJECT_STORAGE_INPUT_TEXT_MAX_CHARS]


def _object_storage_input_text(input_spec: Dict[str, Any]) -> str:
    return _bounded_object_storage_input_text(input_spec, include_description=True)


def _object_storage_input_value_text(input_spec: Dict[str, Any]) -> str:
    return _bounded_object_storage_input_text(input_spec, include_description=False)


def _tokens_have_object_storage_identity(tokens: Set[str]) -> bool:
    return (
        bool(tokens.intersection({"S3", "MINIO", "OBJECTSTORAGE"}))
        or {"OBJECT", "STORAGE"}.issubset(tokens)
    )


def _container_has_object_storage_env(container: Dict[str, Any]) -> bool:
    env = container.get("env")
    if not isinstance(env, list):
        return False
    for item in env:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if not isinstance(name, str):
            continue
        tokens = set(_normalize_template_input_name(name).split("_"))
        if _tokens_have_object_storage_identity(tokens):
            return True
    return False


def _is_object_storage_provider_selector(input_name: str, input_spec: Dict[str, Any]) -> bool:
    normalized = _normalize_template_input_name(input_name)
    tokens = set(normalized.split("_"))
    raw_input_type = input_spec.get("type")
    input_type = raw_input_type.strip().lower() if isinstance(raw_input_type, str) else ""
    has_selector_name = bool(tokens.intersection(OBJECT_STORAGE_SELECTOR_TOKENS))
    has_object_storage_name = (
        "S3" in tokens
        or "MINIO" in tokens
        or "OBJECTSTORAGE" in tokens
        or {"OBJECT", "STORAGE"}.issubset(tokens)
    )
    is_provider_decision = has_object_storage_name and (
        bool(tokens.intersection({"MANAGED", "SEALOS"}))
        or (
            "AWS" in tokens
            and bool(tokens.intersection(OBJECT_STORAGE_PROVIDER_DECISION_TOKENS))
        )
    )
    if is_provider_decision:
        return True
    if tokens.intersection(OBJECT_STORAGE_CONFIG_TOKENS) and not has_selector_name:
        return False
    is_numeric_capacity = input_type in {"integer", "number"} and (
        bool(tokens.intersection({"CAPACITY", "SIZE"}))
        or {"MINIO", "STORAGE"}.issubset(tokens)
    )
    if is_numeric_capacity and not has_selector_name:
        return False

    if "MINIO" in tokens and (
        len(tokens) == 1 or bool(tokens.intersection(OBJECT_STORAGE_PROVIDER_DECISION_TOKENS))
    ):
        return True

    if has_selector_name and has_object_storage_name:
        return True
    if has_selector_name and "STORAGE" in tokens:
        return True

    input_text = _object_storage_input_text(input_spec)
    input_value_text = _object_storage_input_value_text(input_spec)
    has_object_storage_text = OBJECT_STORAGE_PROVIDER_VALUE_RE.search(input_text) is not None
    has_object_storage_value = OBJECT_STORAGE_PROVIDER_VALUE_RE.search(input_value_text) is not None
    if has_selector_name and has_object_storage_text:
        return True
    if "USE" in tokens and OBJECT_STORAGE_PROVIDER_DECISION_VALUE_RE.search(input_text) is not None:
        return True
    if input_type in {"choice", "select"} and has_object_storage_value:
        return True
    if input_type in {"integer", "number"} and "STORAGE" in tokens and has_object_storage_text:
        return True
    return input_type == "string" and "STORAGE" in tokens and has_object_storage_value


def _is_minio_server_image(image: str) -> bool:
    return MINIO_SERVER_IMAGE_RE.search(image.strip()) is not None


def _is_valid_object_storage_hostname(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass

    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return False
    if len(ascii_hostname) > 253 or ascii_hostname.strip(".") != ascii_hostname:
        return False
    labels = ascii_hostname.split(".")
    return all(
        re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label) is not None
        for label in labels
    )


def _is_sensitive_object_storage_source_key(key: str) -> bool:
    separated_key = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", key)
    normalized_key = re.sub(r"[^a-z0-9]+", "_", separated_key.lower()).strip("_")
    query_tokens = set(normalized_key.split("_"))
    compact_key = normalized_key.replace("_", "")
    return bool(
        query_tokens.intersection(OBJECT_STORAGE_SOURCE_SENSITIVE_QUERY_TOKENS)
        or compact_key in OBJECT_STORAGE_SOURCE_SENSITIVE_QUERY_TOKENS
    )


def _object_storage_source_parameter_keys(
    component: str,
    *,
    require_assignment: bool = False,
) -> List[str]:
    fields = re.split(r"[&;]", unquote_plus(component))
    if len(fields) > 64:
        raise ValueError("too many URL parameters")
    return [
        field.partition("=")[0]
        for field in fields
        if field and (not require_assignment or "=" in field)
    ]


def _is_valid_object_storage_source_evidence(value: str) -> bool:
    value = value.strip()
    if (
        not value
        or len(value) > OBJECT_STORAGE_SOURCE_EVIDENCE_MAX_CHARS
        or any(character.isspace() for character in value)
    ):
        return False
    if OBJECT_STORAGE_USER_REQUEST_EVIDENCE_RE.fullmatch(value):
        return True

    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        if parsed.scheme.lower() != "https" or not hostname:
            return False
        if not _is_valid_object_storage_hostname(hostname):
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        _ = parsed.port
        parameter_keys = _object_storage_source_parameter_keys(
            parsed.query
        ) + _object_storage_source_parameter_keys(parsed.fragment, require_assignment=True)
    except ValueError:
        return False

    for key in parameter_keys:
        if _is_sensitive_object_storage_source_key(key):
            return False
    return True


def _compatibility_proxy_image(doc: YamlDocument) -> Optional[str]:
    metadata = doc.data.get("metadata") if isinstance(doc.data, dict) else None
    resource_name = metadata.get("name") if isinstance(metadata, dict) else None
    normalized_name = _normalize_template_input_name(resource_name) if isinstance(resource_name, str) else ""
    name_tokens = set(normalized_name.split("_"))
    containers = list(iter_containers(doc.data))
    resource_has_role = bool(name_tokens.intersection(OBJECT_STORAGE_PROXY_ROLE_TOKENS))
    resource_has_object_storage = _tokens_have_object_storage_identity(name_tokens)
    for container in containers:
        image = container.get("image")
        container_name = container.get("name")
        container_tokens = (
            set(_normalize_template_input_name(container_name).split("_"))
            if isinstance(container_name, str)
            else set()
        )
        if container_tokens.intersection(OBJECT_STORAGE_PROXY_HELPER_TOKENS):
            continue
        has_role = resource_has_role or bool(
            container_tokens.intersection(OBJECT_STORAGE_PROXY_ROLE_TOKENS)
        )
        has_object_storage = (
            resource_has_object_storage
            or _tokens_have_object_storage_identity(container_tokens)
            or _container_has_object_storage_env(container)
        )
        if has_role and has_object_storage and isinstance(image, str) and image.strip():
            return image
    return None


def _compatibility_proxy_uses_persistent_storage(data: Dict[str, Any]) -> bool:
    spec = data.get("spec")
    if isinstance(spec, dict):
        claim_templates = spec.get("volumeClaimTemplates")
        if isinstance(claim_templates, list) and claim_templates:
            return True

    template_spec = get_template_spec(data)
    if not isinstance(template_spec, dict):
        return False
    volumes = template_spec.get("volumes")
    if not isinstance(volumes, list):
        return False
    return any(
        isinstance(volume, dict) and bool(set(volume).intersection(PERSISTENT_VOLUME_SOURCE_KEYS))
        for volume in volumes
    )


def check_object_storage_input_contract(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    inputs_by_path = _template_inputs_by_path(context)
    input_specs_by_path = _template_input_specs_by_path(context)
    provider_inputs_by_path: Dict[Path, Set[str]] = {}

    for doc in _iter_template_artifact_documents(context):
        input_specs = input_specs_by_path.get(doc.path, {})
        provider_inputs = provider_inputs_by_path.setdefault(doc.path, set())
        for input_name, input_spec in input_specs.items():
            if not _is_object_storage_provider_selector(input_name, input_spec):
                continue
            provider_inputs.add(input_name)
            violations.append(
                Violation(
                    rule_id="R044",
                    path=doc.path,
                    line=find_line(doc, rf"^\s*{re.escape(input_name)}\s*:"),
                    message=(
                        f"object storage provider/backend selector inputs.{input_name} must be resolved "
                        "during conversion; expose only an application-level enable/disable boolean"
                    ),
                )
            )

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
                if input_name in provider_inputs_by_path.get(path, set()):
                    continue
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

    artifact_paths = set(_iter_template_artifact_paths(context))
    object_storage_paths = {
        doc.path
        for doc in context.yaml_documents
        if not doc.skip_checks
        and isinstance(doc.data, dict)
        and doc.data.get("kind") == "ObjectStorageBucket"
        and doc.path in artifact_paths
    }
    reported_minio_paths: Set[Path] = set()
    for doc in context.yaml_documents:
        if doc.path not in object_storage_paths or doc.path in reported_minio_paths:
            continue
        if doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") not in DATABASE_RAW_WORKLOAD_KINDS:
            continue
        for container in iter_containers(doc.data):
            image = container.get("image")
            if not isinstance(image, str) or not _is_minio_server_image(image):
                continue
            reported_minio_paths.add(doc.path)
            violations.append(
                Violation(
                    rule_id="R044",
                    path=doc.path,
                    line=find_line(doc, rf"^\s*image\s*:\s*['\"]?{re.escape(image)}['\"]?\s*$"),
                    message=(
                        "managed ObjectStorageBucket must be the sole object-store data plane; "
                        f"remove bundled MinIO server image {image}"
                    ),
                )
            )
            break

    compatibility_proxy_sources = {
        doc.path: _metadata_annotations(doc.data).get(
            OBJECT_STORAGE_COMPATIBILITY_PROXY_SOURCE_ANNOTATION,
            "",
        )
        for doc in _iter_template_artifact_documents(context)
    }
    for doc in context.yaml_documents:
        if doc.path not in artifact_paths or doc.skip_checks or not isinstance(doc.data, dict):
            continue
        if doc.data.get("kind") not in DATABASE_RAW_WORKLOAD_KINDS:
            continue
        proxy_image = _compatibility_proxy_image(doc)
        if proxy_image is None:
            continue

        source = compatibility_proxy_sources.get(doc.path, "")
        if not isinstance(source, str) or not _is_valid_object_storage_source_evidence(source):
            violations.append(
                Violation(
                    rule_id="R044",
                    path=doc.path,
                    line=find_line(doc, rf"^\s*image\s*:\s*['\"]?{re.escape(proxy_image)}['\"]?\s*$"),
                    message=(
                        "object-storage compatibility proxies require metadata.annotations."
                        f"{OBJECT_STORAGE_COMPATIBILITY_PROXY_SOURCE_ANNOTATION} with a credential-free "
                        "HTTPS source URL or user-request:<reference> evidence"
                    ),
                )
            )
            continue

        if _compatibility_proxy_uses_persistent_storage(doc.data):
            violations.append(
                Violation(
                    rule_id="R044",
                    path=doc.path,
                    line=find_line(doc, r"^\s*(?:persistentVolumeClaim|volumeClaimTemplates)\s*:"),
                    message=(
                        "object-storage compatibility proxies must remain stateless and must not "
                        "use persistent storage"
                    ),
                )
            )

    return violations


def _normalize_template_input_name(value: str) -> str:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", value)
    separated = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", "_", separated)
    return re.sub(r"[^A-Z0-9]+", "_", separated.upper()).strip("_")


def _tokens_have_external_object_storage_config(tokens: Set[str]) -> bool:
    return bool(tokens.intersection(EXTERNAL_OBJECT_STORAGE_CONFIG_TOKENS))


def _is_explicit_external_object_storage_input_name(normalized: str) -> bool:
    tokens = set(normalized.split("_"))
    has_object_storage = _tokens_have_object_storage_identity(tokens)
    return has_object_storage and (
        "EXTERNAL" in tokens or _tokens_have_external_object_storage_config(tokens)
    )


def _is_described_external_object_storage_input(input_name: str, input_spec: Any) -> bool:
    input_text = _template_input_text(input_name, input_spec)
    if EXTERNAL_OBJECT_STORAGE_DESCRIPTION_RE.search(input_text) is None:
        return False
    tokens = set(_normalize_template_input_name(input_name).split("_"))
    return _tokens_have_external_object_storage_config(tokens)


def _external_object_storage_input_names(doc: YamlDocument) -> List[str]:
    spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
    inputs = spec.get("inputs") if isinstance(spec, dict) else None
    if not isinstance(inputs, dict):
        return []

    input_items = [(key, value) for key, value in inputs.items() if isinstance(key, str)]
    explicit_names: Set[str] = set()
    for key, input_spec in input_items:
        normalized = _normalize_template_input_name(key)
        if normalized in MANAGED_OBJECT_STORAGE_TOGGLE_NAMES:
            continue
        if _is_explicit_external_object_storage_input_name(
            normalized
        ) or _is_described_external_object_storage_input(key, input_spec):
            explicit_names.add(key)

    has_aws_named_s3_context = False
    for key, _ in input_items:
        normalized = _normalize_template_input_name(key)
        if AWS_OBJECT_STORAGE_INPUT_RE.fullmatch(normalized) and "S3" in set(normalized.split("_")):
            has_aws_named_s3_context = True
            break
    has_aws_described_s3_context = any(
        AWS_OBJECT_STORAGE_INPUT_RE.fullmatch(_normalize_template_input_name(key))
        and AWS_OBJECT_STORAGE_CONTEXT_RE.search(_template_input_text(key, input_spec)) is not None
        for key, input_spec in input_items
    )
    has_aws_object_storage_context = (
        bool(explicit_names) or has_aws_named_s3_context or has_aws_described_s3_context
    )
    names: List[str] = []
    for key, _ in input_items:
        normalized = _normalize_template_input_name(key)
        if normalized in MANAGED_OBJECT_STORAGE_TOGGLE_NAMES:
            continue
        if key in explicit_names or (
            has_aws_object_storage_context and AWS_OBJECT_STORAGE_INPUT_RE.fullmatch(normalized)
        ):
            names.append(key)
    return names


def _external_object_storage_source(doc: YamlDocument) -> str:
    annotations = _metadata_annotations(doc.data) if isinstance(doc.data, dict) else {}
    value = annotations.get(EXTERNAL_OBJECT_STORAGE_SOURCE_ANNOTATION)
    return value.strip() if isinstance(value, str) else ""


def _iter_template_inputs(spec: Dict[str, Any]) -> Iterable[Tuple[str, Any]]:
    inputs = spec.get("inputs")
    if isinstance(inputs, dict):
        for name, input_spec in inputs.items():
            if isinstance(name, str):
                yield name, input_spec
        return
    if isinstance(inputs, list):
        for item in inputs:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if isinstance(name, str):
                yield name, item


def _template_input_text(name: str, input_spec: Any) -> str:
    parts = [name]
    if isinstance(input_spec, dict):
        for key in ("label", "title", "description", "default", "value"):
            value = input_spec.get(key)
            if isinstance(value, str):
                parts.append(value)
    elif isinstance(input_spec, str):
        parts.append(input_spec)
    return "\n".join(parts)


def _object_storage_branch_inputs_by_path(context: ScanContext) -> Dict[Path, set[str]]:
    inputs_by_path: Dict[Path, set[str]] = {}
    for path in _iter_template_artifact_paths(context):
        text = context.file_texts.get(path, "")
        lines = text.splitlines()
        for index, line in enumerate(lines):
            match = TEMPLATE_IF_RE.search(line)
            if match is None:
                continue
            input_names = _condition_input_refs(match.group(1))
            if not input_names:
                continue
            branch_end = _find_branch_end(lines, index)
            branch_text = "\n".join(lines[index: branch_end + 1])
            if not _branch_uses_object_storage(branch_text):
                continue
            inputs_by_path.setdefault(path, set()).update(input_names)
    return inputs_by_path


def _input_declaration_line(doc: YamlDocument, input_name: str) -> int:
    escaped = re.escape(input_name)
    inputs_line = doc.line_locator.find(r"^\s*inputs\s*:", default=doc.start_line)
    list_name_line = doc.line_locator.find(
        rf"^\s*name\s*:\s*['\"]?{escaped}['\"]?\s*$",
        default=inputs_line,
    )
    return doc.line_locator.find(rf"^\s*{escaped}\s*:", default=list_name_line)


def check_license_gated_object_storage_options(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    object_storage_branch_inputs = _object_storage_branch_inputs_by_path(context)

    for doc in _iter_template_artifact_documents(context):
        spec = doc.data.get("spec") if isinstance(doc.data, dict) else None
        if not isinstance(spec, dict):
            continue
        branch_inputs = object_storage_branch_inputs.get(doc.path, set())

        for input_name, input_spec in _iter_template_inputs(spec):
            input_text = _template_input_text(input_name, input_spec)
            if LICENSE_GATED_TEXT_RE.search(input_text) is None:
                continue

            normalized_name = _normalize_template_input_name(input_name)
            is_object_storage_input = (
                input_name in branch_inputs
                or normalized_name in MANAGED_OBJECT_STORAGE_TOGGLE_NAMES
                or _is_explicit_external_object_storage_input_name(normalized_name)
                or OBJECT_STORAGE_INPUT_TEXT_RE.search(input_text) is not None
            )
            if not is_object_storage_input:
                continue

            violations.append(
                Violation(
                    rule_id="R049",
                    path=doc.path,
                    line=_input_declaration_line(doc, input_name),
                    message=(
                        "license-gated object storage/S3 features must not be exposed as standard "
                        "public-template inputs; use the community-supported filesystem/PVC mode "
                        "or create a dedicated enterprise template only when explicitly requested"
                    ),
                )
            )

    return violations


def check_external_object_storage_inputs(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    object_storage_paths = {
        doc.path
        for doc in context.yaml_documents
        if not doc.skip_checks and isinstance(doc.data, dict) and doc.data.get("kind") == "ObjectStorageBucket"
    }

    for doc in _iter_template_artifact_documents(context):
        input_names = _external_object_storage_input_names(doc)
        if not input_names:
            continue

        if doc.path in object_storage_paths:
            add_doc_violation(
                violations,
                rule_id="R047",
                doc=doc,
                pattern=rf"^\s*{re.escape(input_names[0])}\s*:",
                default_pattern=r"^\s*inputs\s*:",
                message=(
                    "templates with managed ObjectStorageBucket resources must not expose external "
                    "S3/object-storage credential inputs"
                ),
            )
            continue

        source = _external_object_storage_source(doc)
        if source and _is_valid_object_storage_source_evidence(source):
            continue

        add_doc_violation(
            violations,
            rule_id="R047",
            doc=doc,
            pattern=rf"^\s*{re.escape(input_names[0])}\s*:",
            default_pattern=r"^\s*inputs\s*:",
            message=(
                f"external S3/object-storage input {input_names[0]} requires metadata.annotations."
                f"{EXTERNAL_OBJECT_STORAGE_SOURCE_ANNOTATION} with a credential-free HTTPS source URL or "
                "user-request:<reference> evidence"
            ),
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


def check_runtime_bundle_consistency(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    templates = _template_artifacts_by_name(context)

    for doc in _iter_runtime_bundle_evidence_documents(context):
        spec = _runtime_bundle_spec(doc)
        source = spec.get(RUNTIME_BUNDLE_SOURCE_FIELD)
        if not isinstance(source, str) or not source.strip():
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=rf"^\s*{re.escape(RUNTIME_BUNDLE_SOURCE_FIELD)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="runtime bundle evidence must declare spec.source",
            )
            continue

        app_name = spec.get("appName")
        if not isinstance(app_name, str) or not app_name.strip():
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=r"^\s*appName\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="runtime bundle evidence must declare spec.appName matching Template metadata.name",
            )
            continue

        template_doc = templates.get(app_name.strip())
        if template_doc is None:
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=r"^\s*appName\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle evidence spec.appName must match a Template metadata.name "
                    "in the scanned artifacts"
                ),
            )
            continue

        state = _collect_runtime_bundle_state(context, template_doc.path)
        expected_images = _split_runtime_bundle_values(spec.get(RUNTIME_BUNDLE_IMAGES_FIELD))
        expected_components = _split_runtime_bundle_values(spec.get(RUNTIME_BUNDLE_COMPONENTS_FIELD))
        expected_routes = _parse_runtime_bundle_routes(spec.get(RUNTIME_BUNDLE_ROUTES_FIELD))
        expected_envs = _split_runtime_bundle_values(spec.get(RUNTIME_BUNDLE_ENVS_FIELD))

        if not any((expected_images, expected_components, expected_routes, expected_envs)):
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle evidence must declare expected images, "
                    "components, routes, or env vars"
                ),
            )
            continue

        missing_images = [image for image in expected_images if image not in state["images"]]
        if missing_images:
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=rf"^\s*{re.escape(RUNTIME_BUNDLE_IMAGES_FIELD)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle image versions must match one official compose/release source; "
                    f"missing expected image(s): {', '.join(missing_images)}"
                ),
            )

        missing_components = [component for component in expected_components if component not in state["workloads"]]
        if missing_components:
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=rf"^\s*{re.escape(RUNTIME_BUNDLE_COMPONENTS_FIELD)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle components must be emitted as explicit managed workloads; "
                    f"missing component(s): {', '.join(missing_components)}"
                ),
            )

        missing_routes: List[str] = []
        for route_path, service_name in expected_routes:
            if not route_path or not service_name:
                missing_routes.append(f"{route_path or '<missing-path>'}=<missing-service>")
                continue
            if service_name not in state["services"] or (route_path, service_name) not in state["routes"]:
                missing_routes.append(f"{route_path}={service_name}")
        if missing_routes:
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=rf"^\s*{re.escape(RUNTIME_BUNDLE_ROUTES_FIELD)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle routes must expose official entry paths through matching Services "
                    f"and Ingress rules; missing route(s): {', '.join(missing_routes)}"
                ),
            )

        missing_envs = [env_name for env_name in expected_envs if env_name not in state["envs"]]
        if missing_envs:
            add_doc_violation(
                violations,
                rule_id="R046",
                doc=doc,
                pattern=rf"^\s*{re.escape(RUNTIME_BUNDLE_ENVS_FIELD)}\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "runtime bundle critical env vars must remain present on managed workloads; "
                    f"missing env var(s): {', '.join(missing_envs)}"
                ),
            )

    return violations


def check_topology_evidence_consistency(context: ScanContext) -> List[Violation]:
    violations: List[Violation] = []
    templates = _template_artifacts_by_name(context)

    for doc in _iter_topology_evidence_documents(context):
        spec = _runtime_bundle_spec(doc)
        app_name = spec.get("appName")
        source = spec.get("source")

        if not isinstance(app_name, str) or not app_name.strip():
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*appName\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="TopologyEvidence must declare spec.appName matching Template metadata.name",
            )
            continue
        app_name = app_name.strip()

        expected_path = doc.path.parent.name == TOPOLOGY_EVIDENCE_DIR and doc.path.parent.parent.name == ".sealos"
        if not expected_path or doc.path.name != f"{app_name}.yaml":
            violations.append(
                Violation(
                    rule_id="R050",
                    path=doc.path,
                    line=doc.start_line,
                    message=(
                        "TopologyEvidence must use .sealos/topology-evidence/<appName>.yaml; "
                        f"expected .sealos/topology-evidence/{app_name}.yaml"
                    ),
                )
            )

        if not isinstance(source, str) or not source.strip():
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*source\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="TopologyEvidence must declare a non-empty spec.source",
            )

        template_doc = templates.get(app_name)
        if template_doc is None:
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*appName\s*:",
                default_pattern=r"^\s*spec\s*:",
                message="TopologyEvidence spec.appName must match a Template in the scanned artifacts",
            )
            continue

        expected_records = _parse_topology_evidence_resources(doc, spec.get("resources"), violations)
        actual_records, docs_by_record = _collect_topology_records(context, template_doc.path, violations)
        if not expected_records:
            continue

        expected_counter = Counter(expected_records)
        actual_counter = Counter(actual_records)
        for record, count in (expected_counter - actual_counter).items():
            add_doc_violation(
                violations,
                rule_id="R050",
                doc=doc,
                pattern=r"^\s*resources\s*:",
                default_pattern=r"^\s*spec\s*:",
                message=(
                    "topology evidence resource is missing or changed in the template: "
                    f"{_topology_record_label(record)} (count={count})"
                ),
            )
        for record, count in (actual_counter - expected_counter).items():
            resource_doc = docs_by_record[record]
            violations.append(
                Violation(
                    rule_id="R050",
                    path=resource_doc.path,
                    line=resource_doc.start_line,
                    message=(
                        "template contains a topology resource absent from evidence: "
                        f"{_topology_record_label(record)} (count={count})"
                    ),
                )
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

        referenced_names: List[str] = []
        if isinstance(image_pull_secrets, list):
            for item in image_pull_secrets:
                if not isinstance(item, dict):
                    continue
                name = item.get("name")
                if isinstance(name, str) and name.strip():
                    referenced_names.append(name.strip())

        requires_pull_secret = any(_container_requires_image_pull_secret(container) for container in iter_containers(doc.data))
        has_pull_secret = len(referenced_names) > 0
        has_only_app_pull_secret = referenced_names == ["${{ defaults.app_name }}"]

        if requires_pull_secret and has_only_app_pull_secret:
            continue
        if not requires_pull_secret and not has_pull_secret:
            continue

        if requires_pull_secret:
            message = (
                "private-registry managed app workloads must reference only the app-scoped image pull secret "
                "`${{ defaults.app_name }}` via template.spec.imagePullSecrets"
            )
        else:
            message = "public-image managed app workloads must omit template.spec.imagePullSecrets"

        add_doc_violation(
            violations,
            rule_id="R035",
            doc=doc,
            pattern=r"^\s*imagePullSecrets\s*:",
            default_pattern=r"^\s*template\s*:",
            message=message,
        )

    return violations


def _container_requires_image_pull_secret(container: Dict[str, Any]) -> bool:
    image = container.get("image")
    if not isinstance(image, str):
        return False
    return any(image.strip().startswith(prefix) for prefix in PRIVATE_IMAGE_REGISTRY_PREFIXES)


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
    "R046": Rule("R046", check_runtime_bundle_consistency),
    "R050": Rule("R050", check_topology_evidence_consistency),
    "R036": Rule("R036", check_cronjob_required_labels),
    "R015": Rule("R015", check_origin_image_name_matches_container),
    "R020": Rule("R020", check_service_ports_have_names),
    "R029": Rule("R029", check_service_labels_match_selector_app),
    "R030": Rule("R030", check_configmap_labels_match_name),
    "R043": Rule("R043", check_configmap_file_mount_contract),
    "R044": Rule("R044", check_object_storage_input_contract),
    "R045": Rule("R045", check_template_input_references_declared),
    "R052": Rule("R052", check_template_default_scalar_types),
    "R047": Rule("R047", check_external_object_storage_inputs),
    "R049": Rule("R049", check_license_gated_object_storage_options),
    "R031": Rule("R031", check_ingress_name_matches_backends),
    "R051": Rule("R051", check_root_ingress_backend_port_numbers),
    "R026": Rule("R026", check_http_ingress_annotations),
    "R048": Rule("R048", check_websocket_ingress_annotations),
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
