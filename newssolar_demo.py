# -*- coding: utf-8 -*-
"""
Blueprint démo NEWS-SOLAR — Technologie HST
=============================================
Module ISOLÉ — n'impacte aucun autre fichier du programme.
Accessible uniquement aux utilisateurs connectés.

Routes :
  GET  /newssolar/          → Dashboard & présentation technologie
  GET  /newssolar/simulation → Simulateur multi-énergies interactif
  POST /newssolar/api/simulate → API calcul de simulation (JSON)
"""

import math
from flask import Blueprint, render_template_string, request, jsonify, redirect, session
from auth_database import get_auth_db

newssolar_demo_bp = Blueprint('newssolar_demo', __name__, url_prefix='/newssolar')

# ── Helpers auth ─────────────────────────────────────────────────────────────

def _get_current_user():
    """Retourne le dict utilisateur depuis le session_token, ou None."""
    token = session.get('session_token') or request.cookies.get('session_token')
    if not token:
        return None
    try:
        conn = get_auth_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.name, u.company
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.session_token = ?
              AND s.expires_at > datetime('now')
              AND u.is_active = 1
        """, (token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'id': row[0], 'email': row[1], 'name': row[2], 'company': row[3]}
    except Exception as e:
        print(f"[NEWSSOLAR] Erreur auth check: {e}")
    return None

def _require_auth():
    """Retourne (user, None) ou (None, redirect_response)."""
    user = _get_current_user()
    if not user:
        return None, redirect('/auth/login')
    return user, None

# ── Moteur de simulation HST ─────────────────────────────────────────────────

# Données d'irradiance fictives mais réalistes par région (kWh/m²/an DNI)
IRRADIANCE_DB = {
    "france_sud":       {"dnI": 1800, "ghi": 1600, "label": "France Sud (Valence, Marseille, Nice)"},
    "france_nord":      {"dnI": 1100, "ghi": 1050, "label": "France Nord (Paris, Lille)"},
    "espagne":          {"dnI": 2200, "ghi": 1900, "label": "Espagne / Portugal"},
    "maroc_algerie":    {"dnI": 2600, "ghi": 2200, "label": "Maroc / Algérie"},
    "moyen_orient":     {"dnI": 2800, "ghi": 2400, "label": "Moyen-Orient / Arabie Saoudite"},
    "afrique_subsah":   {"dnI": 2400, "ghi": 2100, "label": "Afrique sub-saharienne"},
    "inde":             {"dnI": 2100, "ghi": 1900, "label": "Inde / Pakistan"},
    "australie":        {"dnI": 2500, "ghi": 2100, "label": "Australie"},
    "amerique_latine":  {"dnI": 2300, "ghi": 2000, "label": "Amérique Latine (Chili, Brésil)"},
    "europe_centrale":  {"dnI": 1300, "ghi": 1200, "label": "Europe Centrale (Allemagne, Pologne)"},
}

def simulate_hst(surface_ha, region, converter_type, outputs_requested):
    """
    Moteur de calcul HST NEWS-SOLAR.
    surface_ha      : surface en hectares
    region          : clé dans IRRADIANCE_DB
    converter_type  : 'mono' (35%) | 'bi' (60%) | 'photostatic' (42%)
    outputs_requested : liste de 'heat','cold','electricity','h2','nh3'
    Retourne un dict de résultats énergétiques annuels.
    """
    irr = IRRADIANCE_DB.get(region, IRRADIANCE_DB["france_sud"])
    dni_kwh_m2y = irr["dnI"]

    # Paramètres HST
    CAPTATION_EFFICIENCY  = 0.95    # 95% captation hyper-concentration
    SURFACE_M2            = surface_ha * 10_000
    ACTIVE_RATIO          = 1.0     # toute la surface est collectrice (film réfléchissant)
    THERMAL_STORAGE_EFF   = 0.98    # batterie thermique rendement 98%
    HOURS_PER_YEAR        = 8760

    # Énergie thermique brute captée (MWh/an)
    raw_thermal_mwh = (dni_kwh_m2y * SURFACE_M2 * CAPTATION_EFFICIENCY * ACTIVE_RATIO) / 1000

    # Puissance crête thermique (MWc)
    peak_thermal_mwc = (dns := dni_kwh_m2y * CAPTATION_EFFICIENCY / 1000) * SURFACE_M2 / 1000
    # Plus simple :
    peak_thermal_mwc = (dni_kwh_m2y / 1000) * SURFACE_M2 * CAPTATION_EFFICIENCY / 1000

    stored_thermal_mwh = raw_thermal_mwh * THERMAL_STORAGE_EFF

    # Rendement du convertisseur électrique
    conv_eff = {"mono": 0.35, "bi": 0.60, "photostatic": 0.42}.get(converter_type, 0.35)

    # Productions annuelles
    electricity_mwh = stored_thermal_mwh * conv_eff if 'electricity' in outputs_requested else 0
    heat_mwh        = stored_thermal_mwh * (1 - conv_eff) * 0.85 if 'heat' in outputs_requested else 0
    cold_mwh        = stored_thermal_mwh * 0.30 if 'cold' in outputs_requested else 0   # cycle absorption

    # H₂ : 50 kWh électrolyse → 1 kg H₂ (rendement ~60% électrolyseur HTE)
    h2_kg_per_year  = (electricity_mwh * 1000 / 50) * 0.60 if 'h2' in outputs_requested else 0
    nh3_tons        = h2_kg_per_year * 0.18 / 1000 if 'nh3' in outputs_requested else 0   # ratio H₂→NH₃

    # Températures fictives de la batterie selon heure du jour (démo)
    temp_data = _fictitious_temp_profile()

    # Comparatif vs PV (même surface) — 900 kWc/ha, rendement spécifique GHI × PR 85%
    # Valeur réaliste : ~1 250–1 600 kWh/kWc/an selon région
    INSTALLED_KWC_PER_HA = 900          # Capacité installée typique parc PV au sol
    pv_specific_yield    = irr["ghi"] * 0.85  # kWh/kWc/an (PR 85% onduleur+câbles+temp)
    pv_electricity_mwh   = (INSTALLED_KWC_PER_HA * surface_ha * pv_specific_yield) / 1000
    electricity_ratio    = (electricity_mwh / pv_electricity_mwh) if pv_electricity_mwh > 0 else 0

    # CAPEX estimatif (€)
    capex_eur = surface_ha * 1_200_000  # ~1,2M€/ha ordre de grandeur

    # Revenus annuels estimés (€) — tarif moyen 80€/MWh
    revenue_elec  = electricity_mwh  * 80
    revenue_heat  = heat_mwh         * 65
    revenue_cold  = cold_mwh         * 55
    revenue_h2    = h2_kg_per_year   * 6    # ~6€/kg H₂ vert
    revenue_total = revenue_elec + revenue_heat + revenue_cold + revenue_h2

    roi_years = (capex_eur / revenue_total) if revenue_total > 0 else 0
    revenue_25y = revenue_total * 25

    return {
        "region_label":        irr["label"],
        "surface_ha":          surface_ha,
        "raw_thermal_mwh":     round(raw_thermal_mwh, 1),
        "stored_thermal_mwh":  round(stored_thermal_mwh, 1),
        "electricity_mwh":     round(electricity_mwh, 1),
        "heat_mwh":            round(heat_mwh, 1),
        "cold_mwh":            round(cold_mwh, 1),
        "h2_kg":               round(h2_kg_per_year, 0),
        "nh3_tons":            round(nh3_tons, 1),
        "pv_electricity_mwh":  round(pv_electricity_mwh, 1),
        "electricity_ratio":   round(electricity_ratio, 1),
        "capex_eur":           round(capex_eur, 0),
        "revenue_annual_eur":  round(revenue_total, 0),
        "roi_years":           round(roi_years, 1),
        "revenue_25y":         round(revenue_25y, 0),
        "converter_type":      converter_type,
        "conv_eff_pct":        int(conv_eff * 100),
        "hours_per_year":      HOURS_PER_YEAR,
        "temp_profile":        temp_data,
    }

def _fictitious_temp_profile():
    """Profil de température fictif illustratif (batterie thermique HST, 24h)."""
    hours = list(range(24))
    # Batterie maintient une haute T° stable, légère variation jour/nuit
    temps_battery = []
    temps_output  = []
    for h in hours:
        # Batterie : maintenue entre 800°C et 920°C
        t_bat = 860 + 60 * math.sin((h - 14) * math.pi / 12)
        # Sortie process : selon demande (simulation fluctuation)
        t_out = 350 + 80 * math.sin((h - 10) * math.pi / 12) + (20 if 8 <= h <= 18 else -10)
        temps_battery.append(round(t_bat, 1))
        temps_output.append(round(t_out, 1))
    return {"hours": hours, "battery_temp": temps_battery, "output_temp": temps_output}

# ── HTML commun ———————————————————————————————————————————————————————————————

_BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root {
    --bg:       #07091a;
    --card:     #0d1024;
    --border:   rgba(255,255,255,0.07);
    --gold:     #FFB700;
    --gold2:    #FF8C00;
    --green:    #10b981;
    --blue:     #3b82f6;
    --purple:   #8b5cf6;
    --red:      #ef4444;
    --text:     #e2e8f0;
    --muted:    #8892a4;
    --ns-blue:  #0066CC;
    --ns-orange:#FF6600;
}
body { background: var(--bg); color: var(--text); font-family: 'Inter',sans-serif; min-height:100vh; overflow-y: auto; }
a { color: var(--gold); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── HEADER ── */
.ns-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.9rem 2rem;
    background: rgba(13,16,36,0.95);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
    backdrop-filter: blur(12px);
}
.ns-logo { height: 42px; object-fit: contain; }
.ns-badge {
    background: linear-gradient(135deg, var(--ns-blue), var(--ns-orange));
    color: #fff; font-size: 0.72rem; font-weight: 700;
    padding: 0.2rem 0.65rem; border-radius: 20px; letter-spacing: 0.05em;
}
.ns-nav { display: flex; gap: 1rem; align-items: center; }
.ns-nav a {
    color: var(--muted); font-size: 0.85rem; font-weight: 500;
    padding: 0.4rem 0.8rem; border-radius: 8px; transition: all 0.2s;
}
.ns-nav a:hover, .ns-nav a.active { background: rgba(255,255,255,0.06); color: var(--text); text-decoration:none; }
.ns-nav a.cta {
    background: linear-gradient(135deg, var(--ns-blue), var(--ns-orange));
    color: #fff !important; padding: 0.4rem 1rem;
}

/* ── CARDS ── */
.card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 1.5rem;
}
.card-title { font-size: 0.75rem; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }

/* ── KPI ── */
.kpi-value { font-size: 2rem; font-weight: 800; line-height: 1.1; }
.kpi-unit  { font-size: 0.82rem; color: var(--muted); margin-left: 0.2rem; }
.kpi-delta { font-size: 0.78rem; margin-top: 0.3rem; }
.gold  { color: var(--gold); }
.green { color: var(--green); }
.blue  { color: var(--blue); }
.purple{ color: var(--purple); }
.orange{ color: var(--ns-orange); }

/* ── GRID ── */
.grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 1rem; }
.grid-3 { display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; }
.grid-2 { display: grid; grid-template-columns: repeat(2,1fr); gap: 1rem; }
@media(max-width:900px){ .grid-4,.grid-3 { grid-template-columns: repeat(2,1fr); } }
@media(max-width:600px){ .grid-4,.grid-3,.grid-2 { grid-template-columns: 1fr; } }

/* ── SECTION HERO ── */
.hero {
    background: linear-gradient(135deg, rgba(0,102,204,0.12) 0%, rgba(255,102,0,0.08) 100%);
    border-bottom: 1px solid var(--border);
    padding: 2.5rem 2rem 2rem;
}
.hero h1 { font-size: 1.8rem; font-weight: 800; margin-bottom: 0.4rem; }
.hero p   { color: var(--muted); font-size: 0.92rem; max-width: 650px; line-height: 1.6; }
.tagline  { display: inline-block; background: rgba(0,102,204,0.15); border: 1px solid rgba(0,102,204,0.3); color: var(--blue); font-size: 0.78rem; font-weight: 600; padding: 0.25rem 0.7rem; border-radius: 20px; margin-bottom: 0.8rem; }

/* ── TABLE ── */
table { width:100%; border-collapse: collapse; }
th { font-size:0.75rem; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.06em; padding:0.5rem 0.8rem; border-bottom:1px solid var(--border); text-align:left; }
td { padding:0.6rem 0.8rem; font-size:0.88rem; border-bottom:1px solid rgba(255,255,255,0.04); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.03); }

/* ── PROGRESS BAR ── */
.bar-wrap { background: rgba(255,255,255,0.06); border-radius: 4px; height: 6px; margin-top: 0.5rem; overflow:hidden; }
.bar-fill  { height: 100%; border-radius: 4px; transition: width 1s ease; }

/* ── FORMS ── */
.form-group { margin-bottom: 1rem; }
label.fl { font-size:0.8rem; font-weight:600; color:var(--muted); display:block; margin-bottom:0.3rem; }
select, input[type=number], input[type=text] {
    width:100%; background:rgba(255,255,255,0.04); border:1px solid var(--border);
    border-radius:10px; color:var(--text); padding:0.6rem 0.9rem; font-size:0.9rem; font-family:inherit;
    transition: border-color 0.2s;
}
select:focus, input:focus { border-color: var(--ns-blue); outline:none; }
option { background:#0d1024; }
.checkbox-group { display:flex; flex-wrap:wrap; gap:0.6rem; }
.cb-label { display:flex; align-items:center; gap:0.4rem; font-size:0.85rem; cursor:pointer; }
.cb-label input { width:auto; }

/* ── BUTTONS ── */
.btn { display:inline-flex; align-items:center; gap:0.4rem; padding:0.65rem 1.4rem; border-radius:10px; font-size:0.9rem; font-weight:600; border:none; cursor:pointer; font-family:inherit; transition:all 0.25s; }
.btn-primary { background:linear-gradient(135deg,var(--ns-blue),var(--ns-orange)); color:#fff; box-shadow:0 4px 14px rgba(0,102,204,0.3); }
.btn-primary:hover { transform:translateY(-2px); box-shadow:0 6px 20px rgba(0,102,204,0.4); }
.btn-ghost { background:rgba(255,255,255,0.05); color:var(--muted); border:1px solid var(--border); }
.btn-ghost:hover { background:rgba(255,255,255,0.09); color:var(--text); }

/* ── TEMP GAUGE ── */
.gauge-row { display:flex; align-items:center; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid rgba(255,255,255,0.04); }
.gauge-label { font-size:0.82rem; color:var(--muted); }
.gauge-val   { font-size:1.1rem; font-weight:700; }
.temp-high   { color: #ff4444; }
.temp-mid    { color: var(--gold); }
.temp-low    { color: var(--green); }

/* ── DISCLAIMER ── */
.disclaimer { background:rgba(255,183,0,0.06); border:1px solid rgba(255,183,0,0.15); border-radius:10px; padding:0.7rem 1rem; font-size:0.78rem; color:var(--muted); margin-top:0.5rem; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); border-radius: 5px; }
::-webkit-scrollbar-thumb { background: rgba(0,102,204,0.55); border-radius: 5px; border: 2px solid transparent; background-clip: content-box; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,102,204,0.85); border: 2px solid transparent; background-clip: content-box; }
* { scrollbar-width: thin; scrollbar-color: rgba(0,102,204,0.55) rgba(255,255,255,0.05); }

/* ── LAYOUT ── */
.main-content { max-width:1400px; margin:0 auto; padding:1.5rem 2rem; }
.section-title { font-size:1rem; font-weight:700; margin-bottom:1rem; display:flex; align-items:center; gap:0.5rem; }
.section-title::after { content:''; flex:1; height:1px; background:var(--border); margin-left:0.5rem; }
"""

_HEADER_HTML = """
<header class="ns-header">
    <div style="display:flex;align-items:center;gap:0.8rem">
        <img src="/static/images/logo_news_solar.png" alt="NEWS SOLAR" class="ns-logo">
        <span class="ns-badge">DÉMO INVESTISSEURS</span>
    </div>
    <nav class="ns-nav">
        <a href="/newssolar/" id="nav-dash">Tableau de bord</a>
        <a href="/newssolar/simulation" id="nav-sim">Simulateur HST</a>
        <a href="/auth/logout" class="btn-ghost" style="font-size:0.8rem;padding:0.35rem 0.8rem;border-radius:8px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);color:#8892a4;">Déconnexion</a>
    </nav>
</header>
"""

# ── ROUTES ───────────────────────────────────────────────────────────────────

@newssolar_demo_bp.route('/')
def dashboard():
    user, redir = _require_auth()
    if redir:
        return redir

    # Simulation par défaut : 1 ha, France Sud, convertisseur mono-étagé
    default = simulate_hst(1.0, "france_sud", "mono", ["electricity","heat","cold","h2"])

    return render_template_string(DASHBOARD_TEMPLATE,
                                  user=user,
                                  sim=default,
                                  irradiance_regions=IRRADIANCE_DB)

@newssolar_demo_bp.route('/simulation')
def simulation_page():
    user, redir = _require_auth()
    if redir:
        return redir
    return render_template_string(SIMULATION_TEMPLATE,
                                  user=user,
                                  irradiance_regions=IRRADIANCE_DB)

@newssolar_demo_bp.route('/api/simulate', methods=['POST'])
def api_simulate():
    user, redir = _require_auth()
    if redir:
        return jsonify({"error": "Non authentifié"}), 401

    data            = request.get_json(force=True)
    surface_ha      = float(data.get('surface_ha', 1.0))
    region          = data.get('region', 'france_sud')
    converter_type  = data.get('converter_type', 'mono')
    outputs         = data.get('outputs', ['electricity','heat'])

    surface_ha = max(0.1, min(surface_ha, 10000))

    result = simulate_hst(surface_ha, region, converter_type, outputs)
    return jsonify(result)

# ── TEMPLATES HTML ────────────────────────────────────────────────────────────

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEWS-SOLAR — Tableau de bord</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>""" + _BASE_CSS + """
/* Layout 2 colonnes : panneau gauche fixe + contenu droit scrollable */
.dash-layout {
  display: flex; height: calc(100vh - 62px); overflow: hidden;
}
.dash-sidebar {
  width: 300px; min-width: 280px; max-width: 320px;
  background: var(--card); border-right: 1px solid var(--border);
  overflow-y: auto; padding: 1.2rem;
  flex-shrink: 0;
}
.dash-main {
  flex: 1; overflow-y: auto; padding: 1.5rem 2rem;
}
.sim-label { font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--muted); margin-bottom:0.3rem; display:block; }
.sim-badge {
  display:inline-block; background:rgba(0,102,204,0.12); border:1px solid rgba(0,102,204,0.25);
  color: var(--blue); font-size:0.72rem; font-weight:700; padding:0.18rem 0.55rem; border-radius:20px; margin-bottom:0.8rem;
}
.sidebar-section { margin-bottom:1rem; padding-bottom:1rem; border-bottom:1px solid var(--border); }
.sidebar-section:last-child { border-bottom:none; }
.spin { animation:spin 0.8s linear infinite; display:inline-block; }
@keyframes spin { to { transform:rotate(360deg); } }
.updating { opacity: 0.5; transition: opacity 0.2s; }
</style>
</head>
<body>
""" + _HEADER_HTML + """
<script>document.getElementById('nav-dash').classList.add('active');</script>

<div class="dash-layout">

  <!-- ══ PANNEAU GAUCHE : PARAMÈTRES ══ -->
  <aside class="dash-sidebar">
    <div style="margin-bottom:1rem">
      <span class="sim-badge">⚙️ Simulateur interactif</span>
      <div style="font-size:0.8rem;color:var(--muted);line-height:1.5">Modifiez les paramètres — le tableau de bord se met à jour instantanément.</div>
    </div>

    <div class="sidebar-section">
      <label class="sim-label">🌍 Région</label>
      <select id="p_region">
        {% for key, val in irradiance_regions.items() %}
        <option value="{{ key }}" {% if key=='france_sud' %}selected{% endif %}>{{ val.label }}</option>
        {% endfor %}
      </select>
    </div>

    <div class="sidebar-section">
      <label class="sim-label">📐 Surface (hectares)</label>
      <input type="number" id="p_surface" value="1" min="0.1" max="10000" step="0.5">
      <div style="display:flex;justify-content:space-between;margin-top:0.5rem;gap:0.3rem">
        <button class="btn btn-ghost" style="flex:1;padding:0.3rem;font-size:0.75rem" onclick="setHa(0.5)">0.5 ha</button>
        <button class="btn btn-ghost" style="flex:1;padding:0.3rem;font-size:0.75rem" onclick="setHa(1)">1 ha</button>
        <button class="btn btn-ghost" style="flex:1;padding:0.3rem;font-size:0.75rem" onclick="setHa(5)">5 ha</button>
        <button class="btn btn-ghost" style="flex:1;padding:0.3rem;font-size:0.75rem" onclick="setHa(10)">10 ha</button>
      </div>
    </div>

    <div class="sidebar-section">
      <label class="sim-label">⚡ Convertisseur</label>
      <select id="p_converter">
        <option value="mono">Mono-étagé — 35% rdt</option>
        <option value="bi">Bi-étagé — 60% rdt</option>
        <option value="photostatic">Photostatique — 42% rdt</option>
      </select>
    </div>

    <div class="sidebar-section">
      <label class="sim-label">🧩 Sorties actives</label>
      <div class="checkbox-group" style="flex-direction:column;gap:0.45rem">
        <label class="cb-label"><input type="checkbox" value="electricity" checked> ⚡ Électricité</label>
        <label class="cb-label"><input type="checkbox" value="heat" checked> 🔥 Chaleur process</label>
        <label class="cb-label"><input type="checkbox" value="cold" checked> ❄️ Froid industriel</label>
        <label class="cb-label"><input type="checkbox" value="h2" checked> 🌿 Hydrogène H₂</label>
        <label class="cb-label"><input type="checkbox" value="nh3"> 🏭 Ammoniac NH₃</label>
      </div>
    </div>

    <button class="btn btn-primary" style="width:100%" onclick="runSim()">
      <span id="btn-icon">▶</span> Calculer
    </button>

    <div id="sim-info" style="margin-top:0.8rem;font-size:0.75rem;color:var(--muted);text-align:center"></div>
  </aside>

  <!-- ══ CONTENU PRINCIPAL DYNAMIQUE ══ -->
  <main class="dash-main" id="dash-main">

    <!-- Hero summary -->
    <div style="background:linear-gradient(135deg,rgba(0,102,204,0.1),rgba(255,102,0,0.07));border:1px solid var(--border);border-radius:16px;padding:1.2rem 1.5rem;margin-bottom:1.5rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1rem">
      <div>
        <span class="tagline">⚡ Technologie HST — Breveté NEWS-SOLAR</span>
        <div id="hero-desc" style="font-size:0.9rem;color:var(--muted);margin-top:0.3rem">
          Région : <strong class="text-white" id="hero-region">{{ sim.region_label }}</strong> ·
          Surface : <strong id="hero-surface">{{ sim.surface_ha }} ha</strong> ·
          Convertisseur : <strong id="hero-conv">{{ sim.converter_type }} ({{ sim.conv_eff_pct }}%)</strong>
        </div>
      </div>
      <div style="text-align:right">
        <div style="font-size:0.75rem;color:var(--muted)">Production continue</div>
        <div style="font-size:1.6rem;font-weight:800;color:var(--gold)">8 760 h/an</div>
      </div>
    </div>

    <!-- KPI production -->
    <div class="section-title" style="margin-top:0">⚡ Production annuelle estimée</div>
    <div class="grid-4" style="margin-bottom:1.5rem" id="kpi-production">
      <div class="card">
        <div class="card-title">Électricité</div>
        <div class="kpi-value gold"><span id="kpi-elec">{{ '{:,.0f}'.format(sim.electricity_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
        <div class="bar-wrap"><div class="bar-fill" id="bar-elec" style="width:{{ [sim.electricity_mwh / sim.stored_thermal_mwh * 100, 100] | min | round | int }}%; background:var(--gold)"></div></div>
        <div class="kpi-delta muted" id="kpi-elec-info" style="margin-top:0.6rem">Convertisseur {{ sim.converter_type }} — {{ sim.conv_eff_pct }}% rdt</div>
      </div>
      <div class="card">
        <div class="card-title">Chaleur process</div>
        <div class="kpi-value orange"><span id="kpi-heat">{{ '{:,.0f}'.format(sim.heat_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
        <div class="bar-wrap"><div class="bar-fill" id="bar-heat" style="width:{{ [sim.heat_mwh / sim.stored_thermal_mwh * 100, 100] | min | round | int }}%; background:var(--ns-orange)"></div></div>
        <div class="kpi-delta muted" style="margin-top:0.6rem">Chaleur directe THT disponible</div>
      </div>
      <div class="card">
        <div class="card-title">Froid industriel</div>
        <div class="kpi-value blue"><span id="kpi-cold">{{ '{:,.0f}'.format(sim.cold_mwh) }}</span><span class="kpi-unit">MWh/an</span></div>
        <div class="bar-wrap"><div class="bar-fill" id="bar-cold" style="width:30%; background:var(--blue)"></div></div>
        <div class="kpi-delta muted" style="margin-top:0.6rem">Cycle absorption thermique</div>
      </div>
      <div class="card">
        <div class="card-title">Hydrogène H₂</div>
        <div class="kpi-value green"><span id="kpi-h2">{{ '{:,.0f}'.format(sim.h2_kg) }}</span><span class="kpi-unit">kg/an</span></div>
        <div class="bar-wrap"><div class="bar-fill" id="bar-h2" style="width:55%; background:var(--green)"></div></div>
        <div class="kpi-delta muted" style="margin-top:0.6rem">Électrolyse HTE rdt 60%</div>
      </div>
    </div>

    <!-- Financiers & Comparatif -->
    <div class="grid-3" style="margin-bottom:1.5rem">
      <div class="card">
        <div class="card-title">💰 CAPEX estimatif</div>
        <div class="kpi-value gold"><span id="kpi-capex">{{ '{:,.0f}'.format(sim.capex_eur / 1000) }}</span><span class="kpi-unit">k€</span></div>
        <div style="margin-top:1rem">
          <div class="gauge-row"><span class="gauge-label">Revenus annuels</span><span class="gauge-val green"><span id="kpi-rev">{{ '{:,.0f}'.format(sim.revenue_annual_eur / 1000) }}</span> k€</span></div>
          <div class="gauge-row"><span class="gauge-label">ROI estimé</span><span class="gauge-val gold"><span id="kpi-roi">{{ sim.roi_years }}</span> ans</span></div>
          <div class="gauge-row"><span class="gauge-label">CA cumulé 25 ans</span><span class="gauge-val orange"><span id="kpi-ca25">{{ '{:,.0f}'.format(sim.revenue_25y / 1000) }}</span> k€</span></div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">📊 Comparatif vs PV standard (même surface)</div>
        <div class="kpi-value gold">×<span id="kpi-ratio">{{ sim.electricity_ratio }}</span><span class="kpi-unit">productivité élec.</span></div>
        <div style="margin-top:1rem">
          <div class="gauge-row"><span class="gauge-label">PV standard (900 kWc/ha)</span><span class="gauge-val muted"><span id="kpi-pv">{{ '{:,.0f}'.format(sim.pv_electricity_mwh) }}</span> MWh/an</span></div>
          <div class="gauge-row"><span class="gauge-label">NEWS-SOLAR HST</span><span class="gauge-val green"><span id="kpi-hst">{{ '{:,.0f}'.format(sim.electricity_mwh) }}</span> MWh/an</span></div>
          <div class="gauge-row"><span class="gauge-label">Heures production HST</span><span class="gauge-val gold">8 760 h/an</span></div>
          <div class="gauge-row"><span class="gauge-label">PV heures production</span><span class="gauge-val muted">~1 500 h/an</span></div>
        </div>
      </div>
      <div class="card">
        <div class="card-title">🌡️ Températures batterie thermique (illustratif)</div>
        <canvas id="tempChart" height="150"></canvas>
        <div class="disclaimer">⚠️ Données T°C illustratives — Non contractuel.</div>
      </div>
    </div>

    <!-- Tableau techno + chaine -->
    <div class="grid-2" style="margin-bottom:1.5rem">
      <div class="card">
        <div class="section-title">🔩 Paramètres technologiques HST</div>
        <table>
          <tr><th>Paramètre</th><th>Valeur</th></tr>
          <tr><td>Rendement captation solaire</td><td class="gold">95%</td></tr>
          <tr><td>Rendement batterie thermique</td><td class="gold">98%</td></tr>
          <tr><td>Facteur concentration</td><td class="blue">×15 000</td></tr>
          <tr><td>Densité énergétique batterie</td><td class="orange">1,3 – 1,5 MWh/m³</td></tr>
          <tr><td>Température max batterie</td><td class="temp-high">3 000°C</td></tr>
          <tr><td>Perte thermique / jour</td><td class="green">1%</td></tr>
          <tr><td>MTBF convertisseur</td><td class="green">> 220 000 h</td></tr>
          <tr><td>Durée de vie installation</td><td class="green">> 25 ans</td></tr>
          <tr><td>Production annuelle continue</td><td class="gold">8 760 h/an</td></tr>
          <tr><td>Poids film collecteur</td><td>300 g/m²</td></tr>
        </table>
      </div>
      <div class="card">
        <div class="section-title">⚡ Chaîne énergétique HST</div>
        <div style="padding:0.5rem 0">
          {% set steps = [
            ('1', 'Champ solaire', 'Micro-réflecteurs hyper-concentration ×15 000 · Film optique 95%', 'gold'),
            ('2', 'Absorbeur', 'Reçoit le flux THT concentré · Transfert vers batterie', 'orange'),
            ('3', 'Batterie thermique', "Stockage jusqu'à 3 000°C · 1,3 MWh/m³ · 98% rendement · Continu 8760h/an", 'blue'),
            ('4', 'Convertisseur', 'Thermodynamique linéaire · 35% (mono) ou 60% (bi-étagé)', 'purple'),
            ('5', 'Multi-output', 'Chaleur · Froid · Électricité · H₂/NH₃ · SAF/e-SAF', 'green'),
          ] %}
          {% for num, title, desc, color in steps %}
          <div style="display:flex;gap:0.8rem;align-items:flex-start;padding:0.6rem 0;border-bottom:1px solid var(--border)">
            <div style="width:28px;height:28px;min-width:28px;background:rgba(255,255,255,0.06);border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.82rem;color:var(--{{ color }})">{{ num }}</div>
            <div>
              <div style="font-weight:600;font-size:0.88rem;color:var(--{{ color }})">{{ title }}</div>
              <div style="font-size:0.78rem;color:var(--muted);margin-top:0.15rem">{{ desc }}</div>
            </div>
          </div>
          {% endfor %}
        </div>
      </div>
    </div>

    <div class="disclaimer" style="margin-bottom:1.5rem">
      ⚠️ <strong>Document confidentiel — Démo investisseurs.</strong> Estimations à titre illustratif. Non contractuel. NEWS-SOLAR © 2026 — Brevets internationaux déposés.
    </div>

  </main>
</div>

<script>
// ── Graphique température initial ──────────────────────────────────────────
const tp0 = {{ sim.temp_profile | tojson }};
const tempChart = new Chart(document.getElementById('tempChart'), {
  type: 'line',
  data: {
    labels: tp0.hours.map(h => h+'h'),
    datasets: [
      { label: 'Batterie (°C)', data: tp0.battery_temp, borderColor:'#ff4444', backgroundColor:'rgba(255,68,68,0.07)', tension:0.4, pointRadius:0, borderWidth:2 },
      { label: 'Sortie process (°C)', data: tp0.output_temp, borderColor:'#FFB700', backgroundColor:'rgba(255,183,0,0.07)', tension:0.4, pointRadius:0, borderWidth:2 }
    ]
  },
  options: {
    plugins:{ legend:{ labels:{ color:'#8892a4', font:{ size:10 } } } },
    scales:{
      x:{ ticks:{ color:'#8892a4', font:{size:9} }, grid:{ color:'rgba(255,255,255,0.04)' } },
      y:{ ticks:{ color:'#8892a4', font:{size:9} }, grid:{ color:'rgba(255,255,255,0.04)' } }
    },
    animation:{ duration:600 }, maintainAspectRatio:true
  }
});

// ── Helpers ────────────────────────────────────────────────────────────────
function fmt(n){ return Number(n).toLocaleString('fr-FR', {maximumFractionDigits:0}); }
function setHa(v){ document.getElementById('p_surface').value = v; runSim(); }

// ── Simulation dynamique ───────────────────────────────────────────────────
let _debounce = null;
function schedSim(){ clearTimeout(_debounce); _debounce = setTimeout(runSim, 500); }

['p_region','p_converter'].forEach(id => document.getElementById(id).addEventListener('change', runSim));
document.getElementById('p_surface').addEventListener('input', schedSim);
document.querySelectorAll('.checkbox-group input').forEach(cb => cb.addEventListener('change', runSim));

async function runSim(){
  const btn = document.getElementById('btn-icon');
  const info = document.getElementById('sim-info');
  const main = document.getElementById('dash-main');
  btn.textContent = '⟳'; btn.classList.add('spin');
  main.classList.add('updating');
  info.textContent = 'Calcul en cours...';

  const outputs = [...document.querySelectorAll('.checkbox-group input:checked')].map(c => c.value);
  const body = {
    region:         document.getElementById('p_region').value,
    surface_ha:     parseFloat(document.getElementById('p_surface').value) || 1,
    converter_type: document.getElementById('p_converter').value,
    outputs:        outputs.length ? outputs : ['electricity']
  };

  try {
    const r = await fetch('/newssolar/api/simulate', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)
    });
    const d = await r.json();
    applyResults(d, body);
    info.textContent = 'Mis à jour ✓';
  } catch(e) {
    info.textContent = 'Erreur de calcul';
  } finally {
    btn.textContent = '▶'; btn.classList.remove('spin');
    main.classList.remove('updating');
  }
}

function applyResults(d, params){
  // Hero
  document.getElementById('hero-region').textContent  = d.region_label;
  document.getElementById('hero-surface').textContent = d.surface_ha + ' ha';
  const convLabel = {mono:'mono (35%)', bi:'bi-étagé (60%)', photostatic:'photostatique (42%)'}[params.converter_type] || params.converter_type;
  document.getElementById('hero-conv').textContent = convLabel;

  // KPI production
  const therm = d.stored_thermal_mwh || 1;
  document.getElementById('kpi-elec').textContent = fmt(d.electricity_mwh);
  document.getElementById('bar-elec').style.width = Math.min(d.electricity_mwh / therm * 100, 100) + '%';
  document.getElementById('kpi-elec-info').textContent = 'Convertisseur ' + params.converter_type + ' — ' + d.conv_eff_pct + '% rdt';
  document.getElementById('kpi-heat').textContent = fmt(d.heat_mwh);
  document.getElementById('bar-heat').style.width = Math.min(d.heat_mwh / therm * 100, 100) + '%';
  document.getElementById('kpi-cold').textContent = fmt(d.cold_mwh);
  document.getElementById('kpi-h2').textContent   = fmt(d.h2_kg);

  // Financiers
  document.getElementById('kpi-capex').textContent = fmt(d.capex_eur / 1000);
  document.getElementById('kpi-rev').textContent   = fmt(d.revenue_annual_eur / 1000);
  document.getElementById('kpi-roi').textContent   = d.roi_years;
  document.getElementById('kpi-ca25').textContent  = fmt(d.revenue_25y / 1000);

  // Comparatif PV
  document.getElementById('kpi-ratio').textContent = d.electricity_ratio;
  document.getElementById('kpi-pv').textContent    = fmt(d.pv_electricity_mwh);
  document.getElementById('kpi-hst').textContent   = fmt(d.electricity_mwh);
}
</script>
</body></html>
"""

SIMULATION_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NEWS-SOLAR — Simulateur HST</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.2/dist/chart.umd.min.js"></script>
<style>""" + _BASE_CSS + """
.result-panel { display:none; }
.result-panel.visible { display:block; }
.spin { animation: spin 1s linear infinite; display:inline-block; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
""" + _HEADER_HTML + """
<script>document.getElementById('nav-sim').classList.add('active');</script>

<div class="hero">
  <div style="max-width:1400px;margin:0 auto">
    <span class="tagline">🔬 Simulateur interactif — Technologie HST NEWS-SOLAR</span>
    <h1>Calculez votre production <span class="gold">multi-énergies</span></h1>
    <p>Estimez la production annuelle de chaleur, froid, électricité et hydrogène vert pour votre projet, grâce au moteur de simulation basé sur la technologie HST NEWS-SOLAR.</p>
  </div>
</div>

<div class="main-content">
<div class="grid-2">
  <!-- PANNEAU PARAMÈTRES -->
  <div class="card">
    <div class="section-title">⚙️ Paramètres de simulation</div>
    <form id="simForm">
      <div class="form-group">
        <label class="fl">Région / localisation</label>
        <select name="region" id="sel_region">
          {% for key, val in irradiance_regions.items() %}
          <option value="{{ key }}" {% if key=='france_sud' %}selected{% endif %}>{{ val.label }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="form-group">
        <label class="fl">Surface installée (hectares)</label>
        <input type="number" name="surface_ha" id="inp_surface" value="1" min="0.1" max="10000" step="0.1">
        <div style="font-size:0.75rem;color:var(--muted);margin-top:0.3rem">1 ha = 10 000 m² · Toiture, ombrière ou terrain proximal</div>
      </div>
      <div class="form-group">
        <label class="fl">Type de convertisseur électrique</label>
        <select name="converter_type" id="sel_converter">
          <option value="mono">Mono-étagé — rendement 35%</option>
          <option value="bi">Bi-étagé — rendement 60% (haute performance)</option>
          <option value="photostatic">PhotoStatique multi-jonctions — rendement 42%</option>
        </select>
      </div>
      <div class="form-group">
        <label class="fl">Énergies souhaitées en sortie</label>
        <div class="checkbox-group">
          <label class="cb-label"><input type="checkbox" name="outputs" value="electricity" checked> ⚡ Électricité</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="heat" checked> 🔥 Chaleur</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="cold"> ❄️ Froid</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="h2"> 💧 H₂</label>
          <label class="cb-label"><input type="checkbox" name="outputs" value="nh3"> 🌿 NH₃</label>
        </div>
      </div>
      <button type="submit" class="btn btn-primary" id="btnSim" style="width:100%">
        ▶ Lancer la simulation
      </button>
    </form>
  </div>

  <!-- PANNEAU RÉSULTATS -->
  <div>
    <div id="placeholder" class="card" style="text-align:center;padding:3rem;color:var(--muted)">
      <div style="font-size:2.5rem;margin-bottom:0.8rem">🔬</div>
      <div style="font-weight:600;margin-bottom:0.4rem">Configurez les paramètres</div>
      <div style="font-size:0.85rem">Les résultats s'afficheront ici après simulation</div>
    </div>

    <div id="resultPanel" class="result-panel">
      <div class="card" style="margin-bottom:1rem">
        <div class="card-title" id="res_region">—</div>
        <div class="grid-2" id="res_kpis" style="gap:0.8rem;margin-top:0.6rem"></div>
      </div>
      <div class="card" style="margin-bottom:1rem">
        <div class="card-title">Production comparée vs PV standard</div>
        <canvas id="chartCompare" height="160"></canvas>
      </div>
      <div class="card">
        <div class="card-title">Synthèse financière estimative</div>
        <table id="res_finance"></table>
        <div class="disclaimer">⚠️ Valeurs estimatives à titre illustratif — Non contractuel — NEWS-SOLAR 2026</div>
      </div>
    </div>
  </div>
</div>
</div>

<script>
let compareChart = null;

document.getElementById('simForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btnSim');
  btn.innerHTML = '<span class="spin">⟳</span> Calcul en cours...';
  btn.disabled = true;

  const fd = new FormData(e.target);
  const outputs = [...document.querySelectorAll('input[name=outputs]:checked')].map(c=>c.value);

  const payload = {
    region:         fd.get('region'),
    surface_ha:     parseFloat(fd.get('surface_ha')),
    converter_type: fd.get('converter_type'),
    outputs:        outputs
  };

  try {
    const r = await fetch('/newssolar/api/simulate', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const d = await r.json();
    renderResults(d);
  } catch(err) {
    alert('Erreur de simulation: ' + err);
  } finally {
    btn.innerHTML = '▶ Lancer la simulation';
    btn.disabled = false;
  }
});

function fmt(n) { return new Intl.NumberFormat('fr-FR').format(Math.round(n)); }

function renderResults(d) {
  document.getElementById('placeholder').style.display = 'none';
  document.getElementById('resultPanel').classList.add('visible');
  document.getElementById('res_region').textContent = d.region_label + ' · ' + d.surface_ha + ' ha · Convertisseur ' + d.converter_type + ' (' + d.conv_eff_pct + '%)';

  const kpiData = [
    { label:'Électricité', val: fmt(d.electricity_mwh)+' MWh/an', color:'var(--gold)' },
    { label:'Chaleur',     val: fmt(d.heat_mwh)+' MWh/an',        color:'var(--ns-orange)' },
    { label:'Froid',       val: fmt(d.cold_mwh)+' MWh/an',        color:'var(--blue)' },
    { label:'H₂',          val: fmt(d.h2_kg)+' kg/an',            color:'var(--green)' },
    { label:'NH₃',         val: d.nh3_tons > 0 ? fmt(d.nh3_tons)+' t/an' : '—', color:'var(--purple)' },
    { label:'Stockage brut', val: fmt(d.stored_thermal_mwh)+' MWh/an', color:'var(--muted)' },
  ];
  document.getElementById('res_kpis').innerHTML = kpiData.map(k =>
    `<div style="background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:10px;padding:0.8rem">
       <div style="font-size:0.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:.06em">${k.label}</div>
       <div style="font-size:1.3rem;font-weight:800;color:${k.color};margin-top:0.2rem">${k.val}</div>
     </div>`
  ).join('');

  // Graphique comparatif
  if (compareChart) compareChart.destroy();
  compareChart = new Chart(document.getElementById('chartCompare'), {
    type: 'bar',
    data: {
      labels: ['PV standard', 'NEWS-SOLAR HST'],
      datasets: [{
        data: [d.pv_electricity_mwh, d.electricity_mwh],
        backgroundColor: ['rgba(100,100,120,0.5)', 'rgba(255,183,0,0.7)'],
        borderColor: ['rgba(100,100,120,0.8)', '#FFB700'],
        borderWidth: 1, borderRadius: 6
      }]
    },
    options: {
      plugins:{ legend:{display:false}, tooltip:{ callbacks:{ label: ctx => fmt(ctx.raw)+' MWh/an électricité' } } },
      scales: { x:{ticks:{color:'#8892a4'},grid:{color:'rgba(255,255,255,0.04)'}}, y:{ticks:{color:'#8892a4'},grid:{color:'rgba(255,255,255,0.04)'}} }
    }
  });

  // Tableau financier
  document.getElementById('res_finance').innerHTML = `
    <tr><th>Poste</th><th>Valeur</th></tr>
    <tr><td>CAPEX estimatif</td><td class="gold">${fmt(d.capex_eur)} €</td></tr>
    <tr><td>Revenus annuels estimés</td><td class="green">${fmt(d.revenue_annual_eur)} €/an</td></tr>
    <tr><td>ROI estimé</td><td class="gold">${d.roi_years} ans</td></tr>
    <tr><td>CA cumulé 25 ans</td><td class="orange">${fmt(d.revenue_25y)} €</td></tr>
    <tr><td>Productivité électrique vs PV</td><td class="gold">×${d.electricity_ratio}</td></tr>
    <tr><td>Tarif de référence énergie</td><td>80 €/MWh élec. · 65 €/MWh chaleur · 6 €/kg H₂</td></tr>
  `;
}
</script>
</body></html>
"""
