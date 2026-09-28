from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin
)
from django.db import models
from django.utils import timezone
from backend.core.models import TimeStampedUUIDModel
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

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=16, blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True)
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
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['phone'],
                condition=models.Q(phone__isnull=False),
                name='unique_user_login_phone',
            ),
        ]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
