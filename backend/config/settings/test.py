from .base import *  # noqa: F403
from .base import INSTALLED_APPS, env

DATABASES = {
    "default": env.db(
        "TEST_DATABASE_URL",
        default="postgres://as_owner:as_owner@localhost:5433/as_test",
    ),
}

# Concrete TenantModel subclasses used only by the tenancy tests.
INSTALLED_APPS = [*INSTALLED_APPS, "core.tests.tenancy_app"]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Password of the app role (as_app) that infra/postgres/init creates in the test database.
TEST_APP_ROLE_PASSWORD = env("TEST_APP_ROLE_PASSWORD", default="as_app")
