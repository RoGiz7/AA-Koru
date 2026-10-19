# type_id del premio, para enseñar su render de EVE en la ruleta.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0030_premio_isk_del_fondo'),
    ]

    operations = [
        migrations.AddField(
            model_name='raffleprize',
            name='type_id',
            field=models.BigIntegerField(blank=True, help_text='type_id de EVE para la imagen del premio. Vacio = se enseña un icono generico', null=True),
        ),
    ]
