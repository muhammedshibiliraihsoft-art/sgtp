from django.core.exceptions import ValidationError
from django.db import models

from backend.core.models import BaseModel
from apps.clients.normalization import normalize_email, normalize_phone


class ShopOwnedContact(BaseModel):
    """Shared persisted identity/contact fields for Shop-owned people."""

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="%(class)s_records",
    )
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=40, blank=True)
    phone_normalized = models.CharField(max_length=40, blank=True, editable=False)
    email = models.EmailField(blank=True)
    email_normalized = models.CharField(max_length=254, blank=True, editable=False)

    def save(self, *args, **kwargs):
        self.phone_normalized = normalize_phone(self.phone)
        self.email_normalized = normalize_email(self.email)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True


class Client(ShopOwnedContact):
    """A Shop-owned primary client and future billing-owner identity."""

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("tenant", "name"), name="client_shop_name_idx"),
            models.Index(
                fields=("tenant", "phone_normalized"),
                name="client_shop_phone_idx",
            ),
            models.Index(
                fields=("tenant", "email_normalized"),
                name="client_shop_email_idx",
            ),
        ]

    def __str__(self):
        return self.name


class RelatedPerson(ShopOwnedContact):
    """A Shop-owned person whose future Work remains billed to their Client."""

    primary_client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="related_persons",
    )

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("tenant", "name"), name="related_shop_name_idx"),
            models.Index(
                fields=("tenant", "phone_normalized"),
                name="related_shop_phone_idx",
            ),
            models.Index(
                fields=("tenant", "email_normalized"),
                name="related_shop_email_idx",
            ),
            models.Index(
                fields=("tenant", "primary_client"),
                name="related_shop_client_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if self.primary_client_id and self.tenant_id:
            parent = (
                Client.all_objects.filter(pk=self.primary_client_id)
                .values("tenant_id", "deleted")
                .first()
            )
            if (
                parent is None
                or parent["deleted"] is not None
                or parent["tenant_id"] != self.tenant_id
            ):
                raise ValidationError(
                    {"primary_client": "Primary Client must belong to this Shop."}
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.primary_client})"
