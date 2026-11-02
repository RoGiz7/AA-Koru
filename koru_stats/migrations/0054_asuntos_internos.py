from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

TIPOS = [("directores", "A Directores"), ("it", "A IT"), ("soporte", "A Soporte"),
         ("asuntos", "Asuntos Internos")]


def sembrar(apps, schema_editor):
    """Asuntos Internos nace APAGADO, sin piloto en el canal y sin formulario público."""
    C = apps.get_model("koru_stats", "TicketTipoConfig")
    C.objects.get_or_create(tipo="asuntos", defaults=dict(
        orden=4, titulo="Asuntos Internos", activo=False, solo_miembros=False,
        descripcion="Auditorías de pilotos. Las abre el staff, nunca el piloto.",
        categorias=[], max_abiertos=0, prefijo_canal="auditoria-", invitar_piloto=False))


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0053_tickets_soporte_permiso"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tickettipoconfig", name="tipo",
            field=models.CharField(choices=TIPOS, max_length=20, unique=True)),
        migrations.AlterField(
            model_name="koruticket", name="tipo",
            field=models.CharField(choices=TIPOS, db_index=True, max_length=20)),
        migrations.AddField(
            model_name="koruticket", name="abierto_por",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="+", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(
            model_name="koruticket", name="relacionado",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="derivados", to="koru_stats.koruticket")),
        migrations.CreateModel(
            name="TicketCheck",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("clave", models.SlugField(max_length=40, db_index=True)),
                ("etiqueta", models.CharField(blank=True, default="", max_length=200)),
                ("estado", models.CharField(choices=[("pendiente", "Sin mirar"), ("ok", "Correcto"), ("duda", "Duda"),
                                                     ("problema", "Problema"), ("na", "No aplica")],
                                            db_index=True, default="pendiente", max_length=10)),
                ("nota", models.TextField(blank=True, default="")),
                ("valor", models.TextField(blank=True, default="")),
                ("por_nombre", models.CharField(blank=True, default="", max_length=100)),
                ("en", models.DateTimeField(blank=True, null=True)),
                ("por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                                          related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                             related_name="checks", to="koru_stats.koruticket")),
            ],
            options={"verbose_name": "Tickets — punto de auditoría",
                     "verbose_name_plural": "Tickets — puntos de auditoría"},
        ),
        migrations.AddConstraint(
            model_name="ticketcheck",
            constraint=models.UniqueConstraint(fields=("ticket", "clave"), name="uniq_ticket_check")),
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
