#!/usr/bin/env python3
"""
Langfuse 编码流程追踪脚本 - 异步上报各编码步骤的 Trace/Span。

无需安装任何依赖，使用 Python 内置 urllib 调用 Langfuse REST API。

环境变量：
  LANGFUSE_PUBLIC_KEY  - Langfuse 公钥
  LANGFUSE_SECRET_KEY  - Langfuse 私钥
  LANGFUSE_HOST        - 自部署地址，如 http://localhost:3000

用法：
  # 开始 Trace（同步，输出 trace_id）
  python trace.py trace-start --name "logic-layer-method-impl" [--input '{"method":"xxx"}']

  # 开始 Span（同步，输出 span_id）
  python trace.py span-start --trace-id <id> --name "maven-compile" [--input '{"files":[]}']

  # 结束 Span（建议后台运行: python trace.py span-end ... &）
  python trace.py span-end --span-id <id> [--output '{"exit_code":0}'] [--level DEFAULT|WARNING|ERROR]

  # 结束 Trace（建议后台运行: python trace.py trace-end ... &）
  python trace.py trace-end --trace-id <id> [--output '{"status":"success"}']
"""

import os
import sys
import json
import uuid
import base64
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone


def get_config():
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")

    if not public_key or not secret_key:
        print(
            "Error: LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set",
            file=sys.stderr,
        )
        sys.exit(1)

    credentials = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    return host, credentials


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def ingest(host, credentials, batch):
    body = json.dumps({"batch": batch}).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/public/ingestion",
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        print(f"Langfuse HTTP error {e.code}: {body_text}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Langfuse ingestion failed: {e}", file=sys.stderr)
        return None


def cmd_trace_start(args):
    """创建 Trace，同步执行，输出 trace_id 供后续步骤使用"""
    host, creds = get_config()
    trace_id = str(uuid.uuid4())
    input_data = json.loads(args.input) if args.input else None

    batch = [
        {
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": now_iso(),
            "body": {
                "id": trace_id,
                "name": args.name,
                "timestamp": now_iso(),
                "input": input_data,
                "metadata": {"source": "coding-workflow"},
            },
        }
    ]

    result = ingest(host, creds, batch)
    if result is not None:
        print(trace_id)  # 输出 trace_id，供调用方捕获
    else:
        sys.exit(1)


def cmd_span_start(args):
    """创建 Span，同步执行，输出 span_id 供后续步骤使用"""
    host, creds = get_config()
    span_id = str(uuid.uuid4())
    input_data = json.loads(args.input) if args.input else None

    batch = [
        {
            "id": str(uuid.uuid4()),
            "type": "span-create",
            "timestamp": now_iso(),
            "body": {
                "id": span_id,
                "traceId": args.trace_id,
                "name": args.name,
                "startTime": now_iso(),
                "input": input_data,
            },
        }
    ]

    result = ingest(host, creds, batch)
    if result is not None:
        print(span_id)  # 输出 span_id，供调用方捕获
    else:
        sys.exit(1)


def cmd_span_end(args):
    """结束 Span，异步执行（建议配合 & 后台运行）"""
    host, creds = get_config()
    output_data = json.loads(args.output) if args.output else None

    batch = [
        {
            "id": str(uuid.uuid4()),
            "type": "span-update",
            "timestamp": now_iso(),
            "body": {
                "id": args.span_id,
                "endTime": now_iso(),
                "output": output_data,
                "level": args.level or "DEFAULT",
            },
        }
    ]

    ingest(host, creds, batch)


def cmd_trace_end(args):
    """结束 Trace，异步执行（建议配合 & 后台运行）"""
    host, creds = get_config()
    output_data = json.loads(args.output) if args.output else None

    # 用 trace-create 更新已有 trace 的 output
    batch = [
        {
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": now_iso(),
            "body": {
                "id": args.trace_id,
                "output": output_data,
                "metadata": {"source": "coding-workflow", "completed": True},
            },
        }
    ]

    ingest(host, creds, batch)


def main():
    parser = argparse.ArgumentParser(
        description="Langfuse 编码流程追踪脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # trace-start
    p_ts = subparsers.add_parser("trace-start", help="开始一个 Trace，输出 trace_id")
    p_ts.add_argument("--name", required=True, help="Trace 名称，如 logic-layer-method-impl")
    p_ts.add_argument("--input", help="JSON 格式的输入数据，如 '{\"method\":\"xxx\"}'")

    # span-start
    p_ss = subparsers.add_parser("span-start", help="开始一个 Span，输出 span_id")
    p_ss.add_argument("--trace-id", required=True, help="所属 Trace 的 ID")
    p_ss.add_argument("--name", required=True, help="Span 名称，如 maven-compile")
    p_ss.add_argument("--input", help="JSON 格式的输入数据")

    # span-end
    p_se = subparsers.add_parser("span-end", help="结束一个 Span（建议后台运行）")
    p_se.add_argument("--span-id", required=True, help="要结束的 Span ID")
    p_se.add_argument("--output", help="JSON 格式的输出数据，如 '{\"exit_code\":0}'")
    p_se.add_argument(
        "--level",
        choices=["DEFAULT", "WARNING", "ERROR"],
        default="DEFAULT",
        help="日志级别，失败时用 ERROR",
    )

    # trace-end
    p_te = subparsers.add_parser("trace-end", help="结束一个 Trace（建议后台运行）")
    p_te.add_argument("--trace-id", required=True, help="要结束的 Trace ID")
    p_te.add_argument("--output", help="JSON 格式的最终输出，如 '{\"status\":\"success\"}'")

    args = parser.parse_args()

    if args.command == "trace-start":
        cmd_trace_start(args)
    elif args.command == "span-start":
        cmd_span_start(args)
    elif args.command == "span-end":
        cmd_span_end(args)
    elif args.command == "trace-end":
        cmd_trace_end(args)


if __name__ == "__main__":
    main()
