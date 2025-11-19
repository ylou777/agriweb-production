"""
🎯 DÉMO CONCRÈTE : Comment votre recherche par commune alimente automatiquement le CRM

Cette démo montre EXACTEMENT comment vos recherches par commune 
peuvent générer automatiquement des prospects commerciaux dans le CRM.
"""

import json
import time
from datetime import datetime

def simulate_commune_search_results():
    """Simule les résultats typiques d'une recherche par commune dans votre app"""
    
    # Ces données simulent ce que votre fonction search_by_commune() retourne
    return {
        "commune": "Nantes",
        "success": True,
        "timestamp": datetime.now().isoformat(),
        
        # 🏢 DONNÉES SIRENE (Entreprises) - SOURCE PRINCIPALE DE PROSPECTS
        "sirene_data": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "denominationUniteLegale": "FERME SOLAIRE ATLANTIQUE",
                        "adresseEtablissement": "15 Route de la Gare",
                        "libelleCommuneEtablissement": "Nantes",
                        "codePostalEtablissement": "44000",
                        "activitePrincipaleEtablissement": "0161Z",
                        "libelle_activite": "Culture de céréales",
                        "siret": "12345678901234",
                        "telephone": "02.40.XX.XX.XX"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-1.5536, 47.2184]
                    }
                },
                {
                    "type": "Feature", 
                    "properties": {
                        "denominationUniteLegale": "COOPERATIVE AGRICOLE LOIRE",
                        "adresseEtablissement": "89 Avenue des Champs",
                        "libelleCommuneEtablissement": "Nantes",
                        "activitePrincipaleEtablissement": "0162Z",
                        "libelle_activite": "Activités de soutien aux cultures",
                        "siret": "98765432109876"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [-1.5455, 47.2095]
                    }
                }
            ]
        },
        
        # 🌾 DONNÉES RPG (Parcelles agricoles) - PROSPECTS FONCIERS
        "rpg_data": {
            "type": "FeatureCollection", 
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "surf_parc": 15.5,  # hectares
                        "code_cultu": "BTH",
                        "lib_cultu": "Blé tendre d'hiver",
                        "id_parcel": "44109-001-000001"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1.5600, 47.2200], [-1.5580, 47.2200], [-1.5580, 47.2180], [-1.5600, 47.2180], [-1.5600, 47.2200]]]
                    }
                },
                {
                    "type": "Feature",
                    "properties": {
                        "surf_parc": 8.2,
                        "code_cultu": "MAI",
                        "lib_cultu": "Maïs grain et ensilage",
                        "id_parcel": "44109-002-000001"
                    }
                }
            ]
        },
        
        # 🏭 DONNÉES BÂTIMENTS - PROSPECTS TOITURES/HANGARS
        "batiments_data": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "usage": "agricole",
                        "nature": "hangar",
                        "hauteur": 8.5,
                        "surface_plancher": 1200,
                        "adresse": "Zone Industrielle Nord"
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-1.5520, 47.2150], [-1.5510, 47.2150], [-1.5510, 47.2140], [-1.5520, 47.2140], [-1.5520, 47.2150]]]
                    }
                }
            ]
        },
        
        # 🅿️ DONNÉES PARKINGS - PROSPECTS OMBRIÈRES
        "parkings_data": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "nom": "Parking Centre Commercial",
                        "nb_places": 450,
                        "surface": 9000,  # m²
                        "gestionnaire": "Mairie de Nantes"
                    }
                }
            ]
        },
        
        # 🏚️ DONNÉES FRICHES - PROSPECTS CENTRALES AU SOL
        "friches_data": {
            "type": "FeatureCollection", 
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "nom": "Ancienne usine textile",
                        "surface": 25000,  # m²
                        "statut": "friche industrielle",
                        "proprietaire": "Privé"
                    }
                }
            ]
        }
    }

def extract_prospects_from_commune_search(search_results):
    """
    🎯 EXTRACTION DES PROSPECTS - Fonction clé qui transforme vos données AgriWeb en prospects CRM
    
    Cette fonction analyse EXACTEMENT les mêmes données que votre recherche par commune
    et les convertit en prospects commerciaux pour le CRM.
    """
    
    prospects = []
    commune = search_results.get("commune", "Commune inconnue")
    
    print(f"\n🔍 === ANALYSE DES DONNÉES DE RECHERCHE POUR {commune.upper()} ===")
    
    # 1️⃣ PROSPECTS SIRENE (ENTREPRISES) - PRIORITÉ HAUTE
    sirene_data = search_results.get("sirene_data", {})
    if sirene_data.get("features"):
        print(f"\n🏢 ENTREPRISES SIRENE DÉTECTÉES: {len(sirene_data['features'])}")
        
        for feature in sirene_data["features"]:
            props = feature.get("properties", {})
            
            prospect = {
                "name": props.get("denominationUniteLegale", "Entreprise SIRENE"),
                "type": "entreprise",
                "source": "SIRENE",
                "priority": "haute",
                "contact_info": {
                    "address": props.get("adresseEtablissement", ""),
                    "city": props.get("libelleCommuneEtablissement", commune),
                    "postal_code": props.get("codePostalEtablissement", ""),
                    "phone": props.get("telephone", ""),
                    "siret": props.get("siret", "")
                },
                "business_info": {
                    "activity_code": props.get("activitePrincipaleEtablissement", ""),
                    "activity_label": props.get("libelle_activite", ""),
                    "sector": "agricole" if props.get("activitePrincipaleEtablissement", "").startswith("01") else "autre"
                },
                "commercial_potential": "Élevé - Entreprise active",
                "notes": f"Entreprise trouvée via recherche commune {commune}",
                "location": feature.get("geometry", {}).get("coordinates", [])
            }
            
            prospects.append(prospect)
            print(f"   ✅ {prospect['name']} - {prospect['business_info']['activity_label']}")
    
    # 2️⃣ PROSPECTS RPG (PROPRIÉTAIRES FONCIERS) - PRIORITÉ MOYENNE
    rpg_data = search_results.get("rpg_data", {})
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
                "commercial_potential": f"Moyen - Parcelle {surface}ha ({culture})",
                "notes": f"Parcelle de {surface}ha trouvée via recherche commune {commune}",
                "location": feature.get("geometry", {}).get("coordinates", [])
            }
            
            prospects.append(prospect)
            print(f"   ✅ Parcelle {surface}ha - {culture}")
    
    # 3️⃣ PROSPECTS BÂTIMENTS (PROPRIÉTAIRES TOITURES) - PRIORITÉ MOYENNE
    batiments_data = search_results.get("batiments_data", {})
    if batiments_data.get("features"):
        print(f"\n🏭 BÂTIMENTS DÉTECTÉS: {len(batiments_data['features'])}")
        
        for feature in batiments_data["features"]:
            props = feature.get("properties", {})
            usage = props.get("usage", "inconnu")
            surface = props.get("surface_plancher", 0)
            
            if usage in ["agricole", "industriel"] and surface > 500:
                prospect = {
                    "name": f"Propriétaire {props.get('nature', 'bâtiment')} - {commune}",
                    "type": "proprietaire_toiture",
                    "source": "Bâtiments",
                    "priority": "moyenne", 
                    "contact_info": {
                        "address": props.get("adresse", f"Bâtiment {usage} - {commune}"),
                        "city": commune
                    },
                    "building_info": {
                        "usage": usage,
                        "nature": props.get("nature", ""),
                        "surface_plancher": surface,
                        "hauteur": props.get("hauteur", 0),
                        "potential": "Toiture photovoltaïque"
                    },
                    "commercial_potential": f"Bon - {usage} {surface}m²",
                    "notes": f"Bâtiment {usage} trouvé via recherche commune {commune}",
                    "location": feature.get("geometry", {}).get("coordinates", [])
                }
                
                prospects.append(prospect)
                print(f"   ✅ {usage} {surface}m² - Potentiel toiture")
    
    # 4️⃣ PROSPECTS PARKINGS (GESTIONNAIRES) - PRIORITÉ FAIBLE
    parkings_data = search_results.get("parkings_data", {})
    if parkings_data.get("features"):
        print(f"\n🅿️ PARKINGS DÉTECTÉS: {len(parkings_data['features'])}")
        
        for feature in parkings_data["features"]:
            props = feature.get("properties", {})
            surface = props.get("surface", 0)
            nb_places = props.get("nb_places", 0)
            
            if surface > 3000:  # Parkings de plus de 3000m²
                prospect = {
                    "name": props.get("gestionnaire", f"Gestionnaire parking {commune}"),
                    "type": "gestionnaire_parking",
                    "source": "Parkings",
                    "priority": "faible",
                    "contact_info": {
                        "address": f"Parking {props.get('nom', '')} - {commune}",
                        "city": commune
                    },
                    "parking_info": {
                        "nom": props.get("nom", ""),
                        "surface": surface,
                        "nb_places": nb_places,
                        "potential": "Ombrières photovoltaïques"
                    },
                    "commercial_potential": f"Moyen - Parking {nb_places} places",
                    "notes": f"Parking trouvé via recherche commune {commune}",
                    "location": feature.get("geometry", {}).get("coordinates", [])
                }
                
                prospects.append(prospect)
                print(f"   ✅ {props.get('nom', 'Parking')} - {nb_places} places")
    
    # 5️⃣ PROSPECTS FRICHES (PROPRIÉTAIRES) - PRIORITÉ VARIABLE
    friches_data = search_results.get("friches_data", {})
    if friches_data.get("features"):
        print(f"\n🏚️ FRICHES DÉTECTÉES: {len(friches_data['features'])}")
        
        for feature in friches_data["features"]:
            props = feature.get("properties", {})
            surface = props.get("surface", 0)
            
            if surface > 5000:  # Friches de plus de 5000m²
                prospect = {
                    "name": f"Propriétaire friche - {props.get('nom', commune)}",
                    "type": "proprietaire_friche",
                    "source": "Friches",
                    "priority": "moyenne",
                    "contact_info": {
                        "address": f"Friche {props.get('nom', '')} - {commune}",
                        "city": commune
                    },
                    "friche_info": {
                        "nom": props.get("nom", ""),
                        "surface": surface,
                        "statut": props.get("statut", ""),
                        "proprietaire": props.get("proprietaire", ""),
                        "potential": "Centrale photovoltaïque au sol"
                    },
                    "commercial_potential": f"Élevé - Friche {surface/10000:.1f}ha",
                    "notes": f"Friche trouvée via recherche commune {commune}",
                    "location": feature.get("geometry", {}).get("coordinates", [])
                }
                
                prospects.append(prospect)
                print(f"   ✅ {props.get('nom', 'Friche')} - {surface/10000:.1f}ha")
    
    print(f"\n📊 === RÉSUMÉ EXTRACTION ===")
    print(f"🎯 TOTAL PROSPECTS GÉNÉRÉS: {len(prospects)}")
    
    # Statistiques par type
    types_count = {}
    priorities_count = {"haute": 0, "moyenne": 0, "faible": 0}
    
    for prospect in prospects:
        ptype = prospect.get("type", "inconnu")
        priority = prospect.get("priority", "faible")
        
        types_count[ptype] = types_count.get(ptype, 0) + 1
        priorities_count[priority] += 1
    
    print(f"\n📈 RÉPARTITION PAR TYPE:")
    for ptype, count in types_count.items():
        print(f"   • {ptype}: {count}")
    
    print(f"\n🚀 RÉPARTITION PAR PRIORITÉ:")
    for priority, count in priorities_count.items():
        print(f"   • {priority}: {count}")
    
    return prospects

def demo_integration_workflow():
    """Démontre le workflow complet d'intégration"""
    
    print("=" * 80)
    print("🎯 DÉMO COMPLÈTE : RECHERCHE COMMUNE → PROSPECTS CRM")
    print("=" * 80)
    
    # 1️⃣ SIMULATION D'UNE RECHERCHE PAR COMMUNE
    print("\n1️⃣ === SIMULATION RECHERCHE PAR COMMUNE ===")
    print("🔍 L'utilisateur recherche : Commune = Nantes, Filtres = RPG + SIRENE + Bâtiments")
    
    search_results = simulate_commune_search_results()
    print(f"✅ Recherche simulée - Données collectées pour {search_results['commune']}")
    
    # 2️⃣ EXTRACTION AUTOMATIQUE DES PROSPECTS
    print("\n2️⃣ === EXTRACTION AUTOMATIQUE DES PROSPECTS ===")
    prospects = extract_prospects_from_commune_search(search_results)
    
    # 3️⃣ CRÉATION DANS LE CRM (simulation)
    print(f"\n3️⃣ === INTÉGRATION CRM ===")
    print(f"📝 {len(prospects)} prospects prêts à être créés dans le CRM")
    
    # Simulation de l'appel API CRM
    crm_payload = {
        "search_source": "commune_search",
        "search_params": {
            "commune": search_results["commune"],
            "timestamp": search_results["timestamp"],
            "filters_applied": ["rpg", "sirene", "batiments", "parkings", "friches"]
        },
        "prospects": prospects
    }
    
    print(f"\n📤 Payload CRM préparé:")
    print(f"   • Source: {crm_payload['search_source']}")
    print(f"   • Commune: {crm_payload['search_params']['commune']}")
    print(f"   • Prospects: {len(crm_payload['prospects'])}")
    
    # 4️⃣ RÉSULTATS POUR L'UTILISATEUR
    print(f"\n4️⃣ === RÉSULTATS UTILISATEUR ===")
    print(f"🎉 Recherche terminée avec succès !")
    print(f"📊 {len(prospects)} nouveaux prospects créés automatiquement")
    print(f"🔗 Accessible dans le dashboard CRM : /crm/dashboard")
    
    # 5️⃣ EXEMPLES DE PROSPECTS CRÉÉS
    print(f"\n5️⃣ === EXEMPLES DE PROSPECTS CRÉÉS ===")
    
    for i, prospect in enumerate(prospects[:3], 1):  # Afficher les 3 premiers
        print(f"\n   📋 PROSPECT #{i}")
        print(f"      Nom: {prospect['name']}")
        print(f"      Type: {prospect['type']}")
        print(f"      Source: {prospect['source']}")
        print(f"      Priorité: {prospect['priority']}")
        print(f"      Potentiel: {prospect['commercial_potential']}")
        print(f"      Ville: {prospect['contact_info']['city']}")
    
    if len(prospects) > 3:
        print(f"\n   ... et {len(prospects) - 3} autres prospects")
    
    return crm_payload

if __name__ == "__main__":
    print("🚀 DÉMONSTRATION : INTÉGRATION RECHERCHE COMMUNE → CRM")
    print("=" * 80)
    print("Cette démo montre comment vos recherches par commune")
    print("alimentent automatiquement le CRM avec des prospects commerciaux.")
    print("=" * 80)
    
    # Exécuter la démo complète
    result = demo_integration_workflow()
    
    print("\n" + "=" * 80)
    print("🎯 CONCLUSION")
    print("=" * 80)
    print("✅ Vos recherches par commune contiennent EXACTEMENT")
    print("   les données nécessaires pour alimenter un CRM commercial !")
    print()
    print("🔗 LIEN AVEC VOS RECHERCHES:")
    print("   Recherche commune → Données SIRENE/RPG/Bâtiments")
    print("   → Extraction prospects → Création CRM automatique")
    print("   → Dashboard commercial → Suivi des affaires")
    print()
    print("🎬 PROCHAINE ÉTAPE:")
    print("   Ajouter simplement un bouton 'Créer prospects CRM'")
    print("   dans l'interface de vos résultats de recherche commune.")
    print()
    print("💡 VALEUR AJOUTÉE:")
    print("   Chaque recherche AgriWeb devient automatiquement")
    print("   une source de prospects commerciaux qualifiés !")