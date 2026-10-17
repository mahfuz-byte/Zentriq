"""The back-end gate (`verify`) catches what BUILD_PLAN §8.2 and §8.4 forbid.

Each test runs a checker the way `verify` does, against a planted violation, and
expects it to fail and name the location.
"""

import re
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager

import pytest

from scripts.verify import BACKEND, LINT_IMPORTS


def run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *args],
        cwd=BACKEND,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def ruff_check(filename: str, source: str) -> subprocess.CompletedProcess[str]:
    """Lint `source` as if it were the file `filename` (relative to backend/)."""
    return run("ruff", "check", "--stdin-filename", filename, "-", stdin=source)


@pytest.mark.req("P0-T05")
@pytest.mark.parametrize(
    "source",
    [
        "from django.utils import timezone\n\ntimezone.now()\n",
        "from datetime import datetime\n\ndatetime.now()\n",
        "import datetime\n\ndatetime.date.today()\n",
        "import time\n\ntime.time()\n",
        "import time\n\ntime.time_ns()\n",
        "from django.utils import timezone\n\ntimezone.localtime()\n",
        "from django.utils import timezone\n\ntimezone.localdate()\n",
    ],
)
def test_reading_the_clock_directly_fails_lint(source: str) -> None:
    result = ruff_check("modules/accounts/services.py", source)

    assert result.returncode != 0
    assert "TID251" in result.stdout


RAW_CURSOR = "from django.db import connection\n\nconnection.cursor()\n"


@pytest.mark.req("C-01")
@pytest.mark.parametrize(
    "source",
    [
        RAW_CURSOR,
        "from django.db import connection\n\nconnection.connection.cursor()\n",
        "from django.db import transaction\n\ntransaction.get_connection().cursor()\n",
        "from django.db.models.expressions import RawSQL\n\nRawSQL('SELECT 1', [])\n",
    ],
)
def test_a_raw_cursor_fails_lint_outside_reviewed_files(source: str) -> None:
    result = ruff_check("modules/accounts/selectors.py", source)

    assert result.returncode != 0
    assert "TID251" in result.stdout


@pytest.mark.req("C-01")
def test_a_raw_cursor_is_allowed_in_a_reviewed_file() -> None:
    assert ruff_check("modules/accounts/tests/test_app_role.py", RAW_CURSOR).returncode == 0


@pytest.mark.req("P0-T05")
def test_the_connection_itself_stays_usable() -> None:
    source = (
        "from django.db import connection\n"
        "from django.test.utils import CaptureQueriesContext\n"
        "\n"
        "with CaptureQueriesContext(connection):\n"
        "    print(connection.vendor)\n"
    )
    result = ruff_check("modules/accounts/tests/test_queries.py", source)

    assert result.returncode == 0, result.stdout


@pytest.mark.req("P0-T05")
def test_the_backend_passes_lint_and_format() -> None:
    lint = run("ruff", "check", ".")
    fmt = run("ruff", "format", "--check", ".")

    assert lint.returncode == 0, lint.stdout
    assert fmt.returncode == 0, fmt.stdout


@contextmanager
def planted(relative_path: str, source: str) -> Iterator[None]:
    """Put a module into the real tree for one check, and always take it out again."""
    path = BACKEND / relative_path
    assert not path.exists(), f"{relative_path} already exists"
    path.write_text(source, encoding="utf-8")
    try:
        yield
    finally:
        path.unlink()


def lint_imports() -> subprocess.CompletedProcess[str]:
    return subprocess.run(LINT_IMPORTS, cwd=BACKEND, capture_output=True, text=True, check=False)


@pytest.mark.req("P0-T05")
@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        ("domain/gate_probe.py", "import django\n"),
        ("domain/gate_probe.py", "import core.context\n"),
        ("domain/gate_probe.py", "import subprocess\n"),
        ("domain/gate_probe.py", "import http.client\n"),
        ("domain/gate_probe.py", "import smtplib\n"),
        ("core/gate_probe.py", "import modules.accounts.models\n"),
    ],
)
def test_crossing_a_layer_boundary_fails_the_import_check(relative_path: str, source: str) -> None:
    with planted(relative_path, source):
        result = lint_imports()

    assert result.returncode != 0
    assert "gate_probe" in result.stdout


@pytest.mark.req("P0-T05")
def test_the_backend_respects_the_layer_boundaries() -> None:
    result = lint_imports()

    assert result.returncode == 0, result.stdout


def code_rules() -> subprocess.CompletedProcess[str]:
    return run("core.lint")


@pytest.mark.req("C-01")
@pytest.mark.parametrize(
    ("relative_path", "source", "rule"),
    [
        (
            "modules/accounts/gate_probe.py",
            "from modules.accounts.models import User\n\nUser.all_schools.count()\n",
            "AS001",
        ),
        (
            "modules/accounts/gate_probe.py",
            "from modules.accounts.models import User\n\nUser.objects.raw('SELECT 1')\n",
            "AS002",
        ),
        (
            "modules/accounts/gate_probe.py",
            "from modules.accounts.models import User\n\nUser.objects.extra(where=['1=1'])\n",
            "AS002",
        ),
        ("modules/files/gate_probe.py", "from modules.accounts.models import User\n", "AS003"),
        ("modules/files/gate_probe.py", "from modules.accounts import views\n", "AS003"),
        ("modules/files/gate_probe.py", "from ..accounts.models import User\n", "AS003"),
        ("modules/files/gate_probe.py", "from ..accounts import models\n", "AS003"),
        (
            "modules/accounts/gate_probe.py",
            "from modules.accounts.models import User\n\ngetattr(User, 'all_schools')\n",
            "AS001",
        ),
        (
            "modules/accounts/gate_probe.py",
            "from modules.accounts.models import User\n\n"
            "with open('x') as f, f.system_scope('x'):\n    User.all_schools.count()\n",
            "AS001",
        ),
        ("core/gate_probe.py", "from typing import Any\n\nx: Any = 1\n", "AS004"),
        ("core/gate_probe.py", "x: int = '1'  # type: ignore[assignment]\n", "AS004"),
        ("core/gate_probe.py", "import typing\n\nx: typing.Any = 1\n", "AS004"),
        ("core/gate_probe.py", "from typing import Any as A\n\nx: A = 1\n", "AS004"),
    ],
)
def test_a_forbidden_call_site_fails_the_code_rules(
    relative_path: str, source: str, rule: str
) -> None:
    with planted(relative_path, source):
        result = code_rules()

    assert result.returncode != 0
    assert re.search(rf"gate_probe\.py:\d+: {rule} ", result.stdout), result.stdout


@pytest.mark.req("C-01")
def test_a_package_init_cannot_import_another_modules_models() -> None:
    with appended("modules/files/__init__.py", "from modules.accounts.models import User\n"):
        result = code_rules()

    assert re.search(r"modules/files/__init__\.py:\d+: AS003 ", result.stdout), result.stdout


@pytest.mark.req("C-01")
def test_all_schools_inside_a_system_scope_and_justified_escape_hatches_pass() -> None:
    source = (
        "import enum\n"
        "from typing import Any\n"
        "from typing import Any as A  # reason: a probe\n"
        "\n"
        "import core.context\n"
        "from core import context\n"
        "from core.context import system_scope\n"
        "from modules.accounts.models import User\n"
        "\n"
        "with system_scope('retention'):\n"
        "    User.all_schools.count()\n"
        "with core.context.system_scope('retention'):\n"
        "    User.all_schools.count()\n"
        "with context.system_scope('retention'):\n"
        "    User.all_schools.count()\n"
        "x: Any = 1  # reason: a probe\n"
        "y = enum.Any\n"
        "from .models import User as Same\n"
    )
    with planted("modules/accounts/gate_probe.py", source):
        result = code_rules()

    assert result.returncode == 0, result.stdout


@pytest.mark.req("P0-T05")
def test_the_backend_passes_the_code_rules() -> None:
    result = code_rules()

    assert result.returncode == 0, result.stdout


def typecheck() -> subprocess.CompletedProcess[str]:
    return run("mypy", ".")


@pytest.mark.req("P0-T05")
def test_an_untyped_function_fails_the_typecheck() -> None:
    with planted("core/gate_probe.py", "def double(x):\n    return x * 2\n"):
        result = typecheck()

    assert result.returncode != 0
    assert "gate_probe.py:1" in result.stdout


@pytest.mark.req("P0-T05")
def test_the_backend_passes_the_typecheck() -> None:
    result = typecheck()

    assert result.returncode == 0, result.stdout


@contextmanager
def appended(relative_path: str, source: str) -> Iterator[None]:
    """Append `source` to a real file for one check, and always restore it."""
    path = BACKEND / relative_path
    original = path.read_bytes()
    path.write_bytes(original + source.encode())
    try:
        yield
    finally:
        path.write_bytes(original)


@pytest.mark.req("P0-T05")
def test_a_model_change_without_a_migration_fails_the_gate() -> None:
    probe = "\n\nclass GateProbe(TenantModel):\n    pass\n"
    with appended("core/tests/tenancy_app/models.py", probe):
        result = run("scripts.verify", "--only", "migrations")

    assert result.returncode != 0
    assert "GateProbe" in result.stdout + result.stderr


@pytest.mark.req("P0-T05")
def test_verify_stops_at_the_first_failing_step() -> None:
    with planted("core/gate_probe.py", "import os\n"):  # unused import: a lint failure
        result = run("scripts.verify", "--static")

    assert result.returncode != 0
    assert "FAILED: lint" in result.stdout
    assert "typecheck" not in result.stdout


@pytest.mark.req("P0-T05")
def test_the_backend_passes_the_static_gate() -> None:
    result = run("scripts.verify", "--static")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "All checks passed" in result.stdout
