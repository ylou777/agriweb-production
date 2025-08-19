# 🗺️ Analyse GeoServer dans AgriWeb 2.0

## Vue d'ensemble

GeoServer est le **serveur de données géospatiales central** d'AgriWeb 2.0. Il sert de source unique pour toutes les couches géographiques utilisées par l'application.

## 🏗️ Architecture GeoServer

### Configuration de Base
```python
GEOSERVER_URL = "http://localhost:8080/geoserver"
GEOSERVER_WFS_URL = f"{GEOSERVER_URL}/ows"
```

### 📊 Couches de Données Configurées

| Couche | Nom GeoServer | Utilisation |
|--------|---------------|-------------|
| **Cadastre** | `gpu:prefixes_sections` | Données cadastrales |
| **Parcelles** | `gpu:PARCELLE2024` | Parcelles agricoles |
| **Postes BT** | `gpu:poste_elec_shapefile` | Postes électriques basse tension |
| **Postes HTA** | `gpu:postes-electriques-rte` | Postes haute tension |
| **Capacités Réseau** | `gpu:CapacitesDAccueil` | Capacités d'accueil électrique |
| **PLU** | `gpu:gpu1` | Plan Local d'Urbanisme |
| **Parkings** | `gpu:parkings_sup500m2` | Parkings > 500m² |
| **Friches** | `gpu:friches-standard` | Terrains en friche |
| **Potentiel Solaire** | `gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93` | Potentiel énergétique |
| **ZAER** | `gpu:ZAER_ARRETE_SHP_FRA` | Zones à enjeux environnementaux |
| **RPG** | `gpu:PARCELLES_GRAPHIQUES` | Registre Parcellaire Graphique |
| **Sirène** | `gpu:GeolocalisationEtablissement_Sirene france` | Établissements (~50m) |
| **Éleveurs** | `gpu:etablissements_eleveurs` | Établissements d'élevage |
| **PPRI** | `gpu:ppri` | Plans de Prévention des Risques |

## 🔄 Mécanisme d'Accès aux Données

### 1. Fonction Centrale `fetch_wfs_data()`
```python
def fetch_wfs_data(layer_name, bbox, srsname="EPSG:4326"):
    layer_q = quote(layer_name, safe=':')
    url = f"{GEOSERVER_WFS_URL}?service=WFS&version=2.0.0&request=GetFeature&typeName={layer_q}&outputFormat=application/json&bbox={bbox}&srsname={srsname}"
    try:
        resp = http_session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json().get('features', [])
    except Exception as e:
        print(f"[fetch_wfs_data] Erreur {layer_name}: {e}")
        return []
```

### 2. Protocole WFS (Web Feature Service)
- **Version** : 2.0.0
- **Format de sortie** : GeoJSON
- **Requête spatiale** : Bbox (bounding box)
- **Système de coordonnées** : EPSG:4326 (WGS84) ou EPSG:2154 (Lambert 93)

## 🎯 Fonctions d'Accès Spécialisées

### Parcelles Agricoles
```python
def get_all_parcelles(lat, lon, radius=0.03):
    # Conversion WGS84 → Lambert 93
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
    x, y = transformer.transform(lon, lat)
    bbox = f"{x - radius * 111000},{y - radius * 111000},{x + radius * 111000},{y + radius * 111000},EPSG:2154"
    # Requête WFS vers GeoServer
```

### Infrastructure Électrique
```python
def get_all_postes(lat, lon, radius_deg=0.1):
    bbox = f"{lon-radius_deg},{lat-radius_deg},{lon+radius_deg},{lat+radius_deg},EPSG:4326"
    features = fetch_wfs_data(POSTE_LAYER, bbox)
```

### Données PLU/Urbanisme
```python
def get_plu_info(lat, lon, radius=0.03):
    bbox = f"{lon-radius},{lat-radius},{lon+radius},{lat+radius},EPSG:4326"
    features = fetch_wfs_data(PLU_LAYER, bbox)
```

## 🔧 Workflow de Traitement

### 1. **Requête Utilisateur**
- L'utilisateur clique sur la carte ou recherche une adresse
- Les coordonnées (lat, lon) sont extraites

### 2. **Calcul des Zones d'Intérêt**
- Génération d'un bbox autour du point
- Différents rayons selon le type de données

### 3. **Interrogation GeoServer**
- Requête WFS vers les couches pertinentes
- Récupération des features au format GeoJSON

### 4. **Traitement et Enrichissement**
- Parsing des données GeoJSON
- Calcul de distances et surfaces
- Enrichissement avec des APIs externes

### 5. **Affichage Cartographique**
- Intégration dans la carte Folium
- Popups dynamiques avec informations détaillées

## 📍 Exemples d'Usage Concret

### Recherche Multi-Couches
```python
@app.route('/point_info', methods=['POST'])
def point_info():
    data = request.get_json()
    lat, lon = data['lat'], data['lon']
    
    # Interrogation simultanée de plusieurs couches GeoServer
    parcelles = get_all_parcelles(lat, lon)
    postes = get_all_postes(lat, lon)
    plu = get_plu_info(lat, lon)
    capacites = get_all_capacites_reseau(lat, lon)
    
    # Assemblage des résultats
    return {
        'parcelles': parcelles,
        'infrastructure': postes,
        'urbanisme': plu,
        'capacites': capacites
    }
```

## 🚨 État Actuel du GeoServer

### ❌ **Problème Identifié**
Le GeoServer n'est actuellement **PAS actif** :
- Port 8080 fermé
- Service non accessible
- Aucune donnée disponible depuis GeoServer

### 💡 **Alternatives en Cours**
1. **Mode dégradé** : Utilisation d'APIs externes (cadastre.gouv.fr, etc.)
2. **Données statiques** : Fichiers GeoJSON locaux
3. **Mode démo** : Données factices pour les tests

## 🔄 Solutions pour Activer GeoServer

### Option 1 : Installation Locale
```bash
# Télécharger GeoServer
# Installer et configurer
# Importer les couches de données
# Démarrer le service sur port 8080
```

### Option 2 : GeoServer Docker
```bash
docker run -d -p 8080:8080 kartoza/geoserver
```

### Option 3 : GeoServer Cloud/Distant
- Configurer un serveur GeoServer externe
- Modifier l'URL dans la configuration

## 🎯 Impact sur AgriWeb 2.0

### **Avec GeoServer Actif**
- ✅ Données géospatiales complètes et précises
- ✅ Requêtes spatiales optimisées
- ✅ Couches vectorielles haute performance
- ✅ Analyses géographiques avancées

### **Sans GeoServer (État Actuel)**
- ⚠️ Fonctionnalités limitées aux APIs externes
- ⚠️ Pas d'accès aux données spécialisées (PLU, friches, etc.)
- ⚠️ Mode dégradé pour l'infrastructure électrique
- ⚠️ Analyses spatiales réduites

## 📋 Recommandations

1. **Installation GeoServer** : Priorité pour accès aux données complètes
2. **Import des couches** : Charger toutes les couches définies
3. **Tests de connectivité** : Valider l'accès à chaque couche
4. **Monitoring** : Surveiller les performances GeoServer
5. **Backup** : Sauvegarder les configurations et données

---

*Cette analyse montre que GeoServer est le cœur du système de données géospatiales d'AgriWeb 2.0, mais nécessite une activation pour un fonctionnement optimal.*
