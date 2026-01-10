# 📝 Guide d'Édition des Champs PV

## 🎯 Fonctionnalités de Manipulation Interactive

Lorsque vous cliquez sur le bouton **"✏️ Modifier"**, vous activez le mode d'édition complet qui vous permet de manipuler vos champs PV de trois façons différentes :

### 1. 🔲 Redimensionnement (Poignées aux coins)

**Comment l'utiliser :**
- En mode édition, des **poignées blanches avec bordure bleue** apparaissent aux 4 coins de chaque zone PV
- Cliquez et glissez n'importe quelle poignée pour redimensionner la zone
- Les modules sont recalculés automatiquement en temps réel
- Le productible et la surface sont mis à jour instantanément

**Indicateurs visuels :**
- Poignées : cercles blancs avec bordure bleue (#0d6efd)
- Au survol : la poignée grossit et devient bleue
- Curseur : `nwse-resize` (diagonal)

### 2. 🔄 Rotation (Poignée circulaire)

**Comment l'utiliser :**
- Une **poignée bleue circulaire** apparaît au-dessus de chaque zone
- Cliquez et glissez cette poignée pour faire pivoter le champ
- Une **ligne de guidage en pointillés** bleue s'affiche pendant la rotation
- L'orientation est mise à jour en temps réel dans le panneau de configuration
- Le slider d'orientation se synchronise automatiquement

**Indicateurs visuels :**
- Poignée : cercle bleu (#0d6efd) avec bordure blanche
- Au survol : grossit à 1.15x avec ombre portée
- Pendant le drag : grossit à 1.2x, curseur `grabbing`
- Ligne de guidage : pointillés bleus du centre vers la poignée
- Direction affichée : "180° (Sud)", "90° (Est)", etc.

**Astuce :**
- La rotation utilise le véritable système de coordonnées géographiques
- Les modules sont redessinés avec les vraies coordonnées tournées (pas de CSS transform)

### 3. ✋ Déplacement (Drag & Drop)

**Comment l'utiliser :**
- En mode édition, cliquez n'importe où sur la zone PV (pas sur les poignées)
- Maintenez le clic et glissez pour déplacer toute la zone
- Les modules et la poignée de rotation suivent en temps réel
- Relâchez pour finaliser le déplacement

**Indicateurs visuels :**
- Curseur au survol : `move`
- Pendant le drag : opacité réduite (0.7)
- Rectangle : bordure bleue en pointillés (5px, 5px)

## 🎨 Interface Utilisateur

### Badge Indicateur du Mode Édition

Quand le mode édition est actif, un **badge bleu flottant** apparaît en haut à droite :

```
✏️ Mode Édition Actif
🔲 Coins = Redimensionner | 🔄 Poignée = Rotation | ✋ Drag = Déplacer
```

**Position :** `fixed top: 80px, right: 20px`
**Style :** Fond bleu semi-transparent avec animation fadeIn

### Barre d'information

En bas de la barre d'outils, l'info contextuelle affiche :
```
✏️ Mode Édition - 🔲 Coins (redimensionner) | 🔄 Poignée (rotation) | ✋ Drag (déplacer)
```

### Style des Rectangles en Mode Édition

- **Couleur :** Bleu (#0d6efd)
- **Opacité bordure :** 0.7
- **Opacité remplissage :** 0.15
- **Épaisseur :** 3px
- **Style :** Pointillés (dashArray: 5, 5)

## 🔧 Fonctionnement Technique

### Initialisation du Mode Édition

```javascript
// Activation via Leaflet.draw EditToolbar
editHandler = new L.EditToolbar.Edit(map, {
    featureGroup: drawnItems,
    edit: {
        selectedPathOptions: {
            maintainColor: false,
            opacity: 0.5,
            fillOpacity: 0.2,
            color: '#0d6efd',
            dashArray: '5, 5'
        }
    }
});
editHandler.enable();
```

### Gestion du Dragging

Utilise `L.Handler.MarkerDrag` pour permettre le déplacement des rectangles :

```javascript
layer.dragging = new L.Handler.MarkerDrag(layer);
layer.dragging.enable();
```

**Events :**
- `dragstart` : Début du déplacement
- `drag` : Pendant le mouvement (redessine modules en temps réel)
- `dragend` : Fin du mouvement (sauvegarde nouveaux bounds)

### Poignée de Rotation Interactive

**Création :**
```javascript
rotationHandle = L.marker(handlePosition, {
    icon: L.divIcon({
        className: 'rotation-handle',
        html: '🔄',
        iconSize: [24, 24]
    }),
    draggable: true,
    zIndexOffset: 1000
});
```

**Calculs de rotation :**
- Utilise `Math.atan2()` pour calculer l'angle entre centre et poignée
- Convertit angle de rotation en orientation cardinale (0°=Nord, 90°=Est, etc.)
- Applique la rotation via `rotatePoint()` avec correction de distorsion lat/lng

## 📊 Mise à Jour Automatique

Toutes les modifications déclenchent automatiquement :

1. **Recalcul du nombre de modules** (`recalculerZone()`)
2. **Redessin des modules** (`dessinerModulesDansZone()`)
3. **Mise à jour de la surface** (calcul distance géographique)
4. **Recalcul du productible** (`calculerProductibleZone()`)
5. **Actualisation des totaux** (`calculerTotaux()`)
6. **Synchronisation de l'interface** (sliders, affichages)

## ✅ Désactivation du Mode Édition

Pour quitter le mode édition :
- Cliquez sur n'importe quel autre outil (Zone PV, Mesure, etc.)
- Le badge disparaît automatiquement avec animation
- Les rectangles redeviennent invisibles (opacity: 0)
- Les poignées de rotation sont masquées
- Le dragging est désactivé

```javascript
// Restauration automatique
layer.setStyle({
    opacity: 0,
    fillOpacity: 0,
    weight: 2,
    dashArray: null
});
layer.dragging.disable();
```

## 🎓 Bonnes Pratiques

1. **Toujours activer le mode édition avant de modifier** : Cliquez sur "✏️ Modifier"
2. **Utilisez les poignées de coin pour redimensionner** : Plus précis que le dessin
3. **La poignée de rotation pour l'orientation** : Synchronisé avec le slider
4. **Déplacez les zones pour optimiser l'espacement** : Drag & drop fluide
5. **Vérifiez les valeurs après modification** : Modules, puissance, productible

## 🐛 Dépannage

**Les poignées ne s'affichent pas ?**
→ Vérifiez que vous êtes bien en mode "✏️ Modifier" (bouton vert actif)

**Le drag ne fonctionne pas ?**
→ Assurez-vous de cliquer sur la zone elle-même, pas sur une poignée

**La rotation est imprécise ?**
→ Utilisez aussi le slider d'orientation pour un réglage fin

**Les modules ne se redessinent pas ?**
→ Désactivez puis réactivez le mode édition

## 📚 Références Leaflet

- [Leaflet.draw - Edit Mode](https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#l-edit-toolbar)
- [Leaflet Handlers](https://leafletjs.com/reference.html#handler)
- [Leaflet Events](https://leafletjs.com/reference.html#events)
- [L.Rectangle](https://leafletjs.com/reference.html#rectangle)
- [L.Marker Dragging](https://leafletjs.com/reference.html#marker-dragging)

---

**Version :** 2.0 - Janvier 2026  
**Basé sur :** Leaflet 1.9.4 + Leaflet.draw 1.0.4
