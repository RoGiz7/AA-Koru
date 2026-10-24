"""
La checklist de Asuntos Internos dentro de la solicitud.

Los siete puntos de partida son los de la tabla 1702 de Baserow (Auth,
Personajes, Zkill, Skill Points, Omega, ISK, Assets). Se añaden dos que no
estaban y que el dato ya permitía: contactos y actividad de la cuenta.

⚠ Esos dos nacen NO obligatorios. Bloquear el OK con puntos que Asuntos
Internos nunca ha mirado sería meterles trabajo nuevo por la puerta de atrás.
Que los usen; si les sirven, los marcan obligatorios ellos desde el admin.
"""

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


PARTIDA = [
    # orden, clave, etiqueta, fuente, enlace, obligatorio
    (10, "auth", "Registrado en Auth y con los tokens al día", "auth", "", True),
    (20, "personajes", "Ha declarado todos sus personajes y sabemos dónde está cada uno",
     "personajes", "", True),
    (30, "sp", "Skill points coherentes con lo que cuenta", "sp", "", True),
    (40, "omega", "Omega", "", "", True),
    (50, "isk", "Saldo de cartera", "isk", "", True),
    (60, "assets", "Assets", "assets", "", True),
    (70, "zkill", "Historial de combate", "",
     "https://zkillboard.com/character/{id}/", True),
    (80, "contactos", "Contactos con pilotos o corps hostiles", "contactos", "", False),
    (90, "actividad", "Actividad de la cuenta: último login y total de entradas",
     "actividad", "", False),
]


def sembrar(apps, schema_editor):
    AuditCheck = apps.get_model("koru_stats", "AuditCheck")
    for orden, clave, etiqueta, fuente, enlace, oblig in PARTIDA:
        # get_or_create y no create: si alguien ya creó el punto a mano, su
        # versión manda. La migración siembra, no pisa.
        AuditCheck.objects.get_or_create(
            clave=clave,
            defaults={"etiqueta": etiqueta, "fuente": fuente, "enlace": enlace,
                      "obligatorio": oblig, "orden": orden, "activo": True},
        )


def quitar(apps, schema_editor):
    AuditCheck = apps.get_model("koru_stats", "AuditCheck")
    AuditCheck.objects.filter(clave__in=[c[1] for c in PARTIDA]).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0046_recruit_canales_paso"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditCheck",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("clave", models.SlugField(
                    max_length=40, unique=True,
                    help_text="Identificador interno. No lo cambies si ya hay auditorías hechas")),
                ("etiqueta", models.CharField(max_length=200, help_text="Lo que lee el auditor")),
                ("ayuda", models.CharField(
                    blank=True, default="", max_length=250,
                    help_text="Qué hay que mirar exactamente. Opcional")),
                ("fuente", models.CharField(
                    blank=True, default="", max_length=20,
                    help_text="Si el sistema puede responderlo, sale ya resuelto",
                    choices=[("", "Lo mira una persona"),
                             ("auth", "Automático — registro en Auth y tokens"),
                             ("personajes", "Automático — sus personajes y en qué corp está cada uno"),
                             ("sp", "Automático — skill points"),
                             ("isk", "Automático — saldo de cartera"),
                             ("assets", "Automático — número de assets"),
                             ("contactos", "Automático — contactos del personaje"),
                             ("actividad", "Automático — último login y total de logins")])),
                ("enlace", models.CharField(
                    blank=True, default="", max_length=300,
                    help_text="Enlace externo, con {nombre} o {id}. Ej: https://zkillboard.com/character/{id}/")),
                ("obligatorio", models.BooleanField(
                    default=True,
                    help_text="Si está marcado, no se puede dar el OK dejándolo pendiente")),
                ("orden", models.IntegerField(default=0, help_text="De menor a mayor")),
                ("activo", models.BooleanField(
                    default=True,
                    help_text="Desactívalo en vez de borrarlo: las auditorías antiguas lo siguen necesitando")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Reclutamiento — punto de auditoría",
                "verbose_name_plural": "Reclutamiento — puntos de auditoría",
                "ordering": ["orden", "id"],
            },
        ),
        migrations.CreateModel(
            name="RecruitCheck",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("clave", models.SlugField(db_index=True, max_length=40)),
                ("etiqueta", models.CharField(blank=True, default="", max_length=200)),
                ("estado", models.CharField(
                    db_index=True, default="pendiente", max_length=10,
                    choices=[("pendiente", "Sin mirar"), ("ok", "Correcto"),
                             ("duda", "Duda"), ("problema", "Problema"),
                             ("na", "No aplica")])),
                ("nota", models.TextField(
                    blank=True, default="",
                    help_text="Por qué. Se lee como las notas reservadas")),
                ("valor", models.TextField(blank=True, default="")),
                ("por_nombre", models.CharField(
                    blank=True, default="", max_length=100,
                    help_text="Main de quien lo marcó, congelado")),
                ("en", models.DateTimeField(blank=True, null=True)),
                ("por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
                ("solicitud", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="checks", to="koru_stats.recruitapplication")),
            ],
            options={
                "verbose_name": "Reclutamiento — check de una solicitud",
                "verbose_name_plural": "Reclutamiento — checks de solicitudes",
                "ordering": ["id"],
                "unique_together": {("solicitud", "clave")},
            },
        ),
        migrations.RunPython(sembrar, quitar),
    ]
