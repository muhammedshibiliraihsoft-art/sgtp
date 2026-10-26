from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0004_idempotent_response_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="financialdocument",
            name="layout_version",
            field=models.PositiveSmallIntegerField(default=1, editable=False),
        ),
        migrations.RemoveConstraint(
            model_name="financialdocument",
            name="bill_doc_invoice_locale_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="financialdocument",
            name="bill_doc_payment_locale_uniq",
        ),
        migrations.RemoveConstraint(
            model_name="financialdocument",
            name="bill_doc_credit_locale_uniq",
        ),
        migrations.AddConstraint(
            model_name="financialdocument",
            constraint=models.UniqueConstraint(
                condition=Q(kind="INVOICE"),
                fields=("invoice", "locale", "layout_version"),
                name="bill_doc_inv_layout_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="financialdocument",
            constraint=models.UniqueConstraint(
                condition=Q(kind="RECEIPT"),
                fields=("payment", "locale", "layout_version"),
                name="bill_doc_pay_layout_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="financialdocument",
            constraint=models.UniqueConstraint(
                condition=Q(kind="CREDIT_NOTE"),
                fields=("credit_note", "locale", "layout_version"),
                name="bill_doc_cn_layout_uniq",
            ),
        ),
    ]
