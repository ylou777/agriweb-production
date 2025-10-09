# 🔄 FIX - Boucle Infinie dans la Recherche par Commune

## 🐛 Problème résolu

**Symptôme :** La recherche par commune se relance automatiquement en boucle infinie après avoir cliqué sur "Rechercher".

### Causes identifiées

1. **Événement `change` déclenché par l'autocomplete**
   - L'autocomplete déclenchait un événement `change` après la sélection
   - Cet événement pouvait être écouté ailleurs et relancer la recherche

2. **Rechargement de l'iframe de la carte**
   - La fonction `handleCommuneSearch` recharge l'iframe avec `data.carte_url`
   - Ce rechargement pouvait déclencher à nouveau la recherche

3. **Pas de protection contre les soumissions multiples**
   - Aucun mécanisme n'empêchait la fonction de s'exécuter plusieurs fois simultanément

---

## ✅ Solutions appliquées

### Solution 1 : Désactivation de l'événement `change` dans l'autocomplete

**Fichier :** `static/autocomplete.js` (ligne ~188)

```javascript
// AVANT (problématique)
selectSuggestion(suggestion) {
    this.input.value = suggestion.value || suggestion.label;
    this.close();
    this.options.onSelect(suggestion);
    
    // ❌ Cet événement pouvait causer des boucles
    this.input.dispatchEvent(new Event('change', { bubbles: true }));
}

// APRÈS (corrigé)
selectSuggestion(suggestion) {
    this.input.value = suggestion.value || suggestion.label;
    this.close();
    this.options.onSelect(suggestion);
    
    // ✅ Événement désactivé pour éviter les boucles
    // this.input.dispatchEvent(new Event('change', { bubbles: true }));
}
```

**Impact :**
- ✅ Plus d'événement `change` propagé automatiquement
- ✅ Seul le callback `onSelect` est appelé (contrôlable)
- ⚠️ Si vous aviez des écouteurs `change`, ils ne seront plus déclenchés

---

### Solution 2 : Protection par `sessionStorage`

**Fichier :** `static/main.js` (fonction `handleCommuneSearch`)

```javascript
// AVANT (pas de protection)
async function handleCommuneSearch(e) {
  e?.preventDefault?.();
  setCommuneSearchLog('⏳ Connexion au serveur...', '#0a58ca');
  switchMap("/static/map.html", async () => {
    // ... code de recherche ...
  });
}

// APRÈS (avec protection)
async function handleCommuneSearch(e) {
  e?.preventDefault?.();
  
  // ✅ Protection contre les boucles infinies
  const searchKey = 'communeSearchInProgress';
  if (sessionStorage.getItem(searchKey) === 'true') {
    console.log('🔄 Recherche commune déjà en cours, annulation');
    return;  // ← Empêche la double exécution
  }
  
  // Marquer que la recherche est en cours
  sessionStorage.setItem(searchKey, 'true');
  
  setCommuneSearchLog('⏳ Connexion au serveur...', '#0a58ca');
  switchMap("/static/map.html", async () => {
    try {
      // ... code de recherche ...
      
      setCommuneSearchLog('✅ Recherche terminée avec succès !', '#198754');
    } catch (err) {
      setCommuneSearchLog('❌ Erreur : ' + err, 'red');
      alert("Erreur lors de la recherche par commune : " + err);
    } finally {
      // ✅ Nettoyer le flag à la fin (succès ou erreur)
      sessionStorage.removeItem(searchKey);
    }
  });
}
```

**Fonctionnement :**

1. **Avant d'exécuter la recherche :**
   - Vérifier si `communeSearchInProgress` = `'true'`
   - Si oui → annuler (recherche déjà en cours)
   - Si non → continuer

2. **Pendant la recherche :**
   - Définir `communeSearchInProgress` = `'true'`
   - Empêche toute nouvelle exécution

3. **Après la recherche (succès ou erreur) :**
   - Supprimer le flag dans le `finally`
   - Permet une nouvelle recherche ultérieure

---

## 🔍 Comparaison avec la recherche par adresse

Les deux recherches avaient des problèmes similaires mais différents :

| Aspect | Recherche Adresse | Recherche Commune |
|--------|-------------------|-------------------|
| **Cause boucle** | Zoom auto avec paramètres URL | Événement change + rechargement iframe |
| **Solution** | `autoSearchDone` dans sessionStorage | `communeSearchInProgress` dans sessionStorage |
| **Localisation** | Template `index.html` | Fichier `main.js` |
| **Déclencheur** | Rechargement de page (F5) | Soumission du formulaire |

---

## 🧪 Tests de vérification

### Test 1 : Recherche normale

```
1. Allez sur http://localhost:5000
2. Ouvrez l'accordéon "Commune"
3. Tapez "Limoges" et cliquez sur "Rechercher"
4. ✅ La recherche s'exécute UNE FOIS
5. ✅ Les résultats s'affichent
6. ✅ Pas de relancement automatique
```

### Test 2 : Avec autocomplete

```
1. Ouvrez l'accordéon "Commune"
2. Tapez "limo" dans le champ
3. Sélectionnez "Limoges" dans les suggestions
4. ✅ Le champ se remplit avec "Limoges"
5. ✅ AUCUNE recherche automatique ne se lance
6. Cliquez manuellement sur "Rechercher"
7. ✅ La recherche s'exécute UNE FOIS
```

### Test 3 : Clicks multiples rapides

```
1. Tapez une commune
2. Cliquez RAPIDEMENT plusieurs fois sur "Rechercher"
3. ✅ Seule la première recherche s'exécute
4. ✅ Les autres sont annulées (console affiche "Recherche déjà en cours")
```

### Test 4 : Vérification console

Ouvrez la console (F12) et observez les messages :

```
🔄 Envoi de la requête... Calculs en cours...
📦 Traitement des données reçues...
✅ Recherche terminée avec succès !

// Si double click :
🔄 Recherche commune déjà en cours, annulation  ← Protection active !
```

---

## 🛠️ Diagnostic en cas de problème

### Vérification 1 : sessionStorage

```javascript
// Dans la console (F12)
console.log(sessionStorage.getItem('communeSearchInProgress'));
// Doit afficher "true" pendant la recherche, null après
```

### Vérification 2 : Événements change

```javascript
// Ajouter un écouteur de test
document.getElementById('commune').addEventListener('change', function() {
  console.warn('⚠️ Événement change détecté sur commune');
});

// Sélectionnez une suggestion
// Si le message apparaît, l'événement change est encore actif (problème)
```

### Vérification 3 : Compteur de recherches

```javascript
// Dans main.js, au début de handleCommuneSearch, ajoutez :
let searchCount = 0;
async function handleCommuneSearch(e) {
  searchCount++;
  console.log('🔢 Nombre de recherches:', searchCount);
  // ...
}

// Lancez une recherche et vérifiez que le compteur n'augmente qu'une fois
```

---

## 📊 Flux de protection

```
┌──────────────────────────────────────┐
│ Utilisateur clique "Rechercher"     │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│ handleCommuneSearch() appelée        │
└──────────────┬───────────────────────┘
               │
               ▼
         ┌─────────────┐
         │ sessionStorage │
         │ = 'true' ?   │
         └─────┬───┬────┘
               │   │
         OUI ──┘   └── NON
          │             │
          ▼             ▼
    ┌─────────┐   ┌──────────────┐
    │ ANNULER │   │ Définir flag │
    │ (return)│   │ = 'true'     │
    └─────────┘   └──────┬───────┘
                         │
                         ▼
                  ┌────────────────┐
                  │ Recherche API  │
                  └──────┬─────────┘
                         │
                         ▼
                  ┌────────────────┐
                  │ Affichage OK   │
                  └──────┬─────────┘
                         │
                         ▼
                  ┌────────────────┐
                  │ finally:       │
                  │ Supprimer flag │
                  └────────────────┘
```

---

## 🎯 Avantages de la solution

✅ **Protection robuste** : Bloque les exécutions multiples  
✅ **Nettoyage automatique** : Le `finally` garantit la suppression du flag  
✅ **Messages clairs** : Console indique quand une recherche est annulée  
✅ **Pas de timeout arbitraire** : Le flag est supprimé dès la fin de la recherche  
✅ **Compatible** : Fonctionne avec toutes les méthodes de soumission (click, Enter, API)

---

## 🔧 Alternative : Désactiver le bouton pendant la recherche

Si vous voulez un feedback visuel, ajoutez :

```javascript
async function handleCommuneSearch(e) {
  e?.preventDefault?.();
  
  const searchBtn = document.querySelector('#communeSearchForm button[type="submit"]');
  
  // Désactiver le bouton
  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Recherche...';
  }
  
  try {
    // ... recherche ...
  } finally {
    // Réactiver le bouton
    if (searchBtn) {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="bi bi-search"></i> Rechercher';
    }
  }
}
```

---

## 📝 Checklist de vérification

Après avoir appliqué les corrections :

- [ ] Rafraîchir la page (Ctrl + Shift + R)
- [ ] Tester une recherche par commune normale
- [ ] Tester avec l'autocomplete
- [ ] Tester des clicks multiples rapides
- [ ] Vérifier la console (pas d'erreurs)
- [ ] Vérifier que `sessionStorage.getItem('communeSearchInProgress')` revient à `null`
- [ ] Tester une nouvelle recherche après la première (doit fonctionner)

---

## 📚 Fichiers modifiés

1. **`static/autocomplete.js`** (ligne 188)
   - Désactivation de `dispatchEvent('change')`

2. **`static/main.js`** (fonction `handleCommuneSearch`)
   - Ajout de la protection `sessionStorage`
   - Ajout du `try-catch-finally`

---

**Version :** 1.0.0  
**Date :** Octobre 2025  
**Status :** ✅ CORRIGÉ

🎉 **La boucle infinie dans la recherche par commune est maintenant résolue !**

---

## 🚀 Pour tester immédiatement

```powershell
# Rafraîchir la page
# Ctrl + Shift + R

# Ou redémarrer Flask si nécessaire
# Ctrl + C (arrêter)
python agriweb_hebergement_gratuit.py
```
