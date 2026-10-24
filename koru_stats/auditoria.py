"""
Lo que el sistema puede responder solo de una auditoría de Asuntos Internos.

★ LA IDEA. De los siete puntos que Asuntos Internos revisa hoy a mano, cinco
son datos que corptools ya tiene del piloto. Pedirle a un auditor que vaya a
buscarlos convierte la checklist en burocracia. Aquí se calculan y se le ponen
delante; él solo juzga.

⚠⚠ LA TRAMPA DE IDS DE CORPTOOLS (verificado 24/10/2026 contra
`information_schema.KEY_COLUMN_USAGE`, no "a ojo"):

    corptools_characteraudit.character_id  ->  PK de eveonline_evecharacter
    TODO LO DEMAS .character_id            ->  PK del AUDIT

Afecta a characterasset, charactercontact, characterroles, clone, jumpclone,
corporationhistory, skill, skillqueue y skilltotals. Un join mal puesto aquí
NO revienta: devuelve los datos de OTRA PERSONA, y en una auditoría eso es
peor que un error. Ya pasó una vez.

Lo que NO hay y conviene saber:
  · **Omega no existe** como dato en corptools. Ese punto es manual y lo será.
  · **Los assets no tienen precio**: `corptools_typeprice` está vacía, así que
    se cuentan items, no se valora la cartera.
  · **No hay lista de hostiles.** Se pueden enseñar los contactos a los que el
    piloto pone standing alto, pero quién es enemigo de Rekium lo reconoce una
    persona, no esta consulta.
"""

import logging

from django.db import connection

logger = logging.getLogger(__name__)


# Standing a partir del cual un contacto es «alguien que le importa». En EVE
# 5 es «bueno» y 10 «excelente»; por debajo de 5 hay mucho ruido de gente que
# se marca sin más.
STANDING_AMIGO = 5


SQL_PERSONAJES = """
SELECT ec.id                AS pk,
       ec.character_id      AS eve_id,
       ec.character_name    AS nombre,
       ec.corporation_name  AS corp,
       ec.alliance_name     AS alianza,
       ec.birthday          AS nacimiento,
       cau.id               AS audit,
       cau.balance          AS isk,
       cau.last_known_login AS ultimo_login,
       cau.total_logins     AS logins,
       st.total_sp          AS sp
FROM authentication_characterownership co
JOIN eveonline_evecharacter ec         ON ec.id = co.character_id
LEFT JOIN corptools_characteraudit cau ON cau.character_id = ec.id
LEFT JOIN corptools_skilltotals st     ON st.character_id = cau.id
WHERE co.user_id = %s
ORDER BY ec.character_name
"""

# ⚠ a.character_id es el id del AUDIT. Ver la cabecera.
SQL_ASSETS = """
SELECT a.character_id AS audit, COUNT(*) AS n
FROM corptools_characterasset a
WHERE a.character_id IN %s
GROUP BY a.character_id
"""

SQL_CONTACTOS = """
SELECT c.character_id AS audit,
       c.standing     AS standing,
       c.contact_type AS tipo,
       c.blocked      AS bloqueado,
       en.name        AS nombre
FROM corptools_charactercontact c
LEFT JOIN corptools_evename en ON en.eve_id = c.contact_name_id
WHERE c.character_id IN %s
ORDER BY c.standing DESC
"""


def _filas(sql, params):
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, f)) for f in cur.fetchall()]


def _miles(n):
    """1234567 -> «1.234.567». Un número de ocho cifras sin separar no se lee."""
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "?"


def calcular(user):
    """
    Resuelve los puntos automáticos para el usuario de una solicitud.

    Devuelve {clave: {"valor": "una línea", "detalle": ["…", "…"]}}.

    ⚠ Nunca lanza por un dato que falte: una auditoría a medias es útil, una
    pantalla que no abre no. Lo que no se sabe se dice («sin datos de ESI»),
    no se inventa ni se omite.
    """
    if user is None:
        return {}

    try:
        chars = _filas(SQL_PERSONAJES, [user.id])
    except Exception as exc:
        logger.error("koru auditoria: no se pudieron leer los personajes: %s", exc)
        return {}

    audits = tuple(c["audit"] for c in chars if c["audit"])

    assets, contactos = {}, []
    if audits:
        try:
            assets = {f["audit"]: f["n"] for f in _filas(SQL_ASSETS, [audits])}
        except Exception as exc:
            logger.warning("koru auditoria: assets — %s", exc)
        try:
            contactos = _filas(SQL_CONTACTOS, [audits])
        except Exception as exc:
            logger.warning("koru auditoria: contactos — %s", exc)

    fuera = {}

    # ── Auth: ¿está registrado y con datos llegando? ──────────────────────
    sin_audit = [c["nombre"] for c in chars if not c["audit"]]
    sin_sp    = [c["nombre"] for c in chars if c["audit"] and c["sp"] is None]
    detalle = []
    if sin_audit:
        detalle.append("Sin auditoría de corptools: " + ", ".join(sin_audit))
    if sin_sp:
        detalle.append("Con auditoría pero sin datos de ESI todavía: " + ", ".join(sin_sp))
    if not detalle:
        detalle.append("Todos sus personajes tienen datos de ESI llegando.")
    fuera["auth"] = {
        "valor": f"{len(chars)} personaje(s) registrados, "
                 f"{len(chars) - len(sin_audit)} con auditoría",
        "detalle": detalle,
    }

    # ── Personajes: quién es y dónde está cada uno ────────────────────────
    fuera["personajes"] = {
        "valor": f"{len(chars)} personaje(s)",
        "detalle": [
            f"{c['nombre']} — {c['corp'] or 'sin corp'}"
            + (f" [{c['alianza']}]" if c["alianza"] else "")
            for c in chars
        ] or ["Ninguno registrado."],
    }

    # ── Skill points ──────────────────────────────────────────────────────
    sp_total = sum((c["sp"] or 0) for c in chars)
    fuera["sp"] = {
        "valor": f"{_miles(sp_total)} SP en total",
        "detalle": [f"{c['nombre']}: {_miles(c['sp']) if c['sp'] is not None else 'sin datos'} SP"
                    for c in chars],
    }

    # ── ISK: el saldo vive en la propia fila del audit ────────────────────
    isk_total = sum((c["isk"] or 0) for c in chars)
    fuera["isk"] = {
        "valor": f"{_miles(isk_total)} ISK en total",
        "detalle": [f"{c['nombre']}: {_miles(c['isk']) if c['isk'] is not None else 'sin datos'} ISK"
                    for c in chars],
    }

    # ── Assets: SOLO cantidad. No hay precios en la base. ─────────────────
    total_items = sum(assets.get(c["audit"], 0) for c in chars)
    fuera["assets"] = {
        "valor": f"{_miles(total_items)} items",
        "detalle": [f"{c['nombre']}: {_miles(assets.get(c['audit'], 0))} items" for c in chars]
                   + ["⚠ Cantidad, no valor: corptools no guarda precios."],
    }

    # ── Contactos ─────────────────────────────────────────────────────────
    # ⚠ Esto NO dice «tiene contactos hostiles». No existe una lista de quién
    # es hostil para Rekium. Dice a quién aprecia, y el auditor reconoce
    # nombres o no los reconoce. Prometer más sería mentir en una auditoría.
    amigos = [c for c in contactos if (c["standing"] or 0) >= STANDING_AMIGO]
    bloqueados = [c for c in contactos if c["bloqueado"]]
    detalle = [f"{c['nombre'] or '?'} ({c['tipo']}, standing {c['standing']})"
               for c in amigos[:25]]
    if len(amigos) > 25:
        detalle.append(f"… y {len(amigos) - 25} más con standing alto.")
    if bloqueados:
        detalle.append(f"Tiene {len(bloqueados)} contacto(s) bloqueado(s).")
    if not contactos:
        detalle = ["Sin contactos, o todavía sin datos de ESI."]
    elif not amigos:
        detalle.insert(0, "Ninguno con standing alto.")
    fuera["contactos"] = {
        "valor": f"{len(contactos)} contacto(s), {len(amigos)} con standing ≥ {STANDING_AMIGO}",
        "detalle": detalle,
    }

    # ── Actividad de la cuenta ────────────────────────────────────────────
    detalle = []
    for c in chars:
        login = c["ultimo_login"].strftime("%d/%m/%Y") if c["ultimo_login"] else "sin dato"
        detalle.append(f"{c['nombre']}: último login {login}, "
                       f"{_miles(c['logins']) if c['logins'] is not None else '?'} entradas")
    ultimos = [c["ultimo_login"] for c in chars if c["ultimo_login"]]
    fuera["actividad"] = {
        "valor": ("Último login " + max(ultimos).strftime("%d/%m/%Y")) if ultimos
                 else "Sin datos de login",
        "detalle": detalle or ["Sin personajes."],
    }

    return fuera


def enlace_de(plantilla, main_nombre, main_eve_id):
    """
    «https://zkillboard.com/character/{id}/» -> la URL del piloto.

    Un check externo solo ahorra tiempo si el auditor pincha en vez de buscar.
    """
    if not plantilla:
        return ""
    try:
        return plantilla.format(nombre=main_nombre or "", id=main_eve_id or "")
    except (KeyError, IndexError, ValueError):
        # Una plantilla mal escrita en el admin no puede tumbar la pantalla.
        return ""
