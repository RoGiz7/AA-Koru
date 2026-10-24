"""
La entrevista, con su hora y quién la hizo.

★ No es una aprobación ni un permiso: es el momento en que alguien habló con la
persona. Sirve para medir cuánto se tarda desde que entra una solicitud hasta
que alguien la atiende — el número que de verdad dice si reclutamiento va bien.

⚠ Lo que NO prueba: pulsar esto y el OK seguido solo demuestra que alguien
pulsó dos botones.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0044_recruit_invitacion"),
    ]

    operations = [
        migrations.AddField(
            model_name="recruitapplication",
            name="entrevista_en",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="recruitapplication",
            name="entrevista_por",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name="+", to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="recruitapplication",
            name="entrevista_nota",
            field=models.TextField(
                blank=True, default="",
                help_text="Lo que salió de la entrevista. Se guarda como nota del staff"),
        ),
        migrations.AddField(
            model_name="recruitconfig",
            name="exigir_entrevista",
            field=models.BooleanField(
                default=True,
                help_text="No dejar dar el OK de reclutadores sin haber marcado la entrevista"),
        ),
    ]
