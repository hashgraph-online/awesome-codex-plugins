#!/usr/bin/env python3
"""hyper-excel entry point: dispatch one subcommand to one module.

    python3 hyper_excel.py doctor
    python3 hyper_excel.py inspect <workbook> [--rows N] [--json]
    python3 hyper_excel.py verify  <workbook> [--json]
    python3 hyper_excel.py build   --spec spec.json --out out.xlsx
    python3 hyper_excel.py build   --csv data.csv --out out.xlsx [--sheet 이름]
    python3 hyper_excel.py patch   <workbook> --out out.xlsx [operations...]
    python3 hyper_excel.py recalc  <workbook> --out out.xlsx
    python3 hyper_excel.py profile <file.csv|file.xlsx>
    python3 hyper_excel.py test

Each subcommand calls the matching module's own `main(argv)`, so every script
stays runnable on its own. Nothing here needs a third-party package; `doctor`
reports which optional extras exist so the skill can state what is possible on
this machine. Python 3.8+ and the standard library only.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

COMMANDS = {
    "inspect": "inspect_workbook",
    "verify": "verify_formulas",
    "build": "build_workbook",
    "patch": "patch_workbook",
    "recalc": "recalc_cached",
    "profile": "profile_table",
}

SELF_TEST_ORDER = [
    "inspect_workbook",
    "verify_formulas",
    "build_workbook",
    "patch_workbook",
    "recalc_cached",
    "profile_table",
]


def version_tuple():
    return sys.version_info[:2]


def doctor():
    """Report the interpreter and every optional engine, without installing anything."""
    import json
    import shutil

    optional = [
        ("openpyxl", "independent read-back of a workbook"),
        ("xlsxwriter", "alternative writer (write-only; unused here)"),
        ("pandas", "dataframe intake (unused here)"),
        ("uv", "runs a throwaway interpreter with --with openpyxl"),
        ("libreoffice", "headless convert / recalculate"),
        ("soffice", "headless convert / recalculate"),
        ("zip", "package inspection from the shell"),
        ("unzip", "package inspection from the shell"),
    ]
    available = {}
    for name, purpose in optional:
        path = shutil.which(name)
        available[name] = {"present": bool(path), "path": path, "purpose": purpose}

    try:
        import openpyxl  # noqa: F401

        openpyxl_version = getattr(openpyxl, "__version__", "unknown")
    except Exception:
        openpyxl_version = None

    engines = {
        "excel": bool(shutil.which("open") and sys.platform == "darwin"),
        "libreoffice": bool(available["libreoffice"]["present"] or available["soffice"]["present"]),
    }
    report = {
        "ok": True,
        "python": {"version": ".".join(str(p) for p in sys.version_info[:3]), "executable": sys.executable},
        "python_supported": version_tuple() >= (3, 8),
        "tools": os.path.join(HERE),
        "optional": available,
        "openpyxlImportable": openpyxl_version,
        "recalculation": {
            "builtinEvaluator": True,
            "spreadsheetEngine": engines["libreoffice"],
            "note": "수식은 번들 평가기로 재계산하고, 엔진이 없으면 그 한계를 보고한다",
        },
        "readback": {
            "openpyxl": openpyxl_version is not None,
            "uvWithOpenpyxl": bool(available["uv"]["present"]),
            "note": "독립 읽기 확인은 openpyxl이 있거나 uv가 있으면 가능하다. 없으면 확인이 번들 파서까지였다고 밝힌다",
        },
    }
    if not report["python_supported"]:
        report["ok"] = False
        report["error"] = "E_PYTHON"
        report["detail"] = "Python 3.8+가 필요하다. 현재 %s" % report["python"]["version"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 3


def run_tests():
    import importlib

    failures = []
    for name in SELF_TEST_ORDER:
        module = importlib.import_module(name)
        rc = module.main(["--self-test"])
        if rc not in (0, None):
            failures.append("%s (exit %s)" % (name, rc))
    if failures:
        sys.stderr.write("self-test 실패: %s\n" % ", ".join(failures))
        return 1
    sys.stdout.write("self-test 통과: %d개 도구\n" % len(SELF_TEST_ORDER))
    return 0


def usage(stream=sys.stdout):
    stream.write(__doc__.split("\n\n")[1] + "\n")


def main(argv):
    if version_tuple() < (3, 8):
        sys.stderr.write('{"ok":false,"error":"E_PYTHON","detail":"Python 3.8+가 필요하다"}\n')
        return 3
    if not argv or argv[0] in ("-h", "--help", "help"):
        usage()
        return 0 if argv else 2
    command = argv[0]
    if command == "doctor":
        return doctor()
    if command == "test":
        return run_tests()
    module_name = COMMANDS.get(command)
    if module_name is None:
        sys.stderr.write('{"ok":false,"error":"E_USAGE","detail":"unknown subcommand: %s"}\n' % command)
        usage(sys.stderr)
        return 2
    import importlib

    module = importlib.import_module(module_name)
    return module.main(argv[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))