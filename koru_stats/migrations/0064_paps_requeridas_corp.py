"""
Un segundo listón: las PAPs de corp exigidas cada mes.

★ POR QUÉ. La alianza pide estratégicas, y las flotas de corp no lo son. Con
una sola medida, la pantalla de reincidencia señalaba a 22 pilotos de los
cuales 15 tenían MÁS DEL 50% de sus PAPs en flotas de corp — en conjunto, 510
de sus 693 PAPs, el 74%. O sea que la lista parecía de gente que no arrima el
hombro y era justo al revés para dos de cada tres: arrimaban mucho, pero donde
la alianza no lo cuenta.

Midiendo las dos cosas, una fila puede decir «no llega a la alianza pero
cumple de sobra con la corp», que es un dato y no una impresión.

⚠ El régimen de paz/guerra NO toca este número. La paz y la guerra las declara
la alianza; lo que Rekium pide a los suyos lo decide Rekium. Se cambia a mano.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0063_paps_fc_logi"),
    ]

    operations = [
        migrations.AddField(
            model_name="papperiod",
            name="requeridas_corp",
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text="PAPs de flotas de CORP exigidas ese mes. No la toca el régimen: "
                          "la paz y la guerra las declara la alianza, y lo que Rekium pide a "
                          "los suyos es decisión de Rekium. Se cambia a mano cuando un mes lo pida."),
        ),
        migrations.AlterField(
            model_name="papperiod",
            name="requeridas",
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text="Estratégicas de ALIANZA exigidas ese mes. Se pone sola al cambiar "
                          "el régimen, pero se puede tocar si un mes concreto fue distinto."),
        ),
    ]
