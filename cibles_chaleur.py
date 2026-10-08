"""Mode « Cibles chaleur News Solar » de la carte /crm/carte.

Prospects industriels hôtes d'une centrale de chaleur solaire 150-400 °C avec
stockage (News Solar), enrichis du poste source Capareseau et du poste RTE les
plus proches. Ces données sont PROPRES À NEWS SOLAR : elles ne doivent jamais
être visibles d'un autre locataire (marque blanche).

Contrôle d'accès (fail-closed, cf. SECURITE_MULTITENANT_AUDIT.md) :
  1. ``FEATURE_CIBLES_CHALEUR`` doit valoir 1/true/oui/on, sinon le mode
     n'existe pas (404) ;
  2. l'utilisateur doit être authentifié (401 sinon) ;
  3. le compte RÉEL (pas la vue « admin_view_as ») doit être soit dans
     ``CIBLES_CHALEUR_USERS`` (e-mails séparés par des virgules), soit
     administrateur si cette liste est vide. Sinon : 404 (on ne révèle pas
     l'existence du mode).

Le fichier de données n'est PAS dans ``static/`` (qui est servi sans contrôle) :
``data/news_solar/cibles_chaleur.geojson`` (surchargeable par
``CIBLES_CHALEUR_PATH``). Il est produit hors ligne par
``PTV/_documentation/prospection/scripts/enrichir_postes.py``.
"""
import json
import os
import threading

from flask import jsonify, request, Response

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'data', 'news_solar', 'cibles_chaleur.geojson')

_CACHE = {'path': None, 'mtime': None, 'raw': None, 'index': None}
_LOCK = threading.Lock()


def _flag_on():
    return (os.environ.get('FEATURE_CIBLES_CHALEUR') or '').strip().lower() in ('1', 'true', 'oui', 'on', 'yes')


def _allowed_emails():
    raw = os.environ.get('CIBLES_CHALEUR_USERS') or ''
    return {e.strip().lower() for e in raw.replace(';', ',').split(',') if e.strip()}


def _real_user():
    """(user_id, email, is_admin) du compte RÉELLEMENT connecté, sans tenir
    compte de la vue « admin_view_as » ; (None, None, False) si pas de session."""
    from flask import session as flask_session
    token = flask_session.get('session_token') or request.cookies.get('session_token')
    if not token:
        return None, None, False
    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        cur = conn.cursor()
        cur.execute('''
            SELECT u.id, u.email, u.is_admin
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (token,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None, None, False
        if isinstance(row, dict):
            return row.get('id'), (row.get('email') or '').lower(), bool(row.get('is_admin'))
        return row[0], (row[1] or '').lower(), bool(row[2])
    except Exception as e:
        print(f"⚠️ [CIBLES CHALEUR] résolution utilisateur impossible : {e}")
        return None, None, False


def acces_cibles_chaleur():
    """Retourne (statut, user_id) : statut = 'ok' | 'anonyme' | 'refuse'."""
    if not _flag_on():
        return 'refuse', None
    user_id, email, is_admin = _real_user()
    if user_id is None:
        return 'anonyme', None
    # Vue « admin_view_as » active : l'admin regarde l'application avec les yeux
    # d'un client ; le mode ne doit pas apparaître (il n'appartient pas au client).
    from flask import session as flask_session
    if flask_session.get('admin_view_as_user_id'):
        return 'refuse', None
    allowed = _allowed_emails()
    if allowed:
        return ('ok', user_id) if email in allowed else ('refuse', None)
    return ('ok', user_id) if is_admin else ('refuse', None)


def cibles_chaleur_visible():
    """Booléen pour le gabarit (le bouton et le JS ne sont rendus que si True)."""
    try:
        return acces_cibles_chaleur()[0] == 'ok'
    except Exception:
        return False


def data_path():
    return os.environ.get('CIBLES_CHALEUR_PATH') or DEFAULT_PATH


def _load():
    path = data_path()
    mtime = os.path.getmtime(path)
    with _LOCK:
        if _CACHE['path'] != path or _CACHE['mtime'] != mtime:
            with open(path, 'rb') as f:
                raw = f.read()
            gj = json.loads(raw.decode('utf-8'))
            index = {}
            postes = {}
            for ft in gj.get('features', []):
                p = ft.get('properties') or {}
                if p.get('kind') == 'poste_source':
                    postes[p.get('code')] = p
            for ft in gj.get('features', []):
                p = ft.get('properties') or {}
                if p.get('kind') == 'site':
                    index[str(ft.get('id'))] = (ft, postes.get(p.get('ps_code')))
            _CACHE.update(path=path, mtime=mtime, raw=raw, index=index)
        return _CACHE['raw'], _CACHE['index']


def _denied(statut):
    if statut == 'anonyme':
        return jsonify({'success': False, 'error': 'Authentification requise'}), 401
    return jsonify({'success': False, 'error': 'Introuvable'}), 404


def site_vers_ligne_gisement(feature, poste):
    """Convertit une cible chaleur au format d'une ligne ``industrial_prospects``
    attendu par ``_ajouter_site_au_crm`` (réutilisation du bouton existant)."""
    p = feature.get('properties') or {}
    lon, lat = (feature.get('geometry') or {}).get('coordinates', [None, None])[:2]
    naf = p.get('naf') or ''
    chaleur = {k: p.get(k) for k in (
        'score', 'profil', 'libelle_naf_profil', 'naf', 'niveau_thermique', 'temperature_typique',
        'continuite', 'gaz_mwh_an', 'puissance_gaz_moy_kw', 'elec_mwh_an', 'ets', 'ets_co2_t',
        'irep_co2_t', 'icpe_combustion', 'icpe_rubriques_chaleur', 'seveso', 'adequation_taille',
        'remarques', 'ps_code', 'ps_distance_km', 'rte_nom', 'rte_tension', 'rte_distance_km')
        if p.get(k) is not None}
    if poste:
        chaleur['poste_source'] = {k: poste.get(k) for k in (
            'code', 'nom', 'tension_aval_kv', 'tension_amont_kv', 'taux_affectation_pct',
            'capa_reservee_restant_a_affecter_mw', 'capa_transfo_restante_injection_mw')}
    dj = {
        'origine': 'cibles_chaleur_news_solar',
        'cible_chaleur_id': feature.get('id'),
        'chaleur': chaleur,
        'siret': p.get('siret'),
    }
    return {
        'commune': p.get('commune') or '',
        'adresse': p.get('adresse') or '',
        'code_commune': p.get('code_commune') or (p.get('departement') or ''),
        'lat': lat, 'lon': lon,
        'operateur_nom': p.get('raison_sociale') or p.get('enseigne') or 'Exploitant à identifier',
        'operateur_siren': (p.get('siret') or '')[:9] or None,
        'conso_mwh': p.get('elec_mwh_an'),
        'secteur': ('NAF ' + naf) if naf else 'INDUSTRIE',
        'data_json': json.dumps(dj, ensure_ascii=False),
    }


def register_cibles_chaleur_routes(app, ajouter_site_au_crm):
    """Enregistre les routes du mode. ``ajouter_site_au_crm(r, user_id)`` est la
    fonction du CRM qui copie une ligne du gisement dans agriweb_prospects."""

    @app.route('/api/industriel/cibles-chaleur', methods=['GET'])
    def industriel_cibles_chaleur():
        statut, _uid = acces_cibles_chaleur()
        if statut != 'ok':
            return _denied(statut)
        try:
            raw, _ = _load()
        except FileNotFoundError:
            return jsonify({'success': False, 'error': 'Fichier de données absent'}), 503
        resp = Response(raw, mimetype='application/geo+json')
        resp.headers['Cache-Control'] = 'private, no-store'
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        return resp

    @app.route('/api/industriel/cibles-chaleur/ajouter-au-crm', methods=['POST'])
    def industriel_cibles_chaleur_ajouter():
        """Copie UNE cible chaleur dans le CRM de l'utilisateur connecté.
        Body: {id}. Les données sont relues côté serveur (rien n'est pris du client
        hormis l'identifiant) et la cible est toujours le compte courant."""
        statut, uid = acces_cibles_chaleur()
        if statut != 'ok':
            return _denied(statut)
        data = request.get_json(silent=True) or {}
        fid = str(data.get('id') or '').strip()
        if not fid:
            return jsonify({'success': False, 'error': 'id requis'}), 400
        try:
            _, index = _load()
        except FileNotFoundError:
            return jsonify({'success': False, 'error': 'Fichier de données absent'}), 503
        hit = index.get(fid)
        if not hit:
            return jsonify({'success': False, 'error': 'Cible introuvable'}), 404
        try:
            r = site_vers_ligne_gisement(*hit)
            prospect_id, created = ajouter_site_au_crm(r, uid)
            return jsonify({'success': True, 'prospect_id': prospect_id, 'created': created,
                            'commune': r['commune'], 'operateur': r['operateur_nom']})
        except Exception as e:
            print(f"❌ [CIBLES CHALEUR] ajout CRM : {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
