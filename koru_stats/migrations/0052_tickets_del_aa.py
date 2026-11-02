from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

TIPOS = [("directores", "A Directores"), ("it", "A IT"), ("soporte", "A Soporte")]


def sembrar(apps, schema_editor):
    """Las tres configuraciones, APAGADAS: cada una se enciende al cortar su workflow."""
    C = apps.get_model("koru_stats", "TicketTipoConfig")
    filas = [
        dict(tipo="directores", orden=1, titulo="A Directores", solo_miembros=True,
             descripcion="Consultas, peticiones, quejas o algo de seguridad que deba saber Dirección.",
             categorias=["Consulta", "Petición", "Queja", "Reportar seguridad"], prefijo_canal="dir-"),
        dict(tipo="it", orden=2, titulo="A IT", solo_miembros=False,
             descripcion="Problemas con el Auth, Discord o las herramientas de la corp.",
             categorias=["Ayuda con Discord", "Ayuda con el Auth", "Petición", "Otra cosa"], prefijo_canal="it-"),
        dict(tipo="soporte", orden=3, titulo="A Soporte", solo_miembros=False,
             descripcion="Dudas del juego o de cómo funciona Rekium.",
             categorias=[], prefijo_canal="soporte-"),
    ]
    for f in filas:
        C.objects.get_or_create(tipo=f["tipo"], defaults=f)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("koru_stats", "0051_alter_auditorexclusion_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="TicketTipoConfig",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=TIPOS, max_length=20, unique=True)),
                ("activo", models.BooleanField(default=False, help_text="Apagado: el formulario no acepta tickets de este tipo")),
                ("orden", models.PositiveSmallIntegerField(default=0, help_text="Orden en la pantalla de elegir")),
                ("titulo", models.CharField(max_length=60)),
                ("descripcion", models.CharField(blank=True, default="", help_text="Una línea para que el piloto sepa si es aquí", max_length=250)),
                ("solo_miembros", models.BooleanField(default=False, help_text="Solo quien tiene acceso a Mi Dashboard (miembros y Academy) puede abrirlo")),
                ("categorias", models.JSONField(blank=True, default=list, help_text='Opciones del desplegable «Tipo». Ej: ["Consulta", "Queja"]. Vacío = sin desplegable')),
                ("max_abiertos", models.PositiveSmallIntegerField(default=2, help_text="Tickets abiertos a la vez por persona en este tipo. Frena el spam")),
                ("categoria_id", models.CharField(blank=True, default="", help_text="Categoría de Discord donde nacen los canales", max_length=30)),
                ("prefijo_canal", models.CharField(default="ticket-", max_length=30)),
                ("roles_ver", models.JSONField(blank=True, default=list, help_text='Roles de Discord que ven el canal. Ej: ["954100891844231238"]')),
                ("rol_avisar", models.CharField(blank=True, default="", help_text="Rol al que mencionar al abrir. Vacío = nadie", max_length=30)),
                ("avisar_en", models.CharField(blank=True, default="", help_text="Canal donde avisar de cada ticket nuevo. Opcional", max_length=30)),
                ("invitar_piloto", models.BooleanField(default=True, help_text="Meter al piloto en el canal de su ticket")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Tickets — configuración por tipo",
                     "verbose_name_plural": "Tickets — configuración por tipo",
                     "ordering": ["orden", "tipo"]},
        ),
        migrations.CreateModel(
            name="KoruTicket",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(choices=TIPOS, db_index=True, max_length=20)),
                ("main_character_id", models.BigIntegerField(db_index=True)),
                ("main_character_name", models.CharField(max_length=100)),
                ("discord_uid", models.CharField(blank=True, default="", max_length=30)),
                ("categoria", models.CharField(blank=True, default="", max_length=60)),
                ("asunto", models.CharField(max_length=200)),
                ("descripcion", models.TextField(blank=True, default="")),
                ("estado", models.CharField(choices=[("abierto", "Abierto"), ("en_curso", "En curso"), ("esperando", "Esperando al piloto"), ("resuelto", "Resuelto"), ("cerrado", "Cerrado sin más")], db_index=True, default="abierto", max_length=20)),
                ("claim_en", models.DateTimeField(blank=True, null=True)),
                ("fecha_cierre", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("resolucion", models.TextField(blank=True, default="", help_text="Qué se hizo. Obligatorio al cerrar")),
                ("discord_channel_id", models.CharField(blank=True, default="", max_length=30)),
                ("discord_error", models.CharField(blank=True, default="", max_length=250)),
                ("transcripcion", models.TextField(blank=True, default="")),
                ("transcrita_en", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("claim_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("cerrado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="koru_tickets", to=settings.AUTH_USER_MODEL)),
            ],
            options={"verbose_name": "Tickets — ticket del AA",
                     "verbose_name_plural": "Tickets — tickets del AA",
                     "ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="koruticket",
            index=models.Index(fields=["tipo", "estado"], name="koru_kt_tipo_estado"),
        ),
        migrations.CreateModel(
            name="KoruTicketNote",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("autor_nombre", models.CharField(blank=True, default="", max_length=100)),
                ("texto", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("autor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("ticket", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notas", to="koru_stats.koruticket")),
            ],
            options={"verbose_name": "Tickets — nota", "verbose_name_plural": "Tickets — notas",
                     "ordering": ["created_at"]},
        ),
        migrations.RunPython(sembrar, migrations.RunPython.noop),
    ]
