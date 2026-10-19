from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class General(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access",        "Puede ver Estadísticas y Mi Dashboard"),
            ("corp_finance_access", "Puede ver Finanzas Corp"),
            ("moon_tax_access",     "Puede ver Tax Lunas"),
            ("moon_tax_admin",      "Puede gestionar tax de lunas"),
            ("pvp_access",          "Puede ver estadísticas PvP detalladas"),
            ("fc_access",           "Puede ver panel FC/Director"),
            ("auditor_access",      "Puede ver el panel Auditor (seguridad)"),
            ("auditor_admin",       "Puede configurar el Auditor y revisar/descartar alertas"),
            ("auditor_corp_health",  "Puede ver el panel de Salud de Corp (Directores/CEO)"),
            ("tickets_reclutamiento",   "Tickets: ve Reclutamiento"),
            ("tickets_directores",      "Tickets: ve A Directores"),
            ("tickets_asuntos_internos","Tickets: ve Asuntos Internos"),
            ("tickets_it",              "Tickets: ve IT y Soporte"),
            ("tickets_admin",           "Tickets: ve todos los tipos"),
            ("gift_access",   "Regalos: ve lo suyo (Mi aportación)"),
            ("gift_manage",   "Regalos: gestiona aportaciones, sorteos y entregas"),
            ("gift_ceo",      "Regalos: monta los sorteos especiales del CEO"),
        )


class TrackedCorporation(models.Model):
    corporation_id   = models.PositiveIntegerField(unique=True, help_text="EVE Online Corporation ID")
    corporation_name = models.CharField(max_length=100, help_text="Nombre descriptivo")
    is_active        = models.BooleanField(default=True)

    class Meta:
        verbose_name        = "Corp rastreada"
        verbose_name_plural = "Corps rastreadas"
        ordering            = ["corporation_name"]

    def __str__(self):
        return f"{self.corporation_name} ({self.corporation_id})"


class MoonTaxConfig(models.Model):
    tag               = models.CharField(max_length=100, default="default", unique=True)
    ubiquitous_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    common_rate       = models.DecimalField(max_digits=5, decimal_places=2, default=8.00)
    uncommon_rate     = models.DecimalField(max_digits=5, decimal_places=2, default=12.00)
    rare_rate         = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    exceptional_rate  = models.DecimalField(max_digits=5, decimal_places=2, default=25.00)
    is_active         = models.BooleanField(default=True)
    period_desde      = models.CharField(
        max_length=7, default="2026-07",
        help_text="Primer período que se cobra (YYYY-MM). El minado anterior NO genera deuda: "
                  "aplicar las tasas de hoy a minado viejo produce cifras sin sentido. "
                  "Arranca en 2026-07 porque la fractura #190 se repartio entre julio y agosto.")
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Configuración de tax lunar"
        verbose_name_plural = "Configuración de tax lunar"

    def __str__(self):
        return (f"{self.tag} — U:{self.ubiquitous_rate}% C:{self.common_rate}% "
                f"UC:{self.uncommon_rate}% R:{self.rare_rate}% E:{self.exceptional_rate}%")

    @property
    def rates_by_group(self):
        return {
            1884: float(self.ubiquitous_rate)  / 100,
            1920: float(self.common_rate)      / 100,
            1921: float(self.uncommon_rate)    / 100,
            1922: float(self.rare_rate)        / 100,
            1923: float(self.exceptional_rate) / 100,
        }


class MoonTaxPayment(models.Model):
    character_id   = models.IntegerField(db_index=True)
    character_name = models.CharField(max_length=100)
    period         = models.CharField(max_length=7, db_index=True)
    isk_owed       = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    is_paid        = models.BooleanField(default=False, db_index=True)
    paid_by        = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="moon_tax_payments_approved"
    )
    paid_at        = models.DateTimeField(null=True, blank=True)
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Tax lunar — pago"
        verbose_name_plural = "Tax lunar — pagos"
        unique_together     = ("character_id", "period")
        ordering            = ["-period", "character_name"]

    def __str__(self):
        estado = "✅ PAGADO" if self.is_paid else "⏳ PENDIENTE"
        return f"{self.character_name} | {self.period} | {self.isk_owed} ISK | {estado}"


# ---------------------------------------------------------------------------
# Tablas resumen — pre-agregadas por Celery, consultadas por las vistas
# ---------------------------------------------------------------------------

class CharacterMonthlySummary(models.Model):
    """
    Totales por personaje principal por mes.
    Populated by: tasks.aggregate_monthly_summary (Celery)
    """
    main_character_id   = models.IntegerField(db_index=True)
    main_character_name = models.CharField(max_length=100)
    corporation_id      = models.IntegerField(db_index=True, default=0)
    period              = models.CharField(max_length=7, db_index=True)

    # Minería
    mining_units             = models.BigIntegerField(default=0)
    mining_m3                = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    mining_isk               = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                   help_text="ISK a precio raw (market sell)")
    mining_isk_compressed    = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                   help_text="ISK si se vendiera comprimido")
    mining_isk_reprocessed   = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                                   help_text="ISK si se reprocesara al 85%")

    # Wallet
    bounty_isk = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    ess_isk    = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Resumen mensual por personaje"
        verbose_name_plural = "Resúmenes mensuales por personaje"
        constraints = [
            models.UniqueConstraint(
                fields=["main_character_id", "period"],
                name="unique_char_monthly_summary",
            ),
        ]
        indexes = [
            models.Index(fields=["period", "corporation_id"], name="koru_cms_period_corp"),
            models.Index(fields=["period", "mining_isk"],     name="koru_cms_period_mining"),
            models.Index(fields=["period", "bounty_isk"],     name="koru_cms_period_bounty"),
        ]

    def __str__(self):
        return f"{self.main_character_name} | {self.period}"

    @property
    def total_isk(self):
        return self.mining_isk + self.bounty_isk + self.ess_isk


class CharacterMonthlyOre(models.Model):
    """
    Desglose de tipos de ore por personaje principal por mes.
    Populated by: tasks.aggregate_monthly_ore (Celery)
    """
    main_character_id = models.IntegerField(db_index=True)
    corporation_id    = models.IntegerField(db_index=True, default=0)
    period            = models.CharField(max_length=7, db_index=True)

    type_id   = models.IntegerField()
    type_name = models.CharField(max_length=100)
    quantity  = models.BigIntegerField(default=0)
    m3        = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    isk             = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                          help_text="ISK a precio raw (market sell)")
    isk_compressed  = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                          help_text="ISK si se vendiera comprimido")
    isk_reprocessed = models.DecimalField(max_digits=20, decimal_places=2, default=0,
                                          help_text="ISK si se reprocesara al 85%")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Ore mensual por personaje"
        verbose_name_plural = "Ore mensuales por personaje"
        constraints = [
            models.UniqueConstraint(
                fields=["main_character_id", "period", "type_id"],
                name="unique_char_monthly_ore",
            ),
        ]
        indexes = [
            models.Index(fields=["period", "corporation_id", "type_id"], name="koru_cmo_period_corp_type"),
        ]

    def __str__(self):
        return f"{self.main_character_id} | {self.period} | {self.type_name}"


# ---------------------------------------------------------------------------
# Precios de ore — actualizados periódicamente desde Fuzzwork Market API
# ---------------------------------------------------------------------------

class OreMarketPrice(models.Model):
    """
    Precio de mercado de cada tipo de ore, en tres modalidades de valoración.
    Todos los precios son ISK por unidad de ore SIN comprimir (normalizados).
    Populated by: tasks.update_ore_prices (Celery, diario)
    """
    type_id   = models.IntegerField(unique=True, db_index=True)
    type_name = models.CharField(max_length=100)

    price_raw          = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    price_compressed   = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    price_reprocessed  = models.DecimalField(max_digits=20, decimal_places=4, default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Precio de ore"
        verbose_name_plural = "Precios de ore"
        ordering            = ["type_name"]

    def __str__(self):
        return f"{self.type_name} — raw:{self.price_raw} | comp:{self.price_compressed} | repr:{self.price_reprocessed}"


# ---------------------------------------------------------------------------
# PvP mensual — pre-agregado desde aastatistics_zkillmonth
# ---------------------------------------------------------------------------

class CharacterMonthlyPvp(models.Model):
    """
    Estadísticas PvP mensuales por personaje principal.
    Fuente: aastatistics_zkillmonth (zKill API)
    Populated by: tasks.aggregate_character_monthly_pvp (Celery)
    """
    main_character_id   = models.IntegerField(db_index=True)
    main_character_name = models.CharField(max_length=100)
    corporation_id      = models.IntegerField(db_index=True, default=0)
    period              = models.CharField(max_length=7, db_index=True)

    ships_destroyed = models.IntegerField(default=0)
    ships_lost      = models.IntegerField(default=0)
    isk_destroyed   = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    isk_lost        = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    # Detalle de participación (desde ESI attackers[])
    final_blows     = models.IntegerField(default=0)   # tiros de gracia
    participations  = models.IntegerField(default=0)   # killmails donde aparece como atacante
    solo_kills      = models.IntegerField(default=0)   # kills en solitario (zkb.solo)
    top_damage_kills = models.IntegerField(default=0)  # kills donde hizo más daño (sin ser final blow)
    damage_dealt    = models.BigIntegerField(default=0) # daño total infligido

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "PvP mensual por personaje"
        verbose_name_plural = "PvP mensuales por personaje"
        constraints = [
            models.UniqueConstraint(
                fields=["main_character_id", "period"],
                name="unique_char_monthly_pvp",
            ),
        ]
        indexes = [
            models.Index(fields=["period", "corporation_id"],  name="koru_pvp_period_corp"),
            models.Index(fields=["period", "isk_destroyed"],   name="koru_pvp_period_isk"),
            models.Index(fields=["period", "ships_destroyed"], name="koru_pvp_period_ships"),
        ]

    def __str__(self):
        return f"{self.main_character_name} | {self.period} | {self.ships_destroyed}K/{self.ships_lost}D"

    @property
    def isk_efficiency(self):
        total = self.isk_destroyed + self.isk_lost
        if not total:
            return 0.0
        return float(self.isk_destroyed / total * 100)

    @property
    def kd_ratio(self):
        if not self.ships_lost:
            return float(self.ships_destroyed)
        return float(self.ships_destroyed / self.ships_lost)


class CharacterKillRecord(models.Model):
    """Registro individual de killmail — kills y losses por personaje."""

    main_character_id   = models.BigIntegerField(db_index=True)
    main_character_name = models.CharField(max_length=255, default="")
    killmail_id         = models.BigIntegerField()
    period              = models.CharField(max_length=7, db_index=True)  # "2026-05"
    is_loss             = models.BooleanField(default=False)
    ship_type_id        = models.IntegerField(default=0)   # nave víctima (kills) o nave propia (losses)
    ship_name           = models.CharField(max_length=255, default="")
    value_isk           = models.FloatField(default=0.0)
    kill_date           = models.DateField(null=True, blank=True)
    final_blow          = models.BooleanField(default=False)
    solo                = models.BooleanField(default=False)
    # Datos del enemigo (solo en losses: el piloto que dio el final blow)
    enemy_char_id       = models.BigIntegerField(null=True, blank=True, db_index=True)
    enemy_char_name     = models.CharField(max_length=255, default="", blank=True)
    enemy_corp_id       = models.IntegerField(null=True, blank=True, db_index=True)
    enemy_corp_name     = models.CharField(max_length=255, default="", blank=True)
    # Hora EVE (UTC) del killmail — para heatmap de actividad
    kill_hour           = models.SmallIntegerField(null=True, blank=True)  # 0-23
    # Datos de la víctima (en KILLS: para detectar awox = matar a propio/blue)
    victim_corp_id      = models.IntegerField(null=True, blank=True, db_index=True)
    victim_corp_name    = models.CharField(max_length=255, default="", blank=True)
    victim_alliance_id  = models.IntegerField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name        = "Registro killmail"
        verbose_name_plural = "Registros killmail"
        unique_together = ("main_character_id", "killmail_id")
        indexes = [
            models.Index(fields=["main_character_id", "period", "is_loss"],
                         name="koru_killrec_char_period_loss"),
        ]

    def __str__(self):
        t = "Loss" if self.is_loss else "Kill"
        return f"{self.main_character_name} | {t} | {self.killmail_id}"

    @property
    def zkill_url(self):
        return f"https://zkillboard.com/kill/{self.killmail_id}/"

    @property
    def ship_image_url(self):
        return f"https://images.evetech.net/types/{self.ship_type_id}/render?size=64"


# ---------------------------------------------------------------------------
# Auditor — detección de patrones/comportamiento (Fase 1)
# ---------------------------------------------------------------------------

class AuditorConfig(models.Model):
    """Umbrales, pesos y listas de standings — singleton por 'tag'."""
    tag = models.CharField(max_length=50, default="default", unique=True)

    # Pesos de dimensión (0–1, idealmente suman 1) — prioridad al comportamiento
    w_pvp        = models.DecimalField(max_digits=4, decimal_places=2, default=0.25)
    w_ciclo      = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
    w_espias     = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
    w_fuga       = models.DecimalField(max_digits=4, decimal_places=2, default=0.15)
    w_huecos     = models.DecimalField(max_digits=4, decimal_places=2, default=0.10)
    w_financiero = models.DecimalField(max_digits=4, decimal_places=2, default=0.10)

    # Umbrales de nivel (0–100)
    umbral_amarillo = models.IntegerField(default=30)
    umbral_naranja  = models.IntegerField(default=60)
    umbral_rojo     = models.IntegerField(default=80)

    # Parámetros de señales
    token_stale_dias     = models.IntegerField(default=7,  help_text="Días sin sync de wallet/assets = token stale")
    inactividad_dias     = models.IntegerField(default=14, help_text="Días sin last_known_login = inactivo")
    donacion_externa_min = models.BigIntegerField(default=500_000_000, help_text="ISK mínimo de donación externa para señal")

    # Standings — cacheados por sync_blue_standings() desde los States del core de AA
    blue_alliance_ids  = models.JSONField(default=list, blank=True)  # State "Aliados"
    blue_corp_ids      = models.JSONField(default=list, blank=True)
    own_alliance_ids   = models.JSONField(default=list, blank=True)  # States propios (Miembros/Academy)
    own_corp_ids       = models.JSONField(default=list, blank=True)
    # IDs de States a considerar (configurable de cara a plugin)
    blue_state_ids     = models.JSONField(default=list, blank=True)  # p.ej. [7]
    own_state_ids      = models.JSONField(default=list, blank=True)  # p.ej. [2, 4]

    # Assets/staging (se usa en Fase 2)
    staging_location_ids = models.JSONField(default=list, blank=True)

    # Calibración: True = sin push a Discord (solo dashboard)
    modo_calibracion  = models.BooleanField(default=True)
    calibracion_hasta = models.DateField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Configuración del Auditor"
        verbose_name_plural = "Configuración del Auditor"

    def __str__(self):
        modo = "CALIBRACIÓN" if self.modo_calibracion else "ACTIVO"
        return f"AuditorConfig[{self.tag}] — {modo}"


class AuditorRiskScore(models.Model):
    """Score de riesgo por personaje principal por periodo, recalculado por Celery."""
    main_character_id   = models.IntegerField(db_index=True)
    main_character_name = models.CharField(max_length=100)
    corporation_id      = models.IntegerField(db_index=True, default=0)
    period              = models.CharField(max_length=7, db_index=True)  # YYYY-MM

    score_pvp        = models.IntegerField(default=0)
    score_ciclo      = models.IntegerField(default=0)
    score_espias     = models.IntegerField(default=0)
    score_fuga       = models.IntegerField(default=0)
    score_huecos     = models.IntegerField(default=0)
    score_financiero = models.IntegerField(default=0)
    risk_total       = models.IntegerField(default=0, db_index=True)
    nivel            = models.CharField(max_length=10, default="verde")  # verde/amarillo/naranja/rojo

    detalle     = models.JSONField(default=dict, blank=True)  # señales disparadas + valores
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Score de riesgo (Auditor)"
        verbose_name_plural = "Scores de riesgo (Auditor)"
        constraints = [
            models.UniqueConstraint(
                fields=["main_character_id", "period"],
                name="unique_auditor_score",
            ),
        ]
        indexes = [
            models.Index(fields=["period", "risk_total"],     name="koru_aud_period_risk"),
            models.Index(fields=["period", "corporation_id"], name="koru_aud_period_corp"),
        ]

    def __str__(self):
        return f"{self.main_character_name} | {self.period} | {self.risk_total} ({self.nivel})"


class AuditorAlert(models.Model):
    """Evento de alerta — el 'aviso' que se revisa y se acusa de recibo."""
    main_character_id   = models.IntegerField(db_index=True)
    main_character_name = models.CharField(max_length=100)
    period    = models.CharField(max_length=7, db_index=True)
    familia   = models.CharField(max_length=20)   # pvp/ciclo/espias/fuga/huecos/financiero
    codigo    = models.CharField(max_length=50)   # p.ej. "token_caido"
    severidad = models.CharField(max_length=10, default="warn")  # info/warn/critico
    titulo    = models.CharField(max_length=200)
    detalle   = models.JSONField(default=dict, blank=True)
    estado    = models.CharField(max_length=15, default="abierta", db_index=True)  # abierta/revisada/descartada

    revisada_por  = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="auditor_alerts_revisadas",
    )
    revisada_at   = models.DateTimeField(null=True, blank=True)
    nota_revision = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name        = "Alerta del Auditor"
        verbose_name_plural = "Alertas del Auditor"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["main_character_id", "period", "codigo"],
                name="unique_auditor_alert_period_code",
            ),
        ]
        indexes = [
            models.Index(fields=["estado", "severidad"], name="koru_alert_estado_sev"),
        ]

    def __str__(self):
        return f"[{self.severidad}] {self.main_character_name} | {self.codigo} | {self.estado}"


# ---------------------------------------------------------------------------
# Auditor — Fase 2: precios generales, snapshots y ciclo de vida
# ---------------------------------------------------------------------------

class KoruMarketPrice(models.Model):
    """Precio de mercado general por type_id (CCP ESI /markets/prices/ o Fuzzwork).
    Sustituye a eveuniverse_evemarketprice para valorar assets de cualquier tipo."""
    type_id        = models.IntegerField(unique=True, db_index=True)
    type_name      = models.CharField(max_length=255, default="", blank=True)
    average_price  = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    adjusted_price = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    updated_at     = models.DateTimeField(auto_now=True)

    # --- Jita (The Forge / Jita 4-4), para valorar regalos --------------------
    # `average_price` de la ESI NO es precio vendible: para un BPO es su valor
    # base, y por eso valorar assets con el a pelo inflo 610 B el patrimonio en
    # koru-desktop. Estas columnas traen el mercado REAL y se usan para los
    # rangos; `average_price` se queda al lado como contraste para la regla de
    # desviacion.
    jita_buy_max   = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True,
                                         help_text="Mejor orden de compra en Jita: lo que te darian por el")
    jita_sell_min  = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True,
                                         help_text="Orden de venta mas barata en Jita: lo que costaria comprarlo")
    jita_percentil = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True,
                                         help_text="Percentil 5% de venta. Se usa en vez del minimo pelado: "
                                                   "una sola orden troll de 1 ISK no debe decidir un rango")
    jita_ordenes   = models.IntegerField(null=True, blank=True, help_text="Numero de ordenes de venta detras del precio")
    jita_volumen   = models.BigIntegerField(null=True, blank=True, help_text="Unidades a la venta. Si es menor que lo regalado, el precio no aguanta")
    jita_fuente    = models.CharField(max_length=30, blank=True, default="", help_text="fuzzwork / esi")
    jita_consultado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = "Precio de mercado (Koru)"
        verbose_name_plural = "Precios de mercado (Koru)"

    def __str__(self):
        return f"{self.type_id} — {self.average_price}"


class CharacterValueSnapshot(models.Model):
    """Foto diaria de patrimonio (assets) y balance líquido por personaje.
    Base de las señales de liquidación / caída de patrimonio (Financiero/Fuga)."""
    character_id      = models.IntegerField(db_index=True)   # eveonline_evecharacter.character_id (EVE)
    main_character_id = models.IntegerField(db_index=True)
    snapshot_date     = models.DateField(db_index=True)
    asset_value       = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    wallet_balance    = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    item_count        = models.BigIntegerField(default=0)

    class Meta:
        verbose_name        = "Snapshot de patrimonio"
        verbose_name_plural = "Snapshots de patrimonio"
        constraints = [
            models.UniqueConstraint(fields=["character_id", "snapshot_date"],
                                    name="unique_value_snapshot"),
        ]
        indexes = [
            models.Index(fields=["main_character_id", "snapshot_date"], name="koru_valsnap_main_date"),
        ]

    def __str__(self):
        return f"{self.character_id} | {self.snapshot_date} | {self.asset_value}"


class CharacterOwnershipSnapshot(models.Model):
    """Foto diaria de ownership — al comparar días detecta PJ borrados y cambios de main."""
    snapshot_date     = models.DateField(db_index=True)
    character_id      = models.IntegerField(db_index=True)   # EVE character_id
    character_name    = models.CharField(max_length=100, default="")
    main_character_id = models.IntegerField(default=0)
    corporation_id    = models.IntegerField(default=0)

    class Meta:
        verbose_name        = "Snapshot de ownership"
        verbose_name_plural = "Snapshots de ownership"
        constraints = [
            models.UniqueConstraint(fields=["snapshot_date", "character_id"],
                                    name="unique_ownership_snapshot"),
        ]

    def __str__(self):
        return f"{self.snapshot_date} | {self.character_id}"


class CharacterLifecycleEvent(models.Model):
    """Evento de ciclo de vida derivado del diff de ownership / estados."""
    character_id      = models.IntegerField(db_index=True)
    character_name    = models.CharField(max_length=100, default="")
    main_character_id = models.IntegerField(db_index=True, default=0)
    evento  = models.CharField(max_length=30)  # entro_corp/salio_corp/borrado_auth/cambio_main
    fecha   = models.DateTimeField(db_index=True)
    estado_anterior = models.CharField(max_length=50, blank=True, default="")
    estado_nuevo    = models.CharField(max_length=50, blank=True, default="")
    notas   = models.TextField(blank=True, default="")

    class Meta:
        verbose_name        = "Evento de ciclo de vida"
        verbose_name_plural = "Eventos de ciclo de vida"
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["main_character_id", "fecha"], name="koru_lifecycle_main"),
        ]

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d} | {self.character_name} | {self.evento}"


# ---------------------------------------------------------------------------
# Tickets — espejo de Baserow (koru_tickets, T1)
# ---------------------------------------------------------------------------

class TicketsConfig(models.Model):
    """Config del sync de tickets desde Baserow (token, url) — singleton."""
    tag             = models.CharField(max_length=50, default="default", unique=True)
    baserow_base_url = models.CharField(max_length=255, default="https://rekipiloto.sinzg.synology.me")
    baserow_token    = models.CharField(max_length=255, blank=True, default="", help_text="Token de Baserow (solo lectura)")
    enabled          = models.BooleanField(default=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Configuración de Tickets"
        verbose_name_plural = "Configuración de Tickets"

    def __str__(self):
        return f"TicketsConfig[{self.tag}] — {'ON' if self.enabled else 'OFF'}"


class Ticket(models.Model):
    """Espejo unificado de un ticket de Baserow (cualquier tabla)."""

    TIPO_CHOICES = (
        ("reclutamiento", "Reclutamiento"),
        ("directores",    "A Directores"),
        ("asuntos",       "Asuntos Internos"),
        ("it",            "A IT"),
        ("soporte",       "A Soporte"),
    )

    tipo             = models.CharField(max_length=20, db_index=True, choices=TIPO_CHOICES)
    baserow_table_id = models.IntegerField(db_index=True)
    baserow_row_id   = models.IntegerField()

    numero           = models.CharField(max_length=30, blank=True, default="")   # "Nº"
    discord_ticket   = models.CharField(max_length=30, blank=True, default="")   # "Nº Ticket Discord"
    fecha            = models.DateField(null=True, blank=True)
    estado           = models.CharField(max_length=50, blank=True, default="")
    tipo_detalle     = models.CharField(max_length=100, blank=True, default="")  # el "Tipo" select de Baserow
    asunto           = models.TextField(blank=True, default="")

    main_character_name = models.CharField(max_length=100, blank=True, default="", db_index=True)
    main_character_id   = models.IntegerField(default=0, db_index=True)           # resuelto vía AA
    claim_name          = models.CharField(max_length=100, blank=True, default="")

    alerta_peligro   = models.BooleanField(default=False)
    visible_piloto   = models.BooleanField(default=False)  # flag "Visible para piloto" (solo Directores)

    extra            = models.JSONField(default=dict, blank=True)  # campos específicos (checks auditoría, fase, etc.)
    synced_at        = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Ticket (espejo)"
        verbose_name_plural = "Tickets (espejo)"
        ordering = ["-fecha", "-baserow_row_id"]
        constraints = [
            models.UniqueConstraint(fields=["baserow_table_id", "baserow_row_id"],
                                    name="unique_ticket_baserow"),
        ]
        indexes = [
            models.Index(fields=["tipo", "estado"],          name="koru_ticket_tipo_estado"),
            models.Index(fields=["main_character_id", "tipo"], name="koru_ticket_main_tipo"),
        ]

    def __str__(self):
        return f"[{self.tipo}] {self.numero} | {self.main_character_name} | {self.estado}"


# ---------------------------------------------------------------------------
# Auditor — Directores/CEO (D1): salud de corp longitudinal
# ---------------------------------------------------------------------------

class CorpHealthSnapshot(models.Model):
    """Foto mensual agregada de la salud de la corp (una fila por periodo)."""
    period                = models.CharField(max_length=7, unique=True, db_index=True)  # YYYY-MM
    n_miembros            = models.IntegerField(default=0)   # mains activos en el periodo
    altas                 = models.IntegerField(default=0)
    bajas                 = models.IntegerField(default=0)
    neto                  = models.IntegerField(default=0)
    churn_pct             = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    antiguedad_media_dias = models.IntegerField(default=0)
    n_verde               = models.IntegerField(default=0)
    n_amarillo            = models.IntegerField(default=0)
    n_naranja             = models.IntegerField(default=0)
    n_rojo                = models.IntegerField(default=0)
    cobertura_pct         = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    participacion_media   = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    incidentes            = models.IntegerField(default=0)   # awox/espias confirmados (fase Casos)
    indice_salud          = models.IntegerField(default=0)   # 0-100 compuesto
    detalle               = models.JSONField(default=dict, blank=True)
    computed_at           = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Salud de corp (snapshot)"
        verbose_name_plural = "Salud de corp (snapshots)"
        ordering = ["period"]

    def __str__(self):
        return f"{self.period} | {self.n_miembros} miembros | salud {self.indice_salud}"


class CohortRetention(models.Model):
    """Retencion por cohorte de entrada: de los que entraron en 'cohorte', cuantos siguen a +N meses."""
    cohorte      = models.CharField(max_length=7, db_index=True)  # mes de entrada YYYY-MM
    offset_meses = models.IntegerField()                          # 0,1,3,6,12
    base         = models.IntegerField(default=0)
    retenidos    = models.IntegerField(default=0)

    class Meta:
        verbose_name        = "Retencion por cohorte"
        verbose_name_plural = "Retencion por cohorte"
        ordering = ["cohorte", "offset_meses"]
        constraints = [
            models.UniqueConstraint(fields=["cohorte", "offset_meses"], name="uniq_cohort_offset"),
        ]

    def __str__(self):
        return f"{self.cohorte} +{self.offset_meses}m: {self.retenidos}/{self.base}"


class RecruitmentLink(models.Model):
    """Reclutador -> recluta, derivado del espejo de tickets de reclutamiento (D2)."""
    recluta_main_id = models.IntegerField(unique=True, db_index=True)
    recluta_name    = models.CharField(max_length=100, default="", blank=True)
    reclutador_name = models.CharField(max_length=100, default="", blank=True, db_index=True)
    fecha           = models.DateField(null=True, blank=True)
    ticket_numero   = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        verbose_name        = "Enlace de reclutamiento"
        verbose_name_plural = "Enlaces de reclutamiento"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.reclutador_name} -> {self.recluta_name}"


class SocialEdge(models.Model):
    """Arista de co-actividad entre dos mains (volaron en el mismo killmail) — D3."""
    main_a_id   = models.IntegerField(db_index=True)   # canónico: a < b
    main_b_id   = models.IntegerField(db_index=True)
    main_a_name = models.CharField(max_length=100, default="", blank=True)
    main_b_name = models.CharField(max_length=100, default="", blank=True)
    ventana     = models.CharField(max_length=20, default="90d", db_index=True)
    peso        = models.IntegerField(default=0)
    ultima_vez  = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name        = "Arista social"
        verbose_name_plural = "Aristas sociales"
        ordering = ["-peso"]
        constraints = [
            models.UniqueConstraint(fields=["main_a_id", "main_b_id", "ventana"], name="uniq_social_edge"),
        ]
        indexes = [models.Index(fields=["ventana", "peso"], name="koru_edge_ventana_peso")]

    def __str__(self):
        return f"{self.main_a_name} <-> {self.main_b_name} ({self.peso})"


# ---------------------------------------------------------------------------
# Tax lunar — control de contratos (F1: ingesta)
#
# Diseño en `Auth Reki/koru-tax-contratos-diseno.md`. Puntos clave:
#   - La deteccion PROPONE, el director DISPONE. Nada se da por pagado solo.
#   - Al validar se CONGELA una foto: los contratos de EVE se borran (ya hay
#     81.530 en estado `deleted`), asi que un saldo calculado en vivo haria
#     reaparecer como morosos a quienes si pagaron.
#   - Libro de saldos por piloto y mineral, no un contrato = un mes.
# ---------------------------------------------------------------------------

class MoonTaxRecipient(models.Model):
    """
    Destinatarios validos de un contrato de tax lunar.

    CONFIGURABLE A PROPOSITO, no una constante en el codigo: en la BD conviven
    contratos `item_exchange` a precio 0 dirigidos a Goonswarm Federation
    (1354830081), que NO son el tax de Rekium. Si el comparador no filtrase por
    destinatario, daria por pagada la deuda a quien pago en otro sitio.
    """
    entity_id   = models.BigIntegerField(unique=True, help_text="ID de la corp o personaje que recibe los contratos")
    entity_name = models.CharField(max_length=100, blank=True, default="")
    is_active   = models.BooleanField(default=True, db_index=True)
    expected_location_id = models.BigIntegerField(
        null=True, blank=True,
        help_text="Ubicacion donde se espera la entrega. Si el contrato viene de otro sitio se marca para revisar. "
                  "Vacio = no se comprueba.")
    expected_location_name = models.CharField(max_length=150, blank=True, default="")
    notes       = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        verbose_name        = "Tax lunar — destinatario válido"
        verbose_name_plural = "Tax lunar — destinatarios válidos"
        ordering            = ["entity_name"]

    def __str__(self):
        estado = "activo" if self.is_active else "inactivo"
        return f"{self.entity_name or self.entity_id} ({estado})"


class MoonTaxContract(models.Model):
    """
    Foto de un contrato detectado, ya deduplicado.

    OJO con `corptools_corporatecontract`: cada contrato esta repetido una vez
    por corp que lo ve (la PK `id` es varchar = corporation_id + contract_id),
    y sus items tambien. Hay que deduplicar por `contract_id` o cada piloto
    parecera haber pagado el doble. Ademas `issuer_id` vale 0 en TODAS las
    filas: el emisor sale de `issuer_name_id`.
    """
    ESTADO_DETECTADO  = "detectado"
    ESTADO_REVISAR    = "revisar"
    ESTADO_DESCARTADO = "descartado"
    ESTADOS = [
        (ESTADO_DETECTADO,  "Detectado"),
        (ESTADO_REVISAR,    "Revisar"),
        (ESTADO_DESCARTADO, "Descartado"),
    ]

    contract_id     = models.BigIntegerField(unique=True, db_index=True)

    issuer_id       = models.BigIntegerField(db_index=True, help_text="De issuer_name_id; issuer_id viene a 0 siempre")
    issuer_name     = models.CharField(max_length=100, blank=True, default="")
    main_char_id    = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Main al que se imputa; el emisor puede ser un alt")
    main_name       = models.CharField(max_length=100, blank=True, default="")

    assignee_id     = models.BigIntegerField(db_index=True)
    # Quien lo acepto en el juego. A diferencia de `issuer_id` (que vale 0 en las
    # 263.729 filas), `acceptor_id` SI trae el id de EVE correcto: de 167.595
    # contratos `finished`, ninguno lo tiene vacio ni sin fecha.
    acceptor_id     = models.BigIntegerField(null=True, blank=True, db_index=True)
    acceptor_name   = models.CharField(max_length=100, blank=True, default="")
    price           = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    reward          = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    volume          = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    contract_type   = models.CharField(max_length=20, blank=True, default="")
    esi_status      = models.CharField(max_length=25, blank=True, default="", help_text="status de la ESI: outstanding / finished / deleted...")

    start_location_id   = models.BigIntegerField(null=True, blank=True)
    start_location_name = models.CharField(max_length=150, blank=True, default="")

    date_issued     = models.DateTimeField(null=True, blank=True, db_index=True)
    date_accepted   = models.DateTimeField(null=True, blank=True)
    date_completed  = models.DateTimeField(null=True, blank=True)

    estado          = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_DETECTADO, db_index=True)

    # Banderas de anomalia -> el sistema marca, el director resuelve
    tiene_bruto     = models.BooleanField(default=False, help_text="Trae mineral sin comprimir (no se acepta: transporte inviable)")
    ubicacion_rara  = models.BooleanField(default=False, help_text="Entregado fuera de la ubicacion esperada")
    cobra_isk       = models.BooleanField(default=False, help_text="price o reward distintos de cero")
    items_ajenos    = models.BooleanField(default=False, help_text="Trae cosas que no son mineral lunar")
    aviso           = models.CharField(max_length=250, blank=True, default="")

    detected_at     = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Tax lunar — contrato"
        verbose_name_plural = "Tax lunar — contratos"
        ordering            = ["-date_issued"]
        indexes = [
            models.Index(fields=["main_char_id", "date_issued"], name="koru_mtc_main_fecha"),
            models.Index(fields=["estado", "date_issued"],       name="koru_mtc_estado_fecha"),
        ]

    @property
    def tiene_anomalias(self):
        return any([self.tiene_bruto, self.ubicacion_rara, self.cobra_isk, self.items_ajenos])

    def __str__(self):
        return f"#{self.contract_id} · {self.main_name or self.issuer_name} · {self.esi_status}"


class MoonTaxContractItem(models.Model):
    """Un ítem del contrato. `quantity`, nunca `raw_quantity` (ese marca copia/original de BPO)."""
    contract     = models.ForeignKey(MoonTaxContract, on_delete=models.CASCADE, related_name="items")
    type_id      = models.BigIntegerField(db_index=True)
    type_name    = models.CharField(max_length=150, blank=True, default="")
    quantity     = models.BigIntegerField(default=0)
    group_id     = models.IntegerField(null=True, blank=True, db_index=True)
    is_compressed = models.BooleanField(default=False)
    base_type_id = models.BigIntegerField(null=True, blank=True, db_index=True,
                                          help_text="Mineral base al que corresponde (comprime 1:1)")
    base_name    = models.CharField(max_length=150, blank=True, default="")

    class Meta:
        verbose_name        = "Tax lunar — ítem de contrato"
        verbose_name_plural = "Tax lunar — ítems de contrato"
        ordering            = ["-quantity"]
        constraints = [
            models.UniqueConstraint(fields=["contract", "type_id"], name="uniq_mtc_item"),
        ]

    def __str__(self):
        return f"{self.type_name} x{self.quantity:,}"


class MoonTaxLedger(models.Model):
    """
    Libro de saldos por piloto, período y mineral base.

    NO se empareja un contrato con un mes: se acumula lo que debe contra lo que
    ha entregado. Asi el sistema absorbe solo pagar dos meses juntos, partir el
    pago en varios contratos, pagar de mas o pagar en nombre de un alt.

    `validado` congela la fila: a partir de ahi es un asiento contable y deja de
    recalcularse aunque el contrato desaparezca de la ESI.
    """
    main_char_id  = models.BigIntegerField(db_index=True)
    main_name     = models.CharField(max_length=100, blank=True, default="")
    period        = models.CharField(max_length=7, db_index=True, help_text="YYYY-MM")

    base_type_id  = models.BigIntegerField(db_index=True)
    base_name     = models.CharField(max_length=150, blank=True, default="")
    group_id      = models.IntegerField(null=True, blank=True)

    unidades_minadas = models.BigIntegerField(default=0)
    tasa             = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="% aplicado")
    debe             = models.BigIntegerField(default=0, help_text="Comprimidos adeudados (el mineral lunar comprime 1:1)")
    entregado        = models.BigIntegerField(default=0, help_text="Comprimidos detectados en contratos")

    validado      = models.BooleanField(default=False, db_index=True)
    validado_por  = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL,
                                      related_name="moon_tax_ledger_validado")
    validado_at   = models.DateTimeField(null=True, blank=True)
    saldo_cerrado = models.BigIntegerField(default=0, help_text="Lo que el director dejo pendiente al validar; es esto lo que arrastra")
    notes         = models.TextField(blank=True, default="", help_text="Por que se acepto o no una compensacion entre minerales")

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Tax lunar — saldo"
        verbose_name_plural = "Tax lunar — saldos"
        ordering            = ["-period", "main_name", "base_name"]
        constraints = [
            models.UniqueConstraint(fields=["main_char_id", "period", "base_type_id"], name="uniq_mtl_saldo"),
        ]
        indexes = [
            models.Index(fields=["period", "validado"], name="koru_mtl_periodo_val"),
        ]

    @property
    def pendiente(self):
        """Lo que falta por entregar. Si esta validado manda el saldo que fijo el director."""
        if self.validado:
            return self.saldo_cerrado
        return max(self.debe - self.entregado, 0)

    def __str__(self):
        return f"{self.main_name} · {self.period} · {self.base_name}: {self.entregado:,}/{self.debe:,}"


class MoonFuelSnapshot(models.Model):
    """
    Foto diaria del combustible de una estructura.

    El consumo NO se declara: se DERIVA de datos que corptools ya tiene.

        consumo (bloques/hora) = bloques en el hangar / horas hasta fuel_expires

    Verificado el 2026-08-04 contra las tres Athanor de Rekium: las tres dan
    5,01 bloques/hora de forma independiente. Y se autocorrige solo — si apagan
    un servicio, `fuel_expires` se mueve y el consumo recalculado baja.

    Se guarda una foto AL DIA porque el combustible es un dato del momento: sin
    histórico no se puede imputar coste a una fractura pasada.
    """
    structure_id    = models.BigIntegerField(db_index=True)
    structure_name  = models.CharField(max_length=150, blank=True, default="")
    corporation_id  = models.IntegerField(null=True, blank=True, db_index=True)
    fecha           = models.DateField(db_index=True)

    fuel_type_id    = models.IntegerField(null=True, blank=True)
    fuel_type_name  = models.CharField(max_length=100, blank=True, default="")
    bloques         = models.BigIntegerField(default=0)
    fuel_expires    = models.DateTimeField(null=True, blank=True)

    horas_restantes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    consumo_hora    = models.DecimalField(max_digits=10, decimal_places=3, default=0,
                                          help_text="Bloques/hora derivados")
    precio_bloque   = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    coste_hora      = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    coste_dia       = models.DecimalField(max_digits=20, decimal_places=2, default=0)

    servicios       = models.CharField(max_length=255, blank=True, default="",
                                       help_text="Servicios online; explican el consumo")
    state           = models.CharField(max_length=25, blank=True, default="")
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Luna — foto de combustible"
        verbose_name_plural = "Luna — fotos de combustible"
        ordering            = ["-fecha", "structure_name"]
        constraints = [
            models.UniqueConstraint(fields=["structure_id", "fecha"], name="uniq_moon_fuel_dia"),
        ]
        indexes = [
            models.Index(fields=["fecha", "structure_id"], name="koru_mfs_fecha_str"),
        ]

    @property
    def coste_mes(self):
        return self.coste_dia * 30

    def __str__(self):
        return f"{self.structure_name or self.structure_id} · {self.fecha} · {self.consumo_hora} bl/h"


class MoonAllianceFee(models.Model):
    """
    Lo que la alianza cobra a la corp por CADA fractura.

    Es un coste real que no sale de ninguna API: lo declara un director. Se
    imputa por fractura, no por mes.

    `structure_id` vacio = tarifa por DEFECTO para todas las lunas. Una fila con
    structure_id concreto la sobrescribe (las alianzas suelen cobrar segun el
    tipo de luna). `valid_from` permite subir la tarifa sin reescribir el pasado.
    """
    structure_id     = models.BigIntegerField(
        null=True, blank=True, db_index=True,
        help_text="Vacio = tarifa por defecto para todas las lunas")
    structure_name   = models.CharField(max_length=150, blank=True, default="")
    isk_por_fractura = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    valid_from       = models.DateField(
        help_text="Desde cuando aplica. Las fracturas anteriores usan la tarifa vigente entonces.")
    notes            = models.CharField(max_length=200, blank=True, default="")
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Luna — tarifa de alianza"
        verbose_name_plural = "Luna — tarifas de alianza"
        ordering            = ["-valid_from", "structure_name"]
        constraints = [
            models.UniqueConstraint(fields=["structure_id", "valid_from"],
                                    name="uniq_moon_fee_desde"),
        ]

    def __str__(self):
        quien = self.structure_name or self.structure_id or "todas las lunas"
        return f"{quien} · {self.isk_por_fractura} ISK/fractura desde {self.valid_from}"


# ---------------------------------------------------------------------------
# Regalos de la fiesta — R1: aportaciones, valoracion y rangos
#
# Diseno completo en `Auth Reki/koru-regalos-navidad-diseno.md`. Los tres
# principios que vienen del tax lunar y aqui valen igual:
#   - La deteccion propone, el director dispone: el sistema estima y marca,
#     nunca decide cuanto vale un regalo.
#   - Al validar se congela una foto. Los contratos de EVE se borran (81.530
#     en `deleted`), asi que nada se recalcula en vivo.
#   - Resolver siempre a main: quien contrata sera un alt la mitad de las veces.
#
# Y el cuarto, propio de este modulo: el SORTEO es independiente de la
# APORTACION. Por eso aqui no hay nada de sorteos; eso es R3.
# ---------------------------------------------------------------------------

class GiftCampaign(models.Model):
    """Una fiesta. Acota la ventana en la que un contrato o una donacion cuentan."""
    ESTADO_BORRADOR = "borrador"
    ESTADO_ABIERTA  = "abierta"
    ESTADO_CERRADA  = "cerrada"
    ESTADOS = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_ABIERTA,  "Abierta"),
        (ESTADO_CERRADA,  "Cerrada"),
    ]

    # Que precio de Jita manda para los rangos. Por defecto el de venta: para un
    # regalo es lo mas honesto, porque es lo que se ahorra quien lo recibe.
    PRECIO_SELL = "jita_sell"
    PRECIO_BUY  = "jita_buy"
    PRECIO_MODOS = [
        (PRECIO_SELL, "Jita sell (lo que costaria comprarlo)"),
        (PRECIO_BUY,  "Jita buy (lo que te darian por el)"),
    ]

    nombre        = models.CharField(max_length=120, unique=True)
    estado        = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_BORRADOR, db_index=True)
    ventana_desde = models.DateTimeField(help_text="Las aportaciones anteriores a esta fecha no se detectan")
    ventana_hasta = models.DateTimeField(help_text="Ni las posteriores")
    fecha_evento  = models.DateField(null=True, blank=True, help_text="El dia de la fiesta")

    precio_modo        = models.CharField(max_length=20, choices=PRECIO_MODOS, default=PRECIO_SELL)
    usar_percentil     = models.BooleanField(default=True, help_text="Usar el percentil 5% en vez del minimo pelado")
    spread_max_pct     = models.DecimalField(max_digits=6, decimal_places=2, default=60.00,
                                             help_text="Spread buy/sell por encima del cual se marca para valorar a mano")
    desviacion_max_pct = models.DecimalField(max_digits=6, decimal_places=2, default=200.00,
                                             help_text="Desviacion frente a average_price por encima de la cual se marca")

    notes      = models.CharField(max_length=250, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Regalos — campaña"
        verbose_name_plural = "Regalos — campañas"
        ordering            = ["-ventana_desde"]

    def __str__(self):
        return f"{self.nombre} ({self.estado})"


class GiftRecipient(models.Model):
    """
    A donde hay que aportar para que cuente.

    CONFIGURABLE A PROPOSITO, igual que en el tax lunar: con el id en el codigo,
    el dia que cambie quien recoge esto se rompe en silencio.

    Ojo con el ISK: tiene que entrar en la cartera de la CORP. Si alguien dona a
    la cartera personal de un director, el corp audit de corptools no lo ve.
    """
    campaign    = models.ForeignKey(GiftCampaign, on_delete=models.CASCADE, related_name="recipients",
                                    null=True, blank=True,
                                    help_text="Vacio = vale para todas las campañas")
    entity_id   = models.BigIntegerField(db_index=True, help_text="ID de la corp o personaje que recibe")
    entity_name = models.CharField(max_length=100, blank=True, default="")
    is_active   = models.BooleanField(default=True, db_index=True)

    acepta_contratos = models.BooleanField(default=True)
    acepta_isk       = models.BooleanField(default=True)
    wallet_division  = models.IntegerField(null=True, blank=True,
                                           help_text="Division de la cartera de corp donde cuentan las donaciones. Vacio = cualquiera")

    expected_location_id   = models.BigIntegerField(null=True, blank=True,
                                                    help_text="Donde se espera el contrato. Vacio = no se comprueba")
    expected_location_name = models.CharField(max_length=150, blank=True, default="")
    notes       = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        verbose_name        = "Regalos — destinatario válido"
        verbose_name_plural = "Regalos — destinatarios válidos"
        ordering            = ["entity_name"]
        constraints = [
            models.UniqueConstraint(fields=["campaign", "entity_id"], name="uniq_gift_recipient"),
        ]

    def __str__(self):
        estado = "activo" if self.is_active else "inactivo"
        return f"{self.entity_name or self.entity_id} ({estado})"


class GiftTier(models.Model):
    """
    Rango de aportacion. El umbral se mide sobre la SUMA de lo aportado por el
    main (alts incluidos, ya resueltos).

    `papeletas` solo se usa si el sorteo decide ponderar por rango; un sorteo
    plano da una por cabeza. Esa decision es de R3, aqui solo se guarda.
    """
    campaign     = models.ForeignKey(GiftCampaign, on_delete=models.CASCADE, related_name="tiers")
    nombre       = models.CharField(max_length=60)
    umbral_min   = models.DecimalField(max_digits=22, decimal_places=2, default=0,
                                       help_text="Valor minimo aportado (ISK) para entrar en este rango")
    papeletas    = models.PositiveIntegerField(default=1)
    orden        = models.PositiveIntegerField(default=0, help_text="De menor a mayor")
    color        = models.CharField(max_length=20, blank=True, default="", help_text="Clase o hex para la UI")

    class Meta:
        verbose_name        = "Regalos — rango"
        verbose_name_plural = "Regalos — rangos"
        ordering            = ["campaign", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["campaign", "orden"],  name="uniq_gift_tier_orden"),
            models.UniqueConstraint(fields=["campaign", "nombre"], name="uniq_gift_tier_nombre"),
        ]

    def __str__(self):
        return f"{self.nombre} (desde {self.umbral_min})"


class GiftContribution(models.Model):
    """
    Lo que ha aportado una persona: un contrato de items o una donacion de ISK.

    Las trampas de `corptools_corporatecontract` son las mismas del tax lunar:
    cada contrato esta repetido una vez por corp que lo ve (deduplicar por
    `contract_id`), `issuer_id` vale 0 en TODAS las filas (el emisor sale de
    `issuer_name_id`) y `raw_quantity` negativo marca copia de blueprint.

    Para el ISK la cosa es mas limpia: en
    `corptools_corporationwalletjournalentry` el `first_party_id` SI viene
    relleno, y `entry_id` es la clave natural para no contar dos veces en una
    reingesta.
    """
    ORIGEN_CONTRATO = "contrato"
    ORIGEN_ISK      = "isk"
    ORIGENES = [
        (ORIGEN_CONTRATO, "Contrato de ítems"),
        (ORIGEN_ISK,      "Donación de ISK"),
    ]

    ESTADO_DETECTADA  = "detectada"
    ESTADO_VALIDADA   = "validada"
    ESTADO_REVISAR    = "revisar"
    ESTADO_DESCARTADA = "descartada"
    ESTADOS = [
        (ESTADO_DETECTADA,  "Detectada"),
        (ESTADO_VALIDADA,   "Validada"),
        (ESTADO_REVISAR,    "Revisar"),
        (ESTADO_DESCARTADA, "Descartada"),
    ]

    campaign     = models.ForeignKey(GiftCampaign, on_delete=models.CASCADE, related_name="contributions")
    origen       = models.CharField(max_length=15, choices=ORIGENES, db_index=True)

    # ★ Clave de deduplicacion: "c:<contract_id>" o "w:<entry_id>".
    # Se hace asi y NO con dos UniqueConstraint condicionales sobre contract_id /
    # entry_id porque MariaDB no soporta indices parciales: Django lo avisa en
    # `manage.py check` y NO crea la restriccion, asi que la unicidad se quedaria
    # en el aire justo donde mas duele (reingesta que cuenta dos veces el mismo
    # regalo). Con una sola clave de texto, la BD si la garantiza.
    fuente_key   = models.CharField(max_length=40, db_index=True,
                                    help_text='"c:<contract_id>" para contratos, "w:<entry_id>" para donaciones')

    donante_id   = models.BigIntegerField(db_index=True, help_text="Personaje que aporto (puede ser un alt)")
    donante_name = models.CharField(max_length=100, blank=True, default="")
    main_char_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    main_name    = models.CharField(max_length=100, blank=True, default="")

    # --- Foto del contrato (origen = contrato) -------------------------------
    contract_id         = models.BigIntegerField(null=True, blank=True, db_index=True)
    assignee_id         = models.BigIntegerField(null=True, blank=True, db_index=True)
    acceptor_id         = models.BigIntegerField(null=True, blank=True)
    acceptor_name       = models.CharField(max_length=100, blank=True, default="")
    contract_type       = models.CharField(max_length=20, blank=True, default="")
    esi_status          = models.CharField(max_length=25, blank=True, default="")
    price               = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    reward              = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    volume              = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    start_location_id   = models.BigIntegerField(null=True, blank=True)
    start_location_name = models.CharField(max_length=150, blank=True, default="")

    # --- Foto de la donacion (origen = isk) ----------------------------------
    entry_id        = models.BigIntegerField(null=True, blank=True, db_index=True,
                                             help_text="entry_id del journal: clave para no contar dos veces")
    wallet_division = models.IntegerField(null=True, blank=True)
    reason          = models.CharField(max_length=500, blank=True, default="",
                                       help_text="Lo que escribio el donante. Se enseña, no filtra: medio mundo lo deja vacio")

    fecha        = models.DateTimeField(null=True, blank=True, db_index=True, help_text="date_issued o date del journal")

    # --- Valoracion ----------------------------------------------------------
    # Se guardan los DOS numeros a proposito: el que dijo el mercado y el que
    # dijo una persona. Para los rangos manda el ajustado si existe, y la
    # pantalla enseña los dos para que se vea que hubo una decision humana.
    valor_estimado   = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    valor_ajustado   = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True)
    valor_fuente     = models.CharField(max_length=40, blank=True, default="",
                                        help_text="jita_sell / jita_buy / percentil / isk / manual")
    valor_consultado_en = models.DateTimeField(null=True, blank=True,
                                               help_text="Cuando se pregunto el precio. NO se recalcula: el precio justo es el del momento en que se aporto")

    estado       = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_DETECTADA, db_index=True)

    # --- Banderas: el sistema marca y explica, el director resuelve -----------
    requiere_valoracion = models.BooleanField(default=False, help_text="Algo no cuadra con el precio de mercado")
    ubicacion_rara      = models.BooleanField(default=False)
    cobra_isk           = models.BooleanField(default=False, help_text="price o reward distintos de cero")
    sin_main            = models.BooleanField(default=False, help_text="El donante no resuelve a ningun main")
    aviso               = models.CharField(max_length=250, blank=True, default="")

    validado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="gift_contributions_validadas")
    validado_en  = models.DateTimeField(null=True, blank=True)
    nota         = models.TextField(blank=True, default="", help_text="Por que se ajusto el valor o se valido asi")

    detected_at  = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Regalos — aportación"
        verbose_name_plural = "Regalos — aportaciones"
        ordering            = ["-fecha"]
        constraints = [
            models.UniqueConstraint(fields=["campaign", "fuente_key"], name="uniq_gift_fuente"),
        ]
        indexes = [
            models.Index(fields=["campaign", "main_char_id"], name="koru_gift_camp_main"),
            models.Index(fields=["campaign", "estado"],       name="koru_gift_camp_estado"),
        ]

    @property
    def valor_final(self):
        return self.valor_ajustado if self.valor_ajustado is not None else self.valor_estimado

    @property
    def tiene_anomalias(self):
        return any([self.requiere_valoracion, self.ubicacion_rara, self.cobra_isk, self.sin_main])

    def __str__(self):
        quien = self.main_name or self.donante_name or self.donante_id
        return f"{quien} · {self.get_origen_display()} · {self.valor_final}"


class GiftContributionItem(models.Model):
    """
    Un item del regalo. `quantity`, nunca `raw_quantity`.

    ★ `es_bpc`: un BPC NO se vende en el mercado (solo por contrato) y ADEMAS
    comparte typeID con su BPO, asi que preguntar precio por typeID le pone a la
    copia el precio del original. Eso infló 610 B el patrimonio en koru-desktop.
    El chivato en los items de contrato es el `raw_quantity` NEGATIVO. Un BPC
    va SIEMPRE a valoracion manual, nunca hereda precio.
    """
    contribution = models.ForeignKey(GiftContribution, on_delete=models.CASCADE, related_name="items")
    type_id      = models.BigIntegerField(db_index=True)
    type_name    = models.CharField(max_length=150, blank=True, default="")
    quantity     = models.BigIntegerField(default=0)
    group_id     = models.IntegerField(null=True, blank=True, db_index=True)
    category_id  = models.IntegerField(null=True, blank=True, db_index=True, help_text="9 = Blueprints")
    es_bpc       = models.BooleanField(default=False, help_text="raw_quantity negativo = copia de blueprint")

    precio_unitario = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True)
    valor_linea     = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    precio_fuente   = models.CharField(max_length=40, blank=True, default="")

    requiere_valoracion = models.BooleanField(default=False)
    motivo              = models.CharField(max_length=150, blank=True, default="",
                                           help_text="sin_ordenes / volumen_corto / spread / desviacion / bpc / categoria")

    class Meta:
        verbose_name        = "Regalos — ítem aportado"
        verbose_name_plural = "Regalos — ítems aportados"
        ordering            = ["-valor_linea"]
        constraints = [
            models.UniqueConstraint(fields=["contribution", "type_id"], name="uniq_gift_item"),
        ]

    def __str__(self):
        return f"{self.type_name} x{self.quantity:,}"


# ---------------------------------------------------------------------------
# Regalos — R3: sorteos
#
# ★ EL PRINCIPIO QUE ORDENA TODO ESTO: el sorteo es INDEPENDIENTE de la
# aportacion. Un sorteo no es "la lista de quien aporto": es un conjunto de
# PARTICIPANTES y una bolsa de PREMIOS, y cada uno de los dos se llena por
# filtro o a mano, indistintamente.
#
# Por eso las ruletas especiales del CEO —nombres elegidos por el, regalos
# exclusivos que no salen de nadie— no necesitan nada aparte: son un sorteo con
# roster manual y premios de origen `exclusivo`. Si esto se hubiera modelado
# como "sorteo = los que aportaron", habria que romperlo a martillazos.
#
# Y el roster se CONGELA al cerrar: si se recalculara en vivo, alguien que
# aporte entre dos tiradas apareceria a mitad del sorteo.
# ---------------------------------------------------------------------------

class RaffleRosterFilter(models.Model):
    """
    Preset de filtros para construir un roster, reutilizable entre sorteos.

    `spec` guarda los criterios en JSON (valor minimo aportado, states, corps,
    PvP del periodo, tax al dia...). El constructor los aplica, ENSEÑA a quien
    saca, y solo al fijar se escriben las filas de RaffleEntrant.
    """
    nombre     = models.CharField(max_length=80, unique=True)
    spec       = models.JSONField(default=dict)
    notes      = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Regalos — filtro de roster"
        verbose_name_plural = "Regalos — filtros de roster"
        ordering            = ["nombre"]

    def __str__(self):
        return self.nombre


class Raffle(models.Model):
    """
    Un sorteo: participantes congelados x bolsa de premios congelada.

    ★ LIMPIEZA DEMOSTRABLE. Al cerrar se genera una semilla y se publica su
    HASH; al sortear se guarda la semilla en claro. Cualquiera puede recomputar
    el resultado desde semilla + roster + bolsa y comprobar que nadie toco nada.
    Eso vale mas que la animacion: un sorteo discutible es peor que no tenerlo.

    El ganador se decide SIEMPRE en el servidor. La ruleta solo anima un
    resultado ya decidido; si lo eligiera el navegador, cualquiera con la
    consola abierta podria discutirlo.
    """
    TIPO_COMUNITARIO = "comunitario"
    TIPO_ESPECIAL    = "especial"
    TIPOS = [
        (TIPO_COMUNITARIO, "Comunitario"),
        (TIPO_ESPECIAL,    "Especial del CEO"),
    ]

    ESTADO_BORRADOR = "borrador"
    ESTADO_CERRADO  = "cerrado"
    ESTADO_SORTEADO = "sorteado"
    ESTADO_ANULADO  = "anulado"
    ESTADOS = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_CERRADO,  "Cerrado (semilla publicada)"),
        (ESTADO_SORTEADO, "Sorteado"),
        (ESTADO_ANULADO,  "Anulado"),
    ]

    campaign = models.ForeignKey(GiftCampaign, on_delete=models.CASCADE, related_name="raffles")
    nombre   = models.CharField(max_length=120)
    tipo     = models.CharField(max_length=20, choices=TIPOS, default=TIPO_COMUNITARIO, db_index=True)
    estado   = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_BORRADOR, db_index=True)
    orden    = models.PositiveIntegerField(default=0, help_text="Orden en el que se celebran")

    # Reglas, por sorteo
    ponderar_por_rango = models.BooleanField(
        default=True, help_text="Mas aportacion = mas papeletas. Desactivado: una por cabeza")
    excluir_propio_regalo = models.BooleanField(
        default=True, help_text="Que no te toque lo que tu aportaste (solo aplica a los comunitarios)")
    permitir_repetir_ganador = models.BooleanField(
        default=False, help_text="Si una persona puede llevarse mas de un premio del mismo sorteo")

    # Limpieza demostrable
    semilla      = models.CharField(max_length=64, blank=True, default="",
                                    help_text="En claro solo despues de sortear")
    semilla_hash = models.CharField(max_length=64, blank=True, default="",
                                    help_text="SHA-256 de la semilla, publicado AL CERRAR")
    cerrado_en   = models.DateTimeField(null=True, blank=True)
    sorteado_en  = models.DateTimeField(null=True, blank=True)

    anulado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="raffles_anulados")
    anulado_en  = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.CharField(max_length=250, blank=True, default="")

    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="raffles_creados")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Regalos — sorteo"
        verbose_name_plural = "Regalos — sorteos"
        ordering            = ["campaign", "orden", "id"]
        constraints = [
            models.UniqueConstraint(fields=["campaign", "nombre"], name="uniq_raffle_nombre"),
        ]

    @property
    def editable(self):
        """Mientras esta en borrador se puede tocar el roster y la bolsa."""
        return self.estado == self.ESTADO_BORRADOR

    def __str__(self):
        return f"{self.nombre} ({self.get_estado_display()})"


class RaffleEntrant(models.Model):
    """
    Un participante, congelado.

    `origen` distingue quien entro por filtro de quien entro a mano por
    MERITOS: la transparencia de por que esta cada nombre es lo que evita que
    el sorteo huela mal, asi que la insignia en pantalla es parte del diseño y
    no un adorno. El motivo es OBLIGATORIO en los manuales.
    """
    ORIGEN_FILTRO = "filtro"
    ORIGEN_MANUAL = "manual"
    ORIGENES = [
        (ORIGEN_FILTRO, "Por filtro"),
        (ORIGEN_MANUAL, "A mano (méritos)"),
    ]

    raffle       = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="entrants")
    main_char_id = models.BigIntegerField(db_index=True)
    main_name    = models.CharField(max_length=100, blank=True, default="")
    origen       = models.CharField(max_length=10, choices=ORIGENES, default=ORIGEN_FILTRO)
    motivo       = models.CharField(max_length=200, blank=True, default="",
                                    help_text="Obligatorio si entra a mano: por que esta aqui")
    papeletas    = models.PositiveIntegerField(default=1)
    rango_nombre = models.CharField(max_length=60, blank=True, default="",
                                    help_text="Rango congelado al fijar el roster")
    # Alguien de fuera: ni en la corp ni en el Auth, metido a dedo y resuelto
    # contra ESI. Lleva insignia propia en pantalla porque meter a un ajeno es
    # justo la decision que mas conviene que se vea.
    externo        = models.BooleanField(default=False, db_index=True,
                                         help_text="No existe en Alliance Auth: resuelto contra ESI")
    verificado_esi = models.DateTimeField(null=True, blank=True,
                                          help_text="Cuando se contrasto el nombre con ESI")
    valor_aportado = models.DecimalField(max_digits=22, decimal_places=2, default=0)
    anadido_por  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="raffle_entrants_anadidos")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Regalos — participante"
        verbose_name_plural = "Regalos — participantes"
        ordering            = ["main_name"]
        constraints = [
            models.UniqueConstraint(fields=["raffle", "main_char_id"], name="uniq_raffle_entrant"),
        ]

    def __str__(self):
        return f"{self.main_name} x{self.papeletas}"


class RafflePrize(models.Model):
    """
    Un premio de la bolsa.

    Dos origenes que conviven en el mismo sorteo:
      - `aportacion`: sale de una GiftContribution. Arrastra donante y valor.
        Un regalo solo puede estar en UNA bolsa (de ahi el OneToOne), o se
        sortearia dos veces lo mismo y quedaria feo en directo.
      - `exclusivo`: NO viene de ningun miembro. Lo pone el CEO. No requiere
        contrato previo ni aportacion detectada: es la via de las especiales.
    """
    ORIGEN_APORTACION = "aportacion"
    ORIGEN_EXCLUSIVO  = "exclusivo"
    ORIGENES = [
        (ORIGEN_APORTACION, "De una aportación"),
        (ORIGEN_EXCLUSIVO,  "Exclusivo (del CEO)"),
    ]

    raffle       = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="prizes")
    origen       = models.CharField(max_length=15, choices=ORIGENES, default=ORIGEN_APORTACION)
    contribution = models.OneToOneField(GiftContribution, on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name="prize")
    descripcion  = models.CharField(max_length=200, blank=True, default="")
    valor        = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True,
                                       help_text="Opcional en los exclusivos: enseñarlo invita a comparar")
    donante_name = models.CharField(max_length=100, blank=True, default="")
    orden        = models.PositiveIntegerField(default=0, help_text="Orden en que se sortea")

    # ★ EL FONDO. El ISK que aporta la gente NO es un premio: es un bote con el
    # que el CEO compra naves, y con el que el armador nivela los lotes. Este
    # campo dice CUANTO de este premio salio de ese bote.
    #
    # Es decimal y no un booleano a proposito: un lote lleva objetos MAS ISK de
    # mortero, asi que la parte pagada con el fondo es parcial. Con un si/no
    # habria que mentir en un sentido o en el otro.
    #
    # ⚠ Y es lo que evita CONTAR DOS VECES: comprar con el fondo es un TRASPASO,
    # no valor nuevo. Ese ISK ya se conto cuando entro como aportacion, asi que
    # no vuelve a sumar al total de la fiesta.
    isk_del_fondo = models.DecimalField(
        max_digits=22, decimal_places=2, default=0,
        help_text="Cuanto de este premio salio del fondo (ISK aportado). 0 = lo puso alguien de su bolsillo")

    # Para enseñar el render de EVE en la ruleta. Se intenta adivinar del texto
    # al crear el premio, y si no sale se puede poner a mano desde el admin.
    type_id = models.BigIntegerField(
        null=True, blank=True,
        help_text="type_id de EVE para la imagen del premio. Vacio = se enseña un icono generico")

    class Meta:
        verbose_name        = "Regalos — premio"
        verbose_name_plural = "Regalos — premios"
        ordering            = ["raffle", "orden", "id"]

    @property
    def etiqueta(self):
        if self.descripcion:
            return self.descripcion
        if self.contribution_id:
            return str(self.contribution)
        return f"Premio #{self.pk}"

    def __str__(self):
        return self.etiqueta


class RaffleDraw(models.Model):
    """
    El resultado de una tirada. Reproducible desde la semilla.

    `hash_usado` guarda el SHA-256 de "<semilla>:<premio_id>:<intento>" que
    decidio esta tirada: con eso, mas el roster y la bolsa congelados,
    cualquiera reproduce el sorteo entero sin fiarse de nosotros ni de Python.
    """
    raffle  = models.ForeignKey(Raffle, on_delete=models.CASCADE, related_name="draws")
    prize   = models.OneToOneField(RafflePrize, on_delete=models.CASCADE, related_name="draw")
    entrant = models.ForeignKey(RaffleEntrant, on_delete=models.CASCADE, related_name="draws")
    orden   = models.PositiveIntegerField(default=0)
    hash_usado = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Regalos — resultado de sorteo"
        verbose_name_plural = "Regalos — resultados de sorteo"
        ordering            = ["raffle", "orden"]

    def __str__(self):
        return f"{self.entrant.main_name} ← {self.prize.etiqueta}"
