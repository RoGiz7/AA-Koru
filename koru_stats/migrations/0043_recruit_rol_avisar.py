"""
A quién mencionar cuando entra una solicitud.

⚠ Nace vacío: sin mención, nadie se entera de que el canal existe — pero
inventarse un rol aquí sería peor que dejar que lo elija quien sabe cuál es.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0042_recruit_transcripcion")]

    operations = [
        migrations.AddField(
            model_name="recruitconfig",
            name="rol_avisar",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="Rol al que mencionar cuando entra una solicitud. "
                          "Vacío = no mencionar a nadie"),
        ),
    ]
