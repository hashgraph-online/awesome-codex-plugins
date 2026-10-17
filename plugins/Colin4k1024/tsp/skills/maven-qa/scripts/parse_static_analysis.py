#!/usr/bin/env python3
"""
解析静态分析报告目录（ai-coding-service/target/static-analysis），输出静态分析汇总结果 JSON：
- 报告目录：<projectDir>/ai-coding-service/target/static-analysis
- 文件：pmd.html、spotbugs.xml
- 汇总：totalIssues = PMD.totalViolations + SpotBugs.totalBugs
- 汇总：criticalIssues = PMD.criticalViolations + SpotBugs.criticalBugs
- success = (criticalIssues == 0)

Usage:
  python3 parse_static_analysis.py --report-dir /path/to/ai-coding-service/target/static-analysis
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

# PMD 为 HTML，可选使用 beautifulsoup4
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


def _int_attr(elem, name, default=0):
    v = elem.get(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except ValueError:
        return default


# ---------- Checkstyle（与 CheckstyleParser 一致） ----------
def parse_checkstyle(report_dir):
    path = os.path.join(report_dir, "checkstyle-result.xml")
    result = {"totalViolations": 0, "violationsBySeverity": {}, "criticalViolations": []}
    if not os.path.isfile(path):
        return result
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError:
        return result

    by_severity = {}
    critical = []
    for file_elem in root.findall(".//file"):
        file_name = file_elem.get("name", "")
        for err in file_elem.findall("error"):
            severity = (err.get("severity") or "info").lower()
            line = _int_attr(err, "line", None) or 0
            v = {
                "file": file_name,
                "line": line if line else None,
                "severity": err.get("severity", ""),
                "message": err.get("message", ""),
                "source": err.get("source", ""),
            }
            by_severity.setdefault(severity, []).append(v)
            if severity == "error":
                critical.append(v)
    total = sum(len(v) for v in by_severity.values())
    result["totalViolations"] = total
    result["violationsBySeverity"] = {k: len(v) for k, v in by_severity.items()}
    result["criticalViolations"] = critical
    return result


# ---------- SpotBugs（与 SpotBugsParser 一致：critical 判断逻辑） ----------
def _spotbugs_is_critical(priority, type_, category):
    if priority != "High" or not type_ or not category:
        return False
    if category == "SECURITY" or category == "CORRECTNESS" or category == "MT_CORRECTNESS":
        return True
    if category == "BAD_PRACTICE":
        if type_.startswith("OS_") or type_.startswith("ODR_") or type_.startswith("OBL_"):
            return True
        if type_ == "DM_EXIT":
            return True
        return False
    if category == "PERFORMANCE" and type_.startswith("IL_"):
        return True
    return False


def parse_spotbugs(report_dir):
    path = os.path.join(report_dir, "spotbugs.xml")
    result = {"totalBugs": 0, "bugsByPriority": {}, "criticalBugs": []}
    if not os.path.isfile(path):
        return result
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError:
        return result

    by_priority = {}
    critical = []
    for file_elem in root.findall(".//file"):
        classname = file_elem.get("classname", "")
        for bug in file_elem.findall("BugInstance"):
            priority = bug.get("priority", "")
            type_ = bug.get("type", "")
            category = bug.get("category", "")
            line = bug.get("lineNumber")
            line_int = int(line) if line and line.isdigit() else None
            is_crit = _spotbugs_is_critical(priority, type_, category)
            b = {
                "className": classname,
                "type": type_,
                "priority": priority,
                "category": category,
                "line": line_int,
                "message": bug.get("message", ""),
                "critical": is_crit,
            }
            by_priority.setdefault(priority, []).append(b)
            if is_crit:
                critical.append(b)
    total = sum(len(v) for v in by_priority.values())
    result["totalBugs"] = total
    result["bugsByPriority"] = {k: len(v) for k, v in by_priority.items()}
    result["criticalBugs"] = critical
    return result


# ---------- PMD（与 PmdParser 一致：HTML 结构 + critical 为 priority<=2 或规则名匹配） ----------
def _pmd_is_critical(priority, rule):
    if rule is None:
        return False
    if priority is not None and priority <= 2:
        return True
    critical_rules = {
        "BrokenNullCheck", "MisplacedNullCheck", "NullAssignment", "ReturnEmptyCollectionRatherThanNull",
        "EmptyCatchBlock", "EmptyFinallyBlock", "AvoidCatchingGenericException", "AvoidCatchingThrowable",
        "CloseResource", "UseTryWithResources", "AssignmentInOperand", "CompareObjectsWithEquals",
        "OverrideBothEqualsAndHashcode", "DoubleCheckedLocking", "AvoidCallingFinalize",
        "ConstructorCallsOverridableMethod", "ArrayIsStoredDirectly", "CollectionIsStoredDirectly",
        "MethodReturnsInternalArray",
    }
    if rule in critical_rules:
        return True
    if "Injection" in rule or "Crypto" in rule or "SSL" in rule or "Security" in rule:
        return True
    return False


def parse_pmd(report_dir):
    path = os.path.join(report_dir, "pmd.html")
    result = {"totalViolations": 0, "violationsByPriority": {}, "criticalViolations": []}
    if not os.path.isfile(path):
        return result
    if not HAS_BS4:
        sys.stderr.write("PMD 解析需要 beautifulsoup4: pip3 install beautifulsoup4\n")
        return result
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            doc = BeautifulSoup(f.read(), "html.parser")
    except Exception:
        return result

    current_priority = None
    current_file = None
    by_priority = {}
    critical = []
    for elem in doc.select("h4, h5, table"):
        tag = elem.name
        text = elem.get_text(strip=True) if hasattr(elem, "get_text") else (elem.text or "").strip()

        if tag == "h4" and text.startswith("Priority "):
            try:
                current_priority = int(text.replace("Priority", "").strip())
            except ValueError:
                current_priority = None
            current_file = None
        elif tag == "h5" and current_priority is not None:
            current_file = text
        elif tag == "table" and current_priority is not None and current_file:
            headers = elem.find_all("th")
            if not any("Rule" in (h.get_text() or "") for h in headers):
                continue
            rows = elem.find_all("tr")[1:]
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                rule = ""
                rule_el = cells[0].find("a")
                if rule_el:
                    rule = (rule_el.get_text() or "").strip()
                else:
                    rule = (cells[0].get_text() or "").strip()
                msg = (cells[1].get_text() or "").strip()
                line_text = (cells[2].get_text() or "").strip()
                start_line = None
                if line_text:
                    parts = re.split(r"[–\-]", line_text, 1)
                    try:
                        start_line = int(parts[0].strip())
                    except (ValueError, IndexError):
                        pass
                is_crit = _pmd_is_critical(current_priority, rule or None)
                v = {
                    "file": current_file,
                    "rule": rule,
                    "priority": current_priority,
                    "startLine": start_line,
                    "message": msg,
                    "critical": is_crit,
                }
                by_priority.setdefault(current_priority, []).append(v)
                if is_crit:
                    critical.append(v)
    total = sum(len(v) for v in by_priority.values())
    result["totalViolations"] = total
    result["violationsByPriority"] = {k: len(v) for k, v in by_priority.items()}
    result["criticalViolations"] = critical
    return result


def main():
    parser = argparse.ArgumentParser(description="Parse static analysis reports (PMD/SpotBugs)")
    parser.add_argument("--report-dir", required=True, help="Path to ai-coding-service/target/static-analysis")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (0=compact)")
    args = parser.parse_args()

    report_dir = args.report_dir.rstrip("/")
    pmd = parse_pmd(report_dir)
    spotbugs = parse_spotbugs(report_dir)

    total_issues = pmd.get("totalViolations", 0) + spotbugs.get("totalBugs", 0)
    critical_issues = len(pmd.get("criticalViolations", [])) + len(spotbugs.get("criticalBugs", []))
    success = critical_issues == 0

    response = {
        "pmdResult": pmd,
        "spotBugsResult": spotbugs,
        "totalIssues": total_issues,
        "criticalIssues": critical_issues,
        "success": success,
    }
    indent = args.indent if args.indent else None
    print(json.dumps(response, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
