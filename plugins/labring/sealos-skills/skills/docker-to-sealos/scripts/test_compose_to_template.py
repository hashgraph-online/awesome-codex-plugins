#!/usr/bin/env python3
import re
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock
from subprocess import CompletedProcess
from typing import Any, Dict, List, Optional

import yaml

from check_consistency_rule_registry import REGISTERED_RULES
from check_consistency_runner import run_checks
from compose_to_template import (
    MetadataOptions,
    ServiceShape,
    build_zh_description,
    convert_compose_to_template,
    find_svgl_logo_url,
    infer_metadata,
    parse_args,
    resolve_image_reference,
    resolve_kompose_shapes,
)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def parse_yaml_documents(path: Path):
    return list(yaml.safe_load_all(path.read_text(encoding="utf-8")))


def assert_db_visibility_labels(test_case: unittest.TestCase, cluster: Dict[str, Any], engine: str) -> None:
    name = cluster["metadata"]["name"]
    labels = cluster["metadata"]["labels"]
    test_case.assertEqual(name, labels.get("sealos-db-provider-cr"))
    test_case.assertEqual(name, labels.get("app.kubernetes.io/instance"))
    test_case.assertEqual(engine, labels.get("clusterdefinition.kubeblocks.io/name"))


def render_registry(include_paths: Optional[List[str]] = None) -> str:
    include_paths = include_paths or ["SKILL.md", "references/placeholder.md"]
    lines = ["version: 1", "scope:", "  include:"]
    for path in include_paths:
        lines.append(f"    - {path}")
    lines.append("rules:")
    for rule_id in sorted(REGISTERED_RULES.keys()):
        lines.append(f"  - id: {rule_id}")
        lines.append("    description: test")
        lines.append("    severity: error")
    return "\n".join(lines) + "\n"


class ComposeToTemplateTests(unittest.TestCase):
    def setUp(self):
        self._svgl_json_patcher = mock.patch("compose_to_template._read_json_url", return_value=[])
        self._svgl_json_patcher.start()

    def tearDown(self):
        self._svgl_json_patcher.stop()

    def _meta(self, app_name: str = "demo") -> MetadataOptions:
        return MetadataOptions(
            app_name=app_name,
            title="Demo",
            description="Demo app",
            url="https://demo.example.com",
            git_repo="https://github.com/example/demo",
            author="Sealos",
            categories=("tool",),
            repo_raw_base="https://raw.githubusercontent.com/labring-actions/templates/kb-0.9",
        )

    def test_generates_template_and_passes_consistency_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            output_dir = root / "template"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                    ports:
                      - "8080:80"
                    environment:
                      - NODE_ENV=production
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=output_dir,
                meta=self._meta("demo"),
            )

            self.assertTrue(index_path.exists())

            docs = parse_yaml_documents(index_path)
            kinds = [doc.get("kind") for doc in docs if isinstance(doc, dict)]
            self.assertEqual(["Template", "Deployment", "Service", "Ingress", "App"], kinds)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            zh = template["spec"]["i18n"]["zh"]
            self.assertNotIn("title", zh)
            self.assertRegex(zh["description"], re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]"))
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md",
                template["spec"]["readme"],
            )
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md",
                zh["readme"],
            )
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            self.assertEqual("tcp-80", service["spec"]["ports"][0]["name"])
            self.assertEqual("${{ defaults.app_name }}", service["metadata"]["name"])
            self.assertEqual("${{ defaults.app_name }}", service["spec"]["selector"]["app"])
            self.assertEqual("${{ defaults.app_name }}", service["metadata"]["labels"]["app"])
            self.assertEqual(
                "${{ defaults.app_name }}",
                service["metadata"]["labels"]["cloud.sealos.io/app-deploy-manager"],
            )
            ingress = next(doc for doc in docs if doc.get("kind") == "Ingress")
            backend_service_name = ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"]
            backend_service_port = ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["port"]
            self.assertEqual("${{ defaults.app_name }}", ingress["metadata"]["name"])
            self.assertEqual("${{ defaults.app_name }}", backend_service_name)
            self.assertEqual({"number": 80}, backend_service_port)
            self.assertEqual(
                "${{ defaults.app_name }}",
                ingress["metadata"]["labels"]["cloud.sealos.io/app-deploy-manager"],
            )
            workload = next(doc for doc in docs if doc.get("kind") == "Deployment")
            self.assertEqual(1, workload["spec"]["replicas"])
            self.assertEqual("1", workload["metadata"]["annotations"]["deploy.cloud.sealos.io/minReplicas"])
            self.assertEqual("1", workload["metadata"]["annotations"]["deploy.cloud.sealos.io/maxReplicas"])
            self.assertNotIn("imagePullSecrets", workload["spec"]["template"]["spec"])
            self.assertEqual(
                {
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
                },
                ingress["metadata"]["annotations"],
            )
            app = next(doc for doc in docs if doc.get("kind") == "App")
            self.assertEqual("normal", app["spec"]["displayType"])
            self.assertEqual("link", app["spec"]["type"])

            skill_root = Path(__file__).resolve().parent.parent
            checker_skill = root / "SKILL.md"
            checker_refs = root / "references"
            checker_registry = checker_refs / "rules-registry.yaml"
            write_file(checker_skill, "# local checker scope\n")
            write_file(checker_refs / "placeholder.md", "# refs\n")
            checker_registry.write_text(render_registry(), encoding="utf-8")
            violations = run_checks(
                skill_path=checker_skill,
                references_dir=checker_refs,
                registry_path=checker_registry,
                additional_include_paths=[str(index_path)],
            )
            self.assertEqual([], violations)

    def test_preserves_compose_deploy_replicas(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                    deploy:
                      replicas: 3
                """,
            )

            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )

            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") == "Deployment")
            self.assertEqual(3, workload["spec"]["replicas"])
            self.assertEqual("3", workload["metadata"]["annotations"]["deploy.cloud.sealos.io/minReplicas"])
            self.assertEqual("3", workload["metadata"]["annotations"]["deploy.cloud.sealos.io/maxReplicas"])

    def test_rejects_invalid_compose_deploy_replicas(self):
        invalid_values = ("0", "-1", "true", "'2'", "2.5")
        for invalid_value in invalid_values:
            with self.subTest(invalid_value=invalid_value), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                compose = root / "docker-compose.yml"
                write_file(
                    compose,
                    f"""
                    services:
                      app:
                        image: nginx:1.27.2
                        deploy:
                          replicas: {invalid_value}
                    """,
                )

                with self.assertRaisesRegex(ValueError, "deploy.replicas must be a positive integer"):
                    convert_compose_to_template(
                        compose_path=compose,
                        output_root=root / "template",
                        meta=self._meta("demo"),
                    )

    def test_uses_svgl_svg_logo_when_available(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                """,
            )

            with mock.patch("compose_to_template._read_json_url") as read_json:
                with mock.patch("compose_to_template._read_text_url", return_value='<svg viewBox="0 0 24 24"></svg>'):
                    read_json.return_value = [
                        {
                            "title": "Nginx",
                            "route": "https://svgl.app/library/nginx.svg",
                            "url": "https://nginx.org/",
                        }
                    ]
                    index_path, _ = convert_compose_to_template(
                        compose_path=compose,
                        output_root=root / "template",
                        meta=self._meta("nginx"),
                        fetch_logo=True,
                    )

            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            app = next(doc for doc in docs if doc.get("kind") == "App")
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/nginx/logo.svg",
                template["spec"]["icon"],
            )
            self.assertEqual(template["spec"]["icon"], app["spec"]["icon"])
            self.assertEqual('<svg viewBox="0 0 24 24"></svg>', (root / "template" / "nginx" / "logo.svg").read_text())

    def test_fetches_svgl_logo_by_default(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                """,
            )

            with mock.patch("compose_to_template._read_json_url") as read_json:
                with mock.patch("compose_to_template._read_text_url", return_value='<svg viewBox="0 0 24 24"></svg>'):
                    read_json.return_value = [
                        {
                            "title": "Nginx",
                            "route": "https://svgl.app/library/nginx.svg",
                            "url": "https://nginx.org/",
                        }
                    ]
                    index_path, _ = convert_compose_to_template(
                        compose_path=compose,
                        output_root=root / "template",
                        meta=self._meta("nginx"),
                    )

            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/nginx/logo.svg",
                template["spec"]["icon"],
            )

    def test_can_disable_default_svgl_logo_search(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                """,
            )

            with mock.patch("compose_to_template._read_json_url") as read_json:
                index_path, _ = convert_compose_to_template(
                    compose_path=compose,
                    output_root=root / "template",
                    meta=self._meta("nginx"),
                    fetch_logo=False,
                )

            read_json.assert_not_called()
            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/nginx/logo.png",
                template["spec"]["icon"],
            )

    def test_keeps_png_icon_path_when_svgl_search_misses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )

            with mock.patch("compose_to_template._read_json_url", return_value=[]):
                index_path, _ = convert_compose_to_template(
                    compose_path=compose,
                    output_root=root / "template",
                    meta=self._meta("demo"),
                    fetch_logo=True,
                )

            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png",
                template["spec"]["icon"],
            )
            self.assertFalse((root / "template" / "demo" / "logo.svg").exists())

    def test_uses_existing_logo_extension_when_svgl_search_misses(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            output_dir = root / "template"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            write_file(output_dir / "demo" / "logo.webp", "webp")

            with mock.patch("compose_to_template._read_json_url", return_value=[]):
                index_path, _ = convert_compose_to_template(
                    compose_path=compose,
                    output_root=output_dir,
                    meta=self._meta("demo"),
                    fetch_logo=True,
                )

            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            self.assertEqual(
                "https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.webp",
                template["spec"]["icon"],
            )

    def test_find_svgl_logo_url_prefers_matching_title_and_domain(self):
        meta = MetadataOptions(
            app_name="open-webui",
            title="Open WebUI",
            description="Demo app",
            url="https://openwebui.com/",
            git_repo="https://github.com/open-webui/open-webui",
            author="Sealos",
            categories=("ai",),
            repo_raw_base="https://raw.githubusercontent.com/labring-actions/templates/kb-0.9",
        )

        def fake_read_json(url):
            return [
                {
                    "title": "Open WebUI Docs",
                    "route": "https://svgl.app/library/openwebui-docs.svg",
                    "url": "https://docs.openwebui.com/",
                },
                {
                    "title": "Open WebUI",
                    "route": "https://svgl.app/library/openwebui.svg",
                    "url": "https://openwebui.com/",
                },
            ]

        with mock.patch("compose_to_template._read_json_url", side_effect=fake_read_json):
            self.assertEqual("https://svgl.app/library/openwebui.svg", find_svgl_logo_url(meta))

    def test_service_ports_always_include_names_for_multi_port_services(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - "9000:9000"
                      - "9443:9443"
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            ports = service["spec"]["ports"]
            self.assertEqual("tcp-9000", ports[0]["name"])
            self.assertEqual("tcp-9443", ports[1]["name"])
            workload = next(doc for doc in docs if doc.get("kind") == "Deployment")
            self.assertEqual(
                [{"name": "${{ defaults.app_name }}"}],
                workload["spec"]["template"]["spec"]["imagePullSecrets"],
            )

    def test_generates_websocket_ingress_for_named_websocket_port(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - target: 3000
                        published: 3000
                        protocol: tcp
                        name: websocket
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            ingress = next(doc for doc in docs if doc.get("kind") == "Ingress")

            container_port = workload["spec"]["template"]["spec"]["containers"][0]["ports"][0]
            service_port = service["spec"]["ports"][0]
            self.assertEqual("websocket", container_port["name"])
            self.assertEqual("websocket", service_port["name"])
            self.assertEqual(
                {
                    "kubernetes.io/ingress.class": "nginx",
                    "nginx.ingress.kubernetes.io/proxy-body-size": "32m",
                    "nginx.ingress.kubernetes.io/proxy-read-timeout": "3600",
                    "nginx.ingress.kubernetes.io/proxy-send-timeout": "3600",
                    "nginx.ingress.kubernetes.io/backend-protocol": "WS",
                    "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                },
                ingress["metadata"]["annotations"],
            )

    def test_generates_websocket_ingress_for_websocket_url_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - "3000:3000"
                    environment:
                      PUBLIC_WEBSOCKET_URL: wss://demo.example.com
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            ingress = next(doc for doc in docs if doc.get("kind") == "Ingress")

            self.assertEqual("tcp-3000", service["spec"]["ports"][0]["name"])
            self.assertEqual("WS", ingress["metadata"]["annotations"]["nginx.ingress.kubernetes.io/backend-protocol"])
            self.assertEqual(
                "3600",
                ingress["metadata"]["annotations"]["nginx.ingress.kubernetes.io/proxy-read-timeout"],
            )

    def test_drops_https_port_when_http_port_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - "80:80"
                      - "443:443"
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            service = next(doc for doc in docs if doc.get("kind") == "Service")

            container_ports = [item["containerPort"] for item in workload["spec"]["template"]["spec"]["containers"][0]["ports"]]
            service_ports = [item["port"] for item in service["spec"]["ports"]]
            self.assertEqual([80], container_ports)
            self.assertEqual([80], service_ports)

    def test_filters_tls_certificate_mounts_from_persistent_storage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    volumes:
                      - certs:/etc/nginx/ssl
                      - data:/var/lib/demo
                volumes:
                  certs: {}
                  data: {}
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") == "StatefulSet")

            mounts = workload["spec"]["template"]["spec"]["containers"][0]["volumeMounts"]
            mount_paths = [item["mountPath"] for item in mounts]
            self.assertEqual(["/var/lib/demo"], mount_paths)

    def test_generates_configmap_file_mounts_from_compose_configs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(root / "config" / "app-config.yaml", "mode: production\n")
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:1.27.2
                    configs:
                      - source: app_config
                        target: /opt/demo/app-config.yaml
                configs:
                  app_config:
                    file: ./config/app-config.yaml
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            kinds = [doc.get("kind") for doc in docs if isinstance(doc, dict)]
            self.assertEqual(["Template", "ConfigMap", "Deployment", "App"], kinds)

            key = "vn-optvn-demovn-appvn-configvn-yaml"
            configmap = next(doc for doc in docs if doc.get("kind") == "ConfigMap")
            self.assertEqual("${{ defaults.app_name }}", configmap["metadata"]["name"])
            self.assertEqual(
                {
                    "app": "${{ defaults.app_name }}",
                    "cloud.sealos.io/app-deploy-manager": "${{ defaults.app_name }}",
                },
                configmap["metadata"]["labels"],
            )
            self.assertEqual({"mode": "production"}, yaml.safe_load(configmap["data"][key]))

            workload = next(doc for doc in docs if doc.get("kind") == "Deployment")
            self.assertNotIn("volumeClaimTemplates", workload["spec"])
            pod_spec = workload["spec"]["template"]["spec"]
            self.assertNotIn("imagePullSecrets", pod_spec)
            self.assertEqual(
                [
                    {
                        "name": "${{ defaults.app_name }}-cm",
                        "mountPath": "/opt/demo/app-config.yaml",
                        "subPath": key,
                        "readOnly": True,
                    }
                ],
                pod_spec["containers"][0]["volumeMounts"],
            )
            self.assertEqual(
                [
                    {
                        "name": "${{ defaults.app_name }}-cm",
                        "configMap": {"name": "${{ defaults.app_name }}"},
                    }
                ],
                pod_spec["volumes"],
            )

    def test_template_defaults_keep_double_brace_placeholders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            template = next(doc for doc in docs if doc.get("kind") == "Template")
            defaults = template["spec"]["defaults"]
            self.assertEqual("demo-${{ random(8) }}", defaults["app_host"]["value"])
            self.assertEqual("demo-${{ random(8) }}", defaults["app_name"]["value"])

    def test_secondary_workload_name_keeps_double_brace_placeholders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  web:
                    image: ghcr.io/example/demo:1.0.0
                  worker:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workloads = [doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"}]
            names = [doc["metadata"]["name"] for doc in workloads]
            self.assertIn("${{ defaults.app_name }}", names)
            self.assertIn("${{ defaults.app_name }}-worker", names)

    def test_skips_traefik_gateway_when_business_service_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  traefik:
                    image: traefik:v3.1.4
                    ports:
                      - "80:80"
                      - "443:443"
                    command:
                      - --entrypoints.web.address=:80
                      - --entrypoints.websecure.address=:443
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - "3000:3000"
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workloads = [doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"}]
            self.assertEqual(1, len(workloads))
            container_image = workloads[0]["spec"]["template"]["spec"]["containers"][0]["image"]
            self.assertEqual("ghcr.io/example/demo:1.0.0", container_image)

            ingress = next(doc for doc in docs if doc.get("kind") == "Ingress")
            backend_service = ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"]
            self.assertEqual("${{ defaults.app_name }}", backend_service)

    def test_keeps_traefik_when_it_is_only_application_service(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  traefik:
                    image: traefik:v3.1.4
                    ports:
                      - "80:80"
                      - "443:443"
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            container_image = workload["spec"]["template"]["spec"]["containers"][0]["image"]
            self.assertEqual("traefik:v3.1.4", container_image)

    def test_maps_compose_command_to_container_args(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    command:
                      - server
                      - --port
                      - "9000"
                  worker:
                    image: ghcr.io/example/demo:1.0.0
                    command: worker --log-level info
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workloads = [doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"}]
            app_workload = next(doc for doc in workloads if doc["metadata"]["name"] == "${{ defaults.app_name }}")
            worker_workload = next(
                doc for doc in workloads if doc["metadata"]["name"] == "${{ defaults.app_name }}-worker"
            )
            app_args = app_workload["spec"]["template"]["spec"]["containers"][0].get("args")
            worker_args = worker_workload["spec"]["template"]["spec"]["containers"][0].get("args")
            self.assertEqual(["server", "--port", "9000"], app_args)
            self.assertEqual(["worker", "--log-level", "info"], worker_args)

    def test_generates_http_liveness_and_readiness_for_official_authentik_server(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  server:
                    image: ghcr.io/goauthentik/server:2025.12.3
                    command:
                      - server
                    ports:
                      - "9000:9000"
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("authentik"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            container = workload["spec"]["template"]["spec"]["containers"][0]

            liveness = container.get("livenessProbe", {})
            readiness = container.get("readinessProbe", {})
            startup = container.get("startupProbe", {})
            self.assertEqual("/-/health/live/", liveness.get("httpGet", {}).get("path"))
            self.assertEqual(9000, liveness.get("httpGet", {}).get("port"))
            self.assertEqual("/-/health/ready/", readiness.get("httpGet", {}).get("path"))
            self.assertEqual(9000, readiness.get("httpGet", {}).get("port"))
            self.assertEqual("/-/health/ready/", startup.get("httpGet", {}).get("path"))
            self.assertEqual(9000, startup.get("httpGet", {}).get("port"))
            self.assertEqual(90, startup.get("failureThreshold"))

    def test_generates_exec_liveness_and_readiness_for_official_authentik_worker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  worker:
                    image: ghcr.io/goauthentik/server:2025.12.3
                    command:
                      - worker
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("authentik"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            container = workload["spec"]["template"]["spec"]["containers"][0]

            liveness_cmd = container.get("livenessProbe", {}).get("exec", {}).get("command", [])
            readiness_cmd = container.get("readinessProbe", {}).get("exec", {}).get("command", [])
            startup_cmd = container.get("startupProbe", {}).get("exec", {}).get("command", [])
            self.assertIn("ak healthcheck", " ".join(str(item) for item in liveness_cmd))
            self.assertIn("ak healthcheck", " ".join(str(item) for item in readiness_cmd))
            self.assertIn("ak healthcheck", " ".join(str(item) for item in startup_cmd))

    def test_maps_compose_healthcheck_to_liveness_and_readiness(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    ports:
                      - "8080:8080"
                    healthcheck:
                      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
                      interval: 20s
                      timeout: 3s
                      retries: 4
                      start_period: 15s
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            container = workload["spec"]["template"]["spec"]["containers"][0]

            liveness = container.get("livenessProbe", {})
            readiness = container.get("readinessProbe", {})
            startup = container.get("startupProbe", {})
            self.assertEqual("/healthz", liveness.get("httpGet", {}).get("path"))
            self.assertEqual(8080, liveness.get("httpGet", {}).get("port"))
            self.assertEqual(20, liveness.get("periodSeconds"))
            self.assertEqual(3, liveness.get("timeoutSeconds"))
            self.assertEqual(4, liveness.get("failureThreshold"))
            self.assertEqual(15, liveness.get("initialDelaySeconds"))
            self.assertEqual("/healthz", readiness.get("httpGet", {}).get("path"))
            self.assertEqual(8080, readiness.get("httpGet", {}).get("port"))
            self.assertEqual("/healthz", startup.get("httpGet", {}).get("path"))
            self.assertEqual(8080, startup.get("httpGet", {}).get("port"))
            self.assertEqual(1, startup.get("failureThreshold"))

    def test_skips_socket_mount_from_stateful_storage_conversion(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    volumes:
                      - /var/run/docker.sock:/var/run/docker.sock
                      - data:/data
                volumes:
                  data: {}
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") == "StatefulSet")
            self.assertEqual(
                {
                    "cloud.sealos.io/app-deploy-manager": "${{ defaults.app_name }}",
                    "app": "${{ defaults.app_name }}",
                },
                workload["metadata"]["labels"],
            )
            mounts = workload["spec"]["template"]["spec"]["containers"][0]["volumeMounts"]
            mount_paths = [item["mountPath"] for item in mounts]
            self.assertEqual(["/data"], mount_paths)
            pvcs = workload["spec"]["volumeClaimTemplates"]
            pvc_names = [item["metadata"]["name"] for item in pvcs]
            self.assertEqual(["vn-data"], pvc_names)
            self.assertNotIn("labels", pvcs[0]["metadata"])

    def test_rejects_latest_image_tag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: nginx:latest
                """,
            )
            with self.assertRaises(ValueError):
                convert_compose_to_template(
                    compose_path=compose,
                    output_root=root / "template",
                    meta=self._meta("demo"),
                )

    def test_resolves_compose_image_default_expressions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ${APP_IMAGE:-ghcr.io/example/demo}:${APP_TAG:-1.2.3}
                """,
            )
            with mock.patch.dict("os.environ", {}, clear=False):
                index_path, _ = convert_compose_to_template(
                    compose_path=compose,
                    output_root=root / "template",
                    meta=self._meta("demo"),
                )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            image = workload["spec"]["template"]["spec"]["containers"][0]["image"]
            origin = workload["metadata"]["annotations"]["originImageName"]
            self.assertEqual("ghcr.io/example/demo:1.2.3", image)
            self.assertEqual("ghcr.io/example/demo:1.2.3", origin)

    def test_rejects_unresolved_compose_image_variable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ${APP_IMAGE}
                """,
            )
            with mock.patch.dict("os.environ", {}, clear=False):
                with self.assertRaises(ValueError):
                    convert_compose_to_template(
                        compose_path=compose,
                        output_root=root / "template",
                        meta=self._meta("demo"),
                    )

    def test_generates_postgres_resources_and_secret_db_env_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      DB_HOST: postgres
                      DB_PORT: "5432"
                      DB_USER: postgres
                      DB_PASSWORD: super-secret
                      DATABASE_URL: postgres://postgres:super-secret@postgres:5432/postgres
                  postgres:
                    image: postgres:16.4
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            kinds = [doc.get("kind") for doc in docs if isinstance(doc, dict)]

            self.assertIn("ServiceAccount", kinds)
            self.assertIn("Role", kinds)
            self.assertIn("RoleBinding", kinds)
            self.assertIn("Cluster", kinds)

            cluster = next(doc for doc in docs if doc.get("kind") == "Cluster")
            self.assertEqual("${{ defaults.app_name }}-pg", cluster["metadata"]["name"])
            self.assertIn("kb.io/database", cluster["metadata"]["labels"])
            assert_db_visibility_labels(self, cluster, "postgresql")
            self.assertNotIn("finalizers", cluster["metadata"])
            self.assertNotIn("annotations", cluster["metadata"])
            affinity = cluster["spec"]["affinity"]
            self.assertNotIn("nodeLabels", affinity)
            self.assertNotIn("topologyKeys", affinity)
            pg_comp = cluster["spec"]["componentSpecs"][0]
            self.assertEqual("500m", pg_comp["resources"]["limits"]["cpu"])
            self.assertEqual("512Mi", pg_comp["resources"]["limits"]["memory"])
            self.assertEqual("50m", pg_comp["resources"]["requests"]["cpu"])
            self.assertEqual("51Mi", pg_comp["resources"]["requests"]["memory"])

            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]
            host_item = next(item for item in env if item["name"] == "DB_HOST")
            port_item = next(item for item in env if item["name"] == "DB_PORT")
            user_item = next(item for item in env if item["name"] == "DB_USER")
            password_item = next(item for item in env if item["name"] == "DB_PASSWORD")
            endpoint_item = next(item for item in env if item["name"] == "DATABASE_URL")

            for item, key in (
                (host_item, "host"),
                (port_item, "port"),
                (user_item, "username"),
                (password_item, "password"),
            ):
                secret_ref = item.get("valueFrom", {}).get("secretKeyRef", {})
                self.assertEqual("${{ defaults.app_name }}-pg-conn-credential", secret_ref.get("name"))
                self.assertEqual(key, secret_ref.get("key"))

            self.assertEqual(
                "postgres://$(SEALOS_DATABASE_POSTGRES_USERNAME):$(SEALOS_DATABASE_POSTGRES_PASSWORD)"
                "@$(SEALOS_DATABASE_POSTGRES_HOST):$(SEALOS_DATABASE_POSTGRES_PORT)/postgres",
                endpoint_item.get("value"),
            )
            for helper_name, key in (
                ("SEALOS_DATABASE_POSTGRES_HOST", "host"),
                ("SEALOS_DATABASE_POSTGRES_PORT", "port"),
                ("SEALOS_DATABASE_POSTGRES_USERNAME", "username"),
                ("SEALOS_DATABASE_POSTGRES_PASSWORD", "password"),
            ):
                helper_item = next(item for item in env if item["name"] == helper_name)
                secret_ref = helper_item.get("valueFrom", {}).get("secretKeyRef", {})
                self.assertEqual("${{ defaults.app_name }}-pg-conn-credential", secret_ref.get("name"))
                self.assertEqual(key, secret_ref.get("key"))

    def test_uses_statefulset_when_service_has_persistent_mount(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    volumes:
                      - data:/var/lib/demo
                    ports:
                      - "3000:3000"
                volumes:
                  data: {}
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            workload = next(doc for doc in docs if doc.get("kind") in {"Deployment", "StatefulSet"})
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            ingress = next(doc for doc in docs if doc.get("kind") == "Ingress")
            self.assertEqual("StatefulSet", workload["kind"])
            self.assertIn("volumeClaimTemplates", workload["spec"])
            self.assertEqual(workload["metadata"]["name"], workload["spec"]["serviceName"])
            self.assertEqual(workload["metadata"]["name"], service["metadata"]["name"])
            self.assertEqual(
                service["metadata"]["name"],
                ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]["name"],
            )
            request = workload["spec"]["volumeClaimTemplates"][0]["spec"]["resources"]["requests"]["storage"]
            self.assertEqual("1Gi", request)

    def test_generates_redis_cluster_resources_and_secret_env_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      REDIS_HOST: redis
                      REDIS_PORT: "6379"
                      REDIS_PASSWORD: super-secret
                      REDIS_URL: redis://:super-secret@redis:6379/0
                  redis:
                    image: redis:7.2.7
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            kinds = [doc.get("kind") for doc in docs if isinstance(doc, dict)]
            self.assertIn("ServiceAccount", kinds)
            self.assertIn("Role", kinds)
            self.assertIn("RoleBinding", kinds)
            self.assertIn("Deployment", kinds)
            self.assertIn("Cluster", kinds)

            cluster = next(doc for doc in docs if doc.get("kind") == "Cluster")
            assert_db_visibility_labels(self, cluster, "redis")
            component_names = {item["name"] for item in cluster["spec"]["componentSpecs"]}
            self.assertEqual({"redis", "redis-sentinel"}, component_names)
            redis_comp = next(item for item in cluster["spec"]["componentSpecs"] if item["name"] == "redis")
            redis_data = redis_comp["volumeClaimTemplates"][0]["spec"]["resources"]["requests"]["storage"]
            self.assertEqual("1Gi", redis_data)
            self.assertEqual("500m", redis_comp["resources"]["limits"]["cpu"])
            self.assertEqual("512Mi", redis_comp["resources"]["limits"]["memory"])
            self.assertEqual("50m", redis_comp["resources"]["requests"]["cpu"])
            self.assertEqual("51Mi", redis_comp["resources"]["requests"]["memory"])
            sentinel_comp = next(item for item in cluster["spec"]["componentSpecs"] if item["name"] == "redis-sentinel")
            self.assertEqual("500m", sentinel_comp["resources"]["limits"]["cpu"])
            self.assertEqual("512Mi", sentinel_comp["resources"]["limits"]["memory"])
            self.assertEqual("50m", sentinel_comp["resources"]["requests"]["cpu"])
            self.assertEqual("51Mi", sentinel_comp["resources"]["requests"]["memory"])

            raw_redis_workloads = []
            for doc in docs:
                if doc.get("kind") not in {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}:
                    continue
                containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
                if any(item.get("image", "").split(":", 1)[0].rsplit("/", 1)[-1] == "redis" for item in containers):
                    raw_redis_workloads.append(doc)
            self.assertEqual([], raw_redis_workloads)

            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]
            env_by_name = {item["name"]: item for item in env}
            redis_host = env_by_name["REDIS_HOST"]
            self.assertEqual(
                "${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc.cluster.local",
                redis_host.get("value"),
            )
            self.assertEqual("6379", env_by_name["REDIS_PORT"].get("value"))
            self.assertEqual(
                {
                    "name": "${{ defaults.app_name }}-redis-redis-account-default",
                    "key": "password",
                },
                env_by_name["REDIS_PASSWORD"]["valueFrom"]["secretKeyRef"],
            )
            self.assertEqual(
                {
                    "name": "${{ defaults.app_name }}-redis-redis-account-default",
                    "key": "password",
                },
                env_by_name["SEALOS_REDIS_REDIS_PASSWORD"]["valueFrom"]["secretKeyRef"],
            )
            self.assertEqual(
                "redis://:$(SEALOS_REDIS_REDIS_PASSWORD)@$(SEALOS_REDIS_REDIS_HOST):$(SEALOS_REDIS_REDIS_PORT)/0",
                env_by_name["REDIS_URL"].get("value"),
            )

    def test_generates_mysql_cluster_resources_and_secret_env_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      MYSQL_HOST: mysql
                      MYSQL_PORT: "3306"
                  mysql:
                    image: mysql:8.0.35
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            cluster = next(doc for doc in docs if doc.get("kind") == "Cluster")
            self.assertEqual("${{ defaults.app_name }}-mysql", cluster["metadata"]["name"])
            assert_db_visibility_labels(self, cluster, "apecloud-mysql")
            self.assertNotIn("finalizers", cluster["metadata"])
            self.assertNotIn("annotations", cluster["metadata"])
            self.assertEqual(["kubernetes.io/hostname"], cluster["spec"]["affinity"]["topologyKeys"])
            mysql_comp = cluster["spec"]["componentSpecs"][0]
            self.assertEqual("500m", mysql_comp["resources"]["limits"]["cpu"])
            self.assertEqual("512Mi", mysql_comp["resources"]["limits"]["memory"])
            self.assertEqual("50m", mysql_comp["resources"]["requests"]["cpu"])
            self.assertEqual("51Mi", mysql_comp["resources"]["requests"]["memory"])

            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]
            mysql_host = next(item for item in env if item["name"] == "MYSQL_HOST")
            mysql_port = next(item for item in env if item["name"] == "MYSQL_PORT")

            host_ref = mysql_host.get("valueFrom", {}).get("secretKeyRef", {})
            port_ref = mysql_port.get("valueFrom", {}).get("secretKeyRef", {})
            self.assertEqual("${{ defaults.app_name }}-mysql-conn-credential", host_ref.get("name"))
            self.assertEqual("host", host_ref.get("key"))
            self.assertEqual("${{ defaults.app_name }}-mysql-conn-credential", port_ref.get("name"))
            self.assertEqual("port", port_ref.get("key"))

    def test_generates_mongodb_cluster_resources_and_secret_env_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      MONGO_HOST: mongo
                  mongo:
                    image: mongo:8.0.4
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            cluster = next(doc for doc in docs if doc.get("kind") == "Cluster")
            self.assertEqual("${{ defaults.app_name }}-mongo", cluster["metadata"]["name"])
            assert_db_visibility_labels(self, cluster, "mongodb")
            self.assertNotIn("finalizers", cluster["metadata"])
            self.assertNotIn("annotations", cluster["metadata"])
            mongo_comp = cluster["spec"]["componentSpecs"][0]
            self.assertEqual("mongodb", mongo_comp["componentDef"])
            self.assertEqual("8.0.4", mongo_comp["serviceVersion"])
            self.assertEqual("500m", mongo_comp["resources"]["limits"]["cpu"])
            self.assertEqual("512Mi", mongo_comp["resources"]["limits"]["memory"])
            self.assertEqual("50m", mongo_comp["resources"]["requests"]["cpu"])
            self.assertEqual("51Mi", mongo_comp["resources"]["requests"]["memory"])

            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]
            mongo_host = next(item for item in env if item["name"] == "MONGO_HOST")
            host_ref = mongo_host.get("valueFrom", {}).get("secretKeyRef", {})
            self.assertEqual("${{ defaults.app_name }}-mongo-mongodb-account-root", host_ref.get("name"))
            self.assertEqual("host", host_ref.get("key"))

    def test_composes_mongodb_url_with_service_host_and_credential_secret(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      MONGODB_URI: mongodb://root:password@mongo:27017/demo?authSource=admin
                  mongo:
                    image: mongo:8.0.4
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]

            host = next(item for item in env if item["name"] == "SEALOS_MONGODB_MONGODB_HOST")
            port = next(item for item in env if item["name"] == "SEALOS_MONGODB_MONGODB_PORT")
            username = next(item for item in env if item["name"] == "SEALOS_MONGODB_MONGODB_USERNAME")
            password = next(item for item in env if item["name"] == "SEALOS_MONGODB_MONGODB_PASSWORD")
            uri = next(item for item in env if item["name"] == "MONGODB_URI")

            self.assertEqual("${{ defaults.app_name }}-mongo-mongodb.${{ SEALOS_NAMESPACE }}.svc.cluster.local", host["value"])
            self.assertEqual("27017", port["value"])
            self.assertEqual("${{ defaults.app_name }}-mongo-mongodb-account-root", username["valueFrom"]["secretKeyRef"]["name"])
            self.assertEqual("username", username["valueFrom"]["secretKeyRef"]["key"])
            self.assertEqual("${{ defaults.app_name }}-mongo-mongodb-account-root", password["valueFrom"]["secretKeyRef"]["name"])
            self.assertEqual("password", password["valueFrom"]["secretKeyRef"]["key"])
            self.assertEqual(
                "mongodb://$(SEALOS_MONGODB_MONGODB_USERNAME):$(SEALOS_MONGODB_MONGODB_PASSWORD)@$(SEALOS_MONGODB_MONGODB_HOST):$(SEALOS_MONGODB_MONGODB_PORT)/demo?authSource=admin",
                uri["value"],
            )

    def test_generates_kafka_cluster_resources_and_secret_env_mapping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                    environment:
                      KAFKA_HOST: kafka
                  kafka:
                    image: bitnami/kafka:3.3.2
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
            )
            docs = parse_yaml_documents(index_path)
            cluster = next(doc for doc in docs if doc.get("kind") == "Cluster")
            self.assertEqual("${{ defaults.app_name }}-broker", cluster["metadata"]["name"])
            assert_db_visibility_labels(self, cluster, "kafka")
            broker_comp = next(item for item in cluster["spec"]["componentSpecs"] if item["name"] == "broker")
            controller_comp = next(item for item in cluster["spec"]["componentSpecs"] if item["name"] == "controller")
            metrics_comp = next(item for item in cluster["spec"]["componentSpecs"] if item["name"] == "metrics-exp")
            for comp in (broker_comp, controller_comp, metrics_comp):
                self.assertEqual("500m", comp["resources"]["limits"]["cpu"])
                self.assertEqual("512Mi", comp["resources"]["limits"]["memory"])
                self.assertEqual("50m", comp["resources"]["requests"]["cpu"])
                self.assertEqual("51Mi", comp["resources"]["requests"]["memory"])

            deployment = next(doc for doc in docs if doc.get("kind") == "Deployment")
            env = deployment["spec"]["template"]["spec"]["containers"][0]["env"]
            kafka_host = next(item for item in env if item["name"] == "KAFKA_HOST")
            host_ref = kafka_host.get("valueFrom", {}).get("secretKeyRef", {})
            self.assertEqual("${{ defaults.app_name }}-broker-account-admin", host_ref.get("name"))
            self.assertEqual("host", host_ref.get("key"))

    def test_applies_kompose_shape_when_compose_ports_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            compose = root / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            index_path, _ = convert_compose_to_template(
                compose_path=compose,
                output_root=root / "template",
                meta=self._meta("demo"),
                kompose_shapes={"app": ServiceShape(ports=(8080,), mount_paths=())},
            )
            docs = parse_yaml_documents(index_path)
            service = next(doc for doc in docs if doc.get("kind") == "Service")
            self.assertEqual(8080, service["spec"]["ports"][0]["port"])

    def test_resolve_kompose_shapes_always_requires_binary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose = Path(temp_dir) / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            with mock.patch("compose_to_template.shutil.which", return_value=None):
                with self.assertRaises(ValueError):
                    resolve_kompose_shapes(compose, "always")

    def test_resolve_kompose_shapes_auto_falls_back_when_binary_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            compose = Path(temp_dir) / "docker-compose.yml"
            write_file(
                compose,
                """
                services:
                  app:
                    image: ghcr.io/example/demo:1.0.0
                """,
            )
            with mock.patch("compose_to_template.shutil.which", return_value=None):
                self.assertIsNone(resolve_kompose_shapes(compose, "auto"))

    def test_parse_args_defaults_to_always_kompose_mode(self):
        args = parse_args(["--compose", "docker-compose.yml"])
        self.assertEqual("always", args.kompose_mode)

    def test_parse_args_supports_disabling_default_logo_fetch(self):
        args = parse_args(["--compose", "docker-compose.yml", "--no-fetch-logo"])
        self.assertTrue(args.no_fetch_logo)

    def test_infer_metadata_normalizes_categories_to_allowlist(self):
        args = parse_args(
            [
                "--compose",
                "docker-compose.yml",
                "--category",
                "security",
                "--category",
                "devops",
                "--category",
                "tool",
            ]
        )
        compose_data = {"services": {"app": {"image": "ghcr.io/example/demo:1.0.0"}}}
        meta = infer_metadata(args, compose_data, Path("docker-compose.yml"))
        self.assertEqual(("backend", "dev-ops", "tool"), meta.categories)

    def test_infer_metadata_falls_back_to_tool_for_unknown_categories(self):
        args = parse_args(
            [
                "--compose",
                "docker-compose.yml",
                "--category",
                "security-policy",
            ]
        )
        compose_data = {"services": {"app": {"image": "ghcr.io/example/demo:1.0.0"}}}
        meta = infer_metadata(args, compose_data, Path("docker-compose.yml"))
        self.assertEqual(("tool",), meta.categories)

    def test_build_zh_description_rewrites_identity_platform_description(self):
        zh_description = build_zh_description(
            "ZITADEL",
            "Open-source identity and access management platform for authentication and authorization.",
        )
        self.assertEqual("开源身份与访问管理平台，提供认证与授权能力。", zh_description)

    def test_build_zh_description_keeps_existing_chinese_text(self):
        zh_description = build_zh_description(
            "Demo",
            "开源身份与访问管理平台，提供认证与授权能力。",
        )
        self.assertEqual("开源身份与访问管理平台，提供认证与授权能力。", zh_description)

    def test_resolve_image_reference_promotes_floating_tag_to_precise_version(self):
        image = "ghcr.io/example/demo:v2"

        def fake_run(command, capture_output=True, text=True):  # noqa: ANN001
            if command[-2:] == ["digest", "ghcr.io/example/demo:v2"]:
                return CompletedProcess(command, 0, stdout="sha256:abc\n", stderr="")
            if command[-2:] == ["ls", "ghcr.io/example/demo"]:
                return CompletedProcess(command, 0, stdout="v2\nv2.2.0\nv2.1.9\n", stderr="")
            if command[-2:] == ["digest", "ghcr.io/example/demo:v2.2.0"]:
                return CompletedProcess(command, 0, stdout="sha256:abc\n", stderr="")
            if command[-2:] == ["digest", "ghcr.io/example/demo:v2.1.9"]:
                return CompletedProcess(command, 0, stdout="sha256:def\n", stderr="")
            return CompletedProcess(command, 1, stdout="", stderr="unexpected command")

        with mock.patch("compose_to_template.shutil.which", return_value="/usr/local/bin/crane"):
            with mock.patch("compose_to_template.subprocess.run", side_effect=fake_run):
                resolved = resolve_image_reference(image)

        self.assertEqual("ghcr.io/example/demo:v2.2.0", resolved)

    def test_resolve_image_reference_falls_back_to_digest_when_no_precise_tag_matches(self):
        image = "ghcr.io/example/demo:v2"

        def fake_run(command, capture_output=True, text=True):  # noqa: ANN001
            if command[-2:] == ["digest", "ghcr.io/example/demo:v2"]:
                return CompletedProcess(command, 0, stdout="sha256:abc\n", stderr="")
            if command[-2:] == ["ls", "ghcr.io/example/demo"]:
                return CompletedProcess(command, 0, stdout="v2\nv2.2.0\n", stderr="")
            if command[-2:] == ["digest", "ghcr.io/example/demo:v2.2.0"]:
                return CompletedProcess(command, 0, stdout="sha256:def\n", stderr="")
            return CompletedProcess(command, 1, stdout="", stderr="unexpected command")

        with mock.patch("compose_to_template.shutil.which", return_value="/usr/local/bin/crane"):
            with mock.patch("compose_to_template.subprocess.run", side_effect=fake_run):
                resolved = resolve_image_reference(image)

        self.assertEqual("ghcr.io/example/demo@sha256:abc", resolved)


if __name__ == "__main__":
    unittest.main()
