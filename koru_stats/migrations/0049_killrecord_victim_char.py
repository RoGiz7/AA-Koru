from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0048_alerta_una_por_situacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="characterkillrecord",
            name="victim_char_id",
            field=models.BigIntegerField(blank=True, db_index=True, null=True),
        ),
    ]
