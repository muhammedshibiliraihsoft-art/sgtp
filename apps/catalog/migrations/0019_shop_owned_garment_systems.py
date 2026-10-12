import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0018_seed_remaining_family_design_defaults"),
        ("tenants", "0009_membership_work_functions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="familyoptiongroup",
            name="selection_mode",
            field=models.CharField(
                choices=[
                    ("SINGLE", "Single selection"),
                    ("MULTI", "Multiple selections"),
                ],
                default="MULTI",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="familyoptiongroup",
            name="is_required",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="garmentfamily",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="garment_families",
                to="tenants.tenant",
            ),
        ),
        migrations.AddField(
            model_name="optiongroup",
            name="tenant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="option_groups",
                to="tenants.tenant",
            ),
        ),
        migrations.AddField(
            model_name="measurementset",
            name="design_version",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="measurement_sets",
                to="catalog.designversion",
            ),
        ),
        migrations.AlterField(
            model_name="design",
            name="variant",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="designs",
                to="catalog.garmentvariant",
            ),
        ),
        migrations.AlterField(
            model_name="garmentfamily",
            name="code",
            field=models.SlugField(max_length=48),
        ),
        migrations.AlterField(
            model_name="optiongroup",
            name="code",
            field=models.SlugField(max_length=48),
        ),
        migrations.AddConstraint(
            model_name="garmentfamily",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted__isnull", True), ("tenant__isnull", True)),
                fields=("code",),
                name="catalog_global_family_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="garmentfamily",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("deleted__isnull", True), ("tenant__isnull", False)
                ),
                fields=("tenant", "code"),
                name="catalog_shop_family_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="optiongroup",
            constraint=models.UniqueConstraint(
                condition=models.Q(("deleted__isnull", True), ("tenant__isnull", True)),
                fields=("code",),
                name="catalog_global_group_code_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="optiongroup",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ("deleted__isnull", True), ("tenant__isnull", False)
                ),
                fields=("tenant", "code"),
                name="catalog_shop_group_code_uniq",
            ),
        ),
    ]
