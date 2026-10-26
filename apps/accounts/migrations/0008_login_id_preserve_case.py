from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_account_login_eligibility"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="user",
            name="user_login_id_format_valid",
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(login_id__isnull=True)
                | models.Q(login_id__regex=r"^[A-Za-z][A-Za-z0-9_]{2,31}$"),
                name="user_login_id_format_valid",
            ),
        ),
    ]
