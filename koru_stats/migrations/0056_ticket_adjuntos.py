from django.db import migrations, models
import django.db.models.deletion
import koru_stats.models


class Migration(migrations.Migration):

    dependencies = [
        ("koru_stats", "0055_sala_implicados"),
    ]

    operations = [
        migrations.CreateModel(
            name="KoruTicketAdjunto",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("origen", models.CharField(choices=[("canal", "Canal del ticket"), ("sala", "Sala con implicados")],
                                            default="canal", max_length=10)),
                ("orden", models.PositiveIntegerField(default=0)),
                ("nombre", models.CharField(blank=True, default="", max_length=200)),
                ("autor", models.CharField(blank=True, default="", max_length=100)),
                ("fichero", models.FileField(blank=True, max_length=300,
                                             storage=koru_stats.models._almacen_adjuntos, upload_to="")),
                ("tam", models.PositiveIntegerField(default=0)),
                ("error", models.CharField(blank=True, default="", max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="adjuntos", to="koru_stats.koruticket")),
            ],
            options={"verbose_name": "Tickets — adjunto", "verbose_name_plural": "Tickets — adjuntos",
                     "ordering": ["origen", "orden"]},
        ),
    ]
