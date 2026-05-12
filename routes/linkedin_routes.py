#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routes Flask — LinkedIn Auto-Poster (dashboard admin)
======================================================

Routes exposées :
    GET  /admin/linkedin              → Dashboard statut
    GET  /admin/linkedin/auth         → Lance le flow OAuth LinkedIn
    GET  /admin/linkedin/callback     → Callback OAuth (échange code ↔ token)
    POST /admin/linkedin/settings     → Met à jour post_hour, enabled
    POST /admin/linkedin/post-now     → Publie immédiatement le prochain article
    GET  /admin/linkedin/preview      → Prévisualise le texte du prochain post (JSON)
    POST /admin/linkedin/revoke       → Supprime le token enregistré
"""

import secrets
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

import linkedin_poster as lp

linkedin_bp = Blueprint("linkedin", __name__, url_prefix="/admin/linkedin")


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _require_admin():
    """Retourne True si l'utilisateur courant est admin, False sinon."""
    user = session.get("user") or {}
    return bool(user.get("is_admin", False))


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard HTML (inline — pas de template externe nécessaire)
# ─────────────────────────────────────────────────────────────────────────────

_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LinkedIn Auto-Poster — HeliaPV Admin</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; }
    body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
           background: #0f1117; color: #e2e8f0; margin: 0; padding: 24px; }
    .card { background: #1e2231; border-radius: 12px; padding: 24px;
            margin-bottom: 20px; border: 1px solid #2d3748; }
    h1    { color: #f0a500; margin: 0 0 4px; font-size: 1.5rem; }
    h2    { color: #90cdf4; font-size: 1.1rem; margin: 0 0 16px; }
    .badge { display:inline-block; padding: 3px 10px; border-radius: 20px;
             font-size: .75rem; font-weight: 600; }
    .ok   { background: #276749; color:#9ae6b4; }
    .warn { background: #7b341e; color:#fbd38d; }
    .info { background: #2c5282; color:#bee3f8; }
    label { display: block; margin-bottom: 6px; color:#a0aec0; font-size:.9rem; }
    input[type=number], input[type=text] {
      background:#2d3748; border:1px solid #4a5568; color:#e2e8f0;
      border-radius:6px; padding:8px 12px; width:120px; }
    .btn { display:inline-block; padding:9px 20px; border-radius:8px;
           border:none; cursor:pointer; font-size:.9rem; font-weight:600;
           text-decoration:none; transition:.2s; }
    .btn-primary  { background:#0e76a8; color:#fff; }
    .btn-primary:hover { background:#0a5f87; }
    .btn-success  { background:#276749; color:#9ae6b4; }
    .btn-success:hover { background:#2f855a; }
    .btn-danger   { background:#9b2c2c; color:#fed7d7; }
    .btn-danger:hover  { background:#822727; }
    .btn-neutral  { background:#2d3748; color:#e2e8f0; }
    .btn-neutral:hover { background:#4a5568; }
    .preview { background:#111827; border:1px solid #374151; border-radius:8px;
               padding:16px; white-space:pre-wrap; font-size:.85rem; line-height:1.6;
               color:#d1fae5; max-height:320px; overflow-y:auto; }
    .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .kv    { display:flex; gap:8px; align-items:center; margin-bottom:8px; }
    .kv span:first-child { color:#718096; min-width:160px; font-size:.85rem; }
    .kv span:last-child  { color:#e2e8f0; font-size:.9rem; }
    form   { display:inline; }
    #msg   { margin-top:12px; padding:10px 16px; border-radius:8px;
             display:none; font-size:.9rem; }
    .flash-ok   { background:#276749; color:#9ae6b4; }
    .flash-err  { background:#7b341e; color:#fbd38d; }
    .separator  { border-color: #2d3748; margin: 16px 0; }
    .mono { font-family: monospace; font-size:.8rem; }
    .toggle-wrap { display:flex; align-items:center; gap:10px; }
    .toggle { position:relative; width:48px; height:26px; }
    .toggle input { opacity:0; width:0; height:0; }
    .slider { position:absolute; cursor:pointer; inset:0; background:#4a5568;
              border-radius:26px; transition:.3s; }
    .slider:before { position:absolute; content:""; height:20px; width:20px;
                     left:3px; bottom:3px; background:#fff; border-radius:50%;
                     transition:.3s; }
    .toggle input:checked + .slider { background:#0e76a8; }
    .toggle input:checked + .slider:before { transform:translateX(22px); }
  </style>
</head>
<body>

<h1>🔗 LinkedIn Auto-Poster</h1>
<p style="color:#718096;margin-top:4px">HeliaPV · Tableau de bord admin</p>

<!-- ── Statut connexion ── -->
<div class="card">
  <h2>Connexion LinkedIn</h2>
  <div class="kv">
    <span>App configurée</span>
    <span>{% if status.configured %}<span class="badge ok">✓ Oui</span>
          {% else %}<span class="badge warn">✗ Variables manquantes</span>{% endif %}</span>
  </div>
  <div class="kv">
    <span>Token valide</span>
    <span>{% if status.token_valid %}<span class="badge ok">✓ Valide</span>
          {% else %}<span class="badge warn">✗ Absent ou expiré</span>{% endif %}</span>
  </div>
  {% if status.person_urn %}
  <div class="kv">
    <span>Auteur</span>
    <span class="mono">{{ status.person_urn }}</span>
  </div>
  {% endif %}
  {% if status.token_expires %}
  <div class="kv">
    <span>Expiration token</span>
    <span>{{ status.token_expires[:10] }}</span>
  </div>
  {% endif %}

  <hr class="separator">

  {% if not status.configured %}
    <p style="color:#fbd38d;font-size:.9rem">
      ⚠ Définissez <code>LINKEDIN_CLIENT_ID</code> et <code>LINKEDIN_CLIENT_SECRET</code>
      dans vos variables d'environnement, puis redémarrez l'application.
    </p>
  {% elif not status.token_valid %}
    <a href="{{ url_for('linkedin.auth_start') }}" class="btn btn-primary">
      🔐 Autoriser LinkedIn
    </a>
  {% else %}
    <a href="{{ url_for('linkedin.auth_start') }}" class="btn btn-neutral" style="margin-right:8px">
      🔄 Re-autoriser
    </a>
    <form action="{{ url_for('linkedin.revoke') }}" method="post" style="display:inline">
      <button type="submit" class="btn btn-danger"
              onclick="return confirm('Supprimer le token enregistré ?')">
        🗑 Révoquer
      </button>
    </form>
  {% endif %}
</div>

<!-- ── Paramètres ── -->
<div class="card">
  <h2>Paramètres de publication</h2>
  <div class="kv">
    <span>Posts publiés</span>
    <span>{{ status.posted_count }}</span>
  </div>
  <div class="kv">
    <span>Dernier post</span>
    <span>{{ status.last_post_at[:19].replace('T',' ') if status.last_post_at else '—' }} UTC</span>
  </div>
  <div class="kv">
    <span>Déjà posté aujourd'hui</span>
    <span>{% if status.already_today %}<span class="badge ok">Oui</span>
          {% else %}<span class="badge info">Non</span>{% endif %}</span>
  </div>

  <hr class="separator">

  <form action="{{ url_for('linkedin.save_settings') }}" method="post" id="settingsForm">
    <div style="display:flex;gap:32px;align-items:flex-end;flex-wrap:wrap">
      <div>
        <label>Heure de publication (UTC)</label>
        <input type="number" name="post_hour" min="0" max="23"
               value="{{ status.post_hour }}" style="width:80px">
      </div>
      <div>
        <label>Publication automatique</label>
        <div class="toggle-wrap">
          <label class="toggle">
            <input type="checkbox" name="enabled" id="enabledToggle"
                   {% if status.enabled %}checked{% endif %}
                   onchange="document.getElementById('settingsForm').submit()">
            <span class="slider"></span>
          </label>
          <span style="font-size:.9rem;color:#a0aec0">
            {% if status.enabled %}Activée{% else %}Désactivée{% endif %}
          </span>
        </div>
      </div>
      <div>
        <button type="submit" class="btn btn-primary">💾 Enregistrer</button>
      </div>
    </div>
  </form>
</div>

<!-- ── Prochain article ── -->
{% if status.next_article %}
<div class="card">
  <h2>Prochain article à publier</h2>
  <div class="kv">
    <span>Titre</span>
    <span style="color:#90cdf4">{{ status.next_article.titre[:90] }}</span>
  </div>
  <div class="kv">
    <span>Source</span>
    <span>{{ status.next_article.source }}</span>
  </div>
  <div class="kv">
    <span>Date</span>
    <span>{{ status.next_article.date_pub[:10] }}</span>
  </div>
  <div class="kv">
    <span>URL</span>
    <span><a href="{{ status.next_article.url }}" target="_blank"
             style="color:#63b3ed;word-break:break-all">{{ status.next_article.url[:80] }}…</a></span>
  </div>

  <hr class="separator">
  <label style="margin-bottom:8px">Aperçu du post LinkedIn :</label>
  <div class="preview">{{ status.next_post_text }}</div>

  <div style="margin-top:16px">
    <button onclick="postNow()" class="btn btn-success"
            {% if not status.token_valid %}disabled{% endif %}>
      🚀 Publier maintenant
    </button>
    <span style="color:#718096;font-size:.8rem;margin-left:12px">
      (publie immédiatement, sans attendre l'heure programmée)
    </span>
  </div>
</div>
{% elif status.token_valid %}
<div class="card">
  <p style="color:#718096">Aucun article disponible — le cache sera rechargé sous peu.</p>
</div>
{% endif %}

<div id="msg"></div>

<script>
async function postNow() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = '⏳ Publication…';
  try {
    const r = await fetch('/admin/linkedin/post-now', { method: 'POST' });
    const d = await r.json();
    const el = document.getElementById('msg');
    el.style.display = 'block';
    if (d.success) {
      el.className = 'flash-ok';
      el.textContent = '✓ Post publié ! ID : ' + (d.post_id || '?') + ' — rechargez pour voir le nouvel article.';
    } else if (d.skipped) {
      el.className = 'flash-err';
      el.textContent = '⏭ Ignoré : ' + d.reason;
      btn.disabled = false;
      btn.textContent = '🚀 Publier maintenant';
    } else {
      el.className = 'flash-err';
      el.textContent = '✗ Erreur : ' + (d.error || JSON.stringify(d));
      btn.disabled = false;
      btn.textContent = '🚀 Publier maintenant';
    }
  } catch(e) {
    document.getElementById('msg').style.display = 'block';
    document.getElementById('msg').className = 'flash-err';
    document.getElementById('msg').textContent = '✗ Erreur réseau : ' + e;
    btn.disabled = false;
    btn.textContent = '🚀 Publier maintenant';
  }
}
</script>

</body>
</html>
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────────────────────────────────────

@linkedin_bp.route("/", methods=["GET"])
def dashboard():
    if not _require_admin():
        return "Accès réservé aux administrateurs.", 403
    status = lp.get_status()
    return render_template_string(_DASHBOARD_HTML, status=status)


@linkedin_bp.route("/auth", methods=["GET"])
def auth_start():
    """Lance le flow OAuth LinkedIn — redirige vers LinkedIn."""
    if not _require_admin():
        return "Accès réservé aux administrateurs.", 403

    if not lp.LINKEDIN_CLIENT_ID:
        return "LINKEDIN_CLIENT_ID non configuré.", 400

    csrf_state = secrets.token_urlsafe(24)
    session["linkedin_oauth_state"] = csrf_state
    auth_url = lp.build_auth_url(csrf_state)
    return redirect(auth_url)


@linkedin_bp.route("/callback", methods=["GET"])
def auth_callback():
    """
    Reçoit le code OAuth de LinkedIn, échange contre un token,
    enregistre le person_urn, puis redirige vers le dashboard.
    """
    if not _require_admin():
        return "Accès réservé aux administrateurs.", 403

    error = request.args.get("error")
    if error:
        desc = request.args.get("error_description", error)
        return f"<p>LinkedIn a refusé l'autorisation : {desc}</p><a href='/admin/linkedin/'>Retour</a>", 400

    code          = request.args.get("code", "")
    received_state = request.args.get("state", "")
    expected_state = session.pop("linkedin_oauth_state", None)

    # Vérification CSRF
    if not expected_state or received_state != expected_state:
        return "<p>Paramètre state invalide (protection CSRF).</p><a href='/admin/linkedin/'>Retour</a>", 400

    if not code:
        return "<p>Code OAuth manquant.</p><a href='/admin/linkedin/'>Retour</a>", 400

    try:
        token_data = lp.exchange_code_for_token(code)
        person_urn = lp.save_token(token_data)
    except ValueError as e:
        return f"<p>Erreur lors de l'échange du token : {e}</p><a href='/admin/linkedin/'>Retour</a>", 400

    return redirect("/admin/linkedin/")


@linkedin_bp.route("/settings", methods=["POST"])
def save_settings():
    """Enregistre post_hour et enabled dans l'état."""
    if not _require_admin():
        return "Accès réservé aux administrateurs.", 403

    state = lp.load_state()

    post_hour = request.form.get("post_hour")
    if post_hour is not None:
        try:
            h = int(post_hour)
            if 0 <= h <= 23:
                state["post_hour"] = h
        except ValueError:
            pass

    # La case cochée envoie "on", non cochée n'envoie rien
    state["enabled"] = "enabled" in request.form

    lp.save_state(state)
    return redirect("/admin/linkedin/")


@linkedin_bp.route("/post-now", methods=["POST"])
def post_now():
    """Publie immédiatement le prochain article (appel AJAX)."""
    if not _require_admin():
        return jsonify({"error": "Accès refusé"}), 403

    if not lp.is_token_valid():
        return jsonify({"skipped": True, "reason": "Token LinkedIn invalide ou absent"})

    article = lp.pick_best_article()
    if not article:
        return jsonify({"skipped": True, "reason": "Aucun article disponible dans le cache"})

    result = lp.post_article(article)
    return jsonify(result)


@linkedin_bp.route("/preview", methods=["GET"])
def preview():
    """Retourne en JSON le texte du prochain post et l'article choisi."""
    if not _require_admin():
        return jsonify({"error": "Accès refusé"}), 403

    article = lp.pick_best_article()
    if not article:
        return jsonify({"article": None, "post_text": ""})

    return jsonify({
        "article":   article,
        "post_text": lp.build_post_text(article),
    })


@linkedin_bp.route("/revoke", methods=["POST"])
def revoke():
    """Supprime le token enregistré (sans appel API LinkedIn — simple nettoyage local)."""
    if not _require_admin():
        return "Accès réservé aux administrateurs.", 403

    state = lp.load_state()
    state["access_token"]     = ""
    state["token_expires_at"] = ""
    state["person_urn"]       = ""
    lp.save_state(state)
    return redirect("/admin/linkedin/")
