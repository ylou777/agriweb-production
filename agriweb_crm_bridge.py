"""
Intégration CRM dans AgriWeb Principal
Module pour connecter les recherches AgriWeb existantes au système CRM
"""

import sys
import os

# Ajouter le chemin pour importer le CRM
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import des modules CRM
try:
    from crm_integration import AgriWebCRMIntegrator, integrate_search_results_to_crm
    from agriweb_crm_standalone import SimpleCRMManager
    CRM_AVAILABLE = True
    print("✅ Modules CRM importés avec succès")
except ImportError as e:
    print(f"⚠️ CRM non disponible: {e}")
    CRM_AVAILABLE = False

def extract_prospects_from_search_response(search_response, search_params):
    """
    Extrait les prospects depuis une réponse de recherche AgriWeb
    
    Args:
        search_response: Réponse complète d'une recherche AgriWeb
        search_params: Paramètres de la recherche originale
    
    Returns:
        dict: Données GeoJSON compatibles avec le CRM
    """
    if not search_response or not CRM_AVAILABLE:
        return None
    
    features = []
    
    # 1. Extraire les données SIRENE (entreprises)
    sirene_data = search_response.get('sirene', {})
    if isinstance(sirene_data, dict) and 'features' in sirene_data:
        for feature in sirene_data['features']:
            if feature.get('geometry') and feature.get('properties'):
                # Enrichir avec les informations de recherche
                properties = feature['properties'].copy()
                properties['source_search'] = 'sirene'
                properties['search_commune'] = search_params.get('commune', '')
                properties['search_type'] = 'recherche_agriweb'
                
                features.append({
                    'type': 'Feature',
                    'geometry': feature['geometry'],
                    'properties': properties
                })
    
    # 2. Extraire les bâtiments avec activité économique
    batiments_data = search_response.get('batiments', {})
    if isinstance(batiments_data, dict) and 'features' in batiments_data:
        for feature in batiments_data['features']:
            properties = feature.get('properties', {})
            
            # Filtrer les bâtiments d'intérêt commercial
            if (properties.get('usage') in ['commercial', 'industriel', 'agricole'] or
                properties.get('nature') in ['ferme', 'hangar', 'entrepot'] or
                properties.get('type') in ['farm', 'industrial']):
                
                # Enrichir les propriétés
                enriched_props = properties.copy()
                enriched_props['source_search'] = 'batiments'
                enriched_props['search_commune'] = search_params.get('commune', '')
                enriched_props['search_type'] = 'recherche_agriweb'
                enriched_props['name'] = f"Bâtiment {properties.get('usage', 'commercial')}"
                
                features.append({
                    'type': 'Feature',
                    'geometry': feature.get('geometry'),
                    'properties': enriched_props
                })
    
    # 3. Extraire les parcelles agricoles RPG
    rpg_data = search_response.get('rpg', {})
    if isinstance(rpg_data, dict) and 'features' in rpg_data:
        for feature in rpg_data['features']:
            properties = feature.get('properties', {})
            
            # Créer un prospect pour les grandes exploitations
            surface = properties.get('surf_parc', 0)
            if surface > 5:  # Plus de 5 hectares
                enriched_props = properties.copy()
                enriched_props['source_search'] = 'rpg'
                enriched_props['search_commune'] = search_params.get('commune', '')
                enriched_props['search_type'] = 'recherche_agriweb'
                enriched_props['name'] = f"Exploitation agricole {properties.get('code_cultu', '')}"
                enriched_props['landuse'] = 'farmland'
                enriched_props['amenity'] = 'farm'
                enriched_props['surface_hectares'] = surface
                
                # Centroïd pour la géométrie point
                geometry = feature.get('geometry')
                if geometry and geometry.get('type') == 'Polygon':
                    # Calculer centroïd approximatif
                    coords = geometry['coordinates'][0]
                    if len(coords) > 3:
                        avg_lng = sum(coord[0] for coord in coords) / len(coords)
                        avg_lat = sum(coord[1] for coord in coords) / len(coords)
                        geometry = {
                            'type': 'Point',
                            'coordinates': [avg_lng, avg_lat]
                        }
                
                features.append({
                    'type': 'Feature',
                    'geometry': geometry,
                    'properties': enriched_props
                })
    
    # 4. Extraire les zones d'activité
    zones_data = search_response.get('zones_urbanisme', {})
    if isinstance(zones_data, dict) and 'features' in zones_data:
        for feature in zones_data['features']:
            properties = feature.get('properties', {})
            
            # Zones commerciales/industrielles
            type_zone = properties.get('typezone', '').lower()
            if any(keyword in type_zone for keyword in ['commercial', 'industriel', 'activite', 'economique']):
                enriched_props = properties.copy()
                enriched_props['source_search'] = 'zones_urbanisme'
                enriched_props['search_commune'] = search_params.get('commune', '')
                enriched_props['search_type'] = 'recherche_agriweb'
                enriched_props['name'] = f"Zone {type_zone}"
                enriched_props['landuse'] = 'commercial' if 'commercial' in type_zone else 'industrial'
                
                features.append({
                    'type': 'Feature',
                    'geometry': feature.get('geometry'),
                    'properties': enriched_props
                })
    
    if not features:
        return None
    
    return {
        'type': 'FeatureCollection',
        'features': features,
        'search_metadata': {
            'commune': search_params.get('commune', ''),
            'timestamp': search_params.get('timestamp', ''),
            'total_features': len(features)
        }
    }

def integrate_agriweb_search_to_crm(search_response, search_params, user_session):
    """
    Intègre une recherche AgriWeb complète au CRM
    
    Args:
        search_response: Réponse de recherche AgriWeb
        search_params: Paramètres originaux de la recherche
        user_session: Session utilisateur (doit contenir user_id)
    
    Returns:
        dict: Résultat de l'intégration
    """
    if not CRM_AVAILABLE:
        return {
            'success': False,
            'error': 'Module CRM non disponible'
        }
    
    # Extraire les prospects
    prospects_data = extract_prospects_from_search_response(search_response, search_params)
    
    if not prospects_data:
        return {
            'success': False,
            'error': 'Aucun prospect trouvé dans les résultats de recherche'
        }
    
    # Nom de la recherche
    commune = search_params.get('commune', 'Commune inconnue')
    search_name = f"Recherche AgriWeb - {commune}"
    
    # Intégrer au CRM
    return integrate_search_results_to_crm(prospects_data, search_name, user_session)

def add_crm_integration_to_search_response(search_response, search_params, user_session):
    """
    Ajoute automatiquement les données CRM à une réponse de recherche
    
    Args:
        search_response: Réponse originale de recherche
        search_params: Paramètres de recherche
        user_session: Session utilisateur
    
    Returns:
        dict: Réponse enrichie avec données CRM
    """
    if not CRM_AVAILABLE or not user_session.get('user_id'):
        return search_response
    
    try:
        # Tenter l'intégration automatique
        crm_result = integrate_agriweb_search_to_crm(search_response, search_params, user_session)
        
        # Ajouter les informations CRM à la réponse
        if 'crm' not in search_response:
            search_response['crm'] = {}
        
        search_response['crm']['integration_result'] = crm_result
        search_response['crm']['prospects_found'] = len(
            extract_prospects_from_search_response(search_response, search_params)['features']
        ) if extract_prospects_from_search_response(search_response, search_params) else 0
        
        return search_response
        
    except Exception as e:
        print(f"⚠️ Erreur intégration CRM: {e}")
        return search_response

# Fonctions utilitaires pour l'interface
def get_crm_dashboard_data(user_id):
    """Récupère les données du dashboard CRM"""
    if not CRM_AVAILABLE:
        return None
    
    try:
        crm_manager = SimpleCRMManager()
        prospects = crm_manager.get_prospects(user_id)
        
        return {
            'total_prospects': len(prospects),
            'new_prospects': len([p for p in prospects if p['status'] == 'nouveau']),
            'auto_prospects': len([p for p in prospects if p['source'] == 'recherche_automatique']),
            'recent_prospects': prospects[:5]  # 5 plus récents
        }
    except Exception as e:
        print(f"⚠️ Erreur dashboard CRM: {e}")
        return None

def is_crm_available():
    """Vérifie si le CRM est disponible"""
    return CRM_AVAILABLE

# Message de statut
if CRM_AVAILABLE:
    print("🎯 AgriWeb-CRM Integration: ACTIVE")
    print("   • Intégration automatique des recherches")
    print("   • Extraction prospects SIRENE, RPG, Bâtiments")
    print("   • Dashboard CRM disponible")
else:
    print("⚠️ AgriWeb-CRM Integration: INACTIVE")
    print("   • Fonctionnement en mode recherche uniquement")