from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from django.db.models.functions import Lower

from core.models import BaseModel, TenantModel


class School(BaseModel):
    """The tenant root. Not a TenantModel: it has no school of its own."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)


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

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

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
    class Role(models.TextChoices):
        SCHOOL_ADMIN = "SCHOOL_ADMIN"
        TEACHER = "TEACHER"
        STUDENT = "STUDENT"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.CharField(max_length=20, choices=Role.choices)

    class Meta(TenantModel.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user", "role"], name="accounts_roleassignment_school_user_role_uniq"
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
    operator = models.ForeignKey(
        OperatorAccount, null=True, blank=True, on_delete=models.CASCADE
    )
    token_hash = models.CharField(max_length=64, unique=True)
    active_role = models.CharField(max_length=20)
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
        ]


class Invitation(TenantModel):
    """A single-use invitation to set a password. Stores only the token's SHA-256."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invitations")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)


class PasswordResetToken(TenantModel):
    """A single-use password reset. Stores only the token's SHA-256."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
