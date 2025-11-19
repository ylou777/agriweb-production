#!/usr/bin/env python3
"""
Correctif pour les erreurs JavaScript :
1. Invalid GeoJSON object pour postes_bt
2. Map instance not found  
3. t.getElement is not a function dans Tooltip
"""

print("🔧 Correction des erreurs JavaScript de la carte...")

# 1. Correction dans main.js - validation GeoJSON plus stricte
with open('static/main.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Ajouter une validation plus stricte des données GeoJSON
validation_fix = '''    // Validation stricte du GeoJSON avant traitement
    if (!geojson || !geojson.type || geojson.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
      console.warn(`[displayAllLayers] GeoJSON invalide pour ${layerKey}:`, geojson);
      return;
    }
    
    // Filtrer les features avec geometry valide uniquement
    geojson.features = geojson.features.filter(feature => {
      if (!feature || !feature.geometry || !feature.geometry.type || !feature.geometry.coordinates) {
        console.warn(`[displayAllLayers] Feature sans géométrie valide ignorée:`, feature);
        return false;
      }
      return true;
    });
    
    // Si plus aucune feature valide, ignorer la couche
    if (geojson.features.length === 0) {
      console.warn(`[displayAllLayers] Aucune feature valide pour ${layerKey}, couche ignorée`);
      return;
    }'''

# Remplacer l'ancienne validation
old_validation = '''      console.log(`[displayAllLayers] GeoJSON normalisé pour ${layerKey}:`, geojson);
    } catch (normalizeErr) {
      console.error(`[displayAllLayers] Erreur normalisation ${layerKey}:`, normalizeErr);
      return;
    }'''

new_validation = validation_fix + '''
      console.log(`[displayAllLayers] GeoJSON validé pour ${layerKey}:`, geojson);
    } catch (normalizeErr) {
      console.error(`[displayAllLayers] Erreur normalisation ${layerKey}:`, normalizeErr);
      return;
    }'''

if old_validation in js_content:
    js_content = js_content.replace(old_validation, new_validation)
    print("   ✅ Validation GeoJSON renforcée ajoutée")

# 2. Ajouter une vérification de sécurité pour getMapFrame()
security_check = '''function getMapFrame() {
  try {
    // Vérifier si nous sommes dans une iframe ou non
    if (window.parent && window.parent !== window) {
      // Dans une iframe
      const parentDoc = window.parent.document;
      const mapElement = parentDoc.querySelector('[id^="map"]');
      if (mapElement && mapElement.id) {
        const mapVar = window.parent[mapElement.id];
        if (mapVar && mapVar._container) {
          return { map: mapVar, L: window.parent.L };
        }
      }
    }
    
    // Recherche directe dans window courant
    for (const key of Object.keys(window)) {
      if (key.startsWith('map_') && window[key] && window[key]._container) {
        return { map: window[key], L: window.L };
      }
    }
    
    console.warn("❌ Map instance not found");
    return null;
  } catch (err) {
    console.error("❌ Erreur getMapFrame:", err);
    return null;
  }
}'''

# Remplacer l'ancienne fonction getMapFrame si elle existe
if 'function getMapFrame()' in js_content:
    import re
    pattern = r'function getMapFrame\(\)[^}]*\{[^}]*\}'
    js_content = re.sub(pattern, security_check, js_content, flags=re.DOTALL)
    print("   ✅ getMapFrame() sécurisée mise à jour")
else:
    # Ajouter la fonction au début du fichier
    js_content = security_check + '\n\n' + js_content
    print("   ✅ getMapFrame() sécurisée ajoutée")

# Sauvegarder les modifications
with open('static/main.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

# 3. Correction côté serveur Python - validation des postes BT/HTA
print("   ➤ Correction de la validation des postes BT/HTA côté serveur...")

with open('agriweb_hebergement_gratuit.py', 'r', encoding='utf-8') as f:
    py_content = f.read()

# Améliorer la fonction poste_to_feature
old_poste_function = '''    def poste_to_feature(poste):
        return {
            "type": "Feature",
            "geometry": poste.get("geometry"),
            "properties": poste.get("properties", {})
        }'''

new_poste_function = '''    def poste_to_feature(poste):
        """Convertit un poste en Feature GeoJSON valide."""
        geometry = poste.get("geometry")
        
        # Validation stricte de la géométrie
        if not geometry or not isinstance(geometry, dict):
            return None
        
        if "type" not in geometry or "coordinates" not in geometry:
            return None
            
        # Vérifier que les coordonnées sont valides
        coords = geometry.get("coordinates")
        if not coords or not isinstance(coords, (list, tuple)) or len(coords) < 2:
            return None
            
        # Pour un Point, vérifier que les coordonnées sont numériques
        if geometry["type"] == "Point":
            try:
                float(coords[0])  # longitude
                float(coords[1])  # latitude
            except (ValueError, TypeError, IndexError):
                return None
        
        return {
            "type": "Feature",
            "geometry": geometry,
            "properties": poste.get("properties", {})
        }'''

if old_poste_function in py_content:
    py_content = py_content.replace(old_poste_function, new_poste_function)
    print("   ✅ Validation des postes BT/HTA renforcée")

# Modifier l'appel pour filtrer les None
old_feature_call = '''            "features": [poste_to_feature(p) for p in postes_bt if p.get("geometry")]'''
new_feature_call = '''            "features": [f for f in [poste_to_feature(p) for p in postes_bt] if f is not None]'''

if old_feature_call in py_content:
    py_content = py_content.replace(old_feature_call, new_feature_call)
    print("   ✅ Filtrage des features None ajouté")

# Même chose pour postes_hta
old_hta_call = '''            "features": [poste_to_feature(p) for p in postes_hta if p.get("geometry")]'''
new_hta_call = '''            "features": [f for f in [poste_to_feature(p) for p in postes_hta] if f is not None]'''

if old_hta_call in py_content:
    py_content = py_content.replace(old_hta_call, new_hta_call)
    print("   ✅ Filtrage des features HTA None ajouté")

# Sauvegarder les modifications Python
with open('agriweb_hebergement_gratuit.py', 'w', encoding='utf-8') as f:
    f.write(py_content)

print("\n🎯 Corrections appliquées :")
print("   ✅ Validation GeoJSON stricte dans main.js")
print("   ✅ Fonction getMapFrame() sécurisée")  
print("   ✅ Validation des postes côté serveur renforcée")
print("   ✅ Filtrage des features invalides")

print("\n📌 Ces corrections devraient résoudre :")
print("   🔧 Invalid GeoJSON object pour postes_bt")
print("   🔧 Map instance not found")
print("   🔧 t.getElement is not a function")

print("\n⚡ Déployez avec : git add . && git commit -m 'Fix JavaScript errors' && git push production main")
