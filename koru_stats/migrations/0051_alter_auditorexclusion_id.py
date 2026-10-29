# El id de AuditorExclusion se creo como BigAutoField en la 0050, pero el
# plugin usa AutoField en todas sus tablas: Django avisaba en cada migrate de
# «models have changes not reflected in a migration». Esto lo iguala.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('koru_stats', '0050_auditor_exclusion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditorexclusion',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
