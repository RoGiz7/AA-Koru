from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0057_alts_a_la_corp"),
    ]

    operations = [
        migrations.CreateModel(
            name="KoruVinculo",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("character_id", models.BigIntegerField(db_index=True)),
                ("character_name", models.CharField(db_index=True, max_length=100)),
                ("main_character_id", models.BigIntegerField(db_index=True)),
                ("main_character_name", models.CharField(max_length=100)),
                ("user_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("corp_name", models.CharField(blank=True, default="", max_length=100)),
                ("activo", models.BooleanField(db_index=True, default=True)),
                ("primero_visto", models.DateTimeField(auto_now_add=True)),
                ("ultimo_visto", models.DateTimeField(blank=True, null=True)),
                ("quitado_en", models.DateTimeField(blank=True, null=True)),
                ("motivo", models.CharField(blank=True, default="", max_length=20)),
            ],
            options={"verbose_name": "Rastro — vínculo personaje/main",
                     "verbose_name_plural": "Rastro — vínculos personaje/main"},
        ),
        migrations.AddConstraint(
            model_name="korovinculo" if False else "koruvinculo",
            constraint=models.UniqueConstraint(fields=("character_id", "main_character_id"), name="uniq_koru_vinculo"),
        ),
        migrations.CreateModel(
            name="KoruVinculoEvento",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("character_id", models.BigIntegerField(db_index=True)),
                ("character_name", models.CharField(max_length=100)),
                ("main_character_id", models.BigIntegerField(db_index=True)),
                ("main_character_name", models.CharField(max_length=100)),
                ("user_id", models.IntegerField(blank=True, db_index=True, null=True)),
                ("evento", models.CharField(choices=[("alta", "Alta"), ("baja", "Baja")], max_length=5)),
                ("motivo", models.CharField(blank=True, default="", max_length=20)),
                ("en", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={"verbose_name": "Rastro — evento", "verbose_name_plural": "Rastro — eventos",
                     "ordering": ["-en"]},
        ),
    ]
