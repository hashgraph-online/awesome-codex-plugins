"""Render a decision capture candidate from explicit JSON inputs."""

import json
import re
import sys
import unicodedata


REQUIRED = {"title", "decision", "project_path", "folder"}
OPTIONAL = {"rationale"}
UNSAFE_PATH_CHARS = set('<>:"\\|?*[]#^')
DEVICE_NAME = re.compile(r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9¹²³])", re.I)


def validate_segment(value, field):
    if (
        not value
        or value.startswith(".")
        or value != value.strip()
        or value.endswith(".")
        or any(c in UNSAFE_PATH_CHARS or unicodedata.category(c) in {"Cc", "Zl", "Zp"}
               for c in value)
        or DEVICE_NAME.fullmatch(value.split(".", 1)[0].rstrip())
    ):
        raise ValueError(f"{field} contains an unsafe or nonportable path component")


def validate_path(value, field):
    for part in value.split("/"):
        validate_segment(part, field)


def literal_block(text):
    return "\n".join("    " + line if line else "" for line in text.split("\n"))


def render(fields):
    if not isinstance(fields, dict) or not REQUIRED <= fields.keys() <= (REQUIRED | OPTIONAL):
        raise ValueError("provide title, decision, project_path and folder, with optional rationale")
    for name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be nonempty text")
        value.encode("utf-8")
        if any(unicodedata.category(c) == "Cc" and c not in "\n\t" for c in value):
            raise ValueError(f"{name} contains an unsupported control character")

    title = fields["title"]
    folder = fields["folder"]
    project_path = fields["project_path"]
    if "/" in title or title.lower().endswith(".md"):
        raise ValueError("title must be one filename stem without a .md extension")
    validate_segment(title, "title")
    validate_path(folder, "folder")
    validate_path(project_path, "project_path")
    if not project_path.endswith(".md"):
        raise ValueError("project_path must be an exact Markdown note path")

    path = f"{folder}/{title}.md"
    if path.casefold() == project_path.casefold():
        raise ValueError("the decision destination must differ from the project note")
    properties = {"type": "decision", "project": f"[[{project_path}]]"}
    frontmatter = "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}"
                            for key, value in properties.items())
    content = f"---\n{frontmatter}\n---\n\n## Decision\n\n{literal_block(fields['decision'])}\n"
    if "rationale" in fields:
        content += f"\n## Rationale\n\n{literal_block(fields['rationale'])}\n"
    return {"path": path, "properties": properties, "content": content}


def main():
    try:
        result = render(json.loads(sys.stdin.buffer.read().decode("utf-8")))
    except ValueError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
