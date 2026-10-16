from django.db import migrations

# The app connects as as_app (BUILD_PLAN §3.3): data access only. as_owner owns every
# table and runs migrations; default privileges extend the grants to tables it
# creates later. as_app may read django_migrations (Django checks for unapplied
# migrations at startup) but never write it.
GRANT = """
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO as_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO as_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO as_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO as_app;
REVOKE INSERT, UPDATE, DELETE ON django_migrations FROM as_app;
"""

REVOKE = """
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM as_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM as_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM as_app;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM as_app;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_and_roles"),
    ]

    operations = [
        migrations.RunSQL(GRANT, reverse_sql=REVOKE),
    ]
