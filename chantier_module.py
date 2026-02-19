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

DOC_CATEGORIES = [
    {"id": "visite_technique", "label": "Visite technique",    "icon": "bi-clipboard2-check", "color": "#6c5ce7"},
    {"id": "plans",            "label": "Plans & schémas",     "icon": "bi-file-earmark-ruled", "color": "#0984e3"},
    {"id": "tranchees",        "label": "Tranchées & GC",      "icon": "bi-layers",            "color": "#e17055"},
    {"id": "photos",           "label": "Photos chantier",     "icon": "bi-camera",            "color": "#fdcb6e"},
    {"id": "administratif",    "label": "Administratif",       "icon": "bi-briefcase",         "color": "#00b894"},
    {"id": "reception",        "label": "Réception / DOE",     "icon": "bi-patch-check",       "color": "#a29bfe"},
    {"id": "autre",            "label": "Autres pièces",       "icon": "bi-paperclip",         "color": "#636e72"},
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
        import os, psycopg2
        DATABASE_URL = os.environ.get('DATABASE_URL', '')
        if not DATABASE_URL:
            return None
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        return psycopg2.connect(DATABASE_URL)
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
        'documents': [],
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
        'visite_technique': {
            'date_visite': '', 'interlocuteur': '', 'reference_cadastrale': '',
            'type_couverture': '', 'surface_totale_m2': '', 'surface_retenue_m2': '',
            'orientation_azimut': '', 'pente_degres': '', 'longueur_faitiere_m': '',
            'distance_bord_m': '', 'notes_toiture': '',
            'type_charpente': '', 'etat_charpente': '', 'portee_pannes_m': '',
            'charges_admissibles_kg_m2': '', 'renforcement_necessaire': '',
            'notes_structure': '',
            'acces_toiture': '', 'garde_corps': '', 'lignes_vie': '',
            'prise_230v': '', 'eclairage_dispo': '', 'notes_acces': '',
            'puissance_raccordement_kva': '', 'type_compteur': '',
            'tgbt_accessible': '', 'distance_tgbt_m': '', 'chemin_cable': '',
            'notes_elec': '',
            'type_raccordement_enedis': '', 'distance_point_raccordement_m': '',
            'tranchee_necessaire': '', 'longueur_tranchee_m': '', 'notes_enedis': '',
            'age_batiment_ans': '', 'presence_amiante': '', 'dta_disponible': '',
            'etat_etancheite': '', 'travaux_prealables': '',
            'points_bloquants': '', 'reserves_techniques': '',
            'actions_requises': '',
            'faisabilite': '', 'puissance_retenue_kwc': '', 'nb_modules_retenu': '',
            'observations_generales': '',
            'last_saved': '',
        },
        'intervenants': [],   # {id, nom, entreprise, role, specialite, tel, email, date_debut, date_fin, color}
        'presences': [],      # {id, intervenant_id, date, nb_heures, phase_id, arret, notes}
        'planning': {
            'methode': 'phases',          # 'phases' | 'jalons'
            'contraintes': [],            # {id, phase_id, type, description, date_contrainte}
            'jalons': [],                 # {id, label, date_prevue, date_reelle, type, couleur}
            'jours_indisponibles': [],    # ['YYYY-MM-DD', ...] (jours chômés, intempéries)
            'notes_planning': '',
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
    if 'documents' not in chantier:
        chantier['documents'] = []
    if 'visite_technique' not in chantier:
        chantier['visite_technique'] = {}
    if 'intervenants' not in chantier:
        chantier['intervenants'] = []
    if 'presences' not in chantier:
        chantier['presences'] = []
    if 'planning' not in chantier:
        chantier['planning'] = {
            'methode': 'phases',
            'contraintes': [],
            'jalons': [],
            'jours_indisponibles': [],
            'notes_planning': '',
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
        doc_categories=DOC_CATEGORIES,
        visite_technique=chantier.get('visite_technique', {}),
        intervenants=chantier.get('intervenants', []),
        presences=chantier.get('presences', []),
        planning=chantier.get('planning', {}),
        now=datetime.now().strftime('%Y-%m-%d'),
    )

# ── Rapport IEC 62446-1 ───────────────────────────────────────────────────────
@chantier_bp.route('/<int:prospect_id>/rapport_iec')
def rapport_iec(prospect_id: int):
    p = _load_prospect(prospect_id)
    if not p:
        return "Prospect introuvable", 404
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id, p.get('nom_prospect', ''))
    chantier = _ensure_keys(chantier)
    avancement = _calc_avancement(chantier)
    return render_template(
        'rapport_iec_62446.html',
        prospect=p,
        chantier=chantier,
        phases=PHASES,
        avancement=avancement,
        doe_documents=DOE_DOCUMENTS,
        now=datetime.now().strftime('%d/%m/%Y'),
        generated_at=datetime.now().strftime('%d/%m/%Y à %H:%M'),
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

# ── API : Visite Technique ────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/visite_technique', methods=['PATCH'])
def update_visite_technique(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    if 'visite_technique' not in chantier:
        chantier['visite_technique'] = {}
    chantier['visite_technique'].update(d)
    chantier['visite_technique']['last_saved'] = datetime.now().isoformat()
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'last_saved': chantier['visite_technique']['last_saved']})

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

# ── API : Documents & Médias ──────────────────────────────────────────────────
import base64

@chantier_bp.route('/api/<int:prospect_id>/document', methods=['POST'])
def add_document(prospect_id: int):
    """Reçoit un fichier encodé base64 ou une URL externe."""
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False, 'error': 'Chantier introuvable'}), 404
    chantier = _ensure_keys(chantier)
    doc = {
        "id":          str(uuid.uuid4())[:10],
        "nom":         d.get('nom', 'document'),
        "categorie":   d.get('categorie', 'autre'),
        "type_mime":   d.get('type_mime', 'application/octet-stream'),
        "taille_ko":   d.get('taille_ko', 0),
        "date":        d.get('date', date.today().isoformat()),
        "notes":       d.get('notes', ''),
        "data_b64":    d.get('data_b64', ''),   # base64 content
        "url":         d.get('url', ''),         # OR external link
        "uploaded_at": datetime.now().isoformat(),
    }
    chantier['documents'].append(doc)
    _save_chantier(prospect_id, chantier)
    # Return without data_b64 for lighter payload
    doc_meta = {k: v for k, v in doc.items() if k != 'data_b64'}
    return jsonify({'ok': True, 'doc': doc_meta, 'total': len(chantier['documents'])})

@chantier_bp.route('/api/<int:prospect_id>/document/<doc_id>', methods=['DELETE'])
def delete_document(prospect_id: int, doc_id: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    docs = chantier.get('documents', [])
    chantier['documents'] = [d for d in docs if d['id'] != doc_id]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'total': len(chantier['documents'])})

@chantier_bp.route('/api/<int:prospect_id>/document/<doc_id>/download', methods=['GET'])
def download_document(prospect_id: int, doc_id: str):
    """Renvoie le fichier stocké en base64."""
    from flask import Response
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return "Introuvable", 404
    doc = next((d for d in chantier.get('documents', []) if d['id'] == doc_id), None)
    if not doc:
        return "Document introuvable", 404
    if doc.get('url'):
        from flask import redirect
        return redirect(doc['url'])
    if not doc.get('data_b64'):
        return "Aucun fichier", 404
    file_data = base64.b64decode(doc['data_b64'])
    return Response(
        file_data,
        mimetype=doc.get('type_mime', 'application/octet-stream'),
        headers={"Content-Disposition": f"attachment; filename=\"{doc['nom']}\""}
    )

# ── API : Intervenants ────────────────────────────────────────────────────────
INTERVENANT_COLORS = ['#6c5ce7','#0984e3','#00b894','#e17055','#fdcb6e','#a29bfe','#00cec9','#fd79a8','#55efc4','#74b9ff']

@chantier_bp.route('/api/<int:prospect_id>/intervenant', methods=['POST'])
def add_intervenant(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    chantier = _ensure_keys(chantier)
    idx = len(chantier['intervenants'])
    iv = {
        'id':          str(uuid.uuid4()),
        'nom':         d.get('nom', ''),
        'entreprise':  d.get('entreprise', ''),
        'role':        d.get('role', ''),
        'specialite':  d.get('specialite', ''),
        'tel':         d.get('tel', ''),
        'email':       d.get('email', ''),
        'date_debut':  d.get('date_debut', ''),
        'date_fin':    d.get('date_fin', ''),
        'color':       INTERVENANT_COLORS[idx % len(INTERVENANT_COLORS)],
    }
    chantier['intervenants'].append(iv)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'intervenant': iv})

@chantier_bp.route('/api/<int:prospect_id>/intervenant/<iid>', methods=['PATCH', 'DELETE'])
def update_intervenant(prospect_id: int, iid: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier = _ensure_keys(chantier)
    if request.method == 'DELETE':
        chantier['intervenants'] = [iv for iv in chantier['intervenants'] if iv['id'] != iid]
        # Also remove their presences
        chantier['presences'] = [p for p in chantier.get('presences', []) if p.get('intervenant_id') != iid]
        _save_chantier(prospect_id, chantier)
        return jsonify({'ok': True})
    d = request.get_json()
    for iv in chantier['intervenants']:
        if iv['id'] == iid:
            iv.update({k: v for k, v in d.items() if k not in ('id', 'color')})
            break
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})

@chantier_bp.route('/api/<int:prospect_id>/presence', methods=['POST'])
def add_presence(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    chantier = _ensure_keys(chantier)
    pr = {
        'id':             str(uuid.uuid4()),
        'intervenant_id': d.get('intervenant_id', ''),
        'date':           d.get('date', date.today().isoformat()),
        'nb_heures':      float(d.get('nb_heures', 8)),
        'phase_id':       d.get('phase_id', ''),
        'arret':          bool(d.get('arret', False)),
        'notes':          d.get('notes', ''),
    }
    chantier['presences'].append(pr)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'presence': pr})

@chantier_bp.route('/api/<int:prospect_id>/presence/<pid>', methods=['DELETE'])
def delete_presence(prospect_id: int, pid: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier['presences'] = [p for p in chantier.get('presences', []) if p['id'] != pid]
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})

# ── API : Planning ────────────────────────────────────────────────────────────
@chantier_bp.route('/api/<int:prospect_id>/planning', methods=['PATCH'])
def update_planning(prospect_id: int):
    """Met à jour les paramètres généraux du planning + notes."""
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier = _ensure_keys(chantier)
    pl = chantier.setdefault('planning', {})
    for key in ('methode', 'notes_planning'):
        if key in d:
            pl[key] = d[key]
    # Jours indisponibles: on remplace la liste complète
    if 'jours_indisponibles' in d:
        pl['jours_indisponibles'] = d['jours_indisponibles']
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'planning': pl})

@chantier_bp.route('/api/<int:prospect_id>/planning/jalon', methods=['POST'])
def add_jalon(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    chantier = _ensure_keys(chantier)
    JALON_COLORS = {'GO': '#00b894', 'livraison': '#0984e3', 'reception': '#a29bfe',
                    'paiement': '#fdcb6e', 'audit': '#e17055', 'general': '#636e72'}
    jtype = d.get('type', 'general')
    jalon = {
        'id':           str(uuid.uuid4())[:8],
        'label':        d.get('label', ''),
        'date_prevue':  d.get('date_prevue', ''),
        'date_reelle':  d.get('date_reelle', ''),
        'type':         jtype,
        'couleur':      d.get('couleur', JALON_COLORS.get(jtype, '#636e72')),
        'notes':        d.get('notes', ''),
        'created_at':   datetime.now().isoformat(),
    }
    chantier['planning'].setdefault('jalons', []).append(jalon)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'jalon': jalon})

@chantier_bp.route('/api/<int:prospect_id>/planning/jalon/<jid>', methods=['PATCH', 'DELETE'])
def update_jalon(prospect_id: int, jid: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier = _ensure_keys(chantier)
    jalons = chantier['planning'].setdefault('jalons', [])
    if request.method == 'DELETE':
        chantier['planning']['jalons'] = [j for j in jalons if j['id'] != jid]
        _save_chantier(prospect_id, chantier)
        return jsonify({'ok': True})
    d = request.get_json()
    for j in jalons:
        if j['id'] == jid:
            j.update({k: v for k, v in d.items() if k not in ('id',)})
            break
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True})

@chantier_bp.route('/api/<int:prospect_id>/planning/contrainte', methods=['POST'])
def add_contrainte(prospect_id: int):
    d = request.get_json()
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        chantier = _init_chantier(prospect_id)
    chantier = _ensure_keys(chantier)
    ct = {
        'id':               str(uuid.uuid4())[:8],
        'phase_id':         d.get('phase_id', ''),
        'type':             d.get('type', 'externe'),   # externe | administrative | météo | technique
        'description':      d.get('description', ''),
        'date_contrainte':  d.get('date_contrainte', ''),
        'impact_jours':     int(d.get('impact_jours', 0)),
        'created_at':       datetime.now().isoformat(),
    }
    chantier['planning'].setdefault('contraintes', []).append(ct)
    _save_chantier(prospect_id, chantier)
    return jsonify({'ok': True, 'contrainte': ct})

@chantier_bp.route('/api/<int:prospect_id>/planning/contrainte/<cid>', methods=['DELETE'])
def delete_contrainte(prospect_id: int, cid: str):
    chantier = _load_prospect_chantier(prospect_id)
    if not chantier:
        return jsonify({'ok': False}), 404
    chantier = _ensure_keys(chantier)
    chantier['planning']['contraintes'] = [c for c in chantier['planning'].get('contraintes', []) if c['id'] != cid]
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
