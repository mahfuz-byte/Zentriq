# Zentriq

AS, an AI-assisted school assessment platform. The plan is in `BUILD_PLAN.md` and the
requirements are in `SRS of the systenm.md`.

## Back end (Django)

Needs Python 3.13, [uv](https://docs.astral.sh/uv/) and Docker.

```sh
docker compose up -d postgres-test        # test Postgres on :5433, creates the as_app role
cd backend
uv sync
uv run python -m scripts.verify           # the whole gate: format, lint, types, boundaries, rules, migrations, tests
uv run python -m scripts.verify --static  # the same without the test suite
uv run pytest modules/accounts            # one app's tests
```

`verify` stops at the first failing step. The rules it enforces come from
BUILD_PLAN §8.2 and §8.4:

- Ruff formats and lints. Code reads the time only through `core.clock`, and raw
  cursors are allowed only in reviewed files.
- mypy runs in strict mode. Every `Any` and `type: ignore` needs a `# reason:` comment.
- import-linter keeps `domain` pure and stops `core` importing `modules`.
- `python -m core.lint` checks the rest: `all_schools` only inside `system_scope`, no
  `.raw()`/`.extra()`, and no imports of another module's models, views, serializers or
  tasks.

Windows: if `uv` isn't on PATH, run it as `python -m uv`.

## CI

`.github/workflows/ci.yml` runs on every push and pull request:

- `checks` runs `verify --static`.
- `integration` runs the tests against Postgres 17 with coverage.

Protect `main` by requiring both jobs to pass: GitHub → Settings → Branches → Add rule
for `main` → "Require status checks to pass" → select `checks` and `integration`.
