"""
chantier_module.py — Suivi de Chantier PV Professionnel (>100 kWc)
Conforme IEC 62446-1 | PPSPS | Traçabilité modules | NCF | DOE | Milestone Billing
"""
import uuid
import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify

chantier_bp = Blueprint('chantier', __name__, url_prefix='/chantier')

# ── Phases professionnelles PV > 100 kWc ─────────────────────────────────────
PHASES = [
    {
        "id": "etudes",
        "label": "Études & Ingénierie",
        "abbr": "ENG",
        "icon": "bi-pencil-ruler",
        "color": "#6c5ce7",
        "duree_std": 30,
        "checklist": [
            "Étude de production PVsyst validée (P50/P90)",
            "Étude structurelle charpente signée",
            "Note de calcul électrique DC/AC",
            "Plans d'exécution IFC établis",
            "Schéma unifilaire approuvé",
            "Plan de câblage strings établi",
            "CCTP / DPGF finalisé",
            "Plan de masse disponible",
            "Étude d'ombe (masques) réalisée",
            "Choix technologie (modules/onduleurs) validé",
        ]
    },
    {
        "id": "permitting",
        "label": "Permitting & Administratif",
        "abbr": "ADM",
        "icon": "bi-file-earmark-check",
        "color": "#0984e3",
        "duree_std": 90,
        "checklist": [
            "DICT déposée",
            "Déclaration Préalable / PC déposé",
            "DP/PC obtenu",
            "Convention de raccordement ENEDIS signée",
            "Contrat OA / PPA signé",
            "Assurance TRC souscrite",
            "Assurance RC chantier souscrite",
            "PPSPS établi et validé",
            "Plan Général de Coordination (PGC) si applicable",
            "RICT (Mission inspection technique) si applicable",
            "Déclaration ADEME / PTF déposée",
        ]
    },
    {
        "id": "appro",
        "label": "Approvisionnement",
        "abbr": "APPRO",
        "icon": "bi-truck",
        "color": "#00b894",
        "duree_std": 45,
        "checklist": [
            "Commande modules confirmée (bon de commande signé)",
            "Commande onduleurs confirmée",
            "Commande structure/rails confirmée",
            "Commande câblage DC / BOS confirmée",
            "Commande armoire AC / TGBT confirmée",
            "Livraison modules : contrôle quantitatif",
            "Livraison modules : contrôle qualitatif (flashage)",
            "Livraison onduleurs reçue et vérifiée",
            "Livraison structure reçue et vérifiée",
            "Traçabilité numéros de série modules enregistrée",
            "PV de réception matériaux signé",
        ]
    },
    {
        "id": "structure",
        "label": "Génie Civil & Structure",
        "abbr": "GC",
        "icon": "bi-buildings",
        "color": "#e17055",
        "duree_std": 20,
        "checklist": [
            "Dépose / préparation toiture",
            "Renforcement charpente réalisé",
            "Reprise d'étanchéité réalisée",
            "Pose des rails / système de fixation",
            "Vérification alignement et niveaux",
            "Protection anticorrosion appliquée",
            "PV de réception structure signé",
        ]
    },
    {
        "id": "installation",
        "label": "Installation PV",
        "abbr": "INST",
        "icon": "bi-lightning-charge",
        "color": "#fdcb6e",
        "duree_std": 30,
        "checklist": [
            "Pose modules string par string (N/S enregistrés)",
            "Câblage DC strings réalisé",
            "Installation boîtes de jonction / combiners",
            "Tirage câbles DC vers onduleurs",
            "Installation des onduleurs",
            "Câblage AC onduleurs vers TGBT",
            "Installation compteur de prod / monitoring",
            "Mise à la terre et équipotentialité",
            "Vérification protection foudre (parafoudres)",
            "Étiquetage et repérage des câbles réalisé",
            "Nettoyage chantier finalisé",
        ]
    },
    {
        "id": "commissioning",
        "label": "Commissioning IEC 62446",
        "abbr": "COM",
        "icon": "bi-clipboard2-pulse",
        "color": "#a29bfe",
        "duree_std": 10,
        "checklist": [
            "Tests continuité conducteurs DC (IEC 62446-1 §4.2)",
            "Tests polarité strings (§4.3)",
            "Tests isolement DC >= 1 Mohm (§4.4)",
            "Tests de fonctionnement des onduleurs",
            "Tests protection anti-îlotage (découplage)",
            "Mesure Voc strings vs Vocref (écart < 2%)",
            "Mesure Isc strings vs Iscref",
            "Courbes I-V mesurées (si équipement disponible)",
            "Thermographie IR réalisée",
            "Vérification paramétrage monitoring",
            "Rapport MEP IEC 62446-1 établi",
            "Rapport d'essai signé (MOA + installateur)",
        ]
    },
    {
        "id": "raccordement",
        "label": "Raccordement & MEP Officielle",
        "abbr": "RAC",
        "icon": "bi-plug",
        "color": "#00cec9",
        "duree_std": 30,
        "checklist": [
            "Dossier CONSUEL déposé",
            "Visite CONSUEL réalisée",
            "Attestation CONSUEL obtenue",
            "Demande Mise en Service ENEDIS transmise",
            "Mise en service ENEDIS effectuée",
            "Premier kWh injecté enregistré",
            "Monitoring production opérationnel",
            "Compte-rendu MEP transmis au client",
        ]
    },
    {
        "id": "cloture",
        "label": "Clôture & DOE",
        "abbr": "DOE",
        "icon": "bi-archive",
        "color": "#636e72",
        "duree_std": 15,
        "checklist": [
            "PV de réception sans réserve signé",
            "Levée des réserves totale confirmée",
            "Plans de récolement (as-built) remis",
            "Schéma unifilaire final remis",
            "Certificats de garantie modules transmis",
            "Certificats de garantie onduleurs transmis",
            "Manuel d'exploitation / O&M remis",
            "Formation exploitation réalisée",
            "Rapport IEC 62446 final archivé",
            "DOE complet remis et signé",
            "Facture solde émise",
            "Dossier assurance 10 ans transmis (si applicable)",
        ]
    },
]

METEOS = ["Ensoleillé", "Nuageux", "Pluvieux", "Orageux", "Venteux", "Brumeux", "Neige/Gel"]

NCF_ORIGINES = ["Conception", "Approvisionnement", "Travaux", "Commissioning", "Client", "Réglementaire"]
NCF_GRAVITES = ["Critique", "Majeure", "Mineure", "Observation"]
NCF_STATUTS  = ["Ouverte", "En cours de traitement", "Clôturée", "Refusée"]

MILESTONES_DEFAULT = [
    {"id": "m1", "label": "Démarrage chantier (mobilisation)", "pct": 20},
    {"id": "m2", "label": "Livraison matériaux", "pct": 25},
    {"id": "m3", "label": "Fin pose modules", "pct": 30},
    {"id": "m4", "label": "Commissioning IEC 62446", "pct": 15},
    {"id": "m5", "label": "Réception provisoire", "pct": 5},
    {"id": "m6", "label": "Levée réserves / Réception définitive", "pct": 5},
]

DOE_DOCUMENTS = [
    {"id": "plans_recolement",    "label": "Plans de récolement (as-built)"},
    {"id": "schema_unifilaire",   "label": "Schéma unifilaire final"},
    {"id": "rapport_iec_62446",   "label": "Rapport IEC 62446-1"},
    {"id": "pv_reception",        "label": "PV de réception"},
    {"id": "attestation_consuel", "label": "Attestation CONSUEL"},
    {"id": "cert_modules",        "label": "Certificats garantie modules"},
    {"id": "cert_onduleurs",      "label": "Certificats garantie onduleurs"},
    {"id": "manual_om",           "label": "Manuel d'exploitation O&M"},
    {"id": "rapport_pvyst",       "label": "Rapport PVsyst final"},
    {"id": "thermographie",       "label": "Rapport thermographie IR"},
    {"id": "liste_series",        "label": "Liste N° de série modules"},
    {"id": "assurance_do",        "label": "Police assurance DO 10 ans"},
]

# ── Helpers DB ────────────────────────────────────────────────────────────────
def _get_db():
    try:
        from agriweb_hebergement_gratuit import get_db_connection
        return get_db_connection()
    except Exception:
        return None

def _load_prospect_chantier(prospect_id: int):
    conn = _get_db()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT data_json FROM agriweb_prospects WHERE id = %s", (prospect_id,))
        row = cur.fetchone()
        if not row:
            return None
        data = row[0] if isinstance(row[0], dict) else json.loads(row[0] or '{}')
        return data.get('chantier')
    except Exception:
        return None
    finally:
        conn.close()

def _load_prospect(prospect_id: int):
    conn = _get_db()
    if not conn:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, nom_prospect, adresse, commune, surface_m2, latitude, longitude, data_json "
            "FROM agriweb_prospects WHERE id = %s",
            (prospect_id,)
        )
        row = cur.fetchone()
        if not row:
            return None
        data = row[7] if isinstance(row[7], dict) else json.loads(row[7] or '{}')
        calpinage = data.get('calpinage', {})
        puissance = (calpinage.get('puissance_crete_kwc')
                     or calpinage.get('puissance_kwc') or 0)
        return {
            'id': row[0], 'nom_prospect': row[1] or '',
            'adresse': row[2] or '', 'commune': row[3] or '',
            'surface_m2': row[4], 'latitude': row[5], 'longitude': row[6],
            'puissance_kwc': puissance, 'data_json': data,
        }
    except Exception:
        return None
    finally:
        conn.close()

def _save_chantier(prospect_id: int, chantier: dict):
    conn = _get_db()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT data_json FROM agriweb_prospects WHERE id = %s", (prospect_id,))
        row = cur.fetchone()
        if not row:
            return False
        data = row[0] if isinstance(row[0], dict) else json.loads(row[0] or '{}')
        data['chantier'] = chantier
        cur.execute("UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                    (json.dumps(data, ensure_ascii=False), prospect_id))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def _init_chantier(prospect_id: int, nom: str = '') -> dict:
    phases = {}
    for ph in PHASES:
        phases[ph['id']] = {
            'statut': 'non_demarre',
            'date_debut': '', 'date_fin_prevue': '', 'date_fin_reelle': '',
            'checklist': {item: False for item in ph['checklist']},
            'taches': [],
        }
    return {
        'nom_projet': nom,
        'montant_total_ht': 0,
        'retenue_garantie_pct': 5.0,
        'date_debut_projet': '',
        'date_fin_prevue_projet': '',
        'puissance_kwc': 0,
        'nb_modules': 0,
        'phases': phases,
        'journal': [],
        'factures': [],
        'ncf': [],
        'modules_tracking': [],
        'doe_documents': {
            doc['id']: {'statut': 'A_etablir', 'date': '', 'notes': ''}
            for doc in DOE_DOCUMENTS
        },
        'ppsps': {
            'coordonnateur_sps': '',
            'entreprises': [],
            'risques_identifies': '',
            'epi_requis': '',
            'nb_accidents': 0,
            'nb_quasi_accidents': 0,
        },
        'created_at': datetime.now().isoformat(),
    }

def _ensure_keys(chantier: dict) -> dict:
    if 'ncf' not in chantier:
        chantier['ncf'] = []
    if 'modules_tracking' not in chantier:
        chantier['modules_tracking'] = []
    if 'doe_documents' not in chantier:
        chantier['doe_documents'] = {
            doc['id']: {'statut': 'A_etablir', 'date': '', 'notes': ''}
            for doc in DOE_DOCUMENTS
        }
    if 'ppsps' not in chantier:
        chantier['ppsps'] = {
            'coordonnateur_sps': '', 'entreprises': [],
            'risques_identifies': '', 'epi_requis': '',
            'nb_accidents': 0, 'nb_quasi_accidents': 0,
        }
    if 'retenue_garantie_pct' not in chantier:
        chantier['retenue_garantie_pct'] = 5.0
    # Ensure phases have date_fin_reelle
    for ph in PHASES:
        ph_data = chantier.get('phases', {}).get(ph['id'])
        if ph_data and 'date_fin_reelle' not in ph_data:
            ph_data['date_fin_reelle'] = ''
    return chantier

def _calc_avancement(chantier: dict) -> dict:
    phase_pcts = {}
    total = 0
    checked = 0
    for ph in PHASES:
        ph_data = chantier.get('phases', {}).get(ph['id'], {})
        cl = ph_data.get('checklist', {})
        items = len(cl)
        done = sum(1 for v in cl.values() if v)
        taches = ph_data.get('taches', [])
        t_total = len(taches)
        t_done = sum(1 for t in taches if t.get('statut') == 'done')
        if items and t_total:
            pct = round((done / items * 0.7 + t_done / t_total * 0.3) * 100)
        elif items:
            pct = round(done / items * 100)
        elif t_total:
            pct = round(t_done / t_total * 100)
        else:
            pct = 0
        phase_pcts[ph['id']] = pct
        total += items
        checked += done
    global_pct = round(checked / total * 100) if total else 0
    return {'global': global_pct, 'phases': phase_pcts}

def _calc_cash_balance(chantier: dict) -> dict:
    total_ht = chantier.get('montant_total_ht', 0) or 0
    retenue_pct = chantier.get('retenue_garantie_pct', 5.0) or 5.0
    factures = chantier.get('factures', [])
    emis = sum(f.get('montant', 0) for f in factures if f.get('statut') != 'annule')
    encaisse = sum(f.get('montant', 0) for f in factures if f.get('statut') == 'paye')
    retenue = round(total_ht * retenue_pct / 100, 2)
    return {
        'total_ht': total_ht,
        'retenue_garantie': retenue,
        'facture_emis': emis,
        'encaisse': encaisse,
        'restant_a_facturer': max(0, total_ht - emis),
        'restant_a_encaisser': max(0, emis - encaisse),
    }

def _ncf_stats(chantier: dict) -> dict:
    ncf = chantier.get('ncf', [])
    return {
        'total': len(ncf),
        'ouvertes': sum(1 for n in ncf if n.get('statut') == 'Ouverte'),
        'en_cours': sum(1 for n in ncf if n.get('statut') == 'En cours de traitement'),
        'critiques': sum(1 for n in ncf if n.get('gravite') == 'Critique'),
    }

def _doe_pct(chantier: dict) -> int:
    docs = chantier.get('doe_documents', {})
    total = len(DOE_DOCUMENTS)
    done = sum(1 for doc in DOE_DOCUMENTS
               if docs.get(doc['id'], {}).get('statut') == 'Valide')
    return round(done / total * 100) if total else 0

# ── Page principale ───────────────────────────────────────────────────────────
@chantier_bp.route('/<int:prospect_id>')
def page_chantier(prospect_id: int):
    p = _load_prospect(prospect_id)
    if not p:
        return "Prospect introuvable", 404
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id, p.get('nom_prospect', ''))
        if p.get('puissance_kwc'):
            chantier['puissance_kwc'] = p['puissance_kwc']
        _save_chantier(prospect_id, chantier)
    chantier = _ensure_keys(chantier)
    avancement = _calc_avancement(chantier)
    cash = _calc_cash_balance(chantier)
    ncf_stats = _ncf_stats(chantier)
    return render_template(
        'chantier.html',
        prospect=p,
        chantier=chantier,
        phases=PHASES,
        avancement=avancement,
        cash=cash,
        ncf_stats=ncf_stats,
        doe_pct=_doe_pct(chantier),
        meteos=METEOS,
        ncf_origines=NCF_ORIGINES,
        ncf_gravites=NCF_GRAVITES,
        ncf_statuts=NCF_STATUTS,
        doe_documents=DOE_DOCUMENTS,
        milestones_default=MILESTONES_DEFAULT,
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
        "titre": d.get('titre', ''),
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

@chantier_bp.route('/api/<int:prospect_id>/tache/<tache_id>', methods=['PATCH', 'DELETE'])
def update_tache(prospect_id: int, tache_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    for ph_data in chantier['phases'].values():
        for i, t in enumerate(ph_data.get('taches', [])):
            if t['id'] == tache_id:
                if request.method == 'DELETE':
                    ph_data['taches'].pop(i)
                else:
                    t.update(request.get_json())
                _save_chantier(prospect_id, chantier)
                return jsonify({'ok': True, 'tache': t if request.method == 'PATCH' else None,
                                'avancement': _calc_avancement(chantier)})
    return jsonify({'ok': False, 'error': 'Tâche introuvable'}), 404

# ── API : Checklist ───────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/checklist', methods=['PATCH'])
def update_checklist(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    ph_id = d.get('phase_id')
    item = d.get('item')
    val = d.get('value', False)
    if ph_id in chantier['phases']:
        chantier['phases'][ph_id]['checklist'][item] = val
        _save_chantier(prospect_id, chantier)
        return jsonify({'ok': True, 'avancement': _calc_avancement(chantier)})
    return jsonify({'ok': False}), 400

# ── API : Phase ───────────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/phase/<phase_id>', methods=['PATCH'])
def update_phase(prospect_id: int, phase_id: str):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if phase_id in chantier['phases']:
        for key in ('statut', 'date_debut', 'date_fin_prevue', 'date_fin_reelle'):
            if key in d:
                chantier['phases'][phase_id][key] = d[key]
        _save_chantier(prospect_id, chantier)
        return jsonify({'ok': True})
    return jsonify({'ok': False}), 400

# ── API : Journal ─────────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/journal', methods=['POST'])
def add_journal(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    entry = {
        "id": str(uuid.uuid4())[:8],
        "date": d.get('date', date.today().isoformat()),
        "auteur": d.get('auteur', ''),
        "meteo": d.get('meteo', 'Ensoleillé'),
        "arret_chantier": d.get('arret_chantier', False),
        "nb_ouvriers": d.get('nb_ouvriers', ''),
        "contenu": d.get('contenu', ''),
        "created_at": datetime.now().isoformat(),
    }
    chantier['journal'].insert(0, entry)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'entry': entry})

@chantier_bp.route('/api/<int:prospect_id>/journal/<entry_id>', methods=['DELETE'])
def delete_journal(prospect_id: int, entry_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier['journal'] = [e for e in chantier.get('journal', []) if e['id'] != entry_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})

# ── API : Factures (Milestone Billing) ───────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/facture', methods=['POST'])
def add_facture(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    facture = {
        "id": str(uuid.uuid4())[:8],
        "numero": d.get('numero', ''),
        "libelle": d.get('libelle', ''),
        "milestone": d.get('milestone', ''),
        "montant": float(d.get('montant', 0)),
        "retenue_appliquee": d.get('retenue_appliquee', True),
        "date_emission": d.get('date_emission', date.today().isoformat()),
        "date_echeance": d.get('date_echeance', ''),
        "date_paiement": d.get('date_paiement', ''),
        "statut": d.get('statut', 'emis'),
    }
    chantier['factures'].append(facture)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'facture': facture, 'cash': _calc_cash_balance(chantier)})

@chantier_bp.route('/api/<int:prospect_id>/facture/<facture_id>', methods=['PATCH', 'DELETE'])
def update_facture(prospect_id: int, facture_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    for i, f in enumerate(chantier.get('factures', [])):
        if f['id'] == facture_id:
            if request.method == 'DELETE':
                chantier['factures'].pop(i)
            else:
                f.update(request.get_json())
            _save_chantier(prospect_id, chantier)
            return jsonify({'ok': True, 'cash': _calc_cash_balance(chantier)})
    return jsonify({'ok': False}), 404

# ── API : NCF (Non-Conformités) ───────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/ncf', methods=['POST'])
def add_ncf(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if 'ncf' not in chantier:
        chantier['ncf'] = []
    ncf = {
        "id": str(uuid.uuid4())[:8],
        "numero": f"NCF-{len(chantier['ncf']) + 1:03d}",
        "titre": d.get('titre', ''),
        "description": d.get('description', ''),
        "origine": d.get('origine', 'Travaux'),
        "gravite": d.get('gravite', 'Mineure'),
        "phase_id": d.get('phase_id', ''),
        "statut": "Ouverte",
        "actions_correctives": d.get('actions_correctives', ''),
        "responsable": d.get('responsable', ''),
        "date_detection": d.get('date_detection', date.today().isoformat()),
        "date_cloture": '',
        "created_at": datetime.now().isoformat(),
    }
    chantier['ncf'].append(ncf)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'ncf': ncf, 'stats': _ncf_stats(chantier)})

@chantier_bp.route('/api/<int:prospect_id>/ncf/<ncf_id>', methods=['PATCH', 'DELETE'])
def update_ncf(prospect_id: int, ncf_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    for i, n in enumerate(chantier.get('ncf', [])):
        if n['id'] == ncf_id:
            if request.method == 'DELETE':
                chantier['ncf'].pop(i)
            else:
                payload = request.get_json()
                n.update(payload)
                if payload.get('statut') == 'Clôturée' and not n.get('date_cloture'):
                    n['date_cloture'] = date.today().isoformat()
            _save_chantier(prospect_id, chantier)
            return jsonify({'ok': True, 'stats': _ncf_stats(chantier)})
    return jsonify({'ok': False}), 404

# ── API : Modules Tracking ────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/module', methods=['POST'])
def add_module(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if 'modules_tracking' not in chantier:
        chantier['modules_tracking'] = []
    module = {
        "id": str(uuid.uuid4())[:8],
        "numero_serie": d.get('numero_serie', ''),
        "string": d.get('string', ''),
        "position": d.get('position', ''),
        "date_reception": d.get('date_reception', date.today().isoformat()),
        "conforme": d.get('conforme', True),
        "observations": d.get('observations', ''),
    }
    chantier['modules_tracking'].append(module)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'module': module, 'total': len(chantier['modules_tracking'])})

@chantier_bp.route('/api/<int:prospect_id>/module/<mod_id>', methods=['DELETE'])
def delete_module(prospect_id: int, mod_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier['modules_tracking'] = [m for m in chantier.get('modules_tracking', []) if m['id'] != mod_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'total': len(chantier['modules_tracking'])})

# ── API : DOE Documents ───────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/doe', methods=['PATCH'])
def update_doe(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if 'doe_documents' not in chantier:
        chantier['doe_documents'] = {}
    chantier['doe_documents'][d.get('doc_id')] = {
        'statut': d.get('statut', 'A_etablir'),
        'date': d.get('date', ''),
        'notes': d.get('notes', ''),
    }
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'pct': _doe_pct(chantier)})

# ── API : Config ──────────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/config', methods=['PATCH'])
def update_config(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    for key in ('nom_projet', 'montant_total_ht', 'retenue_garantie_pct',
                 'date_debut_projet', 'date_fin_prevue_projet', 'puissance_kwc', 'nb_modules'):
        if key in d:
            chantier[key] = d[key]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'cash': _calc_cash_balance(chantier)})

# ── API : PPSPS ───────────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/ppsps', methods=['PATCH'])
def update_ppsps(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if 'ppsps' not in chantier:
        chantier['ppsps'] = {}
    chantier['ppsps'].update(d)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})

# ── API : Full data ───────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/data', methods=['GET'])
def get_data(prospect_id: int):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    return jsonify({
        'ok': True,
        'chantier': chantier,
        'avancement': _calc_avancement(chantier),
        'cash': _calc_cash_balance(chantier),
        'ncf_stats': _ncf_stats(chantier),
        'doe_pct': _doe_pct(chantier),
    })
