"""
Reclutamiento dentro del Auth: la solicitud deja de vivir en Baserow.

⚠ Escrita a mano a propósito, para que la migración viaje en el repo y no haya
que generarla en el servidor y copiarla de vuelta. Después de aplicarla,
`makemigrations --check` debe decir que no hay cambios pendientes: si dice otra
cosa, es que esta migración no refleja el modelo y hay que corregirla.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0036_ticketsconfig_estados"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecruitApplication",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("main_character_id", models.BigIntegerField(db_index=True)),
                ("main_character_name", models.CharField(max_length=100)),
                ("estado", models.CharField(
                    choices=[
                        ("nuevo", "Nuevo"),
                        ("en_curso", "En curso"),
                        ("pasa_corp", "Pasa a Corp"),
                        ("pasa_academia", "Pasa a Academia"),
                        ("rechazado", "Rechazado"),
                        ("se_marcho", "Se marchó"),
                        ("otra_corp", "Fue a otra corp"),
                        ("archivado", "Archivado"),
                    ],
                    db_index=True, default="nuevo", max_length=20)),
                ("respuestas", models.JSONField(
                    blank=True, default=dict,
                    help_text="Lo que contestó el solicitante, tal cual")),
                ("instantanea", models.JSONField(blank=True, default=dict)),
                ("instantanea_en", models.DateTimeField(blank=True, null=True)),
                ("ok_reclutadores_en", models.DateTimeField(blank=True, null=True)),
                ("ok_asuntos_en", models.DateTimeField(blank=True, null=True)),
                ("ok_directores_en", models.DateTimeField(blank=True, null=True)),
                ("claim_en", models.DateTimeField(blank=True, null=True)),
                ("motivo_cierre", models.TextField(
                    blank=True, default="",
                    help_text="Por qué acabó así. Obligatorio al rechazar")),
                ("fecha_cierre", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("discord_channel_id", models.CharField(blank=True, default="", max_length=30)),
                ("discord_error", models.CharField(blank=True, default="", max_length=250)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("cerrada_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("claim_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ok_asuntos_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ok_directores_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ok_reclutadores_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="solicitudes_rekium", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Reclutamiento — solicitud",
                "verbose_name_plural": "Reclutamiento — solicitudes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="RecruitNote",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("autor_nombre", models.CharField(
                    blank=True, default="", max_length=100,
                    help_text="Main de quien escribió, congelado")),
                ("texto", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("autor", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("solicitud", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="notas", to="koru_stats.recruitapplication")),
            ],
            options={
                "verbose_name": "Reclutamiento — nota",
                "verbose_name_plural": "Reclutamiento — notas",
                "ordering": ["created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="recruitapplication",
            index=models.Index(fields=["estado", "-created_at"],
                               name="koru_sol_estado_fecha"),
        ),
        migrations.AlterModelOptions(
            name="general",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": (
                    ("basic_access", "Puede ver Estadísticas y Mi Dashboard"),
                    ("corp_finance_access", "Puede ver Finanzas Corp"),
                    ("moon_tax_access", "Puede ver Tax Lunas"),
                    ("moon_tax_admin", "Puede gestionar tax de lunas"),
                    ("pvp_access", "Puede ver estadísticas PvP detalladas"),
                    ("fc_access", "Puede ver panel FC/Director"),
                    ("auditor_access", "Puede ver el panel Auditor (seguridad)"),
                    ("auditor_admin", "Puede configurar el Auditor y revisar/descartar alertas"),
                    ("auditor_corp_health", "Puede ver el panel de Salud de Corp (Directores/CEO)"),
                    ("tickets_reclutamiento", "Tickets: ve Reclutamiento"),
                    ("tickets_directores", "Tickets: ve A Directores"),
                    ("tickets_asuntos_internos", "Tickets: ve Asuntos Internos"),
                    ("tickets_it", "Tickets: ve IT y Soporte"),
                    ("tickets_admin", "Tickets: ve todos los tipos"),
                    ("gift_access", "Regalos: ve lo suyo (Mi aportación)"),
                    ("gift_manage", "Regalos: gestiona aportaciones, sorteos y entregas"),
                    ("gift_ceo", "Regalos: monta los sorteos especiales del CEO"),
                    ("recruit_apply", "Reclutamiento: puede enviar una solicitud"),
                    ("recruit_manage", "Reclutamiento: gestiona solicitudes y entrevista"),
                ),
            },
        ),
    ]
