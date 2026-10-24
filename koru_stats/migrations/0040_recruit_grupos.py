"""
Quién aprueba cada paso de la cadena, configurable por grupos de AA.

⚠ Nacen VACÍAS a propósito, y vacío no significa «todos»: significa sin
configurar, y entonces solo un superusuario puede dar ese paso. Sembrarlas con
una suposición sería peor — un paso que puede dar cualquiera es la clase de
descuido que no se nota hasta que alguien aprueba algo que no le tocaba.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("koru_stats", "0039_recruit_config"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitconfig",
            name="grupos_reclutadores",
            field=models.ManyToManyField(
                blank=True, related_name="+", to="auth.group",
                verbose_name="Paso 1 · Reclutadores",
                help_text="Grupos que pueden dar el OK de reclutadores"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="grupos_asuntos",
            field=models.ManyToManyField(
                blank=True, related_name="+", to="auth.group",
                verbose_name="Paso 2 · Asuntos Internos",
                help_text="Grupos que pueden dar el OK de Asuntos Internos"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="grupos_directores",
            field=models.ManyToManyField(
                blank=True, related_name="+", to="auth.group",
                verbose_name="Paso 3 · Directores",
                help_text="Grupos que pueden dar el OK de Dirección"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="grupos_rechazo",
            field=models.ManyToManyField(
                blank=True, related_name="+", to="auth.group",
                verbose_name="Rechazar o cerrar",
                help_text="Grupos que pueden rechazar una solicitud o cerrarla"),
        ),
    ]
