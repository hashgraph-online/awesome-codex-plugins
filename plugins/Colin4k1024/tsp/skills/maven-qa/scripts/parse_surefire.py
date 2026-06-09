#!/usr/bin/env python3
"""
解析 Maven Surefire 报告目录（target/surefire-reports），输出与 Controller 单测接口一致的 JSON。
通过判定：通过率 > 95% 为 success=true；总数为 0 为 success=false。

Usage:
  python3 parse_surefire.py --report-dir /path/to/target/surefire-reports
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET


def parse_surefire_dir(report_dir: str) -> dict:
    """解析 target/surefire-reports 下所有 TEST-*.xml，返回 UnitTestResult 结构。"""
    total_tests = 0
    total_errors = 0
    total_failures = 0
    total_skipped = 0
    failure_details = []

    if not os.path.isdir(report_dir):
        return {
            "success": False,
            "totalTests": 0,
            "passedTests": 0,
            "failedTests": 0,
            "errorTests": 0,
            "skippedTests": 0,
            "failureDetails": [],
            "message": "报告目录不存在",
        }

    for name in sorted(os.listdir(report_dir)):
        if not name.startswith("TEST-") or not name.endswith(".xml"):
            continue
        path = os.path.join(report_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # 可能有多层 testsuite（根或 testsuites/testsuite）
        suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
        for suite in suites:
            total_tests += int(suite.get("tests", 0))
            total_errors += int(suite.get("errors", 0))
            total_failures += int(suite.get("failures", 0))
            total_skipped += int(suite.get("skipped", 0))
            for tc in suite.findall("testcase"):
                cls = tc.get("classname", "")
                method = tc.get("name", "")
                t = float(tc.get("time", 0) or 0)
                failure = tc.find("failure")
                error = tc.find("error")
                skipped = tc.find("skipped")
                if failure is not None:
                    status = "FAIL"
                    msg = failure.get("message") or ""
                    failure_details.append({
                        "className": cls,
                        "methodName": method,
                        "time": round(t, 3),
                        "status": status,
                        "message": (msg[:500]) if msg else "",
                        "stackTrace": (failure.text or "").strip()[:2000],
                    })
                elif error is not None:
                    status = "ERROR"
                    msg = error.get("message") or ""
                    failure_details.append({
                        "className": cls,
                        "methodName": method,
                        "time": round(t, 3),
                        "status": status,
                        "message": (msg[:500]) if msg else "",
                        "stackTrace": (error.text or "").strip()[:2000],
                    })
                elif skipped is not None:
                    pass  # 只计 skipped 数量，不加入 failureDetails

    passed = max(0, total_tests - total_failures - total_errors - total_skipped)
    success = total_tests > 0 and (passed * 100.0 / total_tests) > 95

    return {
        "success": success,
        "totalTests": total_tests,
        "passedTests": passed,
        "failedTests": total_failures,
        "errorTests": total_errors,
        "skippedTests": total_skipped,
        "failureDetails": failure_details,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse Surefire reports and output UnitTestResult JSON")
    parser.add_argument("--report-dir", required=True, help="Path to target/surefire-reports")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent (0=compact)")
    args = parser.parse_args()

    result = parse_surefire_dir(args.report_dir)
    indent = args.indent if args.indent else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))


if __name__ == "__main__":
    main()
