"""
Motor de sorteos de la fiesta (R3).

Vive en su propio modulo a proposito: `views.py` va por 4.300 lineas y
`tasks.py` por 3.300, y esto es logica pura que se puede probar sin base de
datos. El nucleo (`sortear_core`) no toca Django: entran listas de tuplas y
sale el resultado, asi que se verifica con un test de mesa.

★ LAS DOS REGLAS QUE NO SE NEGOCIAN

1. **El ganador se decide en el SERVIDOR.** La ruleta solo anima un resultado
   ya decidido. Si lo eligiera el navegador, cualquiera con la consola abierta
   podria discutirlo, y un sorteo discutible es peor que no tener sorteo.

2. **Limpieza demostrable.** Al CERRAR se genera una semilla y se publica su
   SHA-256. Al SORTEAR se guarda la semilla en claro. Con la semilla, el roster
   y la bolsa —los tres congelados— cualquiera reproduce el resultado entero.

El sorteo NO usa el `random` de Python: cada tirada sale de
`sha256("<semilla>:<premio_id>:<intento>")`. Asi se puede reproducir con
cualquier herramienta en cualquier lenguaje, sin depender de como siembre
Python su generador ni de la version que corra el servidor.
"""

import hashlib
import secrets


# ---------------------------------------------------------------------------
# Nucleo puro — sin Django, sin BD
# ---------------------------------------------------------------------------

def hash_semilla(semilla: str) -> str:
    """El compromiso que se publica al cerrar, antes de sortear nada."""
    return hashlib.sha256(semilla.encode("utf-8")).hexdigest()


def nueva_semilla() -> str:
    """32 bytes de aleatoriedad criptografica, en hex."""
    return secrets.token_hex(32)


def _tirada(semilla: str, prize_id, intento: int, n: int):
    """(indice, hash) — deterministico y reproducible fuera de Python."""
    crudo = f"{semilla}:{prize_id}:{intento}"
    h = hashlib.sha256(crudo.encode("utf-8")).hexdigest()
    return int(h, 16) % n, h


def sortear_core(entrants, prizes, semilla, *, ponderar=True,
                 excluir_propio=True, permitir_repetir=False):
    """
    Resuelve el sorteo entero. Funcion PURA: mismas entradas, mismo resultado.

    entrants: [{"id", "main_char_id", "papeletas"}]
    prizes:   [{"id", "orden", "donante_main_id"}]  (donante None si exclusivo)

    Devuelve (resultados, incidencias):
      resultados: [{"prize_id", "entrant_id", "orden", "hash"}]
      incidencias: ["premio X sin candidatos", ...]

    ORDEN CANONICO, y es parte del contrato de reproducibilidad: los premios se
    recorren por (orden, id) y los participantes se ordenan por main_char_id
    antes de expandir papeletas. Cambiar esto invalida los sorteos ya hechos.
    """
    ganadores = set()
    resultados, incidencias = [], []

    prem = sorted(prizes, key=lambda p: (p.get("orden", 0), p["id"]))
    base = sorted(entrants, key=lambda e: int(e["main_char_id"]))

    for i, p in enumerate(prem):
        candidatos = []
        for e in base:
            if not permitir_repetir and e["id"] in ganadores:
                continue
            # Que no te toque lo que tu mismo aportaste
            if excluir_propio and p.get("donante_main_id") is not None \
                    and int(p["donante_main_id"]) == int(e["main_char_id"]):
                continue
            candidatos.append(e)

        if not candidatos:
            incidencias.append(f"premio {p['id']}: nadie elegible")
            continue

        # Expandir papeletas. Sin ponderar, una por cabeza.
        bolsa = []
        for e in candidatos:
            veces = max(1, int(e.get("papeletas", 1))) if ponderar else 1
            bolsa.extend([e["id"]] * veces)

        idx, h = _tirada(semilla, p["id"], 0, len(bolsa))
        ganador = bolsa[idx]
        ganadores.add(ganador)
        resultados.append({"prize_id": p["id"], "entrant_id": ganador,
                           "orden": i, "hash": h})

    return resultados, incidencias


# ---------------------------------------------------------------------------
# Envoltorio sobre los modelos
# ---------------------------------------------------------------------------

def _payload(raffle):
    """Saca de la BD lo que el nucleo necesita, ya congelado."""
    entrants = [
        {"id": e.id, "main_char_id": e.main_char_id, "papeletas": e.papeletas}
        for e in raffle.entrants.all()
    ]
    prizes = []
    for p in raffle.prizes.select_related("contribution").all():
        donante = None
        if p.contribution_id and p.contribution.main_char_id:
            donante = p.contribution.main_char_id
        prizes.append({"id": p.id, "orden": p.orden, "donante_main_id": donante})
    return entrants, prizes


def cerrar(raffle):
    """
    Congela el sorteo y publica el compromiso.

    A partir de aqui el roster y la bolsa no se tocan: si se recalcularan en
    vivo, alguien que aporte entre dos tiradas apareceria a mitad del sorteo.
    """
    from django.utils import timezone
    from .models import Raffle

    if raffle.estado != Raffle.ESTADO_BORRADOR:
        raise ValueError("Solo se puede cerrar un sorteo en borrador")
    if not raffle.entrants.exists():
        raise ValueError("No hay participantes")
    if not raffle.prizes.exists():
        raise ValueError("No hay premios")

    semilla = nueva_semilla()
    raffle.semilla = semilla
    raffle.semilla_hash = hash_semilla(semilla)
    raffle.cerrado_en = timezone.now()
    raffle.estado = Raffle.ESTADO_CERRADO
    raffle.save(update_fields=["semilla", "semilla_hash", "cerrado_en", "estado"])
    return raffle.semilla_hash


def sortear(raffle):
    """Resuelve el sorteo y guarda los resultados. Solo una vez."""
    from django.db import transaction
    from django.utils import timezone
    from .models import Raffle, RaffleDraw

    if raffle.estado != Raffle.ESTADO_CERRADO:
        raise ValueError("Hay que cerrar el sorteo antes de sortearlo")

    entrants, prizes = _payload(raffle)
    resultados, incidencias = sortear_core(
        entrants, prizes, raffle.semilla,
        ponderar=raffle.ponderar_por_rango,
        excluir_propio=raffle.excluir_propio_regalo and raffle.tipo == Raffle.TIPO_COMUNITARIO,
        permitir_repetir=raffle.permitir_repetir_ganador,
    )

    with transaction.atomic():
        RaffleDraw.objects.bulk_create([
            RaffleDraw(raffle=raffle, prize_id=r["prize_id"], entrant_id=r["entrant_id"],
                       orden=r["orden"], hash_usado=r["hash"])
            for r in resultados
        ])
        raffle.estado = Raffle.ESTADO_SORTEADO
        raffle.sorteado_en = timezone.now()
        raffle.save(update_fields=["estado", "sorteado_en"])

    return resultados, incidencias


def verificar(raffle):
    """
    Recomputa el sorteo desde la semilla y lo compara con lo guardado.

    Esta es la funcion que hace que el sorteo sea DEMOSTRABLE y no solo
    "confia en mi". Devuelve (ok, detalles).
    """
    from .models import Raffle

    if raffle.estado != Raffle.ESTADO_SORTEADO:
        return False, ["El sorteo no esta sorteado"]

    problemas = []
    if hash_semilla(raffle.semilla) != raffle.semilla_hash:
        problemas.append("La semilla no casa con el hash publicado al cerrar")

    entrants, prizes = _payload(raffle)
    resultados, _ = sortear_core(
        entrants, prizes, raffle.semilla,
        ponderar=raffle.ponderar_por_rango,
        excluir_propio=raffle.excluir_propio_regalo and raffle.tipo == Raffle.TIPO_COMUNITARIO,
        permitir_repetir=raffle.permitir_repetir_ganador,
    )
    esperado = {r["prize_id"]: r["entrant_id"] for r in resultados}
    guardado = {d.prize_id: d.entrant_id for d in raffle.draws.all()}

    if esperado != guardado:
        for pid in set(esperado) | set(guardado):
            if esperado.get(pid) != guardado.get(pid):
                problemas.append(
                    f"premio {pid}: guardado {guardado.get(pid)}, recomputado {esperado.get(pid)}")

    return (not problemas), (problemas or ["Reproducido exactamente"])


def anular(raffle, usuario, motivo):
    """
    Tira el sorteo entero y lo devuelve a borrador, dejando rastro.

    Nunca se borra una tirada suelta en silencio: o vale el sorteo entero o se
    anula entero, y con motivo.
    """
    from django.db import transaction
    from django.utils import timezone
    from .models import Raffle

    if not motivo:
        raise ValueError("Anular pide motivo")
    # R5 añadira GiftDelivery: cuando exista, aqui va el corte de "ya hay
    # premios entregados, no se puede anular".

    with transaction.atomic():
        raffle.draws.all().delete()
        raffle.estado = Raffle.ESTADO_BORRADOR
        raffle.semilla = ""
        raffle.semilla_hash = ""
        raffle.cerrado_en = None
        raffle.sorteado_en = None
        raffle.anulado_por = usuario
        raffle.anulado_en = timezone.now()
        raffle.motivo_anulacion = motivo[:250]
        raffle.save()
    return True


# ---------------------------------------------------------------------------
# Constructor de roster
#
# Filtrar -> PREVISUALIZAR -> fijar. El paso del medio no es un lujo: es lo que
# permite ver a quien saca el filtro ANTES de congelarlo, que es justo donde se
# descubren los criterios mal puestos.
# ---------------------------------------------------------------------------

def preview_roster(campaign, spec=None):
    """
    Devuelve los candidatos que saca el filtro, SIN escribir nada.

    spec (todo opcional):
      valor_min        float  — valor aportado minimo
      solo_aportantes  bool   — fuera quien no ha aportado nada
      states           [str]  — states de AA ("Miembros Rekium", ...)
      corps            [int]  — corporation_id de EVE
      excluir_ganadores_de [raffle_id] — quien ya gano en otro sorteo

    Cada candidato trae su valor, su rango y las papeletas que le tocan, ya
    calculados: lo que se fije luego es exactamente lo que se vio.
    """
    from django.db import connection

    from .models import GiftContribution

    spec = spec or {}

    # Lo aportado por main, que es sobre lo que se mide el rango
    aportado = {}
    for g in (GiftContribution.objects
              .filter(campaign=campaign)
              .exclude(estado=GiftContribution.ESTADO_DESCARTADA)):
        if g.main_char_id:
            aportado[g.main_char_id] = aportado.get(g.main_char_id, 0) + (g.valor_final or 0)

    # Universo de mains con su state y su corp
    sql = """
        SELECT DISTINCT main_ec.character_id, main_ec.character_name,
               main_ec.corporation_id, st.name
        FROM authentication_userprofile up
        JOIN eveonline_evecharacter main_ec ON main_ec.id = up.main_character_id
        LEFT JOIN authentication_state st ON st.id = up.state_id
    """
    filas = []
    with connection.cursor() as c:
        c.execute(sql)
        filas = [(int(a), b or "", int(d or 0), e or "") for a, b, d, e in c.fetchall()]

    states = set(spec.get("states") or [])
    corps = {int(x) for x in (spec.get("corps") or [])}
    valor_min = spec.get("valor_min")
    excluir = set()
    if spec.get("excluir_ganadores_de"):
        from .models import RaffleDraw
        excluir = set(
            RaffleDraw.objects
            .filter(raffle_id__in=spec["excluir_ganadores_de"])
            .values_list("entrant__main_char_id", flat=True)
        )

    tiers = list(campaign.tiers.order_by("orden"))

    out = []
    for char_id, nombre, corp_id, state in filas:
        if states and state not in states:
            continue
        if corps and corp_id not in corps:
            continue
        if char_id in excluir:
            continue

        valor = aportado.get(char_id, 0)
        if spec.get("solo_aportantes") and not valor:
            continue
        if valor_min is not None and valor < valor_min:
            continue

        rango = None
        for t in tiers:
            if valor >= t.umbral_min:
                rango = t
        out.append({
            "main_char_id": char_id, "main_name": nombre,
            "corporation_id": corp_id, "state": state,
            "valor": valor,
            "rango_nombre": rango.nombre if rango else "",
            "papeletas": rango.papeletas if rango else 1,
        })

    out.sort(key=lambda x: (-float(x["valor"]), x["main_name"]))
    return out


def fijar_roster(raffle, candidatos, usuario=None, reemplazar=True):
    """
    Escribe el roster. A partir de aqui no cambia aunque alguien aporte mas.

    Se guardan FILAS, no la consulta: una lista viva haria aparecer y
    desaparecer gente entre dos tiradas.
    """
    from django.db import transaction

    from .models import Raffle, RaffleEntrant

    if raffle.estado != Raffle.ESTADO_BORRADOR:
        raise ValueError("El roster solo se toca en borrador")

    with transaction.atomic():
        if reemplazar:
            raffle.entrants.filter(origen=RaffleEntrant.ORIGEN_FILTRO).delete()
        manuales = set(raffle.entrants.values_list("main_char_id", flat=True))
        nuevos = [
            RaffleEntrant(
                raffle=raffle, main_char_id=c["main_char_id"], main_name=c["main_name"],
                origen=RaffleEntrant.ORIGEN_FILTRO,
                papeletas=max(1, int(c.get("papeletas", 1))),
                rango_nombre=c.get("rango_nombre", ""), valor_aportado=c.get("valor", 0),
                anadido_por=usuario,
            )
            for c in candidatos if c["main_char_id"] not in manuales
        ]
        RaffleEntrant.objects.bulk_create(nuevos)
    return len(nuevos)


def anadir_por_meritos(raffle, main_char_id, motivo, papeletas=1, usuario=None):
    """
    Mete a alguien al margen de lo que haya aportado.

    El motivo es OBLIGATORIO, y sale con insignia propia en pantalla: la
    transparencia de por que esta cada nombre es lo que evita que el sorteo
    huela mal.
    """
    from .models import Raffle, RaffleEntrant

    if raffle.estado != Raffle.ESTADO_BORRADOR:
        raise ValueError("El roster solo se toca en borrador")
    if not motivo:
        raise ValueError("Entrar por meritos pide motivo")

    nombre = ""
    from django.db import connection
    with connection.cursor() as c:
        c.execute("SELECT character_name FROM eveonline_evecharacter WHERE character_id = %s",
                  [int(main_char_id)])
        fila = c.fetchone()
        if fila:
            nombre = fila[0] or ""

    obj, creado = RaffleEntrant.objects.update_or_create(
        raffle=raffle, main_char_id=int(main_char_id),
        defaults={
            "main_name": nombre, "origen": RaffleEntrant.ORIGEN_MANUAL,
            "motivo": motivo[:200], "papeletas": max(1, int(papeletas)),
            "anadido_por": usuario,
        },
    )
    return obj, creado


# ---------------------------------------------------------------------------
# Alta por NOMBRE, contrastada contra ESI
#
# Para cuando el CEO decide meter a alguien que no esta en la corp ni en el
# Auth: se teclea el nombre y se resuelve contra ESI en ese momento.
#
# ★ LA TRAMPA, verificada en vivo el 2026-10-19: `POST /universe/ids/` NO da
# error con un nombre que no existe — simplemente lo OMITE de la respuesta.
#   ["Nombre Real Uno", "Nombre Real Dos", "NombreInventado"]
#   -> {"characters":[{"id":...,"name":"Nombre Real Uno"},{"id":...}]}
# Si no se comprueba que el nombre pedido esta en la respuesta, un nombre mal
# escrito entraria con el id de otro. De ahi el emparejado explicito.
# ---------------------------------------------------------------------------

ESI_IDS_URL = "https://esi.evetech.net/universe/ids/"
ESI_COMPAT_DATE_FALLBACK = "2026-08-18"


def _user_agent():
    """El UA sale de tasks.py, pero PEREZOSAMENTE.

    Importarlo arriba arrastraria celery entero solo por una cadena, y
    abriria la puerta a un import circular el dia que tasks necesite este
    modulo. El nucleo del sorteo se queda sin dependencias a proposito.
    """
    try:
        from .tasks import ESI_HEADERS
        return ESI_HEADERS.get("User-Agent", "koru_stats")
    except Exception:
        return "koru_stats"
ESI_COMPAT_DATE = "2026-08-18"


def resolver_nombre_esi(nombre):
    """
    (character_id, nombre_canonico) o (None, None).

    Mira primero en la BD del Auth: no se le pregunta a ESI lo que ya sabemos.
    """
    from django.db import connection

    nombre = (nombre or "").strip()
    if not nombre:
        return None, None

    # 1. Local, gratis
    with connection.cursor() as c:
        c.execute(
            "SELECT character_id, character_name FROM eveonline_evecharacter "
            "WHERE LOWER(character_name) = LOWER(%s) LIMIT 1", [nombre])
        fila = c.fetchone()
    if fila:
        return int(fila[0]), fila[1]

    # 2. ESI. Una peticion, un nombre.
    import requests as http_requests

    try:
        resp = http_requests.post(
            ESI_IDS_URL, json=[nombre], timeout=20,
            headers={"Content-Type": "application/json",
                     "X-Compatibility-Date": ESI_COMPAT_DATE,
                     "User-Agent": _user_agent()},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return None, None

    # El nombre inexistente NO viene de vuelta: hay que emparejar a mano
    for ch in (data.get("characters") or []):
        if (ch.get("name") or "").lower() == nombre.lower():
            return int(ch["id"]), ch["name"]
    return None, None


def anadir_por_nombre(raffle, nombre, motivo, papeletas=1, usuario=None):
    """
    Mete a alguien tecleando su nombre, aunque no este en la corp ni en el Auth.

    Devuelve (entrant, creado, externo). `externo` dice si el personaje no
    existe en Alliance Auth: en pantalla lleva insignia propia, porque meter a
    un ajeno es justo la decision que mas conviene que se vea.
    """
    from django.utils import timezone

    from .models import Raffle, RaffleEntrant

    if raffle.estado != Raffle.ESTADO_BORRADOR:
        raise ValueError("El roster solo se toca en borrador")
    if not motivo:
        raise ValueError("Entrar a mano pide motivo")

    char_id, canonico = resolver_nombre_esi(nombre)
    if not char_id:
        raise ValueError(f"ESI no reconoce a «{nombre}». Revisa como esta escrito.")

    from django.db import connection
    with connection.cursor() as c:
        c.execute("SELECT 1 FROM eveonline_evecharacter WHERE character_id = %s", [char_id])
        en_auth = bool(c.fetchone())

    obj, creado = RaffleEntrant.objects.update_or_create(
        raffle=raffle, main_char_id=char_id,
        defaults={
            "main_name": canonico, "origen": RaffleEntrant.ORIGEN_MANUAL,
            "motivo": motivo[:200], "papeletas": max(1, int(papeletas)),
            "externo": not en_auth, "verificado_esi": timezone.now(),
            "anadido_por": usuario,
        },
    )
    return obj, creado, (not en_auth)
