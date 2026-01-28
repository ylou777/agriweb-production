# Fonctionnalité: Point de consommation le plus proche

## 📋 Description

Cette fonctionnalité enrichit les résultats de recherche par commune en identifiant le **point de consommation électrique Enedis le plus proche** pour chaque parking, toiture et friche détectés.

## 🎯 Objectif

Au lieu de sélectionner des points de consommation aléatoires, le système identifie maintenant le point de consommation **le plus proche géographiquement** de chaque installation photovoltaïque potentielle (parking, toiture, friche), permettant ainsi de proposer des projets d'autoconsommation plus pertinents.

## 🔧 Fonctions créées

### 1. `get_all_consommation(lat, lon, radius_deg=0.05)`

Récupère tous les points de consommation Enedis dans un rayon donné.

**Paramètres:**
- `lat`: Latitude du point de référence
- `lon`: Longitude du point de référence  
- `radius_deg`: Rayon de recherche en degrés (défaut: 0.05 = ~5.5 km)

**Retour:**
Liste de features GeoJSON avec distance calculée depuis le point de référence.

### 2. `get_nearest_consommation(lat, lon, count=3, radius_deg=0.05)`

Récupère les N points de consommation les plus proches d'un point donné.

**Paramètres:**
- `lat`: Latitude du point de référence
- `lon`: Longitude du point de référence
- `count`: Nombre de points à retourner (défaut: 3)
- `radius_deg`: Rayon de recherche en degrés

**Retour:**
Liste des points de consommation triés par distance (les plus proches en premier).

### 3. `_find_nearest_conso(pt_lon, pt_lat, consos)`

Fonction helper interne qui trouve le point de consommation le plus proche d'un point donné.

**Paramètres:**
- `pt_lon`: Longitude du point de référence
- `pt_lat`: Latitude du point de référence
- `consos`: Liste de features GeoJSON de points de consommation

**Retour:**
Dict avec les informations du point de consommation le plus proche:
```python
{
    'distance_m': 234.56,  # Distance en mètres
    'lon': -0.2965,
    'lat': 43.1815,
    'adresse': '2 RUE MIRAMON',
    'consommation_mwh': 43.593,
    'secteur': 'TERTIAIRE',
    'nom_commune': 'Aast',
    'nombre_de_sites': 1,
    'annee': 2023,
    'code_commune': '64001'
}
```

## 📊 Intégration dans le rapport communal

La fonction `generate_integrated_commune_report` a été modifiée pour:

1. **Récupérer les données Enedis** pour la commune via `get_enedis_consommation_by_commune(code_commune)`

2. **Convertir en features GeoJSON** pour permettre le calcul de distance

3. **Enrichir chaque élément** (parking, friche, toiture) avec le champ `conso_proche`:

```python
{
    "parkings_details": [
        {
            "lat": 43.1667,
            "lon": -0.2833,
            "surface_m2": 2500.0,
            "poste_bt_proche": {...},
            "poste_hta_proche": {...},
            "conso_proche": {
                "distance_m": 234.56,
                "adresse": "2 RUE MIRAMON",
                "consommation_mwh": 43.593,
                "secteur": "TERTIAIRE"
                // ... autres informations
            }
        }
    ]
}
```

## ✅ Avantages

1. **Pertinence accrue**: Identification automatique du consommateur le plus proche pour proposer des projets d'autoconsommation optimaux

2. **Données enrichies**: Chaque installation PV potentielle est maintenant associée à:
   - Distance au point de consommation (en mètres)
   - Adresse du consommateur
   - Consommation annuelle (MWh)
   - Secteur d'activité (TERTIAIRE, INDUSTRIEL, etc.)

3. **Compatibilité**: Fonctionne de la même manière que `get_nearest_postes` pour les postes électriques

## 🧪 Tests

Deux fichiers de test ont été créés:

1. **`test_nearest_conso.py`**: Test unitaire des fonctions de récupération
2. **`test_conso_rapport_integration.py`**: Test d'intégration dans le rapport communal

## 💡 Utilisation

La fonctionnalité est automatiquement activée lors de la recherche par commune avec les filtres parkings/friches/toitures activés:

```python
from agriweb_hebergement_gratuit import generate_integrated_commune_report

filters = {
    "filter_parkings": True,
    "filter_friches": True,
    "filter_toitures": True
}

rapport = generate_integrated_commune_report("Aast", filters=filters)

# Accéder aux données enrichies
for parking in rapport["parkings_details"]:
    conso = parking.get("conso_proche", {})
    if conso:
        print(f"Point de conso à {conso['distance_m']}m")
        print(f"Consommation: {conso['consommation_mwh']} MWh/an")
```

## 📝 Notes techniques

- Les coordonnées des points de consommation proviennent de la base GeoServer (couche `gpu:consommation_enedis`)
- Le calcul de distance utilise la formule de distance euclidienne avec conversion en mètres (×111000)
- Le rayon de recherche par défaut (0.05°) correspond à environ 5.5 km
- Les données sont limitées à 20 points maximum par commune pour optimiser les performances
