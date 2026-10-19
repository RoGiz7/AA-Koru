"""
Pegado desde el juego y armador de lotes (R6).

Dos piezas que van juntas pero se prueban por separado:

1. **El pegado.** Un director copia el contenedor o el hangar en EVE y lo pega
   aqui. EVE copia en TSV con el nombre en la primera columna.

2. **El armador de lotes.** Repartir N objetos en K lotes de valor parecido,
   porque casi siempre hay mas cosas que personas.

Como en `raffles.py`, el nucleo es PURO: `parse_pegado` y `armar_lotes` no tocan
Django ni la base de datos, asi que se prueban en una mesa. Solo
`resolver_tipos` necesita la BD.
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# 1. El pegado
# ---------------------------------------------------------------------------

def _a_entero(txt):
    """
    '1.234' -> 1234 y '1,234' -> 1234.

    ⚠ El separador de miles cambia con el idioma del cliente. La cantidad es
    SIEMPRE entera, asi que se limpian los dos separadores sin pensarlo: no hay
    caso donde una cantidad legitima lleve decimales.
    """
    limpio = re.sub(r"[.,\s ]", "", str(txt or "").strip())
    if not limpio or not limpio.isdigit():
        return None
    return int(limpio)


def parse_pegado(texto):
    """
    [(nombre, cantidad)] desde el portapapeles de EVE.

    Aguanta los formatos que suelta el juego:
      "Rifter\\t3\\tFrigate\\tShip\\t..."   (inventario completo)
      "Rifter\\t3"                          (nombre y cantidad)
      "Rifter"                              (una unidad)

    La cantidad se busca como el PRIMER campo entero despues del nombre, no por
    posicion fija: las columnas cambian segun de donde se copie.
    """
    salida = []
    for linea in (texto or "").splitlines():
        if not linea.strip():
            continue
        campos = [c.strip() for c in linea.split("\t")]
        if len(campos) == 1:
            campos = [c.strip() for c in re.split(r"\s{2,}", linea) if c.strip()]

        nombre = campos[0].strip()
        if not nombre:
            continue
        # Un encabezado pegado por error no es un item
        if nombre.lower() in ("name", "nombre", "item", "objeto"):
            continue

        cantidad = 1
        for c in campos[1:]:
            n = _a_entero(c)
            if n is not None:
                cantidad = n
                break
        salida.append((nombre, max(1, cantidad)))
    return salida


def _normaliza(s):
    """Para comparar nombres sin que acentos ni mayusculas estorben."""
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _columnas_de_nombre():
    """
    ['name', 'name_en', 'name_es', ...] — las que EXISTEN de verdad.

    ⚠ Se descubren por introspeccion, no se dan por hechas: que idiomas hay
    depende de `LANGUAGES` en los settings, y dar por supuesto un `name_es` que
    no existe revienta la consulta entera.
    """
    from django.db import connection

    with connection.cursor() as c:
        cols = [d.name for d in connection.introspection.get_table_description(
            c, "eve_sde_itemtype")]
    return [x for x in cols if x == "name" or x.startswith("name_")]


def resolver_tipos(nombres):
    """
    (encontrados, no_encontrados).

    encontrados: {nombre_pegado: (type_id, nombre_canonico)}

    ★ Busca en TODOS los idiomas que tenga el SDE. Si el director tiene el
    cliente en español, el pegado viene en español y buscar solo contra `name`
    (ingles) no encontraria nada: pareceria que el sistema esta roto cuando el
    roto seria el supuesto.

    Lo que no se reconoce se devuelve aparte. Nunca se descarta en silencio.
    """
    from django.db import connection

    pedidos = [n for n in dict.fromkeys(nombres) if n]
    if not pedidos:
        return {}, []

    columnas = _columnas_de_nombre()
    indice = {}          # nombre normalizado -> (type_id, nombre canonico en)
    ph = ",".join(["%s"] * len(pedidos))

    with connection.cursor() as c:
        for col in columnas:
            c.execute(
                f"SELECT it.id, it.name, it.{col} FROM eve_sde_itemtype it "
                f"WHERE it.{col} IN ({ph})", pedidos)
            for tid, canonico, encontrado in c.fetchall():
                if encontrado:
                    indice.setdefault(_normaliza(encontrado), (int(tid), canonico or ""))

    encontrados, faltan = {}, []
    for n in pedidos:
        hit = indice.get(_normaliza(n))
        if hit:
            encontrados[n] = hit
        else:
            faltan.append(n)
    return encontrados, faltan


# ---------------------------------------------------------------------------
# 2. El armador de lotes
# ---------------------------------------------------------------------------

def armar_lotes(objetos, k, isk_disponible=0, umbral_aviso=2.0):
    """
    Reparte `objetos` en `k` lotes de valor parecido. Funcion PURA.

    objetos: [{"id", "etiqueta", "valor"}]  — valor ya calculado
    isk_disponible: ISK suelto para nivelar (PLEX se trata como objeto normal)

    Devuelve (lotes, resumen).

    EL METODO, en dos pasos:

    1. **Reparto LPT**: se ordena de mayor a menor y cada objeto cae en el lote
       que va mas flojo. Es la heuristica clasica de particion multivia y deja
       los lotes bastante igualados con tres lineas de codigo.

    2. ★ **Nivelado con ISK por inundacion**: los objetos son indivisibles pero
       el ISK no, asi que se usa de mortero. Se sube el lote mas bajo hasta el
       siguiente, luego los dos hasta el tercero, y asi mientras quede ISK. Al
       acabar, o los lotes estan a la par, o se acabo el ISK.

    El resumen trae la dispersion y los avisos. Un objeto indivisible muy caro
    NO lo arregla ningun algoritmo: lo que hace el armador es DECIRLO.
    """
    k = max(1, int(k))
    lotes = [{"n": i, "objetos": [], "valor_objetos": 0.0, "isk": 0.0} for i in range(k)]

    orden = sorted(objetos, key=lambda o: float(o.get("valor") or 0), reverse=True)
    for o in orden:
        destino = min(lotes, key=lambda l: l["valor_objetos"])
        destino["objetos"].append(o)
        destino["valor_objetos"] += float(o.get("valor") or 0)

    # --- nivelado por inundacion -------------------------------------------
    isk = float(isk_disponible or 0)
    if isk > 0 and k > 1:
        niveles = sorted(lotes, key=lambda l: l["valor_objetos"])
        i = 1
        while isk > 0 and i < k:
            # subir los i mas bajos hasta el nivel del siguiente
            actual = niveles[i - 1]["valor_objetos"] + niveles[i - 1]["isk"]
            objetivo = niveles[i]["valor_objetos"]
            falta = (objetivo - actual) * i
            if falta <= 0:
                i += 1
                continue
            reparto = min(falta, isk) / i
            for l in niveles[:i]:
                l["isk"] += reparto
            isk -= reparto * i
            if reparto * i < falta:
                break          # se acabo el ISK antes de alcanzar el nivel
            i += 1
        if isk > 0:            # sobra: a repartir a partes iguales
            for l in lotes:
                l["isk"] += isk / k
            isk = 0

    for l in lotes:
        l["total"] = l["valor_objetos"] + l["isk"]

    totales = [l["total"] for l in lotes]
    media = sum(totales) / k if k else 0
    avisos = []
    if media > 0:
        for l in lotes:
            if l["total"] > media * umbral_aviso:
                veces = l["total"] / media
                caro = max(l["objetos"], key=lambda o: float(o.get("valor") or 0), default=None)
                avisos.append(
                    f"lote {l['n'] + 1} vale {veces:.1f}x la media"
                    + (f" (lo arrastra «{caro.get('etiqueta', '?')}»)" if caro else ""))
    if len(objetos) < k:
        avisos.append(f"hay {len(objetos)} objetos para {k} lotes: "
                      f"{k - len(objetos)} se quedarian solo con ISK")

    # ★ El aviso por "x veces la media" se le escapa el caso contrario: que
    # ningun lote se dispare pero los de abajo se queden cortos. Ahi el numero
    # que lo delata es la DISPERSION, no el maximo.
    dispersion = ((max(totales) - min(totales)) / media * 100) if media else 0
    if dispersion > 50 and not avisos:
        avisos.append(f"los lotes no han quedado igualados: {dispersion:.0f}% "
                      f"entre el mayor y el menor")

    # Cuanto ISK haria falta para dejarlos todos a la par. Es LA cifra
    # accionable: con esto el CEO decide si pone mas ISK o si parte un premio.
    techo = max((l["valor_objetos"] for l in lotes), default=0)
    isk_para_igualar = sum(techo - l["valor_objetos"] for l in lotes)

    resumen = {
        "lotes": k, "objetos": len(objetos),
        "valor_total": sum(totales),
        "media": media,
        "min": min(totales) if totales else 0,
        "max": max(totales) if totales else 0,
        "dispersion_pct": ((max(totales) - min(totales)) / media * 100) if media else 0,
        "isk_usado": float(isk_disponible or 0) - isk,
        "isk_sobrante": isk,
        "isk_para_igualar": max(0.0, isk_para_igualar - (float(isk_disponible or 0) - isk)),
        "avisos": avisos,
    }
    return lotes, resumen
