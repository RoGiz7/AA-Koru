"""
PAPs de mando (FC) y de anclaje de logi.

Vienen de dos endpoints de la web que no estábamos leyendo,
`/corporation/commander/` y `/corporation/logi-anchor/`. Medido sobre los 36
meses: **1.088 PAPs de FC** repartidas en 180 filas, y **4 de logi anchor** en
tres años. O sea que el mando es un dato de verdad y el anclaje casi no se usa
en Rekium — se guarda igual porque es el mismo código, pero no se le dedica
pantalla.

⚠ `fc` NO suma al total: quien saca una flota también participa en ella, así
que esas PAPs ya están contadas dentro de `total`. Es una marca de QUÉ hizo en
ellas, no PAPs de más. Sumarlas al total las contaría dos veces.
"""

from django.db import migrations, models

DIMENSIONES = [
    ("flota", "Flota"),
    ("nave", "Grupo de nave"),
    ("rol", "Rol de flota"),
    ("fc", "Flota sacada"),
    ("logi", "Logi anclada"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0062_paps_permiso_regimen"),
    ]

    operations = [
        migrations.AddField(
            model_name="papmonthly",
            name="fc",
            field=models.PositiveIntegerField(
                default=0,
                help_text="PAPs sacando flota. Va aparte porque no suma al total: "
                          "quien saca una flota también participa en ella."),
        ),
        migrations.AddField(
            model_name="papmonthly",
            name="logi",
            field=models.PositiveIntegerField(
                default=0,
                help_text="PAPs anclando logi. En Rekium casi no se usa: 4 en tres años."),
        ),
        migrations.AlterField(
            model_name="papmonthlydetalle",
            name="dimension",
            field=models.CharField(choices=DIMENSIONES, max_length=6),
        ),
    ]
