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

# Nombres REALES de EVE: el type_id se resuelve contra el SDE del propio Auth
# en vez de llevarlo escrito aqui, asi la demo enseña los renders de verdad y
# de paso ejercita el adivinador con los mismos datos que usa la web.
PREMIOS = [
    ("Orca", 2_500_000_000), ("Gila", 480_000_000), ("Vexor Navy Issue", 320_000_000),
    ("Nanite Repair Paste", 336_000_000), ("PLEX", 2_100_000_000),
    ("Rifter", 45_000_000),
]


def _mains_reales(cuantos):
    """[(character_id, nombre)] de mains de verdad del Auth, para que los
    retratos de la ruleta sean retratos y no el avatar generico."""
    from django.db import connection

    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT DISTINCT ec.character_id, ec.character_name
                FROM authentication_userprofile up
                JOIN eveonline_evecharacter ec ON ec.id = up.main_character_id
                ORDER BY ec.character_name LIMIT %s
            """, [int(cuantos)])
            return [(int(a), b or str(a)) for a, b in c.fetchall()]
    except Exception:
        return []


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
        # ★ Pilotos REALES del Auth si los hay: con ids inventados, EVE devuelve
        # el avatar por defecto y la demo no enseña lo que tiene que enseñar.
        reales = _mains_reales(gente)
        for i in range(gente):
            if i < len(reales):
                char_id, nombre = reales[i]
            else:
                base = PILOTOS[i % len(PILOTOS)]
                nombre = base if i < len(PILOTOS) else f"{base} {i // len(PILOTOS) + 1}"
                char_id = 900000000 + i
            RaffleEntrant.objects.create(
                raffle=r, main_char_id=char_id, main_name=nombre,
                papeletas=1, rango_nombre="Pruebas")

        from koru_stats.lotes import tipo_desde_texto
        for i in range(max(1, opciones["premios"])):
            etiqueta, valor = PREMIOS[i % len(PREMIOS)]
            tid, _ = tipo_desde_texto(etiqueta)      # contra el SDE de verdad
            RafflePrize.objects.create(
                raffle=r, origen=RafflePrize.ORIGEN_EXCLUSIVO,
                descripcion=f"{etiqueta} (prueba)", valor=Decimal(valor),
                type_id=tid, orden=i)

        if opciones["sortear"]:
            raffles.cerrar(r)
            raffles.sortear(r)

        self.stdout.write(self.style.SUCCESS(
            f"Sorteo «{NOMBRE_SORTEO}» listo en «{campaign.nombre}»: "
            f"{gente} participantes, {r.prizes.count()} premios, estado {r.estado}."))
        con_render = r.prizes.exclude(type_id=None).count()
        self.stdout.write(f"  Premios con imagen: {con_render} de {r.prizes.count()}")
        self.stdout.write(f"  Pilotos reales en el roster: {len(_mains_reales(gente))}")
        self.stdout.write(f"  Ruleta: /koru/regalos/sorteos/{r.pk}/ruleta/")
        self.stdout.write("  Para quitarlo: python manage.py koru_regalos_demo --borrar")
