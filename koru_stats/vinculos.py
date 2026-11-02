"""
El rastro de personajes: qué personaje fue de qué main, pase lo que pase con
la cuenta.

DOS PIEZAS QUE SE CUBREN:
  · SEÑALES. Cuando Alliance Auth borra una relación personaje→usuario (alguien
    quita un alt o se borra la cuenta), se apunta ANTES de que desaparezca,
    con el motivo.
  · FOTO DE CADA HORA. Recorre todas las relaciones vivas y compara con la
    anterior. Pilla lo que no pasa por las señales (un borrado directo en la
    base de datos, un personaje que cambia de dueño, un cambio de main) y es
    lo que llena la tabla la primera vez.

⚠ Nada de aquí puede tumbar un borrado de Alliance Auth: si el rastro falla,
se loguea y el borrado sigue. Lo que se escape lo recoge la foto siguiente.

MOTIVOS DE BAJA:
  quitado        — el usuario quitó el personaje de su cuenta
  cuenta borrada — se borró la cuenta entera
  cambio de main — sigue en la misma cuenta, con otro main (no es sospechoso)
  otro dueño     — el personaje ahora es de OTRA cuenta
  no visto       — desapareció sin pasar por las señales
"""

import logging

from django.db import connection

logger = logging.getLogger(__name__)

# Motivos que de verdad dicen algo de la persona. «cambio de main» no.
SOSPECHOSOS = ("quitado", "cuenta borrada", "otro dueño", "no visto")

# Cuentas que se están borrando ahora mismo: {user_id: (main_id, main_nombre)}.
# Se rellena en el pre_delete del User para que, al borrar sus personajes en
# cascada, el motivo sea «cuenta borrada» y no «quitado».
_borrando = {}


def _main_de_usuario(user_id):
    with connection.cursor() as cur:
        cur.execute(
            "SELECT mc.character_id, mc.character_name FROM authentication_userprofile up "
            "JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id WHERE up.user_id = %s",
            [user_id])
        fila = cur.fetchone()
    return (int(fila[0]), fila[1] or "") if fila else (None, "")


def apuntar_baja(character_id, character_name, main_id, main_nombre, user_id, motivo):
    """Marca el vínculo como perdido y deja el evento. Crea el vínculo si no estaba."""
    from django.utils import timezone

    from .models import KoruVinculo, KoruVinculoEvento

    if not main_id:
        return
    ahora = timezone.now()
    v, _ = KoruVinculo.objects.get_or_create(
        character_id=character_id, main_character_id=main_id,
        defaults={"character_name": character_name[:100], "main_character_name": main_nombre[:100],
                  "user_id": user_id, "ultimo_visto": ahora})
    if not v.activo:
        return
    v.activo, v.quitado_en, v.motivo = False, ahora, motivo
    v.save(update_fields=["activo", "quitado_en", "motivo"])
    KoruVinculoEvento.objects.create(
        character_id=character_id, character_name=character_name[:100], main_character_id=main_id,
        main_character_name=main_nombre[:100], user_id=user_id, evento=KoruVinculoEvento.BAJA, motivo=motivo)


# ------------------------------------------------------------------ señales

def _usuario_pre_delete(sender, instance, **kwargs):
    try:
        _borrando[instance.pk] = _main_de_usuario(instance.pk)
    except Exception as exc:
        logger.error("koru rastro: pre_delete usuario %s: %s", instance.pk, exc)


def _usuario_post_delete(sender, instance, **kwargs):
    _borrando.pop(instance.pk, None)


def _propiedad_pre_delete(sender, instance, **kwargs):
    try:
        uid = instance.user_id
        if uid in _borrando:
            main_id, main_nombre = _borrando[uid]
            motivo = "cuenta borrada"
        else:
            main_id, main_nombre = _main_de_usuario(uid)
            motivo = "quitado"
        ch = instance.character
        apuntar_baja(int(ch.character_id), ch.character_name or "", main_id, main_nombre, uid, motivo)
    except Exception as exc:
        logger.error("koru rastro: pre_delete personaje: %s", exc)


def conectar():
    """Se llama desde apps.ready(). Si Alliance Auth no está, no hace nada."""
    from django.contrib.auth.models import User
    from django.db.models.signals import post_delete, pre_delete
    try:
        from allianceauth.authentication.models import CharacterOwnership
    except Exception as exc:
        logger.warning("koru rastro: sin CharacterOwnership, no se vigilan bajas: %s", exc)
        return
    pre_delete.connect(_usuario_pre_delete, sender=User, dispatch_uid="koru_rastro_user_pre")
    post_delete.connect(_usuario_post_delete, sender=User, dispatch_uid="koru_rastro_user_post")
    pre_delete.connect(_propiedad_pre_delete, sender=CharacterOwnership, dispatch_uid="koru_rastro_owner_pre")


# ------------------------------------------------------------------ la foto

SQL_VIVOS = """
SELECT co.user_id, ec.character_id, ec.character_name, ec.corporation_name,
       mc.character_id, mc.character_name
FROM authentication_characterownership co
JOIN eveonline_evecharacter ec ON ec.id = co.character_id
JOIN authentication_userprofile up ON up.user_id = co.user_id
JOIN eveonline_evecharacter mc ON mc.id = up.main_character_id
"""


def registrar():
    """
    La foto de cada hora. Devuelve (altas, bajas).

    ★ La primera vez rellena la tabla SIN eventos: si no, el primer día
    saldrían miles de «alta» que no dicen nada.
    """
    from django.utils import timezone

    from .models import KoruVinculo, KoruVinculoEvento

    ahora = timezone.now()
    inicial = not KoruVinculo.objects.exists()
    with connection.cursor() as cur:
        cur.execute(SQL_VIVOS)
        vivos = cur.fetchall()

    existentes = {(v.character_id, v.main_character_id): v for v in KoruVinculo.objects.all()}
    vistos, dueno_actual = set(), {}
    altas = bajas = 0
    nuevos, eventos = [], []

    for uid, cid, cnom, corp, mid, mnom in vivos:
        cid, mid = int(cid), int(mid)
        clave = (cid, mid)
        vistos.add(clave)
        dueno_actual[cid] = uid
        v = existentes.get(clave)
        if v is None:
            nuevos.append(KoruVinculo(character_id=cid, character_name=(cnom or "")[:100], main_character_id=mid,
                                      main_character_name=(mnom or "")[:100], user_id=uid,
                                      corp_name=(corp or "")[:100], ultimo_visto=ahora))
            if not inicial:
                eventos.append(KoruVinculoEvento(character_id=cid, character_name=(cnom or "")[:100],
                                                 main_character_id=mid, main_character_name=(mnom or "")[:100],
                                                 user_id=uid, evento=KoruVinculoEvento.ALTA, motivo="añadido"))
                altas += 1
            continue
        cambios = {}
        if not v.activo:
            cambios.update(activo=True, quitado_en=None, motivo="")
            eventos.append(KoruVinculoEvento(character_id=cid, character_name=(cnom or "")[:100],
                                             main_character_id=mid, main_character_name=(mnom or "")[:100],
                                             user_id=uid, evento=KoruVinculoEvento.ALTA, motivo="vuelve"))
            altas += 1
        if (cnom or "") != v.character_name or (corp or "") != v.corp_name or uid != v.user_id \
                or (mnom or "") != v.main_character_name:
            cambios.update(character_name=(cnom or "")[:100], corp_name=(corp or "")[:100], user_id=uid,
                           main_character_name=(mnom or "")[:100])
        if cambios:
            KoruVinculo.objects.filter(id=v.id).update(**cambios)

    if nuevos:
        KoruVinculo.objects.bulk_create(nuevos, ignore_conflicts=True)

    # Lo que estaba vivo y ya no se ve, sin haber pasado por las señales.
    for clave, v in existentes.items():
        if not v.activo or clave in vistos:
            continue
        cid = clave[0]
        if cid in dueno_actual:
            motivo = "cambio de main" if dueno_actual[cid] == v.user_id else "otro dueño"
        else:
            motivo = "no visto"
        KoruVinculo.objects.filter(id=v.id).update(activo=False, quitado_en=ahora, motivo=motivo)
        eventos.append(KoruVinculoEvento(character_id=cid, character_name=v.character_name,
                                         main_character_id=v.main_character_id,
                                         main_character_name=v.main_character_name, user_id=v.user_id,
                                         evento=KoruVinculoEvento.BAJA, motivo=motivo))
        bajas += 1

    if eventos:
        KoruVinculoEvento.objects.bulk_create(eventos)
    KoruVinculo.objects.filter(activo=True).update(ultimo_visto=ahora)
    return altas, bajas


# ------------------------------------------------------------------ consultas

def de_main(main_id):
    """
    Lo que el rastro sabe de una persona: vínculos perdidos y eventos.

    ★ Se buscan también por `user_id`: si cambió de main, sus alts viejos están
    apuntados con el main anterior y seguirían siendo suyos.
    """
    from django.db.models import Q

    from .models import KoruVinculo, KoruVinculoEvento

    uids = set(KoruVinculo.objects.filter(main_character_id=main_id)
               .exclude(user_id=None).values_list("user_id", flat=True))
    filtro = Q(main_character_id=main_id) | Q(user_id__in=uids)
    perdidos = list(KoruVinculo.objects.filter(filtro, activo=False).exclude(motivo="cambio de main")
                    .order_by("-quitado_en"))
    eventos = list(KoruVinculoEvento.objects.filter(filtro).order_by("-en")[:100])
    return perdidos, eventos
