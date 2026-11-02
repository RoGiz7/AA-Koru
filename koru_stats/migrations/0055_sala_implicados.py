from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0054_asuntos_internos"),
    ]

    operations = [
        migrations.AddField(
            model_name="koruticket", name="sala_channel_id",
            field=models.CharField(blank=True, default="", max_length=30)),
        migrations.AddField(
            model_name="koruticket", name="sala_transcripcion",
            field=models.TextField(blank=True, default="")),
        migrations.CreateModel(
            name="KoruTicketInvitado",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("main_character_id", models.BigIntegerField(blank=True, null=True)),
                ("nombre", models.CharField(blank=True, default="", max_length=100)),
                ("discord_uid", models.CharField(max_length=30)),
                ("invitado_por_nombre", models.CharField(blank=True, default="", max_length=100)),
                ("invitado_en", models.DateTimeField(auto_now_add=True)),
                ("retirado_en", models.DateTimeField(blank=True, null=True)),
                ("retirado_por_nombre", models.CharField(blank=True, default="", max_length=100)),
                ("invitado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                                   related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="invitados", to="koru_stats.koruticket")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                           related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Tickets — piloto invitado",
                     "verbose_name_plural": "Tickets — pilotos invitados",
                     "ordering": ["invitado_en"]},
        ),
    ]
