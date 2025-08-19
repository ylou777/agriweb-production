# 🌐 GUIDE COMPLET : CONFIGURATION GEOSERVER POUR AGRIWEB 2.0

## 🎯 **OBJECTIF**

Configurer votre GeoServer pour intégrer toutes vos couches géographiques avec AgriWeb 2.0 et le système de licences.

---

## 📋 **ANALYSE DE VOS COUCHES EXISTANTES**

D'après votre code, vous utilisez ces couches GeoServer :

| 🗂️ **Couche** | 🏷️ **Nom GeoServer** | 📊 **Usage** |
|---------------|------------------------|---------------|
| **Cadastre** | `gpu:prefixes_sections` | Références cadastrales |
| **Postes BT** | `gpu:poste_elec_shapefile` | Postes électriques BT |
| **Postes HTA** | `gpu:postes-electriques-rte` | Postes électriques HTA |
| **Capacités réseau** | `gpu:CapacitesDAccueil` | Capacités d'accueil électrique |
| **Parkings** | `gpu:parkings_sup500m2` | Parkings > 500m² |
| **Friches** | `gpu:friches-standard` | Friches industrielles |
| **Potentiel solaire** | `gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93` | Potentiel solaire friches |
| **ZAER** | `gpu:ZAER_ARRETE_SHP_FRA` | Zones à enjeux environnementaux |
| **RPG** | `gpu:PARCELLES_GRAPHIQUES` | Registre parcellaire graphique |
| **Sirène** | `gpu:GeolocalisationEtablissement_Sirene france` | Établissements Sirène |
| **PLU** | `gpu:gpu1` | Plan local d'urbanisme |
| **Parcelles** | `gpu:PARCELLE2024` | Parcelles cadastrales 2024 |
| **Éleveurs** | `gpu:etablissements_eleveurs` | Établissements d'élevage |
| **PPRI** | `gpu:ppri` | Plans de prévention risques inondation |

---

## 🔧 **1. VÉRIFICATION DE VOTRE GEOSERVER**

### **1.1 Test de connexion**

```bash
# Test simple de connexion
curl "http://localhost:8080/geoserver/ows?service=WFS&version=1.0.0&request=GetCapabilities"
```

### **1.2 Vérification des couches**

```python
import requests

def test_geoserver_layers():
    """Test de toutes vos couches GeoServer"""
    
    GEOSERVER_URL = "http://localhost:8080/geoserver"
    
    # Liste de toutes vos couches
    layers = {
        "Cadastre": "gpu:prefixes_sections",
        "Postes BT": "gpu:poste_elec_shapefile", 
        "Postes HTA": "gpu:postes-electriques-rte",
        "Capacités": "gpu:CapacitesDAccueil",
        "Parkings": "gpu:parkings_sup500m2",
        "Friches": "gpu:friches-standard",
        "Potentiel solaire": "gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93",
        "ZAER": "gpu:ZAER_ARRETE_SHP_FRA",
        "RPG": "gpu:PARCELLES_GRAPHIQUES",
        "Sirène": "gpu:GeolocalisationEtablissement_Sirene france",
        "PLU": "gpu:gpu1",
        "Parcelles": "gpu:PARCELLE2024",
        "Éleveurs": "gpu:etablissements_eleveurs",
        "PPRI": "gpu:ppri"
    }
    
    print("🔍 Test des couches GeoServer...")
    
    for nom, layer in layers.items():
        url = f"{GEOSERVER_URL}/ows"
        params = {
            "service": "WFS",
            "version": "1.0.0", 
            "request": "GetFeature",
            "typeName": layer,
            "maxFeatures": 1,
            "outputFormat": "application/json"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('features', []))
                print(f"  ✅ {nom} ({layer}) : {count} feature(s)")
            else:
                print(f"  ❌ {nom} ({layer}) : Erreur {response.status_code}")
        except Exception as e:
            print(f"  🚨 {nom} ({layer}) : {str(e)}")

if __name__ == "__main__":
    test_geoserver_layers()
```

---

## 🏗️ **2. CONFIGURATION GEOSERVER PRODUCTION**

### **2.1 Structure des espaces de travail (Workspaces)**

```xml
<!-- Workspace GPU principal -->
<workspace>
    <name>gpu</name>
    <dataStores>
        <!-- Vos stores de données existants -->
    </dataStores>
</workspace>
```

### **2.2 Configuration des stores de données**

Pour chaque type de données, configurez les stores appropriés :

```xml
<!-- Store PostGIS (recommandé pour la production) -->
<dataStore>
    <name>gpu_postgis</name>
    <type>PostGIS</type>
    <connectionParameters>
        <host>localhost</host>
        <port>5432</port>
        <database>agriweb_geo</database>
        <user>agriweb_user</user>
        <passwd>password_secure</passwd>
    </connectionParameters>
</dataStore>
```

---

## 🔐 **3. SÉCURISATION PAR LICENCE**

### **3.1 Règles de sécurité selon le type de licence**

```python
# Intégration dans votre production_system.py

class GeoServerSecurityManager:
    """Gestionnaire de sécurité GeoServer selon les licences"""
    
    def __init__(self):
        self.layer_permissions = {
            "trial": {
                "allowed_layers": [
                    "gpu:prefixes_sections",
                    "gpu:poste_elec_shapefile", 
                    "gpu:PARCELLES_GRAPHIQUES"
                ],
                "max_features": 100,
                "rate_limit": 30  # requêtes/minute
            },
            "basic": {
                "allowed_layers": [
                    "gpu:prefixes_sections",
                    "gpu:poste_elec_shapefile",
                    "gpu:postes-electriques-rte", 
                    "gpu:CapacitesDAccueil",
                    "gpu:parkings_sup500m2",
                    "gpu:PARCELLES_GRAPHIQUES",
                    "gpu:gpu1"
                ],
                "max_features": 1000,
                "rate_limit": 100
            },
            "pro": {
                "allowed_layers": "all",
                "max_features": 10000,
                "rate_limit": 500
            },
            "enterprise": {
                "allowed_layers": "all", 
                "max_features": "unlimited",
                "rate_limit": "unlimited"
            }
        }
    
    def can_access_layer(self, license_type, layer_name):
        """Vérifie si une licence peut accéder à une couche"""
        perms = self.layer_permissions.get(license_type, {})
        allowed = perms.get("allowed_layers", [])
        
        if allowed == "all":
            return True
        return layer_name in allowed
    
    def get_max_features(self, license_type):
        """Retourne le nombre max de features selon la licence"""
        perms = self.layer_permissions.get(license_type, {})
        return perms.get("max_features", 10)
```

---

## 📡 **4. AMÉLIORATION DE LA FONCTION WFS**

### **4.1 Fonction WFS améliorée avec gestion des licences**

```python
def fetch_wfs_data_secured(layer_name, bbox, license_info=None):
    """
    Fetch WFS data avec contrôle de licence et optimisations
    """
    
    if license_info:
        security_manager = GeoServerSecurityManager()
        
        # Vérifier l'accès à la couche
        if not security_manager.can_access_layer(license_info["license_type"], layer_name):
            raise PermissionError(f"Accès refusé à la couche {layer_name} pour licence {license_info['license_type']}")
        
        # Limite de features selon la licence
        max_features = security_manager.get_max_features(license_info["license_type"])
    else:
        max_features = 10  # Mode démo très limité
    
    url = f"{GEOSERVER_URL}/ows"
    
    # Conversion bbox au format WFS
    if isinstance(bbox, list) and len(bbox) == 4:
        bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"
    else:
        bbox_str = None
    
    params = {
        "service": "WFS",
        "version": "2.0.0",  # Version plus récente
        "request": "GetFeature", 
        "typeName": layer_name,
        "outputFormat": "application/json",
        "maxFeatures": max_features
    }
    
    if bbox_str:
        params["bbox"] = bbox_str
    
    # Headers pour optimisation
    headers = {
        "Accept": "application/json",
        "User-Agent": "AgriWeb2.0/1.0"
    }
    
    try:
        print(f"🌐 Requête WFS: {layer_name} (max: {max_features} features)")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            
            print(f"✅ {len(features)} features récupérées de {layer_name}")
            return features
        else:
            print(f"❌ Erreur WFS {response.status_code}: {response.text}")
            return []
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout WFS pour {layer_name}")
        return []
    except Exception as e:
        print(f"🚨 Erreur WFS {layer_name}: {str(e)}")
        return []
```

---

## 🚀 **5. OPTIMISATIONS PERFORMANCE**

### **5.1 Cache et indexation**

```python
import functools
import time
from threading import Lock

class GeoServerCache:
    """Cache intelligent pour les requêtes WFS"""
    
    def __init__(self, ttl=300):  # 5 minutes
        self.cache = {}
        self.ttl = ttl
        self.lock = Lock()
    
    def get_cache_key(self, layer, bbox, max_features):
        """Génère une clé de cache unique"""
        bbox_str = ",".join(map(str, bbox)) if bbox else "nobbox"
        return f"{layer}_{bbox_str}_{max_features}"
    
    def get(self, key):
        """Récupère depuis le cache si valide"""
        with self.lock:
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    print(f"📋 Cache HIT: {key}")
                    return data
                else:
                    del self.cache[key]
        return None
    
    def set(self, key, data):
        """Stocke en cache"""
        with self.lock:
            self.cache[key] = (data, time.time())
            print(f"💾 Cache SET: {key}")

# Instance globale du cache
geoserver_cache = GeoServerCache()

@functools.lru_cache(maxsize=100)
def fetch_wfs_cached(layer_name, bbox_tuple, max_features):
    """Version mise en cache de fetch_wfs_data"""
    bbox = list(bbox_tuple) if bbox_tuple else None
    return fetch_wfs_data_secured(layer_name, bbox, None)
```

---

## 🔧 **6. SCRIPTS DE CONFIGURATION AUTOMATIQUE**

### **6.1 Script de vérification complète**

```python
#!/usr/bin/env python3
"""
Script de diagnostic et configuration GeoServer pour AgriWeb 2.0
"""

import requests
import json
from datetime import datetime

def diagnose_geoserver():
    """Diagnostic complet de votre GeoServer"""
    
    print("🔍 DIAGNOSTIC GEOSERVER AGRIWEB 2.0")
    print("=" * 60)
    
    GEOSERVER_URL = "http://localhost:8080/geoserver"
    
    # 1. Test de connexion
    print("\n1️⃣ Test de connexion...")
    try:
        response = requests.get(f"{GEOSERVER_URL}/rest/about/version.json", timeout=10)
        if response.status_code == 200:
            version_info = response.json()
            print(f"  ✅ GeoServer connecté")
            print(f"  📊 Version: {version_info.get('about', {}).get('resource', [{}])[0].get('Version', 'Inconnue')}")
        else:
            print(f"  ❌ Erreur de connexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"  🚨 Impossible de se connecter: {e}")
        return False
    
    # 2. Test des workspaces
    print("\n2️⃣ Vérification des workspaces...")
    try:
        response = requests.get(f"{GEOSERVER_URL}/rest/workspaces.json")
        if response.status_code == 200:
            workspaces = response.json().get("workspaces", {}).get("workspace", [])
            workspace_names = [ws["name"] for ws in workspaces]
            print(f"  📁 Workspaces trouvés: {', '.join(workspace_names)}")
            
            if "gpu" in workspace_names:
                print("  ✅ Workspace 'gpu' détecté")
            else:
                print("  ⚠️ Workspace 'gpu' manquant - à créer")
        else:
            print(f"  ❌ Erreur workspaces: {response.status_code}")
    except Exception as e:
        print(f"  🚨 Erreur workspaces: {e}")
    
    # 3. Test des couches critiques
    print("\n3️⃣ Test des couches critiques...")
    
    critical_layers = [
        ("Cadastre", "gpu:prefixes_sections"),
        ("Postes BT", "gpu:poste_elec_shapefile"),
        ("RPG", "gpu:PARCELLES_GRAPHIQUES")
    ]
    
    working_layers = 0
    for nom, layer in critical_layers:
        if test_single_layer(GEOSERVER_URL, nom, layer):
            working_layers += 1
    
    print(f"\n📊 Résumé: {working_layers}/{len(critical_layers)} couches critiques fonctionnelles")
    
    return working_layers > 0

def test_single_layer(geoserver_url, nom, layer_name):
    """Test d'une couche spécifique"""
    url = f"{geoserver_url}/ows"
    params = {
        "service": "WFS",
        "version": "1.0.0",
        "request": "GetFeature", 
        "typeName": layer_name,
        "maxFeatures": 1,
        "outputFormat": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            feature_count = len(data.get("features", []))
            print(f"  ✅ {nom}: {feature_count} feature(s)")
            return True
        else:
            print(f"  ❌ {nom}: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  🚨 {nom}: {str(e)}")
        return False

if __name__ == "__main__":
    success = diagnose_geoserver()
    if success:
        print("\n🎉 GeoServer prêt pour AgriWeb 2.0!")
    else:
        print("\n⚠️ Configuration GeoServer requise")
```

---

## 📋 **7. CHECKLIST DE CONFIGURATION**

### **✅ À faire avant la production :**

- [ ] **1. Vérifier toutes les couches** avec le script de diagnostic
- [ ] **2. Configurer les permissions** selon les types de licence  
- [ ] **3. Optimiser les index** sur les géométries (PostGIS)
- [ ] **4. Activer la mise en cache** GeoServer (GeoWebCache)
- [ ] **5. Configurer la sécurité** (authentification si nécessaire)
- [ ] **6. Tester les performances** avec des requêtes réelles
- [ ] **7. Backup de la configuration** GeoServer

### **🚨 Points critiques :**

1. **Projection EPSG:4326** → Assurez-vous que toutes vos couches sont en WGS84
2. **Index spatiaux** → Créez des index sur les colonnes géométriques 
3. **Limites de mémoire** → Configurez JVM avec assez de RAM
4. **Timeout réseau** → Augmentez les timeouts pour les grosses requêtes

---

## 🎯 **CONCLUSION**

Votre GeoServer contient **14 couches critiques** pour AgriWeb 2.0. Avec cette configuration :

- ✅ **Toutes vos couches seront intégrées** au système de licences
- ✅ **Performance optimisée** avec cache et limitations 
- ✅ **Sécurité par licence** (trial/basic/pro/enterprise)
- ✅ **Monitoring et diagnostic** automatiques

**Prochaine étape :** Lancez le script de diagnostic pour identifier les ajustements nécessaires !

---

*Guide généré pour AgriWeb 2.0 - Configuration GeoServer Production*
