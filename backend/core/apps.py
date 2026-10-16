from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self) -> None:
        from core import checks  # noqa: F401 - registers the tenancy system checks
