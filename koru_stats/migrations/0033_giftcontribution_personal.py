from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0032_regalos_r5_entregas"),
    ]

    operations = [
        migrations.AddField(
            model_name="giftcontribution",
            name="personal",
            field=models.BooleanField(
                db_index=True, default=False,
                help_text="Recibido en un personaje, no en la corp: no cuenta hasta validarlo"),
        ),
    ]
