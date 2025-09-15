
# === FILTRAGE SIRENE INTELLIGENT POUR CRM ===
# À ajouter dans agriweb_crm_bridge.py ou créer un nouveau fichier sirene_filtering.py

from shapely.geometry import shape, Point

# Codes NAF pertinents pour le secteur photovoltaïque/énergie
RELEVANT_NAF_CODES = {
    # Agriculture (priorité maximale)
    '01': 'Agriculture, sylviculture et pêche',
    # Industries pertinentes
    '10': 'Industries alimentaires', 
    '16': 'Travail du bois',
    '23': 'Autres produits minéraux non métalliques',
    '24': 'Métallurgie',
    '25': 'Fabrication de produits métalliques',
    '28': 'Fabrication de machines et équipements',
    # Construction et BTP
    '41': 'Construction de bâtiments',
    '42': 'Génie civil', 
    '43': 'Travaux de construction spécialisés',
    # Commerce de gros
    '46': 'Commerce de gros',
    # Transport et logistique
    '49': 'Transports terrestres',
    '52': 'Entreposage et services auxiliaires',
    # Immobilier et services
    '68': 'Activités immobilières',
    '77': 'Activités de location',
    '81': 'Services relatifs aux bâtiments'
}

# Mots-clés qualifiants dans les dénominations sociales
RELEVANT_KEYWORDS = [
    'AGRICOLE', 'ELEVAGE', 'CULTURE', 'FERME', 'EXPLOITATION',
    'SOLAIRE', 'PHOTOVOLTAIQUE', 'ENERGIE', 'ELECTRIQUE', 'RENOUVELABLE',
    'HANGAR', 'ENTREPOT', 'STOCKAGE', 'LOGISTIQUE', 'PLATEFORME',
    'COOPERATIVE', 'SCEA', 'EARL', 'GAEC', 'SA AGRICOLE',
    'TRANSPORT', 'BTP', 'CONSTRUCTION', 'BATIMENT', 'GENIE CIVIL',
    'INDUSTRIE', 'FABRICATION', 'USINE', 'MANUFACTURE', 'PRODUCTION'
]

def filter_sirene_prospects(sirene_features, rpg_features=None, min_score=20):
    """
    Filtre intelligemment les données SIRENE pour identifier les prospects CRM pertinents
    
    Args:
        sirene_features: Liste des entreprises SIRENE trouvées
        rpg_features: Parcelles RPG pour croisement géographique (optionnel)
        min_score: Score minimum de qualification (défaut: 20)
    
    Returns:
        Liste des prospects qualifiés avec leur scoring
    """
    
    qualified_prospects = []
    
    for feature in sirene_features:
        props = feature.get('properties', {})
        
        # Données entreprise
        denomination = props.get('denominationUniteLegale', '').upper()
        naf_code = props.get('activitePrincipaleEtablissement', '')
        naf_2_digits = naf_code[:2] if naf_code else ''
        effectif = props.get('trancheEffectifsUniteLegale', '')
        
        # Calcul du score de qualification
        score = 0
        reasons = []
        
        # 1. Score par secteur d'activité (NAF)
        if naf_2_digits in RELEVANT_NAF_CODES:
            if naf_code.startswith('01'):  # Agriculture = priorité max
                score += 50
                reasons.append(f"🌾 Secteur agricole ({RELEVANT_NAF_CODES[naf_2_digits]})")
            elif naf_2_digits in ['41', '42', '43']:  # BTP
                score += 35
                reasons.append(f"🏗️ BTP ({RELEVANT_NAF_CODES[naf_2_digits]})")
            elif naf_2_digits in ['24', '25', '28']:  # Industrie
                score += 40
                reasons.append(f"🏭 Industrie ({RELEVANT_NAF_CODES[naf_2_digits]})")
            else:
                score += 25
                reasons.append(f"💼 Secteur pertinent ({RELEVANT_NAF_CODES[naf_2_digits]})")
        
        # 2. Score par mots-clés dans la dénomination
        keyword_matches = [kw for kw in RELEVANT_KEYWORDS if kw in denomination]
        if keyword_matches:
            keyword_bonus = min(len(keyword_matches) * 15, 45)  # Max 45 pts
            score += keyword_bonus
            reasons.append(f"🔍 Mots-clés: {', '.join(keyword_matches[:3])}")
        
        # 3. Bonus taille entreprise (si info disponible)
        if effectif:
            if '50' in effectif or '100' in effectif or '250' in effectif:  # >50 salariés
                score += 20
                reasons.append("👥 Grande entreprise")
            elif '10' in effectif or '20' in effectif:  # 10-50 salariés
                score += 10
                reasons.append("👥 Entreprise moyenne")
        
        # 4. Bonus proximité parcelles agricoles
        if rpg_features and feature.get('geometry'):
            try:
                sirene_point = Point(feature['geometry']['coordinates'])
                nearby_parcels = 0
                
                for rpg_feature in rpg_features[:20]:  # Optimisation: max 20 parcelles
                    if rpg_feature.get('geometry'):
                        rpg_geom = shape(rpg_feature['geometry'])
                        distance_deg = sirene_point.distance(rpg_geom.centroid)
                        if distance_deg < 0.005:  # ~500m
                            nearby_parcels += 1
                
                if nearby_parcels > 0:
                    proximity_bonus = min(nearby_parcels * 10, 30)  # Max 30 pts
                    score += proximity_bonus
                    reasons.append(f"📍 Proximité {nearby_parcels} parcelle(s) agricole(s)")
            except Exception:
                pass  # Ignorer les erreurs de géométrie
        
        # Qualification si score suffisant
        if score >= min_score:
            # Détermination de la priorité
            if score >= 80:
                priority = "haute"
                priority_label = "🔥 HAUTE"
            elif score >= 50:
                priority = "moyenne" 
                priority_label = "⚡ MOYENNE"
            else:
                priority = "faible"
                priority_label = "💡 FAIBLE"
            
            qualified_prospects.append({
                'sirene_data': feature,
                'qualification': {
                    'score': score,
                    'priority': priority,
                    'priority_label': priority_label,
                    'reasons': reasons
                },
                'contact_info': {
                    'name': props.get('denominationUniteLegale', 'Entreprise inconnue'),
                    'address': props.get('adresseEtablissement', ''),
                    'city': props.get('libelleCommuneEtablissement', ''),
                    'postal_code': props.get('codePostalEtablissement', ''),
                    'siret': props.get('siret', ''),
                    'naf_code': naf_code,
                    'activity': props.get('libelle_activite', '')
                }
            })
    
    # Tri par score décroissant
    qualified_prospects.sort(key=lambda x: x['qualification']['score'], reverse=True)
    
    return qualified_prospects

def analyze_sirene_qualification(sirene_features, rpg_features=None):
    """
    Analyse rapide pour l'interface utilisateur
    """
    
    total = len(sirene_features)
    qualified = filter_sirene_prospects(sirene_features, rpg_features)
    
    analysis = {
        'total_enterprises': total,
        'qualified_prospects': len(qualified),
        'qualification_rate': round(len(qualified) / total * 100, 1) if total > 0 else 0,
        'by_priority': {
            'haute': len([p for p in qualified if p['qualification']['priority'] == 'haute']),
            'moyenne': len([p for p in qualified if p['qualification']['priority'] == 'moyenne']),
            'faible': len([p for p in qualified if p['qualification']['priority'] == 'faible'])
        },
        'top_prospects': qualified[:5]  # Top 5 pour aperçu
    }
    
    return analysis

# Exemple d'utilisation dans le widget CRM
def get_sirene_prospects_summary(search_results):
    """
    Résumé des prospects SIRENE pour l'affichage CRM
    """
    
    sirene_data = search_results.get('sirene_data', {})
    rpg_data = search_results.get('rpg_data', {})
    
    if not sirene_data.get('features'):
        return {
            'total': 0,
            'qualified': 0,
            'message': 'Aucune entreprise SIRENE trouvée'
        }
    
    analysis = analyze_sirene_qualification(
        sirene_data['features'], 
        rpg_data.get('features', [])
    )
    
    return {
        'total': analysis['total_enterprises'],
        'qualified': analysis['qualified_prospects'],
        'rate': analysis['qualification_rate'],
        'priorities': analysis['by_priority'],
        'top_prospects': [
            {
                'name': p['contact_info']['name'],
                'priority': p['qualification']['priority_label'],
                'score': p['qualification']['score'],
                'activity': p['contact_info']['activity']
            }
            for p in analysis['top_prospects']
        ],
        'message': f"{analysis['qualified_prospects']} prospects qualifiés sur {analysis['total_enterprises']} entreprises ({analysis['qualification_rate']}%)"
    }
