from django.db import migrations, models


def activar_en_borradores(apps, schema_editor):
    """
    ⚠ Solo en BORRADOR. Un sorteo ya cerrado tiene su semilla publicada con
    unas reglas, y uno sorteado tiene que poder verificarse con el método con
    el que se sorteó: cambiarles la regla rompería las dos cosas.
    """
    Raffle = apps.get_model("koru_stats", "Raffle")
    Raffle.objects.filter(estado="borrador").update(reparto_completo=True)


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0059_recluta_salida_discord"),
    ]

    operations = [
        migrations.AddField(
            model_name="raffle", name="reparto_completo",
            field=models.BooleanField(default=False)),
        migrations.RunPython(activar_en_borradores, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="raffle", name="reparto_completo",
            field=models.BooleanField(
                default=True,
                help_text="Todos los nombres reciben regalo y ningún regalo se queda sin dueño. Hacen falta "
                          "al menos tantos regalos como nombres; si sobran, a algunos les tocan dos. "
                          "Con esto activo no se usan papeletas ni «repetir ganador»")),
    ]
