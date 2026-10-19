"""
Monta (o borra) un sorteo de PRUEBAS con datos inventados.

Para ensayar la ruleta y las pantallas sin tocar la fiesta de verdad. Todo lo
que crea lleva el prefijo del sorteo, asi que `--borrar` se lo lleva entero y
no deja nada detras.

    python manage.py koru_regalos_demo            # crea
    python manage.py koru_regalos_demo --gente 30 # con mas gente (prueba la tira)
    python manage.py koru_regalos_demo --borrar   # lo quita
"""

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

NOMBRE_SORTEO = "PRUEBAS — borrar"

PILOTOS = [
    "Jimy", "Mosten", "Satanax Lefour", "PlanOut", "Equinox Prox", "Arraque Gull",
    "mario Tawate", "Party Co", "Trust Prox", "The MinerOne", "FackDown", "INC001",
    "Distel", "Airiana Weims", "G4R3", "Esportive", "Sadiko Gull", "PlaneB",
    "Amere Ekanon", "Iam Neutral", "Oniashi Lefour", "Ekanon A Devil",
]

PREMIOS = [
    ("Orca", 2_500_000_000), ("Gila", 480_000_000), ("Vexor Navy Issue", 320_000_000),
    ("Lote: Nanite Paste ×1.200 + 300 M ISK", 336_000_000), ("PLEX ×500", 2_100_000_000),
    ("Rifter con fit completo", 45_000_000),
]


class Command(BaseCommand):
    help = "Crea o borra un sorteo de pruebas con datos inventados"

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Lo quita todo")
        parser.add_argument("--gente", type=int, default=8,
                            help="Cuantos participantes (más de 24 fuerza la tira en vez de la rueda)")
        parser.add_argument("--premios", type=int, default=4)
        parser.add_argument("--sortear", action="store_true",
                            help="Lo deja ya cerrado y sorteado, listo para proyectar")

    @transaction.atomic
    def handle(self, *args, **opciones):
        from koru_stats import raffles
        from koru_stats.models import (GiftCampaign, Raffle, RaffleEntrant,
                                       RafflePrize)

        campaign = (GiftCampaign.objects.filter(estado=GiftCampaign.ESTADO_ABIERTA)
                    .order_by("-ventana_desde").first()
                    or GiftCampaign.objects.order_by("-ventana_desde").first())
        if not campaign:
            self.stderr.write("No hay ninguna campaña. Créala primero en el admin.")
            return

        viejos = Raffle.objects.filter(campaign=campaign, nombre=NOMBRE_SORTEO)
        if opciones["borrar"]:
            n = viejos.count()
            viejos.delete()          # en cascada se lleva roster, bolsa y resultados
            self.stdout.write(self.style.SUCCESS(f"Borrados {n} sorteos de pruebas."))
            return

        viejos.delete()              # repetible: siempre arranca limpio

        r = Raffle.objects.create(
            campaign=campaign, nombre=NOMBRE_SORTEO, tipo=Raffle.TIPO_COMUNITARIO,
            orden=99, ponderar_por_rango=False, excluir_propio_regalo=False)

        gente = max(2, opciones["gente"])
        for i in range(gente):
            base = PILOTOS[i % len(PILOTOS)]
            nombre = base if i < len(PILOTOS) else f"{base} {i // len(PILOTOS) + 1}"
            RaffleEntrant.objects.create(
                raffle=r, main_char_id=900000000 + i, main_name=nombre,
                papeletas=1, rango_nombre="Pruebas")

        for i in range(max(1, opciones["premios"])):
            etiqueta, valor = PREMIOS[i % len(PREMIOS)]
            RafflePrize.objects.create(
                raffle=r, origen=RafflePrize.ORIGEN_EXCLUSIVO,
                descripcion=f"{etiqueta} (prueba)", valor=Decimal(valor), orden=i)

        if opciones["sortear"]:
            raffles.cerrar(r)
            raffles.sortear(r)

        self.stdout.write(self.style.SUCCESS(
            f"Sorteo «{NOMBRE_SORTEO}» listo en «{campaign.nombre}»: "
            f"{gente} participantes, {r.prizes.count()} premios, estado {r.estado}."))
        self.stdout.write(f"  Ruleta: /koru/regalos/sorteos/{r.pk}/ruleta/")
        self.stdout.write("  Para quitarlo: python manage.py koru_regalos_demo --borrar")
