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

        kept: list[str] = []
        with transaction.atomic():
            school, _ = School.objects.get_or_create(
                slug=SCHOOL_SLUG, defaults={"name": SCHOOL_NAME}
            )
            with tenant_context(school.id):
                for username, display_name, role in USERS:
                    try:
                        # Usernames are unique ignoring case, so look them up that way.
                        user = User.objects.get_by_natural_key(username)
                    except User.DoesNotExist:
                        user = User(
                            username=username,
                            display_name=display_name,
                            status=User.Status.ACTIVE,
                        )
                        user.set_password(password)
                        user.save()
                    else:
                        if not user.check_password(password):
                            kept.append(username)
                    RoleAssignment.objects.get_or_create(user=user, role=role)

        self.stdout.write(f"Seeded {SCHOOL_SLUG} with {len(USERS)} users.")
        if kept:
            # The seed never overwrites a password: say so, so a changed SEED_PASSWORD
            # doesn't look like it took effect.
            self.stdout.write(
                f"{', '.join(sorted(kept))} keep their existing passwords, not SEED_PASSWORD."
            )
