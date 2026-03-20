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

    # Comparatif vs PV (même surface)
    pv_electricity_mwh = (irr["ghi"] * SURFACE_M2 * 0.20) / 1000  # 20% rendement PV standard
    electricity_ratio  = (electricity_mwh / pv_electricity_mwh) if pv_electricity_mwh > 0 else 0

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
body { background: var(--bg); color: var(--text); font-family: 'Inter',sans-serif; min-height:100vh; }
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
::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:transparent; } ::-webkit-scrollbar-thumb { background:rgba(255,255,255,0.1); border-radius:3px; }

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
<style>""" + _BASE_CSS + """</style>
</head>
<body>
""" + _HEADER_HTML + """
<script>document.getElementById('nav-dash').classList.add('active');</script>

<!-- HERO -->
<div class="hero">
  <div style="max-width:1400px;margin:0 auto">
    <span class="tagline">⚡ Technologie HST — High Solar Temperature · Breveté NEWS-SOLAR</span>
    <h1>Poly-génération d'énergies vertes <span class="gold">8 760 h/an</span></h1>
    <p>Captation solaire à hyper-concentration (×15 000) — Rendement 95% — Batterie thermique jusqu'à 3 000°C — Production continue sans interruption. Simulation pour <strong>{{ sim.region_label }}</strong> · 1 ha · Convertisseur {{ sim.converter_type }} ({{ sim.conv_eff_pct }}%).</p>
  </div>
</div>

<div class="main-content">

  <!-- KPI production principale -->
  <div class="section-title" style="margin-top:0">⚡ Production annuelle estimée</div>
  <div class="grid-4" style="margin-bottom:1.5rem">
    <div class="card">
      <div class="card-title">Électricité</div>
      <div class="kpi-value gold">{{ '{:,.0f}'.format(sim.electricity_mwh) }}<span class="kpi-unit">MWh/an</span></div>
      <div class="bar-wrap"><div class="bar-fill" style="width:{{ [sim.electricity_mwh / sim.stored_thermal_mwh * 100, 100] | min | round | int }}%; background:var(--gold)"></div></div>
      <div class="kpi-delta muted" style="margin-top:0.6rem">Convertisseur {{ sim.converter_type }} — {{ sim.conv_eff_pct }}% rendement</div>
    </div>
    <div class="card">
      <div class="card-title">Chaleur process</div>
      <div class="kpi-value orange">{{ '{:,.0f}'.format(sim.heat_mwh) }}<span class="kpi-unit">MWh/an</span></div>
      <div class="bar-wrap"><div class="bar-fill" style="width:{{ [sim.heat_mwh / sim.stored_thermal_mwh * 100, 100] | min | round | int }}%; background:var(--ns-orange)"></div></div>
      <div class="kpi-delta muted" style="margin-top:0.6rem">Chaleur directe THT disponible</div>
    </div>
    <div class="card">
      <div class="card-title">Froid industriel</div>
      <div class="kpi-value blue">{{ '{:,.0f}'.format(sim.cold_mwh) }}<span class="kpi-unit">MWh/an</span></div>
      <div class="bar-wrap"><div class="bar-fill" style="width:30%; background:var(--blue)"></div></div>
      <div class="kpi-delta muted" style="margin-top:0.6rem">Cycle absorption thermique</div>
    </div>
    <div class="card">
      <div class="card-title">Hydrogène H₂</div>
      <div class="kpi-value green">{{ '{:,.0f}'.format(sim.h2_kg) }}<span class="kpi-unit">kg/an</span></div>
      <div class="bar-wrap"><div class="bar-fill" style="width:55%; background:var(--green)"></div></div>
      <div class="kpi-delta muted" style="margin-top:0.6rem">Électrolyse HTE rendement 60%</div>
    </div>
  </div>

  <!-- Financiers & Comparatif -->
  <div class="grid-3" style="margin-bottom:1.5rem">
    <div class="card">
      <div class="card-title">💰 CAPEX estimatif</div>
      <div class="kpi-value gold">{{ '{:,.0f}'.format(sim.capex_eur / 1000) }}<span class="kpi-unit">k€</span></div>
      <div style="margin-top:1rem">
        <div class="gauge-row"><span class="gauge-label">Revenus annuels estimés</span><span class="gauge-val green">{{ '{:,.0f}'.format(sim.revenue_annual_eur / 1000) }} k€</span></div>
        <div class="gauge-row"><span class="gauge-label">ROI estimé</span><span class="gauge-val gold">{{ sim.roi_years }} ans</span></div>
        <div class="gauge-row"><span class="gauge-label">CA cumulé 25 ans</span><span class="gauge-val orange">{{ '{:,.0f}'.format(sim.revenue_25y / 1000) }} k€</span></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">📊 Comparatif vs PV standard</div>
      <div class="kpi-value gold">×{{ sim.electricity_ratio }}<span class="kpi-unit">productivité élec.</span></div>
      <div style="margin-top:1rem">
        <div class="gauge-row"><span class="gauge-label">PV standard (20% rdt)</span><span class="gauge-val muted">{{ '{:,.0f}'.format(sim.pv_electricity_mwh) }} MWh/an</span></div>
        <div class="gauge-row"><span class="gauge-label">NEWS-SOLAR HST</span><span class="gauge-val green">{{ '{:,.0f}'.format(sim.electricity_mwh) }} MWh/an</span></div>
        <div class="gauge-row"><span class="gauge-label">Heures de production</span><span class="gauge-val gold">{{ sim.hours_per_year }} h/an</span></div>
        <div class="gauge-row"><span class="gauge-label">PV heures production</span><span class="gauge-val muted">~1 500 h/an</span></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">🌡️ Températures batterie thermique (illustratif)</div>
      <canvas id="tempChart" height="140"></canvas>
      <div class="disclaimer">⚠️ Données T°C à titre illustratif — Simulation. Non contractuel.</div>
    </div>
  </div>

  <!-- Tableau récapitulatif technologie -->
  <div class="grid-2" style="margin-bottom:1.5rem">
    <div class="card">
      <div class="section-title">🔩 Paramètres technologiques HST</div>
      <table>
        <tr><th>Paramètre</th><th>Valeur</th></tr>
        <tr><td>Rendement de captation solaire</td><td class="gold">95%</td></tr>
        <tr><td>Rendement batterie thermique</td><td class="gold">98%</td></tr>
        <tr><td>Facteur concentration</td><td class="blue">×15 000</td></tr>
        <tr><td>Densité énergétique batterie</td><td class="orange">1,3 – 1,5 MWh/m³</td></tr>
        <tr><td>Température max batterie</td><td class="temp-high">3 000°C</td></tr>
        <tr><td>Perte thermique batterie / jour</td><td class="green">1%</td></tr>
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
    ⚠️ <strong>Document confidentiel — Démo investisseurs.</strong> Toutes les valeurs sont des estimations calculées à titre illustratif. Non contractuel. Données NEWS-SOLAR © 2026 — Brevets internationaux déposés. Technologie HST (High Solar Temperature) propriété exclusive NEWS-SOLAR, Valence (26).
  </div>

</div>

<script>
// Graphique températures
const tp = {{ sim.temp_profile | tojson }};
new Chart(document.getElementById('tempChart'), {
  type: 'line',
  data: {
    labels: tp.hours.map(h => h+'h'),
    datasets: [
      { label: 'Batterie (°C)', data: tp.battery_temp, borderColor: '#ff4444', backgroundColor: 'rgba(255,68,68,0.08)', tension: 0.4, pointRadius: 0, borderWidth: 2 },
      { label: 'Sortie process (°C)', data: tp.output_temp, borderColor: '#FFB700', backgroundColor: 'rgba(255,183,0,0.08)', tension: 0.4, pointRadius: 0, borderWidth: 2 }
    ]
  },
  options: { plugins: { legend: { labels: { color:'#8892a4', font:{ size:10 } } } }, scales: { x: { ticks:{ color:'#8892a4', font:{size:9} }, grid:{ color:'rgba(255,255,255,0.04)' } }, y: { ticks:{ color:'#8892a4', font:{size:9} }, grid:{ color:'rgba(255,255,255,0.04)' } } }, animation:{ duration:800 }, maintainAspectRatio:true }
});
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
