"""
Una alerta por situación, no una por mes.

Medido en producción el 24/10/2026: 369 alertas abiertas para 224 situaciones
reales, repartidas en cinco periodos — y **ninguna** cerrada nunca. Un piloto
inactivo desde junio generaba una alerta cada mes, todas idénticas, y si volvía
a conectarse las cinco seguían abiertas para siempre.

Esta migración fusiona las repetidas: se queda la más antigua (que es cuando
empezó el problema), apunta el último periodo en que se vio y cuántas veces
disparó, y borra las demás.

⚠ Si alguna fila tenía estado puesto por una persona (`revisada`/`descartada`),
ese estado MANDA sobre el de la fila más antigua: es una decisión humana y la
migración no es quién para deshacerla.
"""

from django.db import migrations, models


def fusionar(apps, schema_editor):
    AuditorAlert = apps.get_model("koru_stats", "AuditorAlert")

    grupos = {}
    for a in AuditorAlert.objects.all().order_by("period", "id"):
        grupos.setdefault((a.main_character_id, a.codigo), []).append(a)

    a_borrar = []
    for filas in grupos.values():
        base = filas[0]                      # la más antigua: cuándo empezó
        base.visto_en = max(f.period for f in filas)
        base.veces = len(filas)

        # Una decisión humana en cualquiera de las repetidas se conserva.
        humanas = [f for f in filas if f.estado in ("revisada", "descartada")]
        if humanas:
            ultima = humanas[-1]
            base.estado = ultima.estado
            base.revisada_por_id = ultima.revisada_por_id
            base.revisada_at = ultima.revisada_at
            base.nota_revision = ultima.nota_revision

        # La severidad y el detalle más recientes describen mejor el estado de
        # hoy que los de hace cinco meses.
        ultima_fila = filas[-1]
        base.severidad = ultima_fila.severidad
        base.detalle = ultima_fila.detalle

        base.save()
        a_borrar.extend(f.id for f in filas[1:])

    if a_borrar:
        AuditorAlert.objects.filter(id__in=a_borrar).delete()


def deshacer(apps, schema_editor):
    # No se puede devolver una fila por mes: esa información se fusionó. Se
    # deja pasar en vez de fingir que se restaura algo.
    pass


class Migration(migrations.Migration):

    dependencies = [("koru_stats", "0047_auditcheck_recruitcheck")]

    operations = [
        migrations.AddField(
            model_name="auditoralert",
            name="visto_en",
            field=models.CharField(
                blank=True, db_index=True, default="", max_length=7,
                help_text="Último periodo en que la señal seguía disparando"),
        ),
        migrations.AddField(
            model_name="auditoralert",
            name="veces",
            field=models.IntegerField(default=1, help_text="Periodos en que ha disparado"),
        ),
        migrations.AddField(
            model_name="auditoralert",
            name="resuelta_en",
            field=models.CharField(
                blank=True, default="", max_length=7,
                help_text="Periodo en que dejó de dispararse"),
        ),
        # ⚠ La restricción vieja se quita ANTES de fusionar: si no, el borrado
        # y los save() podrían chocar con ella a media faena.
        migrations.RemoveConstraint(
            model_name="auditoralert",
            name="unique_auditor_alert_period_code",
        ),
        migrations.RunPython(fusionar, deshacer),
        migrations.AddConstraint(
            model_name="auditoralert",
            constraint=models.UniqueConstraint(
                fields=["main_character_id", "codigo"],
                name="unique_auditor_alert_code"),
        ),
    ]
