#!/usr/bin/env python3
import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any, Dict, Optional

from check_consistency_line_locator import LineLocator
from check_consistency_rule_helpers import iter_containers as legacy_iter_containers
from check_consistency_helpers_workload import iter_containers
import check_consistency_rules_app as APP_RULES_MODULE


MODULE_PATH = Path(__file__).resolve().parent / "check_consistency.py"
MODULE_SPEC = importlib.util.spec_from_file_location("check_consistency", MODULE_PATH)
CHECKER = importlib.util.module_from_spec(MODULE_SPEC)
sys.modules[MODULE_SPEC.name] = CHECKER
assert MODULE_SPEC.loader is not None
MODULE_SPEC.loader.exec_module(CHECKER)


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def render_registry(
    overrides: Optional[Dict[str, Dict[str, Any]]] = None,
    include_paths: Optional[list[str]] = None,
) -> str:
    overrides = overrides or {}
    include_paths = include_paths or ["SKILL.md", "references"]

    lines = ["version: 1", "scope:", "  include:"]
    for path in include_paths:
        lines.append(f"    - {path}")
    lines.append("rules:")

    for rule_id in sorted(CHECKER.REGISTERED_RULES.keys()):
        rule_override = overrides.get(rule_id, {})
        lines.append(f"  - id: {rule_id}")
        lines.append("    description: test")
        lines.append(f"    severity: {rule_override.get('severity', 'error')}")
        scope_paths = rule_override.get("include_paths")
        if scope_paths is not None:
            lines.append("    scope:")
            lines.append("      include_paths:")
            for scope_path in scope_paths:
                lines.append(f"        - {scope_path}")

    return "\n".join(lines) + "\n"


def write_registry(path: Path) -> None:
    path.write_text(render_registry(), encoding="utf-8")


class CheckConsistencyTests(unittest.TestCase):
    def run_checker(
        self,
        skill_text: str,
        refs_text: str = "# refs\n",
        rules_override: Optional[str] = None,
        additional_include_paths: Optional[list[str]] = None,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"

            write_file(skill, skill_text)
            write_file(refs_file, refs_text)
            if rules_override is None:
                write_registry(rules_file)
            else:
                write_file(rules_file, rules_override)

            return CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=additional_include_paths,
            )

    def run_artifact_checker(
        self,
        artifact_text: str,
        evidence_text: str = "",
        evidence_path: str = ".sealos/runtime-bundle-evidence.yaml",
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"
            include_paths = ["template/demo/index.yaml"]

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(artifact_file, artifact_text)
            if evidence_text:
                evidence_file = root / evidence_path
                write_file(evidence_file, evidence_text)
                include_paths.append(evidence_path)

            return CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=include_paths,
            )

    def test_detects_app_spec_template_with_long_gap(self):
        long_gap = "x" * 1200
        violations = self.run_checker(
            f"""
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
              annotations:
                note: "{long_gap}"
            spec:
              template:
                url: https://bad.example.com
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R002" for item in violations))

    def test_ignores_parse_errors_for_template_control_snippets(self):
        violations = self.run_checker(
            """
            ```yaml
            ${{ if(inputs.enableIngress === 'true') }}
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ${{ endif() }}
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R000" for item in violations))

    def test_ignores_parse_errors_for_ellipsis_snippets(self):
        violations = self.run_checker(
            """
            ```yaml
            ...
            spec:
              ...
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R000" for item in violations))

    def test_detects_missing_app_data_url(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
            spec:
              data: {}
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R003" for item in violations))

    def test_detects_missing_app_display_type(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
            spec:
              data:
                url: https://demo.example.com
              type: link
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R032" for item in violations))

    def test_detects_invalid_app_display_type(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
            spec:
              data:
                url: https://demo.example.com
              displayType: standalone
              type: link
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R032" for item in violations))

    def test_detects_missing_app_type(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
            spec:
              data:
                url: https://demo.example.com
              displayType: normal
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R033" for item in violations))

    def test_detects_invalid_app_type(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: app-demo
            spec:
              data:
                url: https://demo.example.com
              displayType: normal
              type: web
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R033" for item in violations))

    def test_detects_template_name_variable(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              title: Demo
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R004" for item in violations))

    def test_detects_template_required_metadata_fields_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R012" for item in violations))

    def test_detects_template_folder_name_mismatch_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo-app
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo-app/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    en:
                      title: Demo
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R013" for item in violations))

    def test_detects_template_icon_path_mismatch_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://avatars.githubusercontent.com/u/123?v=4
                  templateType: inline
                  locale: en
                  i18n:
                    en:
                      title: Demo
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R014" for item in violations))

    def test_detects_template_readme_path_mismatch_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  readme: https://raw.githubusercontent.com/example/demo/main/README.md
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                      readme: https://raw.githubusercontent.com/example/demo/main/README_zh.md
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R025" for item in violations))

    def test_allows_template_with_expected_readme_paths_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R025" for item in violations))

    def test_detects_non_chinese_i18n_zh_description_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: Demo template
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R021" for item in violations))

    def test_detects_redundant_i18n_zh_title_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      title: Demo
                      description: 示例应用模板
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R022" for item in violations))

    def test_allows_template_with_chinese_i18n_zh_description_and_no_zh_title(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                  categories:
                    - ai
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id in {"R021", "R022"} for item in violations))

    def test_detects_invalid_template_categories_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                  categories:
                    - tool
                    - security
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R023" for item in violations))

    def test_allows_valid_template_categories_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://demo.example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/example/demo/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                  categories:
                    - tool
                    - backend
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R023" for item in violations))

    def test_detects_missing_official_health_probes_for_authentik_server(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: authentik
              labels:
                cloud.sealos.io/app-deploy-manager: authentik
              annotations:
                originImageName: ghcr.io/goauthentik/server:2025.12.3
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: authentik
                      image: ghcr.io/goauthentik/server:2025.12.3
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R024" for item in violations))

    def test_allows_official_health_probes_for_authentik_server(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: authentik
              labels:
                cloud.sealos.io/app-deploy-manager: authentik
              annotations:
                originImageName: ghcr.io/goauthentik/server:2025.12.3
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: authentik
                      image: ghcr.io/goauthentik/server:2025.12.3
                      imagePullPolicy: IfNotPresent
                      livenessProbe:
                        httpGet:
                          path: /-/health/live/
                          port: 9000
                      readinessProbe:
                        httpGet:
                          path: /-/health/ready/
                          port: 9000
                      startupProbe:
                        httpGet:
                          path: /-/health/ready/
                          port: 9000
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R024" for item in violations))

    def test_detects_missing_startup_probe_for_authentik_server(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: authentik
              labels:
                cloud.sealos.io/app-deploy-manager: authentik
              annotations:
                originImageName: ghcr.io/goauthentik/server:2025.12.3
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: authentik
                      image: ghcr.io/goauthentik/server:2025.12.3
                      imagePullPolicy: IfNotPresent
                      livenessProbe:
                        httpGet:
                          path: /-/health/live/
                          port: 9000
                      readinessProbe:
                        httpGet:
                          path: /-/health/ready/
                          port: 9000
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R024" for item in violations))

    def test_detects_runtime_bundle_image_version_mismatch(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              title: Demo
              url: https://example.com
              gitRepo: https://github.com/example/demo
              author: example
              description: demo
              icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
              templateType: inline
              locale: en
              i18n:
                zh:
                  description: 演示应用模板
              categories:
                - tool
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
              annotations:
                originImageName: ghcr.io/example/bundle-api:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo-api
                      image: ghcr.io/example/bundle-api:1.0.0
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: PUBLIC_ENDPOINT
                          value: https://example.com
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-console
              labels:
                app: demo-console
                cloud.sealos.io/app-deploy-manager: demo-console
              annotations:
                originImageName: ghcr.io/example/bundle-console:2.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo-console
                      image: ghcr.io/example/bundle-console:2.0.0
                      imagePullPolicy: IfNotPresent
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
            spec:
              selector:
                app: demo-api
              ports:
                - name: http
                  port: 3000
                  targetPort: 3000
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: demo-console
              labels:
                app: demo-console
                cloud.sealos.io/app-deploy-manager: demo-console
            spec:
              selector:
                app: demo-console
              ports:
                - name: http
                  port: 80
                  targetPort: 80
            ---
            apiVersion: networking.k8s.io/v1
            kind: Ingress
            metadata:
              name: demo-api
            spec:
              rules:
                - http:
                    paths:
                      - path: /
                        pathType: Prefix
                        backend:
                          service:
                            name: demo-api
                            port:
                              number: 3000
                      - path: /console
                        pathType: Prefix
                        backend:
                          service:
                            name: demo-console
                            port:
                              number: 80
            """
            ,
            """
            apiVersion: docker-to-sealos/v1
            kind: RuntimeBundleEvidence
            metadata:
              name: demo-runtime-bundle
            spec:
              appName: demo
              source: https://example.com/releases/v1/docker-compose.yml
              images:
                - ghcr.io/example/bundle-api:1.0.0
                - ghcr.io/example/bundle-console:1.0.0
              components:
                - demo-api
                - demo-console
              routes:
                - path: /
                  service: demo-api
                - path: /console
                  service: demo-console
              env:
                - PUBLIC_ENDPOINT
            """
        )
        self.assertTrue(any(item.rule_id == "R046" for item in violations))

    def test_detects_missing_runtime_bundle_console_component_and_route(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              title: Demo
              url: https://example.com
              gitRepo: https://github.com/example/demo
              author: example
              description: demo
              icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
              templateType: inline
              locale: en
              i18n:
                zh:
                  description: 演示应用模板
              categories:
                - tool
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
              annotations:
                originImageName: ghcr.io/example/bundle-api:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo-api
                      image: ghcr.io/example/bundle-api:1.0.0
                      imagePullPolicy: IfNotPresent
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
            spec:
              selector:
                app: demo-api
              ports:
                - name: http
                  port: 3000
                  targetPort: 3000
            ---
            apiVersion: networking.k8s.io/v1
            kind: Ingress
            metadata:
              name: demo-api
            spec:
              rules:
                - http:
                    paths:
                      - path: /
                        pathType: Prefix
                        backend:
                          service:
                            name: demo-api
                            port:
                              number: 3000
            """
            ,
            """
            apiVersion: docker-to-sealos/v1
            kind: RuntimeBundleEvidence
            metadata:
              name: demo-runtime-bundle
            spec:
              appName: demo
              source: https://example.com/releases/v1/docker-compose.yml
              images:
                - ghcr.io/example/bundle-api:1.0.0
                - ghcr.io/example/bundle-console:1.0.0
              components:
                - demo-api
                - demo-console
              routes:
                - path: /
                  service: demo-api
                - path: /console
                  service: demo-console
            """
        )
        self.assertTrue(any(item.rule_id == "R046" for item in violations))

    def test_allows_runtime_bundle_with_matching_images_components_routes_and_envs(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              title: Demo
              url: https://example.com
              gitRepo: https://github.com/example/demo
              author: example
              description: demo
              icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
              templateType: inline
              locale: en
              i18n:
                zh:
                  description: 演示应用模板
              categories:
                - tool
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
              annotations:
                originImageName: ghcr.io/example/bundle-api:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo-api
                      image: ghcr.io/example/bundle-api:1.0.0
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: PUBLIC_ENDPOINT
                          value: https://example.com
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-console
              labels:
                app: demo-console
                cloud.sealos.io/app-deploy-manager: demo-console
              annotations:
                originImageName: ghcr.io/example/bundle-console:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo-console
                      image: ghcr.io/example/bundle-console:1.0.0
                      imagePullPolicy: IfNotPresent
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: demo-api
              labels:
                app: demo-api
                cloud.sealos.io/app-deploy-manager: demo-api
            spec:
              selector:
                app: demo-api
              ports:
                - name: http
                  port: 3000
                  targetPort: 3000
            ---
            apiVersion: v1
            kind: Service
            metadata:
              name: demo-console
              labels:
                app: demo-console
                cloud.sealos.io/app-deploy-manager: demo-console
            spec:
              selector:
                app: demo-console
              ports:
                - name: http
                  port: 80
                  targetPort: 80
            ---
            apiVersion: networking.k8s.io/v1
            kind: Ingress
            metadata:
              name: demo-api
            spec:
              rules:
                - http:
                    paths:
                      - path: /
                        pathType: Prefix
                        backend:
                          service:
                            name: demo-api
                            port:
                              number: 3000
                      - path: /console
                        pathType: Prefix
                        backend:
                          service:
                            name: demo-console
                            port:
                              number: 80
            """
            ,
            """
            apiVersion: docker-to-sealos/v1
            kind: RuntimeBundleEvidence
            metadata:
              name: demo-runtime-bundle
            spec:
              appName: demo
              source: https://example.com/releases/v1/docker-compose.yml
              images:
                - ghcr.io/example/bundle-api:1.0.0
                - ghcr.io/example/bundle-console:1.0.0
              components:
                - demo-api
                - demo-console
              routes:
                - path: /
                  service: demo-api
                - path: /console
                  service: demo-console
              env:
                - PUBLIC_ENDPOINT
            """
        )
        self.assertFalse(any(item.rule_id == "R046" for item in violations))

    def test_allows_single_component_artifact_without_runtime_bundle_metadata(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              title: Demo
              url: https://example.com
              gitRepo: https://github.com/example/demo
              author: example
              description: demo
              icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
              templateType: inline
              locale: en
              i18n:
                zh:
                  description: 演示应用模板
              categories:
                - tool
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ghcr.io/example/demo:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo
                      image: ghcr.io/example/demo:1.0.0
                      imagePullPolicy: IfNotPresent
            """
        )
        self.assertFalse(any(item.rule_id == "R046" for item in violations))

    def test_runtime_bundle_check_is_scoped_to_same_artifact_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            demo_artifact = root / "template" / "demo" / "index.yaml"
            other_artifact = root / "template" / "other" / "index.yaml"
            evidence_file = root / ".sealos" / "runtime-bundle-evidence.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                demo_artifact,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: 演示应用模板
                  categories:
                    - tool
                """,
            )
            write_file(
                other_artifact,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo-api
                  labels:
                    app: demo-api
                    cloud.sealos.io/app-deploy-manager: demo-api
                  annotations:
                    originImageName: ghcr.io/example/bundle-api:1.0.0
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: ${{ defaults.app_name }}
                      containers:
                        - name: demo-api
                          image: ghcr.io/example/bundle-api:1.0.0
                          imagePullPolicy: IfNotPresent
                """,
            )
            write_file(
                evidence_file,
                """
                apiVersion: docker-to-sealos/v1
                kind: RuntimeBundleEvidence
                metadata:
                  name: demo-runtime-bundle
                spec:
                  appName: demo
                  source: https://example.com/releases/v1/docker-compose.yml
                  images:
                    - ghcr.io/example/bundle-api:1.0.0
                  components:
                    - demo-api
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=[
                    "template/demo/index.yaml",
                    "template/other/index.yaml",
                    ".sealos/runtime-bundle-evidence.yaml",
                ],
            )
            self.assertTrue(any(item.rule_id == "R046" for item in violations))

    def test_allows_matching_single_replica_topology_evidence(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo-app
            spec:
              replicas: 1
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: template/demo/index.yaml@base-revision
              resources:
                - kind: StatefulSet
                  name: demo-app
                  when: always
                  replicas: 1
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        self.assertFalse(any(item.rule_id == "R050" for item in violations))

    def test_detects_topology_replica_drift(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-app
            spec:
              replicas: 2
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v1
              resources:
                - kind: Deployment
                  name: demo-app
                  when: always
                  replicas: 1
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(r050)
        self.assertTrue(any("replicas=1" in item.message or "replicas=2" in item.message for item in r050))

    def test_detects_ha_topology_replica_shrink(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-api
            spec:
              replicas: 1
            ---
            apiVersion: apps.kubeblocks.io/v1alpha1
            kind: Cluster
            metadata:
              name: demo-pg
            spec:
              componentSpecs:
                - name: postgresql
                  replicas: 1
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@ha-revision
              resources:
                - kind: Deployment
                  name: demo-api
                  when: always
                  replicas: 3
                - kind: Cluster
                  name: demo-pg
                  when: always
                  components:
                    - name: postgresql
                      replicas: 3
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(any("replicas=3" in item.message and "demo-api" in item.message for item in r050))
        self.assertTrue(any("components=postgresql=3" in item.message for item in r050))

    def test_detects_feature_toggle_adding_worker_and_redis(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                enable_s3_storage:
                  description: Enable object storage
                  type: boolean
                  default: 'false'
            ---
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo-app
            spec:
              replicas: 1
            ---
            ${{ if(inputs.enable_s3_storage === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: demo
            spec:
              policy: private
            ${{ endif() }}
            ---
            ${{ if(inputs.enable_s3_storage === 'true') }}
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-worker
            spec:
              replicas: 1
            ${{ endif() }}
            ---
            ${{ if(inputs.enable_s3_storage === 'true') }}
            apiVersion: apps.kubeblocks.io/v1alpha1
            kind: Cluster
            metadata:
              name: demo-redis
            spec:
              componentSpecs:
                - name: redis
                  replicas: 1
            ${{ endif() }}
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: template/demo/index.yaml@base-revision
              resources:
                - kind: StatefulSet
                  name: demo-app
                  when: always
                  replicas: 1
                - kind: ObjectStorageBucket
                  name: demo
                  when: inputs.enable_s3_storage === 'true'
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(any("demo-worker" in item.message for item in r050))
        self.assertTrue(any("demo-redis" in item.message for item in r050))

    def test_detects_topology_condition_drift(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            ${{ if(inputs.enable_s3_storage === 'true') }}
            apiVersion: apps.kubeblocks.io/v1alpha1
            kind: Cluster
            metadata:
              name: demo-pg
            spec:
              componentSpecs:
                - name: postgresql
                  replicas: 1
            ${{ endif() }}
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: template/demo/index.yaml@base-revision
              resources:
                - kind: Cluster
                  name: demo-pg
                  when: inputs.enable_postgresql === 'true'
                  components:
                    - name: postgresql
                      replicas: 1
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(r050)
        self.assertTrue(any("enable_postgresql" in item.message for item in r050))
        self.assertTrue(any("enable_s3_storage" in item.message for item in r050))

    def test_allows_nested_topology_conditions_in_source_order(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            ${{ if(inputs.enable_database === 'true') }}
            ---
            ${{ if(inputs.enable_metrics === 'true') }}
            apiVersion: apps/v1
            kind: DaemonSet
            metadata:
              name: demo-metrics
            spec: {}
            ${{ endif() }}
            ---
            ${{ endif() }}
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v1
              resources:
                - kind: DaemonSet
                  name: demo-metrics
                  when: "inputs.enable_database === 'true' && inputs.enable_metrics === 'true'"
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        self.assertFalse(any(item.rule_id == "R050" for item in violations))

    def test_detects_kubeblocks_component_replica_drift(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps.kubeblocks.io/v1alpha1
            kind: Cluster
            metadata:
              name: demo-pg
            spec:
              componentSpecs:
                - name: postgresql
                  replicas: 2
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v1
              resources:
                - kind: Cluster
                  name: demo-pg
                  when: always
                  components:
                    - name: postgresql
                      replicas: 1
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(r050)
        self.assertTrue(any("components=postgresql=1" in item.message for item in r050))
        self.assertTrue(any("components=postgresql=2" in item.message for item in r050))

    def test_allows_matching_ha_cluster_cronjob_and_ignores_job(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-api
            spec:
              replicas: 3
            ---
            apiVersion: apps/v1
            kind: DaemonSet
            metadata:
              name: demo-agent
            spec: {}
            ---
            ${{ if(inputs.enable_postgresql === 'true') }}
            apiVersion: apps.kubeblocks.io/v1alpha1
            kind: Cluster
            metadata:
              name: demo-pg
            spec:
              componentSpecs:
                - name: postgresql
                  replicas: 3
            ${{ endif() }}
            ---
            apiVersion: batch/v1
            kind: CronJob
            metadata:
              name: demo-maintenance
            spec: {}
            ---
            apiVersion: batch/v1
            kind: Job
            metadata:
              name: demo-bootstrap
            spec: {}
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v2
              resources:
                - kind: Deployment
                  name: demo-api
                  when: always
                  replicas: 3
                - kind: DaemonSet
                  name: demo-agent
                  when: always
                - kind: Cluster
                  name: demo-pg
                  when: inputs.enable_postgresql === 'true'
                  components:
                    - name: postgresql
                      replicas: 3
                - kind: CronJob
                  name: demo-maintenance
                  when: always
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        self.assertFalse(any(item.rule_id == "R050" for item in violations))

    def test_detects_unexpected_cronjob_topology(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: batch/v1
            kind: CronJob
            metadata:
              name: demo-maintenance
            spec: {}
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v1
              resources:
                - kind: ObjectStorageBucket
                  name: demo-storage
                  when: always
            """,
            evidence_path=".sealos/topology-evidence/demo.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(any("demo-maintenance" in item.message for item in r050))

    def test_enforces_topology_evidence_path_and_schema(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo-app
            spec:
              replicas: 1
            """,
            """
            apiVersion: docker-to-sealos/v1
            kind: TopologyEvidence
            metadata:
              name: demo-topology
            spec:
              appName: demo
              source: compose.yaml@v1
              resources:
                - kind: Deployment
                  name: demo-app
                  when: always
            """,
            evidence_path=".sealos/demo-topology.yaml",
        )

        r050 = [item for item in violations if item.rule_id == "R050"]
        self.assertTrue(any(".sealos/topology-evidence/demo.yaml" in item.message for item in r050))
        self.assertTrue(any("require positive integer replicas" in item.message for item in r050))

    def test_detects_origin_image_name_mismatch_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: nginx:1.27.3
                          imagePullPolicy: IfNotPresent
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R015" for item in violations))

    def test_detects_latest_tag(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:latest
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R001" for item in violations))

    def test_detects_floating_tag_for_managed_workload(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ghcr.io/example/demo:v2
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: ghcr.io/example/demo:v2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R016" for item in violations))

    def test_allows_explicit_version_tag_for_managed_workload(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ghcr.io/example/demo:v2.2.0
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: ghcr.io/example/demo:v2.2.0
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R016" for item in violations))

    def test_detects_compose_image_variables_for_managed_workload(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ${APP_IMAGE:-ghcr.io/example/demo}:${APP_TAG:-1.2.3}
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: ${APP_IMAGE:-ghcr.io/example/demo}:${APP_TAG:-1.2.3}
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R018" for item in violations))

    def test_detects_service_ports_missing_names_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  ports:
                    - port: 9000
                      targetPort: 9000
                      protocol: TCP
                    - port: 9443
                      targetPort: 9443
                      protocol: TCP
                  selector:
                    app: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R020" for item in violations))

    def test_enforces_root_ingress_numeric_backend_port_contract(self):
        service = """
            apiVersion: v1
            kind: Service
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              selector:
                app: demo
              ports:
                - name: http
                  port: 8080
                  targetPort: 8080
        """
        cases = [
            ("numeric matching port", service, "Prefix", "/", "number: 8080", False),
            ("named backend port", service, "Prefix", "/", "name: http", True),
            ("mismatched numeric port", service, "Prefix", "/", "number: 9090", True),
            ("missing service", "", "Prefix", "/", "number: 8080", True),
            ("non-root prefix route", service, "Prefix", "/admin", "name: http", False),
        ]

        for label, service_yaml, path_type, path, backend_port, expect_violation in cases:
            with self.subTest(label=label):
                ingress = f"""
                    apiVersion: networking.k8s.io/v1
                    kind: Ingress
                    metadata:
                      name: demo
                      labels:
                        cloud.sealos.io/app-deploy-manager: demo
                    spec:
                      rules:
                        - host: demo.example.com
                          http:
                            paths:
                              - pathType: {path_type}
                                path: {path}
                                backend:
                                  service:
                                    name: demo
                                    port:
                                      {backend_port}
                """
                artifact = "\n---\n".join(
                    part
                    for part in (
                        textwrap.dedent(service_yaml).strip(),
                        textwrap.dedent(ingress).strip(),
                    )
                    if part
                )
                violations = self.run_artifact_checker(artifact)
                has_violation = any(item.rule_id == "R051" for item in violations)
                self.assertEqual(expect_violation, has_violation, label)

    def test_scopes_root_ingress_port_matching_to_the_same_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            rules_file = refs_dir / "rules-registry.yaml"
            demo_artifact = root / "template" / "demo" / "index.yaml"
            other_artifact = root / "template" / "other" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_dir / "sample.md", "# refs\n")
            write_registry(rules_file)
            write_file(
                demo_artifact,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                spec:
                  ports:
                    - name: http
                      port: 8080
                      targetPort: 8080
                ---
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  rules:
                    - http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 9090
                """,
            )
            write_file(
                other_artifact,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                spec:
                  ports:
                    - name: http
                      port: 9090
                      targetPort: 9090
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=[
                    "template/demo/index.yaml",
                    "template/other/index.yaml",
                ],
            )
            self.assertTrue(any(item.rule_id == "R051" for item in violations))

    def test_detects_service_missing_required_labels_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo-svc
                spec:
                  ports:
                    - name: tcp-8080
                      port: 8080
                      targetPort: 8080
                      protocol: TCP
                  selector:
                    app: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R029" for item in violations))

    def test_detects_service_label_mismatch_against_selector_app_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo-svc
                  labels:
                    app: wrong
                    cloud.sealos.io/app-deploy-manager: wrong
                spec:
                  ports:
                    - name: tcp-8080
                      port: 8080
                      targetPort: 8080
                      protocol: TCP
                  selector:
                    app: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R029" for item in violations))

    def test_allows_service_labels_matching_selector_app_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  ports:
                    - name: tcp-8080
                      port: 8080
                      targetPort: 8080
                      protocol: TCP
                  selector:
                    app: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R029" for item in violations))

    def test_detects_configmap_missing_component_labels_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                data:
                  key: value
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R030" for item in violations))

    def test_allows_bootstrap_only_configmap_without_component_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                data:
                  vn-tmpvn-configvn-yaml: value
                ---
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  revisionHistoryLimit: 1
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    spec:
                      automountServiceAccountToken: false
                      initContainers:
                        - name: copy-config
                          image: alpine:3.20
                          imagePullPolicy: IfNotPresent
                          command: ["/bin/sh", "-c", "cp /tmp/config.yaml /etc/demo/config.yaml"]
                          volumeMounts:
                            - name: config
                              mountPath: /tmp/config.yaml
                              subPath: vn-tmpvn-configvn-yaml
                            - name: data
                              mountPath: /etc/demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          volumeMounts:
                            - name: data
                              mountPath: /etc/demo
                      volumes:
                        - name: config
                          configMap:
                            name: demo
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        accessModes:
                          - ReadWriteOnce
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R030" for item in violations))

    def test_detects_bootstrap_only_configmap_with_component_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                data:
                  vn-tmpvn-configvn-yaml: value
                ---
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  revisionHistoryLimit: 1
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    spec:
                      automountServiceAccountToken: false
                      initContainers:
                        - name: copy-config
                          image: alpine:3.20
                          imagePullPolicy: IfNotPresent
                          command: ["/bin/sh", "-c", "cp /tmp/config.yaml /etc/demo/config.yaml"]
                          volumeMounts:
                            - name: config
                              mountPath: /tmp/config.yaml
                              subPath: vn-tmpvn-configvn-yaml
                            - name: data
                              mountPath: /etc/demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          volumeMounts:
                            - name: data
                              mountPath: /etc/demo
                      volumes:
                        - name: config
                          configMap:
                            name: demo
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        accessModes:
                          - ReadWriteOnce
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R030" for item in violations))

    def test_detects_runtime_configmap_missing_component_labels(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                data:
                  vn-etcvn-demovn-configvn-yaml: value
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  revisionHistoryLimit: 1
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          volumeMounts:
                            - name: config
                              mountPath: /etc/demo/config.yaml
                              subPath: vn-etcvn-demovn-configvn-yaml
                      volumes:
                        - name: config
                          configMap:
                            name: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R030" for item in violations))

    def test_accepts_configmap_file_mount_contract(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                data:
                  vn-optvn-demovn-startvn-sh: |
                    echo start
                  vn-optvn-demovn-initvn-py: |
                    print("init")
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  annotations:
                    originImageName: ghcr.io/example/demo:1.0.0
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  replicas: 1
                  revisionHistoryLimit: 1
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    metadata:
                      labels:
                        app: demo
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: ghcr.io/example/demo:1.0.0
                          imagePullPolicy: IfNotPresent
                          resources:
                            limits:
                              cpu: 200m
                              memory: 256Mi
                            requests:
                              cpu: 20m
                              memory: 25Mi
                          volumeMounts:
                            - name: demo-cm
                              mountPath: /opt/demo/start.sh
                              subPath: vn-optvn-demovn-startvn-sh
                            - name: demo-cm
                              mountPath: /opt/demo/init.py
                              subPath: vn-optvn-demovn-initvn-py
                      volumes:
                        - name: demo-cm
                          configMap:
                            name: demo
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R043" for item in violations))

    def test_detects_configmap_defaultmode_in_managed_workload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                data:
                  vn-tmpvn-initvn-sh: |
                    echo init
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  annotations:
                    originImageName: ghcr.io/example/demo:1.0.0
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  replicas: 1
                  revisionHistoryLimit: 1
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    metadata:
                      labels:
                        app: demo
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      initContainers:
                        - name: init-demo
                          image: alpine:3.20
                          imagePullPolicy: IfNotPresent
                          command:
                            - /bin/sh
                            - /tmp/init.sh
                          resources:
                            limits:
                              cpu: 100m
                              memory: 128Mi
                            requests:
                              cpu: 10m
                              memory: 12Mi
                          volumeMounts:
                            - name: demo-cm
                              mountPath: /tmp/init.sh
                              subPath: vn-tmpvn-initvn-sh
                      containers:
                        - name: demo
                          image: ghcr.io/example/demo:1.0.0
                          imagePullPolicy: IfNotPresent
                          resources:
                            limits:
                              cpu: 200m
                              memory: 256Mi
                            requests:
                              cpu: 20m
                              memory: 25Mi
                      volumes:
                        - name: demo-cm
                          configMap:
                            name: demo
                            defaultMode: 493
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R043" and "defaultMode" in item.message for item in violations))

    def test_detects_configmap_file_mount_contract_violations(self):
        base_artifact = """apiVersion: v1
kind: ConfigMap
metadata:
  name: __CONFIGMAP_NAME__
  labels:
    app: __CONFIGMAP_NAME__
    cloud.sealos.io/app-deploy-manager: __CONFIGMAP_NAME__
data:
  vn-optvn-demovn-startvn-sh: |
    echo start
  vn-optvn-demovn-initvn-py: |
    print("init")
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo
  annotations:
    originImageName: ghcr.io/example/demo:1.0.0
  labels:
    app: demo
    cloud.sealos.io/app-deploy-manager: demo
spec:
  replicas: 1
  revisionHistoryLimit: 1
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      automountServiceAccountToken: false
      imagePullSecrets:
        - name: demo
      containers:
        - name: demo
          image: ghcr.io/example/demo:1.0.0
          imagePullPolicy: IfNotPresent
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 20m
              memory: 25Mi
          volumeMounts:
__MOUNTS__
      volumes:
        - name: __VOLUME_NAME__
          configMap:
            name: __CONFIGMAP_NAME__
"""
        cases = [
            (
                "configmap suffix",
                "demo-config",
                "demo-cm",
                """
                - name: demo-cm
                  mountPath: /opt/demo/start.sh
                  subPath: vn-optvn-demovn-startvn-sh
                - name: demo-cm
                  mountPath: /opt/demo/init.py
                  subPath: vn-optvn-demovn-initvn-py
                """,
            ),
            (
                "wrong volume name",
                "demo",
                "vn-optvn-demo",
                """
                - name: vn-optvn-demo
                  mountPath: /opt/demo/start.sh
                  subPath: vn-optvn-demovn-startvn-sh
                - name: vn-optvn-demo
                  mountPath: /opt/demo/init.py
                  subPath: vn-optvn-demovn-initvn-py
                """,
            ),
            (
                "directory mount",
                "demo",
                "demo-cm",
                """
                - name: demo-cm
                  mountPath: /opt/demo
                """,
            ),
            (
                "path subPath",
                "demo",
                "demo-cm",
                """
                - name: demo-cm
                  mountPath: /opt/demo/start.sh
                  subPath: /opt/demo/start.sh
                - name: demo-cm
                  mountPath: /opt/demo/init.py
                  subPath: ./opt/demo/init.py
                """,
            ),
            (
                "missing key mount",
                "demo",
                "demo-cm",
                """
                - name: demo-cm
                  mountPath: /opt/demo/start.sh
                  subPath: vn-optvn-demovn-startvn-sh
                """,
            ),
        ]
        for label, configmap_name, volume_name, mounts in cases:
            with self.subTest(label=label):
                with tempfile.TemporaryDirectory() as temp_dir:
                    root = Path(temp_dir)
                    skill = root / "SKILL.md"
                    refs_dir = root / "references"
                    refs_file = refs_dir / "sample.md"
                    rules_file = refs_dir / "rules-registry.yaml"
                    artifact_file = root / "template" / "demo" / "index.yaml"

                    write_file(skill, "# no yaml snippets\n")
                    write_file(refs_file, "# refs\n")
                    write_registry(rules_file)
                    artifact = (
                        base_artifact.replace("__CONFIGMAP_NAME__", configmap_name)
                        .replace("__VOLUME_NAME__", volume_name)
                        .replace("__MOUNTS__", textwrap.indent(textwrap.dedent(mounts).strip("\n"), " " * 12))
                    )
                    write_file(artifact_file, artifact)

                    violations = CHECKER.run_checks(
                        skill,
                        refs_dir,
                        rules_file,
                        additional_include_paths=["template/demo/index.yaml"],
                    )
                    self.assertTrue(any(item.rule_id == "R043" for item in violations), label)

    def test_detects_ingress_backend_name_mismatch_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo-web
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R031" for item in violations))

    def test_allows_ingress_backend_name_match_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R031" for item in violations))

    def test_allows_non_root_prefix_ingress_backend_name_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo-admin
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /admin
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R031" for item in violations))

    def test_allows_exact_root_ingress_backend_name_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo-redirect
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Exact
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R031" for item in violations))

    def test_detects_missing_http_ingress_annotations_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  annotations:
                    kubernetes.io/ingress.class: nginx
                    nginx.ingress.kubernetes.io/backend-protocol: HTTP
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R026" for item in violations))

    def test_allows_required_http_ingress_annotations_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  annotations:
                    kubernetes.io/ingress.class: nginx
                    nginx.ingress.kubernetes.io/proxy-body-size: 32m
                    nginx.ingress.kubernetes.io/server-snippet: |
                      client_header_buffer_size 64k;
                      large_client_header_buffers 4 128k;
                    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
                    nginx.ingress.kubernetes.io/backend-protocol: HTTP
                    nginx.ingress.kubernetes.io/client-body-buffer-size: 64k
                    nginx.ingress.kubernetes.io/proxy-buffer-size: 64k
                    nginx.ingress.kubernetes.io/proxy-send-timeout: '300'
                    nginx.ingress.kubernetes.io/proxy-read-timeout: '300'
                    nginx.ingress.kubernetes.io/configuration-snippet: |
                      if ($request_uri ~* \.(js|css|gif|jpe?g|png)) {
                        expires 30d;
                        add_header Cache-Control "public";
                      }
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 8080
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R026" for item in violations))

    def test_detects_websocket_ingress_using_http_protocol_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  selector:
                    app: demo
                  ports:
                    - name: websocket
                      port: 3000
                      targetPort: 3000
                      protocol: TCP
                ---
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  annotations:
                    kubernetes.io/ingress.class: nginx
                    nginx.ingress.kubernetes.io/proxy-body-size: 32m
                    nginx.ingress.kubernetes.io/proxy-read-timeout: '3600'
                    nginx.ingress.kubernetes.io/proxy-send-timeout: '3600'
                    nginx.ingress.kubernetes.io/backend-protocol: HTTP
                    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 3000
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R048" for item in violations))

    def test_allows_required_websocket_ingress_annotations_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: v1
                kind: Service
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                spec:
                  selector:
                    app: demo
                  ports:
                    - name: websocket
                      port: 3000
                      targetPort: 3000
                      protocol: TCP
                ---
                apiVersion: networking.k8s.io/v1
                kind: Ingress
                metadata:
                  name: demo
                  annotations:
                    kubernetes.io/ingress.class: nginx
                    nginx.ingress.kubernetes.io/proxy-body-size: 32m
                    nginx.ingress.kubernetes.io/proxy-read-timeout: '3600'
                    nginx.ingress.kubernetes.io/proxy-send-timeout: '3600'
                    nginx.ingress.kubernetes.io/backend-protocol: WS
                    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
                spec:
                  rules:
                    - host: demo.example.com
                      http:
                        paths:
                          - pathType: Prefix
                            path: /
                            backend:
                              service:
                                name: demo
                                port:
                                  number: 3000
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R026" for item in violations))
            self.assertFalse(any(item.rule_id == "R048" for item in violations))

    def test_detects_missing_pg_init_job_for_custom_postgres_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    kb.io/database: postgresql-16.4.0
                    clusterdefinition.kubeblocks.io/name: postgresql
                spec:
                  clusterDefinitionRef: postgresql
                  clusterVersionRef: postgresql-16.4.0
                  componentSpecs: []
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: ghcr.io/posthog/posthog:1.0.0
                spec:
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: ghcr.io/posthog/posthog:1.0.0
                          imagePullPolicy: IfNotPresent
                          env:
                            - name: DATABASE_URL
                              value: postgres://user:pass@demo-pg:5432/posthog
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R027" for item in violations))

    def test_detects_non_robust_pg_init_job_for_custom_postgres_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    kb.io/database: postgresql-16.4.0
                    clusterdefinition.kubeblocks.io/name: postgresql
                spec:
                  clusterDefinitionRef: postgresql
                  clusterVersionRef: postgresql-16.4.0
                  componentSpecs: []
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: ghcr.io/posthog/posthog:1.0.0
                spec:
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: ghcr.io/posthog/posthog:1.0.0
                          imagePullPolicy: IfNotPresent
                          env:
                            - name: DATABASE_URL
                              value: postgres://user:pass@demo-pg:5432/posthog
                ---
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: demo-pg-init
                spec:
                  template:
                    spec:
                      containers:
                        - name: init
                          image: postgres:16.4
                          imagePullPolicy: IfNotPresent
                          command:
                            - sh
                            - -c
                            - |
                              psql "postgresql://postgres:pwd@demo-pg:5432/postgres" -c 'CREATE DATABASE posthog;'
                      restartPolicy: OnFailure
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R027" for item in violations))

    def test_allows_robust_pg_init_job_for_custom_postgres_database(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    kb.io/database: postgresql-16.4.0
                    clusterdefinition.kubeblocks.io/name: postgresql
                spec:
                  clusterDefinitionRef: postgresql
                  clusterVersionRef: postgresql-16.4.0
                  componentSpecs: []
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: ghcr.io/posthog/posthog:1.0.0
                spec:
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: ghcr.io/posthog/posthog:1.0.0
                          imagePullPolicy: IfNotPresent
                          env:
                            - name: DATABASE_URL
                              value: postgres://user:pass@demo-pg:5432/posthog
                ---
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: demo-pg-init
                spec:
                  template:
                    spec:
                      containers:
                        - name: init
                          image: postgres:16.4
                          imagePullPolicy: IfNotPresent
                          command:
                            - sh
                            - -c
                            - |
                              set -eu
                              pg_isready -h demo-pg -p 5432 -U postgres -d postgres >/dev/null 2>&1
                              if ! psql "postgresql://postgres:pwd@demo-pg:5432/postgres" -tAc "SELECT 1 FROM pg_database WHERE datname='posthog'" | grep -q 1; then
                                createdb -h demo-pg -p 5432 -U postgres posthog
                              fi
                      restartPolicy: OnFailure
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R027" for item in violations))

    def test_detects_postgres_secret_ref_not_matching_cluster_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-postgres
                  labels:
                    kb.io/database: postgresql-16.4.0
                    clusterdefinition.kubeblocks.io/name: postgresql
                spec:
                  clusterDefinitionRef: postgresql
                  clusterVersionRef: postgresql-16.4.0
                  componentSpecs: []
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: ghcr.io/example/demo:1.0.0
                spec:
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: ghcr.io/example/demo:1.0.0
                          imagePullPolicy: IfNotPresent
                          env:
                            - name: POSTGRES_HOST
                              valueFrom:
                                secretKeyRef:
                                  name: demo-pg-conn-credential
                                  key: host
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R037" for item in violations))

    def test_detects_missing_cronjob_required_labels(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: batch/v1
            kind: CronJob
            metadata:
              name: demo-task
            spec:
              schedule: "* * * * *"
              jobTemplate:
                spec:
                  template:
                    spec:
                      containers:
                        - name: demo-task
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                      restartPolicy: OnFailure
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R036" for item in violations))

    def test_allows_cronjob_required_labels(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: batch/v1
            kind: CronJob
            metadata:
              name: demo-task
              labels:
                cloud.sealos.io/cronjob: demo-task
                cronjob-launchpad-name: ""
                cronjob-type: image
            spec:
              schedule: "* * * * *"
              jobTemplate:
                spec:
                  template:
                    spec:
                      containers:
                        - name: demo-task
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                      restartPolicy: OnFailure
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R036" for item in violations))

    def test_ignores_latest_tag_in_negative_example_block(self):
        violations = self.run_checker(
            """
            wrong example
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:latest
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R001" for item in violations))

    def test_detects_empty_dir(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  volumes:
                    - name: temp
                      emptyDir: {}
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R005" for item in violations))

    def test_detects_missing_image_pull_policy(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R006" for item in violations))

    def test_detects_business_secret_ref(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: API_TOKEN
                          valueFrom:
                            secretKeyRef:
                              name: custom-secret
                              key: token
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_detects_spoofed_database_secret_suffix(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_PASS
                          valueFrom:
                            secretKeyRef:
                              name: totally-custom-mongodb-account-root
                              key: password
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_allows_approved_database_secret_name(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_PASS
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongodb-account-root
                              key: password
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_new_mongodb_and_legacy_redis_secret_names(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: MONGO_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongo-mongodb-account-root
                              key: password
                        - name: REDIS_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-redis-account-default
                              key: password
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_redis_service_host_port_with_credential_secret(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: REDIS_HOST
                          value: ${{ defaults.app_name }}-redis-redis-redis.${{ SEALOS_NAMESPACE }}.svc.cluster.local
                        - name: REDIS_PORT
                          value: "6379"
                        - name: REDIS_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-redis-redis-account-default
                              key: password
                        - name: REDIS_URL
                          value: redis://:$(REDIS_PASSWORD)@$(REDIS_HOST):$(REDIS_PORT)/0
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_mongodb_url_with_service_host_and_credential_secret(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: MONGO_USERNAME
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongo-mongodb-account-root
                              key: username
                        - name: MONGO_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongo-mongodb-account-root
                              key: password
                        - name: MONGODB_URI
                          value: mongodb://$(MONGO_USERNAME):$(MONGO_PASSWORD)@${{ defaults.app_name }}-mongo-mongodb.${{ SEALOS_NAMESPACE }}.svc:27017/demo?authSource=admin
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_mongodb_service_host_port_with_credential_secret(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo
            spec:
              template:
                spec:
                  initContainers:
                    - name: wait-for-data-store
                      image: busybox:1.36.1
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: MONGO_HOST
                          value: ${{ defaults.app_name }}-mongo-mongodb.${{ SEALOS_NAMESPACE }}.svc.cluster.local
                        - name: MONGO_PORT
                          value: "27017"
                  containers:
                    - name: demo
                      image: appwrite/appwrite:1.9.0
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: _APP_DB_ADAPTER
                          value: mongodb
                        - name: _APP_DB_HOST
                          value: ${{ defaults.app_name }}-mongo-mongodb.${{ SEALOS_NAMESPACE }}.svc.cluster.local
                        - name: _APP_DB_PORT
                          value: "27017"
                        - name: _APP_DB_USER
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongo-mongodb-account-root
                              key: username
                        - name: _APP_DB_PASS
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-mongo-mongodb-account-root
                              key: password
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_ignores_known_non_database_connection_env_names(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: POSTGREST_URL
                          value: http://postgrest:3000
                        - name: PG_META_PORT
                          value: "8080"
                        - name: CODE_SANDBOX_URL
                          value: http://sandbox:8080
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_detects_database_connection_env_without_secret_ref(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: AUTHENTIK_POSTGRESQL__HOST
                          value: ${{ defaults.app_name }}-pg-postgresql.${{ SEALOS_NAMESPACE }}.svc.cluster.local
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R017" for item in violations))

    def test_detects_database_connection_env_with_mismatched_secret_key(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_HOST
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: password
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R017" for item in violations))

    def test_allows_database_connection_env_secret_fields(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_ENDPOINT
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: endpoint
                        - name: DB_HOST
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: host
                        - name: DB_PORT
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: port
                        - name: DB_USERNAME
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: username
                        - name: DB_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: password
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_composed_database_endpoint_with_secret_derived_components(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_HOST
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: host
                        - name: DB_PORT
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: port
                        - name: DB_USERNAME
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: username
                        - name: DB_PASSWORD
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: password
                        - name: DATABASE_URL
                          value: postgres://$(DB_USERNAME):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/postgres
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_allows_composed_database_host_with_secret_derived_host_port(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: PG_HOST
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: host
                        - name: PG_PORT
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: port
                        - name: GF_DATABASE_HOST
                          value: $(PG_HOST):$(PG_PORT)
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R017" for item in violations))

    def test_detects_composed_database_endpoint_with_non_secret_dependency(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_HOST
                          value: postgres
                        - name: DB_PORT
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: port
                        - name: DATABASE_URL
                          value: postgres://$(DB_HOST):$(DB_PORT)/postgres
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R017" for item in violations))

    def test_detects_reserved_database_secret_name_override(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: v1
            kind: Secret
            metadata:
              name: ${{ defaults.app_name }}-pg-conn-credential
            type: Opaque
            stringData:
              password: fake
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: DB_PASS
                          valueFrom:
                            secretKeyRef:
                              name: ${{ defaults.app_name }}-pg-conn-credential
                              key: password
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))
        self.assertTrue(any("reserved" in item.message for item in violations if item.rule_id == "R007"))

    def test_allows_object_storage_secret_refs(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: S3_ACCESS_KEY_ID
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key
                              key: accessKey
                        - name: S3_SECRET_ACCESS_KEY
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key
                              key: secretKey
                        - name: BACKEND_STORAGE_MINIO_EXTERNAL_ENDPOINT
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key
                              key: external
                        - name: S3_BUCKET
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}
                              key: bucket
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))

    def test_allows_object_storage_bucket_secret_with_suffix(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: STORAGE_PUBLIC_BUCKET
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key-${{ SEALOS_SERVICE_ACCOUNT }}-${{ defaults.app_name }}-public
                              key: bucket
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R007" for item in violations))

    def test_detects_external_s3_inputs_with_object_storage_bucket(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    external_s3_endpoint:
                      description: External S3 endpoint
                ---
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R047" for item in violations))

    def test_managed_sealos_toggle_stays_out_of_r047_with_bucket(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    use_sealos_objectstorage:
                      description: Use Sealos Object Storage
                      type: boolean
                      default: 'true'
                ---
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R044" for item in violations))
            self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_detects_license_gated_managed_object_storage_toggle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    use_sealos_objectstorage:
                      description: Provision Sealos ObjectStorage for Enterprise S3 binary data storage. Requires a valid license.
                      type: boolean
                      default: 'false'
                ---
                ${{ if(inputs.use_sealos_objectstorage === 'true') }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )

        self.assertTrue(any(item.rule_id == "R049" for item in violations))
        self.assertTrue(any("license-gated" in item.message for item in violations if item.rule_id == "R049"))

    def test_allows_community_managed_object_storage_toggle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    use_sealos_objectstorage:
                      description: Provision Sealos ObjectStorage for S3-compatible file uploads.
                      type: boolean
                      default: 'false'
                ---
                ${{ if(inputs.use_sealos_objectstorage === 'true') }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )

        self.assertFalse(any(item.rule_id == "R049" for item in violations))

    def test_detects_external_s3_inputs_without_source_annotation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    s3_access_key_id:
                      description: S3 access key
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R047" for item in violations))

    def test_allows_external_s3_inputs_with_source_annotation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                  annotations:
                    docker-to-sealos.external-object-storage-source: https://docs.example.com/storage/s3
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    external_s3_endpoint:
                      description: External S3 endpoint
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R044" for item in violations))
            self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_rejects_external_s3_inputs_with_unstructured_source_annotation(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: x
            spec:
              inputs:
                external_s3_endpoint:
                  description: External S3 endpoint
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("credential-free HTTPS source URL" in item.message for item in r047))

    def test_rejects_external_s3_evidence_urls_with_credentials(self):
        unsafe_sources = (
            "https://.",
            "https://bad host/storage/s3",
            "https://docs.example.com:bad/storage/s3",
            "https://docs.example.com:99999/storage/s3",
            "https://ACCESS:SECRET@docs.example.com/storage/s3",
            "https://docs.example.com/storage/s3?access_key=SECRET",
            "https://docs.example.com/storage/s3?apiKey=SECRET",
            "https://docs.example.com/storage/s3?apikey=SECRET",
            "https://docs.example.com/storage/s3?auth=SECRET",
            "https://docs.example.com/storage/s3?sig=SECRET",
            "https://docs.example.com/storage/s3?ref=docs;sig=SECRET",
            "https://docs.example.com/storage/s3?X-Amz-Security-Token=SECRET",
            "https://docs.example.com/storage/s3#access_token=SECRET",
            "https://docs.example.com/storage/s3#sig=SECRET",
            "https://docs.example.com/storage/s3#sig%3DSECRET",
            "https://docs.example.com/storage/s3#docs%3Bsig%3DSECRET",
        )

        for source in unsafe_sources:
            with self.subTest(source=source):
                violations = self.run_artifact_checker(
                    f"""
                    apiVersion: app.sealos.io/v1
                    kind: Template
                    metadata:
                      name: demo
                      annotations:
                        docker-to-sealos.external-object-storage-source: '{source}'
                    spec:
                      inputs:
                        external_s3_endpoint:
                          description: External S3 endpoint
                    """
                )

                self.assertTrue(any(item.rule_id == "R047" for item in violations))

    def test_allows_external_s3_inputs_with_user_request_evidence(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: user-request:42
            spec:
              inputs:
                external_s3_endpoint:
                  description: External S3 endpoint
            """
        )

        self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_allows_external_s3_evidence_url_with_document_anchor(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: https://docs.example.com/storage/s3#access-key-id
            spec:
              inputs:
                external_s3_endpoint:
                  description: External S3 endpoint
            """
        )

        self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_detects_aws_s3_inputs_without_source_annotation(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                AWS_ACCESS_KEY_ID:
                  description: AWS access key
                AWS_SECRET_ACCESS_KEY:
                  description: AWS secret key
                AWS_ENDPOINT_URL_S3:
                  description: AWS endpoint URL
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("AWS_ACCESS_KEY_ID" in item.message for item in r047))

    def test_detects_described_external_s3_inputs_without_source_annotation(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                storage_endpoint:
                  description: External S3 endpoint
                storage_access_key:
                  description: External S3 access key
                storage_secret_key:
                  description: External S3 secret key
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("storage_endpoint" in item.message for item in r047))

    def test_rejects_managed_bucket_with_described_external_s3_inputs(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: user-request:external-s3
            spec:
              inputs:
                storage_endpoint:
                  description: External S3 endpoint
                storage_access_key:
                  description: External S3 access key
                storage_secret_key:
                  description: External S3 secret key
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("managed ObjectStorageBucket" in item.message for item in r047))

    def test_rejects_managed_bucket_with_generically_named_s3_inputs(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: user-request:external-s3
            spec:
              inputs:
                endpoint:
                  description: S3 endpoint URL
                access_key:
                  description: S3 access key ID
                secret_key:
                  description: S3 secret access key
                bucket:
                  description: S3 bucket name
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("managed ObjectStorageBucket" in item.message for item in r047))

    def test_rejects_managed_bucket_with_camel_case_external_s3_inputs(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: user-request:external-s3
            spec:
              inputs:
                externalS3Endpoint:
                  description: S3 endpoint URL
                externalS3AccessKey:
                  description: S3 access key ID
                externalS3SecretKey:
                  description: S3 secret access key
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("managed ObjectStorageBucket" in item.message for item in r047))

    def test_rejects_managed_bucket_with_aws_s3_inputs(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: user-request:external-s3
            spec:
              inputs:
                AWS_ACCESS_KEY_ID:
                  description: AWS access key for external S3
                AWS_SECRET_ACCESS_KEY:
                  description: AWS secret key for external S3
                AWS_S3_BUCKET:
                  description: External S3 bucket
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            """
        )

        r047 = [item for item in violations if item.rule_id == "R047"]
        self.assertEqual(1, len(r047))
        self.assertTrue(any("managed ObjectStorageBucket" in item.message for item in r047))

    def test_unrelated_aws_credentials_do_not_inherit_s3_context(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                enable_s3_storage:
                  description: Enable the optional S3 feature
                  type: boolean
                  default: 'false'
                AWS_ACCESS_KEY_ID:
                  description: AWS access key for SES
                AWS_SECRET_ACCESS_KEY:
                  description: AWS secret key for SES
                AWS_REGION:
                  description: AWS region for SES
            """
        )

        self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_conditional_managed_sealos_toggle_stays_out_of_r047(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: demo
                spec:
                  title: Demo
                  url: https://example.com
                  gitRepo: https://github.com/example/demo
                  author: example
                  description: demo
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/logo.png
                  templateType: inline
                  locale: en
                  readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README.md
                  i18n:
                    zh:
                      description: demo
                      readme: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/demo/README_zh.md
                  categories:
                    - tool
                  inputs:
                    use_sealos_objectstorage:
                      description: Use Sealos Object Storage
                      type: boolean
                      default: 'false'
                      required: false
                ---
                ${{ if(inputs.use_sealos_objectstorage === 'true') }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ---
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R044" for item in violations))
            self.assertFalse(any(item.rule_id == "R047" for item in violations))

    def test_allows_private_registry_pull_secret_via_image_pull_secrets(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: v1
            kind: Secret
            metadata:
              name: ${{ defaults.app_name }}
            type: kubernetes.io/dockerconfigjson
            data:
              .dockerconfigjson: e30=
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ghcr.io/example/demo:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo
                      image: ghcr.io/example/demo:1.0.0
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id in {"R007", "R035"} for item in violations))

    def test_allows_public_image_without_image_pull_secrets(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: nginx:1.27.2
            spec:
              revisionHistoryLimit: 1
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R035" for item in violations))

    def test_detects_public_image_pull_secret_reference(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: nginx:1.27.2
            spec:
              revisionHistoryLimit: 1
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: ${{ defaults.app_name }}
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R035" for item in violations))

    def test_detects_invalid_registry_pull_secret_reference(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: registry.example.com/private/demo:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  imagePullSecrets:
                    - name: custom-pull-secret
                  containers:
                    - name: demo
                      image: registry.example.com/private/demo:1.0.0
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R035" for item in violations))

    def test_detects_missing_private_registry_pull_secret_reference(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                originImageName: ghcr.io/example/demo:1.0.0
            spec:
              revisionHistoryLimit: 1
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: ghcr.io/example/demo:1.0.0
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R035" for item in violations))

    def test_detects_object_storage_secret_misuse_on_non_s3_env(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: API_TOKEN
                          valueFrom:
                            secretKeyRef:
                              name: object-storage-key
                              key: accessKey
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_detects_env_from_secret_ref(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                      envFrom:
                        - secretRef:
                            name: custom-envfrom-secret
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_detects_volume_secret_ref(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  volumes:
                    - name: certs
                      secret:
                        secretName: custom-volume-secret
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_detects_projected_secret_ref(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  volumes:
                    - name: mixed
                      projected:
                        sources:
                          - secret:
                              name: custom-projected-secret
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R007" for item in violations))

    def test_detects_label_mismatch(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo-v2
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R008" for item in violations))

    def test_detects_missing_deploy_manager_label(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R008" for item in violations))

    def test_detects_missing_app_label(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R034" for item in violations))

    def test_detects_app_label_mismatch(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
                app: demo-v2
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R034" for item in violations))

    def test_detects_container_name_mismatch(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
                app: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo-server
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R028" for item in violations))

    def test_allows_matching_app_label_and_container_name(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
                app: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id in {"R034", "R028"} for item in violations))

    def test_allows_sidecar_container_name_when_primary_matches_workload(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
                app: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
                    - name: demo-sidecar
                      image: busybox:1.36.1
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R028" for item in violations))

    def test_detects_missing_revision_history_limit(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R009" for item in violations))

    def test_detects_missing_automount_service_account_token(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R010" for item in violations))

    def test_detects_unjustified_automount_service_account_token_true(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: true
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R010" for item in violations))

    def test_allows_documented_kubernetes_service_account_token_usage(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
              annotations:
                sealos.io/service-account-token-reason: "Headplane Kubernetes integration needs the service account token to list pods"
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  serviceAccountName: demo
                  automountServiceAccountToken: true
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ```
            """
        )
        self.assertFalse(any(item.rule_id == "R010" for item in violations))

    def test_detects_pvc_storage_over_limit(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
              volumeClaimTemplates:
                - metadata:
                    name: data
                  spec:
                    resources:
                      requests:
                        storage: 2Gi
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R011" for item in violations))

    def test_detects_pvc_storage_variable_expression(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
              volumeClaimTemplates:
                - metadata:
                    name: data
                  spec:
                    resources:
                      requests:
                        storage: ${{ inputs.storage_size }}
            ```
            """
        )
        self.assertTrue(any(item.rule_id == "R011" for item in violations))

    def test_allows_statefulset_volume_claim_template_without_storage_tracking_labels(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo
              labels:
                app: demo
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              selector:
                matchLabels:
                  app: demo
              template:
                metadata:
                  labels:
                    app: demo
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
              volumeClaimTemplates:
                - metadata:
                    name: data
                  spec:
                    resources:
                      requests:
                        storage: 1Gi
            ```
            """
        )
        self.assertFalse(violations)

    def test_allows_declared_template_input_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "erpnext" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: erpnext
                spec:
                  title: ERPNext
                  url: https://erpnext.com
                  gitRepo: https://github.com/frappe/erpnext
                  author: Sealos
                  description: ERPNext template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/erpnext/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: ERPNext 模板
                  categories:
                    - tool
                  inputs:
                    admin_username:
                      description: Administrator login name
                      type: string
                      default: admin
                      required: true
                    admin_password:
                      description: Administrator password
                      type: string
                      default: ''
                      required: true
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: erpnext
                spec:
                  template:
                    spec:
                      containers:
                        - name: erpnext
                          env:
                            - name: ADMIN_USERNAME
                              value: ${{ inputs.admin_username }}
                            - name: ADMIN_PASSWORD
                              value: ${{ inputs.admin_password }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/erpnext/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R045" for item in violations))

    def test_detects_undeclared_template_input_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "erpnext" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: erpnext
                spec:
                  title: ERPNext
                  url: https://erpnext.com
                  gitRepo: https://github.com/frappe/erpnext
                  author: Sealos
                  description: ERPNext template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/erpnext/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: ERPNext 模板
                  categories:
                    - tool
                  inputs:
                    admin_password:
                      description: Administrator password
                      type: string
                      default: ''
                      required: true
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: erpnext
                spec:
                  template:
                    spec:
                      containers:
                        - name: erpnext
                          env:
                            - name: ADMIN_USERNAME
                              value: ${{ inputs.admin_username }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/erpnext/index.yaml"],
            )
            r045 = [item for item in violations if item.rule_id == "R045"]
            self.assertTrue(r045)
            self.assertTrue(any("inputs.admin_username" in item.message for item in r045))

    def test_template_input_reference_rule_ignores_defaults_refs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "erpnext" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: erpnext
                spec:
                  title: ERPNext
                  url: https://erpnext.com
                  gitRepo: https://github.com/frappe/erpnext
                  author: Sealos
                  description: ERPNext template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/erpnext/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: ERPNext 模板
                  categories:
                    - tool
                ---
                apiVersion: v1
                kind: Service
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  selector:
                    app: ${{ defaults.app_name }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/erpnext/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R045" for item in violations))

    def test_detects_undeclared_template_input_reference_in_condition(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "erpnext" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: erpnext
                spec:
                  title: ERPNext
                  url: https://erpnext.com
                  gitRepo: https://github.com/frappe/erpnext
                  author: Sealos
                  description: ERPNext template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/erpnext/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: ERPNext 模板
                  categories:
                    - tool
                  inputs:
                    admin_password:
                      description: Administrator password
                      type: string
                      default: ''
                      required: true
                ---
                ${{ if(inputs.enable_signup === 'true') }}
                apiVersion: v1
                kind: ConfigMap
                metadata:
                  name: erpnext-signup
                data:
                  enabled: "true"
                ---
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/erpnext/index.yaml"],
            )
            r045 = [item for item in violations if item.rule_id == "R045"]
            self.assertTrue(r045)
            self.assertTrue(any("inputs.enable_signup" in item.message for item in r045))

    def test_detects_non_string_template_input_defaults(self):
        cases = {
            "numeric": ("587", "integer"),
            "decimal": ("587.0", "number"),
            "boolean": ("false", "boolean"),
            "null": ("null", "null"),
        }

        for case_name, (default_value, expected_type) in cases.items():
            with self.subTest(case=case_name):
                violations = self.run_artifact_checker(
                    f"""
                    apiVersion: app.sealos.io/v1
                    kind: Template
                    metadata:
                      name: demo
                    spec:
                      inputs:
                        smtp_port:
                          description: SMTP server port
                          type: string
                          default: {default_value}
                          required: false
                    """
                )

                r052 = [item for item in violations if item.rule_id == "R052"]
                self.assertEqual(1, len(r052))
                self.assertEqual(10, r052[0].line)
                self.assertIn("spec.inputs.smtp_port.default", r052[0].message)
                self.assertIn(f"got {expected_type}", r052[0].message)

    def test_detects_non_string_template_default_values(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              defaults:
                smtp_port:
                  type: string
                  value: 587
            """
        )

        r052 = [item for item in violations if item.rule_id == "R052"]
        self.assertEqual(1, len(r052))
        self.assertEqual(9, r052[0].line)
        self.assertIn("spec.defaults.smtp_port.value", r052[0].message)
        self.assertIn("got integer", r052[0].message)

    def test_allows_string_template_defaults_and_numeric_infrastructure_fields(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              defaults:
                smtp_port:
                  type: string
                  value: "587"
                null_marker:
                  type: string
                  value: "null"
              inputs:
                smtp_port:
                  description: SMTP server port
                  type: string
                  default: "587"
                  required: false
                enable_tls:
                  description: Enable SMTP TLS
                  type: boolean
                  default: "false"
                  required: false
                admin_username:
                  description: Administrator login name
                  type: string
                  required: true
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
            spec:
              replicas: 1
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      ports:
                        - containerPort: 3000
            """
        )

        self.assertFalse(any(item.rule_id == "R052" for item in violations))

    def test_registry_rule_scope_filters_violations(self):
        rules_yaml = render_registry(
            overrides={
                "R001": {
                    "include_paths": ["references/*.md"],
                }
            }
        )
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            spec:
              template:
                spec:
                  containers:
                    - name: demo
                      image: nginx:latest
                      imagePullPolicy: IfNotPresent
            ```
            """,
            refs_text="# clean refs\n",
            rules_override=rules_yaml,
        )
        self.assertFalse(any(item.rule_id == "R001" for item in violations))

    def test_detects_violations_in_generated_yaml_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                spec:
                  template:
                    spec:
                      containers:
                        - name: demo
                          image: nginx:latest
                          imagePullPolicy: IfNotPresent
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            latest_violations = [item for item in violations if item.rule_id == "R001"]
            self.assertEqual(1, len(latest_violations))
            self.assertEqual(artifact_file.resolve(), latest_violations[0].path.resolve())

    def test_detects_invalid_database_component_resources_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    kb.io/database: postgresql-16.4.0
                spec:
                  componentSpecs:
                    - name: postgresql
                      resources:
                        limits:
                          cpu: 1000m
                          memory: 1024Mi
                        requests:
                          cpu: 100m
                          memory: 102Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R019" for item in violations))

    def test_detects_database_cluster_missing_visibility_labels_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    sealos-db-provider-cr: demo-pg
                spec:
                  componentSpecs:
                    - name: postgresql
                      resources:
                        limits:
                          cpu: 500m
                          memory: 512Mi
                        requests:
                          cpu: 50m
                          memory: 51Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R040" for item in violations))

    def test_detects_database_cluster_missing_labels_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                spec:
                  componentSpecs:
                    - name: postgresql
                      resources:
                        limits:
                          cpu: 500m
                          memory: 512Mi
                        requests:
                          cpu: 50m
                          memory: 51Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R040" for item in violations))

    def test_allows_database_cluster_visibility_labels_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    sealos-db-provider-cr: demo-pg
                    app.kubernetes.io/instance: demo-pg
                    clusterdefinition.kubeblocks.io/name: postgresql
                    kb.io/database: postgresql-16.4.0
                spec:
                  componentSpecs:
                    - name: postgresql
                      resources:
                        limits:
                          cpu: 500m
                          memory: 512Mi
                        requests:
                          cpu: 50m
                          memory: 51Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R040" for item in violations))

    def test_allows_database_cluster_without_instance_label_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-pg
                  labels:
                    sealos-db-provider-cr: demo-pg
                    clusterdefinition.kubeblocks.io/name: postgresql
                    kb.io/database: postgresql-16.4.0
                spec:
                  componentSpecs:
                    - name: postgresql
                      resources:
                        limits:
                          cpu: 500m
                          memory: 512Mi
                        requests:
                          cpu: 50m
                          memory: 51Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R040" for item in violations))

    def test_detects_raw_database_statefulset_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo-postgres
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo-postgres
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo-postgres
                          image: postgres:16.4
                          imagePullPolicy: IfNotPresent
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R039" for item in violations))

    def test_detects_raw_database_resources_across_supported_kinds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: redis
                  labels:
                    app: redis
                spec:
                  template:
                    spec:
                      containers:
                        - name: redis
                          image: redis:7.2.7
                          imagePullPolicy: IfNotPresent
                ---
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: postgres
                spec:
                  template:
                    spec:
                      containers:
                        - name: postgres
                          image: postgres:16.4
                          imagePullPolicy: IfNotPresent
                ---
                apiVersion: apps/v1
                kind: DaemonSet
                metadata:
                  name: mysql
                spec:
                  template:
                    spec:
                      containers:
                        - name: mysql
                          image: mysql:8.0.35
                          imagePullPolicy: IfNotPresent
                ---
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: kafka
                spec:
                  template:
                    spec:
                      containers:
                        - name: kafka
                          image: bitnami/kafka:3.3.2
                          imagePullPolicy: IfNotPresent
                ---
                apiVersion: v1
                kind: Service
                metadata:
                  name: mongo
                spec:
                  selector:
                    app: mongo
                  ports:
                    - name: tcp-27017
                      port: 27017
                      targetPort: 27017
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertGreaterEqual(len([item for item in violations if item.rule_id == "R039"]), 5)

    def test_allows_stateful_application_workload_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo-worker
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo-worker
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo-worker
                          image: ghcr.io/example/demo-worker:1.2.3
                          imagePullPolicy: IfNotPresent
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_allows_database_client_image_in_app_init_container_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    app: demo
                    cloud.sealos.io/app-deploy-manager: demo
                  annotations:
                    originImageName: ghcr.io/example/demo:v1.0.0
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: ${{ defaults.app_name }}
                      initContainers:
                        - name: wait-for-postgres
                          image: postgres:16-alpine
                          imagePullPolicy: IfNotPresent
                          command: ["sh", "-c", "until pg_isready -h $(PG_HOST); do sleep 2; done"]
                          resources:
                            limits:
                              cpu: 100m
                              memory: 128Mi
                            requests:
                              cpu: 10m
                              memory: 12Mi
                      containers:
                        - name: demo
                          image: ghcr.io/example/demo:v1.0.0
                          imagePullPolicy: IfNotPresent
                          resources:
                            limits:
                              cpu: 200m
                              memory: 256Mi
                            requests:
                              cpu: 20m
                              memory: 25Mi
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_allows_database_client_init_job_in_artifact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: demo-pg-init
                spec:
                  template:
                    spec:
                      restartPolicy: OnFailure
                      containers:
                        - name: pg-init
                          image: postgres:16-alpine
                          imagePullPolicy: IfNotPresent
                          command: ["sh", "-c", "pg_isready -h $(PG_HOST) && psql -c 'select 1'"]
                          resources:
                            limits:
                              cpu: 100m
                              memory: 128Mi
                            requests:
                              cpu: 10m
                              memory: 12Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_allows_database_named_non_database_image_workload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: redis-commander
                  labels:
                    cloud.sealos.io/app-deploy-manager: redis-commander
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: redis-commander
                          image: ghcr.io/example/redis-commander-ui:1.2.3
                          imagePullPolicy: IfNotPresent
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_allows_kubeblocks_redis_cluster_and_app_statefulset_dependency(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps.kubeblocks.io/v1alpha1
                kind: Cluster
                metadata:
                  name: demo-redis
                  labels:
                    kb.io/database: redis-7.2.7
                    sealos-db-provider-cr: demo-redis
                    clusterdefinition.kubeblocks.io/name: redis
                spec:
                  componentSpecs:
                    - name: redis
                      resources:
                        requests:
                          cpu: 50m
                          memory: 51Mi
                        limits:
                          cpu: 500m
                          memory: 512Mi
                    - name: redis-sentinel
                      resources:
                        requests:
                          cpu: 50m
                          memory: 51Mi
                        limits:
                          cpu: 500m
                          memory: 512Mi
                ---
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo-data
                  labels:
                    app: demo-data
                    cloud.sealos.io/app-deploy-manager: demo-data
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      containers:
                        - name: demo
                          image: ghcr.io/example/demo:1.0.0
                          imagePullPolicy: IfNotPresent
                          env:
                            - name: REDIS_HOST
                              value: demo-redis-redis-redis.default.svc.cluster.local
                            - name: REDIS_PASSWORD
                              valueFrom:
                                secretKeyRef:
                                  name: demo-redis-redis-account-default
                                  key: password
                  volumeClaimTemplates:
                    - metadata:
                        name: data
                      spec:
                        resources:
                          requests:
                            storage: 1Gi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_allows_database_client_init_jobs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: batch/v1
                kind: Job
                metadata:
                  name: demo-pg-init
                spec:
                  template:
                    spec:
                      containers:
                        - name: pg-init
                          image: postgres:16-alpine
                          imagePullPolicy: IfNotPresent
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R039" for item in violations))

    def test_detects_invalid_managed_workload_resource_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 30m
                              memory: 160Mi
                            limits:
                              cpu: 300m
                              memory: 384Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R038" for item in violations))

    def test_detects_invalid_resource_ladder_with_template_conditionals(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: grafana/grafana:12.0.2
                spec:
                  selector:
                    matchLabels:
                      app: demo
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: grafana/grafana:12.0.2
                          imagePullPolicy: IfNotPresent
                          env:
                            ${{ if(inputs.use_postgresql === 'true') }}
                            - name: PG_HOST
                              valueFrom:
                                secretKeyRef:
                                  name: demo-pg-conn-credential
                                  key: host
                            ${{ endif() }}
                          resources:
                            requests:
                              cpu: 50m
                              memory: 96Mi
                            limits:
                              cpu: 300m
                              memory: 384Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R038" for item in violations))

    def test_detects_request_not_derived_from_limits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 100m
                              memory: 256Mi
                            limits:
                              cpu: 1
                              memory: 1024Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R038" for item in violations))

    def test_passes_valid_managed_workload_resource_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 50m
                              memory: 51Mi
                            limits:
                              cpu: 500m
                              memory: 512Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R038" for item in violations))

    def test_passes_1024mi_managed_workload_resource_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 100m
                              memory: 102Mi
                            limits:
                              cpu: 1
                              memory: 1024Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R038" for item in violations))


    def test_rejects_bare_g_memory_limit_for_template_api_quota_preview(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 50m
                              memory: 400Mi
                            limits:
                              cpu: 500m
                              memory: 4G
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertTrue(any(item.rule_id == "R038" for item in violations))

    def test_passes_4096mi_managed_workload_resource_ladder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: StatefulSet
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                  annotations:
                    originImageName: nginx:1.27.2
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          resources:
                            requests:
                              cpu: 50m
                              memory: 409Mi
                            limits:
                              cpu: 500m
                              memory: 4096Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R038" for item in violations))

    def test_passes_managed_workload_baseline_controls(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: demo
              labels:
                cloud.sealos.io/app-deploy-manager: demo
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
            ---
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: demo-data
              labels:
                cloud.sealos.io/app-deploy-manager: demo-data
            spec:
              revisionHistoryLimit: 1
              template:
                spec:
                  automountServiceAccountToken: false
                  containers:
                    - name: demo
                      image: nginx:1.27.2
                      imagePullPolicy: IfNotPresent
              volumeClaimTemplates:
                - metadata:
                    name: data
                  spec:
                    resources:
                      requests:
                        storage: 1Gi
            ```
            """
        )
        self.assertFalse(any(item.rule_id in {"R009", "R010", "R011"} for item in violations))

    def test_main_container_multiline_bootstrap_command_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          command:
                            - /bin/sh
                            - -ec
                            - |
                              cp -r /defaults/* /data/
                              chmod -R 777 /data
                              psql -c 'select 1'
                              exec nginx -g 'daemon off;'
                          resources:
                            requests:
                              cpu: 20m
                              memory: 25Mi
                            limits:
                              cpu: 200m
                              memory: 256Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            r042 = [item for item in violations if item.rule_id == "R042"]
            self.assertTrue(r042)
            self.assertTrue(all(item.severity == "error" for item in r042))

    def test_main_container_short_exec_wrapper_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "billionmail" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: billionmail
                  labels:
                    cloud.sealos.io/app-deploy-manager: billionmail
                    app: billionmail
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: billionmail
                      containers:
                        - name: billionmail
                          image: billionmail/core:4.9.3
                          imagePullPolicy: IfNotPresent
                          workingDir: /opt/billionmail/core
                          command:
                            - /bin/sh
                            - -ec
                            - mkdir -p template && exec ./billionmail
                          resources:
                            requests:
                              cpu: 20m
                              memory: 25Mi
                            limits:
                              cpu: 200m
                              memory: 256Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/billionmail/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R042" for item in violations))

    def test_main_container_contract_ignores_init_container_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "demo" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: apps/v1
                kind: Deployment
                metadata:
                  name: demo
                  labels:
                    cloud.sealos.io/app-deploy-manager: demo
                    app: demo
                spec:
                  revisionHistoryLimit: 1
                  template:
                    spec:
                      automountServiceAccountToken: false
                      imagePullSecrets:
                        - name: demo
                      initContainers:
                        - name: init-demo
                          image: postgres:16.4-alpine
                          imagePullPolicy: IfNotPresent
                          command:
                            - /bin/sh
                            - -ec
                            - |
                              cp -r /defaults/* /data/
                              chmod -R 777 /data
                              psql -c 'select 1'
                      containers:
                        - name: demo
                          image: nginx:1.27.2
                          imagePullPolicy: IfNotPresent
                          command: ["nginx", "-g", "daemon off;"]
                          resources:
                            requests:
                              cpu: 20m
                              memory: 25Mi
                            limits:
                              cpu: 200m
                              memory: 256Mi
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/demo/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R042" for item in violations))

    def test_optional_object_storage_choice_input_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "mindsdb" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: mindsdb
                spec:
                  title: MindsDB
                  url: https://mindsdb.com
                  gitRepo: https://github.com/mindsdb/mindsdb
                  author: Sealos
                  description: MindsDB template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/mindsdb/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: MindsDB 模板
                  categories:
                    - ai
                  inputs:
                    file_storage:
                      description: File storage backend
                      type: choice
                      default: local
                      options:
                        - local
                        - s3
                ---
                ${{ if(inputs.file_storage === 's3') }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ---
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/mindsdb/index.yaml"],
            )
            r044 = [item for item in violations if item.rule_id == "R044"]
            self.assertTrue(r044)
            self.assertTrue(any("inputs.file_storage" in item.message for item in r044))

    def test_optional_object_storage_boolean_input_passes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "mindsdb" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: mindsdb
                spec:
                  title: MindsDB
                  url: https://mindsdb.com
                  gitRepo: https://github.com/mindsdb/mindsdb
                  author: Sealos
                  description: MindsDB template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/mindsdb/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: MindsDB 模板
                  categories:
                    - ai
                  inputs:
                    enable_s3_storage:
                      description: Use Sealos Object Storage as S3-compatible storage
                      type: boolean
                      default: 'false'
                      required: false
                ---
                ${{ if(inputs.enable_s3_storage === 'true') }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ---
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/mindsdb/index.yaml"],
            )
            self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_optional_object_storage_boolean_with_extra_clause_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                enable_object_storage:
                  description: Enable optional object storage
                  type: boolean
                  default: 'false'
            ---
            ${{ if(inputs.enable_object_storage === 'true' || true) }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ${{ endif() }}
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("condition must test" in item.message for item in r044))

    def test_optional_object_storage_boolean_without_true_comparison_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill = root / "SKILL.md"
            refs_dir = root / "references"
            refs_file = refs_dir / "sample.md"
            rules_file = refs_dir / "rules-registry.yaml"
            artifact_file = root / "template" / "mindsdb" / "index.yaml"

            write_file(skill, "# no yaml snippets\n")
            write_file(refs_file, "# refs\n")
            write_registry(rules_file)
            write_file(
                artifact_file,
                """
                apiVersion: app.sealos.io/v1
                kind: Template
                metadata:
                  name: mindsdb
                spec:
                  title: MindsDB
                  url: https://mindsdb.com
                  gitRepo: https://github.com/mindsdb/mindsdb
                  author: Sealos
                  description: MindsDB template
                  icon: https://raw.githubusercontent.com/labring-actions/templates/kb-0.9/template/mindsdb/logo.png
                  templateType: inline
                  locale: en
                  i18n:
                    zh:
                      description: MindsDB 模板
                  categories:
                    - ai
                  inputs:
                    enable_s3_storage:
                      description: Use Sealos Object Storage as S3-compatible storage
                      type: boolean
                      default: 'false'
                      required: false
                ---
                ${{ if(inputs.enable_s3_storage) }}
                apiVersion: objectstorage.sealos.io/v1
                kind: ObjectStorageBucket
                metadata:
                  name: ${{ defaults.app_name }}
                spec:
                  policy: private
                ---
                ${{ endif() }}
                """,
            )

            violations = CHECKER.run_checks(
                skill,
                refs_dir,
                rules_file,
                additional_include_paths=["template/mindsdb/index.yaml"],
            )
            r044 = [item for item in violations if item.rule_id == "R044"]
            self.assertTrue(r044)
            self.assertTrue(any("condition must test" in item.message for item in r044))

    def test_object_storage_provider_toggle_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                use_sealos_objectstorage:
                  description: Use Sealos Object Storage instead of bundled MinIO
                  type: boolean
                  default: 'false'
                  required: false
            ---
            ${{ if(inputs.use_sealos_objectstorage === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ${{ endif() }}
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("provider/backend selector" in item.message for item in r044))

    def test_managed_object_storage_provider_toggles_fail(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                use_managed_object_storage:
                  description: Use managed object storage
                  type: boolean
                  default: 'false'
                use_managed_s3:
                  description: Use managed S3
                  type: boolean
                  default: 'false'
                use_aws_s3:
                  description: Use AWS S3
                  type: boolean
                  default: 'false'
                use_managed_s3_bucket:
                  description: Use the managed S3 bucket
                  type: boolean
                  default: 'false'
                use_aws:
                  description: Use AWS S3
                  type: boolean
                  default: 'false'
                use_managed:
                  description: Use managed object storage
                  type: boolean
                  default: 'false'
                useManagedS3:
                  description: Use managed S3
                  type: boolean
                  default: 'false'
            ---
            ${{ if(inputs.use_managed_object_storage === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}-object-storage
            spec:
              policy: private
            ${{ endif() }}
            ---
            ${{ if(inputs.use_managed_s3 === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}-s3
            spec:
              policy: private
            ${{ endif() }}
            ---
            ${{ if(inputs.use_aws_s3 === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}-aws
            spec:
              policy: private
            ${{ endif() }}
            ---
            ${{ if(inputs.use_managed_s3_bucket === 'true') }}
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}-managed-bucket
            spec:
              policy: private
            ${{ endif() }}
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(7, len(r044))
        self.assertTrue(any("inputs.use_managed_object_storage" in item.message for item in r044))
        self.assertTrue(any("inputs.use_managed_s3" in item.message for item in r044))
        self.assertTrue(any("inputs.use_aws_s3" in item.message for item in r044))
        self.assertTrue(any("inputs.use_managed_s3_bucket" in item.message for item in r044))
        self.assertTrue(any("inputs.use_aws" in item.message for item in r044))
        self.assertTrue(any("inputs.use_managed" in item.message for item in r044))
        self.assertTrue(any("inputs.useManagedS3" in item.message for item in r044))

    def test_numeric_object_storage_provider_selectors_fail(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                object_storage_provider:
                  description: Object storage provider
                  type: number
                  default: '0'
                storage_backend:
                  description: Storage backend
                  type: integer
                  default: '0'
                use_managed_s3:
                  description: Use managed S3
                  type: number
                  default: '0'
                storage:
                  description: 0=local, 1=S3
                  type: number
                  default: '0'
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(4, len(r044))
        self.assertTrue(any("inputs.object_storage_provider" in item.message for item in r044))
        self.assertTrue(any("inputs.storage_backend" in item.message for item in r044))
        self.assertTrue(any("inputs.use_managed_s3" in item.message for item in r044))
        self.assertTrue(any("inputs.storage" in item.message for item in r044))

    def test_string_object_storage_provider_values_fail(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                file_storage:
                  description: File storage implementation
                  type: string
                  default: s3
                data_storage:
                  description: Data storage implementation
                  type: string
                  options:
                    - [local, s3]
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(2, len(r044))
        self.assertTrue(any("inputs.file_storage" in item.message for item in r044))
        self.assertTrue(any("inputs.data_storage" in item.message for item in r044))

    def test_choice_description_that_only_mentions_s3_passes(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                backup_format:
                  description: Archive format for files stored in S3
                  type: choice
                  default: zip
                  options:
                    - zip
                    - tar
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_unconditional_local_s3_storage_selector_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                storage_backend:
                  description: Storage backend
                  type: choice
                  default: local
                  options:
                    - local
                    - s3
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertTrue(r044)
        self.assertTrue(any("inputs.storage_backend" in item.message for item in r044))

    def test_bare_storage_backend_selector_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                storage_backend:
                  description: Storage backend
                  type: string
                  default: local
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertTrue(r044)
        self.assertTrue(any("inputs.storage_backend" in item.message for item in r044))

    def test_managed_bucket_with_minio_server_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ---
            apiVersion: apps/v1
            kind: StatefulSet
            metadata:
              name: ${{ defaults.app_name }}-minio
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-minio
                      image: minio/minio:RELEASE.2025-09-07T16-13-09Z
                      imagePullPolicy: IfNotPresent
                    - name: ${{ defaults.app_name }}-minio-secondary
                      image: bitnami/minio:2025.7.23
                      imagePullPolicy: IfNotPresent
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("bundled MinIO server" in item.message for item in r044))

    def test_managed_bucket_with_bitnami_legacy_minio_server_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-minio
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-minio
                      image: docker.io/bitnamilegacy/minio:2025.7.23
                      imagePullPolicy: IfNotPresent
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("bitnamilegacy/minio" in item.message for item in r044))

    def test_required_object_storage_with_compatibility_proxy_passes(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.object-storage-compatibility-proxy-source: https://docs.example.com/storage/proxy
            spec: {}
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-s3-gateway
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-s3-gateway
                      image: envoyproxy/envoy:v1.34.1
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: APPFLOWY_S3_MINIO_URL
                          value: http://${{ defaults.app_name }}-s3-proxy:9000
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_object_storage_compatibility_proxy_requires_source_evidence(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-s3-proxy
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-s3-proxy
                      image: openresty/openresty:1.27.1.2-alpine
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: APPFLOWY_S3_MINIO_URL
                          value: http://${{ defaults.app_name }}-s3-proxy:9000
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("compatibility-proxy-source" in item.message for item in r044))

    def test_compatibility_gateway_with_s3_env_requires_source_evidence(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-compatibility-gateway
            spec:
              template:
                spec:
                  containers:
                    - name: gateway
                      image: envoyproxy/envoy:v1.34.1
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: S3_ENDPOINT
                          value: https://storage.example.com
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("compatibility-proxy-source" in item.message for item in r044))

    def test_s3_proxy_sidecar_with_pvc_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.object-storage-compatibility-proxy-source: https://docs.example.com/storage/proxy
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-api
            spec:
              template:
                spec:
                  containers:
                    - name: api
                      image: example/api:1.0.0
                      imagePullPolicy: IfNotPresent
                    - name: s3-proxy
                      image: envoyproxy/envoy:v1.34.1
                      imagePullPolicy: IfNotPresent
                  volumes:
                    - name: proxy-data
                      persistentVolumeClaim:
                        claimName: ${{ defaults.app_name }}-s3-proxy
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("persistent storage" in item.message for item in r044))

    def test_object_storage_compatibility_proxy_with_pvc_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.object-storage-compatibility-proxy-source: https://docs.example.com/storage/proxy
            spec: {}
            ---
            apiVersion: objectstorage.sealos.io/v1
            kind: ObjectStorageBucket
            metadata:
              name: ${{ defaults.app_name }}
            spec:
              policy: private
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-s3-proxy
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-s3-proxy
                      image: nginx:1.27.5-alpine
                      imagePullPolicy: IfNotPresent
                      env:
                        - name: S3_ENDPOINT
                          value: http://${{ defaults.app_name }}-s3-proxy:9000
                  volumes:
                    - name: proxy-data
                      persistentVolumeClaim:
                        claimName: ${{ defaults.app_name }}-s3-proxy
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("persistent storage" in item.message for item in r044))

    def test_external_object_storage_compatibility_proxy_with_pvc_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.external-object-storage-source: https://docs.example.com/storage/s3
                docker-to-sealos.object-storage-compatibility-proxy-source: https://docs.example.com/storage/proxy
            spec:
              inputs:
                external_s3_endpoint:
                  description: External S3 endpoint
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-s3-gateway
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-s3-gateway
                      image: envoyproxy/envoy:v1.34.1
                      imagePullPolicy: IfNotPresent
                  volumes:
                    - name: proxy-data
                      persistentVolumeClaim:
                        claimName: ${{ defaults.app_name }}-s3-proxy
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("persistent storage" in item.message for item in r044))

    def test_object_storage_compatibility_proxy_with_nfs_fails(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
              annotations:
                docker-to-sealos.object-storage-compatibility-proxy-source: https://docs.example.com/storage/proxy
            spec: {}
            ---
            apiVersion: apps/v1
            kind: Deployment
            metadata:
              name: ${{ defaults.app_name }}-s3-proxy
            spec:
              template:
                spec:
                  containers:
                    - name: ${{ defaults.app_name }}-s3-proxy
                      image: nginx:1.27.5-alpine
                      imagePullPolicy: IfNotPresent
                  volumes:
                    - name: proxy-data
                      nfs:
                        server: storage.example.com
                        path: /exports/s3-proxy
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("persistent storage" in item.message for item in r044))

    def test_non_storage_provider_input_passes_object_storage_rule(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                database_provider:
                  description: Database provider
                  type: choice
                  default: postgres
                  options:
                    - postgres
                    - mysql
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_minio_storage_size_input_passes_object_storage_rule(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                minio_storage:
                  description: Storage size for MinIO in Gi
                  type: number
                  default: '5'
                  required: true
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_minio_storage_size_string_input_passes_object_storage_rule(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                minio_storage_size:
                  description: Storage size for MinIO
                  type: string
                  default: 5Gi
                  required: true
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_minio_runtime_configuration_inputs_pass_object_storage_rule(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                minio_use_ssl:
                  description: Use TLS for the MinIO endpoint
                  type: boolean
                  default: 'true'
                minio_storage_class:
                  description: Storage class for MinIO data
                  type: string
                  default: standard
            """
        )

        self.assertFalse(any(item.rule_id == "R044" for item in violations))

    def test_minio_provider_toggle_fails_object_storage_rule(self):
        violations = self.run_artifact_checker(
            """
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo
            spec:
              inputs:
                use_minio:
                  description: Use bundled MinIO
                  type: boolean
                  default: 'false'
            """
        )

        r044 = [item for item in violations if item.rule_id == "R044"]
        self.assertEqual(1, len(r044))
        self.assertTrue(any("inputs.use_minio" in item.message for item in r044))

    def test_object_storage_input_text_fails_closed_on_nested_options(self):
        nested_options: list[Any] = ["s3"]
        for _ in range(4):
            nested_options = [nested_options] * 8

        rendered = APP_RULES_MODULE._object_storage_input_text({"options": nested_options})

        self.assertIn("object storage provider", rendered)
        self.assertLessEqual(len(rendered), APP_RULES_MODULE.OBJECT_STORAGE_INPUT_TEXT_MAX_CHARS)

    def test_object_storage_choice_fails_closed_after_option_limit(self):
        input_spec = {
            "type": "choice",
            "options": [f"local-{index}" for index in range(32)] + ["s3"],
        }

        self.assertTrue(APP_RULES_MODULE._is_object_storage_provider_selector("data_store", input_spec))

    def test_passes_minimal_compliant_docs(self):
        violations = self.run_checker(
            """
            ```yaml
            apiVersion: app.sealos.io/v1
            kind: Template
            metadata:
              name: demo-app
            spec:
              title: Demo
            ---
            apiVersion: app.sealos.io/v1
            kind: App
            metadata:
              name: demo-app
              labels:
                cloud.sealos.io/app-deploy-manager: demo-app
            spec:
              data:
                url: https://demo.example.com
              displayType: normal
              type: link
            ```
            """
        )
        self.assertEqual([], violations)

    def test_registry_mismatch_raises(self):
        with self.assertRaises(ValueError):
            self.run_checker(
                "# ok",
                rules_override="""
                version: 1
                rules:
                  - id: R001
                    description: test
                    severity: error
                """,
            )

    def test_registry_invalid_severity_raises(self):
        broken = render_registry(overrides={"R001": {"severity": "critical"}})
        with self.assertRaises(ValueError):
            self.run_checker("# ok", rules_override=broken)


class ArchitectureRefactorTests(unittest.TestCase):
    def test_line_locator_uses_index_for_simple_key_patterns(self):
        locator = LineLocator(
            start_line=20,
            lines=(
                "apiVersion: apps/v1",
                "kind: Deployment",
                "spec:",
                "  template:",
            ),
        )

        self.assertEqual(22, locator.find(r"^\s*spec\s*:"))
        self.assertEqual(23, locator.find(r"^\s*template\s*:"))
        self.assertEqual(20, locator.find(r"^\s*metadata\s*:", default=20))

    def test_legacy_helper_exports_match_new_workload_helpers(self):
        sample = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [{"name": "main", "image": "nginx:1.27.2"}],
                        "initContainers": [{"name": "init", "image": "busybox:1.36"}],
                    }
                }
            }
        }

        self.assertEqual(list(iter_containers(sample)), list(legacy_iter_containers(sample)))


if __name__ == "__main__":
    unittest.main()
