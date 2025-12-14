"""
Routes CRM pour AgriWeb - Adaptées pour Railway avec PostgreSQL
Toutes les connexions SQLite ont été converties pour utiliser database_adapter
"""

from flask import render_template, jsonify, request, send_file
from datetime import datetime
from database_adapter import execute_query, get_db_connection
import json
import os

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def auto_create_project_for_prospect(prospect_id, commune=None, adresse=None):
    """
    Crée automatiquement une fiche projet et ses étapes pour un nouveau prospect
    Cette fonction est appelée automatiquement à chaque création de prospect
    """
    try:
        print(f"🆕 [AUTO PROJECT] Création automatique du projet pour prospect {prospect_id}")
        
        # Créer la fiche projet
        result = execute_query('''
            INSERT INTO project_fiches (
                prospect_id, nom_projet, commune, adresse_projet, 
                statut_projet, data_json
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        ''', (
            prospect_id,
            f"Projet {commune or adresse or prospect_id}",
            commune,
            adresse,
            'etude',
            '{}'
        ), fetch_one=True)
        
        if result:
            project_id = result['id']
            print(f"✅ [AUTO PROJECT] Fiche projet {project_id} créée")
            
            # Créer les 11 étapes du workflow
            etapes_autoconso = [
                ('Rapport de recherche AgriWeb', 1),
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
                execute_query('''
                    INSERT INTO project_etapes (
                        project_id, nom_etape, ordre, statut,
                        date_debut_prevue, date_fin_prevue
                    ) VALUES (%s, %s, %s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days')
                ''', (project_id, nom_etape, ordre, 'a_faire'))
            
            print(f"✅ [AUTO PROJECT] 11 étapes créées pour projet {project_id}")
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
        """Page de lancement du CRM AgriWeb - Version web"""
        return render_template('crm_web.html')

    @app.route('/crm/stats')
    def crm_stats_page():
        """Page de statistiques et KPI du CRM"""
        return render_template('crm_dashboard.html')

    @app.route('/crm/desktop')
    def crm_desktop():
        """Page de lancement du CRM AgriWeb - Version desktop (Tkinter)"""
        return render_template('crm_redirect.html')

    @app.route('/crm/projets')
    def crm_projets():
        """Interface de gestion des fiches projets"""
        return render_template('crm_projets.html')

    @app.route('/crm/calendrier')
    def crm_calendrier():
        """Interface calendrier des rendez-vous"""
        return render_template('crm_calendrier.html')

    # ============================================================================
    # ROUTES API - STATISTIQUES
    # ============================================================================

    @app.route('/api/crm/stats')
    def crm_stats():
        """Statistiques CRM pour la page d'accueil"""
        try:
            stats = execute_query('''
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
            ''', fetch_one=True)
            
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
        """Récupère toutes les statistiques pour le dashboard CRM KPI"""
        try:
            print("\n" + "="*70)
            print("🔄 [DASHBOARD KPI] Récupération des statistiques...")
            
            # === KPIs GÉNÉRAUX ===
            kpis = execute_query('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'nouveau' THEN 1 END) as nouveaux,
                    COUNT(CASE WHEN statut = 'contacte' THEN 1 END) as contactes,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies,
                    COUNT(CASE WHEN statut = 'perdu' THEN 1 END) as perdus,
                    COUNT(CASE WHEN date_creation >= NOW() - INTERVAL '30 days' THEN 1 END) as nouveaux_mois
                FROM agriweb_prospects
            ''', fetch_one=True)
            
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
            by_type_rows = execute_query('''
                SELECT type, COUNT(*) as count
                FROM agriweb_prospects
                GROUP BY type
            ''')
            by_type = {row['type']: row['count'] for row in by_type_rows}
            
            # Par statut
            by_statut_rows = execute_query('''
                SELECT statut, COUNT(*) as count
                FROM agriweb_prospects
                GROUP BY statut
            ''')
            by_statut = {row['statut']: row['count'] for row in by_statut_rows}
            
            # Timeline (30 derniers jours)
            timeline_data = execute_query('''
                SELECT 
                    DATE(date_creation) as date,
                    COUNT(*) as count,
                    statut
                FROM agriweb_prospects
                WHERE date_creation >= NOW() - INTERVAL '30 days'
                GROUP BY DATE(date_creation), statut
                ORDER BY date
            ''')
            
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
            avg_contact_row = execute_query('''
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (date_modification - date_creation))/86400) as avg_delay
                FROM agriweb_prospects
                WHERE statut != 'nouveau'
            ''', fetch_one=True)
            avg_contact = avg_contact_row['avg_delay'] or 0 if avg_contact_row else 0
            
            avg_qualification_row = execute_query('''
                SELECT 
                    AVG(EXTRACT(EPOCH FROM (date_modification - date_creation))/86400) as avg_delay
                FROM agriweb_prospects
                WHERE statut = 'qualifie'
            ''', fetch_one=True)
            avg_qualification = avg_qualification_row['avg_delay'] or 0 if avg_qualification_row else 0
            
            # Conversion par type
            conversion_type_rows = execute_query('''
                SELECT 
                    type,
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies
                FROM agriweb_prospects
                GROUP BY type
            ''')
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
            departments_data = execute_query('''
                SELECT 
                    departement,
                    COUNT(*) as total,
                    COUNT(CASE WHEN statut = 'qualifie' THEN 1 END) as qualifies
                FROM agriweb_prospects
                WHERE departement IS NOT NULL
                GROUP BY departement
                ORDER BY total DESC
                LIMIT 10
            ''')
            
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
        """Lance l'application CRM AgriWeb (désactivé sur Railway)"""
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
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'parking', parking.get('commune'), parking.get('departement'), parking.get('adresse'),
                    clean_value(parking.get('lat')), clean_value(parking.get('lon')), clean_value(parking.get('surface_m2')),
                    clean_value(parking.get('surface_m2', 0)) / 10000 if clean_value(parking.get('surface_m2')) else None,
                    json.dumps(parking.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    parking.get('lien_streetview'), parking.get('lien_annuaire'), json.dumps(parking),
                    parking.get('amenity'), parking.get('shop'), parking.get('building'),
                    parking.get('landuse'), parking.get('office'), parking.get('industrial')
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], parking.get('commune'), parking.get('adresse'))
                
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
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'toiture', toiture.get('commune'), toiture.get('departement'), toiture.get('adresse'),
                    clean_value(toiture.get('lat')), clean_value(toiture.get('lon')), clean_value(toiture.get('surface_m2')),
                    clean_value(toiture.get('surface_m2', 0)) / 10000 if clean_value(toiture.get('surface_m2')) else None,
                    json.dumps(toiture.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    toiture.get('lien_streetview'), toiture.get('lien_annuaire'), json.dumps(toiture),
                    toiture.get('amenity'), toiture.get('shop'), toiture.get('building'),
                    toiture.get('landuse'), toiture.get('office'), toiture.get('industrial')
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], toiture.get('commune'), toiture.get('adresse'))
                
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
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json,
                        osm_amenity, osm_shop, osm_building, osm_landuse, osm_office, osm_industrial
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'friche', friche.get('commune'), friche.get('departement'), friche.get('adresse'),
                    clean_value(friche.get('lat')), clean_value(friche.get('lon')), clean_value(friche.get('surface_m2')),
                    clean_value(friche.get('surface_m2', 0)) / 10000 if clean_value(friche.get('surface_m2')) else None,
                    json.dumps(friche.get('parcelles', [])),
                    clean_value(poste_bt.get('distance_m')), poste_bt.get('nom') or poste_bt.get('id'), clean_value(poste_bt.get('puissance')),
                    clean_value(poste_bt.get('lat')), clean_value(poste_bt.get('lon')),
                    clean_value(poste_hta.get('distance_m')), poste_hta.get('nom') or poste_hta.get('id'), clean_value(poste_hta.get('puissance')),
                    clean_value(poste_hta.get('lat')), clean_value(poste_hta.get('lon')),
                    friche.get('lien_streetview'), friche.get('lien_annuaire'), json.dumps(friche),
                    friche.get('amenity'), friche.get('shop'), friche.get('building'),
                    friche.get('landuse'), friche.get('office'), friche.get('industrial')
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], friche.get('commune'), friche.get('adresse'))
                
                total_exported += 1
                details['friches'] += 1
            
            # Exporter les parcelles RPG
            for rpg in data.get('rpg', []):
                result = execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_hta_distance_m, data_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    'parcelle_rpg', rpg.get('commune'), rpg.get('departement'), rpg.get('adresse'),
                    rpg.get('latitude'), rpg.get('longitude'),
                    rpg.get('surface', 0) * 10000 if rpg.get('surface') else None,
                    rpg.get('surface'), rpg.get('parcelle_cadastrale'),
                    rpg.get('distance_bt'), rpg.get('distance_hta'), json.dumps(rpg)
                ), fetch_one=True)
                
                if result and result.get('id'):
                    auto_create_project_for_prospect(result['id'], rpg.get('commune'), rpg.get('adresse'))
                
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
            # Récupérer tous les prospects
            prospects = execute_query('''
                SELECT * FROM agriweb_prospects 
                ORDER BY date_creation DESC
            ''', fetch_all=True)
            
            # Mapper contact_telephone -> contact_tel pour compatibilité frontend
            if prospects:
                for prospect in prospects:
                    if 'contact_telephone' in prospect:
                        prospect['contact_tel'] = prospect['contact_telephone']
            
            # Calculer les stats
            stats = execute_query('''
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN type = 'parking' THEN 1 END) as parkings,
                    COUNT(CASE WHEN type = 'toiture' THEN 1 END) as toitures,
                    COUNT(CASE WHEN type = 'friche' THEN 1 END) as friches,
                    COUNT(CASE WHEN type = 'parcelle_rpg' THEN 1 END) as rpg
                FROM agriweb_prospects
            ''', fetch_one=True)
            
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
                        data.get('commune'),
                        data.get('parcelle_cadastrale'),
                        project_id
                    ))
                    print(f"✅ [PROJECT UPDATE] Fiche projet {project_id} mise à jour avec le rapport")
                    
                    # Marquer l'étape "Rapport de recherche AgriWeb" comme terminée
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
                            parcelles_cadastrales, statut_projet, data_json
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        prospect_id,
                        f"Rapport {data.get('commune', 'inconnu')}",
                        data.get('commune'),
                        data.get('commune'),
                        data.get('parcelle_cadastrale'),
                        'etude',
                        json.dumps(data_json_to_save) if data_json_to_save else '{}'
                    ), fetch_one=True)
                    
                    print(f"🔍 [PROJECT CREATE] Résultat INSERT: {result}")
                    
                    if result:
                        project_id = result['id']
                        print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id} créée avec le rapport")
                        
                        # Créer les étapes du workflow pour ce nouveau projet
                        etapes_autoconso = [
                            ('Rapport de recherche AgriWeb', 1),
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
            execute_query('DELETE FROM agriweb_prospects WHERE id = %s', (prospect_id,))
            
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
            appointments = execute_query('''
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
                ORDER BY ca.date_rdv ASC
            ''', fetch_all=True)
            
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
            # Filtre optionnel par prospect_id
            prospect_id = request.args.get('prospect_id', type=int)
            
            if prospect_id:
                # Recherche pour un prospect spécifique
                projets = execute_query('''
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
                        pf.commune
                    FROM project_fiches pf
                    WHERE pf.prospect_id = %s
                    ORDER BY pf.date_creation DESC
                ''', (prospect_id,), fetch_all=True)
            else:
                # Tous les projets
                projets = execute_query('''
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
                        pf.commune
                    FROM project_fiches pf
                    ORDER BY pf.date_creation DESC
                ''', fetch_all=True)
            
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
                    commune, surface_totale, statut_projet
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data.get('prospect_id') or None,
                data.get('nom_projet'),
                data.get('type_projet', 'autoconsommation'),
                data.get('client_nom'),
                data.get('client_email'),
                data.get('client_telephone'),
                data.get('client_adresse'),
                data.get('adresse_projet') or prospect_info.get('commune'),
                data.get('parcelles_cadastrales') or prospect_info.get('parcelles_cadastrales'),
                'en_cours',
                data.get('date_fin_prevue') or None,
                data.get('responsable'),
                data.get('notes'),
                prospect_data_json,  # Rapport complet
                data.get('commune') or prospect_info.get('commune'),
                data.get('surface_totale') or prospect_info.get('surface_m2'),
                'etude'  # statut_projet par défaut
            ), fetch_one=True)
            
            print(f"[CREATE_PROJECT] INSERT result={result}")
            
            if not result or 'id' not in result:
                print(f"[CREATE_PROJECT] ERREUR: INSERT failed, result={result}")
                return jsonify({'success': False, 'error': 'Erreur lors de la création du projet'}), 500
            
            project_id = result['id']
            print(f"[CREATE_PROJECT] SUCCESS: project_id={project_id}")
            
            # Créer les étapes du workflow autoconsommation
            etapes_autoconso = [
                ('Rapport de recherche AgriWeb', 1),
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
                        nom_document,
                        type_document,
                        chemin_fichier,
                        date_upload,
                        taille_octets,
                        notes
                    FROM project_documents
                    WHERE project_id = %s
                    ORDER BY date_upload DESC
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
        """Ajoute un document au projet"""
        try:
            data = request.json
            
            doc_id = execute_query('''
                INSERT INTO project_documents (
                    project_id, etape_id, type_document, nom_fichier, 
                    chemin_fichier, url_document, statut, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                project_id,
                data.get('etape_id'),
                data.get('type_document'),
                data.get('nom_fichier'),
                data.get('chemin_fichier'),
                data.get('url_document'),
                data.get('statut', 'brouillon'),
                data.get('notes')
            ), fetch_one=True)['id']
            
            return jsonify({'success': True, 'document_id': doc_id})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

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
            "outputformat": "json"
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
        """Télécharger les données horaires 8760h PVGIS au format CSV"""
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
            
            # Créer CSV
            from io import StringIO
            import csv
            
            output = StringIO()
            writer = csv.writer(output)
            
            # En-tête
            writer.writerow(['Date', 'Heure', 'Production (W)', 'Irradiation (W/m²)', 'Température (°C)'])
            
            # Données horaires
            hourly_data = pvgis_data.get('outputs', {}).get('hourly', [])
            for entry in hourly_data:
                time_str = entry.get('time', '')
                power = entry.get('P', 0)
                irradiation = entry.get('G(i)', 0)
                temp = entry.get('T2m', 0)
                
                # Parser date/heure
                if time_str:
                    date_part = time_str[:8]  # YYYYMMDD
                    hour_part = time_str[8:10]  # HH
                    formatted_date = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:]}"
                    formatted_hour = f"{hour_part}:00"
                    
                    writer.writerow([formatted_date, formatted_hour, power, irradiation, temp])
            
            # Préparer réponse
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
                
                result = execute_query('''
                    INSERT INTO project_fiches (
                        prospect_id, nom_projet, statut_projet,
                        date_creation, date_modification
                    ) VALUES (
                        %s, %s, 'en_cours',
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                ''', (prospect_id, f"Projet PV - {prospect.get('nom', '')} {prospect.get('prenom', '')}"),
                fetch_one=True)
                
                if result:
                    project_id = result['id']
                    print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id} créée via visite technique")
                    
                    # Créer les étapes
                    etapes_autoconso = [
                        ('Rapport de recherche AgriWeb', 1),
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
            
            return render_template('calpinage_pv.html', prospect=prospect_dict)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur: {str(e)}", 500
    
    @app.route('/api/crm/prospects/<int:prospect_id>/calpinage', methods=['POST'])
    def save_calpinage(prospect_id):
        """Sauvegarder les données de calpinage dans data_json du prospect"""
        try:
            data = request.json
            print(f"[CALPINAGE SAVE] prospect_id={prospect_id}, zones={len(data.get('zones', []))}")
            
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
            
            # Chercher ou créer un projet pour ce prospect
            project = execute_query(
                'SELECT id FROM project_fiches WHERE prospect_id = %s ORDER BY date_creation DESC LIMIT 1',
                (prospect_id,),
                fetch_one=True
            )
            
            if not project:
                # Créer un nouveau projet car il n'existe pas encore
                print(f"[CALPINAGE SAVE] Pas de projet existant, création...")
                
                # Récupérer les infos du prospect pour créer le projet
                result = execute_query('''
                    INSERT INTO project_fiches (
                        prospect_id, nom_projet, statut_projet,
                        date_creation, date_modification
                    ) VALUES (
                        %s, %s, 'en_cours',
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                    RETURNING id
                ''', (prospect_id, f"Projet PV - {prospect.get('nom', '')} {prospect.get('prenom', '')}"),
                fetch_one=True)
                
                if result:
                    project_id = result['id']
                    print(f"✅ [PROJECT CREATE] Nouvelle fiche projet {project_id} créée via calepinage")
                    
                    # Créer les étapes du workflow
                    etapes_autoconso = [
                        ('Rapport de recherche AgriWeb', 1),
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
                        # L'étape Calepinage (3) est terminée
                        statut = 'termine' if ordre == 3 else 'a_faire'
                        date_fin = 'CURRENT_DATE' if ordre == 3 else 'NULL'
                        execute_query(f'''
                            INSERT INTO project_etapes (project_id, nom_etape, ordre, statut, date_fin_reelle)
                            VALUES (%s, %s, %s, %s, {date_fin})
                        ''', (project_id, etape_nom, ordre, statut))
                    
                    print(f"✅ [ETAPES CREATE] 11 étapes créées pour projet {project_id}, étape 3 (Calepinage) terminée")
            else:
                # Marquer l'étape "Calepinage" (ordre 3) comme terminée
                execute_query('''
                    UPDATE project_etapes 
                    SET statut = 'termine', 
                        date_fin_reelle = CURRENT_DATE
                    WHERE project_id = %s 
                    AND ordre = 3
                    AND statut != 'termine'
                ''', (project['id'],))
                print(f"✅ [ETAPE UPDATE] Étape 3 (Calepinage) marquée comme terminée pour projet {project['id']}")
            
            return jsonify({
                'success': True,
                'message': 'Calpinage sauvegardé avec succès'
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
            c.drawString(2*cm, 1.5*cm, "AgriWeb - Étude de faisabilité photovoltaïque")
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
            prospect_data = {
                'nom': prospect.get('nom', ''),
                'prenom': prospect.get('prenom', ''),
                'adresse': prospect.get('adresse', '')
            }
            
            # Générer le schéma unifilaire
            print(f"📐 [SCHEMA UNIFILAIRE] Génération pour prospect {prospect_id}")
            schema = SchemaUnifilaire(calpinage, prospect_data)
            
            # Générer le PDF en mémoire
            buffer = BytesIO()
            temp_path = f"/tmp/schema_unifilaire_{prospect_id}.pdf"
            schema.generer_schema_pdf(temp_path)
            
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
                        date_completion = CURRENT_TIMESTAMP
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
    # ============================================================================
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
            
            # Récupérer les données de la requête
            data = request.json
            
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
                data_json = json.loads(prospect['data_json']) if prospect['data_json'] else {}
                calpinage = data_json.get('calpinage', {})
                visite_technique = data_json.get('visite_technique', {})
                rapport_commune = data_json.get('rapport_commune', {})
            except:
                calpinage = {}
                visite_technique = {}
                rapport_commune = {}
            
            # Préparer les paramètres pour la proposition
            parametres = {
                'type_projet': data.get('type_projet', 'autoconsommation'),
                'puissance_kwc': float(data.get('puissance_kwc', 100)),
                'prix_kwc': float(data.get('prix_kwc', 850)),
                'consommation_annuelle_kwh': float(data.get('consommation_annuelle_kwh', 0)),
                'tarif_achat_kwh': float(data.get('tarif_achat_kwh', 0.20)),
                'tarif_revente_kwh': float(data.get('tarif_revente_kwh', 0.13)),
                'taux_autoconso': float(data.get('taux_autoconso', 70)),
                'pvgis_hourly_data': data.get('pvgis_hourly_data'),  # Optionnel
                'enedis_hourly_data': data.get('enedis_hourly_data'),  # Optionnel
            }
            
            # Enrichir prospect avec rapport_commune pour contraintes urbanisme
            if rapport_commune:
                prospect['data_json'] = data_json
            
            # Générer la proposition professionnelle
            proposition = PropositionProfessionnelle(prospect, calpinage, parametres)
            buffer = proposition.generer_pdf()
            
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
            
            # Retourner le PDF
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'Proposition_Professionnelle_{prospect.get("commune", "NA")}_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    # ============================================================================
    # ROUTE ADMIN - NETTOYAGE COMPLET PROSPECTS
    # ============================================================================
    @app.route('/api/crm/admin/cleanup-all', methods=['POST'])
    def cleanup_all_prospects():
        """Supprime TOUS les prospects et projets associés - ATTENTION DANGEREUX"""
        try:
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
