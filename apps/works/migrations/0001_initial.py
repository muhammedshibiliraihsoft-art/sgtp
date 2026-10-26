import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("catalog", "0024_retire_variant_measurement_mappings"),
        ("clients", "0001_initial"),
        ("tenants", "0010_add_check_work_function"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkOrder",
            fields=[
                ("deleted", models.DateTimeField(db_index=True, editable=False, null=True)),
                ("deleted_by_cascade", models.BooleanField(default=False, editable=False)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sequence", models.PositiveIntegerField()),
                ("work_number", models.CharField(max_length=24)),
                ("status", models.CharField(choices=[("REQUEST", "Request"), ("CUTTING", "Cutting"), ("STITCHING", "Stitching"), ("CHECK", "Check"), ("FINISHING", "Finishing"), ("QC", "Quality control"), ("COMPLETED", "Completed")], default="REQUEST", max_length=16)),
                ("priority", models.CharField(choices=[("NORMAL", "Normal"), ("URGENT", "Urgent"), ("VERY_URGENT", "Very urgent")], default="NORMAL", max_length=16)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("assigned_membership", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assigned_work_orders", to="tenants.tenantmember")),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="clients.client")),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name="created_%(class)s_objects", to=settings.AUTH_USER_MODEL)),
                ("design_version", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="catalog.designversion")),
                ("material", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="catalog.material")),
                ("measurement_set", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="catalog.measurementset")),
                ("related_person", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="clients.relatedperson")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="work_orders", to="tenants.tenant")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name="updated_%(class)s_objects", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ("-created_at", "-id"),
                "indexes": [models.Index(fields=["tenant", "status", "due_date"], name="work_shop_status_due_idx"), models.Index(fields=["tenant", "priority", "created_at"], name="work_shop_priority_idx")],
                "constraints": [
                    models.UniqueConstraint(fields=("tenant", "sequence"), name="work_shop_sequence_uniq"),
                    models.UniqueConstraint(fields=("tenant", "work_number"), name="work_shop_number_uniq"),
                    models.CheckConstraint(condition=models.Q(sequence__gte=1), name="work_sequence_positive"),
                    models.CheckConstraint(condition=models.Q(status__in=["REQUEST", "CUTTING", "STITCHING", "CHECK", "FINISHING", "QC", "COMPLETED"]), name="work_status_valid"),
                    models.CheckConstraint(condition=models.Q(priority__in=["NORMAL", "URGENT", "VERY_URGENT"]), name="work_priority_valid"),
                ],
            },
        ),
    ]
