"""The back-end gate (BUILD_PLAN §8.3): `uv run python -m scripts.verify` from `backend/`.

Runs every check in order and stops at the first failure. `--static` skips the test
suite (CI's `checks` job, which has no database); `--only STEP` runs one step.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def _script(name: str) -> str:
    # Console scripts without a `python -m` entry point sit next to the interpreter.
    return str(Path(PYTHON).with_name(name))


STEPS: list[tuple[str, list[str]]] = [
    ("format", [PYTHON, "-m", "ruff", "format", "--check", "."]),
    ("lint", [PYTHON, "-m", "ruff", "check", "."]),
    ("typecheck", [PYTHON, "-m", "mypy", "."]),
    ("imports", [_script("lint-imports"), "--no-cache"]),
    ("code-rules", [PYTHON, "-m", "core.lint"]),
    ("migrations", [PYTHON, "manage.py", "makemigrations", "--check", "--dry-run"]),
    ("tests", [PYTHON, "-m", "pytest"]),
]
STATIC = [name for name, _ in STEPS if name != "tests"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--static", action="store_true", help="skip the test suite")
    group.add_argument("--only", choices=[name for name, _ in STEPS], help="run one step")
    args = parser.parse_args(argv)

    if args.only:
        selected = [args.only]
    elif args.static:
        selected = STATIC
    else:
        selected = [name for name, _ in STEPS]

    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.test"}
    for name, command in STEPS:
        if name not in selected:
            continue
        print(f"--- {name}", flush=True)
        if subprocess.run(command, cwd=BACKEND, env=env, check=False).returncode != 0:
            print(f"FAILED: {name}", flush=True)
            return 1
    print("All checks passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
