## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues (mahfuz-byte/Zentriq) via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `GLOSSARY.md` + `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Commands (back end, run from `backend/`)

- Whole gate: `uv run python -m scripts.verify` (`--static` skips tests, `--only <step>` runs one step).
- Tests: `uv run pytest` (needs `docker compose up -d postgres-test` from the repo root).
- One file: `uv run pytest modules/accounts/tests/test_users.py`.
- Django commands use `DJANGO_SETTINGS_MODULE=config.settings.test` locally until the dev database exists.
