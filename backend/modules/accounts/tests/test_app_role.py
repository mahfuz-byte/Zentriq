from collections.abc import Iterator

import psycopg
import pytest
from django.conf import settings
from django.db import connection

# The role the app connects as in every environment (BUILD_PLAN §3.3).
APP_ROLE = "as_app"


@pytest.fixture
def app_role(db: None) -> Iterator[psycopg.Connection]:
    """A connection to the test database as the app role, outside the test's transaction."""
    db_settings = connection.settings_dict
    with psycopg.connect(
        host=db_settings["HOST"],
        port=db_settings["PORT"],
        dbname=db_settings["NAME"],
        user=APP_ROLE,
        password=settings.TEST_APP_ROLE_PASSWORD,
        autocommit=True,
    ) as conn:
        yield conn


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_the_app_role_can_read_and_write_rows(app_role: psycopg.Connection) -> None:
    with app_role.cursor() as cur:
        cur.execute(
            "INSERT INTO accounts_school (id, created_at, updated_at, slug, name) "
            "VALUES (gen_random_uuid(), now(), now(), 'role-check', 'Role Check') RETURNING id"
        )
        row = cur.fetchone()
        assert row is not None
        cur.execute("UPDATE accounts_school SET name = 'Renamed' WHERE id = %s", (row[0],))
        cur.execute("SELECT name FROM accounts_school WHERE id = %s", (row[0],))
        assert cur.fetchone() == ("Renamed",)
        cur.execute("DELETE FROM accounts_school WHERE id = %s", (row[0],))
        assert cur.rowcount == 1


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
@pytest.mark.parametrize(
    "ddl",
    [
        "CREATE TABLE app_role_probe (id int)",
        "ALTER TABLE accounts_school ADD COLUMN probe int",
        "DROP TABLE accounts_school",
        "TRUNCATE accounts_school",
    ],
)
def test_the_app_role_cannot_change_the_schema(app_role: psycopg.Connection, ddl: str) -> None:
    with pytest.raises(psycopg.errors.InsufficientPrivilege), app_role.cursor() as cur:
        cur.execute(ddl)


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_every_app_table_grants_the_app_role_data_access_only() -> None:
    # Covers tables from every app and migration, including ones created after the
    # grants migration ran (default privileges).
    with connection.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
            "AND table_name <> 'django_migrations' "
            "AND NOT ("
            "  has_table_privilege(%(role)s, quote_ident(table_name), 'SELECT')"
            "  AND has_table_privilege(%(role)s, quote_ident(table_name), 'INSERT')"
            "  AND has_table_privilege(%(role)s, quote_ident(table_name), 'UPDATE')"
            "  AND has_table_privilege(%(role)s, quote_ident(table_name), 'DELETE')"
            "  AND NOT has_table_privilege(%(role)s, quote_ident(table_name), 'TRUNCATE')"
            "  AND NOT has_table_privilege(%(role)s, quote_ident(table_name), 'REFERENCES')"
            "  AND NOT has_table_privilege(%(role)s, quote_ident(table_name), 'TRIGGER')"
            ")",
            {"role": APP_ROLE},
        )
        assert cur.fetchall() == []


@pytest.mark.django_db
@pytest.mark.req("P1-T01")
def test_the_app_role_cannot_rewrite_migration_history(app_role: psycopg.Connection) -> None:
    with app_role.cursor() as cur:
        cur.execute("SELECT count(*) FROM django_migrations")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            cur.execute("DELETE FROM django_migrations")
