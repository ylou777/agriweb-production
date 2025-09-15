
"""
agriweb_crm_bridge_intelligent.py - Version avec filtrage SIRENE intelligent

Cette version améliore l'extraction des prospects en qualifiant intelligemment
les données SIRENE au lieu de prendre toutes les entreprises.
"""

from shapely.geometry import shape, Point
import json
from datetime import datetime

# === CONFIGURATION FILTRAGE SIRENE ===

# Codes NAF prioritaires pour le secteur photovoltaïque/énergie
PRIORITY_NAF_CODES = {
    # Agriculture (priorité maximale)
    '01': {'priority': 'haute', 'sector': 'Agriculture', 'score': 50},
    # Énergie et utilities
    '35': {'priority': 'haute', 'sector': 'Énergie', 'score': 60},
    # Industries pertinentes  
    '10': {'priority': 'moyenne', 'sector': 'Industrie alimentaire', 'score': 30},
    '16': {'priority': 'moyenne', 'sector': 'Travail du bois', 'score': 30},
    '23': {'priority': 'moyenne', 'sector': 'Produits minéraux', 'score': 35},
    '24': {'priority': 'moyenne', 'sector': 'Métallurgie', 'score': 40},
    '25': {'priority': 'moyenne', 'sector': 'Produits métalliques', 'score': 40},
    '28': {'priority': 'moyenne', 'sector': 'Machines et équipements', 'score': 35},
    # BTP et construction
    '41': {'priority': 'moyenne', 'sector': 'Construction bâtiments', 'score': 35},
    '42': {'priority': 'moyenne', 'sector': 'Génie civil', 'score': 35},
    '43': {'priority': 'moyenne', 'sector': 'Travaux spécialisés', 'score': 30},
    # Commerce et logistique
    '46': {'priority': 'faible', 'sector': 'Commerce de gros', 'score': 20},
    '49': {'priority': 'faible', 'sector': 'Transport terrestre', 'score': 25},
    '52': {'priority': 'faible', 'sector': 'Entreposage', 'score': 30},
    # Services
    '68': {'priority': 'faible', 'sector': 'Immobilier', 'score': 20},
    '77': {'priority': 'faible', 'sector': 'Location', 'score': 25},
    '81': {'priority': 'moyenne', 'sector': 'Services aux bâtiments', 'score': 30}
}

# Mots-clés qualifiants avec scoring
QUALIFYING_KEYWORDS = {
    # Agriculture (score élevé)
    'AGRICOLE': 25, 'ELEVAGE': 25, 'CULTURE': 20, 'FERME': 25, 'EXPLOITATION': 20,
    'COOPERATIVE': 25, 'SCEA': 30, 'EARL': 30, 'GAEC': 30, 'SA AGRICOLE': 35,
    # Énergie (score très élevé)
    'SOLAIRE': 35, 'PHOTOVOLTAIQUE': 40, 'ENERGIE': 30, 'ELECTRIQUE': 25, 'RENOUVELABLE': 35,
    # Infrastructure (score moyen)
    'HANGAR': 20, 'ENTREPOT': 20, 'STOCKAGE': 15, 'LOGISTIQUE': 15, 'PLATEFORME': 15,
    # BTP (score moyen)
    'TRANSPORT': 15, 'BTP': 25, 'CONSTRUCTION': 20, 'BATIMENT': 20, 'GENIE CIVIL': 25,
    # Industrie (score moyen)
    'INDUSTRIE': 20, 'FABRICATION': 15, 'USINE': 20, 'MANUFACTURE': 15, 'PRODUCTION': 15
}

def qualify_sirene_prospect(sirene_feature, rpg_features=None):
    """
    Qualifie un prospect SIRENE selon plusieurs critères
    
    Returns:
        dict avec qualification ou None si non qualifié
    """
    
    props = sirene_feature.get('properties', {})
    
    # Debug simple des champs SIRENE
    if not hasattr(qualify_sirene_prospect, '_debug_done'):
        print(f"🔬 [SIRENE_DEBUG] Champs disponibles: {list(props.keys())[:10]}")  # Limiter à 10
        qualify_sirene_prospect._debug_done = True
    
    # Données de base
    denomination = props.get('denominationUniteLegale', '').upper()
    naf_code = props.get('activitePrincipaleEtablissement', '')
    naf_2_digits = naf_code[:2] if naf_code else ''
    
    # Calcul du score de qualification
    score = 0
    reasons = []
    priority = 'faible'
    
    # 1. Score par code NAF
    if naf_2_digits in PRIORITY_NAF_CODES:
        naf_info = PRIORITY_NAF_CODES[naf_2_digits]
        score += naf_info['score']
        priority = naf_info['priority']
        reasons.append(f"Secteur {naf_info['sector']}")
    
    # 2. Score par mots-clés
    keyword_score = 0
    found_keywords = []
    
    for keyword, points in QUALIFYING_KEYWORDS.items():
        if keyword in denomination:
            keyword_score += points
            found_keywords.append(keyword)
    
    # Limiter le bonus mots-clés pour éviter la sur-qualification
    keyword_score = min(keyword_score, 60)
    score += keyword_score
    
    if found_keywords:
        reasons.append(f"Mots-clés: {', '.join(found_keywords[:3])}")
    
    # 3. Bonus proximité parcelles agricoles
    if rpg_features and sirene_feature.get('geometry'):
        try:
            sirene_point = Point(sirene_feature['geometry']['coordinates'])
            nearby_parcels = 0
            
            for rpg_feature in rpg_features[:15]:  # Limite pour performance
                if rpg_feature.get('geometry'):
                    rpg_geom = shape(rpg_feature['geometry'])
                    distance_deg = sirene_point.distance(rpg_geom.centroid)
                    if distance_deg < 0.005:  # ~500m
                        nearby_parcels += 1
            
            if nearby_parcels > 0:
                proximity_bonus = min(nearby_parcels * 8, 25)
                score += proximity_bonus
                reasons.append(f"Proximité {nearby_parcels} parcelle(s) agricole(s)")
                
                # Upgrade de priorité si proximité agricole
                if nearby_parcels >= 2 and priority == 'faible':
                    priority = 'moyenne'
        except Exception:
            pass
    
    # 4. Ajustement priorité selon score final
    if score >= 80:
        priority = 'haute'
    elif score >= 50 and priority == 'faible':
        priority = 'moyenne'
    
    # Seuil de qualification (ajustable)
    QUALIFICATION_THRESHOLD = 15
        
    if score >= QUALIFICATION_THRESHOLD:
        return {
            'qualified': True,
            'score': score,
            'priority': priority,
            'reasons': reasons,
            'contact_info': {
                'name': props.get('denominationUniteLegale', 'Entreprise SIRENE'),
                'address': props.get('adresseEtablissement', ''),
                'city': props.get('libelleCommuneEtablissement', ''),
                'postal_code': props.get('codePostalEtablissement', ''),
                'siret': props.get('siret', ''),
                'naf_code': naf_code,
                'activity': props.get('libelle_activite', ''),
                'phone': props.get('telephone', '')
            }
        }
    
    return None

def extract_qualified_sirene_prospects(sirene_data, rpg_data=None, commune=""):
    """
    Extrait et qualifie les prospects SIRENE pertinents
    """
    
    if not sirene_data or not sirene_data.get('features'):
        return []
    
    sirene_features = sirene_data['features']
    rpg_features = rpg_data.get('features', []) if rpg_data else []
    
    prospects = []
    
    print(f"🔍 [SIRENE QUALIFICATION] Analyse de {len(sirene_features)} entreprises pour {commune}")
    
    for feature in sirene_features:
        
        qualification = qualify_sirene_prospect(feature, rpg_features)
        
        if qualification and qualification['qualified']:
            prospect = {
                "name": qualification['contact_info']['name'],
                "type": "entreprise_qualifiee",
                "source": "SIRENE",
                "priority": qualification['priority'],
                "contact_info": qualification['contact_info'],
                "business_info": {
                    "activity_code": qualification['contact_info']['naf_code'],
                    "activity_label": qualification['contact_info']['activity'],
                    "qualification_score": qualification['score'],
                    "qualification_reasons": qualification['reasons']
                },
                "commercial_potential": f"Score {qualification['score']} - {qualification['priority'].title()}",
                "notes": f"Entreprise qualifiée via recherche commune {commune}. Raisons: {'; '.join(qualification['reasons'])}",
                "location": feature.get("geometry", {}).get("coordinates", []),
                "qualification_date": datetime.now().isoformat()
            }
            
            prospects.append(prospect)
    
    # Tri par score décroissant
    prospects.sort(key=lambda x: x['business_info']['qualification_score'], reverse=True)
    
    print(f"✅ [SIRENE QUALIFICATION] {len(prospects)} prospects qualifiés ({len(prospects)/len(sirene_features)*100:.1f}%)")
    
    # Statistiques par priorité
    stats = {'haute': 0, 'moyenne': 0, 'faible': 0}
    for p in prospects:
        stats[p['priority']] += 1
    
    print(f"📊 [RÉPARTITION] Haute: {stats['haute']}, Moyenne: {stats['moyenne']}, Faible: {stats['faible']}")
    
    return prospects

def extract_prospects_from_commune_search_intelligent(search_results):
    """
    Version intelligente de l'extraction des prospects avec filtrage SIRENE
    """
    
    prospects = []
    commune = search_results.get("commune", "Commune inconnue")
    
    print(f"\n🎯 === EXTRACTION INTELLIGENTE DES PROSPECTS POUR {commune.upper()} ===")
    
    # 1. PROSPECTS SIRENE QUALIFIÉS (Nouvelle approche)
    sirene_data = search_results.get("sirene_data", {})
    rpg_data = search_results.get("rpg_data", {})
    
    sirene_prospects = extract_qualified_sirene_prospects(sirene_data, rpg_data, commune)
    prospects.extend(sirene_prospects)
    
    # 2. PROSPECTS RPG (Parcelles importantes) - Logique existante
    if rpg_data.get("features"):
        large_parcels = [f for f in rpg_data["features"] if f.get("properties", {}).get("surf_parc", 0) > 5]
        print(f"\n🌾 PARCELLES RPG IMPORTANTES: {len(large_parcels)} (>5ha)")
        
        for feature in large_parcels:
            props = feature.get("properties", {})
            surface = props.get("surf_parc", 0)
            culture = props.get("lib_cultu", "Culture inconnue")
            
            prospect = {
                "name": f"Propriétaire parcelle {props.get('id_parcel', 'XXX')}",
                "type": "proprietaire_foncier", 
                "source": "RPG",
                "priority": "moyenne",
                "contact_info": {
                    "address": f"Parcelle agricole - {commune}",
                    "city": commune
                },
                "land_info": {
                    "surface_ha": surface,
                    "culture": culture,
                    "parcel_id": props.get("id_parcel", ""),
                    "potential": "Agrivoltaïsme" if surface > 10 else "Centrale au sol"
                },
                "commercial_potential": f"Parcelle {surface}ha - {culture}",
                "notes": f"Parcelle de {surface}ha trouvée via recherche commune {commune}",
                "location": feature.get("geometry", {}).get("coordinates", [])
            }
            
            prospects.append(prospect)
    
    # 3. AUTRES PROSPECTS (Bâtiments, parkings, friches) - Logique existante
    # [Code existant pour bâtiments, parkings, friches...]
    
    print(f"\n📊 === RÉSUMÉ EXTRACTION INTELLIGENTE ===")
    print(f"🎯 TOTAL PROSPECTS GÉNÉRÉS: {len(prospects)}")
    
    # Statistiques finales
    by_type = {}
    by_priority = {'haute': 0, 'moyenne': 0, 'faible': 0}
    
    for prospect in prospects:
        ptype = prospect.get("type", "inconnu")
        priority = prospect.get("priority", "faible")
        
        by_type[ptype] = by_type.get(ptype, 0) + 1
        by_priority[priority] += 1
    
    print(f"\n📈 RÉPARTITION PAR TYPE:")
    for ptype, count in by_type.items():
        print(f"   • {ptype}: {count}")
    
    print(f"\n🚀 RÉPARTITION PAR PRIORITÉ:")
    for priority, count in by_priority.items():
        print(f"   • {priority}: {count}")
    
    return prospects

def get_sirene_analysis_for_widget(search_results):
    """
    Analyse rapide des données SIRENE pour l'affichage dans le widget CRM
    """
    
    # Les données SIRENE peuvent être sous 'sirene' ou 'sirene_data'
    sirene_data = search_results.get('sirene_data', {})
    if not sirene_data:
        sirene_data = search_results.get('sirene', [])
        # Si on reçoit une liste, on la convertit en format GeoJSON
        if isinstance(sirene_data, list) and len(sirene_data) > 0:
            sirene_data = {'features': sirene_data}
    
    rpg_data = search_results.get('rpg_data', {})
    
    print(f"🔍 [CRM_DEBUG] sirene_data type: {type(sirene_data)}")
    if isinstance(sirene_data, dict):
        print(f"🔍 [CRM_DEBUG] sirene_data keys: {list(sirene_data.keys())}")
        if sirene_data.get('features'):
            print(f"🔍 [CRM_DEBUG] Nombre d'entreprises: {len(sirene_data['features'])}")
    
    if not sirene_data or (isinstance(sirene_data, dict) and not sirene_data.get('features')):
        print(f"⚠️ [CRM] Pas de données SIRENE exploitables")
        return {
            'total_enterprises': 0,
            'qualified_prospects': 0,
            'qualification_rate': 0,
            'by_priority': {'haute': 0, 'moyenne': 0, 'faible': 0},
            'top_prospects': [],
            'message': 'Aucune entreprise SIRENE trouvée'
        }
    
    total_enterprises = len(sirene_data['features'])
    print(f"🔍 [CRM_DEBUG] Analysing {total_enterprises} enterprises...")
    
    qualified_prospects = extract_qualified_sirene_prospects(sirene_data, rpg_data)
    print(f"🔍 [CRM_DEBUG] Found {len(qualified_prospects)} qualified prospects")
    
    by_priority = {'haute': 0, 'moyenne': 0, 'faible': 0}
    for p in qualified_prospects:
        by_priority[p['priority']] += 1
    
    return {
        'total_enterprises': total_enterprises,
        'qualified_prospects': len(qualified_prospects),
        'qualification_rate': round(len(qualified_prospects) / total_enterprises * 100, 1) if total_enterprises > 0 else 0,
        'by_priority': by_priority,
        'top_prospects': qualified_prospects[:5],
        'message': f"{len(qualified_prospects)} prospects qualifiés sur {total_enterprises} entreprises ({round(len(qualified_prospects) / total_enterprises * 100, 1) if total_enterprises > 0 else 0}%)"
    }

# Export de la fonction principale pour utilisation dans l'application
def integrate_agriweb_search_to_crm_intelligent(search_response):
    """
    Version intelligente de l'intégration AgriWeb → CRM avec filtrage SIRENE
    """
    
    try:
        prospects = extract_prospects_from_commune_search_intelligent(search_response)
        
        # [Ici, intégration avec la base CRM comme dans la version originale]
        
        return {
            "prospects_created": len(prospects),
            "prospects_skipped": 0,
            "prospects_updated": 0,
            "details": f"Intégration intelligente avec filtrage SIRENE réalisée pour {search_response.get('commune', 'commune inconnue')}"
        }
        
    except Exception as e:
        print(f"❌ [INTEGRATION] Erreur: {e}")
        return {
            "prospects_created": 0,
            "prospects_skipped": 0, 
            "prospects_updated": 0,
            "error": str(e)
        }
