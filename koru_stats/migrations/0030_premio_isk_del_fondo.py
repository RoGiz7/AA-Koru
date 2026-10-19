# El fondo de la fiesta: cuanto de cada premio salio del ISK aportado.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0029_raffle_entrant_externo'),
    ]

    operations = [
        migrations.AddField(
            model_name='raffleprize',
            name='isk_del_fondo',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Cuanto de este premio salio del fondo (ISK aportado). 0 = lo puso alguien de su bolsillo', max_digits=22),
        ),
    ]
