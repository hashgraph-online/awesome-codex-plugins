#!/usr/bin/env python3
"""
Execute a read-only MySQL query. Connection must be provided by the user via arguments (no env/application).
Usage:
  python3 query.py --host HOST --port PORT --user USER --password PASSWORD --database DB --sql "SELECT * FROM t LIMIT 10"
  echo "SELECT 1" | python3 query.py --host 127.0.0.1 --port 3306 --user root --password xxx --database mydb
"""
import sys
import argparse

try:
    import pymysql
except ImportError:
    print("Missing dependency: pip3 install pymysql", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run a read-only MySQL query (connection must be provided by user)")
    parser.add_argument("--host", required=True, help="MySQL host (user must provide)")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port (default 3306)")
    parser.add_argument("--user", required=True, help="MySQL user (user must provide)")
    parser.add_argument("--password", required=True, help="MySQL password (user must provide)")
    parser.add_argument("--database", required=True, help="MySQL database name (user must provide)")
    parser.add_argument("--sql", type=str, help="SQL to execute (SELECT only)")
    args = parser.parse_args()

    sql = args.sql
    if not sql and not sys.stdin.isatty():
        sql = sys.stdin.read()
    if not sql or not sql.strip():
        print("No SQL given. Use --sql '...' or pipe SQL to stdin.", file=sys.stderr)
        sys.exit(1)
    sql = sql.strip().rstrip(";")
    if not sql.upper().strip().startswith("SELECT"):
        print("Only SELECT is allowed.", file=sys.stderr)
        sys.exit(1)

    try:
        conn = pymysql.connect(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            charset="utf8mb4",
        )
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
        if not rows:
            print("(0 rows)")
            return
        keys = list(rows[0].keys())
        widths = [max(len(str(k)), max(len(str(r.get(k, ""))) for r in rows)) for k in keys]
        widths = [min(w, 40) for w in widths]
        sep = " | "
        head = sep.join(k[:40].ljust(widths[i]) for i, k in enumerate(keys))
        line = "-+-".join("-" * w for w in widths)
        print(head)
        print(line)
        for r in rows:
            cells = [str(r.get(k, ""))[:40].ljust(widths[i]) for i, k in enumerate(keys)]
            print(sep.join(cells))
        print(f"({len(rows)} row(s))")
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
