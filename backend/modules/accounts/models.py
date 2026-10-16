from typing import Any, ClassVar

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.db.models.functions import Lower

from core.managers import TenantManager
from core.models import BaseModel, TenantModel
from modules.accounts.roles import Role


class School(BaseModel):
    """The tenant root. Not a TenantModel: it has no school of its own."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        SUSPENDED = "SUSPENDED"

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    logo_file = models.ForeignKey(
        "files.FileObject", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    locale = models.CharField(max_length=20, default="en")
    timezone = models.CharField(max_length=64, default="UTC")
    # Validated by a pydantic model when school settings arrive (P2).
    settings = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)


class UserManager(TenantManager["User"]):
    def get_by_natural_key(self, username: str | None) -> "User":
        """The current school's user with this username, in any case: the same rule as
        the unique constraint, which compares lower-cased usernames.
        """
        return self.alias(username_lower=Lower("username")).get(
            username_lower=Lower(models.Value(username))
        )


class User(AbstractBaseUser, TenantModel):
    """A person in one school. `AUTH_USER_MODEL`; scoped to the current school like
    every TenantModel. Usernames are unique within a school only, so sign-in always
    names the school (P1-T03).
    """

    class Status(models.TextChoices):
        INVITED = "INVITED"
        ACTIVE = "ACTIVE"
        DEACTIVATED = "DEACTIVATED"

    username = models.CharField(max_length=150)
    email = models.EmailField(null=True, blank=True)
    display_name = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.INVITED)
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret_enc = models.TextField(null=True, blank=True)
    failed_logins = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta(TenantModel.Meta):
        constraints = [
            # Case-insensitive, so "Admin" can't pose as "admin" in the same school.
            models.UniqueConstraint(
                "school", Lower("username"), name="accounts_user_school_username_uniq"
            ),
            models.UniqueConstraint(
                "school", Lower("email"), name="accounts_user_school_email_uniq"
            ),
        ]

    def save(
        self,
        *args: Any,  # reason: passed through to Django's save unchanged
        **kwargs: Any,  # reason: as for *args
    ) -> None:
        # Django counts an empty password as usable; until one is set, mark it unusable.
        if not self.password:
            self.set_unusable_password()
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:  # type: ignore[override]  # reason: Django declares it as a plain attribute
        return self.status == self.Status.ACTIVE


class RoleAssignment(TenantModel):
    Role = Role

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta(TenantModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user", "role"],
                name="accounts_roleassignment_school_user_role_uniq",
            ),
        ]


class OperatorAccount(BaseModel):
    """A platform operator. Not a school user and not a TenantModel: it belongs to no
    school, and sees tenant data only through a support grant (P7).
    """

    email = models.EmailField()
    # A Django password hash (make_password); empty until the operator sets one.
    password_hash = models.CharField(max_length=128, blank=True)
    mfa_secret_enc = models.TextField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("email"), name="accounts_operatoraccount_email_uniq"),
        ]


class Session(BaseModel):
    """A signed-in session of a school user or an operator. Not a TenantModel: it is
    looked up by token hash before any school context exists, and operator sessions
    have no school. Stores only the SHA-256 of the token.
    """

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    operator = models.ForeignKey(OperatorAccount, null=True, blank=True, on_delete=models.CASCADE)
    token_hash = models.CharField(max_length=64, unique=True)
    # The role a user session acts as; empty for an operator session.
    active_role = models.CharField(max_length=20, choices=Role.choices, blank=True)
    mfa_verified_at = models.DateTimeField(null=True, blank=True)
    reauth_at = models.DateTimeField(null=True, blank=True)
    idle_expires_at = models.DateTimeField()
    absolute_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, operator__isnull=True)
                    | models.Q(user__isnull=True, operator__isnull=False)
                ),
                name="accounts_session_user_xor_operator",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(user__isnull=False, active_role__in=Role.values)
                    | models.Q(user__isnull=True, active_role="")
                ),
                name="accounts_session_active_role_valid",
            ),
        ]


class SingleUseToken(TenantModel):
    """A token a user redeems once, before it expires. Stores only the token's SHA-256,
    unique across schools so a token resolves to exactly one row.
    """

    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantModel.Meta):
        abstract = True


class Invitation(SingleUseToken):
    """An invitation to set a first password."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")


class PasswordResetToken(SingleUseToken):
    """A password reset."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
