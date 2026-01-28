"""
Test de l'intégration de conso_proche dans le rapport communal
Vérifie que parkings, friches et toitures ont bien leur point de consommation le plus proche
"""
from agriweb_hebergement_gratuit import generate_integrated_commune_report

# Test avec Aast
commune_test = "Aast"

print("=" * 80)
print("🧪 TEST: Intégration conso_proche dans le rapport communal")
print("=" * 80)

print(f"\n📍 Génération du rapport pour {commune_test}")
print("   Filtres: parkings, friches, toitures activés")

filters = {
    "filter_parkings": True,
    "parking_min_area": 500.0,  # Surface minimale réduite pour avoir plus de résultats
    "filter_friches": True,
    "friches_min_area": 500.0,
    "filter_toitures": True,
    "toitures_min_surface": 100.0,
    "max_details": 10  # Limiter pour accélérer le test
}

print("\n🔄 Génération du rapport en cours...")
rapport = generate_integrated_commune_report(commune_test, filters=filters)

if rapport.get("error"):
    print(f"\n❌ ERREUR: {rapport['error']}")
else:
    print("\n✅ Rapport généré avec succès")
    
    # Vérifier les parkings
    parkings_details = rapport.get("parkings_details", [])
    print(f"\n🅿️ PARKINGS: {len(parkings_details)} parkings analysés")
    if parkings_details:
        premier_parking = parkings_details[0]
        conso_proche = premier_parking.get("conso_proche", {})
        print(f"\n   Premier parking:")
        print(f"      - Position: lat={premier_parking.get('lat')}, lon={premier_parking.get('lon')}")
        print(f"      - Surface: {premier_parking.get('surface_m2')} m²")
        if conso_proche:
            print(f"      - ✅ Conso proche trouvée:")
            print(f"           Distance: {conso_proche.get('distance_m', 'N/A')} m")
            print(f"           Adresse: {conso_proche.get('adresse', 'N/A')}")
            print(f"           Consommation: {conso_proche.get('consommation_mwh', 'N/A')} MWh/an")
            print(f"           Secteur: {conso_proche.get('secteur', 'N/A')}")
        else:
            print(f"      - ⚠️ Aucun point de consommation proche trouvé")
    
    # Vérifier les friches
    friches_details = rapport.get("friches_details", [])
    print(f"\n🏚️ FRICHES: {len(friches_details)} friches analysées")
    if friches_details:
        premiere_friche = friches_details[0]
        conso_proche = premiere_friche.get("conso_proche", {})
        print(f"\n   Première friche:")
        print(f"      - Position: lat={premiere_friche.get('lat')}, lon={premiere_friche.get('lon')}")
        print(f"      - Surface: {premiere_friche.get('surface_m2')} m²")
        if conso_proche:
            print(f"      - ✅ Conso proche trouvée:")
            print(f"           Distance: {conso_proche.get('distance_m', 'N/A')} m")
            print(f"           Adresse: {conso_proche.get('adresse', 'N/A')}")
            print(f"           Consommation: {conso_proche.get('consommation_mwh', 'N/A')} MWh/an")
        else:
            print(f"      - ⚠️ Aucun point de consommation proche trouvé")
    
    # Vérifier les toitures
    toitures_details = rapport.get("toitures_details", [])
    print(f"\n🏠 TOITURES: {len(toitures_details)} toitures analysées")
    if toitures_details:
        premiere_toiture = toitures_details[0]
        conso_proche = premiere_toiture.get("conso_proche", {})
        print(f"\n   Première toiture:")
        print(f"      - Position: lat={premiere_toiture.get('lat')}, lon={premiere_toiture.get('lon')}")
        print(f"      - Surface: {premiere_toiture.get('surface_m2')} m²")
        if conso_proche:
            print(f"      - ✅ Conso proche trouvée:")
            print(f"           Distance: {conso_proche.get('distance_m', 'N/A')} m")
            print(f"           Adresse: {conso_proche.get('adresse', 'N/A')}")
            print(f"           Consommation: {conso_proche.get('consommation_mwh', 'N/A')} MWh/an")
            print(f"           Secteur: {conso_proche.get('secteur', 'N/A')}")
        else:
            print(f"      - ⚠️ Aucun point de consommation proche trouvé")
    
    # Résumé
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES ENRICHISSEMENTS")
    print("=" * 80)
    
    nb_parkings_avec_conso = sum(1 for p in parkings_details if p.get('conso_proche'))
    nb_friches_avec_conso = sum(1 for f in friches_details if f.get('conso_proche'))
    nb_toitures_avec_conso = sum(1 for t in toitures_details if t.get('conso_proche'))
    
    print(f"\n🅿️ Parkings avec conso_proche: {nb_parkings_avec_conso}/{len(parkings_details)}")
    print(f"🏚️ Friches avec conso_proche: {nb_friches_avec_conso}/{len(friches_details)}")
    print(f"🏠 Toitures avec conso_proche: {nb_toitures_avec_conso}/{len(toitures_details)}")
    
    total_avec_conso = nb_parkings_avec_conso + nb_friches_avec_conso + nb_toitures_avec_conso
    total_elements = len(parkings_details) + len(friches_details) + len(toitures_details)
    
    if total_elements > 0:
        pourcentage = (total_avec_conso / total_elements) * 100
        print(f"\n✅ Total: {total_avec_conso}/{total_elements} éléments enrichis ({pourcentage:.1f}%)")
    else:
        print(f"\n⚠️ Aucun élément trouvé pour cette commune")

print("\n" + "=" * 80)
print("✅ Test terminé")
print("=" * 80)
