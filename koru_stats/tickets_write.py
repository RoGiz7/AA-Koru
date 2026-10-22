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

    accion            "claim", de momento lo único
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

    try:
        r = requests.post(
            cfg.n8n_webhook_url,
            json=carga,
            headers={"X-Koru-Token": cfg.n8n_webhook_secret},
            timeout=TIEMPO_MAX,
        )
    except requests.RequestException as exc:
        logger.error("koru tickets_write reclamar: no se pudo llamar a n8n: %s", exc)
        raise ValueError(f"No se pudo hablar con n8n: {exc}")

    if r.status_code >= 400:
        # ⚠ Se enseña el cuerpo RECORTADO: un webhook que falla suele devolver
        # el error entero, y ahi dentro puede venir media fila de Baserow.
        logger.error("koru tickets_write reclamar: n8n devolvio %s — %s",
                     r.status_code, r.text[:300])
        raise ValueError(f"n8n respondió {r.status_code}. Mira la ejecución en n8n.")

    # ★ NO se toca el espejo local. Lo que vale es lo que quede en Baserow, y
    # eso entra por `sync_tickets`. Escribirlo aqui «para que se vea ya» seria
    # inventar un estado que a lo mejor n8n no llego a guardar.
    logger.info("koru tickets_write: %s reclama el ticket %s/%s",
                nombre, ticket.tipo, ticket.numero or ticket.baserow_row_id)
    return nombre
