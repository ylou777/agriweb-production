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

    @app.route('/api/crm/launch', methods=['POST'])
    def crm_launch():
        """Lance l'application CRM AgriWeb (désactivé sur Railway)"""
        return jsonify({
            'success': False,
            'message': 'Fonctionnalité disponible uniquement en version desktop'
        }), 400

    # ============================================================================
    # ROUTES API - EXPORT PROSPECTS
    # ============================================================================

    @app.route('/api/crm/export', methods=['POST'])
    def crm_export():
        """Exporte les éléments sélectionnés vers le CRM"""
        try:
            if not request.is_json:
                return jsonify({'success': False, 'error': 'La requête doit être en JSON'}), 400
            
            data = request.get_json()
            total_exported = 0
            details = {'parkings': 0, 'toitures': 0, 'friches': 0, 'rpg': 0}
            
            # Exporter les parkings
            for parking in data.get('parkings', []):
                poste_bt = parking.get('poste_bt_proche', {})
                poste_hta = parking.get('poste_hta_proche', {})
                
                execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    'parking', parking.get('commune'), parking.get('departement'), parking.get('adresse'),
                    parking.get('lat'), parking.get('lon'), parking.get('surface_m2'),
                    parking.get('surface_m2', 0) / 10000 if parking.get('surface_m2') else None,
                    json.dumps(parking.get('parcelles', [])),
                    poste_bt.get('distance_m'), poste_bt.get('nom') or poste_bt.get('id'), poste_bt.get('puissance'),
                    poste_bt.get('lat'), poste_bt.get('lon'),
                    poste_hta.get('distance_m'), poste_hta.get('nom') or poste_hta.get('id'), poste_hta.get('puissance'),
                    poste_hta.get('lat'), poste_hta.get('lon'),
                    parking.get('lien_streetview'), parking.get('lien_annuaire'), json.dumps(parking)
                ))
                total_exported += 1
                details['parkings'] += 1
            
            # Exporter les toitures
            for toiture in data.get('toitures', []):
                poste_bt = toiture.get('poste_bt_proche', {})
                poste_hta = toiture.get('poste_hta_proche', {})
                
                execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    'toiture', toiture.get('commune'), toiture.get('departement'), toiture.get('adresse'),
                    toiture.get('lat'), toiture.get('lon'), toiture.get('surface_m2'),
                    toiture.get('surface_m2', 0) / 10000 if toiture.get('surface_m2') else None,
                    json.dumps(toiture.get('parcelles', [])),
                    poste_bt.get('distance_m'), poste_bt.get('nom') or poste_bt.get('id'), poste_bt.get('puissance'),
                    poste_bt.get('lat'), poste_bt.get('lon'),
                    poste_hta.get('distance_m'), poste_hta.get('nom') or poste_hta.get('id'), poste_hta.get('puissance'),
                    poste_hta.get('lat'), poste_hta.get('lon'),
                    toiture.get('lien_streetview'), toiture.get('lien_annuaire'), json.dumps(toiture)
                ))
                total_exported += 1
                details['toitures'] += 1
            
            # Exporter les friches
            for friche in data.get('friches', []):
                poste_bt = friche.get('poste_bt_proche', {})
                poste_hta = friche.get('poste_hta_proche', {})
                
                execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_bt_nom, poste_bt_puissance, poste_bt_lat, poste_bt_lon,
                        poste_hta_distance_m, poste_hta_nom, poste_hta_puissance, poste_hta_lat, poste_hta_lon,
                        lien_streetview, lien_annuaire, data_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    'friche', friche.get('commune'), friche.get('departement'), friche.get('adresse'),
                    friche.get('lat'), friche.get('lon'), friche.get('surface_m2'),
                    friche.get('surface_m2', 0) / 10000 if friche.get('surface_m2') else None,
                    json.dumps(friche.get('parcelles', [])),
                    poste_bt.get('distance_m'), poste_bt.get('nom') or poste_bt.get('id'), poste_bt.get('puissance'),
                    poste_bt.get('lat'), poste_bt.get('lon'),
                    poste_hta.get('distance_m'), poste_hta.get('nom') or poste_hta.get('id'), poste_hta.get('puissance'),
                    poste_hta.get('lat'), poste_hta.get('lon'),
                    friche.get('lien_streetview'), friche.get('lien_annuaire'), json.dumps(friche)
                ))
                total_exported += 1
                details['friches'] += 1
            
            # Exporter les parcelles RPG
            for rpg in data.get('rpg', []):
                execute_query('''
                    INSERT INTO agriweb_prospects (
                        type, commune, departement, adresse, latitude, longitude,
                        surface_m2, surface_ha, parcelles_cadastrales,
                        poste_bt_distance_m, poste_hta_distance_m, data_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    'parcelle_rpg', rpg.get('commune'), rpg.get('departement'), rpg.get('adresse'),
                    rpg.get('latitude'), rpg.get('longitude'),
                    rpg.get('surface', 0) * 10000 if rpg.get('surface') else None,
                    rpg.get('surface'), rpg.get('parcelle_cadastrale'),
                    rpg.get('distance_bt'), rpg.get('distance_hta'), json.dumps(rpg)
                ))
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
        """Liste tous les projets"""
        try:
            projets = execute_query('''
                SELECT 
                    pf.*,
                    ap.commune,
                    ap.type as prospect_type,
                    ap.adresse,
                    (SELECT COUNT(*) FROM project_etapes ps WHERE ps.project_id = pf.id AND ps.statut = 'termine') as etapes_terminees,
                    (SELECT COUNT(*) FROM project_etapes ps WHERE ps.project_id = pf.id) as etapes_total
                FROM project_fiches pf
                LEFT JOIN agriweb_prospects ap ON pf.prospect_id = ap.id
                ORDER BY pf.date_debut DESC
            ''', fetch_all=True)
            
            return jsonify({'success': True, 'projets': projets if projets else []})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets', methods=['POST'])
    def create_projet():
        """Crée une nouvelle fiche projet"""
        try:
            data = request.json
            
            # Créer le projet
            project_id = execute_query('''
                INSERT INTO project_fiches (
                    prospect_id, nom_projet, type_projet, client_nom, client_email,
                    client_telephone, client_adresse, adresse_projet, parcelles_cadastrales,
                    statut_global, date_fin_prevue, responsable, notes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data.get('prospect_id') or None,
                data.get('nom_projet'),
                data.get('type_projet', 'autoconsommation'),
                data.get('client_nom'),
                data.get('client_email'),
                data.get('client_telephone'),
                data.get('client_adresse'),
                data.get('adresse_projet'),
                data.get('parcelles_cadastrales'),
                'en_cours',
                data.get('date_fin_prevue') or None,
                data.get('responsable'),
                data.get('notes')
            ), fetch_one=True)['id']
            
            # Créer les étapes du workflow autoconsommation
            etapes_autoconso = [
                ('Rapport de recherche AgriWeb', 1),
                ('Étude d\'adresse & visite technique', 2),
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
                execute_query('''
                    INSERT INTO project_etapes (project_id, nom_etape, ordre, statut)
                    VALUES (%s, %s, %s, %s)
                ''', (project_id, etape_nom, ordre, 'a_faire'))
            
            return jsonify({'success': True, 'project_id': project_id})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/crm/projets/<int:project_id>', methods=['GET'])
    def get_projet_details(project_id):
        """Récupère les détails complets d'un projet"""
        try:
            # Infos projet
            projet = execute_query('''
                SELECT pf.*, ap.commune, ap.type as prospect_type, ap.adresse, ap.latitude, ap.longitude
                FROM project_fiches pf
                LEFT JOIN agriweb_prospects ap ON pf.prospect_id = ap.id
                WHERE pf.id = %s
            ''', (project_id,), fetch_one=True)
            
            if not projet:
                return jsonify({'success': False, 'error': 'Projet non trouvé'}), 404
            
            # Étapes du projet
            projet['etapes'] = execute_query('''
                SELECT * FROM project_etapes
                WHERE project_id = %s
                ORDER BY ordre
            ''', (project_id,), fetch_all=True) or []
            
            # Documents du projet
            projet['documents'] = execute_query('''
                SELECT pd.*, pe.nom_etape
                FROM project_documents pd
                LEFT JOIN project_etapes pe ON pd.etape_id = pe.id
                WHERE pd.project_id = %s
                ORDER BY pd.date_creation DESC
            ''', (project_id,), fetch_all=True) or []
            
            return jsonify({'success': True, 'projet': projet})
            
        except Exception as e:
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
                SET statut = %s, date_debut = %s, date_fin = %s, responsable = %s, notes = %s
                WHERE id = %s AND project_id = %s
            ''', (
                data.get('statut'),
                data.get('date_debut'),
                data.get('date_fin'),
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
