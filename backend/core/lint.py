"""Code rules that Ruff and import-linter can't express (BUILD_PLAN §8.2, §8.4).

Run as `python -m core.lint` from `backend/`. Prints `path:line: CODE message` for each
violation and exits 1 if there are any.

- AS001: `all_schools` used outside a `with system_scope(...)` block.
- AS002: `.raw()` or `.extra()` (raw SQL) outside a reviewed file.
- AS003: a module importing another module's models, views, serializers or tasks.
- AS004: `Any` or `type: ignore` without a `# reason:` comment on the same line.
"""

import ast
import io
import re
import sys
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
SKIPPED_DIRS = {".venv", "migrations", "__pycache__", ".pytest_cache", ".mypy_cache"}

# Reviewed exceptions, per rule. Keep each one justified.
ALLOWED: dict[str, set[str]] = {
    # Tests of the system_scope guard itself must call all_schools outside one.
    "AS001": {"core/tests/test_tenancy.py"},
    "AS002": set(),
}
PRIVATE_PARTS = {"models", "views", "serializers", "tasks"}
TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore")


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _is_system_scope(item: ast.withitem) -> bool:
    call = item.context_expr
    if not isinstance(call, ast.Call):
        return False
    func = call.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
    return name == "system_scope"


class _Visitor(ast.NodeVisitor):
    def __init__(self, path: str, comments: dict[int, str]) -> None:
        self.path = path
        self.comments = comments
        self.violations: list[Violation] = []
        self._system_scopes = 0
        parts = path.split("/")
        self._app = parts[1] if len(parts) > 2 and parts[0] == "modules" else None

    def _add(self, node: ast.expr | ast.stmt, code: str, message: str) -> None:
        if self.path not in ALLOWED.get(code, set()):
            self.violations.append(Violation(self.path, node.lineno, code, message))

    def visit_With(self, node: ast.With) -> None:
        scoped = any(_is_system_scope(item) for item in node.items)
        self._system_scopes += scoped
        self.generic_visit(node)
        self._system_scopes -= scoped

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "all_schools" and not self._system_scopes:
            self._add(node, "AS001", "all_schools is only allowed inside `with system_scope(...)`")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"raw", "extra"}:
            self._add(node, "AS002", f".{node.func.attr}() is raw SQL; use the ORM")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(node, alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        self._check_import(node, module)
        for alias in node.names:
            self._check_import(node, f"{module}.{alias.name}")

    def _check_import(self, node: ast.stmt, name: str) -> None:
        parts = name.split(".")
        if (
            self._app is not None
            and len(parts) >= 3
            and parts[0] == "modules"
            and parts[1] != self._app
            and parts[2] in PRIVATE_PARTS
        ):
            self._add(
                node,
                "AS003",
                f"modules.{parts[1]}.{parts[2]} is private to that module; "
                "use its selectors or services",
            )

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "Any" and "reason:" not in self.comments.get(node.lineno, ""):
            self._add(node, "AS004", "Any needs a `# reason:` comment on the same line")


def check_file(path: Path) -> list[Violation]:
    relative = path.relative_to(BACKEND).as_posix()
    source = path.read_text(encoding="utf-8")
    # Real comments only, by line: a "type: ignore" inside a string is not one.
    comments = {
        token.start[0]: token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    }
    visitor = _Visitor(relative, comments)
    visitor.visit(ast.parse(source, filename=relative))
    for number, comment in comments.items():
        if TYPE_IGNORE.search(comment) and "reason:" not in comment:
            visitor.violations.append(
                Violation(relative, number, "AS004", "type: ignore needs a `# reason:` comment")
            )
    return visitor.violations


def python_files(root: Path = BACKEND) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if not SKIPPED_DIRS.intersection(path.relative_to(root).parts):
            yield path


def main() -> int:
    violations = [v for path in python_files() for v in check_file(path)]
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
