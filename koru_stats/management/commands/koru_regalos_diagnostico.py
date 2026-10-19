"""
Modo DIAGNOSTICO de la deteccion de aportaciones. No escribe NADA.

Lee los contratos y el diario de cartera de verdad y enseña que detectaria,
como lo valoraria y que marcaria. Sirve para dos cosas:

  1. Estrenar la rama de CONTRATOS sin esperar a que llegue un regalo real.
  2. Ver, antes de que empiece la fiesta, que tipos de movimiento hay de verdad
     en la cartera y en los contratos — que es la unica forma de saber si los
     filtros estan bien puestos.

    python manage.py koru_regalos_diagnostico                 # la campaña abierta
    python manage.py koru_regalos_diagnostico --dias 365      # mirar mas atras
    python manage.py koru_regalos_diagnostico --todo          # TODOS los ref_type y tipos
    python manage.py koru_regalos_diagnostico --valorar       # ademas pide precios a Jita
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone


class Command(BaseCommand):
    help = "Enseña qué detectaría la ingesta de regalos, sin escribir nada"

    def add_arguments(self, parser):
        parser.add_argument("--dias", type=int, default=90)
        parser.add_argument("--todo", action="store_true",
                            help="No filtra por ref_type ni por tipo de contrato: enseña el reparto completo")
        parser.add_argument("--valorar", action="store_true",
                            help="Pide precios a Jita de lo que aparezca (sale a internet)")
        parser.add_argument("--limite", type=int, default=15)

    def handle(self, *args, **o):
        from koru_stats.models import GiftCampaign, GiftRecipient

        campaign = (GiftCampaign.objects.filter(estado=GiftCampaign.ESTADO_ABIERTA)
                    .order_by("-ventana_desde").first())
        destinos = list(GiftRecipient.objects.filter(is_active=True)
                        .values_list("entity_id", flat=True))
        desde = timezone.now() - timedelta(days=o["dias"])

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"\n=== DIAGNÓSTICO · últimos {o['dias']} días · NO se escribe nada ==="))
        self.stdout.write(f"campaña: {campaign.nombre if campaign else '(ninguna abierta)'}")
        self.stdout.write(f"destinatarios configurados: {destinos or '(ninguno)'}\n")

        self._cartera(desde, destinos, o)
        self._contratos(desde, destinos, o)

    # ------------------------------------------------------------------ cartera
    def _cartera(self, desde, destinos, o):
        self.stdout.write(self.style.MIGRATE_HEADING("--- Diario de cartera de corp ---"))
        with connection.cursor() as c:
            c.execute("""
                SELECT j.ref_type, COUNT(*), SUM(j.amount)
                FROM corptools_corporationwalletjournalentry j
                WHERE j.date >= %s AND j.amount > 0
                GROUP BY j.ref_type ORDER BY COUNT(*) DESC LIMIT 25
            """, [desde])
            filas = c.fetchall()
        if not filas:
            self.stdout.write("  (sin movimientos de entrada en la ventana)")
        for ref, n, total in filas:
            marca = "  <-- esto es lo que cuenta como regalo" if ref == "player_donation" else ""
            self.stdout.write(f"  {ref:34} {n:>6} mov  {float(total or 0):>22,.0f} ISK{marca}")

        if not destinos:
            self.stdout.write(self.style.WARNING(
                "\n  Sin destinatarios configurados no se detectaria ninguna donacion."))
            return

        ph = ",".join(["%s"] * len(destinos))
        with connection.cursor() as c:
            c.execute(f"""
                SELECT en.name, j.amount, j.date, j.reason, d.division
                FROM corptools_corporationwalletjournalentry j
                JOIN corptools_corporationwalletdivision d ON d.id = j.division_id
                JOIN corptools_corporationaudit          ca ON ca.id = d.corporation_id
                JOIN eveonline_evecorporationinfo       eci ON eci.id = ca.corporation_id
                LEFT JOIN corptools_evename en ON en.eve_id = j.first_party_id
                WHERE j.ref_type = 'player_donation' AND j.amount > 0
                  AND j.date >= %s AND eci.corporation_id IN ({ph})
                ORDER BY j.date DESC LIMIT %s
            """, [desde] + destinos + [o["limite"]])
            donaciones = c.fetchall()
        self.stdout.write(f"\n  Donaciones a los destinatarios: {len(donaciones)} (máx {o['limite']})")
        for nombre, importe, fecha, motivo, div in donaciones:
            self.stdout.write(
                f"    {str(fecha)[:16]}  {(nombre or '?')[:22]:22} "
                f"{float(importe):>18,.0f} ISK  div {div}  «{(motivo or '')[:30]}»")

    # ---------------------------------------------------------------- contratos
    def _contratos(self, desde, destinos, o):
        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Contratos ---"))
        with connection.cursor() as c:
            c.execute("""
                SELECT c.contract_type, c.status, COUNT(DISTINCT c.contract_id)
                FROM corptools_corporatecontract c
                WHERE c.date_issued >= %s
                GROUP BY c.contract_type, c.status ORDER BY 3 DESC LIMIT 20
            """, [desde])
            for tipo, estado, n in c.fetchall():
                self.stdout.write(f"  {tipo or '?':16} {estado or '?':14} {n:>7}")

        if not destinos:
            return
        ph = ",".join(["%s"] * len(destinos))

        # ⚠ Deduplicar por contract_id: cada contrato esta repetido una vez por
        # corp que lo ve, y sin esto cada regalo contaria doble.
        with connection.cursor() as c:
            c.execute(f"""
                SELECT c.contract_id, c.contract_type, c.status, c.price, c.reward,
                       en.name, c.date_issued, c.id
                FROM corptools_corporatecontract c
                JOIN (SELECT contract_id, MIN(id) AS rid
                      FROM corptools_corporatecontract
                      WHERE assignee_id IN ({ph}) AND date_issued >= %s
                      GROUP BY contract_id) u ON u.rid = c.id
                LEFT JOIN corptools_evename en ON en.eve_id = c.issuer_name_id
                ORDER BY c.date_issued DESC LIMIT %s
            """, destinos + [desde, o["limite"]])
            contratos = c.fetchall()

        self.stdout.write(f"\n  A los destinatarios: {len(contratos)} (máx {o['limite']}, deduplicados)")
        if not contratos:
            self.stdout.write("    (ninguno: la rama de contratos sigue sin datos reales que probar)")
            return

        from koru_stats.models import MoonTaxContract
        tax = set(MoonTaxContract.objects
                  .filter(contract_id__in=[x[0] for x in contratos])
                  .values_list("contract_id", flat=True))

        tids = set()
        for cid, tipo, estado, precio, premio, emisor, fecha, rid in contratos:
            with connection.cursor() as c:
                c.execute("""
                    SELECT i.type_name_id, SUM(i.quantity), MIN(i.raw_quantity)
                    FROM corptools_corporatecontractitem i
                    WHERE i.contract_id = %s AND i.is_included = 1
                    GROUP BY i.type_name_id
                """, [rid])
                items = c.fetchall()
            avisos = []
            if cid in tax:                       avisos.append("ES TAX LUNAR, se salta")
            if (tipo or "") != "item_exchange":  avisos.append(f"tipo {tipo}")
            if (precio or 0) or (premio or 0):   avisos.append("price/reward != 0")
            if any((raw or 0) < 0 for _, _, raw in items): avisos.append("lleva BPC")
            if not items:                        avisos.append("sin items")
            tids |= {int(t) for t, _, _ in items if t}

            self.stdout.write(
                f"    #{cid}  {str(fecha)[:16]}  {(emisor or '?')[:20]:20} "
                f"{len(items):>3} ítems  {estado:12} "
                + (self.style.WARNING("· " + "; ".join(avisos)) if avisos else ""))

        if o["valorar"] and tids:
            from koru_stats.tasks import _refresh_jita_prices
            self.stdout.write("\n  Pidiendo precios a Jita de " + str(len(tids)) + " tipos…")
            datos = _refresh_jita_prices(list(tids))
            sin = [t for t in tids if t not in datos or not datos[t].get("ordenes")]
            self.stdout.write(f"  con precio: {len(tids) - len(sin)} · sin órdenes en Jita: {len(sin)}")
