"""
Publica en un canal de Discord el panel con los botones de tickets.

    python manage.py koru_panel_tickets <canal_id>
    python manage.py koru_panel_tickets <canal_id> --reclutamiento
    python manage.py koru_panel_tickets <canal_id> --solo-ver      # enseña el mensaje sin publicarlo

Los botones son ENLACES al Auth: no los atiende el bot, así que no hay nada que
registrar ni que se pierda al reiniciar. Salen solo los tipos ACTIVOS en el
admin; al encender uno nuevo, se vuelve a publicar y se borra el panel viejo.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse


class Command(BaseCommand):
    help = "Publica el panel de botones de tickets en un canal de Discord"

    def add_arguments(self, parser):
        parser.add_argument("canal_id")
        parser.add_argument("--reclutamiento", action="store_true",
                            help="Añade el botón «Únete a Rekium»")
        parser.add_argument("--solo-ver", action="store_true")

    def handle(self, *args, **o):
        from koru_stats.models import TicketTipoConfig
        from koru_stats import discordapi

        base = str(getattr(settings, "SITE_URL", "") or "").rstrip("/")
        if not base.startswith("http"):
            raise CommandError("SITE_URL no está configurado en el Auth")

        botones = []
        if o["reclutamiento"]:
            botones.append(("Únete a Rekium", base + reverse("koru_stats:recruit_wizard")))
        for cfg in TicketTipoConfig.objects.filter(activo=True):
            botones.append((f"Ticket {cfg.titulo}", base + reverse("koru_stats:koruticket_nuevo_tipo", args=[cfg.tipo])))
        botones.append(("Mis tickets", base + reverse("koru_stats:koruticket_mios")))

        texto = ("🎫 **¿Necesitas algo?**\n"
                 "Pulsa el botón que toque: se abre el Auth, rellenas dos líneas y te creamos "
                 "un canal privado con quien lo va a atender.")

        for etiqueta, url in botones:
            self.stdout.write(f"  [{etiqueta}] → {url}")
        if o["solo_ver"]:
            self.stdout.write(self.style.WARNING("--solo-ver: no se ha publicado nada"))
            return
        mid = discordapi.publicar_botones(o["canal_id"], texto, botones)
        self.stdout.write(self.style.SUCCESS(f"Panel publicado (mensaje {mid})"))
