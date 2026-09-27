from django.db import models
from django.core.exceptions import ValidationError
from backend.core.models import BaseModel


class Supplier(BaseModel):
    """
    Main Supplier / Main Admin business entity.
    V1 Business Rule: There is EXACTLY ONE top-level Supplier entity.
    """
    singleton_lock = models.BooleanField(
        default=True,
        unique=True,
        editable=False,
        help_text="Enforces that only one Main Supplier can exist in the database."
    )
    name = models.CharField(
        max_length=255,
        default="Main Supplier",
        help_text="Name of the main supplier organization"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the main supplier is active"
    )

    class Meta:
        verbose_name = 'Main Supplier'
        verbose_name_plural = 'Main Supplier'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(singleton_lock=True),
                name='supplier_singleton_lock_true'
            )
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.pk and Supplier.objects.exists():
            raise ValidationError("Only one Main Supplier entity can exist in the system.")
        if self.pk and Supplier.objects.exclude(pk=self.pk).exists():
            raise ValidationError("Only one Main Supplier entity can exist in the system.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, force_policy=None, **kwargs):
        raise ValidationError("The Main Supplier entity cannot be deleted. Use is_active=False instead.")
