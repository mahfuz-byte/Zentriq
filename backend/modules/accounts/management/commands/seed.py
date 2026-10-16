import os
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.context import tenant_context
from modules.accounts.models import RoleAssignment, School, User

# The Greenfield skeleton (BUILD_PLAN Appendix E.1). Classes, subjects and the other
# students arrive with the modules that own them.
SCHOOL_SLUG = "greenfield"
SCHOOL_NAME = "Greenfield School"
USERS = [
    ("admin", "Greenfield Admin", RoleAssignment.Role.SCHOOL_ADMIN),
    ("t.rivera", "T. Rivera", RoleAssignment.Role.TEACHER),
    ("sara", "Sara", RoleAssignment.Role.STUDENT),
]


class Command(BaseCommand):
    help = "Create the Greenfield demo school and its users. Safe to run again."

    def handle(self, *args: Any, **options: Any) -> None:  # reason: Django's command signature
        password = os.environ.get("SEED_PASSWORD", "")
        if not password:
            raise CommandError("SEED_PASSWORD must be set: the seed never uses a default password")

        with transaction.atomic():
            school, _ = School.objects.get_or_create(
                slug=SCHOOL_SLUG, defaults={"name": SCHOOL_NAME}
            )
            with tenant_context(school.id):
                for username, display_name, role in USERS:
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={"display_name": display_name, "status": User.Status.ACTIVE},
                    )
                    if created:
                        user.set_password(password)
                        user.save()
                    RoleAssignment.objects.get_or_create(user=user, role=role)

        self.stdout.write(f"Seeded {SCHOOL_SLUG} with {len(USERS)} users.")
