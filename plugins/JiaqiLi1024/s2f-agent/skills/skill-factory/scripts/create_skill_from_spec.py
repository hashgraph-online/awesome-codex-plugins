#!/usr/bin/env python3
"""Create a new skill package from a JSON spec."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def bool_value(raw: Any, default: bool) -> bool:
    if raw is None:
        return default
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off"}:
            return False
    raise SystemExit(f"Invalid boolean value: {raw!r}")


def as_non_empty_list(value: Any, field_name: str) -> List[str]:
    if not isinstance(value, list) or not value:
        raise SystemExit(f"Spec field '{field_name}' must be a non-empty list")
    items: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"Spec field '{field_name}' contains an invalid item: {item!r}")
        items.append(item.strip())
    return items


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except FileNotFoundError:
        raise SystemExit(f"Spec file not found: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Spec is not valid JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("Spec top-level must be a JSON object")
    return data


def yaml_list(items: List[str], indent: str = "  ") -> str:
    return "".join(f"{indent}- {item}\n" for item in items)


def ensure_short_description(raw: str) -> str:
    text = raw.strip()
    if len(text) < 25:
        text = f"Help with {text} workflows"
    if len(text) > 64:
        text = text[:64].rstrip()
    if len(text) < 25:
        text = "Help with tool setup and workflow execution"
    return text


def render_template(template_path: Path, context: Dict[str, str]) -> str:
    text = template_path.read_text()
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create skill package from JSON spec")
    parser.add_argument("--spec", default=None, help="Path to spec JSON")
    parser.add_argument("--list-templates", action="store_true", help="List available templates and exit")
    parser.add_argument("--repo-root", default=None, help="Repository root override")
    parser.add_argument("--output-root", default=None, help="Output root for generated skills")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing skill directory")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--register", dest="register", action="store_true", help="Force registry append")
    parser.add_argument("--no-register", dest="register", action="store_false", help="Disable registry append")
    parser.set_defaults(register=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    factory_root = Path(__file__).resolve().parents[1]
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[3]
    output_root = Path(args.output_root).resolve() if args.output_root else repo_root / "skills"

    if args.list_templates:
        templates_dir = factory_root / "assets" / "templates"
        for t in sorted(templates_dir.iterdir()):
            print(t.name)
        return 0

    if not args.spec:
        raise SystemExit("--spec is required unless --list-templates is used")

    spec = read_json(Path(args.spec).resolve())

    required_fields = ["id", "title", "description", "family", "tool_name", "tasks", "triggers"]
    for field in required_fields:
        if field not in spec:
            raise SystemExit(f"Spec missing required field: {field}")

    skill_id = str(spec["id"]).strip()
    if not ID_RE.match(skill_id):
        raise SystemExit("Spec field 'id' must be lowercase hyphen-case (e.g., my-tool)")

    title = str(spec["title"]).strip()
    description = str(spec["description"]).strip()
    family = str(spec["family"]).strip()
    tool_name = str(spec["tool_name"]).strip()
    tasks = as_non_empty_list(spec["tasks"], "tasks")
    triggers = as_non_empty_list(spec["triggers"], "triggers")

    include_references = bool_value(spec.get("include_references"), True)
    include_real_run_script = bool_value(spec.get("include_real_run_script"), True)
    register_in_registry = bool_value(spec.get("register_in_registry"), True)
    if args.register is not None:
        register_in_registry = args.register

    openai_display_name = str(spec.get("openai_display_name", title)).strip()
    openai_short_description = ensure_short_description(
        str(spec.get("openai_short_description", f"Help with {title} workflows"))
    )
    openai_default_prompt = str(
        spec.get(
            "openai_default_prompt",
            f"Use ${skill_id} to build and run real {tool_name} workflows.",
        )
    ).strip()

    skill_dir = output_root / skill_id
    try:
        relative_skill_path = skill_dir.relative_to(repo_root)
    except ValueError:
        relative_skill_path = skill_dir
    if skill_dir.exists() and not args.overwrite:
        raise SystemExit(f"Skill directory already exists: {skill_dir}. Use --overwrite to replace.")

    if args.dry_run:
        print(f"[dry-run] repo_root={repo_root}")
        print(f"[dry-run] output_root={output_root}")
        print(f"[dry-run] skill_dir={skill_dir}")
        print(f"[dry-run] include_references={include_references}")
        print(f"[dry-run] include_real_run_script={include_real_run_script}")
        print(f"[dry-run] register_in_registry={register_in_registry}")
        return 0

    if skill_dir.exists() and args.overwrite:
        shutil.rmtree(skill_dir)

    (skill_dir / "agents").mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
    if include_references:
        (skill_dir / "references").mkdir(parents=True, exist_ok=True)

    context = {
        "ID": skill_id,
        "ID_UNDERSCORE": skill_id.replace("-", "_"),
        "TITLE": title,
        "DESCRIPTION": description,
        "FAMILY": family,
        "TOOL_NAME": tool_name,
        "TASKS_YAML": yaml_list(tasks, indent="  "),
        "TRIGGERS_YAML": yaml_list(triggers, indent="  "),
        "OPENAI_DISPLAY_NAME": openai_display_name,
        "OPENAI_SHORT_DESCRIPTION": openai_short_description,
        "OPENAI_DEFAULT_PROMPT": openai_default_prompt,
        "SKILL_PATH": str(relative_skill_path),
    }

    templates = factory_root / "assets" / "templates"

    (skill_dir / "SKILL.md").write_text(render_template(templates / "SKILL.md.tmpl", context))
    (skill_dir / "skill.yaml").write_text(render_template(templates / "skill.yaml.tmpl", context))
    (skill_dir / "agents" / "openai.yaml").write_text(
        render_template(templates / "openai.yaml.tmpl", context)
    )

    if include_references:
        reference_templates = [
            "setup-and-troubleshooting.md.tmpl",
            "constraints.md.tmpl",
            "inference-patterns.md.tmpl",
            "family-selection.md.tmpl",
        ]
        for file_name in reference_templates:
            target_name = file_name.replace(".tmpl", "")
            (skill_dir / "references" / target_name).write_text(
                render_template(templates / file_name, context)
            )

    if include_real_run_script:
        script_name = f"run_real_{skill_id.replace('-', '_')}_workflow.py"
        script_path = skill_dir / "scripts" / script_name
        script_path.write_text(render_template(templates / "run_real_workflow.py.tmpl", context))
        script_path.chmod(0o755)

    print(f"[ok] generated skill: {skill_dir}")

    if register_in_registry:
        register_script = factory_root / "scripts" / "register_skill.py"
        cmd = [
            sys.executable,
            str(register_script),
            "--repo-root",
            str(repo_root),
            "--skill-id",
            skill_id,
            "--path",
            str(relative_skill_path),
            # ^^^ derived from actual output location, not hard-coded to skills/
            "--family",
            family,
        ]
        for task in tasks:
            cmd.extend(["--task", task])
        for trigger in triggers:
            cmd.extend(["--trigger", trigger])

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            raise SystemExit("Registry update failed. Generated files are kept.")

    print("[ok] done")
    print()
    print("Next steps:")
    print(f"  1. Edit {relative_skill_path}/references/inference-patterns.md — replace TODO blocks with real executable code")
    print(f"  2. Edit {relative_skill_path}/references/constraints.md — replace TODO lines with real limits and conventions")
    if include_real_run_script:
        script_name = f"run_real_{skill_id.replace('-', '_')}_workflow.py"
        print(f"  3. Edit {relative_skill_path}/scripts/{script_name} — replace stubs with real inference logic")
    print(f"  4. Edit {relative_skill_path}/SKILL.md — populate '## Grounded API/CLI Surface' with verified import paths")
    if not register_in_registry:
        print(f"  5. Run: python skills/skill-factory/scripts/register_skill.py --repo-root . --skill-id {skill_id} --path {relative_skill_path} --family {family} [--task ...] [--trigger ...]")
    print(f"  6. Run: bash scripts/validate_registry.sh && bash scripts/validate_skill_metadata.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
