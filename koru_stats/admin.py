from django import forms
from django.contrib import admin
from django.utils import timezone
from allianceauth.eveonline.models import EveCorporationInfo

from .models import (
    TrackedCorporation, MoonTaxConfig, MoonTaxPayment,
    AuditorConfig, AuditorRiskScore, AuditorAlert,
    KoruMarketPrice, CharacterValueSnapshot,
    CharacterOwnershipSnapshot, CharacterLifecycleEvent,
    TicketsConfig, Ticket,
    MoonAllianceFee, MoonTaxRecipient,
    GiftCampaign, GiftRecipient, GiftTier,
    GiftContribution, GiftContributionItem,
)


# ---------------------------------------------------------------------------
# TrackedCorporation
# ---------------------------------------------------------------------------

def _corps_con_miembros():
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ci.corporation_id, ci.corporation_name
            FROM eveonline_evecorporationinfo ci
            JOIN eveonline_evecharacter ec ON ec.corporation_id = ci.corporation_id
            JOIN authentication_characterownership co ON co.character_id = ec.id
            ORDER BY ci.corporation_name
        """)
        return [(row[0], f"{row[1]} ({row[0]})") for row in cursor.fetchall()]


class TrackedCorporationForm(forms.ModelForm):
    corp_choice = forms.ChoiceField(
        choices=[],
        label="Corporación",
        required=True,
        help_text="Solo corps con personajes registrados en Auth"
    )

    class Meta:
        model  = TrackedCorporation
        fields = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "---------")] + _corps_con_miembros()
        self.fields["corp_choice"].choices = choices
        if self.instance and self.instance.pk:
            self.fields["corp_choice"].initial = self.instance.corporation_id

    def clean(self):
        cleaned = super().clean()
        corp_id = cleaned.get("corp_choice")
        if corp_id:
            try:
                corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
                cleaned["_corporation_id"]   = corp.corporation_id
                cleaned["_corporation_name"] = corp.corporation_name
            except EveCorporationInfo.DoesNotExist:
                raise forms.ValidationError("Corp no encontrada")
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.corporation_id   = self.cleaned_data["_corporation_id"]
        instance.corporation_name = self.cleaned_data["_corporation_name"]
        if commit:
            instance.save()
        return instance


@admin.register(TrackedCorporation)
class TrackedCorporationAdmin(admin.ModelAdmin):
    form          = TrackedCorporationForm
    list_display  = ("corporation_name", "corporation_id", "is_active")
    list_editable = ("is_active",)
    ordering      = ("corporation_name",)


# ---------------------------------------------------------------------------
# MoonTaxConfig
# ---------------------------------------------------------------------------

@admin.register(MoonTaxConfig)
class MoonTaxConfigAdmin(admin.ModelAdmin):
    list_display = ("tag", "ubiquitous_rate", "common_rate", "uncommon_rate", "rare_rate", "exceptional_rate", "is_active", "updated_at")
    list_editable = ("ubiquitous_rate", "common_rate", "uncommon_rate", "rare_rate", "exceptional_rate", "is_active")
    readonly_fields = ("updated_at",)

    fieldsets = (
        ("Identificación", {
            "fields": ("tag", "is_active", "updated_at")
        }),
        ("Tasas por tier (%)", {
            "description": "Porcentaje sobre el valor de mercado del ore minado.",
            "fields": (
                ("ubiquitous_rate", "common_rate"),
                ("uncommon_rate",   "rare_rate"),
                ("exceptional_rate",),
            )
        }),
    )


# ---------------------------------------------------------------------------
# MoonTaxPayment
# ---------------------------------------------------------------------------

@admin.register(MoonTaxPayment)
class MoonTaxPaymentAdmin(admin.ModelAdmin):
    list_display  = ("character_name", "period", "isk_owed_display", "is_paid", "paid_by", "paid_at")
    list_filter   = ("is_paid", "period")
    search_fields = ("character_name", "period")
    readonly_fields = ("character_id", "character_name", "period", "isk_owed", "created_at", "updated_at", "paid_by", "paid_at")
    ordering = ("-period", "character_name")

    fieldsets = (
        ("Piloto", {
            "fields": ("character_name", "character_id", "period", "isk_owed")
        }),
        ("Estado del pago", {
            "fields": ("is_paid", "paid_by", "paid_at", "notes")
        }),
        ("Auditoría", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def isk_owed_display(self, obj):
        v = float(obj.isk_owed)
        if v >= 1e9:
            return f"{v/1e9:.2f} B ISK"
        if v >= 1e6:
            return f"{v/1e6:.2f} M ISK"
        return f"{v:,.0f} ISK"
    isk_owed_display.short_description = "ISK owed"

    def has_add_permission(self, request):
        return False  # Solo se crean desde la vista, no manualmente


# ---------------------------------------------------------------------------
# Auditor
# ---------------------------------------------------------------------------

@admin.register(AuditorConfig)
class AuditorConfigAdmin(admin.ModelAdmin):
    list_display    = ("tag", "modo_calibracion", "calibracion_hasta", "umbral_amarillo", "umbral_naranja", "umbral_rojo", "updated_at")
    readonly_fields = ("updated_at", "blue_alliance_ids", "blue_corp_ids", "own_alliance_ids", "own_corp_ids")

    fieldsets = (
        ("Identificación", {
            "fields": ("tag", "updated_at"),
        }),
        ("Calibración", {
            "description": "En modo calibración el Auditor calcula y muestra, pero NO envía avisos a Discord.",
            "fields": ("modo_calibracion", "calibracion_hasta"),
        }),
        ("Pesos por dimensión (0–1, idealmente suman 1)", {
            "fields": (
                ("w_pvp", "w_ciclo", "w_espias"),
                ("w_fuga", "w_huecos", "w_financiero"),
            ),
        }),
        ("Umbrales de nivel (0–100)", {
            "fields": (("umbral_amarillo", "umbral_naranja", "umbral_rojo"),),
        }),
        ("Parámetros de señales", {
            "fields": ("token_stale_dias", "inactividad_dias", "donacion_externa_min"),
        }),
        ("States del core AA (qué cuenta como azul / propio)", {
            "fields": ("blue_state_ids", "own_state_ids"),
        }),
        ("Standings cacheados (auto, vía sync_blue_standings)", {
            "classes": ("collapse",),
            "fields": ("blue_alliance_ids", "blue_corp_ids", "own_alliance_ids", "own_corp_ids"),
        }),
        ("Assets / staging (Fase 2)", {
            "classes": ("collapse",),
            "fields": ("staging_location_ids",),
        }),
    )


@admin.register(AuditorRiskScore)
class AuditorRiskScoreAdmin(admin.ModelAdmin):
    list_display  = ("main_character_name", "period", "risk_total", "nivel",
                     "score_pvp", "score_ciclo", "score_espias", "score_fuga", "score_huecos", "score_financiero", "computed_at")
    list_filter   = ("nivel", "period", "corporation_id")
    search_fields = ("main_character_name",)
    ordering      = ("-period", "-risk_total")
    readonly_fields = ("computed_at",)

    def has_add_permission(self, request):
        return False  # Lo crea la task


@admin.register(AuditorAlert)
class AuditorAlertAdmin(admin.ModelAdmin):
    list_display  = ("created_at", "severidad", "familia", "codigo", "main_character_name", "period", "estado", "revisada_por")
    list_filter   = ("estado", "severidad", "familia", "period")
    search_fields = ("main_character_name", "codigo")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        return False  # Las crea la task


@admin.register(KoruMarketPrice)
class KoruMarketPriceAdmin(admin.ModelAdmin):
    list_display  = ("type_id", "type_name", "average_price", "adjusted_price", "updated_at")
    search_fields = ("type_id", "type_name")
    ordering      = ("type_id",)

    def has_add_permission(self, request):
        return False  # La puebla la task


@admin.register(CharacterValueSnapshot)
class CharacterValueSnapshotAdmin(admin.ModelAdmin):
    list_display  = ("snapshot_date", "character_id", "main_character_id", "asset_value", "wallet_balance", "item_count")
    list_filter   = ("snapshot_date",)
    search_fields = ("character_id", "main_character_id")
    ordering      = ("-snapshot_date",)

    def has_add_permission(self, request):
        return False


@admin.register(CharacterOwnershipSnapshot)
class CharacterOwnershipSnapshotAdmin(admin.ModelAdmin):
    list_display  = ("snapshot_date", "character_id", "character_name", "main_character_id", "corporation_id")
    list_filter   = ("snapshot_date",)
    search_fields = ("character_id", "character_name")
    ordering      = ("-snapshot_date",)

    def has_add_permission(self, request):
        return False


@admin.register(CharacterLifecycleEvent)
class CharacterLifecycleEventAdmin(admin.ModelAdmin):
    list_display  = ("fecha", "evento", "character_name", "main_character_id", "estado_anterior", "estado_nuevo")
    list_filter   = ("evento",)
    search_fields = ("character_name", "character_id")
    ordering      = ("-fecha",)

    def has_add_permission(self, request):
        return False


@admin.register(TicketsConfig)
class TicketsConfigAdmin(admin.ModelAdmin):
    list_display    = ("tag", "enabled", "baserow_base_url", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (None, {
            "fields": ("tag", "enabled", "updated_at"),
        }),
        ("Baserow", {
            "description": "URL base y token de SOLO LECTURA de Baserow para el sync de tickets.",
            "fields": ("baserow_base_url", "baserow_token"),
        }),
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ("tipo", "numero", "discord_ticket", "main_character_name",
                     "estado", "tipo_detalle", "claim_name", "visible_piloto", "alerta_peligro", "fecha")
    list_filter   = ("tipo", "estado", "visible_piloto", "alerta_peligro")
    search_fields = ("main_character_name", "numero", "discord_ticket", "asunto")
    ordering      = ("-fecha", "-baserow_row_id")
    readonly_fields = ("synced_at",)

    def has_add_permission(self, request):
        return False  # La puebla el sync


# ---------------------------------------------------------------------------
# Tax lunar — destinatarios y tarifa de la alianza
# ---------------------------------------------------------------------------

@admin.register(MoonTaxRecipient)
class MoonTaxRecipientAdmin(admin.ModelAdmin):
    list_display  = ("entity_name", "entity_id", "is_active", "expected_location_name")
    list_filter   = ("is_active",)
    search_fields = ("entity_name", "entity_id")


@admin.register(MoonAllianceFee)
class MoonAllianceFeeAdmin(admin.ModelAdmin):
    list_display  = ("_quien", "isk_por_fractura", "valid_from", "notes")
    list_filter   = ("valid_from",)
    search_fields = ("structure_name", "notes")
    fields        = ("structure_id", "structure_name", "isk_por_fractura",
                     "valid_from", "notes")

    @admin.display(description="Aplica a")
    def _quien(self, obj):
        return obj.structure_name or obj.structure_id or "TODAS las lunas (por defecto)"


# ---------------------------------------------------------------------------
# Regalos de la fiesta — R1
#
# La campana, los destinatarios y los rangos se montan aqui. Las aportaciones
# las detecta `sync_gift_contributions`, asi que se ven pero no se crean a mano.
# ---------------------------------------------------------------------------

class GiftTierInline(admin.TabularInline):
    model = GiftTier
    extra = 0
    fields = ("orden", "nombre", "umbral_min", "papeletas", "color")
    ordering = ("orden",)


class GiftRecipientInline(admin.TabularInline):
    model = GiftRecipient
    extra = 0
    fields = ("entity_name", "entity_id", "is_active", "acepta_contratos",
              "acepta_isk", "wallet_division", "expected_location_id",
              "expected_location_name")


@admin.register(GiftCampaign)
class GiftCampaignAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "estado", "ventana_desde", "ventana_hasta",
                     "fecha_evento", "precio_modo")
    list_filter   = ("estado",)
    search_fields = ("nombre",)
    inlines       = (GiftRecipientInline, GiftTierInline)
    fieldsets = (
        (None, {"fields": ("nombre", "estado", "ventana_desde", "ventana_hasta", "fecha_evento", "notes")}),
        ("Valoración", {
            "fields": ("precio_modo", "usar_percentil", "spread_max_pct", "desviacion_max_pct"),
            "description": "Jita sell es lo que costaría comprar el regalo; es lo que se ahorra quien lo "
                           "recibe. El percentil evita que una sola orden rara decida un rango. Los dos "
                           "umbrales marcan para valorar a mano, nunca descartan.",
        }),
    )


@admin.register(GiftRecipient)
class GiftRecipientAdmin(admin.ModelAdmin):
    list_display  = ("entity_name", "entity_id", "campaign", "is_active",
                     "acepta_contratos", "acepta_isk", "wallet_division")
    list_filter   = ("is_active", "campaign")
    search_fields = ("entity_name", "entity_id")


@admin.register(GiftTier)
class GiftTierAdmin(admin.ModelAdmin):
    list_display  = ("nombre", "campaign", "umbral_min", "papeletas", "orden")
    list_filter   = ("campaign",)
    ordering      = ("campaign", "orden")


class GiftContributionItemInline(admin.TabularInline):
    model = GiftContributionItem
    extra = 0
    can_delete = False
    fields = ("type_name", "quantity", "es_bpc", "precio_unitario",
              "valor_linea", "precio_fuente", "requiere_valoracion", "motivo")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(GiftContribution)
class GiftContributionAdmin(admin.ModelAdmin):
    list_display  = ("_quien", "campaign", "origen", "valor_estimado",
                     "valor_ajustado", "estado", "fecha", "aviso")
    list_filter   = ("campaign", "origen", "estado", "requiere_valoracion")
    search_fields = ("main_name", "donante_name", "fuente_key")
    date_hierarchy = "fecha"
    inlines = (GiftContributionItemInline,)
    # Se puede ajustar el valor y validar; lo que detecto el sistema se mira,
    # no se reescribe: el precio es el del momento en que se aporto.
    readonly_fields = ("campaign", "origen", "fuente_key", "donante_id", "donante_name",
                       "main_char_id", "main_name", "contract_id", "assignee_id",
                       "acceptor_id", "acceptor_name", "contract_type", "esi_status",
                       "price", "reward", "volume", "start_location_id",
                       "start_location_name", "entry_id", "wallet_division", "reason",
                       "fecha", "valor_estimado", "valor_fuente", "valor_consultado_en",
                       "requiere_valoracion", "ubicacion_rara", "cobra_isk", "sin_main",
                       "aviso", "detected_at", "updated_at")

    def has_add_permission(self, request):
        return False  # Las detecta el sync

    @admin.display(description="Quién", ordering="main_name")
    def _quien(self, obj):
        return obj.main_name or obj.donante_name or obj.donante_id
