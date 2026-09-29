from django.db import models
from django.core.validators import RegexValidator
from backend.core.models import BaseModel


class Tenant(BaseModel):
    """
    Tenant model acting as the technical representation for a 'Shop'.
    V1 Business Rule: A Shop is the business workspace and belongs to the single Main Supplier.
    """
    supplier = models.ForeignKey(
        'tenants.Supplier',
        on_delete=models.CASCADE,
        related_name='shops',
        help_text="The Main Supplier that owns this Shop"
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name of the tenant organization"
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9-]+$',
                message='Slug can only contain lowercase letters, numbers, and hyphens.'
            )
        ],
        help_text="URL-friendly identifier for the tenant"
    )
    domain = models.CharField(
        max_length=253,
        blank=True,
        null=True,
        help_text="Custom domain for this tenant (optional)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tenant is active and can be accessed"
    )
    
    # Tenant settings
    max_users = models.PositiveIntegerField(
        help_text="Maximum number of users allowed for this tenant"
    )
    
    # Contact information
    contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email for this tenant"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary contact phone for this tenant"
    )
    
    # Address information
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    default_locale = models.CharField(
        max_length=5,
        choices=[('en', 'English'), ('ar-KW', 'Arabic (Kuwait)'), ('bn', 'Bangla'), ('ur', 'Urdu')],
        blank=True,
        null=True,
    )
    default_timezone = models.CharField(max_length=64, blank=True, null=True)
    default_currency = models.CharField(max_length=3, blank=True, null=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return self.name
    
    @property
    def user_count(self) -> int:
        """
        Return the number of users associated with this tenant.
        Counts both ACTIVE and INACTIVE memberships.
        REMOVED (soft-deleted) memberships are excluded by the default manager.
        """
        return self.memberships.count()
    
    @property
    def is_at_user_limit(self) -> bool:
        """Check if tenant has reached its user limit."""
        return self.user_count >= self.max_users
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.domain:
            # Basic domain validation
            if not self.domain.replace('-', '').replace('.', '').isalnum():
                raise ValidationError({'domain': 'Invalid domain format.'})
