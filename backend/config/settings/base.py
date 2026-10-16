from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-only")
DEBUG = False
ALLOWED_HOSTS: list[str] = env.list("DJANGO_ALLOWED_HOSTS", default=[])

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "core",
    "modules.accounts",
]

MIDDLEWARE: list[str] = []

ROOT_URLCONF = "config.urls"

DATABASES = {
    "default": env.db(
        "DATABASE_MIGRATE_URL" if env.bool("DJANGO_MIGRATE", default=False) else "DATABASE_URL",
        default="postgres://as_owner:as_owner@localhost:5432/as",
    ),
}
DATABASES["default"]["OPTIONS"] = {"pool": True}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
