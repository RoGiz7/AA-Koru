"""
Un canal de aviso por paso.

⚠ No es comodidad: avisar en el canal de reclutadores de que Asuntos Internos
tiene algo que revisar les está contando que hay una revisión en curso — justo
lo que protegen las notas reservadas. Cada aviso va donde solo lo ve quien debe.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0045_recruit_entrevista")]

    operations = [
        migrations.AddField(
            model_name="recruitconfig",
            name="canal_asuntos",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="Dónde avisar de que le toca a Asuntos Internos. Vacío = no avisar"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="canal_directores",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="Dónde avisar de que le toca a Dirección. Vacío = no avisar"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="canal_invitacion",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="Dónde avisar de que falta mandar la invitación. Vacío = no avisar"),
        ),
    ]
