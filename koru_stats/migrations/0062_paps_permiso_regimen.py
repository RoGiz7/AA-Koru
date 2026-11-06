"""
Permiso propio para marcar los meses de paz o guerra, y el sello de `*LAWN`.

★ POR QUÉ UN TERCER PERMISO. Marcar un mes como de guerra es un juicio sobre la
historia de la alianza: lo sabe Dirección, no quien importa los ficheros. Con un
solo `paps_admin`, dárselo a un director para que corrija un mes le daba también
la importación y la reclasificación de flotas — justo lo que no se quería.
`paps_admin` sigue incluyendo el régimen por arrastre.

⚠ Y se corrige una mentira pequeña de la pantalla: `*LAWN` salía con el sello
«la alianza» en la columna de origen, y la alianza nunca la clasificó. Está a
cero en los 34 ficheros y la API no la lista como tag en ningún mes, así que
ponerla como actividad fue decisión nuestra. No cambia un solo número; cambia
que esa columna diga la verdad, que es para lo único que existe.
"""

from django.db import migrations

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
    ("paps_regimen", "PAPs: marca los meses de paz o guerra"),
)


def destapar_lawn(apps, schema_editor):
    """`*LAWN` deja de figurar como declarada por la alianza.

    Solo se toca si sigue como la dejó la semilla (actividad). Si alguien la ha
    reclasificado a mano o un fichero futuro la declara, mandan ellos.
    """
    FleetType = apps.get_model("koru_stats", "PapFleetType")
    FleetType.objects.filter(nombre="*LAWN", categoria="actividad").update(
        declarada_por_alianza=False)


def volver_a_tapar(apps, schema_editor):
    FleetType = apps.get_model("koru_stats", "PapFleetType")
    FleetType.objects.filter(nombre="*LAWN").update(declarada_por_alianza=True)


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0061_paps"),
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
        migrations.RunPython(destapar_lawn, volver_a_tapar),
    ]
