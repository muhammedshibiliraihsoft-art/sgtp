from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("tenants", "0009_membership_work_functions")]

    operations = [
        migrations.RemoveConstraint(
            model_name="membershipworkfunction",
            name="valid_membership_work_function_code",
        ),
        migrations.AlterField(
            model_name="membershipworkfunction",
            name="function_code",
            field=models.CharField(
                choices=[
                    ("SALES", "Sales"),
                    ("MEASUREMENT", "Measurement"),
                    ("CUTTING", "Cutting"),
                    ("STITCHING", "Stitching"),
                    ("CHECK", "Check"),
                    ("FINISHING", "Finishing"),
                    ("QC", "Quality control"),
                    ("CASHIER", "Cashier"),
                ],
                max_length=16,
            ),
        ),
        migrations.AddConstraint(
            model_name="membershipworkfunction",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    function_code__in=(
                        "SALES",
                        "MEASUREMENT",
                        "CUTTING",
                        "STITCHING",
                        "CHECK",
                        "FINISHING",
                        "QC",
                        "CASHIER",
                    )
                ),
                name="valid_membership_work_function_code",
            ),
        ),
    ]
