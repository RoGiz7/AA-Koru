"""
Entrega y seguimiento de los premios (R5).

La ruleta para y empieza lo aburrido: que cada premio llegue a su dueño y que
dentro de dos semanas nadie tenga que preguntar en Discord «¿a mí me llegó lo
mío?». Este modulo es el que responde a eso.

TRES REGLAS, las mismas de siempre en este plugin:

1. **Detectar propone, el director dispone.** Un contrato que encaja NO cierra
   la entrega por su cuenta: la pone en «contrato puesto». Lo que la cierra es
   que el ganador lo acepte (eso si lo canta ESI) o que un humano diga que se
   entrego a mano.
2. **Nunca se cierra a ciegas.** Si hay dos candidatos posibles, no se elige al
   azar: se deja para que lo confirme alguien. Equivocarse aqui es decirle a
   alguien que ya cobro cuando no ha cobrado.
3. **Se guarda COMO se decidio**, no solo que se decidio: `emparejado_por` dice
   si fue por el titulo, por descarte o a mano.

★ EL TITULO DEL CONTRATO ES LA CLAVE DEL INVENTO. Emparejar por contenido es
imposible —un premio puede ser un lote suelto, ISK, o una nave con su fitting—
pero el titulo lo escribe el director y ahi cabe `Yoiul #<id>`. Si lo pone, el
emparejamiento es exacto y gratis; si no, se intenta por descarte y, si hay
duda, se pregunta.
"""

import re

from django.db import connection
from django.utils import timezone


TITULO_RE = re.compile(r"yoiul\s*#\s*(\d+)", re.I)

# Un regalo se pone a precio 0: si lleva precio es una VENTA, y una venta a un
# ganador no es la entrega de su premio aunque se la pongas el mismo dia.
SQL_CONTRATOS_SALIENTES = """
    SELECT c.contract_id, c.issuer_id, c.assignee_id, c.acceptor_id,
           c.status, c.title, c.date_issued, c.date_accepted, c.date_completed
    FROM {tabla} c
    JOIN (
        SELECT contract_id, MIN(id) AS rid
        FROM {tabla}
        WHERE assignee_id IN ({dest})
          AND contract_type = 'item_exchange'
          AND date_issued >= %s
        GROUP BY contract_id
    ) u ON u.rid = c.id
    WHERE COALESCE(c.price, 0) = 0
    ORDER BY c.date_issued
"""

# corptools guarda los contratos de la corp y los de los personajes auditados en
# dos tablas distintas. Un premio puede salir de cualquiera de las dos: del
# hangar de la corp o del personal del director que lo manda.
TABLAS = ("corptools_corporatecontract", "corptools_contract")

# ESI: lo que significa que el contrato ya no esta en pie
STATUS_MUERTOS = {"rejected", "cancelled", "deleted", "reversed", "failed"}
STATUS_VIVOS_CERRADOS = {"finished", "finished_issuer", "finished_contractor"}


def asegurar(raffle):
    """Crea la ficha de entrega de cada tirada que aun no la tenga."""
    from .models import GiftDelivery, RaffleDraw

    ya = set(GiftDelivery.objects.filter(draw__raffle=raffle).values_list("draw_id", flat=True))
    nuevas = [GiftDelivery(draw=d)
              for d in RaffleDraw.objects.filter(raffle=raffle) if d.id not in ya]
    if nuevas:
        GiftDelivery.objects.bulk_create(nuevas)
    return len(nuevas)


def _chars_por_main(main_ids):
    """
    {character_id: main_char_id} de TODOS los personajes de esos usuarios.

    ★ El premio se manda muchas veces al alt que esta en la estacion, no al
    main. Si solo mirasemos el main, media gala quedaria como no entregada.
    """
    if not main_ids:
        return {}
    ph = ",".join(["%s"] * len(main_ids))
    sql = (
        "SELECT ec.character_id, main_ec.character_id "
        "FROM eveonline_evecharacter ec "
        "JOIN authentication_characterownership co ON co.character_id = ec.id "
        "JOIN authentication_userprofile        up ON up.user_id      = co.user_id "
        "JOIN eveonline_evecharacter       main_ec ON main_ec.id      = up.main_character_id "
        "WHERE main_ec.character_id IN (" + ph + ")"
    )
    with connection.cursor() as cur:
        cur.execute(sql, list(main_ids))
        return {int(a): int(m) for a, m in cur.fetchall()}


def _contratos_hacia(char_ids, desde):
    """Los contratos de regalo que van hacia esos personajes, de las dos tablas."""
    if not char_ids:
        return []
    ids = list(char_ids)
    ph = ",".join(["%s"] * len(ids))
    salida, vistos = [], set()
    for tabla in TABLAS:
        sql = SQL_CONTRATOS_SALIENTES.format(tabla=tabla, dest=ph)
        with connection.cursor() as cur:
            cur.execute(sql, ids + [desde])
            cols = [c[0] for c in cur.description]
            for fila in cur.fetchall():
                d = dict(zip(cols, fila))
                cid = int(d["contract_id"])
                # ⚠ El MISMO contrato sale en las dos tablas cuando el director
                # lo manda desde su personaje y encima esta auditado. Sin este
                # filtro contaria dos veces y el segundo se quedaria huerfano,
                # apareciendo como «contrato sin emparejar» para siempre.
                if cid in vistos:
                    continue
                vistos.add(cid)
                salida.append(d)
    return salida


def sincronizar(campaign):
    """
    Pasa por los contratos y mueve las entregas de estado. Devuelve un resumen.

    No toca lo que ya esta cerrado ni lo entregado a mano: eso lo decidio una
    persona y el programa no tiene nada que añadir.
    """
    from .models import GiftDelivery, Raffle

    E = GiftDelivery
    sorteos = list(Raffle.objects
                   .filter(campaign=campaign, estado=Raffle.ESTADO_SORTEADO)
                   .values_list("id", "sorteado_en"))
    if not sorteos:
        return {"detectadas": 0, "aceptadas": 0, "caidas": 0, "sueltos": []}

    for rid, _ in sorteos:
        asegurar(Raffle.objects.get(pk=rid))

    abiertas = list(
        E.objects
        .filter(draw__raffle_id__in=[r for r, _ in sorteos])
        .exclude(estado__in=[E.ESTADO_CERRADO, E.ESTADO_A_MANO])
        .select_related("draw", "draw__entrant", "draw__prize")
    )
    if not abiertas:
        return {"detectadas": 0, "aceptadas": 0, "caidas": 0, "sueltos": []}

    # El suelo de fecha es el sorteo mas viejo: antes de sortear no hay premio
    # que entregar, asi que mirar mas atras solo trae ruido.
    fechas = [f for _, f in sorteos if f]
    desde = min(fechas) if fechas else campaign.ventana_desde

    mains = {d.draw.entrant.main_char_id for d in abiertas}
    alt_a_main = _chars_por_main(mains)
    # Un ganador de FUERA del Auth no tiene alts que mirar: vale el suyo
    for m in mains:
        alt_a_main.setdefault(m, m)

    contratos = _contratos_hacia(alt_a_main.keys(), desde)
    por_id = {int(c["contract_id"]): c for c in contratos}

    por_draw = {d.draw_id: d for d in abiertas}
    pendientes_por_main = {}
    for d in abiertas:
        pendientes_por_main.setdefault(d.draw.entrant.main_char_id, []).append(d)

    ahora = timezone.now()
    detectadas = aceptadas = caidas = 0
    usados = set()

    def _apuntar(entrega, contrato, como):
        nonlocal detectadas
        entrega.contract_id   = int(contrato["contract_id"])
        entrega.contract_para = int(contrato["assignee_id"] or 0)
        entrega.emparejado_por = como
        entrega.estado = E.ESTADO_DETECTADO
        entrega.detectado_en = ahora
        usados.add(int(contrato["contract_id"]))
        detectadas += 1

    # --- 1. Por titulo: exacto, y por eso va primero ------------------------
    for cid, c in por_id.items():
        m = TITULO_RE.search(c.get("title") or "")
        if not m:
            continue
        entrega = por_draw.get(int(m.group(1)))
        if not entrega or entrega.contract_id:
            continue
        # ⚠ El titulo lo escribe un humano a las tantas de la noche. Si dice un
        # ganador y el contrato va a otro, manda el contrato: se deja sin
        # emparejar para que lo mire alguien, en vez de dar por bueno el dedazo.
        if alt_a_main.get(int(c["assignee_id"] or 0)) != entrega.draw.entrant.main_char_id:
            continue
        _apuntar(entrega, c, "titulo")

    # --- 2. Por descarte: solo cuando no hay ninguna duda -------------------
    for main_id, lista in pendientes_por_main.items():
        sin_contrato = [d for d in lista if not d.contract_id]
        libres = [c for cid, c in por_id.items()
                  if cid not in usados and alt_a_main.get(int(c["assignee_id"] or 0)) == main_id]
        # Uno y uno. Con dos premios y dos contratos no se sabe cual es cual, y
        # adivinar es justo lo que no se puede hacer aqui.
        if len(sin_contrato) == 1 and len(libres) == 1:
            _apuntar(sin_contrato[0], libres[0], "descarte")

    # --- 3. Avanzar o retroceder lo que ya tenia contrato -------------------
    for entrega in abiertas:
        if not entrega.contract_id:
            continue
        c = por_id.get(int(entrega.contract_id))
        if not c:
            continue
        estado_esi = (c.get("status") or "").lower()
        if estado_esi in STATUS_MUERTOS:
            # ⚠ Sin esto, un contrato rechazado se quedaria como «puesto» para
            # siempre y el premio no volveria nunca a la lista de pendientes.
            entrega.estado = E.ESTADO_ASIGNADO
            entrega.contract_id = None
            entrega.contract_para = None
            entrega.emparejado_por = ""
            entrega.detectado_en = None
            entrega.nota = (entrega.nota + "\n" if entrega.nota else "") + \
                f"[auto] el contrato quedo en «{estado_esi}»: vuelve a pendiente"
            caidas += 1
        elif estado_esi in STATUS_VIVOS_CERRADOS or c.get("date_accepted"):
            if entrega.estado != E.ESTADO_ACEPTADO:
                entrega.estado = E.ESTADO_ACEPTADO
                entrega.aceptado_en = c.get("date_accepted") or c.get("date_completed") or ahora
                aceptadas += 1

    from django.db import transaction
    with transaction.atomic():
        for entrega in abiertas:
            entrega.save(update_fields=[
                "estado", "contract_id", "contract_para", "emparejado_por",
                "detectado_en", "aceptado_en", "nota", "updated_at"])

    sueltos = [c for cid, c in por_id.items() if cid not in usados
               and cid not in {d.contract_id for d in abiertas if d.contract_id}]
    return {"detectadas": detectadas, "aceptadas": aceptadas,
            "caidas": caidas, "sueltos": sueltos}


# ---------------------------------------------------------------------------
# Lo que hace un humano
# ---------------------------------------------------------------------------

def marcar_a_mano(entrega, nota, usuario=None):
    """Para lo que no pasa por contrato: ISK, un trade, algo dado en fleet."""
    from .models import GiftDelivery

    nota = (nota or "").strip()
    if not nota:
        # Dentro de un año, «entregado a mano» sin motivo no vale nada
        raise ValueError("Di cómo se entregó: en un mes nadie se acordará")
    entrega.estado = GiftDelivery.ESTADO_A_MANO
    entrega.cerrado_en = timezone.now()
    entrega.por_usuario = usuario
    entrega.nota = (entrega.nota + "\n" if entrega.nota else "") + nota
    entrega.save()
    return entrega


def cerrar(entrega, usuario=None):
    from .models import GiftDelivery

    if entrega.estado != GiftDelivery.ESTADO_ACEPTADO:
        raise ValueError("Solo se cierra lo que el ganador ya ha aceptado")
    entrega.estado = GiftDelivery.ESTADO_CERRADO
    entrega.cerrado_en = timezone.now()
    entrega.por_usuario = usuario
    entrega.save()
    return entrega


def reabrir(entrega, motivo, usuario=None):
    """Volver a pendiente. Siempre con motivo: cerrar y descerrar deja rastro."""
    from .models import GiftDelivery

    motivo = (motivo or "").strip()
    if not motivo:
        raise ValueError("Para reabrir hace falta un motivo")
    entrega.estado = GiftDelivery.ESTADO_ASIGNADO
    entrega.contract_id = None
    entrega.contract_para = None
    entrega.emparejado_por = ""
    entrega.detectado_en = entrega.aceptado_en = entrega.cerrado_en = None
    entrega.por_usuario = usuario
    entrega.nota = (entrega.nota + "\n" if entrega.nota else "") + f"[reabierta] {motivo}"
    entrega.save()
    return entrega


def asignar_contrato(entrega, contract_id, usuario=None):
    """
    El director dice a mano «este contrato es este premio».

    No se comprueba contra ESI: es una decision suya, igual que validar una
    aportacion. Queda marcada como `manual` para que se vea que la tomo alguien.
    """
    from .models import GiftDelivery

    try:
        cid = int(str(contract_id).strip())
    except (TypeError, ValueError):
        raise ValueError("El id del contrato tiene que ser un número")

    otra = (GiftDelivery.objects
            .filter(contract_id=cid, draw__raffle__campaign=entrega.draw.raffle.campaign)
            .exclude(pk=entrega.pk).first())
    if otra:
        raise ValueError(f"Ese contrato ya está puesto en «{otra.draw.prize.etiqueta}»")

    entrega.contract_id = cid
    entrega.emparejado_por = "manual"
    entrega.estado = GiftDelivery.ESTADO_DETECTADO
    entrega.detectado_en = timezone.now()
    entrega.por_usuario = usuario
    entrega.save()
    return entrega
