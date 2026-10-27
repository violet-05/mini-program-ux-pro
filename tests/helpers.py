"""测试辅助。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def run_cli(*args: str, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def run_script(script: str, *args: str, cwd: Path | None = None, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return run_cli(str(SCRIPTS / script), *args, cwd=cwd, timeout=timeout)


def load_json_output(process: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"命令输出不是 JSON：{exc}\nstdout={process.stdout[:1000]}\nstderr={process.stderr[:1000]}"
        ) from exc