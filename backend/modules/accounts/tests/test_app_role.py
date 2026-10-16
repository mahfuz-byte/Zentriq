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
    # django_content_type: an ordinary table whose columns don't change as models grow.
    with app_role.cursor() as cur:
        cur.execute(
            "INSERT INTO django_content_type (app_label, model) "
            "VALUES ('role_check', 'probe') RETURNING id"
        )
        row = cur.fetchone()
        assert row is not None
        cur.execute("UPDATE django_content_type SET model = 'renamed' WHERE id = %s", (row[0],))
        cur.execute("SELECT model FROM django_content_type WHERE id = %s", (row[0],))
        assert cur.fetchone() == ("renamed",)
        cur.execute("DELETE FROM django_content_type WHERE id = %s", (row[0],))
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
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relkind = 'r' "
            "AND c.relname <> 'django_migrations' "
            "AND NOT ("
            "  has_table_privilege(%(role)s, c.oid, 'SELECT')"
            "  AND has_table_privilege(%(role)s, c.oid, 'INSERT')"
            "  AND has_table_privilege(%(role)s, c.oid, 'UPDATE')"
            "  AND has_table_privilege(%(role)s, c.oid, 'DELETE')"
            "  AND NOT has_table_privilege(%(role)s, c.oid, 'TRUNCATE')"
            "  AND NOT has_table_privilege(%(role)s, c.oid, 'REFERENCES')"
            "  AND NOT has_table_privilege(%(role)s, c.oid, 'TRIGGER')"
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
