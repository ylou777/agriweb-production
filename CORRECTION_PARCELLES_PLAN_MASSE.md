# 🔧 Correction - Parcelles cadastrales dans le plan de masse

## 📋 Problème identifié

Lorsqu'un prospect est créé à partir d'un **rapport par point** (`/rapport_map`), les parcelles cadastrales ne s'affichent **PAS** sur le plan de masse. En revanche, cela fonctionne correctement pour les prospects issus du **rapport commune** (`/rapport_commune_complet`).

### Cause racine

Le générateur de plan de masse (`plan_masse_generator.py`) cherche les parcelles cadastrales dans les champs suivants de `prospect_data` :
```python
for field in ['parcelles_cadastrales', 'parcelles', 'cadastre', 'data_json']:
```

**Dans le rapport par point :**
- L'API Cadastre IGN était appelée via `get_api_cadastre_data(point_geojson)`
- Les données étaient stockées dans `report_data["api_cadastre"]`
- ❌ Mais **PAS dans `report_data["parcelles_cadastrales"]`**
- Résultat : le plan de masse ne trouvait aucune parcelle à afficher

**Dans le rapport commune :**
- Les parcelles cadastrales étaient correctement formatées dans le champ `parcelles_cadastrales`
- ✅ Le plan de masse pouvait les trouver et les afficher

## ✅ Solution implémentée

### Fichier modifié : `agriweb_railway_deploy.py`

**Ligne ~5860** - Dans la fonction `collect_context_data()` du rapport par point :

Ajout du formatage des parcelles cadastrales après l'appel à l'API Cadastre :

```python
# 🔧 CORRECTION PLAN DE MASSE: Formater les parcelles cadastrales pour le générateur de plan
parcelles_cadastrales = []
for feat in cadastre_data.get('features', []):
    feat_props = feat.get('properties', {})
    feat_geom = feat.get('geometry', {})
    
    parcelle_formatted = {
        "section": feat_props.get('section', ''),
        "numero": feat_props.get('numero', ''),
        "surface": feat_props.get('contenance', 0),  # Surface en m²
        "commune": feat_props.get('nom_com', ''),
        "code_insee": feat_props.get('code_insee', ''),
        "geometry": feat_geom,  # Géométrie GeoJSON complète
        "geojson": feat  # Feature GeoJSON complet
    }
    parcelles_cadastrales.append(parcelle_formatted)

# Stocker dans le champ que le plan de masse cherche
report_data["parcelles_cadastrales"] = parcelles_cadastrales
```

### Ce que fait cette correction :

1. **Extraction** : Récupère toutes les features (parcelles) retournées par l'API Cadastre
2. **Formatage** : Transforme chaque feature en un dictionnaire avec les champs attendus par le plan de masse :
   - `section` : Section cadastrale (ex: "AB")
   - `numero` : Numéro de parcelle (ex: "123")
   - `surface` : Surface en m² (contenance)
   - `commune`, `code_insee` : Informations de localisation
   - `geometry` : Géométrie GeoJSON pour dessiner la parcelle
   - `geojson` : Feature GeoJSON complet pour enrichissement ultérieur
3. **Stockage** : Place les parcelles formatées dans `report_data["parcelles_cadastrales"]`

### Impact sur le plan de masse

Le générateur de plan de masse (`plan_masse_generator.py`) pourra maintenant :

1. ✅ **Trouver les parcelles** dans le champ `parcelles_cadastrales`
2. ✅ **Dessiner les contours** à partir de la géométrie GeoJSON réelle
3. ✅ **Afficher les étiquettes** avec section, numéro et surface
4. ✅ **Appeler l'API Cadastre Apicarto** pour enrichir avec les géométries précises si nécessaire

## 🧪 Tests à effectuer

### Test 1 : Plan de masse depuis rapport par point

1. Générer un rapport par point (cliquer sur la carte)
2. Dans le rapport, cliquer sur "Exporter vers CRM"
3. Créer le prospect
4. Ouvrir le prospect dans le CRM
5. Faire un calpinage (placer des modules PV)
6. Générer le plan de masse PDF
7. ✅ **Vérifier** : Les parcelles cadastrales doivent apparaître avec leurs contours réels

### Test 2 : Plan de masse depuis rapport commune

1. Générer un rapport commune
2. Sélectionner un parking/toiture/friche
3. Exporter vers CRM
4. Faire un calpinage
5. Générer le plan de masse
6. ✅ **Vérifier** : Les parcelles doivent toujours s'afficher (régression)

## 📊 Données transmises

### Avant la correction

```json
{
  "api_cadastre": {
    "type": "FeatureCollection",
    "features": [...]
  }
  // ❌ parcelles_cadastrales: ABSENT
}
```

### Après la correction

```json
{
  "api_cadastre": {
    "type": "FeatureCollection",
    "features": [...]
  },
  "parcelles_cadastrales": [
    {
      "section": "AB",
      "numero": "123",
      "surface": 5420,
      "commune": "Example",
      "code_insee": "12345",
      "geometry": { "type": "Polygon", "coordinates": [...] },
      "geojson": { "type": "Feature", ... }
    }
  ]
}
```

## 🔍 Code concerné

### Fichiers impliqués

1. **`agriweb_railway_deploy.py`** (ligne ~5860) 
   - Fonction : `collect_context_data()` dans `rapport_map_point()`
   - Modification : Ajout du formatage des parcelles cadastrales

2. **`plan_masse_generator.py`** (ligne ~1108)
   - Fonction : `_extract_parcelles()`
   - Cherche dans : `['parcelles_cadastrales', 'parcelles', 'cadastre', 'data_json']`
   - Utilisation : Dessine les parcelles sur le plan PDF

3. **`templates/rapport_point.html`** (ligne ~1644)
   - Export CRM : Envoie `report.parcelles_cadastrales` dans le data_json
   - Fonctionnait déjà correctement, mais n'avait pas de données à envoyer

### API utilisée

**API Cadastre IGN Apicarto**
- Endpoint : `https://apicarto.ign.fr/api/cadastre/parcelle`
- Paramètre : `geom` (GeoJSON Point)
- Retour : GeoJSON FeatureCollection avec parcelles cadastrales et géométries

## 📝 Notes techniques

### Format de parcelle attendu par le plan de masse

```python
{
    "section": str,      # Section cadastrale
    "numero": str,       # Numéro de parcelle
    "surface": float,    # Surface en m²
    "geometry": dict,    # GeoJSON Geometry (Polygon/MultiPolygon)
    "geojson": dict      # GeoJSON Feature complet (optionnel)
}
```

### Enrichissement automatique

Si une parcelle n'a pas de géométrie, le plan de masse peut :
1. Dessiner un rectangle approximatif basé sur la surface
2. Appeler l'API Cadastre Apicarto pour récupérer la géométrie réelle

Grâce à cette correction, les parcelles ont déjà leur géométrie dès le rapport, donc pas besoin d'appel supplémentaire.

## ✅ Résultat attendu

Après cette correction, les plans de masse générés depuis un prospect issu d'un **rapport par point** doivent afficher :

1. ✅ Les contours précis des parcelles cadastrales
2. ✅ Les étiquettes avec section + numéro
3. ✅ La surface en m² de chaque parcelle
4. ✅ Les modules PV positionnés sur les parcelles
5. ✅ Les cotations et légendes
6. ✅ Une rose des vents et l'échelle 1/500

---

**Date de correction** : 2026-01-24
**Fichiers modifiés** : `agriweb_railway_deploy.py`
**Impact** : ✅ Résolution du problème d'affichage des parcelles cadastrales
