"""
Las PAPs de la alianza entran en Koru.

El porqué de cada campo está en `koru_stats/paps.py`. Lo imprescindible para
leer esta migración:

  · `PapMonthlyDetalle` guarda el desglose por flota. No es un adorno para una
    ficha bonita: sin él, clasificar una flota obligaría a reimportar todos los
    ficheros, y encima habría que seguir teniéndolos.
  · `estrategicas_declaradas` separa «lo dijo la alianza» de «lo hemos
    calculado». Lo primero no se recalcula nunca.
  · El catálogo nace sembrado con las 16 flotas conocidas, 15 de ellas con la
    categoría que declara la propia web.
"""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

PERMISOS = (
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
    ("tickets_soporte", "Tickets: ve solo Soporte (ayudantes)"),
    ("tickets_admin", "Tickets: ve todos los tipos"),
    ("gift_access", "Regalos: ve lo suyo (Mi aportación)"),
    ("gift_manage", "Regalos: gestiona aportaciones, sorteos y entregas"),
    ("gift_ceo", "Regalos: monta los sorteos especiales del CEO"),
    ("recruit_apply", "Reclutamiento: puede enviar una solicitud"),
    ("recruit_manage", "Reclutamiento: gestiona solicitudes y entrevista"),
    ("paps_access", "PAPs: ve el cumplimiento de la alianza"),
    ("paps_admin", "PAPs: importa ficheros y clasifica flotas"),
)

CATEGORIAS = [
    ("estrategica", "Estratégica — cuenta para el filtro"),
    ("actividad", "Actividad — no obligatoria"),
    ("sin", "Sin clasificar"),
]
REGIMENES = [("paz", "Paz"), ("guerra", "Guerra")]
DIMENSIONES = [("flota", "Flota"), ("nave", "Grupo de nave"), ("rol", "Rol de flota")]


def sembrar_flotas(apps, schema_editor):
    """Las 16 flotas conocidas, con la categoría que declara la alianza.

    Se siembra aquí y no solo en el importador para que la pantalla del
    catálogo tenga algo que enseñar antes de la primera importación.
    """
    from koru_stats.paps import SEMILLA_CORP, SEMILLA_FLOTAS

    FleetType = apps.get_model("koru_stats", "PapFleetType")
    for nombre, categoria in SEMILLA_FLOTAS.items():
        FleetType.objects.get_or_create(
            nombre=nombre,
            defaults={"categoria": categoria,
                      "es_corp": nombre in SEMILLA_CORP,
                      "declarada_por_alianza": True})


def quitar_flotas(apps, schema_editor):
    # La tabla se borra entera al revertir la migración; no hay nada que deshacer.
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0060_sorteo_reparto_completo"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="general",
            options={
                "default_permissions": (),
                "managed": False,
                "permissions": PERMISOS,
            },
        ),
        migrations.CreateModel(
            name="PapFleetType",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("nombre", models.CharField(max_length=80, unique=True)),
                ("categoria", models.CharField(choices=CATEGORIAS, default="sin",
                                               max_length=12)),
                ("es_corp", models.BooleanField(
                    default=False,
                    help_text="Cuenta aparte como asistencia a flotas de la corp.")),
                ("declarada_por_alianza", models.BooleanField(
                    default=False,
                    help_text="La categoría la dio la propia fuente (isStrategic del JSON "
                              "o el sufijo :strategic del CSV). Lo que diga la alianza "
                              "pisa lo puesto a mano.")),
            ],
            options={
                "verbose_name": "PAPs · tipo de flota",
                "verbose_name_plural": "PAPs · tipos de flota",
                "ordering": ["categoria", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="PapPeriod",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("anio", models.PositiveSmallIntegerField()),
                ("mes", models.PositiveSmallIntegerField()),
                ("origen", models.CharField(
                    default="csv", max_length=8,
                    help_text="json = API de la web (completo). csv = exportación "
                              "(se deja gente fuera).")),
                ("regimen", models.CharField(choices=REGIMENES, default="paz", max_length=8)),
                ("requeridas", models.PositiveSmallIntegerField(
                    default=5,
                    help_text="Estratégicas exigidas ese mes. Se pone sola al cambiar el "
                              "régimen, pero se puede tocar si un mes concreto fue distinto.")),
                ("fichero", models.CharField(blank=True, max_length=160)),
                ("fichero_hash", models.CharField(blank=True, db_index=True, max_length=64)),
                ("importado_en", models.DateTimeField(auto_now=True)),
                ("filas", models.PositiveIntegerField(default=0)),
                ("sin_casar", models.PositiveIntegerField(default=0)),
                ("avisos", models.TextField(blank=True)),
                ("importado_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "PAPs · mes",
                "verbose_name_plural": "PAPs · meses",
                "ordering": ["-anio", "-mes"],
                "unique_together": {("anio", "mes")},
            },
        ),
        migrations.CreateModel(
            name="PapAccountAlias",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("account_name", models.CharField(max_length=100, unique=True)),
                ("main_character_id", models.PositiveIntegerField(default=0)),
                ("main_character_name", models.CharField(blank=True, max_length=100)),
                ("nota", models.CharField(blank=True, max_length=200)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("creado_por", models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "PAPs · nombre atado",
                "verbose_name_plural": "PAPs · nombres atados",
                "ordering": ["account_name"],
            },
        ),
        migrations.CreateModel(
            name="PapMonthly",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("account_name", models.CharField(db_index=True, max_length=100)),
                ("main_character_id", models.PositiveIntegerField(db_index=True, default=0)),
                ("main_character_name", models.CharField(blank=True, max_length=100)),
                ("total", models.PositiveIntegerField(default=0)),
                ("estrategicas", models.PositiveIntegerField(default=0)),
                ("estrategicas_declaradas", models.IntegerField(
                    blank=True, null=True,
                    help_text="La cifra que dio la fuente. Si está puesta, manda: "
                              "reclasificar una flota a mano no mejora un dato que viene "
                              "de la alianza.")),
                ("actividades", models.PositiveIntegerField(default=0)),
                ("corp", models.PositiveIntegerField(default=0)),
                ("sin_clasificar", models.PositiveIntegerField(
                    default=0,
                    help_text="PAPs en flotas que nadie ha clasificado todavía.")),
                ("cuadra", models.BooleanField(
                    default=True,
                    help_text="La suma del desglose coincide con el total. Si está en "
                              "falso, el fichero traía algo que no supimos leer.")),
                ("periodo", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="lineas",
                    to="koru_stats.papperiod")),
            ],
            options={
                "verbose_name": "PAPs · línea mensual",
                "verbose_name_plural": "PAPs · líneas mensuales",
                "ordering": ["-estrategicas", "-total"],
                "unique_together": {("periodo", "account_name")},
            },
        ),
        migrations.CreateModel(
            name="PapMonthlyDetalle",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True,
                                        serialize=False, verbose_name="ID")),
                ("dimension", models.CharField(choices=DIMENSIONES, max_length=6)),
                ("nombre", models.CharField(max_length=80)),
                ("paps", models.PositiveIntegerField(default=0)),
                ("fila", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE, related_name="detalles",
                    to="koru_stats.papmonthly")),
            ],
            options={
                "verbose_name": "PAPs · desglose",
                "verbose_name_plural": "PAPs · desglose",
                "ordering": ["dimension", "-paps", "nombre"],
            },
        ),
        migrations.AddIndex(
            model_name="papmonthly",
            index=models.Index(fields=["main_character_id", "periodo"],
                               name="koru_pap_main_periodo"),
        ),
        migrations.AddIndex(
            model_name="papmonthlydetalle",
            index=models.Index(fields=["fila", "dimension"], name="koru_pap_fila_dim"),
        ),
        migrations.RunPython(sembrar_flotas, quitar_flotas),
    ]
