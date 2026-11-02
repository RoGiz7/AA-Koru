from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

TIPOS = [("directores", "A Directores"), ("it", "A IT"), ("soporte", "A Soporte"),
         ("asuntos", "Asuntos Internos"), ("alts", "Alts a la corp")]


def sembrar(apps, schema_editor):
    """
    «Alts» nace APAGADO y con el Discord de Directores copiado: lo atienden
    ellos y en n8n vivía en su misma categoría.
    """
    C = apps.get_model("koru_stats", "TicketTipoConfig")
    d = C.objects.filter(tipo="directores").first()
    C.objects.get_or_create(tipo="alts", defaults=dict(
        orden=5, titulo="Añadir alts a la corp", activo=False, solo_miembros=True,
        descripcion="Pide a Dirección que metan a tus alts en la corp.",
        categorias=[], max_abiertos=1, prefijo_canal="alt-", invitar_piloto=True,
        categoria_id=d.categoria_id if d else "", roles_ver=list(d.roles_ver or []) if d else [],
        rol_avisar=d.rol_avisar if d else ""))


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0056_ticket_adjuntos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tickettipoconfig", name="tipo",
            field=models.CharField(choices=TIPOS, max_length=20, unique=True)),
        migrations.AlterField(
            model_name="koruticket", name="tipo",
            field=models.CharField(choices=TIPOS, db_index=True, max_length=20)),
        migrations.CreateModel(
            name="TicketAlt",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("character_id", models.BigIntegerField()),
                ("nombre", models.CharField(max_length=100)),
                ("corp_al_pedir", models.CharField(blank=True, default="", max_length=100)),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"),
                                                     ("aprobado", "Aprobado — falta que entre"),
                                                     ("rechazado", "Rechazado"), ("dentro", "Ya en la corp")],
                                            db_index=True, default="pendiente", max_length=12)),
                ("motivo", models.TextField(blank=True, default="")),
                ("por_nombre", models.CharField(blank=True, default="", max_length=100)),
                ("en", models.DateTimeField(blank=True, null=True)),
                ("dentro_en", models.DateTimeField(blank=True, null=True)),
                ("por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                          related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="alts", to="koru_stats.koruticket")),
            ],
            options={"verbose_name": "Tickets — alt pedido", "verbose_name_plural": "Tickets — alts pedidos",
                     "ordering": ["nombre"]},
        ),
        migrations.AddConstraint(
            model_name="ticketalt",
            constraint=models.UniqueConstraint(fields=("ticket", "character_id"), name="uniq_ticket_alt"),
        ),
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
