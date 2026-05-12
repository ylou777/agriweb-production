"""
Routes Flask — Campagne email 36 000 mairies
=============================================
/campaign/                  → Dashboard (admin)
/campaign/new               → Créer une campagne
/campaign/<id>/import       → Upload CSV mairies
/campaign/<id>/start        → Lancer l'envoi (thread)
/campaign/<id>/stop         → Arrêter l'envoi
/campaign/<id>/stats        → JSON stats en temps réel
/campaign/open/<rid>        → Pixel tracking ouverture
/campaign/click/<rid>       → Tracking clic + redirect
/campaign/unsub             → Désabonnement RGPD
"""

import os
import threading
import uuid
from flask import (Blueprint, render_template_string, request, redirect,
                   url_for, jsonify, session, send_file, Response)
from mairies_campaign import (
    create_campaign, import_mairies_csv, run_campaign, get_campaign_stats,
    list_campaigns, record_open, record_click, record_click_plan, record_unsub, get_db, BASE_URL
)

campaign_bp = Blueprint('campaign_bp', __name__, url_prefix='/campaign')

# Thread actif par campaign_id
_running_threads: dict = {}
_stop_events: dict     = {}


# ── Auth helper ────────────────────────────────────────────────────────────────

def _is_admin():
    token = session.get('session_token') or request.cookies.get('session_token')
    if not token:
        return False
    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        c = conn.cursor()
        c.execute("""SELECT u.is_admin FROM users u
                     JOIN user_sessions s ON u.id=s.user_id
                     WHERE s.session_token=? AND s.expires_at>CURRENT_TIMESTAMP""", (token,))
        row = c.fetchone()
        conn.close()
        return bool(row and row[0])
    except Exception:
        return False


def _require_admin():
    if not _is_admin():
        return redirect('/auth/login'), True
    return None, False


# ── Pixel 1×1 GIF transparent (inline) ────────────────────────────────────────

_GIF1x1 = (
    b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!'
    b'\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


# ── Dashboard ──────────────────────────────────────────────────────────────────

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Campagne Mairies — HeliaPV</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;min-height:100vh}
  .topbar{background:#1e293b;border-bottom:1px solid #334155;padding:16px 32px;display:flex;align-items:center;gap:16px}
  .topbar h1{font-size:18px;color:#10b981}
  .topbar span{color:#94a3b8;font-size:13px}
  .container{max-width:1100px;margin:32px auto;padding:0 24px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:24px}
  .card h2{font-size:15px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px}
  .btn{display:inline-block;padding:10px 20px;border-radius:7px;font-size:13px;font-weight:600;cursor:pointer;border:none;text-decoration:none;transition:.2s}
  .btn-green{background:#10b981;color:#fff}.btn-green:hover{background:#059669}
  .btn-red{background:#ef4444;color:#fff}.btn-red:hover{background:#dc2626}
  .btn-blue{background:#3b82f6;color:#fff}.btn-blue:hover{background:#2563eb}
  .btn-gray{background:#334155;color:#cbd5e1}.btn-gray:hover{background:#475569}
  form{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}
  input,select{background:#0f1b2d;border:1px solid #475569;color:#f1f5f9;padding:9px 14px;border-radius:7px;font-size:13px}
  input:focus,select:focus{outline:none;border-color:#10b981}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{text-align:left;padding:10px 12px;color:#64748b;font-weight:600;border-bottom:1px solid #334155}
  td{padding:10px 12px;border-bottom:1px solid #1e293b;color:#cbd5e1}
  .badge{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:700}
  .badge-draft{background:#334155;color:#94a3b8}
  .badge-running{background:#10b9811a;color:#10b981;animation:pulse 1.5s infinite}
  .badge-finished{background:#2563eb1a;color:#3b82f6}
  .badge-error{background:#ef44441a;color:#ef4444}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.6}}
  .stat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-top:12px}
  .stat-box{background:#0f1b2d;border:1px solid #334155;border-radius:8px;padding:16px;text-align:center}
  .stat-box .val{font-size:26px;font-weight:700;color:#10b981}
  .stat-box .label{font-size:11px;color:#64748b;margin-top:4px}
  .progress{height:6px;background:#334155;border-radius:3px;overflow:hidden;margin-top:12px}
  .progress-bar{height:100%;background:linear-gradient(90deg,#10b981,#3b82f6);transition:width .5s}
  .dropzone{border:2px dashed #475569;border-radius:10px;padding:32px;text-align:center;cursor:pointer;transition:.2s}
  .dropzone:hover{border-color:#10b981;background:#10b9810a}
  .alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px}
  .alert-success{background:#10b9811a;border:1px solid #10b981;color:#10b981}
  .alert-error{background:#ef44441a;border:1px solid #ef4444;color:#ef4444}
</style>
</head>
<body>
<div class="topbar">
  <h1>☀ Campagne Mairies</h1>
  <span>Prospection 36 000 communes — HeliaPV</span>
</div>

<div class="container">

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
  <div class="alert alert-{{cat}}">{{msg}}</div>
  {% endfor %}
  {% endwith %}

  <!-- Nouvelle campagne -->
  <div class="card">
    <h2>Créer une campagne</h2>
    <form method="post" action="/campaign/new">
      <div><label style="color:#64748b;font-size:12px;display:block;margin-bottom:4px">Nom interne</label>
        <input name="name" placeholder="Ex: Mairies Printemps 2026" style="width:260px"></div>
      <div><label style="color:#64748b;font-size:12px;display:block;margin-bottom:4px">Objet de l'email</label>
        <input name="subject" placeholder="Ex: Diagnostic solaire gratuit pour votre commune" style="width:380px"></div>
      <button class="btn btn-green" type="submit">+ Créer</button>
    </form>
  </div>

  <!-- Liste campagnes -->
  <div class="card">
    <h2>Campagnes</h2>
    <div style="margin-bottom: 20px; display: flex; gap: 10px;">
      <a href="/campaign/export-all" class="btn btn-blue">📦 Télécharger l'export complet (CSV + JSONL)</a>
      <span style="color: #64748b; font-size: 12px; align-self: center;">Exporte tous les résultats et diagnostics de la base PostgreSQL</span>
    </div>
    <table>
      <tr>
        <th>Nom</th><th>Statut</th><th>Total</th><th>Envoyés</th>
        <th>Ouvertures</th><th>Clics</th><th>Bounce</th><th>Actions</th>
      </tr>
      {% for c in campaigns %}
      <tr>
        <td><strong>{{c.name}}</strong><br><small style="color:#64748b">{{c.subject}}</small></td>
        <td><span class="badge badge-{{c.status}}">{{c.status}}</span></td>
        <td>{{c.total}}</td>
        <td>{{c.sent}}</td>
        <td>{{c.opened}} ({{c.open_rate|default(0)}}%)</td>
        <td>{{c.clicked}} ({{c.click_rate|default(0)}}%)</td>
        <td>{{c.bounced}}</td>
        <td>
          <a href="/campaign/{{c.id}}/detail" class="btn btn-gray" style="font-size:11px;padding:6px 12px">Détail</a>
          {% if c.status in ['draft','error','finished','paused'] %}
          <a href="/campaign/{{c.id}}/import_form" class="btn btn-blue" style="font-size:11px;padding:6px 12px">Import CSV</a>
          {% endif %}
          {% if c.status in ['draft','paused','error','finished'] %}
          <a href="/campaign/{{c.id}}/start" class="btn btn-green" style="font-size:11px;padding:6px 12px">{% if c.status == 'paused' %}▶ Reprendre{% else %}▶ Lancer{% endif %}</a>
          {% elif c.status == 'running' %}
          <a href="/campaign/{{c.id}}/stop" class="btn btn-red" style="font-size:11px;padding:6px 12px">⏹ Stop</a>
          {% endif %}
        </td>
      </tr>
      {% else %}
      <tr><td colspan="8" style="text-align:center;color:#64748b;padding:24px">Aucune campagne</td></tr>
      {% endfor %}
    </table>
  </div>

</div>
<script>
// Auto-refresh pour les campagnes "running" — suspendu si l'utilisateur saisit dans un champ
if (document.querySelector('.badge-running')) {
  let userTyping = false;
  document.querySelectorAll('input, textarea, select').forEach(el => {
    el.addEventListener('focus', () => { userTyping = true; });
    el.addEventListener('blur',  () => { userTyping = false; });
  });
  setTimeout(function tick() {
    if (!userTyping) { location.reload(); return; }
    setTimeout(tick, 3000);
  }, 8000);
}
</script>
</body>
</html>"""

IMPORT_HTML = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Import CSV Mairies</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;padding:40px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:32px;max-width:600px;margin:0 auto}
  h2{color:#10b981;margin-bottom:24px}
  input[type=file]{background:#0f1b2d;border:1px solid #475569;color:#f1f5f9;padding:10px;border-radius:7px;width:100%;margin-bottom:16px}
  .btn{padding:12px 28px;border-radius:7px;font-size:14px;font-weight:600;cursor:pointer;border:none}
  .btn-green{background:#10b981;color:#fff}
  p{color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:16px}
  code{background:#0f1b2d;padding:2px 6px;border-radius:4px;font-size:12px;color:#10b981}
  a{color:#3b82f6}
</style>
</head>
<body>
<div class="card">
  <h2>Import CSV — {{campaign_name}}</h2>
  <p>Importez votre fichier CSV ou Excel (converti en CSV) contenant les mairies.</p>
  <p>Colonnes reconnues automatiquement : <code>email</code>, <code>nom_commune</code>,
     <code>code_insee</code>, <code>departement</code>, <code>population</code>,
     <code>nom_maire</code>, <code>lat</code>, <code>lon</code></p>
  <p>Séparateurs acceptés : virgule <code>,</code> point-virgule <code>;</code> tabulation</p>
  <form method="post" enctype="multipart/form-data" action="/campaign/{{campaign_id}}/import">
    <input type="file" name="csv_file" accept=".csv,.txt">
    <button class="btn btn-green" type="submit">Importer →</button>
  </form>
  <br>
  <a href="/campaign/">← Retour</a>
</div>
</body>
</html>"""

DETAIL_HTML = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Détail campagne</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;padding:32px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;max-width:900px;margin:0 auto 24px}
  h2{color:#10b981;margin-bottom:20px;font-size:16px}
  .stat-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px}
  .stat-box{background:#0f1b2d;border:1px solid #334155;border-radius:8px;padding:14px;text-align:center;cursor:pointer;transition:.15s}
  .stat-box:hover{border-color:#10b981;background:#0f1b2d;box-shadow:0 0 12px rgba(16,185,129,.15)}
  .stat-box[data-clickable=true]{cursor:pointer}.stat-box[data-clickable=true]:hover{transform:translateY(-2px)}
  .val{font-size:24px;font-weight:700;color:#10b981}.label{font-size:11px;color:#64748b;margin-top:4px}
  table{width:100%;border-collapse:collapse;font-size:12px;margin-top:16px}
  th{padding:8px 10px;color:#64748b;text-align:left;border-bottom:1px solid #334155}
  td{padding:8px 10px;color:#cbd5e1;border-bottom:1px solid #1e293b}
  .progress{height:6px;background:#334155;border-radius:3px;overflow:hidden;margin-top:16px}
  .progress-bar{height:100%;background:linear-gradient(90deg,#10b981,#3b82f6)}
  a{color:#3b82f6;font-size:13px;text-decoration:none}
</style>
</head>
<body>
<div class="card">
  <h2>{{stats.name}} — <span id="status">{{stats.status}}</span></h2>
  <div class="stat-grid">
    <div class="stat-box" data-clickable="false"><div class="val">{{stats.total}}</div><div class="label">Total</div></div>
    <div class="stat-box" data-clickable="false"><div class="val">{{stats.sent}}</div><div class="label">Envoyés</div></div>
    <a href="/campaign/{{campaign_id}}/recipients?status=opened&page=1" style="text-decoration:none">
      <div class="stat-box" data-clickable="true" {% if stats.opened > 0 %}title="Cliquez pour voir les emails ouverts"{% endif %}>
        <div class="val">{{stats.opened}}</div><div class="label">Ouvertures</div>
      </div>
    </a>
    <div class="stat-box" data-clickable="false"><div class="val">{{stats.open_rate}}%</div><div class="label">Taux ouv.</div></div>
    <a href="/campaign/{{campaign_id}}/recipients?status=clicked&page=1" style="text-decoration:none">
      <div class="stat-box" data-clickable="true" {% if stats.clicked > 0 %}title="Cliquez pour voir les emails cliqués"{% endif %}>
        <div class="val">{{stats.clicked}}</div><div class="label">Clics</div>
      </div>
    </a>
    <div class="stat-box" data-clickable="false"><div class="val">{{stats.bounced}}</div><div class="label">Bounces</div></div>
  </div>
  <div class="progress" style="margin-top:20px">
    <div class="progress-bar" style="width:{{(stats.sent / [stats.total, 1]|max * 100)|round}}%"></div>
  </div>
  <div style="margin-top:24px">
    <div style="font-size:14px;font-weight:700;color:#94a3b8;margin-bottom:12px;">Statistiques diagnostics</div>
    <div class="stat-grid">
      <div class="stat-box"><div class="val">{{stats.diag_count}}</div><div class="label">Analyses</div></div>
      <div class="stat-box"><div class="val">{{stats.total_nb_batiments}}</div><div class="label">Bâtiments identifiés</div></div>
      <div class="stat-box"><div class="val">{{stats.total_nb_parkings}}</div><div class="label">Parkings identifiés</div></div>
      <div class="stat-box"><div class="val">{{stats.total_asset_surface_m2|round}}</div><div class="label">Surface étudiée (m²)</div></div>
      <div class="stat-box"><div class="val">{{stats.avg_kwc}}</div><div class="label">Puissance moyenne (kWc)</div></div>
      <div class="stat-box"><div class="val">{{stats.max_kwc}}</div><div class="label">Potentiel max (kWc)</div></div>
    </div>
  </div>
</div>
<div class="card">
  <a href="/campaign/{{campaign_id}}/recipients?page=1">Voir les destinataires →</a>
  &nbsp;&nbsp;<a href="/campaign/">← Retour</a>
</div>
<script>
if ('{{stats.status}}' === 'running') {
  setTimeout(() => location.reload(), 4000);
}
</script>
</body>
</html>"""


# ── Routes ─────────────────────────────────────────────────────────────────────

@campaign_bp.route('/')
def dashboard():
    redir, blocked = _require_admin()
    if blocked: return redir
    from flask import get_flashed_messages
    campaigns = list_campaigns()
    # Enrichir avec taux
    for c in campaigns:
        c['open_rate']   = round(c['opened']  / max(c['sent'], 1) * 100, 1)
        c['click_rate']  = round(c['clicked'] / max(c['sent'], 1) * 100, 1)
    return render_template_string(DASHBOARD_HTML, campaigns=campaigns)


@campaign_bp.route('/new', methods=['POST'])
def new_campaign():
    redir, blocked = _require_admin()
    if blocked: return redir
    name    = request.form.get('name', '').strip()
    subject = request.form.get('subject', '').strip()
    if not name or not subject:
        return redirect('/campaign/')
    create_campaign(name, subject)
    return redirect('/campaign/')

@campaign_bp.route('/export-all')
def export_all_data():
    """Génère et envoie le ZIP complet de la base PostgreSQL"""
    redir, blocked = _require_admin()
    if blocked: return redir
    
    try:
        from export_complete_base import export_complete
        # Génère le fichier ZIP via ton script existant
        fname, count = export_complete()
        # Envoie le fichier pour téléchargement
        return send_file(os.path.join(os.getcwd(), fname), as_attachment=True)
    except Exception as e:
        print(f"❌ [EXPORT ERROR] {e}")
        return f"Erreur lors de la génération de l'export : {str(e)}", 500

@campaign_bp.route('/<campaign_id>/import_form')
def import_form(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir
    conn = get_db()
    row = conn.execute("SELECT name FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()
    if not row: return "Campagne introuvable", 404
    return render_template_string(IMPORT_HTML, campaign_id=campaign_id, campaign_name=row['name'])


@campaign_bp.route('/<campaign_id>/import', methods=['POST'])
def do_import(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir

    f = request.files.get('csv_file')
    if not f:
        return redirect(f'/campaign/{campaign_id}/import_form')

    # Sauvegarde temporaire sécurisée
    import tempfile, os
    suffix = os.path.splitext(f.filename)[1].lower()
    if suffix not in ('.csv', '.txt'):
        return "Format non supporté. Utilisez un fichier .csv", 400

    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Essayer utf-8 d'abord, puis latin-1
        try:
            count = import_mairies_csv(tmp_path, campaign_id, encoding='utf-8')
        except UnicodeDecodeError:
            count = import_mairies_csv(tmp_path, campaign_id, encoding='latin-1')
    finally:
        os.unlink(tmp_path)

    return redirect(f'/campaign/{campaign_id}/detail')


@campaign_bp.route('/<campaign_id>/start')
def start_campaign(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir

    if campaign_id in _running_threads and _running_threads[campaign_id].is_alive():
        return redirect(f'/campaign/{campaign_id}/detail')

    conn = get_db()
    row = conn.execute("SELECT subject, status FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()
    if not row or row['status'] == 'running':
        return redirect('/campaign/')

    # Remettre les erreurs SMTP (221, timeout) en 'pending' pour re-tentative
    conn2 = get_db()
    conn2.execute(
        "UPDATE recipients SET status='pending', error=NULL WHERE campaign_id=? AND status='error'",
        (campaign_id,)
    )
    conn2.commit()
    conn2.close()

    stop_event = threading.Event()
    _stop_events[campaign_id] = stop_event
    t = threading.Thread(target=run_campaign, args=(campaign_id, row['subject'], stop_event), daemon=True)
    _running_threads[campaign_id] = t
    t.start()
    return redirect(f'/campaign/{campaign_id}/detail')


@campaign_bp.route('/<campaign_id>/stop')
def stop_campaign(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir

    if campaign_id in _stop_events:
        _stop_events[campaign_id].set()
    conn = get_db()
    conn.execute("UPDATE campaigns SET status='paused' WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()
    return redirect(f'/campaign/{campaign_id}/detail')


@campaign_bp.route('/<campaign_id>/stats')
def stats_json(campaign_id):
    return jsonify(get_campaign_stats(campaign_id))


@campaign_bp.route('/<campaign_id>/detail')
def detail(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir
    stats = get_campaign_stats(campaign_id)
    if not stats: return "Campagne introuvable", 404
    return render_template_string(DETAIL_HTML, stats=stats, campaign_id=campaign_id)


@campaign_bp.route('/<campaign_id>/recipients')
def recipients(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir

    # JSON brut si demandé via ?format=json
    if request.args.get('format') == 'json':
        page = int(request.args.get('page', 1))
        status_filter = request.args.get('status', '')
        per_page = 50
        offset = (page - 1) * per_page
        conn = get_db()
        where = "WHERE campaign_id=?"
        params = [campaign_id]
        if status_filter == 'opened':
            where += " AND opened_at IS NOT NULL"
        elif status_filter == 'clicked':
            where += " AND clicked_at IS NOT NULL"
        elif status_filter:
            where += " AND status=?"
            params.append(status_filter)
        rows = conn.execute(
            f"SELECT * FROM recipients {where} ORDER BY sent_at DESC LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
        total = conn.execute(f"SELECT COUNT(*) FROM recipients {where}", params).fetchone()[0]
        conn.close()
        return jsonify({'recipients': [dict(r) for r in rows], 'total': total,
                        'page': page, 'per_page': per_page})

    # Page HTML
    page = int(request.args.get('page', 1))
    status_filter = request.args.get('status', '')
    per_page = 50
    offset = (page - 1) * per_page
    conn = get_db()

    # Compteurs par statut + comptages spéciaux pour opened/clicked
    counts_rows = conn.execute(
        "SELECT status, COUNT(*) n FROM recipients WHERE campaign_id=? GROUP BY status",
        (campaign_id,)
    ).fetchall()
    counts = {r['status']: r['n'] for r in counts_rows}
    
    # Compter aussi les "opened" et "clicked" par timestamp (rétrocompatibilité)
    opened_count = conn.execute(
        "SELECT COUNT(*) FROM recipients WHERE campaign_id=? AND opened_at IS NOT NULL",
        (campaign_id,)
    ).fetchone()[0]
    clicked_count = conn.execute(
        "SELECT COUNT(*) FROM recipients WHERE campaign_id=? AND clicked_at IS NOT NULL",
        (campaign_id,)
    ).fetchone()[0]
    counts['opened'] = max(counts.get('opened', 0), opened_count)
    counts['clicked'] = max(counts.get('clicked', 0), clicked_count)
    total_all = sum(counts.values())

    # Construit la clause WHERE en fonction du filtre
    where = "WHERE campaign_id=?"
    params = [campaign_id]
    if status_filter == 'opened':
        where += " AND opened_at IS NOT NULL"
    elif status_filter == 'clicked':
        where += " AND clicked_at IS NOT NULL"
    elif status_filter:
        where += " AND status=?"
        params.append(status_filter)

    rows = conn.execute(
        f"SELECT * FROM recipients {where} ORDER BY sent_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()
    total = conn.execute(f"SELECT COUNT(*) FROM recipients {where}", params).fetchone()[0]

    # Nom campagne
    camp = conn.execute("SELECT name FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()

    def _fmt(v):
        if v is None: return ''
        if hasattr(v, 'strftime'): return v.strftime('%Y-%m-%d %H:%M')
        return str(v)

    rows = [dict(r) for r in rows]
    for r in rows:
        r['sent_at']        = _fmt(r.get('sent_at'))
        r['opened_at']      = _fmt(r.get('opened_at'))
        r['clicked_at']     = _fmt(r.get('clicked_at'))
        r['plan_clicked_at']= _fmt(r.get('plan_clicked_at'))

    total_pages = max(1, (total + per_page - 1) // per_page)
    camp_name = camp['name'] if camp else campaign_id

    return render_template_string(RECIPIENTS_HTML,
        campaign_id=campaign_id,
        camp_name=camp_name,
        rows=rows,
        counts=counts,
        total_all=total_all,
        total=total,
        page=page,
        total_pages=total_pages,
        status_filter=status_filter,
        per_page=per_page,
    )


@campaign_bp.route('/<campaign_id>/recipients/<recipient_id>/preview')
def preview_email(campaign_id, recipient_id):
    """Affiche dans le navigateur l'email reconstruit depuis diagnostic_json."""
    redir, blocked = _require_admin()
    if blocked: return redir
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM recipients WHERE id=? AND campaign_id=?",
        (recipient_id, campaign_id)
    ).fetchone()
    camp = conn.execute("SELECT subject FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    conn.close()
    if not row:
        return "Destinataire introuvable", 404

    rec = dict(row)
    diag_json = rec.get('diagnostic_json')
    if not diag_json:
        return "Email non disponible (diagnostic non enregistré pour ce destinataire)", 404

    import json as _json
    from mairies_campaign import build_email_html, BASE_URL
    diag = _json.loads(diag_json)

    pixel_url = f"{BASE_URL}/campaign/open/{recipient_id}"
    cta_url   = f"{BASE_URL}/campaign/click/{recipient_id}"
    plan_url  = f"{BASE_URL}/campaign/plan/{recipient_id}"
    html = build_email_html(rec, diag, pixel_url, cta_url, plan_url)
    # Afficher inline (pas d'attachement)
    return Response(html, mimetype='text/html')


@campaign_bp.route('/<campaign_id>/recipients/<recipient_id>/delete', methods=['POST'])
def delete_recipient(campaign_id, recipient_id):
    redir, blocked = _require_admin()
    if blocked: return redir
    conn = get_db()
    conn.execute("DELETE FROM recipients WHERE id=? AND campaign_id=?",
                 (recipient_id, campaign_id))
    conn.commit()
    conn.close()
    return redirect(request.referrer or f'/campaign/{campaign_id}/recipients')


@campaign_bp.route('/<campaign_id>/recipients/delete-bounces', methods=['POST'])
def delete_all_bounces(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir
    conn = get_db()
    conn.execute("DELETE FROM recipients WHERE campaign_id=? AND status='bounce'",
                 (campaign_id,))
    conn.execute("UPDATE campaigns SET bounced=0 WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()
    return redirect(f'/campaign/{campaign_id}/recipients')


@campaign_bp.route('/<campaign_id>/recipients/delete-unsubscribed', methods=['POST'])
def delete_all_unsubscribed(campaign_id):
    redir, blocked = _require_admin()
    if blocked: return redir
    conn = get_db()
    
    # Compter les clics et ouvertures des désabonnés avant suppression
    stats = conn.execute("""
        SELECT 
            COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END) as opened_count,
            COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END) as clicked_count
        FROM recipients WHERE campaign_id=? AND status='unsub'
    """, (campaign_id,)).fetchone()
    
    opened_count = stats['opened_count'] if stats else 0
    clicked_count = stats['clicked_count'] if stats else 0
    
    # Supprimer les désabonnés de cette campagne de la BDD
    conn.execute("DELETE FROM recipients WHERE campaign_id=? AND status='unsub'",
                 (campaign_id,))
    
    # Mettre à jour les compteurs de la campagne
    if opened_count > 0:
        conn.execute("UPDATE campaigns SET opened=opened-? WHERE id=?",
                     (opened_count, campaign_id))
    if clicked_count > 0:
        conn.execute("UPDATE campaigns SET clicked=clicked-? WHERE id=?",
                     (clicked_count, campaign_id))
    
    conn.execute("UPDATE campaigns SET unsub=0 WHERE id=?", (campaign_id,))
    conn.commit()
    conn.close()
    return redirect(f'/campaign/{campaign_id}/recipients')


RECIPIENTS_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Destinataires — {{camp_name}}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;min-height:100vh}
  .topbar{background:#1e293b;border-bottom:1px solid #334155;padding:14px 28px;
          display:flex;align-items:center;gap:16px;flex-wrap:wrap}
  .topbar h1{font-size:16px;color:#10b981;white-space:nowrap}
  .topbar a{color:#64748b;font-size:13px;text-decoration:none}
  .topbar a:hover{color:#f1f5f9}
  .container{max-width:1200px;margin:24px auto;padding:0 20px}
  .filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px;align-items:center}
  .filter-btn{padding:6px 14px;border-radius:20px;font-size:12px;font-weight:600;
              border:1px solid #334155;background:#1e293b;color:#94a3b8;
              cursor:pointer;text-decoration:none;transition:.15s}
  .filter-btn:hover{border-color:#475569;color:#f1f5f9}
  .filter-btn.active{background:#10b981;border-color:#10b981;color:#fff}
  .filter-btn.bounce{border-color:#ef4444;color:#ef4444}
  .filter-btn.bounce.active{background:#ef4444;color:#fff}
  .card{background:#1e293b;border:1px solid #334155;border-radius:10px;overflow:hidden}
  table{width:100%;border-collapse:collapse;font-size:13px}
  th{padding:10px 14px;color:#64748b;font-weight:600;text-align:left;
     border-bottom:1px solid #334155;white-space:nowrap;background:#162032}
  td{padding:10px 14px;border-bottom:1px solid #0f1b2d;color:#cbd5e1;vertical-align:middle}
  tr:last-child td{border-bottom:none}
  tr:hover td{background:#162032}
  .badge{display:inline-block;padding:2px 9px;border-radius:12px;font-size:11px;font-weight:700}
  .badge-sent{background:#10b9811a;color:#10b981}
  .badge-opened{background:#3b82f61a;color:#3b82f6}
  .badge-clicked{background:#8b5cf61a;color:#8b5cf6}
  .badge-bounce{background:#ef44441a;color:#ef4444}
  .badge-pending{background:#f59e0b1a;color:#f59e0b}
  .badge-error{background:#ef44441a;color:#ef4444}
  .badge-unsub{background:#6b72801a;color:#9ca3af}
  .badge-skipped{background:#0f1b2d;color:#475569;border:1px solid #334155}
  .btn-del{background:none;border:1px solid #334155;color:#64748b;padding:4px 10px;
           border-radius:5px;font-size:11px;cursor:pointer;transition:.15s}
  .btn-del:hover{border-color:#ef4444;color:#ef4444}
  .btn-danger{background:#ef44441a;border:1px solid #ef4444;color:#ef4444;
              padding:8px 16px;border-radius:7px;font-size:12px;font-weight:600;
              cursor:pointer;text-decoration:none;transition:.15s}
  .btn-danger:hover{background:#ef4444;color:#fff}
  .pagination{display:flex;gap:6px;margin-top:18px;align-items:center;flex-wrap:wrap}
  .page-btn{padding:6px 12px;border-radius:6px;font-size:12px;font-weight:600;
            border:1px solid #334155;background:#1e293b;color:#94a3b8;
            cursor:pointer;text-decoration:none;transition:.15s}
  .page-btn:hover{border-color:#475569;color:#f1f5f9}
  .page-btn.active{background:#10b981;border-color:#10b981;color:#fff;cursor:default}
  .page-btn.disabled{opacity:.35;pointer-events:none}
  .info{color:#64748b;font-size:12px;margin-left:auto}
  .dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:4px}
  .empty{text-align:center;padding:40px;color:#475569;font-size:13px}
  .actions-bar{display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap}
</style>
</head>
<body>

<div class="topbar">
  <h1>📋 Destinataires — {{camp_name}}</h1>
  <a href="/campaign/{{campaign_id}}/detail">← Détail campagne</a>
  <a href="/campaign/">← Tableau de bord</a>
</div>

<div class="container">

  <!-- Filtres statut -->
  <div class="filters">
    <a href="/campaign/{{campaign_id}}/recipients?page=1"
       class="filter-btn {% if not status_filter %}active{% endif %}">
      Tous <span style="opacity:.7">({{total_all}})</span>
    </a>
    {% for st, label, cls in [
        ('sent','Envoyés',''),('opened','Ouverts',''),('clicked','Cliqués',''),
        ('bounce','Bounces','bounce'),('pending','En attente',''),
        ('error','Erreurs','bounce'),('skipped','Non éligibles',''),('unsub','Désabonnés','')] %}
    {% if counts.get(st, 0) > 0 %}
    <a href="/campaign/{{campaign_id}}/recipients?status={{st}}&page=1"
       class="filter-btn {{cls}} {% if status_filter == st %}active{% endif %}">
      {{label}} <span style="opacity:.7">({{counts[st]}})</span>
    </a>
    {% endif %}
    {% endfor %}
  </div>

  <!-- Actions globales -->
  <div class="actions-bar">
    {% if counts.get('unsub', 0) > 0 %}
    <form method="post" action="/campaign/{{campaign_id}}/recipients/delete-unsubscribed"
          onsubmit="return confirm('Supprimer définitivement les {{counts.unsub}} désabonnés de la BDD ? Ils ne recevront plus de futurs emails même en réimportant.')">
      <button type="submit" class="btn-danger">
        🗑 Supprimer désabonnés ({{counts.get('unsub',0)}})
      </button>
    </form>
    {% endif %}
    {% if counts.get('bounce', 0) > 0 %}
    <form method="post" action="/campaign/{{campaign_id}}/recipients/delete-bounces"
          onsubmit="return confirm('Supprimer les {{counts.bounce}} bounces de cette campagne ?')">
      <button type="submit" class="btn-danger">
        🗑 Supprimer tous les bounces ({{counts.get('bounce',0)}})
      </button>
    </form>
    {% endif %}
    <span class="info">{{total}} résultat(s) — page {{page}}/{{total_pages}}</span>
  </div>

  <!-- Tableau -->
  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Commune</th>
          <th>Email</th>
          <th>Statut</th>
          <th>Envoyé</th>
          <th>Ouvert</th>
          <th>Cliqué</th>
          <th>kWc</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {% for r in rows %}
        <tr>
          <td>
            <strong>{{r.nom_commune or '—'}}</strong>
            {% if r.departement %}<br><span style="color:#64748b;font-size:11px">Dept {{r.departement}}</span>{% endif %}
          </td>
          <td style="color:#94a3b8;font-size:12px">{{r.email}}</td>
          <td>
            <span class="badge badge-{{r.status}}">{{r.status}}</span>
            {% if r.error %}<br><span style="color:#ef4444;font-size:10px" title="{{r.error}}">⚠ {{r.error[:40]}}</span>{% endif %}
          </td>
          <td style="font-size:11px;color:#64748b">{{r.sent_at[:16] if r.sent_at else '—'}}</td>
          <td style="font-size:11px;color:{% if r.opened_at %}#3b82f6{% else %}#334155{% endif %}">
            {{r.opened_at[:16] if r.opened_at else '—'}}
          </td>
          <td style="font-size:11px;color:{% if r.clicked_at or r.plan_clicked_at %}#8b5cf6{% else %}#334155{% endif %}">
            {{(r.clicked_at or r.plan_clicked_at or '')[:16] or '—'}}
          </td>
          <td style="color:#10b981;font-weight:600">
            {% if r.irradiance %}{{r.irradiance|int}}{% else %}—{% endif %}
          </td>
          <td style="white-space:nowrap">
            {% if r.status in ['sent','opened','clicked'] %}
            <a href="/campaign/{{campaign_id}}/recipients/{{r.id}}/preview"
               target="_blank" class="btn-del" style="margin-bottom:4px;display:inline-block;color:#10b981;border-color:#10b981">👁 Voir</a>
            {% endif %}
            <form method="post"
                  action="/campaign/{{campaign_id}}/recipients/{{r.id}}/delete"
                  onsubmit="return confirm('Supprimer {{r.nom_commune}} ?')">
              <button type="submit" class="btn-del">✕ Retirer</button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="8" class="empty">Aucun destinataire pour ce filtre.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- Pagination -->
  {% if total_pages > 1 %}
  <div class="pagination">
    <a href="/campaign/{{campaign_id}}/recipients?status={{status_filter}}&page={{page-1}}"
       class="page-btn {% if page <= 1 %}disabled{% endif %}">‹ Préc.</a>
    {% for p in range([1, page-2]|max, [total_pages+1, page+3]|min) %}
    <a href="/campaign/{{campaign_id}}/recipients?status={{status_filter}}&page={{p}}"
       class="page-btn {% if p == page %}active{% endif %}">{{p}}</a>
    {% endfor %}
    <a href="/campaign/{{campaign_id}}/recipients?status={{status_filter}}&page={{page+1}}"
       class="page-btn {% if page >= total_pages %}disabled{% endif %}">Suiv. ›</a>
    <span class="info">{{total}} / {{total_all}} destinataires</span>
  </div>
  {% endif %}

</div>
</body>
</html>"""




@campaign_bp.route('/plan/<recipient_id>')
def plan_commune(recipient_id):
    """
    Page HTML publique — carte Folium + CTAs.
    Accès gratuit 7 jours après l'envoi de l'email.
    """
    from datetime import datetime, timedelta
    row = None
    try:
        conn = get_db()
        row = conn.execute("SELECT * FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
    except Exception:
        row = None

    if not row:
        # Fallback params GET (tests sans DB)
        nom        = request.args.get('commune', '')
        code_insee = request.args.get('insee', '')
        lat_q      = request.args.get('lat')
        lon_q      = request.args.get('lon')
        dept_q     = request.args.get('dept', '')
        pop_q      = request.args.get('pop', '0')
        if not nom or not lat_q or not lon_q:
            return "Lien invalide ou expiré", 404
        rec = {
            'nom_commune': nom, 'code_insee': code_insee,
            'lat': float(lat_q), 'lon': float(lon_q),
            'departement': dept_q, 'population': int(pop_q),
            'diagnostic_json': None, 'pdf_unlocked': False,
        }
        days_left = 7   # pas d'expiry pour les tests
    else:
        rec = dict(row)
        # Expiry 7 jours depuis sent_at
        days_left = 7
        sent_at_raw = rec.get('sent_at')
        if sent_at_raw:
            try:
                if isinstance(sent_at_raw, str):
                    sent_dt = datetime.fromisoformat(sent_at_raw.replace(' ', 'T').replace('Z', '').replace('+00:00', ''))
                else:
                    sent_dt = sent_at_raw
                days_elapsed = (datetime.utcnow() - sent_dt).days
                days_left = max(0, 7 - days_elapsed)
            except Exception:
                days_left = 7
        if days_left == 0:
            return render_template_string(PLAN_EXPIRED_HTML,
                nom=rec.get('nom_commune', 'votre commune'),
                recipient_id=recipient_id, BASE_URL=BASE_URL)

    nom        = rec.get('nom_commune', 'Commune')
    code_insee = rec.get('code_insee', '')
    pdf_unlocked   = bool(rec.get('pdf_unlocked', False))
    etude_unlocked = bool(rec.get('etude_unlocked', False))

    try:
        from mairies_diagnostic import build_commune_diagnostic, generate_map_html
        lat = rec.get('lat')
        lon = rec.get('lon')
        if not lat or not lon:
            from mairies_campaign import geocode_commune
            lat, lon = geocode_commune(nom, code_insee)
        diag_full = build_commune_diagnostic(
            code_insee=code_insee,
            nom_commune=nom,
            lat=lat or 46.5,
            lon=lon or 2.3,
        )
        map_html_content = generate_map_html(diag_full)
    except Exception as e:
        map_html_content = f'<div style="color:#ef4444;padding:20px;font-family:Arial">Carte indisponible ({e})</div>'
        diag_full = {}

    eco       = (diag_full or {}).get('economie_totale', 0)
    puiss     = (diag_full or {}).get('puissance_totale_kwc', 0)
    nb_assets = len((diag_full or {}).get('assets', []))
    dept      = rec.get('departement', '')

    return render_template_string(PLAN_PAGE_HTML,
        nom=nom, dept=dept, eco=eco, puiss=puiss, nb_assets=nb_assets,
        map_html=map_html_content, recipient_id=recipient_id,
        BASE_URL=BASE_URL, diag=diag_full or {},
        days_left=days_left, pdf_unlocked=pdf_unlocked,
        etude_unlocked=etude_unlocked)


PLAN_EXPIRED_HTML = """<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>Lien expiré — HeliaPV</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;
       display:flex;align-items:center;justify-content:center;min-height:100vh;padding:24px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:14px;
        padding:40px;max-width:480px;text-align:center}
  h2{color:#f59e0b;font-size:22px;margin-bottom:16px}
  p{color:#94a3b8;font-size:14px;line-height:1.7;margin-bottom:24px}
  .btn{display:inline-block;background:#10b981;color:#fff;text-decoration:none;
       padding:12px 28px;border-radius:8px;font-weight:700;font-size:14px}
</style>
</head>
<body>
<div class="card">
  <div style="font-size:48px;margin-bottom:16px">⏳</div>
  <h2>Votre accès gratuit a expiré</h2>
  <p>Le plan interactif de <strong>{{nom}}</strong> était accessible gratuitement pendant 7 jours
     après réception de l'email.<br><br>
     Pour obtenir votre rapport complet ou un accès prolongé, contactez-nous directement.</p>
  <a href="mailto:info@heliapv.fr?subject=Demande accès plan — {{nom}}&body=Bonjour, je souhaite accéder au plan solaire de {{nom}}. Référence : {{recipient_id}}"
     class="btn">Contacter HeliaPV →</a>
  <p style="margin-top:16px;font-size:12px;color:#475569">
    Ou appelez-nous : 06 XX XX XX XX — info@heliapv.fr
  </p>
</div>
</body>
</html>"""


PLAN_PAGE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plan solaire — {{nom}}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;overflow:hidden}
  .topbar{position:fixed;top:0;left:0;right:0;z-index:100;
          background:#1e293b;border-bottom:1px solid #334155;padding:12px 24px;
          display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
  .topbar h1{font-size:15px;color:#10b981}
  .topbar .sub{color:#94a3b8;font-size:12px;margin-top:2px}
  .badge-days{background:#f59e0b1a;color:#f59e0b;border:1px solid #f59e0b55;
              padding:3px 10px;border-radius:20px;font-size:11px;font-weight:700;
              white-space:nowrap}
  .kpis{position:fixed;top:60px;left:0;right:0;z-index:100;
        display:flex;gap:10px;padding:12px 24px;flex-wrap:wrap;background:#1e293b;
        border-bottom:1px solid #334155}
  .kpi{background:#0f1b2d;border:1px solid #334155;border-radius:8px;padding:10px 18px;
       text-align:center;min-width:120px}
  .kpi .val{font-size:20px;font-weight:700;color:#10b981}
  .kpi .label{font-size:11px;color:#64748b;margin-top:2px}
  .map-wrap{position:fixed;top:130px;left:0;right:0;bottom:64px}
  .map-wrap .map-inner{width:100%;height:100%;border:0}
  .cta-bar{position:fixed;bottom:0;left:0;right:0;height:64px;
           background:#0f1b2d;border-top:2px solid #334155;padding:8px 24px;
           display:flex;align-items:center;justify-content:space-between;
           flex-wrap:nowrap;gap:12px;z-index:1000}
  .cta-hint{font-size:12px;color:#64748b;max-width:400px;line-height:1.5}
  .cta-hint strong{color:#94a3b8}
  .cta-btns{display:flex;gap:10px;flex-wrap:wrap}
  .btn{padding:10px 22px;border-radius:7px;font-size:13px;font-weight:700;
       text-decoration:none;display:inline-block;cursor:pointer;border:none}
  .btn-green{background:#10b981;color:#fff}
  .btn-green:hover{background:#059669}
  .btn-outline{background:transparent;color:#10b981;border:2px solid #10b981}
  .btn-outline:hover{background:#10b98120}
  .btn-pdf{background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff}
  .btn-pdf:hover{opacity:.9}
  /* Modal */
  .modal-bg{display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);
            z-index:9999;align-items:center;justify-content:center}
  .modal-bg.open{display:flex}
  .modal{background:#1e293b;border:1px solid #334155;border-radius:14px;
         padding:32px;max-width:440px;width:90%}
  .modal h3{color:#10b981;margin-bottom:18px;font-size:17px}
  .modal input,.modal textarea{width:100%;background:#0f1b2d;border:1px solid #334155;
    color:#f1f5f9;padding:10px 12px;border-radius:7px;font-size:13px;margin-bottom:12px;
    font-family:inherit}
  .modal label{font-size:12px;color:#64748b;display:block;margin-bottom:4px}
  .modal-footer{display:flex;gap:10px;margin-top:4px}
  .btn-cancel{background:#334155;color:#94a3b8}
  .btn-cancel:hover{background:#475569}
  .msg-success{color:#10b981;font-size:13px;text-align:center;padding:12px;display:none}
</style>
</head>
<body>

<!-- Topbar -->
<div class="topbar">
  <div>
    <h1>☀ Plan solaire — Commune de {{nom}}{{' (' + dept + ')' if dept else ''}}</h1>
    <div class="sub">Données cadastrales MAJIC + IGN · GeoServer parkings</div>
  </div>
  <div style="display:flex;align-items:center;gap:12px">
    {% if days_left is not none %}
    <span class="badge-days">⏳ Accès gratuit — encore {{days_left}} j.</span>
    {% endif %}
    <a href="{{BASE_URL}}" style="color:#10b981;font-size:12px;text-decoration:none">heliapv.fr →</a>
  </div>
</div>

<!-- KPIs -->
<div class="kpis">
  <div class="kpi"><div class="val">{{nb_assets}}</div><div class="label">Sites identifiés</div></div>
  <div class="kpi"><div class="val">{{puiss}} kWc</div><div class="label">Puissance installable</div></div>
  <div class="kpi"><div class="val">{{'{:,}'.format(eco)|replace(',','\\u202f')}} €</div><div class="label">Économies/an</div></div>
  <div class="kpi"><div class="val">{{'{:,}'.format(diag.get('co2_evite_kg',0))|replace(',','\\u202f')}} kg</div><div class="label">CO₂ évité/an</div></div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:14px;font-size:11px;color:#64748b;flex-wrap:wrap">
    <span><span style="display:inline-block;width:10px;height:10px;background:#10b981;border-radius:2px;margin-right:4px;vertical-align:middle"></span>Parcelles MAJIC</span>
    <span><span style="display:inline-block;width:10px;height:10px;background:#f97316;border-radius:2px;margin-right:4px;vertical-align:middle"></span>Bâtiments publics</span>
    <span><span style="display:inline-block;width:10px;height:10px;background:#0ea5e9;border-radius:2px;margin-right:4px;vertical-align:middle"></span>Parkings éligibles</span>
  </div>
</div>

<!-- Carte -->
<div class="map-wrap">
  <div class="map-inner">{{map_html|safe}}</div>
</div>

<!-- Légende — rendue hors map-wrap pour éviter le stacking context Folium -->
<div style="position:fixed;bottom:80px;left:16px;z-index:9999;
     background:rgba(15,27,45,0.95);color:#f1f5f9;padding:12px 16px;
     border-radius:10px;font-family:system-ui,Arial,sans-serif;font-size:12px;
     border:1px solid #334155;min-width:220px;pointer-events:none">
  <b style="color:#10b981;font-size:13px">☀ {{nom}}{{' (' + dept + ')' if dept else ''}} — Plan solaire</b><br>
  <span style="color:#94a3b8;font-size:10px">Obligations Loi APER 2023 &amp; DDADUE 2025</span><br><br>
  <span style="display:inline-block;width:11px;height:11px;background:#10b981;border-radius:2px;margin-right:5px;opacity:0.5;vertical-align:middle"></span>Parcelles communales (MAJIC)<br>
  <span style="display:inline-block;width:11px;height:11px;background:#7c3aed;border-radius:2px;margin-right:5px;vertical-align:middle"></span>⚖️ Bâtiment public ≥500m² — <b style="color:#93c5fd">Jan. 2028</b><br>
  <span style="display:inline-block;width:11px;height:11px;background:#0ea5e9;border-radius:2px;margin-right:5px;vertical-align:middle"></span>⚠️ Parking 1 500–10 000m² — <b style="color:#fcd34d">Juil. 2028</b><br>
  <span style="display:inline-block;width:11px;height:11px;background:#dc2626;border-radius:2px;margin-right:5px;vertical-align:middle"></span>🔴 Parking >10 000m² — <b style="color:#fca5a5">URGENT juil. 2026</b><br><br>
  <b>Total :</b> {{puiss}} kWc | {{'{:,}'.format(eco)|replace(',','\u202f')}} €/an
</div>

<!-- CTA bar -->
<div class="cta-bar">
  <div class="cta-hint">
    Cliquez sur chaque site pour le détail du potentiel solaire.<br>
    <strong>Chaque zone = une parcelle ou bâtiment communal identifié (données MAJIC).</strong>
  </div>
  <div class="cta-btns">
    <button onclick="trackCta();document.getElementById('modal-rappel').classList.add('open')"
            class="btn btn-outline">📞 Être rappelé — Gratuit</button>
    {% if pdf_unlocked %}
    <a href="/campaign/pdf/{{recipient_id}}" class="btn btn-pdf" target="_blank">
      📄 Télécharger le rapport PDF
    </a>
    {% endif %}
    {% if etude_unlocked %}
    <a href="/campaign/etude/{{recipient_id}}" class="btn btn-green" target="_blank" style="background:linear-gradient(135deg,#10b981,#059669)">
      🔬 Accéder à l'étude complète
    </a>
    {% else %}
    <a href="/campaign/etude-checkout/{{recipient_id}}" class="btn btn-green" style="background:linear-gradient(135deg,#10b981,#059669)"
       onclick="trackCta()">
      🔬 Étude complète &amp; exhaustive — 129 €/site
    </a>
    {% endif %}
  </div>
</div>

<!-- Modal rappel -->
<div id="modal-rappel" class="modal-bg">
  <div class="modal">
    <h3>📞 Demande de rappel gratuit</h3>
    <form id="form-rappel" onsubmit="envoyerRappel(event)">
      <input type="hidden" id="rc" value="{{recipient_id}}">
      <input type="hidden" id="rc-commune" value="{{nom}}">
      <label>Votre nom *</label>
      <input type="text" id="r-nom" placeholder="Jean Dupont" required>
      <label>Fonction</label>
      <input type="text" id="r-fonction" placeholder="DGS, Élu, Responsable travaux…">
      <label>Email *</label>
      <input type="email" id="r-email" placeholder="contact@commune.fr" required>
      <label>Téléphone</label>
      <input type="tel" id="r-tel" placeholder="06 …">
      <label>Message (optionnel)</label>
      <textarea id="r-msg" rows="3" placeholder="Vos questions ou disponibilités…"></textarea>
      <div class="modal-footer">
        <button type="submit" class="btn btn-green" style="flex:1">Envoyer →</button>
        <button type="button" onclick="document.getElementById('modal-rappel').classList.remove('open')"
                class="btn btn-cancel">Annuler</button>
      </div>
      <div class="msg-success" id="rappel-ok">✓ Demande envoyée ! Nous vous rappelons sous 24h.</div>
    </form>
  </div>
</div>

<script>
function trackCta() {
  fetch('/campaign/track/{{recipient_id}}', {method:'GET'}).catch(()=>{});
}
async function envoyerRappel(e) {
  e.preventDefault();
  const btn = e.target.querySelector('[type=submit]');
  btn.disabled = true; btn.textContent = '⏳ Envoi…';
  try {
    await fetch('/campaign/rappel', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        nom_contact: document.getElementById('r-nom').value,
        fonction:    document.getElementById('r-fonction').value,
        email:       document.getElementById('r-email').value,
        telephone:   document.getElementById('r-tel').value,
        message:     document.getElementById('r-msg').value,
        commune:     document.getElementById('rc-commune').value,
        recipient_id: document.getElementById('rc').value,
      })
    });
    document.getElementById('form-rappel').style.display = 'none';
    document.getElementById('rappel-ok').style.display   = 'block';
    setTimeout(() => document.getElementById('modal-rappel').classList.remove('open'), 2500);
  } catch(err) {
    btn.disabled = false; btn.textContent = 'Envoyer →';
    alert('Erreur réseau, réessayez.');
  }
}
// Fermer modal si clic sur le fond
document.getElementById('modal-rappel').addEventListener('click', function(e){
  if (e.target === this) this.classList.remove('open');
});
</script>
</body>
</html>"""


# ── Réception demande de devis ─────────────────────────────────────────────────

@campaign_bp.route('/devis', methods=['POST'])
def receive_devis():
    import smtplib, os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formatdate, make_msgid, formataddr
    data = request.get_json(silent=True) or {}
    nom_c    = data.get('nom_contact', '—')
    fonction = data.get('fonction', '—')
    email_c  = data.get('email', '—')
    tel      = data.get('telephone', '—')
    commune  = data.get('commune', '—')
    message  = data.get('message', '')
    rid      = data.get('recipient_id', '')

    body = (
        f"Nouvelle demande de devis AMO solaire\n\n"
        f"Commune    : {commune}\n"
        f"Contact    : {nom_c} ({fonction})\n"
        f"Email      : {email_c}\n"
        f"Téléphone  : {tel}\n"
        f"Message    : {message or '(aucun)'}\n"
        f"Recipient  : {rid}\n"
    )
    try:
        mail_user = os.environ.get('MAIL_USERNAME', 'info@heliapv.fr')
        mail_pwd  = os.environ.get('MAIL_PASSWORD', '')
        mail_srv  = os.environ.get('MAIL_SERVER', 'ssl0.ovh.net')
        mail_port = int(os.environ.get('MAIL_PORT', 465))
        msg = MIMEMultipart('alternative')
        msg['Subject']    = f"[HeliaPV] Demande devis AMO — {commune}"
        msg['From']       = formataddr(('HeliaPV Campagne', mail_user))
        msg['To']         = mail_user
        msg['Date']       = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='heliapv.fr')
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        s = smtplib.SMTP_SSL(mail_srv, mail_port, timeout=15)
        s.login(mail_user, mail_pwd)
        s.sendmail(mail_user, [mail_user], msg.as_bytes())
        s.quit()
    except Exception:
        pass  # Ne pas bloquer le retour client si SMTP échoue
    return jsonify({'ok': True})


# ── Rappel gratuit ─────────────────────────────────────────────────────────────

@campaign_bp.route('/rappel', methods=['POST'])
def rappel_gratuit():
    """Reçoit la demande de rappel depuis le modal du plan interactif."""
    import smtplib, os
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formatdate, make_msgid, formataddr
    data = request.get_json(silent=True) or {}
    nom_c    = data.get('nom_contact', '—')
    fonction = data.get('fonction', '—')
    email_c  = data.get('email', '—')
    tel      = data.get('telephone', '—')
    commune  = data.get('commune', '—')
    message  = data.get('message', '')
    rid      = data.get('recipient_id', '')

    body = (
        f"🔔 DEMANDE DE RAPPEL GRATUIT\n\n"
        f"Commune    : {commune}\n"
        f"Contact    : {nom_c} ({fonction})\n"
        f"Email      : {email_c}\n"
        f"Téléphone  : {tel}\n"
        f"Message    : {message or '(aucun)'}\n"
        f"Recipient  : {rid}\n"
        f"Lien plan  : {BASE_URL}/campaign/plan/{rid}\n"
    )
    try:
        mail_user = os.environ.get('MAIL_USERNAME', 'info@heliapv.fr')
        mail_pwd  = os.environ.get('MAIL_PASSWORD', '')
        mail_srv  = os.environ.get('MAIL_SERVER', 'ssl0.ovh.net')
        mail_port = int(os.environ.get('MAIL_PORT', 465))
        msg = MIMEMultipart('alternative')
        msg['Subject']    = f"[HeliaPV] Rappel gratuit — {commune}"
        msg['From']       = formataddr(('HeliaPV Campagne', mail_user))
        msg['To']         = mail_user
        msg['Date']       = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid(domain='heliapv.fr')
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        s = smtplib.SMTP_SSL(mail_srv, mail_port, timeout=15)
        s.login(mail_user, mail_pwd)
        s.sendmail(mail_user, [mail_user], msg.as_bytes())
        s.quit()
    except Exception:
        pass
    return jsonify({'ok': True})


# ── Stripe — PDF 99 € ──────────────────────────────────────────────────────────

PDF_CHECKOUT_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rapport PDF solaire — {{nom}} — HeliaPV</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;
       min-height:100vh;display:flex;flex-direction:column;align-items:center;
       justify-content:center;padding:24px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:16px;
        padding:40px 44px;max-width:640px;width:100%}
  .logo{color:#10b981;font-size:13px;font-weight:700;letter-spacing:.05em;
        margin-bottom:28px;display:flex;align-items:center;gap:8px}
  h1{font-size:22px;color:#f1f5f9;margin-bottom:8px;line-height:1.4}
  .subtitle{color:#64748b;font-size:13px;margin-bottom:28px}
  .price-badge{display:inline-flex;align-items:baseline;gap:6px;
               background:#10b98118;border:1px solid #10b98155;
               border-radius:10px;padding:10px 18px;margin-bottom:28px}
  .price-badge .amount{font-size:32px;font-weight:800;color:#10b981}
  .price-badge .label{font-size:13px;color:#64748b}
  h2{font-size:13px;font-weight:700;color:#94a3b8;text-transform:uppercase;
     letter-spacing:.08em;margin-bottom:14px}
  .features{list-style:none;margin-bottom:28px;display:flex;flex-direction:column;gap:10px}
  .features li{display:flex;align-items:flex-start;gap:12px;font-size:14px;
               color:#cbd5e1;line-height:1.5}
  .features li .ic{color:#10b981;font-size:16px;flex-shrink:0;margin-top:1px}
  .features li strong{color:#f1f5f9}
  .divider{border:none;border-top:1px solid #334155;margin:24px 0}
  .cta-row{display:flex;gap:12px;flex-wrap:wrap}
  .btn-primary{flex:1;min-width:200px;background:#10b981;color:#fff;
               text-decoration:none;padding:14px 24px;border-radius:9px;
               font-weight:700;font-size:15px;text-align:center;display:block}
  .btn-primary:hover{background:#059669}
  .btn-secondary{flex:1;min-width:200px;background:transparent;color:#10b981;
                 border:2px solid #10b981;text-decoration:none;padding:12px 24px;
                 border-radius:9px;font-weight:700;font-size:14px;text-align:center;
                 display:block}
  .btn-secondary:hover{background:#10b98115}
  .trust{margin-top:16px;font-size:11px;color:#475569;text-align:center}
  .trust span{margin:0 8px}
</style>
</head>
<body>
<div class="card">
  <div class="logo">☀ HeliaPV</div>

  <h1>Rapport solaire complet<br><span style="color:#10b981">Commune de {{nom}}</span></h1>
  <p class="subtitle">Document PDF professionnel — livré sous 24h après commande</p>

  <div class="price-badge">
    <span class="amount">9,90 €</span>
    <span class="label">TTC · paiement unique · accès permanent</span>
  </div>

  <h2>Ce que contient le rapport</h2>
  <ul class="features">
    <li><span class="ic">✅</span>
      <span><strong>Inventaire complet des sites solaires</strong> — toutes les parcelles communales, parkings &gt; 500 m² et bâtiments publics identifiés via les données cadastrales MAJIC officielles</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Potentiel solaire chiffré site par site</strong> — surface exploitable, puissance installable (kWc), production annuelle (kWh) calculée avec l'irradiance PVGIS ERA5 locale</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Analyse financière</strong> — économies annuelles estimées, CO₂ évité, retour sur investissement indicatif par site</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Références cadastrales MAJIC</strong> — section et numéro de parcelle pour chaque site, facilitant les démarches administratives (déclaration préalable, permis de construire)</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Carte interactive téléchargeable</strong> — vue satellite IGN avec tous les sites localisés et leurs caractéristiques</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Synthèse réglementaire</strong> — rappel des obligations L. 171-5 CCH, dispositifs CEE disponibles et aides régionales applicables</span>
    </li>
    <li><span class="ic">✅</span>
      <span><strong>Document prêt pour délibération</strong> — format PDF A4 paginé, utilisable directement en conseil municipal ou pour un dossier de subvention</span>
    </li>
  </ul>

  <hr class="divider">

  <div class="cta-row">
    <a href="mailto:info@heliapv.fr?subject=Commande rapport PDF — {{nom}}&body=Bonjour,%0A%0AJe souhaite commander le rapport PDF solaire pour la commune de {{nom}} (99 €).%0ARéférence : {{rid}}%0A%0ACordialement"
       class="btn-primary">✉ Commander par email →</a>
    <a href="/campaign/plan/{{rid}}" class="btn-secondary">← Retour au plan</a>
  </div>

  <p class="trust">
    <span>🔒 Paiement sécurisé</span>
    <span>📄 PDF livré sous 24h</span>
    <span>🇫🇷 Données officielles IGN / MAJIC</span>
  </p>
</div>
</body>
</html>"""


@campaign_bp.route('/pdf-checkout/<recipient_id>')
def pdf_checkout(recipient_id):
    """Crée une Stripe Checkout Session (99 €) et redirige vers la page Stripe."""
    import os
    stripe_key = os.environ.get('STRIPE_SECRET_KEY', '')

    # Récupérer le nom de la commune pour personnaliser la page
    nom_commune = 'votre commune'
    try:
        conn = get_db()
        row = conn.execute("SELECT nom_commune FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
        if row:
            nom_commune = row['nom_commune'] or nom_commune
    except Exception:
        pass

    if not stripe_key:
        return render_template_string(PDF_CHECKOUT_HTML,
            rid=recipient_id, nom=nom_commune, BASE_URL=BASE_URL)

    try:
        import stripe
        stripe.api_key = stripe_key
        base = BASE_URL.rstrip('/')
        price_id = os.environ.get('STRIPE_PRICE_ID', '')

        # Construire les line_items selon qu'on a un Price ID ou pas
        if price_id:
            line_items = [{'price': price_id, 'quantity': 1}]
        else:
            line_items = [{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 990,
                    'product_data': {'name': 'Rapport PDF solaire commune — HeliaPV'},
                },
                'quantity': 1,
            }]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f'{base}/campaign/pdf-success/{recipient_id}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base}/campaign/plan/{recipient_id}',
            metadata={'recipient_id': recipient_id, 'product': 'rapport_pdf'},
        )
        return redirect(checkout_session.url, code=303)
    except Exception:
        # Clé invalide, lib absente ou autre erreur → page descriptif
        return render_template_string(PDF_CHECKOUT_HTML,
            rid=recipient_id, nom=nom_commune, BASE_URL=BASE_URL)


@campaign_bp.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe → déverrouille le PDF dès paiement confirmé."""
    import os, stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    payload = request.get_data()
    sig     = request.headers.get('Stripe-Signature', '')
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(payload, sig, endpoint_secret)
        else:
            import json
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except Exception as e:
        return f'Webhook error: {e}', 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        rid     = session.get('metadata', {}).get('recipient_id', '')
        product = session.get('metadata', {}).get('product', 'rapport_pdf')
        if rid:
            try:
                conn = get_db()
                if product == 'etude_complete':
                    try:
                        conn.execute("ALTER TABLE recipients ADD COLUMN etude_unlocked BOOLEAN DEFAULT FALSE")
                        conn.commit()
                    except Exception:
                        pass
                    conn.execute("UPDATE recipients SET etude_unlocked=? WHERE id=?", (True, rid))
                else:
                    conn.execute("UPDATE recipients SET pdf_unlocked=? WHERE id=?", (True, rid))
                conn.commit()
                conn.close()
            except Exception:
                pass
    return jsonify({'received': True})


@campaign_bp.route('/pdf-success/<recipient_id>')
def pdf_success(recipient_id):
    """Page de retour après paiement Stripe réussi ; déverrouille et redirige vers le PDF."""
    try:
        conn = get_db()
        conn.execute("UPDATE recipients SET pdf_unlocked=? WHERE id=?", (True, recipient_id))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return redirect(f'/campaign/pdf/{recipient_id}', code=303)


@campaign_bp.route('/pdf/<recipient_id>')
def pdf_report(recipient_id):
    """Rapport HTML print-ready (gated — requiert pdf_unlocked=TRUE)."""
    try:
        conn = get_db()
        row  = conn.execute("SELECT * FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
    except Exception:
        row = None

    if not row:
        return "Lien invalide", 404
    rec = dict(row)
    if not rec.get('pdf_unlocked'):
        return redirect(f'/campaign/plan/{recipient_id}', code=303)

    nom        = rec.get('nom_commune', 'Commune')
    code_insee = rec.get('code_insee', '')
    dept       = rec.get('departement', '')
    try:
        from mairies_diagnostic import build_commune_diagnostic, diagnostic_summary
        lat = rec.get('lat') or 46.5
        lon = rec.get('lon') or 2.3
        diag_full = build_commune_diagnostic(
            code_insee=code_insee, nom_commune=nom, lat=lat, lon=lon)
        summary = diagnostic_summary(diag_full)
    except Exception as e:
        return f"<pre>Erreur génération rapport : {e}</pre>", 500

    return render_template_string(PDF_REPORT_HTML,
        nom=nom, dept=dept, summary=summary, diag=diag_full)


PDF_REPORT_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Rapport solaire — {{nom}}</title>
<style>
  @media print{.no-print{display:none}body{background:#fff}}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:Georgia,serif;background:#f8fafc;color:#1e293b;padding:40px 48px;max-width:860px;margin:auto}
  h1{font-size:24px;color:#10b981;margin-bottom:6px}
  h2{font-size:16px;color:#1e293b;margin:28px 0 10px;border-bottom:1px solid #e2e8f0;padding-bottom:6px}
  .meta{color:#64748b;font-size:13px;margin-bottom:32px}
  .kpi-row{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}
  .kpi{border:1px solid #e2e8f0;border-radius:8px;padding:14px 22px;text-align:center;min-width:140px}
  .kpi .val{font-size:26px;font-weight:700;color:#10b981}
  .kpi .label{font-size:11px;color:#64748b;margin-top:4px}
  table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
  th{background:#f1f5f9;padding:8px 10px;text-align:left;font-weight:600;color:#475569}
  td{padding:7px 10px;border-bottom:1px solid #e2e8f0}
  tr:hover td{background:#f8fafc}
  .footer{margin-top:48px;font-size:11px;color:#94a3b8;text-align:center;border-top:1px solid #e2e8f0;padding-top:16px}
  .print-btn{margin-bottom:24px}
  .print-btn button{background:#10b981;color:#fff;border:none;padding:10px 24px;
                    border-radius:7px;font-size:13px;font-weight:700;cursor:pointer}
</style>
</head>
<body>
<div class="print-btn no-print">
  <button onclick="window.print()">🖨 Imprimer / Enregistrer en PDF</button>
</div>
<h1>☀ Rapport solaire — Commune de {{nom}}{% if dept %} ({{dept}}){% endif %}</h1>
<p class="meta">Analyse HeliaPV · Données MAJIC, IGN, GeoServer · {{ summary.get('date', '') }}</p>

<div class="kpi-row">
  <div class="kpi"><div class="val">{{summary.get('nb_assets', 0)}}</div><div class="label">Sites identifiés</div></div>
  <div class="kpi"><div class="val">{{summary.get('puissance_totale_kwc', 0)}} kWc</div><div class="label">Puissance installable</div></div>
  <div class="kpi"><div class="val">{{'{:,}'.format(summary.get('economie_totale', 0))}} €</div><div class="label">Économies/an</div></div>
  <div class="kpi"><div class="val">{{'{:,}'.format(summary.get('co2_evite_kg', 0))}} kg</div><div class="label">CO₂ évité/an</div></div>
  <div class="kpi"><div class="val">{{summary.get('irradiance_locale', 0)}} kWh/m²</div><div class="label">Irradiance locale</div></div>
</div>

<h2>Top sites solaires</h2>
<table>
  <thead><tr>
    <th>#</th><th>Type</th><th>Surface (m²)</th>
    <th>Puissance (kWc)</th><th>Économies/an (€)</th>
    <th>Parcelle MAJIC</th><th>Source</th>
  </tr></thead>
  <tbody>
  {% for a in summary.get('top_assets', []) %}
  <tr>
    <td>{{loop.index}}</td>
    <td>{{a.get('type','—')}}</td>
    <td>{{a.get('surface_m2','—')}}</td>
    <td>{{a.get('puissance_kwc','—')}}</td>
    <td>{{a.get('economie_annuelle','—')}}</td>
    <td style="font-family:monospace">{{a.get('id_parcelle','—')}}</td>
    <td style="font-size:11px;color:#64748b">{{a.get('source','—')}}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>

<h2>Méthodologie</h2>
<p style="font-size:13px;color:#475569;line-height:1.8">
  Parcelles identifiées via base MAJIC (forme juridique communes). Geometries IGN Apicarto.
  Parkings : GeoServer <em>parkings_sup500m2</em> (primary) + OSM Overpass (fallback).
  Bâtiments : BD TOPO IGN WFS. Irradiance : PVGIS ERA5.
  Surface exploitable = 40% de la surface brute. Rendement = 150 Wc/m².
</p>

<div class="footer">
  HeliaPV · AMO photovoltaïque pour collectivités · info@heliapv.fr · heliapv.fr<br>
  Document confidentiel — usage interne
</div>
</body>
</html>"""


# ── Étude complète 39 € ───────────────────────────────────────────────────────────────

ETUDE_CHECKOUT_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Étude complète solaire — {{nom}} — HeliaPV</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;
       min-height:100vh;display:flex;flex-direction:column;align-items:center;
       justify-content:center;padding:24px}
  .card{background:#1e293b;border:1px solid #334155;border-radius:16px;
        padding:40px 44px;max-width:680px;width:100%}
  .logo{color:#10b981;font-size:13px;font-weight:700;letter-spacing:.05em;
        margin-bottom:28px;display:flex;align-items:center;gap:8px}
  h1{font-size:22px;color:#f1f5f9;margin-bottom:8px;line-height:1.4}
  .subtitle{color:#64748b;font-size:13px;margin-bottom:28px}
  .compare-row{display:flex;gap:14px;margin-bottom:28px;flex-wrap:wrap}
  .compare-card{flex:1;min-width:200px;border-radius:10px;padding:16px 18px}
  .compare-card.basic{background:#1e3a5f22;border:1px solid #3b82f655}
  .compare-card.premium{background:#10b98115;border:2px solid #10b981}
  .compare-card .price{font-size:22px;font-weight:800;margin-bottom:4px}
  .compare-card.basic .price{color:#3b82f6}
  .compare-card.premium .price{color:#10b981}
  .compare-card .ctitle{font-size:11px;font-weight:700;text-transform:uppercase;
                         letter-spacing:.07em;margin-bottom:12px;color:#94a3b8}
  .compare-card li{font-size:12px;color:#cbd5e1;margin-bottom:6px;list-style:none;
                   display:flex;align-items:flex-start;gap:8px}
  .compare-card li .ic{flex-shrink:0;margin-top:1px}
  h2{font-size:13px;font-weight:700;color:#94a3b8;text-transform:uppercase;
     letter-spacing:.08em;margin-bottom:14px}
  .features{list-style:none;margin-bottom:28px;display:flex;flex-direction:column;gap:10px}
  .features li{display:flex;align-items:flex-start;gap:12px;font-size:14px;
               color:#cbd5e1;line-height:1.5}
  .features li .ic{color:#10b981;font-size:16px;flex-shrink:0;margin-top:1px}
  .features li strong{color:#f1f5f9}
  .divider{border:none;border-top:1px solid #334155;margin:24px 0}
  .cta-row{display:flex;gap:12px;flex-wrap:wrap}
  .btn-primary{flex:1;min-width:200px;background:linear-gradient(135deg,#10b981,#059669);
               color:#fff;text-decoration:none;padding:14px 24px;border-radius:9px;
               font-weight:700;font-size:15px;text-align:center;display:block}
  .btn-primary:hover{opacity:.9}
  .btn-secondary{flex:1;min-width:180px;background:transparent;color:#10b981;
                 border:2px solid #10b981;text-decoration:none;padding:12px 24px;
                 border-radius:9px;font-weight:700;font-size:14px;text-align:center;
                 display:block}
  .btn-secondary:hover{background:#10b98115}
  .trust{margin-top:16px;font-size:11px;color:#475569;text-align:center}
  .trust span{margin:0 8px}
  .err{background:#7f1d1d33;border:1px solid #ef444455;border-radius:8px;
       padding:10px 14px;font-size:11px;color:#fca5a5;margin-top:14px;
       font-family:monospace;word-break:break-all;display:{%if stripe_error%}block{%else%}none{%endif%}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">☀ HeliaPV &mdash; Étude complète</div>

  <h1>Étude complète &amp; exhaustive<br><span style="color:#10b981">Commune de {{nom}}</span></h1>
  <p class="subtitle">Livrée sous 24 h — document PDF professionnel A4 + carte interactive + calpinage détaillé</p>

  <div class="compare-row">
    <div class="compare-card basic">
      <div class="ctitle">📄 Rapport PDF &mdash; 9,90 €</div>
      <ul>
        <li><span class="ic">✅</span> Inventaire sites solaires</li>
        <li><span class="ic">✅</span> Potentiel kWc / kWh par site</li>
        <li><span class="ic">✅</span> Analyse financière indicative</li>
        <li><span class="ic">✅</span> Références cadastrales MAJIC</li>
        <li><span class="ic">✅</span> Synthèse réglementaire L.171-5</li>
      </ul>
    </div>
    <div class="compare-card premium">
      <div class="ctitle">🔬 Étude complète &mdash; <span class="price">129 €/site</span></div>
      <ul>
        <li><span class="ic">✅</span> Tout ce qui est dans le rapport PDF</li>
        <li><span class="ic">⭐</span> <strong>Calpinage détaillé</strong> module par module pour chaque toiture</li>
        <li><span class="ic">⭐</span> <strong>Plan de masse</strong> à l’échelle 1/500 (prêt pour déclaration préalable)</li>
        <li><span class="ic">⭐</span> <strong>Étude autoconsommation</strong> 8 760 h PVGIS + courbes de charge</li>
        <li><span class="ic">⭐</span> <strong>Scenarios d’investissement</strong> comparés (TRI, VAN, ROI 20 ans)</li>
      </ul>
    </div>
  </div>

  <h2>Ce que vous recevez</h2>
  <ul class="features">
    <li><span class="ic">📍</span>
      <span><strong>Calpinage module par module</strong> — schéma PDF de chaque toiture avec positionnement exact des panneaux et puissances réelles</span>
    </li>
    <li><span class="ic">📍</span>
      <span><strong>Plan de masse officiel</strong> — vue cadastrale à l’échelle 1/500, légende, rose des vents ; prêt pour déclaration préalable de travaux</span>
    </li>
    <li><span class="ic">📊</span>
      <span><strong>Étude autoconsommation</strong> — simulation 8 760 h/an PVGIS ERA5, taux d’autoconsommation, bénéfice net annuel, CO₂ évité</span>
    </li>
    <li><span class="ic">📈</span>
      <span><strong>Scenarios financiers comparés</strong> — retour sur investissement détaillé sur 20 ans (TRI, VAN, ROI)</span>
    </li>
    <li><span class="ic">📄</span>
      <span><strong>Dossier prêt pour délibération</strong> — PDF A4 complet, utilisable directement en conseil municipal ou dossier de subvention</span>
    </li>
  </ul>

  <hr class="divider">

  <div class="cta-row">
    <button onclick="openRappelEtude()" class="btn-primary">📞 Être rappelé — Gratuit →</button>
    <a href="mailto:info@heliapv.fr?subject=Commande+etude+{{nom}}&body=Je+souhaite+l%27etude+complete+pour+{{nom}}+Ref:{{rid}}"
       class="btn-secondary">✉ Commander par email →</a>
    <a href="/campaign/plan/{{rid}}" class="btn-secondary">← Retour au plan</a>
  </div>

  <p class="trust">
    <span>🔒 Données confidentielles</span>
    <span>📄 Livraison sous 24h</span>
    <span>🇫🇷 Données officielles IGN / MAJIC / PVGIS</span>
  </p>
</div>

<div id="modal-rappel-etude" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9999;align-items:center;justify-content:center">
  <div style="background:#1e293b;border:1px solid #334155;border-radius:14px;padding:32px;max-width:440px;width:90%;font-family:system-ui,Arial,sans-serif;color:#f1f5f9">
    <h3 style="color:#10b981;margin-bottom:18px;font-size:17px">📞 Demande de rappel gratuit</h3>
    <form id="form-rappel-etude" onsubmit="envoyerRappelEtude(event)">
      <label style="font-size:12px;color:#64748b;display:block;margin-bottom:4px">Votre nom *</label>
      <input type="text" id="re-nom" placeholder="Jean Dupont" required style="width:100%;background:#0f1b2d;border:1px solid #334155;color:#f1f5f9;padding:10px 12px;border-radius:7px;font-size:13px;margin-bottom:12px">
      <label style="font-size:12px;color:#64748b;display:block;margin-bottom:4px">Email *</label>
      <input type="email" id="re-email" placeholder="contact@commune.fr" required style="width:100%;background:#0f1b2d;border:1px solid #334155;color:#f1f5f9;padding:10px 12px;border-radius:7px;font-size:13px;margin-bottom:12px">
      <label style="font-size:12px;color:#64748b;display:block;margin-bottom:4px">Téléphone</label>
      <input type="tel" id="re-tel" placeholder="06 ..." style="width:100%;background:#0f1b2d;border:1px solid #334155;color:#f1f5f9;padding:10px 12px;border-radius:7px;font-size:13px;margin-bottom:12px">
      <div style="display:flex;gap:10px;margin-top:4px">
        <button type="submit" style="flex:1;background:#10b981;color:#fff;border:none;padding:12px;border-radius:7px;font-weight:700;cursor:pointer;font-size:13px">Envoyer →</button>
        <button type="button" onclick="document.getElementById('modal-rappel-etude').style.display='none'" style="background:#334155;color:#94a3b8;border:none;padding:12px 20px;border-radius:7px;cursor:pointer;font-size:13px">Annuler</button>
      </div>
      <div id="rappel-etude-ok" style="display:none;color:#10b981;font-size:13px;text-align:center;padding:12px;margin-top:8px">✓ Demandé ! Rappel sous 24h.</div>
    </form>
  </div>
</div>
<script>
function openRappelEtude(){document.getElementById('modal-rappel-etude').style.display='flex';}
document.getElementById('modal-rappel-etude').addEventListener('click',function(e){if(e.target===this)this.style.display='none';});
async function envoyerRappelEtude(e){
  e.preventDefault();
  const btn=e.target.querySelector('[type=submit]');
  btn.disabled=true;btn.textContent='⏳ Envoi...';
  try{
    await fetch('/campaign/rappel',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({nom_contact:document.getElementById('re-nom').value,email:document.getElementById('re-email').value,telephone:document.getElementById('re-tel').value,message:'Interet etude complete 39EUR/site',commune:'{{nom}}',recipient_id:'{{rid}}'})});
    e.target.style.display='none';
    document.getElementById('rappel-etude-ok').style.display='block';
    setTimeout(()=>document.getElementById('modal-rappel-etude').style.display='none',2500);
  }catch(err){btn.disabled=false;btn.textContent='Envoyer →';}
}
</script>
</body>
</html>"""


@campaign_bp.route('/etude-info/<recipient_id>')
def etude_info(recipient_id):
    """Page descriptive de l'étude complète 39 € (sans Stripe — présentation + CTA)."""
    nom_commune = 'votre commune'
    try:
        conn = get_db()
        row = conn.execute("SELECT nom_commune FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
        if row:
            nom_commune = row['nom_commune'] or nom_commune
    except Exception:
        pass
    return render_template_string(ETUDE_CHECKOUT_HTML,
        rid=recipient_id, nom=nom_commune, BASE_URL=BASE_URL, stripe_error=None)


@campaign_bp.route('/etude-checkout/<recipient_id>')
def etude_checkout(recipient_id):
    """Crée une Stripe Checkout Session (39 €) pour l'étude complète."""
    import os
    stripe_key = os.environ.get('STRIPE_SECRET_KEY', '')

    nom_commune = 'votre commune'
    try:
        conn = get_db()
        row = conn.execute("SELECT nom_commune FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
        if row:
            nom_commune = row['nom_commune'] or nom_commune
    except Exception:
        pass

    if not stripe_key:
        return render_template_string(ETUDE_CHECKOUT_HTML,
            rid=recipient_id, nom=nom_commune, BASE_URL=BASE_URL, stripe_error=None)

    try:
        import stripe
        stripe.api_key = stripe_key
        base = BASE_URL.rstrip('/')
        price_id = os.environ.get('STRIPE_PRICE_ID_ETUDE', '')

        if price_id:
            line_items = [{'price': price_id, 'quantity': 1}]
        else:
            line_items = [{
                'price_data': {
                    'currency': 'eur',
                    'unit_amount': 12900,
                    'product_data': {'name': 'Étude complète et exhaustive — site solaire HeliaPV'}
                },
                'quantity': 1,
            }]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f'{base}/campaign/etude-success/{recipient_id}?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base}/campaign/plan/{recipient_id}',
            metadata={'recipient_id': recipient_id, 'product': 'etude_complete'},
        )
        return redirect(checkout_session.url, code=303)
    except Exception as stripe_err:
        print(f"⚠️ [STRIPE] Erreur checkout étude pour {recipient_id}: {stripe_err}")
        return render_template_string(ETUDE_CHECKOUT_HTML,
            rid=recipient_id, nom=nom_commune, BASE_URL=BASE_URL,
            stripe_error=str(stripe_err))


@campaign_bp.route('/etude-success/<recipient_id>')
def etude_success(recipient_id):
    """Page de retour après paiement étude complète réussi."""
    try:
        conn = get_db()
        try:
            conn.execute("ALTER TABLE recipients ADD COLUMN etude_unlocked BOOLEAN DEFAULT FALSE")
            conn.commit()
        except Exception:
            pass
        conn.execute("UPDATE recipients SET etude_unlocked=? WHERE id=?", (True, recipient_id))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return redirect(f'/campaign/plan/{recipient_id}', code=303)


@campaign_bp.route('/etude/<recipient_id>')
def etude_report(recipient_id):
    """Rapport étude complète (gated — requiert etude_unlocked=TRUE)."""
    try:
        conn = get_db()
        row  = conn.execute("SELECT * FROM recipients WHERE id=?", (recipient_id,)).fetchone()
        conn.close()
    except Exception:
        row = None

    if not row:
        return "Lien invalide", 404
    rec = dict(row)
    if not rec.get('etude_unlocked'):
        return redirect(f'/campaign/etude-info/{recipient_id}', code=303)

    nom        = rec.get('nom_commune', 'Commune')
    code_insee = rec.get('code_insee', '')
    try:
        from mairies_diagnostic import build_commune_diagnostic, diagnostic_summary
        lat = rec.get('lat') or 46.5
        lon = rec.get('lon') or 2.3
        diag_full = build_commune_diagnostic(
            code_insee=code_insee, nom_commune=nom, lat=lat, lon=lon)
        summary = diagnostic_summary(diag_full)
    except Exception as e:
        return f"<pre>Erreur génération étude : {e}</pre>", 500

    return render_template_string(PDF_REPORT_HTML,
        nom=nom, dept=rec.get('departement', ''), summary=summary, diag=diag_full)


# ── Tracking endpoints (publics) ───────────────────────────────────────────────

@campaign_bp.route('/track/<recipient_id>')
def track_cta_click(recipient_id):
    """Tracking silencieux pour les boutons CTA de la page plan (rappel, étude)."""
    record_click(recipient_id)
    return '', 204


@campaign_bp.route('/open/<recipient_id>')
def track_open(recipient_id):
    record_open(recipient_id)
    return Response(_GIF1x1, mimetype='image/gif',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate'})


@campaign_bp.route('/click-plan/<recipient_id>')
def track_click_plan(recipient_id):
    """Track le clic sur la carte interactive, puis redirige vers /plan/<id>."""
    record_click_plan(recipient_id)
    # Transmettre tous les query params vers la route plan
    plan_url = f"{BASE_URL}/campaign/plan/{recipient_id}"
    if request.query_string:
        plan_url += '?' + request.query_string.decode('utf-8')
    return redirect(plan_url)


@campaign_bp.route('/click/<recipient_id>')
def track_click(recipient_id):
    record_click(recipient_id)
    # Récupérer infos commune si dispo
    nom, dept = '', ''
    try:
        conn = get_db()
        row = conn.execute("SELECT nom_commune, departement FROM recipients WHERE id=?",
                           (recipient_id,)).fetchone()
        conn.close()
        if row:
            nom  = row['nom_commune'] or ''
            dept = row['departement'] or ''
    except Exception:
        pass
    # Fallback depuis query params (emails de test)
    if not nom:
        nom  = request.args.get('commune', '')
        dept = request.args.get('dept', '')
    return render_template_string(CONTACT_PAGE_HTML,
        nom=nom, dept=dept,
        BASE_URL=BASE_URL, recipient_id=recipient_id)


CONTACT_PAGE_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Diagnostic complet — HeliaPV{% if nom %} · {{nom}}{% endif %}</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,Arial,sans-serif;background:#0f1b2d;color:#f1f5f9;min-height:100vh}
.topbar{background:#1e293b;border-bottom:1px solid #334155;padding:16px 32px;display:flex;align-items:center;gap:16px}
.topbar .brand{color:#10b981;font-size:15px;font-weight:700;letter-spacing:1px;text-transform:uppercase}
.topbar .sub{color:#64748b;font-size:13px}
.navbar{background:#1e293b;border-bottom:1px solid #0f1b2d;padding:0 32px;display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.navbar a{color:#94a3b8;font-size:13px;font-weight:500;text-decoration:none;padding:10px 14px;
           border-bottom:2px solid transparent;transition:color .15s,border-color .15s;white-space:nowrap}
.navbar a:hover{color:#f1f5f9;border-bottom-color:#334155}
.navbar a.active{color:#10b981;border-bottom-color:#10b981}
.hero{background:linear-gradient(135deg,#0f1b2d 0%,#1e3a5f 100%);padding:56px 32px 48px;text-align:center;border-bottom:1px solid #334155}
.hero h1{font-size:28px;font-weight:700;color:#fff;margin-bottom:12px;line-height:1.3}
.hero p{color:#94a3b8;font-size:15px;max-width:600px;margin:0 auto}
.badge{display:inline-block;background:#10b98122;border:1px solid #10b98155;color:#10b981;
       font-size:12px;font-weight:600;padding:4px 14px;border-radius:20px;margin-bottom:20px;letter-spacing:.5px}
.content{max-width:840px;margin:0 auto;padding:48px 24px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:40px}
@media(max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:28px}
.card h2{font-size:15px;font-weight:700;color:#10b981;text-transform:uppercase;
         letter-spacing:1px;margin-bottom:18px;display:flex;align-items:center;gap:8px}
.card ul{list-style:none;padding:0}
.card ul li{color:#cbd5e1;font-size:14px;line-height:1.7;padding:7px 0;
            border-bottom:1px solid #334155;display:flex;gap:10px;align-items:flex-start}
.card ul li:last-child{border-bottom:none}
.card ul li::before{content:"→";color:#10b981;font-weight:700;flex-shrink:0;margin-top:1px}
.cta-box{background:#1e293b;border:1px solid #10b98155;border-radius:14px;padding:40px 32px;text-align:center}
.cta-box h2{font-size:20px;font-weight:700;color:#fff;margin-bottom:10px}
.cta-box p{color:#94a3b8;font-size:14px;margin-bottom:28px;line-height:1.6}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
@media(max-width:560px){.form-row{grid-template-columns:1fr}}
.form-row input,.form-full input,.form-full textarea{
  width:100%;background:#0f1b2d;border:1px solid #334155;color:#f1f5f9;
  border-radius:7px;padding:11px 14px;font-size:14px;outline:none;font-family:inherit}
.form-full{margin-bottom:14px}
.form-full textarea{resize:vertical;min-height:90px}
input:focus,textarea:focus{border-color:#10b981}
.form-hint{color:#64748b;font-size:12px;margin-bottom:20px;text-align:left}
.btn-submit{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;
            padding:14px 40px;border-radius:8px;font-size:15px;font-weight:700;
            cursor:pointer;width:100%;letter-spacing:.5px;transition:opacity .2s}
.btn-submit:hover{opacity:.9}
.success-msg{display:none;background:#10b98122;border:1px solid #10b981;border-radius:8px;
             padding:16px;color:#10b981;font-size:14px;margin-top:16px;text-align:center}
.footer{text-align:center;color:#475569;font-size:12px;padding:32px;border-top:1px solid #1e293b;margin-top:40px}
</style>
</head>
<body>
<div class="topbar">
  <span class="brand">HeliaPV</span>
  <span class="sub">Assistance à Maîtrise d'Ouvrage — Énergie Solaire</span>
</div>
<nav class="navbar">
  <a href="{{BASE_URL}}/">Accueil</a>
  <a href="{{BASE_URL}}/app">Application</a>
  <a href="{{BASE_URL}}/actualites-solaires">Actualités</a>
  <a href="{{BASE_URL}}/bureaux-etudes">Bureau d'études</a>
  <a href="{{BASE_URL}}/blog">Blog</a>
</nav>

<div class="hero">
  <div class="badge">✓ Diagnostic cadastral MAJIC {% if nom %}— Commune de {{nom}}{% if dept %} ({{dept}}){% endif %}{% endif %}</div>
  <h1>Diagnostic complet &amp; accompagnement AMO</h1>
  <p>HeliaPV accompagne votre collectivité de l'étude de faisabilité jusqu'à la mise en service, en toute indépendance vis-à-vis des fournisseurs et installateurs.</p>
</div>

<div class="content">
  <div class="grid">
    <div class="card">
      <h2>🔍 Diagnostic approfondi</h2>
      <ul>
        <li>Analyser le potentiel réel du site sur l'ensemble du patrimoine communal</li>
        <li>Identifier les contraintes techniques et réglementaires (urbanisme, ABF, réseau)</li>
        <li>Anticiper les conditions de raccordement au réseau Enedis</li>
        <li>Vérifier les équilibres économiques et le temps de retour sur investissement</li>
      </ul>
    </div>
    <div class="card">
      <h2>🤝 Accompagnement AMO</h2>
      <ul>
        <li>Rédiger un cahier des charges précis et adapté au photovoltaïque</li>
        <li>Analyser objectivement les offres des opérateurs et installateurs</li>
        <li>Sécuriser le choix du contractant général ou en autoconsommation</li>
        <li>Assurer un suivi indépendant jusqu'à la mise en service</li>
      </ul>
    </div>
  </div>

  <div class="cta-box">
    <h2>Demander un devis d'accompagnement</h2>
    <p>Renseignez vos coordonnées, nous vous recontactons sous 48h avec une proposition adaptée à votre commune.</p>
    <form id="devisForm" onsubmit="submitForm(event)">
      <div class="form-row">
        <input type="text" name="nom_contact" placeholder="Votre nom" required>
        <input type="text" name="fonction" placeholder="Fonction (ex : DGS, Maire…)">
      </div>
      <div class="form-row">
        <input type="email" name="email" placeholder="Email de contact" required>
        <input type="tel" name="telephone" placeholder="Téléphone">
      </div>
      <div class="form-full">
        <input type="text" name="commune" placeholder="Commune"
               value="{% if nom %}{{nom}}{% endif %}">
      </div>
      <div class="form-full">
        <textarea name="message" placeholder="Message (optionnel) — sites prioritaires, questions…"></textarea>
      </div>
      <div class="form-hint">* En soumettant ce formulaire vous acceptez d'être recontacté par HeliaPV dans le cadre de votre demande.</div>
      <button type="submit" class="btn-submit">Envoyer ma demande de devis →</button>
      <div class="success-msg" id="successMsg">
        ✓ Votre demande a bien été envoyée. Nous vous recontactons sous 48h.
      </div>
    </form>
  </div>
</div>

<div class="footer">
  HeliaPV — Diagnostic Solaire Municipal &nbsp;|&nbsp; <a href="{{BASE_URL}}/campaign/unsub?email={{recipient_id}}" style="color:#475569">Se désabonner</a>
</div>

<script>
async function submitForm(e) {
  e.preventDefault();
  const form = e.target;
  const btn = form.querySelector('.btn-submit');
  btn.disabled = true;
  btn.textContent = 'Envoi en cours…';
  const data = Object.fromEntries(new FormData(form));
  data.recipient_id = '{{recipient_id}}';
  data.source = 'campaign_click';
  try {
    const res = await fetch('{{BASE_URL}}/campaign/devis', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
    document.getElementById('successMsg').style.display = 'block';
    btn.style.display = 'none';
  } catch(err) {
    btn.disabled = false;
    btn.textContent = 'Envoyer ma demande de devis →';
    alert('Erreur réseau, veuillez réessayer.');
  }
}
</script>
</body>
</html>"""


@campaign_bp.route('/unsub')
def unsubscribe():
    rid = request.args.get('email', '')
    if rid:
        record_unsub(rid)
    return render_template_string("""
<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"><title>Désabonnement</title>
<style>body{font-family:Arial;background:#0f1b2d;color:#f1f5f9;display:flex;align-items:center;
justify-content:center;min-height:100vh}.box{background:#1e293b;border-radius:12px;padding:40px;
text-align:center;max-width:400px}h2{color:#10b981;margin-bottom:16px}p{color:#94a3b8;font-size:14px}
</style></head><body><div class="box">
<h2>✓ Désabonnement enregistré</h2>
<p>Vous ne recevrez plus d'emails de prospection HeliaPV.<br>
Conformément au RGPD, votre demande est prise en compte immédiatement.</p>
</div></body></html>""")
