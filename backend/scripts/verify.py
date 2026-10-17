"""The back-end gate (BUILD_PLAN §8.3): `uv run python -m scripts.verify` from `backend/`.

Runs every check in order and stops at the first failure. `--static` skips the test
suite (CI's `checks` job, which has no database); `--only STEP` runs one step.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

BACKEND = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


# import-linter has no `python -m` entry point; its script sits next to the interpreter.
LINT_IMPORTS = [str(Path(PYTHON).with_name("lint-imports")), "--no-cache"]


class Step(NamedTuple):
    name: str
    command: list[str]


STEPS = [
    Step("format", [PYTHON, "-m", "ruff", "format", "--check", "."]),
    Step("lint", [PYTHON, "-m", "ruff", "check", "."]),
    Step("typecheck", [PYTHON, "-m", "mypy", "."]),
    Step("imports", LINT_IMPORTS),
    Step("code-rules", [PYTHON, "-m", "core.lint"]),
    Step("migrations", [PYTHON, "manage.py", "makemigrations", "--check", "--dry-run"]),
    Step("tests", [PYTHON, "-m", "pytest"]),
]
ALL = [step.name for step in STEPS]
STATIC = [name for name in ALL if name != "tests"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--static", action="store_true", help="skip the test suite")
    group.add_argument("--only", choices=ALL, help="run one step")
    args = parser.parse_args(argv)

    if args.only:
        selected = [args.only]
    elif args.static:
        selected = STATIC
    else:
        selected = ALL

    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.test"}
    for step in STEPS:
        if step.name not in selected:
            continue
        print(f"--- {step.name}", flush=True)
        if subprocess.run(step.command, cwd=BACKEND, env=env, check=False).returncode != 0:
            print(f"FAILED: {step.name}", flush=True)
            return 1
    print("All checks passed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
