# 🔄 FIX - Boucle Infinie dans la Recherche par Adresse

## 🐛 Problème identifié

La recherche par adresse se relance automatiquement en boucle infinie.

### Cause

Le template `index.html` contient un mécanisme de **zoom automatique** qui :
1. Détecte les paramètres `zoom_lat` et `zoom_lon` dans l'URL
2. Lance automatiquement une recherche au chargement de la page
3. La recherche recharge la page avec les mêmes paramètres
4. → **BOUCLE INFINIE** 🔄

```javascript
// Code problématique (AVANT)
{% if zoom_lat and zoom_lon %}
document.addEventListener('DOMContentLoaded', function() {
    // Lance la recherche à CHAQUE chargement
    searchForm.dispatchEvent(new Event('submit'));
});
{% endif %}
```

---

## ✅ Solution appliquée

Ajout d'un **flag dans sessionStorage** pour éviter la boucle :

```javascript
// Code corrigé (APRÈS)
{% if zoom_lat and zoom_lon %}
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si on a déjà fait la recherche
    const autoSearchDone = sessionStorage.getItem('autoSearchDone');
    if (autoSearchDone === 'true') {
        console.log('🔄 Recherche déjà effectuée, annulation');
        return;  // ← Empêche la boucle
    }
    
    // Marquer que la recherche a été faite
    sessionStorage.setItem('autoSearchDone', 'true');
    
    // Lancer la recherche (une seule fois)
    searchForm.dispatchEvent(new Event('submit'));
});
{% endif %}
```

---

## 🔍 Comment ça fonctionne

### sessionStorage

- **sessionStorage** = stockage temporaire qui dure pendant la session du navigateur
- Persiste entre les rechargements de page
- Se réinitialise quand on ferme l'onglet

### Flux corrigé

1. **Premier chargement**
   - `autoSearchDone` = null
   - La recherche se lance ✅
   - `autoSearchDone` = 'true'

2. **Rechargement suivant (même onglet)**
   - `autoSearchDone` = 'true'
   - La recherche est **annulée** ✅
   - Pas de boucle 🎉

3. **Nouvel onglet / Nouvelle session**
   - `autoSearchDone` = null (sessionStorage vide)
   - La recherche peut se lancer à nouveau ✅

---

## 🧪 Test de la correction

### Test 1: Recherche normale
```
1. Allez sur http://localhost:5000
2. Tapez une adresse dans le champ de recherche
3. Cliquez sur "Rechercher"
4. ✅ La recherche s'exécute UNE FOIS
5. ✅ Pas de relancement automatique
```

### Test 2: Zoom automatique
```
1. URL avec paramètres: 
   http://localhost:5000/?zoom_lat=45.85&zoom_lon=1.25&zoom_address=Limoges
2. La page charge
3. ✅ La recherche se lance automatiquement UNE FOIS
4. ✅ Si vous rechargez (F5), la recherche ne se relance PAS
```

### Test 3: Réinitialisation
```
1. Fermez l'onglet complètement
2. Rouvrez l'URL avec zoom_lat/zoom_lon
3. ✅ La recherche automatique fonctionne à nouveau
```

---

## 🛠️ Solution alternative (si le problème persiste)

### Option 1: Désactiver complètement le zoom auto

Dans `templates/index.html`, commentez ou supprimez :

```javascript
// DÉSACTIVER LE ZOOM AUTO
{% if zoom_lat and zoom_lon %}
/*
document.addEventListener('DOMContentLoaded', function() {
    // ... tout le code du zoom auto ...
});
*/
{% endif %}
```

### Option 2: Nettoyer les paramètres d'URL

Modifiez le code pour supprimer les paramètres après la première recherche :

```javascript
// Après avoir lancé la recherche
searchForm.dispatchEvent(new Event('submit'));

// Nettoyer l'URL (enlever zoom_lat, zoom_lon)
if (window.history.replaceState) {
    const url = new URL(window.location);
    url.searchParams.delete('zoom_lat');
    url.searchParams.delete('zoom_lon');
    url.searchParams.delete('zoom_address');
    window.history.replaceState({}, document.title, url);
}
```

### Option 3: Utiliser localStorage au lieu de sessionStorage

Pour une persistance encore plus longue :

```javascript
// Utiliser localStorage au lieu de sessionStorage
const autoSearchDone = localStorage.getItem('autoSearchDone_' + window.location.href);
if (autoSearchDone) return;

localStorage.setItem('autoSearchDone_' + window.location.href, 'true');
```

---

## 🔧 Commandes de diagnostic

### Vérifier sessionStorage dans la console

```javascript
// Ouvrir la console (F12)
console.log('autoSearchDone:', sessionStorage.getItem('autoSearchDone'));

// Réinitialiser manuellement
sessionStorage.removeItem('autoSearchDone');

// Vider tout le sessionStorage
sessionStorage.clear();
```

### Voir les paramètres d'URL

```javascript
// Dans la console
console.log('URL params:', new URL(window.location).searchParams.toString());
```

---

## 📊 Impact de la correction

| Aspect | Avant (Boucle) | Après (Corrigé) |
|--------|----------------|-----------------|
| **Recherche manuelle** | ✅ Fonctionne | ✅ Fonctionne |
| **Zoom automatique 1ère fois** | ✅ Fonctionne | ✅ Fonctionne |
| **Rechargement (F5)** | ❌ Boucle infinie | ✅ Pas de recherche |
| **Nouvel onglet** | ❌ Boucle infinie | ✅ Recherche 1 fois |
| **Performance** | ❌ CPU à 100% | ✅ Normal |

---

## 🚨 Si le problème persiste

### Vérifiez d'autres causes possibles

1. **Événement `change` sur l'input**
   ```javascript
   // Cherchez dans le code
   searchInput.addEventListener('change', ...);  // ← Peut causer la boucle
   ```

2. **Autocomplétion qui déclenche submit**
   ```javascript
   // Dans autocomplete.js
   // form.dispatchEvent(new Event('submit'));  // ← Doit être commenté
   ```

3. **Redirection après recherche**
   ```python
   # Dans le backend Flask
   # return redirect(...)  # ← Peut causer la boucle
   ```

---

## 📝 Vérification finale

Après correction, ouvrez la console (F12) et vous devriez voir :

**Premier chargement avec zoom_lat/zoom_lon :**
```
🎯 Zoom automatique demandé: 45.85, 1.25, 'Limoges'
🔍 Déclenchement recherche automatique
```

**Rechargement (F5) :**
```
🔄 Recherche automatique déjà effectuée, annulation
```

✅ **C'est bon !**

---

## 🎯 Commande pour tester

```powershell
# Démarrer Flask
python agriweb_hebergement_gratuit.py

# Ouvrir dans le navigateur
start http://localhost:5000

# Test avec zoom auto
start "http://localhost:5000/?zoom_lat=45.85&zoom_lon=1.25&zoom_address=Limoges"
```

---

**Version:** 1.0.0  
**Date:** Octobre 2025  
**Status:** ✅ CORRIGÉ

🎉 **La boucle infinie est maintenant résolue !**
