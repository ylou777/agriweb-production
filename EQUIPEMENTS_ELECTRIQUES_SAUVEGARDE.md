# Sauvegarde et Restauration des Équipements Électriques

## ✅ Fonctionnalité Implémentée

La configuration électrique (onduleurs, TGBT, point d'injection) est maintenant **sauvegardée et restaurée automatiquement** avec le calepinage, comme l'implantation des modules.

## 📋 Données Sauvegardées

### 1. Équipements Électriques
```javascript
equipments: {
    onduleurs: [
        { num: 1, lat: 48.8566, lng: 2.3522 },
        { num: 2, lat: 48.8567, lng: 2.3523 }
    ],
    tgbt: { lat: 48.8568, lng: 2.3524 },
    injection: { lat: 48.8569, lng: 2.3525 }
}
```

### 2. Distances Calculées (NF C 15-712)
```javascript
distances: {
    dc_strings: 25.5,              // Distance DC strings → onduleur (m)
    ac_onduleur_tgbt: 15.3,       // Distance AC onduleur → TGBT (m)
    ac_tgbt_injection: 10.8,      // Distance AC TGBT → injection (m)
    zones_detail: [...]            // Détail par zone (multi-zone)
}
```

## 🔧 Implémentation Technique

### Sauvegarde (prepareCalepinageData)
**Fichier** : `AgW3b/templates/calpinage_pv.html`  
**Lignes** : 3045-3115

La fonction `prepareCalepinageData()` collecte :
- Les zones avec leurs modules
- Les paramètres des modules PV
- **Les équipements électriques** (onduleurs, TGBT, injection)
- **Les distances calculées** entre équipements

```javascript
function prepareCalepinageData() {
    return {
        zones: [...],
        module: {...},
        totaux: {...},
        equipments: {
            onduleurs: equipments.onduleurs.map(ond => ({
                num: ond.num,
                lat: ond.marker.getLatLng().lat,
                lng: ond.marker.getLatLng().lng
            })),
            tgbt: equipments.tgbt ? {...} : null,
            injection: equipments.injection ? {...} : null
        },
        distances: window.cableDistances || {...}
    };
}
```

### Restauration (loadSavedCalpinage)
**Fichier** : `AgW3b/templates/calpinage_pv.html`  
**Lignes** : 3192-3327

Lors du chargement de la page, si un calepinage existe :
1. Restaure les zones PV avec modules
2. **Restaure les onduleurs** → `placeOnduleur(latlng)`
3. **Restaure le TGBT** → `placeTGBT(latlng)`
4. **Restaure le point d'injection** → `placeInjection(latlng)`
5. **Restaure les distances** → `window.cableDistances` + `updateDistanceDisplay()`

```javascript
// Restaurer les équipements électriques si sauvegardés
if (savedCalpinage.equipments) {
    // Onduleurs
    savedCalpinage.equipments.onduleurs?.forEach(ondData => {
        placeOnduleur(L.latLng(ondData.lat, ondData.lng));
    });
    
    // TGBT
    if (savedCalpinage.equipments.tgbt) {
        placeTGBT(L.latLng(savedCalpinage.equipments.tgbt.lat, ...));
    }
    
    // Injection
    if (savedCalpinage.equipments.injection) {
        placeInjection(L.latLng(savedCalpinage.equipments.injection.lat, ...));
    }
    
    // Distances
    if (savedCalpinage.distances) {
        window.cableDistances = savedCalpinage.distances;
        updateDistanceDisplay();
    }
}
```

## 🎯 Utilisation

### Workflow Normal
1. **Dessiner les zones PV** sur la carte
2. **Placer les équipements** :
   - Cliquer sur "⚡ Onduleur" puis sur la carte
   - Cliquer sur "🔌 TGBT" puis sur la carte  
   - Cliquer sur "🔗 Injection" puis sur la carte
3. **Les distances sont calculées automatiquement** (GPS)
4. **Sauvegarder le calepinage** → Bouton "💾 Sauvegarder Calpinage"
5. **Fermer et rouvrir la page** → Tous les équipements sont restaurés ! ✅

### Vérification
- Les marqueurs réapparaissent aux mêmes positions
- Les distances s'affichent automatiquement
- Le panneau "📏 Distances câbles" affiche les valeurs sauvegardées
- Les équipements sont draggables pour ajustement

## 📊 Données Stockées dans PostgreSQL

**Table** : `prospects`  
**Colonne** : `data_json -> calpinage`

Structure JSON complète :
```json
{
    "zones": [...],
    "module": {...},
    "totaux": {...},
    "equipments": {
        "onduleurs": [{"num": 1, "lat": 48.856, "lng": 2.352}],
        "tgbt": {"lat": 48.857, "lng": 2.353},
        "injection": {"lat": 48.858, "lng": 2.354}
    },
    "distances": {
        "dc_strings": 25.5,
        "ac_onduleur_tgbt": 15.3,
        "ac_tgbt_injection": 10.8,
        "zones_detail": [...]
    }
}
```

## 🔄 Algorithme de Calcul des Distances

### Multi-zone / Multi-onduleur
**Fichier** : `calpinage_pv.html`  
**Fonction** : `updateCableDistances()`  
**Lignes** : 1873-1990

Logique intelligente :
- **Attribution par proximité** : Chaque zone PV → onduleur le plus proche
- **Moyenne pondérée** : Distance DC = moyenne pondérée par puissance de chaque zone
- **Distance max AC** : TGBT placé pour desservir tous les onduleurs
- **Respect NF C 15-712** : Calculs pour chute de tension 2% max

## ✨ Avantages

✅ **Persistance complète** : Comme l'implantation modules  
✅ **Reprise de travail** : Pas besoin de replacer les équipements  
✅ **Distances pré-calculées** : Sections câbles instantanées  
✅ **Multi-onduleur** : Gère plusieurs onduleurs automatiquement  
✅ **Modification facile** : Équipements draggables après restauration  
✅ **Schéma unifilaire** : Distances réelles dans le PDF NF C 15-712  

## 📝 Logs Console

Au chargement d'un calepinage sauvegardé :
```
Chargement du calpinage sauvegardé: {...}
3 zone(s) chargée(s) depuis la sauvegarde
🔌 Restauration des équipements électriques...
✅ 2 onduleur(s) restauré(s)
✅ TGBT restauré
✅ Point d'injection restauré
✅ Distances câbles restaurées: {dc_strings: 25.5, ...}
```

## 🐛 Résolution de Problème

Si les équipements ne se restaurent pas :
1. Vérifier que le calepinage a été sauvegardé (bouton 💾)
2. Vérifier la console navigateur (F12)
3. Vérifier que `savedCalpinage.equipments` existe
4. Vérifier que les fonctions `placeOnduleur()`, `placeTGBT()`, `placeInjection()` existent

## 📅 Historique

- **Version initiale** : Équipements non sauvegardés
- **Commit actuel** : Sauvegarde et restauration complètes
  - `prepareCalepinageData()` : déjà incluait equipments + distances
  - `loadSavedCalpinage()` : ajout restauration equipments + distances
  - `updateDistanceDisplay()` : nouvelle fonction pour affichage restauré

---
**Auteur** : GitHub Copilot  
**Standard** : NF C 15-712-1 (Installations photovoltaïques raccordées au réseau)  
**Date** : 2025  
