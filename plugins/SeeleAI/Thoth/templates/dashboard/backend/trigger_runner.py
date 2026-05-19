"""
trigger_runner.py — Async subprocess wrappers for validation scripts.
"""

import asyncio
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


async def _run(cmd: list[str], timeout: int = 60) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "returncode": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
        }
    except asyncio.TimeoutError:
        proc.kill()
        return {"returncode": -1, "stdout": "", "stderr": "Timeout"}
    except Exception as exc:
        return {"returncode": -1, "stdout": "", "stderr": str(exc)}


async def run_validate() -> dict:
    result = await _run(["python", "-m", "thoth.cli", "doctor", "--json"])
    output = result["stdout"] or result["stderr"]
    passed = 1 if result["returncode"] == 0 else 0
    failed = 0 if result["returncode"] == 0 else 1
    return {
        "passed": passed,
        "failed": failed,
        "output": output,
        "returncode": result["returncode"],
    }


async def run_sync() -> dict:
    result = await _run(["python", "-m", "thoth.cli", "init", "--sync"])
    return {
        "output": result["stdout"],
        "returncode": result["returncode"],
    }


async def run_verify(work_id: str) -> dict:
    result = await _run(["python", "-m", "thoth.cli", "status", "--json"])
    return {
        "passed": result["returncode"] == 0 and work_id in result["stdout"],
        "output": result["stdout"] or result["stderr"],
        "returncode": result["returncode"],
    }


async def run_health_check() -> dict:
    validate_all = PROJECT_ROOT / "scripts" / "validate-all.sh"
    if not validate_all.exists():
        return {"returncode": -1, "output": "validate-all.sh not found"}
    result = await _run(["bash", str(validate_all)], timeout=30)
    return {
        "output": result["stdout"],
        "returncode": result["returncode"],
    }
