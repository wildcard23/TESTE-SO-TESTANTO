from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="payment_method",
            field=models.CharField(
                choices=[("pix", "Pix"), ("card", "Cartão"), ("wallet", "Carteira")],
                default="pix",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="payment_status",
            field=models.CharField(
                choices=[("pending", "Pendente"), ("paid", "Pago"), ("cancelled", "Cancelado")],
                default="pending",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="pix_code",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
