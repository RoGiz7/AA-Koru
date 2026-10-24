"""
El paso de la invitación in-game, los avisos por paso y la detección de entrada.

⚠ La invitación NO es una aprobación: no dice «me parece bien», dice «ya está
hecho». Por eso va en sus propios campos y no entre los OK — si se mezclaran,
el expediente no distinguiría quién decidió de quién ejecutó.
"""

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("koru_stats", "0043_recruit_rol_avisar"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitapplication",
            name="invitacion_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recruitapplication",
            name="invitacion_por",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="+", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="rol_asuntos",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="A quién avisar cuando reclutadores dan su OK"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="rol_directores",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="A quién avisar cuando Asuntos Internos da su OK"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="rol_invitacion",
            field=models.CharField(
                blank=True, default="", max_length=30,
                help_text="A quién avisar cuando Dirección da su OK (los que mandan la invitación)"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="corp_academia_id",
            field=models.CharField(
                blank=True, default="", max_length=20,
                help_text="Id de la corp Academia. Si el piloto entra ahí, la solicitud "
                          "se cierra como «Pasa a Academia» en vez de «Pasa a Corp»"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="cerrar_al_entrar",
            field=models.BooleanField(
                default=True,
                help_text="Cerrar la solicitud sola cuando el piloto entre en una corp rastreada"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="grupos_invitacion",
            field=models.ManyToManyField(
                blank=True, related_name="+", to="auth.group",
                verbose_name="Paso 4 · Marcar la invitación enviada",
                help_text="Grupos que mandan la invitación in-game y la marcan"),
        ),
    ]
