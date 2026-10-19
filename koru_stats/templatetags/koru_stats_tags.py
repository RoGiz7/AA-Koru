from django import template

register = template.Library()


@register.filter
def rknum(value):
    """Formato EVE: coma de miles. Ej: 1234567 → 1,234,567"""
    try:
        v = float(value or 0)
        return f"{v:,.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
def rkisk(value):
    """ISK con sufijo legible estilo EVE. Ej: 1234567890 → 1.23 B"""
    try:
        v = float(value or 0)
        if v >= 1e12:
            return f"{v/1e12:.2f} T"
        if v >= 1e9:
            return f"{v/1e9:.2f} B"
        if v >= 1e6:
            return f"{v/1e6:.2f} M"
        if v >= 1e3:
            return f"{v/1e3:.1f} K"
        return f"{v:,.0f}"
    except (ValueError, TypeError):
        return value


@register.filter
def rkm3(value):
    """m³ con coma de miles estilo EVE. Ej: 43273000 → 43,273,000 m³"""
    try:
        v = float(value or 0)
        return f"{v:,.0f} m³"
    except (ValueError, TypeError):
        return value


@register.inclusion_tag("koru_stats/includes/gift_card.html", takes_context=True)
def koru_gift_card(context):
    """
    Tarjeta estacional de la fiesta para Mi Dashboard.

    Va como tag y no por contexto de la vista a proposito: asi `mi_dashboard`
    no se toca (son 4.000 lineas y un reemplazo por texto ahi es donde se
    rompen las cosas), y la tarjeta se puede colgar de cualquier plantilla con
    una sola linea. Si no hay campana abierta no pinta nada.
    """
    from ..views import _gift_mi_ctx

    request = context.get("request")
    if request is None or not request.user.is_authenticated:
        return {"g": None}
    if not request.user.has_perm("koru_stats.gift_access"):
        return {"g": None}
    try:
        return {"g": _gift_mi_ctx(request)}
    except Exception:      # una tarjeta nunca debe tumbar el dashboard
        return {"g": None}


@register.filter
def dict_key(d, key):
    """Permite acceder a un dict por clave en templates Django."""
    try:
        return d[key]
    except (KeyError, TypeError):
        return None
