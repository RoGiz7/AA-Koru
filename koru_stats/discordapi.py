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
