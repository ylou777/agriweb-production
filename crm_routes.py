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
            return result[0], bool(result[1])
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
            
            # Créer les 11 étapes du workflow
            # L'étape 1 (Rapport) est marquée comme terminée car l'export provient d'un rapport
            etapes_autoconso = [
                ('Rapport de recherche HeliaPV', 1),
                ('Visite technique', 2),
                ('Calepinage', 3),
                ('Étude d\'autoconsommation', 4),
                ('Devis commercial', 5),
                ('Signature & Facture', 6),
                ('Déclaration Préalable de Travaux (DP)', 7),
                ('Déclaration de Raccordement (DDR)', 8),
                ('Installation & DOE', 9),
                ('Consuel', 10),
                ('Mise en service & Maintenance', 11)
            ]
            
            for nom_etape, ordre in etapes_autoconso:
                statut = 'termine' if ordre == 1 else 'a_faire'
                execute_query('''
                    INSERT INTO project_etapes (
                        project_id, nom_etape, ordre, statut,
                        date_debut_prevue, date_fin_prevue
                    ) VALUES (%s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days')
                ''', (project_id, nom_etape, ordre, statut))
            
            print(f"✅ [AUTO PROJECT] 11 étapes créées pour projet {project_id} (étape 1 Rapport = terminée)")
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

# ============================================================================
# ROUTES PAGES - INTERFACE CRM
# ============================================================================

def register_crm_routes(app):
    """Enregistre toutes les routes CRM dans l'application Flask"""
    
    @app.route('/crm')
    def crm_dashboard():
        """Page de lancement du CRM HeliaPV - Version web"""
        user_id, is_admin = get_current_crm_user()
        return render_template('crm_web.html', is_admin=is_admin)

    @app.route('/crm/stats')
    def crm_stats_page():
        """Page de statistiques et KPI du CRM - Admin seulement"""
        user_id, is_admin = get_current_crm_user()
        if not is_admin:
            return redirect('/crm')
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
        """Statistiques CRM pour la page d'accueil - Admin seulement"""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Accès réservé aux administrateurs'}), 403
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
                    COUNT(CASE WHEN type = 'parcelle_rpg' THEN 1 END) as rpg
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)
            
            if not stats:
                return jsonify({
                    'success': True,
                    'stats': {'total': 0, 'nouveau': 0, 'contacte': 0, 'qualifie': 0, 'perdu': 0, 'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0}
                })
            
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

    @app.route('/api/crm/dashboard/stats')
    def get_dashboard_stats():
        """Récupère toutes les statistiques pour le dashboard CRM KPI - Admin seulement"""
        try:
            user_id, is_admin = get_current_crm_user()
            if not is_admin:
                return jsonify({'success': False, 'error': 'Accès réservé aux administrateurs'}), 403
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
            
            # Propositions
            proposals = execute_query('''
                SELECT 
                    COUNT(*) as nb_proposals,
                    COALESCE(SUM(CAST(investissement_total AS NUMERIC)), 0) as total_value
                FROM prospect_proposals
            ''', fetch_one=True) or {'nb_proposals': 0, 'total_value': 0}
            
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
            ''', filter_params if filter_params else None)
            by_type = {row['type']: row['count'] for row in by_type_rows}
            
            # Par statut
            by_statut_rows = execute_query(f'''
                SELECT statut, COUNT(*) as count
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
                GROUP BY statut
            ''', filter_params if filter_params else None)
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
            ''', filter_params if filter_params else None)
            
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
            ''', filter_params if filter_params else None)
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
            ''', filter_params if filter_params else None)
            
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
                
                total_exported += 1
                details['rpg'] += 1
            
            print(f"✅ [CRM EXPORT] Export réussi: {total_exported} prospects ajoutés")
            
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
            
            # Mapper contact_telephone -> contact_tel pour compatibilité frontend
            if prospects:
                for prospect in prospects:
                    if 'contact_telephone' in prospect:
                        prospect['contact_tel'] = prospect['contact_telephone']
            
            # Calculer les stats
            stats = execute_query(f'''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN type = 'parking' THEN 1 END) as parkings,
                    COUNT(CASE WHEN type = 'toiture' THEN 1 END) as toitures,
                    COUNT(CASE WHEN type = 'friche' THEN 1 END) as friches,
                    COUNT(CASE WHEN type = 'parcelle_rpg' THEN 1 END) as rpg
                FROM agriweb_prospects
                WHERE 1=1{filter_clause}
            ''', filter_params if filter_params else None, fetch_one=True)
            
            return jsonify({
                'success': True,
                'prospects': prospects if prospects else [],
                'stats': stats if stats else {'total': 0, 'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0}
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
            
            if 'parcelle_cadastrale' in data:
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
                            ('Étude d\'autoconsommation', 4),
                            ('Devis commercial', 5),
                            ('Signature & Facture', 6),
                            ('Déclaration Préalable de Travaux (DP)', 7),
                            ('Déclaration de Raccordement (DDR)', 8),
                            ('Installation & DOE', 9),
                            ('Consuel', 10),
                            ('Mise en service & Maintenance', 11)
                        ]
                        
                        for etape_nom, ordre in etapes_autoconso:
                            # La première étape (rapport) est déjà terminée
                            statut = 'termine' if ordre == 1 else 'a_faire'
                            date_fin = 'CURRENT_DATE' if ordre == 1 else 'NULL'
                            execute_query(f'''
                                INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                                VALUES (%s, %s, %s, %s, {date_fin})
                            ''', (project_id, etape_nom, ordre, statut))
                        
                        print(f"✅ [ETAPES CREATE] 11 étapes créées pour projet {project_id}, étape 1 terminée")
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
    def create_prospect_appointment(prospect_id):
        """Crée un rendez-vous pour un prospect"""
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            rdv_datetime = f"{data['date']} {data['time']}"
            
            # Créer le rendez-vous
            execute_query('''
                INSERT INTO crm_appointments (
                    prospect_id, date_rdv, type_rdv, notes, date_creation
                ) VALUES (%s, %s, %s, %s, %s)
            ''', (
                prospect_id,
                rdv_datetime,
                data.get('type', 'visite'),
                data.get('notes', ''),
                datetime.now().isoformat()
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
                ORDER BY ca.date_rdv ASC
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
                ('Étude d\'autoconsommation', 4),
                ('Devis commercial', 5),
                ('Signature & Facture', 6),
                ('Déclaration Préalable de Travaux (DP)', 7),
                ('Déclaration de Raccordement (DDR)', 8),
                ('Installation & DOE', 9),
                ('Consuel', 10),
                ('Mise en service & Maintenance', 11)
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
                    'tariff_type'    : tariff_type,
                    'tariff_label'   : TARIFF_LABELS.get(tariff_type, tariff_type),
                    'date_calcul'    : datetime.now().isoformat(),
                }
                execute_query(
                    "UPDATE agriweb_prospects SET data_json = %s WHERE id = %s",
                    (json.dumps(_dj), prospect_id)
                )
                print(f"[AUTOCONSO] Résultats sauvegardés en BDD (prospect {prospect_id})")
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
                        ('Étude d\'autoconsommation', 4),
                        ('Devis commercial', 5),
                        ('Signature & Facture', 6),
                        ('Déclaration Préalable de Travaux (DP)', 7),
                        ('Déclaration de Raccordement (DDR)', 8),
                        ('Installation & DOE', 9),
                        ('Consuel', 10),
                        ('Mise en service & Maintenance', 11)
                    ]
                    
                    for etape_nom, ordre in etapes_autoconso:
                        # L'étape visite technique (2) est terminée
                        statut = 'termine' if ordre == 2 else 'a_faire'
                        date_fin = 'CURRENT_DATE' if ordre == 2 else 'NULL'
                        execute_query(f'''
                            INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                            VALUES (%s, %s, %s, %s, {date_fin})
                        ''', (project_id, etape_nom, ordre, statut))
                    
                    print(f"✅ [ETAPES CREATE] 11 étapes créées, étape 2 (Visite technique) terminée")
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
            
            _, is_admin = get_current_crm_user()
            return render_template('calpinage_pv.html', prospect=prospect_dict, is_admin=is_admin)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}", 500
    
    @app.route('/api/crm/prospects/<int:prospect_id>/calpinage', methods=['POST'])
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
                            ('Étude d\'autoconsommation', 4),
                            ('Devis commercial', 5),
                            ('Signature & Facture', 6),
                            ('Déclaration Préalable de Travaux (DP)', 7),
                            ('Déclaration de Raccordement (DDR)', 8),
                            ('Installation & DOE', 9),
                            ('Consuel', 10),
                            ('Mise en service & Maintenance', 11)
                        ]
                        
                        for etape_nom, ordre in etapes_autoconso:
                            statut = 'termine' if ordre == 3 else 'a_faire'
                            execute_query('''
                                INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                                VALUES (%s, %s, %s, %s, {})
                            '''.format('CURRENT_DATE' if ordre == 3 else 'NULL'),
                            (project_id_fiche, etape_nom, ordre, statut))
                        
                        print(f"✅ [ETAPES CREATE] 11 étapes créées pour projet {project_id_fiche}")
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
                    
                    # Marquer l'étape Calepinage (ordre 3) comme terminée
                    execute_query('''
                        UPDATE project_etapes 
                        SET statut = 'termine', 
                            date_fin_reelle = CURRENT_DATE
                        WHERE project_id = %s 
                        AND ordre = 3
                        AND statut != 'termine'
                    ''', (project['id'],))
                    
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
            
            # Marquer l'étape "Étude d'autoconsommation" (ordre 4) comme terminée si un projet existe
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
                    AND ordre = 4
                    AND statut != 'termine'
                ''', (project['id'],))
                print(f"✅ [ETAPE UPDATE] Étape 4 (Étude d'autoconsommation) marquée comme terminée pour projet {project['id']}")
            
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
    # PROPOSITION COMMERCIALE PROFESSIONNELLE
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
                    or eco_saved.get('tarif_revente'), 0.13),
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
            
            # Enrichir prospect avec rapport_commune pour contraintes urbanisme
            if rapport_commune:
                prospect['data_json'] = data_json

            # Injecter screenshot_3d depuis la requête (priorité) ou depuis la DB
            screenshot_3d_req = data.get('screenshot_3d', '')
            screenshot_3d_db  = calpinage.get('screenshot_3d', '')
            calpinage['screenshot_3d'] = screenshot_3d_req or screenshot_3d_db
            
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
            
            # Marquer l'étape "Devis commercial" (ordre 5) comme terminée
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
                print(f"✅ [ETAPE UPDATE] Étape 5 (Devis commercial) marquée comme terminée pour projet {project['id']}")
            
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
    
    @app.route('/api/crm/parametrage/entreprise', methods=['GET', 'POST'])
    def parametrage_entreprise():
        """GET: Charger les infos entreprise, POST: Sauvegarder"""
        try:
            if request.method == 'GET':
                # Charger les données
                result = execute_query(
                    'SELECT * FROM parametrage_entreprise WHERE actif = TRUE ORDER BY id DESC LIMIT 1',
                    fetch_one=True
                )
                
                return jsonify({
                    'success': True,
                    'entreprise': dict(result) if result else None
                })
            
            else:  # POST
                data = request.json
                
                # Convertir les dates vides en None (PostgreSQL n'accepte pas '' pour DATE)
                for date_field in ('rge_date_validite', 'qualibat_date_validite'):
                    if date_field in data and not data[date_field]:
                        data[date_field] = None
                
                # Vérifier si une entreprise existe déjà
                existing = execute_query(
                    'SELECT id FROM parametrage_entreprise WHERE actif = TRUE LIMIT 1',
                    fetch_one=True
                )
                
                if existing:
                    # UPDATE
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
                    # INSERT
                    execute_query("""
                        INSERT INTO parametrage_entreprise (
                            nom_entreprise, adresse, code_postal, ville, telephone, email, site_web,
                            siret, tva_intracommunautaire, rge_numero, rge_date_validite,
                            qualibat_numero, qualibat_date_validite, qualifelec_numero, logo_base64
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                        data.get('logo_base64')
                    ))
                
                print("✅ Paramétrage entreprise sauvegardé")
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
        """GET: Charger les couleurs, POST: Sauvegarder"""
        try:
            if request.method == 'GET':
                result = execute_query(
                    'SELECT couleur_primaire, couleur_secondaire, couleur_accent FROM parametrage_entreprise WHERE actif = TRUE LIMIT 1',
                    fetch_one=True
                )
                
                return jsonify({
                    'success': True,
                    'graphique': dict(result) if result else None
                })
            
            else:  # POST
                data = request.json
                
                execute_query("""
                    UPDATE parametrage_entreprise SET
                        couleur_primaire = %s,
                        couleur_secondaire = %s,
                        couleur_accent = %s,
                        date_modification = CURRENT_TIMESTAMP
                    WHERE actif = TRUE
                """, (
                    data.get('couleur_primaire'),
                    data.get('couleur_secondaire'),
                    data.get('couleur_accent')
                ))
                
                print("✅ Couleurs sauvegardées")
                return jsonify({'success': True})
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ============================================================================
    # ROUTES GÉNÉRATION DOCUMENTS - DÉCLARATION PRÉALABLE
    # ============================================================================
    
    @app.route('/api/crm/prospect/<int:prospect_id>/generer-dp', methods=['POST'])
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
