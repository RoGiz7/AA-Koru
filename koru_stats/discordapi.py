"""
Hablar con Discord desde AA, sin pasar por n8n.

★ POR QUÉ DIRECTO. El Auth ya tiene un bot de Discord con su token
(`DISCORD_BOT_TOKEN`) y ya lo usa para gestionar roles. Mandar a n8n una cosa
que podemos hacer aquí añade un workflow que mantener, un secreto más que
cruzar y un sitio más donde mirar cuando algo falla. Lo que SÍ se queda en n8n
es lo que nace en Discord —botones, modales—, porque allí está el disparador.

⚠ Este módulo no decide nada: crea canales y publica mensajes. Quién puede ver
qué lo deciden los llamantes con lo que haya en la configuración.
"""

import logging
import re

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API = "https://discord.com/api/v10"
ESPERA = 15          # segundos

# Permisos de Discord, en crudo. 1024 = VIEW_CHANNEL.
VER_CANAL = 1024
# 52224 = VIEW_CHANNEL + SEND_MESSAGES + READ_MESSAGE_HISTORY + ATTACH_FILES.
# Es exactamente lo que usan los canales de auditoría creados desde Discord:
# si aquí pusiéramos otra cosa, dos canales del mismo tipo se comportarían
# distinto según quién los creó.
PARTICIPAR = 52224


class SinBot(Exception):
    """No hay token de bot configurado en el Auth."""


def _cabeceras():
    token = getattr(settings, "DISCORD_BOT_TOKEN", "") or ""
    if not token:
        raise SinBot("El Auth no tiene DISCORD_BOT_TOKEN configurado")
    return {"Authorization": f"Bot {token}", "Content-Type": "application/json"}


def _guild():
    g = str(getattr(settings, "DISCORD_GUILD_ID", "") or "")
    if not g:
        raise SinBot("El Auth no tiene DISCORD_GUILD_ID configurado")
    return g


def nombre_canal(prefijo, texto):
    """Un nombre de canal válido: minúsculas, guiones y nada más."""
    limpio = "".join(
        c if (c.isalnum() or c == "-") else "-"
        for c in str(texto or "").strip().lower().replace(" ", "-"))
    while "--" in limpio:
        limpio = limpio.replace("--", "-")
    # ⚠ Discord corta en 100 caracteres. Mejor cortarlo nosotros que recibir un
    # 400 que no dice de qué va.
    return (str(prefijo) + limpio.strip("-"))[:100]


def crear_canal(nombre, categoria_id, roles_ver=(), uid_invitado=""):
    """
    Crea un canal de texto privado y devuelve su id.

    `roles_ver` son ids de rol que pueden participar. `uid_invitado` es la
    persona del ticket, que también entra — si no, tendríamos un canal privado
    donde no está quien lo motivó.
    """
    guild = _guild()

    # @everyone no lo ve: en Discord el rol @everyone tiene el id del guild.
    permisos = [{"id": guild, "type": 0, "deny": str(VER_CANAL)}]
    for rid in roles_ver or []:
        if rid:
            permisos.append({"id": str(rid), "type": 0, "allow": str(PARTICIPAR)})
    if uid_invitado:
        # type 1 = miembro, no rol.
        permisos.append({"id": str(uid_invitado), "type": 1, "allow": str(PARTICIPAR)})

    cuerpo = {"name": nombre, "type": 0, "permission_overwrites": permisos}
    if categoria_id:
        cuerpo["parent_id"] = str(categoria_id)

    r = requests.post(f"{API}/guilds/{guild}/channels", json=cuerpo,
                      headers=_cabeceras(), timeout=ESPERA)
    if r.status_code >= 400:
        # ⚠ Se recorta: Discord devuelve el cuerpo entero y esto acaba en una
        # pantalla y en un log.
        logger.error("koru discord: crear canal %s devolvio %s — %s",
                     nombre, r.status_code, r.text[:300])
        raise RuntimeError(f"Discord respondió {r.status_code} al crear el canal")
    return str(r.json().get("id") or "")


def publicar(canal_id, contenido):
    """Un mensaje en un canal. Trocea si se pasa del límite de Discord."""
    # 2000 caracteres por mensaje. Un retrato con muchos alts los pasa, y
    # perder la mitad de la ficha sin avisar sería peor que mandar dos mensajes.
    trozos, actual = [], ""
    for linea in str(contenido or "").split("\n"):
        if len(actual) + len(linea) + 1 > 1900:
            trozos.append(actual)
            actual = ""
        actual += linea + "\n"
    if actual.strip():
        trozos.append(actual)

    ultimo = None
    for trozo in trozos:
        r = requests.post(f"{API}/channels/{canal_id}/messages",
                          json={"content": trozo},
                          headers=_cabeceras(), timeout=ESPERA)
        if r.status_code >= 400:
            logger.error("koru discord: publicar en %s devolvio %s — %s",
                         canal_id, r.status_code, r.text[:300])
            raise RuntimeError(f"Discord respondió {r.status_code} al publicar")
        ultimo = r.json().get("id")
    return ultimo


def listar_roles():
    """
    Los roles del servidor, de mayor a menor posición: [(id, nombre), …].

    Se usa para ofrecer una lista en el admin en vez de pedir ids a mano. Los
    ids se copian mal con una facilidad pasmosa, y un id mal copiado aquí es un
    canal que no ve quien tiene que verlo.
    """
    from django.core.cache import cache

    guardado = cache.get("koru_discord_roles")
    if guardado is not None:
        return guardado

    r = requests.get(f"{API}/guilds/{_guild()}/roles",
                     headers=_cabeceras(), timeout=ESPERA)
    if r.status_code >= 400:
        logger.error("koru discord: listar roles devolvio %s — %s",
                     r.status_code, r.text[:200])
        raise RuntimeError(f"Discord respondió {r.status_code} al listar los roles")

    roles = []
    for rol in r.json():
        # @everyone no se ofrece: darle permiso de ver un canal privado es
        # exactamente lo contrario de lo que se quiere aquí.
        if str(rol.get("id")) == _guild():
            continue
        if rol.get("managed"):
            continue      # roles de bots e integraciones; no son de personas
        roles.append((str(rol["id"]), rol.get("name") or rol["id"]))

    roles.sort(key=lambda x: x[1].lower())
    # Diez minutos: cambiar un rol y que tarde eso en aparecer es asumible;
    # pedirle la lista a Discord en cada carga del admin, no.
    cache.set("koru_discord_roles", roles, 600)
    return roles


# Tipos de canal de Discord, de los que nos interesan aquí.
CANAL_TEXTO = 0
CATEGORIA   = 4


def listar_canales(tipo=CANAL_TEXTO):
    """
    Los canales del servidor de ese tipo: [(id, nombre), …].

    Con `tipo=CATEGORIA` devuelve las categorías, que para Discord son canales
    de otro tipo y vienen en la misma respuesta.
    """
    from django.core.cache import cache

    clave = f"koru_discord_canales_{tipo}"
    guardado = cache.get(clave)
    if guardado is not None:
        return guardado

    r = requests.get(f"{API}/guilds/{_guild()}/channels",
                     headers=_cabeceras(), timeout=ESPERA)
    if r.status_code >= 400:
        logger.error("koru discord: listar canales devolvio %s — %s",
                     r.status_code, r.text[:200])
        raise RuntimeError(f"Discord respondió {r.status_code} al listar los canales")

    todos = r.json()
    # Para un canal de texto se enseña también su categoría: en un Discord con
    # cien canales, tres se llaman «general» y sin el contexto no se sabe cuál
    # es cuál.
    nombres_cat = {str(c["id"]): c.get("name") or ""
                   for c in todos if c.get("type") == CATEGORIA}

    fuera = []
    for c in todos:
        if c.get("type") != tipo:
            continue
        nombre = c.get("name") or str(c["id"])
        padre = nombres_cat.get(str(c.get("parent_id") or ""))
        if tipo == CANAL_TEXTO and padre:
            nombre = f"{padre} / #{nombre}"
        fuera.append((str(c["id"]), nombre))

    fuera.sort(key=lambda x: x[1].lower())
    cache.set(clave, fuera, 600)
    return fuera


MENCION = re.compile(r"<(@[!&]?|#)(\d{5,25})>")


def _nombre_de_uid(uid):
    """
    El nombre de quien tiene ese id de Discord.

    ★ Primero se mira en Auth, que es gratis y además da el nombre QUE NOS
    IMPORTA: el del personaje principal, no el apodo de Discord. Solo si Auth
    no lo conoce — un invitado que nunca se registró — se le pregunta a
    Discord.
    """
    try:
        from allianceauth.services.modules.discord.models import DiscordUser
        du = (DiscordUser.objects
              .filter(uid=int(uid))
              .select_related("user__profile__main_character")
              .first())
        if du:
            main = getattr(getattr(du.user, "profile", None), "main_character", None)
            if main and main.character_name:
                return main.character_name
            if du.username:
                return du.username
    except Exception:
        pass

    try:
        r = requests.get(f"{API}/guilds/{_guild()}/members/{uid}",
                         headers=_cabeceras(), timeout=ESPERA)
        if r.status_code < 400:
            d = r.json()
            u = d.get("user") or {}
            return (d.get("nick") or u.get("global_name")
                    or u.get("username") or "")
    except Exception as exc:
        logger.debug("koru discord: no se pudo leer el miembro %s — %s", uid, exc)
    return ""


def resolver_menciones(texto):
    """
    Cambia «<@&951128547316076614>» por «@Asuntos Internos».

    ⚠ SE HACE AL MOSTRAR, NO AL GUARDAR. Lo que Discord manda son ids, y así
    es como se archiva la transcripción: si se tradujera al guardar, lo ya
    archivado seguiría enseñando ids para siempre y un rol renombrado quedaría
    congelado con el nombre viejo. Traduciendo al leer, el histórico entero se
    arregla solo.

    Un id que ya no existe — rol borrado, persona que se fue — se queda como
    «@desconocido» en vez de reventar la ficha.
    """
    texto = texto or ""
    if "<" not in texto:
        return texto

    from django.core.cache import cache

    try:
        roles = dict(listar_roles())
    except Exception:
        roles = {}
    try:
        canales = dict(listar_canales(CANAL_TEXTO))
    except Exception:
        canales = {}

    def _uno(m):
        tipo, ident = m.group(1), m.group(2)
        if tipo == "#":
            nombre = canales.get(ident, "")
            # listar_canales devuelve «Categoría / #canal»; aquí sobra.
            nombre = nombre.split("/")[-1].strip().lstrip("#")
            return f"#{nombre}" if nombre else "#desconocido"
        if tipo == "@&":
            return f"@{roles.get(ident) or 'desconocido'}"

        clave = f"koru_discord_nombre_{ident}"
        nombre = cache.get(clave)
        if nombre is None:
            nombre = _nombre_de_uid(ident) or ""
            # Se cachea incluso el fallo: si no se sabe quién es, preguntarlo
            # otra vez en cada carga de la ficha no lo va a saber mejor.
            cache.set(clave, nombre, 3600)
        return f"@{nombre or 'desconocido'}"

    return MENCION.sub(_uno, texto)


def leer_canal(canal_id, tope=2000):
    """
    Todos los mensajes de un canal, del más viejo al más nuevo.

    Devuelve [(cuando, autor, texto, [adjuntos])]. ⚠ Discord los da del más
    NUEVO al más viejo y de 100 en 100, así que hay que paginar hacia atrás con
    `before` y darle la vuelta al final. Quedarse con la primera página sería
    guardar el final de la conversación y tirar el principio.
    """
    fuera = []
    antes = None

    while len(fuera) < tope:
        url = f"{API}/channels/{canal_id}/messages?limit=100"
        if antes:
            url += f"&before={antes}"
        r = requests.get(url, headers=_cabeceras(), timeout=ESPERA)
        if r.status_code >= 400:
            logger.error("koru discord: leer canal %s devolvio %s — %s",
                         canal_id, r.status_code, r.text[:200])
            raise RuntimeError(f"Discord respondió {r.status_code} al leer el canal")

        lote = r.json()
        if not lote:
            break

        for m in lote:
            autor = (m.get("author") or {})
            fuera.append((
                m.get("timestamp") or "",
                autor.get("global_name") or autor.get("username") or "?",
                m.get("content") or "",
                [a.get("filename") or "" for a in (m.get("attachments") or [])],
            ))
        antes = lote[-1].get("id")
        if len(lote) < 100:
            break

    fuera.reverse()
    return fuera


def borrar_canal(canal_id):
    """Borra el canal. Solo después de haberlo guardado."""
    r = requests.delete(f"{API}/channels/{canal_id}",
                        headers=_cabeceras(), timeout=ESPERA)
    if r.status_code >= 400:
        logger.error("koru discord: borrar canal %s devolvio %s — %s",
                     canal_id, r.status_code, r.text[:200])
        raise RuntimeError(f"Discord respondió {r.status_code} al borrar el canal")
    return True
