"""
Acciones sobre un ticket desde la web (T3).

★ KORU NO ESCRIBE EN BASEROW. Le pide a n8n que escriba.

La decisión de junio fue «un único dueño por dato»: Baserow es la fuente de
verdad del ticket operativo y lo escribe n8n. Un `PATCH` directo desde aquí
serían dos sistemas escribiendo la misma fila, que es exactamente lo que se
decidió evitar — y encima **Discord no se enteraría**: reclamarías el ticket en
la web y en el canal seguiría figurando sin reclamar, con su botón intacto.

Así que esto manda un POST a un webhook de n8n y se acabó. Quien escribe en
Baserow y quien edita el mensaje de Discord sigue siendo n8n, con sus
credenciales, como hasta ahora.

LO QUE MANDA, y por qué cada cosa:

    accion            "claim" | "estado" | "auditoria"
    tipo              reclutamiento | directores | asuntos | it | soporte
    tabla             id de tabla en Baserow, para que n8n no tenga que adivinarlo
    row_id            la fila del ticket (la tenemos del espejo)
    claim_personaje   el MAIN de quien reclama, para buscarlo en la tabla Main
    claim_discord_uid su id de Discord, para la mención «Claimado por <@id>»
    canal_discord     el canal del ticket, para localizar el mensaje a editar

⚠ No se manda el rol ni se comprueba nada de permisos en n8n: quién puede
reclamar qué lo decide AA con sus grupos, aquí, antes de llamar. n8n solo
comprueba que la llamada viene de Koru (la cabecera `X-Koru-Token`).
"""

import logging

import requests

logger = logging.getLogger(__name__)

# Las tablas, que n8n ya conoce pero mejor no obligarle a deducirlas
TABLA_POR_TIPO = {
    "reclutamiento": 502,
    "directores":    503,
    "soporte":       508,
    "it":            510,
    "asuntos":       1702,
}

# ⚠ De donde sale el canal de Discord en cada tabla: NO se llama igual en todas.
# El orden importa, se coge el primero que exista.
CLAVES_CANAL = ("Canal Discord", "Discord Channel ID", "Canal Auditoría")

TIEMPO_MAX = 15        # segundos; si n8n tarda mas, algo va mal y mejor avisar


class SinConfigurar(Exception):
    """El webhook no esta puesto: la web no puede escribir todavia."""


def _config():
    from .models import TicketsConfig

    cfg = TicketsConfig.objects.filter(tag="default").first()
    if not cfg or not cfg.enabled or not cfg.n8n_webhook_url:
        raise SinConfigurar(
            "Falta el webhook de n8n en la configuración de Tickets "
            "(admin → Koru Stats → Configuración de Tickets)")
    return cfg


def canal_de(ticket):
    """
    El id del canal de Discord del ticket, mirando donde haga falta.

    `discord_ticket` vale de ultimo recurso porque en estas tablas el «Nº Ticket
    Discord» ES el id del canal; no es una coincidencia bonita, es como se creo.
    """
    extra = ticket.extra or {}
    for clave in CLAVES_CANAL:
        v = extra.get(clave)
        if v:
            return str(v)
    return str(ticket.discord_ticket or "")


def _quien(user):
    """(nombre del main, uid de Discord) de quien esta pulsando el boton."""
    from django.db import connection

    nombre, uid = "", ""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT mc.character_name FROM authentication_userprofile up "
            "JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id "
            "WHERE up.user_id = %s", [user.id])
        fila = cur.fetchone()
        if fila:
            nombre = fila[0] or ""
        # El uid solo sirve para la mencion en Discord: si no esta, no es grave
        try:
            cur.execute("SELECT uid FROM discord_discorduser WHERE user_id = %s", [user.id])
            fila = cur.fetchone()
            if fila:
                uid = str(fila[0] or "")
        except Exception:
            uid = ""
    return nombre, uid


def reclamar(ticket, user):
    """
    Pide a n8n que apunte a `user` como quien lleva este ticket.

    Devuelve el nombre del personaje con el que queda reclamado. Lanza
    ValueError con un motivo legible si no se puede.
    """
    cfg = _config()

    nombre, uid = _quien(user)
    if not nombre:
        raise ValueError(
            "Tu usuario no tiene personaje principal en el Auth, así que no hay "
            "nombre con el que reclamar")

    canal = canal_de(ticket)
    if not canal:
        raise ValueError(
            "Este ticket no tiene canal de Discord apuntado: n8n no sabría qué "
            "mensaje editar")

    tabla = TABLA_POR_TIPO.get(ticket.tipo)
    if not tabla:
        raise ValueError(f"No sé en qué tabla vive un ticket de «{ticket.tipo}»")

    carga = {
        "accion": "claim",
        "tipo": ticket.tipo,
        "tabla": tabla,
        "row_id": ticket.baserow_row_id,
        "claim_personaje": nombre,
        "claim_discord_uid": uid,
        "canal_discord": canal,
        "origen": "koru",
    }

    _llamar(cfg, carga, "reclamar")

    # ★ NO se toca el espejo local. Lo que vale es lo que quede en Baserow, y
    # eso entra por `sync_tickets`. Escribirlo aqui «para que se vea ya» seria
    # inventar un estado que a lo mejor n8n no llego a guardar.
    logger.info("koru tickets_write: %s reclama el ticket %s/%s",
                nombre, ticket.tipo, ticket.numero or ticket.baserow_row_id)
    return nombre


def _llamar(cfg, carga, que):
    """El POST a n8n, que es igual para todas las acciones."""
    try:
        r = requests.post(
            cfg.n8n_webhook_url, json=carga,
            headers={"X-Koru-Token": cfg.n8n_webhook_secret}, timeout=TIEMPO_MAX)
    except requests.RequestException as exc:
        logger.error("koru tickets_write %s: no se pudo llamar a n8n: %s", que, exc)
        raise ValueError(f"No se pudo hablar con n8n: {exc}")

    if r.status_code >= 400:
        # ⚠ El cuerpo se recorta: un webhook que falla suele devolver el error
        # entero, y ahi dentro puede venir media fila de Baserow.
        logger.error("koru tickets_write %s: n8n devolvio %s — %s",
                     que, r.status_code, r.text[:300])
        raise ValueError(f"n8n respondió {r.status_code}. Mira la ejecución en n8n.")

    try:
        return r.json()
    except ValueError:
        return {}


def abrir_auditoria(main_id, nombre_piloto, motivo, user, riesgo=None, alerta=""):
    """
    Abre una auditoría de Asuntos Internos para este piloto, desde el Auditor.

    Se lo pide a n8n (K1 → K2), que crea el canal en Discord y la ficha en la
    tabla 1702. Devuelve el dict que responde n8n: `canal`, `canal_nombre`,
    `fila_1702`.

    ★ EL MOTIVO ES OBLIGATORIO y va a parar a las Notas de la ficha. Una
    auditoría cuyo único rastro es «la abrió el Auditor» no le sirve a nadie
    dentro de tres meses, que es justo cuando se consulta.
    """
    from .models import Ticket

    cfg = _config()

    motivo = " ".join((motivo or "").split())
    if len(motivo) < 10:
        raise ValueError("Pon un motivo de al menos 10 caracteres: es lo que "
                         "queda escrito en la ficha de la auditoría")

    nombre, uid = _quien(user)
    if not nombre:
        raise ValueError(
            "Tu usuario no tiene personaje principal en el Auth, así que no hay "
            "nombre al que asignar la auditoría")

    # ⚠ Una auditoria abierta por piloto. Dos canales para el mismo caso es
    # como se pierde la mitad de la conversacion. Las auditorias NO tienen
    # Estado en Baserow, asi que «abierta» = sin fecha de cierre.
    abierta = (Ticket.objects
               .filter(tipo="asuntos", main_character_id=main_id, fecha_cierre__isnull=True)
               .order_by("-fecha").first())
    if abierta:
        raise ValueError(
            f"{nombre_piloto} ya tiene una auditoría abierta"
            + (f" ({abierta.numero or abierta.discord_ticket})" if (abierta.numero or abierta.discord_ticket) else "")
            + ". Ciérrala antes de abrir otra.")

    carga = {
        "accion": "auditoria",
        "piloto": nombre_piloto,
        "motivo": motivo,
        "quien_personaje": nombre,
        "quien_discord_uid": uid,
        "riesgo": "" if riesgo is None else str(riesgo),
        "alerta": alerta or "",
        "origen": "koru",
    }

    datos = _llamar(cfg, carga, "auditoria")
    logger.info("koru tickets_write: %s abre auditoria de %s (canal %s)",
                nombre, nombre_piloto, datos.get("canal") or "?")
    return datos


def estados_posibles(ticket):
    """
    Los estados que admite la tabla de este ticket, segun Baserow.

    Vacio si esa tabla no tiene campo `Estado` —IT y Asuntos Internos no lo
    tienen— o si el sync aun no los ha leido.
    """
    try:
        cfg = _config()
    except SinConfigurar:
        return []
    tabla = TABLA_POR_TIPO.get(ticket.tipo)
    return list((cfg.estados_por_tabla or {}).get(str(tabla), []))


def cambiar_estado(ticket, estado, user):
    """
    Pide a n8n que ponga este ticket en `estado`.

    ⚠ ESTO NO CIERRA EL TICKET. Cerrar de verdad es lo que hace W5 desde
    Discord: vuelca la transcripcion, sube el fichero y archiva. Aqui solo se
    cambia la ETIQUETA. Poner «Archivado» desde la web y creer que el ticket
    quedo cerrado te deja sin transcripcion, que es justo lo que luego hace
    falta cuando alguien pregunta que paso.
    """
    cfg = _config()

    estado = (estado or "").strip()
    posibles = estados_posibles(ticket)
    if not posibles:
        raise ValueError(
            f"Los tickets de «{ticket.tipo}» no tienen campo Estado en Baserow")
    # ★ Se valida contra lo que Baserow dice que admite, no contra una lista
    # nuestra: un select rechaza cualquier valor que no sea una de SUS opciones,
    # y el error saldria de Baserow, feo y a destiempo.
    if estado not in posibles:
        raise ValueError(f"«{estado}» no es un estado válido ahí. Son: {', '.join(posibles)}")
    if estado == (ticket.estado or ""):
        raise ValueError(f"El ticket ya está en «{estado}»")

    nombre, uid = _quien(user)
    carga = {
        "accion": "estado",
        "tipo": ticket.tipo,
        "tabla": TABLA_POR_TIPO.get(ticket.tipo),
        "row_id": ticket.baserow_row_id,
        "estado": estado,
        "quien_personaje": nombre,
        "quien_discord_uid": uid,
        "canal_discord": canal_de(ticket),
        "origen": "koru",
    }

    _llamar(cfg, carga, "estado")

    logger.info("koru tickets_write: %s pone el ticket %s/%s en «%s»",
                nombre or user, ticket.tipo, ticket.numero or ticket.baserow_row_id, estado)
    return estado
