"""
Module Suivi de Chantier Agile – Blueprint Flask
/chantier/<prospect_id>
Stockage : data_json['chantier'] de la table agriweb_prospects
"""

import json
import uuid
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify

chantier_bp = Blueprint('chantier', __name__, url_prefix='/chantier')

# ─── Phases du chantier PV ────────────────────────────────────────────────────

PHASES = [
    {
        "id": "etudes",
        "label": "Études & Conception",
        "icon": "bi-pencil-ruler",
        "color": "#6c5ce7",
        "checklist": [
            "Visite de site effectuée",
            "Rapport de visite rédigé",
            "Plan masse réalisé",
            "Calpinage validé",
            "Note de calcul onduleur",
            "Schema unifilaire réalisé",
            "Étude structure toiture",
        ]
    },
    {
        "id": "admin",
        "label": "Démarches Administratives",
        "icon": "bi-file-text",
        "color": "#0984e3",
        "checklist": [
            "DICT envoyée",
            "Réponse DICT reçue",
            "Déclaration Préalable / PC déposée",
            "Non-opposition DP/PC obtenue",
            "Convention de raccordement Enedis initiée",
            "Accord propriétaire / bail signé",
            "Consuel commandé (anticipé)",
        ]
    },
    {
        "id": "appro",
        "label": "Approvisionnement",
        "icon": "bi-box-seam",
        "color": "#00b894",
        "checklist": [
            "Commande modules PV passée",
            "Commande onduleurs passée",
            "Commande structure / fixations",
            "Commande câblage DC/AC",
            "Livraison modules confirmée",
            "Livraison onduleurs confirmée",
            "Livraison structure confirmée",
            "Contrôle réception matériel",
        ]
    },
    {
        "id": "travaux",
        "label": "Travaux",
        "icon": "bi-hammer",
        "color": "#e17055",
        "checklist": [
            "Ouverture de chantier déclarée",
            "Installation structure / fixations",
            "Pose des modules PV",
            "Câblage DC (strings)",
            "Câblage AC (coffret, onduleur)",
            "Mise à la terre / parafoudre",
            "Tests de continuité DC",
            "Tests AC onduleur",
            "Étanchéité vérifiée",
        ]
    },
    {
        "id": "mep",
        "label": "Mise en Service",
        "icon": "bi-lightning-charge",
        "color": "#fdcb6e",
        "checklist": [
            "Première mise sous tension",
            "Tests onduleur / supervision",
            "Monitoring configuré",
            "Attestation Consuel demandée",
            "Attestation Consuel reçue",
            "PV de réception signé (client)",
        ]
    },
    {
        "id": "raccordement",
        "label": "Raccordement & Facturation",
        "icon": "bi-plug",
        "color": "#00cec9",
        "checklist": [
            "Dossier de raccordement complet envoyé à Enedis",
            "Visite technique Enedis planifiée",
            "Mise en service Enedis effectuée",
            "Contrat OA / CNR / EDF signé",
            "Monitoring production vérifié",
            "Facture solde émise",
            "Règlement solde encaissé",
        ]
    },
]

STATUTS_TACHE = ["todo", "doing", "done", "blocked"]
METEOS = ["☀️ Beau", "🌤 Nuageux", "🌧 Pluie", "🌩 Orage", "🌨 Neige", "💨 Vent", "🌫 Brouillard"]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_prospect_chantier(prospect_id: int) -> dict:
    """Lit data_json['chantier'] du prospect. Retourne un dict vide si absent."""
    from database_adapter import execute_query
    rows = execute_query(
        'SELECT data_json FROM agriweb_prospects WHERE id = %s',
        (prospect_id,), fetch_one=True
    )
    if not rows:
        return {}
    try:
        raw = rows.get('data_json') or {}
        dj = json.loads(raw) if isinstance(raw, str) else raw
        return dj.get('chantier', {})
    except Exception:
        return {}


def _save_chantier(prospect_id: int, chantier: dict):
    """Persiste data_json['chantier'] dans la DB."""
    from database_adapter import execute_query
    rows = execute_query(
        'SELECT data_json FROM agriweb_prospects WHERE id = %s',
        (prospect_id,), fetch_one=True
    )
    if not rows:
        raise ValueError(f"Prospect {prospect_id} introuvable")
    try:
        raw = rows.get('data_json') or {}
        dj = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        dj = {}
    dj['chantier'] = chantier
    execute_query(
        'UPDATE agriweb_prospects SET data_json = %s, date_modification = NOW() WHERE id = %s',
        (json.dumps(dj, ensure_ascii=False), prospect_id)
    )


def _init_chantier(prospect_id: int, nom_projet: str = '') -> dict:
    """Initialise un chantier vierge."""
    return {
        "prospect_id": prospect_id,
        "nom_projet": nom_projet,
        "date_creation": datetime.now().isoformat(),
        "montant_total_ht": 0,
        "phases": {p['id']: {
            "statut": "non_demarre",
            "date_debut": None,
            "date_fin_prevue": None,
            "taches": [],
            "checklist": {item: False for item in p['checklist']},
        } for p in PHASES},
        "journal": [],
        "factures": [],
        "avances_reglement": [],  # cash balance entries
    }


def _calc_avancement(chantier: dict) -> dict:
    """Calcule l'avancement global et par phase."""
    phases_avance = {}
    total_tasks = 0
    done_tasks = 0
    total_check = 0
    done_check = 0

    for ph in PHASES:
        ph_data = chantier.get('phases', {}).get(ph['id'], {})
        tasks = ph_data.get('taches', [])
        checklist = ph_data.get('checklist', {})
        ph_total = len(tasks) + len(checklist)
        ph_done = sum(1 for t in tasks if t.get('statut') == 'done') + sum(1 for v in checklist.values() if v)
        phases_avance[ph['id']] = round(ph_done / ph_total * 100) if ph_total else 0
        total_tasks += len(tasks)
        done_tasks += sum(1 for t in tasks if t.get('statut') == 'done')
        total_check += len(checklist)
        done_check += sum(1 for v in checklist.values() if v)

    grand_total = total_tasks + total_check
    grand_done = done_tasks + done_check
    global_pct = round(grand_done / grand_total * 100) if grand_total else 0
    return {"global": global_pct, "phases": phases_avance}


def _calc_cash_balance(chantier: dict) -> dict:
    """Calcule encaissements cumulés vs dépenses (simplifié)."""
    factures = chantier.get('factures', [])
    encaisse = sum(f.get('montant', 0) for f in factures if f.get('statut') == 'paye')
    emis = sum(f.get('montant', 0) for f in factures if f.get('statut') in ('emis', 'paye'))
    total = chantier.get('montant_total_ht', 0)
    return {
        "total_ht": total,
        "facture_emis": emis,
        "encaisse": encaisse,
        "restant_a_facturer": max(0, total - emis),
        "restant_a_encaisser": max(0, emis - encaisse),
    }


# ─── Routes ───────────────────────────────────────────────────────────────────

@chantier_bp.route('/<int:prospect_id>')
def page_chantier(prospect_id: int):
    """Page principale du suivi de chantier."""
    from database_adapter import execute_query
    p = execute_query(
        'SELECT id, nom_prospect, adresse, commune, data_json FROM agriweb_prospects WHERE id = %s',
        (prospect_id,), fetch_one=True
    )
    if not p:
        return "Prospect introuvable", 404

    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id, p.get('nom_prospect', ''))
        _save_chantier(prospect_id, chantier)

    avancement = _calc_avancement(chantier)
    cash = _calc_cash_balance(chantier)

    return render_template(
        'chantier.html',
        prospect=p,
        chantier=chantier,
        phases=PHASES,
        avancement=avancement,
        cash=cash,
        meteos=METEOS,
        now=datetime.now().strftime('%Y-%m-%d'),
    )


# ── API : Tâches ──────────────────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/tache', methods=['POST'])
def add_tache(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    phase_id = d.get('phase_id')
    if phase_id not in chantier.get('phases', {}):
        return jsonify({'ok': False, 'error': 'Phase inconnue'}), 400
    tache = {
        "id": str(uuid.uuid4())[:8],
        "titre": d.get('titre', '').strip(),
        "description": d.get('description', ''),
        "statut": d.get('statut', 'todo'),
        "responsable": d.get('responsable', ''),
        "deadline": d.get('deadline', ''),
        "priorite": d.get('priorite', 'normale'),
        "created_at": datetime.now().isoformat(),
    }
    chantier['phases'][phase_id]['taches'].append(tache)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'tache': tache, 'avancement': _calc_avancement(chantier)})


@chantier_bp.route('/api/<int:prospect_id>/tache/<tache_id>', methods=['PATCH'])
def update_tache(prospect_id: int, tache_id: str):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    for ph in chantier.get('phases', {}).values():
        for t in ph.get('taches', []):
            if t['id'] == tache_id:
                for k in ('titre', 'description', 'statut', 'responsable', 'deadline', 'priorite'):
                    if k in d:
                        t[k] = d[k]
                _save_chantier(prospect_id, chantier)
                return jsonify({'ok': True, 'avancement': _calc_avancement(chantier)})
    return jsonify({'ok': False, 'error': 'Tâche non trouvée'}), 404


@chantier_bp.route('/api/<int:prospect_id>/tache/<tache_id>', methods=['DELETE'])
def delete_tache(prospect_id: int, tache_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    for ph in chantier.get('phases', {}).values():
        ph['taches'] = [t for t in ph.get('taches', []) if t['id'] != tache_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'avancement': _calc_avancement(chantier)})


# ── API : Checklist ───────────────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/checklist', methods=['PATCH'])
def update_checklist(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    phase_id = d.get('phase_id')
    item = d.get('item')
    val = bool(d.get('value', False))
    chantier.setdefault('phases', {}).setdefault(phase_id, {}).setdefault('checklist', {})[item] = val
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'avancement': _calc_avancement(chantier)})


# ── API : Phase statut ────────────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/phase/<phase_id>', methods=['PATCH'])
def update_phase(prospect_id: int, phase_id: str):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    ph = chantier.setdefault('phases', {}).setdefault(phase_id, {})
    for k in ('statut', 'date_debut', 'date_fin_prevue'):
        if k in d:
            ph[k] = d[k]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})


# ── API : Journal ─────────────────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/journal', methods=['POST'])
def add_journal(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": d.get('date', date.today().isoformat()),
        "auteur": d.get('auteur', ''),
        "meteo": d.get('meteo', ''),
        "arret_chantier": bool(d.get('arret_chantier', False)),
        "contenu": d.get('contenu', '').strip(),
        "created_at": datetime.now().isoformat(),
    }
    chantier.setdefault('journal', []).insert(0, entry)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'entry': entry})


@chantier_bp.route('/api/<int:prospect_id>/journal/<entry_id>', methods=['DELETE'])
def delete_journal(prospect_id: int, entry_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    chantier['journal'] = [e for e in chantier.get('journal', []) if e['id'] != entry_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})


# ── API : Facturation ─────────────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/facture', methods=['POST'])
def add_facture(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    facture = {
        "id": str(uuid.uuid4())[:8],
        "numero": d.get('numero', ''),
        "libelle": d.get('libelle', ''),
        "montant": float(d.get('montant', 0)),
        "date_emission": d.get('date_emission', date.today().isoformat()),
        "date_paiement": d.get('date_paiement', ''),
        "statut": d.get('statut', 'emis'),  # emis / paye / retard / annule
        "created_at": datetime.now().isoformat(),
    }
    chantier.setdefault('factures', []).append(facture)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'facture': facture, 'cash': _calc_cash_balance(chantier)})


@chantier_bp.route('/api/<int:prospect_id>/facture/<facture_id>', methods=['PATCH'])
def update_facture(prospect_id: int, facture_id: str):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    for f in chantier.get('factures', []):
        if f['id'] == facture_id:
            for k in ('numero', 'libelle', 'montant', 'date_emission', 'date_paiement', 'statut'):
                if k in d:
                    f[k] = float(d[k]) if k == 'montant' else d[k]
            _save_chantier(prospect_id, chantier)
            return jsonify({'ok': True, 'cash': _calc_cash_balance(chantier)})
    return jsonify({'ok': False, 'error': 'Facture non trouvée'}), 404


@chantier_bp.route('/api/<int:prospect_id>/facture/<facture_id>', methods=['DELETE'])
def delete_facture(prospect_id: int, facture_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    chantier['factures'] = [f for f in chantier.get('factures', []) if f['id'] != facture_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'cash': _calc_cash_balance(chantier)})


# ── API : Montant total projet ────────────────────────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/config', methods=['PATCH'])
def update_config(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if 'montant_total_ht' in d:
        chantier['montant_total_ht'] = float(d['montant_total_ht'])
    if 'nom_projet' in d:
        chantier['nom_projet'] = d['nom_projet']
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'cash': _calc_cash_balance(chantier)})


# ── API : Données complètes (pour rechargement JS) ────────────────────────────

@chantier_bp.route('/api/<int:prospect_id>/data', methods=['GET'])
def get_data(prospect_id: int):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    return jsonify({
        'ok': True,
        'chantier': chantier,
        'avancement': _calc_avancement(chantier),
        'cash': _calc_cash_balance(chantier),
    })
