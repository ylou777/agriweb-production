"""
Moteur de campagne email — 36 000 mairies de France
=====================================================
Fonctionnalités :
  - Import CSV/Excel de la base mairies (nom, email, code_insee, dept, population, maire)
  - Diagnostic solaire MAJIC (parcelles municipales via PostgreSQL Railway)
  - Géométries cadastrales via IGN Apicarto
  - Parkings via GeoServer (parkings_sup500m2) + fallback OSM Overpass
  - Envoi SMTP throttlé (OVH) avec personnalisation et plan cartographique
  - Tracking ouverture (pixel 1×1) + clic (redirect)
  - Gestion des désabonnements (RGPD)
  - SQLite campaign DB (statuts, bounces, stats, diagnostic_json)
"""

import os
import csv
import json
import time
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
import threading
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid, formatdate

# ── Configuration ──────────────────────────────────────────────────────────────
RATE_LIMIT       = int(os.environ.get('CAMPAIGN_RATE_PER_HOUR', 200))   # emails/heure
BATCH_SIZE       = 10                                                    # emails par batch
BATCH_DELAY      = 3600 / RATE_LIMIT * BATCH_SIZE                       # secondes entre batchs
BASE_URL         = os.environ.get('BASE_URL', 'https://app.heliapv.fr')

# ── DB helpers — PostgreSQL (persistant sur Railway) ──────────────────────────

class _RowWrapper(dict):
    """Dict qui supporte aussi l'accès par index entier (compat sqlite3.Row)."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class _CursorWrapper:
    """Cursor psycopg2 avec API proche de sqlite3."""
    def __init__(self, cur):
        self._cur = cur

    def _pg_sql(self, sql):
        return (sql
                .replace('?', '%s')
                .replace("datetime('now')", 'NOW()')
                .replace('INSERT OR IGNORE INTO', 'INSERT INTO'))

    def execute(self, sql, params=()):
        self._cur.execute(self._pg_sql(sql), params)
        return self

    def executemany(self, sql, seq):
        self._cur.executemany(self._pg_sql(sql), seq)
        return self

    def fetchone(self):
        row = self._cur.fetchone()
        return _RowWrapper(row) if row is not None else None

    def fetchall(self):
        return [_RowWrapper(r) for r in self._cur.fetchall()]

    def __iter__(self):
        return (lambda: (_RowWrapper(r) for r in self._cur))()


class _PgConn:
    """Connexion PostgreSQL wrappée pour ressembler à sqlite3.Connection."""
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, params=()):
        cur = self._conn.cursor(cursor_factory=RealDictCursor)
        wrapper = _CursorWrapper(cur)
        wrapper.execute(sql, params)
        return wrapper

    def cursor(self):
        return _CursorWrapper(self._conn.cursor(cursor_factory=RealDictCursor))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def get_db() -> _PgConn:
    """Retourne une connexion PostgreSQL wrappée (remplace SQLite)."""
    from mairies_diagnostic import _pg
    return _PgConn(_pg())


def init_db():
    conn = get_db()
    stmts = [
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            subject     TEXT NOT NULL,
            created_at  TIMESTAMP DEFAULT NOW(),
            started_at  TIMESTAMP,
            finished_at TIMESTAMP,
            status      TEXT DEFAULT 'draft',
            total       INTEGER DEFAULT 0,
            sent        INTEGER DEFAULT 0,
            opened      INTEGER DEFAULT 0,
            clicked     INTEGER DEFAULT 0,
            bounced     INTEGER DEFAULT 0,
            unsub       INTEGER DEFAULT 0
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS recipients (
            id               TEXT PRIMARY KEY,
            campaign_id      TEXT NOT NULL REFERENCES campaigns(id),
            email            TEXT NOT NULL,
            nom_commune      TEXT,
            code_insee       TEXT,
            departement      TEXT,
            population       INTEGER,
            nom_maire        TEXT,
            lat              DOUBLE PRECISION,
            lon              DOUBLE PRECISION,
            irradiance       DOUBLE PRECISION,
            diagnostic_json  TEXT,
            plan_clicked_at  TIMESTAMP,
            status           TEXT DEFAULT 'pending',
            sent_at          TIMESTAMP,
            opened_at        TIMESTAMP,
            clicked_at       TIMESTAMP,
            error            TEXT,
            pdf_unlocked     BOOLEAN DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS unsubscribes (
            email       TEXT PRIMARY KEY,
            unsub_at    TIMESTAMP DEFAULT NOW(),
            campaign_id TEXT
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_recipients_campaign ON recipients(campaign_id)",
        "CREATE INDEX IF NOT EXISTS idx_recipients_status   ON recipients(campaign_id, status)",
    ]
    for s in stmts:
        conn.execute(s)
    conn.commit()
    # Migration : colonne pdf_unlocked (tables existantes)
    try:
        conn.execute("ALTER TABLE recipients ADD COLUMN pdf_unlocked BOOLEAN DEFAULT FALSE")
        conn.commit()
    except Exception:
        pass  # Colonne déjà présente
    conn.close()


# ── Import CSV mairies ─────────────────────────────────────────────────────────

def import_mairies_csv(filepath: str, campaign_id: str, encoding='utf-8') -> int:
    """
    Importe un CSV de mairies dans la table recipients.
    Colonnes attendues (flexibles, auto-détectées) :
      email, nom_commune / commune / nom, code_insee / insee,
      departement / dept / dep, population / pop, nom_maire / maire
    Retourne le nombre de lignes importées.
    """
    init_db()

    ALIASES = {
        'email':       ['email', 'mail', 'courriel', 'adresse_mail'],
        'nom_commune': ['nom_commune', 'commune', 'nom', 'libelle', 'ville'],
        'code_insee':  ['code_insee', 'insee', 'code_commune', 'codecommune'],
        'departement': ['departement', 'dept', 'dep', 'num_dep', 'code_dep'],
        'population':  ['population', 'pop', 'nb_habitants'],
        'nom_maire':   ['nom_maire', 'maire', 'prenom_maire', 'elu'],
        'lat':         ['lat', 'latitude', 'y'],
        'lon':         ['lon', 'lng', 'longitude', 'x'],
    }

    def _map_headers(headers):
        mapping = {}
        for col, aliases in ALIASES.items():
            for h in headers:
                if h.strip().lower().replace(' ', '_') in aliases:
                    mapping[col] = h
                    break
        return mapping

    rows_inserted = 0
    conn = get_db()
    try:
        with open(filepath, newline='', encoding=encoding, errors='replace') as f:
            # Détecter le délimiteur automatiquement
            f.seek(0)
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',;\t|')
            except csv.Error:
                dialect = csv.excel  # type: ignore[assignment]
            reader = csv.DictReader(f, dialect=dialect)  # type: ignore[arg-type]
            if reader.fieldnames is None:
                raise ValueError("CSV vide ou non lisible")

            header_map = _map_headers(reader.fieldnames or [])
            if 'email' not in header_map:
                raise ValueError("Colonne 'email' introuvable dans le CSV")

            c = conn.cursor()
            for row in reader:
                em = row.get(header_map['email'], '').strip().lower()
                if not em or '@' not in em:
                    continue

                # Vérifier désabonnement
                c.execute("SELECT 1 FROM unsubscribes WHERE email = ?", (em,))
                if c.fetchone():
                    continue

                rid = str(uuid.uuid4())
                c.execute("""
                    INSERT INTO recipients
                      (id, campaign_id, email, nom_commune, code_insee, departement,
                       population, nom_maire, lat, lon)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    rid, campaign_id,
                    em,
                    row.get(header_map.get('nom_commune',''), '').strip(),
                    row.get(header_map.get('code_insee',''), '').strip(),
                    row.get(header_map.get('departement',''), '').strip(),
                    _to_int(row.get(header_map.get('population',''), '')),
                    row.get(header_map.get('nom_maire',''), '').strip(),
                    _to_float(row.get(header_map.get('lat',''), '')),
                    _to_float(row.get(header_map.get('lon',''), '')),
                ))
                rows_inserted += 1

        # Mettre à jour le total de la campagne
        conn.execute("UPDATE campaigns SET total = ? WHERE id = ?",
                     (rows_inserted, campaign_id))
        conn.commit()
    finally:
        conn.close()

    return rows_inserted


# ── Diagnostic solaire par commune (MAJIC + IGN + GeoServer + PVGIS) ──────────

def geocode_commune(nom_commune: str, code_insee: str = '') -> tuple:
    """Retourne (lat, lon) via l'API geo.api.gouv.fr."""
    try:
        params = {'q': nom_commune, 'limit': 1, 'fields': 'centre'}
        if code_insee:
            params['codeInsee'] = code_insee
        r = requests.get('https://geo.api.gouv.fr/communes', params=params, timeout=8)
        data = r.json()
        if data:
            coords = data[0].get('centre', {}).get('coordinates', [None, None])
            return coords[1], coords[0]   # lat, lon
    except Exception:
        pass
    return None, None


def build_diagnostic(recipient: dict) -> dict:
    """
    Diagnostic MAJIC + IGN + GeoServer + PVGIS pour une mairie.
    Tente le diagnostic complet via mairies_diagnostic.py.
    Fallback vers estimation simple si la BD est inaccessible.
    """
    lat = recipient.get('lat')
    lon = recipient.get('lon')
    if not lat or not lon:
        lat, lon = geocode_commune(
            recipient.get('nom_commune', ''),
            recipient.get('code_insee', '')
        )

    code_insee  = recipient.get('code_insee', '')
    nom_commune = recipient.get('nom_commune', 'votre commune')
    pop         = recipient.get('population') or 0

    # ── Tentative diagnostic MAJIC complet ──────────────────────────────────
    try:
        from mairies_diagnostic import build_commune_diagnostic, diagnostic_summary
        diag_full = build_commune_diagnostic(
            code_insee=code_insee,
            nom_commune=nom_commune,
            lat=lat,
            lon=lon,
        )
        summary = diagnostic_summary(diag_full)
        # Obligations légales
        summary['obligations'] = _build_obligations(pop)
        summary['lat'] = lat
        summary['lon'] = lon
        summary['source'] = 'majic'
        summary['_diag_full'] = diag_full  # gardé pour thumbnail email
        return summary
    except Exception as e:
        pass   # Fallback ci-dessous

    # ── Fallback : estimation simple PVGIS ───────────────────────────────────
    try:
        url = (
            "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
            f"?lat={lat}&lon={lon}&peakpower=100&loss=14&outputformat=json&browser=0"
        ) if lat and lon else None
        irr, label = 1350, 'moyen'
        if url:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            irr = data['outputs']['totals']['fixed']['H(i)_y']
            label = 'excellent' if irr > 1600 else 'bon' if irr > 1400 else 'moyen'
    except Exception:
        irr, label = 1350, 'moyen'

    nb_bat = max(3, (pop or 0) // 2000 + 2)
    puiss  = nb_bat * 30
    prod   = round(puiss * irr)
    eco    = round(prod * 0.18)
    return {
        'lat': lat, 'lon': lon,
        'irradiance': round(irr),
        'ensoleillement': label,
        'nb_parcelles': 0, 'nb_parkings': 0, 'nb_batiments': nb_bat,
        'puissance_totale_kwc': puiss,
        'prod_totale_kwh': prod,
        'economie_totale': eco,
        'co2_evite_kg': round(prod * 0.055),
        'obligations': _build_obligations(pop),
        'top_assets': [],
        'source': 'estimation',
    }


def _build_obligations(pop: int) -> list:
    obs = ["Solarisation obligatoire des bâtiments publics >500 m² d'ici 2028 (Art. L.171-4 / L.171-5 CCH)"]
    if pop > 3000:
        obs.append("Obligation d'ombrières solaires sur parkings extérieurs >1 500 m² (Art. L111-19-1 CU)")
    obs.append("Possibilité de définir des ZAER sur votre commune (Loi APER, art. 15)")
    return obs


# ── Construction email HTML ────────────────────────────────────────────────────

def build_email_html(recipient: dict, diag: dict, tracking_pixel_url: str,
                     cta_url: str, plan_url: str = '',
                     diag_full: dict = None) -> str:
    # Récupère diag_full depuis le dict si non passé explicitement
    if diag_full is None:
        diag_full = diag.get('_diag_full')

    nom      = recipient.get('nom_commune') or 'votre commune'
    maire    = recipient.get('nom_maire') or ''
    dept     = recipient.get('departement') or ''
    pop      = recipient.get('population') or 0
    if not maire:
        civility = 'Madame, Monsieur le Maire'
    elif any(x in maire.lower() for x in ['mme', 'madame', 'mme.']):
        civility = 'Madame la Maire'
    elif any(x in maire.lower() for x in ['m.', 'mr', 'monsieur']):
        civility = 'Monsieur le Maire'
    else:
        civility = 'Madame, Monsieur le Maire'

    ensoleil_label = diag.get('ensoleillement', 'moyen').capitalize()
    ensoleil_color = {'excellent': '#16a34a', 'bon': '#2563eb', 'moyen': '#d97706'}.get(
        diag.get('ensoleillement', 'moyen'), '#2563eb')

    source    = diag.get('source', 'estimation')
    nb_parc   = diag.get('nb_parcelles', 0)
    nb_park   = diag.get('nb_parkings', 0)
    nb_bat    = diag.get('nb_batiments', 0)
    top_assets = diag.get('top_assets', [])

    # ── Badge source des données ─────────────────────────────────────────────
    if source == 'majic':
        majic_badge = (
            '<div style="display:inline-block;background:#dcfce7;color:#166534;'
            'padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;'
            'margin-bottom:20px;border:1px solid #86efac;">'
            '&#10003; Analyse réalisée à partir de vos données cadastrales officielles (MAJIC / IGN)</div>'
        )
    else:
        majic_badge = (
            '<div style="display:inline-block;background:#fef9c3;color:#854d0e;'
            'padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;'
            'margin-bottom:20px;border:1px solid #fde047;">'
            'Estimation préliminaire — données complètes sur demande</div>'
        )

    # ── Bloc obligations légales (HTML structuré) ────────────────────────────
    # Vérification urgence parking > 2 500 m²
    max_park_surf = max(
        (a.get('surface_m2', 0) or 0 for a in top_assets if 'parking' in a.get('type', '')),
        default=0
    )
    park_urgent = max_park_surf >= 10000

    park_urgence_badge = (
        '<span style="background:#fef2f2;color:#b91c1c;padding:2px 8px;'
        'border-radius:4px;font-size:11px;font-weight:700;margin-left:6px;">'
        '&#9888; Échéance juillet 2026</span>'
    ) if park_urgent else ''

    oblig_batiment_rows = """
      <tr>
        <td style="padding:8px 10px;color:#475569;font-size:13px;border-bottom:1px solid #e2e8f0;">
          Bâtiments existants &#8805; 500&#x202F;m²
        </td>
        <td style="padding:8px 10px;font-size:13px;font-weight:700;color:#b45309;
                   border-bottom:1px solid #e2e8f0;white-space:nowrap;">
          1er&#x202F;janvier&#x202F;2028
        </td>
      </tr>
      <tr>
        <td style="padding:8px 10px;color:#475569;font-size:13px;">
          Bâtiments neufs / rénov. lourde &#8805; 500&#x202F;m²
        </td>
        <td style="padding:8px 10px;font-size:13px;font-weight:700;color:#b45309;white-space:nowrap;">
          Depuis jan.&#x202F;2025
        </td>
      </tr>"""

    oblig_parking_rows = f"""
      <tr>
        <td style="padding:8px 10px;color:#475569;font-size:13px;border-bottom:1px solid #e2e8f0;">
          Surface &gt; 10&#x202F;000&#x202F;m²{park_urgence_badge}
        </td>
        <td style="padding:8px 10px;font-size:13px;font-weight:700;
                   color:{'#dc2626' if park_urgent else '#b45309'};white-space:nowrap;
                   border-bottom:1px solid #e2e8f0;">
          1er&#x202F;juillet&#x202F;2026
        </td>
      </tr>
      <tr>
        <td style="padding:8px 10px;color:#475569;font-size:13px;">
          Surface &#8805; 1&#x202F;500&#x202F;m²
        </td>
        <td style="padding:8px 10px;font-size:13px;font-weight:700;color:#b45309;white-space:nowrap;">
          1er&#x202F;juillet&#x202F;2028
        </td>
      </tr>"""

    legal_block = f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0;">
      <tr>
        <td style="padding:20px 24px;">

          <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px;">
            &#9878; Bâtiments publics non résidentiels
            <span style="font-weight:400;color:#64748b;font-size:11px;">
              — Art. L.171-4 / L.171-5 CCH (Loi APER 2023 &amp; loi DDADUE 2025)
            </span>
          </div>
          <p style="color:#64748b;font-size:12px;line-height:1.6;margin:0 0 10px;">
            Tous les bâtiments appartenant à une collectivité publique et dépassant ces seuils
            doivent être équipés d'une installation de production d'énergie renouvelable
            couvrant <strong>au moins 30&#x202F;% de leur toiture</strong>.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;font-size:13px;">
            <tr style="background:#f1f5f9;">
              <th style="padding:8px 10px;text-align:left;color:#64748b;font-weight:600;">Seuil de surface</th>
              <th style="padding:8px 10px;text-align:left;color:#64748b;font-weight:600;">Échéance légale</th>
            </tr>
            {oblig_batiment_rows}
          </table>
          {'<p style="color:#475569;font-size:12px;margin:10px 0 0;"><strong>' + str(nb_bat) + ' bâtiment(s) public(s)</strong> éligible(s) identifié(s) dans le patrimoine de ' + nom + '.</p>' if nb_bat else ''}

          <div style="border-top:1px solid #e2e8f0;margin:18px 0;"></div>

          <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:4px;">
            &#128663; Parkings extérieurs
            <span style="font-weight:400;color:#64748b;font-size:11px;">
              — Art. L.111-19-1 du Code de l'Urbanisme (Loi APER 2023, art. 40)
            </span>
          </div>
          <p style="color:#64748b;font-size:12px;line-height:1.6;margin:0 0 10px;">
            Les parcs de stationnement de plein air doivent être équipés d'ombrières photovoltaïques
            sur <strong>au moins 50&#x202F;% de leur superficie</strong>. Des dérogations existent pour
            contraintes techniques ou patrimoniales dûment justifiées.
          </p>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #e2e8f0;border-radius:6px;overflow:hidden;font-size:13px;">
            <tr style="background:#f1f5f9;">
              <th style="padding:8px 10px;text-align:left;color:#64748b;font-weight:600;">Seuil de surface</th>
              <th style="padding:8px 10px;text-align:left;color:#64748b;font-weight:600;">Échéance légale</th>
            </tr>
            {oblig_parking_rows}
          </table>
          {'<p style="color:#475569;font-size:12px;margin:10px 0 0;"><strong>' + str(nb_park) + ' parking(s)</strong> éligible(s) identifié(s) dans le patrimoine de ' + nom + '.</p>' if nb_park else ''}

          <div style="border-top:1px solid #e2e8f0;margin:18px 0;"></div>
          <p style="color:#64748b;font-size:11px;line-height:1.6;margin:0;">
            &#128161; <strong>Zones d'Accélération des ENR (ZAER)</strong> — Loi APER, art.&#x202F;15 :
            les communes ont également la possibilité de délimiter des zones prioritaires pour
            l'implantation d'énergies renouvelables sur leur territoire, facilitant ainsi
            l'instruction des dossiers et l'accès aux financements.
          </p>

        </td>
      </tr>
    </table>"""

    # ── Tableau des actifs identifiés ────────────────────────────────────────
    assets_rows = ''
    for a in top_assets[:5]:
        aname   = (a.get('name') or a.get('denomination') or 'Site non nommé')[:45]
        atype   = a.get('type', '')
        asurf   = a.get('surface_m2', 0) or 0
        aeco    = a.get('economie_annuelle', 0) or 0
        apuiss  = a.get('puissance_kwc', 0) or 0
        aparc   = a.get('id_parcelle', '') or '—'
        if 'parking' in atype:
            type_label = '&#128663; Parking'
            type_color = '#0ea5e9'
        else:
            type_label = '&#127968; Bâtiment'
            type_color = '#f97316'
        assets_rows += (
            f'<tr>'
            f'<td style="padding:8px 10px;color:#1e293b;">{aname}</td>'
            f'<td style="padding:8px 10px;"><span style="color:{type_color};font-size:11px;font-weight:700;">{type_label}</span></td>'
            f'<td style="padding:8px 10px;color:#64748b;font-size:11px;font-family:monospace;white-space:nowrap;">{aparc}</td>'
            f'<td style="padding:8px 10px;text-align:right;color:#475569;">{asurf:,}&nbsp;m²</td>'
            f'<td style="padding:8px 10px;text-align:right;color:#475569;">{apuiss}&nbsp;kWc</td>'
            f'<td style="padding:8px 10px;text-align:right;color:#16a34a;font-weight:700;">{aeco:,}&nbsp;€/an</td>'
            f'</tr>'
        )

    assets_table_html = ''
    if assets_rows:
        assets_table_html = f"""
        <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:10px;">
          Sites prioritaires identifiés dans votre patrimoine
        </div>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;font-size:12px;">
          <tr style="background:#f1f5f9;">
            <th style="padding:8px 10px;text-align:left;color:#64748b;font-weight:600;">Site</th>
            <th style="padding:8px 10px;color:#64748b;font-weight:600;">Type</th>
            <th style="padding:8px 10px;color:#64748b;font-weight:600;">Parcelle MAJIC</th>
            <th style="padding:8px 10px;text-align:right;color:#64748b;font-weight:600;">Surface</th>
            <th style="padding:8px 10px;text-align:right;color:#64748b;font-weight:600;">Puissance</th>
            <th style="padding:8px 10px;text-align:right;color:#64748b;font-weight:600;">Écon./an</th>
          </tr>
          {assets_rows}
        </table>
        <p style="color:#94a3b8;font-size:11px;margin:6px 0 0;text-align:right;">
          Estimations basées sur les données PVGIS-SARAH2 (Copernicus) et les surfaces cadastrales.
        </p>"""

    # ── Carte miniature ──────────────────────────────────────────────────────
    plan_base_url = (
        f"{BASE_URL}/campaign/click-plan/{recipient['id']}"
        f"?commune={nom}&lat={recipient.get('lat','')}&lon={recipient.get('lon','')}"
        f"&dept={dept}&pop={pop}&insee={recipient.get('code_insee','')}"
    )
    map_thumbnail_html = ''
    if diag_full:
        try:
            from mairies_diagnostic import generate_map_thumbnail
            thumb_uri = generate_map_thumbnail(diag_full, width=560, height=240)
            if thumb_uri:
                overlay_btn = (
                    f'<a href="{plan_base_url}" '
                    f'style="position:absolute;bottom:10px;right:10px;'
                    f'background:#0f1b2d;color:#10b981;text-decoration:none;'
                    f'padding:7px 16px;border-radius:6px;font-size:12px;font-weight:700;'
                    f'border:1px solid #10b981;white-space:nowrap;">&#128506; Plan interactif &rarr;</a>'
                ) if plan_url else ''
                map_thumbnail_html = f"""
    <tr>
      <td style="padding:0 40px 24px;">
        <div style="font-size:13px;font-weight:700;color:#1e293b;margin-bottom:10px;">
          Cartographie des actifs solaires — {nom}
        </div>
        <div style="position:relative;border-radius:8px;overflow:hidden;
                    border:1px solid #e2e8f0;line-height:0;">
          <img src="{thumb_uri}" width="520" height="240"
               alt="Carte des actifs solaires de {nom}"
               style="display:block;width:100%;height:auto;">
          {overlay_btn}
        </div>
        <p style="color:#94a3b8;font-size:11px;margin:6px 0 0;">
          <span style="color:#10b981;">&#9632;</span>&nbsp;Parcelles MAJIC&ensp;
          <span style="color:#0ea5e9;">&#9632;</span>&nbsp;Parkings éligibles&ensp;
          <span style="color:#f97316;">&#9632;</span>&nbsp;Bâtiments publics éligibles
        </p>
      </td>
    </tr>"""
        except Exception:
            pass

    # ── Bouton plan interactif ───────────────────────────────────────────────
    plan_btn = (
        f'<a href="{plan_base_url}" '
        f'style="display:inline-block;background:#f0fdf4;color:#16a34a;'
        f'text-decoration:none;padding:11px 24px;border-radius:7px;font-weight:700;'
        f'font-size:13px;margin-right:10px;border:2px solid #16a34a;">'
        f'&#128506;&nbsp;Voir le plan interactif</a>'
        f'<span style="display:inline-block;vertical-align:middle;font-size:11px;'
        f'color:#64748b;font-style:italic;margin-left:4px;">'
        f'(prévoir&nbsp;~&nbsp;1&nbsp;min&nbsp;de&nbsp;chargement)</span>'
    ) if plan_url else ''

    # ════════════════════════════════════════════════════════════════════════
    # HTML de l'email
    # ════════════════════════════════════════════════════════════════════════
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Transition solaire — Commune de {nom}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f1f5f9;padding:28px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;
              box-shadow:0 2px 12px rgba(0,0,0,.09);max-width:600px;">

  <!-- ── HEADER ──────────────────────────────────────────────────────────── -->
  <tr>
    <td style="background:linear-gradient(135deg,#0f1b2d 0%,#163554 100%);
               padding:32px 40px;text-align:center;">
      <div style="color:#10b981;font-size:11px;font-weight:700;letter-spacing:3px;
                  text-transform:uppercase;margin-bottom:10px;">HeliaPV — Solutions Solaires</div>
      <h1 style="color:#ffffff;font-size:21px;margin:0 0 8px;font-weight:700;line-height:1.3;">
        Transition énergétique de {nom}
      </h1>
      <p style="color:#94a3b8;margin:0;font-size:13px;">
        Diagnostic solaire personnalisé{' · Département ' + dept if dept else ''}
      </p>
    </td>
  </tr>

  <!-- ── SALUTATION & ACCROCHE ───────────────────────────────────────────── -->
  <tr>
    <td style="padding:32px 40px 0px;">
      <p style="color:#1e293b;font-size:15px;line-height:1.6;margin:0 0 16px;font-weight:600;">
        {civility},
      </p>
      {majic_badge}
      <p style="color:#374151;font-size:14px;line-height:1.7;margin:14px 0 12px;">
        La transition énergétique est aujourd'hui au cœur des politiques publiques locales.
        Pour vous aider à anticiper sereinement les nouvelles obligations réglementaires,
        nous avons réalisé <strong>une analyse gratuite et personnalisée du patrimoine
        foncier de {nom}</strong>, à partir des données cadastrales officielles (MAJIC / IGN).
      </p>
      <p style="color:#374151;font-size:14px;line-height:1.7;margin:0 0 16px;">
        Notre analyse porte sur <strong>{nb_parc} parcelles communales</strong>, parmi lesquelles
        nous avons identifié <strong>{nb_bat} bâtiment(s) public(s)</strong>
        et <strong>{nb_park} parking(s)</strong> directement concernés par les obligations
        de solarisation en vigueur.
      </p>
    </td>
  </tr>

  <!-- ── OBLIGATIONS LÉGALES ─────────────────────────────────────────────── -->
  <tr>
    <td style="padding:20px 40px;">
      <div style="font-size:14px;font-weight:700;color:#0f1b2d;margin-bottom:14px;
                  padding-bottom:8px;border-bottom:2px solid #e2e8f0;">
        &#9878;&ensp;Ce que la loi impose à votre commune
      </div>
      {legal_block}
    </td>
  </tr>

  <!-- ── POTENTIEL SOLAIRE (KPIs) ─────────────────────────────────────────── -->
  <tr>
    <td style="padding:4px 40px 20px;">
      <div style="font-size:14px;font-weight:700;color:#0f1b2d;margin-bottom:14px;
                  padding-bottom:8px;border-bottom:2px solid #e2e8f0;">
        &#9728;&ensp;Potentiel solaire estimé — {nom}
      </div>
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
        <tr>
          <td width="25%" style="text-align:center;padding:18px 8px;
                                 border-right:1px solid #e2e8f0;">
            <div style="font-size:24px;font-weight:700;color:{ensoleil_color};">
              {diag.get('irradiance', 1350)}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">kWh/m²/an</div>
            <div style="font-size:10px;color:{ensoleil_color};font-weight:700;margin-top:2px;">
              {ensoleil_label}
            </div>
          </td>
          <td width="25%" style="text-align:center;padding:18px 8px;
                                 border-right:1px solid #e2e8f0;">
            <div style="font-size:24px;font-weight:700;color:#0f1b2d;">
              {diag.get('puissance_totale_kwc', 0)}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">kWc installables</div>
          </td>
          <td width="25%" style="text-align:center;padding:18px 8px;
                                 border-right:1px solid #e2e8f0;">
            <div style="font-size:24px;font-weight:700;color:#16a34a;">
              {diag.get('economie_totale', 0):,}&nbsp;€
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">économies/an</div>
          </td>
          <td width="25%" style="text-align:center;padding:18px 8px;">
            <div style="font-size:24px;font-weight:700;color:#3b82f6;">
              {diag.get('co2_evite_kg', 0):,}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;">kg CO₂ évités/an</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── SITES PRIORITAIRES ──────────────────────────────────────────────── -->
  {'<tr><td style="padding:4px 40px 20px;">' + assets_table_html + '</td></tr>' if assets_table_html else ''}

  <!-- ── CARTE MINIATURE ─────────────────────────────────────────────────── -->
  {map_thumbnail_html}

  <!-- ── NOTRE ACCOMPAGNEMENT ────────────────────────────────────────────── -->
  <tr>
    <td style="padding:4px 40px 20px;">
      <div style="font-size:14px;font-weight:700;color:#0f1b2d;margin-bottom:14px;
                  padding-bottom:8px;border-bottom:2px solid #e2e8f0;">
        &#128204;&ensp;Notre accompagnement, de A à Z
      </div>
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td width="36" valign="top" style="padding:6px 12px 10px 0;">
            <div style="width:32px;height:32px;background:#ecfdf5;border-radius:50%;
                        text-align:center;line-height:32px;font-size:15px;">&#128269;</div>
          </td>
          <td valign="top" style="padding:6px 0 10px;">
            <div style="font-size:13px;font-weight:700;color:#1e293b;">Diagnostic communal global — offert</div>
            <div style="font-size:12px;color:#64748b;line-height:1.6;margin-top:2px;">
              Identification de tous les sites éligibles sur votre territoire, estimations
              de puissance et d'économies par site. L'audit technique approfondi par toiture et parking
              (contraintes structurelles, ombrage précis, dimensionnement) fait l'objet
              d'une prestation dédiée proposée à l'étape suivante.
            </div>
          </td>
        </tr>
        <tr>
          <td width="36" valign="top" style="padding:6px 12px 10px 0;">
            <div style="width:32px;height:32px;background:#eff6ff;border-radius:50%;
                        text-align:center;line-height:32px;font-size:15px;">&#128178;</div>
          </td>
          <td valign="top" style="padding:6px 0 10px;">
            <div style="font-size:13px;font-weight:700;color:#1e293b;">Montage financier, subventions et autoconsommation collective</div>
            <div style="font-size:12px;color:#64748b;line-height:1.6;margin-top:2px;">
              Identification des aides adaptées (DSIL, DETR, CPE/tiers-financement, AO CRE) et étude d'autoconsommation collective,
              simulations de retour sur investissement et calcul du reste à charge.
            </div>
          </td>
        </tr>
        <tr>
          <td width="36" valign="top" style="padding:6px 12px 10px 0;">
            <div style="width:32px;height:32px;background:#faf5ff;border-radius:50%;
                        text-align:center;line-height:32px;font-size:15px;">&#128221;</div>
          </td>
          <td valign="top" style="padding:6px 0 10px;">
            <div style="font-size:13px;font-weight:700;color:#1e293b;">Constitution du dossier réglementaire</div>
            <div style="font-size:12px;color:#64748b;line-height:1.6;margin-top:2px;">
              Accompagnement pour la déclaration préalable, le permis de construire
              (ombrières) et la conformité avec les prescriptions ABF si nécessaire.
            </div>
          </td>
        </tr>
        <tr>
          <td width="36" valign="top" style="padding:6px 12px 10px 0;">
            <div style="width:32px;height:32px;background:#fff7ed;border-radius:50%;
                        text-align:center;line-height:32px;font-size:15px;">&#128736;</div>
          </td>
          <td valign="top" style="padding:6px 0 10px;">
            <div style="font-size:13px;font-weight:700;color:#1e293b;">Sélection d'installateurs certifiés RGE</div>
            <div style="font-size:12px;color:#64748b;line-height:1.6;margin-top:2px;">
              Mise en relation avec des entreprises locales qualifiées, appels d'offres
              et suivi jusqu'à la mise en service.
            </div>
          </td>
        </tr>
        <tr>
          <td width="36" valign="top" style="padding:6px 12px 0 0;">
            <div style="width:32px;height:32px;background:#f0fdf4;border-radius:50%;
                        text-align:center;line-height:32px;font-size:15px;">&#9889;</div>
          </td>
          <td valign="top" style="padding:6px 0 0;">
            <div style="font-size:13px;font-weight:700;color:#1e293b;">Autoconsommation collective — valorisation pour les entreprises du territoire</div>
            <div style="font-size:12px;color:#64748b;line-height:1.6;margin-top:2px;">
              Étude d'opportunité d'autoconsommation collective (Art.&nbsp;L315-2 Code de l'Énergie, Loi APER&nbsp;2023)
              : la commune devient Personne Morale Organisatrice et partage la production avec les PME,
              commerces et riverains dans un rayon de 20&nbsp;km — jusqu'à 30&ndash;60&nbsp;% d'économies
              sur la facture électrique pour chaque participant.
            </div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- ── CTA ─────────────────────────────────────────────────────────────── -->
  <tr>
    <td style="padding:10px 40px 36px;text-align:center;
               background:linear-gradient(180deg,#ffffff 0%,#f8fafc 100%);">
      <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                  padding:20px 24px;margin-bottom:20px;">
        <p style="color:#14532d;font-size:13px;line-height:1.6;margin:0 0 14px;">
          Nous avons préparé un <strong>plan interactif</strong> de vos parcelles et bâtiments
          identifiés, avec calpinage photovoltaïque et estimations financières détaillées
          pour chaque site — consultable directement depuis votre navigateur.
        </p>
        <div>
          {plan_btn}
          <a href="{cta_url}"
             style="display:inline-block;background:linear-gradient(135deg,#10b981,#059669);
                    color:#ffffff;text-decoration:none;padding:12px 28px;border-radius:7px;
                    font-weight:700;font-size:14px;letter-spacing:.3px;">
            Demander le diagnostic complet &rarr;
          </a>
        </div>
      </div>
      <p style="color:#94a3b8;font-size:12px;margin:0;">
        Réponse sous 48h &mdash; Sans engagement &mdash; Données confidentielles
      </p>
    </td>
  </tr>

  <!-- ── FOOTER ───────────────────────────────────────────────────────────── -->
  <tr>
    <td style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:18px 40px;">
      <p style="font-size:11px;color:#94a3b8;line-height:1.7;margin:0;">
        <strong style="color:#64748b;">HeliaPV</strong>
        — Logiciel de diagnostic et de pilotage de projets solaires photovoltaïques.<br>
        13 Ventenat, 23480 Saint-Sulpice-les-Champs — info@heliapv.fr<br>
        Vous recevez ce message car la commune de {nom} est concernée par
        les obligations de solarisation issues des lois Énergie-Climat et APER.<br>
        <span style="color:#b0bec5;">
          Données collectées via les registres publics (annuaire des collectivités / MAJIC / IGN).
          Conformément au RGPD, vous disposez d'un droit d'accès, de rectification et d'opposition
          en écrivant à info@heliapv.fr.
        </span><br>
        <a href="{BASE_URL}/campaign/unsub?email={recipient.get('id', '')}"
           style="color:#64748b;">Se désabonner</a>
        &nbsp;|&nbsp;
        <a href="https://app.heliapv.fr/mentions-legales" style="color:#64748b;">Mentions légales</a>
        &nbsp;|&nbsp;
        <a href="https://app.heliapv.fr" style="color:#64748b;">app.heliapv.fr</a>
      </p>
    </td>
  </tr>

</table>
</td></tr>
</table>
<!-- Pixel de suivi -->
<img src="{tracking_pixel_url}" width="1" height="1" style="display:none;" alt="">
</body>
</html>"""


# ── Moteur d'envoi ─────────────────────────────────────────────────────────────

def _smtp_connect():
    cfg = {
        'server': os.environ.get('MAIL_SERVER', 'ssl0.ovh.net'),
        'port':   int(os.environ.get('MAIL_PORT', 465)),
        'user':   os.environ.get('MAIL_USERNAME', ''),
        'pass':   os.environ.get('MAIL_PASSWORD', ''),
    }
    server = smtplib.SMTP_SSL(cfg['server'], cfg['port'])
    server.login(cfg['user'], cfg['pass'])
    return server, cfg['user']


def send_one(smtp, sender_email: str, recipient: dict, subject: str, html_body: str) -> bool:
    import re as _re, base64 as _b64
    from email.mime.image import MIMEImage

    # Extraire l'image base64 et la remplacer par CID (Gmail bloque data: URIs)
    html = html_body
    png_bytes = None
    m = _re.search(r'(data:image/png;base64,([A-Za-z0-9+/=\r\n]+))', html)
    if m:
        try:
            png_bytes = _b64.b64decode(m.group(2).replace('\n', '').replace('\r', ''))
            html = html.replace(m.group(1), 'cid:map_thumbnail')
        except Exception:
            png_bytes = None

    msg_alt = MIMEMultipart('alternative')
    msg_related = MIMEMultipart('related')
    msg = MIMEMultipart('mixed')
    msg['Subject']  = subject
    msg['From']     = formataddr(('HeliaPV — Diagnostic Solaire', sender_email))
    msg['To']       = recipient['email']
    msg['Date']     = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain='heliapv.fr')
    msg['List-Unsubscribe'] = f'<{BASE_URL}/campaign/unsub?email={recipient["id"]}>'  

    # Texte brut (fallback)
    text = (
        f"Bonjour,\n\nDiagnostic solaire gratuit pour {recipient['nom_commune']}.\n"
        f"Consultez l'offre complète : {BASE_URL}/campaign/click/{recipient['id']}\n\n"
        f"Pour vous désabonner : {BASE_URL}/campaign/unsub?email={recipient['id']}"
    )
    msg_alt.attach(MIMEText(text, 'plain', 'utf-8'))
    msg_alt.attach(MIMEText(html, 'html', 'utf-8'))
    msg_related.attach(msg_alt)

    if png_bytes:
        img_part = MIMEImage(png_bytes, _subtype='png')
        img_part.add_header('Content-ID', '<map_thumbnail>')
        img_part.add_header('Content-Disposition', 'inline', filename='carte_solaire.png')
        msg_related.attach(img_part)

    msg.attach(msg_related)

    smtp.sendmail(sender_email, [recipient['email']], msg.as_bytes())
    return True


def run_campaign(campaign_id: str, subject: str, stop_event: threading.Event = None):
    """
    Moteur principal d'envoi (exécuté dans un thread séparé).
    Envoie par batch de BATCH_SIZE avec pause throttlée.
    """
    init_db()
    conn = get_db()
    conn.execute("UPDATE campaigns SET status='running', started_at=datetime('now') WHERE id=?",
                 (campaign_id,))
    conn.commit()
    conn.close()

    smtp = None
    try:
        smtp, sender = _smtp_connect()
        while True:
            if stop_event and stop_event.is_set():
                break

            conn = get_db()
            rows = conn.execute("""
                SELECT * FROM recipients
                WHERE campaign_id=? AND status='pending'
                LIMIT ?
            """, (campaign_id, BATCH_SIZE)).fetchall()
            conn.close()

            if not rows:
                break

            for row in rows:
                if stop_event and stop_event.is_set():
                    break
                rec = dict(row)
                try:
                    diag = build_diagnostic(rec)

                    # Skip communes sans projet éligible APER (L.171-5 CCH / L111-19-1 CU)
                    if diag.get('nb_batiments', 0) + diag.get('nb_parkings', 0) == 0:
                        _mark_skipped(rec['id'], campaign_id)
                        continue

                    pixel_url = f"{BASE_URL}/campaign/open/{rec['id']}"
                    cta_url   = f"{BASE_URL}/campaign/click/{rec['id']}"
                    plan_url  = f"{BASE_URL}/campaign/plan/{rec['id']}"
                    html      = build_email_html(rec, diag, pixel_url, cta_url, plan_url)

                    # Reconnexion SMTP si session expirée (timeout OVH pendant diagnostic)
                    # OVH envoie un 221 "Service closing" après ~60s d'inactivité
                    def _reconnect():
                        nonlocal smtp, sender
                        try: smtp.quit()
                        except Exception: pass
                        smtp, sender = _smtp_connect()

                    try:
                        smtp.noop()
                    except Exception:
                        _reconnect()

                    # Envoi avec retry automatique si connexion fermée (221)
                    for _attempt in range(3):
                        try:
                            send_one(smtp, sender, rec, subject, html)
                            break
                        except (smtplib.SMTPServerDisconnected,
                                smtplib.SMTPConnectError,
                                smtplib.SMTPException) as _e:
                            if _attempt < 2:
                                _reconnect()
                            else:
                                raise

                    diag_json = json.dumps(diag, ensure_ascii=False, default=str)
                    conn = get_db()
                    conn.execute("""
                        UPDATE recipients SET status='sent', sent_at=NOW(),
                          lat=?, lon=?, irradiance=?, diagnostic_json=?
                        WHERE id=?
                    """, (diag.get('lat'), diag.get('lon'),
                          diag.get('irradiance'), diag_json, rec['id']))
                    conn.execute("UPDATE campaigns SET sent=sent+1 WHERE id=?", (campaign_id,))
                    conn.commit()
                    conn.close()

                except smtplib.SMTPRecipientsRefused:
                    _mark_error(rec['id'], campaign_id, 'bounce')
                except Exception as e:
                    _mark_error(rec['id'], campaign_id, str(e)[:200])

            # Pause throttling
            time.sleep(BATCH_DELAY)

        _finish_campaign(campaign_id, 'finished')

    except Exception as e:
        _finish_campaign(campaign_id, 'error')
        print(f"[CAMPAIGN ERROR] {e}")
    finally:
        if smtp:
            try: smtp.quit()
            except Exception: pass


def _mark_error(recipient_id, campaign_id, error):
    conn = get_db()
    status = 'bounce' if error == 'bounce' else 'error'
    conn.execute("UPDATE recipients SET status=?, error=? WHERE id=?",
                 (status, error, recipient_id))
    if status == 'bounce':
        conn.execute("UPDATE campaigns SET bounced=bounced+1 WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()


def _mark_skipped(recipient_id, campaign_id):
    """Aucun actif éligible (L.171-5 CCH) — on ne compte pas dans sent/bounced."""
    conn = get_db()
    conn.execute(
        "UPDATE recipients SET status='skipped', error='0 projets éligibles (seuils L.171-5 CCH)' WHERE id=?",
        (recipient_id,)
    )
    conn.commit()
    conn.close()


def _finish_campaign(campaign_id, status):
    conn = get_db()
    conn.execute("UPDATE campaigns SET status=?, finished_at=datetime('now') WHERE id=?",
                 (status, campaign_id))
    conn.commit()
    conn.close()


# ── API publique ───────────────────────────────────────────────────────────────

def create_campaign(name: str, subject: str) -> str:
    init_db()
    cid = str(uuid.uuid4())
    conn = get_db()
    conn.execute("INSERT INTO campaigns(id,name,subject) VALUES(?,?,?)", (cid, name, subject))
    conn.commit()
    conn.close()
    return cid


def get_campaign_stats(campaign_id: str) -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()
    if not row:
        return {}
    d = dict(row)
    total = d['total'] or 1
    d['open_rate']  = round(d['opened']  / max(d['sent'], 1) * 100, 1)
    d['click_rate'] = round(d['clicked'] / max(d['sent'], 1) * 100, 1)
    d['bounce_rate'] = round(d['bounced'] / total * 100, 1)
    d.update(get_campaign_diagnostic_summary(campaign_id))
    return d


def get_campaign_diagnostic_summary(campaign_id: str) -> dict:
    conn = get_db()
    rows = conn.execute(
        "SELECT diagnostic_json FROM recipients WHERE campaign_id=? AND diagnostic_json IS NOT NULL",
        (campaign_id,)
    ).fetchall()
    conn.close()

    summary = {
        'diag_count': 0,
        'total_nb_batiments': 0,
        'avg_nb_batiments': 0,
        'max_nb_batiments': 0,
        'total_nb_parkings': 0,
        'avg_nb_parkings': 0,
        'max_nb_parkings': 0,
        'total_nb_parcelles': 0,
        'avg_nb_parcelles': 0,
        'max_nb_parcelles': 0,
        'total_kwc': 0,
        'avg_kwc': 0,
        'max_kwc': 0,
        'total_kwh': 0,
        'avg_kwh': 0,
        'max_kwh': 0,
        'total_economies': 0,
        'avg_economies': 0,
        'max_economies': 0,
        'total_asset_surface_m2': 0,
        'avg_asset_surface_m2': 0,
        'max_asset_surface_m2': 0,
    }

    def _num(v):
        try:
            return float(v)
        except Exception:
            return 0.0

    def _asset_surface(diag):
        total = 0.0
        for asset in (diag.get('top_assets') or []):
            total += _num(asset.get('surface_m2') or asset.get('surface') or 0)
        return total

    for row in rows:
        try:
            diag = json.loads(row['diagnostic_json'])
        except Exception:
            continue
        summary['diag_count'] += 1

        nb_bat = int(_num(diag.get('nb_batiments')))
        nb_park = int(_num(diag.get('nb_parkings')))
        nb_parc = int(_num(diag.get('nb_parcelles')))
        kwc = _num(diag.get('puissance_totale_kwc'))
        kwh = _num(diag.get('prod_totale_kwh'))
        eco = _num(diag.get('economie_totale'))
        surf = _asset_surface(diag)

        summary['total_nb_batiments'] += nb_bat
        summary['total_nb_parkings'] += nb_park
        summary['total_nb_parcelles'] += nb_parc
        summary['total_kwc'] += kwc
        summary['total_kwh'] += kwh
        summary['total_economies'] += eco
        summary['total_asset_surface_m2'] += surf

        summary['max_nb_batiments'] = max(summary['max_nb_batiments'], nb_bat)
        summary['max_nb_parkings'] = max(summary['max_nb_parkings'], nb_park)
        summary['max_nb_parcelles'] = max(summary['max_nb_parcelles'], nb_parc)
        summary['max_kwc'] = max(summary['max_kwc'], kwc)
        summary['max_kwh'] = max(summary['max_kwh'], kwh)
        summary['max_economies'] = max(summary['max_economies'], eco)
        summary['max_asset_surface_m2'] = max(summary['max_asset_surface_m2'], surf)

    if summary['diag_count']:
        diag_count = summary['diag_count']
        summary['avg_nb_batiments'] = round(summary['total_nb_batiments'] / diag_count, 1)
        summary['avg_nb_parkings'] = round(summary['total_nb_parkings'] / diag_count, 1)
        summary['avg_nb_parcelles'] = round(summary['total_nb_parcelles'] / diag_count, 1)
        summary['avg_kwc'] = round(summary['total_kwc'] / diag_count, 1)
        summary['avg_kwh'] = round(summary['total_kwh'] / diag_count, 0)
        summary['avg_economies'] = round(summary['total_economies'] / diag_count, 0)
        summary['avg_asset_surface_m2'] = round(summary['total_asset_surface_m2'] / diag_count, 1)
    return summary


def list_campaigns() -> list:
    conn = get_db()
    rows = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def record_open(recipient_id: str):
    try:
        conn = get_db()
        row = conn.execute("SELECT campaign_id, status, opened_at FROM recipients WHERE id=?",
                           (recipient_id,)).fetchone()
        if row and row['status'] in ('sent', 'pending') and row['opened_at'] is None:
            conn.execute("UPDATE recipients SET status='opened', opened_at=NOW() WHERE id=?",
                         (recipient_id,))
            conn.execute("UPDATE campaigns SET opened=opened+1 WHERE id=?",
                         (row['campaign_id'],))
            conn.commit()
        conn.close()
    except Exception:
        pass


def record_click(recipient_id: str):
    try:
        conn = get_db()
        row = conn.execute("SELECT campaign_id FROM recipients WHERE id=?",
                           (recipient_id,)).fetchone()
        if row:
            conn.execute("UPDATE recipients SET status='clicked', clicked_at=NOW() WHERE id=? AND clicked_at IS NULL",
                         (recipient_id,))
            conn.execute("UPDATE campaigns SET clicked=clicked+1 WHERE id=?",
                         (row['campaign_id'],))
            conn.commit()
        conn.close()
    except Exception:
        pass


def record_unsub(recipient_id: str):
    try:
        conn = get_db()
        row = conn.execute("SELECT email, campaign_id FROM recipients WHERE id=?",
                           (recipient_id,)).fetchone()
        if row:
            conn.execute("INSERT INTO unsubscribes(email,campaign_id) VALUES(?,?) ON CONFLICT (email) DO NOTHING",
                         (row['email'], row['campaign_id']))
            conn.execute("UPDATE recipients SET status='unsub' WHERE id=?", (recipient_id,))
            conn.execute("UPDATE campaigns SET unsub=unsub+1 WHERE id=?", (row['campaign_id'],))
            conn.commit()
        conn.close()
    except Exception:
        pass


def record_click_plan(recipient_id: str):
    """Track le clic sur le lien carte interactive depuis l'email."""
    try:
        conn = get_db()
        conn.execute(
            "UPDATE recipients SET plan_clicked_at=NOW() "
            "WHERE id=? AND plan_clicked_at IS NULL",
            (recipient_id,)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Helpers internes ───────────────────────────────────────────────────────────

def _to_int(v):
    try: return int(str(v).replace(' ', '').replace('\u202f', ''))
    except: return None

def _to_float(v):
    try: return float(str(v).replace(',', '.'))
    except: return None
