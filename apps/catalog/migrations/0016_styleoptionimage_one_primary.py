from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0015_styleoptionimage_primary"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="styleoptionimage",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_primary", True)),
                fields=("style_option",),
                name="catalog_style_option_one_primary_image",
            ),
        ),
    ]
