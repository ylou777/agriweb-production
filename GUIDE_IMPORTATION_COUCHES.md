# 🗂️ GUIDE COMPLET IMPORTATION COUCHES GEOSERVER

## 🎉 GEOSERVER FONCTIONNEL !
- **Interface :** https://geoserver-agriweb-production.up.railway.app/geoserver/web/
- **Identifiants :** admin / admin
- **Workspace GPU :** Créé et prêt

## 📊 COUCHES À IMPORTER (14 couches)

### 1️⃣ COUCHES CADASTRALES (3 couches)
```
Workspace: gpu
Nom des couches:
- gpu:prefixes_sections
- gpu:PARCELLE2024
- gpu:gpu1 (PLU)

Format recommandé: Shapefile (.shp) ou PostGIS
```

### 2️⃣ COUCHES ÉNERGÉTIQUES (3 couches)
```
Workspace: gpu
Nom des couches:
- gpu:poste_elec_shapefile
- gpu:postes-electriques-rte
- gpu:CapacitesDAccueil

Format recommandé: Shapefile (.shp)
```

### 3️⃣ COUCHES AGRICOLES (2 couches)
```
Workspace: gpu
Nom des couches:
- gpu:PARCELLES_GRAPHIQUES (RPG)
- gpu:etablissements_eleveurs

Format recommandé: Shapefile (.shp)
```

### 4️⃣ COUCHES COMMERCIALES (1 couche)
```
Workspace: gpu
Nom des couches:
- gpu:GeolocalisationEtablissement_Sirene (très long nom!)

Format recommandé: Shapefile (.shp) ou CSV géocodé
```

### 5️⃣ COUCHES TERRAIN (3 couches)
```
Workspace: gpu
Nom des couches:
- gpu:parkings_sup500m2
- gpu:friches-standard
- gpu:POTENTIEL_SOLAIRE_FRICHE_BDD_PSF_LAMB93

Format recommandé: Shapefile (.shp)
```

### 6️⃣ COUCHES RÉGLEMENTAIRES (2 couches)
```
Workspace: gpu
Nom des couches:
- gpu:ZAER_ARRETE_SHP_FRA
- gpu:ppri

Format recommandé: Shapefile (.shp)
```

## 🚀 PROCÉDURE D'IMPORTATION

### Méthode 1: Via l'interface web GeoServer
1. **Aller sur :** https://geoserver-agriweb-production.up.railway.app/geoserver/web/
2. **Se connecter :** admin / admin
3. **Workspace :** Sélectionner "gpu"
4. **Datastores :** Créer nouveau datastore
5. **Importer :** Fichiers Shapefile ou connexion PostGIS

### Méthode 2: Via API REST (recommandée)
```python
# Script d'importation automatique
python import_all_layers.py
```

### Méthode 3: Via GeoServer REST Upload
```bash
# Upload direct de fichiers ZIP contenant les Shapefiles
curl -u admin:admin -XPOST \
  "https://geoserver-agriweb-production.up.railway.app/geoserver/rest/workspaces/gpu/datastores/ma_couche/file.shp" \
  -H "Content-type: application/zip" \
  --data-binary @couche.zip
```

## 📋 CHECKLIST POST-IMPORTATION

### Pour chaque couche importée :
- [ ] **Nom correct :** gpu:nom_couche
- [ ] **SRS/CRS :** EPSG:2154 (Lambert 93) ou EPSG:4326 (WGS84)
- [ ] **Style par défaut :** Appliqué
- [ ] **Test WMS :** GetCapabilities et GetMap
- [ ] **Test WFS :** GetCapabilities et GetFeature
- [ ] **Métadonnées :** Titre, description, mots-clés

### URLs de test après importation :
```
WMS GetCapabilities:
https://geoserver-agriweb-production.up.railway.app/geoserver/wms?service=WMS&version=1.3.0&request=GetCapabilities

WFS GetCapabilities:
https://geoserver-agriweb-production.up.railway.app/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities

Test couche spécifique (exemple):
https://geoserver-agriweb-production.up.railway.app/geoserver/gpu/wms?service=WMS&version=1.1.0&request=GetMap&layers=gpu:PARCELLE2024&bbox=...&width=256&height=256&srs=EPSG:2154&format=image/png
```

## 🎨 STYLES RECOMMANDÉS

### Cadastre (vert)
```xml
<sld:PolygonSymbolizer>
  <sld:Fill>
    <sld:CssParameter name="fill">#90EE90</sld:CssParameter>
    <sld:CssParameter name="fill-opacity">0.7</sld:CssParameter>
  </sld:Fill>
  <sld:Stroke>
    <sld:CssParameter name="stroke">#228B22</sld:CssParameter>
    <sld:CssParameter name="stroke-width">1</sld:CssParameter>
  </sld:Stroke>
</sld:PolygonSymbolizer>
```

### Énergétique (jaune/orange)
```xml
<sld:PointSymbolizer>
  <sld:Graphic>
    <sld:Mark>
      <sld:WellKnownName>circle</sld:WellKnownName>
      <sld:Fill>
        <sld:CssParameter name="fill">#FFA500</sld:CssParameter>
      </sld:Fill>
    </sld:Mark>
    <sld:Size>8</sld:Size>
  </sld:Graphic>
</sld:PointSymbolizer>
```

### Agricole (brun)
```xml
<sld:PolygonSymbolizer>
  <sld:Fill>
    <sld:CssParameter name="fill">#DEB887</sld:CssParameter>
    <sld:CssParameter name="fill-opacity">0.6</sld:CssParameter>
  </sld:Fill>
</sld:PolygonSymbolizer>
```

## 🔗 INTÉGRATION AGRIWEB

Une fois toutes les couches importées, mettre à jour `agriweb_hebergement_gratuit.py` :

```python
# Configuration finale des couches
GEOSERVER_LAYERS_CONFIG = {
    "workspace": "gpu",
    "layers": {
        # Toutes les 14 couches seront listées ici
        "cadastre": "gpu:prefixes_sections",
        # ... etc
    },
    "endpoints": {
        "wfs": "https://geoserver-agriweb-production.up.railway.app/geoserver/ows",
        "wms": "https://geoserver-agriweb-production.up.railway.app/geoserver/wms",
        "admin": "https://geoserver-agriweb-production.up.railway.app/geoserver/web/"
    }
}
```

## ✅ VALIDATION FINALE

Test de toutes les couches :
```bash
python test_all_layers.py
```

**🎯 OBJECTIF : 14/14 couches fonctionnelles dans GeoServer !**
