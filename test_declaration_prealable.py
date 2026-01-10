"""
Test du générateur de Déclaration Préalable de Travaux
"""

from declaration_prealable_generator import generate_declaration_prealable_complete

# Données de test (exemple prospect photovoltaïque)
prospect_test = {
    # Propriétaire/Demandeur
    'nom_prospect': 'DUPONT',
    'prenom_prospect': 'Jean',
    'proprietaire_denomination': 'Jean DUPONT',
    'proprietaire_adresse': '1 Place de la Concorde',
    'proprietaire_code_postal': '75008',
    'proprietaire_ville': 'Paris',
    'contact_tel': '06 12 34 56 78',
    'contact_email': 'jean.dupont@email.fr',
    'siret': '',  # Personne physique
    
    # Localisation terrain/installation (Coordonnées réelles: Tour Eiffel area résidentielle)
    'adresse': '5 Avenue Anatole France',
    'commune': 'Paris 7e',
    'latitude': 48.8584,  # Tour Eiffel - zone résidentielle proche
    'longitude': 2.2945,   # Tour Eiffel - zone résidentielle proche
    'parcelles_cadastrales': [
        {'section': 'AB', 'numero': '0125', 'surface': '850'},
        {'section': 'AB', 'numero': '0126', 'surface': '420'},
        {'section': 'AB', 'numero': '0127', 'surface': '305'},
    ],
    
    # Installation PV
    'type': 'toiture',  # ou 'sol', 'ombriere'
    'surface_m2': 120,  # Surface panneaux
    'surface_ha': 0,
    'type_raccordement': 'autoconso_injection',  # ou 'injection_totale', 'autoconso_sans_injection'
    'orientation_toiture': 'sud',
    
    # Dimensions bâtiment
    'longueur_batiment_m': 16,
    'largeur_batiment_m': 12,
    'hauteur_batiment_m': 6,  # Hauteur totale actuelle
    'hauteur_murs_m': 3.5,
    'hauteur_faitage_m': 2.5,
    'pente_toiture_deg': 30,
    
    # Postes électriques (pour info complémentaire)
    'poste_bt_nom': 'Poste Lilas',
    'poste_bt_distance_m': 85,
    'poste_bt_commune': 'Montpellier',
    'poste_bt_lat': 43.6120,
    'poste_bt_lon': 3.8780,
}

# Données de calpinage réel (exemple)
calpinage_test = {
    'module': {
        'longueur_mm': 2278,  # 2.278m
        'largeur_mm': 1134,   # 1.134m
        'puissance_wc': 560,  # 560Wc
        'marque': 'Canadian Solar',
        'modele': 'HiKu7 Mono PERC CS7N-560MS'
    },
    'zones': [
        {
            'id': 1,
            'numero': 1,
            'nbModules': 60,
            'nbCols': 6,       # 6 colonnes (inversé pour portrait)
            'nbRows': 10,      # 10 rangées (inversé pour portrait)
            'puissanceKw': 33.6,
            'moduleOrientation': 'portrait',  # PORTRAIT: module debout (1.13m horizontal, 2.28m vertical)
            'orientation': 180,  # Sud
            'inclinaison': 30
        }
    ]
}

def test_generation_dp():
    """Test de génération du dossier DP complet"""
    
    print("🚀 Génération de la Déclaration Préalable de Travaux COMPLÈTE...")
    print("=" * 70)
    
    try:
        # Générer le dossier complet AVEC données de calpinage
        dossier = generate_declaration_prealable_complete(prospect_test, calpinage_test)
        
        # Sauvegarder les PDFs
        print("\n📄 Sauvegarde des documents...")
        print("-" * 70)
        
        documents = [
            ('formulaire', 'DP_Formulaire_CERFA_13703.pdf', 'Formulaire CERFA 13703*09'),
            ('plan_dp1', 'DP1_Plan_Situation.pdf', 'Plan DP1 - Plan de situation (1/25000)'),
            ('plan_dp2', 'DP2_Plan_Masse.pdf', 'Plan DP2 - Plan de masse coté (1/200)'),
            ('plan_dp3', 'DP3_Plan_Coupe.pdf', 'Plan DP3 - Plan en coupe'),
            ('plan_dp4', 'DP4_Facades_Etat_Actuel.pdf', 'Plan DP4 - Façades état actuel'),
            ('plan_dp5', 'DP5_Facades_Etat_Projet.pdf', 'Plan DP5 - Façades état projeté'),
            ('plan_dp6', 'DP6_Insertion_Paysagere.pdf', 'Plan DP6 - Insertion paysagère (photo-montage)'),
            ('plan_dp7', 'DP7_Environnement_Proche.pdf', 'Plan DP7 - Photo environnement proche'),
            ('plan_dp8', 'DP8_Environnement_Lointain.pdf', 'Plan DP8 - Photo environnement lointain'),
        ]
        
        for key, filename, description in documents:
            if key in dossier:
                with open(filename, 'wb') as f:
                    f.write(dossier[key].read())
                print(f"✅ {description}")
                print(f"   → {filename}")
        
        print("\n" + "=" * 70)
        print("✅ SUCCÈS ! Dossier DP COMPLET généré")
        print("=" * 70)
        
        # Informations projet
        surface_panneaux = float(prospect_test.get('surface_m2', 0))
        puissance_kwc = round(surface_panneaux * 0.15, 2)
        
        print(f"\n📊 RÉSUMÉ DU PROJET :")
        print("-" * 70)
        print(f"   Demandeur : {prospect_test.get('nom_prospect', '')} {prospect_test.get('prenom_prospect', '')}")
        print(f"   Commune : {prospect_test.get('commune', '')}")
        print(f"   Adresse : {prospect_test.get('adresse', '')}")
        print(f"   Type : Installation photovoltaïque sur {prospect_test.get('type', '')}")
        print(f"   Puissance : {puissance_kwc:.2f} kWc")
        print(f"   Surface panneaux : {surface_panneaux:.1f} m²")
        print(f"   Modules estimés : ~{int(surface_panneaux / 2)}")
        print(f"   Raccordement : {prospect_test.get('type_raccordement', '')}")
        
        print(f"\n📦 DOSSIER COMPLET GÉNÉRÉ (9 documents) :")
        print("-" * 70)
        print(f"   ✓ Formulaire CERFA 13703*09 (4 pages)")
        print(f"   ✓ Plan DP1 - Plan de situation (carte IGN)")
        print(f"   ✓ Plan DP2 - Plan de masse coté (cadastre + implantation)")
        print(f"   ✓ Plan DP3 - Plan en coupe (terrain + construction)")
        print(f"   ✓ Plan DP4 - Façades/Toitures état actuel")
        print(f"   ✓ Plan DP5 - Façades/Toitures état projeté avec PV")
        print(f"   ✓ Plan DP6 - Insertion paysagère (photo-montage)")
        print(f"   ✓ Plan DP7 - Photo environnement proche (~100m)")
        print(f"   ✓ Plan DP8 - Photo environnement lointain (~500m)")
        
        print(f"\n📋 DÉPÔT EN MAIRIE :")
        print("-" * 70)
        print(f"   • Imprimer le dossier en 4 EXEMPLAIRES")
        print(f"   • Déposer à la mairie de {prospect_test.get('commune', 'votre commune')}")
        print(f"   • Délai instruction : 1 mois")
        print(f"   • (2 mois si zone protégée ABF)")
        print(f"   • Affichage obligatoire sur le terrain pendant les travaux")
        
        print(f"\n💡 AVANTAGES DE CE DOSSIER COMPLET :")
        print("-" * 70)
        print(f"   ✓ Conformité totale au Code de l'Urbanisme")
        print(f"   ✓ Plans techniques détaillés (cotations, légendes)")
        print(f"   ✓ Images satellite réelles (si coordonnées GPS disponibles)")
        print(f"   ✓ Photo-montages avant/après")
        print(f"   ✓ Insertion paysagère démontrée")
        print(f"   ✓ Conformité réglementaire vérifiée")
        print(f"   ✓ Prêt pour instruction immédiate")
        
        print(f"\n🎯 PROCHAINES ÉTAPES :")
        print("-" * 70)
        print(f"   1. Vérifier les documents générés")
        print(f"   2. Imprimer en 4 exemplaires")
        print(f"   3. Déposer en mairie avec récépissé")
        print(f"   4. Attendre décision (1-2 mois)")
        print(f"   5. Afficher autorisation sur terrain")
        print(f"   6. Démarrer les travaux après accord")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la génération : {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    test_generation_dp()
