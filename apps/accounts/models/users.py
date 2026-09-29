from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin
)
from django.db import models
from django.db.models.functions import Lower, Trim
from django.db.models.lookups import Exact
from django.utils import timezone
from backend.core.models import TimeStampedUUIDModel
from ..identity import generate_user_code
from .user_manager import UserManager


class User(TimeStampedUUIDModel, AbstractBaseUser, PermissionsMixin):
    class Locale(models.TextChoices):
        EN = 'en', 'English'
        AR_KW = 'ar-KW', 'Arabic (Kuwait)'
        BN = 'bn', 'Bangla'
        UR = 'ur', 'Urdu'

    class Appearance(models.TextChoices):
        SYSTEM = 'system', 'System'
        LIGHT = 'light', 'Light'
        DARK = 'dark', 'Dark'

    user_code = models.CharField(max_length=18, unique=True, editable=False)
    owning_shop = models.ForeignKey(
        "tenants.Tenant",
        null=True,
        blank=True,
        editable=False,
        on_delete=models.PROTECT,
        related_name="owned_users",
        help_text="Immutable owning Shop for ordinary accounts; null for Main Supplier accounts.",
    )
    email = models.EmailField(blank=True, null=True, unique=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    auth_version = models.PositiveIntegerField(default=1)
    preferred_locale = models.CharField(
        max_length=5, choices=Locale.choices, blank=True, null=True
    )
    appearance_preference = models.CharField(
        max_length=6, choices=Appearance.choices, default=Appearance.SYSTEM
    )
    date_joined = models.DateTimeField(default=timezone.now) 

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ["first_name", "phone"]

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phone'],
                condition=models.Q(phone__isnull=False),
                name='unique_user_login_phone',
            ),
            models.UniqueConstraint(
                Lower(Trim("email")),
                condition=models.Q(email__isnull=False) & ~models.Q(email=""),
                name="unique_user_email_casefold",
            ),
            models.CheckConstraint(
                condition=~Exact(Trim("first_name"), models.Value("")),
                name="user_first_name_required",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    user_code__regex=r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$"
                ),
                name="user_code_format_valid",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(is_superuser=True)
                    | (
                        models.Q(email__isnull=False)
                        & ~Exact(Trim("email"), models.Value(""))
                        & models.Q(phone__isnull=False)
                        & ~Exact(Trim("phone"), models.Value(""))
                    )
                ),
                name="superuser_requires_contact",
            ),
        ]

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """Return the user's full name."""
        first_name = (self.first_name or "").strip()
        last_name = (self.last_name or "").strip()
        return f"{first_name} {last_name}".strip()

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        if not self.first_name:
            raise ValidationError({"first_name": "First name is required."})
        if self.is_superuser and self.owning_shop_id is not None:
            raise ValidationError(
                {"owning_shop": "Main Supplier accounts are not Shop-owned accounts."}
            )
        if not self.is_superuser and self.owning_shop_id is None:
            raise ValidationError({"owning_shop": "Ordinary accounts require a Shop."})
        if self.is_superuser and (not self.email or not self.phone):
            raise ValidationError("Main Supplier accounts require email and phone.")
        if self.pk:
            from apps.tenants.models import TenantMember, ShopRole

            is_active_shop_admin = TenantMember.objects.filter(
                user_id=self.pk,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
            ).exists()
            if is_active_shop_admin and (not self.email or not self.phone):
                raise ValidationError(
                    "Active Shop Admin accounts require email and phone."
                )

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        from django.db import IntegrityError, transaction

        adding = self._state.adding

        if self.pk and not adding:
            previous = type(self).objects.filter(pk=self.pk).values_list(
                "user_code", "owning_shop_id"
            ).first()
            previous_code = previous[0] if previous else None
            previous_shop_id = previous[1] if previous else None
            if previous_code and self.user_code != previous_code:
                raise ValidationError({"user_code": "User ID is immutable."})
            if previous_shop_id and self.owning_shop_id != previous_shop_id:
                raise ValidationError({"owning_shop": "User Shop ownership is immutable."})
        self.email = (self.email or "").strip().lower() or None
        from ..phone_numbers import InvalidUserPhone, normalize_user_phone

        try:
            self.phone = normalize_user_phone(self.phone)
        except InvalidUserPhone as exc:
            raise ValidationError({"phone": str(exc)}) from exc
        self.first_name = (self.first_name or "").strip()
        self.last_name = (self.last_name or "").strip()
        self.clean()
        if not adding:
            return super().save(*args, **kwargs)
        if self.user_code and not getattr(self, "_system_generated_user_code", False):
            raise ValidationError({"user_code": "User ID is generated by the system."})
        for _ in range(8):
            self.user_code = generate_user_code()
            try:
                with transaction.atomic(using=kwargs.get("using") or self._state.db):
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                cause = getattr(exc, "__cause__", None)
                constraint = getattr(getattr(cause, "diag", None), "constraint_name", None)
                if constraint != "accounts_user_user_code_key":
                    raise
        raise RuntimeError("Unable to allocate a unique User ID; retry account creation.")
