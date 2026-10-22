from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0033_giftcontribution_personal"),
    ]

    operations = [
        migrations.AddField(
            model_name="ticket",
            name="claim_main_id",
            field=models.IntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name="ticket",
            name="fecha_cierre",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]
