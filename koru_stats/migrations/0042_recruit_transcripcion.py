"""
La conversación del canal, guardada en la solicitud antes de borrarlo.

⚠ Sin esto, cerrar una solicitud y borrar su canal pierde la entrevista — que
es justo lo que el expediente existe para conservar.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0041_recruit_nota_visibilidad")]

    operations = [
        migrations.AddField(
            model_name="recruitapplication",
            name="transcripcion",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="recruitapplication",
            name="transcrita_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
