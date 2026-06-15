"""
Routes CRM pour HeliaPV - Adaptées pour Railway avec PostgreSQL
Toutes les connexions SQLite ont été converties pour utiliser database_adapter
Multi-tenant: chaque utilisateur ne voit que ses propres prospects/projets (admin voit tout)
"""

from flask import render_template, jsonify, request, send_file, session as flask_session, redirect
from datetime import datetime
from database_adapter import execute_query, get_db_connection
import json
import os
import io
import zipfile
import threading

# Workers autonomes (process unique, 1 worker gunicorn) : verrou + état partagés
_FRANCE_LOCK = threading.Lock()
_FRANCE_STATE = {'running': False}
_OP_STATE = {'running': False}
_GEO_STATE = {'running': False}
_GEO2_STATE = {'running': False}

# Régions (code INSEE) → départements, pour étendre un droit "région" en
# départements pré-chargeables. Métropole uniquement (le gisement Enedis ne
# couvre pas Corse/DOM = EDF-SEI).
REGION_DEPTS = {
    '11': ['75', '77', '78', '91', '92', '93', '94', '95'],                          # Île-de-France
    '24': ['18', '28', '36', '37', '41', '45'],                                      # Centre-Val de Loire
    '27': ['21', '25', '39', '58', '70', '71', '89', '90'],                          # Bourgogne-Franche-Comté
    '28': ['14', '27', '50', '61', '76'],                                            # Normandie
    '32': ['02', '59', '60', '62', '80'],                                            # Hauts-de-France
    '44': ['08', '10', '51', '52', '54', '55', '57', '67', '68', '88'],              # Grand Est
    '52': ['44', '49', '53', '72', '85'],                                            # Pays de la Loire
    '53': ['22', '29', '35', '56'],                                                  # Bretagne
    '75': ['16', '17', '19', '23', '24', '33', '40', '47', '64', '79', '86', '87'],  # Nouvelle-Aquitaine
    '76': ['09', '11', '12', '30', '31', '32', '34', '46', '48', '65', '66', '81', '82'],  # Occitanie
    '84': ['01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'],  # Auvergne-Rhône-Alpes
    '93': ['04', '05', '06', '13', '83', '84'],                                      # Provence-Alpes-Côte d'Azur
    '94': ['2A', '2B'],                                                              # Corse
}
REGION_NOMS = {
    '11': 'Île-de-France', '24': 'Centre-Val de Loire', '27': 'Bourgogne-Franche-Comté',
    '28': 'Normandie', '32': 'Hauts-de-France', '44': 'Grand Est', '52': 'Pays de la Loire',
    '53': 'Bretagne', '75': 'Nouvelle-Aquitaine', '76': 'Occitanie',
    '84': 'Auvergne-Rhône-Alpes', '93': "Provence-Alpes-Côte d'Azur", '94': 'Corse',
}

DEPT_NOMS = {
    '01':'Ain','02':'Aisne','03':'Allier','04':'Alpes-de-Haute-Provence','05':'Hautes-Alpes',
    '06':'Alpes-Maritimes','07':'Ardèche','08':'Ardennes','09':'Ariège','10':'Aube','11':'Aude',
    '12':'Aveyron','13':'Bouches-du-Rhône','14':'Calvados','15':'Cantal','16':'Charente',
    '17':'Charente-Maritime','18':'Cher','19':'Corrèze','2A':'Corse-du-Sud','2B':'Haute-Corse',
    '21':"Côte-d'Or",'22':"Côtes-d'Armor",'23':'Creuse','24':'Dordogne','25':'Doubs','26':'Drôme',
    '27':'Eure','28':'Eure-et-Loir','29':'Finistère','30':'Gard','31':'Haute-Garonne','32':'Gers',
    '33':'Gironde','34':'Hérault','35':'Ille-et-Vilaine','36':'Indre','37':'Indre-et-Loire',
    '38':'Isère','39':'Jura','40':'Landes','41':'Loir-et-Cher','42':'Loire','43':'Haute-Loire',
    '44':'Loire-Atlantique','45':'Loiret','46':'Lot','47':'Lot-et-Garonne','48':'Lozère',
    '49':'Maine-et-Loire','50':'Manche','51':'Marne','52':'Haute-Marne','53':'Mayenne',
    '54':'Meurthe-et-Moselle','55':'Meuse','56':'Morbihan','57':'Moselle','58':'Nièvre','59':'Nord',
    '60':'Oise','61':'Orne','62':'Pas-de-Calais','63':'Puy-de-Dôme','64':'Pyrénées-Atlantiques',
    '65':'Hautes-Pyrénées','66':'Pyrénées-Orientales','67':'Bas-Rhin','68':'Haut-Rhin','69':'Rhône',
    '70':'Haute-Saône','71':'Saône-et-Loire','72':'Sarthe','73':'Savoie','74':'Haute-Savoie',
    '75':'Paris','76':'Seine-Maritime','77':'Seine-et-Marne','78':'Yvelines','79':'Deux-Sèvres',
    '80':'Somme','81':'Tarn','82':'Tarn-et-Garonne','83':'Var','84':'Vaucluse','85':'Vendée',
    '86':'Vienne','87':'Haute-Vienne','88':'Vosges','89':'Yonne','90':'Territoire de Belfort',
    '91':'Essonne','92':'Hauts-de-Seine','93':'Seine-Saint-Denis','94':'Val-de-Marne','95':"Val-d'Oise",
}
NAF_LABELS = {
    '08':'Carrières/extraction','10':'Agroalimentaire','11':'Boissons','13':'Textile','14':'Habillement',
    '15':'Cuir/chaussure','16':'Bois','17':'Papier/carton','18':'Imprimerie','19':'Raffinage','20':'Chimie',
    '21':'Pharmacie','22':'Plastique/caoutchouc','23':'Verre/ciment/minéraux','24':'Métallurgie',
    '25':'Produits métalliques','26':'Électronique','27':'Équip. électriques','28':'Machines','29':'Automobile',
    '30':'Autres transports','31':'Meubles','32':'Autres manuf.','33':'Réparation machines','35':'Énergie',
    '36':'Eau','38':'Déchets',
}

# Offre SaaS prospection industrielle (abonnement mensuel). Montants en centimes.
INDUSTRIEL_PLANS = {
    'solo': {'amount': 14900, 'territory': 'dept', 'label': 'Solo',
             'name': 'HeliaPV Industriel — Solo',
             'desc': '1 département · prospects industriels pré-chargés (opérateur, conso, autoconso)'},
    'pro':  {'amount': 49000, 'territory': 'region', 'label': 'Pro',
             'name': 'HeliaPV Industriel — Pro',
             'desc': '1 région entière · + calepinage 3D'},
}


def _slim_json_value(v, key=None):
    """Allège récursivement un data_json pour la LISTE (vignettes) : retire les
    géants (images base64, tableaux 8760h, nuages LiDAR, modules) tout en gardant
    la structure et les métadonnées (totaux, kpis, nb de zones). Le data_json
    COMPLET reste en base et est rechargé à l'ouverture d'un prospect."""
    if isinstance(v, str):
        if len(v) > 1500:  # base64 d'image, gros blob -> on ne garde que la présence
            return True if (key and 'screenshot' in key.lower()) else ""
        return v
    if isinstance(v, list):
        # 8760h, modules/points, FeatureCollections (parcelles/toitures/rpg…) -> vidées.
        # Les listes utiles en vignette (postes BT/HTA, zones de calepinage) sont courtes.
        return [_slim_json_value(x) for x in v] if len(v) <= 40 else []
    if isinstance(v, dict):
        # 'features' (FeatureCollection) : on vide les gros tableaux de features.
        return {k: ([] if (k == 'features' and isinstance(val, list) and len(val) > 40)
                    else _slim_json_value(val, k)) for k, val in v.items()}
    return v


def slim_data_json(dj):
    """Retourne une version allégée (string JSON) du data_json d'un prospect."""
    if not dj:
        return dj
    if isinstance(dj, str):
        try:
            dj = json.loads(dj)
        except Exception:
            return dj if len(dj) <= 4000 else "{}"
    if not isinstance(dj, dict):
        return "{}"
    return json.dumps(_slim_json_value(dj), ensure_ascii=False)
from declaration_prealable_generator import generate_declaration_prealable_complete
from plan_masse_generator import generate_plan_masse
from plan_masse_simple import generate_plan_masse_simple

# ============================================================================
# HELPER FUNCTIONS - AUTH & MULTI-TENANT
# ============================================================================

def get_current_crm_user():
    """
    Récupère l'utilisateur courant pour l'isolation des données CRM.
    Retourne (user_id, is_admin) ou (None, False) si non connecté.

    Admin override : si l'utilisateur reel est admin et que la session
    contient 'admin_view_as_user_id', on renvoie cet user_id avec
    is_admin=False (pour que user_filter_clause filtre bien sur ce user
    et que l'admin voie EXACTEMENT ce que voit ce user).
    """
    session_token = flask_session.get('session_token') or request.cookies.get('session_token')
    if not session_token:
        return None, False

    try:
        from auth_database import get_auth_db
        conn = get_auth_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.id, u.is_admin
            FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''', (session_token,))
        result = cursor.fetchone()
        conn.close()
        if result:
            real_user_id, is_admin = result[0], bool(result[1])
            # Admin "view as" : si l'admin a active une vue cible, on retourne
            # cet user comme s'il etait connecte (pas d'admin bypass).
            view_as = flask_session.get('admin_view_as_user_id')
            if is_admin and view_as:
                try:
                    return int(view_as), False
                except (TypeError, ValueError):
                    pass
            return real_user_id, is_admin
        return None, False
    except Exception as e:
        print(f"⚠️ [CRM AUTH] Erreur récupération utilisateur: {e}")
        return None, False

def verify_prospect_ownership(prospect_id, user_id, is_admin):
    """Vérifie qu'un prospect appartient à l'utilisateur courant"""
    if is_admin:
        return True
    result = execute_query(
        'SELECT user_id FROM agriweb_prospects WHERE id = %s',
        (prospect_id,), fetch_one=True
    )
    return result and str(result.get('user_id')) == str(user_id)

def verify_project_ownership(project_id, user_id, is_admin):
    """Vérifie qu'un projet appartient à l'utilisateur courant"""
    if is_admin:
        return True
    result = execute_query(
        'SELECT user_id FROM project_fiches WHERE id = %s',
        (project_id,), fetch_one=True
    )
    return result and str(result.get('user_id')) == str(user_id)

def user_filter_clause(user_id, is_admin, table_alias=''):
    """
    Retourne (clause_sql, params) pour filtrer par user_id.
    Admin: pas de filtre. User: WHERE user_id = %s.
    table_alias: ex 'ap.' pour 'ap.user_id'
    """
    prefix = f"{table_alias}." if table_alias else ''
    if is_admin:
        return '', ()
    return f' AND {prefix}user_id = %s', (str(user_id),)


def require_prospect_owner(f):
    """Décorateur : exige une session valide + la propriété du prospect (param prospect_id)."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401
        if not verify_prospect_ownership(kwargs.get('prospect_id'), user_id, is_admin):
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
        return f(*args, **kwargs)
    return wrapper


def require_project_owner(f):
    """Décorateur : exige une session valide + la propriété du projet (param project_id)."""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401
        if not verify_project_ownership(kwargs.get('project_id'), user_id, is_admin):
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
        return f(*args, **kwargs)
    return wrapper

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def auto_create_project_for_prospect(prospect_id, commune=None, adresse=None, user_id=None):
    """
    Crée automatiquement une fiche projet et ses étapes pour un nouveau prospect
    Cette fonction est appelée automatiquement à chaque création de prospect
    L'étape 1 (Rapport) est marquée comme terminée car l'export vient d'un rapport
    """
    try:
        print(f"🆕 [AUTO PROJECT] Création automatique du projet pour prospect {prospect_id}")
        
        # Récupérer data_json du prospect pour le copier dans le projet
        prospect_data = execute_query(
            'SELECT data_json FROM agriweb_prospects WHERE id = %s',
            (prospect_id,), fetch_one=True
        )
        prospect_data_json = (prospect_data.get('data_json') or '{}') if prospect_data else '{}'
        
        # Créer la fiche projet
        result = execute_query('''
            INSERT INTO project_fiches (
                prospect_id, nom_projet, commune, adresse_projet, 
                statut_projet, data_json, user_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            prospect_id,
            f"Projet {commune or adresse or prospect_id}",
            commune,
            adresse,
            'etude',
            prospect_data_json,
            str(user_id) if user_id is not None else None
        ), fetch_one=True)
        
        if result:
            project_id = result['id']
            print(f"✅ [AUTO PROJECT] Fiche projet {project_id} créée")
            
            # Créer les 12 étapes du workflow
            # L'étape 1 (Rapport) est marquée comme terminée car l'export provient d'un rapport
            etapes_autoconso = [
                ('Rapport de recherche HeliaPV', 1),
                ('Visite technique', 2),
                ('Calepinage', 3),
                ('Plan de masse', 4),
                ('Étude d\'autoconsommation', 5),
                ('Devis commercial', 6),
                ('Signature & Facture', 7),
                ('Déclaration Préalable de Travaux (DP)', 8),
                ('Déclaration de Raccordement (DDR)', 9),
                ('Installation & DOE', 10),
                ('Consuel', 11),
                ('Mise en service & Maintenance', 12)
            ]
            
            for nom_etape, ordre in etapes_autoconso:
                statut = 'termine' if ordre == 1 else 'a_faire'
                execute_query('''
                    INSERT INTO project_etapes (
                        project_id, nom_etape, ordre, statut,
                        date_debut_prevue, date_fin_prevue
                    ) VALUES (%s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days')
                ''', (project_id, nom_etape, ordre, statut))
            
            print(f"✅ [AUTO PROJECT] 12 étapes créées pour projet {project_id} (étape 1 Rapport = terminée)")
            return project_id
        else:
            print(f"❌ [AUTO PROJECT] Échec de création du projet pour prospect {prospect_id}")
            return None
            
    except Exception as e:
        print(f"❌ [AUTO PROJECT] Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None

def clean_value(val):
    """Convertit les chaînes vides en None pour PostgreSQL"""
    return None if val == "" or val is None else val

def clean_numeric_value(val):
    """
    Extrait la valeur numérique d'une chaîne en retirant les unités et formatage
    Exemples: '2171 m²' -> 2171, '145.5 m' -> 145.5, None -> None
    """
    if val is None or val == "":
        return None
    
    # Si c'est déjà un nombre
    if isinstance(val, (int, float)):
        return val
    
    # Si c'est une chaîne, extraire les chiffres
    if isinstance(val, str):
        # Retirer tous les caractères non numériques sauf le point et la virgule
        import re
        # Remplacer les virgules par des points pour les décimales
        cleaned = val.replace(',', '.')
        # Extraire le nombre (chiffres et un point décimal)
        match = re.search(r'[-+]?\d*\.?\d+', cleaned)
        if match:
            try:
                return float(match.group()) if '.' in match.group() else int(match.group())
            except ValueError:
                return None
    
    return None

def _count_mairies_campagne():
    """Nombre de mairies de la campagne email (table recipients, pipeline distinct
    des projets CRM). Total des destinataires analysés. 0 si la table n'existe pas."""
    try:
        r = execute_query("SELECT COUNT(DISTINCT nom_commune) AS n FROM recipients", fetch_one=True)
        return int((dict(r) if r else {}).get('n') or 0)
    except Exception:
        return 0

# ============================================================================
# ROUTES PAGES - INTERFACE CRM
# ============================================================================

def register_crm_routes(app):
    """Enregistre toutes les routes CRM dans l'application Flask"""
    
    @app.route('/crm')
    def crm_dashboard():
        """Page de lancement du CRM HeliaPV - Version web"""
        user_id, is_admin = get_current_crm_user()
        # Mode "vue admin comme utilisateur" : passe le contexte au template
        view_as_user_email = flask_session.get('admin_view_as_user_email')
        view_as_user_id = flask_session.get('admin_view_as_user_id')
        return render_template(
            'crm_web.html',
            is_admin=is_admin,
            view_as_user_email=view_as_user_email,
            view_as_user_id=view_as_user_id,
        )

    @app.route('/crm/stats')
    def crm_stats_page():
        """Page de statistiques et KPI du CRM"""
        user_id, is_admin = get_current_crm_user()
        return render_template('crm_dashboard.html')

    @app.route('/crm/desktop')
    def crm_desktop():
        """Page de lancement du CRM HeliaPV - Version desktop (Tkinter)"""
        return render_template('crm_redirect.html')

    @app.route('/crm/calendrier')
    def crm_calendrier():
        """Interface calendrier des rendez-vous"""
        user_id, is_admin = get_current_crm_user()
        return render_template('crm_calendrier.html', is_admin=is_admin)

    # ============================================================================
    # ROUTES API - STATISTIQUES
    # ============================================================================

    @app.route('/api/crm/stats')
    def crm_stats():
        """Statistiques CRM pour la page d'accueil"""
        try:
            user_id, is_admin = get_current_crm_user()
            filter_clause, filter_params = user_filter_clause(user_id, is_admin)

            stats = execute_query(f'''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveau,
                    COUNT(CASE WHEN statut = 'contacte' THEN 1 END) as contacte,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifie,
                    COUNT(CASE WHEN statut = 'perdu' THEN 1 END) as perdu,
                    COUNT(CASE WHEN type = 'parking' THEN 1 END) as parkings,
                    COUNT(CASE WHEN type = 'toiture' THEN 1 END) as toitures,
                    COUNT(CASE WHEN type = 'friche' THEN 1 END) as friches,
                    COUNT(CASE WHEN type = 'parcelle_rpg' THEN 1 END) as rpg,
                    COUNT(CASE WHEN type = 'industriel' THEN 1 END) as industriels,
                    COUNT(CASE WHEN type = 'mairie' THEN 1 END) as mairies,
                    COUNT(proprietaire_siren) as enrichis
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)

            if not stats:
                return jsonify({
                    'success': True,
                    'stats': {'total': 0, 'nouveau': 0, 'contacte': 0, 'qualifie': 0, 'perdu': 0, 'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0, 'industriels': 0, 'mairies': 0, 'enrichis': 0}
                })

            stats = dict(stats)
            stats['mairies'] = _count_mairies_campagne()  # campagne email (pipeline distinct)
            return jsonify({'success': True, 'stats': stats})
            
        except Exception as e:
            print(f"❌ [CRM STATS] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'stats': {'total': 0, 'nouveau': 0, 'contacte': 0, 'qualifie': 0, 'perdu': 0, 'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0}
            })

    @app.route('/api/crm/mairies-diagnostic', methods=['GET'])
    def mairies_diagnostic():
        """Diagnostic LECTURE SEULE des doublons de la campagne mairies (table recipients)."""
        user_id, is_admin = get_current_crm_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin requis'}), 403
        out = {}
        try:
            g = execute_query(
                "SELECT COUNT(*) AS lignes, COUNT(DISTINCT nom_commune) AS communes, "
                "COUNT(DISTINCT code_insee) AS insee, COUNT(DISTINCT email) AS emails FROM recipients",
                fetch_one=True)
            out['global'] = dict(g) if g else {}
            camps = execute_query(
                "SELECT c.id, c.name, c.total AS total_declare, c.status, "
                "COUNT(r.id) AS lignes, COUNT(DISTINCT r.nom_commune) AS communes "
                "FROM campaigns c LEFT JOIN recipients r ON r.campaign_id = c.id "
                "GROUP BY c.id, c.name, c.total, c.status ORDER BY lignes DESC", fetch_all=True)
            out['campagnes'] = [dict(c) for c in (camps or [])]
            dist = execute_query(
                "SELECT cnt AS occurrences, COUNT(*) AS nb_communes FROM "
                "(SELECT nom_commune, COUNT(*) AS cnt FROM recipients GROUP BY nom_commune) t "
                "GROUP BY cnt ORDER BY cnt DESC LIMIT 25", fetch_all=True)
            out['distribution_doublons'] = [dict(d) for d in (dist or [])]
            top = execute_query(
                "SELECT nom_commune, COUNT(*) AS cnt, COUNT(DISTINCT campaign_id) AS campagnes "
                "FROM recipients GROUP BY nom_commune ORDER BY cnt DESC LIMIT 12", fetch_all=True)
            out['top_doublons'] = [dict(t) for t in (top or [])]
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': True, 'diagnostic': out})

    @app.route('/api/crm/dashboard/stats')
    def get_dashboard_stats():
        """Récupère toutes les statistiques pour le dashboard CRM KPI"""
        try:
            user_id, is_admin = get_current_crm_user()
            filter_clause, filter_params = user_filter_clause(user_id, is_admin)

            print("\n" + "="*70)
            print("🔄 [DASHBOARD KPI] Récupération des statistiques...")
            
            # === KPIs GÉNÉRAUX ===
            kpis = execute_query(f'''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveaux,
                    COUNT(CASE WHEN statut = 'contacte' THEN 1 END) as contactes,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies,
                    COUNT(CASE WHEN statut = 'perdu' THEN 1 END) as perdus,
                    COUNT(CASE WHEN date_creation >= NOW() - INTERVAL '30 days' THEN 1 END) as nouveaux_mois
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)
            
            print(f"📊 [DASHBOARD KPI] KPIs bruts: {kpis}")
            
            # Propositions — utilise project_fiches (peuplée automatiquement à chaque export CRM)
            # Combine avec prospect_proposals si elle existe
            try:
                pf_row = execute_query(f'''
                    SELECT COUNT(*) as nb_proposals
                    FROM project_fiches
                    WHERE 1=1{filter_clause}
                ''', filter_params if filter_params else None, fetch_one=True)
                nb_pf = pf_row['nb_proposals'] if pf_row else 0
            except Exception:
                nb_pf = 0
            try:
                pp_row = execute_query('''
                    SELECT 
                        COUNT(*) as nb_proposals,
                        COALESCE(SUM(CAST(investissement_total AS NUMERIC)), 0) as total_value
                    FROM prospect_proposals
                ''', fetch_one=True)
                proposals = pp_row if pp_row else {'nb_proposals': 0, 'total_value': 0}
                # Si prospect_proposals est vide, utiliser project_fiches
                if proposals['nb_proposals'] == 0 and nb_pf > 0:
                    proposals = {'nb_proposals': nb_pf, 'total_value': 0}
            except Exception:
                proposals = {'nb_proposals': nb_pf, 'total_value': 0}
            
            print(f"💰 [DASHBOARD KPI] Propositions: {proposals}")
            
            kpis['nb_proposals'] = proposals['nb_proposals']
            kpis['total_proposals_value'] = proposals['total_value']
            
            # === CHARTS ===
            # Par type
            by_type_rows = execute_query(f'''
                SELECT type, COUNT(*) as count
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
                GROUP BY type
            ''', filter_params if filter_params else None, fetch_all=True)
            by_type = {row['type']: row['count'] for row in by_type_rows}
            
            # Par statut
            by_statut_rows = execute_query(f'''
                SELECT statut, COUNT(*) as count
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
                GROUP BY statut
            ''', filter_params if filter_params else None, fetch_all=True)
            by_statut = {row['statut']: row['count'] for row in by_statut_rows}
            
            # Timeline (30 derniers jours)
            timeline_data = execute_query(f'''
                SELECT 
                    DATE(date_creation) as date,
                    COUNT(*) as count,
                    statut
                FROM agriweb_prospects
                WHERE date_creation >= NOW() - INTERVAL '30 days'{filter_clause}
                GROUP BY DATE(date_creation), statut
                ORDER BY date
            ''', filter_params if filter_params else None, fetch_all=True)
            
            # Construire timeline
            from collections import defaultdict
            timeline = defaultdict(lambda: {'nouveaux': 0, 'contactes': 0, 'qualifies': 0})
            for row in timeline_data:
                date_str = row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date'])
                if row['statut'] == 'nouveau':
                    timeline[date_str]['nouveaux'] += row['count']
                elif row['statut'] == 'contacte':
                    timeline[date_str]['contactes'] += row['count']
                elif row['statut'] == 'qualifie':
                    timeline[date_str]['qualifies'] += row['count']
            
            sorted_dates = sorted(timeline.keys())
            timeline_formatted = {
                'labels': sorted_dates,
                'nouveaux': [timeline[d]['nouveaux'] for d in sorted_dates],
                'contactes': [timeline[d]['contactes'] for d in sorted_dates],
                'qualifies': [timeline[d]['qualifies'] for d in sorted_dates]
            }
            
            # === CONVERSION ===
            nb_proposals_conversion = proposals['nb_proposals']
            
            # Délais moyens (PostgreSQL utilise EXTRACT(EPOCH) pour les intervalles)
            avg_contact_row = execute_query(f'''
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (date_modification - date_creation))/86400) as avg_delay
                FROM agriweb_prospects
                WHERE statut != 'nouveau'{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)
            avg_contact = avg_contact_row['avg_delay'] or 0 if avg_contact_row else 0
            
            avg_qualification_row = execute_query(f'''
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (date_modification - date_creation))/86400) as avg_delay
                FROM agriweb_prospects
                WHERE statut = 'qualifie'{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)
            avg_qualification = avg_qualification_row['avg_delay'] or 0 if avg_qualification_row else 0
            
            # Conversion par type
            conversion_type_rows = execute_query(f'''
                SELECT 
                    type,
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
                GROUP BY type
            ''', filter_params if filter_params else None, fetch_all=True)
            conversion_by_type = {}
            for row in conversion_type_rows:
                total = row['total']
                qualifies = row['qualifies']
                conversion_by_type[row['type']] = (qualifies / total * 100) if total > 0 else 0
            
            conversion_data = {
                'total': kpis['total'],
                'nouveaux': kpis['nouveaux'],
                'contactes': kpis['contactes'],
                'qualifies': kpis['qualifies'],
                'proposals': nb_proposals_conversion,
                'avg_contact_delay': round(float(avg_contact), 1),
                'avg_qualification_delay': round(float(avg_qualification), 1),
                'by_type': conversion_by_type
            }
            
            # === UTILISATEURS ===
            # Note: Pour l'instant, pas de tracking utilisateur dans agriweb_prospects
            # On simule avec des données agrégées
            users_data = [{
                'nom': 'Système',
                'email': 'system@agriweb.com',
                'total': kpis['total'],
                'contactes': kpis['contactes'],
                'qualifies': kpis['qualifies'],
                'proposals': kpis['nb_proposals'],
                'total_actions': kpis['total']
            }]
            
            # === PERFORMANCE ===
            performance_data = {
                'best_conversion_rate': (kpis['qualifies'] / kpis['total'] * 100) if kpis['total'] > 0 else 0,
                'best_conversion_user': 'Système',
                'fastest_contact_delay': round(float(avg_contact), 1),
                'fastest_contact_user': 'Système',
                'most_productive_count': kpis['total'],
                'most_productive_user': 'Système'
            }
            
            # === DÉPARTEMENTS ===
            departments_data = execute_query(f'''
                SELECT 
                    departement,
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies
                FROM agriweb_prospects
                WHERE departement IS NOT NULL{filter_clause}
                GROUP BY departement
                ORDER BY total DESC
                LIMIT 10
            ''', filter_params if filter_params else None, fetch_all=True)

            print(f"✅ [DASHBOARD KPI] Données complètes - Total prospects: {kpis['total']}")
            print(f"📈 [DASHBOARD KPI] Charts types: {len(by_type)}, statuts: {len(by_statut)}")
            print(f"🗺️ [DASHBOARD KPI] Départements: {len(departments_data)}")
            print("="*70 + "\n")
            
            return jsonify({
                'success': True,
                'kpis': kpis,
                'charts': {
                    'by_type': by_type,
                    'by_statut': by_statut,
                    'timeline': timeline_formatted
                },
                'conversion': conversion_data,
                'users': users_data,
                'performance': performance_data,
                'departments': departments_data
            })
            
        except Exception as e:
            print(f"❌ [DASHBOARD] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/launch', methods=['POST'])
    def crm_launch():
        """Lance l'application CRM HeliaPV (désactivé sur Railway)"""
        return jsonify({
            'success': False,
            'message': 'Fonctionnalité disponible uniquement en version desktop'
        }), 400

    # ============================================================================
    # ROUTES API - EQUIPEMENTS PV
    # ============================================================================

    @app.route('/api/equipements/modules')
    def get_modules_database():
        """API - Base de données modules photovoltaïques"""
        try:
            from equipements_database import MODULES_PV_DATABASE
            return jsonify({
                'success': True,
                'count': len(MODULES_PV_DATABASE),
                'modules': MODULES_PV_DATABASE
            })
        except Exception as e:
            print(f"❌ Erreur chargement base modules: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/equipements/onduleurs')
    def get_onduleurs_database():
        """API - Base de données onduleurs"""
        try:
            from equipements_database import ONDULEURS_DATABASE
            return jsonify({
                'success': True,
                'count': len(ONDULEURS_DATABASE),
                'onduleurs': ONDULEURS_DATABASE
            })
        except Exception as e:
            print(f"❌ Erreur chargement base onduleurs: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/equipements/module/<reference>')
    def get_module_details(reference):
        """API - Détails d'un module spécifique"""
        try:
            from equipements_database import MODULES_PV_DATABASE
            if reference in MODULES_PV_DATABASE:
                return jsonify({
                    'success': True,
                    'module': MODULES_PV_DATABASE[reference]
                })
            return jsonify({'success': False, 'error': 'Module non trouvé'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/equipements/onduleur/<reference>')
    def get_onduleur_details(reference):
        """API - Détails d'un onduleur spécifique"""
        try:
            from equipements_database import ONDULEURS_DATABASE
            if reference in ONDULEURS_DATABASE:
                return jsonify({
                    'success': True,
                    'onduleur': ONDULEURS_DATABASE[reference]
                })
            return jsonify({'success': False, 'error': 'Onduleur non trouvé'}), 404
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES API - EXPORT PROSPECTS
    # ============================================================================

    @app.route('/api/crm/export', methods=['POST'])
    def crm_export():
        """Exporte les éléments sélectionnés vers le CRM"""
        import time
        start_time = time.time()
        
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401

            print(f"\n{'='*80}")
            print(f"🚀 [CRM EXPORT] === DÉBUT EXPORT CRM ===")
            print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            print(f"📦 [CRM EXPORT] Données reçues:")
            print(f"    - Parkings: {len(data.get('parkings', []))}")
            print(f"    - Toitures: {len(data.get('toitures', []))}")
            print(f"    - Friches: {len(data.get('friches', []))}")
            print(f"    - RPG: {len(data.get('rpg', []))}")
            
            total_items = len(data.get('parkings', [])) + len(data.get('toitures', [])) + len(data.get('friches', [])) + len(data.get('rpg', []))
            print(f"📊 [CRM EXPORT] Total à exporter: {total_items} éléments")
            
            # Debug: afficher la première toiture pour vérifier lat/lon
            if data.get('toitures') and len(data.get('toitures')) > 0:
                first_toiture = data['toitures'][0]
                print(f"🔍 [DEBUG] Première toiture:")
                print(f"    - lat: {first_toiture.get('lat')}")
                print(f"    - lon: {first_toiture.get('lon')}")
                print(f"    - surface_m2: {first_toiture.get('surface_m2')}")
                print(f"    - Toutes les clés: {list(first_toiture.keys())}")
            print(f"    - Friches: {len(data.get('friches', []))}")
            
            # Debug: Afficher la première toiture pour vérifier lat/lon
            if data.get('toitures') and len(data['toitures']) > 0:
                first_toiture = data['toitures'][0]
                print(f"🔍 [DEBUG] Première toiture:")
                print(f"    - lat: {first_toiture.get('lat')}")
                print(f"    - lon: {first_toiture.get('lon')}")
                print(f"    - surface_m2: {first_toiture.get('surface_m2')}")
                print(f"    - Toutes les clés: {list(first_toiture.keys())}")
            total_exported = 0
            details = {'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0}
            created_prospects = []  # pour l'enrichissement autoconso (bornee aux nouveaux)
            
            # Exporter les parkings
            for parking in data.get('parkings', []):
                poste_bt = parking.get('poste_bt_proche', {})
                poste_hta = parking.get('poste_hta_proche', {})
                
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_etat, poste_bt_lat, poste_bt_lon,
                        poste_bt_commune, poste_bt_code_commune, poste_bt_epci, poste_bt_code_epci,
                        poste_bt_departement, poste_bt_code_departement, poste_bt_region, poste_bt_code_region,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_etat, poste_hta_lat, poste_hta_lon,
                        poste_hta_commune, poste_hta_code_commune, poste_hta_epci, poste_hta_code_epci,
                        poste_hta_departement, poste_hta_code_departement, poste_hta_region, poste_hta_code_region,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial,
                        user_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'parking', parking.get('commune'), parking.get('departement'), parking.get('adresse'),
                    clean_value(parking.get('lat')), clean_value(parking.get('lon')), clean_value(parking.get('surface_m2')),
                    clean_value(parking.get('surface_m2', 0)) / 10000 if clean_value(parking.get('surface_m2')) else None,
                    json.dumps(parking.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')), poste_bt.get('etat'),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    poste_bt.get('commune'), poste_bt.get('code_commune'), poste_bt.get('epci'), poste_bt.get('code_epci'),
                    poste_bt.get('departement'), poste_bt.get('code_departement'), poste_bt.get('region'), poste_bt.get('code_region'),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')), poste_hta.get('etat'),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    poste_hta.get('commune'), poste_hta.get('code_commune'), poste_hta.get('epci'), poste_hta.get('code_epci'),
                    poste_hta.get('departement'), poste_hta.get('code_departement'), poste_hta.get('region'), poste_hta.get('code_region'),
                    parking.get('lien_streetview'), parking.get('lien_annuaire'), json.dumps(parking),
                    parking.get('amenity'), parking.get('shop'), parking.get('building'),
                    parking.get('landuse'), parking.get('office'), parking.get('industrial'),
                    str(user_id) if user_id is not None else None
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], parking.get('commune'), parking.get('adresse'), user_id=user_id)
                    created_prospects.append({'id': result['id'], 'commune': parking.get('commune'),
                                              'adresse': parking.get('adresse'), 'latitude': clean_value(parking.get('lat')), 'data_json': parking})

                total_exported += 1
                details['parkings'] += 1
            
            # Exporter les toitures
            for toiture in data.get('toitures', []):
                poste_bt = toiture.get('poste_bt_proche', {})
                poste_hta = toiture.get('poste_hta_proche', {})
                
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_etat, poste_bt_lat, poste_bt_lon,
                        poste_bt_commune, poste_bt_code_commune, poste_bt_epci, poste_bt_code_epci,
                        poste_bt_departement, poste_bt_code_departement, poste_bt_region, poste_bt_code_region,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_etat, poste_hta_lat, poste_hta_lon,
                        poste_hta_commune, poste_hta_code_commune, poste_hta_epci, poste_hta_code_epci,
                        poste_hta_departement, poste_hta_code_departement, poste_hta_region, poste_hta_code_region,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial,
                        user_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'toiture', toiture.get('commune'), toiture.get('departement'), toiture.get('adresse'),
                    clean_value(toiture.get('lat')), clean_value(toiture.get('lon')), clean_value(toiture.get('surface_m2')),
                    clean_value(toiture.get('surface_m2', 0)) / 10000 if clean_value(toiture.get('surface_m2')) else None,
                    json.dumps(toiture.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')), poste_bt.get('etat'),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    poste_bt.get('commune'), poste_bt.get('code_commune'), poste_bt.get('epci'), poste_bt.get('code_epci'),
                    poste_bt.get('departement'), poste_bt.get('code_departement'), poste_bt.get('region'), poste_bt.get('code_region'),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')), poste_hta.get('etat'),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    poste_hta.get('commune'), poste_hta.get('code_commune'), poste_hta.get('epci'), poste_hta.get('code_epci'),
                    poste_hta.get('departement'), poste_hta.get('code_departement'), poste_hta.get('region'), poste_hta.get('code_region'),
                    toiture.get('lien_streetview'), toiture.get('lien_annuaire'), json.dumps(toiture),
                    toiture.get('amenity'), toiture.get('shop'), toiture.get('building'),
                    toiture.get('landuse'), toiture.get('office'), toiture.get('industrial'),
                    str(user_id) if user_id is not None else None
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], toiture.get('commune'), toiture.get('adresse'), user_id=user_id)
                    created_prospects.append({'id': result['id'], 'commune': toiture.get('commune'),
                                              'adresse': toiture.get('adresse'), 'latitude': clean_value(toiture.get('lat')), 'data_json': toiture})

                total_exported += 1
                details['toitures'] += 1
            
            # Exporter les friches
            for friche in data.get('friches', []):
                poste_bt = friche.get('poste_bt_proche', {})
                poste_hta = friche.get('poste_hta_proche', {})
                
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_etat, poste_bt_lat, poste_bt_lon,
                        poste_bt_commune, poste_bt_code_commune, poste_bt_epci, poste_bt_code_epci,
                        poste_bt_departement, poste_bt_code_departement, poste_bt_region, poste_bt_code_region,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_etat, poste_hta_lat, poste_hta_lon,
                        poste_hta_commune, poste_hta_code_commune, poste_hta_epci, poste_hta_code_epci,
                        poste_hta_departement, poste_hta_code_departement, poste_hta_region, poste_hta_code_region,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial,
                        user_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'friche', friche.get('commune'), friche.get('departement'), friche.get('adresse'),
                    clean_value(friche.get('lat')), clean_value(friche.get('lon')), clean_value(friche.get('surface_m2')),
                    clean_value(friche.get('surface_m2', 0)) / 10000 if clean_value(friche.get('surface_m2')) else None,
                    json.dumps(friche.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')), poste_bt.get('etat'),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    poste_bt.get('commune'), poste_bt.get('code_commune'), poste_bt.get('epci'), poste_bt.get('code_epci'),
                    poste_bt.get('departement'), poste_bt.get('code_departement'), poste_bt.get('region'), poste_bt.get('code_region'),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')), poste_hta.get('etat'),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    poste_hta.get('commune'), poste_hta.get('code_commune'), poste_hta.get('epci'), poste_hta.get('code_epci'),
                    poste_hta.get('departement'), poste_hta.get('code_departement'), poste_hta.get('region'), poste_hta.get('code_region'),
                    friche.get('lien_streetview'), friche.get('lien_annuaire'), json.dumps(friche),
                    friche.get('amenity'), friche.get('shop'), friche.get('building'),
                    friche.get('landuse'), friche.get('office'), friche.get('industrial'),
                    str(user_id) if user_id is not None else None
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], friche.get('commune'), friche.get('adresse'), user_id=user_id)
                    created_prospects.append({'id': result['id'], 'commune': friche.get('commune'),
                                              'adresse': friche.get('adresse'), 'latitude': clean_value(friche.get('lat')), 'data_json': friche})

                total_exported += 1
                details['friches'] += 1
            
            # Exporter les parcelles RPG
            for rpg in data.get('rpg', []):
                poste_bt = rpg.get('poste_bt_proche', {})
                poste_hta = rpg.get('poste_hta_proche', {})
                
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_etat, poste_bt_lat, poste_bt_lon,
                        poste_bt_commune, poste_bt_code_commune, poste_bt_epci, poste_bt_code_epci,
                        poste_bt_departement, poste_bt_code_departement, poste_bt_region, poste_bt_code_region,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_etat, poste_hta_lat, poste_hta_lon,
                        poste_hta_commune, poste_hta_code_commune, poste_hta_epci, poste_hta_code_epci,
                        poste_hta_departement, poste_hta_code_departement, poste_hta_region, poste_hta_code_region,
                        data_json, user_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'parcelle_rpg', rpg.get('commune'), rpg.get('departement'), rpg.get('adresse'),
                    rpg.get('latitude'), rpg.get('longitude'),
                    rpg.get('surface', 0) * 10000 if rpg.get('surface') else None,
                    rpg.get('surface'), rpg.get('parcelle_cadastrale'),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')), poste_bt.get('etat'),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    poste_bt.get('commune'), poste_bt.get('code_commune'), poste_bt.get('epci'), poste_bt.get('code_epci'),
                    poste_bt.get('departement'), poste_bt.get('code_departement'), poste_bt.get('region'), poste_bt.get('code_region'),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')), poste_hta.get('etat'),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    poste_hta.get('commune'), poste_hta.get('code_commune'), poste_hta.get('epci'), poste_hta.get('code_epci'),
                    poste_hta.get('departement'), poste_hta.get('code_departement'), poste_hta.get('region'), poste_hta.get('code_region'),
                    json.dumps(rpg),
                    str(user_id) if user_id is not None else None
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], rpg.get('commune'), rpg.get('adresse'), user_id=user_id)
                    created_prospects.append({'id': result['id'], 'commune': rpg.get('commune'),
                                              'adresse': rpg.get('adresse'), 'latitude': rpg.get('latitude'), 'data_json': rpg})

                total_exported += 1
                details['rpg'] += 1
            
            print(f"✅ [CRM EXPORT] Export réussi: {total_exported} prospects ajoutés")

            # Enrichissement autoconso AUTOMATIQUE — borné aux prospects qui
            # viennent d'être créés (pas de rescan de toute la commune). Pour
            # chaque commune, 1 seul appel Enedis puis matching adresse -> conso
            # -> diagnostic. Non bloquant (un échec ne casse jamais l'export).
            try:
                from agriweb_hebergement_gratuit import get_enedis_records_raw
                by_commune = {}
                for _p in created_prospects:
                    if (_p.get('adresse') or '').strip() and (_p.get('commune') or '').strip():
                        by_commune.setdefault(_p['commune'], []).append(_p)
                enrichis_auto = 0
                for _commune, _plist in by_commune.items():
                    _ci = _resolve_code_insee(_plist[0], {})
                    if not _ci:
                        continue
                    _records = get_enedis_records_raw(_ci) or []
                    if not _records:
                        continue
                    for _p in _plist:
                        if _enrich_one_prospect(_p, _records, force=False).get('status') == 'enrichi':
                            enrichis_auto += 1
                if enrichis_auto:
                    print(f"☀️ [CRM EXPORT] {enrichis_auto} prospect(s) enrichi(s) autoconso automatiquement")
                    details['autoconso_enrichis'] = enrichis_auto
            except Exception as _e_enr:
                print(f"⚠️ [CRM EXPORT] enrichissement autoconso auto échoué: {_e_enr}")

            return jsonify({
                'success': True,
                'total_exported': total_exported,
                'details': details,
                'message': f'{total_exported} prospects ajoutés au CRM'
            })
            
        except Exception as e:
            print(f"❌ [CRM EXPORT] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES API - GESTION PROSPECTS
    # ============================================================================

    @app.route('/api/crm/prospects')
    def get_prospects():
        """Récupère tous les prospects pour l'interface web CRM"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            filter_clause, filter_params = user_filter_clause(user_id, is_admin)

            # Récupérer tous les prospects
            prospects = execute_query(f'''
                SELECT * FROM agriweb_prospects 
                WHERE 1=1{filter_clause}
                ORDER BY date_creation DESC
            ''', filter_params if filter_params else None, fetch_all=True)
            
            # Mapper contact_telephone -> contact_tel + ALLÉGER le data_json
            # (les vignettes n'ont besoin que du léger ; le calepinage/LiDAR/captures
            # restent en base et sont rechargés à l'ouverture d'un prospect).
            if prospects:
                for prospect in prospects:
                    if 'contact_telephone' in prospect:
                        prospect['contact_tel'] = prospect['contact_telephone']
                    if prospect.get('data_json'):
                        prospect['data_json'] = slim_data_json(prospect['data_json'])

            # Calculer les stats
            stats = execute_query(f'''
                SELECT
                    COUNT(*) as total,
                    COUNT(CASE WHEN type = 'parking' THEN 1 END) as parkings,
                    COUNT(CASE WHEN type = 'toiture' THEN 1 END) as toitures,
                    COUNT(CASE WHEN type = 'friche' THEN 1 END) as friches,
                    COUNT(CASE WHEN type = 'parcelle_rpg' THEN 1 END) as rpg,
                    COUNT(CASE WHEN type = 'industriel' THEN 1 END) as industriels,
                    COUNT(CASE WHEN type = 'mairie' THEN 1 END) as mairies,
                    COUNT(proprietaire_siren) as enrichis
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)

            # Mairies = campagne email (table recipients, pipeline distinct des projets CRM)
            stats = dict(stats) if stats else {'total': 0, 'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0, 'industriels': 0, 'mairies': 0, 'enrichis': 0}
            stats['mairies'] = _count_mairies_campagne()

            return jsonify({
                'success': True,
                'prospects': prospects if prospects else [],
                'stats': stats
            })
            
        except Exception as e:
            print(f"❌ [CRM GET] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>', methods=['GET'])
    def get_prospect(prospect_id):
        """Récupère les détails d'un prospect spécifique"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            prospect = execute_query(
                'SELECT * FROM agriweb_prospects WHERE id = %s',
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect:
                return jsonify({'success': False, 'error': 'Prospect non trouvé'}), 404
            
            # Parser data_json si nécessaire
            if prospect.get('data_json') and isinstance(prospect['data_json'], str):
                try:
                    prospect['data_json'] = json.loads(prospect['data_json'])
                except:
                    pass
            
            return jsonify({'success': True, 'prospect': prospect})
            
        except Exception as e:
            print(f"❌ [GET PROSPECT] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>', methods=['PUT'])
    def update_prospect(prospect_id):
        """Met à jour un prospect"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            
            # Construire la requête UPDATE dynamiquement
            fields = []
            values = []
            
            if 'statut' in data:
                fields.append('statut = %s')
                values.append(data['statut'])
            if 'priorite' in data:
                fields.append('priorite = %s')
                values.append(data['priorite'])
            if 'nom_prospect' in data:
                fields.append('nom_prospect = %s')
                values.append(data['nom_prospect'])
            if 'contact_nom' in data:
                fields.append('contact_nom = %s')
                values.append(data['contact_nom'])
            if 'contact_tel' in data:
                fields.append('contact_telephone = %s')
                values.append(data['contact_tel'])
            if 'contact_email' in data:
                fields.append('contact_email = %s')
                values.append(data['contact_email'])
            if 'dirigeant_nom' in data:
                fields.append('dirigeant_nom = %s')
                values.append(data['dirigeant_nom'])
            if 'siret' in data:
                fields.append('siret = %s')
                values.append(data['siret'])
            if 'dirigeant_email' in data:
                fields.append('dirigeant_email = %s')
                values.append(data['dirigeant_email'])
            if 'dirigeant_tel' in data:
                fields.append('dirigeant_tel = %s')
                values.append(data['dirigeant_tel'])
            if 'notes' in data:
                fields.append('notes = %s')
                values.append(data['notes'])
            
            fields.append('date_modification = %s')
            values.append(datetime.now().isoformat())
            
            values.append(prospect_id)
            
            query = f"UPDATE agriweb_prospects SET {', '.join(fields)} WHERE id = %s"
            execute_query(query, tuple(values))
            
            # Si le nom du contact a changé, mettre à jour le projet associé
            if 'contact_nom' in data:
                projet = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s',
                    (prospect_id,),
                    fetch_one=True
                )
                
                if projet:
                    execute_query('''
                        UPDATE project_fiches
                        SET nom_projet = %s, client_nom = %s
                        WHERE id = %s
                    ''', (f"Projet {data['contact_nom']}", data['contact_nom'], projet['id']))
            
            # Mise à jour email projet
            if 'contact_email' in data:
                projet = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s',
                    (prospect_id,),
                    fetch_one=True
                )
                if projet:
                    execute_query(
                        'UPDATE project_fiches SET client_email = %s WHERE id = %s',
                        (data['contact_email'], projet['id'])
                    )
            
            # Mise à jour téléphone projet
            if 'contact_tel' in data:
                projet = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s',
                    (prospect_id,),
                    fetch_one=True
                )
                if projet:
                    execute_query(
                        'UPDATE project_fiches SET client_telephone = %s WHERE id = %s',
                        (data['contact_tel'], projet['id'])
                    )
            
            return jsonify({
                'success': True,
                'message': 'Prospect mis à jour'
            })
            
        except Exception as e:
            print(f"❌ [CRM UPDATE] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/update-from-report', methods=['PUT'])
    def update_prospect_from_report(prospect_id):
        """Met à jour un prospect avec les données d'un rapport ponctuel"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            print(f"🔄 [CRM UPDATE FROM REPORT] Mise à jour prospect {prospect_id} avec données rapport")
            
            # Préparer les champs à mettre à jour
            update_fields = []
            params = []
            
            if 'lat' in data:
                update_fields.append('latitude = %s')
                params.append(data['lat'])
            
            if 'lon' in data:
                update_fields.append('longitude = %s')
                params.append(data['lon'])
            
            if 'commune' in data:
                update_fields.append('commune = %s')
                params.append(data['commune'])
            
            if 'adresse' in data and data['adresse']:
                update_fields.append('adresse = %s')
                params.append(data['adresse'])
            
            if 'parcelle_cadastrale' in data and data['parcelle_cadastrale']:
                # Ne pas écraser si la valeur contient '+N' (format tronqué d'analyse MAJIC)
                import re as _re
                if not _re.search(r'\+\d+$', str(data['parcelle_cadastrale']).strip()):
                    update_fields.append('parcelles_cadastrales = %s')
                    params.append(data['parcelle_cadastrale'])
            
            if 'surface_parcelle' in data:
                update_fields.append('surface_m2 = %s')
                params.append(clean_numeric_value(data['surface_parcelle']))
            
            if 'poste_bt_nom' in data:
                update_fields.append('poste_bt_nom = %s')
                params.append(data['poste_bt_nom'])
            
            if 'poste_bt_distance' in data:
                update_fields.append('poste_bt_distance_m = %s')
                params.append(clean_numeric_value(data['poste_bt_distance']))
            
            if 'poste_bt_lat' in data:
                update_fields.append('poste_bt_lat = %s')
                params.append(clean_value(data['poste_bt_lat']))
            
            if 'poste_bt_lon' in data:
                update_fields.append('poste_bt_lon = %s')
                params.append(clean_value(data['poste_bt_lon']))
            
            if 'poste_hta_nom' in data:
                update_fields.append('poste_hta_nom = %s')
                params.append(data['poste_hta_nom'])
            
            if 'poste_hta_distance' in data:
                update_fields.append('poste_hta_distance_m = %s')
                params.append(clean_numeric_value(data['poste_hta_distance']))
            
            if 'poste_hta_lat' in data:
                update_fields.append('poste_hta_lat = %s')
                params.append(clean_value(data['poste_hta_lat']))
            
            if 'poste_hta_lon' in data:
                update_fields.append('poste_hta_lon = %s')
                params.append(clean_value(data['poste_hta_lon']))
            
            if 'data_json' in data:
                # Récupérer le data_json existant pour le fusionner au lieu de l'écraser
                existing_data = execute_query(
                    "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                    (prospect_id,),
                    fetch_one=True
                )
                
                if existing_data and existing_data['data_json']:
                    try:
                        current_json = json.loads(existing_data['data_json'])
                    except:
                        current_json = {}
                else:
                    current_json = {}
                
                # Fusionner : garder carte_url et autres données existantes
                new_json = data['data_json']
                
                # Préserver carte_url si elle existe déjà
                if 'carte_url' in current_json and 'carte_url' not in new_json:
                    new_json['carte_url'] = current_json['carte_url']
                
                # Ajouter les nouvelles données du rapport
                if 'rapport' not in current_json:
                    current_json['rapport'] = new_json
                else:
                    # Mettre à jour le rapport existant
                    current_json['rapport'].update(new_json)
                
                update_fields.append('data_json = %s')
                params.append(json.dumps(current_json))
            
            # Ajouter la date de mise à jour
            update_fields.append('date_modification = NOW()')
            
            if not update_fields:
                return jsonify({'success': False, 'error': 'Aucune donnée à mettre à jour'}), 400
            
            # Construire et exécuter la requête
            params.append(prospect_id)
            query = f"UPDATE agriweb_prospects SET {', '.join(update_fields)} WHERE id = %s"
            
            execute_query(query, tuple(params))
            
            print(f"✅ [CRM UPDATE FROM REPORT] Prospect {prospect_id} mis à jour avec succès")
            
            # Créer ou mettre à jour la fiche projet avec le rapport
            project_id = None
            print(f"🔍 [PROJECT CHECK] Vérification data_json dans data: {'data_json' in data}")
            
            # Toujours essayer de créer/mettre à jour le projet
            try:
                # Vérifier si une fiche projet existe déjà pour ce prospect
                existing_project = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                    (prospect_id,),
                    fetch_one=True
                )
                print(f"🔍 [PROJECT CHECK] Projet existant: {existing_project}")
                
                # Récupérer data_json du prospect si pas dans la requête
                data_json_to_save = data.get('data_json')
                if not data_json_to_save:
                    prospect_data = execute_query(
                        "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                        (prospect_id,),
                        fetch_one=True
                    )
                    if prospect_data and prospect_data.get('data_json'):
                        try:
                            data_json_to_save = json.loads(prospect_data['data_json']) if isinstance(prospect_data['data_json'], str) else prospect_data['data_json']
                        except:
                            data_json_to_save = {}
                
                if existing_project:
                    # Mettre à jour la fiche projet existante
                    project_id = existing_project['id']
                    execute_query('''
                        UPDATE project_fiches 
                        SET data_json = %s, 
                            date_modification = NOW(),
                            commune = COALESCE(%s, commune),
                            adresse_projet = COALESCE(%s, adresse_projet),
                            parcelles_cadastrales = COALESCE(%s, parcelles_cadastrales)
                        WHERE id = %s
                    ''', (
                        json.dumps(data_json_to_save) if data_json_to_save else None,
                        data.get('commune'),
                        data.get('adresse') or data.get('commune'),
                        data.get('parcelle_cadastrale'),
                        project_id
                    ))
                    print(f"✅ [PROJECT UPDATE] Fiche projet {project_id} mise à jour avec le rapport")
                    
                    # Marquer l'étape "Rapport de recherche HeliaPV" comme terminée
                    execute_query('''
                        UPDATE project_etapes 
                        SET statut = 'termine', 
                            date_fin_reelle = CURRENT_DATE
                        WHERE project_id = %s 
                        AND ordre = 1
                        AND statut != 'termine'
                    ''', (project_id,))
                    print(f"✅ [ETAPE UPDATE] Étape 1 (Rapport) marquée comme terminée pour projet {project_id}")
                else:
                    # Créer une nouvelle fiche projet
                    print(f"🆕 [PROJECT CREATE] Création d'une nouvelle fiche projet pour prospect {prospect_id}")
                    result = execute_query('''
                        INSERT INTO project_fiches (
                            prospect_id, nom_projet, commune, adresse_projet, 
                            parcelles_cadastrales, statut_projet, data_json, user_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        prospect_id,
                        f"Projet {data.get('adresse') or data.get('commune', 'inconnu')}",
                        data.get('commune'),
                        data.get('adresse') or data.get('commune'),
                        data.get('parcelle_cadastrale'),
                        'etude',
                        json.dumps(data_json_to_save) if data_json_to_save else '{}',
                        str(user_id) if user_id is not None else None
                    ), fetch_one=True)
                    
                    print(f"🔍 [PROJECT CREATE] Résultat INSERT: {result}")
                    
                    if result:
                        project_id = result['id']
                        print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id} créée avec le rapport")
                        
                        # Créer les étapes du workflow pour ce nouveau projet
                        etapes_autoconso = [
                            ('Rapport de recherche HeliaPV', 1),
                            ('Visite technique', 2),
                            ('Calepinage', 3),
                            ('Plan de masse', 4),
                            ('Étude d\'autoconsommation', 5),
                            ('Devis commercial', 6),
                            ('Signature & Facture', 7),
                            ('Déclaration Préalable de Travaux (DP)', 8),
                            ('Déclaration de Raccordement (DDR)', 9),
                            ('Installation & DOE', 10),
                            ('Consuel', 11),
                            ('Mise en service & Maintenance', 12)
                        ]
                        
                        for etape_nom, ordre in etapes_autoconso:
                            # La première étape (rapport) est déjà terminée
                            statut = 'termine' if ordre == 1 else 'a_faire'
                            date_fin = 'CURRENT_DATE' if ordre == 1 else 'NULL'
                            execute_query(f'''
                                INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                                VALUES (%s, %s, %s, %s, {date_fin})
                            ''', (project_id, etape_nom, ordre, statut))
                        
                        print(f"✅ [ETAPES CREATE] 12 étapes créées pour projet {project_id}, étape 1 terminée")
                    else:
                        print(f"⚠️ [PROJECT CREATE] Échec de création du projet - résultat vide")
                    
            except Exception as e:
                print(f"⚠️ [PROJECT SAVE] Erreur lors de l'enregistrement dans la fiche projet: {e}")
                import traceback
                traceback.print_exc()
                # Ne pas bloquer la mise à jour du prospect si la fiche projet échoue
            
            return jsonify({
                'success': True,
                'message': 'Prospect mis à jour avec les données du rapport',
                'prospect_id': prospect_id,
                'project_id': project_id
            })
            
        except Exception as e:
            print(f"❌ [CRM UPDATE FROM REPORT] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>', methods=['DELETE'])
    def delete_prospect(prospect_id):
        """Supprime un prospect"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            if is_admin:
                execute_query('DELETE FROM agriweb_prospects WHERE id = %s', (prospect_id,))
            else:
                execute_query('DELETE FROM agriweb_prospects WHERE id = %s AND user_id = %s', (prospect_id, str(user_id)))
            
            return jsonify({
                'success': True,
                'message': 'Prospect supprimé'
            })
            
        except Exception as e:
            print(f"❌ [CRM DELETE] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES API - GÉNÉRATION CERFA
    # ============================================================================

    @app.route('/api/crm/prospects/<int:prospect_id>/generate-cerfa', methods=['GET'])
    @require_prospect_owner
    def generate_prospect_cerfa(prospect_id):
        """Génère un formulaire CERFA pré-rempli pour le prospect"""
        try:
            from cerfa_generator import generate_cerfa_pdf
            
            # Récupérer les données du prospect
            prospect = execute_query('''
                SELECT * FROM agriweb_prospects WHERE id = %s
            ''', (prospect_id,), fetch_one=True)
            
            if not prospect:
                return jsonify({'success': False, 'error': 'Prospect introuvable'}), 404
            
            # Générer le PDF
            pdf_buffer = generate_cerfa_pdf(prospect)
            
            # Nom du fichier
            nom_fichier = f"CERFA_Raccordement_{prospect.get('nom_prospect', prospect.get('commune', prospect_id))}.pdf"
            nom_fichier = nom_fichier.replace(' ', '_').replace('/', '_')
            
            # Sauvegarder dans la dataroom
            try:
                pdf_buffer.seek(0)
                pdf_bytes = pdf_buffer.read()
                save_to_dataroom(prospect_id, pdf_bytes, nom_fichier, 'cerfa', source='auto-cerfa')
                pdf_buffer.seek(0)
            except Exception as dr_err:
                print(f"⚠️ [DATAROOM] Erreur sauvegarde CERFA: {dr_err}")
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=nom_fichier
            )
            
        except Exception as e:
            print(f"❌ [CERFA GENERATION] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES API - RENDEZ-VOUS
    # ============================================================================

    @app.route('/api/crm/prospects/<int:prospect_id>/appointment', methods=['POST'])
    @require_prospect_owner
    def create_prospect_appointment(prospect_id):
        """Crée un rendez-vous pour un prospect"""
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            rdv_datetime = f"{data['date']} {data['time']}"
            
            # Créer le rendez-vous
            # Schéma réel de crm_appointments : title/start_time/end_time/type/description
            # (cf. database_adapter). On mappe le RDV dessus ; faute de durée fournie,
            # end_time = start_time.
            execute_query('''
                INSERT INTO crm_appointments (
                    prospect_id, title, start_time, end_time, type, description
                ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                prospect_id,
                data.get('type', 'visite'),
                rdv_datetime,
                rdv_datetime,
                data.get('type', 'visite'),
                data.get('notes', '')
            ))
            
            # Mettre à jour le statut du prospect
            execute_query('''
                UPDATE agriweb_prospects 
                SET statut = CASE WHEN statut IN ('nouveau', 'contacte') THEN 'qualifie' ELSE statut END,
                    date_modification = %s
                WHERE id = %s
            ''', (datetime.now().isoformat(), prospect_id))
            
            return jsonify({
                'success': True,
                'message': 'Rendez-vous créé avec succès'
            })
            
        except Exception as e:
            print(f"❌ [CRM APPOINTMENT] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/appointments', methods=['GET'])
    def get_all_appointments():
        """Récupère tous les rendez-vous pour le calendrier"""
        try:
            user_id, is_admin = get_current_crm_user()
            filter_clause, filter_params = user_filter_clause(user_id, is_admin, table_alias='ap')

            appointments = execute_query(f'''
                SELECT
                    ca.*,
                    ca.start_time AS date_rdv,
                    ca.type AS type_rdv,
                    ca.description AS notes,
                    ap.nom_prospect,
                    ap.adresse,
                    ap.contact_nom,
                    ap.contact_email,
                    ap.contact_telephone,
                    ap.type as prospect_type,
                    ap.latitude,
                    ap.longitude
                FROM crm_appointments ca
                JOIN agriweb_prospects ap ON ca.prospect_id = ap.id
                WHERE 1=1{filter_clause}
                ORDER BY ca.start_time ASC
            ''', filter_params if filter_params else None, fetch_all=True)
            
            return jsonify({
                'success': True,
                'appointments': appointments if appointments else []
            })
            
        except Exception as e:
            print(f"❌ [CRM CALENDAR] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # PROSPECTION AUTOCONSO — injection des gros consommateurs Enedis
    # ============================================================================
    @app.route('/api/enedis/inject-crm', methods=['POST'])
    def inject_enedis_autoconso_crm():
        """Injecte les gros consommateurs Enedis d'une commune comme prospects
        'autoconso' (avec pré-diagnostic). Réutilise get_enedis_consommation_by_commune."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            data = request.get_json(silent=True) or {}
            code_commune = str(data.get('code_commune') or '').strip()
            commune_nom = (data.get('commune') or '').strip()
            # Résolution INSEE depuis le nom de commune si code absent (bouton rapport)
            if not code_commune and commune_nom:
                try:
                    import requests as _rq
                    from urllib.parse import quote_plus
                    arr = _rq.get(
                        f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune_nom)}&fields=code&limit=1",
                        timeout=15).json()
                    if arr:
                        code_commune = arr[0].get('code')
                except Exception as _e:
                    print(f"⚠️ [ENEDIS INJECT] lookup INSEE '{commune_nom}': {_e}")
            if not code_commune:
                return jsonify({'success': False, 'error': 'code_commune ou commune requis'}), 400
            min_mwh = float(data.get('min_mwh') or 0)
            limit = int(data.get('limit') or 20)

            from agriweb_hebergement_gratuit import get_enedis_consommation_by_commune
            consommateurs = get_enedis_consommation_by_commune(code_commune) or []
            consommateurs = [c for c in consommateurs
                             if (c.get('consommation_mwh') or 0) >= min_mwh][:limit]

            injected, skipped = 0, 0
            for c in consommateurs:
                adresse = (c.get('adresse') or '').strip()
                commune = c.get('nom_commune') or ''
                if not adresse:
                    continue
                # dédup : même adresse + commune pour cet utilisateur
                existing = execute_query(
                    "SELECT id FROM agriweb_prospects WHERE user_id = %s AND adresse = %s AND commune = %s",
                    (str(user_id), adresse, commune), fetch_one=True)
                if existing:
                    skipped += 1
                    continue
                dj = {
                    'source': 'enedis_autoconso',
                    'code_insee': code_commune,
                    'consommation_mwh': c.get('consommation_mwh'),
                    'secteur': c.get('secteur'),
                    'nombre_de_sites': c.get('nombre_de_sites'),
                    'annee': c.get('annee'),
                    'diagnostic_autoconso': c.get('diagnostic_autoconso') or {},
                }
                res = execute_query('''
                    INSERT INTO agriweb_prospects
                        (type, commune, adresse, latitude, longitude, statut, data_json, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'autoconso', commune, adresse,
                    c.get('latitude'), c.get('longitude'), 'nouveau',
                    json.dumps(dj, ensure_ascii=False), str(user_id),
                ), fetch_one=True)
                if res and res.get('id'):
                    try:
                        auto_create_project_for_prospect(res['id'], commune, adresse, user_id=user_id)
                    except Exception as _e_proj:
                        print(f"⚠️ [ENEDIS INJECT] projet auto échoué pour {res['id']}: {_e_proj}")
                    injected += 1
            return jsonify({'success': True, 'injected': injected, 'skipped': skipped,
                            'total_candidats': len(consommateurs)})
        except Exception as e:
            print(f"❌ [ENEDIS INJECT] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    def _resolve_code_insee(prospect, data_json):
        """Trouve le code INSEE d'un prospect (data_json, sinon lookup nom commune)."""
        code = str((data_json or {}).get('code_insee') or
                   (data_json or {}).get('code_commune') or '').strip()
        if code:
            return code
        commune = (prospect.get('commune') or '').strip()
        if not commune:
            return None
        try:
            import requests
            from urllib.parse import quote_plus
            r = requests.get(
                f"https://geo.api.gouv.fr/communes?nom={quote_plus(commune)}&fields=code&limit=1",
                timeout=15)
            arr = r.json()
            if arr:
                return arr[0].get('code')
        except Exception as _e:
            print(f"⚠️ [ENEDIS ENRICH] lookup INSEE '{commune}': {_e}")
        return None

    def _enrich_one_prospect(prospect, records, force=False):
        """Enrichit un prospect avec le diagnostic autoconso (match Enedis).
        Retourne dict de statut. Modifie data_json en BDD si match trouvé."""
        from autoconsommation import match_enedis_address, diagnostic_autoconso_rapide
        dj = prospect.get('data_json') or {}
        if isinstance(dj, str):
            try: dj = json.loads(dj)
            except Exception: dj = {}
        if dj.get('diagnostic_autoconso') and not force:
            return {'id': prospect.get('id'), 'status': 'deja_enrichi'}
        adresse = (prospect.get('adresse') or '').strip()
        commune = (prospect.get('commune') or '').strip()
        if not adresse:
            return {'id': prospect.get('id'), 'status': 'sans_adresse'}
        rec, score = match_enedis_address(adresse, records, commune=commune)
        if not rec:
            # force : purge un ancien match base sur une correspondance (pas un
            # diagnostic injecte d'origine source=enedis_autoconso)
            if force and dj.get('enedis_match'):
                dj.pop('diagnostic_autoconso', None)
                dj.pop('enedis_match', None)
                execute_query(
                    "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                    (json.dumps(dj, ensure_ascii=False), prospect.get('id')))
                return {'id': prospect.get('id'), 'status': 'match_purge', 'score': score}
            return {'id': prospect.get('id'), 'status': 'aucun_match', 'score': score}
        lat = prospect.get('latitude')
        try: lat = float(lat) if lat is not None else None
        except Exception: lat = None
        diag = diagnostic_autoconso_rapide(rec.get('consommation_mwh'), rec.get('secteur'), lat)
        dj['diagnostic_autoconso'] = diag
        dj['enedis_match'] = {
            'adresse_enedis': rec.get('adresse'),
            'consommation_mwh': rec.get('consommation_mwh'),
            'secteur': rec.get('secteur'),
            'annee': rec.get('annee'),
            'score': score,
        }
        execute_query(
            "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
            (json.dumps(dj, ensure_ascii=False), prospect.get('id')))
        return {'id': prospect.get('id'), 'status': 'enrichi', 'score': score,
                'consommation_mwh': rec.get('consommation_mwh'),
                'secteur': rec.get('secteur'),
                'profil': diag.get('profil'),
                'kwc_reco': diag.get('kwc_reco'),
                'economie_an_eur': diag.get('economie_an_eur')}

    @app.route('/api/enedis/enrich-prospect/<int:prospect_id>', methods=['POST'])
    def enrich_prospect_autoconso(prospect_id):
        """Enrichit UN prospect existant avec son pré-diagnostic autoconso
        en matchant son adresse aux consommations Enedis de sa commune."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès refusé'}), 403
            data = request.get_json(silent=True) or {}
            force = bool(data.get('force'))
            prospect = execute_query(
                "SELECT id, commune, adresse, latitude, data_json FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True)
            if not prospect:
                return jsonify({'success': False, 'error': 'Prospect introuvable'}), 404
            dj = prospect.get('data_json') or {}
            if isinstance(dj, str):
                try: dj = json.loads(dj)
                except Exception: dj = {}
            code_insee = _resolve_code_insee(prospect, dj)
            if not code_insee:
                return jsonify({'success': False, 'error': 'Code INSEE introuvable pour ce prospect'}), 400
            from agriweb_hebergement_gratuit import get_enedis_records_raw
            records = get_enedis_records_raw(code_insee) or []
            res = _enrich_one_prospect(prospect, records, force=force)
            return jsonify({'success': res['status'] == 'enrichi', 'result': res,
                            'code_insee': code_insee, 'candidats_enedis': len(records)})
        except Exception as e:
            print(f"❌ [ENEDIS ENRICH] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/enedis/enrich-commune', methods=['POST'])
    def enrich_commune_autoconso():
        """Enrichit TOUS les prospects d'une commune (de l'utilisateur) avec le
        pré-diagnostic autoconso. body: {code_commune?, commune?, force?}"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            data = request.get_json(silent=True) or {}
            force = bool(data.get('force'))
            code_commune = str(data.get('code_commune') or '').strip()
            commune = (data.get('commune') or '').strip()
            # Sélection des prospects de l'utilisateur (filtrés par commune si fournie)
            clause, params = '', []
            if not is_admin:
                clause += ' AND user_id = %s'; params.append(str(user_id))
            if commune:
                clause += ' AND commune = %s'; params.append(commune)
            prospects = execute_query(
                f"SELECT id, commune, adresse, latitude, data_json FROM agriweb_prospects "
                f"WHERE adresse IS NOT NULL AND adresse <> ''{clause}",
                tuple(params), fetch_all=True) or []
            if not prospects:
                return jsonify({'success': True, 'enrichis': 0, 'total': 0, 'details': []})
            # Cache des records Enedis par commune (1 appel API par commune)
            records_cache = {}
            details, enrichis = [], 0
            for p in prospects:
                dj = p.get('data_json') or {}
                if isinstance(dj, str):
                    try: dj = json.loads(dj)
                    except Exception: dj = {}
                # code_commune n'est utilisé comme INSEE que s'il est apparié à un
                # filtre commune (sinon on l'appliquerait à des prospects d'autres
                # communes). Sans filtre, chaque prospect résout son propre INSEE.
                ci = (code_commune if (code_commune and commune) else None) \
                     or _resolve_code_insee(p, dj)
                if not ci:
                    details.append({'id': p.get('id'), 'status': 'sans_insee'}); continue
                if ci not in records_cache:
                    from agriweb_hebergement_gratuit import get_enedis_records_raw
                    records_cache[ci] = get_enedis_records_raw(ci) or []
                res = _enrich_one_prospect(p, records_cache[ci], force=force)
                if res['status'] == 'enrichi':
                    enrichis += 1
                details.append(res)
            return jsonify({'success': True, 'enrichis': enrichis, 'total': len(prospects),
                            'communes_interrogees': len(records_cache), 'details': details})
        except Exception as e:
            print(f"❌ [ENEDIS ENRICH COMMUNE] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/enedis/majic-test', methods=['GET', 'POST'])
    def majic_enedis_test():
        """MESURE (admin) : sur un échantillon de propriétaires MAJIC, quel taux
        de remontée Enedis ? Pont parcelle -> Géoplateforme (parcel) -> coords ->
        reverse (adresse) -> match Enedis OpenData. Params: limit, max_dist (m)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            limit = int(request.values.get('limit') or 100)
            max_dist = float(request.values.get('max_dist') or 80)
            # Filtre optionnel par forme(s) juridique(s) : ?fj=5499,5710
            fj_raw = request.values.get('fj') or ''
            fj_codes = [c.strip() for c in fj_raw.split(',') if c.strip().isdigit()]
            fj_clause = ''
            if fj_codes:
                fj_clause = " AND forme_juridique IN (" + ",".join(fj_codes) + ")"

            # Mode "count" : volume réel de la base (sans géocodage) pour
            # dimensionner le gisement. /api/enedis/majic-test?count=1
            if request.values.get('count'):
                vol = execute_query("""
                    SELECT COUNT(*) AS lignes,
                           COUNT(DISTINCT siren) AS entites,
                           COUNT(DISTINCT code_insee) AS communes
                    FROM proprietaires_parcelles
                    WHERE denomination IS NOT NULL
                """, fetch_one=True) or {}
                top_fj = execute_query("""
                    SELECT forme_juridique, COUNT(DISTINCT siren) AS entites
                    FROM proprietaires_parcelles
                    WHERE denomination IS NOT NULL AND forme_juridique IS NOT NULL
                    GROUP BY forme_juridique
                    ORDER BY entites DESC
                    LIMIT 15
                """, fetch_all=True) or []
                return jsonify({'success': True, 'volume': vol,
                                'top_formes_juridiques': top_fj})

            # Échantillon ALÉATOIRE national (TABLESAMPLE rapide + random()) pour
            # éviter le biais métropolitain d'un ORDER BY siren. 1 ligne / SIREN.
            # TABLESAMPLE plus large si on filtre un segment (sinon trop peu de lignes).
            pct = 15 if fj_codes else 5
            owners = execute_query(f"""
                SELECT * FROM (
                    SELECT DISTINCT ON (siren) siren, denomination, forme_juridique,
                           code_insee, section, numero
                    FROM proprietaires_parcelles TABLESAMPLE SYSTEM ({pct})
                    WHERE denomination IS NOT NULL AND section IS NOT NULL
                      AND numero IS NOT NULL AND code_insee IS NOT NULL{fj_clause}
                    ORDER BY siren
                ) t ORDER BY random() LIMIT %s
            """, (limit,), fetch_all=True) or []
            if not owners:
                # fallback si TABLESAMPLE ne renvoie rien (table petite)
                owners = execute_query(f"""
                    SELECT DISTINCT ON (siren) siren, denomination, forme_juridique,
                           code_insee, section, numero
                    FROM proprietaires_parcelles
                    WHERE denomination IS NOT NULL AND section IS NOT NULL
                      AND numero IS NOT NULL AND code_insee IS NOT NULL{fj_clause}
                    ORDER BY siren LIMIT %s
                """, (limit,), fetch_all=True) or []
            if not owners:
                return jsonify({'success': True, 'echantillon': 0,
                                'note': 'Aucun propriétaire MAJIC trouvé'})

            import requests as _rq
            from concurrent.futures import ThreadPoolExecutor
            from autoconsommation import match_enedis_address
            from agriweb_hebergement_gratuit import get_enedis_records_raw
            GEO = "https://data.geopf.fr/geocodage"
            enedis_cache = {}
            import time as _time

            def _geo_get(path, params, tries=3):
                """GET Géoplateforme avec retry/backoff (l'API throttle sous charge)."""
                last = None
                for i in range(tries):
                    try:
                        r = _rq.get(f"{GEO}/{path}", params=params, timeout=20)
                        if r.status_code == 200:
                            return r.json()
                        last = f"http{r.status_code}"
                    except Exception as _e:
                        last = type(_e).__name__
                    _time.sleep(0.5 * (i + 1))
                raise RuntimeError(last or 'geo_fail')

            def _process(o):
                ci = str(o.get('code_insee') or '').strip()
                dept, comm = ci[:2], ci[2:]
                # Le cadastre officiel code la section sur 2 caractères : une
                # section d'une seule lettre/chiffre est préfixée par '0' (C -> 0C).
                section = str(o.get('section') or '').strip()
                if len(section) == 1:
                    section = '0' + section
                numero = str(o.get('numero') or '').strip().zfill(4)
                res = {'siren': o.get('siren'), 'denomination': o.get('denomination'),
                       'forme_juridique': o.get('forme_juridique'), 'code_insee': ci,
                       'section_raw': o.get('section'), 'numero_raw': o.get('numero'),
                       'status': 'init'}
                try:
                    pr = _geo_get('search', {
                        'index': 'parcel', 'departmentcode': dept, 'municipalitycode': comm,
                        'section': section, 'number': numero, 'limit': 1})
                    feats = pr.get('features') or []
                    if not feats:
                        res['status'] = 'parcelle_introuvable'; return res
                    lon, lat = feats[0]['geometry']['coordinates']
                    rr = _geo_get('reverse', {
                        'index': 'address', 'lon': lon, 'lat': lat, 'limit': 1})
                    af = rr.get('features') or []
                    if not af:
                        res['status'] = 'adresse_introuvable'; return res
                    ap = af[0].get('properties', {})
                    res['adresse'] = ap.get('label')
                    res['distance_m'] = ap.get('distance')
                    citycode = ap.get('citycode') or ci
                    if ap.get('distance') is not None and ap['distance'] > max_dist:
                        res['status'] = 'parcelle_sans_batiment_proche'; return res
                    if citycode not in enedis_cache:
                        enedis_cache[citycode] = get_enedis_records_raw(citycode) or []
                    rec, score = match_enedis_address(
                        ap.get('label') or '', enedis_cache[citycode], commune=ap.get('city') or '')
                    if rec:
                        res['status'] = 'enedis_ok'
                        res['conso_mwh'] = rec.get('consommation_mwh')
                        res['secteur'] = rec.get('secteur')
                        res['score'] = score
                    else:
                        res['status'] = 'aucun_match_enedis'
                    return res
                except Exception as _e:
                    res['status'] = 'erreur'; res['err'] = str(_e)[:80]; return res

            with ThreadPoolExecutor(max_workers=5) as ex:
                results = list(ex.map(_process, owners))

            from collections import Counter
            stats = dict(Counter(r['status'] for r in results))
            ok = [r for r in results if r['status'] == 'enedis_ok']
            n = len(results)
            taux = {
                'parcelle_geocodee_%': round(100 * sum(1 for r in results if r['status'] not in ('parcelle_introuvable', 'erreur')) / n, 1) if n else 0,
                'adresse_trouvee_%': round(100 * sum(1 for r in results if r.get('adresse')) / n, 1) if n else 0,
                'enedis_remonte_%': round(100 * len(ok) / n, 1) if n else 0,
            }
            conso_vals = sorted((r['conso_mwh'] for r in ok if r.get('conso_mwh')), reverse=True)
            secteurs = dict(Counter(r.get('secteur') for r in ok))
            industrie = [r for r in ok if r.get('secteur') == 'INDUSTRIE']
            return jsonify({
                'success': True, 'echantillon': n, 'max_dist_m': max_dist,
                'taux': taux, 'statuts': stats,
                'secteurs_enedis_ok': secteurs,
                'industrie_n': len(industrie),
                'industrie_conso_max_mwh': max((r.get('conso_mwh') or 0 for r in industrie), default=None),
                'exemples_industrie': industrie[:12],
                'conso_mediane_mwh': conso_vals[len(conso_vals)//2] if conso_vals else None,
                'conso_max_mwh': conso_vals[0] if conso_vals else None,
                'exemples_enedis_ok': ok[:25],
                'exemples_parcelle_introuvable': [r for r in results if r['status'] == 'parcelle_introuvable'][:8],
                'exemples_erreur': [r for r in results if r['status'] == 'erreur'][:8],
            })
        except Exception as e:
            print(f"❌ [MAJIC TEST] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    def _run_industrial_scan(dept, code_commune, secteur, min_mwh, limit, annee, with_foncier=True):
        """PROSPECTION INVERSE : Enedis (sites du secteur, conso >= seuil, triés
        décroissant, paginés) -> opérateur (SIRENE). Le rattachement foncier MAJIC
        est optionnel (with_foncier) car peu pertinent pour l'industriel."""
        if True:
            import requests as _rq
            from concurrent.futures import ThreadPoolExecutor
            import time as _time
            GEO = "https://data.geopf.fr/geocodage"

            # 1) Enedis : sites du secteur, conso >= seuil, triés décroissant.
            # Pagination (limit API max 100) + dédup multi-années -> on récupère
            # assez de lignes brutes pour obtenir `limit` sites UNIQUES.
            where = (f'code_grand_secteur="{secteur}" '
                     f'AND consommation_annuelle_totale_de_ladresse_mwh >= {min_mwh}')
            if dept:
                where += f' AND code_departement="{dept}"'
            if code_commune:
                where += f' AND code_commune="{code_commune}"'
            if annee:
                where += f' AND annee={int(annee)}'
            api_url = ("https://opendata.enedis.fr/api/explore/v2.1/catalog/datasets/"
                       "consommation-annuelle-entreprise-par-adresse/records")
            raw = []
            raw_cap = min(limit * 3, 4000)  # on sur-échantillonne pour la dédup
            offset = 0
            while len(raw) < raw_cap:
                er = _rq.get(api_url, params={
                    'where': where,
                    'order_by': 'consommation_annuelle_totale_de_ladresse_mwh DESC',
                    'limit': min(100, raw_cap - len(raw)), 'offset': offset,
                    'select': ('adresse,numero_de_voie,type_de_voie,libelle_de_voie,nom_commune,'
                               'code_commune,code_secteur_naf2,nombre_de_sites,'
                               'consommation_annuelle_totale_de_ladresse_mwh,annee'),
                }, timeout=30)
                batch = er.json().get('results', []) if er.status_code == 200 else []
                if not batch:
                    break
                raw.extend(batch)
                offset += len(batch)
                if len(batch) < 100:
                    break

            # Déduplication par adresse (1 ligne/année) : garde la conso max.
            _dedup = {}
            for s in raw:
                key = (str(s.get('numero_de_voie') or ''), str(s.get('libelle_de_voie') or ''),
                       str(s.get('adresse') or ''), str(s.get('code_commune') or ''))
                cur = _dedup.get(key)
                if not cur or (s.get('consommation_annuelle_totale_de_ladresse_mwh') or 0) > \
                        (cur.get('consommation_annuelle_totale_de_ladresse_mwh') or 0):
                    _dedup[key] = s
            sites = sorted(_dedup.values(),
                           key=lambda s: s.get('consommation_annuelle_totale_de_ladresse_mwh') or 0,
                           reverse=True)[:limit]

            def _geo_get(path, params, tries=3):
                last = None
                for i in range(tries):
                    try:
                        r = _rq.get(f"{GEO}/{path}", params=params, timeout=20)
                        if r.status_code == 200:
                            return r.json()
                        last = f"http{r.status_code}"
                    except Exception as _e:
                        last = type(_e).__name__
                    _time.sleep(0.5 * (i + 1))
                return {}

            def _resolve_parcelle(site):
                """Adresse Enedis -> coords -> parcelle (section/numero/insee)."""
                a = (site.get('adresse') or '').strip()
                if not a:
                    a = ' '.join(p for p in [str(site.get('numero_de_voie') or '').strip(),
                                             str(site.get('type_de_voie') or '').strip(),
                                             str(site.get('libelle_de_voie') or '').strip()] if p).strip()
                commune = site.get('nom_commune') or ''
                cc = site.get('code_commune') or ''
                site['adresse_resolue'] = f"{a}, {commune}".strip(', ')
                if not a:
                    site['parcelle_status'] = 'sans_adresse'; return site
                gr = _geo_get('search', {'index': 'address', 'q': f"{a} {commune}",
                                         'citycode': cc, 'limit': 1})
                feats = gr.get('features') or []
                if not feats:
                    site['parcelle_status'] = 'adresse_non_geocodee'; return site
                lon, lat = feats[0]['geometry']['coordinates']
                pr = _geo_get('reverse', {'index': 'parcel', 'lon': lon, 'lat': lat, 'limit': 1})
                pf = pr.get('features') or []
                if not pf:
                    site['parcelle_status'] = 'parcelle_non_trouvee'; return site
                pp = pf[0].get('properties', {})
                site['insee'] = f"{pp.get('departmentcode', '')}{pp.get('municipalitycode', '')}"
                site['section'] = pp.get('section')
                site['numero'] = pp.get('number')
                site['parcelle_id'] = pp.get('id')
                site['parcelle_status'] = 'parcelle_ok'
                return site

            owners_found = 0
            if with_foncier:
                # Rattachement foncier MAJIC (optionnel) : adresse -> parcelle -> propriétaire.
                with ThreadPoolExecutor(max_workers=5) as ex:
                    sites = list(ex.map(_resolve_parcelle, sites))
                for site in sites:
                    if site.get('parcelle_status') != 'parcelle_ok':
                        continue
                    sec = str(site.get('section') or '')
                    num = str(site.get('numero') or '')
                    sec_cands = list({sec, sec.lstrip('0'), sec.zfill(2)})
                    num_cands = list({num, num.lstrip('0'), num.zfill(4)})
                    try:
                        owner = execute_query(
                            "SELECT denomination, siren, forme_juridique FROM proprietaires_parcelles "
                            "WHERE code_insee = %s AND section = ANY(%s) AND numero = ANY(%s) "
                            "AND denomination IS NOT NULL LIMIT 1",
                            (site.get('insee'), sec_cands, num_cands), fetch_one=True)
                    except Exception:
                        owner = None
                    if owner:
                        site['proprietaire'] = owner.get('denomination')
                        site['proprietaire_siren'] = owner.get('siren')
                        site['proprietaire_fj'] = owner.get('forme_juridique')
                        owners_found += 1
            else:
                # Sans foncier : on construit juste l'adresse lisible.
                for site in sites:
                    a = (site.get('adresse') or '').strip()
                    if not a:
                        a = ' '.join(p for p in [str(site.get('numero_de_voie') or '').strip(),
                                                 str(site.get('type_de_voie') or '').strip(),
                                                 str(site.get('libelle_de_voie') or '').strip()] if p).strip()
                    site['adresse_resolue'] = f"{a}, {site.get('nom_commune') or ''}".strip(', ')

            # 3) SIRENE : opérateur(s) probable(s) = entreprises de la commune dont
            # l'activité (NAF) colle au secteur Enedis, classées par effectif.
            # Cache par (code_commune, naf2). C'est le DÉCIDEUR (vs MAJIC = foncier).
            sirene_cache = {}

            def _naf2_section(naf2):
                """Section INSEE depuis la division NAF2 (gammes industrielles)."""
                try:
                    nn = int(str(naf2).strip())
                except Exception:
                    return None
                if 5 <= nn <= 9: return 'B'      # industries extractives
                if 10 <= nn <= 33: return 'C'    # industrie manufacturière
                if nn == 35: return 'D'          # énergie
                if 36 <= nn <= 39: return 'E'    # eau / déchets
                return None

            def _eff(c):
                try:
                    return int(c.get('tranche_effectif_salarie') or -1)
                except Exception:
                    return -1

            def _sirene_ops(cc, naf2):
                ck = (cc, naf2)
                if ck in sirene_cache:
                    return sirene_cache[ck]
                ops = []
                naf2s = str(naf2 or '').strip()
                section = _naf2_section(naf2s)
                # Sans NAF exploitable, pas d'opérateur fiable (on n'invente rien).
                if naf2s and section:
                    cands = []
                    # Retry/backoff : l'API recherche-entreprises throttle (~7 req/s).
                    for i in range(4):
                        try:
                            rr = _rq.get("https://recherche-entreprises.api.gouv.fr/search",
                                         params={'code_commune': cc,
                                                 'section_activite_principale': section,
                                                 'per_page': 25, 'page': 1}, timeout=15)
                            if rr.status_code == 200:
                                cands = rr.json().get('results') or []
                                break
                            if rr.status_code != 429 and rr.status_code >= 400 and rr.status_code != 503:
                                break  # erreur non transitoire
                        except Exception:
                            pass
                        _time.sleep(0.7 * (i + 1))
                    # STRICT : uniquement le NAF2 du site (jamais de repli hors-NAF).
                    cands = [c for c in cands
                             if (c.get('activite_principale') or '').replace('.', '').startswith(naf2s)]
                    for c in sorted(cands, key=_eff, reverse=True)[:3]:
                        ops.append({'nom': c.get('nom_complet'), 'siren': c.get('siren'),
                                    'naf': c.get('activite_principale'),
                                    'effectif': c.get('tranche_effectif_salarie')})
                sirene_cache[ck] = ops
                return ops

            with ThreadPoolExecutor(max_workers=4) as ex2:
                ops_list = list(ex2.map(
                    lambda s: _sirene_ops(s.get('code_commune'), s.get('code_secteur_naf2')), sites))
            for s, ops in zip(sites, ops_list):
                s['operateurs'] = ops

            n = len(sites)
            avec_operateur = sum(1 for s in sites if s.get('operateurs'))
            prospects = [{
                'conso_mwh': s.get('consommation_annuelle_totale_de_ladresse_mwh'),
                'naf2': s.get('code_secteur_naf2'),
                'adresse': s.get('adresse_resolue'),
                'commune': s.get('nom_commune'),
                'code_commune': s.get('code_commune'),
                'nb_sites': s.get('nombre_de_sites'),
                'annee': s.get('annee'),
                'operateurs_sirene': s.get('operateurs'),
                'parcelle': s.get('parcelle_id'),
                'proprietaire_foncier': s.get('proprietaire'),
                'proprietaire_siren': s.get('proprietaire_siren'),
            } for s in sites]
            return {
                'sites_enedis': n,
                'avec_operateur_sirene': avec_operateur,
                'taux_operateur_%': round(100 * avec_operateur / n, 1) if n else 0,
                'proprietaire_foncier_resolu': owners_found,
                'prospects': prospects,
            }

    @app.route('/api/enedis/industrial-scan', methods=['GET', 'POST'])
    def industrial_scan():
        """Scan brut (diagnostic, admin) : renvoie la liste sans rien stocker."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            dept = (request.values.get('dept') or '').strip()
            code_commune = (request.values.get('code_commune') or '').strip()
            secteur = (request.values.get('secteur') or 'INDUSTRIE').strip().upper()
            min_mwh = float(request.values.get('min_mwh') or 100)
            limit = min(int(request.values.get('limit') or 50), 100)
            annee = request.values.get('annee')
            if not dept and not code_commune:
                return jsonify({'success': False, 'error': 'dept ou code_commune requis'}), 400
            res = _run_industrial_scan(dept, code_commune, secteur, min_mwh, limit, annee)
            return jsonify({'success': True,
                            'filtre': {'dept': dept, 'code_commune': code_commune,
                                       'secteur': secteur, 'min_mwh': min_mwh}, **res})
        except Exception as e:
            print(f"❌ [INDUSTRIAL SCAN] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # CRM INDUSTRIEL DÉDIÉ (table séparée industrial_prospects)
    # ============================================================================
    def _ensure_industrial_table():
        execute_query("""
            CREATE TABLE IF NOT EXISTS industrial_prospects (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                commune TEXT,
                code_commune TEXT,
                adresse TEXT,
                conso_mwh REAL,
                naf2 TEXT,
                secteur TEXT,
                operateur_nom TEXT,
                operateur_siren TEXT,
                operateur_naf TEXT,
                operateur_effectif TEXT,
                proprietaire_foncier TEXT,
                parcelle TEXT,
                kwc_reco REAL,
                economie_an_eur REAL,
                statut TEXT DEFAULT 'nouveau',
                notes TEXT,
                data_json TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Marqueur de tentative de résolution opérateur (évite les boucles).
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS operateur_tried INTEGER DEFAULT 0")
        # Géocodage du gisement (lat/lon) pour la vignette-carte + le calepinage.
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS lat REAL")
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS lon REAL")
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS geo_tried INTEGER DEFAULT 0")
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS geo_source TEXT")
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS geo_precision TEXT")
        execute_query("ALTER TABLE industrial_prospects ADD COLUMN IF NOT EXISTS geo2_tried INTEGER DEFAULT 0")

    def _ensure_scan_jobs_table():
        execute_query("""
            CREATE TABLE IF NOT EXISTS scan_jobs (
                id SERIAL PRIMARY KEY,
                type TEXT,
                status TEXT DEFAULT 'running',
                user_id TEXT,
                params TEXT,
                depts_todo TEXT,
                depts_done TEXT,
                current_dept TEXT,
                total_injected INTEGER DEFAULT 0,
                total_skipped INTEGER DEFAULT 0,
                claimed_at TIMESTAMP,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        execute_query("ALTER TABLE scan_jobs ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMP")

    def _all_depts():
        d = [f"{i:02d}" for i in range(1, 96) if i != 20]
        return d + ["2A", "2B", "971", "972", "973", "974", "976"]

    def _inject_industrial_dept(dept, min_kwc, limit, user_id, secteur='INDUSTRIE'):
        """Scanne 1 département et injecte dans industrial_prospects.
        Retourne (injected, skipped, sites_scannes)."""
        min_mwh = round(float(min_kwc) * 3.3, 1)
        res = _run_industrial_scan(dept, '', secteur, min_mwh, int(limit), None, with_foncier=False)
        try:
            from autoconsommation import diagnostic_autoconso_rapide
        except Exception:
            diagnostic_autoconso_rapide = None
        injected, skipped = 0, 0
        for p in res.get('prospects', []):
            adresse = (p.get('adresse') or '').strip()
            cc = p.get('code_commune') or ''
            if not adresse:
                skipped += 1; continue
            existing = execute_query(
                "SELECT id FROM industrial_prospects WHERE user_id = %s AND code_commune = %s AND adresse = %s",
                (str(user_id), cc, adresse), fetch_one=True)
            if existing:
                skipped += 1; continue
            ops = p.get('operateurs_sirene') or []
            op = ops[0] if ops else {}
            diag = {}
            if diagnostic_autoconso_rapide:
                try:
                    diag = diagnostic_autoconso_rapide(p.get('conso_mwh'), secteur) or {}
                except Exception:
                    diag = {}
            dj = {'operateurs_sirene': ops, 'naf2': p.get('naf2'), 'parcelle': p.get('parcelle'),
                  'proprietaire_foncier': p.get('proprietaire_foncier'), 'annee': p.get('annee'),
                  'diagnostic_autoconso': diag}
            execute_query("""
                INSERT INTO industrial_prospects
                    (user_id, commune, code_commune, adresse, conso_mwh, naf2, secteur,
                     operateur_nom, operateur_siren, operateur_naf, operateur_effectif,
                     proprietaire_foncier, parcelle, kwc_reco, economie_an_eur, statut, data_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                str(user_id), p.get('commune'), cc, adresse, p.get('conso_mwh'),
                p.get('naf2'), secteur, op.get('nom'), op.get('siren'), op.get('naf'),
                op.get('effectif'), p.get('proprietaire_foncier'), p.get('parcelle'),
                diag.get('kwc_reco'), diag.get('economie_an_eur'),
                'nouveau', json.dumps(dj, ensure_ascii=False),
            ))
            injected += 1
        return injected, skipped, res.get('sites_enedis', 0)

    def _france_worker(job_id):
        """Worker autonome : enchaîne les départements restants d'un job, paçé,
        en mettant à jour l'état en base (survit aux redémarrages via reprise)."""
        import time as _t
        try:
            while True:
                job = execute_query("SELECT * FROM scan_jobs WHERE id = %s", (job_id,), fetch_one=True)
                if not job or job.get('status') != 'running':
                    break
                todo = json.loads(job.get('depts_todo') or '[]')
                if not todo:
                    execute_query("UPDATE scan_jobs SET status='done', current_dept=NULL, updated_at=CURRENT_TIMESTAMP WHERE id=%s", (job_id,))
                    break
                dept = todo[0]
                params = json.loads(job.get('params') or '{}')
                execute_query("UPDATE scan_jobs SET current_dept=%s, updated_at=CURRENT_TIMESTAMP WHERE id=%s", (dept, job_id))
                try:
                    inj, skip, _sites = _inject_industrial_dept(
                        dept, params.get('min_kwc', 100), params.get('limit', 1000), job.get('user_id'))
                except Exception as _e:
                    inj, skip = 0, 0
                    print(f"⚠️ [FRANCE WORKER] dept {dept}: {_e}")
                done = json.loads(job.get('depts_done') or '[]'); done.append(dept)
                execute_query("""UPDATE scan_jobs SET depts_todo=%s, depts_done=%s,
                                 total_injected=total_injected+%s, total_skipped=total_skipped+%s,
                                 updated_at=CURRENT_TIMESTAMP, claimed_at=CURRENT_TIMESTAMP WHERE id=%s""",
                              (json.dumps(todo[1:]), json.dumps(done), inj, skip, job_id))
                _t.sleep(20)  # paçage entre départements (ménage l'app + les API)
        except Exception as _e:
            print(f"❌ [FRANCE WORKER] {_e}")
        finally:
            _FRANCE_STATE['running'] = False

    def _claim_job(job_id):
        """Verrou multi-process : un seul worker gunicorn « réclame » un job à la
        fois (atomique en base). Re-réclamable après 900 s d'inactivité (process mort)."""
        try:
            row = execute_query(
                "UPDATE scan_jobs SET claimed_at = CURRENT_TIMESTAMP "
                "WHERE id = %s AND status = 'running' "
                "AND (claimed_at IS NULL OR claimed_at < CURRENT_TIMESTAMP - INTERVAL '900 seconds') "
                "RETURNING id", (job_id,), fetch_one=True)
            return bool(row)
        except Exception:
            return True  # en cas de doute (colonne absente…), on n'empêche pas le run

    def _start_france_worker(job_id):
        import threading
        if not _claim_job(job_id):
            return False  # un autre process détient déjà ce job
        with _FRANCE_LOCK:
            if _FRANCE_STATE.get('running'):
                return False
            _FRANCE_STATE['running'] = True
        threading.Thread(target=_france_worker, args=(job_id,), daemon=True).start()
        return True

    def _sirene_operator(cc, naf2):
        """Résout l'opérateur d'un site via SIRENE (commune + NAF, tri effectif).
        Retourne (ops_list, ok) ; ok=False = échec API (throttle) -> à réessayer."""
        import requests as _rq, time as _t
        naf2s = str(naf2 or '').strip()

        def _section(n):
            try:
                nn = int(n)
            except Exception:
                return None
            if 5 <= nn <= 9: return 'B'
            if 10 <= nn <= 33: return 'C'
            if nn == 35: return 'D'
            if 36 <= nn <= 39: return 'E'
            return None
        section = _section(naf2s)
        if not naf2s or not section:
            return [], True  # pas de NAF exploitable -> rien à résoudre
        cands = None
        for i in range(5):
            try:
                r = _rq.get("https://recherche-entreprises.api.gouv.fr/search",
                            params={'code_commune': cc, 'section_activite_principale': section,
                                    'per_page': 25, 'page': 1}, timeout=15)
                if r.status_code == 200:
                    cands = r.json().get('results') or []
                    break
            except Exception:
                pass
            _t.sleep(1.0 * (i + 1))  # backoff
        if cands is None:
            return [], False  # throttle / échec -> réessayable
        cands = [c for c in cands
                 if (c.get('activite_principale') or '').replace('.', '').startswith(naf2s)]

        def _eff(c):
            try:
                return int(c.get('tranche_effectif_salarie') or -1)
            except Exception:
                return -1
        ops = [{'nom': c.get('nom_complet'), 'siren': c.get('siren'),
                'naf': c.get('activite_principale'), 'effectif': c.get('tranche_effectif_salarie')}
               for c in sorted(cands, key=_eff, reverse=True)[:3]]
        return ops, True

    def _operators_worker(job_id):
        """Repasse sur les prospects sans opérateur (avec NAF), résout via SIRENE,
        paçé pour ne pas se faire throttler. Chaque prospect est tenté une fois/run."""
        import time as _t
        try:
            cache = {}
            while True:
                job = execute_query("SELECT status FROM scan_jobs WHERE id=%s", (job_id,), fetch_one=True)
                if not job or job.get('status') != 'running':
                    break
                batch = execute_query("""
                    SELECT id, code_commune, naf2 FROM industrial_prospects
                    WHERE operateur_nom IS NULL AND COALESCE(operateur_tried,0)=0
                      AND naf2 IS NOT NULL AND naf2 <> '' LIMIT 40
                """, fetch_all=True) or []
                if not batch:
                    execute_query("UPDATE scan_jobs SET status='done', updated_at=CURRENT_TIMESTAMP WHERE id=%s", (job_id,))
                    break
                resolved = 0
                for p in batch:
                    key = (p.get('code_commune'), p.get('naf2'))
                    if key in cache:
                        ops, ok = cache[key]
                    else:
                        ops, ok = _sirene_operator(p.get('code_commune'), p.get('naf2'))
                        if ok:
                            cache[key] = (ops, ok)
                    op = ops[0] if (ok and ops) else {}
                    # tried=1 dans tous les cas (trouvé / pas de match / throttle) pour
                    # garantir la terminaison ; un re-run réinitialise les non résolus.
                    execute_query("""UPDATE industrial_prospects SET operateur_tried=1,
                                     operateur_nom=%s, operateur_siren=%s, operateur_naf=%s, operateur_effectif=%s
                                     WHERE id=%s""",
                                  (op.get('nom'), op.get('siren'), op.get('naf'), op.get('effectif'), p['id']))
                    if op:
                        resolved += 1
                    if not ok:
                        _t.sleep(3)  # throttle -> on lève le pied
                execute_query("UPDATE scan_jobs SET total_injected=total_injected+%s, "
                              "updated_at=CURRENT_TIMESTAMP, claimed_at=CURRENT_TIMESTAMP WHERE id=%s",
                              (resolved, job_id))
                _t.sleep(6)  # paçage entre lots
        except Exception as _e:
            print(f"❌ [OP WORKER] {_e}")
        finally:
            _OP_STATE['running'] = False

    def _start_operators_worker(job_id):
        import threading
        if not _claim_job(job_id):
            return False  # un autre process détient déjà ce job
        with _FRANCE_LOCK:
            if _OP_STATE.get('running'):
                return False
            _OP_STATE['running'] = True
        threading.Thread(target=_operators_worker, args=(job_id,), daemon=True).start()
        return True

    def _geocode_worker(job_id):
        """Géocode le gisement industriel (lat/lon depuis l'adresse via Géoplateforme),
        paçé. Chaque site tenté une fois/run ; geo_tried évite les boucles."""
        import requests as _rq, time as _t
        GEO = "https://data.geopf.fr/geocodage"

        def _geo(addr, cc):
            for i in range(4):
                try:
                    r = _rq.get(f"{GEO}/search", params={
                        'index': 'address', 'q': addr, 'citycode': cc or '', 'limit': 1}, timeout=15)
                    if r.status_code == 200:
                        f = r.json().get('features') or []
                        if f:
                            lon, lat = f[0]['geometry']['coordinates']
                            return lat, lon, True
                        return None, None, True  # géocodé mais rien -> on marque
                except Exception:
                    pass
                _t.sleep(0.6 * (i + 1))
            return None, None, False  # échec API -> réessayable au prochain run

        try:
            while True:
                job = execute_query("SELECT status FROM scan_jobs WHERE id=%s", (job_id,), fetch_one=True)
                if not job or job.get('status') != 'running':
                    break
                batch = execute_query("""
                    SELECT id, adresse, code_commune FROM industrial_prospects
                    WHERE lat IS NULL AND COALESCE(geo_tried,0)=0
                      AND adresse IS NOT NULL AND adresse <> '' LIMIT 50
                """, fetch_all=True) or []
                if not batch:
                    execute_query("UPDATE scan_jobs SET status='done', updated_at=CURRENT_TIMESTAMP WHERE id=%s", (job_id,))
                    break
                done = 0
                for p in batch:
                    lat, lon, ok = _geo(p.get('adresse'), p.get('code_commune'))
                    if not ok:
                        _t.sleep(2); continue  # throttle -> on lèvera au prochain run
                    execute_query("UPDATE industrial_prospects SET geo_tried=1, lat=%s, lon=%s WHERE id=%s",
                                  (lat, lon, p['id']))
                    if lat is not None:
                        done += 1
                execute_query("UPDATE scan_jobs SET total_injected=total_injected+%s, "
                              "updated_at=CURRENT_TIMESTAMP, claimed_at=CURRENT_TIMESTAMP WHERE id=%s",
                              (done, job_id))
                _t.sleep(2)  # paçage entre lots
        except Exception as _e:
            print(f"❌ [GEO WORKER] {_e}")
        finally:
            _GEO_STATE['running'] = False

    def _start_geocode_worker(job_id):
        import threading
        if not _claim_job(job_id):
            return False
        with _FRANCE_LOCK:
            if _GEO_STATE.get('running'):
                return False
            _GEO_STATE['running'] = True
        threading.Thread(target=_geocode_worker, args=(job_id,), daemon=True).start()
        return True

    def _geocode2_worker(job_id):
        """Géocodage v2 (haute précision) : SIREN → établissement INSEE (parcelle)
        en priorité, sinon BAN mais uniquement si 'housenumber'. Stocke la précision
        (exact / rue / approx) pour pouvoir signaler les localisations approximatives."""
        import requests as _rq, time as _t
        GEO = "https://data.geopf.fr/geocodage"
        SIR = "https://recherche-entreprises.api.gouv.fr/search"

        def _sirene_etab(siren, cc):
            """(lat, lon, ok) depuis l'établissement SIREN SITUÉ DANS la commune cc.
            Ne renvoie JAMAIS le siège s'il est hors de cc (evite de placer l'usine
            du Sud au siege parisien). Si aucun etablissement n'est dans cc -> None
            -> on laisse le repli BAN geocoder l'adresse reelle."""
            cc = (cc or '').strip()
            for i in range(3):
                try:
                    r = _rq.get(SIR, params={'q': siren, 'code_commune': cc,
                                             'page': 1, 'per_page': 1}, timeout=15)
                    if r.status_code == 200:
                        res = (r.json().get('results') or [])
                        if not res:
                            return None, None, True
                        ent = res[0]
                        cands = list(ent.get('matching_etablissements') or [])
                        sg = ent.get('siege') or {}
                        if sg:
                            cands.append(sg)
                        # Ne garder qu'un etablissement DANS la commune cible
                        et = None
                        if cc:
                            for c in cands:
                                if str(c.get('code_commune') or '').strip() == cc:
                                    et = c; break
                        if et is None:
                            # aucun etablissement dans cette commune -> repli BAN (adresse)
                            return None, None, True
                        la, lo = et.get('latitude'), et.get('longitude')
                        if la is not None and lo is not None:
                            try:
                                return float(la), float(lo), True
                            except Exception:
                                return None, None, True
                        return None, None, True
                    if r.status_code == 429:
                        _t.sleep(1.2 * (i + 1)); continue
                except Exception:
                    pass
                _t.sleep(0.7 * (i + 1))
            return None, None, False

        def _ban(addr, cc):
            """(lat, lon, precision, ok) — precision ∈ exact|rue|approx."""
            for i in range(3):
                try:
                    r = _rq.get(f"{GEO}/search", params={'index': 'address', 'q': addr,
                                                         'citycode': cc or '', 'limit': 1}, timeout=15)
                    if r.status_code == 200:
                        f = r.json().get('features') or []
                        if not f:
                            return None, None, None, True
                        pr = f[0]['properties']; lon, lat = f[0]['geometry']['coordinates']
                        t = pr.get('type')
                        prec = 'exact' if t == 'housenumber' else ('rue' if t == 'street' else 'approx')
                        return lat, lon, prec, True
                    if r.status_code == 429:
                        _t.sleep(1.2 * (i + 1)); continue
                except Exception:
                    pass
                _t.sleep(0.6 * (i + 1))
            return None, None, None, False

        def _commune_centroid(cc):
            """(lat, lon, ok) centroïde de la commune INSEE — repli ultime (approx).
            Garantit que le site reste dans SA commune, jamais au siege parisien."""
            cc = (cc or '').strip()
            if not cc:
                return None, None, True
            for i in range(2):
                try:
                    r = _rq.get(f"https://geo.api.gouv.fr/communes/{cc}",
                                params={'fields': 'centre'}, timeout=15)
                    if r.status_code == 200:
                        c = ((r.json() or {}).get('centre') or {}).get('coordinates')
                        if c and len(c) == 2:
                            return float(c[1]), float(c[0]), True   # (lat, lon)
                        return None, None, True
                    if r.status_code in (429, 503):
                        _t.sleep(1.0 * (i + 1)); continue
                    return None, None, True
                except Exception:
                    pass
                _t.sleep(0.5 * (i + 1))
            return None, None, False

        try:
            while True:
                job = execute_query("SELECT status FROM scan_jobs WHERE id=%s", (job_id,), fetch_one=True)
                if not job or job.get('status') != 'running':
                    break
                batch = execute_query("""
                    SELECT id, adresse, code_commune, operateur_siren FROM industrial_prospects
                    WHERE COALESCE(geo2_tried,0)=0 LIMIT 30
                """, fetch_all=True) or []
                if not batch:
                    execute_query("UPDATE scan_jobs SET status='done', updated_at=CURRENT_TIMESTAMP WHERE id=%s", (job_id,))
                    break
                done = 0
                for p in batch:
                    lat = lon = None; source = 'none'; prec = None; ok = True
                    siren = (p.get('operateur_siren') or '').strip()
                    if siren:
                        la, lo, sok = _sirene_etab(siren, p.get('code_commune'))
                        if not sok:
                            ok = False
                        elif la is not None:
                            lat, lon, source, prec = la, lo, 'sirene', 'exact'
                    if lat is None and ok:
                        adr = (p.get('adresse') or '').strip()
                        if adr:
                            la, lo, bprec, bok = _ban(adr, p.get('code_commune'))
                            if not bok:
                                ok = False
                            elif la is not None:
                                lat, lon, source, prec = la, lo, 'ban', bprec
                    if lat is None and ok:
                        # Repli ultime : centroïde commune (jamais le siege hors commune)
                        la, lo, cok = _commune_centroid(p.get('code_commune'))
                        if not cok:
                            ok = False
                        elif la is not None:
                            lat, lon, source, prec = la, lo, 'commune', 'approx'
                    if not ok:
                        _t.sleep(1.5); continue  # throttle → réessayable au prochain run
                    execute_query(
                        "UPDATE industrial_prospects SET geo2_tried=1, geo_source=%s, geo_precision=%s, "
                        "lat=COALESCE(%s, lat), lon=COALESCE(%s, lon) WHERE id=%s",
                        (source, prec, lat, lon, p['id']))
                    if lat is not None:
                        done += 1
                    _t.sleep(0.12)  # paçage doux par site (SIRENE)
                execute_query("UPDATE scan_jobs SET total_injected=total_injected+%s, "
                              "updated_at=CURRENT_TIMESTAMP, claimed_at=CURRENT_TIMESTAMP WHERE id=%s",
                              (done, job_id))
                _t.sleep(1)
        except Exception as _e:
            print(f"❌ [GEO2 WORKER] {_e}")
        finally:
            _GEO2_STATE['running'] = False

    def _start_geocode2_worker(job_id):
        import threading
        if not _claim_job(job_id):
            return False
        with _FRANCE_LOCK:
            if _GEO2_STATE.get('running'):
                return False
            _GEO2_STATE['running'] = True
        threading.Thread(target=_geocode2_worker, args=(job_id,), daemon=True).start()
        return True

    @app.route('/crm/industriel')
    def crm_industriel_page():
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return redirect('/auth/login')
        return render_template('crm_industriel.html', is_admin=is_admin)

    @app.route('/crm/offre')
    def crm_offre_page():
        """Page client : choisir un territoire et s'abonner (Stripe)."""
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return redirect('/auth/login?next=/crm/offre')
        stripe_pub = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
        return render_template('crm_offre.html', stripe_pub=stripe_pub)

    @app.route('/crm/gisement')
    def crm_gisement_page():
        """Vue admin dédiée : tout le gisement en vignettes riches (paginé serveur)."""
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return redirect('/auth/login?next=/crm/gisement')
        # Accessible aux clients : les donnees sont gatees a leurs departements payes.
        return render_template('crm_gisement.html', is_admin=is_admin)

    @app.route('/crm/carte')
    def crm_carte_page():
        """Carte nationale interactive du gisement industriel (admin)."""
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return redirect('/auth/login?next=/crm/carte')
        # Accessible aux clients : carte-data est gatee a leurs departements payes.
        return render_template('crm_carte.html', is_admin=is_admin)

    @app.route('/demo-prospection')
    def demo_prospection_page():
        """Page de démo publique (RGPD-safe) : prospects réels + potentiel, contacts masqués."""
        # (société, commune, dept, conso_mwh, domaine) — contacts masqués pour le public
        data = [
            ("FARMOR", "Châteaulin", "29", 19811, "farmor.fr"),
            ("APTAR STELMI", "Granville", "50", 19763, "aptar.com"),
            ("SANOFI WINTHROP INDUSTRIE", "Val-de-Reuil", "27", 19746, "sanofi.com"),
            ("FRONERI FRANCE", "Plouédern", "29", 19682, "froneri.com"),
            ("OLGA", "Châteaubourg", "35", 19619, "avec-olga.com"),
            ("HEIDELBERG MATERIALS", "Maubeuge", "59", 19615, "heidelbergmaterials.com"),
            ("MELTBLO FRANCE", "Brognard", "25", 799, "meltblofrance.com"),
            ("BAUMIT", "Châteaurenard", "13", 798, "baumit.com"),
            ("EURO PLV", "Saint-Victurnien", "87", 798, "europlv.com"),
        ]
        def _tarif(c):
            return 0.20 if c < 500 else 0.18 if c < 2000 else 0.16 if c < 20000 else 0.13 if c < 70000 else 0.11 if c < 150000 else 0.095
        def _sp(n): return f"{n:,.0f}".replace(",", " ")
        prod = 1200.0
        rows = []
        tot_conso = tot_kwc = tot_eco = 0.0
        for soc, com, dep, conso, dom in data:
            kwc = round(0.40 * conso * 1000 / prod)
            eco = 0.40 * conso * 1000 * _tarif(conso)
            tot_conso += conso; tot_kwc += kwc; tot_eco += eco
            rows.append({'societe': soc, 'commune': com, 'dept': dep, 'conso': _sp(conso),
                         'pot': (f"{kwc/1000:.1f} MWc" if kwc >= 1000 else f"{kwc} kWc"),
                         'eco': _sp(eco), 'email': f"•••@{dom}"})
        return render_template('demo_prospection.html', rows=rows, nb=len(rows),
                               conso_gwh=f"{tot_conso/1000:.1f}", pot_mwc=f"{tot_kwc/1000:.1f}",
                               eco_total=_sp(tot_eco))

    @app.route('/crm/rapport')
    def crm_rapport_page():
        """Page RETIREE : exposait un export CSV du gisement (donnee proprietaire).
        Redirige vers la carte. Pour reactiver : restaurer le render_template et
        re-activer l'export industriel_rapport_csv()."""
        return redirect('/crm/carte')

    @app.route('/api/industriel/scan-inject', methods=['POST'])
    def industriel_scan_inject():
        """Lance un scan industriel et INJECTE les résultats dans le CRM dédié."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            data = request.get_json(silent=True) or {}
            dept = str(data.get('dept') or '').strip()
            code_commune = str(data.get('code_commune') or '').strip()
            secteur = (data.get('secteur') or 'INDUSTRIE').strip().upper()
            # Seuil exprimé en kWc d'autoconso (converti en MWh) : pour viser ≥ N kWc
            # avec un dimensionnement à ~35% de la conso (productible moyen ~1150),
            # il faut conso ≈ N × 1150 / 350 ≈ N × 3.3 MWh/an.
            min_kwc = data.get('min_kwc')
            if min_kwc is not None and str(min_kwc) != '':
                min_mwh = round(float(min_kwc) * 3.3, 1)
            else:
                min_mwh = float(data.get('min_mwh') or 330)
            limit = min(int(data.get('limit') or 100), 1000)
            annee = data.get('annee')
            if not dept and not code_commune:
                return jsonify({'success': False, 'error': 'dept ou code_commune requis'}), 400
            # Industriel : on saute le foncier MAJIC (peu pertinent), on garde SIRENE.
            res = _run_industrial_scan(dept, code_commune, secteur, min_mwh, limit, annee,
                                       with_foncier=False)
            try:
                from autoconsommation import diagnostic_autoconso_rapide
            except Exception:
                diagnostic_autoconso_rapide = None
            injected, skipped = 0, 0
            for p in res.get('prospects', []):
                adresse = (p.get('adresse') or '').strip()
                cc = p.get('code_commune') or ''
                if not adresse:
                    skipped += 1; continue
                existing = execute_query(
                    "SELECT id FROM industrial_prospects WHERE user_id = %s AND code_commune = %s AND adresse = %s",
                    (str(user_id), cc, adresse), fetch_one=True)
                if existing:
                    skipped += 1; continue
                ops = p.get('operateurs_sirene') or []
                op = ops[0] if ops else {}
                diag = {}
                if diagnostic_autoconso_rapide:
                    try:
                        diag = diagnostic_autoconso_rapide(p.get('conso_mwh'), secteur) or {}
                    except Exception:
                        diag = {}
                dj = {'operateurs_sirene': ops, 'naf2': p.get('naf2'),
                      'parcelle': p.get('parcelle'),
                      'proprietaire_foncier': p.get('proprietaire_foncier'),
                      'annee': p.get('annee'), 'diagnostic_autoconso': diag}
                execute_query("""
                    INSERT INTO industrial_prospects
                        (user_id, commune, code_commune, adresse, conso_mwh, naf2, secteur,
                         operateur_nom, operateur_siren, operateur_naf, operateur_effectif,
                         proprietaire_foncier, parcelle, kwc_reco, economie_an_eur,
                         statut, data_json)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    str(user_id), p.get('commune'), cc, adresse, p.get('conso_mwh'),
                    p.get('naf2'), secteur, op.get('nom'), op.get('siren'), op.get('naf'),
                    op.get('effectif'), p.get('proprietaire_foncier'), p.get('parcelle'),
                    diag.get('kwc_reco'), diag.get('economie_an_eur'),
                    'nouveau', json.dumps(dj, ensure_ascii=False),
                ))
                injected += 1
            return jsonify({'success': True, 'injected': injected, 'skipped': skipped,
                            'sites_scannes': res.get('sites_enedis', 0),
                            'seuil_mwh': min_mwh})
        except Exception as e:
            print(f"❌ [INDUSTRIEL INJECT] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/scan-france/start', methods=['POST'])
    def scan_france_start():
        """Démarre le worker autonome qui scanne tous les départements (admin)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table(); _ensure_scan_jobs_table()
            data = request.get_json(silent=True) or {}
            min_kwc = float(data.get('min_kwc') or 100)
            limit = min(int(data.get('limit') or 1000), 1000)
            existing = execute_query(
                "SELECT id FROM scan_jobs WHERE type='france' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Un scan France est déjà en cours',
                                'job_id': existing['id']}), 409
            depts = _all_depts()
            job = execute_query("""
                INSERT INTO scan_jobs (type, status, user_id, params, depts_todo, depts_done)
                VALUES ('france', 'running', %s, %s, %s, '[]') RETURNING id
            """, (str(user_id), json.dumps({'min_kwc': min_kwc, 'limit': limit}),
                  json.dumps(depts)), fetch_one=True)
            _start_france_worker(job['id'])
            return jsonify({'success': True, 'job_id': job['id'], 'total_depts': len(depts)})
        except Exception as e:
            print(f"❌ [SCAN FRANCE START] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/scan-france/status', methods=['GET'])
    def scan_france_status():
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_scan_jobs_table()
            job = execute_query(
                "SELECT * FROM scan_jobs WHERE type='france' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if not job:
                return jsonify({'success': True, 'job': None})
            # Watchdog : job 'running' mais aucun worker actif (thread mort / restart)
            # -> on relance (self-heal, déclenché par n'importe quel poll de statut).
            if job.get('status') == 'running' and not _FRANCE_STATE.get('running'):
                try:
                    _start_france_worker(job['id'])
                except Exception:
                    pass
            todo = json.loads(job.get('depts_todo') or '[]')
            done = json.loads(job.get('depts_done') or '[]')
            return jsonify({'success': True, 'job': {
                'status': job.get('status'), 'current_dept': job.get('current_dept'),
                'faits': len(done), 'restants': len(todo), 'total_depts': len(done) + len(todo),
                'total_injected': job.get('total_injected'), 'total_skipped': job.get('total_skipped'),
                'updated_at': str(job.get('updated_at')),
            }})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/scan-france/stop', methods=['POST'])
    def scan_france_stop():
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_scan_jobs_table()
            execute_query("UPDATE scan_jobs SET status='stopped', updated_at=CURRENT_TIMESTAMP "
                          "WHERE type='france' AND status='running'")
            _FRANCE_STATE['running'] = False
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/clear', methods=['POST'])
    def industriel_clear():
        """Remet à zéro le CRM industriel (admin = tout ; user = ses prospects).
        Arrête aussi tout scan France en cours."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table(); _ensure_scan_jobs_table()
            # stoppe un éventuel scan en cours
            execute_query("UPDATE scan_jobs SET status='stopped' WHERE type='france' AND status='running'")
            _FRANCE_STATE['running'] = False
            if is_admin:
                n = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects", fetch_one=True) or {}
                execute_query("DELETE FROM industrial_prospects")
            else:
                n = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects WHERE user_id = %s",
                                  (str(user_id),), fetch_one=True) or {}
                execute_query("DELETE FROM industrial_prospects WHERE user_id = %s", (str(user_id),))
            return jsonify({'success': True, 'supprimes': n.get('n', 0)})
        except Exception as e:
            print(f"❌ [INDUSTRIEL CLEAR] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/resolve-operators/start', methods=['POST'])
    def resolve_operators_start():
        """Lance le worker autonome qui récupère les opérateurs manquants (admin)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table(); _ensure_scan_jobs_table()
            existing = execute_query(
                "SELECT id FROM scan_jobs WHERE type='operators' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Une résolution est déjà en cours',
                                'job_id': existing['id']}), 409
            # réinitialise les tentatives sur les prospects encore sans opérateur
            execute_query("UPDATE industrial_prospects SET operateur_tried=0 WHERE operateur_nom IS NULL")
            n = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects "
                              "WHERE operateur_nom IS NULL AND naf2 IS NOT NULL AND naf2 <> ''",
                              fetch_one=True) or {}
            job = execute_query("""
                INSERT INTO scan_jobs (type, status, user_id, params, depts_todo, depts_done)
                VALUES ('operators', 'running', %s, '{}', '[]', '[]') RETURNING id
            """, (str(user_id),), fetch_one=True)
            _start_operators_worker(job['id'])
            return jsonify({'success': True, 'job_id': job['id'], 'a_resoudre': n.get('n', 0)})
        except Exception as e:
            print(f"❌ [RESOLVE OP START] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/resolve-operators/status', methods=['GET'])
    def resolve_operators_status():
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_scan_jobs_table()
            job = execute_query(
                "SELECT * FROM scan_jobs WHERE type='operators' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if not job:
                return jsonify({'success': True, 'job': None})
            if job.get('status') == 'running' and not _OP_STATE.get('running'):
                try:
                    _start_operators_worker(job['id'])  # watchdog self-heal
                except Exception:
                    pass
            restants = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects "
                                     "WHERE operateur_nom IS NULL AND COALESCE(operateur_tried,0)=0 "
                                     "AND naf2 IS NOT NULL AND naf2 <> ''", fetch_one=True) or {}
            return jsonify({'success': True, 'job': {
                'status': job.get('status'), 'resolus': job.get('total_injected'),
                'restants': restants.get('n', 0), 'updated_at': str(job.get('updated_at'))}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/resolve-operators/stop', methods=['POST'])
    def resolve_operators_stop():
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_scan_jobs_table()
            execute_query("UPDATE scan_jobs SET status='stopped' WHERE type='operators' AND status='running'")
            _OP_STATE['running'] = False
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def _ensure_territories_table():
        """Table des droits territoriaux (qui a payé quoi)."""
        try:
            execute_query("""
                CREATE TABLE IF NOT EXISTS user_territories (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    territory_type TEXT NOT NULL,
                    territory_code TEXT NOT NULL,
                    plan TEXT,
                    exclusive INTEGER DEFAULT 0,
                    granted_by TEXT,
                    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            for ddl in (
                "ALTER TABLE user_territories ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT",
                "ALTER TABLE user_territories ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT",
            ):
                try:
                    execute_query(ddl)
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ [TERRITORIES] ensure table: {e}")

    def _expand_territory(ttype, code):
        """(type, code) → liste de départements pré-chargeables, ou '*' pour national."""
        ttype = (ttype or '').lower()
        code = (code or '').strip().upper()
        if ttype == 'national':
            return '*'
        if ttype == 'region':
            return list(REGION_DEPTS.get(code, []))
        if ttype == 'dept':
            return [code.zfill(2) if code.isdigit() else code]
        return []

    def _resolve_user_id_by_email(email):
        """email → user_id (auth db SQLite). None si introuvable."""
        try:
            from auth_database import get_auth_db
            conn = get_auth_db(); cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            row = cur.fetchone(); conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"⚠️ [TERRITORIES] resolve email: {e}")
            return None

    def _email_by_user_id(user_id):
        """user_id → email (auth db SQLite). None si introuvable."""
        try:
            from auth_database import get_auth_db
            conn = get_auth_db(); cur = conn.cursor()
            cur.execute("SELECT email FROM users WHERE id = ?", (str(user_id),))
            row = cur.fetchone(); conn.close()
            return row[0] if row else None
        except Exception:
            return None

    def _grant_territory(target_id, ttype, code, plan=None, months=0, granted_by=None,
                         stripe_subscription_id=None, stripe_customer_id=None, do_preload=False):
        """Enregistre un droit territorial et, en option, pré-charge le CRM.
        Retourne {preload, preload_total}."""
        _ensure_territories_table()
        months = int(months or 0)
        expires_sql = "CURRENT_TIMESTAMP + (%s || ' months')::interval" if months > 0 else "NULL"
        params = [str(target_id), ttype, code or 'FR', plan,
                  str(granted_by) if granted_by is not None else None,
                  stripe_subscription_id, stripe_customer_id]
        if months > 0:
            params.append(str(months))
        execute_query(
            "INSERT INTO user_territories "
            "(user_id, territory_type, territory_code, plan, granted_by, "
            " stripe_subscription_id, stripe_customer_id, expires_at) "
            f"VALUES (%s, %s, %s, %s, %s, %s, %s, {expires_sql})", tuple(params))
        result = {'preload': None, 'preload_total': 0}
        if do_preload:
            depts = _expand_territory(ttype, code)
            if depts == '*':
                depts = [r['d'] for r in (execute_query(
                    "SELECT DISTINCT LEFT(code_commune,2) AS d FROM industrial_prospects "
                    "WHERE code_commune IS NOT NULL", fetch_all=True) or [])]
            pre = []
            for d in depts:
                try:
                    pre.append({'dept': d, **_precharger_dept_into(d, target_id)})
                except Exception as e:
                    pre.append({'dept': d, 'error': str(e)})
            result['preload'] = pre
            result['preload_total'] = sum(x.get('copied', 0) for x in pre)
        return result

    def _user_entitled_depts(user_id):
        """Ensemble des départements auxquels l'utilisateur a droit (droits actifs).
        Retourne '*' si droit national, sinon un set de codes département."""
        _ensure_territories_table()
        rows = execute_query(
            "SELECT territory_type, territory_code FROM user_territories "
            "WHERE user_id = %s AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)",
            (str(user_id),), fetch_all=True) or []
        depts = set()
        for r in rows:
            exp = _expand_territory(r.get('territory_type'), r.get('territory_code'))
            if exp == '*':
                return '*'
            depts.update(exp)
        return depts

    def _industriel_gating_clause(uid, is_admin):
        """Restreint le gisement (industrial_prospects) aux DROITS du user.
        Admin -> aucune restriction. Non-admin -> uniquement ses departements
        payes (LEFT(code_commune,2)), ou RIEN s'il n'a aucun droit territorial.
        Retourne (clause_sql, params) a concatener a la requete."""
        if is_admin:
            return "", []
        ent = _user_entitled_depts(uid)
        if ent == '*':
            return "", []
        depts = sorted(ent)
        if not depts:
            return " AND 1=0", []   # aucun droit -> aucun site
        ph = ",".join(["%s"] * len(depts))
        return (f" AND LEFT(code_commune, 2) IN ({ph})", list(depts))

    @app.route('/api/industriel/territoire/grant', methods=['POST'])
    def territoire_grant():
        """Attribue un territoire à un utilisateur (admin). Optionnellement pré-charge
        dans la foulée. Body: {email, type(dept|region|national), code, plan?, months?, preload?}."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            data = request.get_json(silent=True) or {}
            email = (data.get('email') or '').strip()
            ttype = (data.get('type') or 'dept').lower()
            code = (data.get('code') or '').strip().upper()
            plan = data.get('plan')
            preload = bool(data.get('preload'))
            try:
                months = int(data.get('months') or 0)
            except Exception:
                months = 0
            if not email or ttype not in ('dept', 'region', 'national'):
                return jsonify({'success': False, 'error': 'email + type valides requis'}), 400
            if ttype != 'national' and not code:
                return jsonify({'success': False, 'error': 'code (département/région) requis'}), 400
            target_id = _resolve_user_id_by_email(email)
            if target_id is None:
                return jsonify({'success': False, 'error': f'Utilisateur {email} introuvable'}), 404
            g = _grant_territory(target_id, ttype, code, plan=plan, months=months,
                                 granted_by=caller_id, do_preload=preload)
            result = {'success': True, 'email': email, 'user_id': target_id,
                      'type': ttype, 'code': code, 'plan': plan, 'months': months or None}
            if preload:
                result['preload'] = g.get('preload')
                result['preload_total'] = g.get('preload_total')
            return jsonify(result)
        except Exception as e:
            print(f"❌ [TERRITOIRE GRANT] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/territoire/revoke', methods=['POST'])
    def territoire_revoke():
        """Révoque un territoire (admin). Body: {email, type, code} ou {id}."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            data = request.get_json(silent=True) or {}
            _ensure_territories_table()
            if data.get('id'):
                execute_query("DELETE FROM user_territories WHERE id = %s", (int(data['id']),))
                return jsonify({'success': True})
            email = (data.get('email') or '').strip()
            target_id = _resolve_user_id_by_email(email)
            if target_id is None:
                return jsonify({'success': False, 'error': 'Utilisateur introuvable'}), 404
            execute_query(
                "DELETE FROM user_territories WHERE user_id = %s AND territory_type = %s AND territory_code = %s",
                (str(target_id), (data.get('type') or '').lower(), (data.get('code') or '').strip().upper()))
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/territoire/list', methods=['GET'])
    def territoire_list():
        """Liste les droits. Admin: tous (ou ?email=). User: les siens."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if caller_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_territories_table()
            if is_admin:
                email = (request.args.get('email') or '').strip()
                if email:
                    tid = _resolve_user_id_by_email(email)
                    rows = execute_query("SELECT * FROM user_territories WHERE user_id = %s ORDER BY granted_at DESC",
                                         (str(tid),), fetch_all=True) or []
                else:
                    rows = execute_query("SELECT * FROM user_territories ORDER BY granted_at DESC LIMIT 500",
                                         fetch_all=True) or []
            else:
                rows = execute_query("SELECT * FROM user_territories WHERE user_id = %s ORDER BY granted_at DESC",
                                     (str(caller_id),), fetch_all=True) or []
            # Attache l'email (affichage) en un seul aller-retour auth db
            try:
                from auth_database import get_auth_db
                conn = get_auth_db(); cur = conn.cursor()
                emap = {}
                for uid in {str(r.get('user_id')) for r in rows}:
                    cur.execute("SELECT email FROM users WHERE id = ?", (uid,))
                    er = cur.fetchone()
                    if er:
                        emap[uid] = er[0]
                conn.close()
            except Exception:
                emap = {}
            for r in rows:
                if r.get('territory_type') == 'region':
                    r['territory_nom'] = REGION_NOMS.get((r.get('territory_code') or '').upper())
                r['user_email'] = emap.get(str(r.get('user_id')))
            return jsonify({'success': True, 'territoires': rows})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/territoire/mine', methods=['GET'])
    def territoire_mine():
        """Départements auxquels l'utilisateur courant a droit."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if caller_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            ent = _user_entitled_depts(caller_id)
            return jsonify({'success': True, 'national': ent == '*',
                            'depts': sorted(ent) if ent != '*' else 'all', 'admin': is_admin})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    def _ensure_prospect_proprio_columns():
        """Garantit les colonnes proprietaire_* sur agriweb_prospects (présentes en
        prod mais pas dans le schéma versionné)."""
        for ddl in (
            "ALTER TABLE agriweb_prospects ADD COLUMN IF NOT EXISTS proprietaire_siren TEXT",
            "ALTER TABLE agriweb_prospects ADD COLUMN IF NOT EXISTS proprietaire_denomination TEXT",
            "ALTER TABLE agriweb_prospects ADD COLUMN IF NOT EXISTS proprietaire_forme_juridique TEXT",
        ):
            try:
                execute_query(ddl)
            except Exception:
                pass

    def _precharger_dept_into(dept, target_id, limit=5000):
        """Copie le gisement maître d'un département dans le CRM d'un utilisateur,
        en vignettes complètes. Idempotent (dédoublonnage + backfill lat/lon).
        Retourne {copied, updated, skipped, total_gisement}."""
        dept = str(dept).strip().upper()
        try:
            limit = max(1, min(int(limit), 20000))
        except Exception:
            limit = 5000
        _ensure_industrial_table()
        _ensure_prospect_proprio_columns()
        rows = execute_query(
            "SELECT * FROM industrial_prospects WHERE LEFT(code_commune, 2) = %s "
            "AND adresse IS NOT NULL AND adresse <> '' "
            "ORDER BY conso_mwh DESC NULLS LAST LIMIT %s",
            (dept, limit), fetch_all=True) or []
        if not rows:
            return {'copied': 0, 'updated': 0, 'skipped': 0, 'total_gisement': 0}
        existing = execute_query(
            "SELECT id, commune, adresse, latitude FROM agriweb_prospects "
            "WHERE user_id = %s AND type = 'industriel'",
            (str(target_id),), fetch_all=True) or []
        seen = {((e.get('commune') or '').strip().lower(), (e.get('adresse') or '').strip().lower()):
                {'id': e.get('id'), 'lat': e.get('latitude')} for e in existing}
        copied, skipped, updated = 0, 0, 0
        for r in rows:
            commune = r.get('commune') or ''
            adresse = r.get('adresse') or ''
            key = (commune.strip().lower(), adresse.strip().lower())
            if key in seen:
                ex = seen[key]
                if ex.get('lat') is None and r.get('lat') is not None:
                    try:
                        execute_query(
                            "UPDATE agriweb_prospects SET latitude=%s, longitude=%s WHERE id=%s",
                            (r.get('lat'), r.get('lon'), ex['id']))
                        ex['lat'] = r.get('lat'); updated += 1
                    except Exception:
                        skipped += 1
                else:
                    skipped += 1
                continue
            seen[key] = {'id': None, 'lat': r.get('lat')}
            try:
                dj = json.loads(r.get('data_json') or '{}')
            except Exception:
                dj = {}
            dj['source'] = 'industriel'
            dj['enedis_match'] = {'consommation_mwh': r.get('conso_mwh'),
                                  'secteur': r.get('secteur'), 'annee': dj.get('annee')}
            try:
                execute_query('''
                    INSERT INTO agriweb_prospects
                        (type, commune, departement, adresse, latitude, longitude,
                         nom_prospect, proprietaire_siren, proprietaire_denomination, siret,
                         statut, priorite, data_json, user_id)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ''', (
                    'industriel', commune, dept, adresse, r.get('lat'), r.get('lon'),
                    r.get('operateur_nom'), r.get('operateur_siren'), r.get('operateur_nom'),
                    r.get('operateur_siren'), 'nouveau', 'haute',
                    json.dumps(dj, ensure_ascii=False), str(target_id),
                ))
                copied += 1
            except Exception as e_ins:
                print(f"⚠️ [PRECHARGER] insert échoué {commune}/{adresse}: {e_ins}")
                skipped += 1
        print(f"✅ [PRECHARGER] dept={dept} → user {target_id}: {copied} copiés, "
              f"{updated} géoloc. complétés, {skipped} ignorés")
        return {'copied': copied, 'updated': updated, 'skipped': skipped, 'total_gisement': len(rows)}

    @app.route('/api/industriel/precharger', methods=['POST'])
    def industriel_precharger():
        """Pré-charge les prospects industriels d'un département dans le CRM.
        Réservé à l'offre : un non-admin ne peut charger que les départements
        couverts par son abonnement (droits territoriaux). L'admin n'est pas bridé
        et peut cibler un autre utilisateur (email). Body: {dept, email?, limit?}."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if caller_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            data = request.get_json(silent=True) or {}
            dept = str(data.get('dept') or '').strip().upper()
            if not dept:
                return jsonify({'success': False, 'error': 'Département requis'}), 400
            limit = data.get('limit') or 5000

            # Cible : un admin peut pré-charger dans le CRM d'un autre user (par email)
            target_id = caller_id
            target_email = (data.get('email') or '').strip()
            if target_email:
                if not is_admin:
                    return jsonify({'success': False, 'error': 'Admin requis pour cibler un autre utilisateur'}), 403
                target_id = _resolve_user_id_by_email(target_email)
                if target_id is None:
                    return jsonify({'success': False, 'error': f'Utilisateur {target_email} introuvable'}), 404

            # Gating : un non-admin chargeant dans son propre CRM doit avoir le droit
            # territorial sur ce département.
            if not is_admin:
                ent = _user_entitled_depts(caller_id)
                if ent != '*' and dept not in ent:
                    return jsonify({'success': False, 'error': 'territoire_non_couvert',
                                    'message': f"Le département {dept} n'est pas couvert par votre abonnement.",
                                    'depts_autorises': sorted(ent)}), 403

            res = _precharger_dept_into(dept, target_id, limit)
            return jsonify({'success': True, 'dept': dept, 'target_user_id': target_id, **res})
        except Exception as e:
            print(f"❌ [PRECHARGER] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    def _ajouter_site_au_crm(r, target_id):
        """Copie UN site du gisement (ligne industrial_prospects) dans le CRM d'un
        utilisateur, en vignette complète. Idempotent. Retourne (prospect_id, created)."""
        _ensure_prospect_proprio_columns()
        commune = r.get('commune') or ''
        adresse = r.get('adresse') or ''
        dept = (r.get('code_commune') or '')[:2]
        existing = execute_query(
            "SELECT id, latitude FROM agriweb_prospects WHERE user_id = %s AND type = 'industriel' "
            "AND LOWER(COALESCE(commune,'')) = %s AND LOWER(COALESCE(adresse,'')) = %s LIMIT 1",
            (str(target_id), commune.strip().lower(), adresse.strip().lower()), fetch_one=True)
        if existing:
            if existing.get('latitude') is None and r.get('lat') is not None:
                try:
                    execute_query("UPDATE agriweb_prospects SET latitude=%s, longitude=%s WHERE id=%s",
                                  (r.get('lat'), r.get('lon'), existing['id']))
                except Exception:
                    pass
            return existing['id'], False
        try:
            dj = json.loads(r.get('data_json') or '{}')
        except Exception:
            dj = {}
        dj['source'] = 'industriel'
        dj['enedis_match'] = {'consommation_mwh': r.get('conso_mwh'),
                              'secteur': r.get('secteur'), 'annee': dj.get('annee')}
        res = execute_query('''
            INSERT INTO agriweb_prospects
                (type, commune, departement, adresse, latitude, longitude,
                 nom_prospect, proprietaire_siren, proprietaire_denomination, siret,
                 statut, priorite, data_json, user_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        ''', (
            'industriel', commune, dept, adresse, r.get('lat'), r.get('lon'),
            r.get('operateur_nom'), r.get('operateur_siren'), r.get('operateur_nom'),
            r.get('operateur_siren'), 'nouveau', 'haute',
            json.dumps(dj, ensure_ascii=False), str(target_id),
        ), fetch_one=True)
        return (res.get('id') if res else None), True

    @app.route('/api/industriel/ajouter-au-crm', methods=['POST'])
    def industriel_ajouter_au_crm():
        """Importe UN site du gisement dans le CRM de l'utilisateur courant
        (clic « Ajouter » depuis la carte/les vignettes). Body: {id}."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if caller_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            data = request.get_json(silent=True) or {}
            pid = data.get('id')
            if not pid:
                return jsonify({'success': False, 'error': 'id requis'}), 400
            # Cible : un admin peut ajouter dans le CRM d'un autre user (par email)
            target_id = caller_id
            target_email = (data.get('email') or '').strip()
            if target_email:
                if not is_admin:
                    return jsonify({'success': False, 'error': 'Admin requis pour cibler un autre utilisateur'}), 403
                target_id = _resolve_user_id_by_email(target_email)
                if target_id is None:
                    return jsonify({'success': False, 'error': f'Utilisateur {target_email} introuvable'}), 404
            _ensure_industrial_table()
            r = execute_query("SELECT * FROM industrial_prospects WHERE id = %s", (int(pid),), fetch_one=True)
            if not r:
                return jsonify({'success': False, 'error': 'Site introuvable'}), 404
            # Gating territorial pour les non-admins ajoutant dans leur propre CRM
            if not is_admin:
                dept = (r.get('code_commune') or '')[:2]
                ent = _user_entitled_depts(caller_id)
                if ent != '*' and dept not in ent:
                    return jsonify({'success': False, 'error': 'territoire_non_couvert',
                                    'message': f"Le département {dept} n'est pas couvert par votre abonnement."}), 403
            prospect_id, created = _ajouter_site_au_crm(r, target_id)
            return jsonify({'success': True, 'prospect_id': prospect_id, 'created': created,
                            'commune': r.get('commune'), 'operateur': r.get('operateur_nom')})
        except Exception as e:
            print(f"❌ [AJOUTER CRM] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/checkout', methods=['POST'])
    def industriel_checkout():
        """Crée une session Stripe Checkout en mode ABONNEMENT pour un territoire.
        Le territoire choisi voyage dans la metadata → le webhook accorde le droit
        et pré-charge le CRM après paiement. Body: {plan(solo|pro), code}."""
        try:
            caller_id, is_admin = get_current_crm_user()
            if caller_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            data = request.get_json(silent=True) or {}
            plan = (data.get('plan') or '').lower()
            if plan == 'enterprise':
                return jsonify({'success': False,
                                'error': 'Le plan Entreprise (national) est sur devis — contactez-nous.'}), 400
            if plan not in INDUSTRIEL_PLANS:
                return jsonify({'success': False, 'error': 'Plan invalide'}), 400
            cfg = INDUSTRIEL_PLANS[plan]
            ttype = cfg['territory']
            code = (data.get('code') or '').strip().upper()
            if ttype == 'dept':
                code = code.zfill(2) if code.isdigit() else code
                if not code:
                    return jsonify({'success': False, 'error': 'Département requis'}), 400
            elif ttype == 'region':
                if code not in REGION_DEPTS:
                    return jsonify({'success': False, 'error': 'Région invalide'}), 400

            try:
                import stripe as _stripe
            except Exception:
                return jsonify({'success': False, 'error': 'Librairie Stripe absente'}), 500
            _stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
            if not _stripe.api_key:
                return jsonify({'success': False, 'error': 'Stripe non configuré (clé manquante)'}), 500

            email = _email_by_user_id(caller_id) or (data.get('email') or '').strip() or None
            meta = {'user_id': str(caller_id), 'user_email': email or '',
                    'territory_type': ttype, 'territory_code': code, 'plan': plan}
            root = request.url_root
            try:
                cs = _stripe.checkout.Session.create(
                    mode='subscription',
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {'name': cfg['name'], 'description': cfg['desc']},
                            'unit_amount': cfg['amount'],
                            'recurring': {'interval': 'month'},
                        },
                        'quantity': 1,
                    }],
                    client_reference_id=str(caller_id),
                    customer_email=email,
                    metadata=meta,
                    subscription_data={'metadata': meta},
                    success_url=root + 'crm/industriel?abonnement=ok',
                    cancel_url=root + 'crm/offre?annule=1',
                )
            except _stripe.error.AuthenticationError:
                return jsonify({'success': False, 'error': 'Clés Stripe invalides'}), 500
            except _stripe.error.StripeError as e:
                return jsonify({'success': False, 'error': f'Stripe: {e}'}), 500
            return jsonify({'success': True, 'url': cs.url})
        except Exception as e:
            print(f"❌ [CHECKOUT] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/stripe-webhook', methods=['POST'])
    def industriel_stripe_webhook():
        """Webhook Stripe dédié à l'offre territoire. Sur paiement abouti :
        accorde le droit + pré-charge le CRM. Sur résiliation : révoque."""
        try:
            import stripe as _stripe
        except Exception:
            return jsonify({'error': 'stripe absent'}), 500
        _stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        secret = os.environ.get('STRIPE_INDUSTRIEL_WEBHOOK_SECRET') or os.environ.get('STRIPE_WEBHOOK_SECRET')
        payload = request.get_data(as_text=True)
        sig = request.headers.get('Stripe-Signature')
        try:
            event = _stripe.Webhook.construct_event(payload, sig, secret)
        except Exception as e:
            print(f"⚠️ [STRIPE WEBHOOK] signature invalide: {e}")
            return jsonify({'error': 'signature'}), 400
        try:
            etype = event['type']
            obj = event['data']['object']
            if etype == 'checkout.session.completed':
                meta = obj.get('metadata') or {}
                target_id = meta.get('user_id') or obj.get('client_reference_id')
                ttype = meta.get('territory_type')
                code = meta.get('territory_code')
                plan = meta.get('plan')
                sub = obj.get('subscription')
                cust = obj.get('customer')
                if target_id and ttype:
                    g = _grant_territory(target_id, ttype, code, plan=plan, granted_by='stripe',
                                         stripe_subscription_id=sub, stripe_customer_id=cust,
                                         do_preload=True)
                    print(f"✅ [STRIPE] abonnement {plan} {ttype}/{code} → user {target_id}, "
                          f"{g.get('preload_total')} prospects pré-chargés")
            elif etype == 'customer.subscription.deleted':
                sub_id = obj.get('id')
                if sub_id:
                    execute_query("DELETE FROM user_territories WHERE stripe_subscription_id = %s", (sub_id,))
                    print(f"🚫 [STRIPE] abonnement {sub_id} résilié → droits révoqués")
        except Exception as e:
            print(f"❌ [STRIPE WEBHOOK] traitement: {e}")
        return jsonify({'received': True})

    @app.route('/api/industriel/geocode/start', methods=['POST'])
    def geocode_start():
        """Lance le worker autonome de géocodage du gisement (lat/lon). Admin."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table(); _ensure_scan_jobs_table()
            existing = execute_query(
                "SELECT id FROM scan_jobs WHERE type='geocode' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Un géocodage est déjà en cours',
                                'job_id': existing['id']}), 409
            execute_query("UPDATE industrial_prospects SET geo_tried=0 WHERE lat IS NULL")
            n = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects "
                              "WHERE lat IS NULL AND adresse IS NOT NULL AND adresse <> ''",
                              fetch_one=True) or {}
            job = execute_query("""
                INSERT INTO scan_jobs (type, status, user_id, params, depts_todo, depts_done)
                VALUES ('geocode', 'running', %s, '{}', '[]', '[]') RETURNING id
            """, (str(user_id),), fetch_one=True)
            _start_geocode_worker(job['id'])
            return jsonify({'success': True, 'job_id': job['id'], 'a_geocoder': n.get('n', 0)})
        except Exception as e:
            print(f"❌ [GEOCODE START] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/geocode/status', methods=['GET'])
    def geocode_status():
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_scan_jobs_table()
            job = execute_query("SELECT * FROM scan_jobs WHERE type='geocode' ORDER BY id DESC LIMIT 1",
                                fetch_one=True)
            if not job:
                return jsonify({'success': True, 'job': None})
            if job.get('status') == 'running' and not _GEO_STATE.get('running'):
                try:
                    _start_geocode_worker(job['id'])  # watchdog
                except Exception:
                    pass
            restants = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects "
                                     "WHERE lat IS NULL AND COALESCE(geo_tried,0)=0 "
                                     "AND adresse IS NOT NULL AND adresse <> ''", fetch_one=True) or {}
            avec = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects WHERE lat IS NOT NULL",
                                 fetch_one=True) or {}
            return jsonify({'success': True, 'job': {
                'status': job.get('status'), 'geocodes': avec.get('n', 0),
                'restants': restants.get('n', 0), 'updated_at': str(job.get('updated_at'))}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/geocode/stop', methods=['POST'])
    def geocode_stop():
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_scan_jobs_table()
            execute_query("UPDATE scan_jobs SET status='stopped' WHERE type='geocode' AND status='running'")
            _GEO_STATE['running'] = False
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/geocode2/start', methods=['POST'])
    def geocode2_start():
        """Re-géocodage haute précision (SIREN→établissement INSEE, sinon BAN housenumber).
        Re-traite TOUT le gisement et écrase les lat/lon. Admin."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table(); _ensure_scan_jobs_table()
            existing = execute_query(
                "SELECT id FROM scan_jobs WHERE type='geocode2' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if existing:
                return jsonify({'success': False, 'error': 'Un re-géocodage est déjà en cours',
                                'job_id': existing['id']}), 409
            execute_query("UPDATE industrial_prospects SET geo2_tried=0")
            n = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects", fetch_one=True) or {}
            job = execute_query("""
                INSERT INTO scan_jobs (type, status, user_id, params, depts_todo, depts_done)
                VALUES ('geocode2', 'running', %s, '{}', '[]', '[]') RETURNING id
            """, (str(user_id),), fetch_one=True)
            _start_geocode2_worker(job['id'])
            return jsonify({'success': True, 'job_id': job['id'], 'a_traiter': n.get('n', 0)})
        except Exception as e:
            print(f"❌ [GEOCODE2 START] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/geocode2/status', methods=['GET'])
    def geocode2_status():
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_scan_jobs_table()
            job = execute_query("SELECT * FROM scan_jobs WHERE type='geocode2' ORDER BY id DESC LIMIT 1",
                                fetch_one=True)
            if not job:
                return jsonify({'success': True, 'job': None})
            if job.get('status') == 'running' and not _GEO2_STATE.get('running'):
                try:
                    _start_geocode2_worker(job['id'])  # watchdog
                except Exception:
                    pass
            restants = execute_query("SELECT COUNT(*) AS n FROM industrial_prospects WHERE COALESCE(geo2_tried,0)=0",
                                     fetch_one=True) or {}
            prec = execute_query("SELECT geo_precision AS p, COUNT(*) AS n FROM industrial_prospects "
                                 "WHERE geo2_tried=1 GROUP BY geo_precision", fetch_all=True) or []
            srcs = execute_query("SELECT geo_source AS s, COUNT(*) AS n FROM industrial_prospects "
                                 "WHERE geo2_tried=1 GROUP BY geo_source", fetch_all=True) or []
            return jsonify({'success': True, 'job': {
                'status': job.get('status'), 'restants': restants.get('n', 0),
                'updated_at': str(job.get('updated_at')),
                'precision': {(r.get('p') or 'none'): r.get('n') for r in prec},
                'sources': {(r.get('s') or 'none'): r.get('n') for r in srcs}}})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/geocode2/stop', methods=['POST'])
    def geocode2_stop():
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_scan_jobs_table()
            execute_query("UPDATE scan_jobs SET status='stopped' WHERE type='geocode2' AND status='running'")
            _GEO2_STATE['running'] = False
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/feature-3d', methods=['POST'])
    def admin_set_feature_3d():
        """Active/désactive le Calepinage 3D pour un utilisateur (par email). Admin."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            data = request.get_json(silent=True) or {}
            email = (data.get('email') or '').strip().lower()
            enable = bool(data.get('enable', True))
            if not email:
                return jsonify({'success': False, 'error': 'email requis'}), 400
            execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS feature_3d_calpinage BOOLEAN DEFAULT FALSE")
            row = execute_query("SELECT id FROM users WHERE email = %s", (email,), fetch_one=True)
            if not row:
                return jsonify({'success': False, 'error': 'utilisateur introuvable'}), 404
            execute_query("UPDATE users SET feature_3d_calpinage = %s WHERE email = %s", (enable, email))
            chk = execute_query("SELECT feature_3d_calpinage FROM users WHERE email = %s", (email,), fetch_one=True) or {}
            return jsonify({'success': True, 'email': email,
                            'feature_3d_calpinage': chk.get('feature_3d_calpinage')})
        except Exception as e:
            print(f"❌ [FEATURE 3D] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/sysinfo', methods=['GET'])
    def admin_sysinfo():
        """Diagnostic mémoire (admin) : RSS du worker + limite/usage conteneur,
        pour dimensionner le nombre de workers gunicorn sans OOM."""
        try:
            _uid, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            info = {}

            def _mb(b):
                try:
                    return round(int(b) / 1024 / 1024, 1)
                except Exception:
                    return None
            # RSS du process worker courant
            try:
                with open('/proc/self/status') as f:
                    for line in f:
                        if line.startswith('VmRSS'):
                            info['worker_rss_mb'] = round(int(line.split()[1]) / 1024, 1)
                            break
            except Exception:
                pass
            # Limite mémoire du conteneur (cgroup v2 puis v1)
            for p in ('/sys/fs/cgroup/memory.max', '/sys/fs/cgroup/memory/memory.limit_in_bytes'):
                try:
                    v = open(p).read().strip()
                    if v.isdigit() and int(v) < (1 << 62):
                        info['conteneur_limite_mb'] = _mb(v); break
                except Exception:
                    pass
            # Usage mémoire courant du conteneur (tous process)
            for p in ('/sys/fs/cgroup/memory.current', '/sys/fs/cgroup/memory/memory.usage_in_bytes'):
                try:
                    v = open(p).read().strip()
                    if v.isdigit():
                        info['conteneur_usage_mb'] = _mb(v); break
                except Exception:
                    pass
            try:
                info['cpu_count_hote'] = os.cpu_count()
            except Exception:
                pass
            # vCPU RÉELLEMENT alloué au conteneur (cgroup) — la vraie contrainte
            try:
                cm = open('/sys/fs/cgroup/cpu.max').read().split()
                if cm and cm[0] != 'max':
                    info['vcpu_alloue'] = round(int(cm[0]) / int(cm[1]), 2)
            except Exception:
                try:
                    q = int(open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read())
                    p = int(open('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read())
                    if q > 0:
                        info['vcpu_alloue'] = round(q / p, 2)
                except Exception:
                    pass
            # nb de process gunicorn (workers) effectivement lancés
            try:
                n = 0
                for d in os.listdir('/proc'):
                    if d.isdigit():
                        try:
                            cl = open(f'/proc/{d}/cmdline', 'rb').read()
                            if b'gunicorn' in cl:
                                n += 1
                        except Exception:
                            pass
                info['process_gunicorn'] = n
            except Exception:
                pass
            rss = info.get('worker_rss_mb'); lim = info.get('conteneur_limite_mb')
            if rss and lim:
                info['workers_max_RAM'] = max(1, int((lim * 0.85) / rss))
            return jsonify({'success': True, **info})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/etude', methods=['GET'])
    def industriel_etude():
        """Photographie statistique complète de la base (pour étude de marché)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table()
            out = {}
            out['global'] = execute_query("""
                SELECT COUNT(*) AS n, COUNT(operateur_nom) AS avec_operateur,
                       ROUND(MIN(conso_mwh)) AS conso_min, ROUND(MAX(conso_mwh)) AS conso_max,
                       ROUND(AVG(conso_mwh)) AS conso_moy, ROUND(SUM(conso_mwh)) AS conso_totale,
                       ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY conso_mwh)) AS conso_mediane,
                       ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY conso_mwh)) AS conso_p90
                FROM industrial_prospects WHERE conso_mwh IS NOT NULL
            """, fetch_one=True)
            out['par_secteur'] = execute_query("""
                SELECT naf2, COUNT(*) AS n, ROUND(AVG(conso_mwh)) AS conso_moy,
                       ROUND(SUM(conso_mwh)) AS conso_tot
                FROM industrial_prospects WHERE naf2 IS NOT NULL AND naf2 <> ''
                GROUP BY naf2 ORDER BY n DESC
            """, fetch_all=True)
            out['par_tranche_conso'] = execute_query("""
                SELECT CASE
                    WHEN conso_mwh < 1000 THEN '1_0330-1000'
                    WHEN conso_mwh < 3000 THEN '2_1000-3000'
                    WHEN conso_mwh < 10000 THEN '3_3000-10000'
                    WHEN conso_mwh < 30000 THEN '4_10000-30000'
                    ELSE '5_30000+' END AS tranche,
                    COUNT(*) AS n, ROUND(SUM(conso_mwh)) AS conso_tot
                FROM industrial_prospects WHERE conso_mwh IS NOT NULL GROUP BY 1 ORDER BY 1
            """, fetch_all=True)
            out['par_departement'] = execute_query("""
                SELECT LEFT(code_commune,2) AS dept, COUNT(*) AS n, ROUND(SUM(conso_mwh)) AS conso_tot
                FROM industrial_prospects WHERE code_commune IS NOT NULL
                GROUP BY 1 ORDER BY n DESC
            """, fetch_all=True)
            out['par_effectif'] = execute_query("""
                SELECT COALESCE(operateur_effectif,'NN') AS eff, COUNT(*) AS n
                FROM industrial_prospects WHERE operateur_nom IS NOT NULL
                GROUP BY 1 ORDER BY n DESC
            """, fetch_all=True)
            out['top_sites'] = execute_query("""
                SELECT ROUND(conso_mwh) AS conso_mwh, naf2, commune, operateur_nom, operateur_effectif
                FROM industrial_prospects ORDER BY conso_mwh DESC NULLS LAST LIMIT 40
            """, fetch_all=True)
            return jsonify({'success': True, 'etude': out})
        except Exception as e:
            print(f"❌ [ETUDE] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/analyse', methods=['GET'])
    def industriel_analyse():
        """Répartition par secteur NAF et par tranche de conso (priorisation)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            uf = "" if is_admin else " AND user_id = %s"
            up = () if is_admin else (str(user_id),)
            par_secteur = execute_query(
                f"SELECT naf2, COUNT(*) AS n, ROUND(AVG(conso_mwh)) AS conso_moy, "
                f"ROUND(SUM(conso_mwh)) AS conso_tot FROM industrial_prospects "
                f"WHERE naf2 IS NOT NULL AND naf2 <> ''{uf} GROUP BY naf2 ORDER BY n DESC LIMIT 30",
                up or None, fetch_all=True) or []
            tranches = execute_query(
                f"""SELECT CASE
                        WHEN conso_mwh < 1000 THEN '0330-1000'
                        WHEN conso_mwh < 3000 THEN '1000-3000'
                        WHEN conso_mwh < 10000 THEN '3000-10000'
                        WHEN conso_mwh < 30000 THEN '10000-30000'
                        ELSE '30000+' END AS tranche,
                        COUNT(*) AS n
                     FROM industrial_prospects WHERE conso_mwh IS NOT NULL{uf}
                     GROUP BY 1 ORDER BY 1""",
                up or None, fetch_all=True) or []
            return jsonify({'success': True, 'par_secteur': par_secteur, 'par_tranche_conso': tranches})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # Reprise auto des workers au démarrage de l'app (si un job était 'running').
    def _resume_france_on_startup():
        import time as _t
        _t.sleep(25)  # laisser l'app + la base se stabiliser
        try:
            _ensure_scan_jobs_table()
            jf = execute_query(
                "SELECT id FROM scan_jobs WHERE type='france' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if jf and not _FRANCE_STATE.get('running') and _start_france_worker(jf['id']):
                print(f"🔄 [FRANCE WORKER] reprise du job {jf['id']}")
            jo = execute_query(
                "SELECT id FROM scan_jobs WHERE type='operators' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if jo and not _OP_STATE.get('running') and _start_operators_worker(jo['id']):
                print(f"🔄 [OP WORKER] reprise du job {jo['id']}")
            jg = execute_query(
                "SELECT id FROM scan_jobs WHERE type='geocode' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if jg and not _GEO_STATE.get('running') and _start_geocode_worker(jg['id']):
                print(f"🔄 [GEO WORKER] reprise du job {jg['id']}")
            jg2 = execute_query(
                "SELECT id FROM scan_jobs WHERE type='geocode2' AND status='running' ORDER BY id DESC LIMIT 1",
                fetch_one=True)
            if jg2 and not _GEO2_STATE.get('running') and _start_geocode2_worker(jg2['id']):
                print(f"🔄 [GEO2 WORKER] reprise du job {jg2['id']}")
        except Exception as _e:
            print(f"⚠️ [WORKER] reprise: {_e}")
    try:
        threading.Thread(target=_resume_france_on_startup, daemon=True).start()
    except Exception:
        pass

    @app.route('/api/industriel/prospects', methods=['GET'])
    def industriel_prospects_list():
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            dept = (request.args.get('dept') or '').strip()
            naf2 = (request.args.get('naf2') or '').strip()
            conso_min = request.args.get('conso_min')
            conso_max = request.args.get('conso_max')
            limit = min(int(request.args.get('limit') or 200), 500)
            offset = max(int(request.args.get('offset') or 0), 0)
            clause, params = "", []
            _gc, _gp = _industriel_gating_clause(user_id, is_admin)
            clause += _gc; params.extend(_gp)
            if dept:
                clause += " AND LEFT(code_commune, 2) = %s"; params.append(dept)
            if naf2:
                clause += " AND naf2 = %s"; params.append(naf2)
            if conso_min:
                clause += " AND conso_mwh >= %s"; params.append(float(conso_min))
            if conso_max:
                clause += " AND conso_mwh < %s"; params.append(float(conso_max))
            total = execute_query(
                f"SELECT COUNT(*) AS n FROM industrial_prospects WHERE 1=1{clause}",
                tuple(params) if params else None, fetch_one=True) or {}
            rows = execute_query(
                f"SELECT * FROM industrial_prospects WHERE 1=1{clause} "
                f"ORDER BY conso_mwh DESC NULLS LAST LIMIT %s OFFSET %s",
                tuple(params + [limit, offset]), fetch_all=True)
            return jsonify({'success': True, 'prospects': rows or [], 'limit': limit,
                            'offset': offset, 'total': total.get('n', 0)})
        except Exception as e:
            print(f"❌ [INDUSTRIEL LIST] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/potentiel-total', methods=['GET'])
    def industriel_potentiel_total():
        """Compteur global : agrège le potentiel d'installation sur TOUTE la base
        filtrée (pas seulement la page). Puissance = SUM(taux% × conso / productible),
        le productible étant calculé par latitude (≈ PVGIS) directement en SQL.
        Params: taux (def. 40), + mêmes filtres que la liste (dept/naf2/conso_min/max)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            try:
                taux = max(1.0, min(float(request.args.get('taux') or 40), 100.0))
            except Exception:
                taux = 40.0
            dept = (request.args.get('dept') or '').strip()
            naf2 = (request.args.get('naf2') or '').strip()
            conso_min = request.args.get('conso_min')
            conso_max = request.args.get('conso_max')
            clause, params = "", []
            _gc, _gp = _industriel_gating_clause(user_id, is_admin)
            clause += _gc; params.extend(_gp)
            if dept:
                clause += " AND LEFT(code_commune, 2) = %s"; params.append(dept)
            if naf2:
                clause += " AND naf2 = %s"; params.append(naf2)
            if conso_min:
                clause += " AND conso_mwh >= %s"; params.append(float(conso_min))
            if conso_max:
                clause += " AND conso_mwh < %s"; params.append(float(conso_max))
            # productible(lat) = clamp(1350 - (lat-43)*70, 950, 1400) ; 1150 si non géocodé
            row = execute_query(
                f"""SELECT COUNT(*) AS n,
                       COUNT(lat) AS geocodes,
                       COALESCE(SUM(conso_mwh), 0) AS conso_mwh,
                       COALESCE(SUM(
                           (%s/100.0) * conso_mwh * 1000.0 /
                           CASE WHEN lat IS NULL THEN 1150.0
                                ELSE GREATEST(950.0, LEAST(1400.0, 1350.0 - (lat - 43.0) * 70.0))
                           END
                       ), 0) AS kwc_total
                   FROM industrial_prospects
                   WHERE conso_mwh IS NOT NULL{clause}""",
                tuple([taux] + params), fetch_one=True) or {}
            kwc = float(row.get('kwc_total') or 0)
            conso_mwh = float(row.get('conso_mwh') or 0)
            return jsonify({'success': True, 'taux': taux,
                            'nb': row.get('n', 0), 'geocodes': row.get('geocodes', 0),
                            'conso_mwh': round(conso_mwh), 'conso_twh': round(conso_mwh / 1_000_000, 2),
                            'kwc_total': round(kwc), 'mwc_total': round(kwc / 1000, 1),
                            'gwc_total': round(kwc / 1_000_000, 2),
                            'production_gwh': round(taux / 100.0 * conso_mwh / 1000.0, 1),
                            'surface_ha': round(kwc * 6.5 / 10000.0, 1)})
        except Exception as e:
            print(f"❌ [POTENTIEL TOTAL] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/carte-data', methods=['GET'])
    def industriel_carte_data():
        """Points géocodés du gisement pour la carte nationale (payload compact).
        Chaque point = [lat, lon, conso_mwh, naf2, operateur, commune, dept, id]."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            dept = (request.args.get('dept') or '').strip()
            naf2 = (request.args.get('naf2') or '').strip()
            conso_min = request.args.get('conso_min')
            conso_max = request.args.get('conso_max')
            clause, params = "", []
            _gc, _gp = _industriel_gating_clause(user_id, is_admin)
            clause += _gc; params.extend(_gp)
            if dept:
                clause += " AND LEFT(code_commune, 2) = %s"; params.append(dept)
            if naf2:
                clause += " AND naf2 = %s"; params.append(naf2)
            if conso_min:
                clause += " AND conso_mwh >= %s"; params.append(float(conso_min))
            if conso_max:
                clause += " AND conso_mwh < %s"; params.append(float(conso_max))
            rows = execute_query(
                f"SELECT id, lat, lon, conso_mwh, naf2, operateur_nom, commune, code_commune, geo_precision "
                f"FROM industrial_prospects "
                f"WHERE lat IS NOT NULL AND lon IS NOT NULL AND conso_mwh IS NOT NULL{clause} "
                f"ORDER BY conso_mwh DESC LIMIT 30000",
                tuple(params) if params else None, fetch_all=True) or []
            pts = [[round(r['lat'], 5), round(r['lon'], 5), round(r.get('conso_mwh') or 0),
                    r.get('naf2') or '', (r.get('operateur_nom') or '')[:60],
                    r.get('commune') or '', (r.get('code_commune') or '')[:2], r['id'],
                    r.get('geo_precision') or '']
                   for r in rows]
            return jsonify({'success': True, 'count': len(pts), 'points': pts})
        except Exception as e:
            print(f"❌ [CARTE DATA] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    _PRODUCTIBLE_SQL = ("CASE WHEN lat IS NULL THEN 1150.0 "
                        "ELSE GREATEST(950.0, LEAST(1400.0, 1350.0 - (lat - 43.0) * 70.0)) END")

    def _rapport_rows(taux):
        """Agrégation gisement par département × secteur (profil de consommateur).
        Retourne la liste de lignes (dept, naf2, n, conso_mwh, kwc)."""
        _ensure_industrial_table()
        return execute_query(
            f"""SELECT LEFT(code_commune,2) AS dept, COALESCE(NULLIF(naf2,''),'??') AS naf2,
                   COUNT(*) AS n,
                   COALESCE(SUM(conso_mwh),0) AS conso_mwh,
                   COALESCE(SUM((%s/100.0)*conso_mwh*1000.0/{_PRODUCTIBLE_SQL}),0) AS kwc,
                   COUNT(lat) AS geocodes
               FROM industrial_prospects
               WHERE conso_mwh IS NOT NULL AND code_commune IS NOT NULL
               GROUP BY LEFT(code_commune,2), COALESCE(NULLIF(naf2,''),'??')
               ORDER BY dept, conso_mwh DESC""",
            (float(taux),), fetch_all=True) or []

    @app.route('/api/industriel/rapport', methods=['GET'])
    def industriel_rapport():
        """Rapport complet par département et par profil de consommateur (secteur NAF).
        Param taux (def. 40). Structure imbriquée : national → départements → secteurs."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            try:
                taux = max(1.0, min(float(request.args.get('taux') or 40), 100.0))
            except Exception:
                taux = 40.0
            rows = _rapport_rows(taux)
            depts = {}
            nat = {'nb': 0, 'conso_mwh': 0.0, 'kwc': 0.0}
            for r in rows:
                d = r['dept']
                conso = float(r.get('conso_mwh') or 0); kwc = float(r.get('kwc') or 0); n = r.get('n') or 0
                dd = depts.setdefault(d, {'dept': d, 'nom': DEPT_NOMS.get(d, d),
                                          'nb': 0, 'conso_mwh': 0.0, 'kwc': 0.0, 'secteurs': []})
                dd['secteurs'].append({'naf2': r['naf2'], 'label': NAF_LABELS.get(r['naf2'], 'Autre/non classé'),
                                       'nb': n, 'conso_mwh': round(conso),
                                       'kwc': round(kwc), 'mwc': round(kwc / 1000, 2)})
                dd['nb'] += n; dd['conso_mwh'] += conso; dd['kwc'] += kwc
                nat['nb'] += n; nat['conso_mwh'] += conso; nat['kwc'] += kwc
            dept_list = []
            for d in sorted(depts.values(), key=lambda x: x['conso_mwh'], reverse=True):
                d['conso_mwh'] = round(d['conso_mwh']); d['conso_twh'] = round(d['conso_mwh'] / 1_000_000, 3)
                d['mwc'] = round(d['kwc'] / 1000, 1); d['gwc'] = round(d['kwc'] / 1_000_000, 3)
                d['kwc'] = round(d['kwc'])
                dept_list.append(d)
            return jsonify({'success': True, 'taux': taux,
                            'national': {'nb': nat['nb'], 'conso_twh': round(nat['conso_mwh'] / 1_000_000, 2),
                                         'gwc': round(nat['kwc'] / 1_000_000, 2),
                                         'nb_departements': len(dept_list)},
                            'departements': dept_list})
        except Exception as e:
            print(f"❌ [RAPPORT] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/rapport.csv', methods=['GET'])
    def industriel_rapport_csv():
        """DESACTIVE : l'export CSV du gisement (donnee proprietaire) a ete retire
        pour empecher tout partage. Reactivable en supprimant le return ci-dessous."""
        return ("Export du gisement desactive", 410)
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return ("Admin requis", 403)
            try:
                taux = max(1.0, min(float(request.args.get('taux') or 40), 100.0))
            except Exception:
                taux = 40.0
            rows = _rapport_rows(taux)
            import csv, io as _io
            buf = _io.StringIO()
            buf.write('﻿')  # BOM pour Excel (accents)
            w = csv.writer(buf, delimiter=';')
            w.writerow(['Departement', 'Nom departement', 'Secteur (NAF2)', 'Profil consommateur',
                        'Nb sites', 'Conso totale (MWh/an)', 'Conso moyenne (MWh/an)',
                        f'Potentiel PV (kWc, couvrir {int(taux)}%)'])
            for r in rows:
                n = r.get('n') or 0
                conso = round(float(r.get('conso_mwh') or 0))
                w.writerow([r['dept'], DEPT_NOMS.get(r['dept'], r['dept']), r['naf2'],
                            NAF_LABELS.get(r['naf2'], 'Autre/non classé'), n, conso,
                            round(conso / n) if n else 0, round(float(r.get('kwc') or 0))])
            from flask import Response
            return Response(buf.getvalue(), mimetype='text/csv; charset=utf-8',
                            headers={'Content-Disposition': f'attachment; filename=rapport_gisement_taux{int(taux)}.csv'})
        except Exception as e:
            print(f"❌ [RAPPORT CSV] {e}")
            return (str(e), 500)

    @app.route('/api/industriel/stats', methods=['GET'])
    def industriel_stats():
        """Compteurs pour suivre l'avancement : total + par département."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            _ensure_industrial_table()
            clause, params = "", []
            if not is_admin:
                clause = " WHERE user_id = %s"; params.append(str(user_id))
            total = execute_query(
                f"SELECT COUNT(*) AS n, COUNT(operateur_nom) AS avec_op FROM industrial_prospects{clause}",
                tuple(params) if params else None, fetch_one=True) or {}
            par_dept = execute_query(
                f"SELECT LEFT(code_commune, 2) AS dept, COUNT(*) AS n FROM industrial_prospects{clause} "
                f"GROUP BY LEFT(code_commune, 2) ORDER BY dept",
                tuple(params) if params else None, fetch_all=True) or []
            return jsonify({'success': True, 'total': total.get('n', 0),
                            'avec_operateur': total.get('avec_op', 0),
                            'par_departement': {r['dept']: r['n'] for r in par_dept if r.get('dept')}})
        except Exception as e:
            print(f"❌ [INDUSTRIEL STATS] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/overview', methods=['GET'])
    def industriel_overview():
        """Vision d'ensemble admin : état complet du pipeline en un seul appel
        (gisement → opérateurs → géocodage → commercialisation → abonnements)."""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Admin requis'}), 403
            _ensure_industrial_table(); _ensure_scan_jobs_table(); _ensure_territories_table()

            # 1) Gisement
            g = execute_query(
                "SELECT COUNT(*) AS total, COUNT(operateur_nom) AS avec_op, "
                "COUNT(lat) AS geocodes, COALESCE(SUM(conso_mwh),0) AS conso_mwh, "
                "COUNT(DISTINCT LEFT(code_commune,2)) AS depts, "
                "COUNT(*) FILTER (WHERE adresse IS NOT NULL AND adresse <> '') AS avec_adresse "
                "FROM industrial_prospects", fetch_one=True) or {}
            total = g.get('total', 0) or 0
            avec_adresse = g.get('avec_adresse', 0) or 0
            geocodes = g.get('geocodes', 0) or 0
            avec_op = g.get('avec_op', 0) or 0

            def _job(t):
                j = execute_query("SELECT status, updated_at FROM scan_jobs WHERE type=%s "
                                  "ORDER BY id DESC LIMIT 1", (t,), fetch_one=True)
                return {'status': j.get('status'), 'updated_at': str(j.get('updated_at'))} if j else None

            # 2) Jobs autonomes
            jobs = {'scan_france': _job('france'), 'operateurs': _job('operators'),
                    'geocodage': _job('geocode')}
            geo_restants = execute_query(
                "SELECT COUNT(*) AS n FROM industrial_prospects "
                "WHERE lat IS NULL AND COALESCE(geo_tried,0)=0 "
                "AND adresse IS NOT NULL AND adresse <> ''", fetch_one=True) or {}

            # 3) Commercialisation / droits
            terr = execute_query(
                "SELECT COUNT(*) AS droits, COUNT(DISTINCT user_id) AS clients, "
                "COUNT(*) FILTER (WHERE stripe_subscription_id IS NOT NULL) AS abonnes_stripe "
                "FROM user_territories "
                "WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP", fetch_one=True) or {}
            par_type = execute_query(
                "SELECT territory_type, COUNT(*) AS n FROM user_territories "
                "WHERE expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP "
                "GROUP BY territory_type", fetch_all=True) or []

            # 4) Vignettes pré-chargées dans les CRM clients (tous users)
            pre = execute_query(
                "SELECT COUNT(*) AS vignettes, COUNT(DISTINCT user_id) AS crms "
                "FROM agriweb_prospects WHERE type='industriel'", fetch_one=True) or {}

            return jsonify({'success': True,
                'gisement': {
                    'total': total, 'depts': g.get('depts', 0),
                    'twh': round((g.get('conso_mwh', 0) or 0) / 1_000_000, 2),
                    'avec_adresse': avec_adresse,
                    'avec_operateur': avec_op,
                    'pct_operateur': round(100 * avec_op / total) if total else 0,
                },
                'geocodage': {
                    'geocodes': geocodes,
                    'restants': geo_restants.get('n', 0),
                    'pct': round(100 * geocodes / avec_adresse) if avec_adresse else 0,
                    'status': (jobs['geocodage'] or {}).get('status'),
                },
                'jobs': jobs,
                'commercialisation': {
                    'clients': terr.get('clients', 0),
                    'droits': terr.get('droits', 0),
                    'abonnes_stripe': terr.get('abonnes_stripe', 0),
                    'par_type': {r['territory_type']: r['n'] for r in par_type if r.get('territory_type')},
                    'vignettes_prechargees': pre.get('vignettes', 0),
                    'crms_remplis': pre.get('crms', 0),
                },
                'stripe_configure': bool(os.environ.get('STRIPE_SECRET_KEY')),
            })
        except Exception as e:
            print(f"❌ [OVERVIEW] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/industriel/prospects/<int:pid>', methods=['PATCH', 'DELETE'])
    def industriel_prospect_edit(pid):
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            owner = execute_query("SELECT user_id FROM industrial_prospects WHERE id = %s",
                                  (pid,), fetch_one=True)
            if not owner:
                return jsonify({'success': False, 'error': 'Introuvable'}), 404
            if not is_admin and str(owner.get('user_id')) != str(user_id):
                return jsonify({'success': False, 'error': 'Accès refusé'}), 403
            if request.method == 'DELETE':
                execute_query("DELETE FROM industrial_prospects WHERE id = %s", (pid,))
                return jsonify({'success': True})
            data = request.get_json(silent=True) or {}
            if 'statut' in data:
                execute_query("UPDATE industrial_prospects SET statut = %s WHERE id = %s",
                              (data['statut'], pid))
            if 'notes' in data:
                execute_query("UPDATE industrial_prospects SET notes = %s WHERE id = %s",
                              (data['notes'], pid))
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES API - PROJETS
    # ============================================================================

    @app.route('/api/crm/projets', methods=['GET'])
    def get_projets():
        """Liste tous les projets (avec filtre optionnel par prospect_id)"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            filter_clause, filter_params = user_filter_clause(user_id, is_admin, table_alias='pf')

            # Filtre optionnel par prospect_id
            prospect_id = request.args.get('prospect_id', type=int)
            
            if prospect_id:
                # Recherche pour un prospect spécifique
                projets = execute_query(f'''
                    SELECT 
                        pf.id,
                        pf.nom_projet,
                        pf.prospect_id,
                        pf.client_nom,
                        pf.date_creation as date_debut,
                        pf.date_fin_prevue,
                        pf.statut_global,
                        pf.responsable,
                        pf.surface_totale,
                        pf.parcelles_cadastrales,
                        pf.commune,
                        pf.adresse_projet
                    FROM project_fiches pf
                    WHERE pf.prospect_id = %s{filter_clause}
                    ORDER BY pf.date_creation DESC
                ''', (prospect_id,) + filter_params, fetch_all=True)
            else:
                # Tous les projets
                projets = execute_query(f'''
                    SELECT 
                        pf.id,
                        pf.nom_projet,
                        pf.prospect_id,
                        pf.client_nom,
                        pf.date_creation as date_debut,
                        pf.date_fin_prevue,
                        pf.statut_global,
                        pf.responsable,
                        pf.surface_totale,
                        pf.parcelles_cadastrales,
                        pf.commune,
                        pf.adresse_projet
                    FROM project_fiches pf
                    WHERE 1=1{filter_clause}
                    ORDER BY pf.date_creation DESC
                ''', filter_params if filter_params else None, fetch_all=True)
            
            # Ajouter les stats d'étapes pour chaque projet
            if projets:
                for p in projets:
                    etapes_stats = execute_query('''
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN statut = 'termine' THEN 1 END) as terminees
                        FROM project_etapes 
                        WHERE project_id = %s
                    ''', (p['id'],), fetch_one=True)
                    
                    p['etapes_total'] = etapes_stats['total'] if etapes_stats else 0
                    p['etapes_terminees'] = etapes_stats['terminees'] if etapes_stats else 0
            
            return jsonify({'success': True, 'projets': projets if projets else []})
            
        except Exception as e:
            print(f"Erreur get_projets: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets', methods=['POST'])
    def create_projet():
        """Crée une nouvelle fiche projet"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401

            data = request.json
            
            # Si on a un prospect_id, récupérer ses données et son rapport
            prospect_data_json = None
            prospect_info = {}
            
            if data.get('prospect_id'):
                # Isolation multi-tenant : interdire la copie du prospect d'un autre user
                if not verify_prospect_ownership(data.get('prospect_id'), user_id, is_admin):
                    return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
                prospect = execute_query(
                    'SELECT * FROM agriweb_prospects WHERE id = %s',
                    (data.get('prospect_id'),),
                    fetch_one=True
                )
                
                if prospect:
                    # Récupérer le data_json du prospect (contient le rapport complet)
                    if prospect.get('data_json'):
                        try:
                            prospect_data_json = prospect['data_json'] if isinstance(prospect['data_json'], str) else json.dumps(prospect['data_json'])
                        except:
                            prospect_data_json = None
                    
                    # Traiter les parcelles cadastrales (peuvent être un JSON)
                    parcelles_str = ''
                    if prospect.get('parcelles_cadastrales'):
                        try:
                            parcelles = prospect['parcelles_cadastrales']
                            if isinstance(parcelles, str):
                                # Essayer de parser si c'est du JSON
                                try:
                                    parcelles_json = json.loads(parcelles)
                                    if isinstance(parcelles_json, list):
                                        parcelles_str = ', '.join([str(p) for p in parcelles_json])
                                    else:
                                        parcelles_str = parcelles
                                except:
                                    parcelles_str = parcelles
                            else:
                                parcelles_str = str(parcelles)
                        except:
                            parcelles_str = ''
                    
                    # Récupérer les infos du prospect pour pré-remplir
                    prospect_info = {
                        'commune': prospect.get('commune'),
                        'adresse': prospect.get('adresse'),
                        'surface_m2': prospect.get('surface_m2'),
                        'surface_ha': prospect.get('surface_ha'),
                        'latitude': prospect.get('latitude'),
                        'longitude': prospect.get('longitude'),
                        'parcelles_cadastrales': parcelles_str
                    }
            
            # Créer le projet avec le data_json du rapport
            print(f"[CREATE_PROJECT] prospect_id={data.get('prospect_id')}, nom={data.get('nom_projet')}")
            print(f"[CREATE_PROJECT] data_json length={len(prospect_data_json) if prospect_data_json else 0}")
            
            result = execute_query('''
                INSERT INTO project_fiches (
                    prospect_id, nom_projet, type_projet, client_nom, client_email,
                    client_telephone, client_adresse, adresse_projet, parcelles_cadastrales,
                    statut_global, date_fin_prevue, responsable, notes, data_json,
                    commune, surface_totale, statut_projet, user_id
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data.get('prospect_id') or None,
                data.get('nom_projet'),
                data.get('type_projet', 'autoconsommation'),
                data.get('client_nom'),
                data.get('client_email'),
                data.get('client_telephone'),
                data.get('client_adresse'),
                data.get('adresse_projet') or prospect_info.get('adresse') or prospect_info.get('commune'),
                data.get('parcelles_cadastrales') or prospect_info.get('parcelles_cadastrales'),
                'en_cours',
                data.get('date_fin_prevue') or None,
                data.get('responsable'),
                data.get('notes'),
                prospect_data_json,  # Rapport complet
                data.get('commune') or prospect_info.get('commune'),
                data.get('surface_totale') or prospect_info.get('surface_m2'),
                'etude',  # statut_projet par défaut
                str(user_id) if user_id is not None else None
            ), fetch_one=True)
            
            print(f"[CREATE_PROJECT] INSERT result={result}")
            
            if not result or 'id' not in result:
                print(f"[CREATE_PROJECT] ERREUR: INSERT failed, result={result}")
                return jsonify({'success': False, 'error': 'Erreur lors de la création du projet'}), 500
            
            project_id = result['id']
            print(f"[CREATE_PROJECT] SUCCESS: project_id={project_id}")
            
            # Créer les étapes du workflow autoconsommation
            etapes_autoconso = [
                ('Rapport de recherche HeliaPV', 1),
                ('Visite technique', 2),
                ('Calepinage', 3),
                ('Plan de masse', 4),
                ('Étude d\'autoconsommation', 5),
                ('Devis commercial', 6),
                ('Signature & Facture', 7),
                ('Déclaration Préalable de Travaux (DP)', 8),
                ('Déclaration de Raccordement (DDR)', 9),
                ('Installation & DOE', 10),
                ('Consuel', 11),
                ('Mise en service & Maintenance', 12)
            ]
            
            print(f"[CREATE_PROJECT] Création de {len(etapes_autoconso)} étapes...")
            for etape_nom, ordre in etapes_autoconso:
                etape_result = execute_query('''
                    INSERT INTO project_etapes (project_id, nom_etape, ordre, statut)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                ''', (project_id, etape_nom, ordre, 'a_faire'), fetch_one=True)
                print(f"[CREATE_PROJECT] Étape créée: {etape_nom} (id={etape_result['id'] if etape_result else 'ERREUR'})")
            
            print(f"[CREATE_PROJECT] Toutes les étapes créées pour projet {project_id}")
            return jsonify({'success': True, 'project_id': project_id})
            
        except Exception as e:
            print(f"[CREATE_PROJECT] EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
    def get_projet_details(project_id):
        """Récupère les détails complets d'un projet"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_project_ownership(project_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            # Infos projet
            projet = execute_query('''
                SELECT 
                    pf.id,
                    pf.prospect_id,
                    pf.nom_projet,
                    pf.client_nom,
                    pf.client_email,
                    pf.client_telephone,
                    pf.adresse_projet,
                    pf.parcelles_cadastrales,
                    pf.commune,
                    pf.departement,
                    pf.surface_totale,
                    pf.puissance_estimee,
                    pf.statut_projet,
                    pf.date_creation as date_debut,
                    pf.date_modification,
                    pf.notes,
                    pf.data_json,
                    pf.type_projet,
                    pf.client_adresse,
                    pf.statut_global,
                    pf.date_fin_prevue,
                    pf.date_fin_reelle,
                    pf.responsable,
                    ap.type as prospect_type,
                    ap.adresse as prospect_adresse,
                    ap.latitude as prospect_latitude,
                    ap.longitude as prospect_longitude
                FROM project_fiches pf
                LEFT JOIN agriweb_prospects ap ON pf.prospect_id = ap.id
                WHERE pf.id = %s
            ''', (project_id,), fetch_one=True)
            
            if not projet:
                return jsonify({'success': False, 'error': 'Projet non trouvé'}), 404
            
            # Convertir data_json si c'est une chaîne
            if projet.get('data_json') and isinstance(projet['data_json'], str):
                try:
                    projet['data_json'] = json.loads(projet['data_json'])
                except:
                    projet['data_json'] = None
            
            # Étapes du projet
            etapes = execute_query('''
                SELECT 
                    id,
                    project_id,
                    nom_etape,
                    statut,
                    ordre,
                    date_debut,
                    date_fin_prevue,
                    date_fin_reelle,
                    responsable,
                    notes
                FROM project_etapes
                WHERE project_id = %s
                ORDER BY ordre
            ''', (project_id,), fetch_all=True)
            
            print(f"[GET_PROJECT] project_id={project_id}, etapes trouvées: {len(etapes) if etapes else 0}")
            if etapes:
                print(f"[GET_PROJECT] Première étape: {etapes[0].get('nom_etape') if etapes else 'N/A'}")
            
            projet['etapes'] = etapes if etapes else []
            
            # Documents du projet - avec gestion d'erreur
            try:
                documents = execute_query('''
                    SELECT 
                        id,
                        project_id,
                        prospect_id,
                        nom_document,
                        nom_fichier,
                        type_document,
                        categorie,
                        mime_type,
                        chemin_fichier,
                        url_document,
                        taille_octets,
                        etape_id,
                        statut,
                        version,
                        notes,
                        source,
                        date_upload,
                        date_creation,
                        CASE WHEN file_data IS NOT NULL THEN true ELSE false END as has_file
                    FROM project_documents
                    WHERE project_id = %s
                    ORDER BY date_creation DESC
                ''', (project_id,), fetch_all=True)
                projet['documents'] = documents if documents else []
            except Exception as doc_error:
                print(f"Erreur récupération documents: {str(doc_error)}")
                projet['documents'] = []
            
            return jsonify({'success': True, 'projet': projet})
            
        except Exception as e:
            import traceback
            print(f"Erreur get_projet_details: {str(e)}")
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>', methods=['PUT'])
    def update_projet(project_id):
        """Met à jour un projet"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_project_ownership(project_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            data = request.json
            
            execute_query('''
                UPDATE project_fiches
                SET nom_projet = %s, type_projet = %s, client_nom = %s, client_email = %s, client_telephone = %s,
                    client_adresse = %s, adresse_projet = %s, parcelles_cadastrales = %s,
                    statut_global = %s, date_fin_prevue = %s, date_fin_reelle = %s,
                    responsable = %s, notes = %s
                WHERE id = %s
            ''', (
                data.get('nom_projet'),
                data.get('type_projet'),
                data.get('client_nom'),
                data.get('client_email'),
                data.get('client_telephone'),
                data.get('client_adresse'),
                data.get('adresse_projet'),
                data.get('parcelles_cadastrales'),
                data.get('statut_global'),
                data.get('date_fin_prevue') or None,
                data.get('date_fin_reelle') or None,
                data.get('responsable'),
                data.get('notes'),
                project_id
            ))
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>', methods=['DELETE'])
    def delete_projet(project_id):
        """Supprime un projet et toutes ses données associées"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_project_ownership(project_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            # Supprimer les documents
            execute_query('DELETE FROM project_documents WHERE project_id = %s', (project_id,))
            
            # Supprimer les étapes
            execute_query('DELETE FROM project_etapes WHERE project_id = %s', (project_id,))
            
            # Supprimer le projet
            execute_query('DELETE FROM project_fiches WHERE id = %s', (project_id,))
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>/etapes/<int:etape_id>', methods=['PUT'])
    @require_project_owner
    def update_etape(project_id, etape_id):
        """Met à jour une étape du projet"""
        try:
            data = request.json
            
            execute_query('''
                UPDATE project_etapes
                SET statut = %s, date_debut = %s, date_fin_reelle = %s, responsable = %s, notes = %s
                WHERE id = %s AND project_id = %s
            ''', (
                data.get('statut'),
                data.get('date_debut'),
                data.get('date_fin'),  # Le JS envoie 'date_fin' mais on l'insère dans 'date_fin_reelle'
                data.get('responsable'),
                data.get('notes'),
                etape_id,
                project_id
            ))
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>/documents', methods=['POST'])
    @require_project_owner
    def add_document(project_id):
        """Ajoute un document au projet (JSON ou upload fichier)"""
        try:
            # Vérifier que le projet existe et récupérer prospect_id
            project = execute_query(
                'SELECT id, prospect_id FROM project_fiches WHERE id = %s',
                (project_id,), fetch_one=True
            )
            if not project:
                return jsonify({'success': False, 'error': 'Projet non trouvé'}), 404
            
            prospect_id = project.get('prospect_id')
            
            # Upload de fichier (multipart/form-data)
            if request.content_type and 'multipart/form-data' in request.content_type:
                file = request.files.get('file')
                if not file or file.filename == '':
                    return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
                
                import base64
                file_content = file.read()
                file_base64 = base64.b64encode(file_content).decode('utf-8')
                
                nom_fichier = file.filename
                mime_type = file.content_type or 'application/octet-stream'
                taille = len(file_content)
                type_document = request.form.get('type_document', 'autre')
                categorie = request.form.get('categorie', type_document)
                notes = request.form.get('notes', '')
                etape_id = request.form.get('etape_id')
                etape_id = int(etape_id) if etape_id else None
                
                doc_id = execute_query('''
                    INSERT INTO project_documents (
                        project_id, prospect_id, nom_document, nom_fichier,
                        type_document, categorie, mime_type, file_data,
                        taille_octets, etape_id, statut, notes, source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    project_id, prospect_id, nom_fichier, nom_fichier,
                    type_document, categorie, mime_type, file_base64,
                    taille, etape_id, 'valide', notes, 'upload'
                ), fetch_one=True)['id']
                
                print(f"📎 [DATAROOM] Fichier uploadé: {nom_fichier} ({taille} bytes) → doc_id={doc_id}")
                return jsonify({'success': True, 'document_id': doc_id, 'nom_fichier': nom_fichier})
            
            # Ajout par JSON (ancien système, rétrocompatible)
            data = request.json
            doc_id = execute_query('''
                INSERT INTO project_documents (
                    project_id, prospect_id, nom_document, nom_fichier,
                    type_document, categorie, etape_id, 
                    chemin_fichier, url_document, statut, notes, source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                project_id, prospect_id,
                data.get('nom_fichier', data.get('nom_document', 'Document')),
                data.get('nom_fichier'),
                data.get('type_document', 'autre'),
                data.get('categorie', data.get('type_document', 'autre')),
                int(data['etape_id']) if data.get('etape_id') else None,
                data.get('chemin_fichier'),
                data.get('url_document'),
                data.get('statut', 'valide'),
                data.get('notes'),
                data.get('source', 'manual')
            ), fetch_one=True)['id']
            
            return jsonify({'success': True, 'document_id': doc_id})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>/download')
    @require_project_owner
    def download_document(project_id, doc_id):
        """Télécharge un fichier de la dataroom"""
        try:
            doc = execute_query(
                'SELECT nom_fichier, nom_document, mime_type, file_data, url_document FROM project_documents WHERE id = %s AND project_id = %s',
                (doc_id, project_id), fetch_one=True
            )
            
            if not doc:
                return "Document non trouvé", 404
            
            # Si le fichier est stocké en base64
            if doc.get('file_data'):
                import base64
                from io import BytesIO
                file_bytes = base64.b64decode(doc['file_data'])
                buffer = BytesIO(file_bytes)
                buffer.seek(0)
                
                filename = doc.get('nom_fichier') or doc.get('nom_document') or 'document'
                mime = doc.get('mime_type') or 'application/octet-stream'
                
                return send_file(
                    buffer,
                    mimetype=mime,
                    as_attachment=True,
                    download_name=filename
                )
            
            # Si c'est une URL, rediriger
            if doc.get('url_document'):
                from flask import redirect
                return redirect(doc['url_document'])
            
            return "Aucun fichier associé", 404
            
        except Exception as e:
            return f"Erreur: {str(e)}", 500

    @app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>/preview')
    @require_project_owner
    def preview_document(project_id, doc_id):
        """Aperçu inline d'un fichier (PDF, images)"""
        try:
            doc = execute_query(
                'SELECT nom_fichier, mime_type, file_data FROM project_documents WHERE id = %s AND project_id = %s',
                (doc_id, project_id), fetch_one=True
            )
            
            if not doc or not doc.get('file_data'):
                return "Document non trouvé", 404
            
            import base64
            from io import BytesIO
            file_bytes = base64.b64decode(doc['file_data'])
            buffer = BytesIO(file_bytes)
            buffer.seek(0)
            
            mime = doc.get('mime_type') or 'application/octet-stream'
            
            return send_file(
                buffer,
                mimetype=mime,
                as_attachment=False,
                download_name=doc.get('nom_fichier') or 'document'
            )
            
        except Exception as e:
            return f"Erreur: {str(e)}", 500

    def save_to_dataroom(prospect_id, file_bytes, nom_fichier, type_document, mime_type='application/pdf', source='auto'):
        """Sauvegarde automatique d'un fichier généré dans la dataroom du prospect"""
        try:
            import base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            taille = len(file_bytes)
            
            # Trouver le projet du prospect
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,), fetch_one=True
            )
            
            if not project:
                print(f"⚠️ [DATAROOM] Pas de fiche projet pour prospect {prospect_id}, création auto...")
                # Créer le projet s'il n'existe pas
                prospect = execute_query(
                    'SELECT commune, adresse_complete FROM agriweb_prospects WHERE id = %s',
                    (prospect_id,), fetch_one=True
                )
                commune = prospect.get('commune', '') if prospect else ''
                # Récupérer user_id du prospect pour le propager au projet
                prospect_owner = execute_query(
                    'SELECT user_id FROM agriweb_prospects WHERE id = %s',
                    (prospect_id,), fetch_one=True
                )
                owner_id = prospect_owner.get('user_id') if prospect_owner else None
                auto_create_project_for_prospect(prospect_id, commune=commune, user_id=owner_id)
                project = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                    (prospect_id,), fetch_one=True
                )
            
            if not project:
                print(f"❌ [DATAROOM] Impossible de créer le projet pour prospect {prospect_id}")
                return None
            
            # Vérifier si un document du même type/source existe déjà → mettre à jour
            existing = execute_query(
                'SELECT id, version FROM project_documents WHERE project_id = %s AND type_document = %s AND source = %s ORDER BY date_creation DESC LIMIT 1',
                (project['id'], type_document, source), fetch_one=True
            )
            
            if existing:
                # Mettre à jour le document existant (nouvelle version)
                new_version = (existing.get('version') or 1) + 1
                execute_query('''
                    UPDATE project_documents 
                    SET file_data = %s, taille_octets = %s, nom_fichier = %s, nom_document = %s,
                        mime_type = %s, version = %s, date_modification = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (file_base64, taille, nom_fichier, nom_fichier, mime_type, new_version, existing['id']))
                print(f"📎 [DATAROOM] Document mis à jour: {nom_fichier} v{new_version} (doc_id={existing['id']})")
                return existing['id']
            else:
                # Créer un nouveau document
                doc_id = execute_query('''
                    INSERT INTO project_documents (
                        project_id, prospect_id, nom_document, nom_fichier,
                        type_document, categorie, mime_type, file_data,
                        taille_octets, statut, source
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    project['id'], prospect_id, nom_fichier, nom_fichier,
                    type_document, type_document, mime_type, file_base64,
                    taille, 'valide', source
                ), fetch_one=True)['id']
                print(f"📎 [DATAROOM] Nouveau document: {nom_fichier} (doc_id={doc_id})")
                return doc_id
                
        except Exception as e:
            print(f"⚠️ [DATAROOM] Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
            return None

    @app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['PUT'])
    @require_project_owner
    def update_document(project_id, doc_id):
        """Met à jour un document"""
        try:
            data = request.json
            
            execute_query('''
                UPDATE project_documents
                SET nom_fichier = %s, url_document = %s, statut = %s, 
                    notes = %s, date_modification = CURRENT_TIMESTAMP,
                    version = version + 1
                WHERE id = %s AND project_id = %s
            ''', (
                data.get('nom_fichier'),
                data.get('url_document'),
                data.get('statut'),
                data.get('notes'),
                doc_id,
                project_id
            ))
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>/documents/<int:doc_id>', methods=['DELETE'])
    @require_project_owner
    def delete_document(project_id, doc_id):
        """Supprime un document"""
        try:
            execute_query(
                'DELETE FROM project_documents WHERE id = %s AND project_id = %s',
                (doc_id, project_id)
            )
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/prospect/<int:prospect_id>/carte')
    def get_prospect_carte(prospect_id):
        """Génère et retourne la carte d'un prospect à la volée"""
        try:
            # Récupérer le prospect
            prospect = execute_query(
                'SELECT * FROM agriweb_prospects WHERE id = %s',
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect:
                return "Prospect non trouvé", 404
            
            # Si le prospect a déjà une carte dans data_json, utiliser son URL
            if prospect.get('data_json'):
                try:
                    data = json.loads(prospect['data_json']) if isinstance(prospect['data_json'], str) else prospect['data_json']
                    if data.get('carte_url'):
                        # Rediriger vers la carte existante
                        from flask import redirect
                        return redirect(data['carte_url'])
                except:
                    pass
            
            # Sinon, générer une carte simple à partir des coordonnées
            lat = prospect.get('latitude')
            lon = prospect.get('longitude')
            
            if not lat or not lon:
                return "Coordonnées manquantes", 400
            
            # Importer folium pour générer la carte
            try:
                import folium
                from folium import plugins
            except ImportError:
                return "Module folium non disponible", 500
            
            # Créer une carte simple centrée sur le prospect
            m = folium.Map(
                location=[lat, lon],
                zoom_start=16,
                tiles=None,
                max_zoom=22
            )
            
            # Ajouter les tuiles satellite (Google Satellite) - PAR DÉFAUT
            folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google Satellite',
                name='Satellite',
                overlay=False,
                control=True,
                max_zoom=22,
                show=True  # Afficher par défaut
            ).add_to(m)
            
            # Ajouter les tuiles OSM
            folium.TileLayer(
                tiles='OpenStreetMap',
                name='OSM',
                overlay=False,
                control=True,
                show=False  # Ne pas afficher par défaut
            ).add_to(m)
            
            # Ajouter un marqueur pour le prospect
            type_icons = {
                'parking': 'P',
                'toiture': '🏢',
                'friche': '🏭',
                'parcelle_rpg': '🌾'
            }
            
            type_colors = {
                'parking': 'blue',
                'toiture': 'red',
                'friche': 'orange',
                'parcelle_rpg': 'green'
            }
            
            prospect_type = prospect.get('type', 'parking')
            icon_html = f'''
                <div style="background-color: {type_colors.get(prospect_type, 'blue')}; 
                            color: white; 
                            border-radius: 50%; 
                            width: 30px; 
                            height: 30px; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center;
                            font-weight: bold;
                            border: 2px solid white;">
                    {type_icons.get(prospect_type, '📍')}
                </div>
            '''
            
            folium.Marker(
                location=[lat, lon],
                popup=f"""
                    <b>{prospect.get('nom_prospect', 'Prospect')}</b><br>
                    Type: {prospect_type}<br>
                    Adresse: {prospect.get('adresse', 'N/A')}<br>
                    Surface: {prospect.get('surface_m2', 'N/A')} m²
                """,
                icon=folium.DivIcon(html=icon_html)
            ).add_to(m)
            
            # Ajouter le contrôle de couches
            folium.LayerControl().add_to(m)
            
            # Retourner le HTML de la carte
            return m._repr_html_()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la génération de la carte: {str(e)}", 500

    # ============================================================================
    # ROUTES CALPINAGE PHOTOVOLTAÏQUE
    # ============================================================================
    
    def get_pvgis_production(lat, lon, tilt, azimuth, peakpower=1.0):
        """
        Obtenir la production annuelle via l'API PVGIS
        
        Args:
            lat: Latitude
            lon: Longitude
            tilt: Inclinaison des panneaux (0-90°)
            azimuth: Azimut (0°=Nord, 90°=Est, 180°=Sud, 270°=Ouest)
            peakpower: Puissance crête en kWc
        
        Returns:
            Dict avec production annuelle et données horaires ou None
        """
        import requests
        
        url = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
        # PVGIS utilise "aspect" qui est l'inverse de l'azimut standard
        aspect_pvgis = 180.0 - azimuth
        
        params = {
            "lat": lat,
            "lon": lon,
            "peakpower": peakpower,
            "loss": 14,  # Pertes système (14% standard)
            "angle": tilt,  # Inclinaison
            "aspect": aspect_pvgis,  # Orientation
            "outputformat": "json"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            
            # Production annuelle
            production_annual = data["outputs"]["totals"]["fixed"]["E_y"]
            
            # Données mensuelles pour graphiques
            monthly_data = data["outputs"]["monthly"]["fixed"]
            
            return {
                'annual_kwh': production_annual,
                'monthly': monthly_data,
                'raw_data': data
            }
        except Exception as e:
            print(f"Erreur PVGIS: {e}")
            return None
    
    def get_pvgis_hourly(lat, lon, tilt, azimuth, peakpower=1.0):
        """Obtenir les données horaires 8760h de PVGIS"""
        import requests
        
        url = "https://re.jrc.ec.europa.eu/api/v5_2/seriescalc"
        aspect_pvgis = 180.0 - azimuth
        
        params = {
            "lat": lat,
            "lon": lon,
            "peakpower": peakpower,
            "loss": 14,
            "angle": tilt,
            "aspect": aspect_pvgis,
            "outputformat": "json",
            "pvcalculation": 1,   # ← indispensable pour avoir le champ P
            "startyear": 2020,
            "endyear": 2020,
        }
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data
        except Exception as e:
            print(f"Erreur PVGIS hourly: {e}")
            return None
    
    @app.route('/api/crm/prospects/<int:prospect_id>/pvgis', methods=['POST'])
    def calculate_pvgis_production(prospect_id):
        """Calculer le productible d'une zone via PVGIS avec données mensuelles"""
        try:
            data = request.json
            lat = data.get('latitude')
            lon = data.get('longitude')
            tilt = data.get('inclinaison', 30)
            azimuth = data.get('orientation', 180)
            puissance_kw = data.get('puissance_kw', 1.0)
            
            if not lat or not lon:
                return jsonify({'error': 'Coordonnées manquantes'}), 400
            
            # Appel PVGIS avec données mensuelles
            pvgis_data = get_pvgis_production(lat, lon, tilt, azimuth, puissance_kw)
            
            if pvgis_data is None:
                # Fallback sur méthode simplifiée
                return jsonify({
                    'success': False,
                    'error': 'PVGIS temporairement indisponible',
                    'fallback': True
                }), 200
            
            production_kwh = pvgis_data['annual_kwh']
            production_mwh = production_kwh / 1000
            
            # Extraire données mensuelles pour graphiques
            monthly = pvgis_data['monthly']
            months_labels = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
            monthly_values = [m['E_m'] for m in monthly]  # Production mensuelle en kWh
            
            return jsonify({
                'success': True,
                'productible_mwh': round(production_mwh, 3),
                'productible_kwh': round(production_kwh, 1),
                'ratio_kwh_kwc': round(production_kwh / puissance_kw, 0) if puissance_kw > 0 else 0,
                'source': 'PVGIS',
                'monthly_labels': months_labels,
                'monthly_values': monthly_values
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/crm/prospects/<int:prospect_id>/pvgis-hourly', methods=['POST'])
    def download_pvgis_hourly(prospect_id):
        """Télécharger les données horaires 8760h PVGIS au format CSV et les sauvegarder en BDD"""
        try:
            data = request.json
            lat = data.get('latitude')
            lon = data.get('longitude')
            tilt = data.get('inclinaison', 30)
            azimuth = data.get('orientation', 180)
            puissance_kw = data.get('puissance_kw', 1.0)
            zone_numero = data.get('zone_numero', 1)

            if not lat or not lon:
                return jsonify({'error': 'Coordonnées manquantes'}), 400

            # Appel PVGIS hourly
            pvgis_data = get_pvgis_hourly(lat, lon, tilt, azimuth, puissance_kw)

            if pvgis_data is None:
                return jsonify({'error': 'PVGIS hourly indisponible'}), 500

            # Données horaires
            hourly_data = pvgis_data.get('outputs', {}).get('hourly', [])

            # ── Sauvegarder les valeurs P en BDD dans data_json ────────────────────
            try:
                p_values = [float(e.get('P', 0)) for e in hourly_data[:8760]]
                if len(p_values) == 8760:
                    prospect_row = execute_query(
                        "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                        (prospect_id,), fetch_one=True
                    )
                    if prospect_row:
                        current_data = prospect_row['data_json'] or {}
                        if isinstance(current_data, str):
                            current_data = json.loads(current_data)
                        if 'calpinage' not in current_data:
                            current_data['calpinage'] = {}
                        if 'pvgis_8760h' not in current_data['calpinage']:
                            current_data['calpinage']['pvgis_8760h'] = {}
                        current_data['calpinage']['pvgis_8760h'][str(zone_numero)] = p_values
                        execute_query(
                            "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                            (json.dumps(current_data), prospect_id)
                        )
                        print(f"[PVGIS 8760h] Zone {zone_numero} sauvegardée en BDD ({len(p_values)} valeurs)")
            except Exception as save_err:
                print(f"[PVGIS 8760h] Erreur sauvegarde BDD: {save_err}")

            # ── Si save_only → retourner JSON sans générer CSV ──────────────────
            save_only = data.get('save_only', False)
            if save_only:
                return jsonify({'success': True, 'saved': len(p_values) if len(p_values) == 8760 else 0, 'zone_numero': zone_numero})

            # ── Créer CSV pour téléchargement ─────────────────────────────────────
            from io import StringIO
            import csv

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Date', 'Heure', 'Production (W)', 'Irradiation (W/m²)', 'Température (°C)'])

            for entry in hourly_data:
                time_str = entry.get('time', '')
                power = entry.get('P', 0)
                irradiation = entry.get('G(i)', 0)
                temp = entry.get('T2m', 0)
                if time_str:
                    date_part = time_str[:8]
                    hour_part = time_str[8:10]
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
                    formatted_hour = f"{hour_part}:00"
                    writer.writerow([formatted_date, formatted_hour, power, irradiation, temp])

            output.seek(0)
            from flask import Response

            filename = f"PVGIS_8760h_Zone{zone_numero}_Prospect{prospect_id}.csv"
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/pvgis-save-values', methods=['POST'])
    def save_pvgis_values(prospect_id):
        """Sauvegarder les valeurs P 8760h envoyées par le navigateur (PVGIS appelé côté client)"""
        try:
            data = request.json or {}
            zone_numero = data.get('zone_numero', 1)
            p_values    = data.get('p_values', [])

            if len(p_values) != 8760:
                return jsonify({'error': f'Attendu 8760 valeurs, reçu {len(p_values)}'}), 400

            prospect_row = execute_query(
                "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not prospect_row:
                return jsonify({'error': 'Prospect non trouvé'}), 404

            current_data = prospect_row['data_json'] or {}
            if isinstance(current_data, str):
                current_data = json.loads(current_data)
            current_data.setdefault('calpinage', {}).setdefault('pvgis_8760h', {})[str(zone_numero)] = [
                float(v) for v in p_values
            ]
            execute_query(
                "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                (json.dumps(current_data), prospect_id)
            )
            print(f"[PVGIS SAVE] Zone {zone_numero} -> {len(p_values)} valeurs sauvegardées (prospect {prospect_id})")
            return jsonify({'success': True, 'zone_numero': zone_numero, 'values_saved': len(p_values)})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ========================================
    # ROUTES AUTOCONSOMMATION
    # ========================================

    @app.route('/api/crm/enedis-pdl-conso', methods=['POST'])
    def enedis_pdl_conso():
        """
        Récupère la consommation annuelle d'un PDL via :
          1. Enedis Data Connect (si access_token fourni) → /metering_data/v5/daily_consumption
          2. Sinon, tente Enedis Open Data (dataset consommation annuelle entreprise).

        Body JSON :
          pdl          : str   – numéro PDL 14 chiffres (usage_point_id)
          access_token : str   – Bearer token Enedis Data Connect (optionnel)

        Retour :
          ok                 : bool
          consommation_kwh   : float  (total 12 derniers mois)
          source             : str    ('data_connect' | 'open_data' | 'non_trouve')
          annee_ref          : str    (ex: "2023")
          detail             : dict
        """
        import requests as _req
        from datetime import datetime as _dt, timedelta as _td

        data        = request.json or {}
        pdl         = str(data.get('pdl', '')).strip().replace(' ', '')
        token       = str(data.get('access_token', '')).strip()

        if not pdl or len(pdl) != 14 or not pdl.isdigit():
            return jsonify({'ok': False, 'error': 'PDL invalide – doit contenir exactement 14 chiffres'}), 400

        # ── 1. Enedis Data Connect (Bearer token) ────────────────────────────
        if token:
            try:
                end_date   = _dt.now().strftime('%Y-%m-%d')
                start_date = (_dt.now() - _td(days=365)).strftime('%Y-%m-%d')

                url = 'https://ext.prod.api.enedis.fr/metering_data/v5/daily_consumption'
                headers  = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
                params   = {'usage_point_id': pdl, 'start': start_date, 'end': end_date}

                print(f"[PDL] Data Connect: PDL={pdl} période {start_date}→{end_date}")
                resp = _req.get(url, headers=headers, params=params, timeout=15)

                if resp.status_code == 200:
                    jdata = resp.json()
                    readings = jdata.get('meter_reading', {}).get('interval_reading', [])
                    total_wh  = sum(float(r.get('value', 0)) for r in readings)
                    total_kwh = round(total_wh / 1000.0, 0) if total_wh > 0 else 0

                    # Parfois valeurs déjà en kWh (dépend du compteur)
                    # Heuristique : si total très bas (< 10), c'est en MWh
                    if 0 < total_kwh < 50:
                        total_kwh = round(total_kwh * 1000, 0)

                    print(f"[PDL] Data Connect OK → {total_kwh} kWh ({len(readings)} jours)")
                    return jsonify({
                        'ok'               : True,
                        'consommation_kwh' : total_kwh,
                        'source'           : 'data_connect',
                        'annee_ref'        : start_date[:4] + '–' + end_date[:4],
                        'detail'           : {'nb_jours': len(readings), 'start': start_date, 'end': end_date}
                    })
                elif resp.status_code == 403:
                    print(f"[PDL] Data Connect 403 – token invalide ou PDL non consenti")
                    return jsonify({
                        'ok': False, 'source': 'data_connect',
                        'error': 'Accès refusé (403) – vérifiez le token et le consentement du client pour ce PDL'
                    }), 403
                elif resp.status_code == 404:
                    print(f"[PDL] Data Connect 404 – PDL {pdl} non trouvé")
                    return jsonify({'ok': False, 'source': 'data_connect', 'error': f'PDL {pdl} non trouvé'}), 404
                else:
                    print(f"[PDL] Data Connect HTTP {resp.status_code}: {resp.text[:200]}")
                    return jsonify({
                        'ok': False, 'source': 'data_connect',
                        'error': f'Erreur Enedis Data Connect HTTP {resp.status_code}'
                    }), 502

            except Exception as dc_err:
                print(f"[PDL] Data Connect erreur: {dc_err}")
                return jsonify({'ok': False, 'source': 'data_connect', 'error': str(dc_err)}), 502

        # ── 2. Fallback Open Data (sans token) – consommation annuelle entreprise ──
        try:
            od_url = (
                'https://data.enedis.fr/api/explore/v2.1/catalog/datasets'
                '/consommation-annuelle-reseaux-distribution/records'
            )
            # Ce dataset n'a pas de PDL individuel ; on essaie le dataset entreprises par adresse
            od_url2 = (
                'https://opendata.enedis.fr/data-fair/api/v1/datasets'
                '/qjl5f5v2mfxajth6gk2t8u7h/lines'
            )
            params2 = {'size': 5, 'qs': f'pdl:{pdl}'}
            print(f"[PDL] Open Data fallback: PDL={pdl}")
            resp2 = _req.get(od_url2, params=params2, timeout=10)
            if resp2.status_code == 200:
                jdata2 = resp2.json()
                results = jdata2.get('results', [])
                if results:
                    r = results[0]
                    conso_mwh = float(r.get('consommation_annuelle_totale_de_ladresse_mwh', 0) or 0)
                    conso_kwh = round(conso_mwh * 1000, 0)
                    annee     = str(r.get('annee', ''))
                    adresse   = r.get('adresse', '')
                    print(f"[PDL] Open Data OK → {conso_kwh} kWh, adresse: {adresse}")
                    return jsonify({
                        'ok'               : True,
                        'consommation_kwh' : conso_kwh,
                        'source'           : 'open_data',
                        'annee_ref'        : annee,
                        'detail'           : {'adresse': adresse, 'conso_mwh': conso_mwh}
                    })

            # Aucune donnée trouvée
            print(f"[PDL] Open Data : PDL {pdl} non trouvé dans le dataset public")
            return jsonify({
                'ok'     : False,
                'source' : 'non_trouve',
                'error'  : (
                    '⚠️ PDL non trouvé dans les données publiques Enedis. '
                    'Pour accéder aux données réelles, un token Enedis Data Connect '
                    'avec consentement du client est requis.'
                )
            }), 404

        except Exception as od_err:
            print(f"[PDL] Open Data erreur: {od_err}")
            return jsonify({'ok': False, 'source': 'open_data', 'error': str(od_err)}), 502

    @app.route('/api/crm/prospects/<int:prospect_id>/autoconsommation', methods=['POST'])
    @require_prospect_owner
    def calculate_autoconsommation(prospect_id):
        """
        Calcul complet d'autoconsommation solaire.
        Agrège la production PVGIS de toutes les zones et la superpose
        au profil de consommation Enedis choisi.

        Body JSON attendu :
          zones            : [{lat, lon, inclinaison, orientation, puissance_kw, zone_numero}, ...]
          consommation_kwh : float  – consommation annuelle (kWh)
          profil_type      : str    – RES1|RES2|PRO1|PRO2|AGR|ENT
          tarif_achat      : float  – € / kWh (optionnel, défaut 0.2516)
          tarif_revente    : float  – € / kWh surplus (optionnel, défaut S21 selon puissance)
          enedis_pdl       : str    – (optionnel) PDL à 14 chiffres pour courbe réelle Linky
          enedis_token     : str    – (optionnel) access_token Enedis Data Connect
        """
        try:
            from autoconsommation import (
                get_consumption_profile,
                compute_autoconsommation,
                compute_economics,
                PROFILE_LABELS,
                TARIFF_LABELS,
                get_enedis_dataconnect_profile,
            )

            data = request.json or {}
            zones             = data.get('zones', [])
            consommation_kwh  = float(data.get('consommation_kwh', 0))
            profil_type       = data.get('profil_type', 'RES1').upper()
            tariff_type       = data.get('tariff_type', 'BASE').upper()
            # Tarif S21 : calculé selon la puissance totale si non fourni explicitement
            _puissance_totale_kw = sum(float(z.get('puissance_kw', 0)) for z in data.get('zones', []))
            from autoconsommation import get_tarif_revente_s21
            _tr_s21_default = get_tarif_revente_s21(_puissance_totale_kw)
            tarif_revente     = float(data.get('tarif_revente') or _tr_s21_default)
            duree_contrat_ans = int(data.get('duree_contrat_ans', 20))
            hc_plages_custom  = data.get('hc_plages_custom', None)  # ex: [[22,6]]
            # ── Option Enedis Data Connect (courbe réelle Linky) ─────────────────
            enedis_pdl        = (data.get('enedis_pdl') or '').strip()
            enedis_token      = (data.get('enedis_token') or '').strip()

            if not zones:
                return jsonify({'error': 'Aucune zone fournie'}), 400
            if consommation_kwh <= 0:
                return jsonify({'error': 'Consommation annuelle invalide'}), 400

            # ── Charger les données 8760h sauvegardées en BDD ────────────────────
            saved_8760h = {}
            try:
                prospect_row = execute_query(
                    "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                    (prospect_id,), fetch_one=True
                )
                if prospect_row:
                    dj = prospect_row['data_json'] or {}
                    if isinstance(dj, str):
                        dj = json.loads(dj)
                    saved_8760h = dj.get('calpinage', {}).get('pvgis_8760h', {})
                    print(f"[AUTOCONSO] Données 8760h disponibles pour zones: {list(saved_8760h.keys())}")
            except Exception as load_err:
                print(f"[AUTOCONSO] Erreur chargement BDD: {load_err}")

            # ── 1. Agréger la production 8760h pour chaque zone ──────────────────
            combined_wh = [0.0] * 8760
            zones_ok = []
            zones_missing = []

            for zone in zones:
                lat        = zone.get('lat') or zone.get('latitude')
                lon        = zone.get('lon') or zone.get('longitude') or zone.get('lng')
                tilt       = float(zone.get('inclinaison', 30))
                azimuth    = float(zone.get('orientation', 180))
                puissance  = float(zone.get('puissance_kw', 1.0))
                zone_num   = zone.get('zone_numero', zone.get('numero', 1))

                if not lat or not lon:
                    continue

                # Chercher les données en cache BDD (int ou str comme clé)
                p_cached = saved_8760h.get(str(zone_num)) or saved_8760h.get(str(int(zone_num)))

                if p_cached and len(p_cached) >= 8760:
                    # ✅ Utiliser les données sauvegardées
                    for i, v in enumerate(p_cached[:8760]):
                        combined_wh[i] += float(v)
                    print(f"[AUTOCONSO] Zone {zone_num}: données BDD utilisées (cache)")
                else:
                    # ⚡ Fallback PVGIS API
                    zones_missing.append(zone_num)
                    pvgis = get_pvgis_hourly(lat, lon, tilt, azimuth, puissance)
                    if pvgis is None:
                        continue
                    hourly = pvgis.get('outputs', {}).get('hourly', [])
                    if len(hourly) < 8760:
                        continue
                    for i, entry in enumerate(hourly[:8760]):
                        combined_wh[i] += float(entry.get('P', 0))
                    print(f"[AUTOCONSO] Zone {zone_num}: appel PVGIS live (pas de cache)")

                zones_ok.append({
                    'zone_numero': zone_num,
                    'puissance_kw': puissance,
                    'lat': lat, 'lon': lon,
                    'inclinaison': tilt, 'orientation': azimuth,
                    'source': 'cache' if not (zone_num in zones_missing) else 'pvgis_live',
                })

            if not zones_ok:
                return jsonify({
                    'error': 'Aucune donnée PVGIS disponible. Cliquez d\'abord sur "Télécharger données 8760h" pour chaque zone.'
                }), 400

            # ── 2. Profil de consommation : Enedis Data Connect ou profil type ────
            data_source        = 'profil_type'
            enedis_dc_profile  = None
            enedis_dc_warning  = None

            if enedis_pdl and enedis_token:
                import config as _cfg
                real_profile = get_enedis_dataconnect_profile(
                    pdl=enedis_pdl,
                    access_token=enedis_token,
                    sandbox=getattr(_cfg, 'ENEDIS_SANDBOX', True),
                )
                if real_profile and len(real_profile) == 8760:
                    enedis_dc_profile = real_profile
                    data_source       = 'enedis_dataconnect'
                    print(f"[AUTOCONSO] ✅ Profil Enedis Data Connect utilisé (PDL={enedis_pdl})")
                else:
                    enedis_dc_warning = (
                        f"Données Enedis Data Connect indisponibles pour le PDL {enedis_pdl}. "
                        f"Calcul effectué avec le profil type {profil_type}."
                    )
                    print(f"[AUTOCONSO] ⚠️  Fallback profil type {profil_type} (PDL={enedis_pdl})")

            # ── 3. Calcul autoconsommation ────────────────────────────────────────
            if enedis_dc_profile:
                # Injecter le profil réel directement dans compute_autoconsommation
                annual_consumption_wh = consommation_kwh * 1000.0
                custom_consumption_wh = [annual_consumption_wh * v for v in enedis_dc_profile]
                result = compute_autoconsommation(
                    hourly_production_wh=combined_wh,
                    annual_consumption_kwh=consommation_kwh,
                    profile_type=profil_type,
                )
                # Remplacer la consommation profilée par la courbe réelle
                h_autoconso = [min(p, c) for p, c in zip(combined_wh, custom_consumption_wh)]
                h_surplus   = [max(p - c, 0.0) for p, c in zip(combined_wh, custom_consumption_wh)]
                h_deficit   = [max(c - p, 0.0) for p, c in zip(combined_wh, custom_consumption_wh)]
                result['hourly_consumption_wh'] = custom_consumption_wh
                result['hourly_autoconso_wh']   = h_autoconso
                result['hourly_surplus_wh']     = h_surplus
                result['hourly_deficit_wh']     = h_deficit
                # Recalcul KPIs avec courbe réelle
                total_prod  = sum(combined_wh)
                total_conso = sum(custom_consumption_wh)
                total_auto  = sum(h_autoconso)
                total_surp  = sum(h_surplus)
                result['kpis'] = {
                    'production_annuelle_kwh'  : round(total_prod / 1000.0, 1),
                    'consommation_annuelle_kwh': round(total_conso / 1000.0, 1),
                    'autoconso_kwh'            : round(total_auto / 1000.0, 1),
                    'surplus_kwh'              : round(total_surp / 1000.0, 1),
                    'deficit_kwh'              : round((total_conso - total_auto) / 1000.0, 1),
                    'taux_autoconsommation'    : round((total_auto / total_prod * 100) if total_prod > 0 else 0, 1),
                    'taux_autosuffisance'      : round((total_auto / total_conso * 100) if total_conso > 0 else 0, 1),
                }
            else:
                result = compute_autoconsommation(
                    hourly_production_wh=combined_wh,
                    annual_consumption_kwh=consommation_kwh,
                    profile_type=profil_type,
                )

            # ── 4. Calcul économique avec tarifs horaires ─────────────────────────
            economics = compute_economics(
                kpis=result['kpis'],
                prix_revente_kwh=tarif_revente,
                tariff_type=tariff_type,
                duree_contrat_ans=duree_contrat_ans,
                hourly_production_wh=combined_wh,
                hourly_consumption_wh=result['hourly_consumption_wh'],
                hourly_autoconso_wh=result['hourly_autoconso_wh'],
                hourly_surplus_wh=result['hourly_surplus_wh'],
                hc_plages_custom=hc_plages_custom,
            )
            print(f"[AUTOCONSO] Tarif: {tariff_type} | Économie an1: {economics['economie_an1']}€")

            # ── Sauvegarder les résultats en BDD pour la proposition ─────────────
            try:
                _row = execute_query(
                    "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                    (prospect_id,), fetch_one=True
                )
                _dj = (_row['data_json'] or {}) if _row else {}
                if isinstance(_dj, str):
                    _dj = json.loads(_dj)
                _dj.setdefault('calpinage', {})['autoconso_results'] = {
                    'kpis'           : result['kpis'],
                    'economics'      : {
                        k: v for k, v in economics.items()
                        if k != 'prix_8760'
                    },
                    'monthly'        : result['monthly'],
                    'daily_profiles' : result['daily_profiles'],
                    'profil_type'    : profil_type,
                    'profil_label'   : PROFILE_LABELS.get(profil_type, profil_type),
                    'data_source'    : data_source,  # 'profil_type' ou 'enedis_dataconnect'
                    'enedis_pdl'     : enedis_pdl if data_source == 'enedis_dataconnect' else None,
                    'tariff_type'    : tariff_type,
                    'tariff_label'   : TARIFF_LABELS.get(tariff_type, tariff_type),
                    'date_calcul'    : datetime.now().isoformat(),
                }
                # Sauvegarder également les paramètres d'entrée pour restaurer le formulaire
                _dj['calpinage']['autoconso_params'] = {
                    'profil_type'     : profil_type,
                    'consommation_kwh': consommation_kwh,
                    'tariff_type'     : tariff_type,
                    'tarif_revente'   : tarif_revente,
                    'duree_contrat_ans': duree_contrat_ans,
                    'pdl'             : enedis_pdl or '',
                }
                execute_query(
                    "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                    (json.dumps(_dj), prospect_id)
                )
                print(f"[AUTOCONSO] Résultats sauvegardés en BDD (prospect {prospect_id})")
                # Marquer l'étape "Étude d'autoconsommation" (ordre 5) comme terminée
                _proj = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                    (prospect_id,), fetch_one=True
                )
                if _proj:
                    execute_query('''
                        UPDATE project_etapes
                        SET statut = 'termine', date_fin_reelle = CURRENT_DATE
                        WHERE project_id = %s AND ordre = 5 AND statut != 'termine'
                    ''', (_proj['id'],))
                    print(f"[AUTOCONSO] ✅ Étape 5 (Étude autoconsommation) marquée terminée (projet {_proj['id']})")
            except Exception as _save_err:
                print(f"[AUTOCONSO] Warn: impossible de sauvegarder résultats BDD: {_save_err}")

            return jsonify({
                'success'        : True,
                'zones_traitees' : zones_ok,
                'profil_type'    : profil_type,
                'profil_label'   : PROFILE_LABELS.get(profil_type, profil_type),
                'tariff_type'    : tariff_type,
                'tariff_label'   : TARIFF_LABELS.get(tariff_type, tariff_type),
                'data_source'    : data_source,
                'enedis_pdl'     : enedis_pdl or None,
                'enedis_warning' : enedis_dc_warning,
                'monthly'        : result['monthly'],
                'daily_profiles' : result['daily_profiles'],
                'kpis'           : result['kpis'],
                'economics'      : economics,
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/autoconsommation/profils', methods=['GET'])
    def get_profils_liste():
        """Retourne la liste des profils de consommation disponibles."""
        try:
            from autoconsommation import PROFILE_LABELS
            return jsonify({
                'profils': [
                    {'code': k, 'label': v}
                    for k, v in PROFILE_LABELS.items()
                ]
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/autoconso-params', methods=['PATCH'])
    def save_autoconso_params(prospect_id):
        """Sauvegarder uniquement les paramètres du formulaire autoconsommation (sans calcul)."""
        try:
            data = request.json or {}
            profil_type       = str(data.get('profil_type', 'RES1'))[:10]
            consommation_kwh  = float(data.get('consommation_kwh', 0) or 0)
            tariff_type       = str(data.get('tariff_type', 'BASE'))[:20]
            tarif_revente     = float(data.get('tarif_revente', 0) or 0)
            duree_contrat_ans = int(data.get('duree_contrat_ans', 20) or 20)
            pdl               = str(data.get('pdl', '') or '')[:14]

            row = execute_query(
                "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not row:
                return jsonify({'error': 'Prospect non trouvé'}), 404

            dj = row['data_json'] or {}
            if isinstance(dj, str):
                dj = json.loads(dj)

            dj.setdefault('calpinage', {})['autoconso_params'] = {
                'profil_type'     : profil_type,
                'consommation_kwh': consommation_kwh,
                'tariff_type'     : tariff_type,
                'tarif_revente'   : tarif_revente,
                'duree_contrat_ans': duree_contrat_ans,
                'pdl'             : pdl,
            }
            execute_query(
                "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                (json.dumps(dj), prospect_id)
            )
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # ──────────────────────────────────────────────────────────────────────────
    # ENEDIS DATA CONNECT – Routes OAuth 2.0
    # ──────────────────────────────────────────────────────────────────────────

    @app.route('/api/enedis/dc/authorize-url', methods=['GET'])
    def enedis_dc_authorize_url():
        """
        Retourne l'URL de consentement Enedis Data Connect.
        Le front affiche un bouton/lien vers cette URL pour que le client
        s'authentifie sur son espace Enedis et autorise le partage de son PDL.

        Query params optionnels :
          state : valeur aléatoire anti-CSRF (recommandé, générer côté front)
        """
        import config as _cfg
        import secrets

        client_id    = getattr(_cfg, 'ENEDIS_CLIENT_ID', '')
        redirect_uri = getattr(_cfg, 'ENEDIS_REDIRECT_URI', '')

        if not client_id or not redirect_uri:
            return jsonify({
                'error': (
                    'Enedis Data Connect non configuré. '
                    'Définissez ENEDIS_CLIENT_ID et ENEDIS_REDIRECT_URI dans les variables d\'environnement.'
                )
            }), 503

        from autoconsommation import get_enedis_authorize_url
        state = request.args.get('state') or secrets.token_urlsafe(16)
        url   = get_enedis_authorize_url(client_id, redirect_uri, state)

        return jsonify({
            'authorize_url': url,
            'state'        : state,
            'redirect_uri' : redirect_uri,
        })

    @app.route('/api/enedis/dc/callback', methods=['GET'])
    def enedis_dc_callback():
        """
        Callback OAuth Enedis Data Connect.
        Enedis redirige ici après le consentement du client avec ?code=XXX&state=YYY.
        Ce endpoint échange le code contre un access_token et renvoie les infos au front.

        Le token retourné doit être fourni dans le body de /autoconsommation
        sous la clé 'enedis_token', accompagné du PDL ('enedis_pdl').
        """
        import config as _cfg
        from autoconsommation import exchange_enedis_code_for_token

        code  = request.args.get('code', '')
        state = request.args.get('state', '')
        error = request.args.get('error', '')

        if error:
            # Le client a refusé ou une erreur s'est produite côté Enedis
            return jsonify({
                'success': False,
                'error'  : error,
                'message': request.args.get('error_description', 'Autorisation refusée par le client'),
            }), 400

        if not code:
            return jsonify({'success': False, 'error': 'missing_code'}), 400

        client_id     = getattr(_cfg, 'ENEDIS_CLIENT_ID', '')
        client_secret = getattr(_cfg, 'ENEDIS_CLIENT_SECRET', '')
        redirect_uri  = getattr(_cfg, 'ENEDIS_REDIRECT_URI', '')
        sandbox       = getattr(_cfg, 'ENEDIS_SANDBOX', True)

        if not client_id or not client_secret:
            return jsonify({'success': False, 'error': 'enedis_not_configured'}), 503

        try:
            token_data = exchange_enedis_code_for_token(
                code=code,
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                sandbox=sandbox,
            )
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 502

        # usage_points_id liste les PDL autorisés par le client (séparés par virgule)
        usage_points = token_data.get('usage_points_id', '')
        pdl_list = [p.strip() for p in usage_points.split(',') if p.strip()] if usage_points else []

        return jsonify({
            'success'       : True,
            'access_token'  : token_data.get('access_token'),
            'token_type'    : token_data.get('token_type', 'Bearer'),
            'expires_in'    : token_data.get('expires_in'),
            'refresh_token' : token_data.get('refresh_token'),
            'pdl_list'      : pdl_list,
            'state'         : state,
        })

    # ========================================
    # ROUTES VISITE TECHNIQUE
    # ========================================

    @app.route('/crm/prospect/<int:prospect_id>/visite-technique')
    def page_visite_technique(prospect_id):
        """Page de formulaire visite technique pour un prospect"""
        try:
            from datetime import date
            
            # Récupérer le prospect
            result = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not result:
                return "Prospect non trouvé", 404
            
            prospect_dict = dict(result)
            
            # Récupérer les données de visite existantes
            visite_data = None
            if prospect_dict.get('data_json'):
                try:
                    data_json = json.loads(prospect_dict['data_json']) if isinstance(prospect_dict['data_json'], str) else prospect_dict['data_json']
                    visite_data = data_json.get('visite_technique')
                except:
                    pass
            
            return render_template('visite_technique.html', 
                                 prospect=prospect_dict, 
                                 visite_data=visite_data,
                                 today=date.today().isoformat())
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}", 500
    
    @app.route('/api/crm/prospects/<int:prospect_id>/visite-technique', methods=['POST'])
    def save_visite_technique(prospect_id):
        """Sauvegarder les données de visite technique"""
        try:
            data = request.json
            print(f"[VISITE TECHNIQUE SAVE] prospect_id={prospect_id}")
            
            # Récupérer le prospect
            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not row:
                return jsonify({'success': False, 'error': 'Prospect non trouvé'}), 404
            
            prospect = dict(row)
            
            # Parser le JSON existant
            try:
                current_data = json.loads(prospect['data_json']) if prospect['data_json'] else {}
            except:
                current_data = {}
            
            # Ajouter les données de visite technique
            current_data['visite_technique'] = data
            current_data['visite_technique']['date_sauvegarde'] = datetime.now().isoformat()
            
            # Mettre à jour
            execute_query("""
                UPDATE agriweb_prospects 
                SET data_json = %s,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(current_data), prospect_id))
            
            print(f"[VISITE TECHNIQUE SAVE] ✅ Prospect {prospect_id} mis à jour")
            
            # Chercher ou créer un projet pour ce prospect
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,),
                fetch_one=True
            )
            
            if not project:
                # Créer un nouveau projet
                print(f"[VISITE TECHNIQUE SAVE] Pas de projet existant, création...")
                
                # Récupérer user_id du prospect
                prospect_owner = execute_query('SELECT user_id FROM agriweb_prospects WHERE id = %s', (prospect_id,), fetch_one=True)
                owner_id = prospect_owner.get('user_id') if prospect_owner else None
                result = execute_query('''
                    INSERT INTO project_fiches (
                        prospect_id, nom_projet, statut_projet,
                        date_creation, date_modification, user_id
                    ) VALUES (
                        %s, %s, 'en_cours',
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s
                    )
                    RETURNING id
                ''', (prospect_id, f"Projet PV - {prospect.get('nom', '')} {prospect.get('prenom', '')}", owner_id),
                fetch_one=True)
                
                if result:
                    project_id = result['id']
                    print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id} créée via visite technique")
                    
                    # Créer les étapes
                    etapes_autoconso = [
                        ('Rapport de recherche HeliaPV', 1),
                        ('Visite technique', 2),
                        ('Calepinage', 3),
                        ('Plan de masse', 4),
                        ('Étude d\'autoconsommation', 5),
                        ('Devis commercial', 6),
                        ('Signature & Facture', 7),
                        ('Déclaration Préalable de Travaux (DP)', 8),
                        ('Déclaration de Raccordement (DDR)', 9),
                        ('Installation & DOE', 10),
                        ('Consuel', 11),
                        ('Mise en service & Maintenance', 12)
                    ]
                    
                    for etape_nom, ordre in etapes_autoconso:
                        # L'étape visite technique (2) est terminée
                        statut = 'termine' if ordre == 2 else 'a_faire'
                        date_fin = 'CURRENT_DATE' if ordre == 2 else 'NULL'
                        execute_query(f'''
                            INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                            VALUES (%s, %s, %s, %s, {date_fin})
                        ''', (project_id, etape_nom, ordre, statut))
                    
                    print(f"✅ [ETAPES CREATE] 12 étapes créées, étape 2 (Visite technique) terminée")
            else:
                # Marquer l'étape "Visite technique" (ordre 2) comme terminée
                execute_query('''
                    UPDATE project_etapes 
                    SET statut = 'termine', 
                        date_fin_reelle = CURRENT_DATE
                    WHERE project_id = %s 
                    AND ordre = 2
                    AND statut != 'termine'
                ''', (project['id'],))
                print(f"✅ [ETAPE UPDATE] Étape 2 (Visite technique) marquée comme terminée pour projet {project['id']}")
            
            # Synchroniser data_json vers la fiche projet
            if project:
                try:
                    execute_query('''
                        UPDATE project_fiches 
                        SET data_json = %s, date_modification = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (json.dumps(current_data), project['id']))
                    print(f"✅ [PROJECT SYNC] data_json synchronisé vers fiche projet {project['id']}")
                except Exception as sync_err:
                    print(f"⚠️ [PROJECT SYNC] Erreur synchro visite→projet: {sync_err}")
            
            return jsonify({
                'success': True,
                'message': 'Visite technique sauvegardée avec succès'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
    
    @app.route('/crm/prospect/<int:prospect_id>/calpinage')
    @require_prospect_owner
    def page_calpinage_pv(prospect_id):
        """Page de calpinage photovoltaïque pour un prospect"""
        try:
            # Récupérer le prospect
            result = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )

            if not result:
                return "Prospect non trouvé", 404

            # Convertir en dictionnaire
            prospect_dict = dict(result)

            print(f"[CALPINAGE PAGE] prospect_id={prospect_id}")
            print(f"[CALPINAGE PAGE] data_json type: {type(prospect_dict.get('data_json'))}")

            # Parser data_json si c'est une chaîne
            if prospect_dict.get('data_json') and isinstance(prospect_dict['data_json'], str):
                try:
                    prospect_dict['data_json'] = json.loads(prospect_dict['data_json'])
                    print(f"[CALPINAGE PAGE] data_json parsed, keys: {list(prospect_dict['data_json'].keys())}")
                    if 'calpinage' in prospect_dict['data_json']:
                        calp = prospect_dict['data_json']['calpinage']
                        print(f"[CALPINAGE PAGE] calpinage found, zones: {len(calp.get('zones', []))}")
                except Exception as e:
                    print(f"[CALPINAGE PAGE] Erreur parsing data_json: {e}")
                    prospect_dict['data_json'] = {}
            elif not prospect_dict.get('data_json'):
                print(f"[CALPINAGE PAGE] data_json est vide/None")
                prospect_dict['data_json'] = {}

            current_user_id, is_admin = get_current_crm_user()

            # Feature flag granulaire : 3D Calpinage. Migration auto-idempotente
            # de la colonne feature_3d_calpinage sur users. Permet d'autoriser
            # certains prospects (Tryba, etc.) sans leur donner le statut admin.
            can_use_3d = is_admin
            try:
                execute_query("""
                    ALTER TABLE users
                    ADD COLUMN IF NOT EXISTS feature_3d_calpinage BOOLEAN DEFAULT FALSE
                """)
                if current_user_id is not None and not is_admin:
                    flag_row = execute_query(
                        "SELECT feature_3d_calpinage FROM users WHERE id = %s",
                        (current_user_id,),
                        fetch_one=True
                    )
                    if flag_row and flag_row.get('feature_3d_calpinage'):
                        can_use_3d = True
            except Exception as e:
                print(f"⚠️ [FEATURE 3D] erreur check flag : {e}")

            return render_template(
                'calpinage_pv.html',
                prospect=prospect_dict,
                is_admin=is_admin,
                can_use_3d=can_use_3d,
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}", 500
    
    @app.route('/api/crm/prospects/<int:prospect_id>/calpinage', methods=['POST'])
    @require_prospect_owner
    def save_calpinage(prospect_id):
        """Sauvegarder les données de calpinage dans data_json du prospect"""
        try:
            data = request.json
            screenshot_present = 'screenshot_map' in data and data.get('screenshot_map')
            screenshot_len = len(data.get('screenshot_map', '')) if screenshot_present else 0
            print(f"[CALPINAGE SAVE] prospect_id={prospect_id}, zones={len(data.get('zones', []))}, screenshot={'✅ OUI' if screenshot_present else '❌ NON'} ({screenshot_len} chars)")
            
            # Récupérer le prospect
            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not row:
                print(f"[CALPINAGE SAVE] Prospect {prospect_id} non trouvé")
                return jsonify({'success': False, 'error': 'Prospect non trouvé'}), 404
            
            prospect = dict(row)
            
            # Parser le JSON existant ou créer un nouveau
            try:
                current_data = json.loads(prospect['data_json']) if prospect['data_json'] else {}
            except:
                current_data = {}
            
            # Ajouter les données de calpinage
            # Préserver les champs volumétriques existants (screenshots) si non fournis dans ce save
            # AUSSI préserver autoconso_results, autoconso_params et pvgis_8760h qui sont stockés
            # dans le calpinage mais jamais envoyés par le frontend lors d'un save calpinage,
            # sinon chaque re-sauvegarde du calpinage efface l'étude autoconsommation.
            old_calp = current_data.get('calpinage', {}) if isinstance(current_data, dict) else {}
            for preserve_key in ('screenshot_map', 'screenshot_plan_masse', 'screenshot_3d',
                                 'screenshot_irradiation', 'screenshot_irradiation_bbox',
                                 'screenshot_situation_z14',
                                 'map_metadata', 'plan_masse_metadata',
                                 'autoconso_results', 'autoconso_params', 'pvgis_8760h'):
                if not data.get(preserve_key) and old_calp.get(preserve_key):
                    data[preserve_key] = old_calp[preserve_key]
            current_data['calpinage'] = data
            current_data['calpinage']['date_maj'] = datetime.now().isoformat()
            
            # Mettre à jour data_json du prospect
            execute_query("""
                UPDATE agriweb_prospects 
                SET data_json = %s,
                    date_modification = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (json.dumps(current_data), prospect_id))
            
            print(f"[CALPINAGE SAVE] ✅ Prospect {prospect_id} mis à jour")
            
            # Synchroniser avec la fiche projet
            try:
                # Chercher le projet existant pour ce prospect
                project = execute_query(
                    'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                    (prospect_id,),
                    fetch_one=True
                )
                
                if not project:
                    # Créer un nouveau projet
                    print(f"[CALPINAGE SAVE] Pas de projet existant, création...")
                    commune = prospect.get('commune', '')
                    adresse = prospect.get('adresse_complete', '') or prospect.get('adresse', '')
                    
                    # Récupérer user_id du prospect
                    prospect_owner = execute_query('SELECT user_id FROM agriweb_prospects WHERE id = %s', (prospect_id,), fetch_one=True)
                    owner_id = prospect_owner.get('user_id') if prospect_owner else None
                    result = execute_query('''
                        INSERT INTO project_fiches (
                            prospect_id, nom_projet, commune, adresse_projet,
                            statut_projet, data_json,
                            date_creation, date_modification, user_id
                        ) VALUES (
                            %s, %s, %s, %s, 'etude', %s,
                            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, %s
                        )
                        RETURNING id
                    ''', (
                        prospect_id,
                        f"Projet PV - {commune or adresse or prospect_id}",
                        commune,
                        adresse,
                        json.dumps(current_data),
                        owner_id
                    ), fetch_one=True)
                    
                    if result:
                        project_id_fiche = result['id']
                        print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id_fiche} créée via calpinage")
                        
                        # Créer les étapes du workflow
                        etapes_autoconso = [
                            ('Rapport de recherche HeliaPV', 1),
                            ('Visite technique', 2),
                            ('Calepinage', 3),
                            ('Plan de masse', 4),
                            ('Étude d\'autoconsommation', 5),
                            ('Devis commercial', 6),
                            ('Signature & Facture', 7),
                            ('Déclaration Préalable de Travaux (DP)', 8),
                            ('Déclaration de Raccordement (DDR)', 9),
                            ('Installation & DOE', 10),
                            ('Consuel', 11),
                            ('Mise en service & Maintenance', 12)
                        ]
                        
                        _has_pdm = bool(data.get('screenshot_plan_masse'))
                        for etape_nom, ordre in etapes_autoconso:
                            statut = 'termine' if ordre == 3 or (ordre == 4 and _has_pdm) else 'a_faire'
                            _done = (ordre == 3 or (ordre == 4 and _has_pdm))
                            execute_query('''
                                INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                                VALUES (%s, %s, %s, %s, {})
                            '''.format('CURRENT_DATE' if _done else 'NULL'),
                            (project_id_fiche, etape_nom, ordre, statut))
                        
                        print(f"✅ [ETAPES CREATE] 12 étapes créées pour projet {project_id_fiche}")
                        project = {'id': project_id_fiche}
                
                if project:
                    # Mettre à jour la fiche projet avec les données PV du calpinage
                    totaux = current_data.get('calpinage', {}).get('totaux', {})
                    puissance_kwc = float(totaux.get('puissanceTotale', 0))
                    productible_mwh = float(totaux.get('productibleTotal', 0))
                    zones = current_data.get('calpinage', {}).get('zones', [])
                    nb_panneaux = sum(z.get('nbModules', 0) for z in zones)
                    
                    execute_query('''
                        UPDATE project_fiches 
                        SET data_json = %s,
                            puissance_kwc = %s,
                            production_annuelle_kwh = %s,
                            productible_mwh = %s,
                            nombre_panneaux = %s,
                            puissance_estimee = %s,
                            date_modification = CURRENT_TIMESTAMP
                        WHERE id = %s
                    ''', (
                        json.dumps(current_data),
                        puissance_kwc,
                        puissance_kwc * 1100,  # Estimation kWh/an
                        productible_mwh,
                        nb_panneaux,
                        puissance_kwc,
                        project['id']
                    ))
                    
                    # Marquer l'étape Calepinage comme terminée (par nom, indépendamment de l'ordre)
                    execute_query('''
                        UPDATE project_etapes 
                        SET statut = 'termine', 
                            date_fin_reelle = CURRENT_DATE
                        WHERE project_id = %s 
                        AND nom_etape = 'Calepinage'
                        AND statut != 'termine'
                    ''', (project['id'],))
                    
                    # Insérer l'étape "Plan de masse" si elle n'existe pas encore
                    # Vérifier qu'il n'y a pas déjà un autre step à ordre=4 (anciens projets)
                    # pour éviter les doublons d'ordre
                    _existing_ordre4 = execute_query(
                        'SELECT id FROM project_etapes WHERE project_id = %s AND ordre = 4',
                        (project['id'],), fetch_one=True
                    )
                    _existing_pdm = execute_query(
                        "SELECT id FROM project_etapes WHERE project_id = %s AND nom_etape = 'Plan de masse'",
                        (project['id'],), fetch_one=True
                    )
                    if not _existing_pdm:
                        if _existing_ordre4:
                            # Ancien schéma : décaler toutes les étapes >= 4 pour faire de la place
                            execute_query('''
                                UPDATE project_etapes SET ordre = ordre + 1
                                WHERE project_id = %s AND ordre >= 4
                            ''', (project['id'],))
                            print(f"🔧 [MIGRATION] Étapes ordre ≥4 décalées +1 pour projet {project['id']}")
                        execute_query('''
                            INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                            VALUES (%s, 'Plan de masse', 4, 'a_faire', NULL)
                        ''', (project['id'],))
                        print(f"✅ [ETAPE INSERT] 'Plan de masse' (ordre 4) insérée pour projet {project['id']}")
                    
                    # Marquer "Plan de masse" terminé si screenshot_plan_masse disponible
                    if data.get('screenshot_plan_masse'):
                        execute_query('''
                            UPDATE project_etapes 
                            SET statut = 'termine', 
                                date_fin_reelle = CURRENT_DATE
                            WHERE project_id = %s 
                            AND nom_etape = 'Plan de masse'
                            AND statut != 'termine'
                        ''', (project['id'],))
                        print(f"✅ [PROJECT SYNC] Étape 'Plan de masse' marquée terminée pour projet {project['id']}")
                    
                    print(f"✅ [PROJECT SYNC] Fiche projet {project['id']} mise à jour: {puissance_kwc} kWc, {nb_panneaux} panneaux")
                    
            except Exception as e:
                print(f"⚠️ [CALPINAGE→PROJET] Erreur synchro projet: {e}")
                import traceback
                traceback.print_exc()
            
            return jsonify({
                'success': True,
                'message': 'Calpinage sauvegardé avec succès'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/calpinage/export-dxf')
    def export_calpinage_dxf(prospect_id):
        """Exporter le calpinage PV en format DXF (AutoCAD / LibreCAD / BricsCAD)"""
        try:
            import ezdxf
            from pyproj import Transformer

            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not row:
                return jsonify({'error': 'Prospect non trouve'}), 404

            prospect = dict(row)
            try:
                data_json = json.loads(prospect['data_json']) if prospect['data_json'] else {}
            except Exception:
                data_json = {}

            calpinage = data_json.get('calpinage', {})
            zones = calpinage.get('zones', [])
            if not zones:
                return jsonify({'error': 'Aucun calpinage sauvegarde. Veuillez d\'abord sauvegarder le calpinage.'}), 400

            # Transformer GPS (EPSG:4326) -> Lambert 93 (EPSG:2154) - coordonnees metriques France
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

            def gps_to_m(lat, lng):
                x, y = transformer.transform(lng, lat)
                return x, y

            # Centroide de toutes les zones => origine locale (coordonnees relatives en metres)
            all_pts = []
            for zone in zones:
                for c in zone.get('coordinates', []):
                    all_pts.append(gps_to_m(c['lat'], c['lng']))

            if not all_pts:
                return jsonify({'error': 'Aucune coordonnee trouvee dans le calpinage.'}), 400

            origin_x = sum(p[0] for p in all_pts) / len(all_pts)
            origin_y = sum(p[1] for p in all_pts) / len(all_pts)

            def to_local(lat, lng):
                x, y = gps_to_m(lat, lng)
                return (x - origin_x, y - origin_y)

            # --- Document DXF ---
            doc = ezdxf.new(dxfversion='R2010')
            msp = doc.modelspace()

            doc.layers.add('ZONES_PV',          color=3)   # vert
            doc.layers.add('MODULES_PV',          color=5)   # bleu
            doc.layers.add('ANNOTATIONS',         color=1)   # rouge
            doc.layers.add('INFOS_PROJET',        color=7)   # blanc
            doc.layers.add('BATIMENT_PRINCIPAL',  color=2)   # jaune
            doc.layers.add('PARCELLES',           color=6)   # magenta
            doc.layers.add('ENV_BATIMENTS',       color=8)   # gris

            totaux = calpinage.get('totaux', {})
            nom = (prospect.get('nom') or prospect.get('adresse') or f"Prospect {prospect_id}").strip()
            commune = prospect.get('commune', '') or ''
            puissance_totale = float(totaux.get('puissanceTotale') or sum(z.get('puissanceKw', 0) for z in zones))
            nb_modules_total = int(totaux.get('nombreModules') or sum(z.get('nbModules', 0) for z in zones))

            # En-tete projet (positionne sous l'origine)
            msp.add_text(
                f"HeliaPV - Calpinage PV - {nom}",
                dxfattribs={'layer': 'INFOS_PROJET', 'height': 0.5, 'insert': (0, -3)}
            )
            if commune:
                msp.add_text(
                    commune,
                    dxfattribs={'layer': 'INFOS_PROJET', 'height': 0.3, 'insert': (0, -3.8)}
                )
            msp.add_text(
                f"Puissance crete : {puissance_totale:.2f} kWc  |  {nb_modules_total} modules",
                dxfattribs={'layer': 'INFOS_PROJET', 'height': 0.3, 'insert': (0, -4.6)}
            )

            for zone in zones:
                num = zone.get('numero', '?')
                coords = zone.get('coordinates', [])
                modules_pos = zone.get('modulesPositions', [])
                orientation = zone.get('orientation', 0)
                inclinaison = zone.get('inclinaison', 30)
                nb_mod = zone.get('nbModules', 0)
                puissance_kw = float(zone.get('puissanceKw', 0))

                # Contour de la zone pour le DXF
                # Priorité : zone_outline_coords (champ réel après reculs + rotation),
                # sinon : enveloppe convexe des modules, sinon : polygone dessiné
                zone_outline = zone.get('zone_outline_coords') or []
                if len(zone_outline) >= 3:
                    pts_zone = [to_local(c['lat'], c['lng']) for c in zone_outline]
                    msp.add_lwpolyline(
                        pts_zone,
                        dxfattribs={'layer': 'ZONES_PV', 'closed': True}
                    )
                elif modules_pos:
                    # Fallback : enveloppe convexe des coins des modules
                    try:
                        from shapely.geometry import MultiPoint as _MP
                        mod_pts = [to_local(c['lat'], c['lng'])
                                   for m in modules_pos for c in m.get('corners', [])]
                        if len(mod_pts) >= 3:
                            hull = _MP(mod_pts).convex_hull
                            if hull.geom_type == 'Polygon':
                                msp.add_lwpolyline(
                                    list(hull.exterior.coords),
                                    dxfattribs={'layer': 'ZONES_PV', 'closed': True}
                                )
                    except Exception:
                        if len(coords) >= 3:
                            msp.add_lwpolyline(
                                [to_local(c['lat'], c['lng']) for c in coords],
                                dxfattribs={'layer': 'ZONES_PV', 'closed': True}
                            )
                elif len(coords) >= 3:
                    pts_zone = [to_local(c['lat'], c['lng']) for c in coords]
                    msp.add_lwpolyline(
                        pts_zone,
                        dxfattribs={'layer': 'ZONES_PV', 'closed': True}
                    )

                # Modules individuels (rectangles)
                for mod in modules_pos:
                    corners = mod.get('corners', [])
                    if len(corners) >= 4:
                        pts_mod = [to_local(c['lat'], c['lng']) for c in corners[:4]]
                        msp.add_lwpolyline(
                            pts_mod,
                            dxfattribs={'layer': 'MODULES_PV', 'closed': True}
                        )

                # Annotations au centroide de la zone
                # Utiliser le centre des modules si disponibles, sinon centroide des coords
                if modules_pos:
                    all_mod_lats = [c['lat'] for m in modules_pos for c in m.get('corners', [])]
                    all_mod_lngs = [c['lng'] for m in modules_pos for c in m.get('corners', [])]
                    if all_mod_lats:
                        clat = (min(all_mod_lats) + max(all_mod_lats)) / 2
                        clng = (min(all_mod_lngs) + max(all_mod_lngs)) / 2
                    elif coords:
                        clat = sum(c['lat'] for c in coords) / len(coords)
                        clng = sum(c['lng'] for c in coords) / len(coords)
                    else:
                        clat = clng = None
                elif coords:
                    clat = sum(c['lat'] for c in coords) / len(coords)
                    clng = sum(c['lng'] for c in coords) / len(coords)
                else:
                    clat = clng = None

                if clat is not None:
                    lx, ly = to_local(clat, clng)
                    orientation_display = round(float(orientation)) if orientation else 0
                    msp.add_text(
                        f"Zone {num}",
                        dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.4, 'insert': (lx, ly + 1.0)}
                    )
                    msp.add_text(
                        f"{nb_mod} modules - {puissance_kw:.2f} kWc",
                        dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.25, 'insert': (lx, ly + 0.5)}
                    )
                    msp.add_text(
                        f"Orient.: {orientation_display} deg  Incl.: {inclinaison} deg",
                        dxfattribs={'layer': 'ANNOTATIONS', 'height': 0.2, 'insert': (lx, ly + 0.0)}
                    )

            # --- Bâtiment PV principal (empreinte sauvegardée par le viewer 3D) ---
            # Format building_coords : [[lon, lat], ...] (GeoJSON)
            building_coords = calpinage.get('building_coords', [])
            if len(building_coords) >= 3:
                pts_bat = [to_local(c[1], c[0]) for c in building_coords]  # [lon,lat] → to_local(lat, lng)
                msp.add_lwpolyline(
                    pts_bat,
                    dxfattribs={'layer': 'BATIMENT_PRINCIPAL', 'closed': True}
                )

            # --- Parcelles cadastrales (sauvegardées depuis la couche Leaflet) ---
            # Format parcelle_polygons : [[{lat, lng}, ...], ...]
            for poly_pts in calpinage.get('parcelle_polygons', []):
                if len(poly_pts) >= 3:
                    pts_parc = [to_local(p['lat'], p['lng']) for p in poly_pts]
                    msp.add_lwpolyline(
                        pts_parc,
                        dxfattribs={'layer': 'PARCELLES', 'closed': True}
                    )

            # --- Bâtiments environnants (OSM Overpass, rayon 150 m) ---
            try:
                import requests as _req
                prospect_lat = float(prospect.get('latitude') or 0)
                prospect_lon = float(prospect.get('longitude') or 0)
                if prospect_lat and prospect_lon:
                    overpass_q = f"""[out:json][timeout:12];
(way["building"](around:150,{prospect_lat},{prospect_lon}););
out geom tags;"""
                    r_osm = _req.post(
                        'https://overpass-api.de/api/interpreter',
                        data=overpass_q, timeout=15
                    )
                    if r_osm.status_code == 200:
                        for elem in r_osm.json().get('elements', []):
                            geom_pts = elem.get('geometry', [])
                            if len(geom_pts) >= 3:
                                # GeoJSON format: lon first
                                pts_env = [to_local(p['lat'], p['lon']) for p in geom_pts]
                                msp.add_lwpolyline(
                                    pts_env,
                                    dxfattribs={'layer': 'ENV_BATIMENTS', 'closed': True}
                                )
            except Exception as e_osm:
                print(f'[DXF] OSM Overpass ignoré: {e_osm}')

            # ezdxf >= 1.x : doc.write() attend un flux texte (StringIO)
            text_stream = io.StringIO()
            doc.write(text_stream)
            byte_stream = io.BytesIO(text_stream.getvalue().encode('utf-8'))
            byte_stream.seek(0)

            nom_fichier = f"calpinage_pv_{prospect_id}.dxf"
            return send_file(
                byte_stream,
                mimetype='application/dxf',
                as_attachment=True,
                download_name=nom_fichier
            )

        except ImportError:
            return jsonify({'error': 'Module ezdxf non disponible. Contactez l\'administrateur.'}), 500
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/calpinage/export-dxf-3d')
    def export_calpinage_dxf_3d(prospect_id):
        """Exporter le calpinage PV en DXF 3D.
        Altitudes normalisées : Z=0 = sol au niveau du prospect.
        - Terrain MNT : grille de polylignes 3D (LiDAR HD IGN, 20×20)
        - Bâtiments BD TOPO : wireframe 3D (contour bas + contour haut + arêtes)
        - Modules PV  : 3DFACE inclinés (orientation + inclinaison)
        """
        try:
            import ezdxf
            import math as _math
            import numpy as _np
            from pyproj import Transformer
            import requests as _req

            # ── 1. Charger le calpinage ──────────────────────────────────────────────
            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not row:
                return jsonify({'error': 'Prospect non trouvé'}), 404

            prospect = dict(row)
            try:
                data_json = json.loads(prospect['data_json']) if prospect['data_json'] else {}
            except Exception:
                data_json = {}

            calpinage = data_json.get('calpinage', {})
            zones = calpinage.get('zones', [])
            if not zones:
                return jsonify({'error': 'Aucun calpinage sauvegardé.'}), 400

            prospect_lat = float(prospect.get('latitude') or 0)
            prospect_lon = float(prospect.get('longitude') or 0)
            if not prospect_lat or not prospect_lon:
                return jsonify({'error': 'Coordonnées du prospect manquantes.'}), 400

            # ── 2. Projection Lambert 93 ─────────────────────────────────────────────
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)

            def gps_to_l93(lat, lng):
                x, y = transformer.transform(lng, lat)
                return x, y

            # Origine locale XY = centroide des zones
            all_pts = []
            for zone in zones:
                for c in zone.get('coordinates', []):
                    all_pts.append(gps_to_l93(c['lat'], c['lng']))
            if not all_pts:
                return jsonify({'error': 'Aucune coordonnée de zone.'}), 400

            ox = sum(p[0] for p in all_pts) / len(all_pts)
            oy = sum(p[1] for p in all_pts) / len(all_pts)

            def to_xy(lat, lng):
                x, y = gps_to_l93(lat, lng)
                return (x - ox, y - oy)

            # ── 3. Terrain MNT via API IGN altimétrie ───────────────────────────────
            radius_m = 200
            lat_deg_per_m = 1 / 111320
            lng_deg_per_m = 1 / (111320 * _math.cos(_math.radians(prospect_lat)))
            mnt_terrain = None
            terrain_bbox = None
            z_ground = 0.0          # altitude NGF du sol au niveau du prospect
            GRID = 20               # 20×20 → 40 polylignes, léger et lisible

            try:
                lat_min = prospect_lat - radius_m * lat_deg_per_m
                lat_max = prospect_lat + radius_m * lat_deg_per_m
                lon_min = prospect_lon - radius_m * lng_deg_per_m
                lon_max = prospect_lon + radius_m * lng_deg_per_m
                terrain_bbox = (lat_min, lat_max, lon_min, lon_max)

                pts_lats, pts_lons = [], []
                for iy in range(GRID):
                    for ix in range(GRID):
                        pts_lats.append(lat_min + (iy + 0.5) / GRID * (lat_max - lat_min))
                        pts_lons.append(lon_min + (ix + 0.5) / GRID * (lon_max - lon_min))

                r_alti = _req.post(
                    'https://data.geopf.fr/altimetrie/1.0/calcul/alti/rest/elevation.json',
                    json={
                        'lon': '|'.join(f'{v:.8f}' for v in pts_lons),
                        'lat': '|'.join(f'{v:.8f}' for v in pts_lats),
                        'resource': 'ign_lidar_hd_mnx_mono_wld',
                        'delimiter': '|', 'indent': 'false',
                        'measures': 'true', 'zonly': 'false'
                    }, timeout=30
                )
                if r_alti.status_code == 200:
                    elevs = r_alti.json().get('elevations', [])
                    mnt_vals = []
                    for e in elevs:
                        z = e.get('z', -99999)
                        for m in e.get('measures', []):
                            if 'mnt' in m.get('title', '').lower():
                                z = m.get('z', z)
                                break
                        mnt_vals.append(z if z > -9000 else None)
                    if len(mnt_vals) == GRID * GRID:
                        valid_z = [v for v in mnt_vals if v is not None]
                        fill_z  = (sum(valid_z) / len(valid_z)) if valid_z else 0.0
                        mnt_terrain = _np.array(
                            [v if v is not None else fill_z for v in mnt_vals],
                            dtype=_np.float64
                        ).reshape(GRID, GRID)
                        # Z de référence = altitude du sol sous le prospect
                        ix_pr = min(GRID-1, max(0, int((prospect_lon - lon_min) / (lon_max - lon_min) * GRID)))
                        iy_pr = min(GRID-1, max(0, int((prospect_lat - lat_min) / (lat_max - lat_min) * GRID)))
                        z_ground = float(mnt_terrain[iy_pr, ix_pr])
                        print(f'[DXF3D] MNT {GRID}×{GRID}, z_ground={z_ground:.1f}m, relief={mnt_terrain.min():.1f}-{mnt_terrain.max():.1f}m')
            except Exception as e_mnt:
                print(f'[DXF3D] MNT ignoré: {e_mnt}')

            # ── 4. BD TOPO WFS bâtiments ─────────────────────────────────────────────
            bdtopo_buildings = []
            try:
                from pyproj import Transformer as _T2
                t2 = _T2.from_crs('EPSG:4326', 'EPSG:2154', always_xy=True)
                cx_wfs, cy_wfs = t2.transform(prospect_lon, prospect_lat)
                r_wfs = _req.get(
                    'https://data.geopf.fr/wfs/ows',
                    params={
                        'service': 'WFS', 'version': '2.0.0', 'request': 'GetFeature',
                        'typeName': 'BDTOPO_V3:batiment',
                        'outputFormat': 'application/json',
                        'bbox': f'{cx_wfs-radius_m},{cy_wfs-radius_m},{cx_wfs+radius_m},{cy_wfs+radius_m},EPSG:2154',
                        'srsName': 'EPSG:4326', 'count': '100'
                    }, timeout=15
                )
                if r_wfs.status_code == 200:
                    for feat in r_wfs.json().get('features', []):
                        geom  = feat.get('geometry', {})
                        props = feat.get('properties', {})
                        gtype = geom.get('type', '')
                        if gtype == 'MultiPolygon':
                            coords = geom['coordinates'][0][0]
                        elif gtype == 'Polygon':
                            coords = geom['coordinates'][0]
                        else:
                            continue
                        bdtopo_buildings.append({
                            'coords':       coords,
                            'alt_sol_raw':  props.get('altitude_minimale_sol'),   # NGF ou None
                            'alt_toit_raw': props.get('altitude_maximale_toit'),  # NGF ou None
                            'hauteur':      float(props.get('hauteur') or 6),
                        })
                    print(f'[DXF3D] BD TOPO: {len(bdtopo_buildings)} bâtiments')
            except Exception as e_bd:
                print(f'[DXF3D] BD TOPO ignoré: {e_bd}')

            def _bldg_normalized_z(bldg):
                """Renvoie (z_sol_norm, z_toit_norm) avec Z relatif au sol prospect."""
                h = bldg['hauteur']
                if bldg['alt_sol_raw'] is not None:
                    z_sol = float(bldg['alt_sol_raw']) - z_ground
                    if bldg['alt_toit_raw'] is not None:
                        z_toit = float(bldg['alt_toit_raw']) - z_ground
                    else:
                        z_toit = z_sol + h
                else:
                    # Altitudes NGF manquantes : on utilise le MNT local
                    if mnt_terrain is not None and terrain_bbox is not None:
                        _lat_mn, _lat_mx, _lon_mn, _lon_mx = terrain_bbox
                        _cx = sum(c[0] for c in bldg['coords']) / len(bldg['coords'])
                        _cy = sum(c[1] for c in bldg['coords']) / len(bldg['coords'])
                        _ix = min(GRID-1, max(0, int((_cx - _lon_mn) / (_lon_mx - _lon_mn) * GRID)))
                        _iy = min(GRID-1, max(0, int((_cy - _lat_mn) / (_lat_mx - _lat_mn) * GRID)))
                        z_sol = float(mnt_terrain[_iy, _ix]) - z_ground
                    else:
                        z_sol = 0.0
                    z_toit = z_sol + max(h, 3)
                if z_toit <= z_sol:
                    z_toit = z_sol + max(h, 3)
                return z_sol, z_toit

            # ── 5. Document DXF ──────────────────────────────────────────────────────
            doc = ezdxf.new(dxfversion='R2010')
            msp = doc.modelspace()

            doc.layers.add('TERRAIN_MNT',     color=3)   # vert   — grille sol
            doc.layers.add('BATIMENTS_3D',    color=2)   # jaune  — bâtiments BD TOPO
            doc.layers.add('MODULES_PV_3D',   color=5)   # bleu   — panneaux inclinés
            doc.layers.add('ZONE_CONTOUR_3D', color=6)   # magenta — contour champ
            doc.layers.add('ANNOTATIONS_3D',  color=1)   # rouge  — textes

            # ── 6. Terrain MNT → grille de polylignes 3D ────────────────────────────
            if mnt_terrain is not None and terrain_bbox is not None:
                lat_min, lat_max, lon_min, lon_max = terrain_bbox

                def grid_xyz(iy, ix):
                    glat = lat_min + (iy + 0.5) / GRID * (lat_max - lat_min)
                    glon = lon_min + (ix + 0.5) / GRID * (lon_max - lon_min)
                    gx, gy = to_xy(glat, glon)
                    gz = float(mnt_terrain[iy, ix]) - z_ground   # normalisé
                    return (gx, gy, gz)

                for ix in range(GRID):   # lignes N-S
                    msp.add_polyline3d([grid_xyz(iy, ix) for iy in range(GRID)],
                                       dxfattribs={'layer': 'TERRAIN_MNT'})
                for iy in range(GRID):   # lignes E-O
                    msp.add_polyline3d([grid_xyz(iy, ix) for ix in range(GRID)],
                                       dxfattribs={'layer': 'TERRAIN_MNT'})

            # ── 7. Bâtiments BD TOPO → wireframe 3D ─────────────────────────────────
            for bldg in bdtopo_buildings:
                raw_coords = bldg['coords']   # [[lon, lat], ...]
                z_sol, z_toit = _bldg_normalized_z(bldg)

                pts_xy = [(to_xy(c[1], c[0])) for c in raw_coords]   # (x,y) local
                if len(pts_xy) < 2:
                    continue

                base_3d = [(x, y, z_sol)  for x, y in pts_xy]
                top_3d  = [(x, y, z_toit) for x, y in pts_xy]

                # Anneau de base et de toit
                msp.add_polyline3d(base_3d + [base_3d[0]], dxfattribs={'layer': 'BATIMENTS_3D'})
                msp.add_polyline3d(top_3d  + [top_3d[0]],  dxfattribs={'layer': 'BATIMENTS_3D'})
                # Arêtes verticales (maxi 8 pour limiter le bruit visuel)
                step = max(1, len(pts_xy) // 8)
                for i in range(0, len(pts_xy), step):
                    msp.add_line(base_3d[i], top_3d[i], dxfattribs={'layer': 'BATIMENTS_3D'})

            # ── 8. Modules PV 3D inclinés ────────────────────────────────────────────
            # Bâtiment de référence = le plus proche du prospect
            ref_bldg = None
            if bdtopo_buildings:
                po_x, po_y = to_xy(prospect_lat, prospect_lon)
                def _bc(b):
                    cs = b['coords']
                    return to_xy(
                        sum(c[1] for c in cs) / len(cs),
                        sum(c[0] for c in cs) / len(cs)
                    )
                dists_bd = sorted(
                    [((po_x - _bc(b)[0])**2 + (po_y - _bc(b)[1])**2, b) for b in bdtopo_buildings],
                    key=lambda t: t[0]
                )
                ref_bldg = dists_bd[0][1]

            for zone in zones:
                num         = zone.get('numero', '?')
                orientation = float(zone.get('orientation', 180))
                inclinaison = float(zone.get('inclinaison', 30))
                coords      = zone.get('coordinates', [])
                modules_pos = zone.get('modulesPositions', [])
                zone_outline = zone.get('zone_outline_coords') or []
                nb_mod      = zone.get('nbModules', 0)
                puissance_kw = float(zone.get('puissanceKw', 0))

                beta_rad  = _math.radians(orientation)
                alpha_rad = _math.radians(inclinaison)
                tan_alpha = _math.tan(alpha_rad)

                # Centroide de la zone
                if coords:
                    clat_z = sum(c['lat'] for c in coords) / len(coords)
                    clng_z = sum(c['lng'] for c in coords) / len(coords)
                else:
                    clat_z, clng_z = prospect_lat, prospect_lon

                zone_cx, zone_cy = to_xy(clat_z, clng_z)

                # Z de référence = MNT normalisé sous la zone + hauteur du bâtiment
                if mnt_terrain is not None and terrain_bbox is not None:
                    lat_min, lat_max, lon_min, lon_max = terrain_bbox
                    ix_z = min(GRID-1, max(0, int((clng_z - lon_min) / (lon_max - lon_min) * GRID)))
                    iy_z = min(GRID-1, max(0, int((clat_z - lat_min) / (lat_max - lat_min) * GRID)))
                    z_mnt_zone = float(mnt_terrain[iy_z, ix_z]) - z_ground
                else:
                    z_mnt_zone = 0.0

                h_bldg = ref_bldg['hauteur'] if ref_bldg else 6.0
                z_ref  = z_mnt_zone + h_bldg

                def z_module(lx, ly):
                    """Z d'un coin de module selon son décalage (lx,ly) depuis le centroide.
                    β=azimuth (N=0°,S=180°) : z = z_ref − (lx·sinβ + ly·cosβ)·tanα
                    """
                    return z_ref - (lx * _math.sin(beta_rad) + ly * _math.cos(beta_rad)) * tan_alpha

                # Modules — 3DFACE inclinée
                added = 0
                for mod in modules_pos:
                    corners = mod.get('corners', [])
                    if len(corners) < 4:
                        continue
                    pts3d = []
                    for c in corners[:4]:
                        mx, my = to_xy(c['lat'], c['lng'])
                        pts3d.append((mx, my, z_module(mx - zone_cx, my - zone_cy)))
                    msp.add_3dface(pts3d, dxfattribs={'layer': 'MODULES_PV_3D'})
                    added += 1

                # Contour du champ en 3D
                outline_src = zone_outline if len(zone_outline) >= 3 else coords
                if outline_src:
                    pts_ol = []
                    for c in outline_src:
                        ox2, oy2 = to_xy(c['lat'], c['lng'])
                        pts_ol.append((ox2, oy2, z_module(ox2 - zone_cx, oy2 - zone_cy)))
                    if len(pts_ol) >= 2:
                        msp.add_polyline3d(pts_ol + [pts_ol[0]],
                                           dxfattribs={'layer': 'ZONE_CONTOUR_3D'})

                # Annotation (text 2D, insert en XY)
                msp.add_text(
                    f'Zone {num} — {nb_mod} mod. — {puissance_kw:.2f} kWc',
                    dxfattribs={'layer': 'ANNOTATIONS_3D', 'height': 0.4,
                                'insert': (zone_cx, zone_cy)}
                )
                print(f'[DXF3D] Zone {num}: {added} modules, orient={orientation:.0f}°, incl={inclinaison:.0f}°, z_ref={z_ref:.2f}m')

            # ── 9. Infos projet ──────────────────────────────────────────────────────
            totaux = calpinage.get('totaux', {})
            nom = (prospect.get('nom') or prospect.get('adresse') or f'Prospect {prospect_id}').strip()
            commune = prospect.get('commune', '') or ''
            puissance_totale = float(totaux.get('puissanceTotale') or
                                     sum(z.get('puissanceKw', 0) for z in zones))
            nb_mod_total = int(totaux.get('nombreModules') or
                               sum(z.get('nbModules', 0) for z in zones))
            ox_info, oy_info = 0.0, -15.0
            msp.add_text(f'HeliaPV — DXF 3D — {nom}',
                         dxfattribs={'layer': 'ANNOTATIONS_3D', 'height': 0.5,
                                     'insert': (ox_info, oy_info)})
            if commune:
                msp.add_text(commune,
                             dxfattribs={'layer': 'ANNOTATIONS_3D', 'height': 0.3,
                                         'insert': (ox_info, oy_info - 1)})
            msp.add_text(f'{puissance_totale:.2f} kWc  |  {nb_mod_total} modules  |  Lambert 93 / Z normalise sol=0',
                         dxfattribs={'layer': 'ANNOTATIONS_3D', 'height': 0.3,
                                     'insert': (ox_info, oy_info - 2)})

            # ── 10. Sérialiser ───────────────────────────────────────────────────────
            text_stream = io.StringIO()
            doc.write(text_stream)
            byte_stream = io.BytesIO(text_stream.getvalue().encode('utf-8'))
            byte_stream.seek(0)

            return send_file(
                byte_stream,
                mimetype='application/dxf',
                as_attachment=True,
                download_name=f'calpinage_pv_3d_{prospect_id}.dxf'
            )

        except ImportError:
            return jsonify({'error': 'Module ezdxf non disponible.'}), 500
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/irradiation-cache', methods=['POST'])
    def save_irradiation_cache(prospect_id):
        """Sauvegarder uniquement le cache irradiation Google Solar dans data_json.calpinage.
        N'écrase pas les zones ni les autres données calpinage existantes."""
        try:
            payload = request.json or {}
            irr_data = payload.get('irradiation_cache')
            if irr_data is None:
                return jsonify({'error': 'irradiation_cache manquant'}), 400

            row = execute_query(
                "SELECT data_json FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not row:
                return jsonify({'error': 'Prospect non trouvé'}), 404

            try:
                current_data = json.loads(row['data_json']) if row['data_json'] else {}
            except Exception:
                current_data = {}

            current_data.setdefault('calpinage', {})['irradiation_cache'] = irr_data

            execute_query(
                "UPDATE agriweb_prospects SET data_json = %s, date_modification = CURRENT_TIMESTAMP WHERE id = %s",
                (json.dumps(current_data), prospect_id)
            )
            print(f"[IRRADIATION CACHE] ✅ Prospect {prospect_id} — cache sauvegardé")
            return jsonify({'success': True})

        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/etude-productible')
    def generer_etude_productible(prospect_id):
        """Générer un PDF d'étude de productible avec graphique"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.lib import colors
            from reportlab.platypus import Table, TableStyle, Image
            from io import BytesIO
            import matplotlib
            matplotlib.use('Agg')  # Backend sans interface graphique
            import matplotlib.pyplot as plt
            
            # Récupérer le prospect et son calpinage
            result = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not result:
                return "Prospect non trouvé", 404
            
            prospect = dict(result)
            
            # Parser data_json pour récupérer le calpinage
            try:
                data_json = json.loads(prospect['data_json']) if prospect['data_json'] else {}
                calpinage = data_json.get('calpinage', {})
            except:
                calpinage = {}
            
            if not calpinage or not calpinage.get('zones'):
                return "Aucun calpinage trouvé pour ce prospect", 400
            
            # Marquer l'étape "Étude d'autoconsommation" (ordre 5) comme terminée si un projet existe
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,),
                fetch_one=True
            )
            if project:
                execute_query('''
                    UPDATE project_etapes 
                    SET statut = 'termine', 
                        date_fin_reelle = CURRENT_DATE
                    WHERE project_id = %s 
                    AND ordre = 5
                    AND statut != 'termine'
                ''', (project['id'],))
                print(f"✅ [ETAPE UPDATE] Étape 5 (Étude d'autoconsommation) marquée comme terminée pour projet {project['id']}")
            
            # Créer le PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # En-tête
            c.setFont("Helvetica-Bold", 20)
            c.drawString(2*cm, height - 2*cm, "ÉTUDE DE PRODUCTIBLE PHOTOVOLTAÏQUE")
            
            c.setFont("Helvetica", 12)
            c.drawString(2*cm, height - 3*cm, f"Projet: {prospect['nom_prospect'] or 'N/A'}")
            c.drawString(2*cm, height - 3.7*cm, f"Adresse: {prospect['adresse'] or 'N/A'}")
            c.drawString(2*cm, height - 4.4*cm, f"Date: {datetime.now().strftime('%d/%m/%Y')}")
            
            # Ligne de séparation
            c.setStrokeColor(colors.HexColor('#0d6efd'))
            c.setLineWidth(2)
            c.line(2*cm, height - 5*cm, width - 2*cm, height - 5*cm)
            
            # Résumé du projet
            y = height - 6*cm
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, y, "📊 RÉSUMÉ DU PROJET")
            y -= 1*cm
            
            totaux = calpinage.get('totaux', {})
            puissance_totale = totaux.get('puissanceTotale', 0)
            productible_total = totaux.get('productibleTotal', 0)
            
            c.setFont("Helvetica", 11)
            c.drawString(3*cm, y, f"• Puissance installée: {puissance_totale:.2f} kWc")
            y -= 0.7*cm
            c.drawString(3*cm, y, f"• Productible annuel estimé: {productible_total:.2f} MWh/an")
            y -= 0.7*cm
            c.drawString(3*cm, y, f"• Nombre de zones PV: {len(calpinage['zones'])}")
            y -= 0.7*cm
            
            module = calpinage.get('module', {})
            c.drawString(3*cm, y, f"• Module: {module.get('longueur')}×{module.get('largeur')}mm - {module.get('puissance')}Wc")
            
            # Tableau des zones
            y -= 1.5*cm
            c.setFont("Helvetica-Bold", 14)
            c.drawString(2*cm, y, "📋 DÉTAIL DES ZONES")
            y -= 0.8*cm
            
            # Créer les données du tableau
            table_data = [['Zone', 'Surface\n(m²)', 'Modules', 'Puissance\n(kWc)', 'Orient.', 'Inclin.', 'Productible\n(MWh/an)']]
            
            for zone in calpinage['zones']:
                orientation_str = f"{zone['orientation']}°"
                inclinaison_str = f"{zone['inclinaison']}°"
                
                table_data.append([
                    f"Zone {zone['numero']}",
                    f"{zone['surfaceM2']:.1f}",
                    str(zone['nbModules']),
                    f"{zone['puissanceKw']:.2f}",
                    orientation_str,
                    inclinaison_str,
                    f"{zone['productible']:.2f}"
                ])
            
            # Ligne de total
            table_data.append([
                'TOTAL',
                '',
                '',
                f"{puissance_totale:.2f}",
                '',
                '',
                f"{productible_total:.2f}"
            ])
            
            # Créer le tableau
            table = Table(table_data, colWidths=[2.5*cm, 2*cm, 1.8*cm, 2*cm, 1.5*cm, 1.5*cm, 2.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f8f9fa')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            
            table.wrapOn(c, width, height)
            table.drawOn(c, 2*cm, y - len(table_data) * 0.7*cm)
            
            y = y - len(table_data) * 0.7*cm - 1.5*cm
            
            # Graphique de production mensuelle (si données disponibles)
            monthly_data_available = False
            for zone in calpinage['zones']:
                if zone.get('monthly_data'):
                    monthly_data_available = True
                    break
            
            if monthly_data_available:
                # Créer le graphique matplotlib
                fig, ax = plt.subplots(figsize=(7, 3))
                
                months = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
                monthly_total = [0] * 12
                
                # Agréger les données mensuelles de toutes les zones
                for zone in calpinage['zones']:
                    if zone.get('monthly_data'):
                        for i, val in enumerate(zone['monthly_data'][:12]):
                            monthly_total[i] += val
                
                # Convertir en MWh si nécessaire
                monthly_total_mwh = [v / 1000 for v in monthly_total]
                
                ax.bar(months, monthly_total_mwh, color='#FFC107', edgecolor='#FF9800', linewidth=1.5)
                ax.set_ylabel('Production (MWh)', fontsize=10)
                ax.set_title('Production mensuelle estimée (PVGIS)', fontsize=12, fontweight='bold')
                ax.grid(axis='y', alpha=0.3)
                plt.tight_layout()
                
                # Sauvegarder le graphique en mémoire
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                img_buffer.seek(0)
                plt.close(fig)
                
                # Ajouter le graphique au PDF
                c.setFont("Helvetica-Bold", 12)
                c.drawString(2*cm, y, "📊 GRAPHIQUE DE PRODUCTION MENSUELLE")
                y -= 0.5*cm
                
                # Créer une image ReportLab depuis le buffer
                from reportlab.platypus import Image as RLImage
                img = RLImage(img_buffer, width=14*cm, height=6*cm)
                img.drawOn(c, 3*cm, y - 6.5*cm)
                
                y -= 7*cm
            
            # Notes et hypothèses
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2*cm, y, "📝 HYPOTHÈSES DE CALCUL")
            y -= 0.7*cm
            
            c.setFont("Helvetica", 9)
            c.drawString(2.5*cm, y, "• Source des données: PVGIS (EU Science Hub)")
            y -= 0.5*cm
            c.drawString(2.5*cm, y, "• Pertes système: 14% (câblage, onduleur, salissure, température)")
            y -= 0.5*cm
            c.drawString(2.5*cm, y, "• Orientation et inclinaison: paramétrées par zone")
            y -= 0.5*cm
            c.drawString(2.5*cm, y, "• Données météo: moyennes sur 20 ans (PVGIS database)")
            
            # Pied de page
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(2*cm, 1.5*cm, "HeliaPV - Étude de faisabilité photovoltaïque")
            c.drawString(width - 6*cm, 1.5*cm, f"Page 1/1")
            
            # Finaliser le PDF
            c.showPage()
            c.save()
            
            buffer.seek(0)
            
            filename = f"Etude_Productible_{prospect['nom_prospect'] or 'Prospect'}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la génération du PDF: {str(e)}", 500
    
    # ============================================================================
    # SCHÉMA UNIFILAIRE NF C 15-712
    # ============================================================================
    @app.route('/api/crm/prospects/<int:prospect_id>/schema-unifilaire')
    def generer_schema_unifilaire(prospect_id):
        """Générer un schéma unifilaire conforme NF C 15-712 à partir du calepinage"""
        try:
            from schema_unifilaire import SchemaUnifilaire
            from io import BytesIO
            
            # Récupérer le prospect et son calpinage
            result = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not result:
                return "Prospect non trouvé", 404
            
            prospect = dict(result)
            
            # Parser data_json pour récupérer le calpinage
            try:
                data_json = json.loads(prospect['data_json']) if prospect['data_json'] else {}
                calpinage = data_json.get('calpinage', {})
            except:
                calpinage = {}
            
            if not calpinage or not calpinage.get('zones'):
                return "Aucun calepinage trouvé. Veuillez d'abord créer un calepinage.", 400
            
            # Données prospect pour le schéma
            # Priorité: contact_nom > representant_nom > dirigeant_nom > nom_prospect
            nom_client = (prospect.get('contact_nom') or 
                         prospect.get('representant_nom') or 
                         prospect.get('dirigeant_nom') or 
                         prospect.get('nom_prospect') or '')
            
            prospect_data = {
                'nom': nom_client,  # Nom complet du client
                'prenom': '',  # Pas de séparation nom/prénom dans la DB
                'adresse': prospect.get('adresse', ''),
                'code_postal': '',  # Pas dans la DB, sera extrait de commune si besoin
                'commune': prospect.get('commune', ''),
                'references_cadastrales': prospect.get('parcelles_cadastrales', ''),
                # Numéro PDL (Point De Livraison) — obligatoire Consuel / NF C 15-712
                'pdl': prospect.get('pdl', '') or data_json.get('autoconsommation', {}).get('pdl', ''),
                # Département — détermine la zone kéraunique (SPD Type 1+2 si zone C)
                'departement': prospect.get('departement', ''),
                'paratonnerre': data_json.get('equipments', {}).get('paratonnerre', False),
                # Poste de raccordement BT (pour injection < 1MWc)
                'poste_bt_nom': prospect.get('poste_bt_nom', ''),
                'poste_bt_distance_m': prospect.get('poste_bt_distance_m', None),
                'poste_bt_puissance': prospect.get('poste_bt_puissance', None),
                'poste_bt_etat': prospect.get('poste_bt_etat', ''),
                'poste_bt_lat': prospect.get('poste_bt_lat', None),
                'poste_bt_lon': prospect.get('poste_bt_lon', None),
                # Poste de raccordement HTA (pour injection >= 1MWc)
                'poste_hta_nom': prospect.get('poste_hta_nom', ''),
                'poste_hta_distance_m': prospect.get('poste_hta_distance_m', None),
                'poste_hta_puissance': prospect.get('poste_hta_puissance', None),
                'poste_hta_etat': prospect.get('poste_hta_etat', ''),
                'poste_hta_lat': prospect.get('poste_hta_lat', None),
                'poste_hta_lon': prospect.get('poste_hta_lon', None)
            }
            
            # Générer le schéma unifilaire
            print(f"📐 [SCHEMA UNIFILAIRE] Génération pour prospect {prospect_id}")
            schema = SchemaUnifilaire(calpinage, prospect_data)
            
            # Générer le PDF en mémoire
            buffer = BytesIO()
            temp_path = f"/tmp/schema_unifilaire_{prospect_id}.pdf"
            schema.generer_schema_pdf(temp_path)
            
            # Sauvegarder la configuration électrique calculée dans le calepinage
            try:
                electric_config = schema.get_configuration_electrique_json()
                
                # Mettre à jour le calepinage avec la config électrique
                calpinage['configuration_electrique'] = electric_config
                
                # Sauvegarder aussi les infos onduleur dans equipments
                if 'equipments' not in calpinage:
                    calpinage['equipments'] = {'onduleurs': [], 'tgbt': None, 'injection': None}
                
                if len(calpinage['equipments'].get('onduleurs', [])) > 0:
                    # Enrichir l'onduleur existant avec les infos calculées
                    calpinage['equipments']['onduleurs'][0].update({
                        'modele': schema.onduleur['modele'],
                        'marque': schema.onduleur['marque'],
                        'puissance_ac': schema.onduleur['p_ac'],
                        'puissance_dc_max': schema.onduleur['p_dc_max'],
                        'tension_min': schema.onduleur.get('v_min', 150),   # FIX #5c
                        'tension_max': schema.onduleur.get('v_max', 1000),
                        'nb_mppt': schema.onduleur['mppt']
                    })
                
                # Mettre à jour data_json
                data_json['calpinage'] = calpinage
                execute_query("""
                    UPDATE agriweb_prospects 
                    SET data_json = %s,
                        date_modification = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (json.dumps(data_json), prospect_id))
                
                print(f"✅ [SCHEMA] Configuration électrique sauvegardée pour prospect {prospect_id}")
            except Exception as save_error:
                print(f"⚠️ [SCHEMA] Erreur sauvegarde config électrique: {save_error}")
                # Continuer même si sauvegarde échoue
            
            # Lire le fichier généré
            with open(temp_path, 'rb') as f:
                buffer.write(f.read())
            
            buffer.seek(0)
            
            # Supprimer le fichier temporaire
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Nom du fichier
            nom_prospect = f"{prospect.get('nom', '')}_{prospect.get('prenom', '')}".strip().replace(' ', '_') or 'Prospect'
            filename = f"Schema_Unifilaire_NF_C15-712_{nom_prospect}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            print(f"✅ [SCHEMA UNIFILAIRE] PDF généré: {filename}")
            
            # Sauvegarder automatiquement dans la dataroom
            try:
                buffer.seek(0)
                pdf_bytes = buffer.read()
                save_to_dataroom(prospect_id, pdf_bytes, filename, 'schema_unifilaire', source='auto-schema')
                buffer.seek(0)
            except Exception as dr_err:
                print(f"⚠️ [DATAROOM] Erreur sauvegarde schema: {dr_err}")
            
            # Marquer l'étape "Calepinage" (ordre 3) comme terminée si un projet existe
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,),
                fetch_one=True
            )
            
            if project:
                project_id = project['id']
                # Mettre à jour l'étape Calepinage
                execute_query('''
                    UPDATE project_etapes 
                    SET statut = 'termine',
                        date_fin_reelle = CURRENT_TIMESTAMP
                    WHERE project_id = %s 
                    AND nom_etape = 'Calepinage'
                    AND statut != 'termine'
                ''', (project_id,))
                
                print(f"✅ [SCHEMA UNIFILAIRE] Étape 'Calepinage' marquée terminée pour projet {project_id}")
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la génération du schéma unifilaire: {str(e)}", 500

    # ============================================================================
    # ROUTE - GÉNÉRATION PLANS DE STRINGS
    # ============================================================================
    @app.route('/api/crm/prospects/<int:prospect_id>/plans-strings')
    def generer_plans_strings(prospect_id):
        """Génère les plans détaillés de câblage des strings par zone"""
        print(f"\n{'='*80}")
        print(f"🎨 [PLANS STRINGS] Génération pour prospect {prospect_id}")
        print(f"{'='*80}\n")
        
        try:
            # Récupérer le prospect
            prospect = execute_query(
                'SELECT * FROM agriweb_prospects WHERE id = %s',
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect:
                print(f"❌ [PLANS STRINGS] Prospect {prospect_id} non trouvé")
                return "Prospect non trouvé", 404
            
            # Récupérer les données de calepinage
            data_json = prospect.get('data_json', {})
            if isinstance(data_json, str):
                import json
                data_json = json.loads(data_json) if data_json else {}
            
            calpinage = data_json.get('calpinage', {})
            
            if not calpinage or not calpinage.get('zones'):
                print(f"❌ [PLANS STRINGS] Pas de calepinage disponible pour prospect {prospect_id}")
                return "Aucun calepinage disponible. Veuillez d'abord réaliser le calepinage.", 400
            
            zones = calpinage.get('zones', [])
            if not zones:
                print(f"❌ [PLANS STRINGS] Aucune zone définie dans le calepinage")
                return "Aucune zone définie dans le calepinage", 400
            
            # Récupérer les informations du module
            module_info = calpinage.get('module', {})
            if not module_info:
                print(f"⚠️ [PLANS STRINGS] Informations module manquantes")
                return "Informations du module manquantes dans le calepinage", 400
            
            # Récupérer les onduleurs
            equipments = calpinage.get('equipments', {})
            onduleurs = equipments.get('onduleurs', [])
            
            # Créer un buffer pour le PDF
            from io import BytesIO
            buffer = BytesIO()
            
            # Générer les plans avec PlansStrings
            import os
            import tempfile
            from plans_strings import PlansStrings
            
            # Créer un fichier temporaire
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
            
            print(f"📄 [PLANS STRINGS] Génération du PDF...")
            print(f"   - Nombre de zones: {len(zones)}")
            print(f"   - Module: {module_info.get('marque', '')} {module_info.get('modele', '')}")
            print(f"   - Onduleurs: {len(onduleurs)}")
            
            # Préparer les données au format attendu par PlansStrings
            prospect_data = {
                'nom': prospect.get('nom', ''),
                'prenom': prospect.get('prenom', ''),
                'adresse': prospect.get('adresse', ''),
                'commune': prospect.get('commune', '')
            }
            
            # Générer le PDF
            plans = PlansStrings(
                calpinage_data=calpinage,
                prospect_data=prospect_data
            )
            
            plans.generer_plans_pdf(output_path=temp_path)
            
            # Lire le fichier généré
            with open(temp_path, 'rb') as f:
                buffer.write(f.read())
            
            buffer.seek(0)
            
            # Supprimer le fichier temporaire
            try:
                os.remove(temp_path)
            except:
                pass
            
            # Nom du fichier
            nom_prospect = f"{prospect.get('nom', '')}_{prospect.get('prenom', '')}".strip().replace(' ', '_') or 'Prospect'
            filename = f"Plans_Strings_{nom_prospect}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            print(f"✅ [PLANS STRINGS] PDF généré: {filename}")
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur lors de la génération des plans de strings: {str(e)}", 500

    # ============================================================================
    # ROUTE DEBUG - FORMES JURIDIQUES
    # ============================================================================
    @app.route('/api/crm/debug/formes-juridiques')
    def debug_formes_juridiques():
        """Liste toutes les formes juridiques uniques dans la base"""
        try:
            formes = execute_query('''
                SELECT DISTINCT proprietaire_forme_juridique, COUNT(*) as count
                FROM agriweb_prospects
                WHERE proprietaire_forme_juridique IS NOT NULL
                AND proprietaire_forme_juridique != ''
                GROUP BY proprietaire_forme_juridique
                ORDER BY count DESC
                LIMIT 50
            ''', fetch_all=True)
            
            return jsonify({
                'success': True,
                'formes_juridiques': formes
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # DIAGNOSTIC DONNÉES PROSPECT (admin seulement)
    # ============================================================================
    @app.route('/api/crm/prospects/<int:prospect_id>/debug-data')
    def debug_prospect_data(prospect_id):
        """
        Endpoint de diagnostic : vérifie la présence et la taille des données clés
        (calpinage, plan de masse, rapport) pour un prospect donné.
        Réservé aux admins connectés.
        """
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'error': 'Authentification requise'}), 401
            if not is_admin and not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'error': 'Accès non autorisé'}), 403

            row = execute_query(
                "SELECT id, commune, adresse, data_json FROM agriweb_prospects WHERE id = %s",
                (prospect_id,), fetch_one=True
            )
            if not row:
                return jsonify({'error': f'Prospect {prospect_id} non trouvé'}), 404

            prospect = dict(row)
            try:
                dj = json.loads(prospect['data_json']) if isinstance(prospect['data_json'], str) else (prospect['data_json'] or {})
                if not isinstance(dj, dict):
                    dj = {}
            except Exception as e:
                return jsonify({'error': f'Impossible de parser data_json : {e}'}), 500

            calp  = dj.get('calpinage', {}) or {}
            rapport = dj.get('rapport', {}) or {}
            vt    = dj.get('visite_technique', {}) or {}
            rc    = dj.get('rapport_commune', {}) or {}

            def ss_info(val):
                """Analyse un champ screenshot : détecte les valeurs invalides (bool, dict vide, string vide)"""
                if not val:
                    return {'present': False, 'valide': False, 'taille_ko': 0, 'type': 'absent'}
                if isinstance(val, bool):
                    return {'present': False, 'valide': False, 'taille_ko': 0, 'type': 'boolean_invalide',
                            'action': 'Re-sauvegarder le calpinage pour recapturer le screenshot'}
                if isinstance(val, dict):
                    val = val.get('screenshot', '')
                    if not val:
                        return {'present': False, 'valide': False, 'taille_ko': 0, 'type': 'dict_sans_screenshot'}
                if not isinstance(val, str):
                    return {'present': False, 'valide': False, 'taille_ko': 0, 'type': f'type_inattendu_{type(val).__name__}'}
                is_b64 = val.startswith('data:image') or len(val) > 1000
                taille = round(len(val) / 1024, 1)
                return {'present': True, 'valide': is_b64, 'taille_ko': taille,
                        'type': 'base64_image' if is_b64 else 'string_courte_invalide'}

            zones = calp.get('zones', [])
            totaux = calp.get('totaux', {}) or {}

            result = {
                'prospect_id'  : prospect_id,
                'commune'      : prospect.get('commune', ''),
                'adresse'      : prospect.get('adresse', ''),
                'data_json_present': bool(dj),
                'data_json_cles'   : list(dj.keys()),

                'calpinage': {
                    'present'          : bool(calp),
                    'nb_zones'         : len(zones),
                    'puissance_kwc'    : totaux.get('puissanceTotale', 0),
                    'nb_modules'       : totaux.get('nombreModules') or sum(z.get('nbModules', 0) for z in zones),
                    'date_maj'         : calp.get('date_maj', '—'),
                    'screenshot_map'         : ss_info(calp.get('screenshot_map')),
                    'screenshot_plan_masse'  : ss_info(calp.get('screenshot_plan_masse')),
                    'screenshot_3d'          : ss_info(calp.get('screenshot_3d')),
                    'screenshot_irradiation' : ss_info(calp.get('screenshot_irradiation')),
                    'autoconso_results'      : bool(calp.get('autoconso_results')),
                },

                'rapport': {
                    'present'          : bool(rapport),
                    'lat'              : rapport.get('lat'),
                    'lon'              : rapport.get('lon'),
                    'commune'          : rapport.get('commune_name', '—'),
                    'altitude'         : rapport.get('altitude_m', '—'),
                    'kwh_per_kwc'      : rapport.get('kwh_per_kwc', '—'),
                    'has_cadastre'     : bool(rapport.get('api_details', {}).get('cadastre', {}).get('success')),
                    'has_gpu_plu'      : bool(rapport.get('api_details', {}).get('gpu', {}).get('success')),
                    'has_plu_info'     : bool(rapport.get('plu_info')),
                    'has_zaer'         : bool(rapport.get('zaer')),
                    'has_georisques'   : bool(rapport.get('georisques_risks')),  # clé correcte
                    'has_pvgis'        : bool(rapport.get('pvgis_data')),
                    'gpu_layers'       : list(rapport.get('api_details', {}).get('gpu', {}).get('details', {}).keys())[:10],
                },

                'visite_technique': {
                    'present': bool(vt),
                    'date'   : vt.get('date', '—'),
                    'notes'  : bool(vt.get('notes')),
                },

                'rapport_commune': {
                    'present': bool(rc),
                },

                'verdict': {
                    # Plan de masse : UNIQUEMENT screenshot_plan_masse (plus de repli sur screenshot_map)
                    'PDF_plan_de_masse_aura_image'   : bool(
                        isinstance(calp.get('screenshot_plan_masse'), str) and len(calp.get('screenshot_plan_masse','')) > 1000
                    ),
                    'PDF_calpinage_aura_image'        : bool(
                        isinstance(calp.get('screenshot_map'), str) and len(calp.get('screenshot_map','')) > 1000
                    ),
                    'PDF_plan_situation_sera_genere'  : bool(rapport.get('lat') and rapport.get('lon')) or bool(prospect.get('latitude') and prospect.get('longitude')),
                    'PDF_contraintes_site_sera_genere': bool(rapport),
                    'PDF_plu_source'                  : (
                        'plu_info' if rapport.get('plu_info')
                        else 'gpu_details' if rapport.get('api_details', {}).get('gpu', {}).get('details')
                        else 'aucune'
                    ),
                    'ACTION_REQUISE': (
                        'Re-ouvrir la page Calpinage et cliquer Sauvegarder pour recapturer screenshot_map'
                        if not (isinstance(calp.get('screenshot_map'), str) and len(calp.get('screenshot_map','')) > 1000)
                        else 'Aucune action requise pour les screenshots'
                    )
                }
            }

            return jsonify(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ============================================================================
    # RÉPARATION ÉTAPES PROJET (ordre dupliqué)
    # ============================================================================
    @app.route('/api/crm/projets/<int:project_id>/repair-etapes', methods=['POST'])
    def repair_project_etapes(project_id):
        """
        Répare les étapes d'un projet dont les numéros d'ordre sont dupliqués
        (ex: deux étapes à ordre=4 suite à l'ancien bug d'insertion Plan de masse).
        Réservé aux admins.
        """
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'error': 'Authentification requise'}), 401
            if not is_admin:
                return jsonify({'error': 'Réservé aux administrateurs'}), 403

            etapes = execute_query(
                'SELECT id, nom_etape, ordre, statut FROM project_etapes WHERE project_id = %s ORDER BY ordre, id',
                (project_id,), fetch_all=True
            )
            if not etapes:
                return jsonify({'error': 'Projet non trouvé ou sans étapes'}), 404

            # Ordre attendu canonique
            ordre_canonique = [
                'Rapport de recherche HeliaPV',
                'Visite technique',
                'Calepinage',
                'Plan de masse',
                "Étude d'autoconsommation",
                'Devis commercial',
                'Signature & Facture',
                'Déclaration Préalable de Travaux (DP)',
                'Déclaration de Raccordement (DDR)',
                'Installation & DOE',
                'Consuel',
                'Mise en service & Maintenance'
            ]

            # Réassigner les ordres selon le nom canonique
            repaired = []
            for etape in etapes:
                nom = etape['nom_etape']
                try:
                    nouvel_ordre = ordre_canonique.index(nom) + 1
                except ValueError:
                    nouvel_ordre = etape['ordre']  # garder l'ordre existant si étape inconnue
                execute_query(
                    'UPDATE project_etapes SET ordre = %s WHERE id = %s',
                    (nouvel_ordre, etape['id'])
                )
                repaired.append({
                    'id': etape['id'],
                    'nom_etape': nom,
                    'ancien_ordre': etape['ordre'],
                    'nouvel_ordre': nouvel_ordre
                })

            return jsonify({
                'success': True,
                'project_id': project_id,
                'etapes_reparees': repaired
            })

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ============================================================================
    # PROPOSITION COMMERCIALE PROFESSIONNELLE
    def _emprise_batiment_ign(lat, lon):
        """Emprise au sol (m²) du bâtiment au point, via IGN BD TOPO (gratuit, WFS).
        None si indisponible. Sert de plafond toiture pour la pré-étude."""
        if lat is None or lon is None:
            return None
        try:
            import requests as _rq
            from shapely.geometry import shape as _shape, Point as _Point
            from shapely.ops import transform as _sht
            from pyproj import Transformer as _Tr
            _T = _Tr.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
            d = 0.0016
            p = {"SERVICE": "WFS", "VERSION": "2.0.0", "REQUEST": "GetFeature",
                 "typeNames": "BDTOPO_V3:batiment", "outputFormat": "application/json", "count": "80",
                 "bbox": f"{lon-d},{lat-d},{lon+d},{lat+d},urn:ogc:def:crs:OGC:1.3:CRS84"}
            feats = _rq.get("https://data.geopf.fr/wfs/ows", params=p, timeout=15).json().get('features', [])
            if not feats:
                return None
            def _area(g): return _sht(lambda x, y, z=None: _T.transform(x, y), g).area
            pt = _Point(lon, lat)
            cont = [_shape(f['geometry']) for f in feats if _shape(f['geometry']).contains(pt)]
            if cont:
                return round(_area(cont[0]))
            biggest = max((_shape(f['geometry']) for f in feats), key=_area)
            return round(_area(biggest))
        except Exception as e:
            print(f"⚠️ [IGN BD TOPO] emprise: {e}")
            return None

    def _tarif_achat_industriel(conso_mwh):
        """Prix d'achat élec HTVA (€/kWh) selon la taille du consommateur — base SDES/
        Eurostat France 2024 (moyenne entreprise 164,6 €/MWh, dégressif avec le volume).
        Sert de coût évité réaliste pour l'autoconso industrielle."""
        c = float(conso_mwh or 0)
        if c < 500:        return 0.20    # PME (< 0,5 GWh)
        if c < 2000:       return 0.18    # 0,5–2 GWh
        if c < 20000:      return 0.16    # 2–20 GWh (≈ moyenne nationale)
        if c < 70000:      return 0.13    # 20–70 GWh
        if c < 150000:     return 0.11    # 70–150 GWh
        return 0.095                       # ≥ 150 GWh (électro-intensif, accise réduite)

    def _parcelle_au_point_ign(lat, lon):
        """Parcelle cadastrale contenant le point, via IGN apicarto (gratuit).
        Retourne {section, numero, contenance, code_insee} ou {}."""
        if lat is None or lon is None:
            return {}
        try:
            import requests as _rq
            from shapely.geometry import shape as _shape, Point as _Point
            buf = 120 / 111000.0
            bbox = {"type": "Polygon", "coordinates": [[[lon-buf, lat-buf], [lon+buf, lat-buf],
                    [lon+buf, lat+buf], [lon-buf, lat+buf], [lon-buf, lat-buf]]]}
            r = _rq.get("https://apicarto.ign.fr/api/cadastre/parcelle",
                        params={"geom": json.dumps(bbox), "_limit": 50, "source_ign": "PCI"}, timeout=12)
            feats = r.json().get('features', [])
            pt = _Point(lon, lat)
            for f in feats:
                try:
                    if _shape(f['geometry']).contains(pt):
                        p = f.get('properties', {})
                        return {'section': p.get('section', ''), 'numero': p.get('numero', ''),
                                'contenance': p.get('contenance', ''), 'code_insee': p.get('code_insee', '')}
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ [PARCELLE IGN] {e}")
        return {}

    def _pre_etude_sizing(prospect, taux_cible=40.0, prix_wc=0.55):
        """Dimensionnement de la pré-étude (gratuit) : puissance = min(couverture conso,
        plafond toiture IGN). Retourne le détail + les KPIs autoconso."""
        try:
            dj = json.loads(prospect.get('data_json') or '{}')
            if isinstance(dj, list):
                dj = {}
        except Exception:
            dj = {}
        em = dj.get('enedis_match') or {}
        diag0 = dj.get('diagnostic_autoconso') or {}
        conso_mwh = em.get('consommation_mwh')
        if conso_mwh is None and diag0.get('consommation_annuelle_kwh'):
            conso_mwh = diag0['consommation_annuelle_kwh'] / 1000.0
        conso_mwh = float(conso_mwh or 0)
        secteur = em.get('secteur') or 'INDUSTRIE'
        lat = prospect.get('latitude'); lon = prospect.get('longitude')
        try:
            from autoconsommation import _productible_from_lat, diagnostic_autoconso_rapide
        except Exception:
            _productible_from_lat = lambda l: 1150.0; diagnostic_autoconso_rapide = None
        productible = _productible_from_lat(lat)
        conso_kwh = conso_mwh * 1000.0
        kwc_conso = (taux_cible / 100.0) * conso_kwh / productible if conso_kwh > 0 else 0
        # Plafond toiture (IGN BD TOPO) : ~0,1 kWc/m² d'emprise
        surface = _emprise_batiment_ign(lat, lon)
        plafond = round(surface * 0.10) if surface else None
        kwc = kwc_conso
        if plafond:
            kwc = min(kwc, plafond)
        kwc = max(9.0, round(kwc))
        # KPIs à cette puissance (production PVGIS par latitude, taux autoconso, économie)
        diag = {}
        if diagnostic_autoconso_rapide and conso_mwh > 0:
            try:
                diag = diagnostic_autoconso_rapide(conso_mwh, secteur, lat=lat, kwc=kwc) or {}
            except Exception:
                diag = {}
        return {'kwc': kwc, 'kwc_conso': round(kwc_conso), 'plafond_toiture_kwc': plafond,
                'surface_toiture_m2': surface, 'productible': round(productible),
                'conso_mwh': round(conso_mwh), 'secteur': secteur, 'diag': diag,
                'borne_par': 'toiture' if (plafond and plafond < kwc_conso) else 'consommation'}

    # ──────────────────────────────────────────────────────────────────────
    # PAGE PUBLIQUE "PRÉ-ÉTUDE" — lead magnet tracké (mailing de masse → clics)
    # ──────────────────────────────────────────────────────────────────────
    def _etude_serializer():
        from itsdangerous import URLSafeSerializer
        secret = getattr(app, 'secret_key', None) or os.environ.get('SECRET_KEY') or 'heliapv-etude-2026'
        return URLSafeSerializer(secret, salt='etude-publique')

    def _etude_token(prospect_id):
        return _etude_serializer().dumps(int(prospect_id))

    def _etude_resolve(token):
        try:
            return int(_etude_serializer().loads(token))
        except Exception:
            return None

    try:
        execute_query("""CREATE TABLE IF NOT EXISTS etude_events (
            id SERIAL PRIMARY KEY,
            prospect_id INTEGER,
            event VARCHAR(32),
            seconds INTEGER,
            meta TEXT,
            user_agent TEXT,
            referer TEXT,
            ip VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    except Exception as _e_tbl:
        print(f"⚠️ etude_events init: {_e_tbl}")

    def _etude_log(prospect_id, event, seconds=None, meta=None):
        try:
            ua  = (request.headers.get('User-Agent') or '')[:500]
            ref = (request.headers.get('Referer') or '')[:500]
            ip  = (request.headers.get('X-Forwarded-For') or request.remote_addr or '')[:64]
            execute_query(
                "INSERT INTO etude_events (prospect_id, event, seconds, meta, user_agent, referer, ip) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (prospect_id, event, seconds, (json.dumps(meta) if meta else None), ua, ref, ip))
        except Exception as e:
            print(f"⚠️ etude_log: {e}")

    def _etude_teaser(prospect):
        """Chiffres 'teaser' crédibles pour la page publique (détail derrière le CTA)."""
        sz = _pre_etude_sizing(prospect)
        diag = sz.get('diag') or {}
        prod_kwh = diag.get('production_annuelle_kwh') or round((sz.get('kwc') or 0) * (sz.get('productible') or 0))
        eco = diag.get('economie_an_eur')
        return {
            'kwc':             sz.get('kwc'),
            'surface_m2':      sz.get('surface_toiture_m2'),
            'conso_mwh':       sz.get('conso_mwh'),
            'production_mwh':  round(prod_kwh / 1000.0, 1) if prod_kwh else None,
            'economie_an_eur': round(eco) if eco else None,
            'economie_25ans':  round(eco * 25) if eco else None,
            'taux_autoconso':  diag.get('taux_autoconsommation'),
            'co2_t':           round(prod_kwh * 0.06 / 1000.0, 1) if prod_kwh else None,  # ~60 gCO2/kWh élec FR
            'secteur':         sz.get('secteur'),
        }

    def _etude_nom_ville(prospect):
        nom = (prospect.get('nom') or '').strip()
        if not nom:
            try:
                _dj = json.loads(prospect.get('data_json') or '{}')
                if isinstance(_dj, dict):
                    nom = (_dj.get('operateur', {}).get('nom') if isinstance(_dj.get('operateur'), dict) else None) \
                          or _dj.get('denomination') or ''
            except Exception:
                pass
        nom = (nom or prospect.get('adresse') or 'votre entreprise').strip()
        ville = (prospect.get('commune') or '').strip()
        return nom, ville

    @app.route('/etude/<token>', methods=['GET'])
    def etude_publique(token):
        pid = _etude_resolve(token)
        row = execute_query("SELECT * FROM agriweb_prospects WHERE id = %s", (pid,), fetch_one=True) if pid else None
        if not row:
            return render_template('etude_publique.html', invalide=True), 404
        prospect = dict(row)
        try:
            teaser = _etude_teaser(prospect)
        except Exception as e:
            print(f"⚠️ etude teaser: {e}")
            teaser = {'kwc': None}
        nom, ville = _etude_nom_ville(prospect)
        _etude_log(pid, 'view')
        return render_template('etude_publique.html', invalide=False, token=token,
                               teaser=teaser, nom=nom, ville=ville,
                               lat=prospect.get('latitude'), lon=prospect.get('longitude'))

    @app.route('/etude/<token>/track', methods=['POST'])
    def etude_track(token):
        pid = _etude_resolve(token)
        if pid is None:
            return jsonify({'ok': False}), 404
        body = request.get_json(silent=True) or {}
        event = str(body.get('event') or 'heartbeat')[:32]
        seconds = body.get('seconds')
        try:
            seconds = int(seconds) if seconds is not None else None
        except Exception:
            seconds = None
        meta = body.get('meta') if isinstance(body.get('meta'), dict) else None
        _etude_log(pid, event, seconds, meta)
        return jsonify({'ok': True})

    @app.route('/api/crm/prospects/<int:prospect_id>/etude-url', methods=['GET'])
    def etude_url(prospect_id):
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401
        row = execute_query("SELECT user_id FROM agriweb_prospects WHERE id = %s", (prospect_id,), fetch_one=True)
        if not row:
            return jsonify({'success': False, 'error': 'Prospect introuvable'}), 404
        if not is_admin and str(dict(row).get('user_id')) != str(user_id):
            return jsonify({'success': False, 'error': 'Accès refusé'}), 403
        base = request.host_url.rstrip('/')
        return jsonify({'success': True, 'url': f"{base}/etude/{_etude_token(prospect_id)}"})

    @app.route('/api/crm/prospects/<int:prospect_id>/pre-etude', methods=['POST', 'GET'])
    def generer_pre_etude(prospect_id):
        """Génère une PRÉ-ÉTUDE indicative (gratuite) : dimensionnement auto
        (conso + plafond toiture IGN), prix 0,55 €/Wc, proposition pro marquée indicative."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            row = execute_query("SELECT * FROM agriweb_prospects WHERE id = %s", (prospect_id,), fetch_one=True)
            if not row:
                return jsonify({'success': False, 'error': 'Prospect introuvable'}), 404
            prospect = dict(row)
            if not is_admin and str(prospect.get('user_id')) != str(user_id):
                return jsonify({'success': False, 'error': 'Accès refusé'}), 403

            sz = _pre_etude_sizing(prospect)
            if sz['conso_mwh'] <= 0:
                return jsonify({'success': False, 'error': 'Consommation inconnue pour ce prospect'}), 400
            kwc = sz['kwc']
            conso_kwh = sz['conso_mwh'] * 1000.0

            from proposition_professionnelle import PropositionProfessionnelle
            from autoconsommation import (compute_autoconsommation, compute_economics,
                _synthetic_pv_8760_wh, _secteur_to_profile, PROFILE_LABELS, TARIFF_LABELS,
                get_tarif_revente_s21)
            from datetime import datetime as _dt

            # ── Vraie simulation autoconso : 8760h PV synthétique × profil type Enedis ──
            tarif_revente = get_tarif_revente_s21(kwc)
            tarif_achat = _tarif_achat_industriel(sz['conso_mwh'])   # HTVA dégressif (SDES 2024)
            profil_type = _secteur_to_profile(sz['secteur'])
            prod_8760 = _synthetic_pv_8760_wh(kwc, sz['productible'])
            result = compute_autoconsommation(prod_8760, conso_kwh, profil_type)
            economics = compute_economics(
                kpis=result['kpis'], tarif_achat_kwh=tarif_achat, prix_revente_kwh=tarif_revente,
                duree_contrat_ans=25, tariff_type='BASE',
                hourly_production_wh=prod_8760,
                hourly_consumption_wh=result.get('hourly_consumption_wh'),
                hourly_autoconso_wh=result.get('hourly_autoconso_wh'),
                hourly_surplus_wh=result.get('hourly_surplus_wh'))
            autoconso_data = {
                'kpis': result['kpis'],
                'economics': {k: v for k, v in economics.items() if k != 'prix_8760'},
                'monthly': result['monthly'],
                'daily_profiles': result['daily_profiles'],
                'profil_type': profil_type,
                'profil_label': PROFILE_LABELS.get(profil_type, profil_type),
                'data_source': 'profil_type',
                'tariff_type': 'BASE',
                'tariff_label': TARIFF_LABELS.get('BASE', 'Base'),
                'date_calcul': _dt.now().isoformat(),
            }

            # ── Plan de situation : alias + rapport (coords, adresse, cadastre IGN) ──
            lat0 = prospect.get('latitude'); lon0 = prospect.get('longitude')
            prospect['lat'] = lat0; prospect['lon'] = lon0
            prospect['adresse_complete'] = prospect.get('adresse') or ''
            parc = _parcelle_au_point_ign(lat0, lon0)
            try:
                _dj = json.loads(prospect.get('data_json') or '{}')
                if not isinstance(_dj, dict):
                    _dj = {}
            except Exception:
                _dj = {}
            _dj['rapport'] = {
                'lat': lat0, 'lon': lon0,
                'commune_name': prospect.get('commune') or '',
                'code_postal': prospect.get('code_postal') or '',
                'adresse': prospect.get('adresse') or '',
                'api_details': {'cadastre': {'details': {
                    'section': parc.get('section', ''), 'parcelle_numero': parc.get('numero', ''),
                    'contenance_m2': parc.get('contenance', ''),
                    'code_insee': parc.get('code_insee') or (prospect.get('code_commune') or ''),
                }}},
            }
            prospect['data_json'] = _dj

            calpinage = {'totaux': {'puissanceTotale': kwc, 'nbModules': int(kwc / 0.55),
                                    'puissanceModule': 550}, 'zones': [],
                         'type_raccordement': 'autoconsommation'}
            parametres = {
                'type_projet': 'autoconsommation',
                'puissance_kwc': kwc,
                'prix_kwc': 550.0,
                'consommation_annuelle_kwh': conso_kwh,
                'tarif_achat_kwh': tarif_achat,
                'tarif_revente_kwh': tarif_revente,
                'taux_autoconso': result['kpis'].get('taux_autoconsommation', 70.0),
                'indicative': True,
                'autoconso_data': autoconso_data,
            }
            pdf = PropositionProfessionnelle(prospect, calpinage, parametres).generer_pdf()
            commune = (prospect.get('commune') or 'site').replace(' ', '_')
            fname = f"Pre-etude_{commune}_{kwc:.0f}kWc_{datetime.now().strftime('%Y%m%d')}.pdf"
            try:
                pdf.seek(0); save_to_dataroom(prospect_id, pdf.read(), fname, 'pre_etude', source='auto-pre-etude')
                pdf.seek(0)
            except Exception as _e:
                print(f"⚠️ [PRE-ETUDE] dataroom: {_e}")
            print(f"✅ [PRE-ETUDE] prospect {prospect_id}: {kwc:.0f} kWc (borné par {sz['borne_par']}), "
                  f"toiture {sz['surface_toiture_m2']} m²")
            return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name=fname)
        except Exception as e:
            print(f"❌ [PRE-ETUDE] {e}")
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/contact', methods=['POST'])
    def set_prospect_contact(prospect_id):
        """Attache un contact décideur (dirigeant, e-mail, téléphone) à une fiche.
        Stocké dans data_json.contact (affiché dans la vignette) + colonnes dirigeant_*."""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            row = execute_query("SELECT user_id, data_json FROM agriweb_prospects WHERE id = %s",
                                (prospect_id,), fetch_one=True)
            if not row:
                return jsonify({'success': False, 'error': 'Introuvable'}), 404
            if not is_admin and str(row.get('user_id')) != str(user_id):
                return jsonify({'success': False, 'error': 'Accès refusé'}), 403
            d = request.get_json(silent=True) or {}
            contact = {'decideur': (d.get('decideur') or '').strip(),
                       'email': (d.get('email') or '').strip(),
                       'telephone': (d.get('telephone') or '').strip(),
                       'qualite': (d.get('qualite') or '').strip(),
                       'source': (d.get('source') or 'manuel').strip()}
            try:
                dj = json.loads(row.get('data_json') or '{}')
                if not isinstance(dj, dict):
                    dj = {}
            except Exception:
                dj = {}
            dj['contact'] = contact
            execute_query(
                "UPDATE agriweb_prospects SET data_json=%s, dirigeant_nom=%s, dirigeant_email=%s, "
                "dirigeant_tel=%s WHERE id=%s",
                (json.dumps(dj, ensure_ascii=False), contact['decideur'], contact['email'],
                 contact['telephone'], prospect_id))
            return jsonify({'success': True, 'contact': contact})
        except Exception as e:
            print(f"❌ [CONTACT] {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/prospects/<int:prospect_id>/proposition-complete', methods=['POST'])
    def generer_proposition_complete(prospect_id):
        """
        Génère une proposition commerciale professionnelle complète avec:
        - Couverture + Sommaire
        - Présentation entreprise (certifications QualiPV, RGE)
        - Analyse site + contraintes urbanisme (PLU)
        - Solution technique (modules JA Solar, onduleurs Huawei)
        - Étude productible PVGIS
        - Étude financière (TRI, VAN, ROI)
        - Devis détaillé NF C 15-752-1 avec taxes IFER
        - Planning réalisation (DP, DDR, Consuel)
        - Garanties et maintenance
        - Aspects réglementaires
        - CGV
        """
        try:
            from proposition_professionnelle import PropositionProfessionnelle
            from autoconsommation import get_tarif_revente_s21
            from io import BytesIO
            
            # Récupérer les données de la requête
            data = request.json or {}
            
            # Récupérer le prospect
            prospect_result = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect_result:
                return jsonify({'error': 'Prospect non trouvé'}), 404
            
            prospect = dict(prospect_result)
            
            # Parser data_json pour récupérer toutes les données
            try:
                data_json = json.loads(prospect['data_json']) if prospect.get('data_json') else {}
                # data_json peut être une liste dans les anciens formats — normaliser en dict
                if isinstance(data_json, list):
                    data_json = {}
                calpinage = data_json.get('calpinage', {})
                # calpinage peut être une liste de zones (ancien format) — normaliser en dict
                if isinstance(calpinage, list):
                    calpinage = {'zones': calpinage, 'totaux': {}}
                visite_technique = data_json.get('visite_technique', {})
                rapport_commune = data_json.get('rapport_commune', {})
                
                # Vérifier que calpinage contient au moins les données minimales
                if not calpinage:
                    print(f"⚠️ Aucune donnée de calpinage trouvée, utilisation des paramètres fournis")
                    # Créer un calpinage minimal à partir des paramètres
                    calpinage = {
                        'totaux': {
                            'nbModules': int(safe_float(data.get('puissance_kwc', 100)) / 0.55),  # Approximation avec modules de 550W
                            'puissanceModule': 550,
                            'puissanceTotale': safe_float(data.get('puissance_kwc', 100))
                        },
                        'zones': [],
                        'type_raccordement': data.get('type_projet', 'autoconsommation')
                    }
            except Exception as e:
                print(f"⚠️ Erreur parsing data_json: {e}")
                import traceback
                traceback.print_exc()
                calpinage = {
                    'totaux': {
                        'nbModules': int(safe_float(data.get('puissance_kwc', 100)) / 0.55),
                        'puissanceModule': 550,
                        'puissanceTotale': safe_float(data.get('puissance_kwc', 100))
                    },
                    'zones': [],
                    'type_raccordement': data.get('type_projet', 'autoconsommation')
                }
                visite_technique = {}
                rapport_commune = {}
            
            # Fonction helper pour conversion sécurisée
            def safe_float(value, default=0.0):
                try:
                    if value is None or value == '':
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # Préparer les paramètres pour la proposition
            # Charger les résultats autoconsommation sauvegardés si disponibles
            autoconso_results = calpinage.get('autoconso_results', {})
            # autoconso_results peut être une liste dans les anciens formats — normaliser en dict
            if not isinstance(autoconso_results, dict):
                autoconso_results = {}

            # Dériver les paramètres financiers depuis les résultats autoconso si présents
            eco_saved = autoconso_results.get('economics', {})
            kpis_saved = autoconso_results.get('kpis', {})

            # Puissance : priorité calpinage réel > formulaire > défaut 100 kWc
            puissance_from_calpinage = safe_float(
                calpinage.get('totaux', {}).get('puissanceTotale')
                or calpinage.get('totaux', {}).get('puissance_totale'), 0.0)
            puissance_from_form = safe_float(data.get('puissance_kwc'), 0.0)
            puissance_finale = puissance_from_calpinage or puissance_from_form or 100.0
            print(f"📐 Puissance: calpinage={puissance_from_calpinage} kWc / form={puissance_from_form} kWc → finale={puissance_finale} kWc")

            parametres = {
                'type_projet': data.get('type_projet', 'autoconsommation'),
                'puissance_kwc': puissance_finale,
                'prix_kwc': safe_float(data.get('prix_kwc'), 850.0),
                'consommation_annuelle_kwh': safe_float(
                    data.get('consommation_annuelle_kwh')
                    or kpis_saved.get('consommation_annuelle_kwh'), 0.0),   # clé correcte
                'tarif_achat_kwh': safe_float(
                    data.get('tarif_achat_kwh')
                    or eco_saved.get('tarif_achat'), 0.20),
                'tarif_revente_kwh': safe_float(
                    data.get('tarif_revente_kwh')
                    or eco_saved.get('tarif_revente')
                    or get_tarif_revente_s21(puissance_finale), 0.0536),
                # taux_autoconsommation est déjà en % (ex: 75.0) - pas de * 100
                'taux_autoconso': safe_float(
                    data.get('taux_autoconso')
                    or kpis_saved.get('taux_autoconsommation', 70.0), 70.0),
                'pvgis_hourly_data': data.get('pvgis_hourly_data'),
                'enedis_hourly_data': data.get('enedis_hourly_data'),
                # Résultats complets de la simulation autoconsommation
                'autoconso_data': autoconso_results if autoconso_results else None,
            }
            
            print(f"📊 Génération proposition - Paramètres: {parametres}")
            
            # Toujours enrichir prospect avec data_json complet (rapport, visite_technique, rapport_commune, etc.)
            # Ne pas conditionner au seul rapport_commune — le PDF lit aussi rapport, visite_technique, etc.
            prospect['data_json'] = data_json

            # Surcharger depuis le POST body si le frontend a envoyé des clés plus fraîches
            for _dj_key in ('rapport', 'visite_technique', 'rapport_commune'):
                if data.get(_dj_key):
                    data_json[_dj_key] = data[_dj_key]
                    prospect['data_json'] = data_json

            # Injecter les screenshots depuis la requête (priorité) ou depuis la DB
            for _ss_key in ('screenshot_map', 'screenshot_plan_masse', 'screenshot_3d',
                            'screenshot_irradiation', 'screenshot_situation_z14'):
                _from_req = data.get(_ss_key, '')
                _from_db  = calpinage.get(_ss_key, '')
                val = _from_req or _from_db
                if val:
                    calpinage[_ss_key] = val
            # Debug : état des screenshots au moment de la génération
            _ss_map   = calpinage.get('screenshot_map', '')
            _ss_masse = calpinage.get('screenshot_plan_masse', '')
            _ss_3d    = calpinage.get('screenshot_3d', '')
            print(f"📸 screenshot_map:        {'OK '+str(len(str(_ss_map)))+' chars' if _ss_map else 'ABSENT'}")
            print(f"📸 screenshot_plan_masse: {'OK '+str(len(str(_ss_masse)))+' chars' if _ss_masse else 'ABSENT'}")
            print(f"📸 screenshot_3d:         {'OK '+str(len(str(_ss_3d)))+' chars' if _ss_3d else 'ABSENT'}")
            # Synchroniser data_json avec le calpinage enrichi (screenshots inclus)
            data_json['calpinage'] = calpinage
            # Toujours passer data_json complet au prospect pour que self.data_json soit peuplé
            prospect['data_json'] = data_json
            
            # Générer la proposition professionnelle
            try:
                print(f"🔧 Création instance PropositionProfessionnelle...")
                proposition = PropositionProfessionnelle(prospect, calpinage, parametres)
                print(f"📄 Génération PDF...")
                buffer = proposition.generer_pdf()
                print(f"✅ PDF généré avec succès!")
            except Exception as e:
                import traceback
                print(f"❌ Erreur dans PropositionProfessionnelle: {e}")
                print(f"📊 Prospect: {prospect.get('id')} - {prospect.get('commune')}")
                print(f"📊 Calpinage keys: {list(calpinage.keys()) if calpinage else 'None'}")
                print(f"📊 Parametres: {parametres}")
                traceback.print_exc()
                raise
            
            buffer.seek(0)
            
            # Marquer l'étape "Devis commercial" comme terminée (par nom, indépendamment de l'ordre)
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,),
                fetch_one=True
            )
            if project:
                execute_query('''
                    UPDATE project_etapes 
                    SET statut = 'termine', 
                        date_fin_reelle = CURRENT_DATE
                    WHERE project_id = %s 
                    AND nom_etape = 'Devis commercial'
                    AND statut != 'termine'
                ''', (project['id'],))
                print(f"✅ [ETAPE UPDATE] Étape 'Devis commercial' marquée comme terminée pour projet {project['id']}")
            
            # Sauvegarder automatiquement dans la dataroom
            prop_filename = f'Proposition_Professionnelle_{prospect.get("commune", "NA")}_{datetime.now().strftime("%Y%m%d")}.pdf'
            try:
                buffer.seek(0)
                pdf_bytes = buffer.read()
                save_to_dataroom(prospect_id, pdf_bytes, prop_filename, 'proposition', source='auto-proposition')
                buffer.seek(0)
            except Exception as dr_err:
                print(f"⚠️ [DATAROOM] Erreur sauvegarde proposition: {dr_err}")
            
            # Retourner le PDF
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=prop_filename
            )
            
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"❌ [PROPOSITION] ERREUR COMPLETE:\n{tb}")
            return jsonify({'error': str(e), 'traceback': tb}), 500
    # ============================================================================
    @app.route('/api/crm/admin/cleanup-all', methods=['POST'])
    def cleanup_all_prospects():
        """Supprime TOUS les prospects et projets associés - ATTENTION DANGEREUX"""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Accès admin requis'}), 403

            # Supprimer tous les projets et étapes (CASCADE)
            execute_query('DELETE FROM project_fiches')
            
            # Supprimer tous les prospects
            result = execute_query('DELETE FROM agriweb_prospects RETURNING id', fetch_all=True)
            count = len(result) if result else 0
            
            return jsonify({
                'success': True,
                'message': f'✅ {count} prospects supprimés avec succès',
                'deleted_count': count
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/admin/find-user', methods=['GET'])
    def admin_find_user():
        """LECTURE SEULE : retrouve des comptes par nom/email/société + nb de prospects."""
        _uid, is_admin = get_current_crm_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin requis'}), 403
        q = (request.args.get('q') or '').strip().lower()
        if len(q) < 2:
            return jsonify({'success': False, 'error': 'q (>=2 car.) requis'}), 400
        try:
            from auth_database import get_auth_db
            conn = get_auth_db(); cur = conn.cursor()
            like = f'%{q}%'
            cur.execute("SELECT id, email, name, company FROM users "
                        "WHERE LOWER(name) LIKE ? OR LOWER(email) LIKE ? OR LOWER(COALESCE(company,'')) LIKE ? "
                        "ORDER BY id LIMIT 20", (like, like, like))
            rows = cur.fetchall(); conn.close()
            users = []
            for r in rows:
                uid = r[0]
                c = execute_query("SELECT COUNT(*) AS n FROM agriweb_prospects WHERE user_id = %s",
                                  (str(uid),), fetch_one=True) or {}
                users.append({'id': uid, 'email': r[1], 'name': r[2], 'company': r[3],
                              'nb_prospects': int((dict(c)).get('n') or 0)})
            return jsonify({'success': True, 'users': users})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/admin/vider-prospects', methods=['POST'])
    def admin_vider_prospects():
        """Supprime TOUS les prospects d'UN compte (cible par email). Admin only."""
        _uid, is_admin = get_current_crm_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin requis'}), 403
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip()
        if not email:
            return jsonify({'success': False, 'error': 'email requis'}), 400
        target_id = _resolve_user_id_by_email(email)
        if target_id is None:
            return jsonify({'success': False, 'error': f'Utilisateur {email} introuvable'}), 404
        try:
            res = execute_query('DELETE FROM agriweb_prospects WHERE user_id = %s RETURNING id',
                                (str(target_id),), fetch_all=True)
            count = len(res) if res else 0
            return jsonify({'success': True, 'email': email, 'target_user_id': target_id, 'deleted': count})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/admin/recreate-user', methods=['POST'])
    def admin_recreate_user():
        """(Re)cree un compte UTILISATEUR NORMAL (non-admin) : supprime l'existant
        puis cree un compte actif, email verifie, essai 30 j, avec un mot de passe
        connu. Admin only. Body: {email, password, name?}."""
        _uid, is_admin = get_current_crm_user()
        if not is_admin:
            return jsonify({'success': False, 'error': 'Admin requis'}), 403
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        name = (data.get('name') or (email.split('@')[0] if email else '')).strip()
        if not email or not password:
            return jsonify({'success': False, 'error': 'email et password requis'}), 400
        try:
            from auth_system_improved import AuthSystem
            from auth_database import get_auth_db
            from datetime import datetime as _dt, timedelta as _td
            ph, salt = AuthSystem().hash_password(password)
            conn = get_auth_db(); cur = conn.cursor()
            # Supprimer l'existant (sessions puis user) pour une recreation propre
            cur.execute("SELECT id, is_admin FROM users WHERE email = ?", (email,))
            old = cur.fetchone()
            recreated = False
            if old:
                oid = old[0]
                for _q in ("DELETE FROM user_sessions WHERE user_id = ?",):
                    try: cur.execute(_q, (oid,))
                    except Exception:
                        try: cur.execute(_q, (str(oid),))
                        except Exception: pass
                cur.execute("DELETE FROM users WHERE email = ?", (email,))
                recreated = True
            ts = _dt.now(); te = ts + _td(days=30)
            cur.execute('''INSERT INTO users
                (email, name, company, password_hash, salt, is_email_verified,
                 trial_start_date, trial_end_date, subscription_status, is_active, is_admin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (email, name or 'Utilisateur', '', ph, salt, True, ts, te, 'trial', True, False))
            conn.commit()
            cur.execute("SELECT id FROM users WHERE email = ?", (email,))
            newid = cur.fetchone()[0]
            conn.close()
            return jsonify({'success': True, 'email': email, 'user_id': newid,
                            'recreated': recreated, 'is_admin': False,
                            'subscription': 'trial', 'trial_end': te.strftime('%Y-%m-%d')})
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
    # ROUTES PARAMÉTRAGE SYSTÈME
    # ============================================================================

    @app.route('/api/crm/parametrage')
    def page_parametrage():
        """Page de paramétrage système"""
        return render_template('parametrage.html')
    
    @app.route('/api/crm/parametrage/check-init')
    def check_init_parametrage():
        """Vérifier si les tables de paramétrage existent"""
        try:
            # Vérifier existence table parametrage_entreprise
            result = execute_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'parametrage_entreprise'
                )
            """, fetch_one=True)
            
            initialized = result['exists'] if result else False
            
            return jsonify({
                'success': True,
                'initialized': initialized
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/parametrage/init-database', methods=['GET', 'POST'])
    def init_database_parametrage():
        """Initialiser les tables de paramétrage avec données par défaut"""
        try:
            # Lire le script SQL
            sql_file = os.path.join(os.path.dirname(__file__), 'create_tables_parametrage.sql')
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # Séparer les commandes SQL pour PostgreSQL
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Séparer par point-virgule et exécuter commande par commande
                commands = []
                current_command = []
                
                for line in sql_script.split('\n'):
                    # Ignorer les commentaires
                    if line.strip().startswith('--'):
                        continue
                    
                    current_command.append(line)
                    
                    # Si ligne contient un point-virgule, c'est une fin de commande
                    if ';' in line:
                        command = '\n'.join(current_command).strip()
                        if command and not command.startswith('--'):
                            commands.append(command)
                        current_command = []
                
                # Exécuter chaque commande
                executed = 0
                errors = []
                for command in commands:
                    if command.strip():
                        try:
                            cursor.execute(command)
                            executed += 1
                        except Exception as e:
                            # Enregistrer les erreurs mais continuer
                            error_msg = f"{str(e)[:100]}"
                            print(f"⚠️ SQL warning: {error_msg}")
                            errors.append(error_msg)
                            continue
                
                conn.commit()
                cursor.close()
            
            print(f"✅ {executed} commandes SQL exécutées, {len(errors)} erreurs")
            
            return jsonify({
                'success': True,
                'message': f'{executed} commandes exécutées avec succès',
                'errors': errors[:10] if errors else [],  # Max 10 premières erreurs
                'total_errors': len(errors)
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/parametrage/migrate-database', methods=['POST'])
    def migrate_database_parametrage():
        """Migration: Ajouter les colonnes manquantes à parametrage_prix_organes"""
        try:
            migration_queries = [
                # 1. Ajouter description
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'parametrage_prix_organes' 
                        AND column_name = 'description'
                    ) THEN
                        ALTER TABLE parametrage_prix_organes 
                        ADD COLUMN description TEXT;
                    END IF;
                END $$;
                """,
                # 2. Ajouter delai_livraison_jours
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'parametrage_prix_organes' 
                        AND column_name = 'delai_livraison_jours'
                    ) THEN
                        ALTER TABLE parametrage_prix_organes 
                        ADD COLUMN delai_livraison_jours INTEGER;
                    END IF;
                END $$;
                """,
                # 3. Ajouter stock_disponible
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'parametrage_prix_organes' 
                        AND column_name = 'stock_disponible'
                    ) THEN
                        ALTER TABLE parametrage_prix_organes 
                        ADD COLUMN stock_disponible BOOLEAN DEFAULT TRUE;
                    END IF;
                END $$;
                """,
                # 4. Ajouter date_dernier_prix
                """
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'parametrage_prix_organes' 
                        AND column_name = 'date_dernier_prix'
                    ) THEN
                        ALTER TABLE parametrage_prix_organes 
                        ADD COLUMN date_dernier_prix DATE DEFAULT CURRENT_DATE;
                    END IF;
                END $$;
                """
            ]
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                executed = 0
                errors = []
                
                for query in migration_queries:
                    try:
                        cursor.execute(query)
                        executed += 1
                    except Exception as e:
                        errors.append(str(e)[:100])
                
                conn.commit()
                cursor.close()
            
            return jsonify({
                'success': True,
                'message': f'{executed} migrations exécutées',
                'errors': errors
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def _ensure_parametrage_user_id_column():
        """Migration auto : ajoute user_id a parametrage_entreprise si absent.
        Idempotente. Appelee a chaque GET/POST sur les routes parametrage."""
        try:
            execute_query("""
                ALTER TABLE parametrage_entreprise
                ADD COLUMN IF NOT EXISTS user_id INTEGER
            """)
        except Exception as e:
            # Si la DB ne supporte pas IF NOT EXISTS sur ADD COLUMN, on essaie sans
            print(f"⚠️ [PARAM] migration user_id : {e}")


    @app.route('/api/crm/parametrage/entreprise', methods=['GET', 'POST'])
    def parametrage_entreprise():
        """GET: Charger les infos entreprise du user courant, POST: Sauvegarder.
        Multi-tenant : chaque user (ou couple admin / admin_view_as) a sa propre
        ligne. Les anciennes lignes sans user_id sont visibles uniquement aux
        admins en mode normal (back-compat)."""
        _ensure_parametrage_user_id_column()

        # Identifie le user courant (respecte admin_view_as)
        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Non authentifie'}), 401

        try:
            if request.method == 'GET':
                # 1) cherche ligne specifique au user
                result = execute_query(
                    'SELECT * FROM parametrage_entreprise WHERE user_id = %s AND actif = TRUE ORDER BY id DESC LIMIT 1',
                    (user_id,),
                    fetch_one=True
                )
                # 2) fallback : ligne legacy (user_id IS NULL) — uniquement admin
                if not result and is_admin:
                    result = execute_query(
                        'SELECT * FROM parametrage_entreprise WHERE user_id IS NULL AND actif = TRUE ORDER BY id DESC LIMIT 1',
                        fetch_one=True
                    )

                return jsonify({
                    'success': True,
                    'entreprise': dict(result) if result else None
                })

            else:  # POST
                data = request.json or {}

                # Convertir les dates vides en None (PostgreSQL n'accepte pas '' pour DATE)
                for date_field in ('rge_date_validite', 'qualibat_date_validite'):
                    if date_field in data and not data[date_field]:
                        data[date_field] = None

                # Cherche d'abord une ligne pour ce user_id
                existing = execute_query(
                    'SELECT id FROM parametrage_entreprise WHERE user_id = %s AND actif = TRUE LIMIT 1',
                    (user_id,),
                    fetch_one=True
                )

                if existing:
                    # UPDATE (sur la ligne du user)
                    execute_query("""
                        UPDATE parametrage_entreprise SET
                            nom_entreprise = %s,
                            adresse = %s,
                            code_postal = %s,
                            ville = %s,
                            telephone = %s,
                            email = %s,
                            site_web = %s,
                            siret = %s,
                            tva_intracommunautaire = %s,
                            rge_numero = %s,
                            rge_date_validite = %s,
                            qualibat_numero = %s,
                            qualibat_date_validite = %s,
                            qualifelec_numero = %s,
                            logo_base64 = %s,
                            date_modification = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        data.get('nom_entreprise'),
                        data.get('adresse'),
                        data.get('code_postal'),
                        data.get('ville'),
                        data.get('telephone'),
                        data.get('email'),
                        data.get('site_web'),
                        data.get('siret'),
                        data.get('tva_intracommunautaire'),
                        data.get('rge_numero'),
                        data.get('rge_date_validite'),
                        data.get('qualibat_numero'),
                        data.get('qualibat_date_validite'),
                        data.get('qualifelec_numero'),
                        data.get('logo_base64'),
                        existing['id']
                    ))
                else:
                    # INSERT (nouvelle ligne pour ce user_id)
                    execute_query("""
                        INSERT INTO parametrage_entreprise (
                            user_id,
                            nom_entreprise, adresse, code_postal, ville, telephone, email, site_web,
                            siret, tva_intracommunautaire, rge_numero, rge_date_validite,
                            qualibat_numero, qualibat_date_validite, qualifelec_numero, logo_base64
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        data.get('nom_entreprise'),
                        data.get('adresse'),
                        data.get('code_postal'),
                        data.get('ville'),
                        data.get('telephone'),
                        data.get('email'),
                        data.get('site_web'),
                        data.get('siret'),
                        data.get('tva_intracommunautaire'),
                        data.get('rge_numero'),
                        data.get('rge_date_validite'),
                        data.get('qualibat_numero'),
                        data.get('qualibat_date_validite'),
                        data.get('qualifelec_numero'),
                        data.get('logo_base64')
                    ))

                print(f"✅ Paramétrage entreprise sauvegardé pour user_id={user_id}")
                return jsonify({'success': True})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/parametrage/prix', methods=['GET', 'POST'])
    def parametrage_prix():
        """GET: Lister les prix, POST: Ajouter un prix"""
        try:
            if request.method == 'GET':
                # Filtres optionnels
                categorie = request.args.get('categorie')
                search = request.args.get('search')
                
                query = 'SELECT * FROM parametrage_prix_organes WHERE actif = TRUE'
                params = []
                
                if categorie:
                    query += ' AND categorie = %s'
                    params.append(categorie)
                
                if search:
                    query += ' AND (nom_organe ILIKE %s OR marque ILIKE %s OR modele ILIKE %s)'
                    params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
                
                query += ' ORDER BY categorie, nom_organe'
                
                result = execute_query(query, tuple(params), fetch_all=True)
                
                return jsonify({
                    'success': True,
                    'prix': [dict(row) for row in result] if result else []
                })
            
            else:  # POST
                data = request.json
                
                execute_query("""
                    INSERT INTO parametrage_prix_organes (
                        nom_organe, categorie, marque, modele, prix_unitaire_ht, unite, marge_commerciale_pct
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get('nom_organe'),
                    data.get('categorie'),
                    data.get('marque'),
                    data.get('modele'),
                    data.get('prix_unitaire_ht'),
                    data.get('unite'),
                    data.get('marge_commerciale_pct', 15.0)
                ))
                
                print(f"✅ Prix ajouté: {data.get('nom_organe')}")
                return jsonify({'success': True})
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/parametrage/prix/<int:prix_id>', methods=['DELETE'])
    def delete_prix(prix_id):
        """Supprimer un prix (soft delete)"""
        try:
            execute_query(
                'UPDATE parametrage_prix_organes SET actif = FALSE WHERE id = %s',
                (prix_id,)
            )
            
            print(f"✅ Prix {prix_id} supprimé")
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/crm/parametrage/graphique', methods=['GET', 'POST'])
    def parametrage_graphique():
        """GET: Charger les couleurs du user, POST: Sauvegarder. Multi-tenant."""
        _ensure_parametrage_user_id_column()

        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Non authentifie'}), 401

        try:
            if request.method == 'GET':
                # 1) ligne du user
                result = execute_query(
                    'SELECT couleur_primaire, couleur_secondaire, couleur_accent FROM parametrage_entreprise WHERE user_id = %s AND actif = TRUE LIMIT 1',
                    (user_id,),
                    fetch_one=True
                )
                # 2) fallback legacy pour admin
                if not result and is_admin:
                    result = execute_query(
                        'SELECT couleur_primaire, couleur_secondaire, couleur_accent FROM parametrage_entreprise WHERE user_id IS NULL AND actif = TRUE LIMIT 1',
                        fetch_one=True
                    )

                return jsonify({
                    'success': True,
                    'graphique': dict(result) if result else None
                })

            else:  # POST
                data = request.json or {}

                # Cherche la ligne du user
                existing = execute_query(
                    'SELECT id FROM parametrage_entreprise WHERE user_id = %s AND actif = TRUE LIMIT 1',
                    (user_id,),
                    fetch_one=True
                )

                if existing:
                    execute_query("""
                        UPDATE parametrage_entreprise SET
                            couleur_primaire = %s,
                            couleur_secondaire = %s,
                            couleur_accent = %s,
                            date_modification = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        data.get('couleur_primaire'),
                        data.get('couleur_secondaire'),
                        data.get('couleur_accent'),
                        existing['id']
                    ))
                else:
                    # Pas encore de ligne entreprise pour ce user :
                    # on cree une ligne minimale avec les couleurs.
                    execute_query("""
                        INSERT INTO parametrage_entreprise (
                            user_id, nom_entreprise,
                            couleur_primaire, couleur_secondaire, couleur_accent
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        'Mon entreprise',  # default placeholder
                        data.get('couleur_primaire'),
                        data.get('couleur_secondaire'),
                        data.get('couleur_accent')
                    ))

                print(f"✅ Couleurs sauvegardées pour user_id={user_id}")
                return jsonify({'success': True})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ============================================================================
    # ROUTES GÉNÉRATION DOCUMENTS - DÉCLARATION PRÉALABLE
    # ============================================================================
    
    @app.route('/api/crm/prospect/<int:prospect_id>/generer-dp', methods=['POST'])
    @require_prospect_owner
    def generer_declaration_prealable(prospect_id):
        """
        Génère le dossier complet de Déclaration Préalable de Travaux (DP)
        pour un prospect avec son calpinage intégré.
        
        Retourne un fichier ZIP contenant les 9 documents PDF:
        - Formulaire CERFA 13703*09 (4 pages)
        - Plan DP1 - Plan de situation
        - Plan DP2 - Plan de masse coté
        - Plan DP3 - Plan en coupe
        - Plan DP4 - Façades état actuel
        - Plan DP5 - Façades état projeté
        - Plan DP6 - Insertion paysagère
        - Plan DP7 - Environnement proche
        - Plan DP8 - Environnement lointain
        """
        try:
            print(f"\n{'='*70}")
            print(f"📄 [GÉNÉRATION DP] Début pour prospect {prospect_id}")
            print(f"{'='*70}")
            
            # 1. Récupérer le prospect depuis la base de données
            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not row:
                print(f"❌ [GÉNÉRATION DP] Prospect {prospect_id} non trouvé")
                return jsonify({
                    'success': False,
                    'error': f'Prospect {prospect_id} non trouvé'
                }), 404
            
            # Convertir en dictionnaire
            prospect_data = dict(row)
            print(f"✓ Prospect récupéré: {prospect_data.get('nom_entreprise', prospect_data.get('nom_prospect', 'N/A'))}")
            
            # 2. Extraire le calpinage et fusionner data_json dans prospect_data
            calpinage_data = None
            data_json = {}
            if prospect_data.get('data_json'):
                # Parser si c'est une chaîne JSON
                if isinstance(prospect_data['data_json'], str):
                    try:
                        data_json = json.loads(prospect_data['data_json'])
                        calpinage_data = data_json.get('calpinage')
                    except Exception as e:
                        print(f"⚠️ [GÉNÉRATION DP] Erreur parsing data_json: {e}")
                # Sinon c'est déjà un dict (PostgreSQL JSONB)
                elif isinstance(prospect_data['data_json'], dict):
                    data_json = prospect_data['data_json']
                    calpinage_data = data_json.get('calpinage')
            
            # Fusionner les champs enrichis de data_json dans prospect_data
            # (propriétaire, SIRENE, etc.) sans écraser les colonnes existantes non-nulles
            enrichment_keys = [
                'proprietaire_denomination', 'proprietaire_adresse', 'proprietaire_code_postal',
                'proprietaire_ville', 'proprietaire_siren', 'prenom_prospect',
                'nom_entreprise', 'type_raccordement'
            ]
            for key in enrichment_keys:
                if key not in prospect_data or not prospect_data.get(key):
                    val = data_json.get(key)
                    if val:
                        prospect_data[key] = val
                        print(f"  ✓ Enrichi depuis data_json: {key} = {str(val)[:50]}")
            
            if calpinage_data:
                nb_modules = sum(zone.get('nbModules', 0) for zone in calpinage_data.get('zones', []))
                orientation = calpinage_data.get('zones', [{}])[0].get('moduleOrientation', 'N/A') if calpinage_data.get('zones') else 'N/A'
                print(f"✓ Calpinage trouvé: {nb_modules} modules, orientation: {orientation}")
            else:
                print(f"⚠️ [GÉNÉRATION DP] Aucun calpinage trouvé pour ce prospect")
            
            # 3. Générer le dossier complet DP
            print(f"\n📊 Génération des 9 documents PDF...")
            pdfs = generate_declaration_prealable_complete(prospect_data, calpinage_data)
            
            if not pdfs:
                print(f"❌ [GÉNÉRATION DP] Échec de génération des PDFs")
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de la génération des documents PDF'
                }), 500
            
            print(f"✅ {len(pdfs)} documents PDF générés")
            
            # 4. Créer un fichier ZIP en mémoire
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for filename, pdf_bytes in pdfs.items():
                    zip_file.writestr(filename, pdf_bytes.getvalue())
                    print(f"  ✓ Ajouté au ZIP: {filename}")
            
            zip_buffer.seek(0)
            
            # 5. Nom du fichier ZIP
            commune = prospect_data.get('commune', 'Inconnu').replace(' ', '_')
            nom = prospect_data.get('nom_entreprise', prospect_data.get('nom', 'Prospect')).replace(' ', '_')
            zip_filename = f"DP_Complet_{commune}_{nom}_{datetime.now().strftime('%Y%m%d')}.zip"
            
            print(f"\n{'='*70}")
            print(f"✅ [GÉNÉRATION DP] Dossier complet créé: {zip_filename}")
            print(f"{'='*70}\n")
            
            # 6. Retourner le fichier ZIP pour téléchargement
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=zip_filename
            )
            
        except Exception as e:
            print(f"\n{'='*70}")
            print(f"❌ [GÉNÉRATION DP] ERREUR")
            print(f"{'='*70}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'error': f'Erreur lors de la génération: {str(e)}'
            }), 500
    
    @app.route('/api/crm/prospect/<int:prospect_id>/generer-plan-masse', methods=['POST'])
    def generer_plan_masse_cadastral(prospect_id):
        """
        Génère un plan de masse cadastral avec implantation PV selon calpinage
        
        Retourne un PDF A3 professionnel avec:
        - Fond satellite haute résolution
        - Parcelles cadastrales délimitées
        - Bâtiment coté
        - Modules PV positionnés selon le calpinage réel
        - Légende et cartouche technique
        """
        try:
            print(f"\n{'='*70}")
            print(f"📐 [PLAN DE MASSE] Génération pour prospect {prospect_id}")
            print(f"{'='*70}")
            
            # 1. Récupérer le prospect
            row = execute_query(
                "SELECT * FROM agriweb_prospects WHERE id = %s",
                (prospect_id,),
                fetch_one=True
            )
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': f'Prospect {prospect_id} non trouvé'
                }), 404
            
            prospect_data = dict(row)
            
            # 2. Extraire calpinage ET parcelles cadastrales depuis la base de données
            calpinage_data = None
            if prospect_data.get('data_json'):
                if isinstance(prospect_data['data_json'], str):
                    try:
                        data_json = json.loads(prospect_data['data_json'])
                        calpinage_data = data_json.get('calpinage')
                        
                        # 🔧 CORRECTION: Extraire les parcelles cadastrales depuis data_json
                        if 'parcelles_cadastrales' in data_json and data_json['parcelles_cadastrales']:
                            prospect_data['parcelles_cadastrales'] = data_json['parcelles_cadastrales']
                            print(f"✓ Parcelles cadastrales: {len(data_json['parcelles_cadastrales'])} trouvée(s) dans data_json")
                        
                    except Exception as e:
                        print(f"⚠️ Erreur parsing data_json: {e}")
                        pass
                elif isinstance(prospect_data['data_json'], dict):
                    calpinage_data = prospect_data['data_json'].get('calpinage')
                    
                    # 🔧 CORRECTION: Extraire les parcelles cadastrales depuis data_json (dict)
                    if 'parcelles_cadastrales' in prospect_data['data_json']:
                        prospect_data['parcelles_cadastrales'] = prospect_data['data_json']['parcelles_cadastrales']
                        print(f"✓ Parcelles cadastrales: {len(prospect_data['parcelles_cadastrales'])} trouvée(s)")
            
            if calpinage_data:
                nb_modules = sum(z.get('nbModules', 0) for z in calpinage_data.get('zones', []))
                has_metadata = 'map_metadata' in calpinage_data
                print(f"✓ Calpinage: {nb_modules} modules, map_metadata={'✅' if has_metadata else '❌'}")
            
            # 3. Générer le plan de masse avec le générateur ULTIME_CLEAN
            pdf_buffer = generate_plan_masse(prospect_data, calpinage_data)
            
            # 4. Nom du fichier
            commune = prospect_data.get('commune', 'Inconnu').replace(' ', '_')
            filename = f"Plan_Masse_Cadastral_{commune}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            print(f"✅ [PLAN DE MASSE] Fichier créé: {filename}")
            
            # 5. Sauvegarder automatiquement dans la dataroom
            try:
                pdf_buffer.seek(0)
                pdf_bytes = pdf_buffer.read()
                save_to_dataroom(prospect_id, pdf_bytes, filename, 'plan_masse', source='auto-plan-masse')
                pdf_buffer.seek(0)
            except Exception as dr_err:
                print(f"⚠️ [DATAROOM] Erreur sauvegarde plan de masse: {dr_err}")
            
            print(f"{'='*70}\n")
            
            # 6. Retourner le PDF
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
            
        except Exception as e:
            print(f"❌ [PLAN DE MASSE] ERREUR: {e}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'error': f'Erreur: {str(e)}'
            }), 500


def register_autoconso_routes(app):
    """
    Enregistre les routes pour l'autoconsommation collective
    """
    from shapely.geometry import shape, Point
    import math
    import requests
    
    def get_sirene_by_siret(siret):
        """
        Récupère les données d'une entreprise via l'API SIRENE officielle
        https://api.insee.fr/entreprises/sirene/V3/siret/{siret}
        """
        if not siret or len(siret) < 14:
            return None
        
        try:
            url = f"https://api.insee.fr/entreprises/sirene/V3/siret/{siret}"
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'HeliaPV/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                etablissement = data.get('etablissement', {})
                unite_legale = etablissement.get('uniteLegale', {})
                
                return {
                    'siret': siret,
                    'denomination': (
                        unite_legale.get('denominationUniteLegale') or
                        unite_legale.get('prenomUsuelUniteLegale', '') + ' ' + unite_legale.get('nomUniteLegale', '') or
                        etablissement.get('enseigne1Etablissement') or
                        ''
                    ).strip(),
                    'activite': unite_legale.get('activitePrincipaleUniteLegale', ''),
                    'tranche_effectifs': unite_legale.get('trancheEffectifsUniteLegale', ''),
                    'etat': etablissement.get('etatAdministratifEtablissement', ''),
                    'categorie': unite_legale.get('categorieJuridiqueUniteLegale', '')
                }
            elif response.status_code == 404:
                print(f"⚠️ [API SIRENE] SIRET {siret} non trouvé")
                return None
            else:
                print(f"⚠️ [API SIRENE] Erreur {response.status_code} pour SIRET {siret}")
                return None
                
        except Exception as e:
            print(f"❌ [API SIRENE] Erreur requête: {e}")
            return None
    import requests
    
    def get_entreprise_from_siret(siret):
        """
        Interroge l'API SIRENE de l'INSEE pour récupérer les infos d'une entreprise
        https://api.insee.fr/entreprises/sirene/V3/siret/{siret}
        """
        if not siret or len(siret) != 14:
            return None
        
        try:
            # API SIRENE publique (pas besoin de token pour consultation simple)
            url = f"https://api.insee.fr/entreprises/sirene/V3/siret/{siret}"
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'HeliaPV/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                etablissement = data.get('etablissement', {})
                unite_legale = etablissement.get('uniteLegale', {})
                periode = etablissement.get('periodesEtablissement', [{}])[0] if etablissement.get('periodesEtablissement') else {}
                
                return {
                    'siret': siret,
                    'denomination': (
                        unite_legale.get('denominationUniteLegale') or
                        unite_legale.get('nomUniteLegale') or
                        periode.get('enseigne1Etablissement') or
                        ''
                    ),
                    'activite': unite_legale.get('activitePrincipaleUniteLegale', ''),
                    'tranche_effectifs': unite_legale.get('trancheEffectifsUniteLegale', ''),
                    'etat': etablissement.get('etatAdministratifEtablissement', ''),
                    'adresse': etablissement.get('adresseEtablissement', {})
                }
            elif response.status_code == 404:
                print(f"⚠️ [API SIRENE] SIRET {siret} non trouvé dans l'API INSEE")
                return None
            else:
                print(f"⚠️ [API SIRENE] Erreur HTTP {response.status_code} pour SIRET {siret}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏱️ [API SIRENE] Timeout pour SIRET {siret}")
            return None
        except Exception as e:
            print(f"❌ [API SIRENE] Erreur pour SIRET {siret}: {e}")
            return None
    
    def get_sirene_by_adresse(adresse, commune=None):
        """
        Recherche les entreprises par adresse via l'API Recherche-Entreprises.gouv.fr
        API publique, gratuite, sans token : https://recherche-entreprises.api.gouv.fr
        
        Args:
            adresse: Adresse du point de consommation
            commune: Nom de la commune pour filtrer géographiquement (IMPORTANT!)
        """
        if not adresse or len(adresse) < 5:
            return []
        
        try:
            # Nettoyer l'adresse
            adresse_clean = adresse.strip().replace('  ', ' ')
            
            # IMPORTANT: Ajouter la commune pour éviter les résultats d'autres régions
            query = f"{adresse_clean} {commune}" if commune else adresse_clean
            
            # API Recherche-Entreprises (publique, gratuite, sans token)
            url = "https://recherche-entreprises.api.gouv.fr/search"
            params = {
                'q': query,
                'per_page': 5,  # Limiter à 5 résultats
                'page': 1
            }
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'HeliaPV/2.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results_data = data.get('results', [])
                total = data.get('total_results', 0)
                
                if not results_data:
                    print(f"⚠️ [API ENTREPRISE] Aucun résultat pour: {query[:50]}")
                    return []
                
                print(f"✅ [API ENTREPRISE] {total} entreprise(s) trouvée(s) pour: {query[:50]} (affichage: {len(results_data)})")
                
                # FILTRER les résultats pour ne garder QUE ceux de la commune ciblée
                results = []
                for entreprise in results_data:
                    siege = entreprise.get('siege', {})
                    commune_entreprise = siege.get('libelle_commune', '').upper()
                    
                    # Vérifier si la commune correspond (ignorer la casse)
                    if commune and commune_entreprise:
                        commune_clean = commune.upper().strip()
                        # Ne garder que si la commune correspond exactement
                        if commune_clean not in commune_entreprise:
                            print(f"⚠️ [FILTRE] Rejeté: {entreprise.get('nom_complet', 'N/A')[:40]} ({commune_entreprise}) != {commune_clean}")
                            continue
                    
                    results.append({
                        'siret': siege.get('siret', ''),
                        'denomination': entreprise.get('nom_complet', '') or entreprise.get('nom_raison_sociale', ''),
                        'activite': siege.get('activite_principale', ''),
                        'tranche_effectifs': '',  # Non disponible dans cette API
                        'etat': siege.get('etat_administratif', ''),
                        'categorie': '',  # Non disponible directement
                        'adresse_complete': siege.get('adresse', ''),
                        'commune': commune_entreprise,
                        'code_postal': siege.get('code_postal', ''),
                        'latitude': siege.get('latitude', ''),
                        'longitude': siege.get('longitude', '')
                    })
                
                if results:
                    print(f"✅ [FILTRE] {len(results)} entreprise(s) conservée(s) après filtrage commune")
                else:
                    print(f"⚠️ [FILTRE] Aucune entreprise dans la commune '{commune}' après filtrage")
                
                return results
                
            else:
                print(f"⚠️ [API ENTREPRISE] Erreur HTTP {response.status_code} pour: {adresse_clean[:50]}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"⏱️ [API ENTREPRISE] Timeout pour: {adresse[:50]}")
            return []
        except Exception as e:
            print(f"❌ [API ENTREPRISE] Erreur pour '{adresse[:50]}': {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_enedis_consommation_by_coords(lat, lon, radius_m=500):
        """
        Interroge l'API Enedis Open Data pour récupérer les consommations annuelles
        des entreprises dans une commune donnée
        
        ⚠️ LIMITATION: L'API Enedis n'a pas de coordonnées GPS dans le dataset
        On utilise donc une recherche par commune (code_commune via reverse geocoding)
        
        API: https://opendata.enedis.fr/data-fair/api/v1/datasets/consommation-annuelle-entreprise-par-adresse
        
        Args:
            lat: Latitude du point central
            lon: Longitude du point central  
            radius_m: Rayon de recherche en mètres (ignoré - recherche par commune)
        
        Returns:
            Liste des points de consommation de la commune
        """
        try:
            # ⚠️ Étape 1: Trouver le code INSEE de la commune via reverse geocoding
            geocode_url = "https://api-adresse.data.gouv.fr/reverse/"
            geocode_params = {'lat': lat, 'lon': lon}
            
            print(f"🔌 [ENEDIS API] Étape 1: Reverse geocoding ({lat:.6f}, {lon:.6f})")
            
            geocode_resp = requests.get(geocode_url, params=geocode_params, timeout=10)
            
            if geocode_resp.status_code != 200:
                print(f"⚠️ [ENEDIS API] Échec reverse geocoding HTTP {geocode_resp.status_code}")
                return []
            
            geocode_data = geocode_resp.json()
            if not geocode_data.get('features'):
                print(f"⚠️ [ENEDIS API] Aucune commune trouvée aux coordonnées")
                return []
            
            code_commune = geocode_data['features'][0]['properties'].get('citycode')
            nom_commune = geocode_data['features'][0]['properties'].get('city', '')
            
            if not code_commune:
                print(f"⚠️ [ENEDIS API] Code commune introuvable")
                return []
            
            print(f"✅ [ENEDIS API] Commune trouvée: {nom_commune} ({code_commune})")
            
            # Étape 2: Interroger Enedis avec le code commune
            url = "https://opendata.enedis.fr/data-fair/api/v1/datasets/qjl5f5v2mfxajth6gk2t8u7h/lines"
            
            params = {
                'size': 100,  # Max 100 résultats
                'select': 'adresse,nom_commune,code_commune,code_grand_secteur,consommation_annuelle_totale_de_ladresse_mwh,nombre_de_sites,annee',
                'qs': f'code_commune:{code_commune}',  # Filtre par commune
                'sort': '-consommation_annuelle_totale_de_ladresse_mwh'  # Trier par conso décroissante
            }
            
            print(f"🔌 [ENEDIS API] Étape 2: Requête consommations commune {code_commune}")
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                total = data.get('total', len(results))
                
                if results:
                    print(f"✅ [ENEDIS API] {len(results)}/{total} lignes brutes trouvées dans {nom_commune}")
                    
                    import math
                    
                    # 🔑 ÉTAPE 1: Regrouper par adresse et calculer la MOYENNE des années
                    adresse_groups = {}
                    for point in results:
                        adresse_raw = point.get('adresse', '').strip().upper()
                        if not adresse_raw:
                            continue
                        
                        conso = point.get('consommation_annuelle_totale_de_ladresse_mwh', 0) or 0
                        annee = point.get('annee', 0)
                        
                        if adresse_raw not in adresse_groups:
                            adresse_groups[adresse_raw] = {
                                'adresse_original': point.get('adresse', ''),
                                'commune': point.get('nom_commune', nom_commune),
                                'code_commune': point.get('code_commune', code_commune),
                                'secteur': point.get('code_grand_secteur', ''),
                                'nb_sites': point.get('nombre_de_sites', 0),
                                'consos': [],
                                'annees': []
                            }
                        
                        if conso > 0:
                            adresse_groups[adresse_raw]['consos'].append(conso)
                            if annee:
                                adresse_groups[adresse_raw]['annees'].append(annee)
                    
                    print(f"📊 [ENEDIS API] {len(adresse_groups)} adresses uniques (regroupées depuis {len(results)} lignes)")
                    
                    # 🔑 ÉTAPE 2: Géocoder chaque adresse UNIQUE et calculer la moyenne
                    formatted_results = []
                    geocode_cache = {}  # Cache pour éviter les doublons de géocodage
                    
                    for adresse_key, group in adresse_groups.items():
                        adresse_raw = group['adresse_original']
                        commune_name = group['commune']
                        
                        # Calculer la consommation MOYENNE sur toutes les années
                        consos = group['consos']
                        if not consos:
                            continue
                        conso_moyenne = sum(consos) / len(consos)
                        nb_releves = len(consos)
                        annees = sorted(group['annees']) if group['annees'] else []
                        
                        # Géocoder (avec cache)
                        cache_key = f"{adresse_raw}_{commune_name}"
                        if cache_key in geocode_cache:
                            point_lat, point_lon, distance_m = geocode_cache[cache_key]
                        else:
                            point_lat = None
                            point_lon = None
                            distance_m = 0
                            
                            try:
                                geo_url = "https://api-adresse.data.gouv.fr/search/"
                                geo_params = {
                                    'q': f"{adresse_raw} {commune_name}",
                                    'limit': 1,
                                    'citycode': code_commune
                                }
                                geo_resp = requests.get(geo_url, params=geo_params, timeout=5)
                                if geo_resp.status_code == 200:
                                    geo_data = geo_resp.json()
                                    if geo_data.get('features'):
                                        coords = geo_data['features'][0]['geometry']['coordinates']
                                        point_lon = coords[0]
                                        point_lat = coords[1]
                                        
                                        dlat = math.radians(point_lat - lat)
                                        dlon = math.radians(point_lon - lon)
                                        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(point_lat)) * math.sin(dlon/2)**2
                                        distance_m = 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                            except Exception as e:
                                print(f"⚠️ Géocodage échoué pour '{adresse_raw[:40]}': {e}")
                            
                            geocode_cache[cache_key] = (point_lat, point_lon, distance_m)
                        
                        if point_lat is not None and point_lon is not None:
                            formatted_results.append({
                                'adresse': adresse_raw,
                                'commune': commune_name,
                                'nom_commune': commune_name,
                                'code_commune': group['code_commune'],
                                'secteur': group['secteur'],
                                'consommation_annuelle_mwh': round(conso_moyenne, 2),
                                'nb_sites': group['nb_sites'],
                                'nb_releves': nb_releves,
                                'annees': annees,
                                'pdl': None,
                                'latitude': point_lat,
                                'longitude': point_lon,
                                'distance_m': distance_m,
                                'source': 'enedis-commune'
                            })
                    
                    # Trier par consommation décroissante
                    formatted_results.sort(key=lambda x: x['consommation_annuelle_mwh'], reverse=True)
                    
                    print(f"📍 {len(formatted_results)} points uniques géocodés (moyenne sur {nb_releves} années max)")
                    return formatted_results
                else:
                    print(f"⚠️ [ENEDIS API] Aucune consommation dans commune {nom_commune}")
                    return []
            else:
                print(f"⚠️ [ENEDIS API] Erreur HTTP {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            print(f"⏱️ [ENEDIS API] Timeout")
            return []
        except Exception as e:
            print(f"❌ [ENEDIS API] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @app.route('/crm/autoconso-collective/<int:prospect_id>')
    def autoconso_collective_page(prospect_id):
        """Page d'analyse d'autoconsommation collective pour un prospect"""
        try:
            # Récupérer les infos du prospect
            prospect = execute_query(
                'SELECT * FROM agriweb_prospects WHERE id = %s',
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect:
                return "Prospect non trouvé", 404
            
            # Extraire les données de production PV du calpinage
            pv_production = {
                'puissance_kwc': 0,
                'productible_mwh': 0,
                'nb_zones': 0,
                'has_calpinage': False
            }
            
            try:
                data_json = json.loads(prospect['data_json']) if prospect.get('data_json') else {}
                calpinage = data_json.get('calpinage', {})
                if calpinage and calpinage.get('totaux'):
                    totaux = calpinage['totaux']
                    puissance = float(totaux.get('puissanceTotale', 0))
                    productible = float(totaux.get('productibleTotal', 0))
                    
                    # Si pas de productible PVGIS, estimer par latitude
                    if puissance > 0 and productible <= 0:
                        lat = float(prospect.get('latitude', 46))
                        if lat < 44:
                            ratio = 1350
                        elif lat < 47:
                            ratio = 1150
                        else:
                            ratio = 1000
                        productible = puissance * ratio / 1000  # MWh/an
                    
                    pv_production = {
                        'puissance_kwc': round(puissance, 2),
                        'productible_mwh': round(productible, 2),
                        'nb_zones': len(calpinage.get('zones', [])),
                        'has_calpinage': True
                    }
                    print(f"☀️ [AUTOCONSO] Production PV: {puissance} kWc, {productible} MWh/an")
            except Exception as e:
                print(f"⚠️ [AUTOCONSO] Erreur lecture calpinage: {e}")
            
            return render_template('autoconso_collective.html', prospect=prospect, pv_production=pv_production)
            
        except Exception as e:
            print(f"❌ [AUTOCONSO] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}", 500
    
    @app.route('/api/crm/autoconso-collective/<int:prospect_id>/points-conso')
    def get_autoconso_points(prospect_id):
        """
        Récupère tous les points de consommation Enedis RÉELS dans un rayon donné
        autour du prospect, enrichis avec les données SIRENE
        
        🔌 Utilise l'API officielle Enedis Open Data
        """
        try:
            # Récupérer le rayon demandé (défaut: 1km pour autoconso collective)
            radius_km = float(request.args.get('radius', 1))
            radius_m = int(radius_km * 1000)  # Convertir en mètres pour l'API
            
            # Récupérer les coordonnées du prospect  
            prospect = execute_query(
                'SELECT latitude, longitude, commune FROM agriweb_prospects WHERE id = %s',
                (prospect_id,),
                fetch_one=True
            )
            
            if not prospect:
                return jsonify({'error': 'Prospect non trouvé'}), 404
            
            lat = prospect['latitude']
            lon = prospect['longitude']
            commune_prospect = prospect.get('commune', '')
            
            print(f"\n🔌 [AUTOCONSO COLLECTIVE] Recherche consommateurs autour de ({lat:.6f}, {lon:.6f})")
            print(f"📏 Rayon: {radius_km} km ({radius_m} m)")
            
            # 🆕 UTILISER L'API ENEDIS OFFICIELLE
            enedis_points = get_enedis_consommation_by_coords(lat, lon, radius_m)
            
            if not enedis_points:
                print("⚠️ Aucun point Enedis trouvé, fallback sur ancienne méthode")
                # Fallback sur ancienne méthode si API Enedis ne répond pas
                from agriweb_hebergement_gratuit import get_all_consommation
                radius_deg = radius_km / 111.0
                all_features = get_all_consommation(lat, lon, radius_deg=radius_deg)
                
                if not all_features:
                    return jsonify({
                        'points': [],
                        'total': 0,
                        'radius_km': radius_km,
                        'source': 'fallback-empty'
                    })
                
                # Traiter les features (ancien code)
                points_formatted = []
                for feature in all_features:
                    props = feature.get('properties', {})
                    distance_m = props.get('distance', 0)
                    
                    if distance_m / 1000.0 <= radius_km:
                        points_formatted.append({
                            'latitude': props.get('latitude'),
                            'longitude': props.get('longitude'),
                            'adresse': props.get('adresse', 'N/A'),
                            'commune': props.get('nom_commune', ''),
                            'consommation_annuelle_mwh': props.get('consommation_mwh', 0),
                            'secteur': props.get('secteur', 'NON_AFFECTE'),
                            'distance_km': round(distance_m / 1000.0, 2),
                            'source': 'fallback'
                        })
                
                return jsonify({
                    'points': points_formatted,
                    'total': len(points_formatted),
                    'radius_km': radius_km,
                    'source': 'fallback'
                })
            
            # 🆕 TRAITER LES RÉSULTATS ENEDIS
            points_enrichis = []
            
            for point in enedis_points:
                point_lat = point.get('latitude')
                point_lon = point.get('longitude')
                adresse = point.get('adresse', 'N/A')
                commune = point.get('nom_commune', '')
                conso_mwh = point.get('consommation_annuelle_mwh', 0)
                distance_km = round(point.get('distance_m', 0) / 1000.0, 2)
                
                # Enrichir avec SIRENE (entreprise à cette adresse)
                sirene_data = None
                try:
                    entreprises = get_sirene_by_adresse(adresse, commune=commune)
                    if entreprises and len(entreprises) > 0:
                        ent = entreprises[0]
                        sirene_data = {
                            'siret': ent.get('siret', ''),
                            'denomination': ent.get('denomination', ''),
                            'activite': ent.get('activite', ''),
                            'etat': ent.get('etat', '')
                        }
                except Exception as e:
                    print(f"⚠️ Erreur enrichissement SIRENE: {e}")
                
                points_enrichis.append({
                    'latitude': point_lat,
                    'longitude': point_lon,
                    'adresse': adresse,
                    'commune': commune,
                    'consommation_annuelle_mwh': conso_mwh,
                    'secteur': point.get('secteur', 'NON_AFFECTE'),
                    'nb_sites': point.get('nb_sites', 1),
                    'pdl': point.get('pdl', ''),
                    'distance_km': distance_km,
                    'sirene': sirene_data,
                    'source': 'enedis-api'
                })
            
            print(f"✅ [AUTOCONSO] {len(points_enrichis)} points consommateurs trouvés")
            
            return jsonify({
                'points': points_enrichis,
                'total': len(points_enrichis),
                'radius_km': radius_km,
                'prospect': {
                    'latitude': lat,
                    'longitude': lon
                },
                'source': 'enedis-api'
            })
        
        except Exception as e:
            print(f"❌ [AUTOCONSO API] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ========== API LiDAR 3D pour visualisation bâtiment ==========
    
    @app.route('/api/crm/lidar/3d-data')
    def api_lidar_3d_data_crm():
        """
        Retourne les données 3D complètes pour un point GPS :
        - Terrain heightmap (MNS-MNT via WMS GeoTIFF)
        - Bâtiments BD TOPO (hauteur, altitudes, géométrie)
        - Emprise OSM (footprint polygones)
        """
        import numpy as np
        from PIL import Image as PILImage
        
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', 80, type=int)
        resolution = request.args.get('resolution', 128, type=int)
        
        if not lat or not lon:
            return jsonify({'error': 'lat et lon requis'}), 400
        
        result = {
            'terrain': None,
            'buildings': [],
            'footprints': [],
            'center': {'lat': lat, 'lon': lon},
            'radius_m': radius,
            'resolution': resolution
        }
        
        # ---- 1. Terrain MNS + MNT via WMS-R (GeoTIFF) — TUILAGE HD ----
        try:
            lat_deg = radius / 111320
            lon_deg = radius / (111320 * math.cos(math.radians(lat)))
            
            wms_url = "https://data.geopf.fr/wms-r/wms"
            WMS_MAX = 1024  # limite WMS IGN
            
            # Résolution cible : 0.15m/pixel → ~44 pts/m²
            target_res = 0.15
            zone_m = radius * 2
            total_pixels_needed = int(zone_m / target_res)
            
            nb_tiles = max(1, math.ceil(total_pixels_needed / WMS_MAX))
            tile_pixel_size = min(WMS_MAX, total_pixels_needed)
            tile_zone_m = zone_m / nb_tiles
            actual_res = tile_zone_m / tile_pixel_size
            final_size = tile_pixel_size * nb_tiles
            
            south = lat - lat_deg
            north = lat + lat_deg
            west = lon - lon_deg
            east = lon + lon_deg
            
            lat_step = (north - south) / nb_tiles
            lon_step = (east - west) / nb_tiles
            
            mns_full = np.zeros((final_size, final_size), dtype=np.float32)
            mnt_full = np.zeros((final_size, final_size), dtype=np.float32)
            tiles_ok = 0
            
            print(f"📐 CRM LiDAR Tiling: zone={zone_m}m, tuiles={nb_tiles}×{nb_tiles}, "
                  f"résol={actual_res:.3f}m/px ({1/actual_res**2:.0f} pts/m²)")
            
            for ty in range(nb_tiles):
                for tx in range(nb_tiles):
                    t_south = south + ty * lat_step
                    t_north = south + (ty + 1) * lat_step
                    t_west = west + tx * lon_step
                    t_east = west + (tx + 1) * lon_step
                    t_bbox = f"{t_south},{t_west},{t_north},{t_east}"
                    
                    wms_params = {
                        "SERVICE": "WMS", "VERSION": "1.3.0", "REQUEST": "GetMap",
                        "CRS": "EPSG:4326", "BBOX": t_bbox,
                        "WIDTH": str(tile_pixel_size), "HEIGHT": str(tile_pixel_size),
                        "FORMAT": "image/tiff", "STYLES": ""
                    }
                    
                    try:
                        r_mns = requests.get(wms_url, params={
                            **wms_params,
                            "LAYERS": "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES.MNS"
                        }, timeout=12)
                        
                        r_mnt = requests.get(wms_url, params={
                            **wms_params,
                            "LAYERS": "ELEVATION.ELEVATIONGRIDCOVERAGE.HIGHRES"
                        }, timeout=12)
                        
                        if (r_mns.status_code == 200 and r_mnt.status_code == 200 and
                            r_mns.headers.get('content-type', '').startswith('image')):
                            
                            mns_tile = np.array(PILImage.open(io.BytesIO(r_mns.content)), dtype=np.float32)
                            mnt_tile = np.array(PILImage.open(io.BytesIO(r_mnt.content)), dtype=np.float32)
                            
                            if mns_tile.shape != (tile_pixel_size, tile_pixel_size):
                                mns_tile = np.array(PILImage.fromarray(mns_tile).resize((tile_pixel_size, tile_pixel_size), PILImage.BILINEAR), dtype=np.float32)
                            if mnt_tile.shape != (tile_pixel_size, tile_pixel_size):
                                mnt_tile = np.array(PILImage.fromarray(mnt_tile).resize((tile_pixel_size, tile_pixel_size), PILImage.BILINEAR), dtype=np.float32)
                            
                            py = (nb_tiles - 1 - ty) * tile_pixel_size
                            px = tx * tile_pixel_size
                            mns_full[py:py+tile_pixel_size, px:px+tile_pixel_size] = mns_tile
                            mnt_full[py:py+tile_pixel_size, px:px+tile_pixel_size] = mnt_tile
                            tiles_ok += 1
                    except Exception as te:
                        print(f"  ⚠ CRM Tuile [{ty},{tx}] erreur: {te}")
            
            if tiles_ok > 0:
                mnh_full = mns_full - mnt_full
                
                # Sous-échantillonnage pour le JSON (max 128×128 pour la 3D client)
                json_max = max(64, resolution)
                step = max(1, final_size // json_max)
                mns_small = mns_full[::step, ::step]
                mnt_small = mnt_full[::step, ::step]
                mnh_small = mnh_full[::step, ::step]
                
                result['terrain'] = {
                    'mns': mns_small.tolist(),
                    'mnt': mnt_small.tolist(),
                    'mnh': mnh_small.tolist(),
                    'width': int(mns_small.shape[1]),
                    'height': int(mns_small.shape[0]),
                    'mns_min': float(mns_full.min()),
                    'mns_max': float(mns_full.max()),
                    'mnt_min': float(mnt_full.min()),
                    'mnt_max': float(mnt_full.max()),
                    'mnh_max': float(mnh_full.max()),
                    'full_resolution': final_size,
                    'resolution_m_per_px': round(actual_res, 3),
                    'pts_per_m2': round(1 / actual_res**2, 1),
                    'tiles_used': f"{nb_tiles}x{nb_tiles} ({tiles_ok}/{nb_tiles**2} OK)",
                    'bbox': {
                        'south': south,
                        'north': north,
                        'west': west,
                        'east': east
                    }
                }
                print(f"  ✓ LiDAR terrain HD: {mns_small.shape}, "
                      f"MNS={float(mns_full.min()):.1f}-{float(mns_full.max()):.1f}m, "
                      f"{tiles_ok} tuiles, {1/actual_res**2:.0f} pts/m²")
            else:
                print(f"  ⚠ CRM LiDAR: aucune tuile récupérée")
        except Exception as e:
            print(f"  ⚠ LiDAR terrain: {e}")
        
        # ---- 2. BD TOPO bâtiments via WFS (Lambert-93) ----
        try:
            from pyproj import Transformer
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
            x_l93, y_l93 = transformer.transform(lon, lat)
            
            url_wfs = "https://data.geopf.fr/wfs/ows"
            params_wfs = {
                "service": "WFS", "version": "2.0.0",
                "request": "GetFeature",
                "typeName": "BDTOPO_V3:batiment",
                "outputFormat": "application/json",
                "bbox": f"{x_l93 - radius},{y_l93 - radius},{x_l93 + radius},{y_l93 + radius},EPSG:2154",
                "srsName": "EPSG:4326",
                "count": "100"
            }
            r_wfs = requests.get(url_wfs, params=params_wfs, timeout=15)
            if r_wfs.status_code == 200:
                data_wfs = r_wfs.json()
                features = data_wfs.get("features", [])
                for feat in features:
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    gtype = geom.get("type", "")
                    
                    if gtype == "MultiPolygon":
                        coords = geom["coordinates"][0][0]
                    elif gtype == "Polygon":
                        coords = geom["coordinates"][0]
                    else:
                        continue
                    
                    result['buildings'].append({
                        'coordinates': coords,
                        'hauteur': float(props.get('hauteur', 0) or 0),
                        'altitude_sol_min': float(props.get('altitude_minimale_sol', 0) or 0),
                        'altitude_sol_max': float(props.get('altitude_maximale_sol', 0) or 0),
                        'altitude_toit_min': float(props.get('altitude_minimale_toit', 0) or 0),
                        'altitude_toit_max': float(props.get('altitude_maximale_toit', 0) or 0),
                        'nb_etages': int(props.get('nombre_d_etages', 0) or 0),
                        'usage': props.get('usage_1', ''),
                        'nature': props.get('nature', ''),
                        'materiaux_toit': props.get('materiaux_de_la_toiture', ''),
                        'materiaux_murs': props.get('materiaux_des_murs', '')
                    })
                print(f"  ✓ BD TOPO: {len(result['buildings'])} bâtiments")
        except Exception as e:
            print(f"  ⚠ BD TOPO: {e}")
        
        # ---- 3. OSM footprints via Overpass ----
        try:
            overpass_query = f"""
            [out:json][timeout:10];
            (way["building"](around:{radius},{lat},{lon}););
            out geom tags;
            """
            r_osm = requests.post("https://overpass-api.de/api/interpreter",
                                 data=overpass_query, timeout=15)
            if r_osm.status_code == 200:
                data_osm = r_osm.json()
                for elem in data_osm.get("elements", []):
                    geom_pts = elem.get("geometry", [])
                    tags = elem.get("tags", {})
                    if geom_pts:
                        result['footprints'].append({
                            'points': [{'lat': p['lat'], 'lon': p['lon']} for p in geom_pts],
                            'tags': tags
                        })
                print(f"  ✓ OSM: {len(result['footprints'])} emprises")
        except Exception as e:
            print(f"  ⚠ OSM: {e}")
        
        return jsonify(result)

    # ============================================================================
    # ROUTES - RECHERCHE PROPRIÉTAIRE PAR SIREN (MAJIC)
    # ============================================================================

    @app.route('/api/crm/proprietaire/search-by-name')
    def search_proprietaire_by_name():
        """Recherche des propriétaires dans la base MAJIC par nom (ILIKE)"""
        from proprietaires_utils import search_proprietaires_by_name

        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401

        q = request.args.get('q', '').strip()
        if not q or len(q) < 2:
            return jsonify({'success': False, 'error': 'Requête trop courte'}), 400

        results = search_proprietaires_by_name(q)
        return jsonify({'success': True, 'query': q, 'results': results})

    @app.route('/api/crm/proprietaire/search')
    def search_proprietaire_parcelles():
        """Recherche toutes les parcelles d'un propriétaire par SIREN sur toute la France (base MAJIC)"""
        import re as _re
        import requests as _req
        from proprietaires_utils import get_parcelles_by_siren

        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401

        siren = request.args.get('siren', '').strip()
        denomination_param = request.args.get('denomination', '').strip()
        if not siren and not denomination_param:
            return jsonify({'success': False, 'error': 'SIREN ou denomination requis'}), 400
        # Accepter les identifiants MAJIC alphanumériques (ex: U13516091 pour entités publiques)
        # Seule contrainte : pas vide et pas trop long
        if siren and len(siren) > 20:
            return jsonify({'success': False, 'error': 'Identifiant invalide'}), 400
        # Si pas de siren valide mais une denomination → recherche par nom directement
        if not siren and denomination_param:
            from proprietaires_utils import search_proprietaires_by_name
            results = search_proprietaires_by_name(denomination_param)
            return jsonify({'success': True, 'results': results, 'redirect_to_name_search': True})

        parcelles = get_parcelles_by_siren(siren, limit=500)
        if not parcelles:
            # Fallback : essayer de trouver ce propriétaire par son nom dans MAJIC
            # (SIRENE et MAJIC peuvent avoir des SIRENs légèrement différents pour le même groupe)
            from proprietaires_utils import search_proprietaires_by_name
            import requests as _req2
            denomination_hint = ''
            try:
                r2 = _req.get(
                    'https://recherche-entreprises.api.gouv.fr/search',
                    params={'q': siren, 'page': 1, 'per_page': 1},
                    timeout=4
                )
                if r2.ok:
                    results2 = r2.json().get('results', [])
                    if results2:
                        denomination_hint = results2[0].get('nom_complet', '')
            except Exception:
                pass
            return jsonify({
                'success': True,
                'siren': siren,
                'denomination': denomination_hint,
                'total_parcelles': 0,
                'communes': [],
                'not_in_majic': True,
                'denomination_hint': denomination_hint
            })

        denomination = parcelles[0].get('denomination', '')
        forme_juridique = parcelles[0].get('forme_juridique', '')

        # Grouper par code_insee
        communes_map = {}
        for p in parcelles:
            ci = p['code_insee']
            if ci not in communes_map:
                communes_map[ci] = {
                    'code_insee': ci,
                    'commune_nom': ci,
                    'departement': '',
                    'parcelles': [],
                    'surface_totale_m2': 0,
                    'nb_parcelles': 0,
                    'surface_ha': 0.0
                }
            communes_map[ci]['parcelles'].append({
                'section': p['section'],
                'numero': p['numero'],
                'contenance': p['contenance'] or 0
            })
            communes_map[ci]['surface_totale_m2'] += (p['contenance'] or 0)
            communes_map[ci]['nb_parcelles'] += 1

        # Enrichir les communes via geo.api.gouv.fr
        for c in communes_map.values():
            c['surface_ha'] = round(c['surface_totale_m2'] / 10000, 2)
            try:
                r = _req.get(
                    f"https://geo.api.gouv.fr/communes/{c['code_insee']}",
                    params={'fields': 'nom,departement'},
                    timeout=4
                )
                if r.ok:
                    geo = r.json()
                    c['commune_nom'] = geo.get('nom', c['code_insee'])
                    c['departement'] = geo.get('departement', {}).get('nom', '')
            except Exception:
                pass

        result_list = sorted(communes_map.values(), key=lambda x: x['surface_totale_m2'], reverse=True)

        total_surface_ha = round(sum(c.get('surface_totale_m2', 0) for c in result_list) / 10000, 2)

        return jsonify({
            'success': True,
            'siren': siren,
            'denomination': denomination,
            'forme_juridique': forme_juridique,
            'total_parcelles': len(parcelles),
            'total_communes': len(result_list),
            'total_surface_ha': total_surface_ha,
            'communes': result_list
        })

    @app.route('/api/crm/proprietaire/import-parcelles', methods=['POST'])
    def import_proprietaire_parcelles():
        """Importe des communes/parcelles d'un propriétaire MAJIC dans le CRM comme prospects"""
        import requests as _req

        user_id, is_admin = get_current_crm_user()
        if user_id is None:
            return jsonify({'success': False, 'error': 'Authentification requise'}), 401

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'JSON requis'}), 400

        siren = data.get('siren', '').strip()
        denomination = data.get('denomination', '')
        forme_juridique = data.get('forme_juridique', '')
        selected_communes = data.get('communes', [])

        if not siren or not selected_communes:
            return jsonify({'success': False, 'error': 'SIREN et communes requis'}), 400

        imported = 0
        errors = []

        for commune_data in selected_communes:
            code_insee = commune_data.get('code_insee', '')
            commune_nom = commune_data.get('commune_nom', code_insee)
            departement = commune_data.get('departement', '')
            parcelles = commune_data.get('parcelles', [])
            surface_m2 = commune_data.get('surface_totale_m2', 0)

            # Géocodage : centroïde des parcelles via apicarto IGN (plusieurs stratégies)
            lat, lon = None, None

            # Stratégie 1 : apicarto par section+numero en essayant différents formats
            for p in parcelles[:10]:
                if lat is not None:
                    break
                try:
                    section = (p.get('section') or '').strip().upper()
                    numero_raw = (p.get('numero') or '').strip()
                    # Essayer les deux formats : avec et sans zero-padding
                    numero_padded = numero_raw.zfill(4)
                    for num_try in [numero_padded, numero_raw, numero_raw.lstrip('0') or '0']:
                        r = _req.get(
                            'https://apicarto.ign.fr/api/cadastre/parcelle',
                            params={'code_insee': code_insee, 'section': section, 'numero': num_try},
                            timeout=6
                        )
                        if r.ok:
                            features = r.json().get('features', [])
                            if features:
                                geom = features[0].get('geometry', {})
                                coords = None
                                if geom.get('type') == 'MultiPolygon':
                                    coords = geom['coordinates'][0][0]
                                elif geom.get('type') == 'Polygon':
                                    coords = geom['coordinates'][0]
                                if coords:
                                    lon = sum(c[0] for c in coords) / len(coords)
                                    lat = sum(c[1] for c in coords) / len(coords)
                                    break
                    if lat is not None:
                        break
                except Exception as e:
                    print(f"⚠️ Géocodage stratégie 1 {code_insee}/{section}: {e}")

            # Stratégie 2 : apicarto par section uniquement (prend la 1ère parcelle de la section)
            if lat is None and parcelles:
                try:
                    section = (parcelles[0].get('section') or '').strip().upper()
                    r2 = _req.get(
                        'https://apicarto.ign.fr/api/cadastre/parcelle',
                        params={'code_insee': code_insee, 'section': section, '_limit': 1},
                        timeout=8
                    )
                    if r2.ok:
                        features2 = r2.json().get('features', [])
                        if features2:
                            geom2 = features2[0].get('geometry', {})
                            coords2 = None
                            if geom2.get('type') == 'MultiPolygon':
                                coords2 = geom2['coordinates'][0][0]
                            elif geom2.get('type') == 'Polygon':
                                coords2 = geom2['coordinates'][0]
                            if coords2:
                                lon = sum(c[0] for c in coords2) / len(coords2)
                                lat = sum(c[1] for c in coords2) / len(coords2)
                except Exception as e2:
                    print(f"⚠️ Géocodage stratégie 2 {code_insee}: {e2}")

            # Stratégie 3 : centroïde de la commune via geo.api.gouv.fr
            if lat is None and code_insee:
                try:
                    r3 = _req.get(
                        f'https://geo.api.gouv.fr/communes/{code_insee}',
                        params={'fields': 'centre'},
                        timeout=5
                    )
                    if r3.ok:
                        centre = r3.json().get('centre', {})
                        if centre.get('coordinates'):
                            lon = centre['coordinates'][0]
                            lat = centre['coordinates'][1]
                except Exception as e3:
                    print(f"⚠️ Géocodage stratégie 3 (commune) {code_insee}: {e3}")

            parcelles_str = ', '.join([
                f"{(p.get('section') or '').strip()}{(p.get('numero') or '').strip()}"
                for p in parcelles
            ])

            data_json_blob = {
                'proprietaire_siren': siren,
                'proprietaire_denomination': denomination,
                'proprietaire_forme_juridique': forme_juridique,
                'source': 'majic_import',
                'code_insee': code_insee
            }

            try:
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse,
                        latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        proprietaire_siren, proprietaire_denomination, proprietaire_forme_juridique,
                        data_json, user_id, statut, priorite
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'toiture',
                    commune_nom,
                    departement,
                    f"{commune_nom} ({code_insee})",
                    lat, lon,
                    surface_m2,
                    round(surface_m2 / 10000, 4) if surface_m2 else None,
                    parcelles_str,
                    siren, denomination, forme_juridique,
                    json.dumps(data_json_blob),
                    str(user_id) if user_id is not None else None,
                    'nouveau', 'moyenne'
                ), fetch_one=True)

                if result and result.get('id'):
                    imported += 1
            except Exception as e:
                errors.append(f"{commune_nom}: {str(e)}")
                print(f"❌ Import parcelle {code_insee}: {e}")

        return jsonify({
            'success': True,
            'imported': imported,
            'errors': errors,
            'message': f'{imported} commune(s) importée(s) dans le CRM'
        })

    @app.route('/api/crm/prospects/<int:prospect_id>/repair-majic-parcelles', methods=['POST'])
    def repair_majic_parcelles(prospect_id):
        """Répare le champ parcelles_cadastrales tronqué en relisant depuis proprietaires_parcelles"""
        try:
            user_id, is_admin = get_current_crm_user()
            if user_id is None:
                return jsonify({'success': False, 'error': 'Authentification requise'}), 401
            if not verify_prospect_ownership(prospect_id, user_id, is_admin):
                return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

            prospect = execute_query(
                'SELECT data_json, parcelles_cadastrales FROM agriweb_prospects WHERE id = %s',
                (prospect_id,), fetch_one=True
            )
            if not prospect:
                return jsonify({'success': False, 'error': 'Prospect non trouvé'}), 404

            dj = prospect.get('data_json') or {}
            if isinstance(dj, str):
                try: dj = json.loads(dj)
                except: dj = {}

            siren = dj.get('proprietaire_siren', '')
            code_insee = dj.get('code_insee', '')
            if not siren or not code_insee:
                return jsonify({'success': False, 'error': 'Pas de SIREN ou code_insee dans data_json'}), 400

            from proprietaires_utils import get_parcelles_by_siren
            parcelles = get_parcelles_by_siren(siren, limit=5000) or []
            # Filtrer sur ce code_insee
            parcelles_commune = [p for p in parcelles if str(p.get('code_insee', '')) == str(code_insee)]
            if not parcelles_commune:
                return jsonify({'success': False, 'error': f'Aucune parcelle MAJIC pour SIREN={siren} code_insee={code_insee}'}), 404

            parcelles_str = ', '.join([
                f"{(p.get('section') or '').strip()}{(p.get('numero') or '').strip()}"
                for p in parcelles_commune
            ])
            execute_query(
                'UPDATE agriweb_prospects SET parcelles_cadastrales = %s WHERE id = %s',
                (parcelles_str, prospect_id)
            )
            print(f"✅ [REPAIR MAJIC] prospect {prospect_id}: {len(parcelles_commune)} parcelles restaurées")
            return jsonify({
                'success': True,
                'nb_parcelles': len(parcelles_commune),
                'message': f'{len(parcelles_commune)} parcelles restaurées depuis MAJIC'
            })
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
