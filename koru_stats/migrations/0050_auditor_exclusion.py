from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0049_killrecord_victim_char"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditorExclusion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("main_character_id", models.BigIntegerField(db_index=True)),
                ("tipo", models.CharField(choices=[("alt", "Alt sin registrar"), ("kill", "Kill que no es awox")], max_length=10)),
                ("objetivo_id", models.BigIntegerField(help_text="character_id del destinatario o killmail_id")),
                ("etiqueta", models.CharField(blank=True, default="", help_text="Nombre o nave, para leerlo sin buscar el id", max_length=150)),
                ("motivo", models.CharField(max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                 related_name="auditor_exclusiones", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Auditor — falso positivo marcado",
                "verbose_name_plural": "Auditor — falsos positivos marcados",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="auditorexclusion",
            constraint=models.UniqueConstraint(fields=("main_character_id", "tipo", "objetivo_id"),
                                               name="uniq_auditor_exclusion"),
        ),
    ]
