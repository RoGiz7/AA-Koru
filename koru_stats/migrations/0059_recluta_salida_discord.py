from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0058_rastro_personajes"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitapplication", name="salio_discord_en",
            field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(
            model_name="recruitapplication", name="estado_antes_de_salir",
            field=models.CharField(blank=True, default="", max_length=20)),
    ]
