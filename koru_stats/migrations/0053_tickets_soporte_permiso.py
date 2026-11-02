from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0052_tickets_del_aa"),
    ]

    operations = [
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
                    ("tickets_soporte", "Tickets: ve solo Soporte (ayudantes)"),
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
