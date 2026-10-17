"""Code rules that Ruff and import-linter can't express (BUILD_PLAN §8.2, §8.4).

Run as `python -m core.lint` from `backend/`. Prints `path:line: CODE message` for each
violation and exits 1 if there are any.

- AS001: `all_schools` used outside a `with system_scope(...)` block, where
  `system_scope` must be the one from `core.context`.
- AS002: `.raw()` or `.extra()` (raw SQL) outside a reviewed file.
- AS003: a module importing another module's models, views, serializers or tasks,
  absolutely or relatively.
- AS004: `Any` or `type: ignore` without a `# reason:` comment on the same line.

These catch mistakes, not determined evasion (`importlib`, aliasing through
variables): code review covers that.
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
}
PRIVATE_PARTS = {"models", "views", "serializers", "tasks"}
TYPING_MODULES = {"typing", "typing_extensions"}
TYPE_IGNORE = re.compile(r"#\s*type:\s*ignore")


@dataclass(frozen=True)
class Violation:
    path: str
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message}"


def _module_parts(relative_path: str) -> list[str]:
    """`modules/files/x.py` gives modules.files.x; a package's `__init__` is the package."""
    parts = relative_path.removesuffix(".py").split("/")
    return parts[:-1] if parts[-1] == "__init__" else parts


class _RuleChecker(ast.NodeVisitor):
    def __init__(self, path: str, comments: dict[int, str]) -> None:
        self.path = path
        self.comments = comments
        self.violations: list[Violation] = []
        self._system_scopes = 0
        module = _module_parts(path)
        self._package = module if path.endswith("__init__.py") else module[:-1]
        self._app = module[1] if len(module) >= 2 and module[0] == "modules" else None
        # Local (dotted) names bound to core.context.system_scope, to the core.context
        # module and to the typing modules.
        self._scope_names: set[str] = set()
        self._context_modules: set[str] = set()
        self._typing_modules: set[str] = set()

    def _add(self, node: ast.expr | ast.stmt, code: str, message: str) -> None:
        if self.path not in ALLOWED.get(code, set()):
            self.violations.append(Violation(self.path, node.lineno, code, message))

    # AS001

    def _is_system_scope(self, item: ast.withitem) -> bool:
        call = item.context_expr
        if not isinstance(call, ast.Call):
            return False
        func = call.func
        if isinstance(func, ast.Name):
            return func.id in self._scope_names
        return (
            isinstance(func, ast.Attribute)
            and func.attr == "system_scope"
            and _dotted(func.value) in self._context_modules
        )

    def visit_With(self, node: ast.With) -> None:
        scoped = any(self._is_system_scope(item) for item in node.items)
        self._system_scopes += scoped
        self.generic_visit(node)
        self._system_scopes -= scoped

    def _check_all_schools(self, node: ast.expr) -> None:
        if not self._system_scopes:
            self._add(node, "AS001", "all_schools is only allowed inside `with system_scope(...)`")

    # Names and calls

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr == "all_schools":
            self._check_all_schools(node)
        if node.attr == "Any" and _dotted(node.value) in self._typing_modules:
            self._check_any(node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "Any":
            self._check_any(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"raw", "extra"}:
            self._add(node, "AS002", f".{func.attr}() is raw SQL; use the ORM")
        if _is_getattr_of(node, "all_schools"):
            self._check_all_schools(node)
        self.generic_visit(node)

    # AS003, plus the bindings AS001 and AS004 depend on

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(node, alias.name)
            bound = alias.asname or alias.name
            if alias.name == "core.context":
                self._context_modules.add(bound)
            if alias.name in TYPING_MODULES:
                self._typing_modules.add(bound)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = self._absolute(node)
        self._check_import(node, module)
        for alias in node.names:
            self._check_import(node, f"{module}.{alias.name}")
            bound = alias.asname or alias.name
            if module == "core.context" and alias.name == "system_scope":
                self._scope_names.add(bound)
            if module == "core" and alias.name == "context":
                self._context_modules.add(bound)
            if module in TYPING_MODULES and alias.name == "Any" and bound != "Any":
                self._check_any(node, "an alias of Any")

    def _absolute(self, node: ast.ImportFrom) -> str:
        if not node.level:
            return node.module or ""
        base = self._package[: len(self._package) - (node.level - 1)]
        return ".".join([*base, *([node.module] if node.module else [])])

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

    # AS004

    def _check_any(self, node: ast.expr | ast.stmt, what: str = "Any") -> None:
        if "reason:" not in self.comments.get(node.lineno, ""):
            self._add(node, "AS004", f"{what} needs a `# reason:` comment on the same line")


def _dotted(node: ast.expr) -> str | None:
    """`a.b.c` as a string, or None for anything but a chain of names."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return None if base is None else f"{base}.{node.attr}"
    return None


def _is_getattr_of(call: ast.Call, attribute: str) -> bool:
    return (
        isinstance(call.func, ast.Name)
        and call.func.id == "getattr"
        and len(call.args) >= 2
        and isinstance(call.args[1], ast.Constant)
        and call.args[1].value == attribute
    )


def check_file(path: Path) -> list[Violation]:
    relative = path.relative_to(BACKEND).as_posix()
    source = path.read_text(encoding="utf-8")
    # Real comments only, by line: a "type: ignore" inside a string is not one.
    comments = {
        token.start[0]: token.string
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type == tokenize.COMMENT
    }
    checker = _RuleChecker(relative, comments)
    checker.visit(ast.parse(source, filename=relative))
    for number, comment in comments.items():
        if TYPE_IGNORE.search(comment) and "reason:" not in comment:
            checker.violations.append(
                Violation(relative, number, "AS004", "type: ignore needs a `# reason:` comment")
            )
    return checker.violations


def python_files() -> Iterator[Path]:
    for path in sorted(BACKEND.rglob("*.py")):
        if not SKIPPED_DIRS.intersection(path.relative_to(BACKEND).parts):
            yield path


def main() -> int:
    violations = [v for path in python_files() for v in check_file(path)]
    for violation in violations:
        print(violation)
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
