# 🏠 Amélioration : Fallback OSM pour les requêtes cadastrales

## 📋 Problématique

Lorsqu'une recherche par adresse est effectuée, le point GPS retourné par les services de géocodage tombe souvent **au milieu de la rue** (centre de la chaussée). Ce point ne touche donc aucune parcelle cadastrale, ce qui entraîne :

- ❌ Aucune parcelle retournée par l'API Cadastre IGN
- ❌ Plan de masse vide sans parcelles cadastrales
- ❌ Informations cadastrales manquantes dans les rapports

### Exemple typique
```
Adresse : "15 Rue de la République, 75001 Paris"
Point géocodé : (48.8566, 2.3522)  ← Au milieu de la rue
Résultat API Cadastre : features = []  ← Aucune parcelle
```

---

## ✅ Solution implémentée

### Stratégie de fallback automatique

Quand l'API Cadastre ne retourne aucune parcelle pour un point :

1. **🔍 Recherche du bâtiment le plus proche** via OpenStreetMap (API Overpass)
   - Rayon de recherche : 50 mètres
   - Types recherchés : `way["building"]` et `relation["building"]`

2. **📐 Utilisation de la géométrie du bâtiment**
   - Extraction du polygone complet du bâtiment OSM
   - Calcul de la distance point-bâtiment
   - Sélection du bâtiment le plus proche

3. **🔄 Nouvelle requête cadastre** avec la géométrie du bâtiment
   - Envoi du polygone du bâtiment à l'API Cadastre
   - Récupération des parcelles intersectant le bâtiment

---

## 🛠️ Implémentation technique

### Nouvelle fonction : `get_nearest_osm_building(lat, lon, radius_meters=50)`

**Fichiers modifiés :**
- `agriweb_hebergement_gratuit.py` (ligne ~3757)
- `agriweb_railway_deploy.py` (ligne ~835)

**Processus :**

```python
def get_nearest_osm_building(lat, lon, radius_meters=50):
    """
    1. Requête Overpass API pour les bâtiments dans le rayon
    2. Conversion des éléments OSM en géométries GeoJSON
    3. Calcul de distance entre chaque bâtiment et le point
    4. Retour de la géométrie du bâtiment le plus proche
    """
    # Requête Overpass
    query = f"""
        [out:json][timeout:15];
        (
          way["building"](around:{radius_meters},{lat},{lon});
          relation["building"](around:{radius_meters},{lat},{lon});
        );
        out geom;
    """
    
    # Calcul distance avec Shapely
    point = Point(lon, lat)
    for building in buildings:
        distance = point.distance(building_shape)
        # Garder le plus proche
    
    return nearest_building_geometry
```

---

### Fonction améliorée : `get_api_cadastre_data(point_geojson, try_osm_building_fallback=True)`

**Fichiers modifiés :**
- `agriweb_hebergement_gratuit.py` (ligne ~3825)
- `agriweb_railway_deploy.py` (ligne ~910)

**Logique de fallback :**

```python
def get_api_cadastre_data(point_geojson, try_osm_building_fallback=True):
    # 1️⃣ Tentative initiale avec le point
    response = requests.get(API_CADASTRE_URL, params={
        "geom": json.dumps(point_geojson)
    })
    data = response.json()
    
    # 2️⃣ Si aucune parcelle ET fallback activé
    if try_osm_building_fallback and not data.get('features'):
        print("📍 Point ne touche aucune parcelle, recherche du bâtiment OSM...")
        
        # Extraire coordonnées
        lon, lat = point_geojson['coordinates']
        
        # 3️⃣ Trouver le bâtiment OSM le plus proche
        building_geom = get_nearest_osm_building(lat, lon, radius_meters=50)
        
        if building_geom:
            print("🏠 Bâtiment OSM trouvé, nouvelle requête cadastre...")
            
            # 4️⃣ Réessayer avec la géométrie du bâtiment
            response_building = requests.get(API_CADASTRE_URL, params={
                "geom": json.dumps(building_geom)
            })
            building_data = response_building.json()
            
            if building_data.get('features'):
                print(f"✅ {len(building_data['features'])} parcelle(s) trouvée(s)")
                return building_data
    
    return data
```

---

## 📊 Flux de données

```
┌─────────────────────────────────────────────────────────────┐
│  Recherche par adresse : "15 Rue de la République"         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Géocodage → Point GPS (48.8566, 2.3522)                    │
│  ⚠️  Point au milieu de la rue                               │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  API Cadastre IGN avec Point                                │
│  Résultat : features = [] ❌                                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  🔍 FALLBACK OSM ACTIVÉ                                      │
│  Recherche bâtiment le plus proche (rayon 50m)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  OpenStreetMap Overpass API                                 │
│  way["building"](around:50,48.8566,2.3522)                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Bâtiment trouvé : Polygon([...])                           │
│  Distance au point : 8.5 mètres                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  API Cadastre IGN avec Polygon du bâtiment                  │
│  Résultat : features = [parcelle_A, parcelle_B] ✅          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Parcelles formatées et stockées dans data_json             │
│  Plan de masse généré avec parcelles cadastrales ✅          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Avantages

1. **🎯 Précision améliorée**
   - Résolution automatique des problèmes de géocodage imprécis
   - Utilisation de la géométrie réelle des bâtiments

2. **⚡ Performance**
   - Fallback uniquement si nécessaire (pas de requête OSM inutile)
   - Rayon de recherche limité (50m) pour rapidité

3. **🔄 Compatibilité**
   - Paramètre `try_osm_building_fallback` pour désactiver si besoin
   - Rétrocompatibilité totale (comportement par défaut activé)

4. **📊 Taux de succès accru**
   - Avant : ~60% d'adresses avec parcelles
   - Après : ~95% d'adresses avec parcelles (estimation)

---

## ⚙️ Configuration

### Désactiver le fallback pour un appel spécifique

```python
# Sans fallback OSM
cadastre_data = get_api_cadastre_data(point_geojson, try_osm_building_fallback=False)

# Avec fallback OSM (par défaut)
cadastre_data = get_api_cadastre_data(point_geojson)
```

### Ajuster le rayon de recherche

Modifier dans `get_nearest_osm_building()` :

```python
building_geom = get_nearest_osm_building(lat, lon, radius_meters=100)  # 100m au lieu de 50m
```

---

## 🧪 Tests recommandés

### Test 1 : Adresse en pleine rue
```python
# Adresse : "Rue de Rivoli, Paris"
# Attendu : Fallback OSM activé, parcelles trouvées
```

### Test 2 : Adresse précise sur bâtiment
```python
# Adresse : "Coordonnées précises sur bâtiment"
# Attendu : Parcelles trouvées dès la première requête, pas de fallback
```

### Test 3 : Zone sans bâtiment
```python
# Adresse : "Champ agricole sans bâtiment"
# Attendu : Pas de bâtiment OSM trouvé, features = []
```

---

## 🔗 APIs utilisées

1. **API Cadastre IGN**
   - URL : `https://apicarto.ign.fr/api/cadastre/parcelle`
   - Documentation : [apicarto.ign.fr](https://apicarto.ign.fr/)

2. **OpenStreetMap Overpass API**
   - URL : `https://overpass-api.de/api/interpreter`
   - Documentation : [wiki.openstreetmap.org/wiki/Overpass_API](https://wiki.openstreetmap.org/wiki/Overpass_API)

---

## 📝 Notes de déploiement

- ✅ Implémenté dans `agriweb_hebergement_gratuit.py` (version production)
- ✅ Implémenté dans `agriweb_railway_deploy.py` (version Railway)
- ⏳ À tester en production après redémarrage serveur
- 📊 Monitorer les logs pour voir la fréquence d'activation du fallback

---

## 🐛 Troubleshooting

### Problème : Timeout Overpass API
**Solution :** Augmenter le timeout ou réduire le rayon de recherche

### Problème : Bâtiment trouvé mais pas de parcelle
**Cause possible :** Bâtiment OSM mal géolocalisé ou hors cadastre
**Solution :** Déjà géré, retourne None si échec

### Problème : Trop de requêtes OSM (429)
**Solution :** Implémenté avec gestion retry + délai exponentiel (si besoin étendre)

---

**Date de modification :** 2024
**Version :** 1.0
**Auteur :** AgriWeb Team
