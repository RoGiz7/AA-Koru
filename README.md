# AA-Koru (`koru-stats`)

App interna de **Rekium** para **Alliance Auth v5**: estadísticas, tax lunar,
auditoría de corp y tickets, integradas en el menú lateral de AA.

Lee los datos directamente de las tablas de **`corptools`** y los pinta con
Chart.js. Sin Grafana, sin Metabase, sin ingesta propia de ESI salvo donde se dice.

> Hermana del proyecto **koru-desktop** (la app de escritorio). Son cosas
> distintas: esta vive dentro del Auth, aquella en el PC del piloto.

## Qué trae

| Sección | URL | Qué hace |
|---|---|---|
| Estadísticas | `/koru/` | Top mineros y bounties de la corp del mes |
| Mi Dashboard | `/koru/personal/` | Minería por personaje y bounties diarios del usuario |
| Finanzas Corp | `/koru/corp/` | Dashboard de corp + kill feed y top enemigos |
| Tax Lunas | `/koru/lunas/` | Minado por luna, deuda por piloto, rendimiento de fracturas |
| Mi Tax Lunar | `/koru/lunas/mi/` | Lo que debe el piloto y el contrato listo para copiar |
| Gestión de cobro | `/koru/lunas/gestion/` | Contratos detectados, saldos y validación con nota |
| PvP | `/koru/pvp/` | Resumen, kill feed, actividad y ficha de piloto |
| Auditor | `/koru/auditor/` | Detección de patrones de comportamiento |
| Dirección | `/koru/auditor/corp/` | Salud de corp, reclutamiento, social y rentabilidad de lunas |
| Tickets | `/koru/tickets/` | Tickets de reclutamiento, dirección, AA e IT |
| Export CSV | `/koru/export/{resumen,pvp,ore}/` | Descarga con BOM UTF-8 para Excel |

El prefijo de URL lo registra el `UrlHook` como `^koru/`.

## Permisos

Todos cuelgan del modelo `General` (`koru_stats.*`):

| Permiso | Da acceso a |
|---|---|
| `basic_access` | Estadísticas y Mi Dashboard |
| `corp_finance_access` | Finanzas Corp |
| `moon_tax_access` | Tax Lunas |
| `moon_tax_admin` | Gestión del tax de lunas |
| `pvp_access` | Estadísticas PvP detalladas |
| `fc_access` | Panel FC/Director |
| `auditor_access` | Panel Auditor |
| `auditor_admin` | Configurar el Auditor, revisar/descartar alertas |
| `auditor_corp_health` | Panel de Salud de Corp (Directores/CEO) |
| `tickets_reclutamiento` · `tickets_directores` · `tickets_asuntos_internos` · `tickets_it` | Cada tipo de ticket |
| `tickets_admin` | Todos los tipos de ticket |

## Requisitos

- Alliance Auth **≥ 5.0**
- **`corptools`** instalado y con los módulos de audit al día — es la fuente de
  todos los datos de personaje y corp
- **`eve_sde`** para los datos estáticos de EVE
- **`moons`** para las fracturas y los observers de minería lunar

> `memberaudit` **no** se usa (está desactivado en el Auth de Rekium) y
> `eveuniverse` está sustituido por `eve_sde`.

## Instalación

```bash
sudo su allianceserver
source /home/allianceserver/venv/auth/bin/activate
pip install git+https://github.com/RoGiz7/AA-Koru.git
```

En `myauth/myauth/settings/local.py`:

```python
INSTALLED_APPS += ["koru_stats"]
```

Y después:

```bash
cd /home/allianceserver/myauth
python manage.py migrate
python manage.py collectstatic --noinput
exit
sudo supervisorctl restart myauth:
```

## Actualizar

```bash
sudo su allianceserver
source /home/allianceserver/venv/auth/bin/activate
pip install --upgrade git+https://github.com/RoGiz7/AA-Koru.git
cd /home/allianceserver/myauth
python manage.py migrate
python manage.py collectstatic --noinput
exit
sudo supervisorctl restart myauth:
```

> Comprobar qué versión hay instalada:
> `pip show koru-stats | head -2`

## Tareas periódicas

Se programan desde el admin de Django (django-celery-beat). Las principales:

| Tarea | Para qué |
|---|---|
| `run_koru_ore_and_summary` | Agregados mensuales de mineral y resumen por personaje |
| `update_ore_prices` | Precios de mineral, hielo, luna y gas (Fuzzwork) |
| `update_market_prices` | Precios genéricos por `type_id` (ESI `/markets/prices/`) |
| `fetch_pvp_from_zkillboard` | Kills y pérdidas desde zKillboard + ESI |
| `run_auditor_pipeline` | Scores y alertas del auditor |
| `snapshot_corp_health` · `snapshot_ownership` · `detect_lifecycle_events` | Fotos diarias para Dirección |
| `sync_moon_tax_contracts` | Detección de contratos de tax (lee `corptools`, sin ESI) |
| `rebuild_moon_tax_ledger` | Recalcula el libro de saldos del tax lunar |
| `snapshot_moon_fuel` | Combustible de las estructuras de luna |
| `sync_tickets` | Tickets desde el ecosistema n8n/Baserow |

## Versionado

La versión vive en **un solo sitio**: `koru_stats/__init__.py`. El `pyproject.toml`
la lee de ahí (`dynamic = ["version"]`), así que para publicar basta con subirla
ahí, commitear y etiquetar:

```bash
git tag v0.3.0
git push origin main --tags
```

Ver [CHANGELOG.md](CHANGELOG.md).

## Licencia

Código interno de Rekium. Todos los derechos reservados salvo acuerdo expreso.
