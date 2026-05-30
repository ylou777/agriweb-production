"""
Routes Flask — Marketplace AO solaire municipal
================================================
/ao/                              → Dashboard public — liste des AO publiés
/ao/commune/<code_insee>          → Espace mairie — ses projets (depuis diagnostic)
/ao/commune/<code_insee>/claim    → Revendiquer la gestion de sa commune
/ao/projet/new                    → Créer un projet depuis un asset
/ao/projet/<id>                   → Cahier des charges auto-généré
/ao/projet/<id>/publish           → Publier l'AO
/ao/projet/<id>/close             → Clore l'AO
/ao/projet/<id>/repondre          → Installateur soumet une réponse
/ao/mes-reponses                  → Installateur voit ses réponses
/ao/admin                         → Admin : vue globale
"""

import json
import math
from datetime import date, datetime
from flask import (Blueprint, render_template_string, request,
                   redirect, jsonify, session, flash, url_for)

commune_ao_bp = Blueprint('commune_ao_bp', __name__, url_prefix='/ao')


# ── DB + auth helpers ──────────────────────────────────────────────────────────

def _get_db():
    from mairies_campaign import get_db
    return get_db()


def _get_user():
    token = session.get('session_token') or request.cookies.get('session_token')
    if not token:
        return None
    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        c = conn.cursor()
        c.execute("""SELECT u.id, u.email, u.name, u.company, u.subscription_plan, u.is_admin
                     FROM users u JOIN user_sessions s ON u.id=s.user_id
                     WHERE s.session_token=? AND s.expires_at>CURRENT_TIMESTAMP""", (token,))
        row = c.fetchone()
        conn.close()
        if not row:
            return None
        return {k: row[k] for k in ('id', 'email', 'name', 'company', 'subscription_plan', 'is_admin')}
    except Exception:
        return None


def _build_all_assets(diag):
    """Construit la liste complète des assets depuis map_assets (tous les sites, pas que top 5).
    Champs normalisés : type, name, surface_m2, puissance_kwc, economie_annuelle,
                        id_parcelle, lat, lon, geom.
    """
    if not diag:
        return []
    # id_parcelle disponible dans top_assets (5 meilleurs) — enrichir si match
    _ip_map = {a.get('name', ''): a.get('id_parcelle', '') for a in diag.get('top_assets', [])}
    assets = []
    for ma in diag.get('map_assets', []):
        name = ma.get('name', '')
        # id_parcelle : d'abord dans map_assets (enrichi depuis _diag_full), sinon top_assets
        parcelle = ma.get('id_parcelle') or _ip_map.get(name, '')
        assets.append({
            'type':             ma.get('type', ''),
            'name':             name,
            'surface_m2':       ma.get('surface') or 0,
            'puissance_kwc':    ma.get('kwc') or 0,
            'economie_annuelle': ma.get('eco') or 0,
            'id_parcelle':      parcelle,
            'lat':              ma.get('lat'),
            'lon':              ma.get('lon'),
            'geom':             ma.get('geom'),
        })
    assets.sort(key=lambda x: x['puissance_kwc'], reverse=True)
    return assets


def _get_diagnostic_for_commune(code_insee: str):
    """Récupère le dernier diagnostic JSON pour une commune (table recipients)."""
    try:
        db = _get_db()
        row = db.execute("""
            SELECT diagnostic_json, nom_commune, lat, lon
            FROM recipients
            WHERE code_insee = ? AND diagnostic_json IS NOT NULL AND diagnostic_json != ''
            ORDER BY sent_at DESC NULLS LAST
            LIMIT 1
        """, (code_insee,)).fetchone()
        db.close()
        if not row:
            return None
        diag = json.loads(row['diagnostic_json'])
        diag['nom_commune'] = row['nom_commune']
        diag['lat'] = float(row['lat'] or 0)
        diag['lon'] = float(row['lon'] or 0)
        # Extraire les assets avec coordonnées depuis _diag_full ou assets
        _full = diag.get('_diag_full') or {}
        raw_assets = _full.get('assets', diag.get('assets', []))
        diag['map_assets'] = [
            {
                'lat': float(a['lat']), 'lon': float(a['lon']),
                'type': a.get('type', ''),
                'name': a.get('denomination') or a.get('name', ''),
                'surface': int(a.get('surface_m2') or 0),
                'kwc': round(float(a.get('puissance_kwc') or 0), 1),
                'eco': int(a.get('economie_annuelle') or 0),
                'id_parcelle': a.get('id_parcelle', ''),
                # GeoJSON polygon (geometry_osm preferred, else BD TOPO geometry)
                'geom': a.get('geometry_osm') or a.get('geometry'),
            }
            for a in raw_assets
            if a.get('lat') and a.get('lon')
        ]
        return diag
    except Exception:
        return None


# ── Init tables ────────────────────────────────────────────────────────────────

def _init_ao_tables():
    db = _get_db()
    stmts = [
        """
        CREATE TABLE IF NOT EXISTS commune_accounts (
            id          SERIAL PRIMARY KEY,
            code_insee  TEXT UNIQUE NOT NULL,
            nom_commune TEXT NOT NULL,
            user_id     INTEGER REFERENCES users(id),
            created_at  TIMESTAMP DEFAULT NOW(),
            status      TEXT DEFAULT 'active'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ao_projects (
            id                SERIAL PRIMARY KEY,
            commune_id        INTEGER REFERENCES commune_accounts(id),
            code_insee        TEXT NOT NULL,
            nom_commune       TEXT NOT NULL,
            asset_type        TEXT NOT NULL,
            asset_name        TEXT,
            surface_m2        DOUBLE PRECISION,
            puissance_kwc     DOUBLE PRECISION,
            prod_annuelle_kwh INTEGER,
            economie_annuelle INTEGER,
            lat               DOUBLE PRECISION,
            lon               DOUBLE PRECISION,
            id_parcelle       TEXT,
            asset_json        TEXT,
            statut            TEXT DEFAULT 'brouillon',
            created_at        TIMESTAMP DEFAULT NOW(),
            published_at      TIMESTAMP,
            deadline          DATE,
            budget_max        INTEGER,
            notes_mairie      TEXT,
            irradiance        DOUBLE PRECISION,
            nb_reponses       INTEGER DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ao_responses (
            id             SERIAL PRIMARY KEY,
            project_id     INTEGER NOT NULL REFERENCES ao_projects(id),
            user_id        INTEGER NOT NULL REFERENCES users(id),
            company        TEXT,
            message        TEXT,
            prix_kwc       DOUBLE PRECISION,
            delai_semaines INTEGER,
            experience     TEXT,
            statut         TEXT DEFAULT 'soumise',
            created_at     TIMESTAMP DEFAULT NOW(),
            updated_at     TIMESTAMP DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_ao_projects_insee ON ao_projects(code_insee)",
        "CREATE INDEX IF NOT EXISTS idx_ao_projects_statut ON ao_projects(statut)",
        "CREATE INDEX IF NOT EXISTS idx_ao_responses_project ON ao_responses(project_id)",
    ]
    for s in stmts:
        try:
            db.execute(s)
        except Exception as e:
            print(f"[AO] DDL warning: {e}")
    db.commit()
    db.close()


try:
    _init_ao_tables()
    print("🏛️ [AO] Tables commune_accounts / ao_projects / ao_responses OK")
except Exception as _e:
    print(f"⚠️ [AO] Init tables failed: {_e}")


# ── CSS partagé (dark theme HeliaPV) ──────────────────────────────────────────

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,sans-serif;background:#0a0e27;color:#e8eaed;min-height:100vh}
a{color:#ffb700;text-decoration:none}a:hover{text-decoration:underline}
.topbar{background:rgba(26,31,58,.95);border-bottom:1px solid rgba(255,183,0,.15);
        padding:14px 32px;display:flex;align-items:center;gap:16px;position:sticky;top:0;z-index:100}
.topbar h1{font-size:17px;font-weight:700;color:#ffb700}
.topbar span{color:#94a3b8;font-size:13px}
.topbar .nav{margin-left:auto;display:flex;gap:12px}
.container{max-width:1100px;margin:32px auto;padding:0 24px}
.card{background:rgba(26,31,58,.7);border:1px solid rgba(255,183,0,.1);
      backdrop-filter:blur(16px);border-radius:16px;padding:24px;margin-bottom:24px}
.card h2{font-size:14px;color:#94a3b8;font-weight:600;text-transform:uppercase;
         letter-spacing:1px;margin-bottom:18px}
.grid-3{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.asset-card{background:rgba(15,23,42,.6);border:1px solid rgba(255,183,0,.12);
            border-radius:12px;padding:20px;transition:.2s;cursor:pointer}
.asset-card:hover{border-color:#ffb700;transform:translateY(-2px)}
.asset-card .icon{font-size:28px;margin-bottom:8px}
.asset-card h3{font-size:15px;font-weight:600;color:#f1f5f9;margin-bottom:6px}
.asset-card .meta{font-size:12px;color:#64748b;margin-bottom:4px}
.kpi-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.kpi{background:rgba(255,183,0,.08);border:1px solid rgba(255,183,0,.2);
     border-radius:8px;padding:6px 12px;font-size:12px;color:#ffb700;font-weight:600}
.kpi span{font-size:11px;color:#94a3b8;font-weight:400;margin-left:4px}
.btn{display:inline-block;padding:10px 20px;border-radius:8px;font-size:13px;
     font-weight:600;cursor:pointer;border:none;text-decoration:none;transition:.2s}
.btn-gold{background:#ffb700;color:#0a0e27}.btn-gold:hover{background:#ffd33d;color:#0a0e27}
.btn-outline{background:transparent;color:#ffb700;border:1px solid rgba(255,183,0,.4)}
.btn-outline:hover{background:rgba(255,183,0,.08)}
.btn-green{background:#10b981;color:#fff}.btn-green:hover{background:#059669}
.btn-red{background:#ef4444;color:#fff}.btn-red:hover{background:#dc2626}
.btn-gray{background:#1e293b;color:#94a3b8;border:1px solid #334155}
.btn-gray:hover{background:#2d3f5c}
.btn-sm{padding:6px 14px;font-size:12px}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700}
.badge-draft{background:#33415533;color:#94a3b8;border:1px solid #334155}
.badge-publie{background:#10b9811a;color:#10b981;border:1px solid #10b98133}
.badge-clos{background:#ef44441a;color:#ef4444;border:1px solid #ef444433}
.badge-bat{background:#7c3aed1a;color:#a78bfa;border:1px solid #7c3aed33}
.badge-park{background:#1e40af1a;color:#60a5fa;border:1px solid #1e40af33}
.badge-urgent{background:#dc26261a;color:#f87171;border:1px solid #dc262633}
.section-title{font-size:13px;font-weight:700;color:#ffb700;text-transform:uppercase;
               letter-spacing:1px;margin:20px 0 10px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:rgba(255,183,0,.2)}
.info-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:16px}
.info-box{background:rgba(15,23,42,.5);border:1px solid rgba(255,255,255,.05);
          border-radius:10px;padding:14px}
.info-box .val{font-size:22px;font-weight:700;color:#f1f5f9}
.info-box .unit{font-size:11px;color:#64748b;margin-top:2px}
.info-box .label{font-size:11px;color:#ffb700;font-weight:600;margin-bottom:4px}
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px}
.alert-success{background:#10b9811a;border:1px solid rgba(16,185,129,.3);color:#6ee7b7}
.alert-error{background:#ef44441a;border:1px solid rgba(239,68,68,.3);color:#fca5a5}
.alert-info{background:#3b82f61a;border:1px solid rgba(59,130,246,.3);color:#93c5fd}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 12px;color:#64748b;font-weight:600;border-bottom:1px solid #1e293b}
td{padding:10px 12px;border-bottom:1px solid rgba(255,255,255,.04);color:#cbd5e1}
tr:hover td{background:rgba(255,183,0,.03)}
input,select,textarea{background:#0f172a;border:1px solid #334155;color:#f1f5f9;
                      padding:9px 14px;border-radius:8px;font-size:13px;width:100%}
input:focus,select:focus,textarea:focus{outline:none;border-color:#ffb700}
label{display:block;font-size:12px;color:#94a3b8;font-weight:600;margin-bottom:5px}
.form-group{margin-bottom:14px}
.hero{background:linear-gradient(135deg,rgba(255,183,0,.1),rgba(102,126,234,.1));
      border-radius:16px;padding:32px;margin-bottom:24px;text-align:center}
.hero h1{font-size:28px;font-weight:800;margin-bottom:8px}
.hero p{color:#94a3b8;font-size:15px}
.empty-state{text-align:center;padding:48px 24px;color:#64748b}
.empty-state .icon{font-size:48px;margin-bottom:12px}
.legal-box{background:rgba(59,130,246,.06);border:1px solid rgba(59,130,246,.2);
           border-radius:10px;padding:16px;margin-bottom:12px}
.legal-box h4{color:#60a5fa;font-size:13px;font-weight:700;margin-bottom:8px}
.legal-box p{color:#94a3b8;font-size:12px;line-height:1.6}
.urgency{background:rgba(220,38,38,.08);border:1px solid rgba(220,38,38,.3);
         border-radius:10px;padding:12px 16px;color:#f87171;font-size:13px;font-weight:600}
"""

_NAV_LINKS = """
<div class="nav">
  <a href="/ao/" class="btn btn-outline btn-sm">📋 Tous les AO</a>
  {% if user %}
  <a href="/ao/mes-reponses" class="btn btn-outline btn-sm">📝 Mes réponses</a>
  <a href="/auth/logout" class="btn btn-gray btn-sm">Déconnexion</a>
  {% else %}
  <a href="/auth/login" class="btn btn-outline btn-sm">Connexion</a>
  <a href="/auth/register" class="btn btn-gold btn-sm">S'inscrire</a>
  {% endif %}
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 1 — Dashboard public : liste des AO publiés
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/', methods=['GET'])
def dashboard():
    user = _get_user()
    dept_filter = request.args.get('dept', '').strip()

    db = _get_db()
    if dept_filter:
        rows = db.execute("""
            SELECT * FROM ao_projects
            WHERE statut IN ('publie','clos')
              AND LEFT(code_insee, 2) = ?
            ORDER BY published_at DESC NULLS LAST
            LIMIT 200
        """, (dept_filter,)).fetchall()
    else:
        rows = db.execute("""
            SELECT * FROM ao_projects
            WHERE statut IN ('publie','clos')
            ORDER BY published_at DESC NULLS LAST
            LIMIT 200
        """).fetchall()
    db.close()

    projects = [dict(r) for r in rows]

    html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Appels d'offres solaires municipaux — HeliaPV</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<style>""" + _CSS + """</style></head><body>
<div class="topbar">
  <h1>☀ HeliaPV · AO Solaires Municipaux</h1>
  <span>{{ projects|length }} appel(s) d'offres</span>
  """ + _NAV_LINKS + """
</div>
<div class="container">
  <div class="hero">
    <h1>Appels d'offres solaires des communes</h1>
    <p>Les mairies publient leurs projets PV — bâtiments publics &amp; parkings — en toute transparence.<br>
       Vous êtes installateur&nbsp;? Trouvez des projets près de chez vous et répondez directement.</p>
    <div style="margin-top:20px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <form method="get" style="display:flex;gap:8px;align-items:center">
        <input type="text" name="dept" value="{{ dept_filter }}" placeholder="Département (ex: 34)"
               style="width:160px" maxlength="3">
        <button type="submit" class="btn btn-gold">Filtrer</button>
        {% if dept_filter %}<a href="/ao/" class="btn btn-gray btn-sm">✕ Tout</a>{% endif %}
      </form>
    </div>
  </div>

  {% if not projects %}
  <div class="empty-state">
    <div class="icon">📭</div>
    <p>Aucun appel d'offres publié pour le moment.<br>
       Vous êtes une mairie&nbsp;? <a href="/ao/commune/{{ '' }}">Créez votre espace</a></p>
  </div>
  {% else %}
  <div class="card">
    <h2>Appels d'offres ouverts</h2>
    <table>
      <thead><tr>
        <th>Commune</th><th>Type</th><th>Puissance</th><th>Économies/an</th>
        <th>Publié le</th><th>Deadline</th><th>Réponses</th><th>Action</th>
      </tr></thead>
      <tbody>
      {% for p in projects %}
      <tr>
        <td>
          <strong>{{ p.nom_commune }}</strong>
          <div style="font-size:11px;color:#64748b">{{ p.code_insee }}</div>
        </td>
        <td>
          {% if 'parking' in p.asset_type %}
          <span class="badge badge-park">🚗 Parking</span>
          {% else %}
          <span class="badge badge-bat">🏛 Bâtiment</span>
          {% endif %}
        </td>
        <td><strong>{{ "%.0f"|format(p.puissance_kwc or 0) }} kWc</strong></td>
        <td style="color:#10b981"><strong>{{ "{:,}".format(p.economie_annuelle or 0)|replace(",","\u00a0") }} €</strong></td>
        <td style="font-size:12px;color:#64748b">
          {% if p.published_at %}{{ p.published_at|string|truncate(10,killwords=True,end='') }}{% else %}—{% endif %}
        </td>
        <td>
          {% if p.deadline %}
          <span class="badge {% if p.statut=='clos' %}badge-clos{% else %}badge-publie{% endif %}">
            {{ p.deadline }}
          </span>
          {% else %}—{% endif %}
        </td>
        <td style="text-align:center"><strong>{{ p.nb_reponses or 0 }}</strong></td>
        <td>
          <a href="/ao/projet/{{ p.id }}" class="btn btn-gold btn-sm">Voir →</a>
        </td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px">
    <div class="card" style="text-align:center">
      <div style="font-size:28px;margin-bottom:10px">🏛</div>
      <h2>Vous êtes une commune&nbsp;?</h2>
      <p style="color:#94a3b8;font-size:14px;margin-bottom:16px">
        Entrez votre code INSEE pour accéder à votre espace et publier vos projets solaires <strong>gratuitement</strong>.
      </p>
      <form method="get" action="/ao/commune_redirect" style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
        <input type="text" name="insee" placeholder="Code INSEE (ex: 34172)" style="max-width:190px" maxlength="5" pattern="[0-9]{5}" required>
        <button type="submit" class="btn btn-gold">Mon espace mairie →</button>
      </form>
    </div>
    <div class="card" style="text-align:center">
      <div style="font-size:28px;margin-bottom:10px">⚡</div>
      <h2>Vous êtes installateur&nbsp;?</h2>
      <p style="color:#94a3b8;font-size:14px;margin-bottom:16px">
        Créez un compte gratuit pour répondre aux appels d'offres des communes françaises et développer votre carnet de commandes.
      </p>
      {% if user %}
      <a href="/ao/mes-reponses" class="btn btn-gold">Mes réponses →</a>
      {% else %}
      <a href="/auth/register" class="btn btn-gold">Créer mon compte installateur →</a>
      {% endif %}
    </div>
  </div>
</div>
</body></html>"""

    from flask import render_template_string as rts
    return rts(html, projects=projects, user=user, dept_filter=dept_filter)


@commune_ao_bp.route('/commune_redirect', methods=['GET'])
def commune_redirect():
    insee = request.args.get('insee', '').strip()
    if len(insee) == 5 and insee.isdigit():
        return redirect(f'/ao/commune/{insee}')
    return redirect('/ao/')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 2 — Espace mairie
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/commune/<code_insee>', methods=['GET'])
def commune_space(code_insee):
    user = _get_user()
    diag = _get_diagnostic_for_commune(code_insee)

    db = _get_db()
    account = db.execute(
        "SELECT * FROM commune_accounts WHERE code_insee=?", (code_insee,)
    ).fetchone()
    projects = db.execute(
        "SELECT * FROM ao_projects WHERE code_insee=? ORDER BY created_at DESC",
        (code_insee,)
    ).fetchall()
    db.close()

    account = dict(account) if account else None
    projects = [dict(r) for r in projects]
    top_assets = _build_all_assets(diag)
    nom_commune = (diag or {}).get('nom_commune', code_insee)

    # Déterminer si l'utilisateur est gestionnaire de cette commune
    is_owner = (account and user and account.get('user_id') == user.get('id')) or \
               (user and user.get('is_admin'))

    # Isolation : un non-gestionnaire ne voit que les AO publiés/clos (pas les brouillons d'autrui)
    if not is_owner:
        projects = [p for p in projects if p.get('statut') in ('publie', 'clos')]

    html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ nom_commune }} — Espace Solaire Municipal</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>""" + _CSS + """
#commune-map{height:460px;border-radius:0}
.leaflet-popup-content-wrapper{background:#1a1f3a;color:#e8eaed;border:1px solid rgba(255,183,0,.3);border-radius:10px;box-shadow:0 8px 32px rgba(0,0,0,.5)}
.leaflet-popup-tip{background:#1a1f3a}
.leaflet-popup-content{font-size:13px;line-height:1.5;margin:12px 16px}
.leaflet-popup-content b{color:#ffb700}
.leaflet-container a.leaflet-popup-close-button{color:#94a3b8}
</style></head><body>
<div class="topbar">
  <h1>🏛 {{ nom_commune }}</h1>
  <span>Code INSEE {{ code_insee }}</span>
  """ + _NAV_LINKS + """
</div>
<div class="container">

  {% if not diag %}
  <!-- Diagnostic non disponible : lancement automatique -->
  <div class="card" id="build-card" style="text-align:center;padding:48px 32px">
    <div id="build-icon" style="font-size:3rem;margin-bottom:16px">🔍</div>
    <h2 id="build-title" style="margin-bottom:8px">Génération du diagnostic en cours…</h2>
    <p id="build-msg" style="color:#94a3b8;font-size:.95rem;margin-bottom:24px">
      Interrogation des bases MAJIC, IGN, PVGIS — cela prend 20 à 60 secondes.
    </p>
    <div id="build-bar-wrap" style="background:rgba(255,255,255,.07);border-radius:20px;height:8px;max-width:400px;margin:0 auto 20px;overflow:hidden">
      <div id="build-bar" style="background:#fbbf24;height:100%;width:5%;border-radius:20px;transition:width 1s ease"></div>
    </div>
    <p id="build-status" style="color:#64748b;font-size:12px"></p>
  </div>
  <script>
  (function(){
    var _pct = 5;
    var _bar = document.getElementById('build-bar');
    var _msg = document.getElementById('build-msg');
    var _status = document.getElementById('build-status');
    var _title = document.getElementById('build-title');
    var _started = false;

    // Animation barre de progression
    var _ticker = setInterval(function(){
      _pct = Math.min(_pct + (Math.random() * 3 + 1), 90);
      if (_bar) _bar.style.width = _pct + '%';
    }, 1500);

    // Lancer le build
    fetch('/ao/api/commune/{{ code_insee }}/build', {method:'POST'})
      .then(function(r){ return r.json(); })
      .then(function(d){
        clearInterval(_ticker);
        if (d.ok) {
          if (_bar) _bar.style.width = '100%';
          if (_bar) _bar.style.background = '#22c55e';
          if (_title) _title.textContent = 'Diagnostic prêt !';
          if (_msg) _msg.textContent = 'Redirection en cours…';
          setTimeout(function(){ window.location.reload(); }, 800);
        } else {
          if (_title) _title.textContent = 'Diagnostic indisponible';
          if (_msg) _msg.innerHTML = (d.error || 'Données non disponibles pour cette commune.')
            + ' <a href="/ao/" style="color:#fbbf24">← Retour</a>';
          if (_bar) _bar.style.background = '#ef4444';
          if (_bar) _bar.style.width = '100%';
        }
      })
      .catch(function(){
        clearInterval(_ticker);
        if (_title) _title.textContent = 'Erreur réseau';
        if (_msg) _msg.innerHTML = 'Impossible de générer le diagnostic. <a href="/ao/" style="color:#fbbf24">← Retour</a>';
      });
  })();
  </script>
  {% else %}

  <!-- KPIs diagnostic -->
  <div class="card">
    <h2>Potentiel solaire identifié — données publiques (MAJIC + IGN + PVGIS)</h2>
    <div class="info-grid">
      <div class="info-box">
        <div class="label">Puissance totale</div>
        <div class="val">{{ "%.0f"|format(diag.get('puissance_totale_kwc',0)) }}</div>
        <div class="unit">kWc installables</div>
      </div>
      <div class="info-box">
        <div class="label">Production estimée</div>
        <div class="val">{{ "{:,}".format(diag.get('prod_totale_kwh',0))|replace(",","\u00a0") }}</div>
        <div class="unit">kWh/an (PVGIS)</div>
      </div>
      <div class="info-box">
        <div class="label">Ensoleillement</div>
        <div class="val">{{ diag.get('irradiance',0)|int }}</div>
        <div class="unit">kWh/m²/an · {{ diag.get('ensoleillement','') }}</div>
      </div>
      <div class="info-box">
        <div class="label">Sites identifiés</div>
        <div class="val">{{ diag.get('nb_batiments',0) + diag.get('nb_parkings',0) }}</div>
        <div class="unit">bâtiments + parkings</div>
      </div>
    </div>
  </div>

  <!-- Consommation électrique par secteur (Enedis Open Data) -->
  <div class="card" id="conso-card">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
      <h2 style="margin:0">⚡ Consommation électrique par secteur</h2>
      <span id="conso-annee" style="margin-left:auto;font-size:12px;color:#64748b;background:rgba(255,255,255,.06);padding:3px 10px;border-radius:20px"></span>
    </div>
    <div id="conso-body" style="color:#64748b;font-size:13px">Chargement…</div>
  </div>
  <script>
  (function(){
    var _prodKwh = {{ diag.get('prod_totale_kwh', 0) | int }};
    fetch('/ao/api/conso-commune?code_insee={{ code_insee }}')
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d.error || !d.secteurs || d.secteurs.length === 0) {
          document.getElementById('conso-body').innerHTML = '<span style="color:#475569">Données non disponibles pour cette commune.</span>';
          return;
        }
        document.getElementById('conso-annee').textContent = 'Source Enedis — données ' + d.annee;
        var total = d.total_mwh;
        var totalLabel = total >= 1000
          ? (total / 1000).toFixed(1).replace('.', ',') + '\u00a0GWh'
          : Math.round(total).toLocaleString('fr-FR') + '\u00a0MWh';

        // ── Taux d'autoconsommation potentiel ─────────────────────────────
        var autoconsoHtml = '';
        if (_prodKwh > 0 && total > 0) {
          var pctAuto = Math.round(_prodKwh / (total * 1000) * 100);
          var pctCapped = Math.min(pctAuto, 100);
          var acColor = pctAuto >= 50 ? '#22c55e' : pctAuto >= 25 ? '#fbbf24' : pctAuto >= 10 ? '#60a5fa' : '#94a3b8';
          var acBg    = pctAuto >= 50 ? 'rgba(34,197,94,.12)' : pctAuto >= 25 ? 'rgba(251,191,36,.12)' : pctAuto >= 10 ? 'rgba(96,165,250,.12)' : 'rgba(148,163,184,.08)';
          var prodLabel = _prodKwh >= 1000000
            ? (_prodKwh / 1000000).toFixed(1).replace('.', ',') + '\u00a0GWh'
            : Math.round(_prodKwh / 1000).toLocaleString('fr-FR') + '\u00a0MWh';
          autoconsoHtml = '<div style="margin-bottom:20px;padding:14px 16px;border-radius:12px;background:' + acBg + ';border:1px solid ' + acColor + '33">'
            + '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
            + '<div style="flex:1;min-width:160px">'
            + '<div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px">Taux d&#39;autoconsommation potentiel</div>'
            + '<div style="font-size:28px;font-weight:800;color:' + acColor + ';line-height:1">' + pctAuto + '\u00a0%</div>'
            + '<div style="font-size:11px;color:#64748b;margin-top:4px">Production ' + prodLabel + '/an vs consommation ' + totalLabel + '/an</div>'
            + '</div>'
            + '<div style="flex:0 0 140px">'
            + '<div style="background:rgba(255,255,255,.07);border-radius:20px;height:12px;overflow:hidden">'
            + '<div style="background:' + acColor + ';height:100%;width:' + pctCapped + '%;border-radius:20px;transition:width .8s ease"></div>'
            + '</div>'
            + '<div style="font-size:10px;color:#475569;margin-top:5px;text-align:right">' + (pctAuto > 100 ? 'surplus\u00a0' + (pctAuto - 100) + '\u00a0%' : pctCapped + '\u00a0% couvert') + '</div>'
            + '</div>'
            + '</div></div>';
        }

        var colors = {
          'RESIDENTIEL': {bg:'#2563eb', label:'Résidentiel', icon:'🏠'},
          'TERTIAIRE':   {bg:'#7c3aed', label:'Tertiaire',   icon:'🏢'},
          'INDUSTRIE':   {bg:'#d97706', label:'Industrie',   icon:'🏭'},
          'AGRICULTURE': {bg:'#16a34a', label:'Agriculture',  icon:'🌾'},
          'INCONNU':     {bg:'#475569', label:'Autre',        icon:'❓'}
        };
        var rows = d.secteurs.map(function(s){
          var c = colors[s.secteur] || {bg:'#475569', label:s.secteur, icon:'⚡'};
          var mwhLabel = s.conso_mwh >= 1000
            ? (s.conso_mwh / 1000).toFixed(1).replace('.', ',') + '\u00a0GWh'
            : s.conso_mwh.toLocaleString('fr-FR') + '\u00a0MWh';
          return '<div style="margin-bottom:12px">'
            + '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">'
            + '<span style="font-size:13px;color:#e2e8f0">' + c.icon + ' ' + c.label + '</span>'
            + '<span style="font-size:13px;font-weight:600;color:#f8fafc">' + mwhLabel
            + ' <span style="font-size:11px;color:#64748b;font-weight:400">(' + s.pct + '% · ' + s.nb_sites.toLocaleString('fr-FR') + '\u00a0sites)</span></span>'
            + '</div>'
            + '<div style="background:rgba(255,255,255,.07);border-radius:6px;height:8px;overflow:hidden">'
            + '<div style="background:' + c.bg + ';height:100%;width:' + s.pct + '%;border-radius:6px;transition:width .6s ease"></div>'
            + '</div></div>';
        }).join('');
        document.getElementById('conso-body').innerHTML = autoconsoHtml + rows
          + '<div style="margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,.08);display:flex;justify-content:space-between;font-size:13px">'
          + '<span style="color:#94a3b8">Total commune</span>'
          + '<span style="font-weight:700;color:#fbbf24">' + totalLabel + '/an</span></div>';
      })
      .catch(function(){ document.getElementById('conso-body').innerHTML = ''; });
  })();
  </script>

  <!-- Carte satellite des sites -->
  {% if diag and diag.get('lat') %}
  <div class="card" style="padding:0;overflow:hidden;border-radius:16px">
    <div style="padding:20px 24px 0;background:rgba(26,31,58,.85)">
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
        <h2 style="margin:0;font-size:13px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:1px">
          🛰 Sites éligibles — vue satellite
        </h2>
        <span style="margin-left:auto;font-size:12px;color:#64748b">{{ (diag.get('nb_batiments',0) + diag.get('nb_parkings',0)) }} sites identifiés</span>
      </div>
      <!-- Légende -->
      <div style="display:flex;gap:18px;flex-wrap:wrap;padding:12px 0 14px;font-size:12px">
        <span style="display:flex;align-items:center;gap:6px;color:#e8eaed">
          <svg width="22" height="14"><rect x="0" y="1" width="22" height="12" rx="3" fill="#a855f7" fill-opacity=".85" stroke="#c084fc" stroke-width="1.5"/></svg>
          Bâtiment public
        </span>
        <span style="display:flex;align-items:center;gap:6px;color:#e8eaed">
          <svg width="22" height="14"><rect x="0" y="1" width="22" height="12" rx="3" fill="#2563eb" fill-opacity=".85" stroke="#60a5fa" stroke-width="1.5"/></svg>
          Parking (obl. 2026–2028)
        </span>
        <span style="display:flex;align-items:center;gap:6px;color:#e8eaed">
          <svg width="22" height="14"><rect x="0" y="1" width="22" height="12" rx="3" fill="#dc2626" fill-opacity=".85" stroke="#f87171" stroke-width="1.5"/></svg>
          Parking urgent &gt;10 000 m² (juil. 2026)
        </span>
        <span style="display:flex;align-items:center;gap:6px;color:#e8eaed">
          <svg width="22" height="14"><rect x="0" y="1" width="22" height="12" rx="3" fill="#16a34a" fill-opacity=".85" stroke="#4ade80" stroke-width="1.5"/></svg>
          Parcelle communale
        </span>
      </div>
    </div>
    <div id="commune-map"></div>
  </div>
  <script>
  (function(){
    var clat={{ diag.get('lat',46.5) }}, clon={{ diag.get('lon',2.3) }};
    var nomCommune={{ nom_commune | tojson }};
    var assets={{ map_assets | tojson }};

    var map=L.map('commune-map',{zoomControl:true,scrollWheelZoom:false});

    // Satellite ESRI World Imagery
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{
      attribution:'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP',
      maxZoom:19
    }).addTo(map);

    // Noms de rues en overlay semi-transparent
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{
      opacity:0.6,maxZoom:19
    }).addTo(map);

    function colorForAsset(a){
      if(a.type==='parking_osm' && a.surface>10000) return {fill:'#dc2626',stroke:'#f87171'};
      if(a.type==='parking_osm') return {fill:'#2563eb',stroke:'#60a5fa'};
      if(a.type==='batiment_public') return {fill:'#a855f7',stroke:'#c084fc'};
      return {fill:'#16a34a',stroke:'#4ade80'};
    }

    function popupHtml(a){
      return '<div style="font-family:Inter,sans-serif;min-width:180px">'
        +'<div style="font-weight:700;font-size:13px;color:#f1f5f9;margin-bottom:6px">'+(a.name||a.type)+'</div>'
        +'<table style="font-size:12px;width:100%;border-collapse:collapse">'
        +'<tr><td style="color:#94a3b8;padding:2px 0">Surface</td><td style="color:#e8eaed;text-align:right"><b>'+(a.surface?a.surface.toLocaleString('fr-FR')+'\u00a0m\u00b2':'—')+'</b></td></tr>'
        +'<tr><td style="color:#94a3b8;padding:2px 0">Puissance est.</td><td style="color:#e8eaed;text-align:right"><b>'+(a.kwc?a.kwc+'\u00a0kWc':'—')+'</b></td></tr>'
        +'</table></div>';
    }

    var bounds=[];

    assets.forEach(function(a){
      var c=colorForAsset(a);
      var popup=L.popup({className:'ao-popup',maxWidth:240}).setContent(popupHtml(a));
      if(a.geom && a.geom.coordinates){
        L.geoJSON({type:'Feature',geometry:a.geom},{
          style:function(){return{color:c.stroke,weight:2,fillColor:c.fill,fillOpacity:.55};}
        }).bindPopup(popup).addTo(map);
        // Bounding box du polygone pour fitBounds
        try{
          var coords=a.geom.type==='Polygon'?a.geom.coordinates[0]:a.geom.coordinates[0][0];
          coords.forEach(function(pt){bounds.push([pt[1],pt[0]]);});
        }catch(e){bounds.push([a.lat,a.lon]);}
      } else {
        L.circleMarker([a.lat,a.lon],{radius:9,color:c.stroke,fillColor:c.fill,fillOpacity:.7,weight:2})
         .bindPopup(popup).addTo(map);
        bounds.push([a.lat,a.lon]);
      }
    });

    if(bounds.length===0){
      map.setView([clat,clon],15);
    } else if(bounds.length===1){
      map.setView(bounds[0],17);
    } else {
      map.fitBounds(bounds,{padding:[28,28]});
    }
  })();
  </script>
  {% endif %}

  <!-- Claim account -->
  {% if not account %}
  <div class="card" style="border-color:rgba(255,183,0,.3)">
    <h2>🏛 Revendiquer la gestion de cette commune</h2>
    <p style="color:#94a3b8;font-size:13px;margin-bottom:16px">
      Vous êtes élu(e) ou agent de la commune de <strong>{{ nom_commune }}</strong>&nbsp;?
      Créez votre espace pour publier des appels d'offres solaires.
    </p>
    {% if not user %}
    <a href="/auth/register?plan=commune_gratuit&insee={{ code_insee }}" class="btn btn-gold">
      Créer mon espace communal gratuit →
    </a>
    {% else %}
    <form method="post" action="/ao/commune/{{ code_insee }}/claim">
      <button type="submit" class="btn btn-gold">Revendiquer {{ nom_commune }}</button>
    </form>
    {% endif %}
  </div>
  {% elif is_owner %}
  <div class="alert alert-success">
    ✅ Vous gérez cet espace municipal. Publiez vos projets ci-dessous.
  </div>
  {% endif %}

  <!-- Sites éligibles — visible par tous, CTAs selon rôle -->
  {% if top_assets %}
  <div class="card">
    <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:6px">
      <h2 style="margin:0">Sites éligibles — projets solaires</h2>
      {% if user %}
      <button id="btn-inject-crm" onclick="injectCRM()" class="btn btn-outline btn-sm" style="margin-left:auto;display:flex;align-items:center;gap:6px">
        📤 Exporter dans mon CRM
      </button>
      {% endif %}
    </div>
    <p style="color:#8892b0;font-size:.92rem;margin:0 0 18px">
      {{ top_assets|length }} site{{ 's' if top_assets|length > 1 }} identifiés sur la commune.
      {% if not is_owner and not user %}Connectez-vous pour répondre aux appels d'offres publiés.{% endif %}
    </p>
    <div class="grid-3">
    {% for i, asset in top_assets|enumerate %}
      {% set existing = projects|selectattr('asset_name','equalto', asset.name)|list %}
      {% set proj = existing[0] if existing else None %}
      <div class="asset-card" style="overflow:hidden;padding:0">
        {% if asset.get('lat') %}
        <div id="amap-{{ i }}" style="height:130px;width:100%"></div>
        <script>(function(){
          window._aoMaps = window._aoMaps || {};
          var _m=L.map('amap-{{ i }}',{zoomControl:false,scrollWheelZoom:false,dragging:false,
            doubleClickZoom:false,keyboard:false,attributionControl:false,touchZoom:false});
          window._aoMaps[{{ i }}] = _m;
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20}).addTo(_m);
          L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{opacity:0.4,maxZoom:20}).addTo(_m);
          var _fill='{% if 'parking' in asset.type %}#2563eb{% else %}#a855f7{% endif %}';
          var _stroke='{% if 'parking' in asset.type %}#60a5fa{% else %}#c084fc{% endif %}';
          {% if asset.get('geom') %}
          var _l=L.geoJSON({type:'Feature',geometry:{{ asset.geom|tojson }}},{
            style:function(){return{color:_stroke,weight:2,fillColor:_fill,fillOpacity:.55};}
          }).addTo(_m);
          _m.fitBounds(_l.getBounds(),{padding:[10,10]});
          {% else %}
          _m.setView([{{ asset.lat }},{{ asset.lon }}],17);
          L.circleMarker([{{ asset.lat }},{{ asset.lon }}],{radius:9,color:_stroke,fillColor:_fill,fillOpacity:.7,weight:2}).addTo(_m);
          {% endif %}
        })();</script>
        {% endif %}
        <div style="padding:16px 20px">
        <div class="icon">{% if 'parking' in asset.type %}🚗{% else %}🏛{% endif %}</div>
        <h3>{{ asset.name or asset.type }}</h3>
        <div class="meta">Surface\u00a0: {{ asset.surface_m2|int }}\u00a0m²</div>
        {% if asset.id_parcelle %}
        <div class="meta" style="color:#64748b;font-size:11px;font-family:monospace">📍 {{ asset.id_parcelle }}</div>
        {% endif %}
        <div id="poste-{{ i }}" style="font-size:11px;color:#64748b;margin-top:3px">⚡ Poste BT&nbsp;: <span style="color:#94a3b8">…</span></div>
        <div class="kpi-row">
          <div class="kpi">{{ "%.0f"|format(asset.puissance_kwc or 0) }}\u00a0kWc</div>
        </div>
        {% if is_owner %}
          {% if proj %}
          <a href="/ao/projet/{{ proj.id }}" class="btn btn-outline btn-sm" style="margin-top:12px;display:block;text-align:center">
            Voir le projet →
          </a>
          {% else %}
          <form method="post" action="/ao/projet/new" style="margin-top:12px">
            <input type="hidden" name="code_insee" value="{{ code_insee }}">
            <input type="hidden" name="asset_index" value="{{ i }}">
            <button type="submit" class="btn btn-gold" style="width:100%">➕ Créer un AO</button>
          </form>
          {% endif %}
        {% else %}
          {% if proj and proj.statut == 'publie' %}
          <a href="/ao/projet/{{ proj.id }}" class="btn btn-gold btn-sm" style="margin-top:12px;display:block;text-align:center">
            Voir l'appel d'offres →
          </a>
          {% elif proj and proj.statut == 'brouillon' %}
          <div style="margin-top:12px;text-align:center;color:#8892b0;font-size:.85rem;padding:8px;background:rgba(255,255,255,.05);border-radius:6px">
            ⏳ En préparation
          </div>
          {% elif proj and proj.statut == 'clos' %}
          <div style="margin-top:12px;text-align:center;color:#8892b0;font-size:.85rem;padding:8px;background:rgba(255,255,255,.05);border-radius:6px">
            🔒 Clôturé
          </div>
          {% elif not user %}
          <a href="/auth/login" class="btn btn-outline btn-sm" style="margin-top:12px;display:block;text-align:center">
            Se connecter pour répondre
          </a>
          {% else %}
          <div style="margin-top:12px;text-align:center;color:#8892b0;font-size:.85rem;padding:8px;background:rgba(255,255,255,.05);border-radius:6px">
            Pas encore d'AO
          </div>
          {% endif %}
        {% endif %}
        </div>
      </div>
    {% endfor %}
    </div>
  </div>
  {% endif %}

  {% endif %}

  <!-- Projets existants -->
  {% if projects %}
  <div class="card">
    <h2>Projets de {{ nom_commune }}</h2>
    <table>
      <thead><tr>
        <th>Projet</th><th>Type</th><th>Puissance</th><th>Statut</th><th>Réponses</th><th>Action</th>
      </tr></thead>
      <tbody>
      {% for p in projects %}
      <tr>
        <td><strong>{{ p.asset_name or p.asset_type }}</strong></td>
        <td>{% if 'parking' in p.asset_type %}<span class="badge badge-park">🚗</span>
            {% else %}<span class="badge badge-bat">🏛</span>{% endif %}</td>
        <td>{{ "%.0f"|format(p.puissance_kwc or 0) }} kWc</td>
        <td>
          {% if p.statut == 'brouillon' %}<span class="badge badge-draft">Brouillon</span>
          {% elif p.statut == 'publie' %}<span class="badge badge-publie">Publié ✓</span>
          {% else %}<span class="badge badge-clos">Clôturé</span>{% endif %}
        </td>
        <td style="text-align:center">{{ p.nb_reponses or 0 }}</td>
        <td><a href="/ao/projet/{{ p.id }}" class="btn btn-outline btn-sm">Voir →</a></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

</div>
<script>
function injectCRM() {
  var btn = document.getElementById('btn-inject-crm');
  if (!btn) return;
  btn.disabled = true;
  btn.innerHTML = '⏳ Injection en cours...';
  fetch('/ao/commune/{{ code_insee }}/inject-crm', {method:'POST',headers:{'Content-Type':'application/json'}})
    .then(function(r){ return r.json(); })
    .then(function(d) {
      if (d.ok) {
        btn.innerHTML = '✅ ' + d.message;
        btn.style.color = '#10b981';
        btn.style.borderColor = '#10b981';
        setTimeout(function(){ window.location.href = d.crm_url; }, 2000);
      } else {
        btn.innerHTML = '❌ ' + (d.error || 'Erreur');
        btn.disabled = false;
      }
    })
    .catch(function(){ btn.innerHTML = '❌ Erreur réseau'; btn.disabled = false; });
}

// Fetch postes BT pour tous les assets via Overpass (batch)
(function(){
  var assets = {{ indexed_assets | tojson }};
  assets.forEach(function(pair){
    var i = pair[0], a = pair[1];
    if (!a.lat || !a.lon) return;
    var el = document.getElementById('poste-' + i);
    if (!el) return;
    fetch('/ao/api/poste-bt?lat=' + a.lat + '&lon=' + a.lon)
      .then(function(r){ return r.json(); })
      .then(function(d){
        if (d.distance_m != null) {
          var dist = d.distance_m < 1000
            ? Math.round(d.distance_m) + '\u00a0m'
            : (d.distance_m / 1000).toFixed(1) + '\u00a0km';
          el.innerHTML = '⚡ Poste BT\u00a0: <strong style="color:#fbbf24">' + dist + '</strong>'
            + (d.nom ? ' <span style="color:#64748b;font-size:10px">(' + d.nom + ')</span>' : '');
          if (d.poste_lat && d.poste_lon && window._aoMaps && window._aoMaps[i]) {
            var _icon = L.divIcon({
              html: '<div style="font-size:16px;line-height:1;filter:drop-shadow(0 0 3px #000)">⚡</div>',
              className: '',
              iconSize: [18, 18],
              iconAnchor: [9, 9]
            });
            L.marker([d.poste_lat, d.poste_lon], {icon: _icon, interactive: false}).addTo(window._aoMaps[i]);
          }
        } else {
          el.innerHTML = '⚡ Poste BT\u00a0: <span style="color:#475569">non trouvé</span>';
        }
      })
      .catch(function(){ el.innerHTML = ''; });
  });
})();
</script>
</body></html>"""

    from flask import render_template_string as rts

    # Filtre personnalisé pour enumerate dans Jinja2
    class _Env:
        pass
    # On passe enumerate manuellement via zip
    indexed_assets = list(enumerate(top_assets))

    map_assets = (diag or {}).get('map_assets', []) if diag else []

    return rts(
        html.replace('top_assets|enumerate', 'indexed_assets')
            .replace('{% for i, asset in indexed_assets %}', '{% for i, asset in indexed_assets %}'),
        nom_commune=nom_commune,
        code_insee=code_insee,
        diag=diag,
        account=account,
        projects=projects,
        top_assets=top_assets,
        indexed_assets=indexed_assets,
        is_owner=is_owner,
        user=user,
        map_assets=map_assets,
    )


# Cache mémoire postes BT (persistant tant que le process vit)
_POSTE_BT_CACHE: dict = {}

@commune_ao_bp.route('/api/poste-bt', methods=['GET'])
def api_poste_bt():
    """
    Retourne le poste BT le plus proche d'un point lat/lon via WFS GeoServer (gpu:poste_elec_shapefile).
    Cache en mémoire par coordonnées arrondies à 3 décimales (~100 m).
    """
    try:
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'lat/lon invalides'}), 400

    cache_key = f"{round(lat,3)},{round(lon,3)}"
    if cache_key in _POSTE_BT_CACHE:
        return jsonify(_POSTE_BT_CACHE[cache_key])

    try:
        from agriweb_hebergement_gratuit import get_nearest_postes
        postes = get_nearest_postes(lat, lon, count=1, radius_deg=0.15)
        if postes:
            props = postes[0].get('properties', {})
            result = {
                'distance_m': props.get('distance'),
                'nom': props.get('nom') or None,
                'etat': props.get('etat') or None,
                'puissance': props.get('puissance') or None,
                'poste_lat': props.get('latitude'),
                'poste_lon': props.get('longitude'),
            }
        else:
            result = {'distance_m': None, 'nom': None, 'poste_lat': None, 'poste_lon': None}
    except Exception as e:
        print(f"[AO] poste-bt erreur: {e}")
        result = {'distance_m': None, 'nom': None}

    _POSTE_BT_CACHE[cache_key] = result
    return jsonify(result)


_CONSO_CACHE: dict = {}

@commune_ao_bp.route('/api/conso-commune', methods=['GET'])
def api_conso_commune():
    """
    Retourne la consommation électrique annuelle par grand secteur pour une commune (Enedis Open Data).
    Agrège conso_totale_mwh par code_grand_secteur pour l'année la plus récente disponible.
    """
    code_insee = request.args.get('code_insee', '').strip()
    if not code_insee or len(code_insee) not in (4, 5):
        return jsonify({'error': 'code_insee invalide'}), 400

    if code_insee in _CONSO_CACHE:
        return jsonify(_CONSO_CACHE[code_insee])

    import urllib.request
    import urllib.parse

    base_url = (
        'https://opendata.enedis.fr/data-fair/api/v1/datasets/'
        'consommation-electrique-par-secteur-dactivite-commune/lines'
    )

    results = []
    annee_found = None
    for annee in ('2024', '2023', '2022'):
        qs = f'code_commune:{code_insee} AND annee:{annee}'
        params = urllib.parse.urlencode({
            'size': 500,
            'qs': qs,
            'select': 'code_grand_secteur,conso_totale_mwh,nb_sites',
        })
        try:
            req = urllib.request.Request(
                f'{base_url}?{params}',
                headers={'User-Agent': 'heliapv/1.0'}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                import json as _json
                data = _json.loads(resp.read())
            results = data.get('results', [])
            if results:
                annee_found = annee
                break
        except Exception as e:
            print(f'[conso-commune] erreur fetch {annee}: {e}')
            continue

    if not results:
        return jsonify({'error': 'Données non disponibles'}), 404

    # Agrégation par grand secteur
    secteurs: dict = {}
    for r in results:
        s = r.get('code_grand_secteur') or 'INCONNU'
        if s not in secteurs:
            secteurs[s] = {'conso_mwh': 0.0, 'nb_sites': 0}
        secteurs[s]['conso_mwh'] += r.get('conso_totale_mwh') or 0.0
        secteurs[s]['nb_sites'] += r.get('nb_sites') or 0

    total = sum(v['conso_mwh'] for v in secteurs.values())
    order = ['RESIDENTIEL', 'TERTIAIRE', 'INDUSTRIE', 'AGRICULTURE', 'INCONNU']
    secteurs_list = []
    for s in order:
        if s in secteurs:
            v = secteurs[s]
            secteurs_list.append({
                'secteur': s,
                'conso_mwh': round(v['conso_mwh']),
                'nb_sites': v['nb_sites'],
                'pct': round(v['conso_mwh'] / total * 100) if total > 0 else 0,
            })
    for s, v in secteurs.items():
        if s not in order:
            secteurs_list.append({
                'secteur': s,
                'conso_mwh': round(v['conso_mwh']),
                'nb_sites': v['nb_sites'],
                'pct': round(v['conso_mwh'] / total * 100) if total > 0 else 0,
            })

    payload = {
        'annee': annee_found,
        'total_mwh': round(total),
        'secteurs': secteurs_list,
    }
    _CONSO_CACHE[code_insee] = payload
    return jsonify(payload)


@commune_ao_bp.route('/api/commune/<code_insee>/build', methods=['POST'])
def api_build_commune(code_insee):
    """
    Lance le diagnostic MAJIC+IGN+PVGIS pour une commune non encore traitée.
    Insère (ou met à jour) le résultat dans la table recipients.
    Retourne {ok: true} si le diagnostic a été généré, {ok: false, error: ...} sinon.
    """
    if not code_insee or len(code_insee) not in (4, 5):
        return jsonify({'ok': False, 'error': 'Code INSEE invalide'}), 400

    # Si déjà présent, ne pas regénérer
    existing = _get_diagnostic_for_commune(code_insee)
    if existing:
        return jsonify({'ok': True, 'cached': True})

    try:
        # Géocodage via API officielle
        import urllib.request as _ur
        import urllib.parse as _up
        import json as _json

        geo_url = ('https://geo.api.gouv.fr/communes?code=' +
                   _up.quote(code_insee) + '&fields=nom,centre,population&limit=1')
        with _ur.urlopen(geo_url, timeout=8) as _r:
            geo_data = _json.loads(_r.read())

        if not geo_data:
            return jsonify({'ok': False, 'error': 'Commune introuvable pour ce code INSEE'})

        commune_info = geo_data[0]
        nom_commune = commune_info.get('nom', code_insee)
        population  = commune_info.get('population', 0) or 0
        coords      = commune_info.get('centre', {}).get('coordinates', [None, None])
        lon, lat    = coords[0], coords[1]

        if not lat or not lon:
            return jsonify({'ok': False, 'error': 'Géolocalisation impossible'})

        # Lancer le diagnostic complet
        from mairies_campaign import build_diagnostic, get_db as _get_campaign_db
        recipient = {
            'code_insee':   code_insee,
            'nom_commune':  nom_commune,
            'population':   population,
            'lat':          lat,
            'lon':          lon,
        }
        diag = build_diagnostic(recipient)

        if not diag:
            return jsonify({'ok': False, 'error': 'Diagnostic vide'})

        diag_json = _json.dumps(diag, ensure_ascii=False, default=str)

        # Insérer dans recipients (sans campagne, sans email)
        import uuid as _uuid
        db = _get_campaign_db()

        # S'assurer que la campagne 'on_demand' existe (FK recipients.campaign_id)
        db.execute(
            """INSERT INTO campaigns (id, name, subject, status)
               VALUES (?, ?, ?, ?) ON CONFLICT (id) DO NOTHING""",
            ('on_demand', 'Diagnostics à la demande', 'Diagnostic solaire HeliaPV', 'active')
        )
        db.commit()

        existing_row = db.execute(
            "SELECT id FROM recipients WHERE code_insee = ? LIMIT 1", (code_insee,)
        ).fetchone()
        if existing_row:
            db.execute(
                """UPDATE recipients SET nom_commune=?, lat=?, lon=?, irradiance=?,
                   diagnostic_json=?, status='pending' WHERE id=?""",
                (nom_commune, lat, lon, diag.get('irradiance'), diag_json, existing_row['id'])
            )
        else:
            row_id = 'od_' + str(_uuid.uuid4()).replace('-', '')[:20]
            db.execute(
                """INSERT INTO recipients
                   (id, campaign_id, email, nom_commune, code_insee, population, lat, lon,
                    irradiance, diagnostic_json, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row_id, 'on_demand', f'on_demand_{code_insee}@heliapv.fr',
                 nom_commune, code_insee, population,
                 lat, lon, diag.get('irradiance'), diag_json, 'pending')
            )
        db.commit()
        db.close()

        return jsonify({'ok': True})

    except Exception as e:
        print(f'[build-commune] erreur {code_insee}: {e}')
        return jsonify({'ok': False, 'error': str(e)[:200]})


@commune_ao_bp.route('/commune/<code_insee>/claim', methods=['POST'])
def claim_commune(code_insee):
    user = _get_user()
    if not user:
        return redirect(f'/auth/login?next=/ao/commune/{code_insee}')

    diag = _get_diagnostic_for_commune(code_insee)
    nom_commune = (diag or {}).get('nom_commune', code_insee)

    db = _get_db()
    existing = db.execute(
        "SELECT id FROM commune_accounts WHERE code_insee=?", (code_insee,)
    ).fetchone()

    if existing:
        # Mettre à jour le user_id si non assigné
        db.execute(
            "UPDATE commune_accounts SET user_id=? WHERE code_insee=? AND user_id IS NULL",
            (user['id'], code_insee)
        )
    else:
        db.execute(
            "INSERT INTO commune_accounts (code_insee, nom_commune, user_id) VALUES (?,?,?)",
            (code_insee, nom_commune, user['id'])
        )
    db.commit()
    db.close()
    return redirect(f'/ao/commune/{code_insee}')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE — Injection CRM : exporter les sites d'une commune dans agriweb_prospects
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/commune/<code_insee>/inject-crm', methods=['POST'])
def inject_crm(code_insee):
    """
    Injecte tous les sites (map_assets) du diagnostic dans agriweb_prospects
    et crée automatiquement une fiche projet + 12 étapes workflow pour chacun.
    Accessible à tout utilisateur connecté.
    """
    user = _get_user()
    if not user:
        return jsonify({'error': 'Connexion requise'}), 401

    diag = _get_diagnostic_for_commune(code_insee)
    if not diag:
        return jsonify({'error': 'Diagnostic non disponible pour cette commune'}), 404

    nom_commune = diag.get('nom_commune', code_insee)
    dept = code_insee[:2] if len(code_insee) >= 2 else ''
    assets = diag.get('map_assets', [])

    if not assets:
        return jsonify({'error': 'Aucun site géolocalisé dans ce diagnostic'}), 404

    try:
        from database_adapter import execute_query
        from crm_routes import auto_create_project_for_prospect
    except ImportError as e:
        return jsonify({'error': f'Import CRM impossible: {e}'}), 500

    user_id = user['id']
    injected = 0
    skipped = 0
    crm_ids = []

    for asset in assets:
        lat = asset.get('lat')
        lon = asset.get('lon')
        surface = asset.get('surface') or asset.get('surface_m2') or 0
        name = asset.get('name') or asset.get('type', '')
        asset_type = asset.get('type', '')
        kwc = float(asset.get('kwc') or asset.get('puissance_kwc') or 0)

        # Normaliser le type vers les valeurs CRM (parking / toiture)
        crm_type = 'parking' if 'parking' in asset_type else 'toiture'

        # Éviter les doublons : vérifier si un prospect similaire existe déjà pour cet user
        existing = execute_query(
            '''SELECT id FROM agriweb_prospects
               WHERE user_id = %s AND commune = %s AND adresse = %s AND type = %s
               LIMIT 1''',
            (str(user_id), nom_commune, name, crm_type),
            fetch_one=True
        )
        if existing:
            skipped += 1
            continue

        result = execute_query('''
            INSERT INTO agriweb_prospects (
                type, commune, departement, adresse,
                latitude, longitude, surface_m2, surface_ha,
                data_json, user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            crm_type,
            nom_commune,
            dept,
            name,
            lat,
            lon,
            surface,
            surface / 10000 if surface else None,
            json.dumps({
                'source': 'ao_mairies',
                'code_insee': code_insee,
                'type': asset_type,
                'name': name,
                'surface_m2': surface,
                'puissance_kwc': kwc,
                'economie_annuelle': asset.get('eco') or asset.get('economie_annuelle') or 0,
                'lat': lat,
                'lon': lon,
                'geom': asset.get('geom'),
            }),
            str(user_id)
        ), fetch_one=True)

        if result and result.get('id'):
            prospect_id = result['id']
            crm_ids.append(prospect_id)
            project_id = auto_create_project_for_prospect(
                prospect_id,
                commune=nom_commune,
                adresse=name,
                user_id=user_id
            )
            # Nommer le projet avec le contexte mairie
            if project_id:
                execute_query(
                    "UPDATE project_fiches SET nom_projet = %s WHERE id = %s",
                    (f"AO Mairie {nom_commune} — {name}", project_id)
                )
            injected += 1

    return jsonify({
        'ok': True,
        'injected': injected,
        'skipped': skipped,
        'total': len(assets),
        'crm_url': '/crm',
        'message': f'{injected} site(s) injectés dans le CRM ({skipped} déjà existants).'
    })


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 3 — Créer un projet
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/projet/new', methods=['POST'])
def new_project():
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    code_insee = request.form.get('code_insee', '').strip()
    try:
        asset_index = int(request.form.get('asset_index', 0))
    except ValueError:
        asset_index = 0

    if not code_insee:
        return redirect('/ao/')

    diag = _get_diagnostic_for_commune(code_insee)
    if not diag:
        return redirect(f'/ao/commune/{code_insee}')

    top_assets = _build_all_assets(diag)
    if asset_index >= len(top_assets):
        return redirect(f'/ao/commune/{code_insee}')

    asset = top_assets[asset_index]
    nom_commune = diag.get('nom_commune', code_insee)

    db = _get_db()
    account = db.execute(
        "SELECT id, user_id FROM commune_accounts WHERE code_insee=?", (code_insee,)
    ).fetchone()

    # Isolation : interdire de créer un AO sur une commune gérée par un autre compte
    if account and account['user_id'] is not None \
            and str(account['user_id']) != str(user['id']) and not user.get('is_admin'):
        db.close()
        return "Cette commune est gérée par un autre compte.", 403

    commune_id = account['id'] if account else None
    if not commune_id:
        # Auto-créer le compte commune
        db.execute(
            "INSERT INTO commune_accounts (code_insee, nom_commune, user_id) VALUES (?,?,?)",
            (code_insee, nom_commune, user['id'])
        )
        db.commit()
        account = db.execute(
            "SELECT id FROM commune_accounts WHERE code_insee=?", (code_insee,)
        ).fetchone()
        commune_id = account['id']

    db.execute("""
        INSERT INTO ao_projects
            (commune_id, code_insee, nom_commune, asset_type, asset_name,
             surface_m2, puissance_kwc, prod_annuelle_kwh, economie_annuelle,
             lat, lon, id_parcelle, asset_json, irradiance)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        commune_id, code_insee, nom_commune,
        asset.get('type', ''), asset.get('name', ''),
        asset.get('surface_m2', 0),
        asset.get('puissance_kwc', 0),
        int(asset.get('puissance_kwc', 0) * diag.get('irradiance', 1050) * 0.85),
        asset.get('economie_annuelle', 0),
        diag.get('lat', 0), diag.get('lon', 0),
        asset.get('id_parcelle', ''),
        json.dumps(asset),
        diag.get('irradiance', 0),
    ))
    db.commit()
    proj = db.execute(
        "SELECT id FROM ao_projects WHERE code_insee=? ORDER BY created_at DESC LIMIT 1",
        (code_insee,)
    ).fetchone()
    db.close()

    return redirect(f'/ao/projet/{proj["id"]}')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 4 — Cahier des charges (page principale)
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/projet/<int:projet_id>', methods=['GET'])
def projet_detail(projet_id):
    user = _get_user()

    db = _get_db()
    p = db.execute("SELECT * FROM ao_projects WHERE id=?", (projet_id,)).fetchone()
    if not p:
        db.close()
        return "Projet introuvable", 404
    p = dict(p)

    account = db.execute(
        "SELECT * FROM commune_accounts WHERE code_insee=?", (p['code_insee'],)
    ).fetchone()
    account = dict(account) if account else None

    reponses = db.execute("""
        SELECT r.*, u.name as user_name, u.company as user_company
        FROM ao_responses r JOIN users u ON r.user_id=u.id
        WHERE r.project_id=?
        ORDER BY r.created_at DESC
    """, (projet_id,)).fetchall()
    reponses = [dict(r) for r in reponses]

    # Ma réponse si connecté
    ma_reponse = None
    if user:
        for r in reponses:
            if r['user_id'] == user['id']:
                ma_reponse = r
                break
    db.close()

    is_owner = (account and user and account.get('user_id') == user.get('id')) or \
               (user and user.get('is_admin'))

    # Isolation : un brouillon n'est visible que par son gestionnaire (ou admin)
    if p.get('statut') == 'brouillon' and not is_owner:
        return "Projet introuvable", 404

    # Contexte légal selon le type
    is_parking = 'parking' in p.get('asset_type', '')
    surf = p.get('surface_m2') or 0

    if is_parking:
        if surf >= 10000:
            legal_urgence = 'URGENT — Obligation avant juillet 2026'
            legal_color = '#f87171'
            legal_ref = 'Art. L.111-19-1 CU — Parkings > 10 000 m²'
        elif surf >= 1500:
            legal_urgence = 'Obligation avant juillet 2028'
            legal_color = '#fbbf24'
            legal_ref = 'Art. L.111-19-1 CU — Parkings 1 500 à 10 000 m²'
        else:
            legal_urgence = ''
            legal_color = '#64748b'
            legal_ref = 'Art. L.111-19-1 CU'
    else:
        if surf >= 500:
            legal_urgence = 'Obligation avant janvier 2028'
            legal_color = '#fbbf24'
            legal_ref = 'Art. L.171-5 CCH — Bâtiments publics ≥ 500 m²'
        else:
            legal_urgence = ''
            legal_color = '#64748b'
            legal_ref = 'Art. L.171-5 CCH'

    # Récupérer lat/lon précis + géométrie polygone depuis map_assets
    asset_lat = p.get('lat') or 0
    asset_lon = p.get('lon') or 0
    asset_geom = None
    try:
        diag_for_map = _get_diagnostic_for_commune(p['code_insee'])
        if diag_for_map:
            asset_name = p.get('asset_name', '')
            for ma in diag_for_map.get('map_assets', []):
                if ma.get('name') == asset_name:
                    asset_lat = ma['lat']
                    asset_lon = ma['lon']
                    asset_geom = ma.get('geom')
                    break
    except Exception:
        pass

    html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cahier des charges — {{ p.asset_name or p.asset_type }} — {{ p.nom_commune }}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>""" + _CSS + """
.cdc-header{background:linear-gradient(135deg,rgba(255,183,0,.15),rgba(102,126,234,.1));
            border-radius:16px;padding:28px 32px;margin-bottom:24px}
.cdc-header h1{font-size:22px;font-weight:800;margin-bottom:6px}
.cdc-header .sub{color:#94a3b8;font-size:14px}
#projet-minimap{width:100%;height:200px;border-radius:10px;overflow:hidden;
  border:1.5px solid rgba(255,183,0,.25);box-shadow:0 4px 20px rgba(0,0,0,.4)}
.minimap-wrap{flex-shrink:0;width:280px}
@media(max-width:700px){.minimap-wrap{width:100%}}
.step{counter-increment:step}
.steps{counter-reset:step}
.steps .step-header{display:flex;align-items:center;gap:12px;margin:28px 0 14px;
                     font-size:14px;font-weight:700;color:#ffb700}
.steps .step-header::before{content:counter(step);
  width:28px;height:28px;border-radius:50%;background:#ffb700;color:#0a0e27;
  display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;flex-shrink:0}
</style></head><body>
<div class="topbar">
  <h1>📋 Cahier des charges</h1>
  <span>{{ p.nom_commune }}</span>
  """ + _NAV_LINKS + """
</div>
<div class="container">

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}{% for cat, msg in messages %}
  <div class="alert alert-{{ 'success' if cat == 'success' else 'info' }}">{{ msg }}</div>
  {% endfor %}{% endif %}{% endwith %}

  <!-- Header -->
  <div class="cdc-header">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px">
      <!-- LEFT: titre + badges + boutons -->
      <div style="flex:1;min-width:220px">
        <div style="font-size:12px;color:#ffb700;font-weight:700;text-transform:uppercase;margin-bottom:6px">
          {% if is_parking %}🚗 Parking{% else %}🏛 Bâtiment public{% endif %} ·
          <span class="badge {% if p.statut=='publie' %}badge-publie{% elif p.statut=='clos' %}badge-clos{% else %}badge-draft{% endif %}">
            {% if p.statut=='publie' %}AO Publié{% elif p.statut=='clos' %}AO Clôturé{% else %}Brouillon{% endif %}
          </span>
        </div>
        <h1>{{ p.asset_name or p.asset_type }} — {{ p.nom_commune }}</h1>
        <div class="sub">{{ p.surface_m2|int }} m² · {{ "%.0f"|format(p.puissance_kwc or 0) }} kWc estimés · {{ p.code_insee }}</div>
        {% if legal_urgence %}
        <div class="urgency" style="margin-top:12px"><i class="bi bi-exclamation-triangle-fill"></i> {{ legal_urgence }}</div>
        {% endif %}
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px">
          {% if is_owner and p.statut == 'brouillon' %}
          <form method="post" action="/ao/projet/{{ p.id }}/publish">
            <button class="btn btn-gold">📤 Publier cet AO</button>
          </form>
          {% endif %}
          {% if is_owner and p.statut == 'publie' %}
          <form method="post" action="/ao/projet/{{ p.id }}/close">
            <button class="btn btn-red">Clôturer l'AO</button>
          </form>
          {% endif %}
          <button onclick="navigator.clipboard.writeText(window.location.href);alert('Lien copié!')" class="btn btn-outline btn-sm">
            🔗 Copier le lien
          </button>
        </div>
      </div>
      <!-- RIGHT: vignette satellite -->
      {% if asset_lat and asset_lon %}
      <div class="minimap-wrap">
        <div id="projet-minimap"></div>
        <div style="font-size:11px;color:#64748b;text-align:center;margin-top:5px">
          🛰 Vue satellite · {{ asset_lat|round(4) }}, {{ asset_lon|round(4) }}
        </div>
      </div>
      {% endif %}
    </div>
  </div>

  <div class="steps">

    <!-- SECTION 1 — Contexte légal -->
    <div class="step card">
      <div class="step-header">Contexte légal et obligations</div>
      <div class="legal-box">
        <h4>📜 {{ legal_ref }}</h4>
        <p>
          {% if is_parking %}
          La loi APER du 10 mars 2023 (art. L.111-19-1 du Code de l'Urbanisme) impose
          l'installation de panneaux solaires sur les ombrières couvrant au moins 50% des parkings
          extérieurs de plus de 1 500 m². Le non-respect expose la commune à des sanctions
          administratives. Ce projet s'inscrit dans le respect de cette obligation légale.
          {% else %}
          La loi APER du 10 mars 2023 (art. L.171-5 du Code de la Construction et de l'Habitation)
          impose l'installation d'un système de production d'énergie renouvelable sur les bâtiments
          publics à usage tertiaire de plus de 500 m². Ce projet permet à la commune de satisfaire
          cette obligation avant l'échéance réglementaire.
          {% endif %}
        </p>
      </div>
      {% if legal_urgence %}
      <div class="urgency" style="font-size:12px">
        <i class="bi bi-clock-fill"></i> <strong>{{ legal_urgence }}</strong> — {{ legal_ref }}
      </div>
      {% endif %}
    </div>

    <!-- SECTION 2 — Données techniques -->
    <div class="step card">
      <div class="step-header">Données techniques du site</div>
      <div class="info-grid">
        <div class="info-box">
          <div class="label">Emprise au sol réelle</div>
          <div class="val">{{ p.surface_m2|int }}</div>
          <div class="unit">m² (BD TOPO IGN)</div>
        </div>
        <div class="info-box">
          <div class="label">Puissance installable</div>
          <div class="val">{{ "%.0f"|format(p.puissance_kwc or 0) }}</div>
          <div class="unit">kWc estimés</div>
        </div>
        <div class="info-box">
          <div class="label">Production estimée</div>
          <div class="val">{{ "{:,}".format(p.prod_annuelle_kwh or 0)|replace(",","\u00a0") }}</div>
          <div class="unit">kWh/an (PVGIS)</div>
        </div>
        <div class="info-box">
          <div class="label">Irradiance locale</div>
          <div class="val">{{ (p.irradiance or 0)|int }}</div>
          <div class="unit">kWh/m²/an (PVGIS)</div>
        </div>
        <div class="info-box">
          <div class="label">Référence parcelle</div>
          <div class="val" style="font-size:14px">{{ p.id_parcelle or '—' }}</div>
          <div class="unit">MAJIC (cadastre)</div>
        </div>
      </div>
      {% if p.lat and p.lon %}
      <div style="margin-top:16px">
        <a href="/rapport_commune?code_insee={{ p.code_insee }}&lat={{ p.lat }}&lon={{ p.lon }}"
           target="_blank" class="btn btn-outline btn-sm">
          🗺 Voir la carte du site →
        </a>
      </div>
      {% endif %}
    </div>

    <!-- SECTION 3 — Exigences -->
    <div class="step card">
      <div class="step-header">Exigences de la consultation</div>
      <table>
        <thead><tr><th>Critère</th><th>Exigence minimale</th><th>Recommandé</th></tr></thead>
        <tbody>
        <tr>
          <td><strong>Garantie décennale</strong></td>
          <td><span class="badge badge-publie">Obligatoire</span></td>
          <td>Attestation d'assureur</td>
        </tr>
        <tr>
          <td><strong>Qualification RGE</strong></td>
          <td><span class="badge badge-publie">Obligatoire</span></td>
          <td>QualiPV Bât ou QualiPV Elec ≥ 36 kWc</td>
        </tr>
        <tr>
          <td><strong>Assurance RC Pro</strong></td>
          <td><span class="badge badge-publie">Obligatoire</span></td>
          <td>Min. 1 M€ par sinistre</td>
        </tr>
        <tr>
          <td><strong>Expérience</strong></td>
          <td><span class="badge badge-draft">Recommandé</span></td>
          <td>≥ 3 réalisations similaires</td>
        </tr>
        <tr>
          <td><strong>Garanties modules</strong></td>
          <td><span class="badge badge-draft">Recommandé</span></td>
          <td>25 ans performance linéaire ≥ 80%</td>
        </tr>
        <tr>
          <td><strong>Contrat maintenance</strong></td>
          <td><span class="badge badge-draft">Recommandé</span></td>
          <td>Monitoring + intervention sous 48h</td>
        </tr>
        </tbody>
      </table>
    </div>

    <!-- SECTION 4 — Critères de sélection -->
    <div class="step card">
      <div class="step-header">Critères de sélection des offres</div>
      <table>
        <thead><tr><th>Critère</th><th>Pondération</th><th>Sous-critères</th></tr></thead>
        <tbody>
        <tr>
          <td><strong>💶 Prix global HT</strong></td>
          <td><span class="badge badge-bat" style="font-size:13px">60 %</span></td>
          <td style="font-size:12px;color:#94a3b8">Coût €/kWc installé, prix clé en main</td>
        </tr>
        <tr>
          <td><strong>⏱ Délai de réalisation</strong></td>
          <td><span class="badge badge-bat" style="font-size:13px">20 %</span></td>
          <td style="font-size:12px;color:#94a3b8">Semaines de délai annoncées</td>
        </tr>
        <tr>
          <td><strong>🏆 Références et expérience</strong></td>
          <td><span class="badge badge-bat" style="font-size:13px">20 %</span></td>
          <td style="font-size:12px;color:#94a3b8">Nb réalisations similaires, certifications</td>
        </tr>
        </tbody>
      </table>
      <p style="font-size:12px;color:#64748b;margin-top:12px">
        Ces critères sont indicatifs et préparatoires. La commune reste libre de définir ses critères
        définitifs lors de la publication de l'appel d'offres officiel sur son profil acheteur certifié
        (Marché Sécurisé, AWS-Achat, etc.).
      </p>
      {% if p.deadline or p.budget_max or p.notes_mairie %}
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid rgba(255,255,255,.06)">
        <div style="font-size:12px;font-weight:700;color:#ffb700;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px">Conditions fixées par la commune</div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;font-size:13px">
          {% if p.deadline %}<span style="color:#e8eaed">📅 Deadline : <strong>{{ p.deadline }}</strong></span>{% endif %}
          {% if p.budget_max %}<span style="color:#e8eaed">💶 Budget max : <strong>{{ "{:,}".format(p.budget_max)|replace(",","\u00a0") }} € HT</strong></span>{% endif %}
        </div>
        {% if p.notes_mairie %}
        <div style="margin-top:10px;background:rgba(255,183,0,.06);border:1px solid rgba(255,183,0,.15);border-radius:8px;padding:12px;font-size:13px;color:#cbd5e1">
          {{ p.notes_mairie }}
        </div>
        {% endif %}
      </div>
      {% endif %}
    </div>

  </div><!-- /steps -->

  <!-- Répondre à l'AO -->
  {% if p.statut == 'publie' and not is_owner %}
  <div class="card" style="border-color:rgba(255,183,0,.3)">
    <h2>📝 Répondre à cet appel d'offres</h2>
    {% if not user %}
    <div class="alert alert-info">
      <a href="/auth/login">Connectez-vous</a> ou
      <a href="/auth/register">inscrivez-vous</a> pour soumettre une réponse.
    </div>
    {% elif ma_reponse %}
    <div class="alert alert-success">
      ✅ Vous avez déjà soumis une réponse le {{ ma_reponse.created_at|string|truncate(16,killwords=True,end='') }}.
      Statut : <strong>{{ ma_reponse.statut }}</strong>
    </div>
    {% else %}
    <form method="post" action="/ao/projet/{{ p.id }}/repondre">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
        <div class="form-group">
          <label>Entreprise</label>
          <input type="text" name="company" value="{{ user.company or '' }}" required>
        </div>
        <div class="form-group">
          <label>Prix €/kWc installé (HT)</label>
          <input type="number" name="prix_kwc" step="10" min="0" placeholder="Ex : 1200" required>
        </div>
        <div class="form-group">
          <label>Délai de réalisation (semaines)</label>
          <input type="number" name="delai_semaines" min="1" placeholder="Ex : 12" required>
        </div>
        <div class="form-group">
          <label>Références similaires</label>
          <input type="text" name="experience" placeholder="Ex : 3 réalisations sur mairies 200-500 kWc">
        </div>
      </div>
      <div class="form-group">
        <label>Message (motivations, approche technique)</label>
        <textarea name="message" rows="4" placeholder="Présentez votre approche..."></textarea>
      </div>
      <button type="submit" class="btn btn-gold">📤 Soumettre ma réponse</button>
    </form>
    {% endif %}
  </div>
  {% endif %}

  <!-- Réponses reçues (visible uniquement par le propriétaire) -->
  {% if is_owner and reponses %}
  <div class="card">
    <h2>Réponses reçues ({{ reponses|length }})</h2>
    <table>
      <thead><tr>
        <th>Installateur</th><th>Entreprise</th><th>Prix/kWc</th>
        <th>Délai</th><th>Soumis le</th><th>Statut</th><th>Actions</th>
      </tr></thead>
      <tbody>
      {% for r in reponses %}
      <tr>
        <td>{{ r.user_name }}</td>
        <td>{{ r.user_company or r.company or '—' }}</td>
        <td><strong>{{ r.prix_kwc|int if r.prix_kwc else '—' }} €/kWc</strong></td>
        <td>{{ r.delai_semaines or '—' }} sem.</td>
        <td style="font-size:12px;color:#64748b">{{ r.created_at|string|truncate(16,killwords=True,end='') }}</td>
        <td><span class="badge {% if r.statut=='acceptee' %}badge-publie{% elif r.statut=='rejetee' %}badge-clos{% else %}badge-draft{% endif %}">
          {% if r.statut=='acceptee' %}✓ Acceptée{% elif r.statut=='rejetee' %}✗ Rejetée{% else %}En attente{% endif %}
        </span></td>
        <td style="display:flex;gap:6px;flex-wrap:wrap">
          {% if r.statut != 'acceptee' %}
          <form method="post" action="/ao/reponse/{{ r.id }}/statut">
            <input type="hidden" name="statut" value="acceptee">
            <input type="hidden" name="projet_id" value="{{ p.id }}">
            <button class="btn btn-green btn-sm">✓ Accepter</button>
          </form>
          {% endif %}
          {% if r.statut != 'rejetee' %}
          <form method="post" action="/ao/reponse/{{ r.id }}/statut">
            <input type="hidden" name="statut" value="rejetee">
            <input type="hidden" name="projet_id" value="{{ p.id }}">
            <button class="btn btn-red btn-sm">✗ Rejeter</button>
          </form>
          {% endif %}
        </td>
      </tr>
      {% if r.message %}
      <tr>
        <td colspan="7" style="font-size:12px;color:#94a3b8;padding-left:24px;background:rgba(255,255,255,.02)">
          <em>💬 {{ r.message }}</em>
        </td>
      </tr>
      {% endif %}
      {% if r.experience %}
      <tr>
        <td colspan="7" style="font-size:12px;color:#64748b;padding-left:24px;background:rgba(255,255,255,.02)">
          🏆 Références : {{ r.experience }}
        </td>
      </tr>
      {% endif %}
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <!-- Édition deadline + notes (mairie propriétaire) -->
  {% if is_owner and p.statut != 'clos' %}
  <div class="card">
    <h2>⚙️ Paramètres de l'appel d'offres</h2>
    <form method="post" action="/ao/projet/{{ p.id }}/edit" style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
      <div class="form-group">
        <label>Date limite de réponse</label>
        <input type="date" name="deadline" value="{{ p.deadline or '' }}">
      </div>
      <div class="form-group">
        <label>Budget maximum indicatif (€ HT)</label>
        <input type="number" name="budget_max" min="0" step="1000" value="{{ p.budget_max or '' }}" placeholder="Laisser vide si non défini">
      </div>
      <div class="form-group" style="grid-column:1/-1">
        <label>Notes / précisions pour les installateurs</label>
        <textarea name="notes_mairie" rows="3" placeholder="Contraintes d'accès, horaires de chantier, spécificités techniques...">{{ p.notes_mairie or '' }}</textarea>
      </div>
      <div style="grid-column:1/-1">
        <button type="submit" class="btn btn-gold">💾 Enregistrer</button>
      </div>
    </form>
  </div>
  {% endif %}

  <div style="margin-top:16px">
    <a href="/ao/commune/{{ p.code_insee }}" class="btn btn-gray btn-sm">← Retour à {{ p.nom_commune }}</a>
    <a href="/ao/" class="btn btn-gray btn-sm" style="margin-left:8px">← Tous les AO</a>
  </div>

</div>
{% if asset_lat and asset_lon %}
<script>
(function(){
  var lat={{ asset_lat }}, lon={{ asset_lon }};
  var geom={{ asset_geom | tojson }};
  var assetType='{{ 'parking' if is_parking else 'batiment' }}';
  var map=L.map('projet-minimap',{zoomControl:false,scrollWheelZoom:false,dragging:false,doubleClickZoom:false,attributionControl:false});
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20}).addTo(map);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',{opacity:0.5,maxZoom:20}).addTo(map);
  var fill=assetType==='parking'?'#2563eb':'#a855f7';
  var stroke=assetType==='parking'?'#60a5fa':'#c084fc';
  if(geom && geom.coordinates){
    var layer=L.geoJSON({type:'Feature',geometry:geom},{
      style:function(){return{color:stroke,weight:2.5,fillColor:fill,fillOpacity:.55};}
    }).addTo(map);
    map.fitBounds(layer.getBounds(),{padding:[20,20]});
  } else {
    map.setView([lat,lon],17);
    L.circleMarker([lat,lon],{radius:10,color:stroke,fillColor:fill,fillOpacity:.7,weight:2.5}).addTo(map);
  }
})();
</script>
{% endif %}
</body></html>"""

    from flask import render_template_string as rts
    return rts(
        html,
        p=p, user=user, account=account,
        reponses=reponses, ma_reponse=ma_reponse,
        is_owner=is_owner, is_parking=is_parking,
        legal_urgence=legal_urgence, legal_ref=legal_ref,
        asset_lat=asset_lat, asset_lon=asset_lon, asset_geom=asset_geom,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5 — Publier / Clôturer
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/projet/<int:projet_id>/publish', methods=['POST'])
def publish_project(projet_id):
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    db = _get_db()
    p = db.execute("SELECT * FROM ao_projects WHERE id=?", (projet_id,)).fetchone()
    if not p:
        db.close()
        return "Projet introuvable", 404
    p = dict(p)

    account = db.execute(
        "SELECT * FROM commune_accounts WHERE code_insee=?", (p['code_insee'],)
    ).fetchone()
    account = dict(account) if account else {}

    is_owner = (account.get('user_id') == user['id']) or user.get('is_admin')
    if not is_owner:
        db.close()
        return "Accès refusé", 403

    db.execute(
        "UPDATE ao_projects SET statut='publie', published_at=NOW() WHERE id=?",
        (projet_id,)
    )
    db.commit()
    db.close()
    return redirect(f'/ao/projet/{projet_id}')


@commune_ao_bp.route('/projet/<int:projet_id>/close', methods=['POST'])
def close_project(projet_id):
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    db = _get_db()
    p = db.execute("SELECT * FROM ao_projects WHERE id=?", (projet_id,)).fetchone()
    if not p:
        db.close()
        return "Projet introuvable", 404
    p = dict(p)

    account = db.execute(
        "SELECT * FROM commune_accounts WHERE code_insee=?", (p['code_insee'],)
    ).fetchone()
    account = dict(account) if account else {}

    is_owner = (account.get('user_id') == user['id']) or user.get('is_admin')
    if not is_owner:
        db.close()
        return "Accès refusé", 403

    db.execute("UPDATE ao_projects SET statut='clos' WHERE id=?", (projet_id,))
    db.commit()
    db.close()
    return redirect(f'/ao/projet/{projet_id}')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5b — Éditer deadline / notes / budget d'un projet
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/projet/<int:projet_id>/edit', methods=['POST'])
def edit_project(projet_id):
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    db = _get_db()
    p = db.execute("SELECT * FROM ao_projects WHERE id=?", (projet_id,)).fetchone()
    if not p:
        db.close()
        return "Projet introuvable", 404
    p = dict(p)

    account = db.execute(
        "SELECT * FROM commune_accounts WHERE code_insee=?", (p['code_insee'],)
    ).fetchone()
    account = dict(account) if account else {}
    if account.get('user_id') != user['id'] and not user.get('is_admin'):
        db.close()
        return "Accès refusé", 403

    deadline    = request.form.get('deadline', '').strip() or None
    notes       = request.form.get('notes_mairie', '').strip() or None
    try:
        budget = int(request.form.get('budget_max') or 0) or None
    except (ValueError, TypeError):
        budget = None

    db.execute(
        "UPDATE ao_projects SET deadline=?, notes_mairie=?, budget_max=? WHERE id=?",
        (deadline, notes, budget, projet_id)
    )
    db.commit()
    db.close()
    return redirect(f'/ao/projet/{projet_id}')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 5c — Accepter / Rejeter une réponse installateur
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/reponse/<int:reponse_id>/statut', methods=['POST'])
def reponse_statut(reponse_id):
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    statut     = request.form.get('statut', '').strip()
    projet_id  = request.form.get('projet_id', '0')
    if statut not in ('acceptee', 'rejetee', 'soumise'):
        return "Statut invalide", 400

    db = _get_db()
    r = db.execute("SELECT project_id FROM ao_responses WHERE id=?", (reponse_id,)).fetchone()
    if not r:
        db.close()
        return "Réponse introuvable", 404

    p = db.execute("SELECT code_insee FROM ao_projects WHERE id=?", (r['project_id'],)).fetchone()
    if not p:
        db.close()
        return "Projet introuvable", 404

    account = db.execute(
        "SELECT user_id FROM commune_accounts WHERE code_insee=?", (p['code_insee'],)
    ).fetchone()
    if not account or (account['user_id'] != user['id'] and not user.get('is_admin')):
        db.close()
        return "Accès refusé", 403

    db.execute("UPDATE ao_responses SET statut=? WHERE id=?", (statut, reponse_id))
    db.commit()
    db.close()
    return redirect(f'/ao/projet/{r["project_id"]}')


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 6 — Répondre à un AO
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/projet/<int:projet_id>/repondre', methods=['POST'])
def repondre(projet_id):
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    db = _get_db()
    p = db.execute("SELECT statut FROM ao_projects WHERE id=?", (projet_id,)).fetchone()
    if not p or p['statut'] != 'publie':
        db.close()
        return redirect(f'/ao/projet/{projet_id}')

    # Éviter les doublons
    existing = db.execute(
        "SELECT id FROM ao_responses WHERE project_id=? AND user_id=?",
        (projet_id, user['id'])
    ).fetchone()
    if existing:
        db.close()
        return redirect(f'/ao/projet/{projet_id}')

    try:
        prix_kwc = float(request.form.get('prix_kwc') or 0)
        delai = int(request.form.get('delai_semaines') or 0)
    except (ValueError, TypeError):
        prix_kwc, delai = 0.0, 0

    db.execute("""
        INSERT INTO ao_responses
            (project_id, user_id, company, message, prix_kwc, delai_semaines, experience)
        VALUES (?,?,?,?,?,?,?)
    """, (
        projet_id, user['id'],
        request.form.get('company', user.get('company', '')),
        request.form.get('message', ''),
        prix_kwc, delai,
        request.form.get('experience', ''),
    ))
    db.execute(
        "UPDATE ao_projects SET nb_reponses = nb_reponses + 1 WHERE id=?",
        (projet_id,)
    )
    db.commit()
    db.close()
    flash('✅ Votre réponse a bien été enregistrée. La commune en sera notifiée.', 'success')
    return redirect(f'/ao/projet/{projet_id}')
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/mes-reponses', methods=['GET'])
def mes_reponses():
    user = _get_user()
    if not user:
        return redirect('/auth/login')

    db = _get_db()
    rows = db.execute("""
        SELECT r.*, p.nom_commune, p.asset_name, p.asset_type,
               p.puissance_kwc, p.statut as ao_statut, p.code_insee
        FROM ao_responses r
        JOIN ao_projects p ON r.project_id = p.id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
    """, (user['id'],)).fetchall()
    db.close()
    reponses = [dict(r) for r in rows]

    html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mes réponses AO — HeliaPV</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<style>""" + _CSS + """</style></head><body>
<div class="topbar">
  <h1>📝 Mes réponses aux AO</h1>
  <span>{{ user.name }}</span>
  """ + _NAV_LINKS + """
</div>
<div class="container">
  {% if not reponses %}
  <div class="empty-state">
    <div class="icon">📭</div>
    <p>Vous n'avez pas encore répondu à un appel d'offres.<br>
       <a href="/ao/">Voir les AO disponibles →</a></p>
  </div>
  {% else %}
  <div class="card">
    <h2>{{ reponses|length }} réponse(s) soumise(s)</h2>
    <table>
      <thead><tr>
        <th>Commune</th><th>Site</th><th>Puissance</th><th>Mon prix</th>
        <th>Mon délai</th><th>AO</th><th>Ma réponse</th><th>Action</th>
      </tr></thead>
      <tbody>
      {% for r in reponses %}
      <tr>
        <td><strong>{{ r.nom_commune }}</strong></td>
        <td style="font-size:12px">{{ r.asset_name or r.asset_type }}</td>
        <td>{{ "%.0f"|format(r.puissance_kwc or 0) }} kWc</td>
        <td><strong>{{ r.prix_kwc|int if r.prix_kwc else '—' }} €/kWc</strong></td>
        <td>{{ r.delai_semaines or '—' }} sem.</td>
        <td>
          {% if r.ao_statut=='publie' %}<span class="badge badge-publie">Ouvert</span>
          {% elif r.ao_statut=='clos' %}<span class="badge badge-clos">Clôturé</span>
          {% else %}<span class="badge badge-draft">Brouillon</span>{% endif %}
        </td>
        <td>
          {% if r.statut=='acceptee' %}<span class="badge badge-publie">✓ Acceptée</span>
          {% elif r.statut=='rejetee' %}<span class="badge badge-clos">✗ Rejetée</span>
          {% else %}<span class="badge badge-draft">En attente</span>{% endif %}
        </td>
        <td><a href="/ao/projet/{{ r.project_id }}" class="btn btn-outline btn-sm">Voir →</a></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}
</div></body></html>"""

    from flask import render_template_string as rts
    return rts(html, user=user, reponses=reponses)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE SETUP TEST — crée compte mairie de test + claim commune
# Accessible une seule fois : /ao/setup-test?token=<SETUP_TOKEN>
# ─────────────────────────────────────────────────────────────────────────────

_SETUP_TOKEN = 'heliapv_tulle_test_2026'

@commune_ao_bp.route('/setup-test', methods=['GET'])
def setup_test():
    if request.args.get('token') != _SETUP_TOKEN:
        return "Accès refusé", 403

    import secrets as _sec
    import hashlib as _hl
    from datetime import datetime as _dt, timedelta as _td

    EMAIL    = 'mairie.tulle.test@heliapv.fr'
    NAME     = 'Mairie de Tulle (test)'
    COMPANY  = 'Commune de Tulle — 19000'
    PASSWORD = 'TulleTest2026!'
    INSEE    = '19272'
    NOM      = 'Tulle'

    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        c = conn.cursor()

        # Trouver l'ancien user pour nettoyer commune_accounts d'abord (FK constraint)
        c.execute('SELECT id FROM users WHERE email = ?', (EMAIL.lower(),))
        old = c.fetchone()
        if old:
            old_id = old[0]
            db = _get_db()
            db.execute('DELETE FROM commune_accounts WHERE user_id = ?', (old_id,))
            db.execute('DELETE FROM commune_accounts WHERE code_insee = ?', (INSEE,))
            db.commit()
            db.close()
        # Maintenant on peut supprimer le user
        c.execute('DELETE FROM users WHERE email = ?', (EMAIL.lower(),))
        conn.commit()

        salt     = _sec.token_hex(32)
        pw_hash  = _hl.pbkdf2_hmac('sha256', PASSWORD.encode(), salt.encode(), 100000).hex()
        trial_end = _dt.now() + _td(days=365)

        c.execute('''
            INSERT INTO users (email, name, company, password_hash, salt,
                is_email_verified, trial_start_date, trial_end_date,
                subscription_status, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (EMAIL.lower(), NAME, COMPANY, pw_hash, salt, True,
              _dt.now(), trial_end, 'trial', True))
        conn.commit()

        c.execute('SELECT id FROM users WHERE email = ?', (EMAIL.lower(),))
        user_id = c.fetchone()[0]
        conn.close()

        # Créer / mettre à jour commune_accounts
        db = _get_db()
        db.execute('DELETE FROM commune_accounts WHERE code_insee = ?', (INSEE,))
        db.commit()
        db.execute(
            'INSERT INTO commune_accounts (code_insee, nom_commune, user_id) VALUES (?, ?, ?)',
            (INSEE, NOM, user_id)
        )
        db.commit()
        db.close()

        html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Setup test OK</title>
<style>""" + _CSS + """</style></head><body>
<div class="container" style="max-width:600px;margin-top:80px">
  <div class="card">
    <h2>✅ Compte de test créé</h2>
    <table style="margin-top:12px">
      <tr><td style="color:#94a3b8;padding:8px 12px">Email</td>
          <td style="color:#f1f5f9;padding:8px 12px"><code>mairie.tulle.test@heliapv.fr</code></td></tr>
      <tr><td style="color:#94a3b8;padding:8px 12px">Mot de passe</td>
          <td style="color:#f1f5f9;padding:8px 12px"><code>TulleTest2026!</code></td></tr>
      <tr><td style="color:#94a3b8;padding:8px 12px">Commune</td>
          <td style="color:#ffb700;padding:8px 12px">Tulle (19272) — liée</td></tr>
    </table>
    <div style="margin-top:24px;display:flex;gap:12px">
      <a href="/auth/login" class="btn btn-gold">Se connecter →</a>
      <a href="/ao/commune/19272" class="btn btn-outline">Espace Tulle →</a>
    </div>
  </div>
</div></body></html>"""
        from flask import render_template_string as rts
        return rts(html)

    except Exception as e:
        return f"<pre style='color:red'>Erreur: {e}</pre>", 500


# ─────────────────────────────────────────────────────────────────────────────
# ROUTE 8 — Admin
# ─────────────────────────────────────────────────────────────────────────────

@commune_ao_bp.route('/admin', methods=['GET'])
def admin():
    user = _get_user()
    if not user or not user.get('is_admin'):
        return redirect('/auth/login')

    db = _get_db()
    stats = db.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN statut='publie' THEN 1 ELSE 0 END) as publies,
            SUM(CASE WHEN statut='clos' THEN 1 ELSE 0 END) as clos,
            SUM(CASE WHEN statut='brouillon' THEN 1 ELSE 0 END) as brouillons,
            SUM(nb_reponses) as total_reponses
        FROM ao_projects
    """).fetchone()
    stats = dict(stats) if stats else {}

    projects = db.execute("""
        SELECT p.*, COUNT(r.id) as nb_rep
        FROM ao_projects p
        LEFT JOIN ao_responses r ON r.project_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT 100
    """).fetchall()
    projects = [dict(p) for p in projects]

    communes = db.execute(
        "SELECT * FROM commune_accounts ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    communes = [dict(c) for c in communes]
    db.close()

    html = """<!DOCTYPE html><html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin AO — HeliaPV</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">
<style>""" + _CSS + """</style></head><body>
<div class="topbar">
  <h1>🔧 Admin — Marketplace AO</h1>
  """ + _NAV_LINKS + """
</div>
<div class="container">

  <div class="card">
    <h2>Vue globale</h2>
    <div class="info-grid">
      <div class="info-box"><div class="label">Total projets</div>
        <div class="val">{{ stats.total or 0 }}</div></div>
      <div class="info-box"><div class="label">Publiés</div>
        <div class="val" style="color:#10b981">{{ stats.publies or 0 }}</div></div>
      <div class="info-box"><div class="label">Clôturés</div>
        <div class="val" style="color:#ef4444">{{ stats.clos or 0 }}</div></div>
      <div class="info-box"><div class="label">Brouillons</div>
        <div class="val" style="color:#94a3b8">{{ stats.brouillons or 0 }}</div></div>
      <div class="info-box"><div class="label">Réponses totales</div>
        <div class="val" style="color:#ffb700">{{ stats.total_reponses or 0 }}</div></div>
      <div class="info-box"><div class="label">Communes inscrites</div>
        <div class="val">{{ communes|length }}</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Tous les projets</h2>
    <table>
      <thead><tr>
        <th>Commune</th><th>Site</th><th>kWc</th><th>Statut</th><th>Réponses</th><th>Créé le</th><th>Action</th>
      </tr></thead>
      <tbody>
      {% for p in projects %}
      <tr>
        <td><strong>{{ p.nom_commune }}</strong><div style="font-size:11px;color:#64748b">{{ p.code_insee }}</div></td>
        <td style="font-size:12px">{{ p.asset_name or p.asset_type }}</td>
        <td>{{ "%.0f"|format(p.puissance_kwc or 0) }}</td>
        <td>
          {% if p.statut=='brouillon' %}<span class="badge badge-draft">Brouillon</span>
          {% elif p.statut=='publie' %}<span class="badge badge-publie">Publié</span>
          {% else %}<span class="badge badge-clos">Clôturé</span>{% endif %}
        </td>
        <td style="text-align:center">{{ p.nb_rep or p.nb_reponses or 0 }}</td>
        <td style="font-size:12px;color:#64748b">{{ p.created_at|string|truncate(16,killwords=True,end='') }}</td>
        <td><a href="/ao/projet/{{ p.id }}" class="btn btn-outline btn-sm">→</a></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Comptes communes</h2>
    <table>
      <thead><tr><th>INSEE</th><th>Commune</th><th>User ID</th><th>Créé le</th><th>Action</th></tr></thead>
      <tbody>
      {% for c in communes %}
      <tr>
        <td>{{ c.code_insee }}</td>
        <td>{{ c.nom_commune }}</td>
        <td style="color:#64748b">{{ c.user_id or '—' }}</td>
        <td style="font-size:12px;color:#64748b">{{ c.created_at|string|truncate(16,killwords=True,end='') }}</td>
        <td><a href="/ao/commune/{{ c.code_insee }}" class="btn btn-outline btn-sm">→</a></td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

</div></body></html>"""

    from flask import render_template_string as rts
    return rts(html, user=user, stats=stats, projects=projects, communes=communes)
