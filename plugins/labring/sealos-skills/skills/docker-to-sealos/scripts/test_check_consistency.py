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

    def test_allows_registry_pull_secret_via_image_pull_secrets(self):
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
        self.assertFalse(any(item.rule_id in {"R007", "R035"} for item in violations))

    def test_detects_missing_registry_pull_secret_reference(self):
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
