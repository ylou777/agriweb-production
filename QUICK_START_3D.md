# 🚀 Guide de démarrage rapide - Vue 3D WebGL

## ✨ Nouvelle fonctionnalité disponible !

Votre application AgriWeb dispose maintenant d'une **vue 3D immersive** pour visualiser les installations photovoltaïques en relief avec un rendu réaliste.

## 📝 Comment utiliser la vue 3D ?

### 1️⃣ Démarrer l'application

```bash
# Terminal PowerShell
cd C:\Users\Utilisateur\Desktop\AG32.1\ag3reprise
python run_app.py
```

### 2️⃣ Accéder au calpinage

1. Ouvrez votre navigateur : http://localhost:5000
2. Connectez-vous au CRM
3. Sélectionnez un prospect
4. Cliquez sur **"🔆 Calpinage PV"**

### 3️⃣ Dessiner des zones PV (vue 2D)

1. Utilisez l'outil **"▢ Zone PV"**
2. Dessinez un ou plusieurs rectangles sur la carte
3. Ajustez l'orientation et l'inclinaison dans le panneau de droite

### 4️⃣ Activer la vue 3D 🌐

1. Cliquez sur le bouton **"🌐 Vue 3D"** en haut de la carte
2. La vue bascule automatiquement en mode 3D

**Vous verrez :**
- ✅ Le bâtiment en relief (hauteur réelle)
- ✅ Les modules PV en 3D (bleu métallique)
- ✅ Les ombres portées du soleil
- ✅ Le sol avec grille de référence

### 5️⃣ Naviguer en 3D 🎮

| Action | Contrôle |
|--------|----------|
| **Rotation** | Clic gauche + déplacer |
| **Zoom** | Molette de la souris |
| **Déplacement** | Clic droit + déplacer |

### 6️⃣ Simuler le soleil ☀️

1. Cliquez sur le bouton **"☀️ Soleil"**
2. Observez l'animation de la course du soleil
3. Voyez les ombres se déplacer sur les modules
4. Re-cliquez pour arrêter

### 7️⃣ Retour en vue 2D

Cliquez sur **"🗺️ Retour 2D"** pour revenir à Leaflet

## 🎯 Cas d'usage

### Pour un commercial
- **Montrer l'installation** au client en 3D → Impact visuel fort
- **Simulation d'ombrage** → Crédibilité technique
- **Plusieurs angles de vue** → Meilleure compréhension

### Pour un technicien
- **Vérifier le dimensionnement** visuellement
- **Détecter les problèmes** d'ombrage potentiels
- **Valider l'orientation** optimale des modules

### Pour un client
- **Voir son projet** de façon réaliste
- **Comprendre l'installation** facilement
- **Se projeter** dans le résultat final

## 🔧 Dépannage

### La vue 3D ne s'affiche pas ?

**Vérifiez :**
1. ✅ Votre navigateur supporte WebGL (Chrome, Firefox, Edge, Safari)
2. ✅ Vous avez au moins une zone PV dessinée
3. ✅ JavaScript est activé
4. ✅ Pas de bloqueur de contenu actif

**Test WebGL :**
Ouvrez https://get.webgl.org/ → Doit afficher un cube 3D

### Performance lente ?

- **Réduire** le nombre de modules (très grandes installations)
- **Fermer** les autres onglets gourmands
- **Utiliser** un navigateur récent
- **Activer** l'accélération matérielle dans les paramètres du navigateur

### Le soleil ne bouge pas ?

- Vérifier que l'animation est bien démarrée (bouton "⏸️ Stop" affiché)
- Rafraîchir la page et réessayer

## 💡 Astuces pro

1. **Combinez 2D et 3D** : Utilisez la 2D pour la précision, la 3D pour la présentation
2. **Capturez des screenshots** : Utilisez les outils de capture pour vos présentations
3. **Testez différents angles** : Montrez plusieurs vues au client
4. **Utilisez l'animation soleil** : Effet "wow" garanti en rendez-vous !

## 📊 Performances attendues

| Type projet | Modules | Expérience |
|------------|---------|------------|
| Résidentiel (< 10 kWc) | ~20 | 🟢 Fluide (60 FPS) |
| Petit tertiaire (50 kWc) | ~100 | 🟢 Fluide (60 FPS) |
| Grand tertiaire (200 kWc) | ~400 | 🟡 Correct (50 FPS) |
| Centrale sol (1 MWc) | ~2000 | 🟠 Lent (30 FPS) |

## 🆘 Support

En cas de problème :
1. Vérifiez la console JavaScript (F12)
2. Consultez `DOCS_3D_WEBGL.md` pour plus de détails
3. Contactez le support technique

---

**Enjoy! 🎉** La vue 3D WebGL transforme votre présentation commerciale !
