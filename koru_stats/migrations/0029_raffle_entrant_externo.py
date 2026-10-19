# Participantes de FUERA: metidos a dedo y contrastados contra ESI.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0028_regalos_r3_sorteos'),
    ]

    operations = [
        migrations.AddField(
            model_name='raffleentrant',
            name='externo',
            field=models.BooleanField(db_index=True, default=False, help_text='No existe en Alliance Auth: resuelto contra ESI'),
        ),
        migrations.AddField(
            model_name='raffleentrant',
            name='verificado_esi',
            field=models.DateTimeField(blank=True, help_text='Cuando se contrasto el nombre con ESI', null=True),
        ),
    ]
